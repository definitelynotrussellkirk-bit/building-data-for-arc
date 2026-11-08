"""Input generator for task 7fd453cd0339.

The canonical rule treats every nonzero same-color 4-connected component as a
solid axis-aligned rectangle (one-cell-wide rectangles are lawful).  Its output
keeps the distinct corners of each component's bounding box and clears every
other cell.

The six-step curriculum alternates three linked public-profile anchors with
lawful counterexamples.  Each counterexample contains a one-cell-wide rectangle
and a separate rectangle of the same color.  This jointly refutes local-neighbor
shortcuts and the canonical-fitting shortcut that takes one global bbox per
color.  Every four consecutive generated pairs contain two such witnesses, so
holding out any one pair still leaves a witness in the demonstrations.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7fd453cd0339"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "de0c1931e97a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "For each separated solid monochrome rectangle, including one-cell-wide "
    "rectangles, clear the object except for the distinct corners of its own "
    "bounding box. Alternating teaching inputs include a line and a separate "
    "same-color rectangle to rule out local-neighbor and per-color-bbox shortcuts."
)

INVARIANTS = [
    "background is 0 and foreground colors are ARC colors 1..9",
    "there are exactly 2..4 halo-separated same-color 4-connected components",
    "every component exactly fills its axis-aligned bounding box; lines are lawful rectangles",
    "every generated input contains at least one non-corner cell that the rule deletes",
    "counterexample inputs contain a line and a separate same-color 2D rectangle",
]

PALETTE_KINDS = ("canonical_24", "canonical_35", "broad")
PALETTES: dict[str, tuple[int, ...]] = {
    # Disjoint families make the exact string override observable from pixels,
    # even when only one foreground color is used.
    "canonical_24": (2, 4),
    "canonical_35": (3, 5),
    "broad": (1, 6, 7, 8, 9),
}
HELPFUL_TEXTURES = ("canonical", "counterexample")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "public-profile anchors or uniform 6..14",
        "valid": "6..14",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "public-profile anchors or uniform 8..18",
        "valid": "8..18",
        "doc": "Exact returned grid width.",
    },
    "rectangles": {
        "type": "int",
        "default": "2 on public-profile anchors or uniform 2..4",
        "valid": "2..4",
        "doc": "Exact number of separated foreground components.",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled canonical family or uniform family",
        "valid": "|".join(PALETTE_KINDS),
        "doc": "Disjoint foreground-color family; exactly observable.",
    },
    "texture": {
        "type": "str",
        "default": "alternating canonical|counterexample",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": "canonical uses only 2D rectangles; counterexample includes a line and repeated color.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "canonical_a",
    "counterexample",
    "canonical_b",
    "counterexample",
    "canonical_c",
    "counterexample",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
_DIFFICULTY_PHASE = {None: 0, "easy": 0, "medium": 2, "hard": 4}

# (height, width, ((color, rect_height, rect_width), ...))
_CANONICAL_PROFILES: dict[str, tuple[int, int, tuple[tuple[int, int, int], ...]]] = {
    "canonical_a": (6, 9, ((2, 3, 3), (4, 3, 2))),
    "canonical_b": (7, 8, ((3, 2, 4), (5, 3, 3))),
    "canonical_c": (7, 9, ((2, 3, 4), (4, 2, 2))),
}

Cell = tuple[int, int]
Grid = list[list[int]]
Component = tuple[int, set[Cell]]
Signature = tuple[int, int, tuple[tuple[int, int, int], ...]]

CANONICAL_PROFILE_SIGNATURES: set[Signature] = {
    (h, w, tuple(sorted(specs))) for h, w, specs in _CANONICAL_PROFILES.values()
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic semantic schedule profile.

    Difficulty rotates the three canonical anchors by an even phase, preserving
    the alternating witness pattern while making the bands observably distinct.
    """
    del seed
    phase = _DIFFICULTY_PHASE.get(difficulty, 0)
    return SCHEDULE_PROFILES[(int(sample_index) + phase) % LESSON_SCHEDULE_PERIOD]


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _explicit(overrides: dict[str, Any], label: str) -> bool:
    return label in overrides and overrides[label] is not None


