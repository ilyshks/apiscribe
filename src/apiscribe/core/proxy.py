import aiohttp
from aiohttp import web
import json

from apiscribe.core.analyzer import Analyzer
from apiscribe.core.collector import Collector


class ProxyServer:
    def __init__(self, target_host: str):
        self.target_host = target_host
        self.analyzer = Analyzer()
        self.collector = Collector()

    async def handle(self, request: web.Request):
        async with aiohttp.ClientSession() as session:
            body = await request.read()

            async with session.request(
                method=request.method,
                url=f"{self.target_host}{request.rel_url}",
                headers=request.headers,
                data=body,
            ) as response:

                resp_body = await response.read()

                try:
                    req_json = json.loads(body) if body else None
                except:
                    req_json = None

                try:
                    resp_json = json.loads(resp_body) if resp_body else None
                except:
                    resp_json = None

                req_schema = self.analyzer.generate_schema(req_json) if req_json else None
                resp_schema = self.analyzer.generate_schema(resp_json) if resp_json else None

                self.collector.collect(
                    str(request.rel_url),
                    request.method,
                    req_schema,
                    resp_schema,
                )

                return web.Response(
                    body=resp_body,
                    status=response.status,
                    headers=response.headers,
                )

    def run(self, port: int):
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle)
        web.run_app(app, port=port)
