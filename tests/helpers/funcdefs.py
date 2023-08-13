__all__ = ["add", "reserved_params"]


def add(a: int, b: int) -> int:
    return a + b


def reserved_params(v__args: list[str], v__kwargs: dict) -> str:
    return "You'll never get away with this!"
