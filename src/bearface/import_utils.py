__all__ = ["is_torch_available"]

from importlib.util import find_spec


def is_torch_available() -> bool:
    r"""Indicates if the torch package is installed or not."""
    return find_spec("torch") is not None
