#!/usr/bin/env python3
"""Source-bound semantic census for generator ``aea1d569d78b``.

This probe complements the shared battery.  It iterates the generator's actual
shortcut/rival declarations, verifies canonical shortcuts against every usable
canonical pair, checks each sampled demonstration as a one-example teaching
set, and exhaustively rotates queries through consecutive three-example
windows.  Generated labels come from the task-local independent Python mirror;
the shared Racket-backed battery/census remains the label-authority check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "aea1d569d78b"
HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"semantic_probe_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _first_difference(left, right):
    if len(left) != len(right):
        return {"kind": "height", "left": len(left), "right": len(right)}
    for row, (lrow, rrow) in enumerate(zip(left, right)):
        if len(lrow) != len(rrow):
            return {"kind": "width", "row": row, "left": len(lrow), "right": len(rrow)}
        for column, (lvalue, rvalue) in enumerate(zip(lrow, rrow)):
            if lvalue != rvalue:
                return {
                    "kind": "cell",
                    "row": row,
                    "column": column,
                    "left": lvalue,
                    "right": rvalue,
                }
    return None


def run(per_band: int) -> dict[str, Any]:
    gen = _load_generator()
    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root)
    failures: list[dict[str, Any]] = []

    canonical_shortcuts = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = []
        for index, pair in enumerate(canonical):
            match = rival(pair["input"]) == pair["output"]
            fits.append(match)
            if not match:
                failures.append(
                    {"kind": "canonical_shortcut_miss", "rival": name, "pair": index}
                )
        canonical_shortcuts[name] = {"fits": sum(fits), "total": len(fits)}

    band_reports = {}
    lessons = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles: dict[str, int] = {}
        orientations: dict[str, int] = {}
        palettes: set[tuple[int, ...]] = set()
        unique_inputs: set[str] = set()
        crossings = 0
        rival_refutations = {name: 0 for name in gen.LESSON_COMPETITORS}
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        band_lessons = []

        for sample_index in range(per_band):
            seed = 610_000 + 100_000 * band_index + sample_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(grid)
            if errors:
                failures.append(
                    {
                        "kind": "self_check",
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": errors,
                    }
                )
            observed = gen.observe_overrides(grid)
            profiles[observed["canvas_profile"]] = profiles.get(observed["canvas_profile"], 0) + 1
            orientation = observed["blocked_orientation"]
            orientations[orientation] = orientations.get(orientation, 0) + 1
            palettes.add(tuple(sorted({value for row in grid for value in row})))
            unique_inputs.add(_grid_key(grid))
            crossings += int(gen.has_clear_crossing(grid))

            truth = gen.rule_mirror(grid)
            pair = {"input": grid, "output": truth}
            lesson_errors = gen.lesson_identifiable([pair], pair)
            if lesson_errors:
                failures.append(
                    {
                        "kind": "single_demo_ambiguity",
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": lesson_errors,
                    }
                )
            for name, rival in gen.LESSON_COMPETITORS.items():
                prediction = rival(grid)
                if prediction != truth:
                    rival_refutations[name] += 1
                else:
                    failures.append(
                        {
                            "kind": "unrefuted_rival",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "rival": name,
                        }
                    )
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hit = bool(witness(grid))
                witness_hits[name] += int(hit)
                if not hit:
                    failures.append(
                        {
                            "kind": "missing_witness",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "witness": name,
                        }
                    )
            band_lessons.append(pair)
            lessons.append(pair)

        rotations_checked = 0
        rotation_failures = 0
        width = gen.EXAMPLES_NEEDED
        if len(band_lessons) >= width:
            for start in range(len(band_lessons)):
                window = [band_lessons[(start + offset) % len(band_lessons)] for offset in range(width)]
                for query_index, query in enumerate(window):
                    demos = [pair for index, pair in enumerate(window) if index != query_index]
                    rotations_checked += 1
                    reasons = gen.lesson_identifiable(demos, query)
                    if reasons:
                        rotation_failures += 1
                        failures.append(
                            {
                                "kind": "rotation_ambiguity",
                                "band": band,
                                "start": start,
                                "query_index": query_index,
                                "errors": reasons,
                            }
                        )

        band_reports[band] = {
            "samples": per_band,
            "unique_inputs": len(unique_inputs),
            "profiles": profiles,
            "blocked_orientations": orientations,
            "distinct_palettes": len(palettes),
            "clear_crossings": crossings,
            "rival_refutations": rival_refutations,
            "witness_hits": witness_hits,
            "rotation_policy": "all cyclic starts; each of three positions held out",
            "rotations_checked": rotations_checked,
            "rotation_failures": rotation_failures,
        }

    shortcut_witnesses = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        witness = next(
            (
                pair
                for pair in lessons
                if rival(pair["input"]) != pair["output"]
            ),
            None,
        )
        if witness is None:
            failures.append({"kind": "missing_generated_shortcut_witness", "rival": name})
            continue
        prediction = rival(witness["input"])
        shortcut_witnesses[name] = {
            "input": witness["input"],
            "intended_output": witness["output"],
            "rival_output": prediction,
            "first_difference": _first_difference(witness["output"], prediction),
        }

    authority_path = (
        root
        / "shared/data/base/solutions/banks/d3d681cdb82a/E51__aea1d569d78b.json"
    )
    return {
        "schema": "aea1d569d78b-semantic-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "authority_file_sha256": _sha256(authority_path),
        "canonical_pairs": len(canonical),
        "examples_needed": gen.EXAMPLES_NEEDED,
        "canonical_shortcuts": canonical_shortcuts,
        "bands": band_reports,
        "shortcut_witnesses": shortcut_witnesses,
        "limitations": [
            "Finite checks cover only declared rivals, not all possible hypotheses.",
            "Generated labels here use rule_mirror; use the shared battery/census for Racket-authority evidence.",
        ],
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 3:
        parser.error("--per-band must be at least 3 for cyclic three-example windows")
    report = run(args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    print(
        f"{report['status'].upper()}: {args.per_band * 3} samples; "
        f"{len(report['failures'])} failures",
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
