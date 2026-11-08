"""Generator for task 2a41d6b25262: stamp normalized template XOR.

Inputs contain one connected red (2) template, one connected green (3)
template, and one blue (1) anchor.  Each template is normalized to its own
bounding-box top-left.  The selected Racket rule stamps the symmetric
difference of those normalized supports in cyan (8) at the anchor on an
otherwise empty canvas.

The generator deliberately varies template geometry and absolute role order.
A four-example schedule includes a leading-offset case, so lessons distinguish
"preserve the templates' normalized origins" from the tempting shortcut of
cropping the XOR itself before stamping.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = TASK_ID = "2a41d6b25262"
VERSION = "3.0.0"
RULE_HASH = "75fe298a62dd"

SUMMARY = (
    "One connected red-2 template, one connected green-3 template, and one "
    "blue-1 anchor appear on a zero background. Normalize each template to "
    "its own top-left, take the symmetric difference without re-cropping it, "
    "and stamp those offsets in cyan-8 at the anchor on an otherwise empty "
    "same-size output. Templates vary over many connected polyominoes and "
    "swap absolute reading order; recurring 10x15 anchors preserve canonical "
    "profile support in every difficulty band."
)

INVARIANTS = [
    "the canvas is 10..18 rows by 13..22 columns with colors exactly 0,1,2,3",
    "there is exactly one 4-connected red-2 template and one green-3 template",
    "each template has 3..8 cells, fits a 4x4 box, and is normalized independently",
    "the normalized templates overlap and each also has at least one exclusive cell",
    "there is exactly one blue-1 anchor and the uncropped XOR footprint fits in bounds",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10 or difficulty-aware rng 10..18",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 15 or difficulty-aware rng 13..22",
        "valid": "13..22",
    },
}

_VALID_H = (10, 18)
_VALID_W = (13, 22)
_BAND_BOUNDS = {
    "easy": ((10, 13), (13, 17)),
    "medium": ((11, 16), (14, 20)),
    "hard": ((13, 18), (17, 22)),
}
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_SLOT_SIZE = 4

# Four consecutive sample indexes cover all profiles.  The production lesson
# length below therefore contains every named semantic counterexample no matter
# which residue starts the lesson.
_SCHEDULE = (
    "same_size_44",
    "same_size_54",
    "same_size_55",
    "leading_offset",
)
SCHEDULE_PROFILES = _SCHEDULE
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.35


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _SCHEDULE[sample_index % len(_SCHEDULE)]


def _normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = set(points)
    if not cells:
        return frozenset()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _bbox_shape(points: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(points)
    if not cells:
        return (0, 0)
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _enumerate_polyominoes() -> dict[int, tuple[frozenset[tuple[int, int]], ...]]:
    """All fixed connected polyominoes of size <=8 that fit in a 4x4 box.

    Final ordering is coordinate-sorted, so RNG choice is independent of Python
    hash randomization even though sets are convenient during enumeration.
    """
    by_size: dict[int, tuple[frozenset[tuple[int, int]], ...]] = {
        1: (frozenset({(0, 0)}),)
    }
    for size in range(2, 9):
        found: set[frozenset[tuple[int, int]]] = set()
        for shape in by_size[size - 1]:
            for row, col in shape:
                for dr, dc in _CARDINAL:
                    candidate = (row + dr, col + dc)
                    if candidate in shape:
                        continue
                    grown = _normalize(set(shape) | {candidate})
                    height, width = _bbox_shape(grown)
                    if height <= _SLOT_SIZE and width <= _SLOT_SIZE:
                        found.add(grown)
        by_size[size] = tuple(
            sorted(found, key=lambda shape: tuple(sorted(shape)))
        )
    return by_size


_SHAPES = _enumerate_polyominoes()

# A deliberately wrong rule that memorizes only the ordered source-cell counts
# of the three canonical examples.  It fits all public pairs exactly while
# ignoring geometry; generated same-count/different-geometry examples refute it.
_CANONICAL_XOR_BY_SIZE = {
    (4, 4): frozenset({(0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)}),
    (5, 4): frozenset({(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)}),
    (5, 5): frozenset({(0, 1), (0, 2), (1, 2), (2, 1)}),
}
_PROFILE_SIZES = {
    "same_size_44": (4, 4),
    "same_size_54": (5, 4),
    "same_size_55": (5, 5),
}


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = [start]
        component = {start}
        while pending:
            row, col = pending.pop()
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        result.append(component)
    return result


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty list or tuple"]
    rows = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            return None, ["grid rows must be non-empty lists or tuples"]
        rows.append(list(row))
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in rows for value in row):
        return None, ["grid cells must be integer colors 0..9 (not booleans)"]
    return rows, []


def _analyze(grid):
    rows, errors = _coerce_grid(grid)
    if rows is None:
        return None, errors
    height, width = len(rows), len(rows[0])
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 10..18")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 13..22")

    palette = {value for row in rows for value in row}
    if not palette <= {0, 1, 2, 3}:
        errors.append(f"input colors must be drawn from 0,1,2,3; found {sorted(palette)}")
        return None, errors
    if 0 not in palette:
        errors.append("background color 0 is absent")

    marker_cells = [
        (row, col)
        for row, values in enumerate(rows)
        for col, value in enumerate(values)
        if value == 1
    ]
    if len(marker_cells) != 1:
        errors.append(f"expected exactly one blue-1 anchor, found {len(marker_cells)}")

    red_components = _components(rows, 2)
    green_components = _components(rows, 3)
    if len(red_components) != 1:
        errors.append(f"expected exactly one red-2 component, found {len(red_components)}")
    if len(green_components) != 1:
        errors.append(f"expected exactly one green-3 component, found {len(green_components)}")
    if errors:
        return None, errors

    red_absolute = red_components[0]
    green_absolute = green_components[0]
    red = _normalize(red_absolute)
    green = _normalize(green_absolute)
    for name, shape in (("red", red), ("green", green)):
        if not 3 <= len(shape) <= 8:
            errors.append(f"{name} template must contain 3..8 cells")
        box_h, box_w = _bbox_shape(shape)
        if box_h > _SLOT_SIZE or box_w > _SLOT_SIZE:
            errors.append(f"{name} template must fit within a 4x4 box")

    overlap = red & green
    red_only = red - green
    green_only = green - red
    xor = red ^ green
    if not overlap:
        errors.append("normalized templates must overlap")
    if not red_only:
        errors.append("red template needs at least one normalized exclusive cell")
    if not green_only:
        errors.append("green template needs at least one normalized exclusive cell")

    marker = marker_cells[0]
    if xor:
        max_row = max(row for row, _ in xor)
        max_col = max(col for _, col in xor)
        if marker[0] + max_row >= height or marker[1] + max_col >= width:
            errors.append("uncropped normalized XOR stamp leaves the canvas")
    if errors:
        return None, errors

    return {
        "grid": rows,
        "height": height,
        "width": width,
        "red": red,
        "green": green,
        "red_absolute": red_absolute,
        "green_absolute": green_absolute,
        "marker": marker,
        "xor": xor,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _analysis, errors = _analyze(grid)
    return errors


def observe_overrides(grid):
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {"grid_h": analysis["height"], "grid_w": analysis["width"]}


def _render_offsets(analysis, offsets, *, clip=False):
    output = full_grid(analysis["height"], analysis["width"], 0)
    anchor_row, anchor_col = analysis["marker"]
    for dr, dc in offsets:
        row, col = anchor_row + dr, anchor_col + dc
        if 0 <= row < analysis["height"] and 0 <= col < analysis["width"]:
            output[row][col] = 8
        elif not clip:
            raise ValueError("offset stamp leaves the canvas")
    return output


def rule_mirror(grid):
    """Independent diagnostic mirror; production labels remain the Racket rule."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid XOR-stamp input: " + "; ".join(errors))
    return _render_offsets(analysis, analysis["xor"])


