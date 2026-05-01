import pytest
from unittest.mock import patch, Mock
from collections import namedtuple

from apiscribe.generator.openapi import OpenAPIGenerator

# Define a simple endpoint structure
Endpoint = namedtuple("Endpoint", ["method", "path", "request_schema", "responses", "request_field_counts", "request_count"])


class TestApplyRequired:
    @pytest.mark.parametrize("schema, field_counts, total, expected", [
        (None, {"a": 5}, 10, None),
        ({"type": "object", "properties": {"a": {"type": "string"}}}, None, 10,
         {"type": "object", "properties": {"a": {"type": "string"}}}),
        ({"type": "string"}, {"a": 10}, 10, {"type": "string"}),
        (
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}},
            {"a": 10, "b": 5}, 10,
            {"type": "object", "properties": {"a": {"type": "string"}, "b": {"type": "integer"}}, "required": ["a"]}
        ),
        (
            {"type": "object", "properties": {"x": {"type": "boolean"}, "y": {"type": "string"}}},
            {"x": 3, "y": 3}, 3,
            {"type": "object", "properties": {"x": {"type": "boolean"}, "y": {"type": "string"}}, "required": ["x", "y"]}
        ),
        (
            {"type": "object", "properties": {"p": {"type": "number"}}},
            {"p": 2}, 5,
            {"type": "object", "properties": {"p": {"type": "number"}}}
        ),
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"a": 5}, 5,
            {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        ),
    ])
    def test_apply_required(self, schema, field_counts, total, expected):
        gen = OpenAPIGenerator()
        result = gen.apply_required(schema, field_counts, total)
        assert result == expected

    def test_apply_required_does_not_mutate_original(self):
        gen = OpenAPIGenerator()
        original = {"type": "object", "properties": {"a": {"type": "string"}}}
        result = gen.apply_required(original, {"a": 10}, 10)
        assert result == {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]}
        assert original == {"type": "object", "properties": {"a": {"type": "string"}}}


class TestGenerate:
    def test_generate_single_method_single_cluster(self):
        endpoints = [
            Endpoint("GET", "/users/1", None, {200: {"type": "object"}}, None, 0),
            Endpoint("GET", "/users/2", {"type": "object", "properties": {"name": {"type": "string"}}},
                     {200: {"type": "object"}}, {"name": 2}, 2),
        ]

        with patch("apiscribe.utils.path_cluster.cluster_paths") as mock_cluster, \
             patch("apiscribe.utils.path_inference.infer_path_template") as mock_infer:
            mock_cluster.return_value = [["/users/1", "/users/2"]]
            mock_infer.return_value = ("/users/{user_id}", [{"name": "user_id", "in": "path"}])

            gen = OpenAPIGenerator()
            result = gen.generate(endpoints)

        assert "paths" in result
        assert "/users/{users_id}" in result["paths"]
        op = result["paths"]["/users/{users_id}"]["get"]
        assert "requestBody" not in op
        assert "200" in op["responses"]
        assert op["responses"]["200"]["content"]["application/json"]["schema"] == {"type": "object"}

    def test_generate_request_body_from_example(self):
        endpoints = [
            Endpoint("POST", "/items",
                     request_schema={"type": "object", "properties": {"name": {"type": "string"}}},
                     responses={200: {}}, request_field_counts=None, request_count=0)
        ]
        with patch("apiscribe.utils.path_cluster.cluster_paths") as mock_cluster, \
             patch("apiscribe.utils.path_inference.infer_path_template") as mock_infer:
            mock_cluster.return_value = [["/items"]]
            mock_infer.return_value = ("/items", [])
            gen = OpenAPIGenerator()
            result = gen.generate(endpoints)

        op = result["paths"]["/items"]["post"]
        assert "requestBody" in op
        assert op["requestBody"]["content"]["application/json"]["schema"] == {"type": "object", "properties": {"name": {"type": "string"}}}

    def test_generate_apply_required_called(self):
        endpoints = [
            Endpoint("PUT", "/user/1",
                     request_schema={"type": "object", "properties": {"id": {"type": "integer"}}},
                     responses={200: {}},
                     request_field_counts={"id": 1},
                     request_count=1)
        ]
        with patch("apiscribe.utils.path_cluster.cluster_paths") as mock_cluster, \
             patch("apiscribe.utils.path_inference.infer_path_template") as mock_infer, \
             patch.object(OpenAPIGenerator, "apply_required", wraps=OpenAPIGenerator().apply_required) as mock_apply:
            mock_cluster.return_value = [["/user/1"]]
            mock_infer.return_value = ("/user/{id}", [])
            gen = OpenAPIGenerator()
            gen.generate(endpoints)

            mock_apply.assert_called_once_with(
                {"type": "object", "properties": {"id": {"type": "integer"}}},
                {"id": 1},
                1
            )

    def test_generate_multiple_responses(self):
        endpoints = [
            Endpoint("GET", "/status", None,
                     responses={200: {"type": "string"}, 404: {"type": "string"}},
                     request_field_counts=None, request_count=0)
        ]
        with patch("apiscribe.utils.path_cluster.cluster_paths") as mock_cluster, \
             patch("apiscribe.utils.path_inference.infer_path_template") as mock_infer:
            mock_cluster.return_value = [["/status"]]
            mock_infer.return_value = ("/status", [])
            gen = OpenAPIGenerator()
            result = gen.generate(endpoints)

        op = result["paths"]["/status"]["get"]
        assert "200" in op["responses"]
        assert "404" in op["responses"]
        assert op["responses"]["200"]["description"] == "HTTP 200"
        assert op["responses"]["404"]["description"] == "HTTP 404"

    def test_generate_handles_empty_endpoints(self):
        gen = OpenAPIGenerator()
        result = gen.generate([])
        assert result["paths"] == {}
        assert "openapi" in result