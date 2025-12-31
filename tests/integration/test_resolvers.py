from __future__ import annotations

from omegaconf import OmegaConf


def test_add_resolver() -> None:
    assert OmegaConf.has_resolver("hya.add")


def test_asinh_resolver() -> None:
    assert OmegaConf.has_resolver("hya.asinh")


def test_ceildiv_resolver() -> None:
    assert OmegaConf.has_resolver("hya.ceildiv")


def test_exp_resolver() -> None:
    assert OmegaConf.has_resolver("hya.exp")


def test_floordiv_resolver() -> None:
    assert OmegaConf.has_resolver("hya.floordiv")


def test_len_resolver() -> None:
    assert OmegaConf.has_resolver("hya.len")


def test_iter_join_resolver() -> None:
    assert OmegaConf.has_resolver("hya.iter_join")


def test_log_resolver() -> None:
    assert OmegaConf.has_resolver("hya.log")


def test_log10_resolver() -> None:
    assert OmegaConf.has_resolver("hya.log10")


def test_max_resolver() -> None:
    assert OmegaConf.has_resolver("hya.max")


def test_min_resolver() -> None:
    assert OmegaConf.has_resolver("hya.min")


def test_mul_resolver() -> None:
    assert OmegaConf.has_resolver("hya.mul")


def test_neg_resolver() -> None:
    assert OmegaConf.has_resolver("hya.neg")


def test_path_resolver() -> None:
    assert OmegaConf.has_resolver("hya.path")


def test_pi_resolver() -> None:
    assert OmegaConf.has_resolver("hya.pi")


def test_pow_resolver() -> None:
    assert OmegaConf.has_resolver("hya.pow")


def test_sqrt_resolver() -> None:
    assert OmegaConf.has_resolver("hya.sqrt")


def test_sha256_resolver() -> None:
    assert OmegaConf.has_resolver("hya.sha256")


def test_sinh_resolver() -> None:
    assert OmegaConf.has_resolver("hya.sinh")


def test_sub_resolver() -> None:
    assert OmegaConf.has_resolver("hya.sub")


def test_to_path_resolver() -> None:
    assert OmegaConf.has_resolver("hya.to_path")


def test_truediv_resolver() -> None:
    assert OmegaConf.has_resolver("hya.truediv")
