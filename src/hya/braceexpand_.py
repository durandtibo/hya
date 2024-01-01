from collections.abc import Iterator
from unittest.mock import Mock

from hya.imports import check_braceexpand, is_braceexpand_available
from hya.registry import registry

if is_braceexpand_available():
    import braceexpand
else:  # pragma: no cover
    braceexpand = Mock()


def braceexpand_resolver(pattern: str) -> Iterator[str]:
    r"""Implement a resolver to compute a list from a brace expansion of
    pattern.

    Please check https://github.com/trendels/braceexpand for more
    information about the syntax.

    Args:
        pattern: Specifies the pattern of the brace expansion.

    Returns:
        The generator resulting from brace expansion of pattern.

    Example usage:

    ```pycon
    # >>> from omegaconf import OmegaConf
    # >>> conf = OmegaConf.create({"key": "${hya.braceexpand:{1..4}}"})
    # >>> list(conf.key)
    # [1, 2, 3, 4]

    ```
    """
    check_braceexpand()
    return braceexpand.braceexpand(pattern)


if is_braceexpand_available():  # pragma: no cover
    registry.register("hya.braceexpand")(braceexpand_resolver)
