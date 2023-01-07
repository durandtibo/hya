# Contributing to `bearface`

We want to make contributing to this project as easy and transparent as possible.

## Overview

We welcome contributions from anyone, even if you are new to open source.

- If you are planning to contribute back bug-fixes, please do so without any further discussion.
- If you plan to contribute new features, utility functions, or extensions to the core, please first
  open an issue and discuss the feature with us.

Once you implement and test your feature or bug-fix, please submit a Pull Request.

## Pull Requests

We actively welcome your pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes. You can use the following command to run the tests:
   ```shell
   make unit-test-cov
   ```
5. Make sure your code lints. The following commands can help you to format the code:
   ```shell
   black .
   pre-commit run --all-files
   ```

## Issues

We use GitHub issues to track public bugs or feature requests.
For bugs, please ensure your description is clear and concise description, and has sufficient
information to be easily reproducible.
For feature request, please add a clear and concise description of the feature proposal.
Please outline the motivation for the proposal.

## License

By contributing to `bearface`, you agree that your contributions will be licensed under the LICENSE
file in the root directory of this source tree.
