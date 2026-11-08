#!/usr/bin/env python3
"""Proposed episode-level handedness extension for ARC task 196a7ec58bbc.

The selected production task remains the canonical clockwise arrangement.  This
separate prototype adds one bounded hidden episode parameter: which quarter-turn
is placed in the top-right quadrant.  The setting is chosen once per complete
episode and shared by all demonstrations and the query.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
GENERATOR_PATH = TASK_DIR / "generator.py"
TASK_ID = "196a7ec58bbc"

ALLOWED_HANDEDNESS = ("clockwise", "counterclockwise")
DEFAULT_HANDEDNESS = "clockwise"
SETTINGS = ALLOWED_HANDEDNESS
PARAMETER_CONSTRAINTS = {
    "clockwise": (
        "top-right is 90 degrees clockwise and bottom-left is 90 degrees "
        "counterclockwise (the selected canonical rule)"
    ),
    "counterclockwise": (
        "top-right is 90 degrees counterclockwise and bottom-left is 90 "
        "degrees clockwise"
    ),
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "parametric_base_196a7ec58bbc", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_handedness(handedness: str) -> None:
    if type(handedness) is not str or handedness not in ALLOWED_HANDEDNESS:
        raise ValueError(
            f"handedness must be one of {ALLOWED_HANDEDNESS}, got {handedness!r}"
        )


def _validate_seed_index(seed: int, index: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid):
    original = [row[:] for row in grid]
    clockwise = _rotate_cw(original)
    half_turn = _rotate_cw(clockwise)
    counterclockwise = _rotate_cw(half_turn)
    return original, clockwise, half_turn, counterclockwise


def _tile(top_left, top_right, bottom_left, bottom_right):
    return (
        [left + right for left, right in zip(top_left, top_right)]
        + [left + right for left, right in zip(bottom_left, bottom_right)]
    )


def program_for(handedness: str = DEFAULT_HANDEDNESS) -> str:
    """Return exact executable Racket for one proposed hidden setting."""
    _validate_handedness(handedness)
    top_right = "rotate-cw" if handedness == "clockwise" else "rotate-ccw"
    bottom_left = "rotate-ccw" if handedness == "clockwise" else "rotate-cw"
    return f"""(rule! (lambda (g)
  (stack-grids 'vertical
    (list
      (stack-grids 'horizontal (list g ({top_right} g)))
      (stack-grids 'horizontal (list ({bottom_left} g) (rotate-180 g)))))))"""


def normalized_program_hash(handedness: str = DEFAULT_HANDEDNESS) -> str:
    normalized = " ".join(program_for(handedness).split()).encode()
    return hashlib.sha256(normalized).hexdigest()


def solve(grid, *, handedness: str = DEFAULT_HANDEDNESS):
    """Independent Python mirror used to materialize prototype evidence."""
    _validate_handedness(handedness)
    original, clockwise, half_turn, counterclockwise = _rotations(grid)
    if handedness == "clockwise":
        return _tile(original, clockwise, counterclockwise, half_turn)
    return _tile(original, counterclockwise, clockwise, half_turn)


def canonical_output(grid):
    return solve(grid, handedness=DEFAULT_HANDEDNESS)


def grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def select_setting(seed: int) -> str:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    return SETTINGS[seed % len(SETTINGS)]


def prototype_input(
    seed: int,
    index: int,
    *,
    difficulty: str = "medium",
):
    """Generate a lawful input on which both handedness settings disagree."""
    _validate_seed_index(seed, index)
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    input_seed = (seed * 1_000_003 + index * 97 + 196_427) & 0x7FFFFFFF
    sample_index = seed * 4 + index
    grid = _GEN.generate(input_seed, sample_index, difficulty=difficulty)
    outputs = {
        setting: grid_hash(solve(grid, handedness=setting))
        for setting in SETTINGS
    }
    if len(set(outputs.values())) != len(SETTINGS):
        raise RuntimeError("prototype input failed to distinguish handedness settings")
    return grid


def generate_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    handedness: str | None = None,
) -> dict[str, Any]:
    """Build a three-demonstration/one-query episode with one fixed setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    selected = select_setting(seed) if handedness is None else handedness
    _validate_handedness(selected)

    pairs = []
    hashes_by_setting = []
    for index in range(4):
        grid = prototype_input(seed, index, difficulty=difficulty)
        outputs = {
            setting: solve(grid, handedness=setting) for setting in SETTINGS
        }
        hashes = {setting: grid_hash(output) for setting, output in outputs.items()}
        if len(set(hashes.values())) != len(SETTINGS):
            raise RuntimeError("episode pair does not separate both handedness settings")
        pairs.append({"input": grid, "output": outputs[selected]})
        hashes_by_setting.append(hashes)

    program = program_for(selected)
    return {
        "train": pairs[:3],
        "test": pairs[3:],
        "parameters": {"handedness": selected},
        "program": program,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            "selection_scope": "once_per_episode",
            "allowed_handedness": list(ALLOWED_HANDEDNESS),
            "canonical_default": DEFAULT_HANDEDNESS,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "input_constraint": (
                "all retained inputs have four distinct rotations, so swapping "
                "clockwise and counterclockwise quadrants changes every label"
            ),
            "pair_output_hashes_by_setting": hashes_by_setting,
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
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--handedness", choices=ALLOWED_HANDEDNESS)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        difficulty=args.difficulty,
        handedness=args.handedness,
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
