"""Bounded ambiguity and boundary audit for the repaired base generator.

The check enumerates consecutive three-example windows across all supported
ordinary difficulties.  It asks the generator's semantic rival checker whether
any noncanonical quadrant priority order survives the visible labels.  It also
exercises the minimum/maximum declared dimensions and the no-overlap override.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parents[1] / "generator.py"
_SPEC = importlib.util.spec_from_file_location("generator_a23328d45092_base_audit", GENERATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {GENERATOR_PATH}")
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def run_audit(seed_count: int = 64) -> dict[str, Any]:
    _exact_int(seed_count, 1, 4096, "seed_count")
    difficulties = (None, "easy", "medium", "hard")
    window_count = 0
    example_count = 0
    ambiguous_windows = 0
    boundary_cases = 0
    surviving_examples: list[dict[str, Any]] = []

    for seed in range(seed_count):
        for difficulty in difficulties:
            for start in range(12):
                demos = []
                for offset in range(3):
                    grid = GEN.generate(seed, start + offset, difficulty=difficulty)
                    errors = GEN.self_check(grid)
                    if errors:
                        raise AssertionError(
                            f"self_check failed seed={seed} difficulty={difficulty} "
                            f"index={start + offset}: {errors}"
                        )
                    demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
                    example_count += 1
                survivors = GEN.surviving_priority_rivals(demos)
                if survivors:
                    ambiguous_windows += 1
                    if len(surviving_examples) < 8:
                        surviving_examples.append(
                            {
                                "seed": seed,
                                "difficulty": difficulty,
                                "start": start,
                                "survivors": survivors,
                            }
                        )
                window_count += 1

        for size in (5, 30):
            for include_overlap in (False, True):
                grid = GEN.generate(
                    seed,
                    seed % 3,
                    difficulty="medium",
                    grid_h=size,
                    grid_w=size,
                    palette_kind="broad",
                    quadrant_density="dense",
                    sep_position="center",
                    anchor_corner=True,
                    include_overlap=include_overlap,
                )
                errors = GEN.self_check(grid)
                if errors:
                    raise AssertionError(
                        f"boundary self_check failed seed={seed} size={size} "
                        f"include_overlap={include_overlap}: {errors}"
                    )
                GEN.rule_mirror(grid)
                boundary_cases += 1

    if ambiguous_windows:
        raise AssertionError(
            f"{ambiguous_windows}/{window_count} three-example windows retain priority rivals: "
            f"{surviving_examples}"
        )
    return {
        "schema": "arcpuzzles-base-teaching-audit-v1",
        "task_id": GEN.TASK_ID,
        "status": "passed",
        "seed_count": seed_count,
        "difficulties": ["default" if value is None else value for value in difficulties],
        "window_count": window_count,
        "example_count": example_count,
        "ambiguous_windows": ambiguous_windows,
        "boundary_cases": boundary_cases,
        "dimension_bounds": [5, 30],
        "profiles": list(GEN.SCHEDULE_PROFILES),
        "scope_note": "bounded priority-order rival audit; not a universal uniqueness proof",
    }


def write_receipt(receipt: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = run_audit(args.seeds)
    write_receipt(receipt, args.out)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
