# Troubleshooting

This page lists common errors and their solutions.

## How Errors Are Reported

An optional resolver is always registered. When its package is missing, the call raises a
`RuntimeError` that says how to install the package. An error raised by a resolver is reported by
OmegaConf as an `InterpolationResolutionError`. The message names the original exception (for
example `ZeroDivisionError raised while resolving interpolation`) and the original exception is in
the `__context__` chain of the error (`__cause__` is `None`):

```python
import hya
from omegaconf import OmegaConf, errors

try:
    conf = OmegaConf.create({"tensor": "${hya.torch.tensor:[1,2,3]}"})
    print(conf.tensor)
except errors.InterpolationResolutionError as error:
    # Without torch: 'torch' package is required but not installed. ... pip install torch
    print(error)
```

## Resolver Not Found

**Error:** `omegaconf.errors.UnsupportedInterpolationType: Unsupported interpolation type hya.xxx`

**Solution:** Make sure you have imported `hya`:

```python
import hya  # This line is required!
from omegaconf import OmegaConf
```

## Optional Dependency Missing

**Error:**

```text
omegaconf.errors.InterpolationResolutionError: RuntimeError raised while resolving interpolation: 'braceexpand' package is required but not installed
```

The optional resolvers (`hya.braceexpand`, `hya.np.array`, `hya.torch.*`) are always registered, and
need their package when they are called.

**Solution:** Install the required package:

```shell
pip install braceexpand  # or numpy, or torch
```

## Resolver Already Registered

**Error:** `RuntimeError: A resolver is already registered for 'my_key'`

**Solution:** Use `exist_ok=True` to override the resolver of the registry:

```python
@registry.register("my_key", exist_ok=True)
def my_resolver(x):
    return x
```

**Warning:** `A resolver is already registered in OmegaConf for 'my_key': not replaced.`

OmegaConf already has a resolver for each key that the warning lists, and `register_resolvers()` did
not replace them.

**Solution:** Use `registry.register_resolvers(replace=True)` to replace them.

## Invalid Resolver Key

**Error:** `ValueError: Invalid resolver key 'my-key': use names made of letters, digits and _, ...`

**Solution:** Use names joined by dots, for example `my_key` or `my.key`.

## Type Errors in Resolvers

**Error:** `TypeError: unsupported operand type(s) for +: 'int' and 'str'`

**Solution:** Ensure your configuration passes correct types.

Wrong, mixing types:

```yaml
result: ${hya.add:5,abc}
```

Correct, same types:

```yaml
result: ${hya.add:5,10}
```

## Circular References

**Error:** `omegaconf.errors.InterpolationResolutionError: Recursive interpolation detected`

**Solution:** Avoid self-referential configurations.

Wrong, a circular reference:

```yaml
x: ${hya.add:${y},1}
y: ${hya.add:${x},1}
```

Correct, no circular dependency:

```yaml
x: 5
y: ${hya.add:${x},1}
```

## Grammar Error

**Error:** `omegaconf.errors.GrammarParseError: token recognition error at: '~'`

**Solution:** Quote an argument that holds a special character:

```yaml
home: ${hya.path:"~/data"}
```

## Unquoted Brace Pattern

**Error:** `TypeError raised while resolving interpolation: braceexpand_resolver() takes 1
positional argument but 2 were given`

An unquoted comma separates two arguments, even between escaped braces.

**Solution:** Quote the pattern:

```yaml
files: ${hya.braceexpand:"file_{a,b}.txt"}
```

## Missing Colon

**Error:** `omegaconf.errors.InterpolationKeyError: Interpolation key 'hya.pi' not found`

Without a colon, `${hya.pi}` is a reference to the key `pi` of a section `hya`.

**Solution:** Add the colon: `${hya.pi:}`.

## Hydra on Python 3.14

**Error:** `ValueError: badly formed help string`, raised by an application decorated with
`@hydra.main`.

This error comes from `hydra-core` 1.3.8 on Python 3.14, not from `hya`.

**Solution:** Use Python 3.11 to 3.13 with this Hydra release.
