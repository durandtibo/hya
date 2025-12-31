r"""Implement a braceexpand resolver.

The resolver is registered only if ``braceexpand`` is available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hya.imports import check_braceexpand, is_braceexpand_available
from hya.registry import ResolverRegistry, get_default_registry

if TYPE_CHECKING or is_braceexpand_available():
    import braceexpand
else:  # pragma: no cover
    from hya.utils.fallback.braceexpand import braceexpand

if TYPE_CHECKING:
    from collections.abc import Iterator


registry: ResolverRegistry = (
    get_default_registry() if is_braceexpand_available() else ResolverRegistry()
)


@registry.register("hya.braceexpand")
def braceexpand_resolver(pattern: str) -> Iterator[str]:
    r"""Return an iterator from a brace expansion of pattern.

    Please check https://github.com/trendels/braceexpand for more
    information about the syntax.

    Args:
        pattern: Specifies the pattern of the brace expansion.

    Returns:
        The iterator resulting from brace expansion of pattern.
    """
    check_braceexpand()
    return braceexpand.braceexpand(pattern)
