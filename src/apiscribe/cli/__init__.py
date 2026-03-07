"""Интерфейс командной строки (CLI).

Отвечает за взаимодействие с пользователем через терминал.
"""

import typer
import threading
from dotenv import load_dotenv

from apiscribe.core.config import Config
from apiscribe.core.proxy import ProxyServer
from apiscribe.core.collector import Collector
from apiscribe.generator.openapi import OpenAPIGenerator
from apiscribe.generator.exporter import Exporter

from apiscribe.storage.session import session

load_dotenv()

app = typer.Typer()


@app.command()
def start(
    target_url: str = typer.Option(..., "--target-url", "-t"),
):

    if session.running:
        typer.echo("Proxy already running")
        return

    config = Config(target_url=target_url)

    session.collector = Collector()
    session.proxy = ProxyServer(config=config, collector=session.collector)

    def run_proxy():
        session.proxy.run()

    session.thread = threading.Thread(target=run_proxy, daemon=True)
    session.thread.start()

    session.running = True

    typer.echo(f"Proxy started on {config.host}:{config.port}")


@app.command()
def openapi(
    file: str = typer.Argument("openapi.json")
):

    if not session.running:
        typer.echo("Proxy not running")
        return

    generator = OpenAPIGenerator()
    spec = generator.generate(session.collector.get_endpoints())

    exporter = Exporter()
    exporter.to_json(spec, file)

    typer.echo(f"Specification saved to {file}")


@app.command()
def stop(
    output: str = typer.Option("openapi.json")
):

    if not session.running:
        typer.echo("Proxy not running")
        return

    generator = OpenAPIGenerator()
    spec = generator.generate(session.collector.get_endpoints())

    exporter = Exporter()
    exporter.to_json(spec, output)

    typer.echo(f"Specification saved to {output}")

    session.running = False

    typer.echo("Proxy stopped")