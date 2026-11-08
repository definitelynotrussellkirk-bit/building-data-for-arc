"""Generate color-blind dihedral-relation lessons for task df5e596e5e96.

The input is a 5-row strip of 3..5 width-5 panels separated by one blank
column.  The output is the pairwise relation matrix over *normalized binary
support*:

* diagonal: 8
* exact support: 1
* rotation: 2
* reflection (the remaining dihedral images): 3
* unrelated: 0

Version 3 replaces an IID class sampler that accidentally made every unrelated
pair have a different cell count.  The constructive four-slot curriculum below
always includes a same-count unrelated pair and regularly uses different colors
for related panels, so neither cell count nor color can stand in for shape.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df5e596e5e96"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "dd7b7aac9913"

SUMMARY = (
    "Split the 5-row input at blank separator columns into N=3..5 width-5 "
    "panels. Crop each panel to its nonzero bounding box and compare binary "
    "support, ignoring foreground color and placement. Output an N×N matrix: "
    "8 on the diagonal, 1 for exact normalized support, 2 for a non-identity "
    "rotation, 3 for a reflection/other dihedral image, and 0 otherwise."
)

INVARIANTS = [
    "background is 0 and every panel uses one nonzero color",
    "grid is 5 rows by 6*N-1 columns for N=3..5, with blank separators",
    "every panel is one 4-connected support containing 4..8 cells",
    "foreground color and within-panel translation do not affect relations",
]

AXES = {
    "n_panels": {
        "type": "int",
        "default": "scheduled canonical anchor 5",
        "valid": "3..5",
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "full_relations",
    "rotation_duplicate",
    "two_rotations",
    "paired_classes",
)
EXAMPLES_NEEDED = 3

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each pair has the same cell count but occupies a different D4 orbit.  A is
# fully asymmetric, giving distinct exact/rotation/reflection labels.  B only
# needs to be connected and unrelated.  Curated shapes avoid rejection loops
# and make the anti-shortcut guarantee deterministic.
_MOTIF_PAIRS: dict[int, tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]] = {
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 3)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _dihedral(
    cells: Iterable[tuple[int, int]], transform: int
) -> tuple[tuple[int, int], ...]:
    """Return one of the four rotations or four reflected rotations."""
    transformed: list[tuple[int, int]] = []
    for row, col in cells:
        if transform == 0:
            point = (row, col)
        elif transform == 1:
            point = (col, -row)
        elif transform == 2:
            point = (-row, -col)
        elif transform == 3:
            point = (-col, row)
        elif transform == 4:
            point = (row, -col)
        elif transform == 5:
            point = (-col, -row)
        elif transform == 6:
            point = (-row, col)
        elif transform == 7:
            point = (col, row)
        else:
            raise ValueError(f"transform must be 0..7, got {transform!r}")
        transformed.append(point)
    return _normalize(transformed)


def _orbit(cells: Iterable[tuple[int, int]], transforms: range) -> set[tuple[tuple[int, int], ...]]:
    return {_dihedral(cells, transform) for transform in transforms}


def _validate_catalog() -> None:
    for cell_count, (left, right) in _MOTIF_PAIRS.items():
        if len(left) != cell_count or len(right) != cell_count:
            raise AssertionError(f"motif catalog count mismatch for {cell_count}")
        if len(_orbit(left, range(8))) != 8:
            raise AssertionError(f"left motif for {cell_count} is not asymmetric")
        if _orbit(left, range(8)) & _orbit(right, range(8)):
            raise AssertionError(f"motifs for {cell_count} share a D4 orbit")


_validate_catalog()


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if "n_panels" in overrides and overrides["n_panels"] is not None:
        value = overrides["n_panels"]
        if type(value) is not int:
            raise TypeError("n_panels must be an integer (booleans are not accepted)")
        if not 3 <= value <= 5:
            raise ValueError(f"n_panels={value} outside declared range 3..5")


def _draw_scheduled_n_panels(ctx) -> int:
    if ctx.overrides.get("n_panels") is not None:
        return ctx.draw_int("n_panels", 3, 5)
    return ctx.draw_int("n_panels", 5, 5)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic four-slot lesson profile."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _cell_count(rng, difficulty: Any) -> int:
    choices = {
        "easy": (4, 5),
        "medium": (5, 6, 7),
        "hard": (6, 7, 8),
        None: (4, 5, 6, 7, 8),
    }[difficulty]
    return rng.choice(choices)


def _profile_tokens(profile: str, n_panels: int) -> tuple[str, ...]:
    profiles = {
        "full_relations": {
            3: ("a", "f", "b"),
            4: ("a", "r", "f", "b"),
            5: ("a", "a", "r", "f", "b"),
        },
        "rotation_duplicate": {
            3: ("a", "f", "b"),
            4: ("a", "a", "f", "b"),
            5: ("a", "r", "r", "f", "b"),
        },
        "two_rotations": {
            3: ("a", "f", "b"),
            4: ("a", "r2", "f", "b"),
            5: ("a", "r", "r2", "f", "b"),
        },
        "paired_classes": {
            3: ("a", "f", "b"),
            4: ("a", "f", "b", "b"),
            5: ("a", "f", "b", "b", "r"),
        },
    }
    return profiles[profile][n_panels]


def _palette(rng, sample_index: int, n_panels: int) -> tuple[int, ...]:
    # Slots 0/1 are canonical one-color anchors; slots 2/3 prove that color is
    # irrelevant. Any sliding three-demo window therefore contains a varied
    # palette while 50% of default draws exactly match the canonical profile.
    colors = list(range(1, 10))
    if sample_index % 4 in (0, 1):
        color = rng.choice(colors)
        return (color,) * n_panels
    chosen = rng.sample(colors, min(3, n_panels))
    return tuple(chosen[index % len(chosen)] for index in range(n_panels))


def _place_shape(
    grid: list[list[int]],
    panel_index: int,
    cells: Sequence[tuple[int, int]],
    color: int,
    rng,
) -> None:
    height = max(row for row, _col in cells) + 1
    width = max(col for _row, col in cells) + 1
    top = rng.randint(0, 5 - height)
    left = rng.randint(0, 5 - width)
    panel_col = 6 * panel_index
    for row, col in cells:
        grid[top + row][panel_col + left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_panels = _draw_scheduled_n_panels(ctx)
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = ctx.draw_rng("scene")

    count = _cell_count(rng, difficulty)
    base_a, base_b = _MOTIF_PAIRS[count]
    base_rotation = rng.randrange(4)
    a = _dihedral(base_a, base_rotation)
    variants = {
        "a": a,
        "r": _dihedral(a, 1),
        "r2": _dihedral(a, 2),
        "f": _dihedral(a, 4),
        "b": _dihedral(base_b, rng.randrange(8)),
    }
    tokens = list(_profile_tokens(profile, n_panels))
    # Relation semantics depend on pairwise shape classes, not a privileged
    # panel position. Shuffling the constructive multiset preserves every
    # witness while preventing four memorized matrices from becoming the task.
    rng.shuffle(tokens)
    colors = _palette(rng, sample_index, n_panels)

    grid = full_grid(5, 6 * n_panels - 1, 0)
    for panel_index, (token, color) in enumerate(zip(tokens, colors)):
        _place_shape(grid, panel_index, variants[token], color, rng)
    return grid


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for drow, dcol in _CARDINAL:
            neighbor = (row + drow, col + dcol)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(cells)


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list"]
    if any(not isinstance(row, list) for row in grid):
        return {}, ["every grid row must be a list"]
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular with nonempty rows"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be integer ARC colors 0..9")

    height = len(grid)
    if height != 5 or (width + 1) % 6 != 0:
        return {}, errors + [f"expected 5 x (6*N-1) panel grid, got {height}x{width}"]
    n_panels = (width + 1) // 6
    if not 3 <= n_panels <= 5:
        errors.append(f"expected 3..5 panels, got {n_panels}")

    panels: list[tuple[tuple[int, int], ...]] = []
    panel_colors: list[int | None] = []
    panel_counts: list[int] = []
    for panel_index in range(n_panels):
        if panel_index < n_panels - 1:
            separator = 6 * panel_index + 5
            if any(grid[row][separator] != 0 for row in range(5)):
                errors.append(f"separator column {separator} must be blank")

        start_col = 6 * panel_index
        cells: set[tuple[int, int]] = set()
        colors: set[int] = set()
        for row in range(5):
            for local_col in range(5):
                value = grid[row][start_col + local_col]
                if value != 0:
                    cells.add((row, local_col))
                    colors.add(value)
        panel_counts.append(len(cells))
        panels.append(_normalize(cells))
        panel_colors.append(next(iter(colors)) if len(colors) == 1 else None)
        if not 4 <= len(cells) <= 8:
            errors.append(
                f"panel {panel_index} must contain 4..8 nonzero cells, got {len(cells)}"
            )
        if len(colors) != 1:
            errors.append(
                f"panel {panel_index} must use exactly one nonzero color, got {sorted(colors)}"
            )
        if cells and not _connected(cells):
            errors.append(f"panel {panel_index} support must be 4-connected")

    return {
        "height": height,
        "width": width,
        "n_panels": n_panels,
        "panels": tuple(panels),
        "panel_colors": tuple(panel_colors),
        "panel_counts": tuple(panel_counts),
    }, errors


def observe_overrides(grid) -> dict[str, int]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {"n_panels": int(facts["n_panels"])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        if "n_panels" in meta:
            requested["n_panels"] = meta["n_panels"]
    if not errors and requested.get("n_panels") is not None:
        if facts["n_panels"] != requested["n_panels"]:
            errors.append(
                f"override n_panels requested {requested['n_panels']!r}, "
                f"observed {facts['n_panels']!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical task grammar; panel count and colors are incidental."""
    return self_check(grid)


