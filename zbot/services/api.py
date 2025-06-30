from fastapi import FastAPI, HTTPException, BackgroundTasks, Path
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
import asyncio
from threading import Lock
from zbot.exchange.binance.data import History
from zbot.utils.dateutils import str_to_timestamp

app = FastAPI(title="ZBot Data Service API")

# 存储下载任务进度，键为任务ID，值为进度(0-1)或-1表示错误
download_tasks: Dict[str, float] = {}
task_lock = Lock()  # 线程锁确保进度更新安全

class DownloadHistoryRequest(BaseModel):
    symbol: str
    interval: str
    start_date: str
    end_date: str
    candle_type: Optional[str] = "spot"

@app.post("/download-history-data")
async def download_history_data(request: DownloadHistoryRequest, background_tasks: BackgroundTasks):
    # 生成唯一任务ID
    task_id = str(uuid.uuid4())
    
    # 初始化任务进度为0
    with task_lock:
        download_tasks[task_id] = 0.0
    
    # 添加后台任务
    background_tasks.add_task(download_task, request, task_id)
    
    # 立即返回任务ID
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Download task has been started in background"
    }

async def download_task(request: DownloadHistoryRequest, task_id: str):
    """后台执行下载任务并更新进度"""
    try:
        # 更新进度：初始化(10%)
        with task_lock:
            download_tasks[task_id] = 0.1
            
        # 转换日期字符串为时间戳
        start_ts = str_to_timestamp(request.start_date)
        end_ts = str_to_timestamp(request.end_date)
        
        # 更新进度：日期转换完成(20%)
        with task_lock:
            download_tasks[task_id] = 0.2
            
        # 初始化历史数据下载器
        history = History()
        
        # 更新进度：下载器初始化完成(30%)
        with task_lock:
            download_tasks[task_id] = 0.3
            
        # 在单独线程中执行同步下载函数，避免阻塞事件循环
        df = await asyncio.to_thread(
            history.load_and_clean_data,
            symbol=request.symbol,
            interval=request.interval,
            start_ts=start_ts,
            end_ts=end_ts,
            candle_type=request.candle_type
        )
        
        # 更新进度：下载完成(100%)
        with task_lock:
            download_tasks[task_id] = 1.0
            
    except Exception as e:
        # 发生错误时标记进度为-1
        with task_lock:
            download_tasks[task_id] = -1.0
        print(f"Download task {task_id} failed: {str(e)}")

@app.get("/download-progress/{task_id}")
async def get_download_progress(task_id: str = Path(..., description="The ID of the download task")):
    """查询下载任务进度"""
    with task_lock:
        progress = download_tasks.get(task_id)
    
    if progress is None:
        raise HTTPException(status_code=404, detail="Task ID not found")
    
    if progress == -1.0:
        return {
            "task_id": task_id,
            "progress": None,
            "status": "failed",
            "message": "Download task failed"
        }
    elif progress >= 1.0:
        return {
            "task_id": task_id,
            "progress": 1.0,
            "status": "completed",
            "message": "Download completed successfully"
        }
    else:
        return {
            "task_id": task_id,
            "progress": progress,
            "status": "downloading",
            "message": f"Download in progress: {progress*100:.1f}%"
        }

@app.get("/")
async def root():
    return {"message": "ZBot Data Service API is running. Use /download-history-data endpoint to start download and /download-progress/{task_id} to check status."}