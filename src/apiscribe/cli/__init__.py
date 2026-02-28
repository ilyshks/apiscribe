"""Интерфейс командной строки (CLI).

Отвечает за взаимодействие с пользователем через терминал.
"""

import typer
from apiscribe.core.proxy import ProxyServer
from apiscribe.generator.openapi import OpenAPIGenerator
from apiscribe.generator.exporter import Exporter

app = typer.Typer()
proxy_instance = None


@app.command()
def start(target: str, port: int = 8000):
    global proxy_instance
    proxy_instance = ProxyServer(target)
    proxy_instance.run(port)


@app.command()
def export(output: str = "openapi.json"):
    generator = OpenAPIGenerator()
    exporter = Exporter()

    endpoints = proxy_instance.collector.get_endpoints()
    spec = generator.generate(endpoints)

    exporter.to_json(spec, output)


if __name__ == "__main__":
    app()
