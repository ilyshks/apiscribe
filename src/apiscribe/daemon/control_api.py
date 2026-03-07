from aiohttp import web

from apiscribe.daemon.daemon import daemon
from apiscribe.generator.openapi import OpenAPIGenerator


async def start(request):

    data = await request.json()

    target_url = data["target_url"]

    result = await daemon.start_proxy(target_url)

    return web.json_response(result)


async def stop(request):

    result = await daemon.stop_proxy()

    return web.json_response(result)


async def openapi(request):

    generator = OpenAPIGenerator()

    spec = generator.generate(
        daemon.get_collector().get_endpoints()
    )

    return web.json_response(spec)


async def status(request):

    return web.json_response({
        "running": daemon.proxy is not None
    })


def create_app():

    app = web.Application()

    app.router.add_post("/start", start)
    app.router.add_post("/stop", stop)
    app.router.add_get("/openapi", openapi)
    app.router.add_get("/status", status)

    return app