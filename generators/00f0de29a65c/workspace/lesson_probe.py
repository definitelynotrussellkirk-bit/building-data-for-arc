#!/usr/bin/env python3
"""Source-bound semantic lesson census for generator ``00f0de29a65c``.

This probe deliberately computes labels with a small oracle implemented in
this file.  The generator's ``rule_mirror`` is compared against that oracle;
it is never used to produce the lesson labels.  Declared competitors,
shortcuts, and witnesses are discovered from the loaded generator so the
probe remains useful when the semantic contract evolves.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from collections.abc import Callable, Iterable
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "00f0de29a65c"
BANDS = ("easy", "medium", "hard")
EXAMPLES_PER_LESSON = 5
DEFAULT_LESSONS_PER_BAND = 100
_BASE_SEED = 730_000
_BAND_SEED_OFFSETS = {"easy": 0, "medium": 100_000, "hard": 200_000}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
# Importing this retained probe should also make the packet-local generator
# runtime available to callers that load generator.py themselves (as the tests do).
for _runtime_path in (REPO_ROOT / "shared/runtime", REPO_ROOT / "src", REPO_ROOT):
    _runtime_text = str(_runtime_path)
    if _runtime_text not in sys.path:
        sys.path.insert(0, _runtime_text)

CANONICAL_RECORD = (
    REPO_ROOT
    / "shared/data/base/solutions/banks/db2a1cce4e4e/"
    "medium_74_scale_smallest_component_and_recolor__00f0de29a65c.json"
)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    """Return all five canonical input/output pairs without generator imports."""
    record = json.loads(CANONICAL_RECORD.read_text(encoding="utf-8"))
    context = record["visible_context"]
    train = context["train"]
    test_inputs = context["test_inputs"]
    test_outputs = record["verification"]["expected_test_outputs"]
    if len(test_inputs) != len(test_outputs):
        raise ValueError("canonical test input/output count mismatch")
    result = [
        {"input": pair["input"], "output": pair["output"]}
        for pair in train
    ]
    result.extend(
        {"input": item["input"], "output": output}
        for item, output in zip(test_inputs, test_outputs, strict=True)
    )
    return result


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nr, nc = row + drow, col + dcol
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            ordered = tuple(sorted(cells))
            rows = [row for row, _ in ordered]
            cols = [col for _, col in ordered]
            result.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    """Apply the canonical rule using no code or metadata from the generator."""
    components = _components(grid)
    markers = [component for component in components if component["size"] == 1]
    shapes = [component for component in components if component["size"] > 1]
    if len(markers) != 1:
        raise ValueError(f"expected exactly one singleton marker, found {len(markers)}")
    if not shapes:
        raise ValueError("expected at least one multi-cell component")

    target = min(
        shapes,
        key=lambda component: (
            component["size"],
            component["bbox"][0],
            component["bbox"][1],
        ),
    )
    row1, col1, row2, col2 = target["bbox"]
    marker_color = markers[0]["color"]
    crop = [
        [marker_color if grid[row][col] == target["color"] else 0 for col in range(col1, col2 + 1)]
        for row in range(row1, row2 + 1)
    ]
    result: list[list[int]] = []
    for row in crop:
        expanded = [value for value in row for _ in range(2)]
        result.extend([expanded[:], expanded[:]])
    return result


def _safe_call(fn: Callable[[list[list[int]]], Any], grid: list[list[int]]) -> tuple[Any, str | None]:
    try:
        return fn(grid), None
    except Exception as exc:  # report third-party semantic hooks rather than hiding them
        return None, f"{type(exc).__name__}: {exc}"


def _source_metadata(gen: Any) -> dict[str, Any]:
    source = Path(gen.__file__).resolve()
    return {
        "task_id": getattr(gen, "TASK_ID", getattr(gen, "GENERATOR_ID", None)),
        "generator_path": str(source),
        "generator_sha256": _sha256_path(source),
        "version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "probe_path": str(HERE),
        "probe_sha256": _sha256_path(HERE),
        "canonical_record": str(CANONICAL_RECORD),
        "canonical_record_sha256": _sha256_path(CANONICAL_RECORD),
    }


def audit_lessons(gen: Any, *, lessons_per_band: int = DEFAULT_LESSONS_PER_BAND) -> dict[str, Any]:
    """Run a deterministic independent-oracle census over generated lessons."""
    if isinstance(lessons_per_band, bool) or not isinstance(lessons_per_band, int):
        raise TypeError("lessons_per_band must be an integer")
    if lessons_per_band <= 0:
        raise ValueError("lessons_per_band must be positive")

    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))
    if not competitors:
        raise ValueError("generator declares no LESSON_COMPETITORS")
    if not callable(getattr(gen, "lesson_identifiable", None)):
        raise ValueError("generator declares no callable lesson_identifiable")

    canonical_errors: list[dict[str, Any]] = []
    for index, pair in enumerate(canonical_pairs()):
        try:
            observed = independent_output(pair["input"])
            if observed != pair["output"]:
                canonical_errors.append({"index": index, "error": "independent oracle mismatch"})
        except Exception as exc:
            canonical_errors.append({"index": index, "error": f"{type(exc).__name__}: {exc}"})

    totals: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    dimensions: Counter[str] = Counter()
    shape_counts: Counter[str] = Counter()
    strict_counts: Counter[str] = Counter()
    witness_hits: Counter[str] = Counter({name: 0 for name in witnesses})
    witness_errors: Counter[str] = Counter({name: 0 for name in witnesses})
    unique_inputs: set[str] = set()
    unique_outputs: set[str] = set()
    failures: list[dict[str, Any]] = []
    band_reports: dict[str, dict[str, Any]] = {}
    competitor_refutations = {
        name: {"refuted_lessons": 0, "surviving_lessons": 0, "errors": 0}
        for name in competitors
    }
    shortcut_refutations = {
        name: {"refuted_lessons": 0, "surviving_lessons": 0, "errors": 0}
        for name in shortcuts
    }

    for band in BANDS:
        band_totals: Counter[str] = Counter()
        band_profile_counts: Counter[str] = Counter()
        for lesson_index in range(lessons_per_band):
            totals["lessons"] += 1
            band_totals["lessons"] += 1
            seed = _BASE_SEED + _BAND_SEED_OFFSETS[band] + lesson_index
            start_index = lesson_index * EXAMPLES_PER_LESSON
            pairs: list[dict[str, Any]] = []
            lesson_meta = {
                "band": band,
                "lesson_index": lesson_index,
                "seed": seed,
                "sample_indices": list(range(start_index, start_index + EXAMPLES_PER_LESSON)),
            }

            for offset in range(EXAMPLES_PER_LESSON):
                sample_index = start_index + offset
                totals["examples"] += 1
                band_totals["examples"] += 1
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    label = independent_output(grid)
                except Exception as exc:
                    totals["generation_or_oracle_errors"] += 1
                    band_totals["generation_or_oracle_errors"] += 1
                    failures.append(
                        {
                            **lesson_meta,
                            "sample_index": sample_index,
                            "stage": "generation_or_independent_oracle",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue

                input_hash = hashlib.sha256(_json_bytes(grid)).hexdigest()
                output_hash = hashlib.sha256(_json_bytes(label)).hexdigest()
                unique_inputs.add(input_hash)
                unique_outputs.add(output_hash)
                dimensions[f"{len(grid)}x{len(grid[0])}"] += 1

                findings = list(gen.self_check(grid))
                if findings:
                    totals["self_check_errors"] += 1
                    band_totals["self_check_errors"] += 1
                    failures.append(
                        {
                            **lesson_meta,
                            "sample_index": sample_index,
                            "stage": "self_check",
                            "findings": findings,
                        }
                    )

                observed, observed_error = _safe_call(gen.observe_overrides, grid)
                if observed_error:
                    totals["observation_errors"] += 1
                    band_totals["observation_errors"] += 1
                    failures.append(
                        {
                            **lesson_meta,
                            "sample_index": sample_index,
                            "stage": "observe_overrides",
                            "error": observed_error,
                        }
                    )
                else:
                    texture = str(observed.get("texture"))
                    profile_counts[texture] += 1
                    band_profile_counts[texture] += 1
                    shape_counts[str(observed.get("n_shapes"))] += 1

                strict_findings = list(gen.strict_canonical_like(grid))
                strict_counts["accepted" if not strict_findings else "rejected"] += 1

                mirrored, mirror_error = _safe_call(gen.rule_mirror, grid)
                if mirror_error or mirrored != label:
                    totals["oracle_mismatches"] += 1
                    band_totals["oracle_mismatches"] += 1
                    failures.append(
                        {
                            **lesson_meta,
                            "sample_index": sample_index,
                            "stage": "rule_mirror",
                            "error": mirror_error,
                            "expected_sha256": output_hash,
                            "observed_sha256": None
                            if mirrored is None
                            else hashlib.sha256(_json_bytes(mirrored)).hexdigest(),
                        }
                    )

                for name, witness in witnesses.items():
                    value, error = _safe_call(witness, grid)
                    if error:
                        witness_errors[name] += 1
                    elif value:
                        witness_hits[name] += 1

                pairs.append({"input": grid, "output": label})

            if len(pairs) != EXAMPLES_PER_LESSON:
                totals["incomplete_lessons"] += 1
                band_totals["incomplete_lessons"] += 1
                continue

            demos, query = pairs[:-1], pairs[-1]
            try:
                reasons = list(gen.lesson_identifiable(demos, query))
            except Exception as exc:
                reasons = [f"lesson_identifiable raised {type(exc).__name__}: {exc}"]
            if reasons:
                totals["unidentifiable_lessons"] += 1
                band_totals["unidentifiable_lessons"] += 1
                failures.append({**lesson_meta, "stage": "lesson_identifiable", "findings": reasons})

            lesson_survivors: list[str] = []
            for name, competitor in competitors.items():
                survived = True
                had_error = False
                for pair in demos:
                    rival_output, error = _safe_call(competitor, pair["input"])
                    if error:
                        competitor_refutations[name]["errors"] += 1
                        had_error = True
                        survived = False
                        failures.append(
                            {
                                **lesson_meta,
                                "stage": "competitor",
                                "competitor": name,
                                "error": error,
                            }
                        )
                        break
                    if rival_output != pair["output"]:
                        survived = False
                        break
                if survived:
                    competitor_refutations[name]["surviving_lessons"] += 1
                    lesson_survivors.append(name)
                elif not had_error:
                    competitor_refutations[name]["refuted_lessons"] += 1
            if lesson_survivors:
                totals["surviving_competitor_lessons"] += 1
                band_totals["surviving_competitor_lessons"] += 1
                failures.append(
                    {
                        **lesson_meta,
                        "stage": "competitor_survival",
                        "competitors": lesson_survivors,
                    }
                )

            for name, shortcut in shortcuts.items():
                survived = True
                had_error = False
                for pair in demos:
                    shortcut_output, error = _safe_call(shortcut, pair["input"])
                    if error:
                        shortcut_refutations[name]["errors"] += 1
                        had_error = True
                        survived = False
                        break
                    if shortcut_output != pair["output"]:
                        survived = False
                        break
                key = "surviving_lessons" if survived else "refuted_lessons"
                if not had_error:
                    shortcut_refutations[name][key] += 1

        band_reports[band] = {
            **dict(sorted(band_totals.items())),
            "profile_counts": dict(sorted(band_profile_counts.items())),
        }

    for required in (
        "lessons",
        "examples",
        "generation_or_oracle_errors",
        "self_check_errors",
        "observation_errors",
        "oracle_mismatches",
        "incomplete_lessons",
        "unidentifiable_lessons",
        "surviving_competitor_lessons",
    ):
        totals.setdefault(required, 0)
    totals["unique_inputs"] = len(unique_inputs)
    totals["unique_outputs"] = len(unique_outputs)
    totals["canonical_pairs"] = len(canonical_pairs())
    totals["canonical_oracle_errors"] = len(canonical_errors)

    fatal_total_keys = (
        "generation_or_oracle_errors",
        "self_check_errors",
        "observation_errors",
        "oracle_mismatches",
        "incomplete_lessons",
        "unidentifiable_lessons",
        "surviving_competitor_lessons",
        "canonical_oracle_errors",
    )
    passed = not any(totals[key] for key in fatal_total_keys)
    passed = passed and not any(item["errors"] for item in competitor_refutations.values())
    passed = passed and not any(item["errors"] for item in shortcut_refutations.values())

    return {
        "schema_version": 1,
        "status": "PASS" if passed else "FAIL",
        "source": _source_metadata(gen),
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "examples_per_lesson": EXAMPLES_PER_LESSON,
            "demos_per_lesson": EXAMPLES_PER_LESSON - 1,
            "query_examples_per_lesson": 1,
            "seed_formula": "730000 + band_offset + lesson_index",
            "band_seed_offsets": _BAND_SEED_OFFSETS,
            "sample_index_formula": "lesson_index * 5 + example_offset",
            "sample_indices_are_consecutive": True,
            "labels": "independent_output in workspace/lesson_probe.py",
        },
        "totals": dict(sorted(totals.items())),
        "bands": band_reports,
        "profile_counts": dict(sorted(profile_counts.items())),
        "dimension_counts": dict(sorted(dimensions.items())),
        "shape_counts": dict(sorted(shape_counts.items())),
        "strict_counts": dict(sorted(strict_counts.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "witness_errors": dict(sorted(witness_errors.items())),
        "competitor_refutations": competitor_refutations,
        "shortcut_refutations": shortcut_refutations,
        "canonical_oracle_errors": canonical_errors,
        "failures": failures,
    }


def _load_generator(path: Path) -> Any:
    path = path.resolve()
    for candidate in (REPO_ROOT / "src", REPO_ROOT):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)
    spec = importlib.util.spec_from_file_location(f"lesson_probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=TASK_HOME / "generator.py",
        help="generator.py to audit (default: selected task generator)",
    )
    parser.add_argument("--lessons-per-band", type=int, default=DEFAULT_LESSONS_PER_BAND)
    parser.add_argument("--out", type=Path, required=True, help="stable JSON report path")
    args = parser.parse_args(argv)

    report = audit_lessons(_load_generator(args.generator), lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{report['status']} lessons={report['totals']['lessons']} "
        f"examples={report['totals']['examples']} "
        f"unique_inputs={report['totals']['unique_inputs']} "
        f"failures={len(report['failures'])} out={args.out}"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
