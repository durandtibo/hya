from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya import get_default_registry

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
