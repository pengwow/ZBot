import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from zbot.common.config import read_config
from typing import Optional, Dict, List
import uuid
import threading
from multiprocessing import Manager, Queue
from zbot.utils.dateutils import str_to_timestamp
from zbot.exchange.exchange import ExchangeFactory
from zbot.models.log import Log, LogType
import time

app = Flask(__name__)


app.config['SECRET_KEY'] = 'zbot-secret-key'
CORS(app, resources={"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# 创建命名空间
# 定义请求模型
# 存储下载任务进度，键为任务ID，值为进度(0-1)或-1表示错误
download_tasks: Dict[str, float] = {}
task_lock = threading.Lock()  # 线程锁确保进度更新安全

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, str] = {}  # task_id: sid

    def connect(self, sid: str, task_id: str):
        self.active_connections[task_id] = sid

    def disconnect(self, sid: str):
        # 查找并删除对应的任务ID
        to_remove = None
        for task_id, connection_sid in self.active_connections.items():
            if connection_sid == sid:
                to_remove = task_id
                break
        if to_remove:
            del self.active_connections[to_remove]

    def get_socket_id(self, task_id: str) -> Optional[str]:
        return self.active_connections.get(task_id)

manager = ConnectionManager()


@app.route('/download-history-data', methods=['POST'])
def download_history_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    required_fields = ["exchange", "symbol", "interval", "start_date", "end_date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # 生成唯一任务ID
    task_id = str(uuid.uuid4().hex)

    # 初始化任务进度为0
    with task_lock:
        download_tasks[task_id] = 0.0

    # 创建下载请求对象
    download_request = {
        "exchange": data["exchange"],
        "symbol": data["symbol"],
        "interval": data["interval"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "candle_type": data.get("candle_type", "spot")
    }

    # 在后台线程中执行下载任务
    thread = threading.Thread(target=download_task, args=(download_request, task_id))
    thread.daemon = True
    thread.start()

    # 立即返回任务ID
    return jsonify({
        "task_id": task_id,
        "status": "started",
        "message": "Download task has been started in background"
    })

def download_task(request: dict, task_id: str):
    """后台执行下载任务并更新进度"""
    try:
        # 更新进度：初始化(10%)
        with task_lock:
            download_tasks[task_id] = 0.1
        socket_id = manager.get_socket_id(task_id)
        if socket_id:
            socketio.emit('progress', {
                "task_id": task_id,
                "progress": 0.1,
                "message": "Initializing download task",
                "status": "progress"
            }, room=socket_id)

        # 更新进度：日期转换完成(20%)
        with task_lock:
            download_tasks[task_id] = 0.2
        if socket_id:
            socketio.emit('progress', {
                "task_id": task_id,
                "progress": 0.2,
                "message": "Date conversion completed",
                "status": "progress"
            }, room=socket_id)

        # 初始化历史数据下载器
        exchange = ExchangeFactory.create_exchange(request["exchange"])

        # 更新进度：下载器初始化完成(30%)
        with task_lock:
            download_tasks[task_id] = 0.3
        if socket_id:
            socketio.emit('progress', {
                "task_id": task_id,
                "progress": 0.3,
                "message": "Downloader initialized",
                "status": "progress"
            }, room=socket_id)

        queue = Manager().Queue()

        # 执行下载
        def download_sync():
            return exchange.download_data(
                symbol=request["symbol"],
                interval=request["interval"],
                start_time=request["start_date"],
                end_time=request["end_date"],
                candle_type=request["candle_type"],
                progress_queue=queue
            )

        download_thread = threading.Thread(target=download_sync)
        download_thread.start()

        # 循环检查任务状态并处理进度日志
        while download_thread.is_alive():
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
            time.sleep(1)  # 短暂等待后再次检查

        # 更新进度：下载完成(100%)
        with task_lock:
            download_tasks[task_id] = 1.0
        if socket_id:
            socketio.emit('progress', {
                "task_id": task_id,
                "progress": 1.0,
                "message": "Download completed successfully",
                "status": "completed"
            }, room=socket_id)

    except Exception as e:
        # 发生错误时标记进度为-1
        with task_lock:
            download_tasks[task_id] = -1.0
        if socket_id:
            socketio.emit('progress', {
                "task_id": task_id,
                "progress": -1,
                "message": f"Download failed: {str(e)}",
                "status": "error"
            }, room=socket_id)
        print(f"Download task {task_id} failed: {str(e)}")

@app.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id not in download_tasks:
        return jsonify({"error": "Task not found"}), 404

    progress = download_tasks[task_id]
    status = "completed" if progress == 1.0 else "error" if progress == -1 else "in_progress"
    return jsonify({
        "task_id": task_id,
        "progress": progress,
        "status": status
    })

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    manager.disconnect(request.sid)
    print('Client disconnected')

@socketio.on('download-history')
def handle_download_history(data):
    """
    WebSocket处理函数用于实时下载历史数据并推送进度
    客户端需要发送包含下载参数的JSON消息
    """
    # 验证必要参数
    required_fields = ["exchange", "symbol", "interval", "start_date", "end_date"]
    if not all(field in data for field in required_fields):
        emit('error', {
            "status": "error",
            "message": "Missing required fields. Required: symbol, interval, start_date, end_date"
        })
        return

    # 生成任务ID
    task_id = str(uuid.uuid4())
    manager.connect(request.sid, task_id)

    # 发送任务开始消息
    emit('task_started', {
        "task_id": task_id,
        "status": "started",
        "message": "Download task has been started"
    })

    # 创建下载请求对象
    download_request = {
        "exchange": data["exchange"],
        "symbol": data["symbol"],
        "interval": data["interval"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "candle_type": data.get("candle_type", "spot")
    }

    # 在后台线程中执行下载任务
    thread = threading.Thread(target=download_task, args=(download_request, task_id))
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)