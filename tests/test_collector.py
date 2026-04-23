import pytest
from unittest.mock import patch
from apiscribe.core.collector import Collector


# ========== Фикстуры ==========

@pytest.fixture
def mock_storage_and_model():
    """Создаёт фикстуру с замоканными InMemoryStorage и EndpointModel,
    а также экземпляр Collector с подменённым storage."""

    with patch("apiscribe.core.collector.InMemoryStorage") as MockStorage, \
         patch("apiscribe.core.collector.EndpointModel") as MockEndpoint:
        
        mock_storage_instance = MockStorage.return_value
        collector = Collector()
        # Подменяем storage в созданном объекте на мок (на случай, если конструктор создал реальный)
        collector.storage = mock_storage_instance
        yield collector, MockStorage, MockEndpoint, mock_storage_instance


# ========== Тесты для extract_fields ==========

@pytest.mark.parametrize("schema,expected", [
    (None, []),
    ({}, []),                           # нет type
    ({"type": "array"}, []),           # не object
    ({"type": "object"}, []),          # object без properties
    ({"type": "object", "properties": {"a": {}, "b": {}}}, ["a", "b"]),
    ({"type": "object", "properties": {"foo": {"type": "string"}}}, ["foo"]),
])
def test_extract_fields(schema, expected):
    collector = Collector()
    assert collector.extract_fields(schema) == expected


# ========== Тесты для collect ==========

def test_collect_without_resp_schema(mock_storage_and_model):
    collector, MockStorage, MockEndpoint, mock_storage = mock_storage_and_model
    
    collector.collect(
        path="/users",
        method="POST",
        status_code=201,
        req_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        resp_schema=None
    )
    
    # Проверяем, что EndpointModel был создан с правильными аргументами
    MockEndpoint.assert_called_once_with(
        path="/users",
        method="POST",
        request_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        responses={},  # так как resp_schema=None
        request_count=1,
        request_field_counts={"name": 1}
    )
    
    # Проверяем, что storage.save был вызван с созданным экземпляром
    mock_storage.save.assert_called_once_with(MockEndpoint.return_value)


def test_collect_with_resp_schema(mock_storage_and_model):
    collector, MockStorage, MockEndpoint, mock_storage = mock_storage_and_model
    
    req_schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
    resp_schema = {"type": "object"}
    
    collector.collect("/items", "GET", 200, req_schema, resp_schema)
    
    MockEndpoint.assert_called_once_with(
        path="/items",
        method="GET",
        request_schema=req_schema,
        responses={200: resp_schema},
        request_count=1,
        request_field_counts={"id": 1}
    )
    mock_storage.save.assert_called_once()


def test_collect_without_req_schema(mock_storage_and_model):
    collector, MockStorage, MockEndpoint, mock_storage = mock_storage_and_model
    
    collector.collect("/test", "GET", 200, None, {"type": "string"})
    
    # Если req_schema = None, extract_fields вернёт [] → request_field_counts пустой
    MockEndpoint.assert_called_once_with(
        path="/test",
        method="GET",
        request_schema=None,
        responses={200: {"type": "string"}},
        request_count=1,
        request_field_counts={}
    )
    mock_storage.save.assert_called_once()


def test_collect_req_schema_not_object(mock_storage_and_model):
    collector, MockStorage, MockEndpoint, mock_storage = mock_storage_and_model
    
    # Схема не object → fields = [] → request_field_counts пустой
    collector.collect("/api", "POST", 400, {"type": "array"}, {"type": "null"})
    
    MockEndpoint.assert_called_once_with(
        path="/api",
        method="POST",
        request_schema={"type": "array"},
        responses={400: {"type": "null"}},
        request_count=1,
        request_field_counts={}
    )
    mock_storage.save.assert_called_once()


# ========== Тесты для get_endpoints ==========

def test_get_endpoints_returns_from_storage():
    # Используем реальный Collector с реальным InMemoryStorage (без мока)
    # Это интеграционный тест, но он простой и не требует внешних зависимостей.
    collector = Collector()
    assert collector.get_endpoints() == []  # Изначально пусто
    
    # Добавим эндпоинт через collect (не мокая, но используя реальный storage)
    # Для этого импортируем реальный EndpointModel? Если его нет, тест не пройдёт.
    # Проще замокать storage.get_all.
    with patch("apiscribe.core.collector.InMemoryStorage") as MockStorage:
        mock_storage = MockStorage.return_value
        collector = Collector()
        collector.storage = mock_storage
        mock_storage.get_all.return_value = ["endpoint1", "endpoint2"]
        
        result = collector.get_endpoints()
        assert result == ["endpoint1", "endpoint2"]
        mock_storage.get_all.assert_called_once()