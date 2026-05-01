import pytest

from apiscribe.utils.schema_merge import *


class TestCollectTypes:
    @pytest.mark.parametrize("input_value, expected", [
        (None, set()),
        ("string", {"string"}),
        (["integer", "number"], {"integer", "number"}),
        (["string"], {"string"}),
        ([], set()),
    ])
    def test_collect_types(self, input_value, expected):
        assert collect_types(input_value) == expected


class TestNormalizeTypes:
    @pytest.mark.parametrize("input_set, expected", [
        ({"integer", "number"}, {"number"}),
        ({"integer"}, {"integer"}),
        ({"number"}, {"number"}),
        ({"string", "integer", "number"}, {"string", "number"}),
        (set(), set()),
        ({"boolean", "integer"}, {"boolean", "integer"}),
    ])
    def test_normalize_types(self, input_set, expected):
        assert normalize_types(input_set) == expected


class TestMergeSchema:
    @pytest.mark.parametrize("a, b, expected", [
        # Оба None
        (None, None, None),
        # Один None
        (None, {"type": "string"}, {"type": "string"}),
        ({"type": "string"}, None, {"type": "string"}),
        # Равные схемы
        ({"type": "string"}, {"type": "string"}, {"type": "string"}),
        ({"type": "integer"}, {"type": "integer"}, {"type": "integer"}),
        # Разные примитивные типы -> union
        ({"type": "string"}, {"type": "integer"}, {"type": ["integer", "string"]}),
        ({"type": "number"}, {"type": "integer"}, {"type": ["number"]}),  # integer+number -> number
        ({"type": ["string", "integer"]}, {"type": "number"}, {"type": ["number", "string"]}),
        # Object
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"b": {"type": "integer"}}},
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}
        ),
        (
            {"type": "object", "properties": {"x": {"type": "string"}}},
            {"type": "object", "properties": {"x": {"type": "integer"}}},
            {"type": "object", "properties": {"x": {"type": ["integer", "string"]}}}
        ),
        # additionalProperties
        (
            {"type": "object", "additionalProperties": {"type": "string"}},
            {"type": "object", "additionalProperties": {"type": "integer"}},
            {"type": "object", "additionalProperties": {"type": ["integer", "string"]}, "properties": {}}
        ),
        # Array
        (
            {"type": "array", "items": {"type": "string"}},
            {"type": "array", "items": {"type": "integer"}},
            {"type": "array", "items": {"type": ["integer", "string"]}}
        ),
        # Вложенные объекты
        (
            {"type": "object", "properties": {"user": {"type": "object", "properties": {"name": {"type": "string"}}}}},
            {"type": "object", "properties": {"user": {"type": "object", "properties": {"age": {"type": "integer"}}}}},
            {"type": "object", "properties": {"user": {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}}}
        ),
        # Пустые объекты
        ({"type": "object"}, {"type": "object", "properties": {"a": {"type": "string"}}},
         {"type": "object", "properties": {"a": {"type": "string"}}}),
        # Пустые массивы
        ({"type": "array"}, {"type": "array", "items": {"type": "string"}},
         {"type": "array", "items": {"type": "string"}}),
    ])
    def test_merge_schema(self, a, b, expected):
        assert merge_schema(a, b) == expected


class TestMergeObject:
    @pytest.mark.parametrize("a, b, expected", [
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"a": {"type": "integer"}}},
            {"type": "object", "properties": {"a": {"type": ["integer", "string"]}}}
        ),
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "properties": {"b": {"type": "integer"}}},
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}
        ),
        (
            {"type": "object", "additionalProperties": {"type": "string"}},
            {"type": "object", "additionalProperties": {"type": "integer"}},
            {"type": "object", "properties": {}, "additionalProperties": {"type": ["integer", "string"]}}
        ),
        (
            {"type": "object", "additionalProperties": {"type": "boolean"}},
            {"type": "object", "additionalProperties": {"type": "string"}},
            {"type": "object", "properties": {}, "additionalProperties": {"type": ["boolean", "string"]}}
        ),
        # один из дополнительных свойств отсутствует
        (
            {"type": "object", "properties": {"x": {"type": "string"}}},
            {"type": "object", "properties": {"x": {"type": "string"}}, "additionalProperties": {"type": "boolean"}},
            {"type": "object", "properties": {"x": {"type": "string"}}, "additionalProperties": {"type": "boolean"}}
        ),
    ])
    def test_merge_object(self, a, b, expected):
        assert merge_object(a, b) == expected


class TestMergeArray:
    @pytest.mark.parametrize("a, b, expected", [
        (
            {"type": "array", "items": {"type": "string"}},
            {"type": "array", "items": {"type": "integer"}},
            {"type": "array", "items": {"type": ["integer", "string"]}}
        ),
        (
            {"type": "array", "items": {"type": "string"}},
            {"type": "array"},
            {"type": "array", "items": {"type": "string"}}
        ),
        (
            {"type": "array"},
            {"type": "array", "items": {"type": "integer"}},
            {"type": "array", "items": {"type": "integer"}}
        ),
        (
            {"type": "array", "items": {"type": "object", "properties": {"a": {"type": "string"}}}},
            {"type": "array", "items": {"type": "object", "properties": {"b": {"type": "integer"}}}},
            {"type": "array", "items": {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}}}
        ),
    ])
    def test_merge_array(self, a, b, expected):
        assert merge_array(a, b) == expected