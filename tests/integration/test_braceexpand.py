from __future__ import annotations

from omegaconf import OmegaConf

from hya.testing import braceexpand_available


@braceexpand_available
def test_braceexpand_resolver() -> None:
    assert OmegaConf.has_resolver("hya.braceexpand")
