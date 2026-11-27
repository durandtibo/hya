from __future__ import annotations

import pkgutil
from pathlib import Path

import pytest

import hya

REFERENCE = Path(__file__).parents[2] / "docs" / "docs" / "refs"
# Every module of ``hya``, except ``hya.utils``, which only groups modules, and its fallbacks,
# which stand for the missing optional packages
PUBLIC_MODULES = [
    "hya",
    *(
        info.name
        for info in pkgutil.walk_packages(hya.__path__, "hya.")
        if info.name != "hya.utils" and not info.name.startswith("hya.utils.fallback")
    ),
]

###################################
#     Tests for the reference     #
###################################


def test_public_modules_are_discovered() -> None:
    # An empty or partial discovery would make the test of the reference pass without a check
    assert {"hya", "hya.default", "hya.numpy", "hya.utils.config"} <= set(PUBLIC_MODULES)


@pytest.mark.parametrize("module", PUBLIC_MODULES)
def test_public_module_is_in_the_reference(module: str) -> None:
    pages = "\n".join(path.read_text() for path in sorted(REFERENCE.glob("*.md")))
    assert f"::: {module}\n" in pages
