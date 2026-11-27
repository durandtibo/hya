from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from omegaconf import OmegaConf, flag_override
from omegaconf.errors import InterpolationResolutionError, UnsupportedValueType

from hya import get_default_registry
from hya.resolvers import sha256_resolver
from hya.testing import numpy_available, torch_available

DOCS_RESOLVERS = Path(__file__).parents[2] / "docs" / "docs" / "resolvers.md"
# A resolver is documented by a heading (#### `hya.add`) or by a row of a table (| `hya.sub` |)
DOCUMENTED_KEY = re.compile(r"^(?:#### |\| )`(hya\.[\w.]+)`", re.MULTILINE)

OPTIONAL_KEYS = {"hya.braceexpand", "hya.np.array", "hya.torch.tensor", "hya.torch.dtype"}

###########################################
#     Tests for the default resolvers     #
###########################################


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("${hya.add:1,2,3}", 6),
        ("${hya.asinh:0}", 0.0),
        ("${hya.ceildiv:100,32}", 4),
        ("${hya.exp:0}", 1.0),
        ("${hya.float:3}", 3.0),
        ("${hya.floordiv:100,32}", 3),
        ("${hya.int:${hya.mul:100000,0.1}}", 10000),
        ("${hya.int:2.9}", 2),
        ("${hya.iter_join:[a,b,c],/}", "a/b/c"),
        ("${hya.len:[1,2,3]}", 3),
        ("${hya.log:8,2}", 3.0),
        ("${hya.log10:100}", 2.0),
        ("${hya.max:1,5,3}", 5),
        ("${hya.min:4,2,3}", 2),
        ("${hya.mul:2,3,4}", 24),
        ("${hya.neg:2}", -2),
        ("${hya.path:/my/path}", Path("/my/path")),
        ("${hya.pi:}", 3.141592653589793),
        ("${hya.pow:2,10}", 1024),
        (
            "${hya.sha256:abc}",
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        ),
        ("${hya.sinh:0}", 0.0),
        ("${hya.sqrt:64}", 8.0),
        ("${hya.sub:5,3}", 2),
        ("${hya.sum:[1,2,3]}", 6),
        ("${hya.path:file:///my/path}", Path("/my/path")),
        ("${hya.path:FILE:///my/path}", Path("/my/path")),
        ("${hya.path:${hya.path:/my/path}}", Path("/my/path")),
        ("${hya.truediv:10,4}", 2.5),
    ],
)
def test_default_resolver(expression: str, expected: Any) -> None:
    assert OmegaConf.create({"key": expression}).key == expected


def test_default_resolvers_table_covers_the_builtin_keys() -> None:
    keys = set(get_default_registry().state) - OPTIONAL_KEYS
    assert keys == {
        "hya.add",
        "hya.asinh",
        "hya.ceildiv",
        "hya.exp",
        "hya.float",
        "hya.floordiv",
        "hya.int",
        "hya.iter_join",
        "hya.len",
        "hya.log",
        "hya.log10",
        "hya.max",
        "hya.min",
        "hya.mul",
        "hya.neg",
        "hya.path",
        "hya.pi",
        "hya.pow",
        "hya.sha256",
        "hya.sinh",
        "hya.sqrt",
        "hya.sub",
        "hya.sum",
        "hya.truediv",
    }


def test_default_resolvers_are_documented() -> None:
    documented = set(DOCUMENTED_KEY.findall(DOCS_RESOLVERS.read_text()))
    assert set(get_default_registry().state) - documented == set()


def test_documented_resolvers_exist() -> None:
    documented = set(DOCUMENTED_KEY.findall(DOCS_RESOLVERS.read_text()))
    assert documented - set(get_default_registry().state) - OPTIONAL_KEYS == set()


def test_path_resolver_file_url_with_a_host_is_an_error() -> None:
    conf = OmegaConf.create({"key": "${hya.path:file://host/my/path}"})
    with pytest.raises(InterpolationResolutionError, match=r"A file URL with a host"):
        _ = conf.key


