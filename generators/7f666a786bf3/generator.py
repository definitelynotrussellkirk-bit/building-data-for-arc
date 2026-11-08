"""Generator for arc_puzzle_bank_21_set4_d:medium_d07.

For every non-background color, all cells of that color define one tight
bounding rectangle.  The unchanged Racket oracle paints each rectangle solid
in its source color on an otherwise blank grid.  Ordinary lessons alternate
between uniform and mixed per-color marker counts so a learner cannot infer
that colors with a different count should be ignored.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "7f666a786bf3"
VERSION = "4.0.0"
TASK_ID = "7f666a786bf3"
RULE_HASH = "28a554829349"

SUMMARY = (
    "A 0-background grid contains two to four colors. Each color appears as "
    "two to four sparse markers; marker counts may differ between colors. "
    "Each tight bounding rectangle is at least 2x2, contains unpainted cells, "
    "and does not overlap any other color's rectangle. The output fills every "
    "color's own minimal bounding rectangle solid while leaving other cells 0."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("mixed_marker_counts", "uniform_marker_counts")

INVARIANTS = [
    "background is 0 and all input colors are integers 0..9",
    "there are exactly 2..4 distinct nonzero colors",
    "every color has 2..4 markers; counts may be uniform or mixed",
    "each color spans at least two rows and two columns",
    "each color's markers occupy at least two 4-connected components",
    "each color's bounding rectangle contains at least one background cell",
    "different colors' bounding rectangles do not overlap",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 6..18",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 8..20",
        "valid": "8..20",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware rng 2..4",
        "valid": "2..4",
    },
    "markers_per_color": {
        "type": "int",
        "default": "difficulty-aware minimum/floor 2..4",
        "valid": "2..4",
    },
    "mixed_marker_counts": {
        "type": "bool",
        "default": "scheduled true on even samples, false on odd samples",
        "valid": "false|true",
    },
    "edge_touching": {
        "type": "bool",
        "default": "rng false|true",
        "valid": "false|true",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"mixed_marker_counts": True, "markers_per_color": 4},
]

_VALID_H = (6, 18)
_VALID_W = (8, 20)
_VALID_COLORS = (2, 4)
_VALID_MARKERS = (2, 4)
_EDGE_CHOICES = (False, True)
# Profile draws can occur only in the uniform half of the two-slot schedule.
# An 0.80 conditional prior therefore keeps the overall linked-profile rate
# near the previous 0.40 while guaranteeing mixed-count support in every band.
_PROFILE_PRIOR = 0.80
_CARDINAL_COLORS = tuple(range(1, 10))

# Exact canonical input forms.  Profile draws may rename colors and reflect the
# grid, but they begin from one complete linked scene rather than independently
# sampling canonical marginals.
_PROFILE_GRIDS = (
    (
        "000000000",
        "050000000",
        "000000800",
        "000500000",
        "000000080",
        "000000000",
        "000000000",
    ),
    (
        "00000400",
        "00000000",
        "00000040",
        "00000000",
        "07000000",
        "00000000",
        "00070000",
        "00000000",
    ),
    (
        "0000000900",
        "0030000000",
        "0000000090",
        "0000300000",
        "0000000000",
        "0000000000",
    ),
    (
        "0000000000",
        "0600000000",
        "0006000000",
        "0000000000",
        "0000008000",
        "0000000080",
        "0000000000",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "n_colors", "markers_per_color"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    for label in ("mixed_marker_counts", "edge_touching"):
        value = overrides.get(label)
        if value is not None and type(value) is not bool:
            raise ValueError(f"{label} must be a boolean")
    if (
        overrides.get("mixed_marker_counts") is True
        and overrides.get("markers_per_color") == 4
    ):
        raise ValueError(
            "mixed_marker_counts=True is incompatible with markers_per_color=4"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic two-slot teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)



def _component_count(cells):
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count

def _bbox_cells(box):
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
    }


def _bboxes_overlap(left, right):
    return not (
        left[2] < right[0]
        or right[2] < left[0]
        or left[3] < right[1]
        or right[3] < left[1]
    )


def _analyze_scene(grid):
    coerced = _coerce_grid(grid)
    h = len(coerced)
    w = len(coerced[0]) if coerced else 0
    by_color = {}
    for r, row in enumerate(coerced):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))
    boxes = {color: _bbox(cells) for color, cells in by_color.items()}
    edge_touching = any(
        r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1
        for r1, c1, r2, c2 in boxes.values()
    )
    return {
        "grid": coerced,
        "h": h,
        "w": w,
        "by_color": {
            color: tuple(sorted(cells)) for color, cells in by_color.items()
        },
        "boxes": boxes,
        "edge_touching": edge_touching,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task-local teaching distribution, including canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 6..18")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 8..20")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("input values must be integer ARC colors 0..9")
        return errors
    if not any(value == 0 for row in coerced for value in row):
        errors.append("background color 0 must be present")

    scene = _analyze_scene(coerced)
    n_colors = len(scene["by_color"])
    if not (_VALID_COLORS[0] <= n_colors <= _VALID_COLORS[1]):
        errors.append("scene must contain exactly 2..4 nonzero colors")

    counts = {color: len(cells) for color, cells in scene["by_color"].items()}
    if any(not (_VALID_MARKERS[0] <= count <= _VALID_MARKERS[1]) for count in counts.values()):
        errors.append("each color must contain exactly 2..4 sparse markers")
    items = sorted(scene["by_color"].items())
    for color, cells in items:
        r1, c1, r2, c2 = scene["boxes"][color]
        if r1 == r2 or c1 == c2:
            errors.append(
                f"color {color} must span at least two rows and two columns"
            )
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        if area <= len(cells):
            errors.append(
                f"color {color} must leave at least one background cell in its bbox"
            )
        if _component_count(cells) < 2:
            errors.append(
                f"color {color} markers must form at least two 4-connected components"
            )

    for (left_color, _), (right_color, _) in combinations(items, 2):
        if _bboxes_overlap(
            scene["boxes"][left_color], scene["boxes"][right_color]
        ):
            errors.append(
                f"bounding rectangles for colors {left_color} and {right_color} overlap"
            )
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    counts = {len(cells) for cells in scene["by_color"].values()}
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "n_colors": len(scene["by_color"]),
        "markers_per_color": min(counts),
        "mixed_marker_counts": len(counts) > 1,
        "edge_touching": scene["edge_touching"],
    }


def rule_mirror(grid):
    """Python test mirror only; generated outputs still come from Racket."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = full_grid(scene["h"], scene["w"], 0)
    for color, box in scene["boxes"].items():
        for r, c in _bbox_cells(box):
            output[r][c] = color
    return output


