from nicegui import binding, ui




@binding.bindable_dataclass
class Database:
    number: int = 1


@binding.bindable_dataclass
class DownloadData(object):
    exchange: str = 'binance'
    trading_mode: str = 'spot'
    symbol: str = 'BTC/USDT'
    interval: str = '15m'
    start_time: str = ''
    end_time: str = ''