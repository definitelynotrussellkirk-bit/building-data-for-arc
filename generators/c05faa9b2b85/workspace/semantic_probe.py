#!/usr/bin/env python3
"""Reproducible semantic audit for c05faa9b2b85.

The probe uses the generator's own declared contracts rather than a copied list
of rival names.  It checks canonical compatibility, every exact override
combination, all cyclic starts of the three-profile lesson schedule, and writes
one exact input where each surviving canonical shortcut disagrees with the
pinned rule mirror.  Canonical data are used only for generator review, never by
a solve episode.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c05faa9b2b85"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = HOME / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(grid, gen) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(deepcopy(grid))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    gen = _load_generator()
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))

    canonical_shortcuts: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = [rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical]
        canonical_shortcuts[name] = {
            "fits_all": all(fits),
            "fits": fits,
            "canonical_pairs": len(fits),
        }

    override_rows: list[dict[str, Any]] = []
    for scene_profile in gen.SCENE_PROFILES:
        for canvas_profile in gen.CANVAS_PROFILES:
            for n_rooms in range(2, 5):
                grid = gen.generate(
                    1701,
                    23,
                    difficulty="hard",
                    scene_profile=scene_profile,
                    canvas_profile=canvas_profile,
                    n_rooms=n_rooms,
                )
                override_rows.append(
                    {
                        "requested": {
                            "scene_profile": scene_profile,
                            "canvas_profile": canvas_profile,
                            "n_rooms": n_rooms,
                        },
                        "observed": gen.observe_overrides(grid),
                        "self_check": gen.self_check(grid),
                        "nonidentity": gen.rule_mirror(deepcopy(grid)) != grid,
                    }
                )

    cyclic_windows: list[dict[str, Any]] = []
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        grids = [gen.generate(44_000 + start, start + offset, difficulty="medium") for offset in range(4)]
        demos = [_pair(grid, gen) for grid in grids[: gen.EXAMPLES_NEEDED]]
        query = _pair(grids[gen.EXAMPLES_NEEDED], gen)
        cyclic_windows.append(
            {
                "start": start,
                "demo_profiles": [gen.observe_overrides(pair["input"])["scene_profile"] for pair in demos],
                "query_profile": gen.observe_overrides(query["input"])["scene_profile"],
                "lesson_errors": gen.lesson_identifiable(demos, query),
                "rival_fits_all_demos": {
                    name: all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
                    for name, rival in gen.LESSON_COMPETITORS.items()
                },
            }
        )

    witness = gen.generate(
        712,
        9,
        difficulty="medium",
        scene_profile="single_notch",
        canvas_profile="canonical_11x15",
        n_rooms=4,
    )
    intended = gen.rule_mirror(deepcopy(witness))
    rival_outputs = {
        name: rival(deepcopy(witness)) for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }

    report = {
        "schema": "c05faa9b2b85-semantic-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(GENERATOR_PATH.relative_to(find_root(__file__))),
        "generator_sha256": _sha256(GENERATOR_PATH),
        "rule_hash": gen.RULE_HASH,
        "canonical_shortcuts": canonical_shortcuts,
        "override_combinations": {
            "count": len(override_rows),
            "all_constructive_observable_nonidentity": all(
                not row["self_check"]
                and row["requested"] == row["observed"]
                and row["nonidentity"]
                for row in override_rows
            ),
            "rows": override_rows,
        },
        "cyclic_schedule_windows": {
            "assembly": f"{gen.EXAMPLES_NEEDED} consecutive demos followed by one query",
            "period": period,
            "all_identifiable": all(not row["lesson_errors"] for row in cyclic_windows),
            "rows": cyclic_windows,
        },
        "witness": {
            "seed": 712,
            "sample_index": 9,
            "difficulty": "medium",
            "overrides": {
                "scene_profile": "single_notch",
                "canvas_profile": "canonical_11x15",
                "n_rooms": 4,
            },
            "observed": gen.observe_overrides(witness),
            "self_check": gen.self_check(witness),
            "strict_canonical_like": gen.strict_canonical_like(witness),
            "witnesses": {
                name: predicate(witness) for name, predicate in gen.SEMANTIC_WITNESSES.items()
            },
            "input": witness,
            "intended_output_python_mirror": intended,
            "rival_outputs": rival_outputs,
            "rivals_disagree": {
                name: output != intended for name, output in rival_outputs.items()
            },
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "canonical_shortcuts_fit": all(v["fits_all"] for v in canonical_shortcuts.values()),
        "override_combinations": len(override_rows),
        "overrides_pass": report["override_combinations"]["all_constructive_observable_nonidentity"],
        "cyclic_windows": period,
        "cyclic_windows_pass": report["cyclic_schedule_windows"]["all_identifiable"],
        "rivals_disagree": report["witness"]["rivals_disagree"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
