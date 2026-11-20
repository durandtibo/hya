r"""Implement a braceexpand resolver for brace expansion patterns.

This module provides OmegaConf resolvers that use the braceexpand
library to expand string patterns with brace notation (similar to bash
brace expansion). The resolver is registered only if the ``braceexpand``
package is available.
"""

from __future__ import annotations

__all__ = ["braceexpand_resolver"]

from typing import TYPE_CHECKING

from hya.imports import check_braceexpand, is_braceexpand_available

if TYPE_CHECKING or is_braceexpand_available():
    import braceexpand
else:  # pragma: no cover
    from hya.utils.fallback.braceexpand import braceexpand


def braceexpand_resolver(pattern: str) -> list[str]:
    r"""Return the list of the strings of a brace expansion of pattern.

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
        The list of the strings resulting from the brace expansion of
        the pattern. It is a list (and not an iterator), so it has a
        length, can be indexed and can be read several times. The
        whole expansion is built at once.

    Note:
        When using brace expansion patterns in OmegaConf, you need
        to quote the pattern string (``${hya.braceexpand:"a{1,2}"}``)
        or to escape the braces to avoid conflicts with OmegaConf's
        own syntax for curly braces.

    Example:
        ```pycon
        >>> import hya
        >>> from omegaconf import OmegaConf
        >>> conf = OmegaConf.create({"key": '${hya.braceexpand:"file_{1..3}.txt"}'})
        >>> list(conf.key)
        ['file_1.txt', 'file_2.txt', 'file_3.txt']
        >>> len(conf.key)
        3

        ```
    """
    check_braceexpand()
    return list(braceexpand.braceexpand(pattern))
