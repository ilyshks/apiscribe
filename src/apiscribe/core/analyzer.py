from typing import Any
from apiscribe.utils.schema_merge import merge_schema


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

            if not data:
                return {
                    "type": "array",
                    "items": {}
                }

            merged_items_schema = None

            for item in data:

                item_schema = self.generate_schema(item)

                merged_items_schema = merge_schema(
                    merged_items_schema,
                    item_schema
                )

            return {
                "type": "array",
                "items": merged_items_schema
            }

        elif isinstance(data, str):
            return {"type": "string"}
        
        elif isinstance(data, bool):
            return {"type": "boolean"}

        elif isinstance(data, int):
            return {"type": "integer"}

        elif isinstance(data, float):
            return {"type": "number"}

        else:
            return {"type": "null"}