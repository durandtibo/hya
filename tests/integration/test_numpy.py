from __future__ import annotations

from omegaconf import OmegaConf

from hya.imports import is_numpy_available
from hya.testing import numpy_available

if is_numpy_available():
    import numpy as np


@numpy_available
def test_array_resolver() -> None:
    assert OmegaConf.has_resolver("hya.np.array")


@numpy_available
def test_array_resolver_dtype() -> None:
    conf = OmegaConf.create({"key": "${hya.np.array:[1,2],float32}"})
    assert conf.key.dtype == np.float32


@numpy_available
def test_array_resolver_dtype_array() -> None:
    conf = OmegaConf.create({"key": "${hya.np.array:[1,2],float32}"})
    assert np.array_equal(conf.key, np.array([1.0, 2.0], dtype=np.float32))


@numpy_available
def test_array_resolver_dtype_does_not_modify_the_config() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.np.array:${x},float64}"})
    assert conf.key.dtype == np.float64
    assert conf.x == [1, 2]
