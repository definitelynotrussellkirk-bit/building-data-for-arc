#!/usr/bin/env python3
"""Independent, source-bound shortcut and lesson probe for 625b40fb6218.

This is reviewer tooling, not label authority.  It deliberately reimplements the
pixel rule and two canonical-fitting shortcuts instead of calling the generator's
semantic helpers.  The official battery and lesson census remain the Racket-bound
authority checks; this probe is the cheap deterministic diagnostic future agents
can run while editing the generator.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Sequence

from reviewer_support import canonical_pairs, find_root

TASK_ID = "625b40fb6218"
HERE = Path(__file__).resolve()
HOME = HERE.parents[1]
ROOT = find_root(HERE)
BANDS = (None, "easy", "medium", "hard")
RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha256(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def load_generator(path: str | Path | None = None):
    selected = Path(path or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location(
        f"review_probe_{TASK_ID}_{file_sha256(selected)[:12]}", selected
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def split_halves(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], list[list[int]]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    height = len(grid)
    width = len(grid[0])
    separators = [
        col for col in range(width) if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected one full-height color-5 separator, found {separators}")
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError("separator must divide equal-width panels")
    left = [list(row[:separator]) for row in grid]
    right = [list(row[separator + 1 :]) for row in grid]
    return left, right


def intended_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    left, right = split_halves(grid)
    result: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                row.append(2)
            elif left_value == 0 and right_value != 0:
                row.append(1)
            else:
                row.append(left_value)
        result.append(row)
    return result


def equal_overlap_only(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: erase unequal occupied overlaps."""
    left, right = split_halves(grid)
    result: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                row.append(2)
            elif left_value == 0 and right_value != 0:
                row.append(1)
            elif left_value == right_value:
                row.append(left_value)
            else:
                row.append(0)
        result.append(row)
    return result


