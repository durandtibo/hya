from omegaconf import OmegaConf
from pytest import fixture

from bearface import register_resolvers


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


def test_add_resolver_int2():
    assert OmegaConf.create({"key": "${bf.add:1,4}"}).key == 5


def test_add_resolver_int3():
    assert OmegaConf.create({"key": "${bf.add:1,2,4}"}).key == 7


def test_add_resolver_list2():
    assert OmegaConf.create({"key": "${bf.add:[1,2,3],[4]}"}).key == [1, 2, 3, 4]


def test_add_resolver_list3():
    assert OmegaConf.create({"key": "${bf.add:[1,2,3],[4],[5,6]}"}).key == [1, 2, 3, 4, 5, 6]


def test_add_resolver_str2():
    assert OmegaConf.create({"key": "${bf.add:abc,d}"}).key == "abcd"


def test_add_resolver_str3():
    assert OmegaConf.create({"key": "${bf.add:abc,d,ef}"}).key == "abcdef"


def test_floordiv_resolver():
    assert OmegaConf.create({"key": "${bf.floordiv:11,4}"}).key == 2


def test_neg_resolver():
    assert OmegaConf.create({"key": "${bf.neg:2}"}).key == -2


def test_mul_resolver_int2():
    assert OmegaConf.create({"key": "${bf.mul:3,4}"}).key == 12


def test_mul_resolver_int3():
    assert OmegaConf.create({"key": "${bf.mul:3,4,2}"}).key == 24


def test_mul_resolver_float2():
    assert OmegaConf.create({"key": "${bf.mul:1.5,3}"}).key == 4.5


def test_mul_resolver_float3():
    assert OmegaConf.create({"key": "${bf.mul:1.5,3,2.0}"}).key == 9.0


def test_mul_resolver_list():
    assert OmegaConf.create({"key": "${bf.mul:[1,2,3],3}"}).key == [1, 2, 3, 1, 2, 3, 1, 2, 3]


def test_pow_resolver_int():
    assert OmegaConf.create({"key": "${bf.pow:2,3}"}).key == 8


def test_pow_resolver_float():
    assert OmegaConf.create({"key": "${bf.pow:2.5,3}"}).key == 15.625


def test_sqrt_resolver():
    assert OmegaConf.create({"key": "${bf.sqrt:9}"}).key == 3.0


def test_sha1_resolver():
    assert isinstance(OmegaConf.create({"key": "${bf.sha1:${value}}", "value": "blabla"}).key, str)


def test_sha256_resolver():
    assert isinstance(
        OmegaConf.create({"key": "${bf.sha256:${value}}", "value": "blabla"}).key, str
    )


def test_sub_resolver():
    assert OmegaConf.create({"key": "${bf.sub:1,4}"}).key == -3


def test_truediv_resolver():
    assert OmegaConf.create({"key": "${bf.truediv:11,4}"}).key == 2.75