"""Generator for d62a0e470ae8 — a corner key transforms the largest crop.

The top-left key selects one of four dihedral transforms.  After clearing the
key, the canonical program chooses the unique largest four-connected object,
takes its tight bounding-box crop, and transforms that crop.  Smaller, same-
color distractor objects make the size selection causal without changing the
three-color canonical palette.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "d62a0e470ae8"
TASK_ID = "d62a0e470ae8"
VERSION = "3.0.0"
RULE_HASH = "43fde3a5fa41"

SUMMARY = (
    "A zero-background grid has a transform key at (0,0), one asymmetric "
    "main object, and zero to three strictly smaller disconnected objects in "
    "the same foreground color. Clear the key, select the unique largest "
    "four-connected object, crop its bounding box, then apply key 1=clockwise "
    "quarter-turn, 2=left-right reflection, 3=top-bottom reflection, or "
    "4=half-turn. The four-example schedule covers all keys and all "
    "distractor counts, so both transform dispatch and largest-object "
    "selection are observable."
)

INVARIANTS = [
    "background is 0 and (0,0) is a key in 1..4",
    "all non-key foreground cells share one color distinct from the key",
    "there is one unique largest four-connected object of size 5..9",
    "there are 0..3 strictly smaller objects, all outside the main bounding box",
    "the selected transform changes the main crop",
]

GRID_PROFILES = ("7x9", "8x10", "9x9", "9x11", "10x12", "11x13")
_PROFILE_DIMS = {
    "7x9": (7, 9),
    "8x10": (8, 10),
    "9x9": (9, 9),
    "9x11": (9, 11),
    "10x12": (10, 12),
    "11x13": (11, 13),
}
_PROFILE_SCHEDULE = ("7x9", "8x10", "9x9", "9x11", "10x12", "11x13")

AXES = {
    "grid_profile": {
        "type": "str",
        "default": "sample_index schedule, canonical-heavy first three residues",
        "valid": "7x9|8x10|9x9|9x11|10x12|11x13",
    },
    "key": {"type": "int", "default": "1 + sample_index mod 4", "valid": "1..4"},
    "main_size": {
        "type": "int",
        "default": "5 + sample_index mod 5",
        "valid": "5..9",
    },
    "n_distractors": {
        "type": "int",
        "default": "sample_index mod 4",
        "valid": "0..3",
    },
}

# Four demos are enough to show every key and every distractor-count residue.
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.90

# Every template is a connected, normalized polyomino with a full eight-element
# dihedral orbit.  This keeps every selected transform visible.  Multiple
# templates per size preserve shape diversity without rejection sampling.
_MAIN_TEMPLATES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (1, 4)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2), (1, 3)),
    ),
    9: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 4)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
}

_DISTRACTOR_TEMPLATES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    2: (((0, 0), (0, 1)), ((0, 0), (1, 0))),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _orient(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    """Apply one of eight dihedral orientations and normalize coordinates."""
    reflected = code >= 4
    turns = code % 4
    result = []
    for r, c in cells:
        x, y = r, -c if reflected else c
        for _ in range(turns):
            x, y = y, -x
        result.append((x, y))
    return _normalize(result)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _translated(
    cells: Iterable[tuple[int, int]], r0: int, c0: int
) -> tuple[tuple[int, int], ...]:
    return tuple((r0 + r, c0 + c) for r, c in cells)


def _touches(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return True
        if any((r + dr, c + dc) in occupied for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            return True
    return False


def _inside_bbox(cell: tuple[int, int], box: tuple[int, int, int, int]) -> bool:
    r, c = cell
    r1, c1, r2, c2 = box
    return r1 <= r <= r2 and c1 <= c <= c2


def _candidate_origins(
    h: int, w: int, shape: tuple[tuple[int, int], ...], *, interior: bool = True
) -> list[tuple[int, int]]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    r_start = 1 if interior else 0
    c_start = 1 if interior else 0
    return [
        (r, c)
        for r in range(r_start, h - sh + 1)
        for c in range(c_start, w - sw + 1)
    ]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes are {sorted(AXES)}")
    if "grid_profile" in overrides:
        value = overrides["grid_profile"]
        if not isinstance(value, str) or value not in GRID_PROFILES:
            raise ValueError(f"grid_profile must be one of {GRID_PROFILES}, found {value!r}")
    for name, lo, hi in (("key", 1, 4), ("main_size", 5, 9), ("n_distractors", 0, 3)):
        if name not in overrides:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, found {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}, found {value}")


def _schedule_offset(seed: int, label: str, modulus: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{label}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % modulus


def _defaults(seed: int, sample_index: int) -> dict[str, Any]:
    return {
        "grid_profile": _PROFILE_SCHEDULE[
            (sample_index + _schedule_offset(seed, "grid-profile", len(_PROFILE_SCHEDULE)))
            % len(_PROFILE_SCHEDULE)
        ],
        "key": 1 + (sample_index + _schedule_offset(seed, "key", 4)) % 4,
        "main_size": 5 + (sample_index + _schedule_offset(seed, "main-size", 5)) % 5,
        "n_distractors": (
            sample_index + _schedule_offset(seed, "distractors", 4)
        ) % 4,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    _validate_overrides(overrides)
    effective = _defaults(seed, sample_index)
    effective.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("grid_profile", GRID_PROFILES)
    key = ctx.draw_int("key", 1, 4)
    main_size = ctx.draw_int("main_size", 5, 9)
    n_distractors = ctx.draw_int("n_distractors", 0, 3)
    h, w = _PROFILE_DIMS[profile]

    band = difficulty or "default"
    shape_rng = ctx.draw_rng(f"main-shape:{band}")
    color_rng = ctx.draw_rng(f"foreground-color:{band}")
    layout_rng = ctx.draw_rng(f"layout:{band}")
    color = color_rng.choice([value for value in range(1, 10) if value != key])

    templates = list(_MAIN_TEMPLATES[main_size])
    shape_rng.shuffle(templates)
    oriented: list[tuple[tuple[int, int], ...]] = []
    for template in templates:
        codes = list(range(8))
        shape_rng.shuffle(codes)
        oriented.extend(_orient(template, code) for code in codes)

    for main_shape in oriented:
        origins = _candidate_origins(h, w, main_shape)
        layout_rng.shuffle(origins)
        for r0, c0 in origins:
            main_cells = _translated(main_shape, r0, c0)
            main_box = _bbox(main_cells)
            occupied = set(main_cells)
            distractors: list[tuple[tuple[int, int], ...]] = []
            success = True
            for index in range(n_distractors):
                size = 1 + ((sample_index + index) % 3)
                patterns = list(_DISTRACTOR_TEMPLATES[size])
                layout_rng.shuffle(patterns)
                placed = None
                for pattern in patterns:
                    origins2 = _candidate_origins(h, w, pattern)
                    layout_rng.shuffle(origins2)
                    for rr, cc in origins2:
                        cells = _translated(pattern, rr, cc)
                        if any(_inside_bbox(cell, main_box) for cell in cells):
                            continue
                        if _touches(cells, occupied):
                            continue
                        placed = cells
                        break
                    if placed is not None:
                        break
                if placed is None:
                    success = False
                    break
                distractors.append(placed)
                occupied.update(placed)
            if not success:
                continue
            grid = [[0 for _ in range(w)] for _ in range(h)]
            grid[0][0] = key
            for r, c in main_cells:
                grid[r][c] = color
            for cells in distractors:
                for r, c in cells:
                    grid[r][c] = color
            if not self_check(grid):
                return grid
    raise RuntimeError(
        f"constructive layout failed for profile={profile}, main_size={main_size}, "
        f"n_distractors={n_distractors}"
    )


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9, found {value!r}")
                return errors
    return errors


def _components(grid: list[list[int]], *, clear_key: bool = True) -> list[dict[str, Any]]:
    work = [list(row) for row in grid]
    if clear_key:
        work[0][0] = 0
    h, w = len(work), len(work[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = work[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and work[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells), "size": len(cells)})
    return result


def _crop(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    r1, c1, r2, c2 = _bbox(cells)
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _turn_right(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform(grid: list[list[int]], key: int) -> list[list[int]]:
    if key == 1:
        return _turn_right(grid)
    if key == 2:
        return [list(reversed(row)) for row in grid]
    if key == 3:
        return [list(row) for row in reversed(grid)]
    if key == 4:
        return [list(reversed(row)) for row in reversed(grid)]
    return [list(row) for row in grid]


def _predict(
    grid: list[list[int]],
    *,
    selector: str = "largest",
    dispatch: str = "key",
    include_all: bool = False,
) -> list[list[int]]:
    key = grid[0][0]
    clean = [list(row) for row in grid]
    clean[0][0] = 0
    parts = _components(clean, clear_key=False)
    if not parts:
        raise ValueError("no non-key foreground object")
    if include_all:
        cells = tuple((r, c) for r, row in enumerate(clean) for c, value in enumerate(row) if value)
    elif selector == "largest":
        cells = max(parts, key=lambda obj: obj["size"])["cells"]
    elif selector == "smallest":
        cells = min(parts, key=lambda obj: obj["size"])["cells"]
    else:
        raise ValueError(f"unsupported selector {selector!r}")
    crop = _crop(clean, cells)
    chosen = key
    if dispatch == "identity":
        chosen = 0
    elif dispatch == "clockwise":
        chosen = 1
    elif dispatch == "key4_identity":
        chosen = 0 if key == 4 else key
    elif dispatch != "key":
        raise ValueError(f"unsupported dispatch {dispatch!r}")
    return _transform(crop, chosen)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used by tests and semantic competitors."""
    return _predict(grid)


