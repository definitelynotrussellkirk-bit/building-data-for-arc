#!/usr/bin/env python3
"""Unapproved episode-level symmetry-group extension for ea8116b3e778.

The selected production generator and canonical Racket authority remain unchanged.
This task-local prototype fixes one ``symmetry_mode`` for the whole episode and
uses the same lawful single-quadrant inputs across settings so the rule effect is
observable rather than confounded with a different sampler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "ea8116b3e778"
PROTOTYPE_ID = "ea8116b3e778-symmetry-mode-v1"
SYMMETRY_MODES = ("horizontal", "vertical", "half_turn", "both")
DEFAULT_SYMMETRY_MODE = "both"
DEFAULT_DEMONSTRATION_COUNT = 2
DEFAULT_QUERY_COUNT = 4
MAX_EPISODE_PAIR_COUNT = 64
MAX_CANDIDATE_ATTEMPTS = 4096
CANONICAL_NORMALIZED_HASH_PREFIX = "4e2d4d62614f"

_GENERATORS: dict[Path, Any] = {}


def _root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _validate_mode(symmetry_mode: str) -> None:
    if type(symmetry_mode) is not str or symmetry_mode not in SYMMETRY_MODES:
        raise ValueError(
            f"symmetry_mode must be one of {SYMMETRY_MODES}, got {symmetry_mode!r}"
        )


def _validate_seed_index(seed: int, index: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")


def _validate_counts(demonstration_count: int, query_count: int) -> None:
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


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()


def canonical_source(*, root=None) -> str:
    """Return the one source-qualified canonical authority for this task."""
    sources = set()
    for line in canonical_path(_root(root)).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and isinstance(
            row.get("program_solution"), str
        ):
            sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(sources)}"
        )
    source = sources.pop()
    digest = _normalized_hash(source)
    if not digest.startswith(CANONICAL_NORMALIZED_HASH_PREFIX):
        raise ValueError(
            "canonical program no longer matches the pinned normalized hash prefix"
        )
    return source


def _variant_program(predicate: str, label: str) -> str:
    return f"""(rule!
 ;; Proposed {label} reflection variant around the green(3) bbox center.
 ;; Preserve nonzero cells; paint an empty cell red when its selected mirror is red.
 (lambda (g)
  (let* ((bb (bbox-of-cells (find-color g 3)))
         (sr (+ (first bb) (third bb)))
         (sc (+ (second bb) (fourth bb))))
    (cellmap g (r c v)
      (if (!= 0 v) v
        (if {predicate}
          2 0))))))"""


def program_for(
    symmetry_mode: str = DEFAULT_SYMMETRY_MODE,
    *,
    root=None,
) -> str:
    """Materialize the exact Racket authority for one proposed setting."""
    _validate_mode(symmetry_mode)
    if symmetry_mode == "both":
        return canonical_source(root=root)
    predicates = {
        "horizontal": "(= 2 (safe-at g (- sr r) c 0))",
        "vertical": "(= 2 (safe-at g r (- sc c) 0))",
        "half_turn": "(= 2 (safe-at g (- sr r) (- sc c) 0))",
    }
    return _variant_program(predicates[symmetry_mode], symmetry_mode)


def normalized_program_hash(
    symmetry_mode: str = DEFAULT_SYMMETRY_MODE,
    *,
    root=None,
) -> str:
    return _normalized_hash(program_for(symmetry_mode, root=root))


def _generator(*, root=None):
    resolved = _root(root)
    module = _GENERATORS.get(resolved)
    if module is None:
        module, _, _ = load_selected_generator(TASK_ID, root=resolved)
        _GENERATORS[resolved] = module
    return module


def _grid_hash(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def solve(grid, *, symmetry_mode: str = DEFAULT_SYMMETRY_MODE):
    """Independent Python mirror of one proposed Racket setting."""
    _validate_mode(symmetry_mode)
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    greens = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 3
    ]
    if not greens:
        raise ValueError("missing green pivot")
    sr = min(row for row, _ in greens) + max(row for row, _ in greens)
    sc = min(col for _, col in greens) + max(col for _, col in greens)
    result = [row[:] for row in source]

    for row in range(height):
        for col in range(width):
            if source[row][col] != 0:
                continue
            selected = {
                "horizontal": ((sr - row, col),),
                "vertical": ((row, sc - col),),
                "half_turn": ((sr - row, sc - col),),
                "both": (
                    (sr - row, col),
                    (row, sc - col),
                    (sr - row, sc - col),
                ),
            }[symmetry_mode]
            if any(
                0 <= other_row < height
                and 0 <= other_col < width
                and source[other_row][other_col] == 2
                for other_row, other_col in selected
            ):
                result[row][col] = 2
    return result


def select_symmetry_mode(seed: int) -> str:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    return SYMMETRY_MODES[seed % len(SYMMETRY_MODES)]


def prototype_input(
    seed: int,
    index: int,
    *,
    difficulty: str = "medium",
    root=None,
):
    """Return one lawful input whose four candidate settings all disagree."""
    _validate_seed_index(seed, index)
    _validate_difficulty(difficulty)
    input_seed = (seed * 1_000_003 + index * 97 + 811_637) & 0x7FFFFFFF
    sample_index = seed * 4_099 + index
    grid = _generator(root=root).generate(
        input_seed,
        sample_index,
        difficulty=difficulty,
        scene_profile="single_quadrant",
    )
    outputs = {
        mode: _grid_hash(solve(grid, symmetry_mode=mode))
        for mode in SYMMETRY_MODES
    }
    if len(set(outputs.values())) != len(SYMMETRY_MODES):
        raise RuntimeError("prototype input failed to distinguish all symmetry modes")
    return [row[:] for row in grid]


def generate_episode(
    seed: int,
    *,
    symmetry_mode: str | None = None,
    difficulty: str = "medium",
    demonstration_count: int = DEFAULT_DEMONSTRATION_COUNT,
    query_count: int = DEFAULT_QUERY_COUNT,
    root=None,
) -> dict[str, Any]:
    """Build one fixed-setting episode with independent demo/query counts."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    _validate_counts(demonstration_count, query_count)
    _validate_difficulty(difficulty)
    selected = (
        select_symmetry_mode(seed) if symmetry_mode is None else symmetry_mode
    )
    _validate_mode(selected)

    requested = demonstration_count + query_count
    pairs = []
    seen_inputs: set[str] = set()
    attempts = 0
    for candidate_index in range(MAX_CANDIDATE_ATTEMPTS):
        attempts += 1
        grid = prototype_input(
            seed,
            candidate_index,
            difficulty=difficulty,
            root=root,
        )
        key = _grid_hash(grid)
        if key in seen_inputs:
            continue
        seen_inputs.add(key)
        pairs.append(
            {
                "input": grid,
                "output": solve(grid, symmetry_mode=selected),
            }
        )
        if len(pairs) == requested:
            break
    if len(pairs) != requested:
        raise RuntimeError(
            f"found only {len(pairs)} distinct inputs after {attempts} attempts"
        )

    source = program_for(selected, root=root)
    episode = {
        "task_id": TASK_ID,
        "prototype_id": PROTOTYPE_ID,
        "parameters": {"symmetry_mode": selected},
        "program": source,
        "program_normalized_sha256": _normalized_hash(source),
        "train": pairs[:demonstration_count],
        "test": pairs[demonstration_count:],
        "meta": {
            "seed": seed,
            "difficulty": difficulty,
            "demonstration_count": demonstration_count,
            "query_count": query_count,
            "candidate_attempts": attempts,
            "input_profile": "single_quadrant",
        },
    }
    validate_episode(episode, root=root)
    return episode


