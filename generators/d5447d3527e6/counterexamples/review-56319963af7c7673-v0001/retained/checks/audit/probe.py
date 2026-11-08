#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def canonical_row(task_id: str):
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise KeyError(task_id)


def odd_run_true(grid):
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 5:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 5:
                row += 1
            length = row - start
            if length >= 3 and length % 2 == 1:
                out[start + length // 2][col] = 2
    return out


def odd_run_3_or_5_only(grid):
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 5:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 5:
                row += 1
            length = row - start
            if length in (3, 5):
                out[start + length // 2][col] = 2
    return out


def one_gap_true(grid):
    height, width = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for row in range(height):
        for col in range(1, width - 1):
            if (
                grid[row][col] == 0
                and grid[row][col - 1] == 6
                and grid[row][col + 1] == 6
            ):
                out[row][col] = 6
    return out


def fill_whole_span(grid):
    out = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        cols = [col for col, value in enumerate(row) if value == 6]
        if len(cols) >= 2:
            for col in range(min(cols), max(cols) + 1):
                if out[row_index][col] == 0:
                    out[row_index][col] = 6
    return out


SPECS = {
    "d5447d3527e6": {
        "true": odd_run_true,
        "rival": odd_run_3_or_5_only,
        "rival_name": "odd_length_whitelist_3_or_5",
        "domain_note": "Counterexample is accepted by self_check and canonical rule semantics, but ordinary generation only emits target lengths 3 and 5.",
    },
    "26872d42d87a": {
        "true": one_gap_true,
        "rival": fill_whole_span,
        "rival_name": "fill_between_leftmost_and_rightmost_6",
        "domain_note": "Counterexample is accepted by self_check and contains two ordinary trigger rows, but ordinary generation emits only alternating one-cell gaps and no wider near-miss row.",
    },
}


def main():
    report = {"schema": "audit_shortcut_probe/1", "samples_per_band": 100, "tasks": {}}
    for task_id, cfg in SPECS.items():
        gen, gen_path = load_generator(task_id)
        row = canonical_row(task_id)
        pairs = [pair for split in ("train", "test") for pair in row[split]]
        true_fits = sum(cfg["true"](pair["input"]) == pair["output"] for pair in pairs)
        rival_fits = sum(cfg["rival"](pair["input"]) == pair["output"] for pair in pairs)

        per_band = {}
        for band in ("easy", "medium", "hard"):
            total = 0
            rival_matches = 0
            self_check_passes = 0
            unique = set()
            generation_errors = []
            for seed in range(100):
                try:
                    grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
                except Exception as exc:
                    generation_errors.append(f"seed={seed}: {type(exc).__name__}: {exc}")
                    continue
                total += 1
                self_check_passes += not gen.self_check(grid, difficulty=band)
                rival_matches += cfg["rival"](grid) == cfg["true"](grid)
                unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            per_band[band] = {
                "generated": total,
                "unique_inputs": len(unique),
                "self_check_passes": self_check_passes,
                "rival_matches_authority_mirror": rival_matches,
                "generation_errors": generation_errors,
            }

        audit_dir = ROOT / "checks" / "audit" / task_id
        input_grid = json.loads((audit_dir / "input.json").read_text())
        racket = json.loads((audit_dir / "racket.json").read_text())
        racket_output = racket["results"][0]["output"]
        rival_output = cfg["rival"](input_grid)
        true_output = cfg["true"](input_grid)
        self_errors = gen.self_check(input_grid)
        counterexample = {
            "schema": "audit_counterexample/1",
            "task_id": task_id,
            "generator_sha256": hashlib.sha256(gen_path.read_bytes()).hexdigest(),
            "executed_rule_hash": racket["executed_rule_hash"],
            "rule_text_sha256": racket["rule_text_sha256"],
            "rival_name": cfg["rival_name"],
            "input": input_grid,
            "self_check_errors": self_errors,
            "belongs_to_ordinary_generator_distribution": False,
            "domain_note": cfg["domain_note"],
            "racket_output": racket_output,
            "independent_true_mirror_output": true_output,
            "rival_output": rival_output,
            "racket_matches_true_mirror": racket_output == true_output,
            "rival_differs_from_racket": rival_output != racket_output,
            "apply_command": racket["command"],
            "apply_cwd": racket["cwd"],
            "input_sha256": racket["results"][0]["input_sha256"],
            "output_sha256": racket["results"][0]["output_sha256"],
        }
        (audit_dir / "counterexample.json").write_text(
            json.dumps(counterexample, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        report["tasks"][task_id] = {
            "generator_sha256": hashlib.sha256(gen_path.read_bytes()).hexdigest(),
            "rival_name": cfg["rival_name"],
            "canonical_pairs": len(pairs),
            "independent_true_mirror_canonical_fits": true_fits,
            "rival_canonical_fits": rival_fits,
            "per_band": per_band,
            "counterexample_path": f"checks/audit/{task_id}/counterexample.json",
            "counterexample_self_check_errors": self_errors,
            "counterexample_rival_differs": rival_output != racket_output,
        }

    out = ROOT / "checks" / "audit" / "shortcut_probe.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
