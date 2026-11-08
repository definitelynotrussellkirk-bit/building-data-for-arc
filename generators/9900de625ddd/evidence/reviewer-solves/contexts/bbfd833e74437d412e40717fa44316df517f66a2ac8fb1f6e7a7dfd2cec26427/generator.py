"""Inputs for the unchanged monochrome 3x3-window Racket authority.

Every matching window contributes its center, including overlapping windows.
Separated patches include solid rectangles and carefully chosen near misses.
No output labels are generated here. See SUMMARY.md for the finite teaching
contract and its three-profile consecutive-demo schedule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9900de625ddd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "f64febd0911d"
SUMMARY = (
    "On a zero background, retain the center of EVERY solid nonzero monochrome "
    "3x3 window. Larger rectangles and corner-notched 4x4 patches yield "
    "overlapping centers. Other patches include recolored corners/edges, "
    "holes, small squares, and attached tails."
)
INVARIANTS = [
    "rectangular integer grid, dimensions 5..24 and colors 0..9; background 0 is present",
    "1..6 separated nonzero patches; 1..6 distinct foreground colors",
    "patches are solid 3..5 by 3..5 rectangles, corner-notched 4x4, 2x2 squares, one-hole 3x3, recolored 3x3, or 3x3 with one tail cell",
    "at least one complete nonzero monochrome 3x3 window exists",
    "requested patch and visible-color counts are exact; infeasible combinations fail explicitly",
]

HELPFUL_TEXTURES = ("3x3", "overlap", "contrast")
AXES = {
    "grid_h": {"type": "int", "default": "5..24; canonical profile favored", "valid": "5..24"},
    "grid_w": {"type": "int", "default": "5..24; canonical profile favored", "valid": "5..24"},
    "blocks": {"type": "int", "default": "1..6 separated nonzero patches", "valid": "1..6"},
    "n_distinct_colors": {"type": "int", "default": "1..6 visible foreground colors", "valid": "1..6"},
    "texture": {"type": "str", "default": "three-profile teaching schedule", "valid": "|".join(HELPFUL_TEXTURES)},
}
# Refusals are dynamic geometric/count constraints carrying the explicit axes.
# The empty table opts into strict auditing; the exception supplies evidence.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "overlap", "contrast")
MIN_STRICT_FRAC = 1.0
_CANONICAL_PROFILES = ((7, 12, 2), (8, 11, 3), (9, 9, 2), (9, 10, 2), (10, 10, 2))


class IncompatibleOverrides(ValueError):
    """A well-typed combination cannot be constructed in the stated domain."""

    def __init__(self, message, axes):
        self.incompatible_axes = tuple(sorted(axes))
        super().__init__(f"{message}; incompatible axes: {', '.join(self.incompatible_axes)}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Unforced draws: every three consecutive indices cover all profiles."""
    return SCHEDULE_PROFILES[(seed + sample_index) % SCHEDULE_PERIOD]