def _draw_scheduled_int(ctx, overrides, label: str, lo: int, hi: int, default: int | None) -> int:
    if _explicit(overrides, label):
        return ctx.draw_int_strict(label, lo, hi)
    if default is None:
        return ctx.draw_int_strict(label, lo, hi)
    # A singleton keyed choice records the actually returned exact-axis value.
    return ctx.draw_choice(label, (default,))


def _draw_scheduled_choice(ctx, overrides, label: str, options: tuple[str, ...], default: str | None) -> str:
    if _explicit(overrides, label) or default is None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _components(grid: Grid) -> list[Component]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[Component] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[Cell] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _bbox(cells: Iterable[Cell]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _shape(cells: Iterable[Cell]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


def _corners(cells: Iterable[Cell]) -> set[Cell]:
    r0, c0, r1, c1 = _bbox(cells)
    return {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}


def _expected_output(grid: Grid) -> Grid:
    """Python geometry mirror for witnesses/tests; Racket remains authority."""
    out = [[0 for _ in row] for row in grid]
    for color, cells in _components(grid):
        for r, c in _corners(cells):
            out[r][c] = color
    return out


rule_mirror = _expected_output


def _linked_signature(grid: Grid) -> Signature | None:
    errors = self_check(grid)
    if errors:
        return None
    object_specs = tuple(sorted((color, *_shape(cells)) for color, cells in _components(grid)))
    return len(grid), len(grid[0]), object_specs


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = _linked_signature(grid)
    if signature not in CANONICAL_PROFILE_SIGNATURES:
        return [f"linked profile {signature!r} is outside the three public input profiles"]
    return []


def canonical_profile_signature(grid) -> Signature | None:
    return _linked_signature(grid)


def _anchor_grid(h: int, w: int, specs: tuple[tuple[int, int, int], ...], rng) -> Grid:
    """Place an exact public linked profile without replaying canonical pixels."""
    ordered = list(specs)
    if rng.choice((False, True)):
        ordered.reverse()
    minimum_width = sum(rect_w for _, _, rect_w in ordered) + len(ordered) - 1
    slack = w - minimum_width
    if slack < 0:
        raise ValueError("canonical profile does not fit requested width")
    left_slack = rng.randint(0, slack)
    gap_extra = rng.randint(0, slack - left_slack)
    cursor = left_slack
    grid = full_grid(h, w, 0)
    for index, (color, rect_h, rect_w) in enumerate(ordered):
        r0 = rng.randint(0, h - rect_h)
        for r in range(r0, r0 + rect_h):
            for c in range(cursor, cursor + rect_w):
                grid[r][c] = color
        cursor += rect_w
        if index + 1 < len(ordered):
            cursor += 1 + gap_extra
            gap_extra = 0
    return grid


def _slot_bounds(h: int, w: int, rng) -> list[tuple[int, int, int, int]]:
    """Four disjoint slots, each at least 2x3, separated by one full row/col."""
    row_gap = rng.randint(2, h - 3)
    col_gap = rng.randint(3, w - 4)
    slots = [
        (0, row_gap - 1, 0, col_gap - 1),
        (0, row_gap - 1, col_gap + 1, w - 1),
        (row_gap + 1, h - 1, 0, col_gap - 1),
        (row_gap + 1, h - 1, col_gap + 1, w - 1),
    ]
    rng.shuffle(slots)
    return slots


def _paint_rectangle(grid: Grid, slot, color: int, rng, *, force_wide: bool) -> None:
    r0, r1, c0, c1 = slot
    slot_h, slot_w = r1 - r0 + 1, c1 - c0 + 1
    rect_h = rng.randint(2, slot_h)
    rect_w = rng.randint(3 if force_wide else 2, slot_w)
    top = rng.randint(r0, r1 - rect_h + 1)
    left = rng.randint(c0, c1 - rect_w + 1)
    for r in range(top, top + rect_h):
        for c in range(left, left + rect_w):
            grid[r][c] = color


def _paint_line(grid: Grid, slot, color: int, rng) -> None:
    r0, r1, c0, c1 = slot
    slot_h, slot_w = r1 - r0 + 1, c1 - c0 + 1
    orientations = ["horizontal"]
    if slot_h >= 3:
        orientations.append("vertical")
    orientation = rng.choice(orientations)
    if orientation == "horizontal":
        length = rng.randint(3, slot_w)
        row = rng.randint(r0, r1)
        left = rng.randint(c0, c1 - length + 1)
        for c in range(left, left + length):
            grid[row][c] = color
    else:
        length = rng.randint(3, slot_h)
        col = rng.randint(c0, c1)
        top = rng.randint(r0, r1 - length + 1)
        for r in range(top, top + length):
            grid[r][col] = color


def _general_grid(h: int, w: int, rectangles: int, palette_kind: str, texture: str, ctx) -> Grid:
    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("layout")
    slots = _slot_bounds(h, w, layout_rng)[:rectangles]
    palette = list(PALETTES[palette_kind])
    color_rng = ctx.draw_rng("colors")
    color_rng.shuffle(palette)

    if texture == "counterexample":
        # One line plus a separate same-color rectangle refutes all declared
        # canonical-fitting shortcuts in a single lawful input.
        witness_color = palette[0]
        _paint_line(grid, slots[0], witness_color, layout_rng)
        _paint_rectangle(grid, slots[1], witness_color, layout_rng, force_wide=True)
        for index, slot in enumerate(slots[2:], start=1):
            _paint_rectangle(
                grid,
                slot,
                palette[index % len(palette)],
                layout_rng,
                force_wide=False,
            )
    else:
        for index, slot in enumerate(slots):
            _paint_rectangle(
                grid,
                slot,
                palette[index % len(palette)],
                layout_rng,
                force_wide=index == 0,
            )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    anchor = _CANONICAL_PROFILES.get(profile)
    defaults = {
        "grid_h": anchor[0] if anchor else None,
        "grid_w": anchor[1] if anchor else None,
        "rectangles": 2 if anchor else None,
        "palette_kind": (
            "canonical_35"
            if profile == "canonical_b"
            else "canonical_24" if anchor else None
        ),
        "texture": "canonical" if anchor else "counterexample",
    }

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, overrides, "grid_h", 6, 14, defaults["grid_h"])
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 8, 18, defaults["grid_w"])
    rectangles = _draw_scheduled_int(ctx, overrides, "rectangles", 2, 4, defaults["rectangles"])
    palette_kind = _draw_scheduled_choice(
        ctx, overrides, "palette_kind", PALETTE_KINDS, defaults["palette_kind"]
    )
    texture = _draw_scheduled_choice(
        ctx, overrides, "texture", HELPFUL_TEXTURES, defaults["texture"]
    )

    resolved = {
        "grid_h": h,
        "grid_w": w,
        "rectangles": rectangles,
        "palette_kind": palette_kind,
        "texture": texture,
    }
    exact_anchor = bool(anchor) and resolved == {
        "grid_h": anchor[0],
        "grid_w": anchor[1],
        "rectangles": 2,
        "palette_kind": defaults["palette_kind"],
        "texture": "canonical",
    }
    if exact_anchor:
        return _anchor_grid(h, w, anchor[2], ctx.draw_rng("anchor_layout"))
    return _general_grid(h, w, rectangles, palette_kind, texture, ctx)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task grammar, including lawful line rectangles."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if not (6 <= len(grid) <= 14 and 8 <= width <= 18):
        return [f"grid dimensions {len(grid)}x{width} are outside 6..14 by 8..18"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9 (bool is not a color)"]

    comps = _components(grid)
    errors: list[str] = []
    if not 2 <= len(comps) <= 4:
        errors.append(f"expected 2..4 foreground rectangles, found {len(comps)}")
    for color, cells in comps:
        r0, c0, r1, c1 = _bbox(cells)
        expected_area = (r1 - r0 + 1) * (c1 - c0 + 1)
        if len(cells) != expected_area:
            errors.append(f"color {color} component does not fill its bounding box")
            continue
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] != color:
                    errors.append(f"color {color} rectangle has a hole or mixed cell")
                    break
            if errors and errors[-1].startswith(f"color {color} rectangle"):
                break

    # Halo separation prevents touching colors from becoming a positional or
    # object-segmentation ambiguity, while accepting all three public inputs.
    for index, (_, cells) in enumerate(comps):
        halo = {
            (r + dr, c + dc)
            for r, c in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
        }
        for _, other in comps[index + 1 :]:
            if halo & other:
                errors.append("foreground rectangles must be separated by a one-cell halo")
                break
        if errors and errors[-1] == "foreground rectangles must be separated by a one-cell halo":
            break

    if comps and all(len(cells) == len(_corners(cells)) for _, cells in comps):
        errors.append("all rectangles are corner-only identities; at least one deletion is required")
    return errors


