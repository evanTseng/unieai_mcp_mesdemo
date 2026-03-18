import httpx
import uvicorn
import os
from fastapi import FastAPI, Request, Body, status
from fastapi.responses import HTMLResponse
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 1. 初始化 FastMCP 與 FastAPI
mcp = FastMCP("MES-Assistant")
app = FastAPI(
    title="JoyTech MES 系統介面",
    description="本伺服器作為 JoyTech 自動化與 MES 系統的橋樑，提供人員工時與工單狀態的同步功能。",
    version="1.0.0"
)

BASE_URL = "https://mesapidemo.zeabur.app"

# === 資料模型 (提供 API 說明文件) ===

class StaffRequest(BaseModel):
    staff_id: str = Field(..., description="員工工號，例如：'A01'", example="A01")
    station_id: str = Field(..., description="站點或機台編號，例如：'S01'", example="S01")

class JobRequest(BaseModel):
    job_id: str = Field(..., description="生產工單編號，例如：'JOB123'", example="JOB123")
    station_id: str = Field(..., description="站點編號，例如：'S01'", example="S01")

# === 核心邏輯 (共享函式) ===

async def call_mes_api(path: str, payload: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}{path}", json=payload)
        # 假設 MES API 回傳的是 JSON 字串，我們直接返回
        return res.json()

# === API 路由定義 (具備詳細說明) ===

@app.post("/api/staff/check-in", 
          tags=["人員管理"], 
          summary="人員上工登記",
          description="當員工抵達站點準備作業時調用，紀錄員工開始作業的時間與位置。")
async def api_staff_check_in(data: StaffRequest):
    return await staff_check_in(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_in(staff_id: str, station_id: str) -> str:
    """人員上工登記：紀錄 [員工編號] 於 [站點] 開始工作。"""
    return str(await call_mes_api("/staff/check-in", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/staff/check-out", 
          tags=["人員管理"], 
          summary="人員下工登記",
          description="當員工完成作業或休息離開站點時調用，結束該時段的工時計算。")
async def api_staff_check_out(data: StaffRequest):
    return await staff_check_out(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_out(staff_id: str, station_id: str) -> str:
    """人員下工登記：紀錄 [員工編號] 離開 [站點]。"""
    return str(await call_mes_api("/staff/check-out", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/job/entry", 
          tags=["工單管理"], 
          summary="工單進站",
          description="紀錄特定工單進入站點準備加工，用於追蹤在製品 (WIP) 位置。")
async def api_job_entry(data: JobRequest):
    return await job_entry(data.job_id, data.station_id)

@mcp.tool()
async def job_entry(job_id: str, station_id: str) -> str:
    """工單進站：將 [工單編號] 移入 [站點]。"""
    return str(await call_mes_api("/job/entry", {"job_id": job_id, "station_id": station_id}))

@app.post("/api/job/exit", 
          tags=["工單管理"], 
          summary="工單出站",
          description="紀錄工單完成該站點加工並移出，系統將自動更新生產進度。")
async def api_job_exit(data: JobRequest):
    return await job_exit(data.job_id, data.station_id)

@mcp.tool()
async def job_exit(job_id: str, station_id: str) -> str:
    """工單出站：將 [工單編號] 從 [站點] 移出。"""
    return str(await call_mes_api("/job/exit", {"job_id": job_id, "station_id": station_id}))

# === MCP 協議路由 (SSE) ===

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h1>JoyTech MES MCP Server 運行中</h1>
    <p>✅ <b>人機介面 (GUI):</b> <a href="/docs">Swagger API 文件</a></p>
    <p>🤖 <b>AI 連線 (MCP):</b> <code>/sse</code></p>
    """

@app.get("/sse")
async def sse(request: Request):
    async with mcp._app.sse_handler(request) as handler:
        return handler

@app.post("/messages")
async def messages(request: Request):
    return await mcp._app.handle_post_messages(request)

def main():
    #port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=9090)

if __name__ == "__main__":
    main()