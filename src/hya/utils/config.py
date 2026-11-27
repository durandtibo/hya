r"""Implement helpers to read the values of an OmegaConf
configuration."""

from __future__ import annotations

__all__ = ["to_plain"]

from typing import Any

from omegaconf import OmegaConf


def to_plain(value: Any) -> Any:
    r"""Return ``value`` with its configuration nodes converted to plain,
    resolved objects.

    OmegaConf gives a resolver the configuration node itself
    (``ListConfig`` or ``DictConfig``), and a literal such as ``[${x}]``
    is a plain list that contains nodes. A resolver that reads a whole
    value as text or data must resolve the interpolations of these
    nodes, at any depth. Lists and dictionaries are searched for nodes
    and are returned as new containers, so ``value`` is not modified.
    Any other object (including a tuple) is returned as is.

    Args:
        value: The value to convert.

    Returns:
        The value without configuration nodes.

    Raises:
        omegaconf.errors.MissingMandatoryValue: If a node contains a
            missing value (``???``).

    Example:
        ```pycon
        >>> from omegaconf import OmegaConf
        >>> from hya.utils.config import to_plain
        >>> conf = OmegaConf.create({"a": 1, "x": ["${a}", 2]})
        >>> to_plain(conf.x)
        [1, 2]
        >>> to_plain([conf.x, {"y": conf.x}])
        [[1, 2], {'y': [1, 2]}]

        ```
    """
    if OmegaConf.is_config(value):
        return OmegaConf.to_container(value, resolve=True, throw_on_missing=True)
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    return value
