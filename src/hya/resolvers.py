from __future__ import annotations

import hashlib
import logging
import math
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from hya.registry import registry

logger = logging.getLogger(__name__)


@registry.register("hya.add")
def add_resolver(*args: Any) -> Any:
    r"""Implements a resolver to add objects.

    Args:
    ----
        *args: Specifies the values to add.

    Returns:
    -------
        ``arg1 + arg2 + arg3 + ... + argN``
    """
    output = args[0]
    for arg in args[1:]:
        output += arg
    return output


@registry.register("hya.asinh")
def asinh_resolver(number: int | float) -> float:
    r"""Implements a resolver to compute the inverse hyperbolic sine.

    Args:
    ----
        number (int or float): Specifies the number.

    Returns:
    -------
        float: The inverse hyperbolic sine of the input number.
    """
    return math.asinh(number)


@registry.register("hya.ceildiv")
def ceildiv_resolver(dividend: int | float, divisor: int | float) -> int:
    r"""Implements a resolver to compute the ceiling division of two
    numbers.

    Args:
    ----
        dividend (int or float): The dividend.
        divisor (int or float): The divisor.

    Returns:
    -------
        int: The output of the ceiling division.
    """
    return -(dividend // -divisor)


@registry.register("hya.exp")
def exp_resolver(number: int | float) -> float:
    r"""Implements a resolver to compute the exponential value of the
    input.

    Args:
    ----
        number (int or float): Specifies the number.

    Returns:
    -------
        float: The exponential value of the input.
    """
    return math.exp(number)


@registry.register("hya.floordiv")
def floordiv_resolver(dividend: int | float, divisor: int | float) -> int:
    r"""Implements a resolver to compute the floor division of two
    numbers.

    Args:
    ----
        dividend (int or float): The dividend.
        divisor (int or float): The divisor.

    Returns:
    -------
        int: ``dividend // divisor``
    """
    return dividend // divisor


@registry.register("hya.len")
def len_resolver(obj: Any) -> int:
    r"""Implements a resolver to compute the length of an object.

    Args:
    ----
        obj: Specifies the object.

    Returns:
    -------
        int: The length of the object.
    """
    return len(obj)


@registry.register("hya.log")
def log_resolver(number: int | float, base: float = math.e) -> float:
    r"""Implements a resolver to compute logarithm of the input value to
    the given base.

    Args:
    ----
        number (int or float): Specifies the number.
        base (float, optional): Specifies the base.
            Default: ``math.e``

    Returns:
    -------
        float: The logarithm of the input value to the given base.
    """
    return math.log(number, base)


@registry.register("hya.log10")
def log10_resolver(number: int | float) -> float:
    r"""Implements a resolver to compute base 10 logarithm of the input
    value.

    Args:
    ----
        number (int or float): Specifies the number.

    Returns:
    -------
        float: The base 10 logarithm of the input value.
    """
    return math.log10(number)


@registry.register("hya.max")
def max_resolver(*args: Any) -> Any:
    r"""Implements a resolver to compute the maximum between multiple
    values.

    Args:
    ----
        *args: Specifies the values.

    Returns:
    -------
        ``max(arg1, arg2, arg3, ..., argN)``
    """
    return max(*args)


@registry.register("hya.min")
def min_resolver(*args: Any) -> Any:
    r"""Implements a resolver to compute the minimum between multiple
    values.

    Args:
    ----
        *args: Specifies the values.

    Returns:
    -------
        ``min(arg1, arg2, arg3, ..., argN)``
    """
    return min(*args)


@registry.register("hya.mul")
def mul_resolver(*args: Any) -> Any:
    r"""Implements a resolver to multiply objects.

    Args:
    ----
        *args: Specifies the values to multiply.

    Returns:
    -------
        ``arg1 * arg2 * arg3 * ... * argN``
    """
    output = args[0]
    for arg in args[1:]:
        output *= arg
    return output


@registry.register("hya.neg")
def neg_resolver(number: int | float) -> int | float:
    r"""Implements a resolver to compute the negation (``-number``).

    Args:
    ----
        number (int or float): Specifies the number.

    Returns:
    -------
        int or float: The negated input number.
    """
    return -number


@registry.register("hya.path")
def path_resolver(path: str) -> Path:
    r"""Implements a resolver to return a path object.

    Args:
    ----
        path (str): Specifies the target path.

    Returns:
    -------
        ``pathlib.Path``: The path object.
    """
    return Path(path).expanduser().resolve()


@registry.register("hya.pi")
def pi_resolver() -> float:
    r"""Implements a resolver that returns the value PI.

    Returns:
    -------
        float: The value of PI.
    """
    return math.pi


@registry.register("hya.pow")
def pow_resolver(value: float | int, exponent: float | int) -> float | int:
    r"""Implements a resolver to compute a value to a given power.

    Args:
    ----
        value (int or float): The value or base.
        exponent (int or float): The exponent.

    Returns:
    -------
        ``x ** y``
    """
    return value**exponent


@registry.register("hya.sqrt")
def sqrt_resolver(number: int | float) -> float:
    r"""Implements a resolver to compute the square root of a number.

    Args:
    ----
        number (int or float): Specifies the number to compute the
            square root.

    Returns:
    -------
        float: The square root of the input number.
    """
    return math.sqrt(number)


@registry.register("hya.sha1")
def sha1_resolver(obj: Any) -> str:
    r"""Implements a resolver to compute the SHA-1 hash of an object.

    Args:
    ----
        obj: Specifies the object to compute the SHA-1 hash.

    Returns:
    -------
        str: The SHA-1 hash of the object.
    """
    return hashlib.sha1(bytes(str(obj), "utf-8")).hexdigest()


@registry.register("hya.sha256")
def sha256_resolver(obj: Any) -> str:
    r"""Implements a resolver to compute the SHA-256 hash of an object.

    Args:
    ----
        obj: Specifies the object to compute the SHA-256 hash.

    Returns:
    -------
        str: The SHA-256 hash of the object.
    """
    return hashlib.sha256(bytes(str(obj), "utf-8")).hexdigest()


@registry.register("hya.sinh")
def sinh_resolver(number: int | float) -> float:
    r"""Implements a resolver to compute the hyperbolic sine.

    Args:
    ----
        number (int or float): Specifies the number.

    Returns:
    -------
        float: The hyperbolic sine of the input number.
    """
    return math.sinh(number)


@registry.register("hya.sub")
def sub_resolver(object1: Any, object2: Any) -> Any:
    r"""Implements a resolver to subtract two objects.

    Args:
    ----
        object1: The first object.
        object2: The second object.

    Returns:
    -------
        ``object1 - object2``
    """
    return object1 - object2


@registry.register("hya.to_path")
def to_path_resolver(path: str) -> Path:
    r"""Implements a resolver to convert the input path to a
    ``pathlib.Path``.

    Args:
    ----
        path (str): Specifies the path to convert.
            This value should be compatible with ``pathlib.Path``.

    Returns:
    -------
        ``pathlib.Path``: The converted path.
    """
    return Path(unquote(urlparse(path).path)).expanduser().resolve()


@registry.register("hya.truediv")
def truediv_resolver(dividend: int | float, divisor: int | float) -> int | float:
    r"""Implements a resolver to compute the true division of two
    numbers.

    Args:
    ----
        dividend (int or float): The dividend.
        divisor (int or float): The divisor.

    Returns:
    -------
        ``dividend / divisor``
    """
    return dividend / divisor
