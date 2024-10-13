# hya

<p align="center">
    <a href="https://github.com/durandtibo/hya/actions">
        <img alt="CI" src="https://github.com/durandtibo/hya/workflows/CI/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hya/actions">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/hya/workflows/Nightly%20Tests/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/hya/actions">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/hya/workflows/Nightly%20Package%20Tests/badge.svg">
    </a>
    <br/>
    <a href="https://durandtibo.github.io/hya/">
        <img alt="Documentation" src="https://github.com/durandtibo/hya/workflows/Documentation%20(stable)/badge.svg">
    </a>
    <a href="https://durandtibo.github.io/hya/">
        <img alt="Documentation" src="https://github.com/durandtibo/hya/workflows/Documentation%20(unstable)/badge.svg">
    </a>
    <br/>
    <a href="https://codecov.io/gh/durandtibo/hya">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/hya/branch/main/graph/badge.svg">
    </a>
    <a href="https://codeclimate.com/github/durandtibo/hya/maintainability">
        <img src="https://api.codeclimate.com/v1/badges/372b4c4212452ab0b0ad/maintainability" />
    </a>
    <a href="https://codeclimate.com/github/durandtibo/hya/test_coverage">
        <img src="https://api.codeclimate.com/v1/badges/372b4c4212452ab0b0ad/test_coverage" />
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

`hya` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers.
`hya` is designed to be used with [Hydra](https://github.com/facebookresearch/hydra).
The resolvers can be easily registered in your python project by adding the following lines:

```python
from hya import register_resolvers

register_resolvers()
```

- [Documentation](https://durandtibo.github.io/hya/)
- [Installation](#installation)
- [Contributing](#contributing)
- [API stability](#api-stability)
- [License](#license)

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
pip install hya[all]
```

Please check the [get started page](https://durandtibo.github.io/hya/get_started) to see how to
install only some specific packages or other alternatives to install the library.
The following is the corresponding `hya` versions and tested dependencies.

| `hya`   | `omegaconf`  | `braceexpand`<sup>*</sup> | `numpy`<sup>*</sup> | `torch`<sup>*</sup> | `python`      |
|---------|--------------|---------------------------|---------------------|---------------------|---------------|
| `main`  | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<3.0`       | `>=1.11,<3.0`       | `>=3.9,<3.13` |
| `0.2.4` | `>=2.2,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<3.0`       | `>=1.11,<3.0`       | `>=3.9,<3.13` |
| `0.2.3` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13` |
| `0.2.2` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13` |
| `0.2.1` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13` |
| `0.2.0` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.21,<2.0`       | `>=1.10,<3.0`       | `>=3.9,<3.13` |

<sup>*</sup> indicates an optional dependency

<details>
    <summary>older versions</summary>

| `hya`    | `omegaconf`  | `braceexpand`<sup>*</sup> | `torch`<sup>*</sup> | `python`      |
|----------|--------------|---------------------------|---------------------|---------------|
| `0.1.3`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.13` |
| `0.1.2`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.13` |
| `0.1.1`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.1.0`  | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.0.14` | `>=2.1,<3.0` | `>=0.1.7,<0.2.0`          | `>=1.10,<2.2`       | `>=3.9,<3.12` |
| `0.0.13` | `>=2.1,<3.0` |                           | `>=1.10,<2.1`       | `>=3.9,<3.12` |
| `0.0.12` | `>=2.1,<3.0` |                           | `>=1.10,<2.1`       | `>=3.9,<3.12` |

</details>

## Contributing

Please check the instructions in [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## API stability

:warning: While `hya` is in development stage, no API is guaranteed to be stable from one
release to the next.
In fact, it is very likely that the API will change multiple times before a stable 1.0.0 release.
In practice, this means that upgrading `hya` to a new version will possibly break any code that
was using the old version of `hya`.

## License

`hya` is licensed under BSD 3-Clause "New" or "Revised" license available in [LICENSE](LICENSE)
file.
