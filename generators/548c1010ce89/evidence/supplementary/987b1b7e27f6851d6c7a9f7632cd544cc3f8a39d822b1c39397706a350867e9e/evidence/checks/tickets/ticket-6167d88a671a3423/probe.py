#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK_ID = "548c1010ce89"
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SEED_HEX = "bab342d2a825837caaa2c82331af8f1461da3bff49a10ef155f3c808bb029941"
SEED = int(SEED_HEX[:16], 16)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_rule() -> str:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical rule not found")


def grid_literal(grid):
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute_racket(source: str, grid):
    scripts = types.ModuleType("scripts")
    scripts.__path__ = [str(ROOT / "shared/tools")]
    sys.modules.setdefault("scripts", scripts)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    expression = f"({wrap_rule(source)} {grid_literal(grid)})"
    with RacketBridge(timeout=20, max_calls_before_restart=4) as bridge:
        value = bridge.eval_text(expression)
    return [[int(cell) for cell in row] for row in value]


def rows_only_shortcut(grid):
    out = deepcopy(grid)
    width = len(grid[0])
    for r, row in enumerate(grid):
        if all(value == 0 for value in row):
            out[r] = [2] * width
    return out


def main():
    gen = load(SOURCE, "ticket_6167_generator")
    grid = gen.generate(
        SEED,
        0,
        difficulty="medium",
        scene_profile="columns_only",
    )
    expected_python = gen.rule_mirror(grid)
    expected_racket = execute_racket(canonical_rule(), grid)
    shortcut = rows_only_shortcut(grid)
    info = gen._analysis(grid)
    differing = [
        {"row": r, "column": c, "expected": expected_racket[r][c], "shortcut": shortcut[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if expected_racket[r][c] != shortcut[r][c]
    ]
    result = {
        "schema": "arcpuzzles-supplementary-adversarial-witness-v1",
        "ticket_id": "ticket-6167d88a671a3423",
        "task_id": TASK_ID,
        "probe_seed_hex": SEED_HEX,
        "generator_call": {
            "seed": SEED,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {"scene_profile": "columns_only"},
        },
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "shortcut": "paint all-zero rows red but ignore all-zero columns",
        "lawful": gen.self_check(grid) == [],
        "self_check_errors": gen.self_check(grid),
        "observed_overrides": gen.observe_overrides(grid),
        "empty_rows": list(info["empty_rows"]),
        "empty_cols": list(info["empty_cols"]),
        "python_racket_parity": expected_python == expected_racket,
        "shortcut_refuted": expected_racket != shortcut,
        "differing_cell_count": len(differing),
        "first_differences": differing[:20],
        "input": grid,
        "expected_output": expected_racket,
        "shortcut_output": shortcut,
    }
    if not (
        result["lawful"]
        and result["observed_overrides"] == {"scene_profile": "columns_only"}
        and not result["empty_rows"]
        and result["empty_cols"]
        and result["python_racket_parity"]
        and result["shortcut_refuted"]
    ):
        raise SystemExit(json.dumps(result, indent=2))
    path = Path(__file__).with_name("result.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("lawful", "python_racket_parity", "shortcut_refuted", "differing_cell_count")}, indent=2))


if __name__ == "__main__":
    main()
