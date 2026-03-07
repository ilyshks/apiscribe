import re

INT_RE = re.compile(r"^\d+$")
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def infer_path_template(paths: list[str]):

    split_paths = [p.strip("/").split("/") for p in paths]

    max_len = max(len(p) for p in split_paths)

    template = []
    parameters = []

    for i in range(max_len):

        column = []

        for p in split_paths:
            if i < len(p):
                column.append(p[i])

        unique = set(column)

        if len(unique) == 1:
            template.append(column[0])
            continue

        if all(INT_RE.match(v) for v in column):

            prev = template[-1] if template else "param"
            name = f"{prev}_id"

            schema = {"type": "integer"}

        elif all(UUID_RE.match(v) for v in column):

            prev = template[-1] if template else "param"
            name = f"{prev}_uuid"

            schema = {"type": "string", "format": "uuid"}

        else:

            prev = template[-1] if template else "param"
            name = f"{prev}_param"

            schema = {"type": "string"}

        template.append(f"{{{name}}}")

        parameters.append({
            "name": name,
            "in": "path",
            "required": True,
            "schema": schema
        })

    normalized = "/" + "/".join(template)

    return normalized, parameters