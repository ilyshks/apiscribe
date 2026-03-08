import asyncio

from apiscribe.core.config import Config
from apiscribe.core.proxy import ProxyServer
from apiscribe.core.collector import Collector


class APIScribeDaemon:

    def __init__(self):

        self.proxy = None
        self.collector = Collector()
        self.config = None

    async def start_proxy(self, target_url):

        if self.proxy:
            return {"status": "already_running"}

        self.config = Config(target_url=target_url)

        self.proxy = ProxyServer(
            config=self.config,
            collector=self.collector,
        )

        await self.proxy.start()

        return {"status": "started"}

    async def stop_proxy(self):

        if not self.proxy:
            return {"status": "not_running"}

        await self.proxy.shutdown()

        self.proxy = None

        return {"status": "stopped"}

    def get_collector(self):
        return self.collector


daemon = APIScribeDaemon()