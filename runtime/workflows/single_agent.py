from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from agents.executor import AgentExecutor
from agents.registry import agent_registry

router = APIRouter()


class InvokeRequest(BaseModel):
    """Matches the JSON sent by Spring Boot's AgentRuntimeClient."""
    conversation_id: int = Field(alias="conversationId")
    messages: list[dict]

    model_config = {"populate_by_name": True}


@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id: int, req: InvokeRequest):
    """Execute a single agent and return the LLM response."""
    config = agent_registry.get(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        executor = AgentExecutor(config)
        result = await executor.invoke(req.messages)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return result
