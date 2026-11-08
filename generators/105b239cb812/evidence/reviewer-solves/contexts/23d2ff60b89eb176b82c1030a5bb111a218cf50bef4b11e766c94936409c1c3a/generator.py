"""Authority-aligned sampler for 105b239cb812: infer a whole-panel transform.

The canonical Racket rule splits an ``n x (3n+2)`` input into three square
panels separated by full color-5 columns.  It selects the first transform in
``cw, 180, ccw, lr, ud, transpose`` that maps the *entire* first panel to the
second, then applies that transform to the third panel.

This generator constructs that contract directly.  In particular, it never
normalizes or independently repositions the first two motifs: panel B is the
full-panel transform of panel A, and the motif/placement is selected so the six
authoritative candidates are pairwise distinguishable.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "105b239cb812"
TASK_ID = GENERATOR_ID
RULE_HASH = "aa699e35aade"
VERSION = "3.1.0"
SUMMARY = (
    "Three square panels are separated by full color-5 columns. Panel B is a "
    "unique whole-panel transform of panel A, chosen from clockwise rotation, "
    "180-degree rotation, counterclockwise rotation, left-right reflection, "
    "up-down reflection, or transpose. Apply the inferred transform to panel C."
)

EXAMPLES_NEEDED = 3

TRANSFORM_NAMES = ("cw", "180", "ccw", "lr", "ud", "transpose")
# Alternate directional and self-inverse transforms.  Any four consecutive
# generated pairs (three demonstrations plus one query) contain two directional
# quarter-turns, so the A->B direction remains identifiable even when any one
# pair is held out as the query.
TRANSFORM_SCHEDULE = (
    "cw", "180", "ccw", "lr", "cw", "ud", "ccw", "transpose",
)
LESSON_SCHEDULE_PERIOD = len(TRANSFORM_SCHEDULE)
SCHEDULE_PROFILES = TRANSFORM_NAMES
SHAPE_KINDS = ("tetromino", "pentomino", "six_cell")

INVARIANTS = [
    "input shape is n x (3n+2), with n in 4..7",
    "columns n and 2n+1 are the only full color-5 separator columns",
    "panels A and B use one shared foreground color and panel C uses another",
    "exactly one authoritative whole-panel transform maps A to B",
    "the query motif changes under every authoritative non-identity transform",
]

AXES = {
    "panel_size": {
        "type": "int",
        "default": "canonical anchor plus difficulty-aware 4..7",
        "valid": "4..7",
    },
    "transform": {
        "type": "str",
        "default": "balanced deterministic schedule",
        "valid": "|".join(TRANSFORM_NAMES),
    },
    "shape_kind": {
        "type": "str",
        "default": "balanced deterministic schedule",
        "valid": "|".join(SHAPE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Every base motif is connected and fits a 4x4 panel.  Candidate construction
# below retains only translated instances with a trivial stabilizer across the
# identity plus all six transforms used by the authority.
_BASE_SHAPES = {
    "tetromino": (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    "pentomino": (
        ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    "six_cell": (
        ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (3, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2)),
    ),
}


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _transform_panel(panel: list[list[int]], name: str) -> list[list[int]]:
    """Apply one transform in exactly the canonical rule's naming/order."""
    if name == "cw":
        return [list(row) for row in zip(*panel[::-1])]
    if name == "180":
        return [row[::-1] for row in panel[::-1]]
    if name == "ccw":
        return [list(row) for row in zip(*panel)][::-1]
    if name == "lr":
        return [row[::-1] for row in panel]
    if name == "ud":
        return [row[:] for row in panel[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*panel)]
    raise ValueError(f"unsupported transform: {name!r}")


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _paint_panel(size: int, cells: tuple[tuple[int, int], ...], color: int) -> list[list[int]]:
    panel = full_grid(size, size, 0)
    for row, col in cells:
        panel[row][col] = color
    return panel


