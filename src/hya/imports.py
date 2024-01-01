r"""Implement some utility functions to manage optional dependencies."""

from __future__ import annotations

__all__ = [
    "check_torch",
    "is_torch_available",
]

from importlib.util import find_spec


def check_braceexpand() -> None:
    r"""Check if the ``braceexpand`` package is installed.

    Raises:
        RuntimeError: if the ``braceexpand`` package is not installed.

    Example usage:

    ```pycon
    >>> from hya.imports import check_braceexpand
    >>> check_braceexpand()

    ```
    """
    if not is_braceexpand_available():
        msg = (
            "`braceexpand` package is required but not installed. "
            "You can install `braceexpand` package with the command:\n\n"
            "pip install braceexpand\n"
        )
        raise RuntimeError(msg)


def is_braceexpand_available() -> bool:
    r"""Indicate if the braceexpand package is installed or not.

    Returns:
        ``True`` if ``braceexpand`` is installed, otherwise ``False``.

    Example usage:

    ```pycon
    >>> from hya.imports import is_braceexpand_available
    >>> is_braceexpand_available()

    ```
    """
    return find_spec("braceexpand") is not None


def check_torch() -> None:
    r"""Check if the ``torch`` package is installed.

    Raises:
        RuntimeError: if the ``torch`` package is not installed.

    Example usage:

    ```pycon
    >>> from hya.imports import check_torch
    >>> check_torch()

    ```
    """
    if not is_torch_available():
        msg = (
            "`torch` package is required but not installed. "
            "You can install `torch` package with the command:\n\n"
            "pip install torch\n"
        )
        raise RuntimeError(msg)


def is_torch_available() -> bool:
    r"""Indicate if the torch package is installed or not.

    Returns:
        ``True`` if ``torch`` is installed, otherwise ``False``.

    Example usage:

    ```pycon
    >>> from hya.imports import is_torch_available
    >>> is_torch_available()

    ```
    """
    return find_spec("torch") is not None
