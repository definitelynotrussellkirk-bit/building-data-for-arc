#!/usr/bin/env python3
"""Proposed episode-level projection-reach extension for task 48bda9528e71.

The selected production generator and canonical Racket rule remain unchanged.
This task-local prototype keeps the original object roles and transformation:
find the unique rare nested color, erase the source shape, and project from
occupied row/column extents.  One hidden setting, fixed for the whole episode,
chooses whether each projection is one cell (the canonical rule) or continues
to the canvas boundary.
"""
from __future__ import annotations

from collections import Counter
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
for _path in (ROOT / "shared" / "runtime", ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

TASK_ID = "48bda9528e71"
PARAMETER_NAME = "projection_reach"
SETTINGS = ("one_step", "to_boundary")
DEFAULT_SETTING = "one_step"
PUBLIC_PARENT_TASK_ID = "142ca369"
PUBLIC_PARENT_SHA256 = "7c238849470d35e6328fc8f6bb0b5bb3207783c15d5c8c8f7343cd1b87b4f75e"
BACKGROUND = 8
MAX_PAIRS_PER_SPLIT = 16

PARAMETER_SPEC = {
    "name": PARAMETER_NAME,
    "allowed_values": SETTINGS,
    "original_default": DEFAULT_SETTING,
    "selection_scope": "once_per_episode",
    "input_constraint": (
        "retain only lawful canonical-family inputs where projecting to the "
        "boundary changes at least one output cell relative to one-step markers"
    ),
}


def _load_generator():
    source = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "parametric_base_48bda9528e71", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_setting(setting: str) -> str:
    if type(setting) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be an exact string")
    if setting not in SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {SETTINGS}, got {setting!r}")
    return setting


def _validate_nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative exact integer")
    return value


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool, float or string)")
    if not 1 <= value <= MAX_PAIRS_PER_SPLIT:
        raise ValueError(f"{name} must lie in 1..{MAX_PAIRS_PER_SPLIT}")
    return value


def _validate_difficulty(difficulty: str) -> str:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")
    return difficulty


def _grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _occupied(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != BACKGROUND
    }


def _rare_color(grid: list[list[int]]) -> int:
    counts = Counter(
        value for row in grid for value in row if value != BACKGROUND
    )
    ordered = sorted((count, color) for color, count in counts.items())
    if not ordered or (len(ordered) > 1 and ordered[0][0] == ordered[1][0]):
        raise ValueError("input does not have a unique least-frequent non-background color")
    return ordered[0][1]


def apply_python(
    grid: list[list[int]],
    projection_reach: str = DEFAULT_SETTING,
) -> list[list[int]]:
    """Independent Python mirror for one proposed setting."""
    setting = _validate_setting(projection_reach)
    errors = _GEN.self_check(grid)
    if errors:
        raise ValueError("invalid canonical-family input: " + "; ".join(errors))

    return project_extents(grid, setting)


def project_extents(
    grid: list[list[int]],
    projection_reach: str = DEFAULT_SETTING,
) -> list[list[int]]:
    """Project a prevalidated occupied mask; shared by legacy and native APIs.

    Callers own their input grammar. The legacy API retains its 5..16 validator;
    the native adapter validates the same shape semantics on 5..30 canvases.
    This kernel preserves foreground zero, erasure, clipping and exact extents.
    """
    setting = _validate_setting(projection_reach)

    height, width = len(grid), len(grid[0])
    cells = _occupied(grid)
    rare = _rare_color(grid)
    output = [[BACKGROUND for _ in range(width)] for _ in range(height)]

    for row in sorted({row for row, _ in cells}):
        cols = [col for r, col in cells if r == row]
        left, right = min(cols), max(cols)
        if setting == "one_step":
            targets = []
            if left > 0:
                targets.append(left - 1)
            if right + 1 < width:
                targets.append(right + 1)
        else:
            targets = [*range(0, left), *range(right + 1, width)]
        for col in targets:
            output[row][col] = rare

    for col in sorted({col for _, col in cells}):
        rows = [row for row, c in cells if c == col]
        top, bottom = min(rows), max(rows)
        if setting == "one_step":
            targets = []
            if top > 0:
                targets.append(top - 1)
            if bottom + 1 < height:
                targets.append(bottom + 1)
        else:
            targets = [*range(0, top), *range(bottom + 1, height)]
        for row in targets:
            output[row][col] = rare
    return output


def _program_body(row_marks: str, col_marks: str) -> str:
    return f"""(rule! (lambda (g)
  (let* ((hh (rows g))
         (ww (cols g))
         (bg 8)
         (cells (for*/list ((r (range 0 hh))
                            (c (range 0 ww))
                            #:when (!= (at g r c) bg))
                  (list r c (at g r c))))
         (freq (make-hash))
         (dummy (for ((cell cells))
                  (hash-set! freq
                             (third cell)
                             (+ 1 (hash-ref freq (third cell) 0)))))
         (inner-color
           (car (sort (hash-keys freq)
                      (lambda (a b)
                        (< (hash-ref freq a 0)
                           (hash-ref freq b 0))))))
         (result (make-hash)))
    (for* ((r (range 0 hh)) (c (range 0 ww)))
      (hash-set! result (list r c) bg))
    (for ((r (range 0 hh)))
      (let ((row-cs
              (map second
                   (filter (lambda (cell) (= (first cell) r)) cells))))
        (unless (null? row-cs)
          (let ((left (min-list row-cs))
                (right (max-list row-cs)))
            {row_marks}))))
    (for ((c (range 0 ww)))
      (let ((col-rs
              (map first
                   (filter (lambda (cell) (= (second cell) c)) cells))))
        (unless (null? col-rs)
          (let ((top (min-list col-rs))
                (bot (max-list col-rs)))
            {col_marks}))))
    (build-grid hh ww (r c) (hash-ref result (list r c) bg)))))"""


