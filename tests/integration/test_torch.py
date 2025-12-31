from __future__ import annotations

from omegaconf import OmegaConf

from hya.testing import torch_available


@torch_available
def test_tensor_resolver() -> None:
    assert OmegaConf.has_resolver("hya.torch.tensor")


@torch_available
def test_dtype_resolver() -> None:
    assert OmegaConf.has_resolver("hya.torch.dtype")
