from __future__ import annotations

from omegaconf import OmegaConf

from hya.testing import numpy_available


@numpy_available
def test_array_resolver() -> None:
    assert OmegaConf.has_resolver("hya.np.array")
