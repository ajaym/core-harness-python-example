"""JSON result writer for eval runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_eval_results(
    suite: str,
    provider: str,
    task_results: list[dict[str, Any]],
    output_dir: Path | None = None,
) -> Path:
    """Write eval results as a JSON file.

    Args:
        suite: Name of the eval suite.
        provider: Provider used (anthropic, bedrock).
        task_results: List of task result dicts.
        output_dir: Directory to write results to (default: evals/results/).

    Returns:
        Path to the written results file.
    """
    if output_dir is None:
        output_dir = Path("evals/results")

    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    total = len(task_results)
    passed = sum(1 for t in task_results if t.get("pass_rate", 0) == 1.0)
    failed = total - passed

    report = {
        "run_id": run_id,
        "suite": suite,
        "provider": provider,
        "tasks": task_results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0,
        },
    }

    filename = f"{suite}_{provider}_{run_id}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return output_path