def validate_episode(episode: dict[str, Any], *, root=None) -> dict[str, Any]:
    """Reject mislabeled, unidentifiable, duplicate, or inconsistent episodes."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    if episode.get("task_id") != TASK_ID or episode.get("prototype_id") != PROTOTYPE_ID:
        raise ValueError("episode identity does not match this prototype")
    parameters = episode.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode is missing parameters")
    selected = parameters.get("symmetry_mode")
    _validate_mode(selected)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    _validate_counts(len(train), len(test))

    expected_program = program_for(selected, root=root)
    if episode.get("program") != expected_program:
        raise ValueError("episode program does not match its symmetry_mode")
    expected_program_hash = _normalized_hash(expected_program)
    if episode.get("program_normalized_sha256") != expected_program_hash:
        raise ValueError("episode program hash does not match its program")

    seen_inputs: set[str] = set()
    rival_separation = {mode: 0 for mode in SYMMETRY_MODES if mode != selected}
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                raise ValueError(f"{split_name} pair {index} is malformed")
            grid = normalize_grid(pair["input"])
            stored = normalize_grid(pair["output"])
            key = _grid_hash(grid)
            if key in seen_inputs:
                raise ValueError("episode contains duplicate inputs")
            seen_inputs.add(key)
            expected = solve(grid, symmetry_mode=selected)
            if stored != expected:
                raise ValueError(
                    f"stored output does not match {selected} at {split_name}[{index}]"
                )
            for rival in rival_separation:
                if stored != solve(grid, symmetry_mode=rival):
                    rival_separation[rival] += 1
                else:
                    raise ValueError(
                        f"{split_name}[{index}] does not distinguish {selected} from {rival}"
                    )

    meta = episode.get("meta")
    if not isinstance(meta, dict):
        raise ValueError("episode is missing metadata")
    if meta.get("demonstration_count") != len(train):
        raise ValueError("metadata demonstration_count mismatch")
    if meta.get("query_count") != len(test):
        raise ValueError("metadata query_count mismatch")

    return {
        "prototype_id": PROTOTYPE_ID,
        "symmetry_mode": selected,
        "demonstration_count": len(train),
        "query_count": len(test),
        "distinct_inputs": len(seen_inputs),
        "rival_separation_counts": rival_separation,
        "program_normalized_sha256": expected_program_hash,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project only visible challenge data; private fields cannot affect its ID."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return {
            "train": [
                {
                    "input": normalize_grid(pair["input"]),
                    "output": normalize_grid(pair["output"]),
                }
                for pair in train
            ],
            "test": [
                {"input": normalize_grid(pair["input"])}
                for pair in test
            ],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("visible pairs are malformed") from error


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def write_public(episode: dict[str, Any], directory: str | Path) -> Path:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    payload = public_bytes(episode)
    path = destination / f"challenge-{hashlib.sha256(payload).hexdigest()}.json"
    if path.exists() and path.read_bytes() != payload:
        raise FileExistsError(f"refusing to overwrite different public bytes: {path}")
    path.write_bytes(payload)
    return path


def write_private(episode: dict[str, Any], path: str | Path) -> Path:
    validate_episode(episode)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        episode,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    destination.write_text(payload, encoding="utf-8")
    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--symmetry-mode", choices=SYMMETRY_MODES)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument(
        "--demonstrations", type=int, default=DEFAULT_DEMONSTRATION_COUNT
    )
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--private-out")
    parser.add_argument("--public-dir")
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    episode = generate_episode(
        args.seed,
        symmetry_mode=args.symmetry_mode,
        difficulty=args.difficulty,
        demonstration_count=args.demonstrations,
        query_count=args.queries,
    )
    private_path = write_private(episode, args.private_out) if args.private_out else None
    public_path = write_public(episode, args.public_dir) if args.public_dir else None
    receipt = {
        "prototype_id": PROTOTYPE_ID,
        "symmetry_mode": episode["parameters"]["symmetry_mode"],
        "demonstration_count": len(episode["train"]),
        "query_count": len(episode["test"]),
        "public_id": public_id(episode),
        "private_path": str(private_path) if private_path else None,
        "public_path": str(public_path) if public_path else None,
    }
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
