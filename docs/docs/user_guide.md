# User Guide

This guide provides comprehensive information on using `hya` in your projects.

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

### Using Resolvers in YAML Configurations

You can use resolvers directly in YAML configuration files:

```yaml
# config.yaml
model:
  layers: 4
  hidden_size: 256
  # Simplified example: just layers × hidden_size for demonstration
  approx_params: ${hya.mul:${model.layers},${model.hidden_size}}

training:
  total_samples: 10000
  batch_size: 32
  num_batches: ${hya.ceildiv:${training.total_samples},${training.batch_size}}
  learning_rate: ${hya.pow:10,-3}  # 10^-3 = 0.001
```

Load and use the configuration:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.load("config.yaml")
print(conf.model.approx_params)      # Output: 1024
print(conf.training.num_batches)     # Output: 313
print(conf.training.learning_rate)   # Output: 0.001
```

## Integration with Hydra

`hya` is designed to work seamlessly with [Hydra](https://github.com/facebookresearch/hydra).

### Basic Hydra Example

**config.yaml:**
```yaml
dataset:
  name: mnist
  train_samples: 60000
  val_samples: 10000
  total_samples: ${hya.add:${dataset.train_samples},${dataset.val_samples}}

model:
  type: cnn
  channels: [32, 64, 128]
  num_layers: ${hya.len:${model.channels}}

training:
  batch_size: 64
  epochs: 10
  steps_per_epoch: ${hya.ceildiv:${dataset.train_samples},${training.batch_size}}

paths:
  root: /data
  train: ${hya.iter_join:[${paths.root},${dataset.name},train],/}
  val: ${hya.iter_join:[${paths.root},${dataset.name},val],/}

experiment:
  name: ${dataset.name}_${model.type}
  version: ${hya.sha256:${experiment.name}}
```

**train.py:**
```python
import hya
import hydra
from omegaconf import DictConfig

@hydra.main(version_base=None, config_path=".", config_name="config")
def train(cfg: DictConfig):
    print(f"Dataset: {cfg.dataset.name}")
    print(f"Total samples: {cfg.dataset.total_samples}")
    print(f"Model layers: {cfg.model.num_layers}")
    print(f"Steps per epoch: {cfg.training.steps_per_epoch}")
    print(f"Train path: {cfg.paths.train}")
    print(f"Experiment version: {cfg.experiment.version}")

if __name__ == "__main__":
    train()
```

### Multi-Config with Hydra

You can use `hya` resolvers across multiple configuration files:

**config.yaml:**
```yaml
defaults:
  - model: resnet
  - optimizer: adam

experiment:
  name: ${model.name}_${optimizer.name}
  seed: 42
  version: ${hya.sha256:${experiment.name}_${experiment.seed}}
```

**model/resnet.yaml:**
```yaml
name: resnet
depth: 50
width_multiplier: 1.0
effective_depth: ${hya.mul:${model.depth},${model.width_multiplier}}
```

**optimizer/adam.yaml:**
```yaml
name: adam
lr: ${hya.pow:10,-4}  # 0.0001
betas: [0.9, 0.999]
```

## Custom Resolvers

### Creating and Registering Custom Resolvers

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

# Make sure resolvers are registered with OmegaConf
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

### Overriding Existing Resolvers

You can override existing resolvers using the `exist_ok` parameter:

```python
from hya import get_default_registry

registry = get_default_registry()

@registry.register("hya.add", exist_ok=True)
def custom_add(*args):
    """Custom add that also prints the result."""
    result = sum(args)
    print(f"Adding {args} = {result}")
    return result

registry.register_resolvers()
```

### Creating Isolated Registries

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
```

### Mathematical Computations

Perform calculations in your configuration:

```yaml
model:
  embedding_dim: 512
  num_heads: 8
  head_dim: ${hya.floordiv:${model.embedding_dim},${model.num_heads}}  # 64
  
training:
  total_steps: 100000
  warmup_ratio: 0.1
  warmup_steps: ${hya.mul:${training.total_steps},${training.warmup_ratio}}  # 10000
  
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
  input_shape: [3, 224, 224]
  dummy_input: ${hya.torch.tensor:${data.input_shape}}
```

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
```

### List Operations

Work with lists and sequences:

```yaml
datasets:
  train: [mnist, cifar10, imagenet]
  num_datasets: ${hya.len:${datasets.train}}
  
  # Join dataset names
  combined_name: ${hya.iter_join:${datasets.train},_}  # mnist_cifar10_imagenet
