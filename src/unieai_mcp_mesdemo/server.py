import httpx
import uvicorn
import os
from fastapi import FastAPI
from fastmcp import FastMCP

# 1. 初始化 FastMCP
mcp = FastMCP("MES-Assistant")

# 2. 初始化 FastAPI (這是顯示 /docs 的關鍵)
app = FastAPI(title="MES MCP Server API Docs")

BASE_URL = "https://mesapidemo.zeabur.app"

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

# 3. 將 MCP 工具掛載到 FastAPI 上 (預設會掛載在 /sse)
# 這會同時生成 OpenAPI 定義並開啟 Swagger UI
mcp.mount_to_api(app)

def main():
    """MCP 伺服器入口點 - 使用 uvicorn 啟動 FastAPI app"""
    #port = int(os.getenv("PORT", 8000))
    # 這裡要跑的是 app，而不是 mcp.run()
    uvicorn.run(app, host="0.0.0.0", port=9090)

if __name__ == "__main__":
    main()