# Resolvers

:book: This page provides comprehensive documentation for all resolvers implemented in `hya`.

## Overview

`hya` provides over 20 built-in resolvers for use in OmegaConf/Hydra configurations. Resolvers are organized into the following categories:

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

### Arithmetic Operations

#### `hya.add`

Adds multiple values together.

**Syntax:** `${hya.add:value1,value2,...}`

**Example:**
```yaml
# Simple addition
total: ${hya.add:10,20}  # Result: 30

# Multiple values
sum: ${hya.add:1,2,3,4,5}  # Result: 15

# With references
training:
  train_samples: 50000
  val_samples: 10000
  total_samples: ${hya.add:${training.train_samples},${training.val_samples}}  # Result: 60000
```

**Equivalent Python:**
```python
value = object1 + object2 + object3 + ...
```

#### `hya.sub`

Subtracts the second value from the first.

**Syntax:** `${hya.sub:value1,value2}`

**Example:**
```yaml
remaining: ${hya.sub:100,30}  # Result: 70

dataset:
  total_samples: 60000
  val_samples: 10000
  train_samples: ${hya.sub:${dataset.total_samples},${dataset.val_samples}}  # Result: 50000
```

**Equivalent Python:**
```python
value = object1 - object2
```

#### `hya.mul`

Multiplies multiple values together.

**Syntax:** `${hya.mul:value1,value2,...}`

**Example:**
```yaml
# Simple multiplication
area: ${hya.mul:10,20}  # Result: 200

# Multiple values
volume: ${hya.mul:5,10,2}  # Result: 100

# Compute total parameters
model:
  layers: 12
  hidden_size: 768
  total_params: ${hya.mul:${model.layers},${model.hidden_size}}  # Result: 9216
```

**Equivalent Python:**
```python
value = object1 * object2 * object3 * ...
```

#### `hya.truediv`

Performs "true" division (floating-point division).

**Syntax:** `${hya.truediv:dividend,divisor}`

**Example:**
```yaml
ratio: ${hya.truediv:10,4}  # Result: 2.5

training:
  total_steps: 10000
  warmup_ratio: ${hya.truediv:1000,${training.total_steps}}  # Result: 0.1
```

**Equivalent Python:**
```python
value = dividend / divisor
```

#### `hya.floordiv`

Performs floor division (rounds down to nearest integer).

**Syntax:** `${hya.floordiv:dividend,divisor}`

**Example:**
```yaml
batches: ${hya.floordiv:100,32}  # Result: 3

# Complete batches only
training:
  samples: 10000
  batch_size: 64
  complete_batches: ${hya.floordiv:${training.samples},${training.batch_size}}  # Result: 156
```

**Equivalent Python:**
```python
value = dividend // divisor
```

#### `hya.ceildiv`

Performs ceiling division (rounds up to nearest integer).

**Syntax:** `${hya.ceildiv:dividend,divisor}`

**Example:**
```yaml
batches: ${hya.ceildiv:100,32}  # Result: 4

# Calculate number of batches needed
training:
  samples: 10000
  batch_size: 64
  num_batches: ${hya.ceildiv:${training.samples},${training.batch_size}}  # Result: 157
```

**Equivalent Python:**
```python
value = -(dividend // -divisor)
# or
value = math.ceil(dividend / divisor)
```

**Use Case:** Calculating the number of batches needed to process all samples.

### Advanced Mathematical Functions

#### `hya.pow`

Raises a value to a given power.

**Syntax:** `${hya.pow:base,exponent}`

**Example:**
```yaml
squared: ${hya.pow:5,2}  # Result: 25
cubed: ${hya.pow:2,3}  # Result: 8

# Scientific notation for learning rates
training:
  lr: ${hya.pow:10,-3}  # Result: 0.001
  weight_decay: ${hya.pow:10,-4}  # Result: 0.0001
```

**Equivalent Python:**
```python
value = base ** exponent
```

#### `hya.sqrt`

Computes the square root of a number.

**Syntax:** `${hya.sqrt:number}`

**Example:**
```yaml
side: ${hya.sqrt:64}  # Result: 8.0

model:
  embedding_dim: 512
  scale_factor: ${hya.sqrt:${model.embedding_dim}}  # Result: 22.627...
```

**Equivalent Python:**
```python
import math
value = math.sqrt(number)
```

#### `hya.exp`

Computes the exponential (e^x).

**Syntax:** `${hya.exp:number}`

**Example:**
```yaml
exponential: ${hya.exp:0}  # Result: 1.0
growth: ${hya.exp:1}  # Result: 2.718...
```

**Equivalent Python:**
```python
import math
value = math.exp(number)
```

#### `hya.log`

Computes the logarithm with a given base (default: natural log).

**Syntax:** `${hya.log:number,base}` or `${hya.log:number}` (base e)

**Example:**
```yaml
natural_log: ${hya.log:10}  # Result: 2.302... (ln(10))
log_base_2: ${hya.log:8,2}  # Result: 3.0 (log2(8))
log_base_10: ${hya.log:1000,10}  # Result: 3.0
```

**Equivalent Python:**
```python
import math
value = math.log(number, base)  # or math.log(number) for natural log
```

#### `hya.log10`

Computes the base-10 logarithm.

**Syntax:** `${hya.log10:number}`

**Example:**
```yaml
log_value: ${hya.log10:100}  # Result: 2.0
decades: ${hya.log10:1000}  # Result: 3.0
```

**Equivalent Python:**
```python
import math
value = math.log10(number)
```

