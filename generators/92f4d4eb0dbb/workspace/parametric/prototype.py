#!/usr/bin/env python3
"""Proposed episode-level midpoint-rule extension for ARC task 92f4d4eb0dbb.

This module is deliberately separate from the selected production generator.
It explores two bounded hidden parameters while preserving the original rule as
its default: which side of the occupied-row midpoint is recolored, and whether
the midpoint boundary is strict or inclusive.  One setting is selected once per
complete episode and is shared by all demonstrations and the query.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
ROOT = next(parent for parent in HERE.parents if (parent / "shared" / "runtime").is_dir())
for path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

GENERATOR_PATH = TASK_DIR / "generator.py"
TASK_ID = "92f4d4eb0dbb"

ALLOWED_SIDES = ("lower", "upper")
ALLOWED_BOUNDARIES = ("strict", "inclusive")
DEFAULT_SIDE = "lower"
DEFAULT_BOUNDARY = "strict"
SETTINGS = tuple(
    (side, boundary)
    for side in ALLOWED_SIDES
    for boundary in ALLOWED_BOUNDARIES
)
PARAMETER_CONSTRAINTS = {
    "side": {
        "lower": "recolor occupied cells below the occupied-row midpoint",
        "upper": "recolor occupied cells above the occupied-row midpoint",
    },
    "boundary": {
        "strict": "leave an occupied integer midpoint row unchanged",
        "inclusive": "include an occupied integer midpoint row on the selected side",
    },
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "parametric_base_92f4d4eb0dbb", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_setting(side: str, boundary: str) -> None:
    if type(side) is not str or side not in ALLOWED_SIDES:
        raise ValueError(f"side must be one of {ALLOWED_SIDES}, got {side!r}")
    if type(boundary) is not str or boundary not in ALLOWED_BOUNDARIES:
        raise ValueError(
            f"boundary must be one of {ALLOWED_BOUNDARIES}, got {boundary!r}"
        )


def _validate_seed_index(seed: int, index: int) -> None:
    if type(seed) is not int:
        raise ValueError(f"seed must be an exact integer, got {type(seed).__name__}")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")


def _comparison_symbol(side: str, boundary: str) -> str:
    _validate_setting(side, boundary)
    return {
        ("lower", "strict"): ">",
        ("lower", "inclusive"): ">=",
        ("upper", "strict"): "<",
        ("upper", "inclusive"): "<=",
    }[(side, boundary)]


def program_for(
    side: str = DEFAULT_SIDE,
    boundary: str = DEFAULT_BOUNDARY,
) -> str:
    """Return the exact executable Racket program for one hidden setting."""
    comparator = _comparison_symbol(side, boundary)
    return f"""(rule! (lambda (g)
         (let* ((ones (filter (lambda (cell) (= 1 (third cell))) (grid-cells g)))
                (min-r (min-list (map fst ones)))
                (max-r (max-list (map fst ones)))
                (mid (/ (+ min-r max-r) 2)))
           (map-grid g (lambda (r c v)
                         (if (and (= v 1) ({comparator} r mid)) 2 v))))))"""


def normalized_program_hash(side: str, boundary: str) -> str:
    normalized = " ".join(program_for(side, boundary).split()).encode()
    return hashlib.sha256(normalized).hexdigest()


def solve(
    grid,
    *,
    side: str = DEFAULT_SIDE,
    boundary: str = DEFAULT_BOUNDARY,
):
    """Independent Python mirror used only to materialize prototype evidence."""
    _validate_setting(side, boundary)
    rows = [
        r
        for r, row in enumerate(grid)
        for value in row
        if value == 1
    ]
    if not rows:
        return deepcopy(grid)
    midpoint_twice = min(rows) + max(rows)

    def selected(r: int) -> bool:
        row_twice = 2 * r
        if side == "lower":
            return row_twice > midpoint_twice if boundary == "strict" else row_twice >= midpoint_twice
        return row_twice < midpoint_twice if boundary == "strict" else row_twice <= midpoint_twice

    return [
        [2 if value == 1 and selected(r) else value for value in row]
        for r, row in enumerate(grid)
    ]


def canonical_output(grid):
    """Return the selected catalog behavior: lower side, strict boundary."""
    return solve(grid, side=DEFAULT_SIDE, boundary=DEFAULT_BOUNDARY)


def grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def select_setting(seed: int) -> tuple[str, str]:
    if type(seed) is not int:
        raise ValueError(f"seed must be an exact integer, got {type(seed).__name__}")
    return SETTINGS[seed % len(SETTINGS)]


def prototype_input(
    seed: int,
    index: int,
    *,
    difficulty: str = "medium",
):
    """Generate an odd-height witness on which all four settings disagree.

    Explicit axes keep this proposal independent of production scheduling while
    still reusing the reviewed constructive input sampler.  Odd spans ensure an
    occupied midpoint row; every retained morphology also has occupied cells on
    both strict sides of that row.
    """
    _validate_seed_index(seed, index)
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    spans = (5, 7)
    shapes = ("notched_frame", "frame", "ladder", "diamond", "zigzag")
    span = spans[(seed + index) % len(spans)]
    shape_kind = shapes[(seed * 3 + index) % len(shapes)]
    grid_h = 9 + ((seed + 2 * index) % 4)
    grid_w = 9 + ((3 * seed + index) % 4)
    input_seed = (seed * 1_000_003 + index * 97 + 92_404) & 0x7FFFFFFF
    grid = _GEN.generate(
        input_seed,
        index,
        difficulty=difficulty,
        grid_h=grid_h,
        grid_w=grid_w,
        span=span,
        shape_kind=shape_kind,
    )
    outputs = {
        setting: grid_hash(solve(grid, side=setting[0], boundary=setting[1]))
        for setting in SETTINGS
    }
    if len(set(outputs.values())) != len(SETTINGS):
        raise RuntimeError(
            "prototype input failed to distinguish all side/boundary settings"
        )
    return grid


def generate_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    side: str | None = None,
    boundary: str | None = None,
) -> dict[str, Any]:
    """Build a 3-demonstration/1-query episode with one fixed hidden rule."""
    if type(seed) is not int:
        raise ValueError(f"seed must be an exact integer, got {type(seed).__name__}")
    if (side is None) != (boundary is None):
        raise ValueError("side and boundary must be supplied together or both omitted")
    selected = select_setting(seed) if side is None else (side, boundary)
    selected_side, selected_boundary = selected
    _validate_setting(selected_side, selected_boundary)

    pairs = []
    all_setting_hashes: list[dict[str, str]] = []
    for index in range(4):
        grid = prototype_input(seed, index, difficulty=difficulty)
        outputs = {
            setting: solve(grid, side=setting[0], boundary=setting[1])
            for setting in SETTINGS
        }
        hashes = {
            f"{setting[0]}_{setting[1]}": grid_hash(output)
            for setting, output in outputs.items()
        }
        if len(set(hashes.values())) != len(SETTINGS):
            raise RuntimeError("episode pair does not separate every declared setting")
        pairs.append({"input": grid, "output": outputs[selected]})
        all_setting_hashes.append(hashes)

    program = program_for(selected_side, selected_boundary)
    return {
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            "selection_scope": "once_per_episode",
            "parameters": {
                "side": selected_side,
                "boundary": selected_boundary,
            },
            "allowed": {
                "side": list(ALLOWED_SIDES),
                "boundary": list(ALLOWED_BOUNDARIES),
            },
            "canonical_default": {
                "side": DEFAULT_SIDE,
                "boundary": DEFAULT_BOUNDARY,
            },
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(
                selected_side, selected_boundary
            ),
            "input_constraint": (
                "odd occupied height, occupied midpoint row, and occupied cells "
                "on both strict sides; all four settings differ on every pair"
            ),
            "pair_output_hashes_by_setting": all_setting_hashes,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, exact rule, metadata, and query answer."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--side", choices=ALLOWED_SIDES)
    parser.add_argument("--boundary", choices=ALLOWED_BOUNDARIES)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if (args.side is None) != (args.boundary is None):
        parser.error("--side and --boundary must be supplied together")
    episode = generate_episode(
        args.seed,
        difficulty=args.difficulty,
        side=args.side,
        boundary=args.boundary,
    )
    payload = public_challenge(episode) if args.public else episode
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
