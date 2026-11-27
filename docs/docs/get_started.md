# Get Started

## Requirements

- Python 3.11 or later.
- `omegaconf>=2.2,<3.0`, installed with `hya`.

It is highly recommended to install in
a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
to keep your system in order.

## Installing with `uv` (recommended)

The following command installs the latest release of the library:

```shell
uv pip install hya
```

## Installing with `pip`

```shell
pip install hya
```

To make the package as slim as possible, only the packages required to use `hya` are installed.
This minimal installation includes only `omegaconf`, which is sufficient for using all the core
resolvers.

## Installing Optional Dependencies

`hya` provides additional resolvers that require optional dependencies. Each one has an extra, which
installs a supported version of the package:

```shell
uv pip install 'hya[braceexpand]' # For the hya.braceexpand resolver
uv pip install 'hya[numpy]'       # For the hya.np.array resolver
uv pip install 'hya[torch]'       # For the hya.torch.tensor and hya.torch.dtype resolvers
uv pip install 'hya[testing]'     # For the pytest marks of hya.testing

# Install all optional dependencies, including pytest (the testing extra)
uv pip install 'hya[all]'
```

The quotes are needed by some shells, such as `zsh`. Several extras can be combined, for example
`'hya[numpy,torch]'`.

The `torch` extra installs PyTorch on Linux and on macOS with Apple Silicon only. On another
platform it installs nothing: follow the
[PyTorch installation instructions](https://pytorch.org/get-started/locally/).

### Dependency Matrix

The following table shows which features require which packages:

| Feature            | Required Package          | Description                     |
| ------------------ | ------------------------- | ------------------------------- |
| `hya.braceexpand`  | `braceexpand>=0.1.7,<0.2` | Brace expansion patterns        |
| `hya.np.array`     | `numpy>=2.0,<3.0`         | NumPy array creation            |
| `hya.torch.tensor` | `torch>=2.4,<3.0`         | PyTorch tensor creation         |
| `hya.torch.dtype`  | `torch>=2.4,<3.0`         | PyTorch data type specification |
| `hya.testing`      | `pytest>=9.0,<10.0`       | Pytest marks                    |

All other resolvers work with the base installation (only `omegaconf` required).

The optional resolvers are registered even when their package is missing. Calling one of them then
raises an error that says which package to install, for example
`'torch' package is required but not installed. ... pip install torch`.

## Checking the installation

The following script prints the version of `hya` and resolves a configuration:

```python
import hya
from omegaconf import OmegaConf

print(hya.__version__)
conf = OmegaConf.create({"result": "${hya.add:1,2}"})
print(conf.result)  # Output: 3
```

The next step is the [User Guide](user_guide.md).

## Installing from source

To install `hya` from source, you can follow the steps below. First, you will need to
install [`uv`](https://docs.astral.sh/uv/). `uv` is used to manage and install
the dependencies.
If `uv` is already installed on your machine, you can skip this step. You can check the `uv`
installation by running the following command:

```shell
uv --version
```

Then, you can clone the git repository:

```shell
git clone git@github.com:durandtibo/hya.git
```

Then, create the virtual environment and install `hya` with the following commands:

```shell
cd hya
make setup-venv
source .venv/bin/activate
```

`make setup-venv` installs `uv` if it is missing and updates it, creates a Python 3.14 virtual
environment in `.venv` (it replaces an existing one), and installs `hya` in editable mode with all
its dependencies. It asks you to confirm that `.venv` can be cleared: answer `y`, as any other
answer stops the installation.

Once the virtual environment is activated, you can install the dependencies again with the following
command:

```shell
inv env.install
```

You can also use this command to restore the environment to the versions of the lock file
(`uv.lock`). To update the dependencies to more recent versions, use `inv env.update`.

Finally, you can test the installation with the following commands:

```shell
inv test.unit --cov
inv test.integration
```

Run `inv --list` to see all the tasks.
