#!/usr/bin/env python3
"""Task-local episode rule variants for hollow-frame extraction.

The production generator and canonical Racket authority remain unchanged.  This
prototype keeps the same object filtering, top-left range comparison, spatial
ordering, and outline normalization, while selecting two small rule parameters
once per episode: normalized token side length and the orientation used on an
exact row/column-range tie.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_id,
)


TASK_ID = "31b8bedd699a"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not selected or production-approved"
TOKEN_SIZES = (3, 4, 5)
DEFAULT_TOKEN_SIZE = 4
TIE_POLICIES = ("horizontal", "vertical")
DEFAULT_TIE_POLICY = "horizontal"
PARAMETERS = {
    "token_size": {
        "allowed": TOKEN_SIZES,
        "default": DEFAULT_TOKEN_SIZE,
        "selected_once_per_episode": True,
    },
    "tie_policy": {
        "allowed": TIE_POLICIES,
        "default": DEFAULT_TIE_POLICY,
        "selected_once_per_episode": True,
    },
}
ALL_SETTINGS = tuple(
    (token_size, tie_policy)
    for token_size in TOKEN_SIZES
    for tie_policy in TIE_POLICIES
)
MAX_AUTHORING_COUNT = 64
_DEMO_ROLES = ("tie", "vertical", "horizontal")
_QUERY_ROLES = ("vertical", "horizontal", "tie", "vertical")
_RESIDUES = {
    "vertical": (0, 1),
    "horizontal": (2, 3),
    "tie": (4, 5),
}
_CONTROLS = {
    "vertical": (
        (21, 16, 3, 0),
        (26, 19, 4, 2),
        (30, 30, 5, 3),
        (24, 18, 3, 1),
    ),
    "horizontal": (
        (18, 17, 2, 1),
        (20, 27, 4, 2),
        (23, 30, 5, 3),
        (19, 25, 3, 0),
    ),
    "tie": (
        (22, 21, 3, 2),
        (25, 25, 4, 1),
        (28, 26, 5, 3),
        (19, 20, 2, 0),
    ),
}


def _root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError(f"seed must be a nonnegative exact integer, got {seed!r}")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not 1 <= value <= MAX_AUTHORING_COUNT:
        raise ValueError(
            f"{name} must be an exact integer in 1..{MAX_AUTHORING_COUNT}, got {value!r}"
        )
    return value


def _validate_token_size(value: Any) -> int:
    if type(value) is not int or value not in TOKEN_SIZES:
        raise ValueError(
            f"token_size must be one of the exact integers {TOKEN_SIZES}, got {value!r}"
        )
    return value


def _validate_tie_policy(value: Any) -> str:
    if type(value) is not str or value not in TIE_POLICIES:
        raise ValueError(f"tie_policy must be one of {TIE_POLICIES}, got {value!r}")
    return value


def canonical_record(*, root: Path | str | None = None) -> dict[str, Any]:
    """Return the original training row, not its augmented duplicate."""
    matches = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                row.get("task_id") == TASK_ID
                and row.get("content_hash") == TASK_ID
                and row.get("source") == "training"
                and row.get("parent_hash") is None
            ):
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(
            f"expected one original canonical row for {TASK_ID}, found {len(matches)}"
        )
    return matches[0]


def _replace_count(text: str, old: str, new: str, expected: int) -> str:
    count = text.count(old)
    if count != expected:
        raise ValueError(
            f"canonical rule changed: expected {expected} occurrence(s) of {old!r}, found {count}"
        )
    return text.replace(old, new)


def racket_program(
    token_size: Any = DEFAULT_TOKEN_SIZE,
    tie_policy: Any = DEFAULT_TIE_POLICY,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact canonical Racket or one bounded parameter variant."""
    size = _validate_token_size(token_size)
    policy = _validate_tie_policy(tie_policy)
    canonical = canonical_record(root=root)["program_solution"]
    if size == DEFAULT_TOKEN_SIZE and policy == DEFAULT_TIE_POLICY:
        return canonical

    program = canonical
    if policy == "vertical":
        program = _replace_count(
            program,
            "(vertical (> row-range col-range))",
            "(vertical (>= row-range col-range))",
            1,
        )
    else:
        if program.count("(vertical (> row-range col-range))") != 1:
            raise ValueError("canonical rule changed at the tie-comparison site")

    if size != DEFAULT_TOKEN_SIZE:
        edge = size - 1
        program = _replace_count(
            program,
            "(build-grid (* n 4)\n                           4",
            f"(build-grid (* n {size})\n                           {size}",
            1,
        )
        program = _replace_count(
            program,
            "(build-grid 4\n                           (* n 4)",
            f"(build-grid {size}\n                           (* n {size})",
            1,
        )
        for axis in ("r", "c"):
            program = _replace_count(
                program,
                f"(quotient {axis} 4)",
                f"(quotient {axis} {size})",
                1,
            )
            program = _replace_count(
                program,
                f"(remainder {axis} 4)",
                f"(remainder {axis} {size})",
                1,
            )
        program = _replace_count(program, "(= lr 3)", f"(= lr {edge})", 2)
        program = _replace_count(program, "(= lc 3)", f"(= lc {edge})", 2)
    return program


