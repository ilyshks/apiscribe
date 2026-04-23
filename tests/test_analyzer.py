import pytest
from apiscribe.core.analyzer import Analyzer
from unittest.mock import patch

@pytest.fixture
def analyzer():
    return Analyzer()

@pytest.mark.parametrize("value,expected_type", [
    ("hello", "string"),
    (42, "integer"),
    (3.14, "number"),
    (True, "boolean"),
    (False, "boolean"),
    (None, "null"),
])
def test_primitive_types(analyzer, value, expected_type):
    assert analyzer.generate_schema(value) == {"type": expected_type}


# ========== Тесты для словарей (object) ==========

def test_empty_dict(analyzer):
    assert analyzer.generate_schema({}) == {
        "type": "object",
        "properties": {}
    }

def test_dict_with_primitives(analyzer):
    data = {
        "name": "Alice",
        "age": 30,
        "score": 95.5,
        "active": True,
        "extra": None
    }
    expected = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "score": {"type": "number"},
            "active": {"type": "boolean"},
            "extra": {"type": "null"}
        }
    }
    assert analyzer.generate_schema(data) == expected

def test_nested_dict(analyzer):
    data = {
        "user": {
            "name": "Bob",
            "address": {
                "city": "NYC",
                "zip": 10001
            }
        }
    }
    expected = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "address": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "zip": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
    assert analyzer.generate_schema(data) == expected

# ========== Тесты для списков (array) с мокингом merge_schema ==========

def test_empty_list(analyzer):
    # Для пустого списка merge_schema не вызывается
    result = analyzer.generate_schema([])
    assert result == {"type": "array", "items": {}}

def test_list_with_single_item(analyzer):

    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        # При первом вызове prev=None, curr — схема элемента
        mock_merge.return_value = {"type": "integer"}  # упрощённо: возвращаем ту же схему
        result = analyzer.generate_schema([42])
        assert result == {"type": "array", "items": {"type": "integer"}}
        mock_merge.assert_called_once_with(None, {"type": "integer"})

def test_list_with_multiple_items_same_type(analyzer):

    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        # Имитируем, что merge_schema всегда возвращает второй аргумент (последний переданный)
        mock_merge.side_effect = lambda prev, curr: curr

        result = analyzer.generate_schema([1, 2, 3])
        assert result == {"type": "array", "items": {"type": "integer"}}
        # Вызовы: (None, int), (int, int), (int, int)
        assert mock_merge.call_count == 3

def test_list_with_different_types(analyzer):

    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        # Имитируем, что merge_schema объединяет типы, сохраняя последний
        def merge(prev, curr):
            if prev is None:
                return curr
            # Для теста просто возвращаем текущий (это нереалистично, но достаточно для проверки цикла)
            return curr
        mock_merge.side_effect = merge

        result = analyzer.generate_schema([1, "two", 3.0])
        # После трёх вызовов вернётся схема последнего элемента (float → number)
        assert result == {"type": "array", "items": {"type": "number"}}
        assert mock_merge.call_count == 3

def test_dict_containing_list(analyzer):
    # Здесь вызывается generate_schema для вложенного списка, который внутри использует merge_schema.
    # Нам нужно замокать merge_schema глобально для этого теста.

    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        # Для списка [1,2,3] нужно, чтобы merge_schema возвращал integer схему
        mock_merge.side_effect = lambda prev, curr: curr

        data = {
            "id": 1,
            "values": [1, 2, 3]
        }
        result = analyzer.generate_schema(data)
        expected = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "values": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            }
        }
        assert result == expected
        # Проверяем, что merge_schema вызывался для элементов списка (3 раза)
        assert mock_merge.call_count == 3

def test_list_containing_list(analyzer):
    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        # Простой мок: возвращаем второй аргумент (curr)
        mock_merge.side_effect = lambda prev, curr: curr

        data = [[1, 2], [3, 4, 5]]
        result = analyzer.generate_schema(data)

        # Ожидаем: массив, элементы которого — тоже массивы чисел
        expected = {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "integer"}
            }
        }
        assert result == expected

def test_dict_containing_list_of_lists(analyzer):
    with patch("apiscribe.core.analyzer.merge_schema") as mock_merge:
        mock_merge.side_effect = lambda prev, curr: curr

        data = {
            "matrix": [[1, 2], [3, 4]],
            "id": 42
        }
        result = analyzer.generate_schema(data)

        expected = {
            "type": "object",
            "properties": {
                "matrix": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                },
                "id": {"type": "integer"}
            }
        }
        assert result == expected