from collections import defaultdict
from apiscribe.utils.path_inference import infer_path_template
from apiscribe.utils.path_cluster import cluster_paths


class OpenAPIGenerator:

    def generate(self, endpoints):

        paths = {}

        paths_by_method = defaultdict(list)
        endpoint_map = {}

        # группируем endpoints по методу
        for ep in endpoints:
            paths_by_method[ep.method].append(ep.path)
            endpoint_map[(ep.method, ep.path)] = ep

        for method, path_list in paths_by_method.items():

            clusters = cluster_paths(path_list)

            for cluster in clusters:

                normalized_path, params = infer_path_template(cluster)

                example_ep = endpoint_map[(method, cluster[0])]

                paths[normalized_path] = {
                    method.lower(): {
                        "parameters": params,
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": example_ep.request_schema
                                }
                            }
                        } if example_ep.request_schema else {},
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": example_ep.response_schema
                                    }
                                },
                            }
                        },
                    }
                }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
            },
            "paths": paths,
        }
    