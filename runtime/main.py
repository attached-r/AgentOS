from fastapi import FastAPI
from agents.registry import router as agent_router
from workflows.single_agent import router as invoke_router

app = FastAPI(title="AgentOS Runtime")
app.include_router(agent_router, prefix="/runtime/agents")
app.include_router(invoke_router, prefix="/runtime/agents")


