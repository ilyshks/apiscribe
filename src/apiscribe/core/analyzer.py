from typing import Any


class Analyzer:
    def generate_schema(self, data: Any) -> dict:
        if isinstance(data, dict):
            return {
                "type": "object",
                "properties": {
                    key: self.generate_schema(value)
                    for key, value in data.items()
                },
            }
        elif isinstance(data, list):
            if data:
                return {
                    "type": "array",
                    "items": self.generate_schema(data[0]),
                }
            return {"type": "array", "items": {}}
        elif isinstance(data, str):
            return {"type": "string"}
        elif isinstance(data, int):
            return {"type": "integer"}
        elif isinstance(data, float):
            return {"type": "number"}
        elif isinstance(data, bool):
            return {"type": "boolean"}
        else:
            return {"type": "null"}
