from typing import Any

from hya import is_torch_available
from hya.registry import registry

DTYPE_MAPPING = {}
if is_torch_available():
    import torch
    from torch import Tensor, dtype, tensor

    for attr in dir(torch):
        dt = getattr(torch, attr)
        if isinstance(dt, dtype):
            DTYPE_MAPPING[attr] = dt
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
def torch_dtype_resolver(dtype: str) -> dtype:
    r"""Implements a resolver to create a ``torch.dtype`` from its string
    representation.

    Args:
        data: Specifies the target data type.

    Returns:
        ``torch.dtype``: The data type.
    """
    return DTYPE_MAPPING[dtype]
