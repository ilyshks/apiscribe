import json
import yaml


class Exporter:
    def to_json(self, spec: dict, filename: str):
        with open(filename, "w") as f:
            json.dump(spec, f, indent=2)

    def to_yaml(self, spec: dict, filename: str):
        with open(filename, "w") as f:
            yaml.dump(spec, f)
