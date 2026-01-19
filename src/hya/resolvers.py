r"""Implement some resolvers using features from standard libraries."""

from __future__ import annotations

import hashlib
import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlparse

if TYPE_CHECKING:
    from collections.abc import Iterable


logger: logging.Logger = logging.getLogger(__name__)


def add_resolver(*args: Any) -> Any:
    r"""Return the addition of several objects.

    Args:
        *args: The values to add.

    Returns:
        ``arg1 + arg2 + arg3 + ... + argN``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.add:1,2}"})
        >>> conf.key
        3
        >>> conf = OmegaConf.create({"key": "${hya.add:1,2,3,4}"})
        >>> conf.key
        10

        ```
    """
    output = args[0]
    for arg in args[1:]:
        output += arg
    return output


def asinh_resolver(number: float) -> float:
    r"""Return the inverse hyperbolic sine.

    Args:
        number: The number to transform.

    Returns:
        The inverse hyperbolic sine of the input number.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.asinh:1}"})
        >>> conf.key
        0.881373...

        ```
    """
    return math.asinh(number)


def ceildiv_resolver(dividend: float, divisor: float) -> float:
    r"""Compute the ceiling division of two numbers.

    Ceiling division rounds the result up to the nearest integer,
    which is useful for calculating the minimum number of chunks
    needed to accommodate a given total.

    Args:
        dividend: The dividend (numerator).
        divisor: The divisor (denominator).

    Returns:
        The ceiling of dividend / divisor. Equivalent to
        math.ceil(dividend / divisor).

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.ceildiv:11,4}"})
        >>> conf.key
        3
        >>> # Useful for calculating number of batches
        >>> conf = OmegaConf.create({"batches": "${hya.ceildiv:100,32}"})
        >>> conf.batches
        4

        ```
    """
    return -(dividend // -divisor)


def exp_resolver(number: float) -> float:
    r"""Return the exponential value of the input.

    Args:
        number: The number to transform.

    Returns:
        The exponential value of the input.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.exp:0}"})
        >>> conf.key
        1.0

        ```
    """
    return math.exp(number)


def floordiv_resolver(dividend: float, divisor: float) -> float:
    r"""Compute the floor division of two numbers.

    Floor division rounds the result down to the nearest integer,
    equivalent to the // operator in Python.

    Args:
        dividend: The dividend (numerator).
        divisor: The divisor (denominator).

    Returns:
        The floor of dividend / divisor, i.e., ``dividend // divisor``.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.floordiv:11,4}"})
        >>> conf.key
        2
        >>> conf = OmegaConf.create({"key": "${hya.floordiv:10,3}"})
        >>> conf.key
        3

        ```
    """
    return dividend // divisor


def len_resolver(obj: Any) -> int:
    r"""Return the length of an object.

    Args:
        obj: The object.

    Returns:
        The length of the object.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.len:[1,2,3]}"})
        >>> conf.key
        3

        ```
    """
    return len(obj)


def iter_join_resolver(iterable: Iterable[Any], separator: str) -> str:
    r"""Convert all items in an iterable to strings and join them.

    This resolver takes an iterable (e.g., list, tuple) and concatenates
    all elements into a single string, separated by the specified separator.
    Each element is converted to a string using str().

    Args:
        iterable: Any iterable object where all the returned values
            are strings or can be converted to string. Common examples
            include lists, tuples, or OmegaConf ListConfig objects.
        separator: The separator string to use between the items.
            Can be any string including empty string, space, comma, etc.

    Returns:
        A single string with all iterable elements joined by the separator.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.iter_join:[abc,2,def],-}"})
        >>> conf.key
        abc-2-def
        >>> conf = OmegaConf.create({"path": "${hya.iter_join:[data,models,v1],/}"})
        >>> conf.path
        data/models/v1

        ```
    """
    return separator.join(map(str, iterable))


def log_resolver(number: float, base: float = math.e) -> float:
    r"""Compute logarithm of the input value to the given base.

    Args:
        number: The number to transform.
        base: The base.

    Returns:
        The logarithm of the input value to the given base.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.log:1}"})
        >>> conf.key
        0.0

        ```
    """
    return math.log(number, base)


def log10_resolver(number: float) -> float:
    r"""Compute base 10 logarithm of the input value.

    Args:
        number: The number to transform.

    Returns:
        The base 10 logarithm of the input value.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.log10:1}"})
        >>> conf.key
        0.0

        ```
    """
    return math.log10(number)


def max_resolver(*args: Any) -> Any:
    r"""Return the maximum between multiple values.

    Args:
        *args: The values.

    Returns:
        ``max(arg1, arg2, arg3, ..., argN)``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.max:1,2,3}"})
        >>> conf.key
        3

        ```
    """
    return max(*args)


def min_resolver(*args: Any) -> Any:
    r"""Return the minimum between multiple values.

    Args:
        *args: The values.

    Returns:
        ``min(arg1, arg2, arg3, ..., argN)``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.min:1,2,3}"})
        >>> conf.key
        1

        ```
    """
    return min(*args)


def mul_resolver(*args: Any) -> Any:
    r"""Return the multiplication of several objects.

    Args:
        *args: The values to multiply.

    Returns:
        ``arg1 * arg2 * arg3 * ... * argN``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.mul:1,2}"})
        >>> conf.key
        2
        >>> conf = OmegaConf.create({"key": "${hya.mul:1,2,3}"})
        >>> conf.key
        6

        ```
    """
    output = args[0]
    for arg in args[1:]:
        output *= arg
    return output


def neg_resolver(number: float) -> float:
    r"""Return the negation (``-number``).

    Args:
        number: The number to transform.

    Returns:
        The negated input number.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.neg:1}"})
        >>> conf.key
        -1

        ```
    """
    return -number


def path_resolver(path: str) -> Path:
    r"""Return a resolved path object from a string path.

    This resolver converts a string path to a pathlib.Path object,
    expanding user home directory references (~) and resolving to
    an absolute path.

    Args:
        path: The target path as a string. Supports tilde (~) for
            home directory expansion.

    Returns:
        A fully resolved pathlib.Path object with expanded user
        directory and converted to absolute path.

    Note:
        The tilde (~) expansion works when the path is passed as
        a regular string, but may not work correctly when used
        within OmegaConf interpolation syntax due to grammar
        restrictions. For paths with tilde, consider using
        direct Python code or configuration string values.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.path:/my/path}"})
        >>> conf.key
        PosixPath('/my/path')

        ```
    """
    return Path(path).expanduser().resolve()


def pi_resolver() -> float:
    r"""Return the value PI.

    Returns:
        The value of PI.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.pi:}"})
        >>> conf.key
        3.14159...

        ```
    """
    return math.pi


def pow_resolver(value: float, exponent: float) -> float:
    r"""Return a value to a given power.

    Args:
        value: The value or base.
        exponent: The exponent.

    Returns:
        ``x ** y``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.pow:2,3}"})
        >>> conf.key
        8

        ```
    """
    return value**exponent


def sqrt_resolver(number: float) -> float:
    r"""Return the square root of a number.

    Args:
        number: The number to compute the
            square root.

    Returns:
        The square root of the input number.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.sqrt:4}"})
        >>> conf.key
        2.0

        ```
    """
    return math.sqrt(number)


def sha256_resolver(obj: Any) -> str:
    r"""Compute the SHA-256 hash of an input object.

    This resolver converts the object to a string representation and
    computes its SHA-256 hash. Useful for generating consistent identifiers
    or cache keys from configuration values.

    Args:
        obj: The object to compute the SHA-256 hash. The object will
            be converted to a string using str() before hashing.

    Returns:
        The SHA-256 hash as a hexadecimal string (64 characters).

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.sha256:mystring}"})
        >>> conf.key
        bd3ff47540b31e62d4ca6b07794e5a886b0f655fc322730f26ecd65cc7dd5c90
        >>> # Useful for generating consistent IDs
        >>> conf = OmegaConf.create({"id": "${hya.sha256:experiment_v1}"})

        ```
    """
    return hashlib.sha256(bytes(str(obj), "utf-8")).hexdigest()


def sinh_resolver(number: float) -> float:
    r"""Return the hyperbolic sine.

    Args:
        number: The number to transform.

    Returns:
        The hyperbolic sine of the input number.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.sinh:1}"})
        >>> conf.key
        1.175201...

        ```
    """
    return math.sinh(number)


def sub_resolver(object1: Any, object2: Any) -> Any:
    r"""Return the subtraction of two objects.

    Args:
        object1: The first object.
        object2: The second object.

    Returns:
        ``object1 - object2``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.sub:3,1}"})
        >>> conf.key
        2

        ```
    """
    return object1 - object2


def to_path_resolver(path: str) -> Path:
    r"""Convert a path string (including URLs) into a ``pathlib.Path``.

    This resolver handles both regular file paths and file:// URLs,
    converting them to pathlib.Path objects. It also expands user
    home directory references and resolves to absolute paths.

    Args:
        path: The path to convert. Can be a regular file path or
            a file:// URL. URL encoding (e.g., %20 for spaces) is
            automatically decoded. Supports tilde (~) for home
            directory expansion.

    Returns:
        A fully resolved pathlib.Path object with URL decoding,
        expanded user directory, and converted to absolute path.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.to_path:/my/path}"})
        >>> conf.key
        PosixPath('/my/path')
        >>> conf = OmegaConf.create({"key": "${hya.to_path:file:///my/path}"})
        >>> conf.key
        PosixPath('/my/path')

        ```
    """
    return Path(unquote(urlparse(path).path)).expanduser().resolve()


def truediv_resolver(dividend: float, divisor: float) -> float:
    r"""Return the true division of two numbers.

    Args:
        dividend: The dividend.
        divisor: The divisor.

    Returns:
        ``dividend / divisor``

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.truediv:1,2}"})
        >>> conf.key
        0.5

        ```
    """
    return dividend / divisor
