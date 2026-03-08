import pytest

from apiscribe.models.endpoint import EndpointModel
from apiscribe.generator.openapi import OpenAPIGenerator


@pytest.fixture
def endpoint_factory():
    def create(path, method="GET"):
        return EndpointModel(
            path=path,
            method=method,
            request_schema=None,
            response_schema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                }
            }
        )
    return create


@pytest.fixture
def generator():
    return OpenAPIGenerator()