from typing import Any

from bearface import is_torch_available
from bearface.registry import registry

if is_torch_available():
    from torch import Tensor, tensor
else:
    Tensor, tensor = None, None  # pragma: no cover


@registry.register("bf.to_tensor")
def to_tensor_resolver(data: Any) -> Tensor:
    r"""Implements a resolver to transform the input to a ``torch.Tensor``.

    Args:
        data: Specifies the data to transform in ``torch.Tensor``.
            This value should be compatible with ``torch.tensor``

    Returns:
        ``torch.Tensor``: The input in a ``torch.Tensor`` object.
    """
    return tensor(data)