def select_parameters(seed: Any) -> dict[str, Any]:
    """Select one complete setting deterministically exactly once per episode."""
    seed = _validate_seed(seed)
    token_size, tie_policy = ALL_SETTINGS[seed % len(ALL_SETTINGS)]
    return {"token_size": token_size, "tie_policy": tie_policy}


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must each be in 1..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return height, width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    objects = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            cells = {(row, col)}
            seen.add((row, col))
            while pending:
                current_row, current_col = pending.pop()
                for neighbor in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    rr, cc = neighbor
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and neighbor not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add(neighbor)
                        cells.add(neighbor)
                        pending.append(neighbor)
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            bottom = max(rr for rr, _ in cells)
            right = max(cc for _, cc in cells)
            objects.append(
                {
                    "top": top,
                    "left": left,
                    "bottom": bottom,
                    "right": right,
                    "color": color,
                    "cells": cells,
                    "frame": len(cells) < (bottom - top + 1) * (right - left + 1),
                }
            )
    return objects


def _frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    return [obj for obj in _components(grid) if obj["frame"]]


def _axis_relation(grid: list[list[int]]) -> str:
    frames = _frames(grid)
    if not frames:
        raise ValueError("rule requires at least one nonsolid component")
    row_range = max(obj["top"] for obj in frames) - min(obj["top"] for obj in frames)
    col_range = max(obj["left"] for obj in frames) - min(obj["left"] for obj in frames)
    if row_range > col_range:
        return "vertical"
    if col_range > row_range:
        return "horizontal"
    return "tie"


def _pack(frames: Iterable[dict[str, Any]], token_size: int, vertical: bool) -> list[list[int]]:
    frames = list(frames)
    if not frames:
        return [[0]]
    height = token_size * len(frames) if vertical else token_size
    width = token_size if vertical else token_size * len(frames)
    output = [[0] * width for _ in range(height)]
    edge = token_size - 1
    for index, frame in enumerate(frames):
        row_offset = token_size * index if vertical else 0
        col_offset = 0 if vertical else token_size * index
        for local_row in range(token_size):
            for local_col in range(token_size):
                if local_row in (0, edge) or local_col in (0, edge):
                    output[row_offset + local_row][col_offset + local_col] = frame["color"]
    return output


def axis_intermediate(
    grid: list[list[int]],
    tie_policy: Any = DEFAULT_TIE_POLICY,
) -> dict[str, Any]:
    """Stage A: derive the input-dependent axis consumed by spatial ordering."""
    policy = _validate_tie_policy(tie_policy)
    frames = _frames(grid)
    if not frames:
        raise ValueError("rule requires at least one nonsolid component")
    row_range = max(obj["top"] for obj in frames) - min(obj["top"] for obj in frames)
    col_range = max(obj["left"] for obj in frames) - min(obj["left"] for obj in frames)
    vertical = row_range > col_range or (
        row_range == col_range and policy == "vertical"
    )
    return {
        "row_range": row_range,
        "col_range": col_range,
        "relation": (
            "vertical" if row_range > col_range
            else "horizontal" if col_range > row_range
            else "tie"
        ),
        "tie_policy": policy,
        "axis": "vertical" if vertical else "horizontal",
    }


