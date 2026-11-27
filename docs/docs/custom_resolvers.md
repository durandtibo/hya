# Custom Resolvers

A `ResolverRegistry` is a map from a key to a resolver. Using a resolver of your own takes two
steps: `register` adds it to a registry, and `register_resolvers` publishes the registry to
OmegaConf. The default registry, returned by `get_default_registry()`, holds the resolvers of
`hya`. The signatures are in the [reference](refs/registry.md).

## Creating and Registering Resolvers

You can extend `hya` with your own custom resolvers:

```python
from hya import get_default_registry

# Get the default registry
registry = get_default_registry()


# Register a simple custom resolver
@registry.register("double")
def double_resolver(x):
    """Double the input value."""
    return x * 2


# Register a more complex resolver
@registry.register("clip")
def clip_resolver(value, min_val, max_val):
    """Clip a value between min and max."""
    return max(min_val, min(value, max_val))


# Register custom resolvers with OmegaConf
# Note: Default hya resolvers are already registered on import
# This only registers your custom resolvers added to the default registry
registry.register_resolvers()
```

Now use them in your configuration:

```yaml
hyperparameters:
  base_lr: 0.001
  scaled_lr: ${double:${hyperparameters.base_lr}}

  dropout: 0.7
  clipped_dropout: ${clip:${hyperparameters.dropout},0.0,0.5}
```

A key is made of names joined by dots (`double`, `my.clip_2`), where a name is made of ASCII
letters, digits and `_` and does not start with a digit. Any other key, such as `my-clip`, raises a
`ValueError` when it is registered, and a resolver that is not callable raises a `TypeError`. The
decorator needs the key: `@registry.register` alone raises a `TypeError`.

## Overriding Existing Resolvers

You can override a resolver of the registry with the keyword-only `exist_ok` parameter. The
default resolvers are already published to OmegaConf when `hya` is imported, so
`register_resolvers()` does not replace them silently: it skips the key and emits a warning. Use
`replace=True` to replace the resolver of OmegaConf:

```python
from hya import get_default_registry

registry = get_default_registry()


@registry.register("hya.add", exist_ok=True)
def custom_add(first, *others):
    """Custom add that also prints the result."""
    result = first
    for other in others:
        result = result + other
    print(f"Adding {(first, *others)} = {result}")
    return result


# Without replace=True, the published resolver is kept and a warning is emitted.
# With replace=True, the resolver of OmegaConf is replaced by custom_add.
registry.register_resolvers(replace=True)
```

`register_resolvers` is idempotent: calling it twice changes nothing. A resolver removed from
OmegaConf (for example by `OmegaConf.clear_resolvers()`) is published again. A key that another
source registered in OmegaConf is not overwritten unless `replace=True`: one warning lists the
skipped keys, after the other keys are published. With `replace=True`, every key of the registry is
published, whatever OmegaConf holds. A resolver that another source registers over a key that the
registry already published is kept without a warning: use `replace=True` to publish yours again.

OmegaConf caches the value of the nodes it has already resolved. Replacing a resolver does not clear
this cache for existing configurations: call `OmegaConf.clear_cache(cfg)` to clear it.

With OmegaConf 2.4 and later, the resolvers are published with `annotation_validation="off"`: the
type annotations of a resolver are documentation for readers and type checkers, OmegaConf does not
check them at call time.

## Registering a Resolver Lazily

`register_lazy` registers a resolver as a `"module:function"` string. The module is imported the
first time OmegaConf calls the resolver, not when the resolver is registered. This is how `hya`
registers the resolvers that need a heavy optional package:

```python
from hya import get_default_registry

registry = get_default_registry()
# "statistics" is imported when ${my.mean:...} is called for the first time
registry.register_lazy("my.mean", "statistics:mean")
registry.register_resolvers()
```

```yaml
average: ${my.mean:[1,2,6]} # 3
```

A target that is not formatted as `"module:function"`, with an absolute module name made of names
joined by dots and a function name that is a Python identifier, raises a `ValueError` when it is
registered, and a target that is not a string raises a `TypeError`. An unknown module or function
raises an error on the first call of the resolver. A lazy resolver
cannot receive the special parameters of OmegaConf (`_root_`, `_parent_`, `_node_`): register such
a resolver with `register`.

