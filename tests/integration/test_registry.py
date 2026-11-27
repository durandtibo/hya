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


def test_register_resolvers_replace_restores_a_key_replaced_by_another_source() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    ResolverRegistry({KEY: triple}).register_resolvers(replace=True)
    registry.register_resolvers(replace=True)
    assert resolve() == 10


def test_register_resolvers_keeps_a_key_replaced_by_another_source_silently(
    recwarn: pytest.WarningsRecorder,
) -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers()
    ResolverRegistry({KEY: triple}).register_resolvers(replace=True)
    registry.register_resolvers()
    assert (resolve(), len(recwarn)) == (15, 0)


def test_register_resolvers_replace_twice_with_the_same_resolver() -> None:
    registry = ResolverRegistry({KEY: double})
    registry.register_resolvers(replace=True)
    registry.register_resolvers(replace=True)
    assert resolve() == 10


def test_register_resolvers_publishes_the_other_keys_when_warnings_are_errors() -> None:
    code = """
from omegaconf import OmegaConf
from hya import ResolverRegistry

ResolverRegistry({"z.b": len}).register_resolvers()
try:
    ResolverRegistry({"z.a": len, "z.b": max, "z.c": len}).register_resolvers()
except UserWarning as warning:
    assert "for 'z.b': not replaced" in str(warning), warning
else:
    raise AssertionError("no warning")
assert OmegaConf.has_resolver("z.a") and OmegaConf.has_resolver("z.c")
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr


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


#######################################
#     Tests for the accepted keys     #
#######################################


@pytest.fixture(
    params=[
        "hya_test",
        "_hya_test",
        "HyaTest2",
        "hya_test.a",
        "hya_test._a_2.B",
        "_._",
    ]
)
def accepted_key(request: pytest.FixtureRequest) -> Generator[str, None, None]:
    """Give a key of each accepted form and remove it from OmegaConf."""
    yield request.param
    OmegaConf.clear_resolver(request.param)


def test_every_accepted_key_form_resolves(accepted_key: str) -> None:
    ResolverRegistry({accepted_key: double}).register_resolvers()
    assert OmegaConf.create({"key": f"${{{accepted_key}:5}}"}).key == 10


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


def test_second_import_of_hya_emits_one_warning() -> None:
    code = """
import sys
import warnings

import hya

for name in [name for name in sys.modules if name == "hya" or name.startswith("hya.")]:
    del sys.modules[name]
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    import hya
assert len(caught) == 1, caught
assert "'hya.add'" in str(caught[0].message) and "'hya.torch.tensor'" in str(caught[0].message)
"""
    result = run_python(code)
    assert result.returncode == 0, result.stderr
