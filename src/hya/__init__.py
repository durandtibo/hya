__all__ = ["register_resolvers"]

from hya import resolvers
from hya.import_utils import is_torch_available
from hya.registry import register_resolvers

if is_torch_available():
    from hya import pytorch
