from __future__ import annotations

import logging
from pathlib import Path

from omegaconf import OmegaConf

from hya import (
    is_braceexpand_available,
    is_numpy_available,
    is_torch_available,
    register_resolvers,
)

if is_numpy_available():
    import numpy as np
if is_torch_available():
    import torch

logger = logging.getLogger(__name__)


def check_native_resolvers() -> None:
    logger.info("Checking native resolvers...")
    assert OmegaConf.create({"key": "${hya.add:1,4}"}).key == 5
    assert OmegaConf.create({"key": "${hya.ceildiv:11,4}"}).key == 3
    assert OmegaConf.create({"key": "${hya.len:[1,2,3]}"}).key == 3
    assert OmegaConf.create({"key": "${hya.max:3,4}"}).key == 4
    assert OmegaConf.create({"key": "${hya.min:3,4}"}).key == 3
    assert OmegaConf.create({"key": "${hya.mul:3,4}"}).key == 12
    assert OmegaConf.create({"key": "${hya.path:/my/path}"}).key == Path("/my/path")
    assert OmegaConf.create({"key": "${hya.sub:1,4}"}).key == -3
    assert OmegaConf.create({"key": "${hya.truediv:11,4}"}).key == 2.75


def check_braceexpand_resolvers() -> None:
    if not is_braceexpand_available():
        return
    logger.info("Checking braceexpand resolvers...")
    assert list(OmegaConf.create({"key": r"${hya.braceexpand:\{1..4\}}"}).key) == [
        "1",
        "2",
        "3",
        "4",
    ]


def check_numpy_resolvers() -> None:
    if not is_numpy_available():
        return
    logger.info("Checking numpy resolvers...")
    assert np.array_equal(
        OmegaConf.create({"key": "${hya.np.array:[1, 2, 3]}"}).key, np.array([1, 2, 3])
    )


def check_torch_resolvers() -> None:
    if not is_torch_available():
        return
    logger.info("Checking torch resolvers...")
    assert OmegaConf.create({"key": "${hya.torch.tensor:[1, 2, 3]}"}).key.equal(
        torch.tensor([1, 2, 3])
    )
    assert OmegaConf.create({"key": "${hya.torch.dtype:float}"}).key == torch.float


def main() -> None:
    register_resolvers()
    check_native_resolvers()
    check_braceexpand_resolvers()
    check_numpy_resolvers()
    check_torch_resolvers()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
