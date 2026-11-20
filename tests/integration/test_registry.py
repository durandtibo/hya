from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest
from omegaconf import OmegaConf
from omegaconf.errors import InterpolationResolutionError

from hya import ResolverRegistry

if TYPE_CHECKING:
    from collections.abc import Generator

KEY = "hya_test.double"


def double(value: int) -> int:
    return value * 2


def triple(value: int) -> int:
    return value * 3


def quadruple(value: int) -> int:
    return value * 4


def half(value: float) -> float:
    return value / 2


@pytest.fixture(autouse=True)
def _clear_resolver() -> Generator[None, None, None]:
    """Remove the resolver used by the tests from OmegaConf."""
    OmegaConf.clear_resolver(KEY)
    yield
    OmegaConf.clear_resolver(KEY)


def resolve(value: int = 5) -> int:
    return OmegaConf.create({"key": f"${{{KEY}:{value}}}"}).key


####################################################
#     Tests for ResolverRegistry.register_lazy     #
####################################################


def test_register_lazy_resolves_with_omegaconf() -> None:
    registry = ResolverRegistry()
    registry.register_lazy(KEY, "json:dumps")
    registry.register_resolvers()
    assert OmegaConf.create({"key": f"${{{KEY}:[1,2]}}"}).key == "[1, 2]"


def test_register_lazy_error_is_raised_by_omegaconf() -> None:
    registry = ResolverRegistry()
    registry.register_lazy(KEY, "hya_missing_module:function")
    registry.register_resolvers()
    conf = OmegaConf.create({"key": f"${{{KEY}:1}}"})
    with pytest.raises(InterpolationResolutionError, match=r"No module named 'hya_missing_module'"):
        _ = conf.key


#########################################################
#     Tests for ResolverRegistry.register_resolvers     #
#########################################################


def test_register_resolvers_publishes_to_omegaconf() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    assert resolve() == 10


def test_register_resolvers_twice_is_silent(recwarn: pytest.WarningsRecorder) -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register_resolvers()
    assert len(recwarn) == 0


def test_register_resolvers_override_warns() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register(KEY, exist_ok=True)(triple)
    with pytest.warns(UserWarning, match=r"A resolver is already registered in OmegaConf"):
        registry.register_resolvers()


def test_register_resolvers_override_keeps_the_published_resolver() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register(KEY, exist_ok=True)(triple)
    with pytest.warns(UserWarning, match=r"not replaced"):
        registry.register_resolvers()
    assert resolve() == 10


def test_register_resolvers_override_replace() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register(KEY, exist_ok=True)(triple)
    registry.register_resolvers(replace=True)
    assert resolve() == 15


def test_register_resolvers_override_replace_twice_is_silent(
    recwarn: pytest.WarningsRecorder,
) -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register(KEY, exist_ok=True)(triple)
    registry.register_resolvers(replace=True)
    registry.register_resolvers()
    assert len(recwarn) == 0


def test_register_resolvers_replace_twice_with_different_resolvers() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    registry.register(KEY, exist_ok=True)(triple)
    registry.register_resolvers(replace=True)
    registry.register(KEY, exist_ok=True)(quadruple)
    registry.register_resolvers(replace=True)
    assert resolve() == 20


def test_register_resolvers_key_of_another_source_is_not_replaced() -> None:
    ResolverRegistry({KEY: triple}).register_resolvers()
    with pytest.warns(UserWarning, match=r"not replaced"):
        ResolverRegistry({KEY: double}).register_resolvers()
    assert resolve() == 15


def test_register_resolvers_key_of_another_source_is_replaced() -> None:
    ResolverRegistry({KEY: triple}).register_resolvers()
    ResolverRegistry({KEY: double}).register_resolvers(replace=True)
    assert resolve() == 10


def test_register_resolvers_publishes_again_after_clear_resolver() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    OmegaConf.clear_resolver(KEY)
    registry.register_resolvers()
    assert resolve() == 10


def test_register_resolvers_does_not_validate_annotations(
    recwarn: pytest.WarningsRecorder,
) -> None:
    ResolverRegistry({KEY: half}).register_resolvers()
    assert resolve(4) == 2.0
    assert len(recwarn) == 0


def test_register_resolvers_error_is_raised_by_omegaconf() -> None:
    ResolverRegistry({KEY: double}).register_resolvers()
    conf = OmegaConf.create({"key": f"${{{KEY}:}}"})
    with pytest.raises(
        InterpolationResolutionError, match=r"missing 1 required positional argument"
    ):
        _ = conf.key


############################
#     Tests for import     #
############################


def run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-W", "error", "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_hya_emits_no_warning() -> None:
    assert run_python("import hya").returncode == 0


def test_register_default_resolvers_after_clear_resolvers() -> None:
    code = """
import hya
from omegaconf import OmegaConf

OmegaConf.clear_resolvers()
assert not OmegaConf.has_resolver("hya.add")
hya.get_default_registry().register_resolvers()
assert OmegaConf.create({"k": "${hya.add:1,2}"}).k == 3
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


def test_register_default_resolvers_twice_is_silent() -> None:
    result = run_python(
        "import hya; hya.get_default_registry().register_resolvers()",
    )
    assert result.returncode == 0, result.stderr


def test_override_of_a_default_resolver_warns_and_replace_applies() -> None:
    code = """
import warnings
import hya
from omegaconf import OmegaConf

registry = hya.get_default_registry()
registry.register("hya.add", exist_ok=True)(lambda *args: "custom")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    registry.register_resolvers()
assert len(caught) == 1 and "not replaced" in str(caught[0].message), caught
assert OmegaConf.create({"k": "${hya.add:1,2}"}).k == 3
registry.register_resolvers(replace=True)
assert OmegaConf.create({"k": "${hya.add:1,2}"}).k == "custom"
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr
