import click

# 1. 创建命令组
@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", default="World", help="The name to say hello to.")
def run(name):
    click.echo(f"Hello, {name}!")

@cli.command()
def run2():
    click.echo("Hello, World!")

if __name__ == "__main__":
    cli()