from __future__ import annotations

__all__ = ["is_torch_available"]

from importlib.util import find_spec


def is_torch_available() -> bool:
    r"""Indicates if the torch package is installed or not.

    Returns:
    -------
        bool: ``True`` if ``torch`` is installed, otherwise ``False``.

    Example usage:

    .. code-block:: pycon

        >>> from hya.imports import is_torch_available
        >>> is_torch_available()
    """
    return find_spec("torch") is not None
