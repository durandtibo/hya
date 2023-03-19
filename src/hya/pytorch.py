from typing import Any

from omegaconf.errors import InterpolationResolutionError

from hya import is_torch_available
from hya.registry import registry

if is_torch_available():
    import torch
    from torch import Tensor, dtype, tensor
else:
    Tensor, tensor, dtype = None, None, None  # pragma: no cover


@registry.register("hya.to_tensor")
def to_tensor_resolver(data: Any) -> Tensor:
    r"""Implements a resolver to transform the input to a ``torch.Tensor``.

    Args:
        data: Specifies the data to transform in ``torch.Tensor``.
            This value should be compatible with ``torch.tensor``

    Returns:
        ``torch.Tensor``: The input in a ``torch.Tensor`` object.
    """
    return tensor(data)


@registry.register("hya.torch_dtype")
def torch_dtype_resolver(target: str) -> dtype:
    r"""Implements a resolver to create a ``torch.dtype`` from its string
    representation.

    Args:
        target: Specifies the target data type.

    Returns:
        ``torch.dtype``: The data type.
    """
    if not hasattr(torch, target) or not isinstance(getattr(torch, target), dtype):
        raise InterpolationResolutionError(
            f"Incorrect dtype {target}. The available dtypes are {get_dtypes()}"
        )
    return getattr(torch, target)


def get_dtypes() -> set[dtype]:
    r"""Gets all the data types.

    Returns:
        set: The data types.
    """
    dtypes = set()
    for attr in dir(torch):
        dt = getattr(torch, attr)
        if isinstance(dt, dtype):
            dtypes.add(dt)
    return dtypes
