"""Chat endpoint for processing AI queries."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from api.middleware.auth import verify_api_key
from brain_secure import brain

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None
    thread_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    model_used: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None


class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5


class CodeExecutionRequest(BaseModel):
    code: str
    timeout: int = 5


@router.post("/chat")
async def chat(
    request: ChatRequest, user: dict = Depends(verify_api_key)
) -> ChatResponse:
    """Process a chat message and return AI response."""
    import time

    start_time = time.time()

    try:
        # Convert history to format expected by brain
        context = []
        if request.history:
            for msg in request.history:
                context.append({"role": msg.role, "content": msg.content})

        # Process query through brain
        response_text = await brain.process_query(
            user_text=request.message,
            model_id=request.model_id,
            thread_id=request.thread_id,
            context=context if context else None,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Get model info
        model_config = await brain._get_model_config(request.model_id)
        model_name = (
            f"{model_config.get('provider', 'unknown')}/{model_config.get('model_id', 'unknown')}"
            if model_config
            else "unknown"
        )

        return ChatResponse(
            response=response_text, model_used=model_name, latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/web-search")
async def web_search(
    request: WebSearchRequest, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Perform web search."""
    try:
        results = await brain.web_search(request.query, request.max_results)
        return {
            "ok": True,
            "query": request.query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


@router.post("/execute-code")
async def execute_code(
    request: CodeExecutionRequest, user: dict = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Execute Python code securely."""
    try:
        result = await brain.execute_python(request.code)
        return {
            "ok": result.get("success", False),
            "output": result.get("output", ""),
            "error": result.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")


@router.get("/usage")
async def get_usage(user: dict = Depends(verify_api_key)) -> Dict[str, Any]:
    """Get usage statistics."""
    stats = await brain.get_usage_stats()
    return {
        "ok": True,
        "total_requests": stats.get("total_requests", 0),
        "total_tokens": stats.get("total_tokens", 0),
        "providers": stats.get("by_provider", {}),
    }
