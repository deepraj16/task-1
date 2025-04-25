from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests

app = FastAPI()

VAPI_API_KEY = "9dce4862-024b-48e6-b26f-42e4869850d7"
RETELL_API_KEY = "key_9243de26f1e80e60bc2aa0f2a68c"

VAPI_URL = "https://api.vapi.ai/assistants"
RETELL_URL = "https://api.retellai.com/agents"

@app.post("/create-agent")
async def create_agent(request: Request):
    body = await request.json()

    platform = body.get("platform")
    data = body.get("data")

    if not platform or not data:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing 'platform' or 'data'"}
        )

    headers = {"Content-Type": "application/json"}

    if platform.lower() == "vapi":
        headers["Authorization"] = f"Bearer {VAPI_API_KEY}"
        response = requests.post(VAPI_URL, json=data, headers=headers)

    elif platform.lower() == "retell":
        headers["Authorization"] = f"Bearer {RETELL_API_KEY}"
        response = requests.post(RETELL_URL, json=data, headers=headers)

    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid platform. Use 'vapi' or 'retell'."}
        )

    try:
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status_code": response.status_code,
                "response": response.json()
            }
        )
    except Exception:
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status_code": response.status_code,
                "response": response.text
            }
        )
