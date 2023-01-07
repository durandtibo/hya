# Resolvers

:book: This page describes some of the resolvers that are currently implemented.

## Default

### `bf.add`

This resolver adds the two inputs.
The following config

```yaml
value: ${bf.add:object1,object2}
```

is equivalent to:

```python
value = object1 + object2
```

It is possible to add more than 2 inputs.
The following config

```yaml
value: ${bf.add:object1,object2,object3,object4}
```

is equivalent to:

```python
value = object1 + object2 + object3 + object4
```

### `bf.floordiv`

This resolver computes the "true" division between two inputs.
The following config

```yaml
value: ${bf.floordiv:dividend,divisor}
```

is equivalent to:

```python
value = dividend // divisor
```

### `bf.neg`

This resolver computes the negation of the input.
The following config

```yaml
value: ${bf.neg:number}
```

is equivalent to:

```python
value = -number
```

### `bf.mul`

This resolver multiplies the two inputs.
The following config

```yaml
value: ${bf.mul:object1,object2}
```

is equivalent to:

```python
value = object1 * object2
```

It is possible to multiply more than 2 inputs.
The following config

```yaml
value: ${bf.mul:object1,object2,object3,object4}
```

is equivalent to:

```python
value = object1 * object2 * object3 * object4
```

### `bf.pow`

This resolver computes a value to a given power.
The following config

```yaml
value: ${bf.pow:fraction,exponent}
```

is equivalent to:

```python
value = fraction ** exponent
```

### `bf.sqrt`

This resolver computes a squared root value of a number.
The following config

```yaml
value: ${bf.sqrt:number}
```

is equivalent to:

```python
import math

value = math.sqrt(number)
```

### `bf.sha1`

This resolver computes the SHA-1 hash of an object.

### `bf.sha256`

This resolver computes the SHA-256 hash of an object.

### `bf.sub`

This resolver subtracts the two inputs.
The following config

```yaml
value: ${bf.sub:object1,object2}
```

is equivalent to:

```python
value = object1 - object2
```

### `bf.truediv`

This resolver computes the "true" division between two inputs.
The following config

```yaml
value: ${bf.truediv:dividend,divisor}
```

is equivalent to:

```python
value = dividend / divisor
```

## PyTorch

You need to install PyTorch to use these resolvers.

### `bf.to_tensor`

This resolver transforms the input to a ``torch.Tensor``.
The following config

```yaml
value: ${bf.to_tensor:[1,2,3]}
```

is equivalent to:

```python
import torch

value = torch.tensor([1, 2, 3])
```
