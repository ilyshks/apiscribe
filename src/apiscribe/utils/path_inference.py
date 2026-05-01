import re

INT_RE = re.compile(r"^\d+$")
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def infer_path_template(paths: list[str]):
    # Пустой список — возвращаем корневой путь и пустые параметры
    if not paths:
        return "/", []

    split_paths = [p.strip("/").split("/") for p in paths]
    max_len = max(len(p) for p in split_paths)

    template = []
    parameters = []

    for i in range(max_len):
        column = [p[i] for p in split_paths if i < len(p)]
        if not column:
            continue

        unique = set(column)

        # Случай 1: все сегменты одинаковые → константа
        if len(unique) == 1:
            template.append(column[0])
            continue

        all_int = all(INT_RE.match(v) for v in column)
        all_uuid = all(UUID_RE.match(v) for v in column)

        # Случай 2: все целые числа → параметр {prev}_id
        if all_int:
            prev = template[-1] if template else "param"
            name = f"{prev}_id"
            schema = {"type": "integer"}
            template.append(f"{{{name}}}")
            parameters.append({
                "name": name,
                "in": "path",
                "required": True,
                "schema": schema
            })
            continue

        # Случай 3: все UUID → параметр {prev}_uuid
        if all_uuid:
            prev = template[-1] if template else "param"
            name = f"{prev}_uuid"
            schema = {"type": "string", "format": "uuid"}
            template.append(f"{{{name}}}")
            parameters.append({
                "name": name,
                "in": "path",
                "required": True,
                "schema": schema
            })
            continue

        # Случай 4: мало уникальных значений (≤3) и все они — обычные строки
        # (не числа и не UUID). Тогда считаем их реальными endpoint‑константами
        all_strings = not any(INT_RE.match(v) or UUID_RE.match(v) for v in column)
        if len(unique) <= 3 and all_strings:
            template.append(column[0])   # берём первое значение как константу
            continue

        # Случай 5: всё остальное → строковый параметр
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