def right_priority_overlap(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: preserve the right color on conflicts."""
    left, right = split_halves(grid)
    result: list[list[int]] = []
    for left_row, right_row in zip(left, right):
        row: list[int] = []
        for left_value, right_value in zip(left_row, right_row):
            if left_value != 0 and right_value == 0:
                row.append(2)
            elif left_value == 0 and right_value != 0:
                row.append(1)
            elif left_value != 0 and right_value != 0:
                row.append(right_value)
            else:
                row.append(0)
        result.append(row)
    return result


RIVALS = {
    "equal_overlap_only": equal_overlap_only,
    "right_priority_overlap": right_priority_overlap,
}


def pinned_seed(kind: str, band: str | None, ordinal: int) -> int:
    payload = f"{TASK_ID}:reference-probe-v1:{kind}:{band}:{ordinal}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def build_report(
    *,
    samples_per_band: int = 100,
    lessons_per_band: int = 100,
    generator_path: str | Path | None = None,
) -> dict[str, Any]:
    if samples_per_band < 1 or lessons_per_band < 1:
        raise ValueError("sample counts must be positive")
    generator = load_generator(generator_path)
    selected_path = Path(generator.__file__).resolve()

    canonical = canonical_pairs(TASK_ID, root=ROOT)
    canonical_shortcut_fit = Counter()
    canonical_mismatches = 0
    for item in canonical:
        truth = item["output"]
        canonical_mismatches += intended_output(item["input"]) != truth
        for name, rival in RIVALS.items():
            canonical_shortcut_fit[name] += rival(item["input"]) == truth

    generated_totals = Counter()
    rival_agreements = Counter({name: 0 for name in RIVALS})
    per_band: dict[str, Any] = {}
    unique_inputs: set[str] = set()
    for band in BANDS:
        band_key = "default" if band is None else band
        band_shapes = Counter()
        band_palettes = Counter()
        band_conflicts = Counter()
        band_unique: set[str] = set()
        for ordinal in range(samples_per_band):
            seed = pinned_seed("sample", band, ordinal)
            grid = generator.generate(seed, ordinal * 11, difficulty=band)
            digest = grid_sha256(grid)
            unique_inputs.add(digest)
            band_unique.add(digest)
            generated_totals["inputs"] += 1
            findings = list(generator.self_check(grid) or [])
            generated_totals["self_check_errors"] += bool(findings)
            truth = intended_output(grid)
            generated_totals["oracle_mismatches"] += generator.rule_mirror(grid) != truth
            observed = generator.observe_overrides(grid)
            band_shapes[f"{observed['grid_h']}x{observed['half_w']}"] += 1
            band_palettes[str(observed["palette_size"])] += 1
            band_conflicts[str(observed["n_shared_conflict"])] += 1
            for name, rival in RIVALS.items():
                agrees = rival(grid) == truth
                rival_agreements[name] += agrees
                generated_totals[f"{name}_agreements"] += agrees
        per_band[band_key] = {
            "inputs": samples_per_band,
            "unique_inputs": len(band_unique),
            "shapes": _counter_dict(band_shapes),
            "palette_sizes": _counter_dict(band_palettes),
            "unequal_overlap_counts": _counter_dict(band_conflicts),
        }

    lesson_totals = Counter()
    lesson_examples: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for ordinal in range(lessons_per_band):
            seed = pinned_seed("lesson", band, ordinal)
            pairs = []
            for offset in range(5):
                grid = generator.generate(seed, ordinal * 13 + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            lesson_totals["lessons"] += 1
            lesson_totals["rotations"] += len(pairs)
            for query_index, query in enumerate(pairs):
                demos = [item for index, item in enumerate(pairs) if index != query_index]
                reasons = list(generator.lesson_identifiable(demos, query) or [])
                surviving = [
                    name
                    for name, rival in RIVALS.items()
                    if all(rival(item["input"]) == item["output"] for item in demos)
                ]
                if reasons or surviving:
                    lesson_totals["rotation_failures"] += 1
                    if len(lesson_examples) < 12:
                        lesson_examples.append(
                            {
                                "band": band,
                                "ordinal": ordinal,
                                "query_index": query_index,
                                "hook_reasons": reasons,
                                "surviving_rivals": surviving,
                            }
                        )

    return {
        "schema": "625b40fb6218-reference-probe-v1",
        "task_id": TASK_ID,
        "generator": {
            "path": str(selected_path),
            "sha256": file_sha256(selected_path),
            "version": getattr(generator, "VERSION", None),
            "rule_hash": getattr(generator, "RULE_HASH", None),
        },
        "canonical": {
            "pairs": len(canonical),
            "oracle_mismatches": int(canonical_mismatches),
            "shortcut_fit_counts": _counter_dict(canonical_shortcut_fit),
        },
        "generated": {
            "inputs": int(generated_totals["inputs"]),
            "unique_inputs": len(unique_inputs),
            "self_check_errors": int(generated_totals["self_check_errors"]),
            "oracle_mismatches": int(generated_totals["oracle_mismatches"]),
            "rival_agreements": {
                name: int(rival_agreements[name]) for name in sorted(RIVALS)
            },
            "per_band": per_band,
        },
        "lessons": {
            "lessons": int(lesson_totals["lessons"]),
            "demonstrations_per_lesson": 4,
            "queries_per_lesson": 1,
            "query_policy": "all five cyclic query positions checked",
            "rotations": int(lesson_totals["rotations"]),
            "rotation_failures": int(lesson_totals["rotation_failures"]),
            "failure_examples": lesson_examples,
        },
        "limitations": [
            "The independent Python oracle is diagnostic, not the Racket label authority.",
            "Finite pinned samples test only the two declared canonical-fitting shortcuts.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=100)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--generator")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report(
        samples_per_band=args.samples_per_band,
        lessons_per_band=args.lessons_per_band,
        generator_path=args.generator,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    failures = (
        report["canonical"]["oracle_mismatches"]
        + report["generated"]["self_check_errors"]
        + report["generated"]["oracle_mismatches"]
        + sum(report["generated"]["rival_agreements"].values())
        + report["lessons"]["rotation_failures"]
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
