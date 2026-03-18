import httpx
import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastmcp import FastMCP

# 1. 初始化 FastMCP (用於定義 Tools)
mcp = FastMCP("MES-Assistant")

# 2. 初始化 FastAPI (用於提供 /docs 網頁)
app = FastAPI(
    title="MES Assistant MCP Server",
    description="提供人員上/下工與工單進/出站的 API 文件",
    version="1.0.0"
)

BASE_URL = "https://mesapidemo.zeabur.app"

# === MCP Tools 定義 ===

@mcp.tool()
async def staff_check_in(staff_id: str, station_id: str) -> str:
    """人員上工登記"""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/staff/check-in", json={
            "staff_id": staff_id,
            "station_id": station_id
        })
        return res.text

@mcp.tool()
async def staff_check_out(staff_id: str, station_id: str) -> str:
    """人員下工登記"""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/staff/check-out", json={
            "staff_id": staff_id,
            "station_id": station_id
        })
        return res.text

@mcp.tool()
async def job_entry(job_id: str, station_id: str) -> str:
    """工單進站登記"""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/job/entry", json={
            "job_id": job_id,
            "station_id": station_id
        })
        return res.text

@mcp.tool()
async def job_exit(job_id: str, station_id: str) -> str:
    """工單出站登記"""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/job/exit", json={
            "job_id": job_id,
            "station_id": station_id
        })
        return res.text

# === 路由設定 ===

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1>MES MCP Server 運行中</h1>
    <p>查看 API 文件: <a href="/docs">/docs</a></p>
    <p>MCP SSE 連線網址: <code>/sse</code></p>
    """

# 關鍵：處理 MCP 的 SSE 連線，這取代了報錯的 mount_to_api
@app.get("/sse")
async def sse(request: Request):
    async with mcp._app.sse_handler(request) as handler:
        return handler

@app.post("/messages")
async def messages(request: Request):
    return await mcp._app.handle_post_messages(request)

# === 啟動進入點 ===

def main():
    """啟動 Uvicorn 伺服器"""
    #port = int(os.getenv("PORT", 8080))
    # 這裡啟動的是 FastAPI 的 app
    uvicorn.run(app, host="0.0.0.0", port=9090)

if __name__ == "__main__":
    main()