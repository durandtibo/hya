from __future__ import annotations

import math
import re
from enum import Enum, IntEnum
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import (
    GrammarParseError,
    InterpolationResolutionError,
    MissingMandatoryValue,
)

from hya.resolvers import (
    _encode_value,
    add_resolver,
    iter_join_resolver,
    path_resolver,
    sha256_resolver,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class Color(Enum):
    RED = 1


class Number(IntEnum):
    ONE = 1


# An enum that is also a str, without the __str__ of StrEnum
Letter = Enum("Letter", {"A": "a"}, type=str)


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


@pytest.mark.parametrize(
    ("first", "second"),
    [
        pytest.param([0], [1], id="literal-literal"),
        pytest.param([0], OmegaConf.create([1]), id="literal-node"),
        pytest.param(OmegaConf.create([0]), [1], id="node-literal"),
        pytest.param(OmegaConf.create([0]), OmegaConf.create([1]), id="node-node"),
    ],
)
def test_add_resolver_lists_give_a_list(first: Any, second: Any) -> None:
    result = add_resolver(first, second)
    assert (type(result), result) == (list, [0, 1])


@pytest.mark.parametrize(
    "value",
    [
        pytest.param([1, [2]], id="literal-list"),
        pytest.param(OmegaConf.create([1, [2]]), id="list-node"),
        pytest.param({"a": [1]}, id="literal-mapping"),
        pytest.param(OmegaConf.create({"a": [1]}), id="mapping-node"),
    ],
)
def test_add_resolver_of_one_container_is_a_copy(value: Any) -> None:
    assert add_resolver(value) is not value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(OmegaConf.create([1, [2]]), [1, [2]], id="list-node"),
        pytest.param(OmegaConf.create({"a": [1]}), {"a": [1]}, id="mapping-node"),
    ],
)
def test_add_resolver_of_one_node_is_a_plain_container(value: Any, expected: Any) -> None:
    result = add_resolver(value)
    assert (type(result), result) == (type(expected), expected)


@pytest.mark.parametrize("value", [1, 1.5, "abc", (1, 2), None, Path("a")])
def test_add_resolver_of_one_other_object_is_the_object(value: Any) -> None:
    assert add_resolver(value) is value


@pytest.mark.parametrize(
    ("values", "expected"),
    [([1, 2, 3], 6), ([1.5, 2], 3.5), (["ab", "c"], "abc"), ([(1,), (2,)], (1, 2))],
)
def test_add_resolver_of_numbers_and_strings(values: list[Any], expected: Any) -> None:
    assert add_resolver(*values) == expected


def test_add_resolver_of_empty_lists() -> None:
    assert add_resolver(OmegaConf.create([]), []) == []


def test_add_resolver_of_the_same_list_twice() -> None:
    value = [1]
    assert add_resolver(value, value) == [1, 1]


def test_add_resolver_does_not_modify_the_inputs() -> None:
    first, second = [OmegaConf.create([1])], [2]
    node = first[0]
    add_resolver(first, second)
    assert (first[0] is node, second) == (True, [2])


def test_add_resolver_result_does_not_share_a_nested_list() -> None:
    value = [[1]]
    add_resolver(value, [])[0].append(2)
    assert value == [[1]]


def test_add_resolver_nested_interpolation() -> None:
    conf = OmegaConf.create({"a": 1, "x": [["${a}"]]})
    assert add_resolver([conf.x], [2]) == [[[1]], 2]


@pytest.mark.parametrize(
    "values",
    [
        pytest.param([OmegaConf.create(["???"])], id="one"),
        pytest.param([OmegaConf.create([["???"]]), [1]], id="first-nested"),
        pytest.param([[1], OmegaConf.create(["???"])], id="second"),
        pytest.param([[1], [OmegaConf.create({"a": "???"})]], id="second-in-a-list"),
    ],
)
def test_add_resolver_missing_value(values: list[Any]) -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        add_resolver(*values)


def test_add_resolver_incompatible_types() -> None:
    with pytest.raises(TypeError, match=r"unsupported operand type"):
        add_resolver(1, "a")


@pytest.mark.parametrize(
    "expression", ["${hya.add:[0],[1]}", "${hya.add:[0],${x}}", "${hya.add:${y},${x}}"]
)
def test_add_resolver_type_does_not_depend_on_how_a_list_is_written(expression: str) -> None:
    conf = OmegaConf.create({"x": [1], "y": [0], "key": expression})
    assert type(conf.key) is type(OmegaConf.create({"key": "${hya.add:[0],[1]}"}).key)


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


