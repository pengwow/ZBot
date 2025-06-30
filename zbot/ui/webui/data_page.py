import streamlit as st
import pandas as pd
import time
# from data import DownloadData
from multiprocessing import Manager, Queue
# from zbot.common.config import read_config
# from zbot.exchange.exchange import ExchangeFactory
from threading import Thread

data_config = {}
class WorkerThread(Thread):
    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol
        self.return_value = None

    def run(self):
        start_time = time.time()
        my_bar = st.progress(0, text=self.symbol)
        for percent_complete in range(100):
            time.sleep(0.02)
            my_bar.progress(percent_complete + 1, text=self.symbol)
        end_time = time.time()
        my_bar.empty()
        # self.return_value = f"start: {start_time}, end: {end_time} {self.delay}"

def download_data():
    # 使用工厂类动态创建交易所实例
    # exchange = ExchangeFactory.create_exchange(data_config['exchange'], config)

    # async def download_data_task(symbol):
        # print(data_config)
        # queue = Manager().Queue()
        # # 调用下载数据方法
        # if exchange:
        #     print(f"成功加载{exchange.exchange_name}交易所模块")
        #     # 在独立进程中运行下载任务以避免事件循环冲突
        #     exchange.download_data(
        #         symbol=symbol,
        #         interval=data_config['interval'],
        #         start_time=data_config['start_time'],
        #         end_time=data_config['end_time'],
        #         trading_mode=data_config['trading_mode'],
        #         progress_queue=queue
        #     )
        #     msg = f"下载完成，共获取{len(candles)}条K线数据"
        # else:
        #     msg = "交易所模块加载失败"

    # download_bar = st.progress(0)
    with st.status("Downloading data..."):
        for symbol in data_config['symbol']:
            st.write(f"Searching for {symbol} data...")
            time.sleep(2)
            st.write("Found URL.")
            time.sleep(1)
            st.write("Downloading data...")
            progress_text = f'Downloading {symbol} data...'
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
            time.sleep(1)
    #     progress_text = f"下载 {symbol} {data_config['interval']} 数据, 请等待"
    #     my_bar = st.progress(0, text=progress_text)
    #     threads = [WorkerThread(delay) for delay in delays]
    # for thread in threads:
    #     thread.start()
    # for thread in threads:
    #     thread.join()
    # for i, thread in enumerate(threads):
    #     st.header(f"Thread {i}")
    #     st.write(thread.return_value)

    #     for percent_complete in range(100):
    #         time.sleep(0.01)
    #         my_bar.progress(percent_complete + 1, text=progress_text)
    #     time.sleep(1)
    #     my_bar.empty()

    print(data_config)


data_config['exchange'] = st.selectbox('交易商', ['binance', 'okx'])
data_config['trading_mode'] = st.selectbox('交易模式', ['spot', 'futures'])
data_config['symbol'] = st.multiselect(
    "交易对",
    ['BTC/USDT', 'ETH/USDT', 'EOS/USDT'],
    placeholder='选择货币对',
)
data_config['interval'] = st.selectbox(
    '时间周期', ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1s'], index=3)
data_config['start_time'] = st.date_input('开始时间', value='2025-01-01')
data_config['end_time'] = st.date_input('结束时间', value='2025-01-02')


st.button('获取数据', on_click=download_data, use_container_width=True)
