from omegaconf import OmegaConf
from pytest import fixture, mark

from bearface import is_torch_available, register_resolvers

if is_torch_available():
    import torch

torch_available = mark.skipif(not is_torch_available(), reason="Requires PyTorch")


@fixture(scope="module", autouse=True)
def register() -> None:
    register_resolvers()


@torch_available
def test_to_tensor_resolver_number():
    assert OmegaConf.create({"key": "${bf.to_tensor:1.42}"}).key.equal(torch.tensor(1.42))


@torch_available
def test_to_tensor_resolver_list():
    assert OmegaConf.create({"key": "${bf.to_tensor:[1, 2, 3]}"}).key.equal(torch.tensor([1, 2, 3]))
