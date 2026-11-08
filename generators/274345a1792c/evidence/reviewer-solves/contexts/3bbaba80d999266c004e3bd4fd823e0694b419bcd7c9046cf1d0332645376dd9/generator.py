"""Inputs for prototype stamping by fixed control symbols (bank H80).

Racket remains the label authority. The Python predictions below are explicit
rivals and a diagnostic mirror, never the source of generated labels.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "274345a1792c"
TASK_ID = GENERATOR_ID
RULE_HASH = "2a00fd8158ab"
VERSION = "2.0.0"
SUMMARY = (
    "Copy the connected maroon (9) prototype in cyan (8) at each magenta (6) "
    "anchor: the cell above selects identity (1), clockwise rotation (2), "
    "left-right reflection (3), or reflection then clockwise rotation (4)."
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "one four-connected maroon prototype has 2..8 cells in a box at most 3x3",
    "1..5 magenta anchors each have one control from 1..4 directly above",
    "every control belongs to an anchor; all colors have fixed semantic roles",
    "normalized stamps fit, are pairwise disjoint, and avoid other input markers",
    "exact requested dimensions, counts and prototype quadrant are realized",
]
_QUADRANTS = ("top_left", "top_right", "bottom_left", "bottom_right")
_INT_BOUNDS = {
    "grid_h": (9, 24), "grid_w": (12, 24), "n_anchors": (1, 5),
    "prototype_cells": (2, 8), "palette_size": (4, 7),
    "n_distinct_colors": (4, 7),
}
AXES = {
    "grid_h": {"type": "int", "default": "profile/teaching/free schedule", "valid": "9..24"},
    "grid_w": {"type": "int", "default": "profile/teaching/free schedule", "valid": "12..24"},
    "n_anchors": {"type": "int", "default": "3/5/free/5 schedule", "valid": "1..5"},
    "prototype_cells": {"type": "int", "default": "2..8; teaching 6..7", "valid": "2..8"},
    "position_bias": {"type": "str", "default": "uniform prototype quadrant", "valid": "|".join(_QUADRANTS)},
    "n_distinct_colors": {"type": "int", "default": "6/7/free/7 schedule", "valid": "4..7"},
}
# Compatibility spelling, not a second independent dimension. Task-local tests
# exercise both spellings and every conflicting color-count/anchor-count pair.
OVERRIDE_ALIASES = {"palette_size": "n_distinct_colors"}
# Strict classification: only exceptions with explicit incompatible_axes count
# as legitimate joint refusals. No broad wildcard conceals placement failures.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells, code):
    if code == 1:
        return _normalize(cells)
    if code == 2:
        return _normalize((c, -r) for r, c in cells)
    if code == 3:
        return _normalize((r, -c) for r, c in cells)
    return _normalize((-c, -r) for r, c in cells)


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if p in cells and p not in seen:
                seen.add(p)
                todo.append(p)
    return seen == cells


def _asymmetric(cells):
    variants = {_transform(cells, code) for code in (1, 2, 3, 4)}
    turned = _normalize((-r, -c) for r, c in cells)
    variants.update(_transform(turned, code) for code in (1, 2, 3, 4))
    return len(variants) == 8


@lru_cache(maxsize=14)
def _polyominoes(count, asymmetric=False):
    cells = tuple((r, c) for r in range(3) for c in range(3))
    shapes = {_normalize(shape) for shape in combinations(cells, count)
              if _connected(shape)}
    return tuple(sorted(shape for shape in shapes
                        if not asymmetric or _asymmetric(shape)))


def _quadrant(cells, h, w):
    rs, cs = zip(*cells)
    vertical = "top" if min(rs) + max(rs) < h - 1 else "bottom"
    horizontal = "left" if min(cs) + max(cs) < w - 1 else "right"
    return vertical + "_" + horizontal


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = axes
    raise error


def _draw_exact(ctx, overrides, name, default):
    lo, hi = _INT_BOUNDS[name] if name in overrides else (default, default)
    return ctx.draw_int_strict(name, lo, hi)


def schedule_profile(seed, sample_index, difficulty=None):
    return ("profile", "teaching", "free", "teaching")[sample_index % 4]


SCHEDULE_PROFILES = ("profile", "teaching", "free")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - (set(AXES) | set(OVERRIDE_ALIASES))
    if unknown:
        raise ValueError("unknown override axes: " + ", ".join(sorted(unknown)))
    overrides = {k: v for k, v in overrides.items() if v is not None}
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    for name, (lo, hi) in _INT_BOUNDS.items():
        if name in overrides:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(name + " must be an integer, not a coercible value")
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be within {lo}..{hi}")
    if ("palette_size" in overrides and "n_distinct_colors" in overrides
            and overrides["palette_size"] != overrides["n_distinct_colors"]):
        _incompatible("palette_size and n_distinct_colors must agree",
                      "palette_size", "n_distinct_colors")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    if phase == 0:
        default_h, default_w = rng.choice(((14, 16), (13, 15), (15, 14), (14, 14), (15, 15)))
        default_n, default_palette = 3, 6
    elif phase == 2:
        default_h, default_w = rng.randint(9, 24), rng.randint(12, 24)
        default_n = rng.randint(1, 5)
        default_palette = 3 + rng.randint(1, min(4, default_n))
    else:
        bounds = {"easy": (13, 16, 14, 17), "medium": (13, 20, 14, 21),
                  "hard": (16, 24, 17, 24)}[difficulty or "medium"]
        default_h, default_w = rng.randint(*bounds[:2]), rng.randint(*bounds[2:])
        default_n, default_palette = 5, 7
    h = _draw_exact(ctx, overrides, "grid_h", default_h)
    w = _draw_exact(ctx, overrides, "grid_w", default_w)
    palette_keys = tuple(k for k in ("palette_size", "n_distinct_colors") if k in overrides)
    requested_palette = overrides[palette_keys[0]] if palette_keys else None
    if requested_palette is not None and "n_anchors" not in overrides:
        default_n = max(default_n, requested_palette - 3)
    n = _draw_exact(ctx, overrides, "n_anchors", default_n)
    if requested_palette is None:
        requested_palette = 3 + min(default_palette - 3, n)
    if requested_palette > n + 3:
        _incompatible("distinct controls cannot exceed the anchor count",
                      "n_anchors", *palette_keys)
    palette = _draw_exact(ctx, overrides, "n_distinct_colors", requested_palette)
    _draw_exact(ctx, overrides, "palette_size", palette)
    count = _draw_exact(ctx, overrides, "prototype_cells",
                        rng.choice((6, 7)) if phase % 2 else rng.randint(2, 8))
    # Overrides remain lawful even if they deliberately remove a teaching cue.
    teaching_shape = phase % 2 == 1 and count in (6, 7)
    shape = rng.choice(_polyominoes(count, teaching_shape))
    ph = 1 + max(r for r, _ in shape)
    pw = 1 + max(c for _, c in shape)
    quadrant = ctx.draw_choice("position_bias", _QUADRANTS)

    # All eight bins of the smallest canvas can hold either a prototype or a
    # 3x3 stamp plus its control. Six bins suffice for the largest anchor count.
    row_offset, col_offset = rng.randrange(h % 4 + 1), rng.randrange(w % 3 + 1)
    bins = [(row_offset + 4 * r, col_offset + 3 * c)
            for r in range(h // 4) for c in range(w // 3)]
    prototype_candidates = []
    for index, (br, bc) in enumerate(bins):
        for dr in range(5 - ph):
            for dc in range(4 - pw):
                cells = [(br + dr + r, bc + dc + c) for r, c in shape]
                if _quadrant(cells, h, w) == quadrant:
                    prototype_candidates.append((index, cells))
    prototype_bin, prototype = rng.choice(prototype_candidates)
    remaining = [cell for index, cell in enumerate(bins) if index != prototype_bin]
    chosen = rng.sample(remaining, n)
    codes = rng.sample((1, 2, 3, 4), palette - 3)
    codes += [rng.choice(codes) for _ in range(n - len(codes))]
    rng.shuffle(codes)
    grid = full_grid(h, w, 0)
    for r, c in prototype:
        grid[r][c] = 9
    for (br, bc), code in zip(chosen, codes):
        transformed = _transform(shape, code)
        sh = 1 + max(r for r, _ in transformed)
        sw = 1 + max(c for _, c in transformed)
        ar = br + 1 + rng.randrange(4 - sh)
        ac = bc + rng.randrange(4 - sw)
        grid[ar - 1][ac] = code
        grid[ar][ac] = 6
    return grid


def _parts(grid):
    proto = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    anchors = [(r, c, grid[r - 1][c]) for r, row in enumerate(grid)
               for c, v in enumerate(row) if v == 6 and r > 0]
    return proto, anchors


def observe_overrides(grid):
    proto, anchors = _parts(grid)
    h, w = len(grid), len(grid[0])
    palette = len({v for row in grid for v in row})
    return {"grid_h": h, "grid_w": w, "n_anchors": len(anchors),
            "prototype_cells": len(proto), "position_bias": _quadrant(proto, h, w),
            "n_distinct_colors": palette, "palette_size": palette}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or v not in (0, 1, 2, 3, 4, 6, 9)
           for row in grid for v in row):
        return ["input cells must be integer colors 0,1,2,3,4,6,9"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not 9 <= h <= 24 or not 12 <= w <= 24:
        errors.append("canvas must be 9..24 rows by 12..24 columns")
    proto, anchors = _parts(grid)
    if not 2 <= len(proto) <= 8 or not _connected(proto):
        return errors + ["one connected prototype must contain 2..8 maroon cells"]
    shape = _normalize(proto)
    if max(r for r, _ in shape) > 2 or max(c for _, c in shape) > 2:
        errors.append("prototype bounding box must fit within 3x3")
    all_anchors = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6}
    if not 1 <= len(all_anchors) <= 5:
        errors.append("expected 1..5 magenta anchors")
    if any(r == 0 or grid[r - 1][c] not in (1, 2, 3, 4) for r, c in all_anchors):
        errors.append("each anchor needs a 1..4 control directly above")
    controls = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3, 4)}
    bound_controls = {(r - 1, c) for r, c in all_anchors if r > 0}
    if controls != bound_controls:
        errors.append("every control must belong to exactly one anchor")
    protected = set(proto) | controls | all_anchors
    stamped = set()
    for ar, ac, code in anchors:
        if code not in (1, 2, 3, 4):
            continue
        stamp = {(ar + r, ac + c) for r, c in _transform(shape, code)}
        if any(not (0 <= r < h and 0 <= c < w) for r, c in stamp):
            errors.append("transformed stamp must fit in bounds")
        if stamp & (protected - {(ar, ac)}):
            errors.append("stamp overlaps prototype or another control/anchor")
        if stamp & stamped:
            errors.append("transformed stamps must be pairwise disjoint")
        stamped.update(stamp)
    return errors


def strict_canonical_like(grid):
    """The documented task domain, including all five canonical inputs."""
    return self_check(grid)


def _prediction(grid, mode="intended"):
    """Diagnostic mirror and named rivals; labels still come from Racket."""
    prototype, anchors = _parts(grid)
    shape = _normalize(prototype)
    if mode == "fixed_l":
        shape = ((0, 0), (1, 0), (2, 0), (2, 1))
    elif mode == "cap_five":
        shape = shape[:5]
    if mode == "first_three":
        anchors = anchors[:3]
    if mode == "once_per_code":
        seen = set()
        anchors = [a for a in anchors if not (a[2] in seen or seen.add(a[2]))]
    elif mode == "first_three_codes":
        allowed = list(dict.fromkeys(a[2] for a in anchors))[:3]
        anchors = [a for a in anchors if a[2] in allowed]
    out = [list(row) for row in grid]
    for ar, ac, code in anchors:
        if mode == "identity_only":
            code = 1
        elif mode == "swap_2_4":
            code = {2: 4, 4: 2}.get(code, code)
        if mode == "counterclockwise_2" and code == 2:
            transformed = _normalize((-c, r) for r, c in shape)
        elif mode == "reverse_composition_4" and code == 4:
            transformed = _normalize((c, r) for r, c in shape)
        else:
            transformed = _transform(shape, code)
        if mode == "fill_bbox":
            transformed = tuple((r, c) for r in range(1 + max(r for r, _ in transformed))
                                for c in range(1 + max(c for _, c in transformed)))
        for dr, dc in transformed:
            r, c = ar + dr, ac + dc
            if 0 <= r < len(out) and 0 <= c < len(out[0]):
                if mode != "preserve_anchor" or (r, c) != (ar, ac):
                    out[r][c] = 8
    return out


def _once_per_code(grid):
    return _prediction(grid, "once_per_code")


def _first_three(grid):
    return _prediction(grid, "first_three")


def _cap_five(grid):
    return _prediction(grid, "cap_five")


def _first_three_codes(grid):
    return _prediction(grid, "first_three_codes")


def _fixed_l(grid):
    return _prediction(grid, "fixed_l")


def _identity_only(grid):
    return _prediction(grid, "identity_only")


def _swap_2_4(grid):
    return _prediction(grid, "swap_2_4")


def _counterclockwise_2(grid):
    return _prediction(grid, "counterclockwise_2")


def _reverse_composition_4(grid):
    return _prediction(grid, "reverse_composition_4")


def _fill_bbox(grid):
    return _prediction(grid, "fill_bbox")


def _preserve_anchor(grid):
    return _prediction(grid, "preserve_anchor")


def _repeated_code_witness(grid):
    return _once_per_code(grid) != _prediction(grid)


def _many_anchors_witness(grid):
    return _first_three(grid) != _prediction(grid)


def _large_prototype_witness(grid):
    return _cap_five(grid) != _prediction(grid)


def _all_codes_witness(grid):
    return _first_three_codes(grid) != _prediction(grid)


CANONICAL_SHORTCUTS = {
    "once_per_code": _once_per_code, "first_three": _first_three, "cap_five": _cap_five,
    "first_three_codes": _first_three_codes,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
SEMANTIC_WITNESSES = {
    "repeated_code": _repeated_code_witness,
    "more_than_three_anchors": _many_anchors_witness,
    "more_than_five_prototype_cells": _large_prototype_witness,
    "all_four_control_codes": _all_codes_witness,
}
WITNESS_RIVALS = {
    "repeated_code": ["once_per_code"],
    "more_than_three_anchors": ["first_three"],
    "more_than_five_prototype_cells": ["cap_five"],
    "all_four_control_codes": ["first_three_codes"],
}
LESSON_COMPETITORS = {
    **CANONICAL_SHORTCUTS,
    "fixed_l": _fixed_l, "identity_only": _identity_only,
    "swap_2_4": _swap_2_4, "counterclockwise_2": _counterclockwise_2,
    "reverse_composition_4": _reverse_composition_4,
    "fill_bbox": _fill_bbox, "preserve_anchor": _preserve_anchor,
}


def lesson_identifiable(demos, query):
    """Finite rival check only; never a claim of universal identifiability."""
    if not isinstance(query, dict) or "output" not in query:
        return ["a labeled query is needed for the finite rival check"]
    return ["rival survives demonstrations and changes query: " + name
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