def apply_with_axis(
    grid: list[list[int]],
    token_size: Any,
    axis: Any,
) -> list[list[int]]:
    """Stage B: sort and normalize using the supplied Stage-A axis."""
    size = _validate_token_size(token_size)
    if type(axis) is not str or axis not in ("horizontal", "vertical"):
        raise ValueError("axis must be horizontal or vertical")
    frames = _frames(grid)
    if not frames:
        return [[0]]
    vertical = axis == "vertical"
    coordinate = "top" if vertical else "left"
    return _pack(sorted(frames, key=lambda obj: obj[coordinate]), size, vertical)


def apply_python(
    grid: list[list[int]],
    token_size: Any = DEFAULT_TOKEN_SIZE,
    tie_policy: Any = DEFAULT_TIE_POLICY,
) -> list[list[int]]:
    """Independent Python mirror; retained labels are executed in Racket."""
    state = axis_intermediate(grid, tie_policy)
    return apply_with_axis(grid, token_size, state["axis"])


def known_distribution_shortcut(
    grid: list[list[int]], token_size: Any = DEFAULT_TOKEN_SIZE
) -> list[list[int]]:
    """Reproduce the open CR1 axis shortcut while keeping all other steps correct."""
    size = _validate_token_size(token_size)
    frames = _frames(grid)
    if not frames:
        return [[0]]
    vertical = len(frames) == 2 and len(grid[0]) != 24
    coordinate = "top" if vertical else "left"
    return _pack(sorted(frames, key=lambda obj: obj[coordinate]), size, vertical)


def _roles(count: int, pattern: tuple[str, ...]) -> list[str]:
    return [pattern[index % len(pattern)] for index in range(count)]


