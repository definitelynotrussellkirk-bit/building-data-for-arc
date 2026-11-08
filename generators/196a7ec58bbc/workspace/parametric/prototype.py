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
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
GENERATOR_PATH = TASK_DIR / "generator.py"
TASK_ID = "196a7ec58bbc"

ALLOWED_HANDEDNESS = ("clockwise", "counterclockwise")
DEFAULT_HANDEDNESS = "clockwise"
DEFAULT_DEMONSTRATION_COUNT = 3
DEFAULT_QUERY_COUNT = 1
MAX_EPISODE_PAIR_COUNT = 64
MAX_CANDIDATE_ATTEMPTS = 4096
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


def _validate_pair_counts(demonstration_count: int, query_count: int) -> None:
    for name, value in (
        ("demonstration_count", demonstration_count),
        ("query_count", query_count),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive exact integer")
    total = demonstration_count + query_count
    if total > MAX_EPISODE_PAIR_COUNT:
        raise ValueError(
            f"episode requests {total} pairs; maximum is {MAX_EPISODE_PAIR_COUNT}"
        )


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
    demonstration_count: int = DEFAULT_DEMONSTRATION_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independently requested pair counts."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    _validate_pair_counts(demonstration_count, query_count)
    selected = select_setting(seed) if handedness is None else handedness
    _validate_handedness(selected)

    requested = demonstration_count + query_count
    pairs = []
    hashes_by_setting = []
    seen_inputs: set[str] = set()
    attempts = 0
    for candidate_index in range(MAX_CANDIDATE_ATTEMPTS):
        attempts += 1
        grid = prototype_input(seed, candidate_index, difficulty=difficulty)
        input_hash = grid_hash(grid)
        if input_hash in seen_inputs:
            continue
        outputs = {
            setting: solve(grid, handedness=setting) for setting in SETTINGS
        }
        hashes = {setting: grid_hash(output) for setting, output in outputs.items()}
        if len(set(hashes.values())) != len(SETTINGS):
            raise RuntimeError("episode pair does not separate both handedness settings")
        seen_inputs.add(input_hash)
        pairs.append({"input": grid, "output": outputs[selected]})
        hashes_by_setting.append(hashes)
        if len(pairs) == requested:
            break
    else:
        raise RuntimeError(
            f"could not sample {requested} distinct lawful inputs within "
            f"{MAX_CANDIDATE_ATTEMPTS} attempts"
        )

    program = program_for(selected)
    return {
        "train": pairs[:demonstration_count],
        "test": pairs[demonstration_count:],
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
            "demonstration_count": demonstration_count,
            "query_count": query_count,
            "unique_input_count": len(seen_inputs),
            "candidate_attempts": attempts,
            "maximum_episode_pair_count": MAX_EPISODE_PAIR_COUNT,
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


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Canonical visible bytes; private fields and query answers are ignored."""
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    """Opaque SHA-256 identity derived from exactly the visible challenge bytes."""
    return public_challenge_id(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"


def write_public_batch(
    episodes: Iterable[dict[str, Any]],
    out_dir: Path,
) -> list[dict[str, Any]]:
    """Write a stable, duplicate-free public batch keyed only by visible bytes."""
    plans = []
    by_id: dict[str, bytes] = {}
    for episode in episodes:
        payload = public_bytes(episode)
        identifier = public_id(episode)
        previous = by_id.get(identifier)
        if previous is not None:
            if previous == payload:
                raise ValueError(f"duplicate public payload: {identifier}")
            raise ValueError(f"public ID collision: {identifier}")
        by_id[identifier] = payload
        plans.append((identifier, payload))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for identifier, payload in sorted(plans):
        path = out_dir / f"challenge-{identifier}.json"
        path.write_bytes(payload)
        written.append(
            {
                "public_id": identifier,
                "path": str(path),
                "public_sha256": hashlib.sha256(payload).hexdigest(),
                "public_bytes": payload,
            }
        )
    return written


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--handedness", choices=ALLOWED_HANDEDNESS)
    parser.add_argument(
        "--demonstrations", type=int, default=DEFAULT_DEMONSTRATION_COUNT
    )
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--public", action="store_true")
    parser.add_argument(
        "--public-dir",
        type=Path,
        help="write challenge-<visible-sha256>.json and print a JSON receipt",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        difficulty=args.difficulty,
        handedness=args.handedness,
        demonstration_count=args.demonstrations,
        query_count=args.queries,
    )
    if args.public_dir is not None:
        if args.out is not None:
            parser.error("--public-dir and --out are mutually exclusive")
        row = write_public_batch([episode], args.public_dir)[0]
        receipt = {
            "public_id": row["public_id"],
            "path": row["path"],
            "public_sha256": row["public_sha256"],
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0

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
