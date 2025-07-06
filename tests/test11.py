import websocket
import json
# import websockets.client

def on_message(ws, message):
    print(f"收到响应: {message}")  # 处理服务器返回的数据[1,4](@ref)

def on_error(ws, error):
    print(f"连接错误: {error}")

def on_close(ws, status_code, close_msg):
    print("连接关闭")

def on_open(ws):
    # 发送测试数据（JSON格式）
    test_data = {"action": "ping", "payload": "Hello WebSocket!"}
    ws.send(json.dumps(test_data))  # 序列化后发送[4](@ref)

if __name__ == "__main__":
    url = "ws://localhost:8000/ws"  # 替换为你的WebSocket地址
    websocket.enableTrace(True)  # 开启详细日志（调试用）
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open  # 连接成功后自动触发发送[1](@ref)
    ws.run_forever(ping_interval=30)  # 每30秒发送心跳保活[5](@ref)