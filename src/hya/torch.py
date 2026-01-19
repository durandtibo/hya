r"""Implement PyTorch resolvers for tensor creation and dtype handling.

This module provides OmegaConf resolvers that use PyTorch for tensor operations
and data type specifications. The resolvers are registered only if the ``torch``
package is available, enabling users to create PyTorch tensors and specify dtypes
directly from configuration files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from omegaconf.errors import InterpolationResolutionError

from hya.imports import check_torch, is_torch_available

if TYPE_CHECKING or is_torch_available():
    import torch
else:  # pragma: no cover
    from hya.utils.fallback.torch import torch


def to_tensor_resolver(data: Any) -> torch.Tensor:
    r"""Implement a resolver to transform the input to a
    ``torch.Tensor``.

    Args:
        data: Specifies the data to transform in ``torch.Tensor``.
            This value should be compatible with ``torch.tensor``

    Returns:
        The input in a ``torch.Tensor`` object.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2,3,4,5]}"})
        >>> conf.key
        tensor([1, 2, 3, 4, 5])

        ```
    """
    check_torch()
    return torch.tensor(data)


def torch_dtype_resolver(target: str) -> torch.dtype:
    r"""Create a ``torch.dtype`` from its string representation.

    This resolver converts a string name to the corresponding PyTorch
    data type object. The string must match an attribute name in the
    torch module that represents a dtype (e.g., "float32", "int64").

    Args:
        target: The target data type as a string. Must be a valid
            torch dtype attribute name such as "float", "float32",
            "float64", "int32", "int64", "bool", etc. The string
            should match the attribute name in torch (e.g., use
            "float32" not "torch.float32").

    Returns:
        The corresponding torch.dtype object.

    Raises:
        InterpolationResolutionError: If the target string doesn't
            correspond to a valid torch dtype.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.torch.dtype:float}"})
        >>> conf.key
        torch.float32
        >>> conf = OmegaConf.create({"key": "${hya.torch.dtype:int64}"})
        >>> conf.key
        torch.int64

        ```
    """
    check_torch()
    if not hasattr(torch, target) or not isinstance(getattr(torch, target), torch.dtype):
        msg = f"Incorrect dtype {target}. The available dtypes are {get_dtypes()}"
        raise InterpolationResolutionError(msg)
    return getattr(torch, target)


def get_dtypes() -> set[torch.dtype]:
    r"""Get all available PyTorch data types.

    This function introspects the torch module to find all available
    dtype objects. It's useful for validation and error messages when
    working with torch dtype resolvers.

    Returns:
        A set containing all PyTorch dtype objects available in the
        current torch installation (e.g., torch.float32, torch.int64,
        torch.bool, etc.).

    Example:
        ```pycon
        >>> import hya
        >>> from hya.torch import get_dtypes
        >>> dtypes = get_dtypes()
        >>> torch.float32 in dtypes
        True

        ```
    """
    check_torch()
    dtypes = set()
    for attr in dir(torch):
        dt = getattr(torch, attr)
        if isinstance(dt, torch.dtype):
            dtypes.add(dt)
    return dtypes