def _relation(left, right) -> int:
    if right == left:
        return 1
    if right in _orbit(left, range(4)):
        return 2
    if right in _orbit(left, range(8)):
        return 3
    return 0


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket rule."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed input: " + "; ".join(errors))
    panels = facts["panels"]
    return [
        [8 if row == col else _relation(panels[row], panels[col]) for col in range(len(panels))]
        for row in range(len(panels))
    ]


def _rival_reflection_as_rotation(grid) -> list[list[int]]:
    return [[2 if value == 3 else value for value in row] for row in rule_mirror(grid)]


def _rival_same_count_implies_rotation(grid) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed input: " + "; ".join(errors))
    output = rule_mirror(grid)
    counts = facts["panel_counts"]
    for row in range(len(output)):
        for col in range(len(output)):
            if row != col and output[row][col] == 0 and counts[row] == counts[col]:
                output[row][col] = 2
    return output


def _rival_color_sensitive(grid) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("malformed input: " + "; ".join(errors))
    output = rule_mirror(grid)
    colors = facts["panel_colors"]
    for row in range(len(output)):
        for col in range(len(output)):
            if row != col and output[row][col] in (1, 2, 3) and colors[row] != colors[col]:
                output[row][col] = 0
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reflection_as_rotation": _rival_reflection_as_rotation,
    "same_count_implies_rotation": _rival_same_count_implies_rotation,
    "color_sensitive": _rival_color_sensitive,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "same_count_implies_rotation": _rival_same_count_implies_rotation,
    "color_sensitive": _rival_color_sensitive,
}


