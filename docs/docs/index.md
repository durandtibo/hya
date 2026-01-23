# Home

<p align="center">
    <a href="https://github.com/durandtibo/hya/actions/workflows/ci.yaml">
        <img alt="CI" src="https://github.com/durandtibo/hya/actions/workflows/ci.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hya/actions/workflows/nightly-tests.yaml">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/hya/actions/workflows/nightly-tests.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hya/actions/workflows/nightly-package.yaml">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/hya/actions/workflows/nightly-package.yaml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/durandtibo/hya">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/hya/branch/main/graph/badge.svg">
    </a>
    <br/>
    <a href="https://durandtibo.github.io/hya/">
        <img alt="Documentation" src="https://github.com/durandtibo/hya/actions/workflows/docs.yaml/badge.svg">
    </a>
    <a href="https://durandtibo.github.io/hya/dev/">
        <img alt="Documentation" src="https://github.com/durandtibo/hya/actions/workflows/docs-dev.yaml/badge.svg">
    </a>
    <br/>
    <a href="https://github.com/psf/black">
        <img  alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/%20style-google-3666d6.svg">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;">
    </a>
    <a href="https://github.com/guilatrova/tryceratops">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/try%2Fexcept%20style-tryceratops%20%F0%9F%A6%96%E2%9C%A8-black">
    </a>
    <br/>
    <a href="https://pypi.org/project/hya/">
        <img alt="PYPI version" src="https://img.shields.io/pypi/v/hya">
    </a>
    <a href="https://pypi.org/project/hya/">
        <img alt="Python" src="https://img.shields.io/pypi/pyversions/hya.svg">
    </a>
    <a href="https://opensource.org/licenses/BSD-3-Clause">
        <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/hya">
    </a>
    <br/>
    <a href="https://pepy.tech/project/hya">
        <img  alt="Downloads" src="https://static.pepy.tech/badge/hya">
    </a>
    <a href="https://pepy.tech/project/hya">
        <img  alt="Monthly downloads" src="https://static.pepy.tech/badge/hya/month">
    </a>
    <br/>
</p>

## Overview

`hya` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers designed to be used with [Hydra](https://github.com/facebookresearch/hydra). It provides a comprehensive set of resolvers for mathematical operations, path manipulation, data type conversions, and more.

## Quick Start

The default resolvers are automatically registered when you import `hya`:

```python
import hya
from omegaconf import OmegaConf

# Use resolvers in your configuration
conf = OmegaConf.create(
    {
        "batch_size": 32,
        "num_samples": 1000,
        "num_batches": "${hya.ceildiv:${num_samples},${batch_size}}",
        "learning_rate": "${hya.pow:10,-3}",  # 0.001
    }
)

print(conf.num_batches)  # Output: 32
print(conf.learning_rate)  # Output: 0.001
```

### Using with Hydra

Create a configuration file `config.yaml`:

```yaml
model:
  input_dim: 784
  hidden_dim: 256
  output_dim: 10

training:
  batch_size: 32
  num_epochs: 10
  learning_rate: ${hya.pow:10,-3}  # 0.001

paths:
  data_dir: ${hya.path:/data}
  model_dir: ${hya.iter_join:[${paths.data_dir},models,v1],/}

experiment:
  name: mnist_classifier
  id: ${hya.sha256:${experiment.name}}
```

Then use it in your Python script:

```python
import hya
import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig):
    print(f"Learning rate: {cfg.training.learning_rate}")
    print(f"Model dir: {cfg.paths.model_dir}")
    print(f"Experiment ID: {cfg.experiment.id}")


if __name__ == "__main__":
    main()
```

## Registering Custom Resolvers

You can extend `hya` with your own custom resolvers:

```python
from hya import get_default_registry

registry = get_default_registry()


@registry.register("multiply")
def multiply_resolver(x, y):
    return x * y


# Register the custom resolver with OmegaConf
registry.register_resolvers()

# Now use it in your configuration
conf = OmegaConf.create({"result": "${multiply:5,3}"})
print(conf.result)  # Output: 15
```

## Available Resolvers

`hya` provides over 20 built-in resolvers organized into categories:

- **Mathematical operations**: `add`, `sub`, `mul`, `truediv`, `floordiv`, `ceildiv`, `pow`, `sqrt`, `neg`, `max`, `min`, `exp`, `log`, `log10`, `sinh`, `asinh`
- **Constants**: `pi`
- **Path utilities**: `path`, `to_path`, `iter_join`
- **Utilities**: `len`, `sha256`
- **Optional (with dependencies)**:
  - NumPy: `np.array`
  - PyTorch: `torch.tensor`, `torch.dtype`
  - Braceexpand: `braceexpand`

See the [Resolvers](resolvers.md) page for complete documentation of all resolvers.

## API stability

:warning: While `hya` is in development stage, no API is guaranteed to be stable from one
release to the next. In fact, it is very likely that the API will change multiple times before a
stable 1.0.0 release. In practice, this means that upgrading `hya` to a new version will
possibly break any code that was using the old version of `hya`.

## License

`hya` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](https://github.com/durandtibo/hya/blob/main/LICENSE) file.
