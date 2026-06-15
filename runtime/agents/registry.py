from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AgentConfig(BaseModel):
    """Agent configuration model — matches the Spring Boot agent table schema."""
    id: int
    name: str = ""
    description: str = ""
    system_prompt: str = ""
    model_provider: str = "openai"
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    base_url: Optional[str] = None
    api_key: Optional[str] = None


# In-memory registry: agent_id -> agent_config dict
agent_registry: dict[int, dict] = {}


@router.get("/")
async def list_agents():
    """List all registered agents (for debugging / monitoring)."""
    return list(agent_registry.values())


@router.post("/sync")
async def sync_agents(agents: list[AgentConfig]):
    """Replace the entire registry with configs pushed from Spring Boot at startup."""
    agent_registry.clear()
    for agent in agents:
        agent_registry[agent.id] = agent.model_dump()
    return {"status": "ok", "count": len(agents)}
