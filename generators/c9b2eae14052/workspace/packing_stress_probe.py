"""Stress the seed-keyed polyomino packer across the full public axis box.

This is a task-local replay tool for future reviewers.  It draws deterministic
random override combinations, exercises ``generate`` (not just a private
helper), validates every scene, and reports semantic-side/corner coverage plus
color-independent component-shape diversity.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME = REPO_ROOT / "shared" / "runtime"
sys.path.insert(0, str(RUNTIME))


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("packing_stress_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalized_shape(cells: Any) -> tuple[tuple[int, int], ...]:
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_multiset(records: list[dict[str, Any]]) -> tuple[Any, ...]:
    return tuple(
        sorted(
            (
                record["border_count"],
                tuple(sorted(record["sides"])),
                _normalized_shape(record["cells"]),
            )
            for record in records
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=2_400)
    parser.add_argument("--probe-seed", type=int, default=20_261_002)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.draws <= 0:
        parser.error("--draws must be positive")

    generator_path = TASK_ROOT / "generator.py"
    source = generator_path.read_bytes()
    gen = _load_generator(generator_path)
    rng = random.Random(args.probe_seed)

    failures: list[dict[str, Any]] = []
    side_counts: Counter[str] = Counter()
    corner_counts: Counter[str] = Counter()
    shape_multisets: set[tuple[Any, ...]] = set()
    bands: Counter[str] = Counter()
    axis_values = {"grid_h": Counter(), "grid_w": Counter(), "n_objects": Counter()}

    corners = {
        frozenset(("top", "left")): "northwest",
        frozenset(("top", "right")): "northeast",
        frozenset(("bottom", "right")): "southeast",
        frozenset(("bottom", "left")): "southwest",
    }

    for draw_index in range(args.draws):
        difficulty = ("easy", "medium", "hard")[draw_index % 3]
        sample_index = rng.randrange(12)
        seed = rng.randrange(2**31)
        overrides = {
            "grid_h": rng.randint(8, 14),
            "grid_w": rng.randint(7, 14),
            "n_objects": rng.randint(3, 6),
        }
        bands[difficulty] += 1
        for name, value in overrides.items():
            axis_values[name][str(value)] += 1
        try:
            grid = gen.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                **overrides,
            )
            findings = gen.self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
            if findings:
                raise AssertionError("; ".join(findings))
            observed = gen.observe_overrides(grid)
            if observed != overrides:
                raise AssertionError(f"override mismatch: expected={overrides} observed={observed}")
            info = gen._analysis(grid)
            shape_multisets.add(_shape_multiset(info["records"]))
            for record in info["records"]:
                sides = record["sides"]
                if len(sides) == 1:
                    side_counts[next(iter(sides))] += 1
                if sides in corners:
                    corner_counts[corners[sides]] += 1
        except Exception as exc:  # evidence must retain exact failing draw
            failures.append(
                {
                    "draw_index": draw_index,
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": sample_index,
                    "overrides": overrides,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )

    missing_sides = sorted(set(gen.TARGET_SIDES) - set(side_counts))
    missing_corners = sorted(set(corners.values()) - set(corner_counts))
    report = {
        "schema": "c9b2eae14052-packing-stress-v1",
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "generator_version": getattr(gen, "VERSION", None),
        "probe_seed": args.probe_seed,
        "draws": args.draws,
        "successful": args.draws - len(failures),
        "failures": failures,
        "bands": dict(sorted(bands.items())),
        "axis_value_counts": {
            name: dict(sorted(counts.items(), key=lambda pair: int(pair[0])))
            for name, counts in axis_values.items()
        },
        "one_border_side_counts": dict(sorted(side_counts.items())),
        "corner_counts": dict(sorted(corner_counts.items())),
        "unique_component_shape_multisets": len(shape_multisets),
        "missing_one_border_sides": missing_sides,
        "missing_corners": missing_corners,
        "passed": not failures and not missing_sides and not missing_corners,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
