import typing

__all__ = ["add_json_schema", "add_fields"]

add_json_schema = {
    "properties": {
        "a": {"title": "A", "type": "integer"},
        "v__duplicate_kwargs": {
            "default": None,
            "items": {"type": "string"},
            "title": "V  Duplicate Kwargs",
            "type": "array",
        },
        "b": {"title": "B", "type": "integer"},
        "args": {"default": None, "items": {}, "title": "Args", "type": "array"},
        "kwargs": {
            "additionalProperties": True,
            "default": None,
            "title": "Kwargs",
            "type": "object",
        },
    },
    "required": ["a", "b"],
    "title": "Add",
    "type": "object",
}

add_fields = {
    "a": (int, ...),
    "args": (list[typing.Any], None),
    "b": (int, ...),
    "kwargs": (dict[typing.Any, typing.Any], None),
    "v__duplicate_kwargs": (list[str], None),
}