def strict_canonical_like(grid):
    """Canonical-scale morphology accepted by the public task.

    Returns [] when lawful.  This intentionally covers the canonical size
    signatures rather than memorizing the three public geometries.
    """
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    reasons = []
    if (analysis["height"], analysis["width"]) != (10, 15):
        reasons.append("canonical canvas is 10x15")
    signature = (len(analysis["red"]), len(analysis["green"]))
    if signature not in _CANONICAL_XOR_BY_SIZE:
        reasons.append("template cell-count signature is outside canonical 4/4, 5/4, 5/5")
    return reasons


def _valid_pair(red, green, *, require_leading_offset=False, forbidden_xor=None):
    if not (red & green and red - green and green - red):
        return False
    xor = red ^ green
    if forbidden_xor is not None and xor == forbidden_xor:
        return False
    if require_leading_offset:
        if min(row for row, _ in xor) == 0 and min(col for _, col in xor) == 0:
            return False
    return True


def _choose_shapes(profile: str, band: str, rng):
    if profile in _PROFILE_SIZES:
        red_size, green_size = _PROFILE_SIZES[profile]
        forbidden = _CANONICAL_XOR_BY_SIZE[(red_size, green_size)]
        # Residues 1 and 3 are guaranteed no-recrop witnesses.  Every
        # five-example lesson therefore contains at least two such examples,
        # so moving any one pair into the query cannot erase the evidence.
        require_leading_offset = profile == "same_size_54"
        for _ in range(400):
            red = rng.choice(_SHAPES[red_size])
            green = rng.choice(_SHAPES[green_size])
            if _valid_pair(
                red,
                green,
                require_leading_offset=require_leading_offset,
                forbidden_xor=forbidden,
            ):
                return red, green
    else:
        bounds = {"easy": (3, 5), "medium": (4, 7), "hard": (6, 8)}[band]
        for _ in range(800):
            red_size = rng.randint(*bounds)
            green_size = rng.randint(*bounds)
            red = rng.choice(_SHAPES[red_size])
            green = rng.choice(_SHAPES[green_size])
            if _valid_pair(red, green, require_leading_offset=True):
                return red, green
    raise AssertionError(f"could not choose lawful shape pair for profile={profile!r}")


