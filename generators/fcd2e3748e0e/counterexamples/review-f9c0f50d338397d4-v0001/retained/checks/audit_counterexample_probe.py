#!/usr/bin/env python3
"""Reproduce the two assigned audit findings with live Racket outputs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path[:0] = [str(ROOT), str(REPO / "src"), str(REPO / "shared/runtime")]

# The frozen review runtime exposes shared/tools as the ``scripts`` package.
import types
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from setup_racket import ensure_racket
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def load_rule(task_id: str) -> str:
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id and row.get("program_solution"):
            return row["program_solution"]
    raise KeyError(task_id)


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(v) for v in row) + ")" for row in grid)
    return f"'({rows})"


def evaluate(bridge: RacketBridge, rule: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(rule)} {grid_literal(grid)})")


def controls(grid: list[list[int]]) -> dict[str, list[int]]:
    values = [v for row in grid for v in row]
    return {
        "reflect": [v for v in values if v in (2, 3)],
        "rotate": [v for v in values if v in (4, 5, 6, 7)],
    }


def normalized_rule_hash(rule: str) -> str:
    return hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]


def main() -> None:
    binary = ensure_racket()
    os.environ["RACKET_PATH"] = str(binary)
    os.environ["PATH"] = str(binary.parent) + os.pathsep + os.environ.get("PATH", "")

    findings = []
    bridge = RacketBridge()
    try:
        # fcd2e3748e0e: exact control overrides are advertised but ignored.
        task = "fcd2e3748e0e"
        mod, generator_path = load_generator(task)
        rule = load_rule(task)
        requested = {"reflect_ctrl": 2, "rotate_ctrl": 4}
        generated = mod.generate(0, 0, difficulty="medium", **requested)
        second_request = mod.generate(
            0, 0, difficulty="medium", reflect_ctrl=3, rotate_ctrl=7
        )
        intended = [row[:] for row in generated]
        for r, row in enumerate(intended):
            for c, value in enumerate(row):
                if value in (2, 3):
                    intended[r][c] = requested["reflect_ctrl"]
                elif value in (4, 5, 6, 7):
                    intended[r][c] = requested["rotate_ctrl"]
        findings.append(
            {
                "task_id": task,
                "finding_kind": "reproduced_override_contract_defect",
                "generator_sha256": sha256(generator_path),
                "rule_hash": normalized_rule_hash(rule),
                "seed": 0,
                "sample_index": 0,
                "difficulty": "medium",
                "overrides": requested,
                "observed_controls": controls(generated),
                "comparison_overrides": {"reflect_ctrl": 3, "rotate_ctrl": 7},
                "comparison_observed_controls": controls(second_request),
                "comparison_grid_identical": generated == second_request,
                "input_grid": generated,
                "input_self_check": mod.self_check(generated),
                "actual_racket_output": evaluate(bridge, rule, generated),
                "rival_output": evaluate(bridge, rule, intended),
                "rival_label": "caller-intended output after replacing ignored controls with requested 2/4",
                "documented_domain": True,
                "reproduction": {
                    "cwd": "packet_root",
                    "argv": ["python3", "checks/audit_counterexample_probe.py"],
                },
            }
        )

        # 733d5c4a475a: lawful axis-aligned guide vectors are never sampled.
        task = "733d5c4a475a"
        mod, generator_path = load_generator(task)
        rule = load_rule(task)
        counts = {
            "total": 0,
            "horizontal_dr_zero": 0,
            "vertical_dc_zero": 0,
            "diagonal": 0,
            "generation_errors": 0,
        }
        for band in ("easy", "medium", "hard"):
            for seed in range(1000):
                try:
                    grid = mod.generate(seed, 0, difficulty=band)
                except Exception:
                    counts["generation_errors"] += 1
                    continue
                guides = sorted(
                    (r, c)
                    for r, row in enumerate(grid)
                    for c, value in enumerate(row)
                    if value == 9
                )
                if len(guides) != 2:
                    continue
                dr = guides[1][0] - guides[0][0]
                dc = guides[1][1] - guides[0][1]
                counts["total"] += 1
                if dr == 0:
                    counts["horizontal_dr_zero"] += 1
                if dc == 0:
                    counts["vertical_dc_zero"] += 1
                if dr != 0 and dc != 0:
                    counts["diagonal"] += 1
        vertical = [[0] * 6 for _ in range(6)]
        for r, c in ((0, 0), (0, 1), (1, 0)):
            vertical[r][c] = 4
        vertical[1][4] = 9
        vertical[3][4] = 9
        rival = [[0] * 6 for _ in range(6)]
        for r, c in ((0, 0), (0, 1), (1, 0)):
            rival[r][c] = 4
        findings.append(
            {
                "task_id": task,
                "finding_kind": "reproduced_semantic_domain_gap",
                "generator_sha256": sha256(generator_path),
                "rule_hash": normalized_rule_hash(rule),
                "seed_range": {"bands": ["easy", "medium", "hard"], "seeds": "0..999", "sample_index": 0},
                "sample_counts": counts,
                "input_grid": vertical,
                "input_self_check": mod.self_check(vertical),
                "actual_racket_output": evaluate(bridge, rule, vertical),
                "rival_output": rival,
                "rival_label": "axis-aligned-unseen shortcut: erase guides and preserve only the original object",
                "documented_domain": True,
                "reproduction": {
                    "cwd": "packet_root",
                    "argv": ["python3", "checks/audit_counterexample_probe.py"],
                },
            }
        )
    finally:
        bridge.close()

    output = ROOT / "checks/audit_counterexamples.json"
    output.write_text(json.dumps({"schema": "arcpuzzles-audit-counterexamples-v1", "findings": findings}, indent=2) + "\n")
    print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()
