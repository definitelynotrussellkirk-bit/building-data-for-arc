#!/usr/bin/env python3
"""Exhaustive cyclic lesson/rank probe for ARC generator 406739865b43.

This is intentionally task-local.  It materializes five-pair lesson windows from
all three difficulty bands, checks production order and every query rotation
against the generator's *declared* competitors, and independently records the
selected component's order/size/marker-distance ranks.  It also verifies that
``CANONICAL_SHORTCUTS`` names exactly the rivals that fit every canonical pair.

Run from the packet root with the verified environment, for example::

    python3 run_with_racket.py python3 \
      generators/406739865b43/workspace/selection_rank_probe.py \
      --starts-per-band 100 --out ../checks/selection-rank-probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Sequence

TASK_ID = "406739865b43"
DEFAULT_BANDS = ("easy", "medium", "hard")
_CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _load_generator():
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        generator_path = Path(__file__).resolve().parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(
            f"task_{TASK_ID}_generator", generator_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load generator from {generator_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file():
            return parent
    raise FileNotFoundError("could not locate shared/data/canonical/puzzles.jsonl")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _decode_grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list):
        raise TypeError("canonical grid must be a list")
    if value and all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def _canonical_pairs(root: Path) -> list[dict[str, list[list[int]]]]:
    source = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    record = None
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                record = row
                break
    if record is None:
        raise KeyError(f"canonical task {TASK_ID} not found")
    raw_test = record.get("test", [])
    tests = raw_test if isinstance(raw_test, list) else [raw_test]
    raw_pairs = [*record.get("train", []), *tests]
    return [
        {
            "input": _decode_grid(pair["input"]),
            "output": _decode_grid(pair["output"]),
        }
        for pair in raw_pairs
    ]


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                cur_row, cur_col = current
                for drow, dcol in _CARDINAL:
                    nxt = (cur_row + drow, cur_col + dcol)
                    nr, nc = nxt
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and nxt not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "r1": min(rows),
                    "c1": min(cols),
                }
            )
    return sorted(components, key=lambda component: (component["r1"], component["c1"]))


def _rank_signature(grid: Sequence[Sequence[int]]) -> str:
    markers = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if len(markers) != 1:
        raise ValueError(f"expected one marker, found {len(markers)}")
    marker_col, marker_color = markers[0]
    components = _components(grid)
    targets = [component for component in components if component["color"] == marker_color]
    if len(targets) != 1:
        raise ValueError(f"expected one selected component, found {len(targets)}")
    target = targets[0]

    def rank(key: Callable[[dict[str, Any]], Any]) -> int:
        ordered = sorted(
            components,
            key=lambda component: (key(component), component["r1"], component["c1"]),
        )
        return ordered.index(target) + 1

    order_rank = components.index(target) + 1
    size_rank = rank(lambda component: component["size"])
    distance_rank = rank(
        lambda component: min(
            row + abs(col - marker_col) for row, col in component["cells"]
        )
    )
    return (
        f"{len(components)}-components/order-{order_rank}/"
        f"size-{size_rank}/distance-{distance_rank}"
    )


def _rival_fits(
    rival: Callable[[Any], list[list[int]]],
    pairs: Sequence[dict[str, Any]],
) -> tuple[bool, str | None]:
    try:
        return (
            all(rival(pair["input"]) == pair["output"] for pair in pairs),
            None,
        )
    except Exception as exc:  # probe evidence should retain unexpected rival errors
        return False, f"{type(exc).__name__}: {exc}"


def run_probe(
    *,
    starts_per_band: int = 100,
    seed_base: int = 52000,
    bands: Sequence[str] = DEFAULT_BANDS,
) -> dict[str, Any]:
    if type(starts_per_band) is not int or starts_per_band <= 0:
        raise ValueError("starts_per_band must be a positive integer")
    if type(seed_base) is not int:
        raise TypeError("seed_base must be an integer")
    if not bands:
        raise ValueError("at least one band is required")

    generator = _load_generator()
    generator_path = Path(generator.__file__).resolve()
    root = _find_repo_root()
    competitor_names = tuple(sorted(generator.LESSON_COMPETITORS))
    production_refutations = Counter({name: 0 for name in competitor_names})
    rotation_refutations = Counter({name: 0 for name in competitor_names})
    profile_counts: Counter[str] = Counter()
    rank_signatures: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    failures: list[dict[str, Any]] = []
    windows = pairs_count = rotations = 0
    generation_errors = self_check_failures = 0
    production_failures = rotation_failures = 0

    def remember_failure(failure: dict[str, Any]) -> None:
        if len(failures) < 200:
            failures.append(failure)

    for band_index, band in enumerate(bands):
        for start in range(starts_per_band):
            seed = seed_base + band_index * 100_000 + start
            lesson: list[dict[str, Any]] = []
            window_bad = False
            for offset in range(5):
                sample_index = start + offset
                try:
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    output = generator.rule_mirror(grid)
                except Exception as exc:
                    generation_errors += 1
                    window_bad = True
                    remember_failure(
                        {
                            "kind": "generation_error",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    break
                pairs_count += 1
                unique_inputs.add(json.dumps(grid, separators=(",", ":")))
                errors = list(generator.self_check(grid))
                if errors:
                    self_check_failures += 1
                    window_bad = True
                    remember_failure(
                        {
                            "kind": "self_check_failure",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                try:
                    profile = generator.observe_overrides(grid)["selection_profile"]
                    signature = _rank_signature(grid)
                    profile_counts[profile] += 1
                    rank_signatures[signature] += 1
                except Exception as exc:
                    window_bad = True
                    remember_failure(
                        {
                            "kind": "rank_observation_error",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                lesson.append({"input": grid, "output": output})

            if len(lesson) != 5:
                production_failures += 1
                continue
            windows += 1
            demos, query = lesson[:4], lesson[4]
            reasons = list(generator.lesson_identifiable(demos, query))
            fitting: list[str] = []
            competitor_errors: dict[str, str] = {}
            for name, rival in generator.LESSON_COMPETITORS.items():
                fits, error = _rival_fits(rival, demos)
                if fits:
                    fitting.append(name)
                else:
                    production_refutations[name] += 1
                if error is not None:
                    competitor_errors[name] = error
            if window_bad or reasons or fitting or competitor_errors:
                production_failures += 1
                remember_failure(
                    {
                        "kind": "production_window_failure",
                        "band": band,
                        "start": start,
                        "seed": seed,
                        "reasons": reasons,
                        "fitting_competitors": fitting,
                        "competitor_errors": competitor_errors,
                    }
                )

            for query_index, rotated_query in enumerate(lesson):
                rotations += 1
                rotated_demos = [
                    pair for index, pair in enumerate(lesson) if index != query_index
                ]
                reasons = list(generator.lesson_identifiable(rotated_demos, rotated_query))
                fitting = []
                competitor_errors = {}
                for name, rival in generator.LESSON_COMPETITORS.items():
                    fits, error = _rival_fits(rival, rotated_demos)
                    if fits:
                        fitting.append(name)
                    else:
                        rotation_refutations[name] += 1
                    if error is not None:
                        competitor_errors[name] = error
                if reasons or fitting or competitor_errors:
                    rotation_failures += 1
                    remember_failure(
                        {
                            "kind": "rotation_failure",
                            "band": band,
                            "start": start,
                            "seed": seed,
                            "query_index": query_index,
                            "reasons": reasons,
                            "fitting_competitors": fitting,
                            "competitor_errors": competitor_errors,
                        }
                    )

    canonical_pairs = _canonical_pairs(root)
    canonical_fit: dict[str, bool] = {}
    canonical_errors: dict[str, str] = {}
    for name, rival in generator.SEMANTIC_RIVALS.items():
        fits, error = _rival_fits(rival, canonical_pairs)
        canonical_fit[name] = fits
        if error is not None:
            canonical_errors[name] = error
    fits_all = sorted(name for name, fits in canonical_fit.items() if fits)
    declared = sorted(generator.CANONICAL_SHORTCUTS)
    declared_exact = declared == fits_all and not canonical_errors
    if not declared_exact:
        remember_failure(
            {
                "kind": "canonical_shortcut_declaration_mismatch",
                "declared": declared,
                "fits_all": fits_all,
                "errors": canonical_errors,
            }
        )

    counts = {
        "windows": windows,
        "pairs": pairs_count,
        "rotations": rotations,
        "unique_inputs": len(unique_inputs),
        "generation_errors": generation_errors,
        "self_check_failures": self_check_failures,
        "production_failures": production_failures,
        "rotation_failures": rotation_failures,
    }
    expected_windows = len(bands) * starts_per_band
    expected_pairs = expected_windows * 5
    clean = (
        windows == expected_windows
        and pairs_count == expected_pairs
        and rotations == expected_pairs
        and generation_errors == 0
        and self_check_failures == 0
        and production_failures == 0
        and rotation_failures == 0
        and declared_exact
        and not failures
    )
    return {
        "schema": "selection-rank-probe/1",
        "task_id": TASK_ID,
        "status": "pass" if clean else "fail",
        "generator_sha256": _sha256(generator_path),
        "rule_hash": generator.RULE_HASH,
        "sampler": {
            "bands": list(bands),
            "starts_per_band": starts_per_band,
            "seed_base": seed_base,
            "lesson_width": 5,
            "demonstrations": 4,
            "production_query_index": 4,
            "rotation_policy": "all five held out once",
            "sample_index_policy": "cyclic starts start..start+4",
        },
        "counts": counts,
        "selection_profiles": dict(sorted(profile_counts.items())),
        "rank_signatures": dict(sorted(rank_signatures.items())),
        "competitors": {
            "names": list(competitor_names),
            "production_refutations": dict(sorted(production_refutations.items())),
            "rotation_refutations": dict(sorted(rotation_refutations.items())),
        },
        "canonical_shortcuts": {
            "canonical_pairs": len(canonical_pairs),
            "fits_all": fits_all,
            "declared": declared,
            "declared_exact": declared_exact,
            "rival_errors": canonical_errors,
        },
        "failures": failures,
        "limitations": [
            "Finite declared-rival checks do not prove unique induction against undeclared hypotheses.",
            "The probe uses the Python rule mirror; the battery rule_smoke stage separately binds it to Racket authority.",
            "Seeds and cyclic starts are explicit but do not enumerate the generator's infinite seed space.",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=52000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run_probe(
        starts_per_band=args.starts_per_band,
        seed_base=args.seed_base,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
