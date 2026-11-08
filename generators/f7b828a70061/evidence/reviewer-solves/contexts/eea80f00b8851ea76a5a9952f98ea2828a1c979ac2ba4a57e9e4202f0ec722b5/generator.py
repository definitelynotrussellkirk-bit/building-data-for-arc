"""Canonical-profile sampler for the marker/rotation/crop ARC task.

The command at (0, 0) chooses the output rotation.  After clearing that cell,
the authority selects the largest color-insensitive 4-connected component,
crops its bounding box, and rotates the crop: 2 identity, 3 clockwise,
4 half-turn, and 5 counter-clockwise.

The five canonical (height, width, palette-size) profiles are cycled exactly.
Every generated lesson contains a uniquely largest 6--8-cell component and a
smaller 5-cell decoy.  Both components span a 3x3 bounding box, while the decoy
is earlier in reading order.  Therefore the plausible canonical-fitting
shortcut "select the component with largest bounding-box area" is guaranteed to
choose the decoy, whereas the intended cell-count rule chooses the main object.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7b828a70061"
TASK_ID = GENERATOR_ID
RULE_HASH = "d95bdc7a1a1a"
VERSION = "3.1.0"
SUMMARY = (
    "Canonical-sized zero-background grids. An isolated command at (0,0) "
    "selects identity, clockwise, 180-degree, or counter-clockwise rotation. "
    "Choose the uniquely largest component by cell count, crop its bounding "
    "box, and rotate it. A smaller reading-order-first component has the same "
    "bounding-box area and explicitly refutes largest-bbox-area selection."
)

INVARIANTS = [
    "(0,0) is an isolated command in {2,3,4,5}",
    "the generated main component has 6..8 cells in a sparse 3x3 bounding box",
    "one external 5-cell component has the same 3x3 bbox area but occurs first",
    "the non-command palette has one or two colors and every grid profile is canonical",
]

AXES = {
    "grid_h": {"type": "int", "default": "five-profile schedule", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "five-profile schedule", "valid": "9..11"},
    "command": {"type": "int", "default": "cyclic 2,3,4,5", "valid": "2..5"},
    "main_size": {"type": "int", "default": "difficulty-weighted", "valid": "6..8"},
    "main_shape": {"type": "str", "default": "cyclic frame/stair", "valid": "frame|stair"},
    "palette_size": {"type": "int", "default": "profile-bound", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Seven demonstrations plus one query make two complete command cycles.  Any
# leave-one-out query rotation still leaves all four command meanings in demos.
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 1.0

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COMMANDS = (2, 3, 4, 5)
_MAIN_SHAPES = ("frame", "stair")
_CANONICAL_PROFILES = (
    (7, 9, 2),   # background + command + two body colors
    (8, 10, 2),
    (7, 10, 1),  # background + command + one body color
    (8, 9, 1),
    (9, 11, 2),
)
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_DECOY = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    int_domains = {
        "grid_h": (7, 9),
        "grid_w": (9, 11),
        "command": (2, 5),
        "main_size": (6, 8),
        "palette_size": (1, 2),
    }
    for name, (lo, hi) in int_domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be a literal Python integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value!r} is outside [{lo}, {hi}]")

    shape = overrides.get("main_shape")
    if shape is not None and (type(shape) is not str or shape not in _MAIN_SHAPES):
        raise ValueError(f"main_shape must be one of {_MAIN_SHAPES}, got {shape!r}")


def _draw_fixed_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_fixed_choice(ctx, name: str, choices, default):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, choices)
    return ctx.draw_choice(name, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_cells(kind: str, size: int) -> tuple[tuple[int, int], ...]:
    """Return connected, symmetry-distinguishable 3x3 shapes for sizes 6..8."""
    if not 6 <= size <= 8:
        raise ValueError(f"main shape size must be in 6..8, got {size}")
    if kind == "frame":
        order = (
            (0, 0), (0, 1), (0, 2), (1, 0),
            (2, 0), (2, 1), (2, 2), (1, 2),
        )
    elif kind == "stair":
        order = (
            (0, 0), (0, 1), (1, 1), (1, 2),
            (2, 1), (2, 2), (1, 0), (2, 0),
        )
    else:
        raise ValueError(f"unknown main shape {kind!r}")
    return _normalize(order[:size])


def _rot90(cells):
    return _normalize((c, -r) for r, c in cells)


def _reflect(cells):
    return _normalize((r, -c) for r, c in cells)


def _symmetries(cells) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants = set()
    current = _normalize(cells)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rot90(current)
    return tuple(sorted(variants))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    top, left, bottom, right = _bbox(cells)
    return (bottom - top + 1) * (right - left + 1)


def _outside_bbox(cell, bbox) -> bool:
    r, c = cell
    top, left, bottom, right = bbox
    return r < top or r > bottom or c < left or c > right


def _choose_layout(ctx, h: int, w: int, kind: str, size: int):
    """Place a reading-order-first 5-cell decoy and a larger main component.

    Both components span 3x3.  The decoy occupies columns 1..3 and the main
    occupies the right-side 3-column box, leaving at least one zero column
    between them for every declared width.
    """
    top = ctx.draw_rng("object_top").choice(tuple(range(2, h - 2)))
    decoy_shape = ctx.draw_rng("decoy_symmetry").choice(_symmetries(_DECOY))
    main_shape = ctx.draw_rng("main_symmetry").choice(
        _symmetries(_shape_cells(kind, size))
    )
    decoy_left = 1
    main_left = w - 4
    decoy = tuple((top + r, decoy_left + c) for r, c in decoy_shape)
    main = tuple((top + r, main_left + c) for r, c in main_shape)
    return main, decoy


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) == (0, 0) or grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            todo = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) != (0, 0)
                            and grid[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _ordered_components(grid):
    return sorted(_components(grid), key=lambda cells: (-len(cells), min(cells)))


def _shape_kind(cells) -> str:
    normalized = _normalize(cells)
    size = len(normalized)
    for kind in _MAIN_SHAPES:
        if normalized in _symmetries(_shape_cells(kind, size)):
            return kind
    raise ValueError("largest component is not a declared frame/stair shape")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w, default_palette = _CANONICAL_PROFILES[
        sample_index % len(_CANONICAL_PROFILES)
    ]
    h = _draw_fixed_int(ctx, "grid_h", 7, 9, default_h)
    w = _draw_fixed_int(ctx, "grid_w", 9, 11, default_w)
    command = _draw_fixed_int(ctx, "command", 2, 5, _COMMANDS[sample_index % 4])
    palette_size = _draw_fixed_int(ctx, "palette_size", 1, 2, default_palette)
    shape = _draw_fixed_choice(
        ctx, "main_shape", _MAIN_SHAPES, _MAIN_SHAPES[sample_index % len(_MAIN_SHAPES)]
    )

    size_choices = {
        None: (6, 7, 8),
        "easy": (6, 6, 7),
        "medium": (6, 7, 8),
        "hard": (7, 8, 8),
    }[difficulty]
    if overrides.get("main_size") is not None:
        main_size = ctx.draw_int_strict("main_size", 6, 8)
    else:
        main_size = ctx.draw_choice("main_size", size_choices)

    main, decoy = _choose_layout(ctx, h, w, shape, main_size)
    grid = full_grid(h, w, 0)
    grid[0][0] = command

    available_colors = [color for color in range(1, 10) if color != command]
    palette = ctx.draw_rng("object_palette").sample(available_colors, palette_size)

    # Force every declared body color to be visible in the main object, then
    # distribute the remaining colors deterministically through a named RNG.
    ordered_main = list(sorted(main))
    main_rng = ctx.draw_rng("main_colors")
    main_rng.shuffle(ordered_main)
    for index, (r, c) in enumerate(ordered_main):
        grid[r][c] = palette[index] if index < palette_size else main_rng.choice(palette)

    decoy_rng = ctx.draw_rng("decoy_colors")
    for r, c in decoy:
        grid[r][c] = decoy_rng.choice(palette)

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructive sampler violated its contract: " + "; ".join(findings))
    expected = {
        "grid_h": h,
        "grid_w": w,
        "command": command,
        "main_size": main_size,
        "main_shape": shape,
        "palette_size": palette_size,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"override observer drift: expected {expected}, got {observed}")
    if not _bbox_area_tie(grid):
        raise AssertionError("constructive sampler failed to refute largest-bbox-area selection")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    height = len(grid)
    errors = []
    if not 7 <= height <= 9 or not 9 <= width <= 11:
        errors.append(f"grid dimensions {height}x{width} outside 7..9 by 9..11")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be literal integer ARC colors 0..9")
        return errors

    command = grid[0][0]
    if command not in _COMMANDS:
        errors.append(f"control cell must be one of {_COMMANDS}, got {command!r}")
    if width > 1 and grid[0][1] != 0:
        errors.append("control cell must be isolated from the body at (0,1)")
    if height > 1 and grid[1][0] != 0:
        errors.append("control cell must be isolated from the body at (1,0)")

    components = _ordered_components(grid)
    if not components:
        errors.append("at least one non-command object is required")
        return errors
    if len(components) > 1 and len(components[0]) == len(components[1]):
        errors.append("largest object must be strictly unique by cell count")
    main = components[0]
    if not 3 <= len(main) <= 8:
        errors.append(f"largest object size {len(main)} outside canonical/generated range 3..8")
    main_bbox = _bbox(main)
    if _bbox_area(main) <= len(main):
        errors.append("largest object must be sparse inside its bounding box")

    distractors = components[1:]
    if len(distractors) > 1:
        errors.append(f"at most one smaller component is allowed, found {len(distractors)}")
    for component in distractors:
        if len(component) >= len(main):
            errors.append("every distractor must be smaller than the main component")
        if any(not _outside_bbox(cell, main_bbox) for cell in component):
            errors.append("every distractor cell must lie outside the main bounding box")

    body_colors = {
        value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    }
    if command in body_colors:
        errors.append("command color must be reserved for the isolated control cell")
    if not 1 <= len(body_colors) <= 2:
        errors.append(f"body palette must contain one or two colors, found {len(body_colors)}")
    return errors


def strict_canonical_like(grid):
    """Accept canonical inputs and the sampler's narrow source-shaped manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe controls on an invalid grid: " + "; ".join(findings))
    main = _ordered_components(grid)[0]
    body_colors = {
        value for r, row in enumerate(grid) for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "command": grid[0][0],
        "main_size": len(main),
        "main_shape": _shape_kind(main),
        "palette_size": len(body_colors),
    }


