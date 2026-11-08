#!/usr/bin/env python3
"""Source-bound probe for canonical shortcuts and production lesson windows.

The probe intentionally reads the selected generator's live
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` declarations.  It is an
authoring diagnostic, not a proof of uniqueness against undeclared rules.
Run it through ``run_with_racket.py`` so the portable reviewer helpers are on
``PYTHONPATH``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "dc657616ec21"
DIFFICULTIES: tuple[str | None, ...] = (None, "easy", "medium", "hard")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"workspace_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _difficulty_name(value: str | None) -> str:
    return "default" if value is None else value


def _canonical_checks(gen, pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        cases: list[dict[str, Any]] = []
        for index, pair in enumerate(pairs):
            rival_output = rival(deepcopy(pair["input"]))
            usable = rival_output is not None
            cases.append(
                {
                    "index": index,
                    "input_sha256": _grid_sha256(pair["input"]),
                    "usable": usable,
                    "fits": usable and rival_output == pair["output"],
                }
            )
        usable_cases = [case for case in cases if case["usable"]]
        reports.append(
            {
                "rival": name,
                "usable_pairs": len(usable_cases),
                "total_pairs": len(cases),
                "fits_all_usable_pairs": bool(usable_cases)
                and all(case["fits"] for case in usable_cases),
                "cases": cases,
            }
        )
    return reports


def _generated_witnesses(gen, *, seed: int, search_limit: int) -> list[dict[str, Any]]:
    witnesses: list[dict[str, Any]] = []
    for name, rival in gen.LESSON_COMPETITORS.items():
        found: dict[str, Any] | None = None
        for difficulty in DIFFICULTIES:
            for sample_index in range(search_limit):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                intended = gen.rule_mirror(deepcopy(grid))
                rival_output = rival(deepcopy(grid))
                if rival_output is not None and rival_output != intended:
                    facts = None
                    if hasattr(gen, "_analyze"):
                        analyzed, errors = gen._analyze(deepcopy(grid))
                        if not errors:
                            facts = {
                                "depths": analyzed.get("depths"),
                                "bbox_classes": [
                                    panel.get("bbox_shortcut_class")
                                    for panel in analyzed.get("panels", [])
                                ],
                            }
                    found = {
                        "rival": name,
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": _difficulty_name(difficulty),
                        "input_sha256": _grid_sha256(grid),
                        "validator_errors": gen.self_check(deepcopy(grid)),
                        "input": grid,
                        "facts": facts,
                        "intended_output": intended,
                        "rival_output": rival_output,
                    }
                    break
            if found is not None:
                break
        if found is not None:
            witnesses.append(found)
    return witnesses


def _lesson_windows(gen, *, seed: int, search_limit: int) -> dict[str, Any]:
    demos_per_query = int(gen.EXAMPLES_NEEDED)
    windows = 0
    rotations = 0
    ambiguous: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

    for difficulty in DIFFICULTIES:
        for start in range(search_limit):
            labeled: list[dict[str, Any]] = []
            for sample_index in range(start, start + demos_per_query + 1):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                unique_inputs.add(_grid_sha256(grid))
                labeled.append(
                    {
                        "input": grid,
                        "output": gen.rule_mirror(deepcopy(grid)),
                    }
                )
            windows += 1
            for held_out_index, query in enumerate(labeled):
                rotations += 1
                demos = [
                    pair for index, pair in enumerate(labeled) if index != held_out_index
                ]
                reasons = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                if reasons:
                    ambiguous.append(
                        {
                            "difficulty": _difficulty_name(difficulty),
                            "start": start,
                            "held_out_index": held_out_index,
                            "reasons": reasons,
                            "query_input_sha256": _grid_sha256(query["input"]),
                        }
                    )

    return {
        "policy": "consecutive generated pairs; hold out each pair once",
        "seed": seed,
        "start_range": [0, search_limit - 1] if search_limit else [],
        "difficulties": [_difficulty_name(value) for value in DIFFICULTIES],
        "demonstrations_per_query": demos_per_query,
        "windows": windows,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "ambiguous_rotations": len(ambiguous),
        "first_ambiguities": ambiguous[:10],
    }


def build_report(gen, root: Path, *, seed: int = 1701, search_limit: int = 32) -> dict[str, Any]:
    """Build a deterministic report against the supplied live generator module."""
    if search_limit < 1:
        raise ValueError("search_limit must be at least 1")
    root = Path(root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    generator_path = Path(gen.__file__).resolve()
    canonical_file = canonical_path(root)
    canonical_checks = _canonical_checks(gen, pairs)
    witnesses = _generated_witnesses(gen, seed=seed, search_limit=search_limit)
    lesson_windows = _lesson_windows(gen, seed=seed, search_limit=search_limit)

    missing_witnesses = sorted(set(gen.LESSON_COMPETITORS) - {w["rival"] for w in witnesses})
    canonical_failures = [
        item["rival"]
        for item in canonical_checks
        if not item["fits_all_usable_pairs"]
    ]
    return {
        "schema": "arcpuzzles-bbox-rival-probe-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(gen, "VERSION", None),
        "generator_sha256": _sha256(generator_path),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_file_sha256": _sha256(canonical_file),
        "seed": seed,
        "search_limit": search_limit,
        "canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        "lesson_competitors": sorted(gen.LESSON_COMPETITORS),
        "canonical_checks": canonical_checks,
        "canonical_failures": canonical_failures,
        "generated_witnesses": witnesses,
        "missing_generated_witnesses": missing_witnesses,
        "lesson_windows": lesson_windows,
        "scope_limit": (
            "Finite source-bound checks against declared rivals only; this does not "
            "establish uniqueness against undeclared hypotheses or all possible seeds."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--search-limit", type=int, default=32)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    gen = _load_generator()
    root = find_root(__file__)
    report = build_report(gen, root, seed=args.seed, search_limit=args.search_limit)
    text = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(args.out)
    else:
        print(text, end="")
    return 1 if report["canonical_failures"] or report["missing_generated_witnesses"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
