from __future__ import annotations

import subprocess
import sys

import pytest

from hya import get_default_registry
from hya.testing import braceexpand_available, numpy_available, torch_available

# torch warns at import if NumPy is not installed, which is a supported setup (see pyproject.toml)
IGNORE_MISSING_NUMPY = "ignore:Failed to initialize NumPy:UserWarning"


def run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-W", "error", "-W", IGNORE_MISSING_NUMPY, "-c", code],
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


##################################################
#     Tests for the missing optional package     #
##################################################


@pytest.mark.parametrize(
    ("package", "expression"),
    [
        ("braceexpand", '${hya.braceexpand:"a{1,2}"}'),
        ("numpy", "${hya.np.array:[1,2]}"),
        ("torch", "${hya.torch.tensor:[1,2]}"),
        ("torch", "${hya.torch.dtype:float32}"),
    ],
)
def test_missing_package_error_says_how_to_install_it(package: str, expression: str) -> None:
    code = f"""
import sys
sys.modules["{package}"] = None
import hya
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

conf = OmegaConf.create({{"k": {expression!r}}})
try:
    conf.k
except InterpolationResolutionError as error:
    message = str(error)
    assert "'{package}' package is required but not installed" in message, message
    assert "pip install {package}" in message, message
else:
    raise AssertionError("no error")
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


def test_default_registry_keys_do_not_depend_on_the_installed_packages() -> None:
    code = """
import sys
for name in ("braceexpand", "numpy", "torch"):
    sys.modules[name] = None
import hya
print(*sorted(hya.get_default_registry().state))
"""
    result = run_python(code)
    assert result.stdout.split() == sorted(get_default_registry().state), result.stderr


################################
#     Tests for the import     #
################################


def test_import_hya_publishes_the_default_resolvers() -> None:
    code = """
import hya
from omegaconf import OmegaConf

assert all(OmegaConf.has_resolver(key) for key in hya.get_default_registry().state)
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


def test_import_hya_default_module_does_not_publish_by_itself() -> None:
    code = """
from unittest.mock import patch

import hya.registry

with patch.object(hya.registry.ResolverRegistry, "register_resolvers") as register_resolvers:
    import importlib
    import hya.default

    importlib.reload(hya.default)
print(register_resolvers.call_count)
"""
    result = run_python(code)
    assert result.stdout.strip() == "0", result.stderr


def test_default_registry_keys_are_namespaced() -> None:
    assert sorted(key for key in get_default_registry().state if not key.startswith("hya.")) == []
