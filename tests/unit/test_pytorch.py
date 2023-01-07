import torch
from omegaconf import OmegaConf
from pytest import fixture

from bearface import register_resolvers


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


def test_to_tensor_resolver_number():
    assert OmegaConf.create({"key": "${bf.to_tensor:1.42}"}).key.equal(torch.tensor(1.42))


def test_to_tensor_resolver_list():
    assert OmegaConf.create({"key": "${bf.to_tensor:[1, 2, 3]}"}).key.equal(torch.tensor([1, 2, 3]))
