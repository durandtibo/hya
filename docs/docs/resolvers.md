# Resolvers

:book: This page provides comprehensive documentation for all resolvers implemented in `hya`.

## Overview

`hya` provides over 20 built-in resolvers for use in OmegaConf/Hydra configurations. Resolvers are
organized into the following categories:

- **Arithmetic Operations**: Basic mathematical operations (add, subtract, multiply, divide)
- **Advanced Math**: Transcendental and special functions (exp, log, sqrt, powers)
- **Comparison**: Min/max operations
- **Path Utilities**: Path creation and manipulation
- **String Utilities**: Joining and hashing
- **Utility Functions**: Length, negation, constants
- **Optional Resolvers**: Require additional packages (NumPy, PyTorch, braceexpand)

All resolvers are automatically available after importing `hya`.

## Default Resolvers

These resolvers are available with the base installation (no optional dependencies required).

### Standard Library Resolvers

These resolvers are registered as the standard library callable itself, with no wrapper: the
behaviour, the accepted arguments and the error messages are the ones of the callable. See the
documentation of the callable for the details.

| Key            | Callable            | Example                            | Result  |
| -------------- | ------------------- | ---------------------------------- | ------- |
| `hya.sub`      | `operator.sub`      | `${hya.sub:100,30}`                | `70`    |
| `hya.truediv`  | `operator.truediv`  | `${hya.truediv:10,4}`              | `2.5`   |
| `hya.floordiv` | `operator.floordiv` | `${hya.floordiv:100,32}`           | `3`     |
| `hya.neg`      | `operator.neg`      | `${hya.neg:5}`                     | `-5`    |
| `hya.pow`      | `operator.pow`      | `${hya.pow:10,-3}`                 | `0.001` |
| `hya.sqrt`     | `math.sqrt`         | `${hya.sqrt:64}`                   | `8.0`   |
| `hya.exp`      | `math.exp`          | `${hya.exp:0}`                     | `1.0`   |
| `hya.log`      | `math.log`          | `${hya.log:8,2}`                   | `3.0`   |
| `hya.log10`    | `math.log10`        | `${hya.log10:1000}`                | `3.0`   |
| `hya.sinh`     | `math.sinh`         | `${hya.sinh:0}`                    | `0.0`   |
| `hya.asinh`    | `math.asinh`        | `${hya.asinh:0}`                   | `0.0`   |
| `hya.max`      | `max`               | `${hya.max:10,25,15}`              | `25`    |
| `hya.min`      | `min`               | `${hya.min:10,25,15}`              | `10`    |
| `hya.len`      | `len`               | `${hya.len:[1,2,3]}`               | `3`     |
| `hya.sum`      | `sum`               | `${hya.sum:[1,2,3]}`               | `6`     |
| `hya.int`      | `int`               | `${hya.int:${hya.mul:100000,0.1}}` | `10000` |
| `hya.float`    | `float`             | `${hya.float:3}`                   | `3.0`   |

Examples with interpolations:

```yaml
dataset:
  total_samples: 60000
  val_samples: 10000
  train_samples: ${hya.sub:${dataset.total_samples},${dataset.val_samples}} # 50000
  warmup_ratio: ${hya.truediv:1000,${dataset.total_samples}} # 0.016666...

model:
  embedding_dim: 512
  head_dim: ${hya.floordiv:${model.embedding_dim},8} # 64
  scale_factor: ${hya.sqrt:${model.embedding_dim}} # 22.627...
  layer_sizes: [128, 256, 512, 1024]
  num_layers: ${hya.len:${model.layer_sizes}} # 4
  actual_layers: ${hya.max:${model.num_layers},8} # 8
  total_units: ${hya.sum:${model.layer_sizes}} # 1920
```

`hya.int` casts the float of a computation back to an integer, and `hya.sum` adds the elements of a
list (`hya.add` takes values: `${hya.add:${model.layer_sizes}}` returns the list). `bool` and `str`
have no resolver: `bool("false")` is `True`, and `str` is what an interpolation already does.

### Arithmetic Operations

#### `hya.add`

Adds multiple values together.

**Syntax:** `${hya.add:value1,value2,...}`

**Example:**

```yaml
# Simple addition
total: ${hya.add:10,20} # Result: 30

# Multiple values
sum: ${hya.add:1,2,3,4,5} # Result: 15

# With references
training:
  train_samples: 50000
  val_samples: 10000
  total_samples: ${hya.add:${training.train_samples},${training.val_samples}} # Result: 60000
```

**Equivalent Python:**

```python
value = value1 + value2 + value3 + ...
```

**Note:** The arguments are never modified: `${hya.add:${x},[3]}` returns a new list and leaves
`x` unchanged. At least one argument is required.

#### `hya.mul`

Multiplies multiple values together.

**Syntax:** `${hya.mul:value1,value2,...}`

**Example:**

```yaml
# Simple multiplication
area: ${hya.mul:10,20} # Result: 200

# Multiple values
volume: ${hya.mul:5,10,2} # Result: 100

# Compute total parameters
model:
  layers: 12
  hidden_size: 768
  total_params: ${hya.mul:${model.layers},${model.hidden_size}} # Result: 9216
```

