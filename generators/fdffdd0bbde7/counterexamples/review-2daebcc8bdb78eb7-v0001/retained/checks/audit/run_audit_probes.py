#!/usr/bin/env python3
"""Reproduce the two findings-only audit probes for this review packet."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime")]


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid: list[list[int]]) -> str:
    data = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def canonical_record(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def endpoint_presence_rival(grid: list[list[int]]) -> list[list[int]]:
    """Bridge any two nonzero endpoints in a column with the top color."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] != 0]
        if len(rows) == 2 and all(grid[r][c] == 0 for r in range(rows[0] + 1, rows[1])):
            color = grid[rows[0]][c]
            for r in range(rows[0], rows[1] + 1):
                out[r][c] = color
    return out


def intended_cf(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    colors = sorted({v for row in grid for v in row if v != 0})
    for c in range(w):
        for color in colors:
            rows = [r for r in range(h) if grid[r][c] == color]
            if len(rows) == 2 and all(grid[r][c] == 0 for r in range(rows[0] + 1, rows[1])):
                for r in range(rows[0], rows[1] + 1):
                    out[r][c] = color
    return out


def mixed_endpoint_columns(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    count = 0
    for c in range(w):
        cells = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if len(cells) == 2 and cells[0][1] != cells[1][1]:
            count += 1
    return count


def probe_cf() -> dict[str, Any]:
    task_id = "cf60523d1603"
    gen, source = load_generator(task_id)
    canonical = canonical_record(task_id)
    canonical_checks = []
    for index, pair in enumerate(canonical["train"]):
        rival = endpoint_presence_rival(pair["input"])
        canonical_checks.append({
            "index": index,
            "fits": rival == pair["output"],
            "input_sha256": grid_hash(pair["input"]),
        })

    ordinary = []
    for seed in range(8):
        for sample_index in range(10):
            grid = gen.generate(seed, sample_index, difficulty="easy")
            ordinary.append({
                "seed": seed,
                "sample_index": sample_index,
                "input_sha256": grid_hash(grid),
                "validator_errors": gen.self_check(grid),
                "mixed_endpoint_columns": mixed_endpoint_columns(grid),
                "rival_matches_intended": endpoint_presence_rival(grid) == intended_cf(grid),
            })

    ignored_override = None
    for seed in range(100):
        grid = gen.generate(seed, 0, difficulty="easy", n_columns=1)
        populated = sum(any(row[c] != 0 for row in grid) for c in range(len(grid[0])))
        if populated != 1:
            ignored_override = {
                "seed": seed,
                "sample_index": 0,
                "difficulty": "easy",
                "requested_n_columns": 1,
                "observed_populated_columns": populated,
                "input_sha256": grid_hash(grid),
                "validator_errors": gen.self_check(grid),
            }
            break

    input_path = PACKET / "checks" / "audit" / task_id / "input.json"
    counterexample = json.loads(input_path.read_text())
    racket = json.loads((input_path.parent / "racket.json").read_text())
    rival = endpoint_presence_rival(counterexample)
    (input_path.parent / "rival.json").write_text(json.dumps({
        "schema": "arcpuzzles-audit-rival-v1",
        "task_id": task_id,
        "rival": "bridge any two nonzero column endpoints using the top endpoint color",
        "generator_sha256": sha256(source),
        "rule_hash": racket["executed_rule_hash"],
        "input_sha256": grid_hash(counterexample),
        "output": rival,
        "output_sha256": grid_hash(rival),
    }, indent=2) + "\n")

    return {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "rule_hash": racket["executed_rule_hash"],
        "canonical_rival": {
            "name": "endpoint_presence",
            "fits": sum(x["fits"] for x in canonical_checks),
            "denominator": len(canonical_checks),
            "pairs": canonical_checks,
        },
        "ordinary_sample": {
            "difficulty": "easy",
            "seed_range": [0, 7],
            "sample_index_range": [0, 9],
            "draws": len(ordinary),
            "validator_passes": sum(not x["validator_errors"] for x in ordinary),
            "mixed_endpoint_draws": sum(x["mixed_endpoint_columns"] > 0 for x in ordinary),
            "rival_matches_intended": sum(x["rival_matches_intended"] for x in ordinary),
            "unique_inputs": len({x["input_sha256"] for x in ordinary}),
        },
        "counterexample": {
            "input": counterexample,
            "input_sha256": grid_hash(counterexample),
            "validator_errors": gen.self_check(counterexample),
            "validator_domain": not gen.self_check(counterexample),
            "ordinary_generator_support": False,
            "ordinary_support_reason": "ordinary generate() assigns one color to both endpoints in each populated column",
            "racket_output": racket["results"][0]["output"],
            "rival_output": rival,
            "outputs_disagree": racket["results"][0]["output"] != rival,
        },
        "dead_override": ignored_override,
        "command": ["python3", "checks/audit/run_audit_probes.py"],
        "cwd": "packet_root",
    }


def probe_fd() -> dict[str, Any]:
    task_id = "fdffdd0bbde7"
    gen, source = load_generator(task_id)
    base = gen.generate(123, 0, difficulty="medium")
    cases: list[dict[str, Any]] = []
    for overrides in (
        {"grid_h": 24},
        {"grid_w": 28},
        {"grid_h": 24, "grid_w": 28},
        {"stencil_size": 1},
        {"palette_kind": "warm"},
        {"texture": "warm"},
    ):
        grid = gen.generate(123, 0, difficulty="medium", **overrides)
        cases.append({
            "overrides": overrides,
            "shape": [len(grid), len(grid[0])],
            "input_sha256": grid_hash(grid),
            "identical_to_unoverridden": grid == base,
            "validator_errors": gen.self_check(grid),
        })

    rejected: list[dict[str, Any]] = []
    for overrides in ({"n_entries": 4}, {"lib_h": 6}, {"n_body": 12}):
        try:
            gen.generate(123, 0, difficulty="medium", **overrides)
            outcome = "accepted"
        except Exception as exc:  # evidence capture
            outcome = f"{type(exc).__name__}: {exc}"
        rejected.append({"overrides": overrides, "outcome": outcome})

    show = json.loads((PACKET / "checks" / "audit" / task_id / "show.json").read_text())
    return {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": task_id,
        "generator_sha256": sha256(source),
        "rule_hash": show["rule_hash"],
        "seed": 123,
        "sample_index": 0,
        "difficulty": "medium",
        "unoverridden": {
            "shape": [len(base), len(base[0])],
            "input_sha256": grid_hash(base),
            "validator_errors": gen.self_check(base),
        },
        "ignored_declared_overrides": cases,
        "declared_global_values_rejected_by_difficulty_local_draw": rejected,
        "finding": (
            "grid_h, grid_w, stencil_size, palette_kind, and helpful texture overrides "
            "are accepted but have no effect; some globally valid n_entries/lib_h/n_body "
            "values are rejected under medium difficulty"
        ),
        "command": ["python3", "checks/audit/run_audit_probes.py"],
        "cwd": "packet_root",
    }


def main() -> None:
    outputs = {
        "cf60523d1603": probe_cf(),
        "fdffdd0bbde7": probe_fd(),
    }
    for task_id, report in outputs.items():
        path = PACKET / "checks" / "audit" / task_id / "analysis.json"
        path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {path.relative_to(PACKET)}")


if __name__ == "__main__":
    main()
