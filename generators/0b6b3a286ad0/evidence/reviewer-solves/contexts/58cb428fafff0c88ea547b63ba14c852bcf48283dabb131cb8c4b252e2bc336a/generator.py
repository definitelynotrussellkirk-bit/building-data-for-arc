"""Canonical-linked generator for the template-key library lookup task.

Five panels are separated by full-height color-9 columns::

    KEY1 | VALUE1 | KEY2 | VALUE2 | QUERY

The authoritative rule crops the four library panels.  It returns VALUE1 when
KEY1 occurs in QUERY without rotation; zero cells in KEY1 are wildcards.
Otherwise it returns VALUE2.  Generated VALUE2 examples also contain an exact
KEY2 occurrence, matching the visible two-key pedagogy in every canonical
VALUE2 example instead of teaching an accidental "KEY1 versus noise" shortcut.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b6b3a286ad0"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "950fe1e7c618"

SUMMARY = (
    "Five separator-delimited panels encode KEY1->VALUE1 and KEY2->VALUE2. "
    "QUERY contains KEY1 (zero cells are wildcards, no rotations) for VALUE1, "
    "or contains KEY2 plus an optional KEY1 decoy for VALUE2."
)

INVARIANTS = [
    "only the canonical 6x25 and 7x26 five-panel geometries are emitted",
    "KEY1, VALUE1, KEY2, and VALUE2 crop to 3x3, 4x4, 3x3, and 4x4",
    "VALUE1 and VALUE2 are distinct; every VALUE2 draw contains KEY2",
    "match/wildcard draws contain KEY1; all other textures contain no KEY1 match",
    "the palette has exactly background, divider, two key, and one value color",
]

PANEL_HEIGHTS = (6, 7)
TEXTURES = ("match", "no_match", "rotated_decoy", "near_miss", "wildcard")
SCHEDULE_PROFILES = TEXTURES
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "panel_h": {
        "type": "int",
        "default": "rng 6..7",
        "valid": "6..7",
        "doc": "6 -> canonical 6x25 profile; 7 -> canonical 7x26 profile",
    },
    "texture": {
        "type": "str",
        "default": "five-slot sample_index schedule",
        "valid": "|".join(TEXTURES),
        "doc": (
            "match: exact KEY1; no_match: KEY2 only; rotated_decoy: KEY2 plus "
            "rotated KEY1; near_miss: KEY2 plus one-cell-broken KEY1; wildcard: "
            "KEY1 with colored cells beneath its zero wildcard positions"
        ),
    },
}

_CONTENT_COLORS = tuple(range(1, 9))
_PANEL_WIDTHS = (3, 4, 3, 4)
_DIVIDER_COLUMNS = (3, 8, 12, 17)

# Connected, full-bounding-box 3x3 masks.  KEY1 candidates with rotational
# symmetry are filtered out below so the rotated-decoy lesson is observable.
_RAW_KEY_MASKS = (
    ((1, 0, 0), (1, 0, 0), (1, 1, 1)),
    ((1, 1, 1), (0, 0, 1), (0, 1, 1)),
    ((1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 0, 1), (1, 1, 1), (0, 0, 1)),
    ((1, 1, 0), (1, 0, 0), (1, 1, 1)),
    ((0, 1, 1), (1, 1, 0), (1, 0, 0)),
    ((1, 0, 0), (1, 1, 1), (0, 0, 1)),
    ((1, 1, 1), (0, 1, 0), (1, 1, 0)),
    ((1, 0, 1), (1, 1, 1), (0, 1, 0)),
    ((1, 1, 0), (0, 1, 1), (0, 0, 1)),
    ((0, 0, 1), (1, 1, 1), (1, 0, 0)),
)

# Connected, exact-bounding-box 4x4 value masks.  Every mask has a path from
# its left edge to its right edge, joining the divider columns into one library
# component just as the canonical examples do.
_VALUE_MASKS = (
    ((1, 1, 1, 1), (1, 0, 0, 0), (1, 1, 1, 0), (0, 0, 1, 1)),
    ((1, 0, 0, 1), (1, 1, 1, 1), (0, 0, 1, 0), (0, 0, 1, 1)),
    ((1, 1, 0, 0), (0, 1, 1, 1), (0, 1, 0, 0), (1, 1, 1, 1)),
    ((1, 0, 1, 1), (1, 1, 1, 0), (0, 0, 1, 0), (1, 1, 1, 1)),
    ((1, 1, 1, 0), (0, 0, 1, 0), (1, 1, 1, 1), (1, 0, 0, 1)),
    ((1, 0, 0, 1), (1, 1, 1, 1), (1, 0, 0, 0), (1, 1, 1, 1)),
    ((1, 1, 1, 1), (0, 1, 0, 0), (0, 1, 1, 1), (0, 0, 0, 1)),
    ((1, 0, 0, 0), (1, 1, 1, 1), (0, 0, 0, 1), (1, 1, 1, 1)),
    ((1, 1, 1, 1), (0, 0, 0, 1), (1, 1, 1, 1), (1, 0, 0, 0)),
    ((1, 1, 0, 1), (0, 1, 1, 1), (0, 1, 0, 0), (1, 1, 1, 1)),
)

Grid = list[list[int]]
Mask = tuple[tuple[int, ...], ...]


def _rot90(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid: Sequence[Sequence[int]]) -> tuple[Grid, ...]:
    rotations: list[Grid] = [[list(row) for row in grid]]
    for _ in range(3):
        rotations.append(_rot90(rotations[-1]))
    return tuple(rotations)


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _unique_transforms(mask: Mask) -> tuple[Mask, ...]:
    candidates: list[Mask] = []
    base = [list(row) for row in mask]
    for reflected in (base, [list(reversed(row)) for row in base]):
        for rotated in _rotations(reflected):
            frozen = _freeze(rotated)
            if frozen not in candidates:
                candidates.append(frozen)
    return tuple(candidates)


KEY_MASKS = tuple(
    transform
    for mask in _RAW_KEY_MASKS
    for transform in _unique_transforms(mask)
    if all(transform != _freeze(rotation) for rotation in _rotations(transform)[1:])
)
VALUE_MASKS = tuple(
    transform for mask in _VALUE_MASKS for transform in _unique_transforms(mask)
)


def _color_mask(mask: Sequence[Sequence[int]], color: int) -> Grid:
    return [[color if int(value) else 0 for value in row] for row in mask]


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def _grid_errors(grid: Any) -> tuple[list[str], Grid | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    converted = [list(row) for row in grid]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in converted
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"], None
    return [], converted


def _crop(panel: Sequence[Sequence[int]]) -> Grid | None:
    cells = [
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if int(value) not in (0, 9)
    ]
    if not cells:
        return None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left:right + 1]) for row in panel[top:bottom + 1]]


def _find_matches(
    board: Sequence[Sequence[int]],
    template: Sequence[Sequence[int]],
    *,
    wildcard_zeros: bool = True,
) -> list[tuple[int, int]]:
    board_h, board_w = len(board), len(board[0])
    template_h, template_w = len(template), len(template[0])
    if template_h > board_h or template_w > board_w:
        return []
    matches: list[tuple[int, int]] = []
    for row in range(board_h - template_h + 1):
        for col in range(board_w - template_w + 1):
            if all(
                (wildcard_zeros and int(template[dr][dc]) == 0)
                or int(board[row + dr][col + dc]) == int(template[dr][dc])
                for dr in range(template_h)
                for dc in range(template_w)
            ):
                matches.append((row, col))
    return matches


def _required_mismatches(
    board: Sequence[Sequence[int]], template: Sequence[Sequence[int]]
) -> list[tuple[int, int, int]]:
    """Return (mismatch_count,row,col) for every in-bounds placement.

    Only nonzero template cells count.  This is the explicit rival that treats a
    one-cell-broken key as present; it is not used by the authoritative mirror.
    """
    board_h, board_w = len(board), len(board[0])
    template_h, template_w = len(template), len(template[0])
    results: list[tuple[int, int, int]] = []
    for row in range(board_h - template_h + 1):
        for col in range(board_w - template_w + 1):
            mismatches = sum(
                int(board[row + dr][col + dc]) != int(template[dr][dc])
                for dr in range(template_h)
                for dc in range(template_w)
                if int(template[dr][dc]) != 0
            )
            results.append((mismatches, row, col))
    return results


def _split_panels(grid: Sequence[Sequence[int]]) -> tuple[list[Grid], list[int]]:
    height, width = len(grid), len(grid[0])
    dividers = [
        col for col in range(width) if all(int(grid[row][col]) == 9 for row in range(height))
    ]
    panels: list[Grid] = []
    start = 0
    for col in dividers:
        panels.append([list(row[start:col]) for row in grid])
        start = col + 1
    panels.append([list(row[start:]) for row in grid])
    return panels, dividers


def _monochrome_color(grid: Sequence[Sequence[int]]) -> int | None:
    colors = {int(value) for row in grid for value in row if int(value) != 0}
    return next(iter(colors)) if len(colors) == 1 else None


def _wildcard_noise_count(
    query: Sequence[Sequence[int]],
    template: Sequence[Sequence[int]],
    matches: Sequence[tuple[int, int]],
) -> int:
    counts = []
    for row, col in matches:
        counts.append(
            sum(
                int(template[dr][dc]) == 0 and int(query[row + dr][col + dc]) != 0
                for dr in range(len(template))
                for dc in range(len(template[0]))
            )
        )
    return max(counts, default=0)


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Parse the five-panel grammar and expose branch/shortcut observables."""
    errors, converted = _grid_errors(grid)
    if converted is None:
        return {"errors": errors}
    height, width = len(converted), len(converted[0])
    if (height, width) not in {(6, 25), (7, 26)}:
        errors.append(f"expected canonical profile 6x25 or 7x26, found {height}x{width}")

    panels, dividers = _split_panels(converted)
    if dividers != list(_DIVIDER_COLUMNS):
        errors.append(
            f"expected full-height divider columns {list(_DIVIDER_COLUMNS)}, found {dividers}"
        )
    stray_nines = [
        (row, col)
        for row, values in enumerate(converted)
        for col, value in enumerate(values)
        if value == 9 and col not in _DIVIDER_COLUMNS
    ]
    if stray_nines:
        errors.append("color 9 appears outside the four divider columns")
    expected_widths = [3, 4, 3, 4, height + 1]
    if len(panels) != 5 or [len(panel[0]) for panel in panels] != expected_widths:
        errors.append(
            f"expected panel widths {expected_widths}, found "
            f"{[len(panel[0]) for panel in panels] if panels else []}"
        )

    crops: list[Grid | None] = [_crop(panel) for panel in panels[:4]] if len(panels) >= 4 else []
    expected_crop_dims = ((3, 3), (4, 4), (3, 3), (4, 4))
    if len(crops) == 4:
        for index, (crop, dims) in enumerate(zip(crops, expected_crop_dims), start=1):
            actual = None if crop is None else (len(crop), len(crop[0]))
            if actual != dims:
                errors.append(f"panel {index} crop must be {dims[0]}x{dims[1]}, found {actual}")
    else:
        errors.append("could not recover four library crops")

    key1 = crops[0] if len(crops) == 4 else None
    value1 = crops[1] if len(crops) == 4 else None
    key2 = crops[2] if len(crops) == 4 else None
    value2 = crops[3] if len(crops) == 4 else None
    query = panels[4] if len(panels) == 5 else []

    library_colors: tuple[int | None, ...] = ()
    if all(crop is not None for crop in crops):
        library_colors = tuple(_monochrome_color(crop or []) for crop in crops)
        for index, color in enumerate(library_colors, start=1):
            if color is None:
                errors.append(f"panel {index} crop must be monochrome")
        if library_colors[0] == library_colors[2]:
            errors.append("KEY1 and KEY2 must use distinct colors")
        if library_colors[1] != library_colors[3]:
            errors.append("VALUE1 and VALUE2 must share the canonical value color")
        if value1 == value2:
            errors.append("VALUE1 and VALUE2 must be distinct")

    key1_matches: list[tuple[int, int]] = []
    key2_matches: list[tuple[int, int]] = []
    strict_key1_matches: list[tuple[int, int]] = []
    rotated_key1_matches: list[tuple[int, int]] = []
    near_miss_count = 0
    wildcard_noise_cells = 0
    texture = None
    branch = None
    if key1 is not None and key2 is not None and query:
        key1_matches = _find_matches(query, key1)
        key2_matches = _find_matches(query, key2)
        strict_key1_matches = _find_matches(query, key1, wildcard_zeros=False)
        rotated_key1_matches = [
            position
            for rotated in _rotations(key1)[1:]
            for position in _find_matches(query, rotated)
        ]
        near_miss_count = sum(
            mismatch == 1 for mismatch, _row, _col in _required_mismatches(query, key1)
        )
        wildcard_noise_cells = _wildcard_noise_count(query, key1, key1_matches)
        if key1_matches:
            branch = "value1"
            texture = "wildcard" if wildcard_noise_cells else "match"
            if key2_matches:
                errors.append("query ambiguously contains both KEY1 and KEY2")
        elif key2_matches:
            branch = "value2"
            if rotated_key1_matches:
                texture = "rotated_decoy"
            elif near_miss_count:
                texture = "near_miss"
            else:
                texture = "no_match"
        else:
            errors.append("query contains neither KEY1 nor KEY2")

    palette = {value for row in converted for value in row}
    return {
        "errors": errors,
        "grid": converted,
        "panel_h": height,
        "panel_w": width,
        "panels": panels,
        "dividers": dividers,
        "key1": key1,
        "value1": value1,
        "key2": key2,
        "value2": value2,
        "query": query,
        "library_colors": library_colors,
        "key1_matches": len(key1_matches),
        "key2_matches": len(key2_matches),
        "strict_key1_matches": len(strict_key1_matches),
        "rotated_key1_matches": len(rotated_key1_matches),
        "near_miss_count": near_miss_count,
        "wildcard_noise_cells": wildcard_noise_cells,
        "texture": texture,
        "branch": branch,
        "palette": palette,
        "palette_size": len(palette),
    }


