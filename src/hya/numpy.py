r"""Implement NumPy resolvers for array creation and manipulation.

This module provides OmegaConf resolvers that use NumPy for array
operations, allowing users to create NumPy arrays directly from
configuration files. The ``numpy`` package is needed only when the
resolver is called.
"""

from __future__ import annotations

__all__ = ["to_array_resolver"]

from typing import TYPE_CHECKING

from hya.imports import is_numpy_available, validate_numpy
from hya.utils.config import to_plain

if TYPE_CHECKING or is_numpy_available():
    import numpy as np
else:  # pragma: no cover
    from hya.utils.fallback.numpy import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


def to_array_resolver(data: ArrayLike, dtype: str | None = None) -> np.ndarray:
    r"""Implement a resolver to transform the input to a
    ``numpy.ndarray``.

    Args:
        data: Specifies the data to transform in ``numpy.ndarray``: an
            array, a tensor (on the CPU and without gradient), or any
            other value compatible with ``numpy.array``. The
            configuration nodes of a value are resolved first, at any
            depth, so a mapping node gives the same array as a literal
            mapping (an array of the data type ``object``).
        dtype: The data type of the array, as a string that
            ``numpy.array`` accepts (for example ``"float32"``).
            ``None`` lets NumPy infer the data type from the data.

    Returns:
        The input in a ``numpy.ndarray`` object. It is a copy: it does
        not share memory with an array or a tensor given as input, and
        it keeps the memory order of such an input.

    Raises:
        TypeError: If ``dtype`` is not a valid NumPy data type.
        omegaconf.errors.MissingMandatoryValue: If a node contains a
            missing value (``???``).

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"})
        >>> conf.key
        array([1, 2, 3])
        >>> conf = OmegaConf.create({"key": "${hya.np.array:[1, 2, 3],float32}"})
        >>> conf.key
        array([1., 2., 3.], dtype=float32)
        >>> # The interpolations of the data are resolved
        >>> conf = OmegaConf.create({"a": 1, "x": ["${a}", 2], "key": "${hya.np.array:${x}}"})
        >>> conf.key
        array([1, 2])

        ```
    """
    validate_numpy()
    # ``asarray`` does not pass the ``copy`` argument that ``Tensor.__array__`` does not accept
    return np.asarray(to_plain(data), dtype=dtype).copy(order="K")
