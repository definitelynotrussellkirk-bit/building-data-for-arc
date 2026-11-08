"""Curriculum-safe generator for Commanded Template Mosaic (aea86d2776f1).

Four command cells select one of two fixed 3x3 templates and one of four
transforms.  The resulting tiles are concatenated into a 2x2 output mosaic.

Version 2 replaces the former padded-grid/random-palette sampler with a
source-bound four-profile curriculum.  Every four consecutive pair slots
contain an exact canonical-profile anchor plus counterexamples to three rivals
that fit every canonical demonstration: alternating template sources,
monochrome templates, and crop-before-transform templates.
"""
from __future__ import annotations

from itertools import combinations, product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aea86d2776f1"
TASK_ID = GENERATOR_ID
RULE_HASH = "5d25ec4af105"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A fixed 5x11 input holds four commands at row 0 columns 1,3,7,9 and "
    "two connected asymmetric 3x3 templates at rows 2-4, columns 1-3 and "
    "7-9. Commands 1-4 select the left template and 5-8 the right; their "
    "residue selects identity, clockwise rotation, horizontal flip, or 180° "
    "rotation. A four-profile schedule preserves exact canonical support and "
    "teaches source decoding, full-frame transforms, and multicolor fidelity."
)

INVARIANTS = [
    "input shape is exactly 5x11 and all non-designated cells are zero",
    "commands occupy (0,1), (0,3), (0,7), (0,9) and are ARC colors 1..8",
    "left and right templates occupy fixed 3x3 frames at rows 2..4",
    "both templates are referenced and at least two transform classes occur",
    "each generated template has 3..8 connected nonzero cells and 1..3 colors",
]

