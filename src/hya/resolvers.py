r"""Implement some resolvers using features from standard libraries."""

from __future__ import annotations

__all__ = [
    "add_resolver",
    "ceildiv_resolver",
    "iter_join_resolver",
    "mul_resolver",
    "path_resolver",
    "pi_resolver",
    "sha256_resolver",
]

import hashlib
import json
import logging
import math
import operator
import os
from enum import Enum
from functools import reduce
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlparse

from hya.utils.config import to_plain

if TYPE_CHECKING:
    from collections.abc import Iterable


logger: logging.Logger = logging.getLogger(__name__)


def add_resolver(first: Any, *others: Any) -> Any:
    r"""Return the addition of several objects.

    The arguments are not modified: ``first`` is never extended in place,
    so interpolating a list of the configuration does not change it.

    Args:
        first: The first value to add.
        *others: The other values to add.

    Returns:
        ``first + other1 + other2 + ... + otherN``

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
        >>> conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x},[3]}"})
        >>> conf.key
        [1, 2, 3]
        >>> conf.x
        [1, 2]

        ```
    """
    return reduce(operator.add, others, first)


def ceildiv_resolver(dividend: float, divisor: float) -> float:
    r"""Compute the ceiling division of two numbers.

    Ceiling division rounds the result up, which is useful for
    calculating the minimum number of chunks needed to accommodate a
    given total. The type of the result follows ``//``: an ``int`` for
    two integers (exact, whatever their size) and a ``float`` if one of
    them is a float (``11.0, 4`` gives ``3.0``).

    Args:
        dividend: The dividend (numerator).
        divisor: The divisor (denominator).

    Returns:
        The ceiling of dividend / divisor, computed as
        ``-(dividend // -divisor)``.

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
        >>> # The type of the result follows ``//``
        >>> OmegaConf.create({"key": "${hya.ceildiv:11.0,4}"}).key
        3.0

        ```
    """
    return -(dividend // -divisor)


def iter_join_resolver(iterable: Iterable[Any], separator: str) -> str:
    r"""Convert all items in an iterable to strings and join them.

    This resolver takes an iterable (e.g., list, tuple) and concatenates
    all elements into a single string, separated by the specified separator.
    The configuration nodes of the iterable are resolved first, at any
    depth. Each element is then converted to a string using str(), so a
    nested list is written as a Python list.

    Args:
        iterable: Any iterable object where all the returned values
            are strings or can be converted to string. Common examples
            include lists, tuples, or OmegaConf ListConfig objects.
        separator: The separator string to use between the items.
            Can be any string including empty string, space, comma, etc.

    Returns:
        A single string with all iterable elements joined by the separator.

    Raises:
        omegaconf.errors.MissingMandatoryValue: If a node contains a
            missing value (``???``).

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
        >>> # The interpolations of nested values are resolved
        >>> conf = OmegaConf.create(
        ...     {"a": 1, "x": [["${a}"], 2], "key": "${hya.iter_join:${x},-}"}
        ... )
        >>> conf.key
        [1]-2

        ```
    """
    return separator.join(map(str, to_plain(iterable)))


def mul_resolver(first: Any, *others: Any) -> Any:
    r"""Return the multiplication of several objects.

    The arguments are not modified. The values are meant to be numbers: the
    repetition of a list of the configuration (``[1, 2] * 2``) is not
    supported.

    Args:
        first: The first value to multiply.
        *others: The other values to multiply.

    Returns:
        ``first * other1 * other2 * ... * otherN``

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
    return reduce(operator.mul, others, first)


def path_resolver(path: str | os.PathLike[str]) -> Path:
    r"""Return a resolved path object from a path or a file URL.

    This resolver converts a string, or any path-like object (for example
    a ``pathlib.Path`` stored in the configuration), to a ``pathlib.Path``
    object: it expands the user home directory (``~``) and resolves the
    path to an absolute path. A string that starts with ``file:`` (the
    scheme is case-insensitive) is read as a file URL: the path of the URL
    is used, with its percent-encoding (for example ``%20`` for a space)
    decoded. In a URL, ``?`` and ``#`` start a query and a fragment, so a
    file name that contains them is written ``%3F`` and ``%23``. Any
    other string is a plain path, written as is: ``?``, ``#`` and ``%``
    are not interpreted.

    Args:
        path: The target path as a string or a path-like object, or a
            ``file:`` URL.

    Returns:
        A fully resolved ``pathlib.Path`` object with expanded user
        directory and converted to absolute path.

    Raises:
        ValueError: If a ``file:`` URL has a host other than ``localhost``
            (for example ``file://host/a``), a query or a fragment (any
            ``?`` or ``#``, for example ``file:///data/run#1``): they
            would be dropped silently.

    Note:
        Within an OmegaConf interpolation, a path with a tilde (~)
        must be quoted (``${hya.path:"~/data"}``); unquoted, the
        interpolation is a grammar error.

    Example:
        ```pycon
        >>> from pathlib import Path
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.path:/my/path}"})
        >>> conf.key
        PosixPath('/my/path')
        >>> conf = OmegaConf.create({"key": "${hya.path:file:///my/path%20to}"})
        >>> conf.key
        PosixPath('/my/path to')
        >>> conf = OmegaConf.create({"key": '${hya.path:"~/my/path"}'})
        >>> conf.key == Path("~/my/path").expanduser().resolve()
        True
        >>> conf = OmegaConf.create({"key": "${hya.path:${hya.path:/my/path}}"})
        >>> conf.key
        PosixPath('/my/path')

        ```
    """
    path = os.fspath(path)
    url = urlparse(path)
    if url.scheme == "file":
        # The characters are checked: ``url.query`` and ``url.fragment`` are empty for a
        # trailing "?" or "#", which would be dropped too
        if url.netloc not in ("", "localhost") or "?" in path or "#" in path:
            msg = f"A file URL with a host, a query or a fragment is not supported: '{path}'"
            raise ValueError(msg)
        path = unquote(url.path)
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


def sha256_resolver(obj: Any) -> str:
    r"""Compute the SHA-256 hash of the whole content of an object.

    The configuration nodes of the object are resolved first, at any
    depth. A string is then hashed as is, so the result is the SHA-256
    of the text, the same as other tools give. Any other value is
    hashed from its canonical JSON form: sorted keys, no space
    (``[1,2]``, ``{"a":1,"b":2}``, ``true``, ``null``) and non-ASCII
    characters escaped (``\u00e9`` for an ``e`` with an acute accent).
    In this form, a path or an enum is written as its string, except an
    enum that is also an ``int``, a ``float`` or a ``str`` (for example
    an ``IntEnum``), which is written as its value. Useful for
    generating consistent identifiers or cache keys from configuration
    values.

    The hash does not keep the type of a value: the string ``[1]`` and
    the list ``[1]`` have the same hash, and so do an integer key and
    the same string key.

    Args:
        obj: The object to compute the SHA-256 hash: a string, or a
            value with a JSON form (numbers, booleans, ``None``, lists,
            tuples, dictionaries, ``ListConfig``, ``DictConfig``,
            paths and enums).

    Returns:
        The SHA-256 hash as a hexadecimal string (64 characters).

    Raises:
        TypeError: If a value has no JSON form (for example an array, a
            tensor, a data type, a set or bytes), if a key of a mapping
            is not a string, a number, a boolean or ``None``, or if a
            mapping mixes key types that cannot be sorted.
        ValueError: If a value or a key is a non-finite float (``nan``
            or ``inf``), which has no JSON form.
        omegaconf.errors.MissingMandatoryValue: If a node contains a
            missing value (``???``).

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.sha256:mystring}"})
        >>> conf.key
        bd3ff47540b31e62d4ca6b07794e5a886b0f655fc322730f26ecd65cc7dd5c90
        >>> # Useful for generating consistent IDs
        >>> conf = OmegaConf.create({"id": "${hya.sha256:experiment_v1}"})
        >>> # The order of the keys does not change the hash
        >>> conf = OmegaConf.create(
        ...     {
        ...         "x": {"a": 1, "b": 2},
        ...         "y": {"b": 2, "a": 1},
        ...         "hx": "${hya.sha256:${x}}",
        ...         "hy": "${hya.sha256:${y}}",
        ...     }
        ... )
        >>> conf.hx == conf.hy
        True

        ```
    """
    value = to_plain(obj)
    if not isinstance(value, str):
        value = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=_encode_value
        )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _encode_value(value: object) -> str:
    r"""Encode a value that JSON does not support.

    It is the ``default`` function that ``sha256_resolver`` gives to
    ``json.dumps``.

    Args:
        value: The value to encode.

    Returns:
        The string of a path or an enum.

    Raises:
        TypeError: If the value is not a path or an enum.

    Example:
        ```pycon
        >>> from pathlib import PurePosixPath
        >>> from hya.resolvers import _encode_value
        >>> _encode_value(PurePosixPath("/my/path"))
        '/my/path'

        ```
    """
    if isinstance(value, (PurePath, Enum)):
        return str(value)
    msg = f"hya.sha256 cannot hash a value of type {type(value).__name__}"
    raise TypeError(msg)
