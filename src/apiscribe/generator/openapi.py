from collections import defaultdict
import copy

from apiscribe.utils.path_inference import infer_path_template
from apiscribe.utils.path_cluster import cluster_paths


class OpenAPIGenerator:

    def generate(self, endpoints):

        paths = {}

        paths_by_method = defaultdict(list)
        endpoint_map = {}

        for ep in endpoints:
            paths_by_method[ep.method].append(ep.path)
            endpoint_map[(ep.method, ep.path)] = ep

        for method, path_list in paths_by_method.items():

            clusters = cluster_paths(path_list)

            for cluster in clusters:

                normalized_path, params = infer_path_template(cluster)

                example_ep = endpoint_map[(method, cluster[0])]

                req_schema = self.apply_required(
                    example_ep.request_schema,
                    getattr(example_ep, "request_field_counts", None),
                    getattr(example_ep, "request_count", 0),
                )

                responses = {}

                for status, schema in example_ep.responses.items():

                    responses[str(status)] = {
                        "description": f"HTTP {status}",
                        "content": {
                            "application/json": {
                                "schema": schema
                            }
                        },
                    }

                if normalized_path not in paths:
                    paths[normalized_path] = {}

                operation = {
                    "parameters": params,
                    "responses": responses,
                }

                if req_schema:
                    operation["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": req_schema
                            }
                        }
                    }

                paths[normalized_path][method.lower()] = operation

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
            },
            "paths": paths,
        }

    def apply_required(self, schema: dict, field_counts: dict, total: int):

        if not schema:
            return schema

        if not field_counts:
            return schema

        if schema.get("type") != "object":
            return schema

        schema = copy.deepcopy(schema)

        required = []

        for field, count in field_counts.items():

            if count == total:
                required.append(field)

        if required:
            schema["required"] = required

        return schema