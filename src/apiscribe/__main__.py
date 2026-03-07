"""Точка входа для запуска пакета командой `python -m apiscribe <cmd_name>`.

Позволяет запускать пакет как исполняемый скрипт.
"""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "daemon":

    from apiscribe.daemon.server import run
    run()

else:

    from apiscribe.cli.main import app
    app()