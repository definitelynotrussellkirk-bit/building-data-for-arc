"""Input sampler for area-ranked frames and size-ranked loose shapes.

The unchanged Racket authority centers by signed floor division. A shape may
exceed its paired interior by one cell and overwrite the frame border. This
module's Python transform is a diagnostic/rival implementation, never a label
source. See notes.md for the bounded input domain and ordered lesson policy.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d7f13ee34d85"
TASK_ID = GENERATOR_ID
RULE_HASH = "435fa9a55dd3"
VERSION = "4.2.0"
SUMMARY = (
    "Pair 2-4 hollow frames by increasing interior area with equally many loose "
    "connected shapes by increasing cell count. Center using signed floor-half "
    "offsets, including border overlap. Shared or distinct frame colors, unequal "
    "rectangular interiors, and variable shape counts occur in ordinary lessons."
)
INVARIANTS = [
    "background 0; 2-4 frames and the same number of loose shapes",
    "distinct frame interior areas and distinct loose-shape cell counts",
    "all object bounding boxes have a one-cell gap and contain no other object",
    "shape colors are distinct from each other and all frame colors",
    "rank-paired shape bounds exceed interior bounds by at most one cell",
    "any three of four consecutive default pairs refute the three declared rivals",
]
AXES = {
    "grid_h": {"type": "int", "default": "core 13..15; broad 13..24", "valid": "13..24"},
    "grid_w": {"type": "int", "default": "core 18..20; broad 18..28", "valid": "18..28"},
    "n_frames": {"type": "int", "default": "core 3; broad 2..4", "valid": "2..4"},
    "frame_palette": {"type": "str", "default": "core shared; broad either", "valid": "shared|distinct"},
    "shape_relation": {"type": "str", "default": "core oversized; broad either", "valid": "fits|oversized"},
}
# Four-frame layouts use a deliberately stated 22-column minimum. Every other
# advertised joint setting is constructive. A single width/count override
# chooses a compatible unpinned count/width; it never changes the requested axis.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_frames": 4, "grid_w": width} for width in range(18, 22)
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical", "area_witness")
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_GEOMETRIES = ((2, 2), (2, 3), (3, 2), (2, 4), (4, 2), (3, 3),
               (2, 5), (5, 2), (3, 4), (4, 3), (4, 4), (6, 2),
               (7, 2), (2, 6), (2, 7), (3, 5), (5, 3))


def schedule_profile(seed, sample_index, difficulty=None):
    # Mix seed separately: (seed + index) % 2 collapses to one profile when a
    # sampler advances seed and index together. Consecutive indices still
    # alternate, independently of that caller convention and difficulty.
    phase = sha256(f"{TASK_ID}:{int(seed)}:lesson-phase".encode()).digest()[0] % 2
    return SCHEDULE_PROFILES[(phase + int(sample_index)) % LESSON_SCHEDULE_PERIOD]


def _int_axis(ctx, overrides, name, lo, hi, defaults):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _enum_axis(ctx, overrides, name, choices, defaults):
    return ctx.draw_choice(name, choices if overrides.get(name) is not None else defaults)


def _connected(cells):
    unseen = set(cells)
    if not unseen:
        return False
    stack = [unseen.pop()]
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARD:
            point = r + dr, c + dc
            if point in unseen:
                unseen.remove(point)
                stack.append(point)
    return not unseen


@lru_cache(maxsize=1)
def _shape_bank():
    """All normalized connected subsets of a 3x3 box with 1..7 cells.

    Enumerating the small finite bank avoids a retry cap that silently returns
    fewer cells. Colors and positions are not cached. Eight-cell hollow rings
    are outside this bank, so no loose shape can be mistaken for a frame.
    """
    points = tuple((r, c) for r in range(3) for c in range(3))
    bank = set()
    for size in range(1, 8):
        for cells in combinations(points, size):
            if _connected(cells):
                top, left = min(r for r, _ in cells), min(c for _, c in cells)
                bank.add(tuple(sorted((r-top, c-left) for r, c in cells)))
    return tuple(sorted(bank, key=lambda x: (len(x), x)))


def _bounds(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


@lru_cache(maxsize=256)
def _shape_choices(ih, iw, oversized):
    by_size = {}
    for shape in _shape_bank():
        h, w = _bounds(shape)
        if h <= ih+1 and w <= iw+1 and ((h > ih or w > iw) == oversized):
            by_size.setdefault(len(shape), []).append(shape)
    return {size: tuple(options) for size, options in by_size.items()}


@lru_cache(maxsize=128)
def _broad_geometry(k, width):
    legal = []
    for group in combinations(_GEOMETRIES, k):
        ranked = tuple(sorted(group, key=lambda x: x[0]*x[1]))
        areas = [h*w for h, w in ranked]
        if len(set(areas)) != k or min(ranked[0]) != 2:
            continue
        if sum(w+2 for _, w in ranked) + k-1 <= width:
            legal.append(ranked)
    return tuple(legal)


@lru_cache(maxsize=128)
def _area_geometry(k, width):
    # Require strict inversions, not reading-order tie breaks. The bank always
    # includes the 7x2 area14 versus 4x4 area16 counterexample and alternatives.
    return tuple(group for group in _broad_geometry(k, width)
                 if any(a[0] > b[0] for a, b in combinations(group, 2))
                 and any(sum(a) > sum(b) for a, b in combinations(group, 2)))


def _geometry(ctx, profile, k, width):
    rng = ctx.draw_rng("frame_geometry")
    if profile == "area_witness":
        # 7x2 has area14, height7, perimeter18; 4x4 has area16,
        # height4, perimeter16. Both height and perimeter reverse their ranks.
        return rng.choice(_area_geometry(k, width))
    if profile == "canonical":
        choices = {2: (((2, 2), (3, 3)), ((2, 2), (4, 3))),
                   3: (((2, 2), (3, 3), (4, 4)),
                       ((2, 2), (3, 3), (4, 3)),
                       ((2, 2), (3, 2), (4, 4))),
                   4: (((2, 2), (3, 2), (3, 3), (4, 4)),)}[k]
        return rng.choice(choices) if rng.randrange(3) else rng.choice(_broad_geometry(k, width))
    return rng.choice(_broad_geometry(k, width))


def _shapes(ctx, geometry, relation, profile):
    rng = ctx.draw_rng("shape_geometry")
    options = [_shape_choices(ih, iw, relation == "oversized" and i == 0)
               for i, (ih, iw) in enumerate(geometry)]
    vectors = [sizes for sizes in combinations(range(1, 8), len(geometry))
               if all(size in available for size, available in zip(sizes, options))]
    if profile == "canonical" and len(geometry) == 3:
        preferred = [v for v in ((3, 4, 5), (3, 4, 6)) if v in vectors]
        vectors += preferred * 6
    sizes = rng.choice(vectors)
    return [rng.choice(available[size]) for available, size in zip(options, sizes)]


def _band_positions(widths, canvas_width, rng):
    """Random order and distributable empty columns; no rejection or clipping."""
    order = list(range(len(widths)))
    rng.shuffle(order)
    slack = canvas_width - sum(widths) - (len(widths)-1)
    gaps = [0] * (len(widths)+1)
    for _ in range(slack):
        gaps[rng.randrange(len(gaps))] += 1
    cursor = gaps[0]
    lefts = [0] * len(widths)
    for place, index in enumerate(order):
        lefts[index] = cursor
        cursor += widths[index] + 1 + gaps[place+1]
    return lefts


def _draw_frame(grid, top, left, ih, iw, color):
    for r in range(top, top+ih+2):
        for c in range(left, left+iw+2):
            if r in (top, top+ih+1) or c in (left, left+iw+1):
                grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key in ("grid_h", "grid_w", "n_frames"):
        value = overrides.get(key)
        if value is not None and type(value) is not int:
            raise ValueError(f"{key} must be an integer, not {type(value).__name__}")
    if overrides.get("n_frames") == 4 and overrides.get("grid_w") in range(18, 22):
        raise ValueError("incompatible overrides: n_frames=4 requires grid_w>=22")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("lesson_profile", (schedule_profile(seed, sample_index, difficulty),))
    count_defaults = [3] if profile == "canonical" else (
        [2, 2, 3] if difficulty == "easy" else [3, 4, 4] if difficulty == "hard" else [2, 3, 4])
    if overrides.get("grid_w") is not None and overrides["grid_w"] < 22:
        count_defaults = [k for k in count_defaults if k <= 3]
    k = _int_axis(ctx, overrides, "n_frames", 2, 4, count_defaults)
    core_h, core_w = ctx.draw_rng("core_dimensions").choice(((14, 20), (13, 18), (15, 19)))
    min_width = 22 if k == 4 else 18
    h_defaults = [core_h] if profile == "canonical" else list(range(13, 25))
    w_defaults = [max(core_w, min_width)] if profile == "canonical" else list(range(min_width, 29))
    h = _int_axis(ctx, overrides, "grid_h", 13, 24, h_defaults)
    w = _int_axis(ctx, overrides, "grid_w", 18, 28, w_defaults)
    palette = _enum_axis(ctx, overrides, "frame_palette", ("shared", "distinct"),
                         ("shared",) if profile == "canonical" else ("shared", "distinct"))
    relation = _enum_axis(ctx, overrides, "shape_relation", ("fits", "oversized"),
                          ("oversized",) if profile == "canonical" else ("fits", "oversized"))
    geometry = _geometry(ctx, profile, k, w)
    shapes = _shapes(ctx, geometry, relation, profile)
    colors = ctx.draw_rng("colors").sample(list(range(1, 10)), k + (1 if palette == "shared" else k))
    fcolors = [colors[0]] * k if palette == "shared" else colors[:k]
    scolors = colors[1:] if palette == "shared" else colors[k:]
    rng = ctx.draw_rng("positions")
    frame_h = max(ih+2 for ih, _ in geometry)
    shape_h = max(_bounds(shape)[0] for shape in shapes)
    slack = h-frame_h-shape_h-1
    gap = 1+rng.randint(0, slack)
    first = rng.randint(0, slack-(gap-1))
    if rng.randrange(2):
        frame_top, shape_top = first, first+frame_h+gap
    else:
        shape_top, frame_top = first, first+shape_h+gap
    flefts = _band_positions([iw+2 for _, iw in geometry], w, rng)
    slefts = _band_positions([_bounds(s)[1] for s in shapes], w, rng)
    grid = full_grid(h, w, 0)
    for (ih, iw), color, left in zip(geometry, fcolors, flefts):
        top = frame_top+rng.randint(0, frame_h-ih-2)
        _draw_frame(grid, top, left, ih, iw, color)
    for shape, color, left in zip(shapes, scolors, slefts):
        top = shape_top+rng.randint(0, shape_h-_bounds(shape)[0])
        for r, c in shape:
            grid[top+r][left+c] = color
    return grid


def split_objects(grid):
    """Same-color cardinal components; coordinates preserve reading-order ties."""
    seen, frames, shapes = set(), [], []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            cells, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr+dr, cc+dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            top, left = min(rr for rr, _ in cells), min(cc for _, cc in cells)
            bottom, right = max(rr for rr, _ in cells), max(cc for _, cc in cells)
            height, width = bottom-top+1, right-left+1
            border = {(rr, cc) for rr in range(top, bottom+1) for cc in range(left, right+1)
                      if rr in (top, bottom) or cc in (left, right)}
            obj = {"top": top, "left": left, "h": height, "w": width,
                   "cells": cells, "color": color, "size": len(cells), "area": (height-2)*(width-2)}
            (frames if height >= 3 and width >= 3 and set(cells) == border else shapes).append(obj)
    return frames, shapes


def has_negative_centering(grid):
    frames, shapes = split_objects(grid)
    return any(s["h"] > f["h"]-2 or s["w"] > f["w"]-2
               for f, s in zip(sorted(frames, key=lambda o: o["area"]), sorted(shapes, key=lambda o: o["size"])))


def observe_axes(grid):
    frames, _ = split_objects(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(frames),
            "frame_palette": "shared" if len({f["color"] for f in frames}) == 1 else "distinct",
            "shape_relation": "oversized" if has_negative_centering(grid) else "fits"}


observe_overrides = observe_axes


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty rectangular list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    if not (13 <= len(grid) <= 24 and 18 <= width <= 28):
        return ["canvas outside supported 13..24 by 18..28 bounds"]
    frames, shapes = split_objects(grid)
    errors = []
    if not 2 <= len(frames) <= 4 or len(frames) != len(shapes):
        errors.append("expected 2-4 frames and exactly one loose shape per frame")
    if len({f["area"] for f in frames}) != len(frames):
        errors.append("frame interior areas must be distinct")
    if len({s["size"] for s in shapes}) != len(shapes):
        errors.append("shape cell counts must be distinct")
    if len({s["color"] for s in shapes}) != len(shapes):
        errors.append("shape colors must be distinct")
    if {s["color"] for s in shapes} & {f["color"] for f in frames}:
        errors.append("shape and frame palettes must be disjoint")
    for f, s in zip(sorted(frames, key=lambda o: o["area"]), sorted(shapes, key=lambda o: o["size"])):
        if s["h"] > f["h"]-1 or s["w"] > f["w"]-1:
            errors.append("rank-paired shape exceeds interior by more than one cell")
    for a, b in combinations(frames+shapes, 2):
        # Canonical train 1 has differently colored boxes touching at an edge.
        # Generation leaves a gap; validation requires only disjoint crops.
        if not (a["top"]+a["h"] <= b["top"] or b["top"]+b["h"] <= a["top"]
                or a["left"]+a["w"] <= b["left"] or b["left"]+b["w"] <= a["left"]):
            errors.append("object bounding boxes must be disjoint")
            break
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def diagnostic_transform(grid, rival="area"):
    """Task-domain diagnostic, cross-checked with Racket; not output authority."""
    frames, shapes = split_objects(grid)
    key = {"frame_height": lambda o: o["h"], "frame_perimeter": lambda o: o["h"]+o["w"]}.get(
        rival, lambda o: o["area"])
    frames = sorted(frames, key=key)
    shapes = sorted(shapes, key=lambda o: o["size"])
    result = full_grid(len(grid), len(grid[0]), 0)
    for frame in frames:
        for r, c in frame["cells"]:
            result[r][c] = frame["color"]
    for frame, shape in zip(frames, shapes):
        dr, dc = (frame["h"]-2-shape["h"])//2, (frame["w"]-2-shape["w"])//2
        if rival == "clamp_negative_offset":
            dr, dc = max(0, dr), max(0, dc)
        top, left = frame["top"]+1+dr, frame["left"]+1+dc
        # The rule copies every nonzero input pixel in the cropped bounding box.
        for r in range(shape["h"]):
            for c in range(shape["w"]):
                value = grid[shape["top"]+r][shape["left"]+c]
                if value and 0 <= top+r < len(grid) and 0 <= left+c < len(grid[0]):
                    result[top+r][left+c] = value
    return result


def _height_rival(grid):
    return diagnostic_transform(grid, "frame_height")


def _perimeter_rival(grid):
    return diagnostic_transform(grid, "frame_perimeter")


def _clamp_rival(grid):
    return diagnostic_transform(grid, "clamp_negative_offset")


def _rank_reversal(grid, key):
    frames, _ = split_objects(grid)
    identity = lambda ordered: [(o["top"], o["left"]) for o in ordered]
    return identity(sorted(frames, key=lambda o: o["area"])) != identity(sorted(frames, key=key))


def _height_witness(grid):
    return _rank_reversal(grid, lambda o: o["h"])


def _perimeter_witness(grid):
    return _rank_reversal(grid, lambda o: o["h"]+o["w"])


SEMANTIC_WITNESSES = {"negative_centering": has_negative_centering,
                      "height_rank_reversal": _height_witness,
                      "perimeter_rank_reversal": _perimeter_witness}
SEMANTIC_RIVALS = {"frame_height": _height_rival, "frame_perimeter": _perimeter_rival,
                   "clamp_negative_offset": _clamp_rival}
WITNESS_RIVALS = {"negative_centering": ["clamp_negative_offset"],
                 "height_rank_reversal": ["frame_height"],
                 "perimeter_rank_reversal": ["frame_perimeter"]}
CANONICAL_SHORTCUTS = {"frame_height": _height_rival, "frame_perimeter": _perimeter_rival}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Each named rival must be refuted in the demonstrations.

    Four consecutive default pairs contain two of each profile. Holding out
    any one leaves a canonical negative-offset witness and an area-rank witness.
    Overrides or nonconsecutive assembly can violate this sufficient condition.
    This is a finite-rival teaching check, not a proof against arbitrary rules.
    """
    if len(demos) < EXAMPLES_NEEDED:
        return [f"requires at least {EXAMPLES_NEEDED} demonstrations"]
    return [f"demonstrations do not refute {name}" for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
