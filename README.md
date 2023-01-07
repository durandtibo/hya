# :bear: bearface :bear:

<p align="center">
   <a href="https://github.com/durandtibo/bearface/actions">
      <img alt="CI" src="https://github.com/durandtibo/bearface/workflows/CI/badge.svg?event=push&branch=main">
   </a>
    <a href="https://pypi.org/project/bearface/">
      <img alt="PYPI version" src="https://img.shields.io/pypi/v/bearface">
    </a>
   <a href="https://pypi.org/project/bearface/">
      <img alt="Python" src="https://img.shields.io/pypi/pyversions/bearface.svg">
   </a>
   <a href="https://opensource.org/licenses/BSD-3-Clause">
      <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/bearface">
   </a>
   <a href="https://codecov.io/gh/durandtibo/bearface">
      <img alt="Codecov" src="https://codecov.io/gh/durandtibo/bearface/branch/main/graph/badge.svg">
   </a>
   <a href="https://github.com/psf/black">
     <img  alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
   </a>
   <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
     <img  alt="Doc style: google" src="https://img.shields.io/badge/%20style-google-3666d6.svg">
   </a>
   <br/>
</p>

## Overview

`bearface` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers.
The resolvers can be easily registered in your python project by adding the following lines:

```python
from bearface import register_resolvers

register_resolvers()
```

- [Documentation](https://durandtibo.github.io/bearface/)
- [Installation](#installation)
- [Contributing](#contributing)
- [API stability](#api-stability)
- [License](#license)

## Installation

We highly recommend installing
a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/).
`bearface` can be installed from pip using the following command:

```shell
pip install bearface
```

To make the package as slim as possible, only the minimal packages required to use `bearface` are
installed.
To include all the packages, you can use the following command:

```shell
pip install bearface[all]
```

Please check the [get started page](https://durandtibo.github.io/bearface/get_started) to see how to
install only some specific packages or other alternatives to install the library.

## Contributing

Please check the instructions in [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## API stability

:warning: While `bearface` is in development stage, no API is guaranteed to be stable from one
release to the next.
In fact, it is very likely that the API will change multiple times before a stable 1.0.0 release.
In practice, this means that upgrading `bearface` to a new version will possibly break any code that
was using the old version of `bearface`.

## License

`bearface` is licensed under BSD 3-Clause "New" or "Revised" license available in [LICENSE](LICENSE)
file.
