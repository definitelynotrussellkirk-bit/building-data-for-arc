#!/usr/bin/env python3
"""Source-bound curriculum audit for ARC generator ``a3086dea6cff``.

The repository battery verifies the selected implementation.  This independent,
task-local probe makes the before/after teaching difference easy to reproduce:

* every emitted scene is structurally valid and contains both orientations;
* every three-demo sliding window contains a canonical-scale anchor, an
  interior crossing, a non-aligned pair, and a three-occurrence color;
* the two strongest rules that fit every canonical pair are each falsified by a
  generated input; and
* horizontal-only, vertical-only, and fixed crossing-precedence competitors do
  not survive a generated lesson.

It does not import the generator's mirror or semantic declarations.  The rule,
features, rivals, and canonical-profile census below are independent review
code.  Run it from anywhere::

    python3 workspace/audit_curriculum.py --seeds 20 --starts 9 \
        --json-out report.json

Use ``--generator workspace/generator-before.py --allow-findings`` to reproduce
the frozen baseline's shortcut windows without making the command fail.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any, Callable

TASK_ID = "a3086dea6cff"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
WINDOW = 3
for path in (REPO_ROOT / "shared" / "runtime", REPO_ROOT / "src", REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

Grid = list[list[int]]
Rule = Callable[[Grid], Grid]


def _copy_grid(grid: Any) -> Grid:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if isinstance(grid[0], str):
        copied = [[int(value) for value in row] for row in grid]
    else:
        copied = [list(row) for row in grid]
    width = len(copied[0])
    if width == 0 or any(len(row) != width for row in copied):
        raise ValueError("grid must be rectangular and nonempty")
    if any(type(value) is not int or not 0 <= value <= 9 for row in copied for value in row):
        raise ValueError("grid values must be integer ARC colors 0..9")
    return copied


def _positions(grid: Any) -> tuple[list[int], dict[int, list[tuple[int, int]]]]:
    copied = _copy_grid(grid)
    order: list[int] = []
    result: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(copied):
        for col, value in enumerate(values):
            if value == 0:
                continue
            if value not in result:
                order.append(value)
                result[value] = []
            result[value].append((row, col))
    return order, result


def _paint_segment(output: Grid, color: int, cells: list[tuple[int, int]]) -> None:
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        for col in range(min(c1, c2), max(c1, c2) + 1):
            output[r1][col] = color
    elif c1 == c2:
        for row in range(min(r1, r2), max(r1, r2) + 1):
            output[row][c1] = color


def intended_rule(grid: Any) -> Grid:
    """Independent mirror: connect exactly-two colors only when axis aligned."""
    copied = _copy_grid(grid)
    order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for color in order:
        cells = positions[color]
        if len(cells) == 2:
            _paint_segment(output, color, cells)
    return output


def rival_connect_non_aligned_with_l(grid: Any) -> Grid:
    copied = _copy_grid(grid)
    order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for color in order:
        cells = positions[color]
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2 or c1 == c2:
            _paint_segment(output, color, cells)
            continue
        for col in range(min(c1, c2), max(c1, c2) + 1):
            output[r1][col] = color
        for row in range(min(r1, r2), max(r1, r2) + 1):
            output[row][c2] = color
    return output


def rival_connect_aligned_any_count(grid: Any) -> Grid:
    copied = _copy_grid(grid)
    order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for color in order:
        cells = positions[color]
        if len(cells) < 2:
            continue
        rows = {row for row, _col in cells}
        cols = {col for _row, col in cells}
        if len(rows) == 1:
            row = next(iter(rows))
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = color
        elif len(cols) == 1:
            col = next(iter(cols))
            for row in range(min(rows), max(rows) + 1):
                output[row][col] = color
    return output


def rival_horizontal_only(grid: Any) -> Grid:
    copied = _copy_grid(grid)
    order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for color in order:
        cells = positions[color]
        if len(cells) == 2 and cells[0][0] == cells[1][0]:
            _paint_segment(output, color, cells)
    return output


def rival_vertical_only(grid: Any) -> Grid:
    copied = _copy_grid(grid)
    order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for color in order:
        cells = positions[color]
        if len(cells) == 2 and cells[0][1] == cells[1][1]:
            _paint_segment(output, color, cells)
    return output


def rival_vertical_wins_crossings(grid: Any) -> Grid:
    copied = _copy_grid(grid)
    _order, positions = _positions(copied)
    output = copy.deepcopy(copied)
    for orientation in ("horizontal", "vertical"):
        for color, cells in positions.items():
            if len(cells) != 2:
                continue
            aligned = (
                orientation == "horizontal" and cells[0][0] == cells[1][0]
            ) or (
                orientation == "vertical" and cells[0][1] == cells[1][1]
            )
            if aligned:
                _paint_segment(output, color, cells)
    return output


CANONICAL_SHORTCUTS: dict[str, Rule] = {
    "connect_non_aligned_with_l": rival_connect_non_aligned_with_l,
    "connect_aligned_any_count": rival_connect_aligned_any_count,
}
COMPETITORS: dict[str, Rule] = {
    **CANONICAL_SHORTCUTS,
    "horizontal_only": rival_horizontal_only,
    "vertical_only": rival_vertical_only,
    "vertical_wins_crossings": rival_vertical_wins_crossings,
}


def _segment(cells: list[tuple[int, int]]) -> set[tuple[int, int]]:
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        return {(r1, col) for col in range(min(c1, c2), max(c1, c2) + 1)}
    if c1 == c2:
        return {(row, c1) for row in range(min(r1, r2), max(r1, r2) + 1)}
    return set()


def analyze(grid: Any) -> dict[str, Any]:
    copied = _copy_grid(grid)
    _order, positions = _positions(copied)
    horizontal: list[tuple[int, list[tuple[int, int]]]] = []
    vertical: list[tuple[int, list[tuple[int, int]]]] = []
    nonaligned: list[tuple[int, list[tuple[int, int]]]] = []
    triples: list[tuple[int, list[tuple[int, int]]]] = []
    other_counts: dict[int, int] = {}
    for color, cells in positions.items():
        if len(cells) == 2:
            if cells[0][0] == cells[1][0]:
                horizontal.append((color, cells))
            elif cells[0][1] == cells[1][1]:
                vertical.append((color, cells))
            else:
                nonaligned.append((color, cells))
        elif len(cells) == 3:
            triples.append((color, cells))
        else:
            other_counts[color] = len(cells)

    crossing = False
    for _hcolor, hcells in horizontal:
        for _vcolor, vcells in vertical:
            intersection = _segment(hcells) & _segment(vcells)
            if intersection - set(hcells) - set(vcells):
                crossing = True
                break
        if crossing:
            break

    return {
        "height": len(copied),
        "width": len(copied[0]),
        "palette_size": len({value for row in copied for value in row}),
        "horizontal_pairs": len(horizontal),
        "vertical_pairs": len(vertical),
        "nonaligned_pairs": len(nonaligned),
        "triple_colors": len(triples),
        "other_counts": other_counts,
        "crossing": crossing,
    }


def _load_generator(path: Path):
    path = path.resolve()
    suffix = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(f"curriculum_probe_{suffix}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Grid]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row.get("test", [])
            if isinstance(test, dict):
                test = [test]
            return [
                {"input": _copy_grid(pair["input"]), "output": _copy_grid(pair["output"])}
                for pair in [*row.get("train", []), *test]
            ]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _counterexample(
    *,
    name: str,
    rival: Rule,
    generated: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for item in generated:
        intended = intended_rule(item["input"])
        rival_output = rival(item["input"])
        if rival_output != intended:
            return {
                "band": item["band"],
                "seed": item["seed"],
                "sample_index": item["sample_index"],
                "input": item["input"],
                "intended_output": intended,
                "rival_output": rival_output,
                "rival": name,
            }
    return None


def run_probe(*, generator_path: Path, seeds: int, starts: int) -> dict[str, Any]:
    if seeds < 1 or starts < 1:
        raise ValueError("seeds and starts must be positive")
    gen = _load_generator(generator_path)
    canonical_pairs = _canonical_pairs()
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in canonical_pairs
    }

    failures: list[str] = []
    canonical_rule_matches = sum(
        intended_rule(pair["input"]) == pair["output"] for pair in canonical_pairs
    )
    if canonical_rule_matches != len(canonical_pairs):
        failures.append(
            f"independent intended rule matched {canonical_rule_matches}/{len(canonical_pairs)} canonical pairs"
        )

    generated_by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    generation_errors: list[dict[str, Any]] = []
    self_check_errors: list[dict[str, Any]] = []
    maximum_sample = starts + WINDOW - 2
    for band in BANDS:
        for seed in range(seeds):
            for sample_index in range(maximum_sample + 1):
                key = (band, seed, sample_index)
                try:
                    grid = _copy_grid(gen.generate(seed, sample_index, difficulty=band))
                except Exception as exc:  # report exact reproducible call
                    generation_errors.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                if callable(getattr(gen, "self_check", None)):
                    reasons = gen.self_check(copy.deepcopy(grid))
                    if reasons:
                        self_check_errors.append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "reasons": list(reasons),
                            }
                        )
                generated_by_key[key] = {
                    "band": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "input": grid,
                    "features": analyze(grid),
                }

    if generation_errors:
        failures.append(f"{len(generation_errors)} generation calls failed")
    if self_check_errors:
        failures.append(f"{len(self_check_errors)} generated grids failed self_check")

    generated = list(generated_by_key.values())
    scenes_without_both = [
        item
        for item in generated
        if not (
            item["features"]["horizontal_pairs"]
            and item["features"]["vertical_pairs"]
        )
    ]
    if scenes_without_both:
        failures.append(
            f"{len(scenes_without_both)}/{len(generated)} scenes omit one connector orientation"
        )

    profile_counts = Counter(
        (
            item["features"]["height"],
            item["features"]["width"],
            item["features"]["palette_size"],
        )
        for item in generated
    )
    canonical_profile_scenes = sum(profile_counts[profile] for profile in canonical_profiles)

    window_reports: list[dict[str, Any]] = []
    incomplete_windows: list[dict[str, Any]] = []
    survivor_counts: Counter[str] = Counter()
    for band in BANDS:
        for seed in range(seeds):
            for start in range(starts):
                items = [
                    generated_by_key.get((band, seed, sample_index))
                    for sample_index in range(start, start + WINDOW)
                ]
                if any(item is None for item in items):
                    report = {
                        "band": band,
                        "seed": seed,
                        "start": start,
                        "complete": False,
                        "missing_generated_scene": True,
                    }
                    window_reports.append(report)
                    incomplete_windows.append(report)
                    continue
                concrete = [item for item in items if item is not None]
                features = [item["features"] for item in concrete]
                profiles = {
                    (feature["height"], feature["width"], feature["palette_size"])
                    for feature in features
                }
                outputs = [intended_rule(item["input"]) for item in concrete]
                survivors = [
                    name
                    for name, competitor in COMPETITORS.items()
                    if all(
                        competitor(item["input"]) == output
                        for item, output in zip(concrete, outputs)
                    )
                ]
                for name in survivors:
                    survivor_counts[name] += 1
                checks = {
                    "every_scene_both_orientations": all(
                        feature["horizontal_pairs"] and feature["vertical_pairs"]
                        for feature in features
                    ),
                    "has_nonaligned_pair": any(feature["nonaligned_pairs"] for feature in features),
                    "has_three_occurrence_color": any(feature["triple_colors"] for feature in features),
                    "has_interior_crossing": any(feature["crossing"] for feature in features),
                    "has_canonical_profile_anchor": bool(profiles & canonical_profiles),
                    "refutes_all_competitors": not survivors,
                }
                report = {
                    "band": band,
                    "seed": seed,
                    "start": start,
                    "complete": all(checks.values()),
                    "checks": checks,
                    "surviving_competitors": survivors,
                }
                window_reports.append(report)
                if not report["complete"]:
                    incomplete_windows.append(report)

    if incomplete_windows:
        failures.append(
            f"{len(incomplete_windows)}/{len(window_reports)} three-demo windows are incomplete"
        )

    shortcut_report: dict[str, Any] = {}
    for name, rival in CANONICAL_SHORTCUTS.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs)
        counterexample = _counterexample(name=name, rival=rival, generated=generated)
        shortcut_report[name] = {
            "fits_all_canonical": fits,
            "generated_counterexample": counterexample,
        }
        if not fits:
            failures.append(f"declared shortcut {name!r} does not fit every canonical pair")
        if counterexample is None:
            failures.append(f"no generated counterexample found for canonical-fitting shortcut {name!r}")

    summary = {
        "canonical_pairs": len(canonical_pairs),
        "canonical_rule_matches": canonical_rule_matches,
        "generated_scenes": len(generated),
        "generation_errors": len(generation_errors),
        "self_check_errors": len(self_check_errors),
        "scenes_without_both_orientations": len(scenes_without_both),
        "canonical_profile_scenes": canonical_profile_scenes,
        "windows": len(window_reports),
        "incomplete_windows": len(incomplete_windows),
        "surviving_competitor_windows": dict(sorted(survivor_counts.items())),
    }
    return {
        "schema": "a3086dea6cff-curriculum-audit-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.resolve()),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "parameters": {"bands": list(BANDS), "seeds": seeds, "starts": starts, "window": WINDOW},
        "summary": summary,
        "canonical_profiles": [list(profile) for profile in sorted(canonical_profiles)],
        "profile_counts": {
            "x".join(map(str, profile)): count for profile, count in sorted(profile_counts.items())
        },
        "canonical_shortcuts": shortcut_report,
        "first_scenes_without_both_orientations": [
            {key: item[key] for key in ("band", "seed", "sample_index", "input")}
            for item in scenes_without_both[:3]
        ],
        "first_incomplete_windows": incomplete_windows[:5],
        "generation_error_examples": generation_errors[:5],
        "self_check_error_examples": self_check_errors[:5],
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator",
        type=Path,
        default=TASK_HOME / "generator.py",
        help="Generator source to inspect (default: selected generator.py).",
    )
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--starts", type=int, default=9)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--allow-findings",
        action="store_true",
        help="Report findings but return exit 0 (useful for frozen baselines).",
    )
    args = parser.parse_args(argv)
    report = run_probe(generator_path=args.generator, seeds=args.seeds, starts=args.starts)
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(raw)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if report["failures"]:
        for failure in report["failures"]:
            print(f"FAIL: {failure}")
        return 0 if args.allow_findings else 1
    print("PASS: every sampled scene/window satisfies the curriculum contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
