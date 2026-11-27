# User Guide

This guide explains how to use `hya` in a configuration and in Python. See also [Resolvers](resolvers.md)
for each resolver, [Custom Resolvers](custom_resolvers.md) to add your own, [Using with Hydra](hydra.md)
and [Troubleshooting](troubleshooting.md).

## Basic Usage

### Importing and Automatic Registration

When you import `hya`, all default resolvers are automatically registered with OmegaConf:

```python
import hya
from omegaconf import OmegaConf

# Resolvers are now available
conf = OmegaConf.create({"result": "${hya.add:2,3}"})
print(conf.result)  # Output: 5
```

Importing `hya` is needed once per process, in any module that runs before the values are
accessed.

The optional resolvers (`hya.braceexpand`, `hya.np.array`, `hya.torch.tensor`, `hya.torch.dtype`)
are always registered, so the registry has the same keys on every machine. `import hya` does not
import `numpy`, `torch` or `braceexpand`: the module of an optional resolver is imported on the first
call of that resolver, which raises an error that says how to install the package if it is missing.

### Using Resolvers in YAML Configurations

You can use resolvers directly in YAML configuration files:

```yaml
# config.yaml
model:
  layers: 4
  hidden_size: 256
  # NOTE: This is a simple demonstration of the mul resolver
  # Real neural network parameter counts are much more complex
  approx_params: ${hya.mul:${model.layers},${model.hidden_size}}

training:
  total_samples: 10000
  batch_size: 32
  num_batches: ${hya.ceildiv:${training.total_samples},${training.batch_size}}
  learning_rate: ${hya.pow:10,-3} # 10^-3 = 0.001
```

Load and use the configuration:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.load("config.yaml")
print(conf.model.approx_params)  # Output: 1024
print(conf.training.num_batches)  # Output: 313
print(conf.training.learning_rate)  # Output: 0.001
```

## Interpolation Syntax

A resolver is called with `${key:argument1,argument2,...}`. The syntax is the one of
[OmegaConf](https://omegaconf.readthedocs.io/en/latest/grammar.html); `hya` adds the resolvers
only. The following rules cover the common cases.

```yaml
x: 4
# A reference is an argument like any other
double: ${hya.mul:${x},2} # 8
# Calls can be nested
nested: ${hya.add:${hya.mul:${x},3},1} # 13
# The colon is required, even without argument
tau: ${hya.mul:2,${hya.pi:}} # 6.283185307179586
# An interpolation can be a part of a string
name: run-${hya.add:${x},1} # "run-5"
# Numbers, booleans and null are typed; a quoted value is a string
number: ${hya.add:1,2} # 3
text: ${hya.add:'1','2'} # "12"
# Lists and dictionaries can be written in the arguments
length: ${hya.len:[1,2,3]} # 3
# Quote a string that holds a comma or a space that matters
joined: ${hya.iter_join:[a,b],', '} # "a, b"
# Quote a string that holds a special character, such as ~, =, { or }
home: ${hya.path:"~/data"}
# A backslash keeps the text as is
literal: \${hya.add:1,2} # "${hya.add:1,2}"
```

Spaces around the arguments are ignored. A resolver is called with positional arguments only.

In a Python string, write the interpolation as is (`"${hya.add:1,2}"`); do not use an f-string, which
would read the braces. In YAML, quote a whole value that holds a colon followed by a space, or a
space followed by a `#`, as for any YAML string.

## Using the Values in Python

Accessing a key calls the resolver and returns its output, which can be any Python object:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.create({"output": "${hya.path:/data/output}", "steps": "${hya.add:1,2}"})
print(conf.output.name)  # Output: output
print(conf.steps + 1)  # Output: 4
```

To get a plain dictionary with the resolved values, use `OmegaConf.to_container`:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.create({"model": {"size": "${hya.mul:64,4}"}})
print(OmegaConf.to_container(conf, resolve=True))  # Output: {'model': {'size': 256}}
```

An array, a tensor or a data type is not a value that a configuration can store. `to_container`
returns it, but `OmegaConf.resolve`, which replaces the interpolations in place, needs the
`allow_objects` flag, and `OmegaConf.to_yaml(conf, resolve=True)` does not support it:

```python
import hya
from omegaconf import OmegaConf, flag_override

conf = OmegaConf.create({"dtype": "${hya.torch.dtype:float32}"})
with flag_override(conf, "allow_objects", True):
    OmegaConf.resolve(conf)
print(conf.dtype)  # Output: torch.float32
```

`OmegaConf.to_yaml(conf)`, without `resolve=True`, writes the interpolations as they are, so use it
to save a configuration.

## Common Use Cases

### Path Construction

Build file paths dynamically:

```yaml
paths:
  root: /data
  project: myproject
  version: v1

  # Build paths using iter_join
  data_dir: ${hya.iter_join:[${paths.root},${paths.project},${paths.version}],/}
  train_file: ${hya.iter_join:[${paths.data_dir},train.csv],/}

  # Use path resolver for proper Path objects
  model_checkpoint: ${hya.path:${paths.data_dir}/models/checkpoint.pth}

  # A tilde must be quoted in an interpolation (unquoted, it is a grammar error)
  home_dir: ${hya.path:"~/data"}
```

### Mathematical Computations

Perform calculations in your configuration:

```yaml
model:
  embedding_dim: 512
  num_heads: 8
  head_dim: ${hya.floordiv:${model.embedding_dim},${model.num_heads}} # 64

training:
  total_steps: 100000
  warmup_ratio: 0.1
  # 100000 * 0.1 is the float 10000.0: cast it back to an integer with hya.int
  warmup_steps: ${hya.int:${hya.mul:${training.total_steps},${training.warmup_ratio}}} # 10000

  # Calculate batch size for distributed training
  per_device_batch_size: 16
  num_devices: 4
  global_batch_size: ${hya.mul:${training.per_device_batch_size},${training.num_devices}}
```

