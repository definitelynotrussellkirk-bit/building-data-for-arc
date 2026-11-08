#!/usr/bin/env python3
"""Task-local episode-level orientation-scope prototype for d09fae8197f6.

The production generator and canonical Racket authority remain unchanged.  This
prototype adds one hidden setting chosen once per episode:

``dihedral`` (default)
    Search all four rotations and all four reflected rotations, exactly matching
    the canonical task.
``rotations``
    Search only the four rotations of the yellow/magenta template.

Inputs are rejection-sampled from the selected production generator.  Every
retained pair is lawful, both settings visibly stamp at least one cell, and the
settings produce different labels, so demonstrations identify the episode rule.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_id,
)

TASK_ID = "d09fae8197f6"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
PARAMETERS = {
    "orientation_scope": {
        "allowed": ("dihedral", "rotations"),
        "default": "dihedral",
        "selected_once_per_episode": True,
    }
}
_AUTO = object()
_CANONICAL_ORIENTATION_ANCHOR = "(orientations (list t0 t1 t2 t3 t4 t5 t6 t7))"
_ROTATIONS_ORIENTATION_ANCHOR = "(orientations (list t0 t1 t2 t3))"
_DIFFICULTIES = ("hard", "medium", "easy")
_MAX_CANDIDATES_PER_PAIR = 128


def _validate_scope(orientation_scope: str) -> None:
    allowed = PARAMETERS["orientation_scope"]["allowed"]
    if type(orientation_scope) is not str or orientation_scope not in allowed:
        raise ValueError(
            "orientation_scope must be exactly 'dihedral' or 'rotations'"
        )


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative Python int")


def _validate_counts(demo_count: int, query_count: int) -> None:
    if type(demo_count) is not int or not 1 <= demo_count <= 8:
        raise ValueError("demo_count must be an integer count in 1..8")
    if type(query_count) is not int or not 1 <= query_count <= 4:
        raise ValueError("query_count must be an integer count in 1..4")


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    """Return the original canonical record after checking rule agreement."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record)
    if not matches:
        raise ValueError(f"missing canonical record for {TASK_ID}")
    programs = {record.get("program_solution") for record in matches}
    if len(programs) != 1:
        raise ValueError(f"canonical variants disagree on rule authority for {TASK_ID}")
    return next(
        (record for record in matches if record.get("content_hash") == TASK_ID),
        matches[0],
    )


def racket_program(
    orientation_scope: str = "dihedral", *, root: Path | str = ROOT
) -> str:
    """Materialize exact executable Racket for one bounded setting."""
    _validate_scope(orientation_scope)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_CANONICAL_ORIENTATION_ANCHOR) != 1:
        raise ValueError(
            "canonical orientation anchor changed; prototype requires review"
        )
    if orientation_scope == "dihedral":
        return canonical
    return canonical.replace(
        _CANONICAL_ORIENTATION_ANCHOR,
        _ROTATIONS_ORIENTATION_ANCHOR,
        1,
    )


