#!/usr/bin/env python3
"""Source-bound distribution and cyclic-lesson audit for 9baf979683ef.

This is intentionally task-local: it inspects the generator's own declared
shortcuts instead of hard-coding a second rule catalog.  It complements the
shared lesson census by rotating every member of a four-pair window into the
query position.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9baf979683ef"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_generator_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_key(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _demo(gen, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}


def _axis_counts(observations: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    names = sorted({name for observed in observations for name in observed})
    return {
        name: dict(sorted(Counter(str(observed.get(name)) for observed in observations).items()))
        for name in names
    }


def run_audit(*, per_band: int = 100, cyclic_windows: int = 25) -> dict[str, Any]:
    if per_band <= 0 or cyclic_windows <= 0:
        raise ValueError("per_band and cyclic_windows must be positive")

    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    source_hash = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()

    shortcut_report: dict[str, dict[str, Any]] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        fits = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        shortcut_report[name] = {
            "pairs": len(pairs),
            "fits": fits,
            "status": "fits_all" if fits == len(pairs) else "does_not_fit_all",
        }

    bands: dict[str, Any] = {}
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(
                100_000 + band_index * 10_000 + index,
                index,
                difficulty=difficulty,
            )
            for index in range(per_band)
        ]
        observations = [gen.observe_overrides(grid) for grid in grids]
        invalid = [gen.self_check(grid) for grid in grids]
        strict = [gen.strict_canonical_like(grid) for grid in grids]
        rival_refutations = {
            name: sum(rival(grid) != gen.rule_mirror(grid) for grid in grids)
            for name, rival in gen.CANONICAL_SHORTCUTS.items()
        }
        canonical_profile_hits = sum(
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            in {(7, 11, 4), (8, 9, 4), (7, 13, 4)}
            for grid in grids
        )
        bands[difficulty] = {
            "draws": per_band,
            "invalid": sum(bool(reasons) for reasons in invalid),
            "strict_rejections": sum(bool(reasons) for reasons in strict),
            "unique_inputs": len({_grid_key(grid) for grid in grids}),
            "canonical_profile_hits": canonical_profile_hits,
            "axis_counts": _axis_counts(observations),
            "shortcut_refutations": rival_refutations,
        }

    rotations_tested = 0
    ambiguous = 0
    hook_reasons: Counter[str] = Counter()
    surviving_rivals: Counter[str] = Counter()
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for start in range(cyclic_windows):
            seed = 900_000 + band_index * 10_000 + start
            grids = [
                gen.generate(seed, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs_for_window = [_demo(gen, grid) for grid in grids]
            for query_index in range(len(pairs_for_window)):
                query_pair = pairs_for_window[query_index]
                demos = [
                    pair
                    for index, pair in enumerate(pairs_for_window)
                    if index != query_index
                ]
                query = {"input": query_pair["input"]}
                rotations_tested += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    ambiguous += 1
                    hook_reasons.update(reasons)
                truth = gen.rule_mirror(query["input"])
                for name, rival in gen.LESSON_COMPETITORS.items():
                    survives_demos = all(
                        rival(pair["input"]) == pair["output"] for pair in demos
                    )
                    if survives_demos and rival(query["input"]) != truth:
                        surviving_rivals[name] += 1

    return {
        "schema": "9baf979683ef-distribution-audit-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "sampler": {
            "per_band": per_band,
            "cyclic_windows_per_band": cyclic_windows,
            "bands": ["easy", "medium", "hard"],
        },
        "canonical_shortcuts": shortcut_report,
        "bands": bands,
        "cyclic_lessons": {
            "rotations_tested": rotations_tested,
            "ambiguous": ambiguous,
            "hook_reasons": dict(sorted(hook_reasons.items())),
            "surviving_rivals": dict(sorted(surviving_rivals.items())),
        },
        "limits": [
            "Finite declared-rival audit; it does not prove universal identifiability.",
            "Exact grid hashes measure byte-level uniqueness, not semantic equivalence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--cyclic-windows", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit(per_band=args.per_band, cyclic_windows=args.cyclic_windows)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["cyclic_lessons"]["ambiguous"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
