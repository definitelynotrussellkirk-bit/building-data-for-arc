#!/usr/bin/env python3
"""Retain evidence for the canonical-profile-only shortcut and its repair."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "e1516c24afbd"


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_source(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError("canonical source missing")


def callable_source(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("expected one (rule! BODY) form")
    return stripped[len("(rule!") : -1].strip()


def grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def execute(source: str, grid: list[list[int]], bridge: RacketBridge) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({callable_source(source)} {grid_literal(grid)})"))


def pair(gen, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--counterexample", required=True)
    parser.add_argument("--draws-per-band", type=int, default=100)
    args = parser.parse_args()
    if args.draws_per_band < 4:
        raise SystemExit("draws-per-band must be at least 4")

    root = find_root(__file__)
    gen, source_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    source = canonical_source(root)

    canonical_rows = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_fit = []
    for row in canonical_rows:
        prediction = gen._canonical_profile_only(row["input"])
        canonical_fit.append(
            {
                "variant": row["variant"],
                "split": row["split"],
                "pair_index": row["pair_index"],
                "shape": [len(row["input"]), len(row["input"][0])],
                "fits": prediction == row["output"],
            }
        )
    if not canonical_fit or not all(row["fits"] for row in canonical_fit):
        raise SystemExit("shortcut does not fit every canonical labeled pair")

    witness = gen.generate(5000, 1, difficulty="easy")
    intended_python = gen.rule_mirror(witness)
    shortcut_output = gen._canonical_profile_only(witness)
    if shortcut_output == intended_python:
        raise SystemExit("retained witness does not distinguish the shortcut")

    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        runtime_identity = bridge.runtime_identity
        intended_racket = execute(source, witness, bridge)
        canonical_racket = [
            execute(source, row["input"], bridge) == row["output"]
            for row in canonical_rows
        ]
    if intended_racket != intended_python or not all(canonical_racket):
        raise SystemExit("Racket authority does not match retained expected outputs")

    per_band: dict[str, Any] = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        samples = []
        pairs = []
        for index in range(args.draws_per_band):
            seed = 90_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            output = gen.rule_mirror(grid)
            shortcut = gen._canonical_profile_only(grid)
            shape = (len(grid) // 2, len(grid[0]))
            samples.append(
                {
                    "seed": seed,
                    "sample_index": index,
                    "half_shape": list(shape),
                    "canonical_profile": shape == (3, 3),
                    "shortcut_disagrees": shortcut != output,
                }
            )
            pairs.append({"input": grid, "output": output})
        lesson_failures = []
        for start in range(len(pairs)):
            demos = [pairs[(start + offset) % len(pairs)] for offset in range(3)]
            query = pairs[(start + 3) % len(pairs)]
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"start": start, "reasons": reasons})
        if lesson_failures:
            raise SystemExit(f"repaired {band} cyclic schedule remains ambiguous")
        per_band[band] = {
            "draws": len(samples),
            "canonical_profile_draws": sum(row["canonical_profile"] for row in samples),
            "noncanonical_profile_draws": sum(not row["canonical_profile"] for row in samples),
            "shortcut_disagreements": sum(row["shortcut_disagrees"] for row in samples),
            "odd_slots_noncanonical": all(
                not row["canonical_profile"]
                for row in samples
                if row["sample_index"] % 2 == 1
            ),
            "cyclic_three_demo_windows_checked": len(pairs),
            "cyclic_window_failures": lesson_failures,
            "samples": samples,
        }

    demos = canonical_rows[:3]
    query = pair(gen, witness)
    hook_reasons = gen.lesson_identifiable(demos, query)
    if not any("canonical-profile-only" in reason for reason in hook_reasons):
        raise SystemExit("lesson hook did not expose the retained shortcut")

    counterexample = {
        "schema": "e1516c24afbd-canonical-profile-only-counterexample-v1",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": generator_sha,
        "rule_hash": gen.RULE_HASH,
        "canonical_rule_source_sha256": sha256(source),
        "shortcut": (
            "Apply aligned NOR only when the full input is 6x3 (two 3x3 panels); "
            "on every other lawful shape return an all-zero half-size grid."
        ),
        "fits_all_canonical_labeled_pairs": True,
        "generation": {"seed": 5000, "sample_index": 1, "difficulty": "easy", "overrides": {}},
        "input": witness,
        "input_shape": [len(witness), len(witness[0])],
        "intended_output_python": intended_python,
        "intended_output_racket": intended_racket,
        "shortcut_output": shortcut_output,
        "disagrees": shortcut_output != intended_racket,
        "lesson_hook_reasons_with_three_canonical_demos": hook_reasons,
        "racket_runtime": runtime_identity,
    }
    write_json(Path(args.counterexample), counterexample)

    report = {
        "schema": "e1516c24afbd-canonical-profile-shortcut-probe-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": generator_sha,
        "rule_hash": gen.RULE_HASH,
        "canonical_rule_source_sha256": sha256(source),
        "canonical_fit": canonical_fit,
        "canonical_racket_matches": canonical_racket,
        "counterexample_path": str(Path(args.counterexample)),
        "counterexample": counterexample,
        "per_band": per_band,
        "conclusion": (
            "The shortcut fits all canonical demonstrations, but the default generator emits "
            "noncanonical witnesses. Odd fully-default slots are now guaranteed noncanonical, "
            "and the lesson hook rejects a canonical-only demo set before a differing query."
        ),
        "limits": [
            "The cyclic probe covers the retained finite starts and one named shortcut.",
            "The shortcut is checked explicitly by lesson_identifiable rather than added to the frozen declaration sets.",
            "Finite rival checks do not prove universal identifiability.",
        ],
    }
    write_json(Path(args.out), report)
    print(json.dumps({
        "status": "passed",
        "generator_sha256": generator_sha,
        "canonical_pairs": len(canonical_fit),
        "draws": 3 * args.draws_per_band,
        "counterexample": str(Path(args.counterexample)),
        "out": str(Path(args.out)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
