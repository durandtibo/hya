#!/usr/bin/env bash

# check_dependency_tree.sh - Validate package dependency tree
#
# Description:
#   Verifies that the package dependency tree matches expected patterns. Checks
#   that the package has no unexpected dependencies and validates the structure
#   of the dependency tree. This ensures clean packaging without extra dependencies.
#
# Usage:
#   ./check_dependency_tree.sh
#
# Requirements:
#   - uv must be installed and available in PATH
#   - hya package must be installed in the current environment
#
# Exit Codes:
#   0 - Dependency tree matches expected patterns
#   1 - Dependency tree has unexpected dependencies or structure
#
# Note:
#   Update the validation patterns in this script when dependencies change.

set -euo pipefail

OUTPUT=$(uv pip tree --package hya --show-version-specifiers)
echo "$OUTPUT"

# Define patterns for each line (in order).
# Add as many patterns as needed.
PATTERNS=(
  '^hya v[0-9]+(\.[0-9]+)*[A-Za-z0-9]*$'
  '^└── omegaconf v[0-9]+(\.[0-9]+)*[[:space:]]+\[required:.*\]$'
)

# Number of lines we want to check
MAX_LINES=${#PATTERNS[@]}

# --- Validator ---
# Iterate through each line and validate against expected patterns
i=1
while IFS= read -r line; do
    # Stop once all patterns have been checked
    if (( i > MAX_LINES )); then
        break
    fi

    pattern="${PATTERNS[$((i-1))]}"

    # Check if the line matches the expected pattern
    if ! [[ "$line" =~ $pattern ]]; then
        echo "❌ Line $i does NOT match expected pattern"
        echo "   Line content:    '$line'"
        echo "   Expected pattern: $pattern"
        exit 1
    fi

    ((i++))
done <<< "$OUTPUT"

echo "✅ First $MAX_LINES lines match."
