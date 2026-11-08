#!/usr/bin/env python3
"""Proposed episode-level rule variants for ARC task 195dfcc5b541.

The production generator and selected canonical Racket authority remain unchanged.
This task-local prototype keeps the same stencil/copy reasoning while varying two
small rule choices once per complete episode:

* ``reflection_mode``: rotations only, or the canonical dihedral orbit.
* ``column_order``: greedily resolve same-row overlapping matches left-to-right
  (canonical) or right-to-left.

Inputs are selected-generator draws augmented with one isolated 2x4 overlap motif.
Every retained pair distinguishes all four settings.  Labels in retained evidence
are verified by the matching Racket programs; ``solve`` is an independent mirror.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "195dfcc5b541"
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_RULE_HASH = "22e420574f26"
REFLECTION_MODES = ("dihedral", "rotations_only")
COLUMN_ORDERS = ("left_to_right", "right_to_left")
DEFAULT_SETTING = ("dihedral", "left_to_right")
SETTINGS = (
    ("dihedral", "left_to_right"),
    ("dihedral", "right_to_left"),
    ("rotations_only", "left_to_right"),
    ("rotations_only", "right_to_left"),
)
DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4
MAX_COUNT = 16
MAX_CANDIDATE_ATTEMPTS = 512

_DIHEDRAL_VARIANTS = """(define variants
                   (list (list 0 base)
                         (list 0 r1)
                         (list 0 r2)
                         (list 0 r3)
                         (list 1 (flip base))
                         (list 1 (flip r1))
                         (list 1 (flip r2))
                         (list 1 (flip r3))))"""
_ROTATION_VARIANTS = """(define variants
                   (list (list 0 base)
                         (list 0 r1)
                         (list 0 r2)
                         (list 0 r3)))"""
_LEFT_ORDER_FRAGMENT = "(else (< (third a) (third b)))"
_RIGHT_ORDER_FRAGMENT = "(else (> (third a) (third b)))"
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _validate_choice(name: str, value: Any, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    return value


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer (not bool)")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not 1 <= value <= MAX_COUNT:
        raise ValueError(
            f"{name} must be an exact integer in 1..{MAX_COUNT} (not bool)"
        )
    return value


def normalized_source_hash(source: str) -> str:
    """Repository-style 12-hex digest of whitespace-normalized Racket text."""
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        source = row["program_solution"]
        digest = normalized_source_hash(source)
        if digest != CANONICAL_RULE_HASH:
            raise RuntimeError(
                f"canonical rule hash drift: {digest} != {CANONICAL_RULE_HASH}"
            )
        if source.count(_DIHEDRAL_VARIANTS) != 1:
            raise RuntimeError("canonical variants block is missing or ambiguous")
        if source.count(_LEFT_ORDER_FRAGMENT) != 1:
            raise RuntimeError("canonical column-order fragment is missing or ambiguous")
        return source
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


@lru_cache(maxsize=1)
def selected_generator():
    """Return the selected generator module, exact path, and source SHA-256."""
    return load_selected_generator(TASK_ID, root=find_root(__file__))


def program_for(
    reflection_mode: str = DEFAULT_SETTING[0],
    column_order: str = DEFAULT_SETTING[1],
) -> str:
    """Return exact executable Racket for one bounded prototype setting."""
    reflection_mode = _validate_choice(
        "reflection_mode", reflection_mode, REFLECTION_MODES
    )
    column_order = _validate_choice("column_order", column_order, COLUMN_ORDERS)
    source = _canonical_program()
    if reflection_mode == "rotations_only":
        source = source.replace(_DIHEDRAL_VARIANTS, _ROTATION_VARIANTS, 1)
    if column_order == "right_to_left":
        source = source.replace(_LEFT_ORDER_FRAGMENT, _RIGHT_ORDER_FRAGMENT, 1)
    return source


def normalized_program_hash(
    reflection_mode: str = DEFAULT_SETTING[0],
    column_order: str = DEFAULT_SETTING[1],
) -> str:
    return normalized_source_hash(program_for(reflection_mode, column_order))


def exact_program_hash(
    reflection_mode: str = DEFAULT_SETTING[0],
    column_order: str = DEFAULT_SETTING[1],
) -> str:
    return hashlib.sha256(
        program_for(reflection_mode, column_order).encode()
    ).hexdigest()


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _norm(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot normalize an empty shape")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(cells):
    return _norm((col, -row) for row, col in cells)


def _reflect(cells):
    return _norm((row, -col) for row, col in cells)


def _rotations(cells):
    shape = _norm(cells)
    result = []
    for _ in range(4):
        result.append(shape)
        shape = _rotate(shape)
    return tuple(result)


def _bbox(cells):
    shape = _norm(cells)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _components_8(grid: list[list[int]], color: int):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                point = stack.pop()
                component.append(point)
                for dr, dc in _NEIGHBORS_8:
                    nxt = point[0] + dr, point[1] + dc
                    if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                        continue
                    if nxt in seen or grid[nxt[0]][nxt[1]] != color:
                        continue
                    seen.add(nxt)
                    stack.append(nxt)
            result.append(component)
    return result


def solve(
    grid: list[list[int]],
    *,
    reflection_mode: str = DEFAULT_SETTING[0],
    column_order: str = DEFAULT_SETTING[1],
) -> list[list[int]]:
    """Independent Python mirror of one prototype setting."""
    reflection_mode = _validate_choice(
        "reflection_mode", reflection_mode, REFLECTION_MODES
    )
    column_order = _validate_choice("column_order", column_order, COLUMN_ORDERS)
    height, width = _validate_grid(grid)
    matches = []
    for component in _components_8(grid, 8):
        base = _norm(component)
        rotations = _rotations(base)
        variants = [(0, shape) for shape in rotations]
        if reflection_mode == "dihedral":
            variants.extend((1, _reflect(shape)) for shape in rotations)
        # The canonical program conses each candidate before a stable key sort.
        for flip_rank, shape in variants:
            shape_h, shape_w = _bbox(shape)
            for row0 in range(height - shape_h + 1):
                for col0 in range(width - shape_w + 1):
                    cells = tuple(
                        (row0 + row, col0 + col) for row, col in shape
                    )
                    if all(grid[row][col] == 3 for row, col in cells):
                        matches.insert(0, (flip_rank, row0, col0, cells))
    if column_order == "left_to_right":
        matches.sort(key=lambda item: (item[0], item[1], item[2]))
    else:
        matches.sort(key=lambda item: (item[0], item[1], -item[2]))
    output = deepcopy(grid)
    used = set()
    for _, _, _, cells in matches:
        if used.intersection(cells):
            continue
        used.update(cells)
        for row, col in cells:
            output[row][col] = 8
    return output


def select_setting(seed: int) -> tuple[str, str]:
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|symmetry-order|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return SETTINGS[digest[0] % len(SETTINGS)]


def _resolve_setting(
    seed: int,
    reflection_mode: str | None,
    column_order: str | None,
) -> tuple[str, str]:
    selected_reflection, selected_order = select_setting(seed)
    if reflection_mode is not None:
        selected_reflection = _validate_choice(
            "reflection_mode", reflection_mode, REFLECTION_MODES
        )
    if column_order is not None:
        selected_order = _validate_choice("column_order", column_order, COLUMN_ORDERS)
    return selected_reflection, selected_order


def _grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode()
    ).hexdigest()


def _candidate_numbers(seed: int, pair_index: int, attempt: int) -> tuple[int, int]:
    digest = hashlib.sha256(
        (
            f"{TASK_ID}|teaching-input|{PROTOTYPE_VERSION}|"
            f"{seed}|{pair_index}|{attempt}"
        ).encode()
    ).digest()
    generator_seed = int.from_bytes(digest[:8], "big") & 0x7FFFFFFF
    sample_index = int.from_bytes(digest[8:16], "big") & 0x7FFFFFFF
    return generator_seed, sample_index


def _isolated_overlap_patch(
    grid: list[list[int]], seed: int, pair_index: int, attempt: int
) -> tuple[int, int] | None:
    """Choose a 2x4 patch whose one-cell halo contains no existing 3 or 8."""
    height, width = len(grid), len(grid[0])
    candidates = []
    for row0 in range(1, height - 2):
        for col0 in range(1, width - 4):
            halo = (
                grid[row][col]
                for row in range(row0 - 1, row0 + 3)
                for col in range(col0 - 1, col0 + 5)
            )
            if all(value not in (3, 8) for value in halo):
                candidates.append((row0, col0))
    if not candidates:
        return None
    digest = hashlib.sha256(
        f"{TASK_ID}|patch|{seed}|{pair_index}|{attempt}".encode()
    ).digest()
    return candidates[int.from_bytes(digest[:8], "big") % len(candidates)]


def _all_outputs(grid: list[list[int]]) -> dict[tuple[str, str], list[list[int]]]:
    return {
        setting: solve(
            grid,
            reflection_mode=setting[0],
            column_order=setting[1],
        )
        for setting in SETTINGS
    }


def _build_teaching_input(
    seed: int,
    pair_index: int,
    used_hashes: set[str],
) -> tuple[list[list[int]], dict[str, Any]]:
    generator, _, _ = selected_generator()
    bands = ("easy", "medium", "hard", None)
    for attempt in range(MAX_CANDIDATE_ATTEMPTS):
        generator_seed, sample_index = _candidate_numbers(seed, pair_index, attempt)
        copy_count = 2 + ((pair_index + attempt) % 3)
        difficulty = bands[(pair_index + attempt) % len(bands)]
        grid = generator.generate(
            generator_seed,
            sample_index,
            difficulty=difficulty,
            grid_h=18,
            grid_w=18,
            shape_variant=0,
            copy_count=copy_count,
        )
        components = _components_8(grid, 8)
        if len(components) != 1 or _bbox(components[0]) != (2, 3):
            continue
        patch = _isolated_overlap_patch(grid, seed, pair_index, attempt)
        if patch is None:
            continue
        row0, col0 = patch
        candidate = deepcopy(grid)
        for row in range(row0, row0 + 2):
            for col in range(col0, col0 + 4):
                candidate[row][col] = 3
        input_hash = _grid_hash(candidate)
        if input_hash in used_hashes:
            continue
        if generator.self_check(candidate):
            continue
        outputs = _all_outputs(candidate)
        if len({_grid_hash(output) for output in outputs.values()}) != len(SETTINGS):
            continue
        return candidate, {
            "generator_seed": generator_seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "copy_count": copy_count,
            "accepted_attempt": attempt,
            "input_sha256": input_hash,
            "overlap_patch": {
                "row": row0,
                "column": col0,
                "height": 2,
                "width": 4,
            },
            "all_setting_outputs_distinct": True,
            "setting_output_sha256": {
                f"{setting[0]}__{setting[1]}": _grid_hash(output)
                for setting, output in outputs.items()
            },
        }
    raise RuntimeError(
        f"could not construct teaching-rich input {pair_index} within "
        f"{MAX_CANDIDATE_ATTEMPTS} attempts"
    )


def generate_episode(
    seed: int,
    *,
    reflection_mode: str | None = None,
    column_order: str | None = None,
    n_train: int = DEFAULT_N_TRAIN,
    n_test: int = DEFAULT_N_TEST,
) -> dict[str, Any]:
    """Build one deterministic fixed-setting episode with distinct rich inputs."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    setting = _resolve_setting(seed, reflection_mode, column_order)
    generator, source_path, source_sha256 = selected_generator()
    root = find_root(__file__)
    program = program_for(*setting)

    used_hashes: set[str] = set()
    pairs = []
    provenance = []
    for pair_index in range(n_train + n_test):
        grid, metadata = _build_teaching_input(seed, pair_index, used_hashes)
        used_hashes.add(metadata["input_sha256"])
        output = solve(
            grid,
            reflection_mode=setting[0],
            column_order=setting[1],
        )
        pairs.append({"input": grid, "output": output})
        provenance.append(metadata)

    return {
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "private": {
            "seed": seed,
            "setting": {
                "reflection_mode": setting[0],
                "column_order": setting[1],
            },
            "parameter_contract": {
                "reflection_mode": {
                    "values": list(REFLECTION_MODES),
                    "default": DEFAULT_SETTING[0],
                },
                "column_order": {
                    "values": list(COLUMN_ORDERS),
                    "default": DEFAULT_SETTING[1],
                },
            },
            "n_train": n_train,
            "n_test": n_test,
            "input_constraint": (
                "selected-generator shape_variant=0 input with a horizontal 2x3 "
                "stencil, canonical reflection witness, and one isolated 2x4 "
                "color-3 overlap motif; all four setting outputs must be distinct"
            ),
            "generator_path": str(Path(source_path).relative_to(root)),
            "generator_sha256": source_sha256,
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "program": program,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "pairs": provenance,
        },
    }


