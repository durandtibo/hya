from __future__ import annotations

import math
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import (
    GrammarParseError,
    InterpolationResolutionError,
    MissingMandatoryValue,
)

from hya.resolvers import _encode_value, path_resolver, sha256_resolver


class Color(Enum):
    RED = 1


def test_add_resolver_int2() -> None:
    assert OmegaConf.create({"key": "${hya.add:1,4}"}).key == 5


def test_add_resolver_int3() -> None:
    assert OmegaConf.create({"key": "${hya.add:1,2,4}"}).key == 7


def test_add_resolver_list2() -> None:
    assert OmegaConf.create({"key": "${hya.add:[1,2,3],[4]}"}).key == [1, 2, 3, 4]


def test_add_resolver_list3() -> None:
    assert OmegaConf.create({"key": "${hya.add:[1,2,3],[4],[5,6]}"}).key == [1, 2, 3, 4, 5, 6]


def test_add_resolver_str2() -> None:
    assert OmegaConf.create({"key": "${hya.add:abc,d}"}).key == "abcd"


def test_add_resolver_str3() -> None:
    assert OmegaConf.create({"key": "${hya.add:abc,d,ef}"}).key == "abcdef"


def test_add_resolver_one_argument() -> None:
    assert OmegaConf.create({"key": "${hya.add:5}"}).key == 5


def test_add_resolver_list_interpolation() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x},[3]}"})
    assert conf.key == [1, 2, 3]


def test_add_resolver_does_not_modify_config_list() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x},[3]}"})
    _ = conf.key
    assert conf.x == [1, 2]


def test_add_resolver_does_not_modify_config_list_when_read_twice() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x},[3]}"})
    _ = conf.key
    assert conf.key == [1, 2, 3]


def test_add_resolver_no_argument() -> None:
    conf = OmegaConf.create({"key": "${hya.add:}"})
    with pytest.raises(InterpolationResolutionError, match=r"missing 1 required positional"):
        _ = conf.key


def test_ceildiv_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.ceildiv:11,4}"}).key == 3


def test_ceildiv_resolver_division_by_zero() -> None:
    with pytest.raises(InterpolationResolutionError, match=r"ZeroDivisionError"):
        OmegaConf.create({"key": "${hya.ceildiv:10,0}"}).key  # noqa: B018


def test_iter_join_resolver_list_str() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[a,b,c],-}"}).key == "a-b-c"


def test_iter_join_resolver_list_int() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[1,2,3],x}"}).key == "1x2x3"


def test_iter_join_resolver_empty_separator() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[a,b,c],''}"}).key == "abc"


def test_mul_resolver_int2() -> None:
    assert OmegaConf.create({"key": "${hya.mul:3,4}"}).key == 12


def test_mul_resolver_int3() -> None:
    assert OmegaConf.create({"key": "${hya.mul:3,4,2}"}).key == 24


def test_mul_resolver_float2() -> None:
    assert OmegaConf.create({"key": "${hya.mul:1.5,3}"}).key == 4.5


def test_mul_resolver_float3() -> None:
    assert OmegaConf.create({"key": "${hya.mul:1.5,3,2.0}"}).key == 9.0


def test_mul_resolver_list() -> None:
    assert OmegaConf.create({"key": "${hya.mul:[1,2,3],3}"}).key == [1, 2, 3, 1, 2, 3, 1, 2, 3]


def test_mul_resolver_one_argument() -> None:
    assert OmegaConf.create({"key": "${hya.mul:5}"}).key == 5


def test_mul_resolver_config_list_is_not_repeated() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.mul:${x},2}"})
    with pytest.raises(InterpolationResolutionError, match=r"unsupported operand type"):
        _ = conf.key


def test_mul_resolver_config_list_is_not_modified() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.mul:${x},2}"})
    with pytest.raises(InterpolationResolutionError, match=r"unsupported operand type"):
        _ = conf.key
    assert conf.x == [1, 2]


def test_mul_resolver_no_argument() -> None:
    conf = OmegaConf.create({"key": "${hya.mul:}"})
    with pytest.raises(InterpolationResolutionError, match=r"missing 1 required positional"):
        _ = conf.key


def test_path_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.path:/my/path}"}).key == Path("/my/path")


