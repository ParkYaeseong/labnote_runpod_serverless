import os
import json
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse


RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY") or os.getenv("RUNPOD_API_TOKEN") or os.getenv("VESSL_API_TOKEN")
PROXY_RUNPOD_ENDPOINT_ID = os.getenv("PROXY_RUNPOD_ENDPOINT_ID") or os.getenv("RUNPOD_ENDPOINT_ID")

if not PROXY_RUNPOD_ENDPOINT_ID:
    # Allow starting without endpoint ID for local dev; requests will fail with 500 until configured.
    pass

RUNSYNC_BASE = f"https://api.runpod.ai/v2/{PROXY_RUNPOD_ENDPOINT_ID}" if PROXY_RUNPOD_ENDPOINT_ID else None

app = FastAPI(title="LabNote RunPod Proxy", version="1.0.0")


async def _call_runsync(method: str, path: str, body: Optional[Dict[str, Any]] = None, timeout: float = 300.0) -> Dict[str, Any]:
    if not RUNSYNC_BASE:
        raise HTTPException(status_code=500, detail="PROXY_RUNPOD_ENDPOINT_ID is not configured.")
    if not RUNPOD_API_KEY:
        raise HTTPException(status_code=500, detail="RUNPOD_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": {
            "method": method,
            "path": path,
            "body": body if method.upper() != "GET" else None,
        }
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{RUNSYNC_BASE}/runsync", headers=headers, json=payload)
        try:
            data = resp.json()
        except Exception:
            raise HTTPException(status_code=resp.status_code, detail=f"RunPod runsync returned non-JSON body (status {resp.status_code}).")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=data)

        # runsync response usually: { status: 'COMPLETED', output: {...} }
        if isinstance(data, dict) and "output" in data:
            return data["output"]
        return data


@app.get("/constants")
async def constants_proxy() -> JSONResponse:
    out = await _call_runsync("GET", "/constants", None, timeout=30)
    return JSONResponse(content=out)


@app.get("/v1/models")
async def list_models() -> JSONResponse:
    # Optional: try forwarding; if fails, return minimal stub
    try:
        out = await _call_runsync("GET", "/v1/models", None, timeout=30)
        if isinstance(out, dict):
            return JSONResponse(content=out)
    except Exception:
        pass
    return JSONResponse(
        content={
            "data": [
                {
                    "id": os.getenv("OPENAI_MODEL_ID", "labnote-backend"),
                    "object": "model",
                    "owned_by": "labnote",
                }
            ]
        }
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload for chat completions.")

    # Ensure non-streaming to simplify proxying
    if isinstance(payload, dict):
        payload.setdefault("stream", False)

    out = await _call_runsync("POST", "/v1/chat/completions", payload, timeout=300)
    if not isinstance(out, (dict, list)):
        # Try to coerce text into OpenAI-like response
        out = {
            "id": "chatcmpl-proxy",
            "object": "chat.completion",
            "created": int(__import__("time").time()),
            "model": payload.get("model", "labnote-backend") if isinstance(payload, dict) else "labnote-backend",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": str(out)}, "finish_reason": "stop"}
            ],
        }
    return JSONResponse(content=out)


@app.get("/")
async def root() -> Dict[str, Any]:
    return {"status": "ok", "proxy": "LabNote RunPod Proxy", "endpoint_id": PROXY_RUNPOD_ENDPOINT_ID}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def generic_forwarder(full_path: str, request: Request) -> JSONResponse:
    """
    Fallback forwarder so that extension-specific routes like /populate_note,
    /record_preference, /record_completion_feedback, /api/chat, etc. also work
    via the same proxy without code changes on the client side.
    """
    method = request.method.upper()
    body: Optional[Dict[str, Any]] = None
    if method != "GET":
        try:
            body = await request.json()
        except Exception:
            body = None
    # Prepend leading slash for the target path
    target_path = "/" + (full_path or "")
    out = await _call_runsync(method, target_path, body, timeout=300)
    # out is expected to be JSON-serializable (dict/list/str)
    if isinstance(out, (dict, list)):
        return JSONResponse(content=out)
    return JSONResponse(content={"result": out})
