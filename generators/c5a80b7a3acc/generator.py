"""Input sampler for Header Chooses the Set Operation (c5a80b7a3acc).

The unchanged Racket authority normalizes the single 2/3 components separately,
uses intersection if ANY 7 exists (else XOR), and tightly crops in color 8.
This module generates inputs only; local set calculations support construction
and explicitly named rivals, never replace the Racket label authority.

All 151 normalized connected shapes inside a 3x3 envelope are available.
Five demonstrations cover the AND witness / XOR witness / broad schedule:
each six-pair episode has two of each role, allowing cyclic query rotation.
Explicit semantic controls use the broad construction; a forced single-mode
lesson does not promise to teach both operations.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5a80b7a3acc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "db99a498afde"
SUMMARY = (
    "Independently placed connected red/green shapes: any 7 selects their "
    "normalized intersection; otherwise XOR. Color 9 is irrelevant. Exact "
    "overlap, unequal areas, empty answers and tight cropping are supported."
)
INVARIANTS = [
    "background 0, exactly one 4-connected component of color 2 and of color 3",
    "7 selects AND anywhere; absent 7 selects XOR, regardless of color 9",
    "source areas and placement vary; normalized overlap may be empty",
    "generated shapes fit 3x3 envelopes; output labels come from canonical Racket",
    "markers are painted only on unoccupied cells",
]
DEGENERATE_TEXTURES = ("identical", "disjoint", "no_marker")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
HELPFUL_TEXTURES = ("and_mode", "xor_mode")
_TEXTURES = ("mixed", *HELPFUL_TEXTURES, *DEGENERATE_TEXTURES)
AXES = {
    "grid_h": {"type": "int", "default": "8..16, canonical 8/9 favored", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "8..16, canonical 14/15 favored", "valid": "8..16"},
    "core_size": {"type": "int", "default": "0..6 normalized intersection cells", "valid": "0..6"},
    "marker": {"type": "int", "default": "scheduled or 0..1; presence of 7", "valid": "0|1"},
    "texture": {"type": "str", "default": "mixed; explicit sampling policy",
                "valid": "mixed|and_mode|xor_mode|identical|disjoint|no_marker"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "and_mode", "marker": 0},
    {"texture": ["xor_mode", "no_marker"], "marker": 1},
    {"texture": "disjoint", "core_size": [1, 2, 3, 4, 5, 6]},
    {"texture": "identical", "core_size": 0},
]
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("and_witness", "xor_witness", "broad")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(seed + sample_index) % 3]


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return frozenset((r-top, c-left) for r, c in cells)


@lru_cache(maxsize=512)
def _mask_cells(mask):
    return tuple((i // 3, i % 3) for i in range(9) if mask & (1 << i))


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    pending = [remaining.pop()]
    while pending:
        r, c = pending.pop()
        for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                pending.append(neighbor)
    return not remaining


@lru_cache(maxsize=1)
def _shape_masks():
    return tuple(mask for mask in range(1, 512)
                 if min(r for r, c in _mask_cells(mask)) == 0
                 and min(c for r, c in _mask_cells(mask)) == 0
                 and _connected(_mask_cells(mask)))


def _crop(cells, *, keep_origin=False):
    if not cells:
        return [[0]]
    top = 0 if keep_origin else min(r for r, _ in cells)
    left = 0 if keep_origin else min(c for _, c in cells)
    return [[8 if (r, c) in cells else 0
             for c in range(left, max(c for _, c in cells)+1)]
            for r in range(top, max(r for r, _ in cells)+1)]


@lru_cache(maxsize=512)
def _mask_crop(mask):
    return tuple(tuple(row) for row in _crop(set(_mask_cells(mask))))


@lru_cache(maxsize=128)
def _pair_pool(overlap, relation, role, band):
    pairs, favored = [], []
    for a in _shape_masks():
        for b in _shape_masks():
            common, difference = a & b, a ^ b
            if common.bit_count() != overlap:
                continue
            if relation == "identical" and a != b:
                continue
            if role == "and_witness":
                cells = _mask_cells(common)
                if (not cells or a.bit_count() <= b.bit_count()
                        or not (min(r for r, c in cells) > 0
                                or min(c for r, c in cells) > 0)
                        or _mask_crop(common) == _mask_crop(difference)
                        or _mask_crop(common) == _mask_crop(b & ~a)):
                    continue
            if role == "xor_witness":
                if (not common or a.bit_count() >= b.bit_count()
                        or difference.bit_count() % 2 != 1
                        or _mask_crop(common) == _mask_crop(difference)):
                    continue
            pairs.append((a, b))
            total = a.bit_count() + b.bit_count()
            lo, hi = {"easy": (3, 9), "medium": (7, 12), "hard": (10, 18)}[band]
            if lo <= total <= hi:
                favored.append((a, b))
    # Weight complexity without removing any legal shape pair in this role.
    return tuple(pairs + favored * 3)


def _conflict(axes, message):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_controls(difficulty, overrides):
    if difficulty is not None and (not isinstance(difficulty, str)
                                   or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if name == "texture":
            if not isinstance(value, str) or value not in _TEXTURES:
                raise ValueError("texture must name a declared sampling policy")
        elif type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        else:
            lo, hi = {"grid_h": (8, 16), "grid_w": (8, 16),
                      "core_size": (0, 6), "marker": (0, 1)}[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be in [{lo}, {hi}]")
    texture = overrides.get("texture", "mixed")
    if texture == "and_mode" and overrides.get("marker") == 0:
        _conflict(("texture", "marker"), "texture and_mode conflicts with marker=0")
    if texture in ("xor_mode", "no_marker") and overrides.get("marker") == 1:
        _conflict(("texture", "marker"), f"texture {texture} conflicts with marker=1")
    if texture == "disjoint" and overrides.get("core_size", 0) != 0:
        _conflict(("texture", "core_size"), "texture disjoint requires core_size=0")
    if texture == "identical" and overrides.get("core_size") == 0:
        _conflict(("texture", "core_size"), "texture identical requires positive core_size")


def _dimensions(ctx):
    profile = ctx.draw_choice("size_profile", ("canonical", "canonical", "canonical", "broad"))
    anchor = ctx.draw_choice("canonical_dimensions", ((8, 14), (9, 15)))
    values = list(range(8, 17))
    h = ctx.draw_choice("grid_h", values + ([anchor[0]] * 100 if profile == "canonical" else []))
    w = ctx.draw_choice("grid_w", values + ([anchor[1]] * 100 if profile == "canonical" else []))
    return h, w


def _positions(rng, h, w, a, b, *, separated_rows):
    ah, aw = max(r for r, c in a)+1, max(c for r, c in a)+1
    bh, bw = max(r for r, c in b)+1, max(c for r, c in b)+1
    apos = [(r, c) for r in range(h-ah+1) for c in range(w-aw+1)]
    bpos = [(r, c) for r in range(h-bh+1) for c in range(w-bw+1)]
    rng.shuffle(apos)
    rng.shuffle(bpos)
    for ar, ac in apos:
        occupied = {(ar+r, ac+c) for r, c in a}
        for br, bc in bpos:
            if separated_rows and not (ar+ah < br or br+bh < ar):
                continue
            if occupied.isdisjoint((br+r, bc+c) for r, c in b):
                return (ar, ac), (br, bc)
    raise RuntimeError("no legal placement for the requested dimensions and shapes")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(difficulty, overrides)
    band = difficulty or "medium"
    texture = overrides.get("texture", "mixed")
    # A texture is a sampling policy, not a uniquely recoverable pixel label.
    # Record its default and explicit value through the public context API.
    effective = dict(overrides)
    effective.setdefault("texture", texture)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=effective)
    ctx.draw_choice("texture", _TEXTURES)
    controlled = bool(set(overrides) & {"texture", "marker", "core_size"})
    role = "broad" if controlled else schedule_profile(seed, sample_index, difficulty)
    marker_options = (1,) if role == "and_witness" or texture == "and_mode" else (
        (0,) if role == "xor_witness" or texture in ("xor_mode", "no_marker") else (0, 1))
    marker = ctx.draw_choice("marker", marker_options)
    if texture == "disjoint":
        overlap_options = [0]
    elif role != "broad" or texture == "identical":
        overlap_options = list(range(1, 7))
    else:
        overlap_options = list(range(7))
    preferred = {"easy": (1, 2, 3), "medium": (2, 3, 4), "hard": (4, 5, 6)}[band]
    overlap_options += [k for k in preferred if k in overlap_options] * 3
    overlap = ctx.draw_choice("core_size", overlap_options)
    h, w = _dimensions(ctx)
    relation = "identical" if texture == "identical" else "any"
    pool = _pair_pool(overlap, relation, role, band)
    if not pool:
        raise RuntimeError(f"empty constructive pool for overlap={overlap}, role={role}")
    masks = ctx.draw_rng("shape_pair").choice(pool)
    a, b = (_mask_cells(mask) for mask in masks)
    apos, bpos = _positions(ctx.draw_rng("shape_positions"), h, w, a, b,
                           separated_rows=role != "broad")
    grid = full_grid(h, w, 0)
    for cells, (top, left), color in ((a, apos, 2), (b, bpos, 3)):
        for r, c in cells:
            grid[top+r][left+c] = color
    free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    marker_rng = ctx.draw_rng("marker_positions")
    if marker:
        locations = [p for p in free if p[0] > 0] if role == "and_witness" else free
        point = marker_rng.choice(locations)
        grid[point[0]][point[1]] = 7
        free.remove(point)
    if texture != "no_marker":
        # AND witnesses show 7 taking priority over irrelevant 9. Broad draws
        # retain ordinary single-marker palettes plus some absent/mixed markers.
        draw = ctx.draw_choice("nine_presence", (1, 1, 1, 1, 0))
        nine = role != "broad" or draw == (1 if not marker else 0)
        if nine:
            r, c = marker_rng.choice(free)
            grid[r][c] = 9
    return grid


def _components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending, cells = [start], {start}
        while pending:
            r, c = pending.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in remaining:
                    remaining.remove(point)
                    pending.append(point)
                    cells.add(point)
        result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(type(value) is not int or value not in (0, 2, 3, 7, 9)
           for row in grid for value in row):
        return ["cells must be integer colors 0, 2, 3, 7 or 9"]
    return [f"expected exactly one connected color-{color} object"
            for color in (2, 3) if len(_components(grid, color)) != 1]


def strict_canonical_like(grid):
    """Task-domain validity; exact canonical dimension/palette support is separate."""
    return self_check(grid)


def _sources(grid):
    return tuple(_normalize(_components(grid, color)[0]) for color in (2, 3))


def observe_overrides(grid):
    a, b = _sources(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "core_size": len(a & b),
            "marker": int(any(7 in row for row in grid))}


def _operation_cells(grid):
    a, b = _sources(grid)
    return a & b if any(7 in row for row in grid) else a ^ b


def _intended_for_probe(grid):
    """Independent of Racket; used only in diagnostic witness/lesson hooks."""
    return _crop(_operation_cells(grid))


def _area_selector(grid):
    a, b = _sources(grid)
    return _crop(a & b if len(a) <= len(b) else a ^ b)


def _top_left_header(grid):
    a, b = _sources(grid)
    return _crop(a & b if grid[0][0] == 7 else a ^ b)


def _top_row_header(grid):
    a, b = _sources(grid)
    return _crop(a & b if 7 in grid[0] else a ^ b)


def _nine_selector(grid):
    a, b = _sources(grid)
    return _crop(a ^ b if any(9 in row for row in grid) else a & b)


def _row_alignment(grid):
    # WRONG: normalize columns separately but keep the absolute row origins.
    shapes = [_components(grid, color)[0] for color in (2, 3)]
    a, b = ({(r, c-min(col for row, col in cells)) for r, c in cells}
            for cells in shapes)
    return _crop(a & b if any(7 in row for row in grid) else a ^ b)


def _no_final_crop(grid):
    return _crop(_operation_cells(grid), keep_origin=True)


def _always_and(grid):
    a, b = _sources(grid)
    return _crop(a & b)


def _always_xor(grid):
    a, b = _sources(grid)
    return _crop(a ^ b)


def _union(grid):
    a, b = _sources(grid)
    return _crop(a | b)


def _red_only(grid):
    return _crop(_sources(grid)[0])


def _green_only(grid):
    return _crop(_sources(grid)[1])


def _red_minus_green(grid):
    a, b = _sources(grid)
    return _crop(a - b)


def _green_minus_red(grid):
    a, b = _sources(grid)
    return _crop(b - a)


CANONICAL_SHORTCUTS = {
    "area_selector": _area_selector, "top_left_header": _top_left_header,
    "top_row_header": _top_row_header, "nine_selector": _nine_selector,
    "row_alignment": _row_alignment, "no_final_crop": _no_final_crop,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS, "always_and": _always_and, "always_xor": _always_xor,
    "union": _union, "red_only": _red_only, "green_only": _green_only,
    "red_minus_green": _red_minus_green, "green_minus_red": _green_minus_red,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness(name):
    def predicate(grid):
        return _intended_for_probe(grid) != SEMANTIC_RIVALS[name](grid)
    return predicate


SEMANTIC_WITNESSES = {name: _witness(name) for name in CANONICAL_SHORTCUTS}
WITNESS_RIVALS = {name: [name] for name in CANONICAL_SHORTCUTS}


def lesson_identifiable(demos, query):
    """Finite named-rival check; this is not a universal uniqueness proof."""
    return [f"declared rival survives all demonstrations: {name}"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
