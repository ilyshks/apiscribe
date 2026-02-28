from typing import Dict, Tuple
from apiscribe.models.endpoint import EndpointModel


class InMemoryStorage:
    def __init__(self):
        self._endpoints: Dict[Tuple[str, str], EndpointModel] = {}

    def save(self, endpoint: EndpointModel):
        key = (endpoint.path, endpoint.method)
        self._endpoints[key] = endpoint

    def get_all(self):
        return list(self._endpoints.values())