AXES = {
    "left_cells": {
        "type": "int",
        "default": "scheduled",
        "valid": "3..8",
    },
    "right_cells": {
        "type": "int",
        "default": "scheduled",
        "valid": "3..8",
    },
    "left_colors": {
        "type": "int",
        "default": "scheduled",
        "valid": "1..3",
    },
    "right_colors": {
        "type": "int",
        "default": "scheduled",
        "valid": "1..3",
    },
    "source_balance": {
        "type": "int",
        "default": "scheduled number of commands selecting the left template",
        "valid": "1..3",
    },
    "transform_count": {
        "type": "int",
        "default": "scheduled number of distinct transform residues",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

SCHEDULE_PROFILES = (
    "canonical_core",
    "multicolor_left",
    "multicolor_right",
    "dense_counterexample",
)
MIN_STRICT_FRAC = 1.0

_COMMAND_COLS = (1, 3, 7, 9)
_PANEL_SPECS = (("left", 1), ("right", 7))
_INT_DOMAINS = {
    "left_cells": tuple(range(3, 9)),
    "right_cells": tuple(range(3, 9)),
    "left_colors": tuple(range(1, 4)),
    "right_colors": tuple(range(1, 4)),
    "source_balance": tuple(range(1, 4)),
    "transform_count": tuple(range(2, 5)),
}
_PROFILE_DEFAULTS = {
    # Four distinct commands + two panel colors + background = canonical palette 7.
    "canonical_core": {
        "left_cells": 5,
        "right_cells": 5,
        "left_colors": 1,
        "right_colors": 1,
        "source_balance": 2,
        "transform_count": 4,
    },
    "multicolor_left": {
        "left_cells": 4,
        "right_cells": 6,
        "left_colors": 2,
        "right_colors": 1,
        "source_balance": 3,
        "transform_count": 3,
    },
    "multicolor_right": {
        "left_cells": 7,
        "right_cells": 3,
        "left_colors": 1,
        "right_colors": 3,
        "source_balance": 3,
        "transform_count": 2,
    },
    "dense_counterexample": {
        "left_cells": 4,
        "right_cells": 8,
        "left_colors": 2,
        "right_colors": 2,
        "source_balance": 1,
        "transform_count": 4,
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Repeat a four-pair source-bound lesson schedule in every band."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value} outside {domain[0]}..{domain[-1]}")


def _draw_axis(ctx, name: str, scheduled_value: int) -> int:
    """Expose every exact value while recording the scheduled default honestly."""
    value = ctx.draw_choice(name, _INT_DOMAINS[name])
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return value
    # GenCtx has no public scheduled-default setter. This is the same recording
    # path used by its typed draws and keeps provenance/override probes truthful.
    return ctx._record(name, scheduled_value, from_override=False)


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


_TRANSFORMS: tuple[Callable[[list[list[int]]], list[list[int]]], ...] = (
    _identity,
    _rotate_cw,
    _flip_lr,
    _rotate_180,
)


def _transform_cells(cells: frozenset[tuple[int, int]], transform: int):
    if transform == 0:
        return frozenset(cells)
    if transform == 1:
        return frozenset((c, 2 - r) for r, c in cells)
    if transform == 2:
        return frozenset((r, 2 - c) for r, c in cells)
    return frozenset((2 - r, 2 - c) for r, c in cells)


def _connected(cells: frozenset[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return len(seen) == len(cells)


def _shape_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    cells = tuple(product(range(3), repeat=2))
    result: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 9):
        candidates = []
        for choice in combinations(cells, size):
            shape = frozenset(choice)
            if not _connected(shape):
                continue
            # All four command transforms must remain visibly distinguishable.
            if len({_transform_cells(shape, kind) for kind in range(4)}) != 4:
                continue
            candidates.append(tuple(sorted(shape)))
        result[size] = tuple(candidates)
    return result


_SHAPES = _shape_catalog()


def _full_bbox(shape: tuple[tuple[int, int], ...]) -> bool:
    return ({r for r, _ in shape} >= {0, 2}) and ({c for _, c in shape} >= {0, 2})


def _offset_bbox(shape: tuple[tuple[int, int], ...]) -> bool:
    return min(r for r, _ in shape) > 0 or min(c for _, c in shape) > 0


def _choose_shape(ctx, label: str, size: int, *, full_bbox=False, offset_bbox=False):
    candidates = list(_SHAPES[size])
    if full_bbox:
        candidates = [shape for shape in candidates if _full_bbox(shape)]
    if offset_bbox:
        candidates = [shape for shape in candidates if _offset_bbox(shape)]
    if not candidates:
        raise RuntimeError(
            f"no asymmetric connected 3x3 shape for {label}: size={size}, "
            f"full_bbox={full_bbox}, offset_bbox={offset_bbox}"
        )
    return ctx.draw_rng(f"{label}_shape").choice(candidates)


def _source_pattern(ctx, balance: int) -> list[int]:
    """Return 0=A/1=B sources, deliberately excluding strict alternation."""
    candidates = []
    for pattern in product((0, 1), repeat=4):
        if pattern.count(0) != balance:
            continue
        if pattern in ((0, 1, 0, 1), (1, 0, 1, 0)):
            continue
        candidates.append(pattern)
    if not candidates:
        raise RuntimeError(f"no nonalternating source pattern for balance {balance}")
    return list(ctx.draw_rng("source_pattern").choice(candidates))


def _transform_pattern(ctx, count: int) -> list[int]:
    rng = ctx.draw_rng("transform_pattern")
    chosen = rng.sample(range(4), count)
    residues = list(chosen)
    while len(residues) < 4:
        residues.append(rng.choice(chosen))
    rng.shuffle(residues)
    return residues


def _assign_colors(ctx, label: str, shape, colors: list[int]) -> list[list[int]]:
    rng = ctx.draw_rng(f"{label}_coloring")
    points = list(shape)
    rng.shuffle(points)
    values = list(colors)
    values.extend(rng.choice(colors) for _ in range(len(points) - len(colors)))
    rng.shuffle(values)
    panel = full_grid(3, 3, 0)
    for (r, c), value in zip(points, values):
        panel[r][c] = value
    return panel


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    """Generate one deterministic lawful input; exact axes override the schedule."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _PROFILE_DEFAULTS[profile]
    values = {
        name: _draw_axis(ctx, name, defaults[name])
        for name in _INT_DOMAINS
    }

    sources = _source_pattern(ctx, values["source_balance"])
    transforms = _transform_pattern(ctx, values["transform_count"])
    # Difficulty changes the command colors through a residue bijection rather
    # than changing the declared task domain. This prevents dead curriculum
    # bands while preserving source balance, transform count, and profile size.
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    transforms = [(residue + band_offset) % 4 for residue in transforms]
    commands = [residue + (1 if source == 0 else 5) for source, residue in zip(sources, transforms)]

    # The canonical anchor spans the full frame, preserving the exact
    # 5x11/palette-7 profile. Every non-core scheduled profile includes an
    # offset bounding box, making crop-before-transform observably wrong.
    full_frame = profile == "canonical_core" and not overrides
    offset_side = None
    if not full_frame:
        if values["left_cells"] <= 5:
            offset_side = "left"
        elif values["right_cells"] <= 5:
            offset_side = "right"

    left_shape = _choose_shape(
        ctx,
        "left",
        values["left_cells"],
        full_bbox=full_frame,
        offset_bbox=offset_side == "left",
    )
    right_shape = _choose_shape(
        ctx,
        "right",
        values["right_cells"],
        full_bbox=full_frame,
        offset_bbox=offset_side == "right",
    )

    panel_color_count = values["left_colors"] + values["right_colors"]
    palette_rng = ctx.draw_rng("panel_palette")
    available = list(range(1, 10))
    palette_rng.shuffle(available)
    command_colors = set(commands)
    # Prefer command-disjoint colors. For the core profile this guarantees the
    # exact seven-color canonical signature; broad profiles may lawfully reuse.
    available.sort(key=lambda color: color in command_colors)
    palette = available[:panel_color_count]
    left_palette = palette[: values["left_colors"]]
    right_palette = palette[values["left_colors"] :]

    left = _assign_colors(ctx, "left", left_shape, left_palette)
    right = _assign_colors(ctx, "right", right_shape, right_palette)

    grid = full_grid(5, 11, 0)
    for col, command in zip(_COMMAND_COLS, commands):
        grid[0][col] = command
    for r in range(3):
        for c in range(3):
            grid[2 + r][1 + c] = left[r][c]
            grid[2 + r][7 + c] = right[r][c]
    return grid


def _rectangular_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    copied = [list(row) for row in grid]
    if any(type(value) is not int or not 0 <= value <= 9 for row in copied for value in row):
        return None, ["cells must be integer ARC colors 0..9"]
    return copied, []


def _panels(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    return (
        [row[1:4] for row in grid[2:5]],
        [row[7:10] for row in grid[2:5]],
    )


def _panel_stats(panel: list[list[int]]) -> tuple[int, int, bool]:
    cells = frozenset((r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value)
    colors = {value for row in panel for value in row if value}
    return len(cells), len(colors), _connected(cells)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the fixed command/template grammar without throwing."""
    del difficulty, meta
    grid, errors = _rectangular_grid(grid)
    if errors:
        return errors
    assert grid is not None
    if (len(grid), len(grid[0])) != (5, 11):
        return [f"expected exact 5x11 input, got {len(grid)}x{len(grid[0])}"]

    allowed = {(0, col) for col in _COMMAND_COLS}
    allowed.update((r, c) for r in range(2, 5) for c in range(1, 4))
    allowed.update((r, c) for r in range(2, 5) for c in range(7, 10))
    outside = [(r, c) for r in range(5) for c in range(11) if (r, c) not in allowed and grid[r][c] != 0]
    if outside:
        errors.append(f"nonzero cell outside fixed command/panel regions at {outside[0]}")

    commands = [grid[0][col] for col in _COMMAND_COLS]
    if any(command not in range(1, 9) for command in commands):
        errors.append("four command cells must each be in 1..8")
    else:
        balance = sum(command <= 4 for command in commands)
        if balance not in _INT_DOMAINS["source_balance"]:
            errors.append("commands must reference both templates")
        transform_count = len({(command - 1) % 4 for command in commands})
        if transform_count not in _INT_DOMAINS["transform_count"]:
            errors.append("commands must contain 2..4 distinct transform classes")

    for (name, _), panel in zip(_PANEL_SPECS, _panels(grid)):
        cells, colors, connected = _panel_stats(panel)
        if cells not in _INT_DOMAINS[f"{name}_cells"]:
            errors.append(f"{name} template needs 3..8 nonzero cells, found {cells}")
        if colors not in _INT_DOMAINS[f"{name}_colors"]:
            errors.append(f"{name} template needs 1..3 nonzero colors, found {colors}")
        if cells and not connected:
            errors.append(f"{name} template occupancy must be 4-connected")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] exactly for inputs in this generator's intended grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    left, right = _panels(grid)
    commands = [grid[0][col] for col in _COMMAND_COLS]
    return {
        "left_cells": sum(value != 0 for row in left for value in row),
        "right_cells": sum(value != 0 for row in right for value in row),
        "left_colors": len({value for row in left for value in row if value}),
        "right_colors": len({value for row in right for value in row if value}),
        "source_balance": sum(command <= 4 for command in commands),
        "transform_count": len({(command - 1) % 4 for command in commands}),
    }


def _decode(command: int) -> tuple[int, int]:
    return (0 if command <= 4 else 1), (command - 1) % 4


def _mosaic(tiles: list[list[list[int]]]) -> list[list[int]]:
    return [tiles[0][r] + tiles[1][r] for r in range(3)] + [
        tiles[2][r] + tiles[3][r] for r in range(3)
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Readable Python mirror; the pinned canonical Racket program is authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    panels = _panels(grid)
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[source]))
    return _mosaic(tiles)


def _alternating_sources(grid: list[list[int]]) -> list[list[int]]:
    """Rival: use only the first source bit, then alternate A/B by tile."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    panels = _panels(grid)
    first_source, _ = _decode(grid[0][_COMMAND_COLS[0]])
    tiles = []
    for index, col in enumerate(_COMMAND_COLS):
        _, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[(first_source + index) % 2]))
    return _mosaic(tiles)


def _monochrome_templates(grid: list[list[int]]) -> list[list[int]]:
    """Rival: keep occupancy but replace each template by its first color."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    collapsed = []
    for panel in _panels(grid):
        colors = [value for row in panel for value in row if value]
        color = colors[0]
        collapsed.append([[color if value else 0 for value in row] for row in panel])
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](collapsed[source]))
    return _mosaic(tiles)


