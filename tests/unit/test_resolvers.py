from __future__ import annotations

import math
from pathlib import Path

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import GrammarParseError, InterpolationResolutionError

from hya.resolvers import path_resolver


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


def test_path_resolver_file_prefix_is_case_sensitive() -> None:
    assert path_resolver("File:/my/path") == Path.cwd() / "File:" / "my" / "path"


def test_pi_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.pi:}"}).key == math.pi


def test_sha256_resolver() -> None:
    assert isinstance(
        OmegaConf.create({"key": "${hya.sha256:${value}}", "value": "blabla"}).key, str
    )
