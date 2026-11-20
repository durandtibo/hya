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
        data: Specifies the data to transform in ``numpy.ndarray``.
            This value should be compatible with ``numpy.array``
        dtype: The data type of the array, as a string that
            ``numpy.array`` accepts (for example ``"float32"``).
            ``None`` lets NumPy infer the data type from the data.

    Returns:
        The input in a ``numpy.ndarray`` object.

    Raises:
        TypeError: If ``dtype`` is not a valid NumPy data type.

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

        ```
    """
    validate_numpy()
    return np.array(data, dtype=dtype)