def _crop_top_left(panel: list[list[int]]) -> list[list[int]]:
    points = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value]
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    r1 = max(r for r, _ in points)
    c1 = max(c for _, c in points)
    result = full_grid(3, 3, 0)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            result[r - r0][c - c0] = panel[r][c]
    return result


def _cropped_templates(grid: list[list[int]]) -> list[list[int]]:
    """Rival: crop each template to its nonzero bbox before transforming."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    panels = tuple(_crop_top_left(panel) for panel in _panels(grid))
    tiles = []
    for col in _COMMAND_COLS:
        source, transform = _decode(grid[0][col])
        tiles.append(_TRANSFORMS[transform](panels[source]))
    return _mosaic(tiles)


def _nonalternating_source_witness(grid) -> bool:
    if self_check(grid):
        return False
    sources = tuple(0 if grid[0][col] <= 4 else 1 for col in _COMMAND_COLS)
    return sources not in ((0, 1, 0, 1), (1, 0, 1, 0))


def _multicolor_template_witness(grid) -> bool:
    if self_check(grid):
        return False
    return any(len({value for row in panel for value in row if value}) > 1 for panel in _panels(grid))


def _offset_bbox_witness(grid) -> bool:
    if self_check(grid):
        return False
    return any(_crop_top_left(panel) != panel for panel in _panels(grid))


SEMANTIC_WITNESSES = {
    "nonalternating_sources": _nonalternating_source_witness,
    "multicolor_template": _multicolor_template_witness,
    "offset_template_bbox": _offset_bbox_witness,
}
SEMANTIC_RIVALS = {
    "alternating_sources": _alternating_sources,
    "monochrome_templates": _monochrome_templates,
    "cropped_templates": _cropped_templates,
}
WITNESS_RIVALS = {
    "nonalternating_sources": ["alternating_sources"],
    "multicolor_template": ["monochrome_templates"],
    "offset_template_bbox": ["cropped_templates"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def semantic_signature(grid) -> dict[str, Any]:
    """Small reusable summary for qualification and future review agents."""
    observed = observe_overrides(grid)
    observed.update(
        {
            "source_pattern": tuple(0 if grid[0][col] <= 4 else 1 for col in _COMMAND_COLS),
            "transform_pattern": tuple((grid[0][col] - 1) % 4 for col in _COMMAND_COLS),
            "palette_size": len({value for row in grid for value in row}),
            "witnesses": tuple(
                name for name, predicate in SEMANTIC_WITNESSES.items() if predicate(grid)
            ),
        }
    )
    return observed


def lesson_identifiable(demos, query) -> list[str]:
    """Report surviving declared competitors that would change the query."""
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return [f"query input malformed: {'; '.join(query_errors)}"]
    truth = rule_mirror(query_input)
    reasons: list[str] = []
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict):
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(demo.get("input"))
        if errors:
            reasons.append(f"demo {index} input malformed: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo["input"])
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the intended rule")
            continue
        valid_demos.append(demo)
    if reasons:
        return sorted(set(reasons))
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            if rival(query_input) != truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but changes the query"
                )
    return reasons
