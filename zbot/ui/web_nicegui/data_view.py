# coding=utf-8
import time
from nicegui import ui, run
from multiprocessing import Manager, Queue
from data import DownloadData
from zbot.common.config import read_config
from zbot.exchange.exchange import ExchangeFactory

config = read_config('BINANCE')


def heavy_computation(q: Queue) -> str:
    """Run some heavy computation that updates the progress bar through the queue."""
    n = 50
    for i in range(n):
        # Perform some heavy computation
        time.sleep(0.1)

        # Update the progress bar through the queue
        q.put_nowait(i / n)
    return 'Done!'


def download_data_view(download_data_config: DownloadData):
    async def download_data():
        print(download_data_config)
        progressbar.visible = True
        # 使用工厂类动态创建交易所实例
        exchange = ExchangeFactory.create_exchange(
            download_data_config.exchange, config)
        
        # 调用下载数据方法
        if exchange:
            print(f"成功加载{exchange.exchange_name}交易所模块")
            # 在独立进程中运行下载任务以避免事件循环冲突
            candles = await run.cpu_bound(
                exchange.download_data,
                symbol=download_data_config.symbol,
                interval=download_data_config.interval,
                start_time=download_data_config.start_time,
                end_time=download_data_config.end_time,
                trading_mode=download_data_config.trading_mode,
                progress_queue=queue
            )
            msg = f"下载完成，共获取{len(candles)}条K线数据"
        else:
            msg = "交易所模块加载失败"
        ui.notify(msg)
        print(msg)
        # result = await run.cpu_bound(heavy_computation, queue)
        
        progressbar.visible = False

    exchange = ['binance', 'okx']
    symbol = ['BTC/USDT', 'ETH/USDT', 'DOGE/USDC']
    with ui.row():
        ui.select(exchange, multiple=False,
                  value=exchange[0], label='交易所').classes('w-64').bind_value(download_data_config, 'exchange')
        ui.select(symbol, multiple=False, with_input=True,
                  value=symbol[0], label='货币对').bind_value(download_data_config, 'symbol').classes('w-64').props('use-chips')
        ui.select(['1m', '3m', '5m', '15m', '30m', '1h', '4h',
                   '1d', '1s'], value='15m', label='时间间隔').bind_value(download_data_config, 'interval').classes('w-64')

    with ui.row():
        ui.select({'spot': 'spot现货', 'futures': 'futures合约'}, value='spot', label='交易模式').bind_value(download_data_config, 'trading_mode').classes('w-64')
        with ui.input('开始时间').bind_value(download_data_config, 'start_time') as date:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date().bind_value(date):
                    with ui.row().classes('justify-end'):
                        ui.button('确定', on_click=menu.close).props('flat')
            with date.add_slot('append'):
                ui.icon('edit_calendar').on(
                    'click', menu.open).classes('cursor-pointer')
        with ui.input('结束时间').bind_value(download_data_config, 'end_time') as date:
            with ui.menu().props('no-parent-event') as menu:
                with ui.date().bind_value(date):
                    with ui.row().classes('justify-end'):
                        ui.button('确定', on_click=menu.close).props('flat')
            with date.add_slot('append'):
                ui.icon('edit_calendar').on(
                    'click', menu.open).classes('cursor-pointer')
    ui.button('下载数据', on_click=download_data)
    # Create a queue to communicate with the heavy computation process
    queue = Manager().Queue()
    # Update the progress bar on the main process
    ui.timer(0.1, callback=lambda: progressbar.set_value(
        queue.get() if not queue.empty() else progressbar.value))

    # Create the UI
    # ui.button('compute', on_click=start_computation)
    progressbar = ui.linear_progress(value=0, show_value=False).props('instant-feedback')
    progressbar.visible = False