## Creating Isolated Registries

For advanced use cases, you can create independent registries:

```python
from hya.registry import ResolverRegistry

# Create a new, isolated registry
custom_registry = ResolverRegistry()


@custom_registry.register("custom.multiply")
def multiply(x, y):
    return x * y


# Register only these custom resolvers
custom_registry.register_resolvers()
```

`ResolverRegistry` is also available from the top-level package: `from hya import ResolverRegistry`.
Its constructor takes an optional mapping of keys to resolvers, validated as by `register`; anything
else than a mapping or `None` raises a `TypeError`.

## Reading Configuration Values

A resolver receives a list or a mapping of the configuration as a configuration node (`ListConfig`
or `DictConfig`), and a literal such as `[${x}]` as a list that holds nodes. If your resolver reads
a whole value as data, convert it first with `hya.utils.config.to_plain`: it resolves the
interpolations at any depth, raises on a missing value (`???`), and returns plain lists and
dictionaries without modifying the configuration.

```python
import hya
from hya import get_default_registry
from hya.utils.config import to_plain
from omegaconf import OmegaConf

registry = get_default_registry()


@registry.register("my.unique")
def unique_resolver(values):
    return list(dict.fromkeys(to_plain(values)))


registry.register_resolvers()

conf = OmegaConf.create({"a": "x", "names": ["${a}", "y", "x"], "unique": "${my.unique:${names}}"})
print(conf.unique)  # Output: ['x', 'y']
```

## Reading Other Keys

OmegaConf gives a resolver the special keyword arguments `_root_` (the whole configuration) and
`_parent_` (the node that holds the interpolation) when its signature declares them:

```python
from hya import get_default_registry
from omegaconf import OmegaConf

registry = get_default_registry()


@registry.register("my.sibling")
def sibling_resolver(key, *, _parent_):
    return _parent_[key]


registry.register_resolvers()

conf = OmegaConf.create({"model": {"size": 4, "alias": "${my.sibling:size}"}})
print(conf.model.alias)  # Output: 4
```

## Optional Dependencies in a Resolver

`hya.imports` checks the packages that `hya` knows (`braceexpand`, `numpy` and `torch`):
`is_<package>_available` returns a boolean without importing the package, and `validate_<package>`
raises a `RuntimeError` that says how to install it.

```python
from hya import get_default_registry
from hya.imports import validate_numpy

registry = get_default_registry()


@registry.register("my.zeros")
def zeros_resolver(size):
    validate_numpy()
    import numpy as np

    return np.zeros(size)


registry.register_resolvers()
```

## Testing with Optional Dependencies

`hya.testing` provides pytest marks that skip a test depending on the installed packages. Install it
with the `testing` extra (`pip install 'hya[testing]'`).

| Mark                        | The test runs when             |
| --------------------------- | ------------------------------ |
| `braceexpand_available`     | `braceexpand` is installed     |
| `braceexpand_not_available` | `braceexpand` is not installed |
| `numpy_available`           | `numpy` is installed           |
| `numpy_not_available`       | `numpy` is not installed       |
| `torch_available`           | `torch` is installed           |
| `torch_not_available`       | `torch` is not installed       |

```python
import hya
from hya.testing import numpy_available
from omegaconf import OmegaConf


@numpy_available
def test_array() -> None:
    conf = OmegaConf.create({"x": "${hya.np.array:[1,2]}"})
    assert conf.x.tolist() == [1, 2]
```

## Inspecting a Registry

### Checking for Resolvers

Check if a resolver is registered:

```python
from hya import get_default_registry

registry = get_default_registry()

# Check if a resolver exists
if registry.has_resolver("hya.add"):
    print("add resolver is available")

# List all registered resolvers
for key in registry.state.keys():
    print(f"Registered: {key}")
```

### Accessing Registry State

```python
from hya import get_default_registry

registry = get_default_registry()

# Get all registered resolvers: a read-only mapping (use registry.register to add one)
resolvers_dict = registry.state

# Count resolvers
print(f"Total resolvers: {len(resolvers_dict)}")

# Check specific resolvers
core_resolvers = [k for k in resolvers_dict.keys() if k.startswith("hya.")]
print(f"Core hya resolvers: {len(core_resolvers)}")
```
