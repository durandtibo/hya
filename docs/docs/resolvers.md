# Resolvers

:book: This page describes some of the resolvers that are currently implemented.

## Default

### `hya.add`

This resolver adds the two inputs.
The following config

```yaml
value: ${hya.add:object1,object2}
```

is equivalent to:

```python
value = object1 + object2
```

It is possible to add more than 2 inputs.
The following config

```yaml
value: ${hya.add:object1,object2,object3,object4}
```

is equivalent to:

```python
value = object1 + object2 + object3 + object4
```

### `hya.asinh`

This resolver computes the inverse hyperbolic sine of the input.
The following config

```yaml
value: ${hya.asinh:number}
```

is equivalent to:

```python
import math

value = math.asinh(number)
```

### `hya.ceildiv`

This resolver computes the ceiling division between two inputs.
The following config

```yaml
value: ${hya.ceildiv:dividend,divisor}
```

is equivalent to:

```python
value = -(dividend // -divisor)
```

### `hya.exp`

This resolver computes the exponential value of the input.
The following config

```yaml
value: ${hya.exp:number}
```

is equivalent to:

```python
import math

value = math.exp(number)
```

### `hya.floordiv`

This resolver computes the floor division between two inputs.
The following config

```yaml
value: ${hya.floordiv:dividend,divisor}
```

is equivalent to:

```python
value = dividend // divisor
```

### `hya.iter_join`

This resolver converts all items in an iterable to a string and joins them into one string.
The following config

```yaml
value: ${hya.iter_join:[abc,2,def],-}
```

is equivalent to:

```python
value = "-".join(["abc", "2", "def"])
```

### `hya.len`

This resolver returns the length of an object.
The following config

```yaml
value: ${hya.len:[1,2,3]}
```

is equivalent to:

```python
value = len([1, 2, 3])
```

### `hya.log`

This resolver computes the logarithm of the input value to the given base.
The following config

```yaml
value: ${hya.log:number,base}
```

is equivalent to:

```python
import math

value = math.log(number, base)
```

The base parameter is optional and defaults to e (natural logarithm).

### `hya.log10`

This resolver computes the base 10 logarithm of the input value.
The following config

```yaml
value: ${hya.log10:number}
```

is equivalent to:

```python
import math

value = math.log10(number)
```

### `hya.max`

This resolver returns the maximum between multiple values.
The following config

```yaml
value: ${hya.max:value1,value2,value3}
```

is equivalent to:

```python
value = max(value1, value2, value3)
```

### `hya.min`

This resolver returns the minimum between multiple values.
The following config

```yaml
value: ${hya.min:value1,value2,value3}
```

is equivalent to:

```python
value = min(value1, value2, value3)
```

### `hya.mul`

This resolver multiplies the two inputs.
The following config

```yaml
value: ${hya.mul:object1,object2}
```

is equivalent to:

```python
value = object1 * object2
```

It is possible to multiply more than 2 inputs.
The following config

```yaml
value: ${hya.mul:object1,object2,object3,object4}
```

is equivalent to:

```python
value = object1 * object2 * object3 * object4
```

### `hya.neg`

This resolver computes the negation of the input.
The following config

```yaml
value: ${hya.neg:number}
```

is equivalent to:

```python
value = -number
```

### `hya.path`

This resolver transforms the input string to a ``pathlib.Path`` with expansion and resolution.
The following config

```yaml
value: ${hya.path:/my/path}
```

is equivalent to:

```python
from pathlib import Path

value = Path("/my/path").expanduser().resolve()
```

### `hya.pi`

This resolver returns the value of PI.
The following config

```yaml
value: ${hya.pi:}
```

is equivalent to:

```python
import math

value = math.pi
```

### `hya.pow`

This resolver computes a value to a given power.
The following config

```yaml
value: ${hya.pow:base,exponent}
```

is equivalent to:

```python
value = base**exponent
```

### `hya.sha256`

This resolver computes the SHA-256 hash of an object.
The following config

```yaml
value: ${hya.sha256:mystring}
```

is equivalent to:

```python
import hashlib

value = hashlib.sha256(bytes("mystring", "utf-8")).hexdigest()
```

### `hya.sinh`

This resolver computes the hyperbolic sine of the input.
The following config

```yaml
value: ${hya.sinh:number}
```

is equivalent to:

```python
import math

value = math.sinh(number)
```

### `hya.sqrt`

This resolver computes the square root value of a number.
The following config

```yaml
value: ${hya.sqrt:number}
```

is equivalent to:

```python
import math

value = math.sqrt(number)
```

### `hya.sub`

This resolver subtracts the two inputs.
The following config

```yaml
value: ${hya.sub:object1,object2}
```

is equivalent to:

```python
value = object1 - object2
```

### `hya.to_path`

This resolver transforms the input string to a ``pathlib.Path`` with URL decoding support.
The following config

```yaml
value: ${hya.to_path:/my/path}
```

is equivalent to:

```python
from pathlib import Path
from urllib.parse import unquote, urlparse

value = Path(unquote(urlparse("/my/path").path)).expanduser().resolve()
```

### `hya.truediv`

This resolver computes the "true" division between two inputs.
The following config

```yaml
value: ${hya.truediv:dividend,divisor}
```

is equivalent to:

```python
value = dividend / divisor
```

## Braceexpand

You need to install braceexpand to use these resolvers.

### `hya.braceexpand`

This resolver returns an iterator from a brace expansion of pattern.
Please check [braceexpand documentation](https://github.com/trendels/braceexpand) for more information about the syntax.

The following config

```yaml
value: ${hya.braceexpand:file_{a,b,c}.txt}
```

returns an iterator that yields `file_a.txt`, `file_b.txt`, `file_c.txt`.

## NumPy

You need to install NumPy to use these resolvers.

### `hya.np.array`

This resolver transforms the input to a ``numpy.ndarray``.
The following config

```yaml
value: ${hya.np.array:[1,2,3]}
```

is equivalent to:

```python
import numpy as np

value = np.array([1, 2, 3])
```

## PyTorch

You need to install PyTorch to use these resolvers.

### `hya.torch.dtype`

This resolver creates a ``torch.dtype`` from its string representation.
The following config

```yaml
value: ${hya.torch.dtype:float}
```

is equivalent to:

```python
import torch

value = torch.float
```

### `hya.torch.tensor`

This resolver transforms the input to a ``torch.Tensor``.
The following config

```yaml
value: ${hya.torch.tensor:[1,2,3]}
```

is equivalent to:

```python
import torch

value = torch.tensor([1, 2, 3])
```
