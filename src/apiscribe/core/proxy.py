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

        self.runner = None
        self.site = None
        self.session: aiohttp.ClientSession | None = None

    async def handle(self, request: web.Request):

        if any(request.path.startswith(p) for p in self.config.exclude_paths):
            return await self._forward(request)

        if not self.config.analyze_all:
            if random.random() > self.config.sample_rate:
                return await self._forward(request)

        return await self._process(request)

    async def _forward(self, request: web.Request):

        try:

            body = await request.read()

            async with self.session.request(
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

            body = await request.read()

            if len(body) > self.config.max_body_size:
                return web.Response(status=413, text="Body too large")

            async with self.session.request(
                method=request.method,
                url=f"{self.config.target_url}{request.rel_url}",
                headers=request.headers,
                data=body,
            ) as response:

                resp_body = await response.read()

                try:
                    req_json = json.loads(body) if body else None
                except Exception:
                    req_json = None

                try:
                    resp_json = json.loads(resp_body) if resp_body else None
                except Exception:
                    resp_json = None

                req_schema = (
                    self.analyzer.generate_schema(req_json)
                    if req_json else None
                )

                resp_schema = (
                    self.analyzer.generate_schema(resp_json)
                    if resp_json else None
                )

                path = request.rel_url.path

                self.collector.collect(
                    path,
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

    async def start(self):

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        connector = aiohttp.TCPConnector(
            limit=1000,
            limit_per_host=100,
            ttl_dns_cache=300,
            keepalive_timeout=30,
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
        )

        app = web.Application()
        app.router.add_route("*", "/{path:.*}", self.handle)

        self.runner = web.AppRunner(app)
        await self.runner.setup()

        self.site = web.TCPSite(
            self.runner,
            self.config.host,
            self.config.port,
        )

        await self.site.start()

    async def shutdown(self):

        if self.session:
            await self.session.close()

        if self.runner:
            await self.runner.cleanup()