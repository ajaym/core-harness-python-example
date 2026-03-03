#!/usr/bin/env python3
"""Run LLM eval tests with output reliably captured.

The Claude Code SDK spawns subprocesses that take over stdout/stderr file
descriptors, which swallows pytest output in many environments (terminals,
CI, Claude Code's Bash tool, etc.).

This wrapper runs pytest in its own session with stdout directed to a log
file, then prints the results. This guarantees output is never lost.

Usage:
    python scripts/run_evals.py                        # run all evals
    python scripts/run_evals.py -k test_file_read      # run specific eval
    python scripts/run_evals.py --log eval-results.log  # save to custom log
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO_ROOT / "eval-results.log"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LLM evals")
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help=f"Log file for results (default: {DEFAULT_LOG.name})",
    )
    args, pytest_args = parser.parse_known_args()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(REPO_ROOT / "evals"),
        "--override-ini=timeout=180",
        "--capture=no",
        "-v",
        *pytest_args,
    ]

    # Run pytest in a new session with stdout/stderr going to a file.
    # start_new_session=True prevents the SDK's subprocesses from
    # inheriting and clobbering our parent's file descriptors.
    with open(args.log, "w") as log_file:
        proc = subprocess.run(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=str(REPO_ROOT),
            start_new_session=True,
        )

    # Print results from the log file (safe — SDK subprocesses are done)
    output = args.log.read_text()
    sys.stdout.write(output)
    sys.stdout.flush()

    sys.stderr.write(f"\nResults saved to {args.log}\n")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
