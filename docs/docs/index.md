# Home

<p align="center">
    <a href="https://github.com/durandtibo/hya/actions/workflows/ci.yaml">
        <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/durandtibo/hya/ci.yaml?branch=main&label=CI&logo=github"></a>
    <a href="https://github.com/durandtibo/hya/actions/workflows/nightly-package.yaml">
        <img alt="Nightly Package Tests" src="https://img.shields.io/github/actions/workflow/status/durandtibo/hya/nightly-package.yaml?label=nightly&logo=github"></a>
    <a href="https://codecov.io/gh/durandtibo/hya">
        <img alt="Codecov" src="https://img.shields.io/codecov/c/github/durandtibo/hya?logo=codecov"></a>
    <a href="https://durandtibo.github.io/hya/">
        <img alt="Documentation (stable)" src="https://img.shields.io/badge/docs-stable-blue?logo=readthedocs&logoColor=white"></a>
    <br/>
    <a href="https://pypi.org/project/hya/">
        <img alt="PyPI version" src="https://img.shields.io/pypi/v/hya?logo=pypi&logoColor=white"></a>
    <a href="https://pypi.org/project/hya/">
        <img alt="Python" src="https://img.shields.io/pypi/pyversions/hya?logo=python&logoColor=white"></a>
    <a href="https://opensource.org/licenses/BSD-3-Clause">
        <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/hya"></a>
    <br/>
    <a href="https://github.com/astral-sh/ruff">
        <img alt="Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
        <img alt="Doc style: google" src="https://img.shields.io/badge/docstyle-google-3666d6"></a>
    <a href="https://scorecard.dev/viewer/?uri=github.com/durandtibo/hya">
        <img alt="OpenSSF Scorecard" src="https://img.shields.io/ossf-scorecard/github.com/durandtibo/hya?label=openssf%20scorecard"></a>
    <br/>
    <a href="https://pepy.tech/project/hya">
        <img alt="Downloads" src="https://img.shields.io/pepy/dt/hya"></a>
    <a href="https://pepy.tech/project/hya">
        <img alt="Monthly downloads" src="https://img.shields.io/pepy/dm/hya"></a>
    <a href="https://github.com/durandtibo/hya/stargazers">
        <img alt="GitHub stars" src="https://img.shields.io/github/stars/durandtibo/hya?logo=github"></a>
</p>

## Overview

`hya` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers designed to be
used with [Hydra](https://github.com/facebookresearch/hydra). A resolver is a function that a
configuration calls with the syntax `${key:argument,...}`. With `hya`, a configuration can compute
values (arithmetic and math functions), build paths and identifiers, and create NumPy arrays or
PyTorch tensors, instead of repeating hand-computed values.

## How it works

1. `import hya` registers the resolvers with OmegaConf. No other call is needed.
2. A configuration calls a resolver by its key, which starts with `hya.`.
3. OmegaConf calls the resolver when the value is accessed, with the referenced values of the
   configuration as arguments.

The required dependency is `omegaconf`. A few resolvers need an optional package (NumPy, PyTorch or
braceexpand), which is imported only when one of them is called.

## Quick Start

Install the library:

```shell
pip install hya
```

Then import `hya` and use the resolvers in a configuration:

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
  learning_rate: ${hya.pow:10,-3} # 0.001

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

See [Using with Hydra](hydra.md) for multiple configuration files, command line overrides and the
supported Python versions.

## Registering Custom Resolvers

You can extend `hya` with your own resolvers:

```python
from hya import get_default_registry
from omegaconf import OmegaConf

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

See [Custom Resolvers](custom_resolvers.md) to override, load lazily and test your resolvers.

## Available Resolvers

`hya` provides 24 built-in resolvers, plus 4 that need an optional package. All keys start with
`hya.`:

| Category           | Resolvers                                                    |
| ------------------ | ------------------------------------------------------------ |
| **Arithmetic**     | `add`, `sub`, `mul`, `truediv`, `floordiv`, `ceildiv`, `neg` |
| **Math Functions** | `pow`, `sqrt`, `exp`, `log`, `log10`, `sinh`, `asinh`        |
| **Comparison**     | `max`, `min`                                                 |
| **Casts**          | `int`, `float`                                               |
| **Collections**    | `len`, `sum`                                                 |
| **Constants**      | `pi`                                                         |
| **Paths**          | `path`, `iter_join`                                          |
| **Hashing**        | `sha256`                                                     |
| **Optional**       | `braceexpand`, `np.array`, `torch.tensor`, `torch.dtype`     |

## Where to go next

| Page                                    | Content                                          |
| --------------------------------------- | ------------------------------------------------ |
| [Get Started](get_started.md)           | Installation and optional dependencies           |
| [User Guide](user_guide.md)             | Syntax, common use cases and values in Python    |
| [Resolvers](resolvers.md)               | Reference of every resolver                      |
| [Custom Resolvers](custom_resolvers.md) | Add your own resolvers to a registry             |
| [Using with Hydra](hydra.md)            | Hydra applications, overrides and multiple files |
| [Troubleshooting](troubleshooting.md)   | Common errors and their solutions                |
| [Design Choices](design.md)             | How `hya` is designed, why, and the trade-offs   |
| [Properties](properties.md)             | The rules `hya` guarantees, and what it does not |

## API stability

:warning: While `hya` is in development stage, no API is guaranteed to be stable from one
release to the next. In fact, it is very likely that the API will change multiple times before a
stable 1.0.0 release. In practice, this means that upgrading `hya` to a new version will
possibly break any code that was using the old version of `hya`.

## License

`hya` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](https://github.com/durandtibo/hya/blob/main/LICENSE) file.
