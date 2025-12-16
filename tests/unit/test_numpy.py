from __future__ import annotations

import pytest
from omegaconf import OmegaConf

from hya import is_numpy_available, register_resolvers
from hya.testing import numpy_available

if is_numpy_available():
    import numpy as np


@pytest.fixture(scope="module", autouse=True)
def _register() -> None:
    register_resolvers()


@numpy_available
def test_to_array_resolver_number() -> None:
    assert np.array_equal(OmegaConf.create({"key": "${hya.np.array:1.42}"}).key, np.array(1.42))


@numpy_available
def test_to_array_resolver_list() -> None:
    assert np.array_equal(
        OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"}).key, np.array([1, 2, 3])
    )
