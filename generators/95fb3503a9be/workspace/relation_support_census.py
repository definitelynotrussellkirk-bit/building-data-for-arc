#!/usr/bin/env python3
"""Measure canonical relational support and shortcut survival for 95fb3503a9be.

This probe exists because pooled morphology/diversity counts can look healthy
while every generated input shares one accidental layout convention.  It checks
whole four-sample lessons, not only aggregate scene counts, and can compare the
frozen review baseline with the current source.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable, Iterable


TASK_ID = "95fb3503a9be"
DEFAULT_BANDS = ("easy", "medium", "hard")


def _occupied_column_runs(grid: list[list[int]]) -> int:
    occupied = [any(row[c] != 0 for row in grid) for c in range(len(grid[0]))]
    return sum(
        used and (index == 0 or not occupied[index - 1])
        for index, used in enumerate(occupied)
    )


def grid_signature(
    grid: list[list[int]],
    object_records: Callable[[list[list[int]]], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Return the low-cost relational signature used by this gate prototype."""
    records = object_records(grid)
    overlapping = any(
        max(records[i]["bbox"][1], records[j]["bbox"][1])
        <= min(records[i]["bbox"][3], records[j]["bbox"][3])
        for i in range(len(records))
        for j in range(i + 1, len(records))
    )
    crop_widths = [rec["bbox"][3] - rec["bbox"][1] + 1 for rec in records]
    return {
        "overlapping_bbox_columns": overlapping,
        "max_crop_width": max(crop_widths, default=0),
        "occupied_column_runs": _occupied_column_runs(grid),
        "object_sizes": sorted(rec["size"] for rec in records),
    }


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def census_variant(
    module: Any,
    *,
    seeds: int,
    bands: Iterable[str] = DEFAULT_BANDS,
    schedule_size: int = 4,
    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] | None = None,
    rule: Callable[[list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    """Census generated scenes and require support inside each complete lesson."""
    if seeds < 1 or schedule_size < 1:
        raise ValueError("seeds and schedule_size must be positive")
    bands = tuple(bands)
    if not bands:
        raise ValueError("at least one difficulty band is required")

    object_records = module._object_records
    rivals = rivals if rivals is not None else getattr(module, "SEMANTIC_RIVALS", {})
    rule = rule if rule is not None else module.rule_mirror

    feature_counts = Counter()
    run_histogram = Counter()
    width_histogram = Counter()
    rival_disagreements = Counter()
    rival_errors = Counter()
    unique = set()
    generation_errors = 0
    self_check_failures = 0
    first_errors: list[dict[str, Any]] = []
    lessons = 0
    lesson_overlap = 0
    lesson_width4 = 0

    for band in bands:
        for seed in range(seeds):
            lessons += 1
            lesson_has_overlap = False
            lesson_has_width4 = False
            for sample_index in range(schedule_size):
                try:
                    grid = module.generate(seed, sample_index, difficulty=band)
                except Exception as exc:  # evidence should count, not hide, failures
                    generation_errors += 1
                    if len(first_errors) < 8:
                        first_errors.append({
                            "kind": "generate",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                    continue

                unique.add(_grid_digest(grid))
                problems = module.self_check(copy.deepcopy(grid))
                if problems:
                    self_check_failures += 1
                    if len(first_errors) < 8:
                        first_errors.append({
                            "kind": "self_check",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "problems": list(problems),
                        })

                signature = grid_signature(grid, object_records)
                overlap = signature["overlapping_bbox_columns"]
                width4 = signature["max_crop_width"] >= 4
                feature_counts["overlapping_bbox_columns"] += int(overlap)
                feature_counts["max_crop_width_at_least_4"] += int(width4)
                run_histogram[str(signature["occupied_column_runs"])] += 1
                width_histogram[str(signature["max_crop_width"])] += 1
                lesson_has_overlap |= overlap
                lesson_has_width4 |= width4

                official = rule(copy.deepcopy(grid))
                for rival_name in ("column_bands", "crop_width_three"):
                    rival = rivals.get(rival_name)
                    if rival is None:
                        continue
                    try:
                        predicted = rival(copy.deepcopy(grid))
                    except Exception as exc:
                        rival_errors[rival_name] += 1
                        if len(first_errors) < 8:
                            first_errors.append({
                                "kind": "rival",
                                "rival": rival_name,
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "error": f"{type(exc).__name__}: {exc}",
                            })
                        continue
                    rival_disagreements[rival_name] += int(predicted != official)

            lesson_overlap += int(lesson_has_overlap)
            lesson_width4 += int(lesson_has_width4)

    scenes = seeds * len(bands) * schedule_size
    return {
        "scenes": scenes,
        "unique_input_grids": len(unique),
        "generation_errors": generation_errors,
        "self_check_failures": self_check_failures,
        "feature_counts": dict(feature_counts),
        "occupied_column_runs": dict(sorted(run_histogram.items())),
        "max_crop_width": dict(sorted(width_histogram.items())),
        "rival_disagreements": dict(rival_disagreements),
        "rival_errors": dict(rival_errors),
        "lesson_coverage": {
            "lessons": lessons,
            "overlapping_bbox_columns": lesson_overlap,
            "max_crop_width_at_least_4": lesson_width4,
        },
        "first_errors": first_errors,
    }


def canonical_summary(
    grids: Iterable[list[list[int]]],
    object_records: Callable[[list[list[int]]], list[dict[str, Any]]],
) -> dict[str, Any]:
    signatures = [grid_signature(grid, object_records) for grid in grids]
    return {
        "inputs": len(signatures),
        "feature_counts": {
            "overlapping_bbox_columns": sum(
                sig["overlapping_bbox_columns"] for sig in signatures
            ),
            "max_crop_width_at_least_4": sum(
                sig["max_crop_width"] >= 4 for sig in signatures
            ),
        },
        "occupied_column_runs": dict(sorted(Counter(
            str(sig["occupied_column_runs"]) for sig in signatures
        ).items())),
        "max_crop_width": dict(sorted(Counter(
            str(sig["max_crop_width"]) for sig in signatures
        ).items())),
    }


def _decode_grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return copy.deepcopy(value)


def _canonical_inputs(library: Path) -> list[list[list[int]]]:
    with (library / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row["train"])
            test = row["test"]
            pairs.extend(test if isinstance(test, list) else [test])
            return [_decode_grid(pair["input"]) for pair in pairs]
    raise ValueError(f"canonical task {TASK_ID} not found")


def _load_generator(source: Path, runtime: Path, label: str) -> Any:
    runtime_text = str(runtime)
    if runtime_text not in sys.path:
        sys.path.insert(0, runtime_text)
    module_name = f"relation_support_{label}_{hashlib.sha256(str(source).encode()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator source {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate_failures(report: dict[str, Any]) -> list[str]:
    candidate = report["variants"]["candidate"]
    coverage = candidate["lesson_coverage"]
    failures = []
    if candidate["generation_errors"]:
        failures.append(f"candidate generation errors: {candidate['generation_errors']}")
    if candidate["self_check_failures"]:
        failures.append(f"candidate self-check failures: {candidate['self_check_failures']}")
    for key in ("overlapping_bbox_columns", "max_crop_width_at_least_4"):
        if coverage[key] != coverage["lessons"]:
            failures.append(
                f"candidate lesson coverage {key}={coverage[key]}/{coverage['lessons']}"
            )
    for rival_name in ("column_bands", "crop_width_three"):
        if candidate["rival_errors"].get(rival_name, 0):
            failures.append(
                f"candidate rival {rival_name} errors: "
                f"{candidate['rival_errors'][rival_name]}"
            )
        if candidate["rival_disagreements"].get(rival_name, 0) == 0:
            failures.append(f"candidate never refutes rival {rival_name}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="ARCpuzzles library root (default: this packet's repo)",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=500)
    parser.add_argument("--schedule-size", type=int, default=4)
    parser.add_argument("--bands", nargs="+", default=list(DEFAULT_BANDS))
    parser.add_argument(
        "--baseline-source",
        type=Path,
        help="optional baseline generator.py; packet frozen baseline is auto-detected",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="write evidence but do not exit nonzero for candidate coverage failures",
    )
    args = parser.parse_args(argv)

    library = args.library.resolve()
    candidate_source = library / f"generators/{TASK_ID}/generator.py"
    baseline_source = args.baseline_source
    if baseline_source is None:
        auto = library.parent / f".review/baseline/repo/generators/{TASK_ID}/generator.py"
        baseline_source = auto if auto.is_file() else None
    if baseline_source is not None:
        baseline_source = baseline_source.resolve()

    # Imported lazily so unit tests for the pure census helpers only need a
    # prepared runtime, not the source-layout management package.
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime

    with tempfile.TemporaryDirectory(prefix="relation-support-") as directory:
        runtime = Path(directory)
        prepare_runtime(Catalog(root=library), runtime, TASK_ID)
        candidate = _load_generator(candidate_source, runtime, "candidate")
        canonical = canonical_summary(_canonical_inputs(library), candidate._object_records)
        variants = {
            "candidate": census_variant(
                candidate,
                seeds=args.seeds,
                bands=args.bands,
                schedule_size=args.schedule_size,
            )
        }
        if baseline_source is not None:
            baseline = _load_generator(baseline_source, runtime, "baseline")
            variants["baseline"] = census_variant(
                baseline,
                seeds=args.seeds,
                bands=args.bands,
                schedule_size=args.schedule_size,
                rivals=candidate.SEMANTIC_RIVALS,
                rule=candidate.rule_mirror,
            )

    report = {
        "schema": "95fb3503a9be-relation-support-census-v1",
        "task_id": TASK_ID,
        "parameters": {
            "seeds": args.seeds,
            "bands": list(args.bands),
            "schedule_size": args.schedule_size,
            "candidate_source": str(candidate_source),
            "baseline_source": str(baseline_source) if baseline_source else None,
        },
        "canonical": canonical,
        "variants": variants,
        "gate_policy": {
            "canonical_relation_min_occurrences": 2,
            "candidate_requirement": (
                "each complete four-sample lesson must contain overlapping object "
                "column projections and a crop at least four columns wide"
            ),
        },
    }
    report["failures"] = _candidate_failures(report)
    report["passed"] = not report["failures"]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "out": str(args.out.resolve()),
        "passed": report["passed"],
        "failures": report["failures"],
    }))
    return 0 if report["passed"] or args.report_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
