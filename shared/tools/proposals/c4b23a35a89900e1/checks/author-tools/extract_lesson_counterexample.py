#!/usr/bin/env python3
"""Extract one retained lesson-census ambiguity into compact replay files.

The lesson-census summary already retains exact materialized instances and
predictions. This tool turns one `first_witnesses` entry into a small JSON plus
query/expected/rival sidecars suitable for audits and regression fixtures.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _choose_witness(
    witnesses: dict[str, Any], rival_substring: str | None
) -> tuple[str, dict[str, Any]]:
    items = [(k, v) for k, v in witnesses.items() if isinstance(v, dict)]
    if rival_substring:
        items = [(k, v) for k, v in items if rival_substring in k]
    if not items:
        label = f" containing {rival_substring!r}" if rival_substring else ""
        raise ValueError(f"no retained first witness{label}")
    # Prefer a query-rotation witness because it captures the lesson-level defect.
    items.sort(key=lambda item: (item[1].get("scope") != "rotation", item[0]))
    return items[0]


def extract(report: dict[str, Any], rival_substring: str | None) -> dict[str, Any]:
    witnesses = report.get("first_witnesses")
    if not isinstance(witnesses, dict):
        raise ValueError("report has no first_witnesses object")
    key, witness = _choose_witness(witnesses, rival_substring)
    prediction = witness.get("prediction")
    if not isinstance(prediction, dict):
        raise ValueError(f"witness {key!r} has no recorded prediction")
    required = ("input", "expected_output", "rival_output")
    missing = [name for name in required if name not in prediction]
    if missing:
        raise ValueError(f"witness {key!r} prediction is missing {missing}")

    return {
        "schema": "arcpuzzles-lesson-counterexample-v1",
        "task_id": report.get("task_id"),
        "source_binding": report.get("source_binding", {}),
        "census_status": report.get("status"),
        "census_summary": report.get("summary", {}),
        "witness_key": key,
        "scope": witness.get("scope"),
        "recipe": witness.get("recipe", {}),
        "query_index": witness.get("query_index"),
        "train_indices": witness.get("train_indices", []),
        "warnings": witness.get("warnings", []),
        "rivals": witness.get("rivals", {}),
        "instance": witness.get("instance", {}),
        "prediction": prediction,
    }


def _sidecar_path(out: Path, suffix: str) -> Path:
    return out.with_name(f"{out.stem}.{suffix}.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="lesson-census summary JSON")
    parser.add_argument("--rival", help="substring selecting the retained rival")
    parser.add_argument("--out", required=True, type=Path, help="compact output JSON")
    args = parser.parse_args()

    extracted = extract(_load(args.report), args.rival)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(extracted, indent=2) + "\n", encoding="utf-8")
    prediction = extracted["prediction"]
    for suffix, key in (
        ("query-input", "input"),
        ("expected-output", "expected_output"),
        ("rival-output", "rival_output"),
    ):
        _sidecar_path(args.out, suffix).write_text(
            json.dumps(prediction[key], indent=2) + "\n", encoding="utf-8"
        )
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