def self_check(grid: Any, *, difficulty: str | None = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    return list(semantic_observables(grid).get("errors", []))


def strict_canonical_like(grid: Any) -> list[str]:
    facts = semantic_observables(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    if facts.get("palette_size") != 5:
        reasons.append(f"canonical palette has five colors, found {facts.get('palette_size')}")
    return reasons


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return {"panel_h": facts["panel_h"], "texture": facts["texture"]}


def rule_mirror(grid: Any) -> Grid:
    """Python test mirror; canonical Racket remains the output authority."""
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    selected = facts["value1"] if facts["branch"] == "value1" else facts["value2"]
    return _copy_grid(selected)


def _paint(grid: Grid, top: int, left: int, pattern: Sequence[Sequence[int]]) -> None:
    for row, values in enumerate(pattern):
        for col, value in enumerate(values):
            if int(value) != 0:
                grid[top + row][left + col] = int(value)


def _build_query(
    panel_h: int,
    texture: str,
    key1: Grid,
    key2: Grid,
    value_color: int,
    rng: Any,
) -> Grid:
    query_w = panel_h + 1
    # Column zero stays blank, preserving the canonical separation between the
    # library/divider component and the query component.
    for _attempt in range(160):
        query = full_grid(panel_h, query_w, 0)
        if texture in {"match", "wildcard"}:
            row = rng.randint(0, panel_h - 3)
            col = rng.randint(1, query_w - 3)
            _paint(query, row, col, key1)
            if texture == "wildcard":
                zero_cells = [
                    (dr, dc)
                    for dr in range(3)
                    for dc in range(3)
                    if key1[dr][dc] == 0
                ]
                # Fill every zero with the value color.  This guarantees a
                # counterexample to the zero-strict shortcut while adding no
                # second-key-colored accidental match.
                for dr, dc in zero_cells:
                    query[row + dr][col + dc] = value_color
        elif texture == "no_match":
            row = rng.randint(0, panel_h - 3)
            col = rng.randint(1, query_w - 3)
            _paint(query, row, col, key2)
        else:
            # Two 3x3 motifs fit side-by-side in both canonical query widths.
            left_first = bool(rng.randrange(2))
            first_col, second_col = (1, 4) if left_first else (4, 1)
            key2_col = first_col
            decoy_col = second_col
            key2_row = rng.randint(0, panel_h - 3)
            decoy_row = rng.randint(0, panel_h - 3)
            _paint(query, key2_row, key2_col, key2)
            if texture == "rotated_decoy":
                decoy = _rotations(key1)[1 + rng.randrange(3)]
            else:
                decoy = _copy_grid(key1)
                colored = [
                    (row, col)
                    for row in range(3)
                    for col in range(3)
                    if decoy[row][col] != 0
                ]
                # Deleting one required cell reproduces the canonical test's
                # near miss and avoids introducing a fourth content color.
                remove_row, remove_col = colored[rng.randrange(len(colored))]
                decoy[remove_row][remove_col] = 0
            _paint(query, decoy_row, decoy_col, decoy)

        key1_hits = _find_matches(query, key1)
        key2_hits = _find_matches(query, key2)
        wildcard_noise = _wildcard_noise_count(query, key1, key1_hits)
        rotated_hits = any(_find_matches(query, rotated) for rotated in _rotations(key1)[1:])
        one_miss = any(mismatch == 1 for mismatch, _row, _col in _required_mismatches(query, key1))
        valid = {
            "match": bool(key1_hits) and not key2_hits and wildcard_noise == 0,
            "wildcard": bool(key1_hits) and not key2_hits and wildcard_noise > 0,
            "no_match": not key1_hits and bool(key2_hits) and not rotated_hits and not one_miss,
            "rotated_decoy": not key1_hits and bool(key2_hits) and rotated_hits,
            "near_miss": not key1_hits and bool(key2_hits) and not rotated_hits and one_miss,
        }[texture]
        if valid:
            return query
    raise ValueError(f"could not realize texture {texture!r}")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    del seed, difficulty
    return TEXTURES[sample_index % len(TEXTURES)]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> Grid:
    _validate_call(difficulty, overrides)
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("texture", schedule_profile(seed, sample_index, difficulty))
    if "panel_h" not in effective_overrides:
        if difficulty == "easy":
            effective_overrides["panel_h"] = 6
        elif difficulty == "hard":
            effective_overrides["panel_h"] = 7
        else:
            effective_overrides["panel_h"] = 6 + ((seed + sample_index) % 2)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    panel_h = ctx.draw_int("panel_h", 6, 7)
    texture = ctx.draw_choice("texture", TEXTURES)
    rng = ctx.draw_rng("content")

    for _attempt in range(240):
        key1_mask = rng.choice(KEY_MASKS)
        key2_mask = rng.choice(KEY_MASKS)
        if key2_mask == key1_mask:
            continue
        value1_mask = rng.choice(VALUE_MASKS)
        value2_mask = rng.choice(VALUE_MASKS)
        if value2_mask == value1_mask:
            continue
        key1_color, key2_color, value_color = rng.sample(_CONTENT_COLORS, 3)
        key1 = _color_mask(key1_mask, key1_color)
        key2 = _color_mask(key2_mask, key2_color)
        value1 = _color_mask(value1_mask, value_color)
        value2 = _color_mask(value2_mask, value_color)
        try:
            query = _build_query(panel_h, texture, key1, key2, value_color, rng)
        except ValueError:
            continue

        query_w = panel_h + 1
        width = sum(_PANEL_WIDTHS) + len(_PANEL_WIDTHS) + query_w
        grid = full_grid(panel_h, width, 0)
        left = 0
        for panel, panel_w in zip((key1, value1, key2, value2), _PANEL_WIDTHS):
            top = rng.randint(0, panel_h - len(panel))
            _paint(grid, top, left, panel)
            left += panel_w
            for row in range(panel_h):
                grid[row][left] = 9
            left += 1
        for row in range(panel_h):
            grid[row][left:left + query_w] = list(query[row])

        facts = semantic_observables(grid)
        if not facts["errors"] and facts["texture"] == texture:
            return grid
    raise ValueError("could not realize a canonical-linked template-key board")


def _fixed_value(which: int) -> Callable[[Any], Grid]:
    def apply(grid: Any) -> Grid:
        facts = semantic_observables(grid)
        selected = facts["value1"] if which == 1 else facts["value2"]
        return _copy_grid(selected)

    return apply


def _any_key_selects_value1(grid: Any) -> Grid:
    facts = semantic_observables(grid)
    selected = facts["value1"] if facts["key1_matches"] or facts["key2_matches"] else facts["value2"]
    return _copy_grid(selected)


def _rotation_counts(grid: Any) -> Grid:
    facts = semantic_observables(grid)
    selected = facts["value1"] if facts["key1_matches"] or facts["rotated_key1_matches"] else facts["value2"]
    return _copy_grid(selected)


def _near_miss_counts(grid: Any) -> Grid:
    facts = semantic_observables(grid)
    selected = facts["value1"] if facts["key1_matches"] or facts["near_miss_count"] else facts["value2"]
    return _copy_grid(selected)


def _zero_strict_match(grid: Any) -> Grid:
    facts = semantic_observables(grid)
    selected = facts["value1"] if facts["strict_key1_matches"] else facts["value2"]
    return _copy_grid(selected)


SEMANTIC_RIVALS = {
    "fixed_value1": _fixed_value(1),
    "fixed_value2": _fixed_value(2),
    "any_key_selects_value1": _any_key_selects_value1,
    "rotation_counts": _rotation_counts,
    "near_miss_counts": _near_miss_counts,
    "zero_strict_match": _zero_strict_match,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"zero_strict_match": _zero_strict_match}


def _facts(grid: Any) -> dict[str, Any]:
    return semantic_observables(grid)


SEMANTIC_WITNESSES = {
    "selects_value1": lambda grid: _facts(grid).get("branch") == "value1",
    "selects_value2": lambda grid: _facts(grid).get("branch") == "value2",
    "key2_supports_else": lambda grid: (
        _facts(grid).get("branch") == "value2" and _facts(grid).get("key2_matches", 0) > 0
    ),
    "rotated_key1_is_not_a_match": lambda grid: _facts(grid).get("texture") == "rotated_decoy",
    "one_cell_near_miss_is_not_a_match": lambda grid: _facts(grid).get("texture") == "near_miss",
    "zero_cells_are_wildcards": lambda grid: _facts(grid).get("texture") == "wildcard",
}

WITNESS_RIVALS = {
    "selects_value1": ["fixed_value2"],
    "selects_value2": ["fixed_value1"],
    "key2_supports_else": ["any_key_selects_value1"],
    "rotated_key1_is_not_a_match": ["rotation_counts"],
    "one_cell_near_miss_is_not_a_match": ["near_miss_counts"],
    "zero_cells_are_wildcards": ["zero_strict_match"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    surviving = set(LESSON_COMPETITORS)
    textures: set[str] = set()
    branches: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        facts = semantic_observables(pair["input"])
        if facts.get("errors"):
            return [f"demo {index} input invalid: {facts['errors'][0]}"]
        official = _freeze(pair["output"])
        if _freeze(rule_mirror(pair["input"])) != official:
            reasons.append(f"demo {index} output disagrees with the lookup rule")
        textures.add(facts["texture"])
        branches.add(facts["branch"])
        surviving &= {
            name
            for name in surviving
            if _freeze(LESSON_COMPETITORS[name](pair["input"])) == official
        }
    missing_textures = set(TEXTURES) - textures
    if missing_textures:
        reasons.append("demos omit texture(s): " + ", ".join(sorted(missing_textures)))
    if branches != {"value1", "value2"}:
        reasons.append("demos do not show both value branches")
    if surviving:
        reasons.append("demos leave shortcut(s) unrefuted: " + ", ".join(sorted(surviving)))

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_facts = semantic_observables(query["input"])
    if query_facts.get("errors"):
        reasons.append(f"query input invalid: {query_facts['errors'][0]}")
    elif _freeze(rule_mirror(query["input"])) != _freeze(query["output"]):
        reasons.append("query output disagrees with the lookup rule")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-semantic near-misses that the structural checker must reject."""
    base = generate(314159, 0, difficulty="medium", panel_h=6, texture="match")
    facts = semantic_observables(base)
    fixtures: list[tuple[str, Grid]] = []

    broken_divider = _copy_grid(base)
    broken_divider[0][_DIVIDER_COLUMNS[0]] = 0
    fixtures.append(("broken_divider", broken_divider))

    extra_divider = _copy_grid(base)
    for row in range(len(extra_divider)):
        extra_divider[row][0] = 9
    fixtures.append(("extra_divider", extra_divider))

    empty_key1 = _copy_grid(base)
    for row in range(len(empty_key1)):
        for col in range(0, 3):
            empty_key1[row][col] = 0
    fixtures.append(("empty_key1", empty_key1))

    identical_values = _copy_grid(base)
    value1_panel = facts["panels"][1]
    for row in range(len(identical_values)):
        identical_values[row][13:17] = list(value1_panel[row])
    fixtures.append(("identical_values", identical_values))

    empty_query = _copy_grid(base)
    for row in range(len(empty_query)):
        for col in range(18, len(empty_query[0])):
            empty_query[row][col] = 0
    fixtures.append(("empty_query", empty_query))

    both_keys = _copy_grid(empty_query)
    _paint(both_keys, 0, 19, facts["key1"])
    _paint(both_keys, 3, 22, facts["key2"])
    fixtures.append(("query_contains_both_keys", both_keys))

    mixed_value_color = _copy_grid(base)
    cell = next(
        (row, col)
        for row in range(len(mixed_value_color))
        for col in range(4, 8)
        if mixed_value_color[row][col] not in (0, 9)
    )
    replacement = next(
        color for color in _CONTENT_COLORS if color not in facts["palette"]
    )
    mixed_value_color[cell[0]][cell[1]] = replacement
    fixtures.append(("mixed_value_color", mixed_value_color))

    wrong_width = [row[:-1] for row in base]
    fixtures.append(("wrong_profile_width", wrong_width))
    return fixtures
