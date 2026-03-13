import os
from aiohttp import web
from apiscribe.daemon.control_api import create_app


def run():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UI_DIR = os.path.join(BASE_DIR, "..", "ui")

    app = create_app()
    app.router.add_static("/ui", UI_DIR)

    try:
        web.run_app(app, host="127.0.0.1", port=9001)

    except KeyboardInterrupt:
        print("Daemon stopped")