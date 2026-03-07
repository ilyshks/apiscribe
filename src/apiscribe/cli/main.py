import typer
import requests
import json

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

    with open(file, "w") as f:
        json.dump(spec, f, indent=2)

    typer.echo(f"Saved to {file}")


@app.command()
def status():

    r = requests.get(f"{CONTROL_URL}/status")

    typer.echo(r.json())