from __future__ import annotations

import pytest
from omegaconf import OmegaConf

from hya import register_resolvers
from hya.testing import braceexpand_available


@pytest.fixture(scope="module", autouse=True)
def _register() -> None:
    register_resolvers()


@braceexpand_available
def test_braceexpand_resolver_1_4() -> None:
    assert list(OmegaConf.create({"key": r"${hya.braceexpand:\{1..4\}}"}).key) == [
        "1",
        "2",
        "3",
        "4",
    ]


@braceexpand_available
def test_braceexpand_resolver_a_e() -> None:
    assert list(OmegaConf.create({"key": r"${hya.braceexpand:\{a..e\}}"}).key) == [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]


@braceexpand_available
def test_braceexpand_resolver_item() -> None:
    assert list(OmegaConf.create({"key": r"${hya.braceexpand:item\{1..3\}}"}).key) == [
        "item1",
        "item2",
        "item3",
    ]