**Equivalent Python:**

```python
value = object1 * object2 * object3 * ...
```

**Note:** The arguments are never modified and are meant to be numbers. Repeating a list of the
configuration (`${hya.mul:${x},2}` with `x: [1, 2]`) is not supported and raises an error. At least
one argument is required.

#### `hya.ceildiv`

Performs ceiling division (rounds up to nearest integer).

**Syntax:** `${hya.ceildiv:dividend,divisor}`

**Example:**

```yaml
batches: ${hya.ceildiv:100,32} # Result: 4

# Calculate number of batches needed
training:
  samples: 10000
  batch_size: 64
  num_batches: ${hya.ceildiv:${training.samples},${training.batch_size}} # Result: 157
```

**Equivalent Python:**

```python
value = -(dividend // -divisor)  # Canonical implementation (no floating point)
# Alternative (but may have precision issues with large integers):
# value = math.ceil(dividend / divisor)
```

**Use Case:** Calculating the number of batches needed to process all samples.

### Constants

#### `hya.pi`

Returns the mathematical constant π (pi).

**Syntax:** `${hya.pi:}`

**Example:**

```yaml
pi_value: ${hya.pi:} # Result: 3.14159...

geometry:
  radius: 5
  circumference: ${hya.mul:2,${hya.pi:},${geometry.radius}} # Result: 31.41...
```

**Equivalent Python:**

```python
import math

value = math.pi
```

### Path Utilities

#### `hya.path`

Converts a string, a path-like object, or a `file:` URL, to a resolved `pathlib.Path` object with user expansion.

**Syntax:** `${hya.path:path_string}`

**Example:**

```yaml
data_dir: ${hya.path:/data/datasets}
model_path: ${hya.path:"~/models/checkpoint.pth"}
local_file: ${hya.path:file:///data/file.txt}
url_decoded: ${hya.path:file:///data/my%20file.txt} # /data/my file.txt
```

**Equivalent Python:**

```python
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

path = os.fspath(path)
url = urlparse(path)
if url.scheme == "file":
    if url.netloc not in ("", "localhost"):
        raise ValueError(f"A file URL with a host is not supported: '{path}'")
    path = unquote(url.path)
value = Path(path).expanduser().resolve()
```

**Notes:**

- Returns a `pathlib.Path` object, which is useful for path operations in Python.
- Only a string that starts with `file:` (the scheme is case-insensitive) is read as a URL (its
  percent-encoding is decoded and its query is dropped). A host other than `localhost`
  (`file://host/a`) raises a `ValueError` instead of being dropped.
- Any other string is a plain path, written as is: `/data/a?b` and `/data/a%20b` keep the `?` and
  the `%20`.
- A `pathlib.Path` is accepted, so the output of `hya.path` can be passed to `hya.path` again.
- A path with a tilde must be quoted in an interpolation: `${hya.path:"~/data"}`. Unquoted, it is a
  grammar error.
- `hya.to_path` was merged into `hya.path` in 0.5.0.

#### `hya.iter_join`

Joins elements of an iterable into a string with a separator.

**Syntax:** `${hya.iter_join:iterable,separator}`

**Example:**

```yaml
# Simple join
joined: ${hya.iter_join:[a,b,c],-} # Result: "a-b-c"

# Build paths
paths:
  root: data
  project: myproject
  version: v1
  full_path: ${hya.iter_join:[${paths.root},${paths.project},${paths.version}],/}
  # Result: "data/myproject/v1"

# Build experiment names
experiment:
  model: resnet
  dataset: cifar10
  name: ${hya.iter_join:[${experiment.model},${experiment.dataset}],_}
  # Result: "resnet_cifar10"
```

**Equivalent Python:**

```python
value = separator.join(map(str, iterable))
```

**Use Case:** Dynamically constructing file paths, experiment names, or configuration strings.

### Utility Functions

#### `hya.sha256`

Computes the SHA-256 hash of an object.

**Syntax:** `${hya.sha256:object}`

**Example:**

```yaml
hash: ${hya.sha256:mystring}
# Result: "bd3ff47540b31e62d4ca6b07794e5a886b0f655fc322730f26ecd65cc7dd5c90"

experiment:
  config: "resnet50_adam_0.001"
  version_id: ${hya.sha256:${experiment.config}}
  # Generates consistent hash for versioning
```

**Equivalent Python:**

```python
import hashlib

value = hashlib.sha256(bytes(str(obj), "utf-8")).hexdigest()
```

**Use Case:** Creating unique identifiers for experiments, cache keys, or version tracking.

## Optional Resolvers

These resolvers require additional packages to be installed.

### Braceexpand

**Package Required:** `braceexpand>=0.1.7`

Install with: `pip install braceexpand`

#### `hya.braceexpand`

Expands brace patterns similar to bash brace expansion.

**Syntax:** `${hya.braceexpand:pattern}`