def _candidate(
    generator,
    *,
    seed: int,
    pair_index: int,
    role: str,
    role_index: int,
    attempt: int,
) -> dict[str, Any]:
    controls = _CONTROLS[role][role_index % len(_CONTROLS[role])]
    grid_h, grid_w, n_frames, n_solids = controls
    residues = _RESIDUES[role]
    residue = residues[(role_index + attempt) % len(residues)]
    sample_index = 6 * (seed * 257 + pair_index * 37 + attempt) + residue
    generator_seed = (
        (seed + 1) * 1_000_003 + pair_index * 104_729 + attempt * 13_007
    ) & 0x7FFFFFFF
    grid = generator.generate(
        generator_seed,
        sample_index,
        grid_h=grid_h,
        grid_w=grid_w,
        n_frames=n_frames,
        n_solids=n_solids,
    )
    return {
        "input": grid,
        "profile": role,
        "generator_seed": generator_seed,
        "sample_index": sample_index,
        "controls": {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_frames": n_frames,
            "n_solids": n_solids,
        },
    }


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def generate_episode(
    seed: Any,
    *,
    token_size: Any | None = None,
    tie_policy: Any | None = None,
    demo_count: Any = 3,
    query_count: Any = 4,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build a deterministic fixed-setting episode with independent counts."""
    seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    selected = select_parameters(seed)
    if token_size is not None:
        selected["token_size"] = _validate_token_size(token_size)
    if tie_policy is not None:
        selected["tie_policy"] = _validate_tie_policy(tie_policy)

    source_root = _root(root)
    generator, _, _ = load_selected_generator(TASK_ID, root=source_root)
    roles = [*_roles(demos, _DEMO_ROLES), *_roles(queries, _QUERY_ROLES)]
    role_counts = {role: 0 for role in _RESIDUES}
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts_per_pair = 32

    for pair_index, role in enumerate(roles):
        role_index = role_counts[role]
        role_counts[role] += 1
        for attempt in range(max_attempts_per_pair):
            candidate = _candidate(
                generator,
                seed=seed,
                pair_index=pair_index,
                role=role,
                role_index=role_index,
                attempt=attempt,
            )
            grid = candidate["input"]
            key = _grid_key(grid)
            if key in seen:
                continue
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError(
                    f"selected generator emitted an invalid parametric input: {errors}"
                )
            actual_role = _axis_relation(grid)
            if actual_role != role:
                raise AssertionError(
                    f"requested {role} input but sampled {actual_role}: {candidate}"
                )
            seen.add(key)
            rows.append(
                {
                    **candidate,
                    "output": apply_python(
                        grid, selected["token_size"], selected["tie_policy"]
                    ),
                }
            )
            break
        else:
            raise RuntimeError(
                f"could not sample a distinct {role} input for pair {pair_index} "
                f"within {max_attempts_per_pair} attempts"
            )

    episode = {
        "schema": "31b8bedd699a-token-size-tie-policy-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": selected,
        "program": racket_program(
            selected["token_size"], selected["tie_policy"], root=source_root
        ),
        "train": rows[:demos],
        "test": rows[demos:],
    }
    errors = episode_errors(episode, root=source_root)
    if errors:
        raise AssertionError(f"constructed invalid episode: {errors}")
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project only visible demonstrations and unlabeled query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_challenge_id(public_challenge(episode))}.json"


def episode_errors(
    episode: Any, *, root: Path | str | None = None
) -> list[str]:
    """Check fixed parameters, source domain, labels, and declared rivals."""
    if not isinstance(episode, dict):
        return ["episode must be a dictionary"]
    errors: list[str] = []
    parameter = episode.get("parameter")
    if not isinstance(parameter, dict):
        return ["episode parameter must be a dictionary"]
    try:
        size = _validate_token_size(parameter.get("token_size"))
        policy = _validate_tie_policy(parameter.get("tie_policy"))
    except ValueError as error:
        return [str(error)]
    if episode.get("parameter_draw_count") != 1:
        errors.append("parameter must be selected exactly once per episode")
    try:
        expected_program = racket_program(size, policy, root=root)
    except (ValueError, FileNotFoundError) as error:
        errors.append(f"could not materialize selected program: {error}")
        expected_program = None
    if expected_program is not None and episode.get("program") != expected_program:
        errors.append("episode program does not match the selected parameter tuple")

    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not train:
        errors.append("episode needs at least one demonstration")
        train = []
    if type(test) is not list or not test:
        errors.append("episode needs at least one query")
        test = []
    source_root = _root(root)
    try:
        generator, _, _ = load_selected_generator(TASK_ID, root=source_root)
    except Exception as error:  # Preserve a useful verifier diagnostic.
        errors.append(f"could not load selected generator: {type(error).__name__}: {error}")
        generator = None

    seen: set[str] = set()
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            label = f"{split_name}[{index}]"
            if not isinstance(pair, dict):
                errors.append(f"{label} must be a dictionary")
                continue
            try:
                key = _grid_key(pair["input"])
                expected_output = apply_python(pair["input"], size, policy)
            except (KeyError, ValueError) as error:
                errors.append(f"{label} has an invalid input: {error}")
                continue
            if key in seen:
                errors.append(f"{label} duplicates an earlier input")
            seen.add(key)
            if pair.get("output") != expected_output:
                errors.append(f"{label} output does not match the selected rule")
            try:
                actual_role = _axis_relation(pair["input"])
            except ValueError as error:
                errors.append(f"{label} has no frame support: {error}")
                continue
            if pair.get("profile") != actual_role:
                errors.append(
                    f"{label} profile {pair.get('profile')!r} does not match {actual_role!r}"
                )
            if generator is not None:
                domain_errors = generator.self_check(pair["input"])
                if domain_errors:
                    errors.append(f"{label} is outside the selected domain: {domain_errors}")

    alternatives = [setting for setting in ALL_SETTINGS if setting != (size, policy)]
    if train:
        for alternative_size, alternative_policy in alternatives:
            if all(
                apply_python(pair["input"], alternative_size, alternative_policy)
                == pair.get("output")
                for pair in train
                if isinstance(pair, dict) and "input" in pair
            ):
                errors.append(
                    "demonstrations do not identify the selected setting against "
                    f"token_size={alternative_size}, tie_policy={alternative_policy}"
                )
    if test:
        for index, pair in enumerate(test):
            if not isinstance(pair, dict) or "input" not in pair:
                continue
            if not any(
                apply_python(pair["input"], alt_size, alt_policy)
                != pair.get("output")
                for alt_size, alt_policy in alternatives
            ):
                errors.append(f"test[{index}] is nondiscriminative across declared settings")
        if not any(
            known_distribution_shortcut(pair["input"], size) != pair.get("output")
            for pair in test
            if isinstance(pair, dict) and "input" in pair
        ):
            errors.append("queries do not refute the known n_frames/canvas-width shortcut")
    return errors