def _capacity(h, w, side):
    return ((h + 1) // (side + 1)) * ((w + 1) // (side + 1))


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if name == "texture":
            if value not in HELPFUL_TEXTURES:
                raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")
        else:
            lo, hi = (5, 24) if name in ("grid_h", "grid_w") else (1, 6)
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _pick(ctx, name, choices, *, anchor=None, favored=()):
    """Record the exact accepted value, never a value subsequently clipped."""
    if name not in ctx.overrides and anchor in choices:
        return ctx.draw_choice(name, [anchor])
    return ctx.draw_choice(name, list(choices) + [v for v in favored if v in choices])


def _configuration(ctx, seed, sample_index, difficulty, overrides):
    hmax, wmax = overrides.get("grid_h", 24), overrides.get("grid_w", 24)
    requested_colors = overrides.get("n_distinct_colors", 1)
    textures = []
    for texture in HELPFUL_TEXTURES:
        minimum = max(requested_colors, 3 if texture == "contrast" else 1)
        maximum = min(6, _capacity(hmax, wmax, 4 if texture == "overlap" else 3))
        if texture == "contrast" and overrides.get("n_distinct_colors") == 1:
            continue
        if minimum <= overrides.get("blocks", minimum) <= maximum:
            textures.append(texture)
    if not textures or ("texture" in overrides and overrides["texture"] not in textures):
        raise IncompatibleOverrides("patch count, palette, texture and canvas cannot coexist", overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    wanted = "3x3" if profile == "canonical" else profile
    texture = _pick(ctx, "texture", textures, anchor=wanted)
    core = texture == "3x3" and profile == "canonical"
    ah, aw, ac = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
    side = 4 if texture == "overlap" else 3
    minimum = max(requested_colors, 3 if texture == "contrast" else 1)
    maximum = min(6, _capacity(hmax, wmax, side))
    favored_count = {"easy": 2, "medium": 3, "hard": 5}.get(difficulty, 3)
    count = _pick(ctx, "blocks", range(minimum, maximum + 1),
                  anchor=ac if core else None, favored=[favored_count] * 5)
    heights = [h for h in range(5, 25) if _capacity(h, wmax, side) >= count]
    size_hint = {"easy": 9, "medium": 12, "hard": 17}.get(difficulty, 12)
    h = _pick(ctx, "grid_h", heights, anchor=ah if core else None, favored=[size_hint] * 5)
    widths = [w for w in range(5, 25) if _capacity(h, w, side) >= count]
    w = _pick(ctx, "grid_w", widths, anchor=aw if core else None, favored=[size_hint] * 5)
    color_minimum = 2 if texture == "contrast" else 1
    colors = _pick(ctx, "n_distinct_colors", range(color_minimum, count + 1),
                   anchor=ac if core else None, favored=[2, 2, 3])
    return h, w, count, colors, texture


def _segments(total, count, minimum, rng):
    """Distribute slack among cells and both outer margins; gaps remain zero."""
    extras = [0] * (count + 2)
    for _ in range(total - count * minimum - (count - 1)):
        extras[rng.randrange(len(extras))] += 1
    starts, position = [], extras[0]
    for index in range(count):
        length = minimum + extras[index + 1]
        starts.append((position, length))
        position += length + 1
    return starts


def _slots(h, w, count, side, rng):
    layouts = [(nr, nc) for nr in range(1, count + 1) for nc in range(1, count + 1)
               if nr * nc >= count and nr * side + nr - 1 <= h and nc * side + nc - 1 <= w]
    fewest = min(nr * nc for nr, nc in layouts)
    nr, nc = rng.choice([(nr, nc) for nr, nc in layouts if nr * nc == fewest])
    rows, cols = _segments(h, nr, side, rng), _segments(w, nc, side, rng)
    slots = [(r, c, rh, cw) for r, rh in rows for c, cw in cols]
    rng.shuffle(slots)
    return slots[:count]


def _patch(texture, index, slot_h, slot_w, color, palette, rng, *, notched=False):
    if texture == "overlap":
        # A corner-notched 4x4 has three overlapping windows in a positive
        # nonrectangular component. Forced overlap keeps the complete 4x4;
        # further patches are ordinary independently sized solid rectangles.
        ph, pw = (4, 4) if index == 0 else (rng.randint(3, min(5, slot_h)), rng.randint(3, min(5, slot_w)))
        patch = full_grid(ph, pw, color)
        if index == 0 and notched:
            r, c = rng.choice(((0, 0), (0, 3), (3, 0), (3, 3)))
            patch[r][c] = 0
        return patch
    patch = full_grid(3, 3, color)
    if texture == "3x3" or index == 0:
        return patch
    if index in (1, 2):
        choices = ((0, 0), (0, 2), (2, 0), (2, 2)) if index == 1 else ((0, 1), (1, 0), (1, 2), (2, 1))
        r, c = rng.choice(choices)
        patch[r][c] = rng.choice([v for v in palette if v != color])
        return patch
    kinds = ["solid", "hole", "small"]
    if slot_w >= 4 or slot_h >= 4:
        kinds.append("tail")
    kind = rng.choice(kinds)
    if kind == "hole":
        patch[rng.randrange(3)][rng.randrange(3)] = 0
    elif kind == "small":
        patch = full_grid(2, 2, color)
    elif kind == "tail":
        horizontal = slot_w >= 4 and (slot_h < 4 or rng.randrange(2) == 0)
        patch = full_grid(3, 4, 0)
        for r in range(3):
            for c in range(3):
                patch[r][c] = color
        patch[rng.randrange(3)][3] = color
        if rng.randrange(2):
            patch = [row[::-1] for row in patch]
        if not horizontal:
            patch = [list(row) for row in zip(*patch)]
    return patch


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w, count, ncolors, texture = _configuration(ctx, seed, sample_index, difficulty, overrides)
    rng = ctx.draw_rng("patch_layout")
    slots = _slots(h, w, count, 4 if texture == "overlap" else 3, rng)
    palette = ctx.draw_rng("palette").sample(range(1, 10), ncolors)
    colors = palette + [rng.choice(palette) for _ in range(count - ncolors)]
    rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for index, ((r0, c0, sh, sw), color) in enumerate(zip(slots, colors)):
        patch = _patch(texture, index, sh, sw, color, palette, rng,
                       notched="texture" not in overrides)
        r0 += rng.randrange(sh - len(patch) + 1)
        c0 += rng.randrange(sw - len(patch[0]) + 1)
        for dr, row in enumerate(patch):
            for dc, value in enumerate(row):
                grid[r0 + dr][c0 + dc] = value
    return grid


def _components(grid):
    """Four-connected nonzero patches, independent of their internal colors."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        part, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    part.add(point)
                    todo.append(point)
        components.append(part)
    return components


def _bounds(part):
    return min(r for r, c in part), min(c for r, c in part), max(r for r, c in part), max(c for r, c in part)


def _solid_centers(grid):
    """Positions used only for input-domain validation and witness predicates."""
    return {(r, c) for r in range(1, len(grid) - 1) for c in range(1, len(grid[0]) - 1)
            if grid[r][c] != 0 and all(grid[r + dr][c + dc] == grid[r][c]
                                      for dr in (-1, 0, 1) for dc in (-1, 0, 1))}


def _kind(grid, part):
    r0, c0, r1, c1 = _bounds(part)
    h, w = r1 - r0 + 1, c1 - c0 + 1
    counts = Counter(grid[r][c] for r, c in part)
    if len(counts) == 1:
        if (h, w, len(part)) == (4, 4, 15) and any(
                point not in part for point in ((r0, c0), (r0, c1), (r1, c0), (r1, c1))):
            return "notched"
        if len(part) == h * w and 3 <= h <= 5 and 3 <= w <= 5:
            return "3x3" if (h, w) == (3, 3) else "rectangle"
        if (h, w, len(part)) == (2, 2, 4):
            return "small"
        if (h, w, len(part)) == (3, 3, 8):
            return "hole"
        if (h, w) in ((3, 4), (4, 3)) and len(part) == 10:
            if any({(r + dr, c + dc) for dr in range(3) for dc in range(3)} <= part
                   for r in range(r0, r1 - 1) for c in range(c0, c1 - 1)):
                return "tail"
    if (h, w, len(part)) == (3, 3, 9) and sorted(counts.values()) == [1, 8]:
        return "mixed"
    return "unsupported"


def observe_overrides(grid):
    """Recover exact controls from pixels, with no stored draw metadata."""
    parts = _components(grid)
    kinds = [_kind(grid, part) for part in parts]
    if kinds and all(kind == "3x3" for kind in kinds):
        texture = "3x3"
    elif any(kind in ("rectangle", "notched") for kind in kinds) and all(
            kind in ("3x3", "rectangle", "notched") for kind in kinds):
        texture = "overlap"
    elif "mixed" in kinds:
        texture = "contrast"
    else:
        texture = "other"
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "blocks": len(parts),
            "n_distinct_colors": len({v for row in grid for v in row} - {0}), "texture": texture}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    if not (5 <= len(grid) <= 24 and 5 <= len(grid[0]) <= 24):
        return ["canvas dimensions must be 5..24"]
    palette = {value for row in grid for value in row}
    if 0 not in palette or not 1 <= len(palette - {0}) <= 6:
        return ["zero background and 1..6 foreground colors are required"]
    parts = _components(grid)
    errors = []
    if not 1 <= len(parts) <= 6:
        errors.append("expected 1..6 nonzero patches")
    if any(_kind(grid, part) == "unsupported" for part in parts):
        errors.append("patch outside the documented rectangle/near-miss grammar")
    ownership = {point: index for index, part in enumerate(parts) for point in part}
    if any((r + dr, c + dc) in ownership and ownership[(r + dr, c + dc)] != index
           for (r, c), index in ownership.items() for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
        errors.append("distinct patches must have at least one separating background cell")
    if not _solid_centers(grid):
        errors.append("at least one monochrome 3x3 window is required")
    return errors


def strict_canonical_like(grid):
    """Lawful members of the documented task domain, including overlap cases."""
    return self_check(grid)


def _component_centers(grid, exact=False, erode=False):
    out = full_grid(len(grid), len(grid[0]), 0)
    for part in _components(grid):
        r0, c0, r1, c1 = _bounds(part)
        if exact and _kind(grid, part) != "3x3":
            continue
        color = Counter(grid[r][c] for r, c in part).most_common(1)[0][0]
        points = ((r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)) if erode else [((r0 + r1) // 2, (c0 + c1) // 2)]
        for r, c in points:
            out[r][c] = color
    return out


def _exact_3x3_components(grid):
    return _component_centers(grid, exact=True)


def _one_center_per_component(grid):
    return _component_centers(grid)


def _bbox_erosion(grid):
    return _component_centers(grid, erode=True)


def _rectangles_only_erosion(grid):
    """Rival: discard nonrectangular components, even when they contain windows."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for part in _components(grid):
        r0, c0, r1, c1 = _bounds(part)
        colors = {grid[r][c] for r, c in part}
        if len(colors) == 1 and len(part) == (r1 - r0 + 1) * (c1 - c0 + 1):
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    out[r][c] = grid[r][c]
    return out


def _one_center_per_color(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for color in sorted({v for row in grid for v in row} - {0}):
        part = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        r0, c0, r1, c1 = _bounds(part)
        out[(r0 + r1) // 2][(c0 + c1) // 2] = color
    return out


def _local_rival(grid, kind):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            color = grid[r][c]
            if color == 0:
                continue
            values = [grid[r + dr][c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)]
            if kind == "occupancy":
                match = all(values)
            elif kind == "eight":
                match = values.count(color) >= 8
            else:
                offsets = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)) if kind == "cross" else ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
                match = all(grid[r + dr][c + dc] == color for dr, dc in offsets)
            if match:
                out[r][c] = color
    return out


def _occupancy_windows(grid):
    return _local_rival(grid, "occupancy")


def _cross_centers(grid):
    return _local_rival(grid, "cross")


def _diagonal_centers(grid):
    return _local_rival(grid, "diagonal")


def _majority_eight_windows(grid):
    return _local_rival(grid, "eight")


def _disjoint_windows(grid):
    out, used = full_grid(len(grid), len(grid[0]), 0), set()
    for r, c in sorted(_solid_centers(grid)):
        window = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if not window & used:
            out[r][c] = grid[r][c]
            used.update(window)
    return out


def _has_overlap(grid):
    return any(_kind(grid, part) in ("rectangle", "notched") and
               _bounds(part)[2] - _bounds(part)[0] >= 3 and
               _bounds(part)[3] - _bounds(part)[1] >= 3 for part in _components(grid))


def _has_positive_nonrectangle(grid):
    return any(_kind(grid, part) in ("notched", "tail") for part in _components(grid))


def _mixed_position(grid, corner):
    for part in _components(grid):
        if _kind(grid, part) != "mixed":
            continue
        r0, c0, r1, c1 = _bounds(part)
        counts = Counter(grid[r][c] for r, c in part)
        minority = next(color for color, count in counts.items() if count == 1)
        r, c = next((r, c) for r, c in part if grid[r][c] == minority)
        is_corner = r in (r0, r1) and c in (c0, c1)
        is_edge = (r in (r0, r1)) != (c in (c0, c1))
        if (corner and is_corner) or (not corner and is_edge):
            return True
    return False


def _has_mixed_corner(grid):
    return _mixed_position(grid, True)


def _has_mixed_edge(grid):
    return _mixed_position(grid, False)


# Deliberate wrong programs, not alternate output authorities.
SEMANTIC_RIVALS = {
    "exact_3x3_components": _exact_3x3_components,
    "one_center_per_component": _one_center_per_component,
    "one_center_per_color": _one_center_per_color,
    "occupancy_windows": _occupancy_windows,
    "cross_centers": _cross_centers,
    "diagonal_centers": _diagonal_centers,
    "majority_eight_windows": _majority_eight_windows,
    "bbox_erosion": _bbox_erosion,
    "rectangles_only_erosion": _rectangles_only_erosion,
    "disjoint_windows": _disjoint_windows,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "overlapping_windows": _has_overlap,
    "recolored_corner": _has_mixed_corner,
    "recolored_edge": _has_mixed_edge,
    "positive_nonrectangle": _has_positive_nonrectangle,
}
WITNESS_RIVALS = {
    "overlapping_windows": ["exact_3x3_components", "one_center_per_component", "one_center_per_color", "disjoint_windows"],
    "recolored_corner": ["occupancy_windows", "cross_centers", "majority_eight_windows", "bbox_erosion"],
    "recolored_edge": ["occupancy_windows", "diagonal_centers", "majority_eight_windows", "bbox_erosion"],
    "positive_nonrectangle": ["rectangles_only_erosion"],
}


def lesson_identifiable(demos, query):
    """Require visible demos to eliminate the finite declared rival set.

    This is not unique induction among arbitrary programs. Query labels are
    deliberately not used to claim that the demonstrations teach.
    """
    if not demos:
        return ["no demonstrations"]
    return [f"surviving declared rival: {name}" for name, rival in LESSON_COMPETITORS.items()
            if all(rival(demo["input"]) == demo["output"] for demo in demos)]
