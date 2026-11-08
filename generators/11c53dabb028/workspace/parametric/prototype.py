#!/usr/bin/env python3
"""Task-local repeat-count parameter prototype for ARC task 11c53dabb028.

The selected production generator and canonical Racket authority remain fixed.
Each prototype episode chooses vertical and horizontal tile repeat counts once
and keeps them fixed across every demonstration and query.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import (  # noqa: E402
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "11c53dabb028"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_RULE_HASH = "573d7b5ea64c"
PARAMETER_NAMES = ("vertical_repeats", "horizontal_repeats")
ALLOWED_REPEATS = (1, 2)
DEFAULT_SETTING = (2, 2)
SETTINGS = ((1, 1), (1, 2), (2, 1), (2, 2))
_HEIGHT_FRAGMENT = "(* 2 h)"
_WIDTH_FRAGMENT = "(* 2 w)"


def _validate_repeat(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool)")
    if value not in ALLOWED_REPEATS:
        raise ValueError(f"{name} must be one of {ALLOWED_REPEATS}, got {value!r}")
    return value


def normalized_source_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        source = row.get("program_solution")
        if not isinstance(source, str) or not source:
            raise RuntimeError(f"canonical row {TASK_ID} has no program_solution")
        digest = normalized_source_hash(source)
        if digest != CANONICAL_RULE_HASH:
            raise RuntimeError(
                f"canonical rule hash drift: {digest} != {CANONICAL_RULE_HASH}"
            )
        if source.count(_HEIGHT_FRAGMENT) != 1 or source.count(_WIDTH_FRAGMENT) != 1:
            raise RuntimeError("canonical repeat fragments are missing or ambiguous")
        return source
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def program_for(
    vertical_repeats: int = DEFAULT_SETTING[0],
    horizontal_repeats: int = DEFAULT_SETTING[1],
) -> str:
    """Return exact executable Racket for one bounded repeat-count setting."""
    vertical_repeats = _validate_repeat("vertical_repeats", vertical_repeats)
    horizontal_repeats = _validate_repeat("horizontal_repeats", horizontal_repeats)
    source = _canonical_program()
    if vertical_repeats != DEFAULT_SETTING[0]:
        source = source.replace(
            _HEIGHT_FRAGMENT, f"(* {vertical_repeats} h)", 1
        )
    if horizontal_repeats != DEFAULT_SETTING[1]:
        source = source.replace(
            _WIDTH_FRAGMENT, f"(* {horizontal_repeats} w)", 1
        )
    return source


def normalized_program_hash(
    vertical_repeats: int = DEFAULT_SETTING[0],
    horizontal_repeats: int = DEFAULT_SETTING[1],
) -> str:
    return normalized_source_hash(program_for(vertical_repeats, horizontal_repeats))


@lru_cache(maxsize=1)
def _selected_generator():
    return load_selected_generator(TASK_ID, root=find_root(__file__))


def _validate_grid(grid: Any) -> None:
    generator, _, _ = _selected_generator()
    before = deepcopy(grid)
    reasons = generator.self_check(grid)
    if grid != before:
        raise RuntimeError("selected generator self_check mutated the input")
    if reasons:
        raise ValueError(
            "input is outside the selected generator grammar: " + "; ".join(reasons)
        )


def solve(
    grid: list[list[int]],
    *,
    vertical_repeats: int = DEFAULT_SETTING[0],
    horizontal_repeats: int = DEFAULT_SETTING[1],
) -> list[list[int]]:
    """Independent Python mirror for one repeat-count setting."""
    vertical_repeats = _validate_repeat("vertical_repeats", vertical_repeats)
    horizontal_repeats = _validate_repeat("horizontal_repeats", horizontal_repeats)
    _validate_grid(grid)
    return tile_output(grid, vertical_repeats=vertical_repeats,
                       horizontal_repeats=horizontal_repeats)


def tile_output(
    grid: list[list[int]],
    *,
    vertical_repeats: int = DEFAULT_SETTING[0],
    horizontal_repeats: int = DEFAULT_SETTING[1],
) -> list[list[int]]:
    """Shared color/complement/tile kernel, including solid derived frames.

    ``solve`` retains the original mixed-mask input grammar. The native
    component extension can produce an all-solid intermediate, whose correct
    complement is empty. This helper validates that wider intermediate grammar
    without weakening the original public solver's input validation.
    """
    vertical_repeats = _validate_repeat("vertical_repeats", vertical_repeats)
    horizontal_repeats = _validate_repeat("horizontal_repeats", horizontal_repeats)
    if (not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 15
            or not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 15
            or any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)
            or not any(v for row in grid for v in row)):
        raise ValueError('tile must be a rectangular1..15 ARC grid with a nonzero cell')
    h, w = len(grid), len(grid[0])
    selected = next(value for row in grid for value in row if value != 0)
    return [
        [
            selected if grid[row % h][column % w] == 0 else 0
            for column in range(horizontal_repeats * w)
        ]
        for row in range(vertical_repeats * h)
    ]


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer (not bool)")
    return seed


def select_setting(seed: int) -> tuple[int, int]:
    """Choose one deterministic hidden repeat setting for the complete episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|repeat-count|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return SETTINGS[digest[0] % len(SETTINGS)]

DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4
_BANDS = ("easy", "medium", "hard", "medium", "hard", "easy", "medium")


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive exact integer (not bool)")
    return value


def grid_hash(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _resolve_setting(
    seed: int,
    vertical_repeats: int | None,
    horizontal_repeats: int | None,
) -> tuple[int, int]:
    vertical, horizontal = select_setting(seed)
    if vertical_repeats is not None:
        vertical = _validate_repeat("vertical_repeats", vertical_repeats)
    if horizontal_repeats is not None:
        horizontal = _validate_repeat("horizontal_repeats", horizontal_repeats)
    return vertical, horizontal


def _input_seed(seed: int, sample_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}|repeat-input|{PROTOTYPE_VERSION}|{seed}|{sample_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


def generate_episode(
    seed: int,
    *,
    vertical_repeats: int | None = None,
    horizontal_repeats: int | None = None,
    n_train: int = DEFAULT_N_TRAIN,
    n_test: int = DEFAULT_N_TEST,
) -> dict[str, Any]:
    """Build one complete episode with one fixed hidden repeat setting."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    setting = _resolve_setting(seed, vertical_repeats, horizontal_repeats)
    generator, source_path, source_sha256 = _selected_generator()

    total = n_train + n_test
    accepted: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()
    max_attempts = max(256, total * 64)
    for sample_index in range(max_attempts):
        band = _BANDS[len(accepted) % len(_BANDS)]
        input_seed = _input_seed(seed, sample_index)
        grid = generator.generate(input_seed, sample_index, difficulty=band)
        digest = grid_hash(grid)
        if digest in seen_inputs:
            continue
        seen_inputs.add(digest)
        output = solve(
            grid,
            vertical_repeats=setting[0],
            horizontal_repeats=setting[1],
        )
        accepted.append(
            {
                "input": grid,
                "output": output,
                "meta": {
                    "sample_index": sample_index,
                    "input_seed": input_seed,
                    "difficulty": band,
                    "input_sha256": digest,
                    "setting": setting,
                    "output_sha256": grid_hash(output),
                },
            }
        )
        if len(accepted) == total:
            break
    if len(accepted) != total:
        raise RuntimeError(
            f"could not sample {total} distinct lawful inputs within {max_attempts} attempts"
        )

    program = program_for(*setting)
    root = find_root(__file__)
    return {
        "train": accepted[:n_train],
        "test": accepted[n_train:],
        "parameters": {
            "vertical_repeats": setting[0],
            "horizontal_repeats": setting[1],
        },
        "program": program,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "version": PROTOTYPE_VERSION,
            "seed": seed,
            "selection_scope": "once_per_episode",
            "canonical_default": {
                "vertical_repeats": DEFAULT_SETTING[0],
                "horizontal_repeats": DEFAULT_SETTING[1],
            },
            "allowed_repeats": list(ALLOWED_REPEATS),
            "n_train": n_train,
            "n_test": n_test,
            "generator_path": str(Path(source_path).relative_to(root)),
            "generator_sha256": source_sha256,
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_hash": normalized_program_hash(*setting),
            "accepted_sample_indices": [
                pair["meta"]["sample_index"] for pair in accepted
            ],
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible demonstrations and answer-free queries."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--vertical-repeats", type=int, choices=ALLOWED_REPEATS)
    parser.add_argument("--horizontal-repeats", type=int, choices=ALLOWED_REPEATS)
    parser.add_argument("--train", type=int, default=DEFAULT_N_TRAIN)
    parser.add_argument("--test", type=int, default=DEFAULT_N_TEST)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        vertical_repeats=args.vertical_repeats,
        horizontal_repeats=args.horizontal_repeats,
        n_train=args.train,
        n_test=args.test,
    )
    payload = public_challenge(episode) if args.public else episode
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
