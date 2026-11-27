r"""Contain the main features of the ``hya`` package.

Importing ``hya`` publishes the default resolvers to OmegaConf, so a
configuration can use them without any other call. The package exposes
``ResolverRegistry`` and ``get_default_registry`` to add your own
resolvers.

Example:
    ```pycon
    >>> import hya
    >>> from omegaconf import OmegaConf
    >>> conf = OmegaConf.create({"steps": "${hya.ceildiv:1000,32}"})
    >>> conf.steps
    32

    ```
"""

from __future__ import annotations

__all__ = ["ResolverRegistry", "get_default_registry"]

from importlib.metadata import PackageNotFoundError, version

from hya.default import get_default_registry
from hya.registry import ResolverRegistry

# Publish the default resolvers to OmegaConf: importing hya is enough to use them
get_default_registry().register_resolvers()

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # Package is not installed, fallback if needed
    __version__ = "0.0.0"
