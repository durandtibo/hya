r"""Implement some utility functions to manage optional dependencies.

For each optional package (``braceexpand``, ``numpy`` and ``torch``),
``is_<package>_available`` indicates whether the package is installed,
without importing it, and ``validate_<package>`` raises a
``RuntimeError`` that says how to install it when it is missing.
"""

from __future__ import annotations

__all__ = [
    "is_braceexpand_available",
    "is_numpy_available",
    "is_torch_available",
    "validate_braceexpand",
    "validate_numpy",
    "validate_torch",
]

from importlib.util import find_spec

#######################
#     braceexpand     #
#######################


def validate_braceexpand() -> None:
    r"""Check if the ``braceexpand`` package is installed.

    Raises:
        RuntimeError: if the ``braceexpand`` package is not installed.

    Example:
        ```pycon
        >>> from hya.imports import validate_braceexpand
        >>> validate_braceexpand()

        ```
    """
    if not is_braceexpand_available():
        msg = (
            "'braceexpand' package is required but not installed. "
            "You can install `braceexpand` package with the command:\n\n"
            "pip install braceexpand\n"
        )
        raise RuntimeError(msg)


def is_braceexpand_available() -> bool:
    r"""Indicate if the braceexpand package is installed or not.

    Returns:
        ``True`` if ``braceexpand`` is installed, otherwise ``False``.

    Example:
        ```pycon
        >>> from hya.imports import is_braceexpand_available
        >>> is_braceexpand_available()

        ```
    """
    return find_spec("braceexpand") is not None


#################
#     numpy     #
#################


def validate_numpy() -> None:
    r"""Check if the ``numpy`` package is installed.

    Raises:
        RuntimeError: if the ``numpy`` package is not installed.

    Example:
        ```pycon
        >>> from hya.imports import validate_numpy
        >>> validate_numpy()

        ```
    """
    if not is_numpy_available():
        msg = (
            "'numpy' package is required but not installed. "
            "You can install `numpy` package with the command:\n\n"
            "pip install numpy\n"
        )
        raise RuntimeError(msg)


def is_numpy_available() -> bool:
    r"""Indicate if the numpy package is installed or not.

    Returns:
        ``True`` if ``numpy`` is installed, otherwise ``False``.

    Example:
        ```pycon
        >>> from hya.imports import is_numpy_available
        >>> is_numpy_available()

        ```
    """
    return find_spec("numpy") is not None


#################
#     torch     #
#################


def validate_torch() -> None:
    r"""Check if the ``torch`` package is installed.

    Raises:
        RuntimeError: if the ``torch`` package is not installed.

    Example:
        ```pycon
        >>> from hya.imports import validate_torch
        >>> validate_torch()

        ```
    """
    if not is_torch_available():
        msg = (
            "'torch' package is required but not installed. "
            "You can install `torch` package with the command:\n\n"
            "pip install torch\n"
        )
        raise RuntimeError(msg)


def is_torch_available() -> bool:
    r"""Indicate if the torch package is installed or not.

    Returns:
        ``True`` if ``torch`` is installed, otherwise ``False``.

    Example:
        ```pycon
        >>> from hya.imports import is_torch_available
        >>> is_torch_available()

        ```
    """
    return find_spec("torch") is not None
