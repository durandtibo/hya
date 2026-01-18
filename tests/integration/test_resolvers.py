from __future__ import annotations

import pytest
from omegaconf import OmegaConf

import hya  # noqa: F401


@pytest.mark.parametrize(
    "resolver_name",
    [
        "hya.add",
        "hya.asinh",
        "hya.ceildiv",
        "hya.exp",
        "hya.floordiv",
        "hya.len",
        "hya.iter_join",
        "hya.log",
        "hya.log10",
        "hya.max",
        "hya.min",
        "hya.mul",
        "hya.neg",
        "hya.path",
        "hya.pi",
        "hya.pow",
        "hya.sqrt",
        "hya.sha256",
        "hya.sinh",
        "hya.sub",
        "hya.to_path",
        "hya.truediv",
    ],
)
def test_resolver_registered(resolver_name: str) -> None:
    assert OmegaConf.has_resolver(resolver_name)