def test_path_resolver_returns_a_path() -> None:
    assert isinstance(OmegaConf.create({"key": "${hya.path:/my/path}"}).key, Path)


def test_path_resolver_absolute_path() -> None:
    assert path_resolver("/my/path") == Path("/my/path")


def test_path_resolver_relative_path() -> None:
    assert path_resolver("my/path") == Path.cwd() / "my" / "path"


def test_path_resolver_parent_directory() -> None:
    assert path_resolver("/my/path/../other") == Path("/my/other")


def test_path_resolver_trailing_slash() -> None:
    assert path_resolver("/my/path/") == Path("/my/path")


def test_path_resolver_tilde() -> None:
    assert path_resolver("~/my/path") == Path.home() / "my" / "path"


def test_path_resolver_tilde_quoted_in_an_interpolation() -> None:
    conf = OmegaConf.create({"key": '${hya.path:"~/my/path"}'})
    assert conf.key == Path.home() / "my" / "path"


def test_path_resolver_tilde_unquoted_in_an_interpolation() -> None:
    with pytest.raises(GrammarParseError, match=r"token recognition error"):
        OmegaConf.create({"key": "${hya.path:~/my/path}"})


def test_path_resolver_file_url() -> None:
    assert path_resolver("file:///my/path") == Path("/my/path")


def test_path_resolver_file_url_with_host() -> None:
    assert path_resolver("file://localhost/my/path") == Path("/my/path")


def test_path_resolver_file_url_decodes_percent_encoding() -> None:
    assert path_resolver("file:///my/path%20to/a%25b") == Path("/my/path to/a%b")


def test_path_resolver_file_url_without_slashes() -> None:
    assert path_resolver("file:/my/path") == Path("/my/path")


def test_path_resolver_file_url_in_an_interpolation() -> None:
    assert OmegaConf.create({"key": "${hya.path:file:///my/path%20to}"}).key == Path("/my/path to")


def test_path_resolver_plain_path_keeps_percent_encoding() -> None:
    assert path_resolver("/my/a%20b") == Path("/my/a%20b")


def test_path_resolver_plain_path_keeps_question_mark() -> None:
    assert path_resolver("/my/a?b") == Path("/my/a?b")


def test_path_resolver_plain_path_keeps_fragment_character() -> None:
    assert path_resolver("/my/a#b") == Path("/my/a#b")


def test_path_resolver_url_is_not_parsed_when_it_is_not_a_file_url() -> None:
    assert path_resolver("http://host/path") == Path.cwd() / "http:" / "host" / "path"


def test_path_resolver_file_scheme_is_case_insensitive() -> None:
    assert path_resolver("FILE:///my/path") == Path("/my/path")


def test_path_resolver_file_scheme_is_case_insensitive_without_slashes() -> None:
    assert path_resolver("File:/my/path") == Path("/my/path")


def test_path_resolver_file_url_with_a_host_raises() -> None:
    with pytest.raises(
        ValueError, match=r"A file URL with a host is not supported: 'file://host/a'"
    ):
        path_resolver("file://host/a")


def test_path_resolver_file_url_with_a_host_raises_in_an_interpolation() -> None:
    conf = OmegaConf.create({"key": "${hya.path:file://host/a/b}"})
    with pytest.raises(InterpolationResolutionError, match=r"with a host"):
        _ = conf.key


def test_path_resolver_file_url_relative_path() -> None:
    assert path_resolver("file:my/path") == Path.cwd() / "my" / "path"


def test_path_resolver_path_object() -> None:
    assert path_resolver(Path("/my/path")) == Path("/my/path")


def test_path_resolver_path_object_with_tilde() -> None:
    assert path_resolver(Path("~/my/path")) == Path.home() / "my" / "path"


def test_path_resolver_path_of_a_path_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.path:${hya.path:/my/path}}"}).key == Path("/my/path")


def test_path_resolver_path_object_in_a_configuration() -> None:
    conf = OmegaConf.create({"p": Path("/my/path"), "key": "${hya.path:${p}}"})
    assert conf.key == Path("/my/path")


def test_pi_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.pi:}"}).key == math.pi


