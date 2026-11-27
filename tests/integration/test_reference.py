from __future__ import annotations

from pathlib import Path

import pytest

REFERENCE = Path(__file__).parents[2] / "docs" / "docs" / "refs"

###################################
#     Tests for the reference     #
###################################


@pytest.mark.parametrize(
    "module",
    [
        "hya",
        "hya.braceexpand",
        "hya.imports",
        "hya.numpy",
        "hya.registry",
        "hya.resolvers",
        "hya.testing",
        "hya.torch",
        "hya.utils.config",
    ],
)
def test_public_module_is_in_the_reference(module: str) -> None:
    pages = "\n".join(path.read_text() for path in sorted(REFERENCE.glob("*.md")))
    assert f"::: {module}\n" in pages
