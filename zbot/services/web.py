
import uvicorn
import click
from zbot.services.apis import api_app
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
    uvicorn.run(api_app, host=host, port=int(port), log_level="info")


if __name__ == "__main__":
    cli()