def _witness_same_count_unrelated(grid) -> bool:
    try:
        facts, errors = _analyze(grid)
        if errors:
            return False
        official = rule_mirror(grid)
        counts = facts["panel_counts"]
        return any(
            official[row][col] == 0 and counts[row] == counts[col]
            for row in range(len(official))
            for col in range(row + 1, len(official))
        )
    except Exception:
        return False


def _witness_cross_color_related(grid) -> bool:
    try:
        facts, errors = _analyze(grid)
        if errors:
            return False
        official = rule_mirror(grid)
        colors = facts["panel_colors"]
        return any(
            official[row][col] in (1, 2, 3) and colors[row] != colors[col]
            for row in range(len(official))
            for col in range(row + 1, len(official))
        )
    except Exception:
        return False


def _witness_reflection_relation(grid) -> bool:
    try:
        return any(value == 3 for row in rule_mirror(grid) for value in row)
    except Exception:
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "same_count_unrelated": _witness_same_count_unrelated,
    "cross_color_related": _witness_cross_color_related,
    "reflection_relation": _witness_reflection_relation,
}
WITNESS_RIVALS = {
    "same_count_unrelated": ["same_count_implies_rotation"],
    "cross_color_related": ["color_sensitive"],
    "reflection_relation": ["reflection_as_rotation"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared rival left able to change the query answer."""
    reasons: list[str] = []
    if len(demos) != EXAMPLES_NEEDED:
        reasons.append(f"expected {EXAMPLES_NEEDED} demos, received {len(demos)}")

    valid_demos: list[tuple[list[list[int]], list[list[int]]]] = []
    for index, pair in enumerate(demos):
        grid = pair.get("input") if isinstance(pair, dict) else None
        output = pair.get("output") if isinstance(pair, dict) else None
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {'; '.join(errors)}")
        elif output != rule_mirror(grid):
            reasons.append(f"demo {index} output does not match the pinned rule")
        else:
            valid_demos.append((grid, output))

    query_grid = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query malformed: {'; '.join(query_errors)}")
    elif query_output != rule_mirror(query_grid):
        reasons.append("query output does not match the pinned rule")

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(competitor(grid) == output for grid, output in valid_demos)
            changes_query = competitor(query_grid) != query_output
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
