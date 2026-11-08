#!/usr/bin/env python3
"""Replay one anti-shortcut witness and optionally census the generator.

Run from the packet root so the verified local Racket is on PATH:

    python3 run_with_racket.py python3 \
      generators/4e4fa6c8d4ce/workspace/analyze_generator.py \
      --seed 8500 --sample-index 2 --difficulty medium \
      --out ../checks/shortcut_witness.json

The report independently applies the selected Racket rule, compares the Python
mirror, evaluates the canonical `drop_shape_color` shortcut, records observable
axes/witnesses, and pins all grids with stable hashes.  `--census N` additionally
reports profile and witness support over N consecutive sample indexes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import types
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
TASK_ID = "4e4fa6c8d4ce"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

sys.path.insert(0, str(ROOT / "shared" / "runtime"))
# The normal battery projects shared/tools as the ``scripts`` package.  A
# packet-local workspace tool runs against the unprojected tree, so recreate
# only that namespace mapping rather than copying or mutating shared files.
_scripts = types.ModuleType("scripts")
_scripts.__path__ = [str(ROOT / "shared" / "tools")]
sys.modules.setdefault("scripts", _scripts)

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"workspace_{TASK_ID}_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> tuple[str, list[dict]]:
    source = None
    pairs: list[dict] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = source or row.get("program_solution")
            pairs.extend(row.get("train") or [])
            pairs.extend(row.get("test") or [])
    if not source:
        raise RuntimeError(f"no selected canonical rule for {TASK_ID}")
    return str(source), pairs


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in grid
    )
    return f"'({rows})"


def _apply_racket(source: str, grid: list[list[int]]) -> list[list[int]]:
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    bridge = RacketBridge(max_calls_before_restart=8)
    try:
        output = bridge.eval_text(expression)
    finally:
        bridge.shutdown()
    if not isinstance(output, list) or not output or not isinstance(output[0], list):
        raise RuntimeError(f"selected rule returned non-grid output: {output!r}")
    return [[int(value) for value in row] for row in output]


def _sha16(value) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _profile(grid: list[list[int]]) -> list[int]:
    return [
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    ]


def _census(module, *, seed: int, difficulty: str, count: int) -> dict:
    profiles: Counter[tuple[int, int, int]] = Counter()
    schedule: Counter[str] = Counter()
    witnesses: Counter[str] = Counter()
    distinct_inputs: set[str] = set()
    distinct_outputs: set[str] = set()
    for sample_index in range(count):
        grid = module.generate(seed, sample_index, difficulty=difficulty)
        output = module.rule_mirror(grid)
        profiles[tuple(_profile(grid))] += 1
        schedule[module.schedule_profile(seed, sample_index, difficulty)] += 1
        for name, predicate in module.SEMANTIC_WITNESSES.items():
            witnesses[name] += bool(predicate(grid))
        distinct_inputs.add(_sha16(grid))
        distinct_outputs.add(_sha16(output))
    return {
        "draws": count,
        "profiles": {"x".join(map(str, key)): value for key, value in sorted(profiles.items())},
        "schedule_profiles": dict(sorted(schedule.items())),
        "witness_hits": dict(sorted(witnesses.items())),
        "distinct_inputs": len(distinct_inputs),
        "distinct_outputs": len(distinct_outputs),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=8500)
    parser.add_argument("--sample-index", type=int, default=2)
    parser.add_argument("--difficulty", default="medium")
    parser.add_argument("--census", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    module = _load_generator()
    source, canonical_pairs = _canonical()
    grid = module.generate(args.seed, args.sample_index, difficulty=args.difficulty)
    mirror = module.rule_mirror(grid)
    racket = _apply_racket(source, grid)
    shortcut = module.CANONICAL_SHORTCUTS["drop_shape_color"](grid)
    canonical_shortcut_fits = sum(
        module.CANONICAL_SHORTCUTS["drop_shape_color"](pair["input"])
        == pair["output"]
        for pair in canonical_pairs
    )

    report = {
        "schema": "4e4fa6c8d4ce-shortcut-witness-v1",
        "task_id": TASK_ID,
        "replay": {
            "seed": args.seed,
            "sample_index": args.sample_index,
            "difficulty": args.difficulty,
        },
        "profile": _profile(grid),
        "observed_axes": module.observe_overrides(grid),
        "witnesses": {
            name: bool(predicate(grid))
            for name, predicate in module.SEMANTIC_WITNESSES.items()
        },
        "canonical_shortcut": {
            "name": "drop_shape_color",
            "fits_pairs": canonical_shortcut_fits,
            "canonical_pairs": len(canonical_pairs),
        },
        "input": grid,
        "intended_output_racket": racket,
        "intended_output_python_mirror": mirror,
        "shortcut_output": shortcut,
        "checks": {
            "racket_equals_python_mirror": racket == mirror,
            "shortcut_disagrees": shortcut != racket,
            "self_check": module.self_check(grid),
            "strict_canonical_like": module.strict_canonical_like(grid),
        },
        "hashes": {
            "input_sha16": _sha16(grid),
            "racket_output_sha16": _sha16(racket),
            "mirror_output_sha16": _sha16(mirror),
            "shortcut_output_sha16": _sha16(shortcut),
        },
    }
    if args.census:
        report["census"] = _census(
            module,
            seed=args.seed,
            difficulty=args.difficulty,
            count=args.census,
        )

    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    else:
        print(text, end="")

    return 0 if (
        report["checks"]["racket_equals_python_mirror"]
        and report["checks"]["shortcut_disagrees"]
        and not report["checks"]["self_check"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