def observe_overrides(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    parts = _components(grid)
    if not parts:
        raise ValueError("cannot observe axes without a foreground object")
    sizes = sorted((obj["size"] for obj in parts), reverse=True)
    return {
        "grid_profile": f"{len(grid)}x{len(grid[0])}",
        "key": grid[0][0],
        "main_size": sizes[0],
        "n_distractors": len(sizes) - 1,
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors
    profile = f"{len(grid)}x{len(grid[0])}"
    if profile not in GRID_PROFILES:
        errors.append(f"grid profile {profile} is outside {GRID_PROFILES}")
    key = grid[0][0]
    if key not in (1, 2, 3, 4):
        errors.append(f"corner key must be in 1..4, found {key!r}")
    parts = _components(grid)
    if not parts:
        errors.append("expected at least one non-key foreground object")
        return errors
    colors = {obj["color"] for obj in parts}
    if len(colors) != 1:
        errors.append(f"all objects must share one foreground color, found {sorted(colors)}")
    elif key in colors:
        errors.append("foreground color must be distinct from the corner key")
    if not 1 <= len(parts) <= 4:
        errors.append(f"expected one main object and 0..3 distractors, found {len(parts)} objects")
    ordered = sorted(parts, key=lambda obj: obj["size"], reverse=True)
    main = ordered[0]
    if not 5 <= main["size"] <= 9:
        errors.append(f"main object size must be in 5..9, found {main['size']}")
    if len(ordered) > 1 and main["size"] <= ordered[1]["size"]:
        errors.append("largest object must be unique")
    if any(not 1 <= obj["size"] <= 3 for obj in ordered[1:]):
        errors.append("every distractor must have size 1..3")
    main_box = _bbox(main["cells"])
    if any(_inside_bbox(cell, main_box) for obj in ordered[1:] for cell in obj["cells"]):
        errors.append("distractors must lie outside the main-object bounding box")
    r1, c1, r2, c2 = main_box
    if (r2 - r1 + 1) * (c2 - c1 + 1) == main["size"]:
        errors.append("main object cannot be a filled rectangle")
    if key in (1, 2, 3, 4):
        crop = _crop(grid, main["cells"])
        if _transform(crop, key) == crop:
            errors.append("selected transform is invisible on the main crop")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """A strict generated/canonical manifold validator for the semantic gate."""
    return self_check(grid)


def _rival_ignore_key(grid):
    return _predict(grid, dispatch="identity")


def _rival_fixed_clockwise(grid):
    return _predict(grid, dispatch="clockwise")


def _rival_include_all_objects(grid):
    return _predict(grid, include_all=True)


def _rival_select_smallest(grid):
    return _predict(grid, selector="smallest")


def _rival_identity_for_key4(grid):
    return _predict(grid, dispatch="key4_identity")


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_key": _rival_ignore_key,
    "fixed_clockwise": _rival_fixed_clockwise,
    "include_all_objects": _rival_include_all_objects,
    "select_smallest": _rival_select_smallest,
    "identity_for_key4": _rival_identity_for_key4,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_non_identity(grid):
    return _rival_ignore_key(grid) != rule_mirror(grid)


def _witness_non_clockwise_key(grid):
    return grid[0][0] != 1


def _witness_has_distractors(grid):
    return len(_components(grid)) > 1


def _witness_key_four(grid):
    return grid[0][0] == 4


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "non_identity_transform": _witness_non_identity,
    "non_clockwise_key": _witness_non_clockwise_key,
    "has_smaller_distractors": _witness_has_distractors,
    "key_four_half_turn": _witness_key_four,
}

WITNESS_RIVALS = {
    "non_identity_transform": ["ignore_key"],
    "non_clockwise_key": ["fixed_clockwise"],
    "has_smaller_distractors": ["include_all_objects", "select_smallest"],
    "key_four_half_turn": ["identity_for_key4"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared competitor that fits all demos but changes the query."""
    reasons = []
    for name, competitor in sorted(LESSON_COMPETITORS.items()):
        try:
            fits = all(competitor(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            changes_query = competitor(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