@lru_cache(maxsize=None)
def _candidate_cells(size: int, kind: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All translated motifs whose authoritative transform is unambiguous."""
    if size not in range(4, 8):
        raise ValueError(f"panel_size must be in 4..7, got {size!r}")
    if kind not in SHAPE_KINDS:
        raise ValueError(f"unknown shape_kind: {kind!r}")

    retained: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[kind]:
        height = max(row for row, _ in base) + 1
        width = max(col for _, col in base) + 1
        for top in range(size - height + 1):
            for left in range(size - width + 1):
                cells = tuple(sorted((top + row, left + col) for row, col in base))
                panel = _paint_panel(size, cells, 1)
                orbit = {_grid_key(panel)}
                orbit.update(_grid_key(_transform_panel(panel, name)) for name in TRANSFORM_NAMES)
                if len(orbit) == len(TRANSFORM_NAMES) + 1:
                    retained.add(cells)
    if not retained:
        raise RuntimeError(f"no unambiguous {kind} candidates fit panel size {size}")
    return tuple(sorted(retained))


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "panel_size" in overrides and overrides["panel_size"] is not None:
        value = overrides["panel_size"]
        if type(value) is not int or not 4 <= value <= 7:
            raise ValueError("panel_size must be an integer in 4..7 (not bool)")
    if "transform" in overrides and overrides["transform"] is not None:
        value = overrides["transform"]
        if type(value) is not str or value not in TRANSFORM_NAMES:
            raise ValueError(f"transform must be one of {TRANSFORM_NAMES}")
    if "shape_kind" in overrides and overrides["shape_kind"] is not None:
        value = overrides["shape_kind"]
        if type(value) is not str or value not in SHAPE_KINDS:
            raise ValueError(f"shape_kind must be one of {SHAPE_KINDS}")


def _draw_panel_size(ctx, sample_index: int, difficulty) -> int:
    # Every fourth sample is a canonical 4x14 profile in every band.  Overrides
    # remain legal across all bands; difficulty only changes the non-anchor mix.
    if ctx.overrides.get("panel_size") is not None:
        return ctx.draw_int_strict("panel_size", 4, 7)
    if sample_index % 4 == 0:
        return ctx.draw_choice("panel_size", (4,))
    options = {
        "easy": (4, 4, 5, 5, 6, 7),
        "hard": (4, 5, 6, 6, 7, 7),
    }.get(difficulty, (4, 5, 6, 7))
    return ctx.draw_choice("panel_size", options)


def _draw_scheduled_choice(ctx, label: str, values: tuple[str, ...], offset: int) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, values)
    scheduled = values[offset % len(values)]
    return ctx.draw_choice(label, (scheduled,))


def _draw_transform(ctx, sample_index: int) -> str:
    if ctx.overrides.get("transform") is not None:
        return ctx.draw_choice("transform", TRANSFORM_NAMES)
    scheduled = TRANSFORM_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]
    return ctx.draw_choice("transform", (scheduled,))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Expose the finite transform schedule to the semantic census."""
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    return TRANSFORM_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size = _draw_panel_size(ctx, sample_index, difficulty)
    transform_name = _draw_transform(ctx, sample_index)
    shape_kind = _draw_scheduled_choice(
        ctx, "shape_kind", SHAPE_KINDS, sample_index
    )

    layout_rng = ctx.draw_rng("motif_layout")
    a_cells = layout_rng.choice(_candidate_cells(size, shape_kind))
    query_kind = layout_rng.choice(SHAPE_KINDS)
    c_cells = layout_rng.choice(_candidate_cells(size, query_kind))

    color_rng = ctx.draw_rng("foreground_colors")
    color_a, color_c = color_rng.sample((1, 2, 3, 4, 6, 7, 8, 9), 2)

    panel_a = _paint_panel(size, a_cells, color_a)
    panel_b = _transform_panel(panel_a, transform_name)
    panel_c = _paint_panel(size, c_cells, color_c)

    grid = full_grid(size, 3 * size + 2, 0)
    sep1, sep2 = size, 2 * size + 1
    for row in range(size):
        grid[row][0:size] = panel_a[row]
        grid[row][sep1] = 5
        grid[row][sep1 + 1:sep2] = panel_b[row]
        grid[row][sep2] = 5
        grid[row][sep2 + 1:] = panel_c[row]
    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (not bool)"]
    return []


def _split_panels(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    size = len(grid)
    expected_width = 3 * size + 2
    if len(grid[0]) != expected_width:
        raise ValueError(f"expected width {expected_width} for {size} rows")
    sep1, sep2 = size, 2 * size + 1
    return (
        [list(row[:sep1]) for row in grid],
        [list(row[sep1 + 1:sep2]) for row in grid],
        [list(row[sep2 + 1:]) for row in grid],
    )


def _matching_transforms(panel_a: list[list[int]], panel_b: list[list[int]]) -> list[str]:
    return [name for name in TRANSFORM_NAMES if _transform_panel(panel_a, name) == panel_b]


def _infer_transform(grid: list[list[int]]) -> str:
    panel_a, panel_b, _ = _split_panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one authoritative transform mapping A to B, got {matches}")
    return matches[0]


def _foreground_colors(panel: list[list[int]]) -> set[int]:
    return {value for row in panel for value in row if value != 0}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _basic_grid_errors(grid)
    if errors:
        return errors

    size, width = len(grid), len(grid[0])
    if not 4 <= size <= 7:
        errors.append(f"panel size / grid height must be in 4..7, got {size}")
    if width != 3 * size + 2:
        errors.append(f"expected width 3*n+2={3 * size + 2}, got {width}")
        return errors

    sep1, sep2 = size, 2 * size + 1
    full_fives = [col for col in range(width) if all(grid[row][col] == 5 for row in range(size))]
    if full_fives != [sep1, sep2]:
        errors.append(f"expected only separator columns {[sep1, sep2]}, got {full_fives}")
    if any(grid[row][col] == 5 for row in range(size) for col in range(width) if col not in (sep1, sep2)):
        errors.append("color 5 may appear only in the two separator columns")

    panel_a, panel_b, panel_c = _split_panels(grid)
    colors_a = _foreground_colors(panel_a)
    colors_b = _foreground_colors(panel_b)
    colors_c = _foreground_colors(panel_c)
    if len(colors_a) != 1:
        errors.append(f"panel A must contain exactly one foreground color, got {sorted(colors_a)}")
    if colors_b != colors_a or len(colors_b) != 1:
        errors.append("panels A and B must use the same single foreground color")
    if len(colors_c) != 1:
        errors.append(f"panel C must contain exactly one foreground color, got {sorted(colors_c)}")
    if colors_a and colors_c and colors_a == colors_c:
        errors.append("panel C foreground color must differ from panels A/B")

    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1:
        errors.append(f"expected exactly one authoritative whole-panel transform A->B, got {matches}")
    return errors


def strict_canonical_like(grid):
    """Canonical-manifold hook: lawful task structure at canonical 4x14 scale."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 4 or len(grid[0]) != 14:
        return ["canonical scale is 4 rows by 14 columns"]
    if len({value for row in grid for value in row}) != 4:
        return ["canonical palette profile contains background, divider, A/B, and C colors"]
    return []


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    panel_a, _, _ = _split_panels(grid)
    occupied = sum(value != 0 for row in panel_a for value in row)
    kind_by_count = {4: "tetromino", 5: "pentomino", 6: "six_cell"}
    if occupied not in kind_by_count:
        raise ValueError(f"panel A has unsupported motif size {occupied}")
    return {
        "panel_size": len(grid),
        "transform": _infer_transform(grid),
        "shape_kind": kind_by_count[occupied],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    _, _, panel_c = _split_panels(grid)
    return _transform_panel(panel_c, _infer_transform(grid))


def _copy_query(grid) -> list[list[int]]:
    return _split_panels(grid)[2]


def _reverse_pair(grid) -> list[list[int]]:
    panel_a, panel_b, panel_c = _split_panels(grid)
    reverse_matches = _matching_transforms(panel_b, panel_a)
    if len(reverse_matches) != 1:
        raise ValueError(f"expected one reverse transform, got {reverse_matches}")
    return _transform_panel(panel_c, reverse_matches[0])


def _query_changes(grid) -> bool:
    try:
        return rule_mirror(grid) != _copy_query(grid)
    except ValueError:
        return False


def _quarter_turn_direction(grid) -> bool:
    try:
        return _infer_transform(grid) in {"cw", "ccw"}
    except ValueError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Reject mislabeled pairs and declared rivals that survive the demos."""
    reasons: list[str] = []
    labeled = [(f"demo {index}", pair) for index, pair in enumerate(demos)] + [("query", query)]
    for label, pair in labeled:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must be a labeled input/output pair")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"{label} is not a lawful uniquely identified task input: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"{label} output does not match its uniquely inferred transform")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(_copy_grid(pair["input"])) == pair["output"]
                for pair in demos
            )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised on a demonstration: {exc}")
            continue
        if not survives:
            continue
        try:
            rival_query = competitor(_copy_grid(query["input"]))
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised on the query: {exc}")
            continue
        if rival_query != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query answer"
            )
    return reasons


SEMANTIC_WITNESSES = {
    "query_changes": _query_changes,
    "quarter_turn_direction": _quarter_turn_direction,
}
SEMANTIC_RIVALS = {
    "copy_query": _copy_query,
    "reverse_pair": _reverse_pair,
}
WITNESS_RIVALS = {
    "query_changes": ["copy_query"],
    "quarter_turn_direction": ["reverse_pair"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
