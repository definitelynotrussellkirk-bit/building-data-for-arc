"""Generator for ARC task 1ce259f214c8: XOR two side-by-side masks.

A full-height gray (5) divider splits an input into equal left/right panels.
Each panel contains one 4-connected, monochrome object.  The output is one
panel wide and colors a cell 8 exactly when that relative cell is occupied in
one panel but not the other.

Every scene contains overlap, left-only, and right-only cells.  The linked
eighteen-slot curriculum keeps one-third exact canonical 5x11 inset scenes and
rotates three generalized corner-relation phases.  Every five consecutive
samples contain all three phases, so each fixed corner is observed as
left-only, right-only, and overlap.  This refutes seventy canonical-compatible
Boolean shortcuts that apply a different operation only to an output edge, the
corner set, or one particular corner.
"""
from __future__ import annotations

import hashlib
from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ce259f214c8"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "8b24eb18c704"
SUMMARY = (
    "Two monochrome connected masks occupy equal panels separated by a full "
    "gray column; output 8 at relative cells occupied by exactly one mask."
)
EXAMPLES_NEEDED = 5

INVARIANTS = [
    "height is 4..9 and each panel width is 3..8",
    "one full-height column of 5 splits the grid into equal-width panels",
    "each panel contains one nonempty 4-connected monochrome object",
    "the two object colors are distinct nonzero colors other than 5",
    "overlap, left-only, and right-only relative cells are all present",
    "generalized corner relations follow one of three declared phases",
    "every five consecutive scheduled samples include all three corner phases",
    "six of every eighteen scheduled samples use exact canonical geometry",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "one-third canonical 5; otherwise difficulty-aware 4..9",
        "valid": "4..9",
    },
    "half_w": {
        "type": "int",
        "default": "one-third canonical 5; otherwise difficulty-aware 3..8",
        "valid": "3..8",
    },
    "left_color": {
        "type": "color",
        "default": "keyed nonzero color excluding 5 and right_color",
        "valid": "1..9 (≠5)",
    },
    "right_color": {
        "type": "color",
        "default": "keyed nonzero color excluding 5 and left_color",
        "valid": "1..9 (≠5)",
    },
}

_OBJECT_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"left_color": color, "right_color": color} for color in _OBJECT_COLORS
]

SCHEDULE_PROFILES = ("canonical", "generalized")
CORNER_RELATION_PHASES = (
    ("left_only", "right_only", "overlap", "left_only"),
    ("right_only", "overlap", "left_only", "right_only"),
    ("overlap", "left_only", "right_only", "overlap"),
)
# Six canonical slots and twelve generalized slots.  Generalized phases follow
# 0,1,2 repeatedly while canonical slots occur after each pair of generalized
# slots.  Consequently every circular five-slot window has at least three
# generalized scenes and contains all three phases.  Seed-dependent rotation
# avoids tying an absolute sample-index residue to one profile or phase.
_SCHEDULE_CYCLE = (
    ("canonical", None),
    ("generalized", 0),
    ("generalized", 1),
    ("canonical", None),
    ("generalized", 2),
    ("generalized", 0),
    ("canonical", None),
    ("generalized", 1),
    ("generalized", 2),
    ("canonical", None),
    ("generalized", 0),
    ("generalized", 1),
    ("canonical", None),
    ("generalized", 2),
    ("generalized", 0),
    ("canonical", None),
    ("generalized", 1),
    ("generalized", 2),
)

_BAND_RANGES = {
    "easy": ((4, 6), (3, 5)),
    "medium": ((5, 7), (4, 6)),
    "hard": ((7, 9), (6, 8)),
}


