r"""Implement NumPy resolvers for array creation and manipulation.

This module provides OmegaConf resolvers that use NumPy for array operations.
The resolvers are registered only if the ``numpy`` package is available,
allowing users to create NumPy arrays directly from configuration files.
        registry.register_resolvers()

        # Then in your OmegaConf config:
        # data: ${hya.np.array:[1, 2, 3]}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hya.imports import check_numpy, is_numpy_available

if TYPE_CHECKING or is_numpy_available():
    import numpy as np
else:  # pragma: no cover
    from hya.utils.fallback.numpy import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


def to_array_resolver(data: ArrayLike) -> np.ndarray:
    r"""Implement a resolver to transform the input to a
    ``numpy.ndarray``.

    Args:
        data: Specifies the data to transform in ``numpy.ndarray``.
            This value should be compatible with ``numpy.array``

    Returns:
        The input in a ``numpy.ndarray`` object.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"})
        >>> conf.key
        array([1, 2, 3])

        ```
    """
    check_numpy()
    return np.array(data)
