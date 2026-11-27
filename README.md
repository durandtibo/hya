# hya

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

`hya` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers, designed to
be used with [Hydra](https://github.com/facebookresearch/hydra). With `hya`, a configuration can
compute values instead of repeating hand-computed ones:

- arithmetic and math functions, such as `hya.mul`, `hya.ceildiv` or `hya.sqrt`;
- paths and identifiers, with `hya.path`, `hya.iter_join` and `hya.sha256`;
- NumPy arrays, PyTorch tensors and data types, and brace expansion, with optional dependencies;
- your own resolvers, managed by a registry.

The only required dependency is `omegaconf`. An optional package is imported only when a resolver
that needs it is called.

- [Documentation](https://durandtibo.github.io/hya/)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Available resolvers](#available-resolvers)
- [Contributing](#contributing)
- [API stability](#api-stability)
- [License](#license)

> This page describes the `main` branch. For the latest release, see the
> [stable documentation](https://durandtibo.github.io/hya/). In `0.4.0`, importing `hya` does not
> register the resolvers: call `hya.get_default_registry().register_resolvers()` first.

## Quick start

Install `hya`:

```shell
pip install hya
```

Importing `hya` registers the resolvers, so a configuration can call them with the syntax
`${key:argument,...}`:

```pycon
>>> import hya
>>> from omegaconf import OmegaConf
>>> conf = OmegaConf.create(
...     {
...         "num_samples": 1000,
...         "batch_size": 32,
...         "num_batches": "${hya.ceildiv:${num_samples},${batch_size}}",
...         "learning_rate": "${hya.pow:10,-3}",
...         "run_name": "${hya.iter_join:[mnist,${batch_size}],-}",
...     }
... )
>>> conf.num_batches
32
>>> conf.learning_rate
0.001
>>> conf.run_name
'mnist-32'

```

### Using with Hydra

Install Hydra with `pip install hydra-core`, and add `import hya` to your application. Given the file
`config.yaml`:

```yaml
dataset:
  train_samples: 60000

training:
  batch_size: 64
  steps_per_epoch: ${hya.ceildiv:${dataset.train_samples},${training.batch_size}}
```

the following script prints `938`:

```python
import hya
import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig):
    print(cfg.training.steps_per_epoch)


if __name__ == "__main__":
    main()
```

With `hydra-core` 1.3.8, use Python 3.11 to 3.13: on Python 3.14, Hydra stops with
`ValueError: badly formed help string`. See
[Using with Hydra](https://durandtibo.github.io/hya/main/hydra/).

### Custom resolvers

Add a resolver to the default registry, then publish it to OmegaConf:

```pycon
>>> from hya import get_default_registry
>>> registry = get_default_registry()
>>> @registry.register("multiply")
... def multiply_resolver(x, y):
...     return x * y
>>> registry.register_resolvers()
>>> OmegaConf.create({"result": "${multiply:5,3}"}).result
15

```

See [Custom Resolvers](https://durandtibo.github.io/hya/main/custom_resolvers/) to override a
resolver, load it lazily or build your own registry.

## Available resolvers

| Category       | Resolvers                                                                                                |
| -------------- | -------------------------------------------------------------------------------------------------------- |
| Arithmetic     | `hya.add`, `hya.sub`, `hya.mul`, `hya.truediv`, `hya.floordiv`, `hya.ceildiv`, `hya.neg`                 |
| Math functions | `hya.pow`, `hya.sqrt`, `hya.exp`, `hya.log`, `hya.log10`, `hya.sinh`, `hya.asinh`                        |
| Comparison     | `hya.max`, `hya.min`                                                                                     |
| Casts          | `hya.int`, `hya.float`                                                                                   |
| Collections    | `hya.len`, `hya.sum`                                                                                     |
| Constants      | `hya.pi`                                                                                                 |
| Paths          | `hya.path`, `hya.iter_join`                                                                              |
| Hashing        | `hya.sha256`                                                                                             |
| Optional       | `hya.braceexpand` (braceexpand), `hya.np.array` (NumPy), `hya.torch.tensor`, `hya.torch.dtype` (PyTorch) |

The [resolvers page](https://durandtibo.github.io/hya/main/resolvers/) documents each one.

## Installation

We highly recommend installing
a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).
`hya` can be installed from pip using the following command:

```shell
pip install hya
```

To make the package as slim as possible, only the minimal packages required to use `hya` are
installed.
To include all the packages, you can use the following command:

```shell
pip install 'hya[all]'
```

A single extra can be installed too: `braceexpand`, `numpy`, `torch` (Linux and macOS with Apple
Silicon) or `testing` (the pytest marks of `hya.testing`), for example `pip install 'hya[numpy]'`.

Please check the [get started page](https://durandtibo.github.io/hya/get_started) to see how to
install only some specific packages or other alternatives to install the library.
The following is the corresponding `hya` versions and tested dependencies.

| `hya`   | `omegaconf`  | `braceexpand`<sup>*</sup> | `numpy`<sup>*</sup> | `torch`<sup>*</sup> | `python`       |
| ------- | ------------ | ------------------------- | ------------------- | ------------------- | -------------- |
| `main`  | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=2.0,<3.0`        | `>=2.4,<3.0`        | `>=3.11`       |
| `0.4.0` | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.24,<3.0`       | `>=2.0,<3.0`        | `>=3.10`       |
| `0.3.1` | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.24,<3.0`       | `>=2.0,<3.0`        | `>=3.10,<3.15` |
| `0.3.0` | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.24,<3.0`       | `>=2.0,<3.0`        | `>=3.9,<3.14`  |
| `0.2.4` | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<3.0`       | `>=1.11,<3.0`       | `>=3.9,<3.14`  |
| `0.2.3` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13`  |
| `0.2.2` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13`  |
| `0.2.1` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13`  |
| `0.2.0` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13`  |

<sup>*</sup> indicates an optional dependency

<details>
    <summary>older versions</summary>

| `hya`    | `omegaconf`  | `braceexpand`<sup>*</sup> | `torch`<sup>*</sup> | `python`      |
| -------- | ------------ | ------------------------- | ------------------- | ------------- |
| `0.1.3`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.13` |
| `0.1.2`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.13` |
| `0.1.1`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.1.0`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.0.14` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.0.13` | `>=2.1,<3.0` |                           | `>=1.10,<2.1`       | `>=3.9,<3.12` |
| `0.0.12` | `>=2.1,<3.0` |                           | `>=1.10,<2.1`       | `>=3.9,<3.12` |

</details>

## Contributing

Please check the instructions in [CONTRIBUTING.md](CONTRIBUTING.md).

## API stability

:warning: While `hya` is in development stage, no API is guaranteed to be stable from one
release to the next.
In fact, it is very likely that the API will change multiple times before a stable 1.0.0 release.
In practice, this means that upgrading `hya` to a new version will possibly break any code that
was using the old version of `hya`.

## License

`hya` is licensed under BSD 3-Clause "New" or "Revised" license available in [LICENSE](LICENSE)
file.
