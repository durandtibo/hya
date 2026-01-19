# Get Started

It is highly recommended to install in
a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
to keep your system in order.

## Installing with `pip` (recommended)

The following command installs the latest version of the library:

```shell
pip install hya
```

To make the package as slim as possible, only the packages required to use `hya` are installed.
This minimal installation includes only `omegaconf`, which is sufficient for using all the core resolvers.

### Installing Optional Dependencies

`hya` provides additional resolvers that require optional dependencies:

```shell
# Install all optional dependencies
pip install 'hya[all]'

# Install specific optional dependencies
pip install hya braceexpand  # For hya.braceexpand resolver
pip install hya numpy        # For hya.np.array resolver
pip install hya torch        # For hya.torch.tensor and hya.torch.dtype resolvers
```

### Dependency Matrix

The following table shows which resolvers require which packages:

| Resolver | Required Package | Description |
|----------|-----------------|-------------|
| `hya.braceexpand` | `braceexpand>=0.1.7` | Brace expansion patterns |
| `hya.np.array` | `numpy>=1.24` | NumPy array creation |
| `hya.torch.tensor` | `torch>=2.0` | PyTorch tensor creation |
| `hya.torch.dtype` | `torch>=2.0` | PyTorch data type specification |

All other resolvers work with the base installation (only `omegaconf` required).

If you try to use a resolver that requires an optional package without installing it, you'll receive a helpful error message indicating which package needs to be installed.

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

It is recommended to create a Python 3.10+ virtual environment. This step is optional so you
can skip it. To create a virtual environment, you can use the following command:

```shell
make conda
```

It automatically creates a conda virtual environment. When the virtual environment is created, you
can activate it with the following command:

```shell
conda activate hya
```

This example uses `conda` to create a virtual environment, but you can use other tools or
configurations. Then, you should install the required package to use `hya` with the following
command:

```shell
make install
```

This command will install all the required packages. You can also use this command to update the
required packages. This command will check if there is a more recent package available and will
install it. Finally, you can test the installation with the following command:

```shell
make unit-test-cov
```
