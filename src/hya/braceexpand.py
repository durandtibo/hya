r"""Implement a braceexpand resolver for brace expansion patterns.

This module provides OmegaConf resolvers that use the braceexpand library
to expand string patterns with brace notation (similar to bash brace expansion).
The resolver is registered only if the ``braceexpand`` package is available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from hya.imports import check_braceexpand, is_braceexpand_available

if TYPE_CHECKING or is_braceexpand_available():
    import braceexpand
else:  # pragma: no cover
    from hya.utils.fallback.braceexpand import braceexpand

if TYPE_CHECKING:
    from collections.abc import Iterator


def braceexpand_resolver(pattern: str) -> Iterator[str]:
    r"""Return an iterator from a brace expansion of pattern.

    This resolver expands a string with brace patterns similar to
    bash brace expansion, generating multiple strings from a single
    pattern. Useful for generating lists of similar configuration
    values.

    Please check https://github.com/trendels/braceexpand for more
    information about the syntax.

    Args:
        pattern: Specifies the pattern of the brace expansion.
            Supports numeric ranges (e.g., "file{1..3}.txt"),
            character sequences (e.g., "{a,b,c}"), and nested
            patterns.

    Returns:
        An iterator yielding strings resulting from brace expansion
        of the pattern.

    Note:
        When using brace expansion patterns in OmegaConf, you may need
        to escape or quote the pattern string to avoid conflicts with
        OmegaConf's own syntax for curly braces.
    """
    check_braceexpand()
    return braceexpand.braceexpand(pattern)