def choose_orientation_scope(seed: int) -> str:
    """Choose one hidden setting deterministically, exactly once per episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:orientation_scope".encode()
    ).digest()
    allowed = PARAMETERS["orientation_scope"]["allowed"]
    return allowed[digest[0] % len(allowed)]


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not grid:
        raise ValueError("grid must be a nonempty rectangular list of rows")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid must be a nonempty rectangular list of rows")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    return len(grid), width


def _rotate_cw(shape: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*shape[::-1])]


def _flip_lr(shape: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in shape]


def _orientations(shape: list[list[int]]) -> tuple[list[list[int]], ...]:
    rotations = [[row[:] for row in shape]]
    for _ in range(3):
        rotations.append(_rotate_cw(rotations[-1]))
    reflected = [_flip_lr(shape)]
    for _ in range(3):
        reflected.append(_rotate_cw(reflected[-1]))
    return tuple(rotations + reflected)


def _template_from_yellow_bbox(grid: list[list[int]]) -> list[list[int]]:
    yellows = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    ]
    if not yellows:
        raise ValueError("grid has no yellow template cells")
    row_lo = min(row for row, _ in yellows)
    row_hi = max(row for row, _ in yellows)
    col_lo = min(col for _, col in yellows)
    col_hi = max(col for _, col in yellows)
    return [
        [
            grid[row][col] if grid[row][col] in (4, 6) else -1
            for col in range(col_lo, col_hi + 1)
        ]
        for row in range(row_lo, row_hi + 1)
    ]


def apply_python(
    grid: list[list[int]], orientation_scope: str = "dihedral"
) -> list[list[int]]:
    """Independent Python mirror of both proposed rule settings."""
    _validate_scope(orientation_scope)
    height, width = _validate_grid(grid)
    template = _template_from_yellow_bbox(grid)
    variants = _orientations(template)
    if orientation_scope == "rotations":
        variants = variants[:4]

    output = [row[:] for row in grid]
    for candidate in variants:
        template_height = len(candidate)
        template_width = len(candidate[0])
        row_stop = min(height, height + 2 - template_height)
        col_stop = min(width, width + 2 - template_width)
        for row in range(0, row_stop):
            for col in range(0, col_stop):
                magenta_hits = 0
                mismatch = False
                for tr in range(template_height):
                    for tc in range(template_width):
                        grid_row, grid_col = row + tr, col + tc
                        if not (0 <= grid_row < height and 0 <= grid_col < width):
                            continue
                        template_value = candidate[tr][tc]
                        grid_value = grid[grid_row][grid_col]
                        if template_value == 6:
                            if grid_value == 6:
                                magenta_hits += 1
                            else:
                                mismatch = True
                        elif template_value == 4 and grid_value == 6:
                            mismatch = True
                if mismatch or magenta_hits < 2:
                    continue
                for tr in range(template_height):
                    for tc in range(template_width):
                        grid_row, grid_col = row + tr, col + tc
                        if (
                            0 <= grid_row < height
                            and 0 <= grid_col < width
                            and candidate[tr][tc] == 4
                        ):
                            output[grid_row][grid_col] = 4
    return output


def _grid_digest(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _candidate_spec(seed: int, pair_index: int, attempt: int) -> tuple[int, int, str]:
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:{pair_index}:{attempt}:input".encode()
    ).digest()
    generator_seed = int.from_bytes(digest[:8], "big") % (2**31)
    sample_index = int.from_bytes(digest[8:16], "big") % 1_000_000
    difficulty = _DIFFICULTIES[digest[16] % len(_DIFFICULTIES)]
    return generator_seed, sample_index, difficulty


def _distinguishing_pair(
    generator,
    *,
    seed: int,
    pair_index: int,
    selected_scope: str,
    used_inputs: set[str],
) -> dict[str, Any]:
    """Return one lawful pair where both settings fire and disagree."""
    for attempt in range(_MAX_CANDIDATES_PER_PAIR):
        generator_seed, sample_index, difficulty = _candidate_spec(
            seed, pair_index, attempt
        )
        try:
            grid = generator.generate(
                generator_seed,
                sample_index,
                difficulty=difficulty,
            )
        except ValueError:
            continue
        if generator.self_check(grid):
            continue
        digest = _grid_digest(grid)
        if digest in used_inputs:
            continue
        rotation_output = apply_python(grid, "rotations")
        dihedral_output = apply_python(grid, "dihedral")
        if rotation_output == grid or dihedral_output == grid:
            continue
        if rotation_output == dihedral_output:
            continue
        used_inputs.add(digest)
        outputs = {
            "dihedral": dihedral_output,
            "rotations": rotation_output,
        }
        return {
            "input": grid,
            "output": outputs[selected_scope],
            "generator_seed": generator_seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "candidate_attempt": attempt,
            "input_sha256": digest,
            "output_sha256_by_setting": {
                scope: _grid_digest(output) for scope, output in outputs.items()
            },
        }
    raise RuntimeError(
        "could not find a unique lawful orientation-scope witness for "
        f"seed={seed}, pair_index={pair_index} after "
        f"{_MAX_CANDIDATES_PER_PAIR} candidates"
    )


def generate_episode(
    seed: int,
    *,
    orientation_scope: str | object = _AUTO,
    root: Path | str = ROOT,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode with one fixed hidden orientation scope."""
    _validate_seed(seed)
    _validate_counts(demo_count, query_count)
    if orientation_scope is _AUTO:
        selected = choose_orientation_scope(seed)
    else:
        _validate_scope(orientation_scope)
        selected = orientation_scope

    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    used_inputs: set[str] = set()
    pairs = [
        _distinguishing_pair(
            generator,
            seed=seed,
            pair_index=index,
            selected_scope=selected,
            used_inputs=used_inputs,
        )
        for index in range(demo_count + query_count)
    ]
    program = racket_program(selected, root=root)
    return {
        "schema": "d09fae8197f6-orientation-scope-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": {"orientation_scope": selected},
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "source": {
            "generator_path": str(
                Path(generator_path).resolve().relative_to(Path(root).resolve())
            ),
            "generator_sha256": generator_sha,
            "generator_rule_hash": generator.RULE_HASH,
        },
        "constraints": {
            "input_grammar_changed": False,
            "both_settings_stamp_every_pair": True,
            "every_pair_distinguishes_settings": True,
            "max_candidates_per_pair": _MAX_CANDIDATES_PER_PAIR,
        },
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Mask hidden settings, source metadata, programs, and query answers."""
    return {
        "train": [
            {
                "input": deepcopy(pair["input"]),
                "output": deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def public_filename(episode: dict[str, Any]) -> str:
    """Return an opaque ID derived only from exact visible challenge bytes."""
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--orientation-scope", choices=PARAMETERS["orientation_scope"]["allowed"])
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    episode = generate_episode(
        args.seed,
        orientation_scope=(
            _AUTO if args.orientation_scope is None else args.orientation_scope
        ),
        demo_count=args.demo_count,
        query_count=args.query_count,
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
