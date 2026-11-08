"""E69: crop the uniquely smallest monochromatic four-connected component.

Only inputs are sampled here. Training labels still come from the selected
canonical Racket program. The Python mirrors below are diagnostic rivals and
semantic hooks, not an alternate label authority.

Three consecutive ordinary draws cover a sparse/compact area inversion, an
unconstrained small target, and a same-color diagonal-contact counterexample.
Objects live in randomly sized, permuted construction regions; those regions
are not painted. Different colors may touch. Repeated colors are deliberately
not a proxy for object identity. Explicit overrides preserve geometry/counts,
but can disable a scheduled witness (e.g. small_size=1 cannot invert area).
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ba988f8d25d5"
TASK_ID = "ba988f8d25d5"
VERSION = "3.0.0"
RULE_HASH = "f0c7b10ccb1c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Crop the uniquely smallest monochromatic 4-connected object. Vary target "
    "size 1..7, polyomino shape, colors, position and distractor sizes. Include "
    "sparse/compact ranking inversions, repeated colors, different-color edge "
    "contacts and same-color diagonal contacts; retain canonical-scale draws."
)
INVARIANTS = [
    "rectangular integer ARC grid, colors 0..9, with background 0",
    "at least three monochromatic four-connected foreground components",
    "exactly one component has the minimum cell count; distractors may tie",
    "the smallest object's crop contains only its color and background",
]
AXES = {
    "grid_h": {"type": "int", "default": "75% rng 10..12; 25% rng 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "75% rng 10..12; 25% rng 10..20", "valid": "10..20"},
    "n_objs": {"type": "int", "default": "rng 4..6", "valid": "3..6"},
    "small_size": {"type": "int", "default": "profile-dependent 1..7", "valid": "1..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
# Negative fixtures are not part of the valid AXES texture domain. Legacy
# palette names were inert; they now fail loudly instead of claiming support.
DEGENERATE_TEXTURES = ("equal_smallest", "single_component", "no_components")
HELPFUL_TEXTURES = ()
SCHEDULE_PROFILES = ("contrast", "general", "diagonal")


def schedule_profile(seed, sample_index, difficulty=None):
    """A sliding-window schedule, not a special case for sample_index==0."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _components(grid, *, connectivity=4, multicolor=False):
    """Input measurements; same-color 4-connectivity matches `objects g 0`."""
    h, w = len(grid), len(grid[0])
    steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            stack, cells = [(r, c)], []
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0
                            and (multicolor or grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs, cs = zip(*cells)
            result.append({"color": color, "size": len(cells), "cells": cells,
                           "bbox": (min(rs), min(cs), max(rs), max(cs))})
    return result


def _rank(obj):
    return obj["size"], obj["bbox"]


def _crop(grid, obj):
    r1, c1, r2, c2 = obj["bbox"]
    return [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]


def _area(obj):
    r1, c1, r2, c2 = obj["bbox"]
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the input manifold, including all five canonical examples."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty sequences"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return [f"grid too large: {h}x{w}"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid values must be literal integer ARC colors 0..9"]
    obs = sorted(_components(grid), key=_rank)
    if len(obs) < 3:
        return [f"expected >=3 monochromatic 4-connected components, got {len(obs)}"]
    errors = []
    if obs[0]["size"] == obs[1]["size"]:
        errors.append("minimum component size must be unique")
    if not any(v == 0 for row in grid for v in row):
        errors.append("background 0 must be present")
    if any(v not in (0, obs[0]["color"]) for row in _crop(grid, obs[0]) for v in row):
        errors.append("smallest object's bounding box contains another color")
    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict):
        realized = {"grid_h": h, "grid_w": w, "n_objs": len(obs), "small_size": obs[0]["size"]}
        for key, value in requested.items():
            if key in AXES and value is not None and realized[key] != value:
                errors.append(f"override {key}={value!r} realized as {realized[key]!r}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    obs = _components(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_objs": len(obs),
            "small_size": min((o["size"] for o in obs), default=0)}


def _normalize(cells):
    mr = min(r for r, c in cells)
    mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _dims(cells):
    return max(r for r, c in cells) + 1, max(c for r, c in cells) + 1


def _orientations(cells):
    variants = set()
    for transpose in (False, True):
        for flip_r in (-1, 1):
            for flip_c in (-1, 1):
                changed = [(flip_r * (c if transpose else r),
                            flip_c * (r if transpose else c)) for r, c in cells]
                variants.add(tuple(_normalize(changed)))
    return [list(v) for v in sorted(variants)]


def _poly(rng, size, h, w, *, corner=False):
    """Bounded connected growth; no unbounded placement/rejection loop."""
    if size > h * w:
        raise ValueError("polyomino size exceeds construction region")
    for _ in range(64):
        cells = {(rng.randrange(h), rng.randrange(w))}
        frontier = set()
        while len(cells) < size:
            for r, c in cells:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in cells:
                        frontier.add((nr, nc))
            new = rng.choice(sorted(frontier))
            cells.add(new)
            frontier.remove(new)
        cells = _normalize(cells)
        ph, pw = _dims(cells)
        if not corner or any(p in cells for p in ((0, 0), (0, pw-1), (ph-1, 0), (ph-1, pw-1))):
            return cells
    # Guaranteed connected corner-bearing fallback, not a changed size/count.
    return [(i // w, i % w) for i in range(size)]


def _split(rng, total, n, minimum):
    lengths = [minimum] * n
    for _ in range(total - n * minimum):
        lengths[rng.randrange(n)] += 1
    return lengths


def _regions(rng, h, w, n):
    """2 x (2 or 3) regions, each at least 5x3: fits every declared tuple."""
    hs = _split(rng, h, 2, 5)
    ws = _split(rng, w, 2 if n <= 4 else 3, 3)
    result, r0 = [], 0
    for ri, rh in enumerate(hs):
        c0 = 0
        for ci, cw in enumerate(ws):
            result.append((r0, c0, rh, cw, ri, ci))
            c0 += cw
        r0 += rh
    return result


def _at(cells, position):
    r0, c0 = position
    return {(r0 + r, c0 + c) for r, c in cells}


def _random_position(rng, cells, region):
    r0, c0, h, w = region[:4]
    ph, pw = _dims(cells)
    return r0 + rng.randrange(h - ph + 1), c0 + rng.randrange(w - pw + 1)


def _edge_positions(rng, first, second, a, b):
    """Place different-colored shapes across one region edge with contact."""
    ah, aw = _dims(first)
    bh, bw = _dims(second)
    if a[4] == b[4]:
        ac = a[1] + a[3] - aw if a[5] < b[5] else a[1]
        bc = b[1] if a[5] < b[5] else b[1] + b[3] - bw
        ap = [(r, ac) for r in range(a[0], a[0] + a[2] - ah + 1)]
        bp = [(r, bc) for r in range(b[0], b[0] + b[2] - bh + 1)]
    else:
        ar = a[0] + a[2] - ah if a[4] < b[4] else a[0]
        br = b[0] if a[4] < b[4] else b[0] + b[2] - bh
        ap = [(ar, c) for c in range(a[1], a[1] + a[3] - aw + 1)]
        bp = [(br, c) for c in range(b[1], b[1] + b[3] - bw + 1)]
    rng.shuffle(ap)
    rng.shuffle(bp)
    for pa in ap:
        ca = _at(first, pa)
        adjacent = {(r + dr, c + dc) for r, c in ca for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))}
        for pb in bp:
            if adjacent & _at(second, pb):
                return pa, pb
    raise AssertionError("adjacent regions could not realize an edge contact")



def _edge_pair(rng, first, second, a, b):
    """Try finite shape orientations: fixed boundary supports can be disjoint."""
    variants_a = [v for v in _orientations(first) if _dims(v)[0] <= a[2] and _dims(v)[1] <= a[3]]
    variants_b = [v for v in _orientations(second) if _dims(v)[0] <= b[2] and _dims(v)[1] <= b[3]]
    rng.shuffle(variants_a)
    rng.shuffle(variants_b)
    for va in variants_a:
        for vb in variants_b:
            try:
                pa, pb = _edge_positions(rng, va, vb, a, b)
            except AssertionError:
                continue
            return va, vb, pa, pb
    raise AssertionError("no fitting orientation realizes required color contact")


def _corner_position(cells, region, toward):
    """Reflect an occupied bbox corner toward a diagonally adjacent region."""
    r0, c0, h, w, ri, ci = region
    bottom, right = toward[4] > ri, toward[5] > ci
    # Reflection only preserves the construction-region fit.
    ph, pw = _dims(cells)
    wanted = (ph-1 if bottom else 0, pw-1 if right else 0)
    for fr in (False, True):
        for fc in (False, True):
            variant = sorted((ph-1-r if fr else r, pw-1-c if fc else c) for r, c in cells)
            if wanted in variant:
                return variant, (r0 + h - ph if bottom else r0,
                                 c0 + w - pw if right else c0)
    raise AssertionError("diagonal profile needs an occupied corner")


def _negative(texture):
    grid = full_grid(10, 10, 0)
    if texture == "no_components":
        return grid
    grid[1][1:4] = [4, 4, 4]
    if texture == "single_component":
        return grid
    grid[5][1:4] = [7, 7, 7]
    grid[8][5:10] = [8, 8, 8, 8, 8]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer; sample_index a nonnegative integer")
    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise TypeError(f"unknown override axes: {', '.join(unknown)}")
    limits = {"grid_h": (10, 20), "grid_w": (10, 20), "n_objs": (3, 6), "small_size": (1, 7)}
    for name, (lo, hi) in limits.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be a literal integer in {lo}..{hi}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError("texture supports only explicit negative fixtures; palette aliases were removed")
        if any(overrides.get(key) is not None for key in AXES):
            exc = ValueError("negative texture fixtures cannot be combined with ordinary axes")
            exc.incompatible_axes = tuple(overrides)
            raise exc
        return _negative(texture)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    # Preserve canonical scale in EVERY band, with broad support for the
    # complete declared domain. A scale draw never overrides an explicit axis.
    broad = ctx.draw_choice("scale", (False, False, False, True))
    h = ctx.draw_int("grid_h", 10, 20 if broad or overrides.get("grid_h") is not None else 12)
    w = ctx.draw_int("grid_w", 10, 20 if broad or overrides.get("grid_w") is not None else 12)
    n = ctx.draw_int("n_objs", 3, 6) if overrides.get("n_objs") is not None else ctx.draw_int("n_objs", 4, 6)
    if overrides.get("small_size") is not None:
        small = ctx.draw_int("small_size", 1, 7)
    elif profile == "contrast":
        small = ctx.draw_int("small_size", 5, 7)
    else:
        small = ctx.draw_int("small_size", 1, 4 if difficulty == "easy" else 7)
    rng = ctx.draw_rng("layout:" + str(difficulty))
    transpose = rng.choice((False, True))
    ih, iw = (w, h) if transpose else (h, w)
    slots = _regions(rng, ih, iw, n)
    a = rng.choice(slots)
    diagonal = [b for b in slots if abs(a[4]-b[4]) == 1 and abs(a[5]-b[5]) == 1]
    z = rng.choice(diagonal)
    neighbors = [b for b in slots if abs(a[4]-b[4]) + abs(a[5]-b[5]) == 1]
    b = rng.choice(neighbors)
    remaining = [s for s in slots if s not in (a, b, z)]
    rng.shuffle(remaining)
    selected = [a, b] + remaining[:n-3] + [z]
    colors = rng.sample(list(range(1, 10)), n)
    if profile != "general" or rng.random() < 0.6:
        colors[-1] = colors[0]
    sizes = [small] + [small + rng.randint(1, 3) for _ in range(n-1)]
    sizes[1] = small + 1
    shapes = []
    for index, (size, region) in enumerate(zip(sizes, selected)):
        rh, rw = region[2:4]
        if profile == "contrast" and small >= 5 and index == 0:
            cells = [(r, 0) for r in range(small-2)] + [(small-3, 1), (small-3, 2)]
            fitting = [s for s in _orientations(cells) if _dims(s)[0] <= rh and _dims(s)[1] <= rw]
            cells = rng.choice(fitting)
        elif profile == "contrast" and small >= 5 and index == 1:
            cells = [(i // 3, i % 3) for i in range(size)]
            fitting = [s for s in _orientations(cells) if _dims(s)[0] <= rh and _dims(s)[1] <= rw]
            cells = rng.choice(fitting)
        else:
            cells = _poly(rng, size, min(rh, 7), min(rw, 7),
                          corner=(profile == "diagonal" and index in (0, n-1)))
        shapes.append(cells)
    positions = [_random_position(rng, cells, region) for cells, region in zip(shapes, selected)]
    if profile == "contrast":
        shapes[0], shapes[1], positions[0], positions[1] = _edge_pair(rng, shapes[0], shapes[1], a, b)
    elif profile == "diagonal":
        shapes[0], positions[0] = _corner_position(shapes[0], a, z)
        shapes[-1], positions[-1] = _corner_position(shapes[-1], z, a)
    grid = full_grid(ih, iw, 0)
    for cells, position, color in zip(shapes, positions, colors):
        for r, c in _at(cells, position):
            grid[r][c] = color
    if transpose:
        grid = [list(row) for row in zip(*grid)]
    # Checking the realized result prevents future packing changes from silently
    # merging components or changing requested counts. No retry or label filter.
    observed = observe_overrides(grid)
    requested = {"grid_h": h, "grid_w": w, "n_objs": n, "small_size": small}
    if observed != requested:
        raise AssertionError(f"layout realized {observed}, expected {requested}")
    return grid


# Diagnostic mirrors and named alternatives. Racket remains the label source.
def rule_mirror(grid):
    obs = _components(grid)
    if not obs:
        raise ValueError("cannot crop an empty foreground")
    return _crop(grid, min(obs, key=_rank))


def _rival_bbox_area(grid):
    return _crop(grid, min(_components(grid), key=lambda obj: (_area(obj), obj["size"], obj["bbox"])))


def _rival_multicolor(grid):
    return _crop(grid, min(_components(grid, multicolor=True), key=_rank))


def _rival_eight_connected(grid):
    return _crop(grid, min(_components(grid, connectivity=8), key=_rank))


def _rival_rare_color(grid):
    counts = Counter(v for row in grid for v in row if v)
    return _crop(grid, min(_components(grid), key=lambda obj: (counts[obj["color"]], obj["bbox"])))


def _rival_solid_bbox(grid):
    obj = min(_components(grid), key=_rank)
    r1, c1, r2, c2 = obj["bbox"]
    return full_grid(r2-r1+1, c2-c1+1, obj["color"])


SEMANTIC_RIVALS = {
    "bbox_area": _rival_bbox_area,
    "multicolor_connectivity": _rival_multicolor,
    "eight_connectivity": _rival_eight_connected,
    "rare_color": _rival_rare_color,
    "solid_bbox": _rival_solid_bbox,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"bbox_area": _rival_bbox_area, "solid_bbox": _rival_solid_bbox}


def _area_witness(grid):
    return _rival_bbox_area(grid) != rule_mirror(grid)


def _color_contact_witness(grid):
    return _rival_multicolor(grid) != rule_mirror(grid)


def _diagonal_witness(grid):
    return _rival_eight_connected(grid) != rule_mirror(grid)


def _repeated_color_witness(grid):
    return _rival_rare_color(grid) != rule_mirror(grid)


def _hole_witness(grid):
    return _rival_solid_bbox(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "cell_count_not_bbox_area": _area_witness,
    "color_boundaries_are_object_boundaries": _color_contact_witness,
    "diagonal_contact_does_not_merge": _diagonal_witness,
    "component_count_not_color_frequency": _repeated_color_witness,
    "preserve_background_inside_crop": _hole_witness,
}
WITNESS_RIVALS = {
    "cell_count_not_bbox_area": ["bbox_area"],
    "color_boundaries_are_object_boundaries": ["multicolor_connectivity"],
    "diagonal_contact_does_not_merge": ["eight_connectivity"],
    "component_count_not_color_frequency": ["rare_color"],
    "preserve_background_inside_crop": ["solid_bbox"],
}


def lesson_identifiable(demos, query):
    """Finite-rival identifiability, not a proof against every possible rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
            continue
        reasons = self_check(pair["input"])
        errors.extend(f"demo {index}: {reason}" for reason in reasons)
        if not reasons and rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demo {index}: incorrect output")
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        reasons = self_check(query["input"])
        errors.extend(f"query: {reason}" for reason in reasons)
        if not reasons and "output" in query and rule_mirror(query["input"]) != query["output"]:
            errors.append("query: incorrect output")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives all demonstrations")
    return errors
