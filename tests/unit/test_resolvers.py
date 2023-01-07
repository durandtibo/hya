from omegaconf import OmegaConf
from pytest import fixture

from bearface import register_resolvers


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


def test_add_resolver():
    assert OmegaConf.create({"key": "${bf.add:1,4}"}).key == 5


def test_floordiv_resolver():
    assert OmegaConf.create({"key": "${bf.floordiv:11,4}"}).key == 2


def test_neg_resolver():
    assert OmegaConf.create({"key": "${bf.neg:2}"}).key == -2


def test_mergelist_resolver_1():
    assert OmegaConf.create({"key": "${bf.mergelist:[1,2,3]}"}).key == [1, 2, 3]


def test_mergelist_resolver_2():
    assert OmegaConf.create({"key": "${bf.mergelist:[1,2,3],[2,3,4]}"}).key == [
        1,
        2,
        3,
        2,
        3,
        4,
    ]


def test_mergelist_resolver_3():
    assert OmegaConf.create({"key": "${bf.mergelist:[1,2,3],[2,3,4],[a,b,c]}"}).key == [
        1,
        2,
        3,
        2,
        3,
        4,
        "a",
        "b",
        "c",
    ]


def test_mul_resolver_int():
    assert OmegaConf.create({"key": "${bf.mul:3,4}"}).key == 12


def test_mul_resolver_float():
    assert OmegaConf.create({"key": "${bf.mul:1.5,3}"}).key == 4.5


def test_pow_resolver_int():
    assert OmegaConf.create({"key": "${bf.pow:2,3}"}).key == 8


def test_pow_resolver_float():
    assert OmegaConf.create({"key": "${bf.pow:2.5,3}"}).key == 15.625


def test_repeatlist_resolver_list():
    assert OmegaConf.create({"key": "${bf.repeatlist:[1,2,3],3}"}).key == [
        1,
        2,
        3,
        1,
        2,
        3,
        1,
        2,
        3,
    ]


def test_repeatlist_resolver_str():
    assert OmegaConf.create({"key": "${bf.repeatlist:abc,2}"}).key == ["abc", "abc"]


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