def test_sha256_resolver() -> None:
    assert isinstance(
        OmegaConf.create({"key": "${hya.sha256:${value}}", "value": "blabla"}).key, str
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("mystring", "bd3ff47540b31e62d4ca6b07794e5a886b0f655fc322730f26ecd65cc7dd5c90"),
        ("", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (1, "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"),
        (1.5, "9f29a130438b81170b92a42650f9a94291ecad60bd47af2a3886e75f7f728725"),
        (True, "b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b"),
        (None, "74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b"),
        ([1, 2], "49a64717d5d4cb19952e6eac2946415cf6879adacf9908e7d872332d32c6e684"),
        ((1, 2), "49a64717d5d4cb19952e6eac2946415cf6879adacf9908e7d872332d32c6e684"),
        ({"b": 2, "a": 1}, "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"),
        (
            PurePosixPath("/a"),
            "54b379c98639bd24c4d8282825cd34f0cde7fcd347dc7655706f6a37fb680122",
        ),
    ],
)
def test_sha256_resolver_value(value: Any, expected: str) -> None:
    assert sha256_resolver(value) == expected


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ([], "[]"),
        ({}, "{}"),
        ({"b": [1, {"d": None, "c": "x"}], "a": 1.5}, '{"a":1.5,"b":[1,{"c":"x","d":null}]}'),
        ([Color.RED], '["Color.RED"]'),
        ([PurePosixPath("/a")], '["/a"]'),
        ({1: 2}, '{"1":2}'),
    ],
)
def test_sha256_resolver_hashes_the_canonical_json(value: Any, text: str) -> None:
    assert sha256_resolver(value) == sha256_resolver(text)


def test_sha256_resolver_string_is_not_encoded_in_json() -> None:
    assert sha256_resolver("a") != sha256_resolver('"a"')


def test_sha256_resolver_does_not_depend_on_the_order_of_the_keys() -> None:
    assert sha256_resolver({"a": 1, "b": 2}) == sha256_resolver({"b": 2, "a": 1})


def test_sha256_resolver_depends_on_the_order_of_a_list() -> None:
    assert sha256_resolver([1, 2]) != sha256_resolver([2, 1])


def test_sha256_resolver_config_node_and_plain_value() -> None:
    assert sha256_resolver(OmegaConf.create({"a": [1]})) == sha256_resolver({"a": [1]})


def test_sha256_resolver_resolves_the_interpolations_of_a_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": ["${a}"]})
    assert sha256_resolver(conf.x) == sha256_resolver([1])


def test_sha256_resolver_is_deterministic() -> None:
    assert sha256_resolver({"a": [1, 2]}) == sha256_resolver({"a": [1, 2]})


def test_sha256_resolver_does_not_modify_the_input() -> None:
    value = {"b": [2, 1], "a": 1}
    sha256_resolver(value)
    assert list(value.items()) == [("b", [2, 1]), ("a", 1)]


def test_sha256_resolver_mixed_key_types() -> None:
    with pytest.raises(TypeError, match=r"'<' not supported between instances of"):
        sha256_resolver({1: 2, "a": 3})


def test_sha256_resolver_key_without_json_form() -> None:
    with pytest.raises(TypeError, match=r"keys must be str, int, float, bool or None"):
        sha256_resolver({(1, 2): 3})


@pytest.mark.parametrize(
    ("value", "name"),
    [({1, 2}, "set"), (b"abc", "bytes"), ([object()], "object"), (1j, "complex")],
)
def test_sha256_resolver_value_without_json_form(value: Any, name: str) -> None:
    with pytest.raises(TypeError, match=rf"hya.sha256 cannot hash a value of type {name}"):
        sha256_resolver(value)


def test_sha256_resolver_missing_value() -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        sha256_resolver(OmegaConf.create(["???"]))


def test_encode_value_path() -> None:
    assert _encode_value(PurePosixPath("/my/path")) == "/my/path"


def test_encode_value_concrete_path() -> None:
    assert _encode_value(Path("my_path")) == "my_path"


def test_encode_value_enum() -> None:
    assert _encode_value(Color.RED) == "Color.RED"


@pytest.mark.parametrize(
    ("value", "name"), [({1}, "set"), (b"a", "bytes"), ("a", "str"), (None, "NoneType")]
)
def test_encode_value_other_type(value: Any, name: str) -> None:
    with pytest.raises(TypeError, match=rf"hya.sha256 cannot hash a value of type {name}"):
        _encode_value(value)
