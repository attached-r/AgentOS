"""
健康检查端点 —— 供后端 / Docker 检测运行时是否存活。
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查。后端启动时会先 ping 此接口确认运行时就绪。"""
    return {"status": "ok", "service": "AgentOS Runtime"}
