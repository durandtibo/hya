import math
from pathlib import Path

from omegaconf import OmegaConf
from pytest import fixture

from hya import register_resolvers


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


def test_add_resolver_int2():
    assert OmegaConf.create({"key": "${hya.add:1,4}"}).key == 5


def test_add_resolver_int3():
    assert OmegaConf.create({"key": "${hya.add:1,2,4}"}).key == 7


def test_add_resolver_list2():
    assert OmegaConf.create({"key": "${hya.add:[1,2,3],[4]}"}).key == [1, 2, 3, 4]


def test_add_resolver_list3():
    assert OmegaConf.create({"key": "${hya.add:[1,2,3],[4],[5,6]}"}).key == [1, 2, 3, 4, 5, 6]


def test_add_resolver_str2():
    assert OmegaConf.create({"key": "${hya.add:abc,d}"}).key == "abcd"


def test_add_resolver_str3():
    assert OmegaConf.create({"key": "${hya.add:abc,d,ef}"}).key == "abcdef"


def test_asinh_resolver_int():
    assert OmegaConf.create({"key": "${hya.asinh:1}"}).key == 0.881373587019543


def test_asinh_resolver_float():
    assert OmegaConf.create({"key": "${hya.asinh:1.0}"}).key == 0.881373587019543


def test_ceildiv_resolver():
    assert OmegaConf.create({"key": "${hya.ceildiv:11,4}"}).key == 3


def test_floordiv_resolver():
    assert OmegaConf.create({"key": "${hya.floordiv:11,4}"}).key == 2


def test_max_resolver_int2():
    assert OmegaConf.create({"key": "${hya.max:3,4}"}).key == 4


def test_max_resolver_int3():
    assert OmegaConf.create({"key": "${hya.max:3,4,-1}"}).key == 4


def test_max_resolver_float2():
    assert OmegaConf.create({"key": "${hya.max:1.2,3.4}"}).key == 3.4


def test_min_resolver_int2():
    assert OmegaConf.create({"key": "${hya.min:3,4}"}).key == 3


def test_min_resolver_int3():
    assert OmegaConf.create({"key": "${hya.min:3,4,-1}"}).key == -1


def test_min_resolver_float2():
    assert OmegaConf.create({"key": "${hya.min:1.2,3.4}"}).key == 1.2


def test_mul_resolver_int2():
    assert OmegaConf.create({"key": "${hya.mul:3,4}"}).key == 12


def test_mul_resolver_int3():
    assert OmegaConf.create({"key": "${hya.mul:3,4,2}"}).key == 24


def test_mul_resolver_float2():
    assert OmegaConf.create({"key": "${hya.mul:1.5,3}"}).key == 4.5


def test_mul_resolver_float3():
    assert OmegaConf.create({"key": "${hya.mul:1.5,3,2.0}"}).key == 9.0


def test_mul_resolver_list():
    assert OmegaConf.create({"key": "${hya.mul:[1,2,3],3}"}).key == [1, 2, 3, 1, 2, 3, 1, 2, 3]


def test_neg_resolver():
    assert OmegaConf.create({"key": "${hya.neg:2}"}).key == -2


def test_pi_resolver():
    assert OmegaConf.create({"key": "${hya.pi:}"}).key == math.pi


def test_pow_resolver_int():
    assert OmegaConf.create({"key": "${hya.pow:2,3}"}).key == 8


def test_pow_resolver_float():
    assert OmegaConf.create({"key": "${hya.pow:2.5,3}"}).key == 15.625


def test_sqrt_resolver():
    assert OmegaConf.create({"key": "${hya.sqrt:9}"}).key == 3.0


def test_sha1_resolver():
    assert isinstance(OmegaConf.create({"key": "${hya.sha1:${value}}", "value": "blabla"}).key, str)


def test_sha256_resolver():
    assert isinstance(
        OmegaConf.create({"key": "${hya.sha256:${value}}", "value": "blabla"}).key, str
    )


def test_sub_resolver():
    assert OmegaConf.create({"key": "${hya.sub:1,4}"}).key == -3


def test_to_path_resolver():
    assert OmegaConf.create({"key": "${hya.to_path:/my/path/to}"}).key == Path("/my/path/to")


def test_truediv_resolver():
    assert OmegaConf.create({"key": "${hya.truediv:11,4}"}).key == 2.75
