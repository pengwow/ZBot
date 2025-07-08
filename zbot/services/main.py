import click
from zbot.common.config import read_config
from zbot.exchange.exchange import ExchangeFactory


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
    click.echo(f"下载数据")
    click.echo(f"交易商: {exchange}")
    click.echo(f"交易对: {symbol}")
    click.echo(f"K线时间间隔: {interval}")
    click.echo(f"开始日期: {start}")
    click.echo(f"结束日期: {end}")
    config = read_config('exchange').get(exchange)
    exchange = ExchangeFactory.create_exchange(exchange, config)
    candles = exchange.download_data(symbol=symbol, interval=interval, start_time=start, end_time=end)
    click.echo(f"下载完成，共获取{len(candles)}天K线数据")


if __name__ == "__main__":
    cli()
