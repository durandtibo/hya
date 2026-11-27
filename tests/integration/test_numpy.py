from __future__ import annotations

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya.imports import is_numpy_available
from hya.testing import numpy_available, torch_available

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


@numpy_available
@torch_available
@pytest.mark.parametrize(
    "expression",
    [
        "${hya.np.array:${hya.torch.tensor:[1,2]}}",
        "${hya.np.array:${hya.torch.tensor:[1,2]},float32}",
    ],
)
def test_array_resolver_of_a_tensor(expression: str) -> None:
    # The warnings are errors (see filterwarnings), so a warning of the conversion fails the test
    conf = OmegaConf.create({"key": expression})
    assert conf.key.tolist() == [1, 2]


@numpy_available
def test_array_resolver_of_a_mapping_node() -> None:
    conf = OmegaConf.create({"a": 1, "x": {"b": "${a}"}, "key": "${hya.np.array:${x}}"})
    assert conf.key.item() == {"b": 1}


@numpy_available
def test_array_resolver_of_a_mapping_node_with_a_missing_value() -> None:
    conf = OmegaConf.create({"x": {"a": "???"}, "key": "${hya.np.array:${x}}"})
    with pytest.raises(InterpolationResolutionError, match=r"MissingMandatoryValue"):
        _ = conf.key


@numpy_available
def test_array_resolver_of_a_read_only_configuration() -> None:
    conf = OmegaConf.create({"x": [1, 2], "key": "${hya.np.array:${x}}"})
    OmegaConf.set_readonly(conf, True)
    assert conf.key.tolist() == [1, 2]