def _schedule_entry(
    seed: int, sample_index: int, difficulty: Any = None
) -> tuple[str, int | None]:
    del difficulty
    digest = hashlib.sha256(
        f"{TASK_ID}|{VERSION}|{seed!r}|profile".encode("utf-8")
    ).digest()
    offset = int.from_bytes(digest[:8], "big") % len(_SCHEDULE_CYCLE)
    return _SCHEDULE_CYCLE[(int(sample_index) + offset) % len(_SCHEDULE_CYCLE)]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the linked curriculum profile for one sequential sample."""
    return _schedule_entry(seed, sample_index, difficulty)[0]


def schedule_corner_phase(
    seed: int, sample_index: int, difficulty: Any = None
) -> int | None:
    """Return 0..2 for generalized slots and ``None`` for canonical slots."""
    return _schedule_entry(seed, sample_index, difficulty)[1]


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return str(difficulty)


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in overrides.items() if v is not None}
    unknown = sorted(set(out) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    return out


def _draw_banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    if label in overrides:
        return int(ctx.draw_int(label, valid_lo, valid_hi))
    return int(ctx.draw_int(label, lo, hi))


def _neighbors(cell: tuple[int, int], allowed: set[tuple[int, int]]):
    r, c = cell
    for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if nb in allowed:
            yield nb


def _grow_connected(rng, allowed: set[tuple[int, int]], target: int):
    start = rng.choice(tuple(sorted(allowed)))
    cells = {start}
    frontier = set(_neighbors(start, allowed))
    while len(cells) < target and frontier:
        cell = rng.choice(tuple(sorted(frontier)))
        frontier.remove(cell)
        cells.add(cell)
        frontier.update(nb for nb in _neighbors(cell, allowed) if nb not in cells)
    return cells


def _component_count(mask: Iterable[tuple[int, int]]) -> int:
    remaining = set(mask)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for nb in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nb in remaining:
                    remaining.remove(nb)
                    stack.append(nb)
    return count


def _relation_counts(left, right):
    return {
        "overlap": len(left & right),
        "left_only": len(left - right),
        "right_only": len(right - left),
    }


def _border_xor_count(
    left: set[tuple[int, int]],
    right: set[tuple[int, int]],
    h: int,
    half: int,
) -> int:
    return sum(
        r in (0, h - 1) or c in (0, half - 1)
        for r, c in left ^ right
    )


def _random_path_to_tree(
    rng,
    start: tuple[int, int],
    tree: set[tuple[int, int]],
    allowed: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Return a randomized shortest path from ``start`` to ``tree``."""
    if start in tree:
        return [start]
    queue = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while queue:
        cell = queue.popleft()
        neighbors = list(_neighbors(cell, allowed))
        rng.shuffle(neighbors)
        for neighbor in neighbors:
            if neighbor in parent:
                continue
            parent[neighbor] = cell
            if neighbor in tree:
                path = [neighbor]
                cursor: tuple[int, int] | None = cell
                while cursor is not None:
                    path.append(cursor)
                    cursor = parent[cursor]
                return path
            queue.append(neighbor)
    raise RuntimeError("required cells cannot be connected inside the allowed panel")


