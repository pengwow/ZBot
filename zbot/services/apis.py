from fastapi import FastAPI, BackgroundTasks, Request, Response, HTTPException, Path, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from zbot.common.config import read_config
from typing import Optional, Dict, List
import uuid
import asyncio
from threading import Lock
from fastapi.background import BackgroundTasks
from multiprocessing import Manager, Queue
from zbot.utils.dateutils import str_to_timestamp
from zbot.exchange.exchange import ExchangeFactory
from zbot.models.log import Log, LogType

api_app = FastAPI()

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 存储下载任务进度，键为任务ID，值为进度(0-1)或-1表示错误
download_tasks: Dict[str, float] = {}
task_lock = Lock()  # 线程锁确保进度更新安全

# exchange_name = read_config('exchange').get('name')

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.task_connections: Dict[str, WebSocket] = {}  # 任务ID到WebSocket的映射

    async def connect(self, websocket: WebSocket, task_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if task_id:
            self.task_connections[task_id] = websocket

    def disconnect(self, websocket: WebSocket, task_id: str = None):
        self.active_connections.remove(websocket)
        if task_id and task_id in self.task_connections:
            del self.task_connections[task_id]

    async def send_progress(self, task_id: str, progress: float, message: str = ""):
        if task_id in self.task_connections:
            websocket = self.task_connections[task_id]
            await websocket.send_json({
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "status": "progress" if progress < 1 else "completed" if progress == 1 else "error"
            })


manager = ConnectionManager()


class DownloadHistoryRequest(BaseModel):
    exchange: str
    symbol: str
    interval: str
    start_date: str
    end_date: str
    candle_type: Optional[str] = "spot"


@api_app.post("/download-history-data")
async def download_history_data(request: DownloadHistoryRequest, background_tasks: BackgroundTasks):
    # 生成唯一任务ID
    task_id = str(uuid.uuid4().hex)

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
    """后台执行下载任务并更新进度（HTTP接口使用）"""
    try:
        # 更新进度：初始化(10%)
        with task_lock:
            download_tasks[task_id] = 0.1

        # 更新进度：日期转换完成(20%)
        with task_lock:
            download_tasks[task_id] = 0.2
        # 初始化历史数据下载器
        exchange = ExchangeFactory.create_exchange(request.exchange)
        # 更新进度：下载器初始化完成(30%)
        with task_lock:
            download_tasks[task_id] = 0.3
        queue = Manager().Queue()
        # 在单独线程中执行同步下载函数，避免阻塞事件循环
        # 启动下载任务，不等待完成
        download_future = asyncio.create_task(asyncio.to_thread(
            exchange.download_data,
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_date,
            end_time=request.end_date,
            candle_type=request.candle_type,
            progress_queue=queue
        ))
        
        # 循环检查任务状态并处理进度日志
        while not download_future.done():
            # 从进度队列获取更新信息
            while not queue.empty():
                progress_msg = queue.get()
                # 查找或创建日志记录并更新
                log_entry, created = Log.get_or_create(
                    task_id=task_id,
                    defaults={
                        'type': LogType.DATA,
                        'message': progress_msg,
                        'status': 'processing'
                    }
                )
                if not created:
                    log_entry.message = progress_msg
                    log_entry.status = 'processing'
                    log_entry.save()
            await asyncio.sleep(1)  # 短暂等待后再次检查
            
        # 获取下载结果并处理
        try:
            df = download_future.result()
            # 下载成功日志
            # 更新或创建成功日志
            log_entry, created = Log.get_or_create(
                task_id=task_id,
                defaults={
                    'type': LogType.DATA,
                    'message': f"Successfully downloaded {len(df)} records for {request.symbol}",
                    'status': 'success'
                }
            )
            if not created:
                log_entry.message = f"Successfully downloaded {len(df)} records for {request.symbol}"
                log_entry.status = 'success'
                log_entry.save()
        except Exception as e:
            # 下载失败日志
            # 更新或创建失败日志
            log_entry, created = Log.get_or_create(
                task_id=task_id,
                defaults={
                    'type': LogType.DATA,
                    'message': f"Download failed: {str(e)}",
                    'status': 'error'
                }
            )
            if not created:
                log_entry.message = f"Download failed: {str(e)}"
                log_entry.status = 'error'
                log_entry.save()
            raise
        # 更新进度：下载完成(100%)
        with task_lock:
            download_tasks[task_id] = 1.0

    except Exception as e:
        # 发生错误时标记进度为-1
        with task_lock:
            download_tasks[task_id] = -1.0
        print(f"Download task {task_id} failed: {str(e)}")


async def download_task_websocket(request: DownloadHistoryRequest, task_id: str, manager: ConnectionManager):
    """通过WebSocket发送进度的下载任务"""
    try:
        # 发送初始化进度(10%)
        asyncio.run_coroutine_threadsafe(
            manager.send_progress(task_id, 0.1, "Initializing download task"),
            asyncio.get_event_loop()
        )

        # 转换日期字符串为时间戳
        start_ts = str_to_timestamp(request.start_date)
        end_ts = str_to_timestamp(request.end_date)

        # 发送进度更新(20%)
        asyncio.run_coroutine_threadsafe(
            manager.send_progress(task_id, 0.2, "Date conversion completed"),
            asyncio.get_event_loop()
        )

        # 初始化历史数据下载器
        history = History()

        # 发送进度更新(30%)
        asyncio.run_coroutine_threadsafe(
            manager.send_progress(task_id, 0.3, "Downloader initialized"),
            asyncio.get_event_loop()
        )

        # 执行下载
        df = history.load_and_clean_data(
            symbol=request.symbol,
            interval=request.interval,
            start_ts=start_ts,
            end_ts=end_ts,
            candle_type=request.candle_type
        )

        # 发送完成进度(100%)
        asyncio.run_coroutine_threadsafe(
            manager.send_progress(
                task_id, 1.0, "Download completed successfully"),
            asyncio.get_event_loop()
        )

    except Exception as e:
        # 发送错误状态
        asyncio.run_coroutine_threadsafe(
            manager.send_progress(task_id, -1, f"Download failed: {str(e)}"),
            asyncio.get_event_loop()
        )
        print(f"Download task {task_id} failed: {str(e)}")
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


@api_app.get("/download-progress/{task_id}")
async def get_download_progress(task_id: str):
    """获取下载任务进度"""
    with task_lock:
        progress = download_tasks.get(task_id, None)

    if progress is None:
        raise HTTPException(status_code=404, detail="Task not found")

    status = "in_progress"
    message = "Download in progress"

    if progress == -1:
        status = "error"
        message = "Download failed"
    elif progress == 1:
        status = "completed"
        message = "Download completed successfully"

    return {
        "task_id": task_id,
        "progress": progress,
        "status": status,
        "message": message
    }


@api_app.websocket("/ws/download-history")
async def websocket_download_history(websocket: WebSocket):
    """
    WebSocket端点用于实时下载历史数据并推送进度
    客户端需要发送包含下载参数的JSON消息：
    {
        "symbol": "BTC/USDT",
        "interval": "15m",
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
        "candle_type": "spot"  # 可选，默认为"spot"
    }
    """
    await manager.connect(websocket)
    task_id = None
    try:
        while True:
            # 接收客户端发送的下载参数
            data = await websocket.receive_json()

            # 验证必要参数
            required_fields = ["symbol", "interval", "start_date", "end_date"]
            if not all(field in data for field in required_fields):
                await websocket.send_json({
                    "status": "error",
                    "message": "Missing required fields. Required: symbol, interval, start_date, end_date"
                })
                continue

            # 生成任务ID
            task_id = str(uuid.uuid4())
            await manager.connect(websocket, task_id)  # 将任务ID与WebSocket关联

            # 发送任务开始消息
            await websocket.send_json({
                "task_id": task_id,
                "status": "started",
                "message": "Download task has been started"
            })

            # 创建下载请求对象
            request = DownloadHistoryRequest(
                symbol=data["symbol"],
                interval=data["interval"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                candle_type=data.get("candle_type", "spot")
            )

            # 在后台线程中执行下载任务
            loop = asyncio.get_event_loop()
            loop.run_in_executor(
                None, download_task_websocket, request, task_id, manager)

    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        if task_id:
            # 使用run_coroutine_threadsafe在同步上下文中调用异步方法
            asyncio.run_coroutine_threadsafe(
                manager.send_progress(task_id, -1, f"Error: {str(e)}"),
                asyncio.get_event_loop()
            )
        manager.disconnect(websocket, task_id)


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


# @api_app.get("/")
# def root():
#     return {"message": "ZBot Data Service API is running. Use /download-history-data endpoint to start download and /download-progress/ to check status."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api_app, host="0.0.0.0", port=8000)