def merge_schema(a: dict | None, b: dict | None) -> dict | None:

    if not a:
        return b

    if not b:
        return a

    if a == b:
        return a

    type_a = a.get("type")
    type_b = b.get("type")

    # different types
    if type_a != type_b:

        types = collect_types(type_a) | collect_types(type_b)

        types = normalize_types(types)

        return {
            "type": sorted(types)
        }

    t = type_a

    if t == "object":
        return merge_object(a, b)

    if t == "array":
        return merge_array(a, b)

    # primitives → keep original
    return a


def collect_types(t):

    if not t:
        return set()

    if isinstance(t, list):
        return set(t)

    return {t}


def normalize_types(types):

    types = set(types)

    # integer + number -> number
    if "number" in types and "integer" in types:
        types.remove("integer")

    return types


def merge_object(a, b):

    props_a = a.get("properties", {})
    props_b = b.get("properties", {})

    merged = {}

    keys = set(props_a) | set(props_b)

    for key in keys:

        merged[key] = merge_schema(
            props_a.get(key),
            props_b.get(key)
        )

    result = {
        "type": "object",
        "properties": merged
    }

    # merge additionalProperties if present
    if "additionalProperties" in a or "additionalProperties" in b:

        result["additionalProperties"] = merge_schema(
            a.get("additionalProperties"),
            b.get("additionalProperties"),
        )

    return result


def merge_array(a, b):

    return {
        "type": "array",
        "items": merge_schema(
            a.get("items"),
            b.get("items")
        )
    }