def _connected_required_mask(
    rng,
    required: set[tuple[int, int]],
    allowed: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    """Connect required cells, then add keyed growth for shape diversity."""
    if not required or not required <= allowed:
        raise ValueError("required mask cells must be a nonempty subset of allowed")
    order = list(sorted(required))
    rng.shuffle(order)
    cells = {order[0]}
    for target in order[1:]:
        cells.update(_random_path_to_tree(rng, target, cells, allowed))

    density = rng.uniform(0.38, 0.68)
    target_hi = min(len(allowed), max(len(cells), round(len(allowed) * density)))
    target = rng.randint(len(cells), target_hi) if target_hi > len(cells) else len(cells)
    frontier = {
        neighbor
        for cell in cells
        for neighbor in _neighbors(cell, allowed)
        if neighbor not in cells
    }
    while len(cells) < target and frontier:
        cell = rng.choice(tuple(sorted(frontier)))
        frontier.remove(cell)
        cells.add(cell)
        frontier.update(
            neighbor
            for neighbor in _neighbors(cell, allowed)
            if neighbor not in cells
        )
    return cells


def _corner_cells(h: int, half: int) -> tuple[tuple[int, int], ...]:
    return ((0, 0), (0, half - 1), (h - 1, 0), (h - 1, half - 1))


def _corner_relations(
    left: set[tuple[int, int]],
    right: set[tuple[int, int]],
    h: int,
    half: int,
) -> list[str]:
    relations = []
    for cell in _corner_cells(h, half):
        in_left, in_right = cell in left, cell in right
        if in_left and in_right:
            relations.append("overlap")
        elif in_left:
            relations.append("left_only")
        elif in_right:
            relations.append("right_only")
        else:
            relations.append("empty")
    return relations


def _draw_generalized_masks(rng, h: int, half: int, corner_phase: int):
    expected = CORNER_RELATION_PHASES[corner_phase]
    all_cells = {(r, c) for r in range(h) for c in range(half)}
    corners = _corner_cells(h, half)
    left_required = {
        cell
        for cell, relation in zip(corners, expected)
        if relation in ("left_only", "overlap")
    }
    right_required = {
        cell
        for cell, relation in zip(corners, expected)
        if relation in ("right_only", "overlap")
    }
    left_forbidden = {
        cell
        for cell, relation in zip(corners, expected)
        if relation == "right_only"
    }
    right_forbidden = {
        cell
        for cell, relation in zip(corners, expected)
        if relation == "left_only"
    }
    left = _connected_required_mask(rng, left_required, all_cells - left_forbidden)
    right = _connected_required_mask(rng, right_required, all_cells - right_forbidden)
    if tuple(_corner_relations(left, right, h, half)) != expected:
        raise AssertionError("constructed masks violated their corner relation phase")
    return left, right


def _draw_masks(
    rng,
    h: int,
    half: int,
    canonical_geometry: bool,
    corner_phase: int | None,
):
    if not canonical_geometry:
        if corner_phase not in (0, 1, 2):
            raise ValueError("generalized masks require corner phase 0, 1, or 2")
        return _draw_generalized_masks(rng, h, half, int(corner_phase))

    allowed = {(r, c) for r in range(1, h - 1) for c in range(1, half - 1)}
    size_lo, size_hi = 5, 8
    size_hi = max(size_lo, min(size_hi, len(allowed) - 1))
    for _ in range(500):
        left = _grow_connected(rng, allowed, rng.randint(size_lo, size_hi))
        right = _grow_connected(rng, allowed, rng.randint(size_lo, size_hi))
        if all(_relation_counts(left, right).values()):
            return left, right
    raise RuntimeError("failed to construct a lawful canonical XOR mask pair")


def _draw_colors(ctx, overrides):
    requested_left = overrides.get("left_color")
    requested_right = overrides.get("right_color")
    if requested_left is not None and int(requested_left) in (0, 5):
        raise ValueError("left_color must be a nonzero color other than 5")
    if requested_right is not None and int(requested_right) in (0, 5):
        raise ValueError("right_color must be a nonzero color other than 5")
    if (
        requested_left is not None
        and requested_right is not None
        and int(requested_left) == int(requested_right)
    ):
        raise ValueError("left_color and right_color must be distinct")

    left_exclude = {0, 5}
    if requested_right is not None:
        left_exclude.add(int(requested_right))
    left = int(ctx.draw_color("left_color", exclude=left_exclude))
    right = int(ctx.draw_color("right_color", exclude={0, 5, left}))
    return left, right


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _normalize_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    shape_overridden = "grid_h" in overrides or "half_w" in overrides
    scheduled_profile, scheduled_phase = _schedule_entry(
        seed, sample_index, difficulty
    )
    canonical_geometry = not shape_overridden and scheduled_profile == "canonical"
    realized_profile = (
        "override" if shape_overridden else scheduled_profile
    )
    corner_phase = None if canonical_geometry else scheduled_phase
    if corner_phase is None and not canonical_geometry:
        corner_phase = ctx.draw_rng("corner_phase").randrange(3)

    if canonical_geometry:
        h = int(ctx.draw_int("grid_h", 5, 5))
        half = int(ctx.draw_int("half_w", 5, 5))
    else:
        (h_lo, h_hi), (w_lo, w_hi) = _BAND_RANGES[band]
        h = _draw_banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 4, 9)
        half = _draw_banded_int(ctx, overrides, "half_w", w_lo, w_hi, 3, 8)

    left_color, right_color = _draw_colors(ctx, overrides)
    left, right = _draw_masks(
        ctx.draw_rng("masks"), h, half, canonical_geometry, corner_phase
    )

    grid = full_grid(h, 2 * half + 1, 0)
    for r in range(h):
        grid[r][half] = 5
    for r, c in left:
        grid[r][c] = left_color
    for r, c in right:
        grid[r][half + 1 + c] = right_color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={
            "overrides": overrides,
            "profile": realized_profile,
            "corner_phase": corner_phase,
        },
    )
    if errors:
        raise AssertionError("constructed invalid XOR lesson: " + "; ".join(errors))
    return grid


def analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"], "facts": None}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["rows must be nonempty sequences"], "facts": None}
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be ARC color integers 0..9"], "facts": None}

    h = len(grid)
    if not 4 <= h <= 9:
        errors.append(f"grid_h must be in 4..9, got {h}")
    if width % 2 != 1:
        errors.append(f"total width must be odd, got {width}")
        return {"errors": errors, "facts": None}
    half = (width - 1) // 2
    if not 3 <= half <= 8:
        errors.append(f"half_w must be in 3..8, got {half}")
    if errors:
        return {"errors": errors, "facts": None}

    dividers = [c for c in range(width) if all(grid[r][c] == 5 for r in range(h))]
    if dividers != [half]:
        errors.append(f"expected only the centered full-height 5 divider, got {dividers}")
        return {"errors": errors, "facts": None}
    if any(
        grid[r][c] == 5
        for r in range(h)
        for c in range(width)
        if c != half
    ):
        errors.append("color 5 may appear only in the divider")

    left = {(r, c) for r in range(h) for c in range(half) if grid[r][c] != 0}
    right = {
        (r, c - half - 1)
        for r in range(h)
        for c in range(half + 1, width)
        if grid[r][c] != 0
    }
    left_colors = {grid[r][c] for r, c in left}
    right_colors = {grid[r][half + 1 + c] for r, c in right}
    if len(left_colors) != 1:
        errors.append(
            f"left panel must have exactly one object color, got {sorted(left_colors)}"
        )
    if len(right_colors) != 1:
        errors.append(
            f"right panel must have exactly one object color, got {sorted(right_colors)}"
        )
    if errors:
        return {"errors": errors, "facts": None}

    left_color = next(iter(left_colors))
    right_color = next(iter(right_colors))
    if left_color in (0, 5) or right_color in (0, 5) or left_color == right_color:
        errors.append("object colors must be distinct nonzero colors other than 5")
    if _component_count(left) != 1:
        errors.append("left object must be 4-connected")
    if _component_count(right) != 1:
        errors.append("right object must be 4-connected")
    relations = _relation_counts(left, right)
    for name, count in relations.items():
        if count < 1:
            errors.append(f"{name} relation must have at least one cell")

    facts = {
        "grid_h": h,
        "half_w": half,
        "left_color": left_color,
        "right_color": right_color,
        "left_size": len(left),
        "right_size": len(right),
        **relations,
        "border_xor": _border_xor_count(left, right, h, half),
        "corner_relations": _corner_relations(left, right, h, half),
        "inset_canonical_geometry": (
            h == 5
            and half == 5
            and all(1 <= r <= 3 and 1 <= c <= 3 for r, c in left | right)
        ),
    }
    return {"errors": errors, "facts": facts}


def observe_overrides(grid: Any) -> dict[str, int]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid lesson: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {axis: int(facts[axis]) for axis in AXES}


def _scene_masks(grid: Any) -> tuple[set[tuple[int, int]], set[tuple[int, int]], int, int]:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid XOR scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    h, half = facts["grid_h"], facts["half_w"]
    left = {(r, c) for r in range(h) for c in range(half) if grid[r][c] != 0}
    right = {
        (r, c - half - 1)
        for r in range(h)
        for c in range(half + 1, 2 * half + 1)
        if grid[r][c] != 0
    }
    return left, right, h, half


def _mask_output(mask: set[tuple[int, int]], h: int, half: int) -> list[list[int]]:
    return [[8 if (r, c) in mask else 0 for c in range(half)] for r in range(h)]


def _output_for_operation(
    grid: Any,
    operation: Callable[[set[tuple[int, int]], set[tuple[int, int]]], set[tuple[int, int]]],
) -> list[list[int]]:
    left, right, h, half = _scene_masks(grid)
    return _mask_output(operation(left, right), h, half)


