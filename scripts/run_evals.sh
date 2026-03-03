#!/usr/bin/env bash
# Run LLM eval tests via the Python wrapper for reliable output capture.
# See scripts/run_evals.py for details on why this is needed.
#
# Usage:
#   ./scripts/run_evals.sh                   # run all evals
#   ./scripts/run_evals.sh -k test_file_read # run a specific eval

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "${REPO_ROOT}/scripts/run_evals.py" "$@"