#### `hya.sinh`

Computes the hyperbolic sine.

**Syntax:** `${hya.sinh:number}`

**Example:**
```yaml
result: ${hya.sinh:1}  # Result: 1.175...
```

**Equivalent Python:**
```python
import math
value = math.sinh(number)
```

#### `hya.asinh`

Computes the inverse hyperbolic sine.

**Syntax:** `${hya.asinh:number}`

**Example:**
```yaml
result: ${hya.asinh:1}  # Result: 0.881...
```

**Equivalent Python:**
```python
import math
value = math.asinh(number)
```

#### `hya.neg`

Returns the negation of a number.

**Syntax:** `${hya.neg:number}`

**Example:**
```yaml
negative: ${hya.neg:5}  # Result: -5
flipped: ${hya.neg:-10}  # Result: 10
```

**Equivalent Python:**
```python
value = -number
```

### Comparison Functions

#### `hya.max`

Returns the maximum value among multiple inputs.

**Syntax:** `${hya.max:value1,value2,...}`

**Example:**
```yaml
maximum: ${hya.max:10,25,15}  # Result: 25

model:
  min_layers: 4
  max_layers: 12
  requested_layers: 20
  actual_layers: ${hya.min:${model.requested_layers},${model.max_layers}}  # Result: 12
```

**Equivalent Python:**
```python
value = max(value1, value2, value3, ...)
```

#### `hya.min`

Returns the minimum value among multiple inputs.

**Syntax:** `${hya.min:value1,value2,...}`

**Example:**
```yaml
minimum: ${hya.min:10,25,15}  # Result: 10

training:
  requested_lr: 0.1
  max_lr: 0.01
  actual_lr: ${hya.min:${training.requested_lr},${training.max_lr}}  # Result: 0.01
```

**Equivalent Python:**
```python
value = min(value1, value2, value3, ...)
```

### Constants

#### `hya.pi`

Returns the mathematical constant π (pi).

**Syntax:** `${hya.pi:}`

**Example:**
```yaml
pi_value: ${hya.pi:}  # Result: 3.14159...

geometry:
  radius: 5
  circumference: ${hya.mul:2,${hya.pi:},${geometry.radius}}  # Result: 31.41...
```

**Equivalent Python:**
```python
import math
value = math.pi
```

### Path Utilities

#### `hya.path`

Converts a string to a resolved `pathlib.Path` object with user expansion.

**Syntax:** `${hya.path:path_string}`

**Example:**
```yaml
data_dir: ${hya.path:/data/datasets}
model_path: ${hya.path:~/models/checkpoint.pth}
```

**Equivalent Python:**
```python
from pathlib import Path
value = Path(path).expanduser().resolve()
```

**Note:** Returns a `pathlib.Path` object, which is useful for path operations in Python.

#### `hya.to_path`

Converts a string (including file:// URLs) to a `pathlib.Path` with URL decoding.

**Syntax:** `${hya.to_path:path_string}`

**Example:**
```yaml
local_file: ${hya.to_path:file:///data/file.txt}
url_decoded: ${hya.to_path:/path/with%20spaces}
```

**Equivalent Python:**
```python
from pathlib import Path
from urllib.parse import unquote, urlparse
value = Path(unquote(urlparse(path).path)).expanduser().resolve()
```

**Use Case:** Handling file URLs and paths with URL encoding.

#### `hya.iter_join`

Joins elements of an iterable into a string with a separator.

**Syntax:** `${hya.iter_join:iterable,separator}`

**Example:**
```yaml
# Simple join
joined: ${hya.iter_join:[a,b,c],-}  # Result: "a-b-c"

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

#### `hya.len`

Returns the length of an object.

**Syntax:** `${hya.len:object}`

**Example:**
```yaml
list_length: ${hya.len:[1,2,3,4,5]}  # Result: 5

model:
  layer_sizes: [128, 256, 512, 1024]
  num_layers: ${hya.len:${model.layer_sizes}}  # Result: 4
```

**Equivalent Python:**
```python
value = len(obj)
```

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
files: ${hya.braceexpand:file_{1..5}.txt}
# Returns iterator: file_1.txt, file_2.txt, ..., file_5.txt

# Choice expansion
configs: ${hya.braceexpand:config_{train,val,test}.yaml}
# Returns iterator: config_train.yaml, config_val.yaml, config_test.yaml

# Nested patterns
paths: ${hya.braceexpand:data/{2020..2022}/{jan,feb,mar}}
# Returns: data/2020/jan, data/2020/feb, ..., data/2022/mar
```

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

**Available dtypes:** `float`, `float16`, `float32`, `float64`, `bfloat16`, `int`, `int8`, `int16`, `int32`, `int64`, `uint8`, `bool`, `complex64`, `complex128`, etc.

**Equivalent Python:**
```python
import torch
value = torch.float32  # for dtype_name="float32"
```

## Resolver Categories Summary

| Category | Resolvers |
|----------|-----------|
| **Arithmetic** | `add`, `sub`, `mul`, `truediv`, `floordiv`, `ceildiv`, `neg` |
| **Math Functions** | `pow`, `sqrt`, `exp`, `log`, `log10`, `sinh`, `asinh` |
| **Comparison** | `max`, `min` |
| **Constants** | `pi` |
| **Paths** | `path`, `to_path`, `iter_join` |
| **Utilities** | `len`, `sha256` |
| **Optional** | `braceexpand`, `np.array`, `torch.tensor`, `torch.dtype` |

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
