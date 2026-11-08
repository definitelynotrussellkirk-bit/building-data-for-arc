#!/usr/bin/env python3
"""Reproduce the two current audit findings without editing audited sources."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
from typing import Any

TASKS = ("ce40117f40f9", "f2e717c7c250")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_generator(repo: Path, task_id: str):
    path = repo / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def nonzero_top_count(grid: list[list[int]]) -> int:
    return sum(value != 0 for value in grid[0])


def ce401_probe(repo: Path) -> dict[str, Any]:
    task_id = "ce40117f40f9"
    gen, path = load_generator(repo, task_id)
    blank = [[0] * 8 for _ in range(8)]
    no_marker = gen.generate(0, 0, texture="no_marker")
    marker_only = gen.generate(0, 0, texture="no_blob")
    valid_with_bool = [[0] * 9 for _ in range(8)]
    for row, col in ((1, 1), (1, 2), (2, 1)):
        valid_with_bool[row][col] = 4
    valid_with_bool[5][6] = 9
    valid_with_bool[0][0] = True

    default = gen.generate(0, 0)
    unknown_override = gen.generate(0, 0, not_an_axis=123)
    requested_blob_size = gen.generate(0, 0, blob_size=6)
    requested_blob_cells = sum(
        value not in (0, 9) for row in requested_blob_size for value in row
    )

    direction_rows = []
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(100):
            grid = gen.generate(20261022, sample_index, difficulty=difficulty)
            marker = [
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value == 9
            ]
            blob = [
                (r, c)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value not in (0, 9)
            ]
            direction_rows.append(
                {
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    "marker_count": len(marker),
                    "blob_cell_count": len(blob),
                    "marker_strictly_southeast": bool(
                        len(marker) == 1
                        and blob
                        and marker[0][0] > max(r for r, _ in blob)
                        and marker[0][1] > max(c for _, c in blob)
                    ),
                }
            )

    cases = {
        "blank": {"grid": blank, "self_check": gen.self_check(blank)},
        "no_marker": {"grid": no_marker, "self_check": gen.self_check(no_marker)},
        "marker_only": {
            "grid": marker_only,
            "self_check": gen.self_check(marker_only),
        },
        "bool_cell": {
            "grid": valid_with_bool,
            "self_check": gen.self_check(valid_with_bool),
        },
        "unknown_override": {
            "override": {"not_an_axis": 123},
            "accepted": True,
            "equals_default": unknown_override == default,
            "grid": unknown_override,
        },
        "ignored_blob_size": {
            "override": {"blob_size": 6},
            "requested": 6,
            "observed_non_marker_cells": requested_blob_cells,
            "self_check": gen.self_check(requested_blob_size),
            "grid": requested_blob_size,
        },
    }
    return {
        "schema": "arcpuzzles-current-audit-probe-v1",
        "task_id": task_id,
        "generator_path": str(path.relative_to(repo)),
        "generator_sha256": sha256_bytes(path.read_bytes()),
        "generator_version": gen.VERSION,
        "finding": "reproduced_contract_and_validator_defects",
        "cases": cases,
        "direction_census": {
            "seed": 20261022,
            "samples_per_band": 100,
            "total": len(direction_rows),
            "marker_strictly_southeast": sum(
                row["marker_strictly_southeast"] for row in direction_rows
            ),
            "all_have_one_marker_and_blob": all(
                row["marker_count"] == 1 and row["blob_cell_count"] >= 1
                for row in direction_rows
            ),
            "rows": direction_rows,
        },
        "conclusion": (
            "self_check accepts missing entities and bool cells; unknown and blob_size "
            "overrides are silently ignored; all sampled defaults place the marker "
            "strictly southeast of the blob, leaving a positional shortcut."
        ),
    }


def f2e_probe(repo: Path) -> dict[str, Any]:
    task_id = "f2e717c7c250"
    gen, path = load_generator(repo, task_id)
    runs: dict[str, list[dict[str, Any]]] = {}
    for requested in (1, 3):
        label = f"n_keys_{requested}"
        runs[label] = []
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(5):
                grid = gen.generate(
                    12345,
                    sample_index,
                    difficulty=difficulty,
                    n_keys=requested,
                )
                runs[label].append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "requested_n_keys": requested,
                        "observed_top_row_nonzero": nonzero_top_count(grid),
                        "grid": grid,
                    }
                )
    default = gen.generate(0, 0)
    unknown = gen.generate(0, 0, not_an_axis=123)
    no_keys = gen.generate(0, 0, texture="no_keys")
    return {
        "schema": "arcpuzzles-current-audit-probe-v1",
        "task_id": task_id,
        "generator_path": str(path.relative_to(repo)),
        "generator_sha256": sha256_bytes(path.read_bytes()),
        "generator_version": gen.VERSION,
        "finding": "reproduced_ignored_n_keys_override_and_missing_contract",
        "declared_n_keys_axis": gen.AXES["n_keys"],
        "has_rule_hash": hasattr(gen, "RULE_HASH"),
        "has_self_check": callable(getattr(gen, "self_check", None)),
        "override_runs": runs,
        "summary": {
            label: {
                "calls": len(items),
                "observed_counts": sorted(
                    {item["observed_top_row_nonzero"] for item in items}
                ),
            }
            for label, items in runs.items()
        },
        "unknown_override": {
            "override": {"not_an_axis": 123},
            "accepted": True,
            "equals_default": unknown == default,
            "grid": unknown,
        },
        "degenerate_no_keys": {"grid": no_keys},
        "conclusion": (
            "AXES advertises n_keys=1..3, but all 30 explicit calls still emit "
            "exactly two keys; there is no self_check or pinned RULE_HASH, and an "
            "unknown override is accepted."
        ),
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = Path.cwd().resolve()
    if not (repo / "generators").is_dir():
        raise SystemExit("run from WORK/repo (normally through review.py run)")
    args.out.mkdir(parents=True, exist_ok=False)
    reports = {
        "ce40117f40f9": ce401_probe(repo),
        "f2e717c7c250": f2e_probe(repo),
    }
    for task_id, report in reports.items():
        report["command"] = shlex.join([sys.executable, *sys.argv])
        report["cwd"] = "WORK/repo"
        write_json(args.out / task_id / "probe.json", report)
    manifest = {
        "schema": "arcpuzzles-current-audit-probe-manifest-v1",
        "tasks": {
            task_id: {
                "path": f"{task_id}/probe.json",
                "generator_sha256": report["generator_sha256"],
                "finding": report["finding"],
            }
            for task_id, report in reports.items()
        },
        "script_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "command": shlex.join([sys.executable, *sys.argv]),
        "cwd": "WORK/repo",
    }
    write_json(args.out / "manifest.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