def test_iter_join_resolver_empty_iterable() -> None:
    assert iter_join_resolver([], "-") == ""


def test_iter_join_resolver_one_element() -> None:
    assert iter_join_resolver([1], "-") == "1"


def test_iter_join_resolver_duplicate_elements() -> None:
    assert iter_join_resolver(["a", "a"], "-") == "a-a"


def test_iter_join_resolver_string_iterable() -> None:
    assert iter_join_resolver("abc", "-") == "a-b-c"


def test_iter_join_resolver_tuple() -> None:
    assert iter_join_resolver((1, 2), "-") == "1-2"


def test_iter_join_resolver_generator() -> None:
    assert iter_join_resolver((i for i in [1, 2]), "-") == "1-2"


def test_iter_join_resolver_mapping_joins_the_keys() -> None:
    assert iter_join_resolver({"b": 1, "a": 2}, "-") == "b-a"


def test_iter_join_resolver_nested_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": [["${a}"], 2]})
    assert iter_join_resolver(conf.x, "-") == "[1]-2"


def test_iter_join_resolver_node_in_a_list() -> None:
    conf = OmegaConf.create({"a": 1, "x": ["${a}"]})
    assert iter_join_resolver([conf.x, 2], "-") == "[1]-2"


def test_iter_join_resolver_nested_mapping_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": [{"b": "${a}"}]})
    assert iter_join_resolver(conf.x, "-") == "{'b': 1}"


@pytest.mark.parametrize("value", [["???"], [["???"]]])
def test_iter_join_resolver_missing_value(value: list[Any]) -> None:
    with pytest.raises(MissingMandatoryValue, match=r"Missing mandatory value"):
        iter_join_resolver(OmegaConf.create(value), "-")


def test_iter_join_resolver_does_not_modify_the_input() -> None:
    node = OmegaConf.create([1])
    value = [node]
    iter_join_resolver(value, "-")
    assert value[0] is node


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
        ValueError,
        match=r"A file URL with a host, a query or a fragment is not supported: 'file://host/a'",
    ):
        path_resolver("file://host/a")


@pytest.mark.parametrize(
    "url",
    [
        "file:///data/run#1",
        "file:///data/run?a=1",
        "file:///data/run?a#b",
        "file:///data/run#",
        "file:///data/run?",
        "file:/data/run#1",
        "file:data/run?1",
        "file://localhost/data/run#1",
        "FILE:///data/run#1",
    ],
)
def test_path_resolver_file_url_with_a_query_or_a_fragment_raises(url: str) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape(f"A file URL with a host, a query or a fragment is not supported: '{url}'"),
    ):
        path_resolver(url)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("file:///data/run%231", "/data/run#1"),
        ("file:///data/run%3F1", "/data/run?1"),
        ("file:///data/a%23b%3F", "/data/a#b?"),
    ],
)
def test_path_resolver_file_url_with_an_encoded_query_or_fragment_character(
    url: str, expected: str
) -> None:
    assert path_resolver(url) == Path(expected)


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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # SHA-256 of [1]
        ([Number.ONE], "080a9ed428559ef602668b4c00f114f1a11c3f6b02a435f0bdc154578e4d7f22"),
        # SHA-256 of ["a"]
        ([Letter.A], "0eb5b8d6f81bc677da8a08567cc4fa9a06a57e9ec8da85ed73a7f62727996002"),
        # SHA-256 of ["\u00e9"], the non-ASCII character is escaped
        (["\u00e9"], "d8f81e7a2fa1455720e881bd1d164699bdc9bd7dd91641754a2ead7107c1ea0a"),
    ],
)
def test_sha256_resolver_format_of_the_json(value: Any, expected: str) -> None:
    assert sha256_resolver(value) == expected


@pytest.mark.parametrize("number", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize(
    "wrap",
    [
        pytest.param(lambda x: x, id="value"),
        pytest.param(lambda x: [x], id="list"),
        pytest.param(lambda x: {"a": [x]}, id="mapping"),
        pytest.param(lambda x: {x: 1}, id="key"),
        pytest.param(lambda x: OmegaConf.create([x]), id="node"),
    ],
)
def test_sha256_resolver_non_finite_float(number: float, wrap: Callable[[float], Any]) -> None:
    with pytest.raises(ValueError, match=r"Out of range float values are not JSON compliant"):
        sha256_resolver(wrap(number))


@pytest.mark.parametrize("text", ["nan", "inf", "-inf", "NaN", "Infinity"])
def test_sha256_resolver_string_of_a_non_finite_float(text: str) -> None:
    assert len(sha256_resolver(text)) == 64


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