```

### Brace Expansion (requires braceexpand)

Generate multiple values from patterns:

```yaml
files:
  # Expands to iterator: file_1.txt, file_2.txt, ..., file_5.txt
  pattern: ${hya.braceexpand:file_{1..5}.txt}
  
  # Expands to: train_a.json, train_b.json, train_c.json
  train_configs: ${hya.braceexpand:train_{a,b,c}.json}
```

## Registry API

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

# Get all registered resolvers
resolvers_dict = registry.state

# Count resolvers
print(f"Total resolvers: {len(resolvers_dict)}")

# Check specific resolvers
core_resolvers = [k for k in resolvers_dict.keys() if k.startswith("hya.")]
print(f"Core hya resolvers: {len(core_resolvers)}")
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

### Error Handling

When using optional resolvers, provide helpful error messages:

```python
import hya
from omegaconf import OmegaConf, errors

try:
    conf = OmegaConf.create({"tensor": "${hya.torch.tensor:[1,2,3]}"})
    print(conf.tensor)
except errors.InterpolationResolutionError as e:
    print(f"Error: PyTorch is required. Install with: pip install torch")
```

### Type Safety

Use appropriate resolvers for type safety:

```yaml
# Good: Use correct division operators
samples: 1000
batch_size: 32
num_batches: ${hya.ceildiv:${samples},${batch_size}}  # Integer result: 32

# Avoid: Using wrong division type
# num_batches: ${hya.truediv:${samples},${batch_size}}  # Float result: 31.25
```

### Performance Considerations

Resolvers are evaluated lazily when accessed:

```python
conf = OmegaConf.create({
    "slow_computation": "${hya.pow:2,1000}",  # Not computed yet
    "fast_value": 42
})

# Only computed when accessed
result = conf.slow_computation  # Computed here
```

Cache expensive computations:

```yaml
# Good: Compute once, reuse
model:
  vocab_size: 50000
  embedding_dim: 512
  total_embeddings: ${hya.mul:${model.vocab_size},${model.embedding_dim}}
  
layer1:
  input_size: ${model.total_embeddings}  # Reuses cached computation

layer2:
  input_size: ${model.total_embeddings}  # Reuses cached computation
```

## Troubleshooting

### Resolver Not Found

**Error:** `omegaconf.errors.UnsupportedInterpolationType: Unsupported interpolation type hya.xxx`

**Solution:** Make sure you have imported `hya`:

```python
import hya  # This line is required!
from omegaconf import OmegaConf
```

### Optional Dependency Missing

**Error:** `ImportError: braceexpand is required to use hya.braceexpand resolver`

**Solution:** Install the required package:

```shell
pip install braceexpand  # or numpy, or torch
```

### Resolver Already Registered

**Error:** `RuntimeError: A resolver is already registered for 'my_key'`

**Solution:** Use `exist_ok=True` to override:

```python
@registry.register("my_key", exist_ok=True)
def my_resolver(x):
    return x
```

### Type Errors in Resolvers

**Error:** `TypeError: unsupported operand type(s) for +: 'int' and 'str'`

**Solution:** Ensure your configuration passes correct types:

```yaml
# Wrong: Mixing types
result: ${hya.add:5,abc}

# Correct: Same types
result: ${hya.add:5,10}
```

### Circular References

**Error:** `omegaconf.errors.InterpolationResolutionError: Circular reference detected`

**Solution:** Avoid self-referential configurations:

```yaml
# Wrong: Circular reference
x: ${hya.add:${y},1}
y: ${hya.add:${x},1}

# Correct: No circular dependency
x: 5
y: ${hya.add:${x},1}
```

## Advanced Topics

### Working with Complex Data Types

Create NumPy arrays and PyTorch tensors:

```python
import hya
from omegaconf import OmegaConf

conf = OmegaConf.create({
    "numpy_array": "${hya.np.array:[[1,2,3],[4,5,6]]}",
    "torch_tensor": "${hya.torch.tensor:[1.0,2.0,3.0]}",
    "torch_dtype": "${hya.torch.dtype:float32}",
})

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
defaults:
  - base_config

# Use resolvers with variable interpolation
paths:
  root: /data
  project: ${oc.env:PROJECT_NAME,default_project}
  output: ${hya.iter_join:[${paths.root},${paths.project}],/}

# Use resolvers with optional values
model:
  size: ${size:512}  # Can be overridden via command line
  doubled_size: ${hya.mul:${model.size},2}
```
