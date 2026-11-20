from __future__ import annotations

import subprocess
import sys

import pytest

from hya.testing import braceexpand_available, numpy_available, torch_available


def run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-W", "error", "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


#################################################
#     Tests for the lazy optional resolvers     #
#################################################


@pytest.mark.parametrize("package", ["braceexpand", "numpy", "torch"])
def test_import_hya_does_not_import_optional_packages(package: str) -> None:
    result = run_python(f"import sys, hya; print('{package}' in sys.modules)")
    assert result.stdout.strip() == "False", result.stderr


@pytest.mark.parametrize("module", ["hya.braceexpand", "hya.numpy", "hya.torch"])
def test_import_hya_does_not_import_optional_modules(module: str) -> None:
    result = run_python(f"import sys, hya; print('{module}' in sys.modules)")
    assert result.stdout.strip() == "False", result.stderr


@numpy_available
def test_numpy_is_imported_on_the_first_call_of_the_resolver() -> None:
    code = """
import sys
import hya
from omegaconf import OmegaConf

assert "numpy" not in sys.modules
assert OmegaConf.create({"k": "${hya.np.array:[1,2]}"}).k.tolist() == [1, 2]
assert "numpy" in sys.modules
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


@torch_available
def test_torch_is_imported_on_the_first_call_of_the_resolver() -> None:
    code = """
import sys
import hya
from omegaconf import OmegaConf

assert "torch" not in sys.modules
assert OmegaConf.create({"k": "${hya.torch.tensor:[1,2]}"}).k.tolist() == [1, 2]
assert "torch" in sys.modules
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


@braceexpand_available
def test_braceexpand_is_imported_on_the_first_call_of_the_resolver() -> None:
    code = """
import sys
import hya
from omegaconf import OmegaConf

assert "braceexpand" not in sys.modules
assert list(OmegaConf.create({"k": '${hya.braceexpand:"a{1,2}"}'}).k) == ["a1", "a2"]
assert "braceexpand" in sys.modules
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr
