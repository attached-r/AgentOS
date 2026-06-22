"""
嵌入服务 —— 文本向量化。

V2 简化方案：
  使用 TF-IDF 进行简单的文本向量化（基于词频统计）。
  不依赖外部嵌入服务（如 fastembed）或向量数据库（如 Qdrant）。
  V3 迁移到 fastembed + Qdrant 实现语义检索。

注意：
  V2 的嵌入服务主要用于记忆检索的排序辅助，
  核心的记忆和 RAG 检索仍以关键词匹配为主。
"""
import math
import re
from collections import Counter
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# TFIDFEmbedding —— 基于词频的文本向量化
# ---------------------------------------------------------------------------

class TFIDFEmbedding:
    """
    基于 TF-IDF 的文本嵌入服务。

    V2 简化实现：
      - 对所有文本进行分词（按空格和非字母字符分割）
      - 计算 TF-IDF 向量
      - 通过余弦相似度比较文本相似度
      - 不依赖外部库，纯 Python 实现

    注意：此实现适用于短文本（<1000 词）的记忆检索场景。
    对于大规模文档检索，应使用 fastembed + Qdrant（V3）。
    """

    def __init__(self, max_features: int = 256):
        """
        Args:
            max_features: 最大特征数（词汇表大小上限）
        """
        self.max_features = max_features
        self._vocab: Dict[str, int] = {}       # 词 → 索引
        self._idf: Dict[str, float] = {}       # 词 → IDF 值
        self._doc_count: int = 0               # 文档总数

    def _tokenize(self, text: str) -> List[str]:
        """分词：转小写，按非字母数字字符分割。"""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return [t for t in tokens if len(t) > 1]  # 过滤单字符词

    def fit(self, texts: List[str]) -> None:
        """
        训练 TF-IDF 模型。

        统计文档频率，计算 IDF。

        Args:
            texts: 训练文本列表
        """
        self._doc_count = len(texts)
        doc_freq: Dict[str, int] = {}

        for text in texts:
            tokens = set(self._tokenize(text))  # 每篇文档内去重
            for token in tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        # 按频率排序，截取 max_features
        sorted_terms = sorted(doc_freq.items(), key=lambda x: -x[1])[:self.max_features]

        for idx, (term, _) in enumerate(sorted_terms):
            self._vocab[term] = idx
            # IDF = log(总文档数 / 包含该词的文档数) + 1（平滑）
            self._idf[term] = math.log(self._doc_count / (doc_freq[term] + 1)) + 1

    def transform(self, text: str) -> List[float]:
        """
        将文本转换为 TF-IDF 向量。

        Args:
            text: 输入文本

        Returns:
            TF-IDF 向量（长度 = vocab_size 或 max_features）
        """
        if not self._vocab:
            return []

        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * len(self._vocab)

        # 计算 TF
        tf = Counter(tokens)
        max_tf = max(tf.values()) if tf else 1

        # 构建向量
        vector = [0.0] * len(self._vocab)
        for token, count in tf.items():
            if token in self._vocab:
                idx = self._vocab[token]
                # TF-IDF = (词频 / 最大词频) * IDF
                vector[idx] = (count / max_tf) * self._idf.get(token, 1.0)

        return vector

    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的余弦相似度。

        Args:
            text1: 第一段文本
            text2: 第二段文本

        Returns:
            余弦相似度（0.0 ~ 1.0）
        """
        vec1 = self.transform(text1)
        vec2 = self.transform(text2)

        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


# ---------------------------------------------------------------------------
# EmbeddingService —— 嵌入服务统一入口
# ---------------------------------------------------------------------------

class EmbeddingService:
    """
    文本嵌入服务统一入口。

    V2 使用 TF-IDF，V3 切换到 fastembed。

    用法：
        service = EmbeddingService()
        service.fit(corpus_texts)           # 训练
        vector = service.embed("查询文本")   # 嵌入
        sim = service.similarity("a", "b")  # 相似度
    """

    def __init__(self, model: str = "tfidf"):
        """
        Args:
            model: 嵌入模型类型
                   - "tfidf": TF-IDF（V2 默认）
                   - "fastembed": fastembed 嵌入（V3 启用）
        """
        self.model_name = model
        self._tfidf = TFIDFEmbedding() if model == "tfidf" else None
        self._fitted = False

    def fit(self, texts: List[str]) -> None:
        """训练嵌入模型。"""
        if self._tfidf:
            self._tfidf.fit(texts)
            self._fitted = True

    def embed(self, text: str) -> List[float]:
        """
        将文本转换为向量。

        Args:
            text: 输入文本

        Returns:
            向量表示（TF-IDF 维度为 max_features，fastembed 为 384 维）
        """
        if self._tfidf:
            return self._tfidf.transform(text)
        # V2 占位：返回 384 维零向量（fastembed 默认维度）
        return [0.0] * 384

    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两段文本的相似度。

        Args:
            text1: 第一段文本
            text2: 第二段文本

        Returns:
            相似度分数（0.0 ~ 1.0）
        """
        if self._tfidf:
            return self._tfidf.similarity(text1, text2)
        return 0.0
