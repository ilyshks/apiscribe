import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import web
import json
import aiohttp
import asyncio

from apiscribe.core.proxy import ProxyServer


# ---------- Фикстуры ----------

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.host = "localhost"
    config.port = 8080
    config.target_url = "http://target-api"
    config.exclude_paths = ["/health", "/metrics"]
    config.analyze_all = True
    config.sample_rate = 1.0
    config.max_body_size = 1024 * 1024
    config.timeout = 30
    return config


@pytest.fixture
def mock_collector():
    return MagicMock()


@pytest.fixture
def mock_daemon():
    daemon = MagicMock()
    daemon.log_clients = []  # будем подменять в тестах при необходимости
    return daemon


@pytest.fixture
def mock_analyzer():
    analyzer = MagicMock()
    analyzer.generate_schema = MagicMock(return_value={"type": "object"})
    return analyzer


@pytest.fixture
def proxy(mock_config, mock_collector, mock_daemon, mock_analyzer):
    with patch("apiscribe.core.proxy.Analyzer", return_value=mock_analyzer):
        proxy = ProxyServer(mock_config, mock_collector, mock_daemon)
        # подменяем analyzer на явно переданный мок (чтобы не создавать новый)
        proxy.analyzer = mock_analyzer
        proxy.session = AsyncMock()
        return proxy


# ---------- Тесты для broadcast_log ----------

@pytest.mark.asyncio
async def test_broadcast_log_sends_to_open_clients(proxy):
    ws1 = AsyncMock()
    ws1.closed = False
    ws2 = AsyncMock()
    ws2.closed = False
    proxy.daemon.log_clients = [ws1, ws2]

    log_msg = {"test": "data"}
    await proxy.broadcast_log(log_msg)

    ws1.send_json.assert_awaited_once_with(log_msg)
    ws2.send_json.assert_awaited_once_with(log_msg)
    # Убедимся, что закрытые не удалялись
    assert len(proxy.daemon.log_clients) == 2


@pytest.mark.asyncio
async def test_broadcast_log_removes_closed_clients(proxy):
    ws1 = AsyncMock()
    ws1.closed = True
    ws2 = AsyncMock()
    ws2.closed = False
    ws3 = AsyncMock()
    ws3.closed = True
    proxy.daemon.log_clients = [ws1, ws2, ws3]

    await proxy.broadcast_log({})

    # ws1 и ws3 должны быть удалены
    assert proxy.daemon.log_clients == [ws2]


@pytest.mark.asyncio
async def test_broadcast_log_handles_exception(proxy):
    ws = AsyncMock()
    ws.closed = False
    ws.send_json = AsyncMock(side_effect=Exception("Send failed"))
    proxy.daemon.log_clients = [ws]

    await proxy.broadcast_log({})

    # Сокет с ошибкой должен быть удалён
    assert proxy.daemon.log_clients == []


# ---------- Тесты для handle ----------

@pytest.mark.asyncio
async def test_handle_exclude_path_forward(proxy):
    request = MagicMock()
    request.path = "/health"
    proxy._forward = AsyncMock(return_value=web.Response(text="ok"))
    response = await proxy.handle(request)
    assert response is proxy._forward.return_value  # убрали await
    proxy._forward.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_handle_not_analyze_all_and_sampling_skip(proxy):
    proxy.config.analyze_all = False
    proxy.config.sample_rate = 0.0  # никогда не берём
    proxy._forward = AsyncMock()
    proxy._process = AsyncMock()

    request = MagicMock()
    request.path = "/api/test"
    await proxy.handle(request)

    # Должен быть вызван _forward, а не _process
    proxy._forward.assert_awaited_once_with(request)
    proxy._process.assert_not_awaited()


