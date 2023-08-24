from __future__ import annotations

from typing import Any
from unittest.mock import Mock

from omegaconf.errors import InterpolationResolutionError

from hya.imports import check_torch, is_torch_available
from hya.registry import registry

if is_torch_available():
    import torch
else:  # pragma: no cover
    torch = Mock()


def to_tensor_resolver(data: Any) -> torch.Tensor:
    r"""Implements a resolver to transform the input to a
    ``torch.Tensor``.

    Args:
    ----
        data: Specifies the data to transform in ``torch.Tensor``.
            This value should be compatible with ``torch.tensor``

    Returns:
    -------
        ``torch.Tensor``: The input in a ``torch.Tensor`` object.
    """
    check_torch()
    return torch.tensor(data)


def torch_dtype_resolver(target: str) -> torch.dtype:
    r"""Implements a resolver to create a ``torch.dtype`` from its string
    representation.

    Args:
    ----
        target: Specifies the target data type.

    Returns:
    -------
        ``torch.dtype``: The data type.
    """
    check_torch()
    if not hasattr(torch, target) or not isinstance(getattr(torch, target), torch.dtype):
        raise InterpolationResolutionError(
            f"Incorrect dtype {target}. The available dtypes are {get_dtypes()}"
        )
    return getattr(torch, target)


def get_dtypes() -> set[torch.dtype]:
    r"""Gets all the data types.

    Returns:
    -------
        set: The data types.
    """
    check_torch()
    dtypes = set()
    for attr in dir(torch):
        dt = getattr(torch, attr)
        if isinstance(dt, torch.dtype):
            dtypes.add(dt)
    return dtypes


if is_torch_available():
    resolvers = {
        "hya.to_tensor": to_tensor_resolver,
        "hya.torch_dtype": torch_dtype_resolver,
    }
    for name, resolver in resolvers.items():
        registry.register(name)(resolver)