**Example:**

```yaml
# Numeric range
files: ${hya.braceexpand:"file_{1..5}.txt"}
# Returns a list: [file_1.txt, file_2.txt, ..., file_5.txt]

# Choice expansion
configs: ${hya.braceexpand:"config_{train,val,test}.yaml"}
# Returns a list: [config_train.yaml, config_val.yaml, config_test.yaml]

# Nested patterns
paths: ${hya.braceexpand:"data/{2020..2022}/{jan,feb,mar}"}
# Returns a list: [data/2020/jan, data/2020/feb, ..., data/2022/mar]

# The list can be used by another resolver
names: ${hya.iter_join:${hya.braceexpand:"a{1..3}"},-} # Result: "a1-a2-a3"
```

**Notes:**

- The pattern must be quoted (or its braces escaped) in an interpolation: unquoted, the braces are
  a grammar error of OmegaConf.
- The resolver returns a `list`, not an iterator: it has a length, can be indexed and can be read
  several times. The whole expansion is built at once.

**Reference:** [braceexpand documentation](https://github.com/trendels/braceexpand)

### NumPy

**Package Required:** `numpy>=1.24`

Install with: `pip install numpy`

#### `hya.np.array`

Converts data to a NumPy array.

**Syntax:** `${hya.np.array:data}`

**Example:**

```yaml
# 1D array
vector: ${hya.np.array:[1,2,3,4,5]}

# 2D array
matrix: ${hya.np.array:[[1,2,3],[4,5,6]]}

# Use in configuration
data:
  shape: [28, 28]
  default_image: ${hya.np.array:${data.shape}}
```

**Equivalent Python:**

```python
import numpy as np

value = np.array(data)
```

### PyTorch

**Package Required:** `torch>=2.0`

Install with: `pip install torch`

#### `hya.torch.tensor`

Converts data to a PyTorch tensor.

**Syntax:** `${hya.torch.tensor:data}`

**Example:**

```yaml
# 1D tensor
weights: ${hya.torch.tensor:[0.1,0.2,0.3,0.4]}

# 2D tensor
matrix: ${hya.torch.tensor:[[1,2],[3,4]]}

# Use in model configuration
model:
  default_bias: ${hya.torch.tensor:[0.0,0.0,0.0]}
```

**Equivalent Python:**

```python
import torch

value = torch.tensor(data)
```

#### `hya.torch.dtype`

Creates a PyTorch dtype from its string representation.

**Syntax:** `${hya.torch.dtype:dtype_name}`

**Example:**

```yaml
# Common dtypes
float_type: ${hya.torch.dtype:float32}
int_type: ${hya.torch.dtype:int64}
bool_type: ${hya.torch.dtype:bool}

# Use in model configuration
model:
  compute_dtype: ${hya.torch.dtype:float16}
  parameter_dtype: ${hya.torch.dtype:float32}

training:
  use_mixed_precision: true
  amp_dtype: ${hya.torch.dtype:float16}
```

**Available dtypes:** Common dtype string names include `float`, `float16`, `float32`, `float64`,
`bfloat16`, `int`, `int8`, `int16`, `int32`, `int64`, `uint8`, `bool`, `complex64`, `complex128`.
The exact available dtypes depend on your PyTorch installation. For a complete list, see the
[PyTorch dtype documentation](https://pytorch.org/docs/stable/tensor_attributes.html#torch-dtype).

**Equivalent Python:**

```python
import torch

value = torch.float32  # for dtype_name="float32"
```

**Note:** An unknown name raises an `InterpolationResolutionError` whose message lists the
available dtype names, sorted.

## Resolver Categories Summary

| Category           | Resolvers                                                    |
| ------------------ | ------------------------------------------------------------ |
| **Arithmetic**     | `add`, `sub`, `mul`, `truediv`, `floordiv`, `ceildiv`, `neg` |
| **Math Functions** | `pow`, `sqrt`, `exp`, `log`, `log10`, `sinh`, `asinh`        |
| **Comparison**     | `max`, `min`                                                 |
| **Constants**      | `pi`                                                         |
| **Paths**          | `path`, `iter_join`                                          |
| **Utilities**      | `len`, `sha256`                                              |
| **Optional**       | `braceexpand`, `np.array`, `torch.tensor`, `torch.dtype`     |

## Quick Reference Examples

### Configuration Calculations

```yaml
training:
  total_samples: 60000
  batch_size: 64
  num_batches: ${hya.ceildiv:${training.total_samples},${training.batch_size}}
  learning_rate: ${hya.pow:10,-3}
```

### Path Construction

```yaml
paths:
  base: /data
  project: myproject
  full_path: ${hya.iter_join:[${paths.base},${paths.project},models],/}
```

### Data Type Configuration

```yaml
model:
  dtype: ${hya.torch.dtype:float32}
  input_tensor: ${hya.torch.tensor:[1,2,3]}
```

### Experiment Versioning

```yaml
experiment:
  name: resnet50_cifar10
  hash: ${hya.sha256:${experiment.name}}
```