@pytest.mark.parametrize("analyze_all,sample_rate,rand_val,expected_method", [
    (True, 0.5, 0.2, "_process"),    # analyze_all=True → всегда _process
    (False, 0.5, 0.2, "_process"),   # попадает в выборку
    (False, 0.5, 0.8, "_forward"),   # не попадает в выборку
])
@pytest.mark.asyncio
async def test_handle_sampling(proxy, analyze_all, sample_rate, rand_val, expected_method):
    proxy.config.analyze_all = analyze_all
    proxy.config.sample_rate = sample_rate
    proxy._forward = AsyncMock()
    proxy._process = AsyncMock()

    with patch("apiscribe.core.proxy.random.random", return_value=rand_val):
        request = MagicMock()
        request.path = "/some"
        await proxy.handle(request)

    if expected_method == "_process":
        proxy._process.assert_awaited_once_with(request)
        proxy._forward.assert_not_awaited()
    else:
        proxy._forward.assert_awaited_once_with(request)
        proxy._process.assert_not_awaited()


# ---------- Тесты для _forward ----------

@pytest.mark.asyncio
async def test_forward_unexpected_exception(proxy):
    request = MagicMock()
    request.read = AsyncMock(return_value=b"")
    proxy.session.request = AsyncMock(side_effect=RuntimeError("Unexpected"))

    response = await proxy._forward(request)
    assert response.status == 500
    body = json.loads(response.body)
    assert body["error"] == "Internal proxy error"


# ---------- Тесты для _process ----------

@pytest.mark.asyncio
async def test_process_success(proxy):
    request = MagicMock()
    request.method = "POST"
    request.path = "/api"
    request.rel_url = MagicMock()
    request.rel_url.path = "/api"
    request.headers = {}
    request.read = AsyncMock(return_value=b'{"name":"test"}')

    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.headers = {}
    mock_response.read = AsyncMock(return_value=b'{"id":1}')

    proxy.session.request = AsyncMock()
    proxy.session.request.return_value.__aenter__.return_value = mock_response

    proxy.analyzer.generate_schema.side_effect = [
        {"type": "object", "properties": {"name": {"type": "string"}}},
        {"type": "object", "properties": {"id": {"type": "integer"}}}
    ]
    proxy.broadcast_log = AsyncMock()

    response = await proxy._process(request)

    # Проверяем сбор схем
    proxy.analyzer.generate_schema.assert_any_call({"name": "test"})
    proxy.analyzer.generate_schema.assert_any_call({"id": 1})
    # Collector собирает данные
    proxy.collector.collect.assert_called_once_with(
        "/api", "POST", 201,
        {"type": "object", "properties": {"name": {"type": "string"}}},
        {"type": "object", "properties": {"id": {"type": "integer"}}}
    )
    # Лог
    proxy.broadcast_log.assert_awaited_once_with({
        "method": "POST",
        "path": "/api",
        "status": 201
    })
    # Ответ
    assert response.status == 201
    assert response.body == b'{"id":1}'


@pytest.mark.asyncio
async def test_process_body_too_large(proxy):
    request = MagicMock()
    request.read = AsyncMock(return_value=b"x" * (proxy.config.max_body_size + 1))

    response = await proxy._process(request)
    assert response.status == 413
    assert response.text == "Body too large"
    # Дальше ничего не должно вызываться
    proxy.session.request.assert_not_called()


