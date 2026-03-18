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
          description="""
    【人員上工登記】
    當使用者提到「某人開始工作」、「某人到崗」、「人員報到」或「開啟作業」時使用。
    此工具會將員工 ID 繫結至特定的工作站點，啟動工時計算。
    參數：
    - staff_id: 員工工號 (例如: A01, F01)
    - station_id: 站點編號 (例如: S01, Assembly_Line_1)
    """)
async def api_staff_check_in(data: StaffRequest):
    return await staff_check_in(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_in(staff_id: str, station_id: str) -> str:
    """人員上工登記：紀錄 [員工編號] 於 [站點] 開始工作。"""
    return str(await call_mes_api("/staff/check-in", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/staff/check-out", 
          tags=["人員管理"], 
          summary="人員下工登記",
          description="""
    【人員下工登記】
    當使用者提到「下班」、「休息」、「離開崗位」、「完成今日作業」或「結束工作」時使用。
    此工具會解除員工與站點的繫結，並停止工時統計。
    參數：
    - staff_id: 員工工號 (例如: A01)
    - station_id: 站點編號 (例如: S01)
    """)
async def api_staff_check_out(data: StaffRequest):
    return await staff_check_out(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_out(staff_id: str, station_id: str) -> str:
    """人員下工登記：紀錄 [員工編號] 離開 [站點]。"""
    return str(await call_mes_api("/staff/check-out", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/job/entry", 
          tags=["工單管理"], 
          summary="工單進站",
          description="""
    【工單進站/投產】
    當有新的生產任務抵達特定機台、開始加工特定編號的產品或工單時使用。
    用於追蹤生產進度與在製品 (WIP) 的實體位置。
    參數：
    - job_id: 工單編號 (例如: JOB123, WO-2024-001)
    - station_id: 目標加工站點 (例如: S01, CNC_Machine)
    """)
async def api_job_entry(data: JobRequest):
    return await job_entry(data.job_id, data.station_id)

@mcp.tool()
async def job_entry(job_id: str, station_id: str) -> str:
    """工單進站：將 [工單編號] 移入 [站點]。"""
    return str(await call_mes_api("/job/entry", {"job_id": job_id, "station_id": station_id}))

@app.post("/api/job/exit", 
          tags=["工單管理"], 
          summary="工單出站",
          description="""
    【工單出站/完工】
    當特定工單在該站點加工完成、準備移往下一站、或是生產結束時使用。
    執行此工具代表該站點的加工程序已結束。
    參數：
    - job_id: 工單編號 (例如: JOB123)
    - station_id: 當前離開的站點 (例如: S01)
    """)
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