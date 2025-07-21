from tkinter import N
import click
from zbot.common.config import read_config, write_config
from zbot.exchange.exchange import ExchangeFactory
from zbot.services.backtest import Backtest
from zbot.ui.web.app import run_web_ui
from zbot.utils.dateutils import parse_date_range
import yaml
from pathlib import Path
import os


@click.group()
def cli():
    pass


@cli.command()
@click.option('--exchange', default='binance', help='交易商名')
@click.option('--symbol', default='BTCUSDT', help='交易对 例如 BTCUSDT')
@click.option('--interval', default='15m', help='K线时间间隔 例如 15m, 30m, 1h, 4h, 1d, 1m, 5m')
@click.option('--start', default='2025-01-01', help='开始日期 %Y-%m-%d 例如 2025-01-01')
@click.option('--end', default='2025-01-31', help='结束日期 %Y-%m-%d 例如 2025-01-31')
def download_data(exchange, symbol, interval, start, end):
    """下载K线数据"""
    click.echo(f"下载数据")
    click.echo(f"交易商: {exchange}")
    click.echo(f"交易对: {symbol}")
    click.echo(f"K线时间间隔: {interval}")
    click.echo(f"开始日期: {start}")
    click.echo(f"结束日期: {end}")
    config = read_config('exchange').get(exchange)
    exchange = ExchangeFactory.create_exchange(exchange, config)
    candles = exchange.download_data(
        symbol=symbol, interval=interval, start_time=start, end_time=end)
    click.echo(f"下载完成，共获取{len(candles)}天K线数据")


@cli.command()
@click.option('--exchange', default='binance', help='交易商名')
@click.option('--api_key', default='', help='api key')
@click.option('--secret_key', default='', help='secret key')
@click.option('--proxy_url', default='', help='代理url')
@click.option('--trading_mode', default='spot', help='交易模式: spot现货, futures合约')
def config(exchange, api_key, secret_key, proxy_url, trading_mode):
    """
    创建或修改交易所配置信息

    先从配置文件读取现有配置，更新或添加指定交易所的配置参数，然后写回文件。

    参数:
        exchange (str): 交易所名称
        api_key (str): API密钥
        secret_key (str): 密钥
        proxy_url (str): 代理URL
        trading_mode (str): 交易模式
    """
    click.echo(f"配置交易商: {exchange}")
    click.echo(f"api key: {api_key}")
    click.echo(f"secret key: {secret_key}")
    click.echo(f"代理url: {proxy_url}")
    click.echo(f"交易模式: {trading_mode}")
    # 配置文件路径
    config_path = None
    # config_path = Path(os.path.dirname(os.path.abspath(__file__))).parent / 'config2.yaml'

    # 读取现有配置
    existing_config = read_config(file_path=config_path)

    # 确保exchange配置部分存在并更新
    exchange_config = existing_config.get('exchange', {})
    exchange_config['name'] = exchange  # 更新当前选中的交易所名称

    # 获取当前交易所的配置，不存在则创建新字典
    current_exchange_config = exchange_config.get(exchange, {})
    current_exchange_config.update({
        'api_key': api_key,
        'secret_key': secret_key,
        'proxy_url': proxy_url,
        'trading_mode': trading_mode
    })
    exchange_config[exchange] = current_exchange_config
    existing_config['exchange'] = exchange_config
    # 将更新后的配置数据写入 yaml 文件
    write_config(existing_config, file_path=config_path)


@cli.command()
@click.option('--strategy', help='策略名')
@click.option('--symbol', help='交易对')
@click.option('--interval', default='15m', help='K线时间间隔 例如 15m, 30m, 1h, 4h, 1d, 1m, 5m')
@click.option('--cash', default=1000, help='初始资金')
@click.option('--timerange', help='时间范围')
@click.option('--commission', default=0.0, help='手续费')
def backtesting(strategy, symbol, interval, cash, timerange, commission):
    """回测"""
    start, end = parse_date_range(timerange)
    backtest = Backtest(strategy, symbol, interval, start, end, cash, commission)
    stats = backtest.run()
    print(stats)



@cli.command()
@click.option('--host', default='0.0.0.0', help='主机名')
@click.option('--port', default=8080, help='端口号')
def start_web_ui(host, port):
    """启动Web UI"""
    run_web_ui(host, port)


if __name__ == "__main__":
    cli()
