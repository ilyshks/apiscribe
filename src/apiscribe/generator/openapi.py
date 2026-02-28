class OpenAPIGenerator:
    def generate(self, endpoints):
        paths = {}

        for ep in endpoints:
            if ep.path not in paths:
                paths[ep.path] = {}

            paths[ep.path][ep.method.lower()] = {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": ep.request_schema
                        }
                    }
                } if ep.request_schema else {},
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": ep.response_schema
                            }
                        },
                    }
                },
            }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
            },
            "paths": paths,
        }
