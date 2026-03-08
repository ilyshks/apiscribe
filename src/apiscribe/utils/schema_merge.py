def merge_schema(a: dict | None, b: dict | None) -> dict | None:

    if not a:
        return b

    if not b:
        return a

    if a.get("type") != b.get("type"):
        return {
            "oneOf": [a, b]
        }

    t = a.get("type")

    if t == "object":
        return merge_object(a, b)

    if t == "array":
        return merge_array(a, b)

    return a


def merge_object(a, b):

    props_a = a.get("properties", {})
    props_b = b.get("properties", {})

    merged = {}

    for key in set(props_a) | set(props_b):

        merged[key] = merge_schema(
            props_a.get(key),
            props_b.get(key)
        )

    return {
        "type": "object",
        "properties": merged
    }


def merge_array(a, b):

    return {
        "type": "array",
        "items": merge_schema(
            a.get("items"),
            b.get("items")
        )
    }