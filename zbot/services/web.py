import click
from zbot.ui.web.app import run_web_ui
from zbot.common.config import read_config

# 1. 创建命令组
@click.group()
def cli():
    pass


@cli.command()
def run():
    click.echo(f"运行服务")
    host = read_config('server').get('server_host', '0.0.0.0')
    port = read_config('server').get('server_port', 8000)
    run_web_ui(host, port)


if __name__ == "__main__":
    cli()