##########################################
#     Tests for the stdlib resolvers     #
##########################################


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        ("${hya.max:1}", r"'int' object is not iterable"),
        ("${hya.sum:1}", r"'int' object is not iterable"),
        ("${hya.int:abc}", r"invalid literal for int\(\)"),
        ("${hya.sqrt:-1}", r"(math domain error|expected a nonnegative input)"),
        ("${hya.truediv:1,0}", r"division by zero"),
        ("${hya.floordiv:1,0}", r"(division|modulo) by zero"),
    ],
)
def test_stdlib_resolver_error_is_the_error_of_the_stdlib(expression: str, message: str) -> None:
    conf = OmegaConf.create({"key": expression})
    with pytest.raises(InterpolationResolutionError, match=message):
        _ = conf.key


def test_stdlib_resolver_does_not_warn_on_int_arguments(recwarn: pytest.WarningsRecorder) -> None:
    assert OmegaConf.create({"key": "${hya.log:1}"}).key == 0.0
    assert len(recwarn) == 0


def test_add_resolver_does_not_modify_config_list() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x},[3]}"})
    assert conf.key == [1, 2, 3]
    assert conf.x == [1, 2]


def test_mul_resolver_does_not_modify_config_list() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.mul:${x},2}"})
    with pytest.raises(InterpolationResolutionError, match=r"TypeError"):
        _ = conf.key
    assert conf.x == [1, 2]


def test_iter_join_resolver_does_not_modify_config_list() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.iter_join:${x},-}"})
    assert conf.key == "1-2"
    assert conf.x == [1, 2]


def test_sha256_resolver_does_not_modify_config_list() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.sha256:${x}}"})
    assert len(conf.key) == 64
    assert conf.x == [1, 2]


def test_sha256_resolver_does_not_modify_config_dict() -> None:
    conf = OmegaConf.create({"x": {"a": 1}, "key": "${hya.sha256:${x}}"})
    assert len(conf.key) == 64
    assert conf.x == {"a": 1}


def test_add_resolver_of_one_value_returns_a_copy() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.add:${x}}"})
    conf.key.append(3)
    assert conf.x == [1, 2]


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("${hya.add:${x}}", [1]),
        ("${hya.add:${x},[2]}", [1, 2]),
        ("${hya.add:[0],${x}}", [0, 1]),
        ("${hya.add:${x},${x}}", [1, 1]),
    ],
)
def test_add_resolver_of_a_read_only_configuration(expression: str, expected: list[int]) -> None:
    conf = OmegaConf.create({"x": [1], "key": expression})
    OmegaConf.set_readonly(conf, True)
    assert conf.key == expected


@pytest.mark.parametrize(
    "expression", ["${hya.add:${s.l},[2]}", "${hya.add:[],${s.l},[2]}", "${hya.add:[${s.a}],[2]}"]
)
def test_add_resolver_relative_interpolation_in_an_operand(expression: str) -> None:
    conf = OmegaConf.create({"s": {"a": 1, "l": ["${..a}"]}, "key": expression})
    assert conf.key == [1, 2]


def test_add_resolver_of_a_mapping_node_returns_a_copy() -> None:
    conf = OmegaConf.create({"x": {"a": 1}, "key": "${hya.add:${x}}"})
    conf.key["b"] = 2
    assert conf.x == {"a": 1}


##########################################
#     Tests for the returned objects     #
##########################################

OBJECT_EXPRESSIONS = [
    pytest.param("${hya.np.array:[1,2]}", marks=numpy_available),
    pytest.param("${hya.torch.tensor:[1,2]}", marks=torch_available),
    pytest.param("${hya.torch.dtype:float32}", marks=torch_available),
]


@pytest.mark.parametrize("expression", OBJECT_EXPRESSIONS)
def test_resolve_of_an_object_needs_the_allow_objects_flag(expression: str) -> None:
    conf = OmegaConf.create({"key": expression})
    with pytest.raises(UnsupportedValueType, match=r"is not a supported primitive type"):
        OmegaConf.resolve(conf)


@pytest.mark.parametrize("expression", OBJECT_EXPRESSIONS)
def test_resolve_of_an_object_with_the_allow_objects_flag(expression: str) -> None:
    conf = OmegaConf.create({"key": expression}, flags={"allow_objects": True})
    OmegaConf.resolve(conf)
    assert not OmegaConf.is_interpolation(conf, "key")


