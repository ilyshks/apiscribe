from typing import Dict, Tuple
from apiscribe.models.endpoint import EndpointModel
from apiscribe.utils.schema_merge import merge_schema


class InMemoryStorage:
    def __init__(self):
        self._endpoints: Dict[Tuple[str, str], EndpointModel] = {}

    def save(self, endpoint: EndpointModel):

        key = (endpoint.path, endpoint.method)
        existing = self._endpoints.get(key)

        if not existing:
            self._endpoints[key] = endpoint
            return

        merged_request = merge_schema(
            existing.request_schema,
            endpoint.request_schema
        )

        merged_response = merge_schema(
            existing.response_schema,
            endpoint.response_schema
        )

        existing.request_schema = merged_request
        existing.response_schema = merged_response

        self._endpoints[key] = existing

    def get_all(self):
        return list(self._endpoints.values())
