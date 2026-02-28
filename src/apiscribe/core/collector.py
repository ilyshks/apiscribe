from apiscribe.storage.memory import InMemoryStorage
from apiscribe.models.endpoint import EndpointModel


class Collector:
    def __init__(self):
        self.storage = InMemoryStorage()

    def collect(self, path: str, method: str, req_schema: dict, resp_schema: dict):
        endpoint = EndpointModel(
            path=path,
            method=method,
            request_schema=req_schema,
            response_schema=resp_schema,
        )
        self.storage.save(endpoint)

    def get_endpoints(self):
        return self.storage.get_all()