@pytest.mark.parametrize("expression", OBJECT_EXPRESSIONS)
def test_resolve_of_an_object_with_the_allow_objects_flag_override(expression: str) -> None:
    conf = OmegaConf.create({"key": expression})
    with flag_override(conf, "allow_objects", True):
        OmegaConf.resolve(conf)
    assert not OmegaConf.is_interpolation(conf, "key")


#############################################
#     Tests for the errors of OmegaConf     #
#############################################


def test_resolver_error_has_no_cause() -> None:
    conf = OmegaConf.create({"key": "${hya.ceildiv:1,0}"})
    with pytest.raises(InterpolationResolutionError, match="ZeroDivisionError") as exc_info:
        _ = conf.key
    assert exc_info.value.__cause__ is None


def test_resolver_error_has_the_original_exception_in_the_context_chain() -> None:
    conf = OmegaConf.create({"key": "${hya.ceildiv:1,0}"})
    with pytest.raises(InterpolationResolutionError, match="ZeroDivisionError") as exc_info:
        _ = conf.key
    chain = []
    error: BaseException | None = exc_info.value
    while error is not None:
        chain.append(type(error))
        error = error.__context__
    assert ZeroDivisionError in chain


########################################
#     Tests for composed resolvers     #
########################################


def test_add_resolver_of_two_config_lists() -> None:
    conf = OmegaConf.create({"x": [1, 2], "y": [3], "key": "${hya.add:${x},${y}}"})
    assert conf.key == [1, 2, 3]


def test_add_resolver_of_two_config_lists_does_not_modify_the_lists() -> None:
    conf = OmegaConf.create({"x": [1, 2], "y": [3], "key": "${hya.add:${x},${y}}"})
    assert conf.key == [1, 2, 3]
    assert (conf.x, conf.y) == ([1, 2], [3])


def test_resolver_of_the_output_of_another_resolver() -> None:
    conf = OmegaConf.create({"key": "${hya.int:${hya.ceildiv:11.0,4}}"})
    assert conf.key == 3


def test_iter_join_resolver_of_the_output_of_another_resolver() -> None:
    conf = OmegaConf.create({"key": "${hya.iter_join:[${hya.add:1,2},${hya.len:[1,2]}],-}"})
    assert conf.key == "3-2"


#########################################
#     Tests for the resolved values     #
#########################################

# The resolvers that read a list or a mapping, applied to the node ``x``
WHOLE_VALUE_RESOLVERS = [
    pytest.param("${hya.add:${x}}", id="add"),
    pytest.param("${hya.sha256:${x}}", id="sha256"),
    pytest.param("${hya.iter_join:${x},-}", id="iter_join"),
    pytest.param("${hya.np.array:${x}}", id="np.array", marks=numpy_available),
    pytest.param("${hya.torch.tensor:${x}}", id="torch.tensor", marks=torch_available),
]


@pytest.mark.parametrize("expression", WHOLE_VALUE_RESOLVERS)
def test_whole_value_resolver_resolves_a_nested_interpolation(expression: str) -> None:
    nested = OmegaConf.create({"a": 1, "x": [["${a}"]], "key": expression})
    plain = OmegaConf.create({"x": [[1]], "key": expression})
    assert str(nested.key) == str(plain.key)


@pytest.mark.parametrize("expression", WHOLE_VALUE_RESOLVERS)
def test_whole_value_resolver_missing_value(expression: str) -> None:
    conf = OmegaConf.create({"x": [["???"]], "key": expression})
    with pytest.raises(InterpolationResolutionError, match=r"MissingMandatoryValue"):
        _ = conf.key


