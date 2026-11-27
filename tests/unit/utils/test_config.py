from __future__ import annotations

from typing import Any

import pytest
from omegaconf import DictConfig, ListConfig, OmegaConf
from omegaconf.errors import MissingMandatoryValue

from hya.utils.config import to_plain

##############################
#     Tests for to_plain     #
##############################


@pytest.mark.parametrize("value", ["abc", "", 1, 0, -1.5, True, None])
def test_to_plain_scalar(value: Any) -> None:
    assert to_plain(value) is value


@pytest.mark.parametrize("value", [object(), (1, 2), {1, 2}, b"abc"])
def test_to_plain_object_is_returned_as_is(value: Any) -> None:
    assert to_plain(value) is value


@pytest.mark.parametrize("value", [[], {}])
def test_to_plain_empty_container(value: Any) -> None:
    assert to_plain(value) == value


@pytest.mark.parametrize("value", [[], {}])
def test_to_plain_empty_config(value: Any) -> None:
    assert type(to_plain(OmegaConf.create(value))) is type(value)


def test_to_plain_list_config() -> None:
    result = to_plain(OmegaConf.create([1, [2, {"a": 3}]]))
    assert result == [1, [2, {"a": 3}]]


def test_to_plain_list_config_returns_a_list() -> None:
    assert type(to_plain(OmegaConf.create([1]))) is list


def test_to_plain_dict_config() -> None:
    result = to_plain(OmegaConf.create({"a": 1, "b": {"c": [2]}}))
    assert result == {"a": 1, "b": {"c": [2]}}


def test_to_plain_dict_config_returns_a_dict() -> None:
    assert type(to_plain(OmegaConf.create({"a": 1}))) is dict


def test_to_plain_resolves_the_interpolations_of_a_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": [["${a}"], {"b": "${a}"}]})
    assert to_plain(conf.x) == [[1], {"b": 1}]


def test_to_plain_node_in_a_list() -> None:
    conf = OmegaConf.create({"a": 1, "x": ["${a}"]})
    result = to_plain([conf.x, 2])
    assert result == [[1], 2]


def test_to_plain_node_in_a_nested_list_is_not_a_config() -> None:
    result = to_plain([[OmegaConf.create([1])]])
    assert not isinstance(result[0][0], ListConfig)


def test_to_plain_node_in_a_dict() -> None:
    conf = OmegaConf.create({"a": 1, "x": {"b": "${a}"}})
    assert to_plain({"y": conf.x, "z": 2}) == {"y": {"b": 1}, "z": 2}


def test_to_plain_node_in_a_dict_is_not_a_config() -> None:
    result = to_plain({"y": OmegaConf.create({"a": 1})})
    assert not isinstance(result["y"], DictConfig)


def test_to_plain_keeps_the_order_of_the_keys() -> None:
    assert list(to_plain({"b": 1, "a": 2})) == ["b", "a"]


def test_to_plain_object_in_a_list_is_kept() -> None:
    item = object()
    assert to_plain([item])[0] is item


@pytest.mark.parametrize("value", [["???"], [["???"]], {"a": {"b": "???"}}])
def test_to_plain_missing_value_in_a_node(value: Any) -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        to_plain(OmegaConf.create(value))


def test_to_plain_missing_value_in_a_node_of_a_list() -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        to_plain([OmegaConf.create(["???"])])


def test_to_plain_returns_a_new_list() -> None:
    value = [1, 2]
    assert to_plain(value) is not value


def test_to_plain_does_not_modify_a_list() -> None:
    node = OmegaConf.create([1])
    value = [node]
    to_plain(value)
    assert value[0] is node


def test_to_plain_does_not_modify_a_dict() -> None:
    node = OmegaConf.create([1])
    value = {"a": node}
    to_plain(value)
    assert value["a"] is node


def test_to_plain_does_not_modify_a_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": ["${a}"]})
    to_plain(conf)
    assert OmegaConf.to_container(conf) == {"a": 1, "x": ["${a}"]}


def test_to_plain_is_deterministic() -> None:
    node = OmegaConf.create({"a": [1, 2]})
    assert to_plain(node) == to_plain(node)
