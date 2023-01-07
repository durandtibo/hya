import hashlib
import logging
import math
from typing import Any, Union

from bearface.registry import registry

logger = logging.getLogger(__name__)


@registry.register("bf.add")
def add_resolver(*args: Any) -> Any:
    r"""Implements a resolver to add objects.

    Args:
        *args: Specifies the values to add.

    Returns:
        ``arg1 + arg2 + arg3 + ... + argN``
    """
    output = args[0]
    for arg in args[1:]:
        output += arg
    return output


@registry.register("bf.floordiv")
def floordiv_resolver(dividend: Union[int, float], divisor: Union[int, float]) -> int:
    r"""Implements a resolver to compute the floor division of two numbers.

    Args:
        dividend (int or float): The dividend.
        divisor (int or float): The divisor.

    Returns:
        int: ``dividend // divisor``
    """
    return dividend // divisor


@registry.register("bf.neg")
def neg_resolver(number: Union[int, float]) -> Union[int, float]:
    r"""Implements a resolver to compute the negation (``-number``).

    Args:
        number (int or float): Specifies the number.

    Returns:
        int or float: The negated input number.
    """
    return -number


@registry.register("bf.mul")
def mul_resolver(*args: Any) -> Any:
    r"""Implements a resolver to multiply objects.

    Args:
        *args: Specifies the values to multiply.

    Returns:
        ``arg1 * arg2 * arg3 * ... * argN``
    """
    output = args[0]
    for arg in args[1:]:
        output *= arg
    return output


@registry.register("bf.pow")
def pow_resolver(value: Union[float, int], exponent: Union[float, int]) -> Union[float, int]:
    r"""Implements a resolver to compute a value to a given power.

    Args:
        value (int or float): The value or base.
        exponent (int or float): The exponent.

    Returns:
        ``x ** y``
    """
    return value**exponent


@registry.register("bf.sqrt")
def sqrt_resolver(number: Union[int, float]) -> float:
    r"""Implements a resolver to compute the square root of a number.

    Args:
        number (int or float): Specifies the number to compute the
            square root.

    Returns:
        float: The square root of the input number.
    """
    return math.sqrt(number)


@registry.register("bf.sha1")
def sha1_resolver(obj: Any) -> str:
    r"""Implements a resolver to compute the SHA-1 hash of an object.

    Args:
        obj: Specifies the object to compute the SHA-1 hash.

    Returns:
        str: The SHA-1 hash of the object.
    """
    return hashlib.sha1(bytes(str(obj), "utf-8")).hexdigest()


@registry.register("bf.sha256")
def sha256_resolver(obj: Any) -> str:
    r"""Implements a resolver to compute the SHA-256 hash of an object.

    Args:
        obj: Specifies the object to compute the SHA-256 hash.

    Returns:
        str: The SHA-256 hash of the object.
    """
    return hashlib.sha256(bytes(str(obj), "utf-8")).hexdigest()


@registry.register("bf.sub")
def sub_resolver(object1: Any, object2: Any) -> Any:
    r"""Implements a resolver to subtract two objects.

    Args:
        object1: The first object.
        object2: The second object.

    Returns:
        ``object1 - object2``
    """
    return object1 - object2


@registry.register("bf.truediv")
def truediv_resolver(dividend: Union[int, float], divisor: Union[int, float]) -> Union[int, float]:
    r"""Implements a resolver to compute the true division of two numbers.

    Args:
        dividend (int or float): The dividend.
        divisor (int or float): The divisor.

    Returns:
        ``dividend / divisor``
    """
    return dividend / divisor
