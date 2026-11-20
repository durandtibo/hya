from __future__ import annotations

from omegaconf import OmegaConf

from hya.testing import braceexpand_available


@braceexpand_available
def test_braceexpand_resolver() -> None:
    assert OmegaConf.has_resolver("hya.braceexpand")


@braceexpand_available
def test_braceexpand_resolver_resolves_a_list() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"file_{1..3}.txt"}'})
    assert isinstance(conf.key, list)


@braceexpand_available
def test_braceexpand_resolver_output() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"file_{1..3}.txt"}'})
    assert OmegaConf.to_container(conf, resolve=True) == {
        "key": ["file_1.txt", "file_2.txt", "file_3.txt"]
    }


@braceexpand_available
def test_braceexpand_resolver_can_be_dumped() -> None:
    conf = OmegaConf.create({"key": '${hya.braceexpand:"a{1,2}"}'})
    assert OmegaConf.to_yaml(conf, resolve=True) == "key:\n- a1\n- a2\n"
