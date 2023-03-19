from typing import Any

from hya import is_torch_available
from hya.registry import registry

DTYPE_MAPPING = {}
if is_torch_available():
    import torch
    from torch import Tensor, dtype, tensor

    DTYPE_MAPPING.update(
        {
            "float32": torch.float32,
            "float": torch.float,
            "float64": torch.float64,
            "double": torch.double,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "half": torch.half,
            "uint8": torch.uint8,
            "int8": torch.int8,
            "int16": torch.int16,
            "short": torch.short,
            "int32": torch.int32,
            "int": torch.int,
            "int64": torch.int64,
            "long": torch.long,
            "complex32": torch.complex32,
            "complex64": torch.complex64,
            "cfloat": torch.cfloat,
            "complex128": torch.complex128,
            "cdouble": torch.cdouble,
            "quint8": torch.quint8,
            "qint8": torch.qint8,
            "qint32": torch.qint32,
            "bool": torch.bool,
            "quint4x2": torch.quint4x2,
            "quint2x4": torch.quint2x4,
        }
    )
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
