"""Keyed local rotation/recentering with complete key and rectangle support.

Validity is distinct from informativeness: canonical symmetric objects and
zero-turn keys are valid. Ordinary draws use four-orientation objects, and
key 2 is translated away from the target center so every normal frame changes.
Labels remain exclusively the responsibility of the unchanged Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "f2dbde875127"
VERSION = "3.2.0"
TASK_ID = "f2dbde875127"
RULE_HASH = "f0178b249d84"
SUMMARY = (
    "Rotate each single-color object inside a blue rectangular frame by "
    "(key-2)*90 degrees clockwise, then center its bounding box. All keys "
    "2..5, rectangular and square interiors, and 1..3 separated frames occur."
)
INVARIANTS = [
    "color-1 components are separated hollow rectangular frames",
    "each frame has exactly one key 2..5 in the row directly above",
    "each frame contains one connected single-color object",
    "both the original and keyed-rotated object fit the frame interior",
]
DEGENERATE_TEXTURES = ("no_key", "no_frame", "no_object")
# Negative fixtures are diagnostic, never ordinary texture-domain members.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty dependent", "valid": "9..24"},
    "grid_w": {"type": "int", "default": "difficulty dependent", "valid": "10..26"},
    "n_frames": {"type": "int", "default": "difficulty dependent", "valid": "1..3"},
    "interior_h": {"type": "int", "default": "maximum height; other frames vary", "valid": "3..7"},
    "interior_w": {"type": "int", "default": "maximum width; other frames vary", "valid": "3..7"},
    "key": {"type": "int", "default": "first frame by bbox; other keys vary", "valid": "2|3|4|5"},
}
_LIMITS = {"grid_h": (9, 24), "grid_w": (10, 26), "n_frames": (1, 3),
           "interior_h": (3, 7), "interior_w": (3, 7), "key": (2, 5)}


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size, smax):
    for _ in range(30):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(_CARD)
            cells.add((r + dr, c + dc))
        nl = _norm(cells)
        h = max(r for r, c in nl) + 1; w = max(c for r, c in nl) + 1
        if h <= smax and w <= smax:
            return nl
    return [(0, 0)]


def _rotate_norm(cells, turns):
    pts = _norm(cells)
    for _ in range(turns % 4):
        hh = max(r for r, _ in pts) + 1
        pts = _norm([(c, hh - 1 - r) for r, c in pts])
    return sorted(pts)


def _visibly_rotates(cells, key):
    return sorted(_norm(cells)) != _rotate_norm(cells, key - 2)


def _reserve(occ, top, left, bh, bw, h, w, margin=1):
    for r in range(top - margin, top + bh + margin):
        for c in range(left - margin, left + bw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + bh):
        for c in range(left, left + bw):
            occ[r][c] = True
    return True


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)}")
    for name, value in overrides.items():
        if name == "texture":
            if value not in DEGENERATE_TEXTURES:
                raise ValueError(f"texture is diagnostic only; expected {DEGENERATE_TEXTURES}")
        elif type(value) is not int or not _LIMITS[name][0] <= value <= _LIMITS[name][1]:
            raise ValueError(f"{name} must be an integer in {_LIMITS[name]}; got {value!r}")
    if "texture" in overrides and len(overrides) != 1:
        exc = ValueError("diagnostic texture cannot be combined with geometric overrides")
        exc.incompatible_axes = tuple(overrides)
        raise exc


def _full_rotation_orbit(cells):
    return len({tuple(_rotate_norm(cells, t)) for t in range(4)}) == 4


def _incompatible(overrides, reason):
    exc = ValueError(reason)
    exc.incompatible_axes = tuple(name for name in overrides if name != "key")
    return exc


def _slot_lengths(total, count):
    """Split a dimension into cells with a one-cell separator between them."""
    usable = total - count + 1
    size, extra = divmod(usable, count)
    lengths = [size + (i < extra) for i in range(count)]
    starts = []
    cursor = 0
    for length in lengths:
        starts.append((cursor, length))
        cursor += length + 1
    return starts


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if "texture" in overrides:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        hr, wr, nr, sr = (9, 12), (10, 13), (1, 1), (3, 4)
    elif difficulty == "hard":
        hr, wr, nr, sr = (16, 24), (17, 26), (2, 3), (4, 7)
    else:
        hr, wr, nr, sr = (12, 18), (13, 22), (1, 2), (3, 6)
    # One third of unpinned draws retain canonical scale/palette support in
    # every band. The objects, poses and placement are still newly sampled.
    anchor = not overrides and ctx.draw_choice("layout_regime", ("canonical_scale", "broad", "broad")) == "canonical_scale"
    if anchor:
        ah, aw = ctx.draw_choice("canonical_scale", ((13, 19), (14, 18), (15, 20), (16, 21)))
        hr, wr, nr, sr = (ah, ah), (aw, aw), (2, 2), (3, 7)
    target = ctx.draw_int("n_frames", *((1, 3) if "n_frames" in overrides else nr))
    if overrides.get("n_frames", nr[0]) > nr[1]:
        hr, wr = (16, 24), (17, 26)

    # Construct feasible slots BEFORE drawing exact dimensions; no requested
    # count or sampled exact axis is ever shrunk after a placement failure.
    max_h, max_w = overrides.get("grid_h", hr[1]), overrides.get("grid_w", wr[1])
    min_ih = overrides.get("interior_h", sr[0])
    min_iw = overrides.get("interior_w", sr[0])
    layouts = sorted({(1, target), (target, 1)} | ({(2, 2)} if target == 3 else set()))
    feasible = [(rows, cols) for rows, cols in layouts
                if rows*(min_ih+3)+rows-1 <= max_h
                and cols*(min_iw+2)+cols-1 <= max_w]
    if not feasible:
        raise _incompatible(overrides, "no separated-slot layout fits the requested geometry")
    rows, cols = ctx.draw_choice("packing_layout", feasible)
    cap_h = (max_h-rows+1)//rows-3
    cap_w = (max_w-cols+1)//cols-2
    hi_bounds = (overrides["interior_h"],)*2 if "interior_h" in overrides else (sr[0], min(sr[1], cap_h))
    wi_bounds = (overrides["interior_w"],)*2 if "interior_w" in overrides else (sr[0], min(sr[1], cap_w))
    max_ih = ctx.draw_int("interior_h", *hi_bounds)
    max_iw = ctx.draw_int("interior_w", *wi_bounds)
    needed_h, needed_w = rows*(max_ih+3)+rows-1, cols*(max_iw+2)+cols-1
    hb = (overrides["grid_h"],)*2 if "grid_h" in overrides else (max(hr[0], needed_h), hr[1])
    wb = (overrides["grid_w"],)*2 if "grid_w" in overrides else (max(wr[0], needed_w), wr[1])
    h, w = ctx.draw_int("grid_h", *hb), ctx.draw_int("grid_w", *wb)
    slots = [(r, c, sh, sw) for r, sh in _slot_lengths(h, rows)
             for c, sw in _slot_lengths(w, cols)]
    rng.shuffle(slots)
    planned = []
    for index, (slot_r, slot_c, sh, sw) in enumerate(slots[:target]):
        # At least one frame realizes BOTH sampled maximum dimensions. An
        # explicit dimension pin applies to every frame, not merely its max.
        ih = max_ih if index == 0 or "interior_h" in overrides else rng.randint(sr[0], max_ih)
        iw = max_iw if index == 0 or "interior_w" in overrides else rng.randint(sr[0], max_iw)
        top = slot_r + 1 + rng.randint(0, sh-ih-3)
        left = slot_c + rng.randint(0, sw-iw-2)
        planned.append((top, left, ih, iw))
    planned.sort()  # the key axis names the first frame in this spatial order
    key_rng = ctx.draw_rng("keys")
    first_key = ctx.draw_choice("key", (2, 3, 4, 5))
    if "key" in overrides:
        keys = [first_key] * target
    elif anchor:
        keys = [first_key, key_rng.choice([k for k in (2, 3, 4, 5) if k != first_key])]
    else:
        keys = [first_key] + [key_rng.choice((2, 3, 4, 5)) for _ in range(target-1)]
    object_colors = key_rng.sample([c for c in range(2, 10) if c not in keys], 2) if anchor else None
    shape_rng = ctx.draw_rng("objects")
    g = full_grid(h, w, 0)
    for index, (top, left, ih, iw) in enumerate(planned):
        draw_frame(g, top, left, top+ih+1, left+iw+1, 1)
        key = keys[index]
        # All four key interventions fit, including on non-square frames.
        size_limit = min(ih, iw)
        for _shape_try in range(40):
            obj = _poly(shape_rng, shape_rng.randint(3, max(3, size_limit*size_limit//2)), size_limit)
            oh = max(r for r, c in obj)+1
            ow = max(c for r, c in obj)+1
            if _full_rotation_orbit(obj) and (key != 2 or oh < ih or ow < iw):
                break
        else:
            obj, oh, ow = [(0, 0), (1, 0), (1, 1)], 2, 2
        offsets = [(r, c) for r in range(ih-oh+1) for c in range(iw-ow+1)
                   if key != 2 or (r, c) != ((ih-oh)//2, (iw-ow)//2)]
        dr, dc = shape_rng.choice(offsets)
        color = object_colors[index] if anchor else shape_rng.choice((2, 3, 4, 5, 6, 7, 8, 9))
        for r, c in obj:
            g[top+1+dr+r][left+1+dc+c] = color
        g[top-1][rng.randint(left, left+iw+1)] = key
    return g


def observe_overrides(grid):
    """Exact default projections: max interior dimensions and first-frame key.

    Explicit interior/key pins are broadcast to every frame. Additional-frame
    variation is not misrepresented as a single common default value.
    """
    boxes = sorted((min(r for r, c in cells), min(c for r, c in cells),
                    max(r for r, c in cells), max(c for r, c in cells))
                   for cells in _color1_components(grid))
    r0, c0, r1, c1 = boxes[0]
    key = next(grid[r0-1][c] for c in range(c0, c1+1) if grid[r0-1][c] in (2, 3, 4, 5))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(boxes),
            "interior_h": max(r1-r0-1 for r0, c0, r1, c1 in boxes),
            "interior_w": max(c1-c0-1 for r0, c0, r1, c1 in boxes), "key": key}


def _color1_components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check semantic domain, not the stronger normal-draw teaching policy."""
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(v) is not int or v < 0 or v > 9 for row in grid for v in row):
        return ["grid cells must be integer ARC colors 0..9"]
    errs = []
    comps = _color1_components(grid)
    if not 1 <= len(comps) <= 3:
        errs.append(f"expected 1..3 color-1 frames, found {len(comps)}")
    allowed = set()
    for cells in comps:
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        box = (r0, c0, r1, c1)
        if r1-r0 < 2 or c1-c0 < 2:
            errs.append(f"frame bbox {box} needs a nonempty rectangular interior")
            continue
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if set(cells) != border:
            errs.append(f"color-1 component at {box} is not a hollow rectangular frame")
            continue
        if r0 == 0:
            errs.append("frame has no row above for the key")
            continue
        allowed.update(border)
        allowed.update((r, c) for r in range(r0+1, r1) for c in range(c0+1, c1))
        allowed.update((r0-1, c) for c in range(c0, c1+1) if grid[r0-1][c] in (2, 3, 4, 5))
        keys = [grid[r0-1][c] for c in range(c0, c1+1) if grid[r0-1][c] in (2, 3, 4, 5)]
        if len(keys) != 1:
            errs.append(f"frame {box} expected exactly one key 2..5 above it, found {len(keys)}")
        interior = {(r, c): grid[r][c] for r in range(r0+1, r1) for c in range(c0+1, c1) if grid[r][c] != 0}
        if not interior:
            errs.append(f"frame {box} has empty interior object")
            continue
        colors = set(interior.values())
        if len(colors) != 1:
            errs.append(f"frame {box} interior should be one object color, found {sorted(colors)}")
        pending = set(interior)
        todo = [next(iter(pending))]
        while todo:
            point = todo.pop()
            if point in pending:
                pending.remove(point)
                r, c = point
                todo.extend((r+dr, c+dc) for dr, dc in _CARD)
        if pending:
            errs.append(f"frame {box} interior object must be 4-connected")
        oh = max(r for r, c in interior) - min(r for r, c in interior) + 1
        ow = max(c for r, c in interior) - min(c for r, c in interior) + 1
        if len(keys) == 1 and keys[0] in (3, 5):
            oh, ow = ow, oh
        if oh > r1-r0-1 or ow > c1-c0-1:
            errs.append(f"frame {box} keyed rotation would not fit its interior")
    if any(v != 0 and (r, c) not in allowed for r, row in enumerate(grid) for c, v in enumerate(row)):
        errs.append("nonzero cells outside the recognized frames and keys")
    return sorted(set(errs))


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 9, 0)
    shape = [(0, 0), (1, 0), (1, 1), (2, 1)]
    if name == "no_key":
        draw_frame(g, 1, 1, 7, 7, 1)
        for (r, c) in shape:
            g[2 + r][2 + c] = 7
        return g
    if name == "no_frame":
        g[0][3] = 3
        for (r, c) in shape:
            g[2 + r][2 + c] = 7
        return g
    if name == "no_object":
        draw_frame(g, 1, 1, 7, 7, 1)
        g[0][3] = 3
        return g
    return g


def strict_canonical_like(grid):
    return self_check(grid)


def _has_key(grid, key):
    for cells in _color1_components(grid):
        r0 = min(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        if r0 > 0 and key in grid[r0-1][c0:c1+1]:
            return True
    return False


SEMANTIC_WITNESSES = {
    "key_2_recenter": lambda grid: _has_key(grid, 2),
    "key_3_clockwise": lambda grid: _has_key(grid, 3),
    "key_4_half_turn": lambda grid: _has_key(grid, 4),
    "key_5_counterclockwise": lambda grid: _has_key(grid, 5),
}
# These witnesses establish branch presence and refute doing nothing. They do
# NOT claim lesson identifiability; workspace/key_contrast_probe.py exercises
# the stronger key-only interventions using actual Racket labels.
SEMANTIC_RIVALS = {"identity": lambda grid: [list(row) for row in grid]}
WITNESS_RIVALS = {name: ["identity"] for name in SEMANTIC_WITNESSES}
