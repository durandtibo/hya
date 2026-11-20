from __future__ import annotations

from unittest.mock import patch

import pytest
from omegaconf import OmegaConf

from hya.braceexpand import braceexpand_resolver
from hya.testing import braceexpand_available


@braceexpand_available
def test_braceexpand_resolver_1_4() -> None:
    assert OmegaConf.create({"key": r"${hya.braceexpand:\{1..4\}}"}).key == ["1", "2", "3", "4"]


@braceexpand_available
def test_braceexpand_resolver_a_e() -> None:
    assert OmegaConf.create({"key": r"${hya.braceexpand:\{a..e\}}"}).key == [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]


@braceexpand_available
def test_braceexpand_resolver_item() -> None:
    assert OmegaConf.create({"key": r"${hya.braceexpand:item\{1..3\}}"}).key == [
        "item1",
        "item2",
        "item3",
    ]


@braceexpand_available
def test_braceexpand_resolver_quoted_pattern() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"train_{a,b,c}.json"}'})
    assert conf.key == ["train_a.json", "train_b.json", "train_c.json"]


@braceexpand_available
def test_braceexpand_resolver_nested_patterns() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"data/{2020..2021}/{jan,feb}"}'})
    assert conf.key == ["data/2020/jan", "data/2020/feb", "data/2021/jan", "data/2021/feb"]


@braceexpand_available
def test_braceexpand_resolver_has_a_length() -> None:
    assert len(OmegaConf.create({"key": '${hya.braceexpand:"a{1..3}"}'}).key) == 3


@braceexpand_available
def test_braceexpand_resolver_can_be_indexed() -> None:
    assert OmegaConf.create({"key": '${hya.braceexpand:"a{1..3}"}'}).key[1] == "a2"


@braceexpand_available
def test_braceexpand_resolver_can_be_read_twice() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"a{1..3}"}'})
    assert list(conf.key) == list(conf.key)


@braceexpand_available
def test_braceexpand_resolver_feeds_iter_join() -> None:
    conf = OmegaConf.create({"key": '${hya.iter_join:${hya.braceexpand:"a{1..3}"},-}'})
    assert conf.key == "a1-a2-a3"


@braceexpand_available
def test_braceexpand_resolver_without_braces() -> None:
    assert braceexpand_resolver("abc") == ["abc"]


@braceexpand_available
def test_braceexpand_resolver_empty_pattern() -> None:
    assert braceexpand_resolver("") == [""]


@braceexpand_available
def test_braceexpand_resolver_returns_a_list() -> None:
    assert isinstance(braceexpand_resolver("a{1..3}"), list)


@braceexpand_available
def test_braceexpand_resolver_direct_call() -> None:
    assert braceexpand_resolver("a{1,2}b") == ["a1b", "a2b"]


def test_braceexpand_resolver_missing_package() -> None:
    with (
        patch("hya.braceexpand.validate_braceexpand", side_effect=RuntimeError("missing package")),
        pytest.raises(RuntimeError, match=r"missing package"),
    ):
        braceexpand_resolver("a{1,2}")
