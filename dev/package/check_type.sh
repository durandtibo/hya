#!/usr/bin/env bash

# check_type.sh - Validate package type annotations
#
# Description:
#   Verifies that the package is properly typed by running pyright on a test
#   import. Creates a temporary test file that imports the package and checks
#   that pyright recognizes it as typed. Ensures the package includes py.typed
#   marker and proper type stubs.
#
# Usage:
#   ./check_type.sh
#
# Requirements:
#   - pyright must be installed and available in PATH
#   - objectory package must be installed in the current environment
#
# Exit Codes:
#   0 - Package is properly typed and pyright validation passed
#   1 - Package type checking failed or pyright detected errors

set -euo pipefail

PYRIGHT_DIR=tmp/pyright_check
mkdir -p $PYRIGHT_DIR

# Ensure cleanup on exit, even on error
cleanup() {
  rm -rf "$PYRIGHT_DIR"
}
trap cleanup EXIT

# Create pyright test file
cat >$PYRIGHT_DIR/check_pyright_import.py <<'EOF'
from hya.registry import ResolverRegistry

register = ResolverRegistry()
EOF

# Check that pyright recognizes the package as typed
pyright $PYRIGHT_DIR