@pytest.mark.parametrize("req_body,resp_body,req_schema_call,resp_schema_call", [
    (b'{"valid":1}', b'{"valid":2}', True, True),
    (b'invalid json', b'{"ok":1}', False, True),
    (b'{"a":1}', b'invalid json', True, False),
    (b'', b'', False, False),  # пустое тело -> None
])
@pytest.mark.asyncio
async def test_process_json_parsing_errors(proxy, req_body, resp_body, req_schema_call, resp_schema_call):
    request = MagicMock()
    request.method = "GET"
    request.path = "/"
    request.rel_url = MagicMock()
    request.rel_url.path = "/"
    request.headers = {}
    request.read = AsyncMock(return_value=req_body)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {}
    mock_response.read = AsyncMock(return_value=resp_body)

    proxy.session.request = AsyncMock()
    proxy.session.request.return_value.__aenter__.return_value = mock_response

    proxy.analyzer.generate_schema.reset_mock()
    proxy.collector.collect.reset_mock()
    proxy.broadcast_log = AsyncMock()

    await proxy._process(request)

    # Проверяем, вызывался ли generate_schema для request
    if req_schema_call:
        # ожидаем, что хотя бы попытка разбора была
        # при невалидном JSON req_json = None, generate_schema не вызывается
        if req_body != b'invalid json':
            proxy.analyzer.generate_schema.assert_any_call({"valid": 1} if req_body == b'{"valid":1}' else {"a": 1})
    else:
        # generate_schema не вызывается для request (если невалидный JSON или пустой)
        # Проверяем только, что не было вызова с декодированным объектом (которого нет)
        calls = [call[0][0] for call in proxy.analyzer.generate_schema.call_args_list]
        assert None not in calls  # generate_schema не вызывается с None

    if resp_schema_call:
        if resp_body == b'{"ok":1}':
            proxy.analyzer.generate_schema.assert_any_call({"ok": 1})
        elif resp_body == b'{"valid":2}':
            proxy.analyzer.generate_schema.assert_any_call({"valid": 2})
    else:
        # Для невалидного JSON или пустого — не вызывается
        pass

    # Проверяем вызов collector.collect — он всегда вызывается, но с None для схем, если не удалось распарсить
    collect_call_args = proxy.collector.collect.call_args[0]
    assert collect_call_args[0] == "/"
    assert collect_call_args[1] == "GET"
    assert collect_call_args[2] == 200
    # req_schema/ resp_schema – могут быть None или dict
    if not req_schema_call:
        assert collect_call_args[3] is None
    if not resp_schema_call:
        assert collect_call_args[4] is None


@pytest.mark.asyncio
async def test_process_network_errors(proxy):
    # Проверяем, что _process перехватывает те же исключения, что и _forward
    request = MagicMock()
    request.read = AsyncMock(return_value=b"{}")
    proxy.session.request = AsyncMock(side_effect=aiohttp.ClientConnectorError(None, Exception()))

    response = await proxy._process(request)
    assert response.status == 502
    body = json.loads(response.body)
    assert body["error"] == "Target API unreachable"


# ---------- Тесты для start ----------

@pytest.mark.asyncio
async def test_start_creates_session_and_runner(proxy):
    with patch("aiohttp.ClientSession") as MockSession, \
         patch("aiohttp.TCPConnector") as MockConnector, \
         patch("aiohttp.web.Application") as MockApp, \
         patch("aiohttp.web.AppRunner") as MockRunner, \
         patch("aiohttp.web.TCPSite") as MockSite:

        mock_session = AsyncMock()
        MockSession.return_value = mock_session
        mock_runner = AsyncMock()
        MockRunner.return_value = mock_runner
        mock_site = AsyncMock()
        MockSite.return_value = mock_site

        await proxy.start()

        # Проверяем создание Connector с параметрами
        MockConnector.assert_called_once_with(limit=1000, limit_per_host=100, ttl_dns_cache=300, keepalive_timeout=30)
        # Проверяем создание ClientSession с таймаутом и коннектором
        MockSession.assert_called_once()
        assert proxy.session is mock_session

        # Проверяем создание приложения и добавление маршрута
        mock_app = MockApp.return_value
        mock_app.router.add_route.assert_called_once_with("*", "/{path:.*}", proxy.handle)

        # Проверяем запуск runner
        mock_runner.setup.assert_awaited_once()
        # Проверяем создание и запуск сайта
        MockSite.assert_called_once_with(mock_runner, proxy.config.host, proxy.config.port)
        mock_site.start.assert_awaited_once()


# ---------- Тесты для shutdown ----------

@pytest.mark.asyncio
async def test_shutdown_closes_session_and_runner(proxy):
    proxy.session = AsyncMock()
    proxy.runner = AsyncMock()

    await proxy.shutdown()

    proxy.session.close.assert_awaited_once()
    proxy.runner.cleanup.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_handles_none_session(proxy):
    proxy.session = None
    proxy.runner = AsyncMock()
    await proxy.shutdown()
    proxy.runner.cleanup.assert_awaited_once()
    # нет ошибки
