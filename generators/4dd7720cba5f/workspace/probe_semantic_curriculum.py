#!/usr/bin/env python3
"""Reproduce 4dd7720cba5f's canonical-shortcut and lesson-window checks.

Run from either a source tree or a copied task-test runtime.  The report is
small by design: it records counts and replay coordinates, not full grids.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from puzzle_generators.runner import _load_generator_module
from reviewer_support import canonical_pairs, find_root


TASK_ID = "4dd7720cba5f"
BANDS = ("easy", "medium", "hard")
DEFAULT_SEED = 72_001


def load_generator(root: Path):
    """Load from a copied runtime or directly from the source-tree task."""
    try:
        return _load_generator_module(TASK_ID)
    except FileNotFoundError:
        path = root / "generators" / TASK_ID / "generator.py"
        if not path.is_file():
            raise
        spec = importlib.util.spec_from_file_location(
            f"review_probe_{TASK_ID}", path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load generator from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def audit(*, starts: int, seed: int) -> dict:
    root = find_root(__file__)
    module = load_generator(root)
    pairs = canonical_pairs(TASK_ID, root=root)

    canonical_fit = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        matches = sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        canonical_fit[name] = {"matches": matches, "pairs": len(pairs)}

    windows = []
    failures = []
    for band in BANDS:
        for start in range(starts):
            demos = []
            demo_profiles = []
            for offset in range(module.EXAMPLES_NEEDED):
                grid = module.generate(
                    seed,
                    start + offset,
                    difficulty=band,
                )
                demos.append(
                    {"input": grid, "output": module.solve_python(grid)}
                )
                demo_profiles.append(
                    module.observe_overrides(grid)["scene_profile"]
                )
            query_grid = module.generate(
                seed,
                start + module.EXAMPLES_NEEDED,
                difficulty=band,
            )
            query = {
                "input": query_grid,
                "output": module.solve_python(query_grid),
            }
            reasons = module.lesson_identifiable(demos, query)
            survivor_names = [
                name
                for name, rival in module.LESSON_COMPETITORS.items()
                if all(
                    rival(pair["input"]) == pair["output"]
                    for pair in demos
                )
            ]
            row = {
                "band": band,
                "start": start,
                "demo_profiles": demo_profiles,
                "query_profile": module.observe_overrides(query_grid)[
                    "scene_profile"
                ],
                "reasons": reasons,
                "surviving_competitors": survivor_names,
            }
            windows.append(row)
            if reasons or survivor_names:
                failures.append(row)

    return {
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_path": str(
            Path(module.__file__).resolve()
        ),
        "seed": seed,
        "starts_per_band": starts,
        "lesson_policy": (
            f"{module.EXAMPLES_NEEDED} consecutive demos plus one query"
        ),
        "canonical_shortcut_fit": canonical_fit,
        "windows_checked": len(windows),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.starts < 1:
        parser.error("--starts must be positive")
    report = audit(starts=args.starts, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
