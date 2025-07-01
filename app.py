import asyncio
import json

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from utils import handle_repo, get_repo_name

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    async def handle_and_send(url):
        repo_name = get_repo_name(url)
        if repo_name:
            await websocket.send_text(json.dumps({"type": "received", "repo": repo_name}))
        result = await handle_repo(url)
        await websocket.send_text(json.dumps(result))

    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            asyncio.create_task(handle_and_send(data))
        except WebSocketDisconnect:
            print("WebSocket closed")
            break

async def run():
    uvicorn_config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config=uvicorn_config)
    await server.serve()

asyncio.run(run())