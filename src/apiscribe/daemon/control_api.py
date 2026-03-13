from aiohttp import web
from apiscribe.daemon.daemon import daemon
from apiscribe.generator.openapi import OpenAPIGenerator
from collections import defaultdict
import re
import logging

# Отключаем вывод логов, устанавливая уровень WARNING (выше INFO/DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

INT_RE = re.compile(r"^\d+$")
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")

def get_segment_signature(segment: str):
    if INT_RE.match(segment):
        return ('param', 'integer')
    if UUID_RE.match(segment):
        return ('param', 'uuid')
    return ('const', segment)

def path_to_signature(path: str):
    if not path:
        return tuple()
    segments = path.strip('/').split('/')
    return tuple(get_segment_signature(seg) for seg in segments)

def signature_to_template(sig: tuple) -> str:
    segments = []
    param_counter = {}
    for idx, (kind, value) in enumerate(sig):
        if kind == 'const':
            segments.append(value)
        else:
            base_name = {
                'integer': 'id',
                'uuid': 'uuid',
                'string': 'param'
            }.get(value, 'param')
            if base_name in param_counter:
                param_counter[base_name] += 1
                name = f"{base_name}_{param_counter[base_name]}"
            else:
                param_counter[base_name] = 1
                name = base_name
            segments.append(f"{{{name}}}")
    return '/' + '/'.join(segments) if segments else '/'

async def start(request):
    data = await request.json()
    result = await daemon.start_proxy(data["target_url"])
    return web.json_response(result)

async def stop(request):
    result = await daemon.stop_proxy()
    return web.json_response(result)

async def status(request):
    return web.json_response({
        "running": daemon.proxy is not None,
        "target": str(daemon.config.target_url) if daemon.config else None
    })

async def stats(request):
    endpoints = daemon.collector.get_endpoints()
    total = sum(e.request_count for e in endpoints)
    methods = {}
    for e in endpoints:
        methods[e.method] = methods.get(e.method, 0) + e.request_count
    return web.json_response({
        "total_requests": total,
        "endpoint_count": len(endpoints),
        "methods": methods
    })

async def endpoints(request):
    try:
        eps = daemon.collector.get_endpoints()
        groups = defaultdict(int)
        for ep in eps:
            sig = path_to_signature(ep.path)
            key = (ep.method, sig)
            groups[key] += ep.request_count
        result = [
            {"method": method, "path": signature_to_template(sig), "count": count}
            for (method, sig), count in groups.items()
        ]
        return web.json_response(result)
    except Exception as e:
        logger.exception("Error in endpoints handler")  # только при реальной ошибке
        return web.json_response({"error": str(e)}, status=500)

async def logs_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    daemon.log_clients.append(ws)
    try:
        async for _ in ws:
            pass
    finally:
        if ws in daemon.log_clients:
            daemon.log_clients.remove(ws)
    return ws

async def get_openapi(request):
    endpoints = daemon.collector.get_endpoints()
    generator = OpenAPIGenerator()
    spec = generator.generate(endpoints)
    return web.json_response(spec)

def create_app():
    app = web.Application()
    app.router.add_post("/api/start", start)
    app.router.add_post("/api/stop", stop)
    app.router.add_get("/api/status", status)
    app.router.add_get("/api/stats", stats)
    app.router.add_get("/api/endpoints", endpoints)
    app.router.add_get("/ws/logs", logs_ws)
    app.router.add_get("/openapi", get_openapi)
    return app