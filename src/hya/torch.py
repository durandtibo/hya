r"""Implement PyTorch resolvers for tensor creation and dtype handling.

This module provides OmegaConf resolvers that use PyTorch for tensor
operations and data type specifications. The resolvers are always
registered; the ``torch`` package is needed only when one of them is
called, and a missing package raises an error that says how to install
it. Users can create PyTorch tensors and specify dtypes directly from
configuration files.
"""

from __future__ import annotations

__all__ = ["to_tensor_resolver", "torch_dtype_resolver"]

from typing import TYPE_CHECKING, Any

from hya.imports import is_torch_available, validate_torch
from hya.utils.config import to_plain

if TYPE_CHECKING or is_torch_available():
    import torch
else:  # pragma: no cover
    from hya.utils.fallback.torch import torch


def to_tensor_resolver(data: Any, dtype: torch.dtype | str | None = None) -> torch.Tensor:
    r"""Implement a resolver to transform the input to a
    ``torch.Tensor``.

    Args:
        data: Specifies the data to transform in ``torch.Tensor``: a
            tensor, or a value compatible with ``torch.tensor``. The
            configuration nodes of a value are resolved first, at any
            depth.
        dtype: The data type of the tensor: a ``torch.dtype`` (for
            example the output of the ``hya.torch.dtype`` resolver) or
            its name (for example ``"float32"``). ``None`` keeps the
            data type of a tensor, and lets PyTorch infer the data type
            of any other value.

    Returns:
        The input in a ``torch.Tensor`` object. It is a copy: it does
        not share memory with a tensor given as input, and it does not
        require a gradient.

    Raises:
        ValueError: If ``dtype`` is a string that is not the name of a
            torch dtype.
        omegaconf.errors.MissingMandatoryValue: If a node contains a
            missing value (``???``).

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2,3,4,5]}"})
        >>> conf.key
        tensor([1, 2, 3, 4, 5])
        >>> conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2,3],${hya.torch.dtype:float32}}"})
        >>> conf.key
        tensor([1., 2., 3.])
        >>> # The data type can be given by its name
        >>> conf = OmegaConf.create({"key": "${hya.torch.tensor:[1,2],float32}"})
        >>> conf.key
        tensor([1., 2.])
        >>> # A tensor is copied
        >>> conf = OmegaConf.create({"key": "${hya.torch.tensor:${hya.torch.tensor:[1,2]}}"})
        >>> conf.key
        tensor([1, 2])

        ```
    """
    validate_torch()
    if isinstance(dtype, str):
        dtype = torch_dtype_resolver(dtype)
    if isinstance(data, torch.Tensor):
        return data.detach().to(dtype=data.dtype if dtype is None else dtype, copy=True)
    return torch.tensor(to_plain(data), dtype=dtype)


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
        ValueError: If the target string doesn't correspond to a valid
            torch dtype. The message lists the available dtype names,
            sorted. Through an interpolation, OmegaConf reports it as an
            ``InterpolationResolutionError``.

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
    validate_torch()
    dtype = getattr(torch, target, None)
    if isinstance(dtype, torch.dtype):
        return dtype
    msg = f"Incorrect dtype {target}. The available dtypes are {_dtype_names()}"
    raise ValueError(msg)


def _dtype_names() -> list[str]:
    r"""Get the sorted names of the available PyTorch data types.

    This function introspects the torch module to find the names of the
    attributes that are a ``torch.dtype``. It is used in the error
    message of the dtype resolver, which has already checked that
    ``torch`` is installed. The names are sorted, so the message
    does not depend on the order of a set.

    Returns:
        The sorted names of the attributes of ``torch`` that are a
        ``torch.dtype`` (e.g., ``"float32"``, ``"int64"``, ``"bool"``).

    Example:
        ```pycon
        >>> from hya.torch import _dtype_names
        >>> "float32" in _dtype_names()
        True

        ```
    """
    return sorted(name for name in dir(torch) if isinstance(getattr(torch, name), torch.dtype))
