#!/usr/bin/env bash

# custom_checks.sh - Run custom package validation checks
#
# Description:
#   Executes project-specific validation checks that are not covered by
#   standard checks. This can include any custom requirements or validations
#   specific to the package.
#
# Usage:
#   ./custom_checks.sh
#
# Requirements:
#   - Python must be available
#   - Package must be installed in the current environment
#   - tests/package_checks.py must exist
#
# Exit Codes:
#   0 - Custom checks passed
#   1 - Custom checks failed

set -euo pipefail

python tests/package_checks.py
