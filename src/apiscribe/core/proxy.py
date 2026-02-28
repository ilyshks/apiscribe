import typer
from dotenv import load_dotenv

from apiscribe.core.config import Config
from apiscribe.core.proxy import ProxyServer
from apiscribe.generator.openapi import OpenAPIGenerator
from apiscribe.generator.exporter import Exporter

load_dotenv()

app = typer.Typer()
proxy_instance = None


@app.command()
def start():
    global proxy_instance

    config = Config()  # читаем из env
    proxy_instance = ProxyServer(config)

    proxy_instance.run()


@app.command()
def export(output: str = "openapi.json"):
    generator = OpenAPIGenerator()
    exporter = Exporter()

    endpoints = proxy_instance.collector.get_endpoints()
    spec = generator.generate(endpoints)

    exporter.to_json(spec, output)


if __name__ == "__main__":
    app()