def _xor_output(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket XOR occupancy rule."""
    return _output_for_operation(grid, lambda left, right: left ^ right)


rule_mirror = _xor_output


def _rival_or(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: left | right)


def _rival_and(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: left & right)


def _rival_copy_left(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: set(left))


def _rival_copy_right(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: set(right))


def _rival_left_minus_right(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: left - right)


def _rival_right_minus_left(grid: Any) -> list[list[int]]:
    return _output_for_operation(grid, lambda left, right: right - left)


def _rival_empty_output_border(grid: Any) -> list[list[int]]:
    output = _xor_output(grid)
    h, half = len(output), len(output[0])
    return [
        [
            0 if r in (0, h - 1) or c in (0, half - 1) else output[r][c]
            for c in range(half)
        ]
        for r in range(h)
    ]


def _regional_cells(name: str, h: int, half: int) -> set[tuple[int, int]]:
    top = {(0, c) for c in range(half)}
    bottom = {(h - 1, c) for c in range(half)}
    left_edge = {(r, 0) for r in range(h)}
    right_edge = {(r, half - 1) for r in range(h)}
    corners = set(_corner_cells(h, half))
    regions = {
        "border": top | bottom | left_edge | right_edge,
        "top": top,
        "bottom": bottom,
        "left_edge": left_edge,
        "right_edge": right_edge,
        "corners": corners,
        "top_left": {(0, 0)},
        "top_right": {(0, half - 1)},
        "bottom_left": {(h - 1, 0)},
        "bottom_right": {(h - 1, half - 1)},
    }
    return regions[name]


def _regional_operation(
    name: str,
    left: set[tuple[int, int]],
    right: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    operations = {
        "zero": set(),
        "or": left | right,
        "and": left & right,
        "left": set(left),
        "right": set(right),
        "left_minus_right": left - right,
        "right_minus_left": right - left,
    }
    return operations[name]


def _regional_rival_output(
    grid: Any, region_name: str, operation_name: str
) -> list[list[int]]:
    left, right, h, half = _scene_masks(grid)
    region = _regional_cells(region_name, h, half)
    intended = left ^ right
    alternate = _regional_operation(operation_name, left, right)
    return _mask_output((intended - region) | (alternate & region), h, half)


def _make_regional_rival(
    region_name: str, operation_name: str
) -> Callable[[Any], list[list[int]]]:
    def rival(grid: Any) -> list[list[int]]:
        return _regional_rival_output(grid, region_name, operation_name)

    rival.__name__ = f"regional_{region_name}_{operation_name}"
    return rival


_REGIONAL_NAMES = (
    "border",
    "top",
    "bottom",
    "left_edge",
    "right_edge",
    "corners",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
_REGIONAL_OPERATION_NAMES = (
    "zero",
    "or",
    "and",
    "left",
    "right",
    "left_minus_right",
    "right_minus_left",
)
REGIONAL_LESSON_COMPETITORS = {
    f"{region}:{operation}": _make_regional_rival(region, operation)
    for region in _REGIONAL_NAMES
    for operation in _REGIONAL_OPERATION_NAMES
}


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "or": _rival_or,
    "and": _rival_and,
    "copy_left": _rival_copy_left,
    "copy_right": _rival_copy_right,
    "left_minus_right": _rival_left_minus_right,
    "right_minus_left": _rival_right_minus_left,
    "empty_output_border": _rival_empty_output_border,
    **REGIONAL_LESSON_COMPETITORS,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"empty_output_border": _rival_empty_output_border}


def _panel_relation(grid, name: str) -> bool:
    """True when the grid is a lawful scene witnessing relation ``name``."""
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return False
    return analysis["facts"][name] >= 1


def strict_canonical_like(grid) -> list[str]:
    """Canonical-like means the linked 5x11 inset geometry of all public inputs."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    facts = analysis["facts"]
    reasons = []
    if facts["grid_h"] != 5 or facts["half_w"] != 5:
        reasons.append(
            f"canonical scenes are 5x11 (half_w 5); got grid_h={facts['grid_h']}, "
            f"half_w={facts['half_w']}"
        )
    if not facts["inset_canonical_geometry"]:
        reasons.append("objects are not inset one cell from the panel borders")
    return reasons


SEMANTIC_WITNESSES = {
    "overlap": lambda grid: _panel_relation(grid, "overlap"),
    "left_only": lambda grid: _panel_relation(grid, "left_only"),
    "right_only": lambda grid: _panel_relation(grid, "right_only"),
    "border_xor": lambda grid: _panel_relation(grid, "border_xor"),
}
WITNESS_RIVALS = {
    "overlap": ["or", "and"],
    "left_only": ["copy_right", "right_minus_left"],
    "right_only": ["copy_left", "left_minus_right"],
    "border_xor": ["empty_output_border"],
}


def _lesson_pair_error(pair: Any, label: str) -> str | None:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return f"{label} must contain input and output"
    errors = self_check(pair["input"])
    if errors:
        return f"{label} input is unlawful: {errors[0]}"
    if pair["output"] != _xor_output(pair["input"]):
        return f"{label} output is not the XOR of its panels"
    return None


def lesson_identifiable(demos, query) -> list[str]:
    """Require five demonstrations that refute every declared plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        error = _lesson_pair_error(pair, f"demo {index}")
        if error:
            reasons.append(error)
        else:
            valid_demos.append(pair)

    query_error = _lesson_pair_error(query, "query")
    if query_error:
        reasons.append(query_error)

    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]

    requested: dict[str, Any] = {}
    profile = None
    corner_phase = None
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if not isinstance(requested, dict):
            requested = {}
        profile = meta.get("profile")
        corner_phase = meta.get("corner_phase")
    for axis, value in requested.items():
        if axis in facts and facts[axis] != value:
            errors.append(f"{axis} requested {value!r}, realized {facts[axis]!r}")

    if profile == "canonical" and not facts["inset_canonical_geometry"]:
        errors.append("canonical profile must use 5x11 inset geometry")
    if profile == "generalized" and corner_phase not in (0, 1, 2):
        errors.append("generalized profile must declare corner phase 0, 1, or 2")
    if corner_phase in (0, 1, 2):
        expected = list(CORNER_RELATION_PHASES[int(corner_phase)])
        if facts["corner_relations"] != expected:
            errors.append(
                f"corner phase {corner_phase} requires {expected}, got "
                f"{facts['corner_relations']}"
            )
    return errors
