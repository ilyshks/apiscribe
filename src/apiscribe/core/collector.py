from apiscribe.storage.memory import InMemoryStorage
from apiscribe.models.endpoint import EndpointModel


class Collector:
    def __init__(self):
        self.storage = InMemoryStorage()
    
    def extract_fields(self, schema: dict | None):

        if not schema:
            return []

        if schema.get("type") != "object":
            return []

        return list(schema.get("properties", {}).keys())

    def collect(self, path: str, method: str, req_schema: dict, resp_schema: dict):

        fields = self.extract_fields(req_schema)

        endpoint = EndpointModel(
            path=path,
            method=method,
            request_schema=req_schema,
            response_schema=resp_schema,
            request_count=1,
            request_field_counts={f: 1 for f in fields},
        )

        self.storage.save(endpoint)
    

    def get_endpoints(self):
        return self.storage.get_all()
