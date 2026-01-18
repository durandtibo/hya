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
It is possible to install all the optional dependencies by running the following command:

```shell
pip install 'hya[all]'
```

This command also installed PyTorch.
It is also possible to install the optional packages manually or to select the packages to install.

```shell
pip install hya torch
```

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
