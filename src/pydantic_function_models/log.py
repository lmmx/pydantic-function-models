from sys import stderr

__all__ = ["err"]


def err(*msg) -> None:
    print(*msg, file=stderr)
