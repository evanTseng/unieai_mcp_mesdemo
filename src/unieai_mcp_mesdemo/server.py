import httpx
import uvicorn
import os
from fastapi import FastAPI, Request, Body, status, HTTPException
from fastapi.responses import HTMLResponse
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 1. 初始化 FastMCP 與 FastAPI
mcp = FastMCP("MES-Assistant")
app = FastAPI(
    title="MCP MES 系統介面",
    description="本伺服器作為 MCP 自動化與 MES 系統的橋樑，提供人員工時與工單狀態的同步功能。",
    version="1.0.0"
)

BASE_URL = "https://mesapidemo.zeabur.app"

# === 資料模型 ===

class StaffRequest(BaseModel):
    staff_id: str = Field(..., description="員工工號，例如：'A01'", example="A01")
    station_id: str = Field(..., description="站點或機台編號，例如：'S01'", example="S01")

class JobRequest(BaseModel):
    job_id: str = Field(..., description="生產工單編號，例如：'JOB123'", example="JOB123")
    station_id: str = Field(..., description="站點編號，例如：'S01'", example="S01")

# === 核心邏輯 (共享函式) ===

async def call_mes_api(method: str, path: str, payload: dict = None):
    async with httpx.AsyncClient() as client:
        res = await client.request(
            method=method.upper(), 
            url=f"{BASE_URL}{path}", 
            json=payload if method.upper() != "GET" else None,
            params=payload if method.upper() == "GET" else None
        )
        res.raise_for_status()
        return res.json()

# 新增：參數檢查工具
def check_empty(params: dict):
    for name, value in params.items():
        if not value or str(value).strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"參數 [{name}] 不能為空值"
            )

# === API 路由定義 (保留原始註解說明) ===

@app.post("/api/staff/check-in", 
          tags=["人員管理"], 
          summary="人員上工登記",
          description="""
    ### 工具名稱：staff_checkin (人員上工登記)
**描述：** 當使用者表達「開始工作」的意圖時觸發。適用詞彙包含：上工、報到、到崗、開工、接班、開始作業、啟動計時。
此工具會將員工 ID 與工作站點繫結並開始計算工時。

**對話邏輯規範：**
1. **強制參數：** `staff_id` 與 `station_id` 均為必填。
2. **主動追問：** 若使用者僅提及「我要上班」而未提供工號或站點，AI 必須在回覆中明確詢問缺失的資訊，不可虛構參數。
3. **格式規範：** - staff_id 應為字母加數字（如: A01）。
   - station_id 可為編號（如: S01）或有名稱的站點（如: Assembly_Line）。
4. **多輪處理：** 若使用者在對話過程中才分次提供資訊，AI 需記憶前文，直到參數齊全後立即呼叫此工具。

**參數詳細說明：**
- staff_id : 員工的唯一辨識碼。
- station_id : 具體的工作位置或設備編號。
    """)
async def api_staff_check_in(data: StaffRequest):
    check_empty({"staff_id": data.staff_id, "station_id": data.station_id})
    return await staff_check_in(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_in(staff_id: str, station_id: str) -> str:
    """人員上工登記：紀錄 [員工編號] 於 [站點] 開始工作。"""
    if not staff_id or not station_id: return "錯誤：staff_id 或 station_id 不能為空"
    return str(await call_mes_api("POST", "/staff/check-in", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/staff/check-out", 
          tags=["人員管理"], 
          summary="人員下工登記",
          description="""
    ### 工具名稱：staff_checkout (人員下工登記)
**描述：** 當使用者表達結束工作意圖（如：下班、收工、完成作業、離開崗位）時觸發。
此工具具備邏輯：
1. 自動識別語義：包含所有與「停止工作」相關的口語表達。
2. 參數檢查：必須具備 `staff_id` 與 `station_id` 才能執行。
3. 缺失補全：若使用者未提供參數，須主動詢問；若只提供一個，須追問另一個。
4. 安全確認：在執行前，應簡單覆核資訊以防誤觸。

**參數定義：**
- staff_id: 員工編號。
- station_id: 站點編號。
    """)
async def api_staff_check_out(data: StaffRequest):
    check_empty({"staff_id": data.staff_id, "station_id": data.station_id})
    return await staff_check_out(data.staff_id, data.station_id)

@mcp.tool()
async def staff_check_out(staff_id: str, station_id: str) -> str:
    """人員下工登記：紀錄 [員工編號] 離開 [站點]。"""
    if not staff_id or not station_id: return "錯誤：staff_id 或 station_id 不能為空"
    return str(await call_mes_api("POST", "/staff/check-out", {"staff_id": staff_id, "station_id": station_id}))

@app.post("/api/job/entry", 
          tags=["工單管理"], 
          summary="工單進站",
          description="""
    ### 工具名稱：job_checkin (工單進站/投產)
**描述：** 當有新的生產任務、批次產品或工單抵達特定站點開始加工時觸發。
此工具用於更新 WIP 狀態，確保系統能追蹤產品的實體位置。

**對話邏輯規範：**
1. **識別意圖：** 識別如「投產」、「進站」、「開始加工某單」等語義。
2. **參數必填：** `job_id` (工單) 與 `station_id` (站點) 缺一不可。
3. **主動引導：** - 若使用者僅給出站點，需詢問：「請提供工單編號以便登記投產。」
   - 若使用者僅給出工單，需詢問：「這張單要在哪個站點/機台開始作業？」
4. **上下文關聯：** 若前一輪對話已提到某站點，在詢問工單時應預設該站點，並請使用者確認。

**參數定義：**
- job_id (string): 工單或生產任務編號。
- station_id (string): 接收該工單的機台或站點代碼。
    """)
async def api_job_entry(data: JobRequest):
    check_empty({"job_id": data.job_id, "station_id": data.station_id})
    return await job_entry(data.job_id, data.station_id)

@mcp.tool()
async def job_entry(job_id: str, station_id: str) -> str:
    """工單進站：將 [工單編號] 移入 [站點]。"""
    if not job_id or not station_id: return "錯誤：job_id 或 station_id 不能為空"
    return str(await call_mes_api("POST", "/job/entry", {"job_id": job_id, "station_id": station_id}))

@app.post("/api/job/exit", 
          tags=["工單管理"], 
          summary="工單出站",
          description="""
    ### 工具名稱：job_checkout (工單出站/完工)
**描述：** 當特定的生產工單在當前站點加工結束、準備移轉或完成生產時觸發。
此工具會標記該工單在該站點的加工程序已「關閉」。

**對話邏輯規範：**
1. **觸發識別：** 辨識「完工」、「做完了」、「出站」、「下機台」、「移交」等關鍵詞。
2. **參數防呆：** - 必須同時獲得 `job_id` 與 `station_id` 才能呼叫。
   - 若使用者只說「這站做完了」，須追問工單編號。
   - 若使用者只說「工單完成」，須追問是在哪個站點完成。
3. **流程銜接：** 執行完畢後，可主動詢問是否要進行「下一個站點的進站投產」。

**參數定義：**
- job_id : 剛完成加工的工單 or 任務編號。
- station_id : 該工單目前所在的站點編號。
    """)
async def api_job_exit(data: JobRequest):
    check_empty({"job_id": data.job_id, "station_id":