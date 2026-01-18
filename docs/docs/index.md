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

`hya` is a library of custom [OmegaConf](https://github.com/omry/omegaconf) resolvers.
`hya` is designed to be used with [Hydra](https://github.com/facebookresearch/hydra).
The default resolvers are automatically registered when you import `hya`.
You can also register custom resolvers by adding the following lines:

```python
from hya import get_default_registry

registry = get_default_registry()

@registry.register("multiply")
def multiply_resolver(x, y):
    return x * y

registry.register_resolvers()
```

## API stability

:warning: While `hya` is in development stage, no API is guaranteed to be stable from one
release to the next. In fact, it is very likely that the API will change multiple times before a
stable 1.0.0 release. In practice, this means that upgrading `hya` to a new version will
possibly break any code that was using the old version of `hya`.

## License

`hya` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](https://github.com/durandtibo/hya/blob/main/LICENSE) file.
