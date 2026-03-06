import aiohttp
from aiohttp import web
import asyncio
import json
import random

from apiscribe.core.analyzer import Analyzer
from apiscribe.core.collector import Collector
from apiscribe.core.config import Config


class ProxyServer:
    def __init__(self, config: Config, collector: Collector):
        self.config = config
        self.collector = collector
        self.analyzer = Analyzer()

    async def handle(self, request: web.Request):

        if any(request.path.startswith(p) for p in self.config.exclude_paths):
            return await self._forward(request)

        if not self.config.analyze_all:
            if random.random() > self.config.sample_rate:
                return await self._forward(request)

        return await self._process(request)

    async def _forward(self, request: web.Request):
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:

                body = await request.read()

                async with session.request(
                    method=request.method,
                    url=f"{self.config.target_url}{request.rel_url}",
                    headers=request.headers,
                    data=body,
                ) as response:

                    resp_body = await response.read()

                    return web.Response(
                        body=resp_body,
                        status=response.status,
                        headers=response.headers,
                    )

        except aiohttp.ClientConnectorError:
            return web.json_response(
                {"error": "Target API unreachable"},
                status=502,
            )

        except asyncio.TimeoutError:
            return web.json_response(
                {"error": "Target API timeout"},
                status=504,
            )

        except aiohttp.ClientError as e:
            return web.json_response(
                {"error": f"Client error: {str(e)}"},
                status=502,
            )

        except Exception:
            return web.json_response(
                {"error": "Internal proxy error"},
                status=500,
            )

    async def _process(self, request: web.Request):
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as session:

                body = await request.read()

                if len(body) > self.config.max_body_size:
                    return web.Response(status=413, text="Body too large")

                async with session.request(
                    method=request.method,
                    url=f"{self.config.target_url}{request.rel_url}",
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

                    req_schema = (
                        self.analyzer.generate_schema(req_json)
                        if req_json else None
                    )

                    resp_schema = (
                        self.analyzer.generate_schema(resp_json)
                        if resp_json else None
                    )

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

        except aiohttp.ClientConnectorError:
            return web.json_response(
                {"error": "Target API unreachable"},
                status=502,
            )

        except asyncio.TimeoutError:
            return web.json_response(
                {"error": "Target API timeout"},
                status=504,
            )

        except aiohttp.ClientError as e:
            return web.json_response(
                {"error": f"Client error: {str(e)}"},
                status=502,
            )

        except Exception:
            return web.json_response(
                {"error": "Internal proxy error"},
                status=500,
            )

    def run(self):
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle)

        self.runner = web.AppRunner(app)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def start():
            await self.runner.setup()
            site = web.TCPSite(self.runner, self.config.host, self.config.port)
            await site.start()

        loop.run_until_complete(start())
        loop.run_forever()
    
    async def shutdown(self):
        await self.runner.cleanup()
