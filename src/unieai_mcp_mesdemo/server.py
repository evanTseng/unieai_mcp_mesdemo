import httpx
import uvicorn
from fastmcp import FastMCP

# 初始化 MCP Server
mcp = FastMCP("MES-Assistant")

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

#def main():
#    # 針對 Zeabur 部署，建議使用 SSE 模式
#    # 可以透過環境變數動態調整 port
#    import os
#    port = int(os.getenv("PORT", 9090))
#    mcp.run(mode="sse", port=port)

#if __name__ == "__main__":
#    main()



def main():  
    """MCP 伺服器入口點"""  
    mcp.run(transport="sse")
if __name__ == "__main__":  
    main()  