def _rotate(grid, command):
    if command == 2:
        return [list(row) for row in grid]
    if command == 3:
        return [list(row) for row in zip(*grid[::-1])]
    if command == 4:
        return [list(reversed(row)) for row in reversed(grid)]
    return [list(row) for row in zip(*grid)][::-1]


def _crop(grid, cells):
    top, left, bottom, right = _bbox(cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def _cleaned(grid):
    result = [list(row) for row in grid]
    result[0][0] = 0
    return result


def intended_output(grid):
    """Python mirror used only by semantic declarations and focused tests."""
    cleaned = _cleaned(grid)
    main = _ordered_components(grid)[0]
    return _rotate(_crop(cleaned, main), grid[0][0])


def _largest_bbox_area(grid):
    """Plausible canonical shortcut: select largest bbox area, ties top-left."""
    cleaned = _cleaned(grid)
    components = _components(grid)
    chosen = min(components, key=lambda cells: (-_bbox_area(cells), min(cells)))
    return _rotate(_crop(cleaned, chosen), grid[0][0])


def _bbox_area_tie(grid) -> bool:
    """Whether bbox-area selection ties and chooses a component other than main."""
    try:
        components = _components(grid)
        if len(components) < 2:
            return False
        intended = min(components, key=lambda cells: (-len(cells), min(cells)))
        rival = min(components, key=lambda cells: (-_bbox_area(cells), min(cells)))
        return intended != rival and _bbox_area(intended) == _bbox_area(rival)
    except (TypeError, ValueError, IndexError):
        return False


def lesson_identifiable(demos, query):
    """Require all command meanings and an explicit bbox-area shortcut refutation."""
    del query
    reasons = []
    try:
        commands = {pair["input"][0][0] for pair in demos}
    except (KeyError, TypeError, IndexError):
        return ["malformed demonstration pair"]
    missing = set(_COMMANDS) - commands
    if missing:
        reasons.append(f"demonstrations omit command(s) {sorted(missing)}")
    if not any(_bbox_area_tie(pair["input"]) for pair in demos):
        reasons.append("demonstrations do not refute largest-bounding-box-area selection")
    return reasons


SEMANTIC_WITNESSES = {"bbox_area_tie": _bbox_area_tie}
SEMANTIC_RIVALS = {"largest_bbox_area": _largest_bbox_area}
WITNESS_RIVALS = {"bbox_area_tie": ["largest_bbox_area"]}
CANONICAL_SHORTCUTS = {"largest_bbox_area": _largest_bbox_area}
LESSON_COMPETITORS = {"largest_bbox_area": _largest_bbox_area}
