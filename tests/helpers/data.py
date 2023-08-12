__all__ = ["add_json_schema"]

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
        "kwargs": {"default": None, "title": "Kwargs", "type": "object"},
    },
    "required": ["a", "b"],
    "title": "Add",
    "type": "object",
}
