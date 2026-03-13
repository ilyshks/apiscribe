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

    def collect(
        self,
        path: str,
        method: str,
        status_code: int,
        req_schema: dict | None,
        resp_schema: dict | None,
    ):

        fields = self.extract_fields(req_schema)

        endpoint = EndpointModel(
            path=path,
            method=method,
            request_schema=req_schema,
            responses={
                status_code: resp_schema
            } if resp_schema else {},
            request_count=1,
            request_field_counts={f: 1 for f in fields},
        )

        self.storage.save(endpoint)

    def get_endpoints(self):
        return self.storage.get_all()