def strict_canonical_like(grid):
    """Lawful sparse per-color bounding-box instances."""
    return self_check(grid)


def _identity_rival(grid):
    """Rival: leave every sparse marker unchanged."""
    return [row[:] for row in _coerce_grid(grid)]


def _first_color_only_rival(grid):
    """Rival: fill only the numerically first color's rectangle."""
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    if not scene["by_color"]:
        return output
    color = min(scene["by_color"])
    for r, c in _bbox_cells(scene["boxes"][color]):
        output[r][c] = color
    return output


def _uniform_marker_count_rival(grid):
    """Rival: fill only colors tied at the minimum marker count.

    All four canonical examples use one shared count, so this shortcut agrees
    there.  Mixed-count lessons make it visibly wrong without changing the
    actual task rule.
    """
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    if not scene["by_color"]:
        return output
    counts = {
        color: len(cells) for color, cells in scene["by_color"].items()
    }
    floor = min(counts.values())
    for color, count in counts.items():
        if count != floor:
            continue
        for r, c in _bbox_cells(scene["boxes"][color]):
            output[r][c] = color
    return output


def _has_mixed_marker_counts(grid):
    errors = self_check(grid)
    if errors:
        return False
    counts = {
        len(cells) for cells in _analyze_scene(grid)["by_color"].values()
    }
    return len(counts) > 1