def lesson_checks(episode: dict[str, Any]) -> dict[str, Any]:
    """Check bounded setting identifiability using demonstrations only."""
    try:
        setting_dict = episode["private"]["setting"]
        setting = (
            setting_dict["reflection_mode"],
            setting_dict["column_order"],
        )
        demos = episode["train"]
        queries = episode["test"]
    except (KeyError, TypeError) as error:
        raise ValueError("episode is missing private setting/train/test data") from error
    if setting not in SETTINGS or not demos or not queries:
        raise ValueError("episode must use a known setting and nonempty train/test")

    rivals = []
    for rival in SETTINGS:
        if rival == setting:
            continue
        fits_all_demos = all(
            solve(
                pair["input"],
                reflection_mode=rival[0],
                column_order=rival[1],
            )
            == pair["output"]
            for pair in demos
        )
        rivals.append(
            {
                "setting": {
                    "reflection_mode": rival[0],
                    "column_order": rival[1],
                },
                "fits_all_demos": fits_all_demos,
            }
        )

    query_rows = []
    for index, pair in enumerate(queries):
        changing_fitted_rivals = []
        differing_rivals = []
        for row in rivals:
            rival = (
                row["setting"]["reflection_mode"],
                row["setting"]["column_order"],
            )
            rival_output = solve(
                pair["input"],
                reflection_mode=rival[0],
                column_order=rival[1],
            )
            differs = rival_output != pair["output"]
            if differs:
                differing_rivals.append(row["setting"])
            if row["fits_all_demos"] and differs:
                changing_fitted_rivals.append(row["setting"])
        query_rows.append(
            {
                "index": index,
                "identifiable": not changing_fitted_rivals,
                "setting_sensitive": len(differing_rivals) == len(SETTINGS) - 1,
                "changing_fitted_rivals": changing_fitted_rivals,
            }
        )

    return {
        "setting": setting_dict,
        "rivals": rivals,
        "demos_refute_all_rivals": all(not row["fits_all_demos"] for row in rivals),
        "queries": query_rows,
        "all_queries_identifiable": all(row["identifiable"] for row in query_rows),
        "all_queries_setting_sensitive": all(
            row["setting_sensitive"] for row in query_rows
        ),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and answer-masked query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)
