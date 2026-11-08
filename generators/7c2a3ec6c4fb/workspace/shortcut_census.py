#!/usr/bin/env python3
"""Deterministic shortcut and morphology census for generator 7c2a3ec6c4fb.

This is a review aid, not part of generation.  It evaluates a small library of
low-complexity component signatures on the canonical pairs and on generated
samples, then checks morphology/layout coverage that generic marginal gates can
miss.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable


TASK_ID = "7c2a3ec6c4fb"
HERE = Path(__file__).resolve()
GENERATOR_PATH = HERE.parents[1] / "generator.py"
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


Component = dict[str, Any]
Signature = Callable[[Component], Any]


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"shortcut_census_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bbox_dimensions(component: Component) -> tuple[int, int]:
    crop = component["crop"]
    return len(crop), len(crop[0])


SIGNATURES: dict[str, Signature] = {
    "unique_cell_count": lambda component: component["cell_count"],
    "unique_bbox_dimensions": _bbox_dimensions,
    "unique_color_signature": lambda component: component["colors"],
    "unique_color_histogram": lambda component: component["color_histogram"],
    "unique_geometry_signature": lambda component: component["geometry"],
    "unique_geometry_and_colors": lambda component: (
        component["geometry"],
        component["colors"],
    ),
    "unique_bbox_and_histogram": lambda component: (
        _bbox_dimensions(component),
        component["color_histogram"],
    ),
}


def _freeze(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _canonical_pairs() -> list[dict[str, Any]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs: list[dict[str, Any]] = []
            for split in ("train", "test"):
                values = row.get(split, [])
                if isinstance(values, dict):
                    values = [values]
                pairs.extend(values)
            return pairs
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _signature_prediction(
    generator,
    grid: list[list[int]],
    signature: Signature,
) -> list[list[int]]:
    facts = generator.semantic_observables(grid)
    components = facts.get("components") or []
    if not components:
        return []
    values = [signature(component) for component in components]
    counts = Counter(values)
    unique = [
        component
        for component, value in zip(components, values)
        if counts[value] == 1
    ]
    selected = unique[0] if len(unique) == 1 else components[0]
    return [list(row) for row in selected["crop"]]


def _old_lattice_origins(
    size: int,
    height: int,
    width: int,
) -> set[tuple[int, int]]:
    starts = (0, (size - 3) // 2, size - 3)
    return {
        (zone_row + row_jitter, zone_col + col_jitter)
        for zone_row in starts
        for zone_col in starts
        for row_jitter in range(max(0, 4 - height))
        for col_jitter in range(max(0, 4 - width))
    }


def run_census(
    *,
    samples: int = 1000,
    seed: str = "shortcut-census",
    layout_samples: int = 300,
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable review report."""
    if samples <= 0 or layout_samples <= 0:
        raise ValueError("samples and layout_samples must be positive")

    generator = _load_generator()
    pairs = _canonical_pairs()
    # Signature comparisons alone cannot detect a wrong segmentation rule.
    predictors = {
        name: (lambda grid, signature=signature:
               _signature_prediction(generator, grid, signature))
        for name, signature in SIGNATURES.items()
    }
    predictors.update(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    canonical_hits = Counter()
    for pair in pairs:
        expected = _freeze(pair["output"])
        for name, predict in predictors.items():
            prediction = predict(pair["input"])
            canonical_hits[name] += int(_freeze(prediction) == expected)

    strict_failures: list[dict[str, Any]] = []
    strict_failure_count = 0
    generated_hits = Counter()
    answer_color_counts = Counter()
    answer_dimensions = Counter()
    scene_profiles = Counter()
    n_pairs_counts = Counter()
    pattern_profiles = Counter()
    witness_hits = Counter()
    edge_answers = 0

    difficulties = ("easy", "medium", "hard")
    for index in range(samples):
        difficulty = difficulties[index % len(difficulties)]
        grid = generator.generate(
            f"{seed}:main",
            index,
            difficulty=difficulty,
        )
        facts = generator.semantic_observables(grid)
        if facts["errors"]:
            strict_failure_count += 1
            if len(strict_failures) < 20:
                strict_failures.append(
                    {"index": index, "errors": list(facts["errors"])}
                )
            continue

        singleton = facts["singleton"]
        answer_color_counts[str(len(singleton["colors"]))] += 1
        height, width = _bbox_dimensions(singleton)
        answer_dimensions[f"{height}x{width}"] += 1
        scene_profiles[str(facts["scene_profile"])] += 1
        n_pairs_counts[str(facts["repeated_pattern_classes"])] += 1
        pattern_profiles[str(facts["pattern_profile"])] += 1
        row0, col0, row1, col1 = singleton["bbox"]
        edge_answers += int(
            row0 == 0
            or col0 == 0
            or row1 == len(grid) - 1
            or col1 == len(grid[0]) - 1
        )

        expected = _freeze(generator.rule_mirror(grid))
        for name, predict in predictors.items():
            prediction = predict(grid)
            generated_hits[name] += int(_freeze(prediction) == expected)
        for name, witness in generator.SEMANTIC_WITNESSES.items():
            witness_hits[name] += int(witness(grid))

    layout_eligible = 0
    layout_escaped = 0
    for index in range(layout_samples):
        grid = generator.generate(
            f"{seed}:layout",
            index,
            n_pairs=2,
        )
        singleton = generator.semantic_observables(grid)["singleton"]
        height, width = _bbox_dimensions(singleton)
        if height > 3 or width > 3:
            continue
        layout_eligible += 1
        if singleton["bbox"][:2] not in _old_lattice_origins(
            len(grid),
            height,
            width,
        ):
            layout_escaped += 1

    pair_count = len(pairs)
    canonical_perfect = sorted(
        name for name in predictors if canonical_hits[name] == pair_count
    )
    declared = sorted(generator.CANONICAL_SHORTCUTS)
    signature_results = {
        name: {
            "canonical_hits": canonical_hits[name],
            "canonical_rate": canonical_hits[name] / pair_count,
            "generated_hits": generated_hits[name],
            "generated_rate": generated_hits[name] / samples,
            "valid_generated_rate": (generated_hits[name] / (samples - strict_failure_count)
                                     if samples > strict_failure_count else None),
        }
        for name in sorted(predictors)
    }
    return {
        "schema": "arcpuzzles-task-shortcut-census-v1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "seed": seed,
        "main_seed": f"{seed}:main",
        "main_sample_index_range": [0, samples - 1],
        "layout_seed": f"{seed}:layout",
        "layout_sample_index_range": [0, layout_samples - 1],
        "valid_samples": samples - strict_failure_count,
        "samples": samples,
        "layout_samples": layout_samples,
        "canonical_pair_count": pair_count,
        "signature_results": signature_results,
        "canonical_perfect_signatures": canonical_perfect,
        "declared_canonical_shortcuts": declared,
        "canonical_perfect_undeclared": sorted(
            set(canonical_perfect) - set(declared)
        ),
        "strict_failure_count": strict_failure_count,
        "strict_failures": strict_failures,
        "answer_color_counts": dict(sorted(answer_color_counts.items())),
        "answer_dimensions": dict(sorted(answer_dimensions.items())),
        "answer_edge_fraction": edge_answers / samples,
        "scene_profiles": dict(sorted(scene_profiles.items())),
        "n_pairs_counts": dict(sorted(n_pairs_counts.items())),
        "pattern_profiles": dict(sorted(pattern_profiles.items())),
        "witness_hits": dict(sorted(witness_hits.items())),
        "layout_escape": {
            "eligible": layout_eligible,
            "escaped": layout_escaped,
            "fraction": (
                layout_escaped / layout_eligible if layout_eligible else 0.0
            ),
        },
    }


def evaluate_guardrails(report: dict[str, Any]) -> list[str]:
    """Return human-readable regressions found in a census report."""
    failures: list[str] = []
    if report.get("strict_failure_count"):
        failures.append("generated samples failed strict/self checks")
    if report.get("canonical_pair_count", 0) <= 0:
        failures.append("no canonical pairs were loaded")
    undeclared = report.get("canonical_perfect_undeclared") or []
    if undeclared:
        failures.append(
            "canonical-perfect signatures are undeclared: "
            + ", ".join(undeclared)
        )
    if not {"1", "2"} <= set(report.get("answer_color_counts") or {}):
        failures.append("answer pool does not cover both monochrome and multicolor")

    dimensions = report.get("answer_dimensions") or {}
    long_crop = any(
        max(int(value) for value in str(key).split("x")) >= 4
        for key in dimensions
    )
    if not long_crop:
        failures.append("answer pool has no crop dimension of length four or five")

    layout = report.get("layout_escape") or {}
    eligible = int(layout.get("eligible", 0))
    escaped = int(layout.get("escaped", 0))
    if eligible <= 0:
        failures.append("layout census had no compact eligible answers")
    elif escaped / eligible < 0.25:
        failures.append("fewer than 25% of compact sparse answers escape the old lattice")

    samples = int(report.get("samples", 0))
    minimum_axis_support = max(1, samples // 20)
    expected_controls = {
        "scene_profiles": {
            "square11_c3",
            "square12_c4",
            "square13_c3",
            "square13_c4",
        },
        "n_pairs_counts": {"2", "3", "4"},
        "pattern_profiles": {
            "color_swap",
            "shape_shift",
            "mixed_signature",
        },
    }
    for field, expected in expected_controls.items():
        counts = report.get(field) or {}
        missing = sorted(expected - set(counts))
        if missing:
            failures.append(
                f"{field} is missing observable values: " + ", ".join(missing)
            )
        weak = sorted(
            name
            for name in expected & set(counts)
            if int(counts[name]) < minimum_axis_support
        )
        if weak:
            failures.append(
                f"{field} has weak support below {minimum_axis_support}: "
                + ", ".join(weak)
            )

    witness_hits = report.get("witness_hits") or {}
    minimum_witness_support = max(1, samples // 4)
    for name, value in sorted(witness_hits.items()):
        if int(value) < minimum_witness_support:
            failures.append(
                f"semantic witness {name} has weak support "
                f"({value}/{samples}; need at least {minimum_witness_support})"
            )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--layout-samples", type=int, default=300)
    parser.add_argument("--seed", default="shortcut-census")
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit nonzero when the task-local guardrails fail",
    )
    args = parser.parse_args(argv)

    report = run_census(
        samples=args.samples,
        seed=args.seed,
        layout_samples=args.layout_samples,
    )
    report["guardrail_failures"] = evaluate_guardrails(report)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return int(args.check and bool(report["guardrail_failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
