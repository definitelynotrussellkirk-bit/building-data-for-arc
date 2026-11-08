#!/usr/bin/env python3
"""Bounded source-bound robustness probe for generator 6fde852adb54."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "6fde852adb54"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def canonical_program() -> str:
    rows = []
    for line in canonical_path(ROOT).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if len(rows) != 1:
        raise AssertionError(f"expected one canonical row, found {len(rows)}")
    return rows[0]["program_solution"]


def execute(bridge: RacketBridge, program: str, grid):
    bridge.define_grid("g", grid)
    return bridge.eval_text(f"({wrap_rule(program)} g)")


def generated_digest() -> str:
    payload = []
    for band in (None, "default", "easy", "medium", "hard"):
        for family in ("public", "generalized"):
            payload.append(GEN.generate(701, len(payload), difficulty=band, scene_family=family))
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def child_mode() -> int:
    print(generated_digest())
    return 0


def run_probe() -> dict:
    checks: list[dict] = []

    invalid_cases = [
        ("difficulty", lambda: GEN.generate(0, 0, difficulty="bogus")),
        ("unknown_override", lambda: GEN.generate(0, 0, typo_axis=1)),
        ("scene_family_value", lambda: GEN.generate(0, 0, scene_family="bogus")),
        ("scene_family_type", lambda: GEN.generate(0, 0, scene_family=True)),
    ]
    for name, operation in invalid_cases:
        try:
            operation()
        except (TypeError, ValueError):
            checks.append({"name": f"invalid_control:{name}", "status": "pass"})
        else:
            raise AssertionError(f"invalid control {name} was silently accepted")

    top = [9, 9, 9, 7, 7, 7, 1, 5, 7, 7, 7, 7, 7, 7]
    second = [9, 9, 9] + [7] * 11
    for grid in ([top], [top, second]):
        original = copy.deepcopy(grid)
        errors = GEN.self_check(grid)
        if not any("dimensions" in error for error in errors):
            raise AssertionError(f"short grid lacked dimension diagnostic: {errors}")
        if GEN.observe_overrides(grid) != {}:
            raise AssertionError("short grid produced observable overrides")
        try:
            GEN.rule_mirror(grid)
        except ValueError as error:
            if "dimensions" not in str(error):
                raise
        else:
            raise AssertionError("short grid was accepted by rule_mirror")
        if grid != original:
            raise AssertionError("short-grid validation mutated its input")
    checks.append({"name": "short_grid_public_apis", "status": "pass", "cases": 2})

    deterministic_cases = 0
    generalized_grids = []
    for index, band in enumerate((None, "default", "easy", "medium", "hard")):
        for family in ("public", "generalized"):
            kwargs = {"difficulty": band, "scene_family": family}
            first = GEN.generate(900 + index, index * 7 + (family == "generalized"), **kwargs)
            second_grid = GEN.generate(900 + index, index * 7 + (family == "generalized"), **kwargs)
            if first != second_grid:
                raise AssertionError(f"nondeterministic replay for {band}/{family}")
            if GEN.self_check(first):
                raise AssertionError(f"invalid generated grid for {band}/{family}")
            if GEN.observe_overrides(first) != {"scene_family": family}:
                raise AssertionError(f"override not observable for {band}/{family}")
            deterministic_cases += 1
            if family == "generalized":
                generalized_grids.append(first)
    checks.append({"name": "deterministic_replay", "status": "pass", "cases": deterministic_cases})

    env_outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        env_outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", str(Path(__file__).resolve()), "--child"],
                env=env,
                text=True,
            ).strip()
        )
    if env_outputs[0] != env_outputs[1]:
        raise AssertionError("generation changed across PYTHONHASHSEED values")
    checks.append({"name": "fresh_process_hash_seed", "status": "pass", "digest": env_outputs[0]})

    program = canonical_program()
    canonical_rows = []
    generalized_rows = []
    with RacketBridge(max_calls_before_restart=64) as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            actual = execute(bridge, program, pair["input"])
            if actual != pair["output"] or GEN.rule_mirror(pair["input"]) != pair["output"]:
                raise AssertionError(
                    f"canonical parity failed at {pair['split']}[{pair['pair_index']}]"
                )
            canonical_rows.append(
                {"split": pair["split"], "pair_index": pair["pair_index"], "status": "pass"}
            )
        for index, grid in enumerate(generalized_grids):
            racket = execute(bridge, program, grid)
            mirror = GEN.rule_mirror(grid)
            if racket != mirror:
                raise AssertionError(f"generalized Racket parity failed at index {index}")
            generalized_rows.append(
                {"index": index, "input_sha256": hashlib.sha256(json.dumps(grid).encode()).hexdigest(), "status": "pass"}
            )
    checks.append({"name": "canonical_racket_parity", "status": "pass", "cases": len(canonical_rows)})
    checks.append({"name": "generalized_racket_parity", "status": "pass", "cases": len(generalized_rows)})

    return {
        "schema": "arcpuzzles-bounded-robustness-probe-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "source": {
            "path": SOURCE.relative_to(ROOT).as_posix(),
            "sha256": SOURCE_SHA256,
            "version": GEN.VERSION,
            "rule_hash": GEN.RULE_HASH,
        },
        "checks": checks,
        "canonical_cases": canonical_rows,
        "generalized_cases": generalized_rows,
        "source_changed": False,
        "limitations": [
            "bounded to four invalid controls, two malformed short grids, ten replay cases, all labeled canonical pairs, and five generalized Racket cases",
            "the pre-existing task-test portability lint remains separate from generator behavior",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.child:
        return child_mode()
    if args.out is None:
        parser.error("--out is required unless --child is used")
    report = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
