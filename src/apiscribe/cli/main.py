import typer
import requests
import json
from pathlib import Path

app = typer.Typer()

CONTROL_URL = "http://127.0.0.1:9001"


@app.command()
def start(target_url: str):

    r = requests.post(
        f"{CONTROL_URL}/start",
        json={"target_url": target_url}
    )

    typer.echo(r.json())


@app.command()
def stop():

    r = requests.post(f"{CONTROL_URL}/stop")

    typer.echo(r.json())


@app.command()
def openapi(file: str = "openapi.json"):

    r = requests.get(f"{CONTROL_URL}/openapi")

    spec = r.json()

    # путь к папке generated_docs внутри пакета apiscribe
    base_dir = Path(__file__).resolve().parent.parent
    docs_dir = base_dir / "generated_docs"

    docs_dir.mkdir(exist_ok=True)

    output_path = docs_dir / file

    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)

    typer.echo(f"Saved to {output_path}")


@app.command()
def status():

    r = requests.get(f"{CONTROL_URL}/status")

    typer.echo(r.json())