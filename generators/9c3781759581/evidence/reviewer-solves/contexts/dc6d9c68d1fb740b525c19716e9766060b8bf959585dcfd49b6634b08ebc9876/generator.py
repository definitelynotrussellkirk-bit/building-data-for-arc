"""Inputs for the unchanged marker-box crop rule (bank M48).

Color 9 defines an inclusive two-dimensional bounding box. Other cells are
payload, including distractors outside that box. Racket remains the label
authority; the small rival functions below are semantic checks only.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c3781759581"
TASK_ID = GENERATOR_ID
VERSION = "3.0.2"
RULE_HASH = "a489a823697d"
SUMMARY = (
    "Crop the inclusive bounding box of all color-9 markers, preserving every "
    "cell inside. Sparse diagonal pairs, reverse-diagonal pairs and scattered "
    "side extrema vary the box. Exterior payload distinguishes marker-defined "
    "cropping from trimming all nonzero cells; varied payload multiplicities "
    "supply counterexamples to the declared frequency shortcuts."
)
INVARIANTS = [
    "rectangular grids of literal integer colors 0..9, at most 30 rows and columns",
    "one or more color-9 markers define the inclusive crop; all other cells are payload",
    "default draws use 2 or 4 sparse markers, 0 background, and a nontrivial box",
    "default draws shrink both dimensions and contain payload inside and outside the box",
    "exact overrides are measured from pixels; impossible joint controls raise visibly",
]
TEXTURES = ("canonical_pair", "anti_diagonal", "scattered")
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES = ()
AXES = {
    "height": {"type": "int", "default": "canonical mixture or band-biased 6..30", "valid": "6..30"},
    "width": {"type": "int", "default": "canonical mixture or band-biased 6..30", "valid": "6..30"},
    "box_h": {"type": "int", "default": "feasible 3..height-1", "valid": "3..28"},
    "box_w": {"type": "int", "default": "feasible 3..width-1", "valid": "3..28"},
    "marker_count": {"type": "int", "default": "2 for diagonal pairs; 4 for scattered", "valid": "2..8"},
    "n_distinct_colors": {"type": "int", "default": "canonical 5/6 or band-biased 4..10", "valid": "3..10"},
    "texture": {"type": "str", "default": "pair/scattered/reverse/scattered schedule", "valid": "canonical_pair|anti_diagonal|scattered"},
}
_RANGES = {
    "height": (6, 30), "width": (6, 30), "box_h": (3, 28),
    "box_w": (3, 28), "marker_count": (2, 8), "n_distinct_colors": (3, 10),
}
# The named pairs are incompatible only when the box exceeds its canvas.
# Capacity failures carry the actual constrained axes on the exception.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("height", "box_h"), ("width", "box_w"),
    {"texture": "scattered", "marker_count": [2, 3]},
]
EXAMPLES_NEEDED = 4
# Twelve residues cover three input profiles and the four semantic positions.
# Every five consecutive default pairs contain at least two scattered witnesses,
# leaving one after any one query holdout. Sparse pairs also vary frequency rank.
LESSON_SCHEDULE_PERIOD = 12
_PROFILES = ((8, 9, 5), (9, 10, 5), (10, 10, 6))
_TEXTURE_SCHEDULE = ("canonical_pair", "scattered", "anti_diagonal", "scattered")


class IncompatibleOverrides(ValueError):
    """A concrete combination of otherwise valid exact controls cannot fit."""

    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(axes))


def _axis(ctx, name, default):
    """Record the actual value, with the full legal range for explicit controls."""
    lo, hi = _RANGES[name]
    if ctx.overrides.get(name) is None:
        return ctx.draw_int_strict(name, default, default)
    return ctx.draw_int_strict(name, lo, hi)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "texture":
            if value not in TEXTURES:
                raise ValueError(f"texture must be one of {TEXTURES}")
        else:
            lo, hi = _RANGES[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be a literal integer in {lo}..{hi}")


def _geometry(ctx, texture, marker_count, profile, core):
    rng = ctx.draw_rng("geometry")
    lo, hi = {"easy": (6, 12), "hard": (12, 30)}.get(ctx.difficulty, (8, 20))
    default_h = profile[0] if core else rng.randint(lo, hi)
    default_w = profile[1] if core else rng.randint(lo, hi)
    # Grow only unpinned canvas dimensions to accommodate pinned box dimensions.
    if ctx.overrides.get("box_h") is not None:
        default_h = max(default_h, ctx.overrides["box_h"] + 2)
    if ctx.overrides.get("box_w") is not None:
        default_w = max(default_w, ctx.overrides["box_w"] + 2)
    h, w = _axis(ctx, "height", default_h), _axis(ctx, "width", default_w)
    bh_pin, bw_pin = ctx.overrides.get("box_h"), ctx.overrides.get("box_w")
    for canvas, box, size, pin in (("height", "box_h", h, bh_pin),
                                  ("width", "box_w", w, bw_pin)):
        if pin is not None and pin > size:
            raise IncompatibleOverrides(f"{box}={pin} exceeds {canvas}={size}", (canvas, box))
    hs = (bh_pin,) if bh_pin is not None else range(3, min(28, h) + 1)
    ws = (bw_pin,) if bw_pin is not None else range(3, min(28, w) + 1)
    # Reserve the center for payload, and opposite/all corners to make texture
    # recoverable. At least one of those corners is kept zero in the output.
    reserved = 5 if texture == "scattered" else 3
    feasible = [(a, b) for a in hs for b in ws if a * b - reserved >= marker_count]
    if not feasible:
        axes = [key for key in ("height", "width", "box_h", "box_w", "marker_count", "texture")
                if ctx.overrides.get(key) is not None]
        raise IncompatibleOverrides("pinned box geometry has insufficient marker/payload capacity", axes)
    preferred = [(a, b) for a, b in feasible
                 if (bh_pin is not None or a < h) and (bw_pin is not None or b < w)]
    bh0, bw0 = rng.choice(preferred or feasible)
    bh, bw = _axis(ctx, "box_h", bh0), _axis(ctx, "box_w", bw0)
    top, left = rng.randrange(h - bh + 1), rng.randrange(w - bw + 1)
    return h, w, bh, bw, top, left


def _markers(ctx, texture, count, bh, bw):
    rng = ctx.draw_rng("marker_positions")
    corners = {(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)}
    center = (bh // 2, bw // 2)
    if texture == "scattered":
        chosen = [(0, rng.randrange(1, bw - 1)), (bh - 1, rng.randrange(1, bw - 1)),
                  (rng.randrange(1, bh - 1), 0), (rng.randrange(1, bh - 1), bw - 1)]
        forbidden = corners
    elif texture == "anti_diagonal":
        chosen = [(0, bw - 1), (bh - 1, 0)]
        forbidden = {(0, 0), (bh - 1, bw - 1)}
    else:
        chosen = [(0, 0), (bh - 1, bw - 1)]
        forbidden = {(0, bw - 1), (bh - 1, 0)}
    available = [(r, c) for r in range(bh) for c in range(bw)
                 if (r, c) not in forbidden and (r, c) != center and (r, c) not in chosen]
    chosen.extend(rng.sample(available, count - len(chosen)))
    return chosen, center, min(forbidden)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, 'easy', 'medium' or 'hard'")
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    residue = sample_index % LESSON_SCHEDULE_PERIOD
    desired_texture = _TEXTURE_SCHEDULE[residue % 4]
    if overrides.get("marker_count") in (2, 3) and desired_texture == "scattered":
        desired_texture = "canonical_pair"
    choices = TEXTURES if overrides.get("texture") is not None else (desired_texture,)
    texture = ctx.draw_choice("texture", choices)
    marker_count = _axis(ctx, "marker_count", 4 if texture == "scattered" else 2)
    if texture == "scattered" and marker_count < 4:
        raise IncompatibleOverrides("texture='scattered' requires marker_count >= 4", ("texture", "marker_count"))
    profile = _PROFILES[residue // 4]
    core = residue % 4 != 3
    h, w, bh, bw, top, left = _geometry(ctx, texture, marker_count, profile, core)
    palette_rng = ctx.draw_rng("palette_profile")
    color_default = profile[2] if core else palette_rng.randint(4, 6 if difficulty == "easy" else 10)
    color_count = _axis(ctx, "n_distinct_colors", color_default)
    palette = ctx.draw_distinct_colors("payload_palette", n=color_count - 2, exclude={0, 9})
    markers, center, blank = _markers(ctx, texture, marker_count, bh, bw)
    grid = full_grid(h, w, 0)
    for r, c in markers:
        grid[top + r][left + c] = 9
    content = (top + center[0], left + center[1])
    keep_zero = (top + blank[0], left + blank[1])
    occupied = {(top + r, left + c) for r, c in markers}
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) not in occupied and (r, c) != keep_zero]
    outside = [p for p in candidates
               if not (top <= p[0] < top + bh and left <= p[1] < left + bw)]
    rng = ctx.draw_rng("payload_positions")
    if texture != "scattered":
        # Canonical-like sparse payload: the markers can be most frequent.
        # Scattered samples below reverse that ordering, avoiding a new
        # always-second-most-frequent marker shortcut. Keep an exterior witness
        # using another payload color where possible, without duplicating it.
        slots = [content]
        if outside:
            slots.append(rng.choice(outside))
        remaining = [p for p in candidates if p not in slots]
        slots.extend(rng.sample(remaining, max(0, len(palette) - len(slots))))
        for index, (r, c) in enumerate(slots):
            grid[r][c] = palette[index % len(palette)]
        return grid
    # A frequent payload color refutes maximum-frequency cropping; a second
    # payload color occurring twice refutes least-repeated and least-even
    # frequency cropping. Default scattered draws always have both colors.
    # Explicit three-color controls remain legal but do not promise that lesson
    # property. Other multiplicities vary within the actual remaining capacity.
    multiplicities = [marker_count + rng.randint(1, 3)]
    if len(palette) > 1:
        multiplicities.append(2)
    spare = len(candidates) - sum(multiplicities) - (len(palette) - len(multiplicities))
    for _ in palette[len(multiplicities):]:
        extra = rng.randint(0, min(marker_count + 1, spare))
        multiplicities.append(1 + extra)
        spare -= extra
    remaining = list(candidates)
    for index, (color, count) in enumerate(zip(palette, multiplicities)):
        chosen = [content] if index == 0 else []
        exterior = [p for p in remaining if p in outside and p not in chosen]
        if exterior:
            chosen.append(rng.choice(exterior))
        free = [p for p in remaining if p not in chosen]
        chosen.extend(rng.sample(free, count - len(chosen)))
        for r, c in chosen:
            grid[r][c] = color
        remaining = [p for p in remaining if p not in chosen]
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the rule's domain, including canonical and lawful small cases."""
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["grid must have 1..30 rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["each row must be a sequence"]
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        return ["grid must be rectangular with 1..30 columns"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integers in 0..9"]
    if not any(value == 9 for row in grid for value in row):
        return ["at least one color-9 marker is required"]
    return []


def strict_canonical_like(grid):
    """The Racket-defined marker-crop domain; pair-only prose is not authority."""
    return self_check(grid)


def _cells(grid, predicate):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if predicate(value)]


def _bbox(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def _crop(grid, bounds):
    top, left, bottom, right = bounds
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def _marker_bounds(grid):
    return _bbox(_cells(grid, lambda v: v == 9))


def observe_overrides(grid):
    top, left, bottom, right = _marker_bounds(grid)
    if grid[top][left] == grid[bottom][right] == 9:
        texture = "canonical_pair"
    elif grid[top][right] == grid[bottom][left] == 9:
        texture = "anti_diagonal"
    else:
        texture = "scattered"
    return {"height": len(grid), "width": len(grid[0]), "box_h": bottom - top + 1,
            "box_w": right - left + 1, "marker_count": sum(row.count(9) for row in grid),
            "n_distinct_colors": len({v for row in grid for v in row}), "texture": texture}


def _crop_all_nonzero(grid):
    return _crop(grid, _bbox(_cells(grid, lambda v: v != 0)))


def _crop_first_last_markers(grid):
    markers = _cells(grid, lambda v: v == 9)
    return _crop(grid, _bbox((markers[0], markers[-1])))


def _crop_most_frequent_color(grid):
    counts = Counter(v for row in grid for v in row if v != 0)
    color = max(counts, key=lambda v: (counts[v], v))
    return _crop(grid, _bbox(_cells(grid, lambda v: v == color)))


def _crop_second_most_frequent_color(grid):
    counts = Counter(v for row in grid for v in row if v != 0)
    order = sorted(counts, key=lambda v: (counts[v], v), reverse=True)
    color = order[min(1, len(order) - 1)]
    return _crop(grid, _bbox(_cells(grid, lambda v: v == color)))


def _crop_least_repeated_color(grid):
    counts = Counter(v for row in grid for v in row if v != 0)
    eligible = [v for v, count in counts.items() if count > 1]
    color = min(eligible or counts, key=lambda v: (counts[v], -v))
    return _crop(grid, _bbox(_cells(grid, lambda v: v == color)))


def _crop_least_even_color(grid):
    counts = Counter(v for row in grid for v in row if v != 0)
    eligible = [v for v, count in counts.items() if count % 2 == 0]
    color = min(eligible or counts, key=lambda v: (counts[v], -v))
    return _crop(grid, _bbox(_cells(grid, lambda v: v == color)))


def _crop_columns_only(grid):
    _, left, _, right = _marker_bounds(grid)
    return [list(row[left:right + 1]) for row in grid]


def _crop_rows_only(grid):
    top, _, bottom, _ = _marker_bounds(grid)
    return [list(row) for row in grid[top:bottom + 1]]


def _keep_markers_only(grid):
    return [[v if v == 9 else 0 for v in row] for row in _crop(grid, _marker_bounds(grid))]


def _has_exterior_payload(grid):
    top, left, bottom, right = _marker_bounds(grid)
    return any(v not in (0, 9) and not (top <= r <= bottom and left <= c <= right)
               for r, row in enumerate(grid) for c, v in enumerate(row))


def _needs_all_markers(grid):
    cells = _cells(grid, lambda v: v == 9)
    return _bbox(cells) != _bbox((cells[0], cells[-1]))


def _frequency_is_not_role(grid):
    return _crop_most_frequent_color(grid) != _crop(grid, _marker_bounds(grid))


def _second_frequency_is_not_role(grid):
    return _crop_second_most_frequent_color(grid) != _crop(grid, _marker_bounds(grid))


def _least_repeated_is_not_role(grid):
    return _crop_least_repeated_color(grid) != _crop(grid, _marker_bounds(grid))


def _least_even_is_not_role(grid):
    return _crop_least_even_color(grid) != _crop(grid, _marker_bounds(grid))


def _needs_row_crop(grid):
    top, _, bottom, _ = _marker_bounds(grid)
    return top > 0 or bottom < len(grid) - 1


def _needs_column_crop(grid):
    _, left, _, right = _marker_bounds(grid)
    return left > 0 or right < len(grid[0]) - 1


def _retains_payload(grid):
    return any(v not in (0, 9) for row in _crop(grid, _marker_bounds(grid)) for v in row)


SEMANTIC_RIVALS = {
    "crop_all_nonzero": _crop_all_nonzero,
    "first_last_markers": _crop_first_last_markers,
    "most_frequent_color": _crop_most_frequent_color,
    "second_most_frequent_color": _crop_second_most_frequent_color,
    "least_repeated_color": _crop_least_repeated_color,
    "least_even_color": _crop_least_even_color,
    "columns_only": _crop_columns_only,
    "rows_only": _crop_rows_only,
    "markers_only": _keep_markers_only,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                      ("crop_all_nonzero", "first_last_markers", "most_frequent_color",
                       "least_repeated_color", "least_even_color")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "outside_content": _has_exterior_payload,
    "all_extrema": _needs_all_markers,
    "frequency_role": _frequency_is_not_role,
    "frequency_rank_varies": _second_frequency_is_not_role,
    "least_repeated_role": _least_repeated_is_not_role,
    "least_even_role": _least_even_is_not_role,
    "row_crop": _needs_row_crop,
    "column_crop": _needs_column_crop,
    "retained_content": _retains_payload,
}
WITNESS_RIVALS = {
    "outside_content": ["crop_all_nonzero"],
    "all_extrema": ["first_last_markers"],
    "frequency_role": ["most_frequent_color"],
    "frequency_rank_varies": ["second_most_frequent_color"],
    "least_repeated_role": ["least_repeated_color"],
    "least_even_role": ["least_even_color"],
    "row_crop": ["columns_only"],
    "column_crop": ["rows_only"],
    "retained_content": ["markers_only"],
}
