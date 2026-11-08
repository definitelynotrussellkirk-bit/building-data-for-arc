#!/usr/bin/env python3
"""Reproduce the selected generator's canonical fit and shortcut counterexample.

Run from the packet root with:
    python3 run_with_racket.py python3 ../checks/selected_probe.py

The wrapper supplies the packet's verified local Racket.  This probe deliberately
uses the selected Racket authority for labels rather than trusting the generator's
Python mirror.
"""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys
import types
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
# Runtime normalization imports shared tools via the production package name.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)
from puzzle_generators import runner

TASK_ID = "99405cd80c26"
OUT = ROOT / "checks/selected-probe/report.json"
COUNTEREXAMPLE_REPLAY = {
    "seed": 73,
    "sample_index": 11,
    "difficulty": "medium",
    "overrides": {
        "transform": "rot180",
        "exemplar_cells": 4,
        "query_cells": 5,
    },
}


def load_generator() -> Any:
    path = REPO / f"generators/{TASK_ID}/generator.py"
    spec = spec_from_file_location(f"review_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                test = row["test"]
                return list(row["train"]) + (test if isinstance(test, list) else [test])
    raise KeyError(TASK_ID)


def load_rule() -> str:
    matches = sorted((REPO / "shared/data/base/solutions").rglob(f"*{TASK_ID}*.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one base solution for {TASK_ID}, found {matches}")
    row = json.loads(matches[0].read_text(encoding="utf-8"))
    target = row["racket_target"]
    return target.get("target_code") or target["raw_code"]


def apply_all(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(load_rule()))
    try:
        return [runner._apply_rule(bridge, fn_name, grid) for grid in grids]
    finally:
        bridge.shutdown()


def main() -> None:
    gen = load_generator()
    pairs = canonical_pairs()
    shortcut = gen.CANONICAL_SHORTCUTS["observed_transform_family_only"]
    canonical_inputs = [pair["input"] for pair in pairs]
    canonical_racket_outputs = apply_all(canonical_inputs)

    replay = COUNTEREXAMPLE_REPLAY
    counterexample = gen.generate(
        replay["seed"],
        replay["sample_index"],
        difficulty=replay["difficulty"],
        **replay["overrides"],
    )
    [racket_output] = apply_all([counterexample])
    shortcut_output = shortcut(counterexample)

    transform_windows = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 17):
            transforms = [
                gen._infer_transform(gen.generate(seed, index, difficulty=difficulty))
                for index in range(8)
            ]
            transform_windows.append({
                "difficulty": difficulty,
                "seed": seed,
                "transforms": transforms,
                "covers_all_eight": set(transforms) == set(gen.ALL_TRANSFORMS),
            })

    report = {
        "schema": "arc-review-selected-shortcut-probe-v1",
        "task_id": TASK_ID,
        "rule_hash": gen.RULE_HASH,
        "shortcut": {
            "name": "observed_transform_family_only",
            "description": (
                "Infer only identity, rotate-90-clockwise, or horizontal-reflection "
                "branches observed in the canonical task; for every other A-to-B "
                "mapping, leave panel C unchanged."
            ),
            "canonical_racket_matches_stored": [
                actual == pair["output"] for actual, pair in zip(canonical_racket_outputs, pairs)
            ],
            "fits_every_canonical_pair": [
                shortcut(pair["input"]) == pair["output"] for pair in pairs
            ],
        },
        "counterexample": {
            "replay": replay,
            "observed_overrides": gen.observe_overrides(counterexample),
            "input": counterexample,
            "racket_output": racket_output,
            "python_mirror_output": gen._apply_rule(counterexample),
            "shortcut_output": shortcut_output,
            "racket_matches_python_mirror": racket_output == gen._apply_rule(counterexample),
            "shortcut_disagrees": racket_output != shortcut_output,
            "self_check": gen.self_check(counterexample),
            "teaching_reasons": gen._teaching_reasons(counterexample),
            "witness_fires": gen.SEMANTIC_WITNESSES["transform_rot180_unique"](counterexample),
        },
        "ordinary_schedule_probes": transform_windows,
        "ordinary_generation_emits_unseen_canonical_branches": all(
            row["covers_all_eight"] for row in transform_windows
        ),
    }

    if not all(report["shortcut"]["canonical_racket_matches_stored"]):
        raise AssertionError("selected Racket authority does not reproduce canonical outputs")
    if not all(report["shortcut"]["fits_every_canonical_pair"]):
        raise AssertionError("declared shortcut does not fit every canonical pair")
    if not report["counterexample"]["racket_matches_python_mirror"]:
        raise AssertionError("Python semantic mirror diverges from Racket on counterexample")
    if not report["counterexample"]["shortcut_disagrees"]:
        raise AssertionError("counterexample does not separate the shortcut")
    if report["counterexample"]["self_check"] or report["counterexample"]["teaching_reasons"]:
        raise AssertionError("counterexample is outside the selected generator grammar")
    if not report["ordinary_generation_emits_unseen_canonical_branches"]:
        raise AssertionError("ordinary schedule probe did not cover all eight transforms")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "canonical_fit": all(report["shortcut"]["fits_every_canonical_pair"]),
        "counterexample_disagrees": report["counterexample"]["shortcut_disagrees"],
        "racket_matches_python": report["counterexample"]["racket_matches_python_mirror"],
        "ordinary_schedule_covers_all_eight": report["ordinary_generation_emits_unseen_canonical_branches"],
    }, indent=2))


if __name__ == "__main__":
    main()