@pytest.mark.parametrize(
    ("x", "expression"),
    [
        pytest.param(["${a}"], "${hya.sha256:${x}}", id="list"),
        pytest.param({"b": "${a}"}, "${hya.sha256:${x}}", id="mapping"),
        pytest.param([["${a}"]], "${hya.sha256:${x}}", id="nested"),
        pytest.param(["${a}"], "${hya.sha256:[${x}]}", id="literal-list"),
        pytest.param(1, "${hya.sha256:[${a}]}", id="literal-interpolation"),
    ],
)
def test_sha256_resolver_hash_changes_with_an_interpolated_value(x: Any, expression: str) -> None:
    first = OmegaConf.create({"a": 1, "x": x, "key": expression})
    second = OmegaConf.create({"a": 2, "x": x, "key": expression})
    assert first.key != second.key


def test_sha256_resolver_does_not_depend_on_the_order_of_the_keys() -> None:
    conf = OmegaConf.create(
        {
            "x": {"a": 1, "b": 2},
            "y": {"b": 2, "a": 1},
            "hx": "${hya.sha256:${x}}",
            "hy": "${hya.sha256:${y}}",
        }
    )
    assert conf.hx == conf.hy


def test_sha256_resolver_of_a_mapping() -> None:
    conf = OmegaConf.create({"x": {"b": 2, "a": 1}, "key": "${hya.sha256:${x}}"})
    assert conf.key == "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"


def test_sha256_resolver_of_a_path() -> None:
    conf = OmegaConf.create({"key": "${hya.sha256:${hya.path:/a}}"})
    assert conf.key == sha256_resolver(Path("/a"))


def test_sha256_resolver_of_a_list_of_paths() -> None:
    conf = OmegaConf.create({"x": ["${hya.path:/a}"], "key": "${hya.sha256:${x}}"})
    assert conf.key == sha256_resolver([Path("/a")])


@pytest.mark.parametrize("expression", OBJECT_EXPRESSIONS)
def test_sha256_resolver_of_an_object_without_json_form(expression: str) -> None:
    conf = OmegaConf.create({"key": f"${{hya.sha256:{expression}}}"})
    with pytest.raises(InterpolationResolutionError, match=r"hya.sha256 cannot hash a value"):
        _ = conf.key


@pytest.mark.parametrize(
    "expression",
    [
        "${hya.sha256:${hya.float:nan}}",
        "${hya.sha256:[${hya.float:inf}]}",
        "${hya.sha256:${x}}",
    ],
)
def test_sha256_resolver_of_a_non_finite_float(expression: str) -> None:
    conf = OmegaConf.create({"x": {"a": float("-inf")}, "key": expression})
    with pytest.raises(InterpolationResolutionError, match=r"not JSON compliant"):
        _ = conf.key


def test_sha256_resolver_of_a_mapping_with_mixed_key_types() -> None:
    conf = OmegaConf.create({"x": {1: 2, "a": 3}, "key": "${hya.sha256:${x}}"})
    with pytest.raises(InterpolationResolutionError, match=r"TypeError"):
        _ = conf.key


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("${hya.iter_join:${x},-}", "[1]-2"),
        ("${hya.iter_join:[${x},3],-}", "[[1], 2]-3"),
        ("${hya.iter_join:[[${a}],2],-}", "[1]-2"),
    ],
)
def test_iter_join_resolver_nested_interpolation(expression: str, expected: str) -> None:
    conf = OmegaConf.create({"a": 1, "x": [["${a}"], 2], "key": expression})
    assert conf.key == expected


def test_iter_join_resolver_nested_missing_value_in_a_literal_list() -> None:
    conf = OmegaConf.create({"x": [["???"]], "key": "${hya.iter_join:[${x}],-}"})
    with pytest.raises(InterpolationResolutionError, match=r"MissingMandatoryValue"):
        _ = conf.key


@pytest.mark.parametrize(
    "expression",
    ['${hya.path:"file:///data/run#1"}', '${hya.path:"file:///data/run?a"}'],
)
def test_path_resolver_file_url_with_a_query_or_a_fragment_is_an_error(expression: str) -> None:
    conf = OmegaConf.create({"key": expression})
    with pytest.raises(InterpolationResolutionError, match=r"a query or a fragment"):
        _ = conf.key


def test_path_resolver_file_url_with_an_encoded_fragment_character() -> None:
    conf = OmegaConf.create({"key": "${hya.path:file:///data/run%231}"})
    assert conf.key == Path("/data/run#1").resolve()