def program_for(projection_reach: str = DEFAULT_SETTING) -> str:
    """Return exact executable Racket for one fixed episode setting."""
    setting = _validate_setting(projection_reach)
    if setting == "one_step":
        row_marks = """(when (>= (- left 1) 0)
              (hash-set! result (list r (- left 1)) inner-color))
            (when (< (+ right 1) ww)
              (hash-set! result (list r (+ right 1)) inner-color))"""
        col_marks = """(when (>= (- top 1) 0)
              (hash-set! result (list (- top 1) c) inner-color))
            (when (< (+ bot 1) hh)
              (hash-set! result (list (+ bot 1) c) inner-color))"""
    else:
        row_marks = """(for ((mark-c (range 0 left)))
              (hash-set! result (list r mark-c) inner-color))
            (for ((mark-c (range (+ right 1) ww)))
              (hash-set! result (list r mark-c) inner-color))"""
        col_marks = """(for ((mark-r (range 0 top)))
              (hash-set! result (list mark-r c) inner-color))
            (for ((mark-r (range (+ bot 1) hh)))
              (hash-set! result (list mark-r c) inner-color))"""
    return _program_body(row_marks, col_marks)


def normalized_program_hash(projection_reach: str = DEFAULT_SETTING) -> str:
    normalized = " ".join(program_for(projection_reach).split()).encode()
    return hashlib.sha256(normalized).hexdigest()


def select_setting(seed: int) -> str:
    _validate_nonnegative_int(seed, "seed")
    return SETTINGS[seed % len(SETTINGS)]


def _candidate_input(seed: int, candidate_index: int, difficulty: str):
    input_seed = (
        seed * 1_000_003 + candidate_index * 9_973 + int(TASK_ID[:8], 16)
    ) & 0x7FFFFFFF
    sample_index = candidate_index
    return _GEN.generate(input_seed, sample_index, difficulty=difficulty)


def generate_episode(
    seed: int,
    *,
    projection_reach: str | None = None,
    difficulty: str = "medium",
    n_train: int = 4,
    n_test: int = 4,
    start_index: int = 0,
) -> dict[str, Any]:
    """Build one complete episode with a single fixed hidden reach setting."""
    _validate_nonnegative_int(seed, "seed")
    _validate_nonnegative_int(start_index, "start_index")
    _validate_difficulty(difficulty)
    _validate_count(n_train, "n_train")
    _validate_count(n_test, "n_test")
    selected = select_setting(seed) if projection_reach is None else _validate_setting(projection_reach)
    total = n_train + n_test

    pairs: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()
    pair_hashes: list[dict[str, str]] = []
    max_attempts = max(256, total * 64)
    for offset in range(max_attempts):
        candidate_index = start_index + offset
        grid = _candidate_input(seed, candidate_index, difficulty)
        input_hash = _grid_hash(grid)
        if input_hash in seen_inputs:
            continue
        outputs = {setting: apply_python(grid, setting) for setting in SETTINGS}
        hashes = {setting: _grid_hash(output) for setting, output in outputs.items()}
        if len(set(hashes.values())) != len(SETTINGS):
            continue
        seen_inputs.add(input_hash)
        pairs.append({"input": grid, "output": outputs[selected]})
        pair_hashes.append(hashes)
        if len(pairs) == total:
            break
    if len(pairs) != total:
        raise RuntimeError(
            f"found only {len(pairs)} distinct setting-sensitive inputs after "
            f"{max_attempts} deterministic candidates"
        )

    program = program_for(selected)
    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "parameters": {PARAMETER_NAME: selected},
        "program": program,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "public_parent_task_id": PUBLIC_PARENT_TASK_ID,
            "public_parent_sha256": PUBLIC_PARENT_SHA256,
            "transfer": (
                "142ca369 teaches object-derived projections that continue beyond "
                "a local marker. This extension keeps the nested-shape/rare-color "
                "roles and varies whether extent projections stop after one cell "
                "or continue to the canvas boundary."
            ),
            "seed": seed,
            "difficulty": difficulty,
            "selection_scope": "once_per_episode",
            "n_train": n_train,
            "n_test": n_test,
            "start_index": start_index,
            "allowed_settings": list(SETTINGS),
            "canonical_default": DEFAULT_SETTING,
            "input_constraint": PARAMETER_SPEC["input_constraint"],
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "pair_output_hashes_by_setting": pair_hashes,
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Strip private setting metadata, Racket code, and query answers."""
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train/test lists")
    try:
        return {
            "train": [
                {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                for pair in train
            ],
            "test": [{"input": deepcopy(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("episode pairs require input and stored output grids") from exc


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--projection-reach", choices=SETTINGS)
    parser.add_argument("--train", type=int, default=4)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        projection_reach=args.projection_reach,
        difficulty=args.difficulty,
        n_train=args.train,
        n_test=args.test,
        start_index=args.start_index,
    )
    payload = public_challenge(episode) if args.public else episode
    if args.public:
        data = public_challenge_bytes(payload)
    else:
        data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
    else:
        sys.stdout.buffer.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
