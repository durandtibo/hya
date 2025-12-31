from __future__ import annotations

import math
from pathlib import Path

import pytest
from omegaconf import OmegaConf

from hya import register_resolvers


@pytest.fixture(scope="module", autouse=True)
def _register() -> None:
    register_resolvers()


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


def test_asinh_resolver_int() -> None:
    assert OmegaConf.create({"key": "${hya.asinh:1}"}).key == 0.881373587019543


def test_asinh_resolver_float() -> None:
    assert OmegaConf.create({"key": "${hya.asinh:1.0}"}).key == 0.881373587019543


def test_ceildiv_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.ceildiv:11,4}"}).key == 3


def test_exp_resolver_int() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.exp:1}"}).key, math.e)


def test_exp_resolver_float() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.exp:1.0}"}).key, math.e)


def test_floordiv_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.floordiv:11,4}"}).key == 2


def test_len_resolver_list() -> None:
    assert OmegaConf.create({"key": "${hya.len:[1,2,3]}"}).key == 3


def test_len_resolver_str() -> None:
    assert OmegaConf.create({"key": "${hya.len:abcdef}"}).key == 6


def test_iter_join_resolver_list_str() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[a,b,c],-}"}).key == "a-b-c"


def test_iter_join_resolver_list_int() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[1,2,3],x}"}).key == "1x2x3"


def test_iter_join_resolver_empty_separator() -> None:
    assert OmegaConf.create({"key": "${hya.iter_join:[a,b,c],''}"}).key == "abc"


def test_log_resolver_int() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.log:2}"}).key, 0.6931471805599453)


def test_log_resolver_float() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.log:2.0}"}).key, 0.6931471805599453)


def test_log_resolver_base_10() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.log:2.0,10}"}).key, 0.3010299956639812)


def test_log10_resolver_int() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.log10:2}"}).key, 0.3010299956639812)


def test_log10_resolver_float() -> None:
    assert math.isclose(OmegaConf.create({"key": "${hya.log10:2.0}"}).key, 0.3010299956639812)


def test_max_resolver_int2() -> None:
    assert OmegaConf.create({"key": "${hya.max:3,4}"}).key == 4


def test_max_resolver_int3() -> None:
    assert OmegaConf.create({"key": "${hya.max:3,4,-1}"}).key == 4


def test_max_resolver_float2() -> None:
    assert OmegaConf.create({"key": "${hya.max:1.2,3.4}"}).key == 3.4


def test_min_resolver_int2() -> None:
    assert OmegaConf.create({"key": "${hya.min:3,4}"}).key == 3


def test_min_resolver_int3() -> None:
    assert OmegaConf.create({"key": "${hya.min:3,4,-1}"}).key == -1


def test_min_resolver_float2() -> None:
    assert OmegaConf.create({"key": "${hya.min:1.2,3.4}"}).key == 1.2


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


def test_neg_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.neg:2}"}).key == -2


def test_path_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.path:/my/path}"}).key == Path("/my/path")


def test_pi_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.pi:}"}).key == math.pi


def test_pow_resolver_int() -> None:
    assert OmegaConf.create({"key": "${hya.pow:2,3}"}).key == 8


def test_pow_resolver_float() -> None:
    assert OmegaConf.create({"key": "${hya.pow:2.5,3}"}).key == 15.625


def test_sqrt_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.sqrt:9}"}).key == 3.0


def test_sha256_resolver() -> None:
    assert isinstance(
        OmegaConf.create({"key": "${hya.sha256:${value}}", "value": "blabla"}).key, str
    )


def test_sinh_resolver_int() -> None:
    assert OmegaConf.create({"key": "${hya.sinh:1}"}).key == 1.1752011936438014


def test_sinh_resolver_float() -> None:
    assert OmegaConf.create({"key": "${hya.sinh:1.0}"}).key == 1.1752011936438014


def test_sub_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.sub:1,4}"}).key == -3


def test_to_path_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.to_path:/my/path/to}"}).key == Path("/my/path/to")


def test_truediv_resolver() -> None:
    assert OmegaConf.create({"key": "${hya.truediv:11,4}"}).key == 2.75