SEMANTIC_WITNESSES = {"mixed_marker_counts": _has_mixed_marker_counts}
SEMANTIC_RIVALS = {
    "identity": _identity_rival,
    "first_color_only": _first_color_only_rival,
    "uniform_marker_count": _uniform_marker_count_rival,
}
WITNESS_RIVALS = {
    "mixed_marker_counts": ["uniform_marker_count"],
}
CANONICAL_SHORTCUTS = {
    "uniform_marker_count": _uniform_marker_count_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 1.0


def lesson_identifiable(demos, query):
    """Require every declared rival to be contradicted by the demonstrations."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons


def _normalize_cells(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    normalized = _normalize_cells(cells)
    height = max(r for r, _ in normalized) + 1
    return _normalize_cells((c, height - 1 - r) for r, c in normalized)


def _reflect(cells):
    normalized = _normalize_cells(cells)
    width = max(c for _, c in normalized) + 1
    return _normalize_cells((r, width - 1 - c) for r, c in normalized)


def _shape_key(cells):
    current = _normalize_cells(cells)
    variants = []
    for _ in range(4):
        variants.append(current)
        variants.append(_reflect(current))
        current = _rotate_cw(current)
    return min(variants)


def canonical_profile_signature(grid):
    errors = self_check(grid)
    if errors:
        return None
    scene = _analyze_scene(grid)
    profile_shapes = []
    for color, cells in scene["by_color"].items():
        r1, c1, _r2, _c2 = scene["boxes"][color]
        relative = tuple((r - r1, c - c1) for r, c in cells)
        profile_shapes.append(_shape_key(relative))
    return scene["h"], scene["w"], tuple(sorted(profile_shapes))


def _profile_grid(rows):
    return [[int(value) for value in row] for row in rows]


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    canonical_profile_signature(_profile_grid(rows)) for rows in _PROFILE_GRIDS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _rename_and_reflect_profile(rows, rng):
    grid = _profile_grid(rows)
    colors = sorted({value for row in grid for value in row if value != 0})
    replacements = rng.sample(_CARDINAL_COLORS, len(colors))
    color_map = dict(zip(colors, replacements))
    grid = [[color_map.get(value, value) for value in row] for row in grid]
    if rng.choice((False, True)):
        grid = [list(reversed(row)) for row in grid]
    if rng.choice((False, True)):
        grid = list(reversed(grid))
    return grid


def _draw_int_axis(ctx, overrides, label, random_bounds, valid_bounds):
    bounds = valid_bounds if overrides.get(label) is not None else random_bounds
    return ctx.draw_int(label, *bounds)


def _split_sizes(total, parts, minimum, rng):
    if total < parts * minimum:
        raise ValueError(
            f"cannot split extent {total} into {parts} parts of at least {minimum}"
        )
    sizes = [minimum] * parts
    for _ in range(total - parts * minimum):
        sizes[rng.randrange(parts)] += 1
    rng.shuffle(sizes)
    return sizes


def _slots(h, w, n_colors, edge_touching, rng):
    top = 0 if edge_touching else 1
    left = 0 if edge_touching else 1
    bottom = h if edge_touching else h - 1
    right = w if edge_touching else w - 1
    height = bottom - top
    width = right - left

    if n_colors == 2:
        if rng.choice((False, True)):
            widths = _split_sizes(width, 2, 2, rng)
            slots = []
            c = left
            for slot_w in widths:
                slots.append((top, c, bottom - 1, c + slot_w - 1))
                c += slot_w
        else:
            heights = _split_sizes(height, 2, 2, rng)
            slots = []
            r = top
            for slot_h in heights:
                slots.append((r, left, r + slot_h - 1, right - 1))
                r += slot_h
    elif n_colors == 3:
        widths = _split_sizes(width, 3, 2, rng)
        slots = []
        c = left
        for slot_w in widths:
            slots.append((top, c, bottom - 1, c + slot_w - 1))
            c += slot_w
    else:
        heights = _split_sizes(height, 2, 2, rng)
        widths = _split_sizes(width, 2, 3, rng)
        slots = []
        r = top
        for slot_h in heights:
            c = left
            for slot_w in widths:
                slots.append((r, c, r + slot_h - 1, c + slot_w - 1))
                c += slot_w
            r += slot_h
    # Put the roomiest slot first so ordinary lessons can include at least
    # one thick rectangle whose interior distinguishes solid fill from an
    # outline-only shortcut. Preserve variation by shuffling the remainder.
    slots.sort(
        key=lambda slot: (
            min(slot[2] - slot[0] + 1, slot[3] - slot[1] + 1) >= 3,
            (slot[2] - slot[0] + 1) * (slot[3] - slot[1] + 1),
        ),
        reverse=True,
    )
    tail = slots[1:]
    rng.shuffle(tail)
    return slots[:1] + tail


def _rectangle_candidates(slot, markers, h, w, require_edge):
    r0, c0, r3, c3 = slot
    candidates = []
    for r1 in range(r0, r3):
        for c1 in range(c0, c3):
            for r2 in range(r1 + 1, r3 + 1):
                for c2 in range(c1 + 1, c3 + 1):
                    area = (r2 - r1 + 1) * (c2 - c1 + 1)
                    if area <= markers or (markers >= 3 and area < markers + 2):
                        continue
                    if require_edge and not (
                        r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1
                    ):
                        continue
                    candidates.append((r1, c1, r2, c2))
    return candidates


def _has_opposite_corner_pair(cells, box):
    r1, c1, r2, c2 = box
    cell_set = set(cells)
    return (
        {(r1, c1), (r2, c2)} <= cell_set
        or {(r1, c2), (r2, c1)} <= cell_set
    )


def _marker_style(cells, box):
    r1, c1, r2, c2 = box
    interior = any(r1 < r < r2 and c1 < c < c2 for r, c in cells)
    if interior:
        return "interior"
    if _has_opposite_corner_pair(cells, box):
        return "opposite_corners"
    return "split_extrema"


def _choose_markers(box, count, rng, preferred_style):
    cells = tuple(sorted(_bbox_cells(box)))
    if count == 2:
        r1, c1, r2, c2 = box
        choices = (
            ((r1, c1), (r2, c2)),
            ((r1, c2), (r2, c1)),
        )
        return tuple(sorted(rng.choice(choices)))

    for _ in range(256):
        chosen = tuple(sorted(rng.sample(cells, count)))
        if _bbox(chosen) != box or _component_count(chosen) < 2:
            continue
        if preferred_style == "interior":
            r1, c1, r2, c2 = box
            if r2 - r1 < 2 or c2 - c1 < 2:
                continue
        if _marker_style(chosen, box) == preferred_style:
            return chosen

    # The exhaustive fallback is bounded (count <= 4 and generator rectangles
    # are small) and makes explicit boundary overrides deterministic instead of
    # silently shedding the requested marker count or geometry.
    valid = [
        tuple(candidate)
        for candidate in combinations(cells, count)
        if _bbox(candidate) == box and _component_count(candidate) >= 2
    ]
    styled = [
        candidate
        for candidate in valid
        if _marker_style(candidate, box) == preferred_style
    ]
    return rng.choice(styled or valid)


def _marker_counts(n_colors, floor, mixed, rng):
    if not mixed:
        return [floor] * n_colors
    if floor >= _VALID_MARKERS[1]:
        raise ValueError(
            "mixed_marker_counts=True is incompatible with markers_per_color=4"
        )
    counts = [floor, floor + 1]
    choices = tuple(range(floor, _VALID_MARKERS[1] + 1))
    counts.extend(rng.choice(choices) for _ in range(n_colors - 2))
    rng.shuffle(counts)
    return counts


def _draw_general(
    h,
    w,
    n_colors,
    marker_counts,
    edge_touching,
    sample_index,
    rng,
):
    grid = full_grid(h, w, 0)
    colors = rng.sample(_CARDINAL_COLORS, n_colors)
    slots = _slots(h, w, n_colors, edge_touching, rng)
    styles_seen = []
    for index, (color, slot, markers) in enumerate(
        zip(colors, slots, marker_counts)
    ):
        require_edge = edge_touching and index == 0
        candidates = _rectangle_candidates(
            slot, markers, h, w, require_edge=require_edge
        )
        if not candidates:
            raise AssertionError(
                "no lawful rectangle candidate for an advertised override combination"
            )
        if index == 0:
            thick_candidates = [
                box
                for box in candidates
                if box[2] - box[0] >= 2 and box[3] - box[1] >= 2
            ]
            if thick_candidates:
                candidates = thick_candidates
        requested_style = (
            "opposite_corners",
            "split_extrema",
            "interior",
        )[(sample_index + index) % 3]
        if markers == 2:
            requested_style = "opposite_corners"
        if requested_style == "interior":
            styled_candidates = [
                box
                for box in candidates
                if box[2] - box[0] >= 2 and box[3] - box[1] >= 2
            ]
            if styled_candidates:
                candidates = styled_candidates
            else:
                requested_style = "split_extrema"
        if requested_style == "split_extrema":
            styled_candidates = [
                box
                for box in candidates
                if box[2] - box[0] >= 2 or box[3] - box[1] >= 2
            ]
            if styled_candidates:
                candidates = styled_candidates
            else:
                requested_style = "opposite_corners"
        # Prefer moderate rectangles, but retain large and thin cases as the
        # slot shape changes across seeds and difficulty bands.
        candidates.sort(
            key=lambda box: (
                abs((box[2] - box[0] + 1) * (box[3] - box[1] + 1) - (markers + 3)),
                box,
            )
        )
        near_pool = candidates[: max(1, min(12, len(candidates)))]
        moderate_pool = [
            box
            for box in candidates
            if box[2] - box[0] + 1 <= 6
            and box[3] - box[1] + 1 <= 6
        ]
        pool = (
            moderate_pool
            if moderate_pool and rng.random() < 0.35
            else near_pool
        )
        box = rng.choice(pool)
        chosen = _choose_markers(box, markers, rng, requested_style)
        styles_seen.append(_marker_style(chosen, box))
        for r, c in chosen:
            grid[r][c] = color

    # This is a construction invariant, not an output path.  Keeping the check
    # local catches future slot/marker refactors before malformed data escapes.
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid, tuple(styles_seen)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)

    if overrides.get("mixed_marker_counts") is not None:
        mixed_marker_counts = ctx.draw_choice(
            "mixed_marker_counts", (False, True)
        )
    elif has_override:
        # Preserve exact single-axis behavior for callers that predate this
        # axis: an explicit call remains uniform unless it opts into mixing.
        mixed_marker_counts = ctx.draw_choice(
            "mixed_marker_counts", (False,)
        )
    else:
        scheduled_mixed = schedule_profile(seed, sample_index, difficulty) == (
            "mixed_marker_counts"
        )
        mixed_marker_counts = ctx.draw_choice(
            "mixed_marker_counts", (scheduled_mixed,)
        )

    profile = None
    if not has_override and not mixed_marker_counts:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}", tuple(range(len(_PROFILE_GRIDS)))
            )
            profile = _PROFILE_GRIDS[profile_index]

    if profile is not None:
        grid = _rename_and_reflect_profile(profile, ctx.draw_rng("layout"))
        observed = _analyze_scene(grid)
        ctx.draw_int("grid_h", observed["h"], observed["h"])
        ctx.draw_int("grid_w", observed["w"], observed["w"])
        ctx.draw_int("n_colors", 2, 2)
        ctx.draw_int("markers_per_color", 2, 2)
        # The scheduled mixed-count draw above is already recorded as false.
        ctx.draw_choice("edge_touching", (observed["edge_touching"],))
    else:
        h = _draw_int_axis(
            ctx,
            overrides,
            "grid_h",
            {
                "easy": (6, 9),
                "medium": (8, 13),
                "hard": (12, 18),
            }[band],
            _VALID_H,
        )
        w = _draw_int_axis(
            ctx,
            overrides,
            "grid_w",
            {
                "easy": (8, 11),
                "medium": (10, 15),
                "hard": (15, 20),
            }[band],
            _VALID_W,
        )
        n_colors = _draw_int_axis(
            ctx,
            overrides,
            "n_colors",
            {
                "easy": (2, 2),
                "medium": (2, 3),
                "hard": (3, 4),
            }[band],
            _VALID_COLORS,
        )
        marker_floor = _draw_int_axis(
            ctx,
            overrides,
            "markers_per_color",
            {
                "easy": (2, 2),
                "medium": (2, 3),
                "hard": (3, 3) if mixed_marker_counts else (3, 4),
            }[band],
            (2, 3) if mixed_marker_counts else _VALID_MARKERS,
        )
        edge_touching = ctx.draw_choice("edge_touching", _EDGE_CHOICES)
        marker_counts = _marker_counts(
            n_colors,
            marker_floor,
            mixed_marker_counts,
            ctx.draw_rng("marker_counts"),
        )
        grid, _styles = _draw_general(
            h,
            w,
            n_colors,
            marker_counts,
            edge_touching,
            sample_index,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
