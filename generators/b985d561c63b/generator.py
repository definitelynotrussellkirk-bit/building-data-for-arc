"""Input distribution for complete bounding-box template stamping (e76a88a6).

The canonical Racket rule supplies labels. Default three-demo lessons alternate
fresh canonical-style rectangles with explicit zero/surplus/position witnesses.
See workspace/probe_distribution.py for source-bound Racket/lesson measurements.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b985d561c63b"
TASK_ID = "b985d561c63b"
VERSION = "3.0.0"
RULE_HASH = "c86839f15a5d"
SUMMARY = (
    "Copy a connected multicolor source bounding box, including its zeros, into "
    "each gray rectangle at its top-left corner; retain gray beyond the stamp. "
    "Alternate fresh canonical-size examples with explicit shortcut witnesses."
)
INVARIANTS = [
    "one connected nonzero non-gray source has a 2..5 by 2..5 isolated bounding box",
    "the source realizes exactly 2..3 colors, excluding background 0 and target gray 5",
    "1..4 solid gray rectangles contain the entire stamp and have uniform 0..2 row/column surplus",
    "source and targets have at least one empty-cell gap between their bounding boxes",
    "default three-consecutive-draw lessons contain a zero-copy, surplus-gray, and source-position witness",
]
AXES = {
    "grid_h": {"type": "int", "default": "core 10; broad band-weighted 9..22", "valid": "9..22"},
    "grid_w": {"type": "int", "default": "core 10; broad band-weighted 9..22", "valid": "9..22"},
    "template_h": {"type": "int", "default": "core 3..4; broad 2..5", "valid": "2..5"},
    "template_w": {"type": "int", "default": "core 3..4; broad 2..5", "valid": "2..5"},
    "region_count": {"type": "int", "default": "core 2..3; broad band-weighted 1..4", "valid": "1..4"},
    "palette_size": {"type": "int", "default": "core 2; broad 2..3", "valid": "2..3"},
    "template_style": {"type": "str", "default": "core dense; extension punctured", "valid": "dense|punctured"},
    "extra_rows": {"type": "int", "default": "core 0; extension 0..2 with positive surplus", "valid": "0..2"},
    "extra_cols": {"type": "int", "default": "core 0; extension 0..2 with positive surplus", "valid": "0..2"},
}
# No broad catch-all exemptions. Infeasible geometry carries the exact pinned
# geometric axes in ValueError.incompatible_axes, accepted by the shared gate.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("core", "extension")
_RANGES = {
    "grid_h": (9, 22), "grid_w": (9, 22), "template_h": (2, 5),
    "template_w": (2, 5), "region_count": (1, 4), "palette_size": (2, 3),
    "extra_rows": (0, 2), "extra_cols": (0, 2),
}
_GEOMETRY = ("grid_h", "grid_w", "template_h", "template_w", "region_count", "extra_rows", "extra_cols")


def schedule_profile(seed, sample_index, difficulty=None):
    """A hashed seed phase avoids the seed==sample_index census alias."""
    phase = stable_rng(seed, TASK_ID + "/profile_phase", VERSION).randrange(2)
    return SCHEDULE_PROFILES[(sample_index + phase) % 2]


def _validate_call_scalars(seed, sample_index):
    """Reject implicit coercions before schedule or RNG state is touched."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or removed override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "template_style":
            if value not in ("dense", "punctured"):
                raise ValueError("template_style must be dense or punctured")
        else:
            lo, hi = _RANGES[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _capacity(h, w, rh, rw):
    return ((h + 1) // (rh + 1)) * ((w + 1) // (rw + 1))


def _preferences(name, preferred, overrides, rng):
    if overrides.get(name) is not None:
        return [overrides[name]]
    lo, hi = _RANGES[name]
    rest = list(range(lo, hi + 1))
    rng.shuffle(rest)
    return [preferred] + [value for value in rest if value != preferred]


def _geometry(ctx, profile, band, overrides):
    """Choose a feasible joint domain before recording exact keyed values.

    A source reserves a target-sized slot as well. This conservative constructive
    packing is explicit; it never silently reduces an explicitly requested count.
    """
    rng = ctx.draw_rng("geometry/" + band)
    if profile == "core":
        th, tw = rng.choice(((3, 3), (3, 4), (4, 3)))
        defaults = dict(grid_h=10, grid_w=10, template_h=th, template_w=tw,
                        region_count=3 if band == "hard" else 2,
                        extra_rows=0, extra_cols=0)
    else:
        low, high = {"easy": (10, 14), "medium": (11, 18), "hard": (15, 22)}[band]
        er, ec = rng.choice([(a, b) for a in range(3) for b in range(3) if a or b])
        defaults = dict(grid_h=rng.randint(low, high), grid_w=rng.randint(low, high),
                        template_h=rng.randint(2, 5), template_w=rng.randint(2, 5),
                        region_count=rng.choice({"easy": (1, 2), "medium": (2, 3), "hard": (3, 4)}[band]),
                        extra_rows=er, extra_cols=ec)
    choices = {name: _preferences(name, defaults[name], overrides, rng) for name in _GEOMETRY}
    keep_surplus = profile == "extension" and not (
        overrides.get("extra_rows") == 0 and overrides.get("extra_cols") == 0)
    found = None
    # A teaching preference must not make otherwise feasible explicit pins
    # impossible. Try positive surplus first, then allow a zero-surplus
    # completion of tight geometry pins. Ordinary unpinned draws keep their
    # guaranteed surplus witness and their original keyed choices.
    policies = [keep_surplus]
    if keep_surplus and any(overrides.get(name) is not None for name in _GEOMETRY):
        policies.append(False)
    for require_surplus in policies:
        for th, tw, count, er, ec in product(*(choices[name] for name in
                ("template_h", "template_w", "region_count", "extra_rows", "extra_cols"))):
            if require_surplus and er == ec == 0:
                continue
            rh, rw = th + er, tw + ec
            if _capacity(max(choices["grid_h"]), max(choices["grid_w"]), rh, rw) < count + 1:
                continue
            for h, w in product(choices["grid_h"], choices["grid_w"]):
                if _capacity(h, w, rh, rw) >= count + 1:
                    found = dict(grid_h=h, grid_w=w, template_h=th, template_w=tw,
                                 region_count=count, extra_rows=er, extra_cols=ec)
                    break
            if found is not None:
                break
        if found is not None:
            break
    if found is None:
        pins = tuple(name for name in _GEOMETRY if overrides.get(name) is not None)
        exc = ValueError(f"incompatible slot-packing geometry for pins {pins}; "
                         "all source/target footprints need an empty-cell gap")
        exc.incompatible_axes = pins
        raise exc
    # These are feasible joint keyed draws, not a post-draw clamp. Every supplied
    # override is checked again by GenCtx and every observed value is recorded.
    return {name: ctx.draw_choice(name, (found[name],)) for name in _GEOMETRY}


def _starts(length, size, count, rng):
    slack = length - count * size - (count - 1)
    cuts = sorted(rng.sample(range(slack + count), count))
    return [i * (size + 1) + cut - i for i, cut in enumerate(cuts)]


def _layout(ctx, shape, profile):
    h, w = shape["grid_h"], shape["grid_w"]
    th, tw = shape["template_h"], shape["template_w"]
    rh, rw = th + shape["extra_rows"], tw + shape["extra_cols"]
    count = shape["region_count"] + 1
    rng = ctx.draw_rng("layout")
    plans = [(nr, nc) for nr in range(1, (h + 1) // (rh + 1) + 1)
             for nc in range(1, (w + 1) // (rw + 1) + 1) if nr * nc >= count]
    nr, nc = rng.choice(plans)
    rows = _starts(h, rh, nr, rng)
    cols = _starts(w, rw, nc, rng)
    places = rng.sample(list(product(rows, cols)), count)
    # The extension must refute choosing the leftmost object as the source.
    choices = places if profile == "core" else [p for p in places if p != min(places, key=lambda p: (p[1], p[0]))]
    source_slot = rng.choice(choices)
    source = (source_slot[0] + rng.randint(0, rh - th),
              source_slot[1] + rng.randint(0, rw - tw))
    return source, [p for p in places if p != source_slot]


def _template(ctx, th, tw, colors, style):
    rng = ctx.draw_rng("template")
    cells = list(product(range(th), range(tw)))
    if style == "punctured":
        interior = [(r, c) for r, c in cells if 0 < r < th - 1 and 0 < c < tw - 1]
        # A single interior hole, or one corner for a two-cell-thick source,
        # leaves the colored source connected and preserves its exact bbox.
        hole = rng.choice(interior or [(0, 0), (0, tw - 1), (th - 1, 0), (th - 1, tw - 1)])
        cells.remove(hole)
    values = {p: rng.choice(colors) for p in cells}
    for point, color in zip(rng.sample(cells, len(colors)), colors):
        values[point] = color
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_scalars(seed, sample_index)
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    band = difficulty or "medium"
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    shape = _geometry(ctx, profile, band, overrides)
    style = overrides.get("template_style") or ("dense" if profile == "core" else "punctured")
    style = ctx.draw_choice("template_style", (style,))
    n_colors = overrides.get("palette_size")
    if n_colors is None:
        n_colors = 2 if profile == "core" else ctx.draw_rng("palette_size_preference").choice((2, 3))
    n_colors = ctx.draw_choice("palette_size", (n_colors,))
    colors = ctx.draw_distinct_colors("template_colors", n=n_colors, exclude=(0, 5))
    source, targets = _layout(ctx, shape, profile)
    th, tw = shape["template_h"], shape["template_w"]
    grid = full_grid(shape["grid_h"], shape["grid_w"], 0)
    for (dr, dc), color in _template(ctx, th, tw, colors, style).items():
        grid[source[0] + dr][source[1] + dc] = color
    for r0, c0 in targets:
        for dr in range(th + shape["extra_rows"]):
            for dc in range(tw + shape["extra_cols"]):
                grid[r0 + dr][c0 + dc] = 5
    return grid


def _components(points):
    remaining = set(points)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, component = [start], []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for q in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if q in remaining:
                    remaining.remove(q)
                    stack.append(q)
        result.append(component)
    return result


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _parts(grid):
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 5)]
    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    return source, _components(gray)


def observe_overrides(grid):
    """Recover exact realized controls from pixels, independently of draw metadata."""
    source, targets = _parts(grid)
    r0, c0, r1, c1 = _bbox(source)
    a, b, d, e = _bbox(targets[0])
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "template_h": r1-r0, "template_w": c1-c0,
        "region_count": len(targets),
        "palette_size": len({grid[r][c] for r, c in source}),
        "template_style": "dense" if len(source) == (r1-r0)*(c1-c0) else "punctured",
        "extra_rows": d-a-(r1-r0), "extra_cols": e-b-(c1-c0),
    }


def _separated(a, b):
    return a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular integer grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9, excluding bool and float"]
    h, w = len(grid), len(grid[0])
    if not (9 <= h <= 22 and 9 <= w <= 22):
        return ["canvas dimensions must be 9..22"]
    source, targets = _parts(grid)
    if not source or not targets:
        return ["need a non-gray colored source and at least one gray target"]
    errors = []
    sb = _bbox(source)
    th, tw = sb[2]-sb[0], sb[3]-sb[1]
    if not (2 <= th <= 5 and 2 <= tw <= 5):
        errors.append("source bounding box must be 2..5 by 2..5")
    if len(_components(source)) != 1:
        errors.append("colored source must be one orthogonally connected object")
    if not 2 <= len({grid[r][c] for r, c in source}) <= 3:
        errors.append("source must expose 2..3 distinct colors")
    if not 1 <= len(targets) <= 4:
        errors.append("need 1..4 distinct gray targets")
    boxes, pads = [sb], set()
    for component in targets:
        box = _bbox(component)
        rh, rw = box[2]-box[0], box[3]-box[1]
        if len(component) != rh * rw:
            errors.append("gray target must be a solid rectangle")
        if not (0 <= rh-th <= 2 and 0 <= rw-tw <= 2):
            errors.append("gray target must contain the source bbox with 0..2 surplus rows/columns")
        pads.add((rh-th, rw-tw))
        if any(not _separated(box, other) for other in boxes):
            errors.append("source and target bounding boxes need an empty-cell gap")
        boxes.append(box)
    if len(pads) != 1:
        errors.append("all targets must have the same surplus dimensions")
    return errors


def strict_canonical_like(grid):
    """Measured canonical-style subdomain, not all authority-supported extensions."""
    errors = self_check(grid)
    if errors:
        return errors
    obs = observe_overrides(grid)
    if (obs["grid_h"], obs["grid_w"], obs["palette_size"]) != (10, 10, 2):
        errors.append("canonical-style profile requires a 10x10 canvas and two source colors")
    if (obs["template_h"], obs["template_w"]) not in ((3, 3), (3, 4), (4, 3)):
        errors.append("canonical-style source dimensions are 3x3, 3x4 or 4x3")
    if obs["template_style"] != "dense" or obs["extra_rows"] or obs["extra_cols"]:
        errors.append("canonical-style sources are dense and targets congruent")
    if obs["region_count"] not in (2, 3):
        errors.append("canonical-style inputs have two or three targets")
    return errors


def _rival(grid, mode):
    """Explicitly wrong hypotheses for the gate; never used to create labels."""
    source, targets = _parts(grid)
    sb = _bbox(source)
    if mode == "leftmost_source":
        sb = min([sb] + [_bbox(t) for t in targets], key=lambda b: (b[1], b[0]))
    th, tw = sb[2]-sb[0], sb[3]-sb[1]
    out = [list(row) for row in grid]
    if mode == "clear_all_gray":
        for target in targets:
            for r, c in target:
                out[r][c] = 0
    for target in targets:
        a, b, d, e = _bbox(target)
        rh, rw = (d-a, e-b) if mode == "tile_target" else (th, tw)
        for dr in range(rh):
            for dc in range(rw):
                value = grid[sb[0] + dr % th][sb[1] + dc % tw]
                if mode == "nonzero_only" and value == 0:
                    continue
                if a+dr < len(out) and b+dc < len(out[0]):
                    out[a+dr][b+dc] = value
    return out


def _nonzero_only(grid):
    return _rival(grid, "nonzero_only")


def _clear_all_gray(grid):
    return _rival(grid, "clear_all_gray")


def _tile_target(grid):
    return _rival(grid, "tile_target")


def _leftmost_source(grid):
    return _rival(grid, "leftmost_source")


def _has_template_zero(grid):
    return observe_overrides(grid)["template_style"] == "punctured"


def _has_surplus(grid):
    obs = observe_overrides(grid)
    return obs["extra_rows"] > 0 or obs["extra_cols"] > 0


def _source_not_leftmost(grid):
    source, targets = _parts(grid)
    sb = _bbox(source)
    return any((_bbox(t)[1], _bbox(t)[0]) < (sb[1], sb[0]) for t in targets)


SEMANTIC_WITNESSES = {
    "template_zero": _has_template_zero,
    "retained_gray": _has_surplus,
    "source_not_leftmost": _source_not_leftmost,
}
SEMANTIC_RIVALS = {
    "nonzero_only": _nonzero_only, "clear_all_gray": _clear_all_gray,
    "tile_target": _tile_target, "leftmost_source": _leftmost_source,
}
WITNESS_RIVALS = {
    "template_zero": ["nonzero_only"],
    "retained_gray": ["clear_all_gray", "tile_target"],
    "source_not_leftmost": ["leftmost_source"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