### Data Type Specifications (PyTorch)

Specify tensor data types in configuration:

```yaml
model:
  dtype: ${hya.torch.dtype:float32}
  use_half_precision: false
  compute_dtype: ${hya.torch.dtype:float16}

data:
  class_weights: [1, 2, 5]
  weights: ${hya.torch.tensor:${data.class_weights}} # tensor([1, 2, 5])
  # The data type is the second argument of the tensor resolver: its name or a torch.dtype
  float_weights: ${hya.torch.tensor:${data.class_weights},float32} # tensor([1., 2., 5.])
  same_dtype_weights: ${hya.torch.tensor:${data.class_weights},${model.dtype}}
```

The NumPy resolver takes the data type as a string too: `${hya.np.array:[1,2,3],float32}`.

### Versioning and Hashing

Generate consistent identifiers:

```yaml
experiment:
  model_name: resnet50
  dataset: imagenet
  augmentation: heavy

  # Create a unique experiment ID
  full_name: ${experiment.model_name}_${experiment.dataset}_${experiment.augmentation}
  experiment_id: ${hya.sha256:${experiment.full_name}}

  # Use for reproducible paths
  output_dir: ${hya.iter_join:[outputs,${experiment.experiment_id}],/}

model:
  name: resnet
  depth: 50
model_id: ${hya.sha256:${model}} # The hash of the whole section
```

`hya.sha256` hashes the resolved content of a value: a string as is, any other value as canonical
JSON, so the order of the keys does not matter. A value without a JSON form, such as an array, a
tensor or a non-finite float, raises an error. See [`hya.sha256`](resolvers.md#hyasha256).

### List Operations

Work with lists and sequences:

```yaml
datasets:
  train: [mnist, cifar10, imagenet]
  num_datasets: ${hya.len:${datasets.train}}

  # Join dataset names
  combined_name: ${hya.iter_join:${datasets.train},_} # mnist_cifar10_imagenet
```

### Brace Expansion (requires braceexpand)

Generate multiple values from patterns:

```yaml
files:
  # Expands to a list: file_1.txt, file_2.txt, ..., file_5.txt
  pattern: ${hya.braceexpand:"file_{1..5}.txt"}

  # Expands to a list: train_a.json, train_b.json, train_c.json
  train_configs: ${hya.braceexpand:"train_{a,b,c}.json"}
```

The pattern must be quoted in an interpolation. The result is a list (it has a length, can be
indexed and can be read several times), so it can be used by other resolvers such as
`hya.iter_join`.

### Working with Complex Data Types

Create NumPy arrays and PyTorch tensors:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.create(
    {
        "numpy_array": "${hya.np.array:[[1,2,3],[4,5,6]]}",
        "torch_tensor": "${hya.torch.tensor:[1.0,2.0,3.0]}",
        "torch_dtype": "${hya.torch.dtype:float32}",
    }
)

print(type(conf.numpy_array))  # <class 'numpy.ndarray'>
print(type(conf.torch_tensor))  # <class 'torch.Tensor'>
print(conf.torch_dtype)  # torch.float32
```

### Combining Multiple Resolvers

Chain resolvers for complex operations:

```yaml
model:
  base_size: 64
  multiplier: 4
  layers: 3

  # Compute total size: (64 * 4) * 3 = 768
  intermediate_size: ${hya.mul:${model.base_size},${model.multiplier}}
  total_size: ${hya.mul:${model.intermediate_size},${model.layers}}
```

### Using Resolvers with OmegaConf Features

Combine resolvers with OmegaConf's native features:

```yaml
# Use resolvers with the oc.env resolver of OmegaConf
paths:
  root: /data
  project: ${oc.env:PROJECT_NAME,default_project}
  output: ${hya.iter_join:[${paths.root},${paths.project}],/}

# Use resolvers with Hydra overrides
model:
  size: 512 # Can be overridden via the command line: model.size=1024
  doubled_size: ${hya.mul:${model.size},2}
```

## Best Practices

### Configuration Organization

Organize your configurations for maintainability:

```yaml
# Good: Use resolvers to avoid duplication
model:
  hidden_size: 768
  num_layers: 12
  total_hidden: ${hya.mul:${model.hidden_size},${model.num_layers}}

# Avoid: Hardcoding computed values
# total_hidden: 9216  # If you change hidden_size, this becomes incorrect
```

### Type Safety

Use appropriate resolvers for type safety:

```yaml
# Good: Use correct division operators
samples: 1000
batch_size: 32
num_batches: ${hya.ceildiv:${samples},${batch_size}} # Integer result: 32

# Avoid: Using wrong division type
# num_batches: ${hya.truediv:${samples},${batch_size}}  # Float result: 31.25
```

### Performance Considerations

Resolvers are evaluated lazily when accessed:

```python
conf = OmegaConf.create(
    {"slow_computation": "${hya.pow:2,1000}", "fast_value": 42}  # Not computed yet
)

# Only computed when accessed
result = conf.slow_computation  # Computed here
```

OmegaConf does not cache the output of a resolver: every access of an interpolation calls the
resolver again, even when several keys point to the same interpolation. Compute an expensive
value once in Python and store it in the configuration if it is used many times:

```yaml
model:
  vocab_size: 50000
  embedding_dim: 512
  total_embeddings: ${hya.mul:${model.vocab_size},${model.embedding_dim}}

layer1:
  input_size: ${model.total_embeddings} # Calls hya.mul at each access

layer2:
  input_size: ${model.total_embeddings} # Calls hya.mul at each access
```
