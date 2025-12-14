#!/usr/bin/env bash

# check_metadata.sh - Validate package metadata
#
# Description:
#   Verifies that the installed package has correct metadata by checking that
#   the package name and dependencies are properly defined. This ensures the
#   package was installed correctly and has expected metadata fields.
#
# Usage:
#   ./check_metadata.sh
#
# Requirements:
#   - uv must be installed and available in PATH
#   - objectory package must be installed in the current environment
#
# Exit Codes:
#   0 - Package metadata is valid
#   1 - Package metadata is missing or invalid

set -euo pipefail

METADATA=$(uv pip show hya)

echo "$METADATA"

echo "$METADATA" | grep -q "Name: hya"
echo "$METADATA" | grep -q "Requires: omegaconf"
