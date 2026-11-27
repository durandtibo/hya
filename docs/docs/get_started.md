# Get Started

It is highly recommended to install in
a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
to keep your system in order.

## Installing with `uv` (recommended)

The following command installs the latest version of the library:

```shell
uv pip install hya
```

To make the package as slim as possible, only the packages required to use `hya` are installed.
This minimal installation includes only `omegaconf`, which is sufficient for using all the core
resolvers.

### Installing Optional Dependencies

`hya` provides additional resolvers that require optional dependencies:

```shell
# Install all optional dependencies, including pytest (the testing extra)
uv pip install 'hya[all]'

# Install specific optional dependencies
uv pip install hya braceexpand  # For hya.braceexpand resolver
uv pip install hya numpy        # For hya.np.array resolver
uv pip install hya torch        # For hya.torch.tensor and hya.torch.dtype resolvers
uv pip install 'hya[testing]'   # For the pytest marks of hya.testing
```

### Dependency Matrix

The following table shows which resolvers require which packages:

| Resolver           | Required Package     | Description                     |
| ------------------ | -------------------- | ------------------------------- |
| `hya.braceexpand`  | `braceexpand>=0.1.7` | Brace expansion patterns        |
| `hya.np.array`     | `numpy>=2.0`         | NumPy array creation            |
| `hya.torch.tensor` | `torch>=2.4`         | PyTorch tensor creation         |
| `hya.torch.dtype`  | `torch>=2.4`         | PyTorch data type specification |

All other resolvers work with the base installation (only `omegaconf` required).

If you try to use a resolver that requires an optional package without installing it, you'll receive
a helpful error message indicating which package needs to be installed, for example
`'torch' package is required but not installed. ... pip install torch`.

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
