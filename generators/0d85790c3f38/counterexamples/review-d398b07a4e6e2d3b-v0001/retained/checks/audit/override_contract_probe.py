#!/usr/bin/env python3
"""Source-bound generator override contract probe.

The probe loads each exact generator from an explicit ARCpuzzles root, runs a
small declarative case matrix, and records outputs/exceptions plus source hashes.
It never imports private per-puzzle aliases and does not mutate generators.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def distinct_colors(grid: Any) -> list[int] | None:
    if not isinstance(grid, list) or any(not isinstance(row, list) for row in grid):
        return None
    values = {cell for row in grid for cell in row if type(cell) is int}
    return sorted(values)


def run_variant(module: Any, case: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    kwargs = dict(variant.get("overrides", {}))
    difficulty = case.get("difficulty")
    if difficulty is not None:
        kwargs["difficulty"] = difficulty
    row: dict[str, Any] = {
        "label": variant["label"],
        "overrides": variant.get("overrides", {}),
        "expected_error": variant.get("expected_error"),
    }
    observed = []
    base = importlib.import_module("puzzle_generators.base")
    base.set_ctx_observer(observed.append)
    try:
        grid = module.generate(case["seed"], case["sample_index"], **kwargs)
    except BaseException as exc:  # Evidence should retain the exact public failure class/message.
        row.update({
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        })
        if observed:
            row["overrides_used"] = observed[-1].overrides_used()
            row["recorded_draws"] = observed[-1].recorded_draws()
        return row
    finally:
        base.set_ctx_observer(None)
    errors = module.self_check(grid, difficulty=difficulty, meta=None) if hasattr(module, "self_check") else []
    row.update({
        "status": "returned",
        "grid": grid,
        "grid_sha256": digest(grid),
        "shape": [len(grid), len(grid[0]) if grid and isinstance(grid[0], list) else None],
        "distinct_colors": distinct_colors(grid),
        "self_check_errors": errors,
        "overrides_used": observed[-1].overrides_used() if observed else {},
        "recorded_draws": observed[-1].recorded_draws() if observed else {},
    })
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    loaded: dict[str, tuple[Any, Path, str]] = {}
    results: list[dict[str, Any]] = []
    for case in spec["cases"]:
        task_id = case["task_id"]
        if task_id not in loaded:
            loaded[task_id] = load_selected_generator(task_id, root=root)
        module, source, source_sha = loaded[task_id]
        variants = [run_variant(module, case, variant) for variant in case["variants"]]
        returned = [row for row in variants if row["status"] == "returned"]
        result = {
            "name": case["name"],
            "task_id": task_id,
            "generator_path": str(source.relative_to(root)),
            "generator_sha256": source_sha,
            "seed": case["seed"],
            "sample_index": case["sample_index"],
            "difficulty": case.get("difficulty"),
            "claim": case.get("claim"),
            "variants": variants,
            "all_returned_outputs_equal": bool(returned) and len(returned) == len(variants)
                and len({row["grid_sha256"] for row in returned}) == 1,
        }
        results.append(result)

    payload = {
        "schema": "arcpuzzles-override-contract-probe-v1",
        "root": str(root),
        "spec_sha256": digest(spec),
        "cases": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "cases": len(results),
        "source_hashes": {task_id: row[2] for task_id, row in loaded.items()},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
