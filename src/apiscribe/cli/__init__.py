"""Интерфейс командной строки (CLI).

Отвечает за взаимодействие с пользователем через терминал.
"""

import typer
from dotenv import load_dotenv

from apiscribe.core.config import Config
from apiscribe.core.proxy import ProxyServer
from apiscribe.core.collector import Collector
from apiscribe.generator.openapi import OpenAPIGenerator
from apiscribe.generator.exporter import Exporter

load_dotenv()

app = typer.Typer()


@app.command()
def start(
    target_url: str = typer.Option(..., "--target-url", "-t", help="Target API URL"),
    output: str = typer.Option("openapi.json", "--output", "-o", help="Output file"),
):
    """
    Запуск прокси-сервера и автоматический экспорт спецификации при остановке.
    """

    config = Config(target_url=target_url)
    collector = Collector()
    proxy = ProxyServer(config=config, collector=collector)

    try:
        proxy.run()
    except KeyboardInterrupt:
        typer.echo("\nStopping proxy and generating OpenAPI...")

        generator = OpenAPIGenerator()
        spec = generator.generate(collector.get_endpoints())

        exporter = Exporter()
        exporter.to_json(spec, output)

        typer.echo(f"Specification saved to {output}")