def _slot_layout(height: int, width: int, rng):
    """Three separated 4x4 slots inside a randomly translated 10x13 frame."""
    frame_top = rng.randint(0, height - 10)
    frame_left = rng.randint(0, width - 13)
    top, left = frame_top, frame_left
    bottom = top + 6
    right = left + 9
    middle_row = top + 3
    middle_col = left + 4
    layouts = (
        ((top, left), (top, right), (bottom, middle_col)),
        ((bottom, left), (bottom, right), (top, middle_col)),
        ((top, left), (bottom, left), (middle_row, right)),
        ((top, right), (bottom, right), (middle_row, left)),
    )
    return list(rng.choice(layouts))


def _paint_shape(grid, shape, slot, color, rng):
    shape_h, shape_w = _bbox_shape(shape)
    row0 = slot[0] + rng.randint(0, _SLOT_SIZE - shape_h)
    col0 = slot[1] + rng.randint(0, _SLOT_SIZE - shape_w)
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def _draw_scene(height: int, width: int, red, green, rng):
    grid = full_grid(height, width, 0)
    xor = red ^ green
    xor_h, xor_w = _bbox_shape(xor)
    slots = _slot_layout(height, width, rng)
    roles = [("red", red), ("green", green), ("anchor", xor)]
    rng.shuffle(roles)
    for (role, shape), slot in zip(roles, slots):
        if role == "red":
            _paint_shape(grid, shape, slot, 2, rng)
        elif role == "green":
            _paint_shape(grid, shape, slot, 3, rng)
        else:
            # Reserve the complete 4x4 normalized-template footprint, not only
            # the true XOR bbox.  Otherwise a marker at the bottom/right edge
            # can clip a wrong union or size-lookup rival down to the correct
            # answer, turning a generated counterexample into an alias.
            row_shift = min(
                _SLOT_SIZE - xor_h,
                height - _SLOT_SIZE - slot[0],
            )
            col_shift = min(
                _SLOT_SIZE - xor_w,
                width - _SLOT_SIZE - slot[1],
            )
            row = slot[0] + rng.randint(0, row_shift)
            col = slot[1] + rng.randint(0, col_shift)
            grid[row][col] = 1
    return grid


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    bounds = {"grid_h": _VALID_H, "grid_w": _VALID_W}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = difficulty or "medium"
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Profiles 0 and 2 are exact canonical-scale anchors.  All bands therefore
    # retain canonical profile support while the other profiles vary dimensions.
    canonical_anchor = profile in {"same_size_44", "same_size_55"}
    if overrides.get("grid_h") is not None:
        height = ctx.draw_int("grid_h", *_VALID_H)
    elif canonical_anchor:
        height = ctx.draw_int("grid_h", 10, 10)
    else:
        height = ctx.draw_int("grid_h", *_BAND_BOUNDS[band][0])

    if overrides.get("grid_w") is not None:
        width = ctx.draw_int("grid_w", *_VALID_W)
    elif canonical_anchor:
        width = ctx.draw_int("grid_w", 15, 15)
    else:
        width = ctx.draw_int("grid_w", *_BAND_BOUNDS[band][1])

    red, green = _choose_shapes(profile, band, ctx.draw_rng(f"shapes|{profile}"))
    grid = _draw_scene(height, width, red, green, ctx.draw_rng("layout"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid


# --- Executable semantic contract -----------------------------------------

def _analysis_or_raise(grid):
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    return analysis


def _rival_union(grid):
    analysis = _analysis_or_raise(grid)
    return _render_offsets(analysis, analysis["red"] | analysis["green"], clip=True)


def _rival_intersection(grid):
    analysis = _analysis_or_raise(grid)
    return _render_offsets(analysis, analysis["red"] & analysis["green"], clip=True)


def _rival_red_only(grid):
    analysis = _analysis_or_raise(grid)
    return _render_offsets(analysis, analysis["red"], clip=True)


def _rival_green_only(grid):
    analysis = _analysis_or_raise(grid)
    return _render_offsets(analysis, analysis["green"], clip=True)


def _rival_crop_xor(grid):
    analysis = _analysis_or_raise(grid)
    return _render_offsets(analysis, _normalize(analysis["xor"]), clip=True)


def _rival_canonical_size_lookup(grid):
    analysis = _analysis_or_raise(grid)
    signature = (len(analysis["red"]), len(analysis["green"]))
    offsets = _CANONICAL_XOR_BY_SIZE.get(signature, analysis["red"])
    return _render_offsets(analysis, offsets, clip=True)


SEMANTIC_RIVALS = {
    "union_instead_of_xor": _rival_union,
    "intersection_only": _rival_intersection,
    "red_only": _rival_red_only,
    "green_only": _rival_green_only,
    "crop_xor_to_bbox": _rival_crop_xor,
    "canonical_size_lookup": _rival_canonical_size_lookup,
}


def _refutes_all(grid, names):
    if self_check(grid):
        return False
    target = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != target for name in names)


WITNESS_RIVALS = {
    "set_operation": [
        "union_instead_of_xor",
        "intersection_only",
        "red_only",
        "green_only",
    ],
    "preserve_normalized_origin": ["crop_xor_to_bbox"],
    "geometry_not_size_lookup": ["canonical_size_lookup"],
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, rivals=tuple(rivals): _refutes_all(grid, rivals))
    for name, rivals in WITNESS_RIVALS.items()
}
CANONICAL_SHORTCUTS = {
    "canonical_size_lookup": _rival_canonical_size_lookup,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Falsify declared rivals; this is not a proof of unique induction."""
    query_grid = query["input"] if isinstance(query, dict) else query
    target = rule_mirror(query_grid)
    return [
        f"{name} fits every demo but disagrees on the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(demo["input"]) == demo["output"] for demo in demos)
        and rival(query_grid) != target
    ]
