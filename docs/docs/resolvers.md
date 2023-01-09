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

### `hya.floordiv`

This resolver computes the "true" division between two inputs.
The following config

```yaml
value: ${hya.floordiv:dividend,divisor}
```

is equivalent to:

```python
value = dividend // divisor
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

### `hya.pow`

This resolver computes a value to a given power.
The following config

```yaml
value: ${hya.pow:fraction,exponent}
```

is equivalent to:

```python
value = fraction ** exponent
```

### `hya.sqrt`

This resolver computes a squared root value of a number.
The following config

```yaml
value: ${hya.sqrt:number}
```

is equivalent to:

```python
import math

value = math.sqrt(number)
```

### `hya.sha1`

This resolver computes the SHA-1 hash of an object.

### `hya.sha256`

This resolver computes the SHA-256 hash of an object.

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

This resolver transforms the input string to a ``pathlib.Path``.

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

## PyTorch

You need to install PyTorch to use these resolvers.

### `hya.to_tensor`

This resolver transforms the input to a ``torch.Tensor``.
The following config

```yaml
value: ${hya.to_tensor:[1,2,3]}
```

is equivalent to:

```python
import torch

value = torch.tensor([1, 2, 3])
```