def observe_overrides(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed task grid: " + "; ".join(errors))
    comps = _components(grid)
    colors = {color for color, _ in comps}
    matches = [name for name, palette in PALETTES.items() if colors <= set(palette)]
    if len(matches) != 1:
        raise ValueError(f"foreground colors {sorted(colors)} do not identify one palette_kind")
    has_line = any(1 in _shape(cells) for _, cells in comps)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "rectangles": len(comps),
        "palette_kind": matches[0],
        "texture": "counterexample" if has_line else "canonical",
    }


def semantic_signature(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    comps = _components(grid)
    counts = Counter(color for color, _ in comps)
    return {
        **observe_overrides(grid),
        "line_rectangles": sum(1 in _shape(cells) for _, cells in comps),
        "repeated_component_colors": tuple(sorted(color for color, count in counts.items() if count > 1)),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _same_color_neighbor_count(grid: Grid, r: int, c: int) -> int:
    color = grid[r][c]
    return sum(
        0 <= r + dr < len(grid)
        and 0 <= c + dc < len(grid[0])
        and grid[r + dr][c + dc] == color
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _rival_exactly_two_neighbors(grid: Grid) -> Grid:
    """Canonical-fitting local shortcut: keep degree-2 foreground cells."""
    return [
        [
            value if value != 0 and _same_color_neighbor_count(grid, r, c) == 2 else 0
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _rival_at_most_two_neighbors(grid: Grid) -> Grid:
    """Canonical-fitting local shortcut: keep foreground degree <= 2."""
    return [
        [
            value if value != 0 and _same_color_neighbor_count(grid, r, c) <= 2 else 0
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(grid)
    ]


def _rival_one_bbox_per_color(grid: Grid) -> Grid:
    """Canonical-fitting shortcut that merges separated objects of one color."""
    out = [[0 for _ in row] for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        for r, c in _corners(cells):
            out[r][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "exactly_two_same_color_neighbors": _rival_exactly_two_neighbors,
    "at_most_two_same_color_neighbors": _rival_at_most_two_neighbors,
    "one_bbox_per_color": _rival_one_bbox_per_color,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_line_rectangle(grid: Grid) -> bool:
    return any(1 in _shape(cells) for _, cells in _components(grid))


def _has_repeated_component_color(grid: Grid) -> bool:
    counts = Counter(color for color, _ in _components(grid))
    return any(count > 1 for count in counts.values())


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "line_rectangle": _has_line_rectangle,
    "separate_same_color_rectangles": _has_repeated_component_color,
}
WITNESS_RIVALS = {
    "line_rectangle": [
        "exactly_two_same_color_neighbors",
        "at_most_two_same_color_neighbors",
    ],
    "separate_same_color_rectangles": ["one_bbox_per_color"],
}


def _validate_pair(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    expected = _expected_output(pair["input"])
    if pair["output"] != expected:
        return [f"{label} output is not exact per-component bbox-corner extraction"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Check the generated three-demo curriculum against named shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    reasons.extend(f"query input: {error}" for error in query_errors)
    if "output" in query and query["output"] != _expected_output(query["input"]):
        reasons.append("query output is not exact per-component bbox-corner extraction")
    if reasons:
        return reasons

    if not any(
        _has_line_rectangle(demo["input"]) and _has_repeated_component_color(demo["input"])
        for demo in demos
    ):
        reasons.append("demonstrations lack the joint line-plus-repeated-color shortcut witness")

    expected_query = _expected_output(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != expected_query:
                reasons.append(f"named competitor {name!r} fits every demo but disagrees on query")
    return reasons
