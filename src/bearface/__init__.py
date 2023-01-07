__all__ = ["register_resolvers"]

from bearface import resolvers
from bearface.import_utils import is_torch_available
from bearface.registry import register_resolvers

if is_torch_available():
    from bearface import pytorch
