/**
 * Markdown 渲染工具
 *
 * 将 LLM 返回的 Markdown 文本渲染为带代码高亮的 HTML。
 * 使用 marked 解析 Markdown，highlight.js 处理代码块高亮。
 */

import { marked } from 'marked'
import hljs from 'highlight.js'
// 引入 highlight.js 的样式（根据主题二选一，默认 GitHub 风格）
import 'highlight.js/styles/github.css'

// ── 配置 marked ──────────────────────────────────────────────

marked.setOptions({
  gfm: true,                  // 启用 GitHub Flavored Markdown
  breaks: true,               // 支持换行符 <br>
})

/**
 * 自定义代码块渲染
 *
 * 在 marked 默认的 <pre><code> 外包再包一层容器，用于后续添加复制按钮。
 * 处理后的结构：
 *   <div class="code-block-wrapper">
 *     <div class="code-block-header">
 *       <span class="code-lang">语言名</span>
 *       <button class="copy-btn" data-code="原始代码">复制</button>
 *     </div>
 *     <pre><code class="hljs language-xxx">高亮后的 HTML</code></pre>
 *   </div>
 */
function renderCodeBlock(code: string, lang: string | undefined): string {
  const language = lang || 'plaintext'

  // 用 highlight.js 做语法高亮，失败则降级为纯文本
  let highlighted: string
  try {
    if (lang && hljs.getLanguage(lang)) {
      highlighted = hljs.highlight(code, { language: lang }).value
    } else {
      highlighted = hljs.highlightAuto(code).value
    }
  } catch {
    highlighted = escapeHtml(code)
  }

  // 构建代码块外包装
  const langLabel = language !== 'plaintext' ? language : ''
  const encodedCode = encodeAttr(code)       // 存到 data-code 供复制按钮读取
  return `
    <div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-lang">${escapeHtml(langLabel)}</span>
        <button class="copy-btn" data-code="${encodedCode}">复制</button>
      </div>
      <pre><code class="hljs language-${escapeHtml(language)}">${highlighted}</code></pre>
    </div>
  `.trim()
}

/**
 * 扩展 marked 的默认渲染器
 *
 * 主要替换 code 和 codespan 的渲染逻辑：
 *   - 代码块 → 使用 highlight.js + 复制按钮包装
 *   - 行内代码 → 保持默认 <code> 样式
 */
const renderer = new marked.Renderer()

// 覆盖代码块渲染
renderer.code = ({ text, lang }) => renderCodeBlock(text, lang)

// ── HTML 转义工具（防止 XSS）──────────────────────────────

/** 转义 HTML 特殊字符，用于安全地插入纯文本到 HTML 中 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/** 编码 HTML 属性值，用于嵌入 data-* 属性 */
function encodeAttr(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '&#10;')
}

// ── 公共渲染函数 ──────────────────────────────────────────

/**
 * 将 Markdown 文本渲染为安全的 HTML
 *
 * @param content - 原始 Markdown 文本（来自 LLM 回复）
 * @returns 渲染后的 HTML 字符串
 */
export function renderMarkdown(content: string): string {
  if (!content) return ''

  try {
    return marked.parse(content, { renderer }) as string
  } catch {
    // 解析失败时降级为纯文本（转义后显示）
    return `<p>${escapeHtml(content)}</p>`
  }
}

/**
 * 初始化代码块复制按钮的点击事件
 *
 * 在 DOM 更新后调用，为所有 .copy-btn 绑定点击事件。
 * 使用事件委托避免重复绑定。
 *
 * @param container - 包含代码块的父容器（通常是消息列表）
 */
export function initCopyButtons(container: HTMLElement): void {
  container.addEventListener('click', async (e: Event) => {
    const target = e.target as HTMLElement
    const btn = target.closest<HTMLButtonElement>('.copy-btn')
    if (!btn) return

    const code = btn.getAttribute('data-code') || ''
    try {
      // 解码 data-code 中的 HTML 实体
      const decoded = code
        .replace(/&#10;/g, '\n')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&amp;/g, '&')

      await navigator.clipboard.writeText(decoded)
      btn.textContent = '已复制'
      btn.classList.add('copied')

      // 2 秒后恢复
      setTimeout(() => {
        btn.textContent = '复制'
        btn.classList.remove('copied')
      }, 2000)
    } catch {
      btn.textContent = '复制失败'
      setTimeout(() => {
        btn.textContent = '复制'
      }, 2000)
    }
  })
}
