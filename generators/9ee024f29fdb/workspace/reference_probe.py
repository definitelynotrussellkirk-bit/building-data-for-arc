"""Independent probes for generator 9ee024f29fdb.

The Python oracle and observations below re-express the visible grid semantics
without importing production helpers.  They supplement, but never replace, the
canonical Racket authority exercised by the repository battery.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "9ee024f29fdb"
CANONICAL_SHAPES = {(9, 13), (5, 13), (9, 9), (13, 13)}
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def authority_output(grid):
    """Independent direct cell rule: clear lattice and cyan, paint the rest red."""
    return [
        [
            0 if r % 4 == 0 or c % 4 == 0 or value == 8 else 2
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def interior_cells(grid):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, _ in enumerate(row)
        if r % 4 != 0 and c % 4 != 0
    ]


def lattice_cells(grid):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, _ in enumerate(row)
        if r % 4 == 0 or c % 4 == 0
    ]


def interior_eight_count(grid):
    return sum(grid[r][c] == 8 for r, c in interior_cells(grid))


def observed_exact_axes(grid):
    decoys = {
        grid[r][c]
        for r, c in interior_cells(grid)
        if grid[r][c] not in (0, 8)
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "decoy_palette_size": len(decoys),
        "lattice_noise": any(grid[r][c] != 0 for r, c in lattice_cells(grid)),
    }


def is_strict_canonical_profile(grid):
    return (
        (len(grid), len(grid[0])) in CANONICAL_SHAPES
        and {value for row in grid for value in row} == {0, 8}
        and all(grid[r][c] == 0 for r, c in lattice_cells(grid))
        and interior_eight_count(grid) > 0
        and interior_eight_count(grid) < len(interior_cells(grid))
    )


def distribution_summary(module, count=96):
    by_band = {}
    for band in (None, "easy", "medium", "hard"):
        rows = []
        for index in range(count):
            grid = module.generate(1103 + index, 17 * index + 3, difficulty=band)
            rows.append(
                {
                    "grid": grid,
                    "observed": observed_exact_axes(grid),
                    "strict": is_strict_canonical_profile(grid),
                    "profile": module.schedule_profile(1103 + index, 17 * index + 3, band),
                }
            )
        by_band[str(band)] = {
            "samples": count,
            "strict": sum(row["strict"] for row in rows),
            "profiles": Counter(row["profile"] for row in rows),
            "shapes": Counter(
                (row["observed"]["grid_h"], row["observed"]["grid_w"])
                for row in rows
            ),
            "decoy_counts": Counter(row["observed"]["decoy_palette_size"] for row in rows),
            "lattice_noise": Counter(row["observed"]["lattice_noise"] for row in rows),
        }
    return by_band



def _lesson_pair(grid):
    return {"input": grid, "output": authority_output(grid)}


def cyclic_lesson_summary(module, *, starts_per_band=100, seed_base=808):
    """Rotate every pair of a materialized lesson into the query position.

    The shared census checks production ordering only.  This stricter probe
    takes ``EXAMPLES_NEEDED + 1`` consecutive generated pairs and, for every
    query rotation, gives all remaining pairs to ``lesson_identifiable``.
    It catches schedules whose only counterexample can accidentally become the
    query, leaving shortcut-compatible demonstrations.
    """
    if type(starts_per_band) is not int or starts_per_band <= 0:
        raise ValueError("starts_per_band must be a positive integer")
    n_demos = getattr(module, "EXAMPLES_NEEDED", None)
    if type(n_demos) is not int or n_demos < 1:
        raise ValueError("generator must declare positive EXAMPLES_NEEDED")
    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        raise ValueError("generator must define callable lesson_identifiable")

    bands = ("easy", "medium", "hard")
    by_band = {}
    failures = []
    total_rotations = 0
    for band in bands:
        band_failures = 0
        for start in range(starts_per_band):
            seed = seed_base + start
            pairs = [
                _lesson_pair(
                    module.generate(seed, start + offset, difficulty=band)
                )
                for offset in range(n_demos + 1)
            ]
            for query_index, query in enumerate(pairs):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = list(hook(demos, query))
                total_rotations += 1
                if reasons:
                    band_failures += 1
                    if len(failures) < 50:
                        failures.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start_sample_index": start,
                                "query_offset": query_index,
                                "reasons": reasons,
                            }
                        )
        by_band[band] = {
            "starts": starts_per_band,
            "query_rotations": starts_per_band * (n_demos + 1),
            "failures": band_failures,
        }

    generator_path = Path(module.__file__).resolve()
    total_failures = sum(row["failures"] for row in by_band.values())
    return {
        "schema": "9ee024f29fdb-cyclic-lesson-probe-v1",
        "task_id": TASK,
        "generator_version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "examples_needed": n_demos,
        "seed_base": seed_base,
        "sample_policy": (
            "for each band/start s, seed=seed_base+s and generate "
            "EXAMPLES_NEEDED+1 consecutive samples at indexes s..s+n; "
            "rotate every pair into query position"
        ),
        "bands": by_band,
        "totals": {
            "bands": len(bands),
            "starts": starts_per_band * len(bands),
            "query_rotations": total_rotations,
            "failures": total_failures,
        },
        "failures_first_50": failures,
        "passed": total_failures == 0,
        "limitations": [
            "Finite declared-rival/hook probe, not a proof of universal identifiability.",
            "Uses the independent Python cell oracle; Racket authority is covered by the standard battery.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts-per-band", type=int, default=100)
    parser.add_argument("--seed-base", type=int, default=808)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = cyclic_lesson_summary(
        load_generator(),
        starts_per_band=args.starts_per_band,
        seed_base=args.seed_base,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "passed": report["passed"], **report["totals"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
