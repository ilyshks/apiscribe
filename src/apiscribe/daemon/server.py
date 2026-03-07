from aiohttp import web
from apiscribe.daemon.control_api import create_app


def run():

    app = create_app()

    try:
        web.run_app(app, host="127.0.0.1", port=9001)

    except KeyboardInterrupt:
        print("Daemon stopped")