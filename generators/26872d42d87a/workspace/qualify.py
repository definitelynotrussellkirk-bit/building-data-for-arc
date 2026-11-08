#!/usr/bin/env python3
"""Fast source-only qualification census for generator 26872d42d87a.

This task-local probe complements the repository battery.  It checks the exact
failure modes that motivated the repair:

* all labeled canonical inputs are accepted and reproduced by the Python mirror;
* declared shortcuts genuinely fit every canonical pair;
* every generated input refutes both the whole-row-span and vertical-extension
  shortcuts while retaining the intended local transformation;
* all five exact scene profiles are observable in every difficulty band; and
* every held-out query rotation is identifiable against the declared lesson
  competitors.

The tool intentionally does not execute Racket.  Use the shared battery for the
independent Python/Racket authority check.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "26872d42d87a"
BANDS = ("easy", "medium", "hard")
LESSON_SIZE = 4
HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "generator.py"


def _load_generator(source: Path | None = None):
    # Load the task source directly so the CLI works both in the repository and
    # in the battery's staged runtime.  The task package exists only in the
    # latter environment.
    path = Path(source or DEFAULT_SOURCE).resolve()
    name = f"qualification_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(module: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": module.rule_mirror(grid)}


def _merged_competitors(module: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, solve in getattr(module, namespace, {}).items():
            merged.setdefault(name, solve)
    return merged


def run_qualification(
    *,
    per_band: int = 100,
    seed: int = 731,
    source: Path | None = None,
) -> dict[str, Any]:
    """Run the task-local census and return a JSON-serializable report."""
    if per_band < 1:
        raise ValueError("per_band must be positive")

    module = _load_generator(source)
    root = find_root(__file__)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    errors: list[dict[str, Any]] = []

    canonical_rows: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical):
        validation = list(module.self_check(deepcopy(pair["input"])))
        mirror_matches = module.rule_mirror(deepcopy(pair["input"])) == pair["output"]
        canonical_rows.append(
            {
                "index": index,
                "shape": [len(pair["input"]), len(pair["input"][0])],
                "self_check_errors": validation,
                "mirror_matches_label": mirror_matches,
            }
        )
        if validation:
            errors.append(
                {
                    "kind": "canonical_rejected",
                    "index": index,
                    "reasons": validation,
                }
            )
        if not mirror_matches:
            errors.append({"kind": "canonical_mirror_mismatch", "index": index})

    shortcuts: dict[str, Any] = dict(getattr(module, "CANONICAL_SHORTCUTS", {}))
    shortcut_rows: dict[str, dict[str, Any]] = {}
    for name, solve in shortcuts.items():
        matches = [
            solve(deepcopy(pair["input"])) == pair["output"] for pair in canonical
        ]
        shortcut_rows[name] = {
            "fits_all_canonical": all(matches),
            "canonical_matches": matches,
            "generated_counterexamples": 0,
            "first_counterexample": None,
        }
        if not all(matches):
            errors.append({"kind": "misdeclared_canonical_shortcut", "name": name})

    schedule_profiles: Counter[str] = Counter()
    witness_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    generated_inputs = 0
    invalid_inputs = 0
    no_op_inputs = 0

    for band_index, band in enumerate(BANDS):
        band_seed = seed + band_index * 100_003
        for sample_index in range(per_band):
            grid = module.generate(band_seed, sample_index, difficulty=band)
            generated_inputs += 1
            validation = list(module.self_check(deepcopy(grid), difficulty=band))
            if validation:
                invalid_inputs += 1
                errors.append(
                    {
                        "kind": "invalid_generated_input",
                        "band": band,
                        "sample_index": sample_index,
                        "reasons": validation,
                    }
                )
                continue
            observed = module.observe_overrides(deepcopy(grid))
            profile = str(observed["scene_profile"])
            schedule_profiles[profile] += 1
            unique_inputs.add(_grid_hash(grid))
            expected = module.rule_mirror(deepcopy(grid))
            if expected == grid:
                no_op_inputs += 1
                errors.append(
                    {
                        "kind": "generated_no_op",
                        "band": band,
                        "sample_index": sample_index,
                    }
                )
            for witness_name, predicate in module.SEMANTIC_WITNESSES.items():
                if predicate(deepcopy(grid)):
                    witness_counts[witness_name] += 1
                else:
                    errors.append(
                        {
                            "kind": "missing_semantic_witness",
                            "witness": witness_name,
                            "band": band,
                            "sample_index": sample_index,
                        }
                    )
            for name, solve in shortcuts.items():
                if solve(deepcopy(grid)) != expected:
                    row = shortcut_rows[name]
                    row["generated_counterexamples"] += 1
                    if row["first_counterexample"] is None:
                        row["first_counterexample"] = {
                            "band": band,
                            "sample_index": sample_index,
                            "profile": profile,
                        }
                else:
                    errors.append(
                        {
                            "kind": "shortcut_survives_generated_input",
                            "name": name,
                            "band": band,
                            "sample_index": sample_index,
                        }
                    )

    competitors = _merged_competitors(module)
    lesson_rotations = 0
    ambiguous_rotations = 0
    ambiguity_counts: Counter[str] = Counter()
    for band_index, band in enumerate(BANDS):
        band_seed = seed + 700_001 + band_index * 100_003
        for start in range(per_band):
            pairs = [
                _pair(
                    module,
                    module.generate(
                        band_seed,
                        start * LESSON_SIZE + offset,
                        difficulty=band,
                    ),
                )
                for offset in range(LESSON_SIZE)
            ]
            for query_index, query in enumerate(pairs):
                lesson_rotations += 1
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = list(
                    module.lesson_identifiable(deepcopy(demos), deepcopy(query))
                )
                surviving = []
                for name, solve in competitors.items():
                    if all(
                        solve(deepcopy(pair["input"])) == pair["output"]
                        for pair in demos
                    ) and solve(deepcopy(query["input"])) != query["output"]:
                        surviving.append(name)
                        ambiguity_counts[name] += 1
                if reasons or surviving:
                    ambiguous_rotations += 1
                    errors.append(
                        {
                            "kind": "ambiguous_lesson_rotation",
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "hook_reasons": reasons,
                            "surviving_competitors": sorted(surviving),
                        }
                    )

    exact_override_cases = 0
    for band_index, band in enumerate(BANDS):
        for profile_index, profile in enumerate(module.SCENE_PROFILES):
            exact_override_cases += 1
            grid = module.generate(
                seed + 1_400_003 + band_index * 100_003,
                profile_index,
                difficulty=band,
                scene_profile=profile,
            )
            validation = list(module.self_check(deepcopy(grid), difficulty=band))
            observed = module.observe_overrides(deepcopy(grid))
            expected = {"scene_profile": profile}
            if validation or observed != expected:
                errors.append(
                    {
                        "kind": "exact_override_failure",
                        "band": band,
                        "requested": expected,
                        "observed": observed,
                        "reasons": validation,
                    }
                )

    source_path = source.resolve() if source is not None else DEFAULT_SOURCE.resolve()
    report = {
        "schema": "26872d42d87a-qualification-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_rule_hash": module.RULE_HASH,
        "source": str(source_path),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "status": "passed" if not errors else "failed",
        "parameters": {
            "per_band": per_band,
            "bands": list(BANDS),
            "seed": seed,
            "lesson_size": LESSON_SIZE,
            "query_policy": "all four rotations",
        },
        "summary": {
            "canonical_pairs": len(canonical),
            "generated_inputs": generated_inputs,
            "unique_inputs": len(unique_inputs),
            "invalid_inputs": invalid_inputs,
            "no_op_inputs": no_op_inputs,
            "lesson_rotations": lesson_rotations,
            "ambiguous_rotations": ambiguous_rotations,
            "exact_override_cases": exact_override_cases,
        },
        "canonical": canonical_rows,
        "canonical_shortcuts": shortcut_rows,
        "schedule_profiles": dict(sorted(schedule_profiles.items())),
        "semantic_witnesses": dict(sorted(witness_counts.items())),
        "ambiguity_counts": dict(sorted(ambiguity_counts.items())),
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="alternate generator.py to probe")
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=731)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = run_qualification(
        per_band=args.per_band,
        seed=args.seed,
        source=args.source,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
