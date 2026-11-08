"""Inputs for a keyed transform followed by a keyed Boolean mask operation.

Racket is the label authority: 1=CW, 2=left/right reflection, 3=up/down
reflection; 4=union, 5=intersection, 6=XOR. Output is cropped color 8, or [[0]].
The authoring helpers below select informative inputs and implement explicit
rivals. They never replace reference execution in exported examples.
"""
from __future__ import annotations

from functools import lru_cache, partial

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "1e7a6ba0bb90"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "cb29ce937e33"
SUMMARY = (
    "Read transform (1=CW, 2=LR, 3=UD) and operation (4=union, 5=intersection, "
    "6=XOR) by color in row 0. Transform the left motif, align both local "
    "origins, combine masks, and crop a color-8 result; empty gives [[0]]."
)
INVARIANTS = [
    "rectangular integer colors 0..9; background 0; row 1 is blank",
    "row 0 contains only one transform key 1..3 and one operation key 4..6",
    "two monochrome four-connected body motifs of distinct colors 1..9",
    "motif bounding boxes have disjoint horizontal ranges with a blank column",
    "equal operands and empty Boolean outputs are lawful, not invalid textures",
]
AXES = {
    "grid_h": {"type": "int", "default": "8 on core profiles; otherwise 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "12 on core profiles; otherwise 10..16", "valid": "10..16"},
    "transform_key": {"type": "int", "default": "seed-shifted nine-profile schedule", "valid": "1..3"},
    "operation_key": {"type": "int", "default": "seed-shifted nine-profile schedule", "valid": "4..6"},
    "palette_kind": {"type": "str", "default": "canonical on core; otherwise reversed|varied", "valid": "canonical|reversed|varied"},
    "relation": {"type": "str", "default": "overlap on teaching profiles; all three on core", "valid": "overlap|equal|disjoint"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 9
LESSON_SCHEDULE_PERIOD = 9
MIN_STRICT_FRAC = 1.0
SOLID_OUTPUT_JUSTIFICATION = (
    "The selected Boolean-mask rule permits full rectangles and empty intersections "
    "or XORs. Empty results are exactly [[0]], and nonempty results use fixed color 8."
)

# A fixed four-column bit stride makes geometry cheap during the override matrix.
# Both pools are exhaustive connected normalized masks, not canonical examples.
_D4_NAMES = ("identity", "cw", "r180", "ccw", "lr", "ud", "transpose", "anti_transpose")
_T_INDEX = {1: 1, 2: 4, 3: 5}
_OFF_DIAGONAL = (1, 2, 3, 5, 6, 7)


@lru_cache(maxsize=65536)
def _normalize(mask):
    if not mask:
        return 0
    row_shift = ((mask & -mask).bit_length() - 1) // 4
    cols = (mask | (mask >> 4) | (mask >> 8) | (mask >> 12)) & 15
    col_shift = (cols & -cols).bit_length() - 1
    return mask >> (4 * row_shift + col_shift)


def _cells(mask):
    return [(i // 4, i % 4) for i in range(16) if mask & (1 << i)]


@lru_cache(maxsize=65536)
def _transforms(mask):
    result = [0] * 8
    for r, c in _cells(mask):
        for i, (rr, cc) in enumerate(((r, c), (c, 3-r), (3-r, 3-c), (3-c, r),
                                     (r, 3-c), (3-r, c), (c, r), (3-c, 3-r))):
            result[i] |= 1 << (4 * rr + cc)
    return tuple(_normalize(value) for value in result)


def _connected(mask):
    seen, frontier = 0, mask & -mask
    while frontier:
        seen |= frontier
        neighbors = ((frontier << 4) | (frontier >> 4)
                     | ((frontier & 0x7777) << 1) | ((frontier & 0xEEEE) >> 1))
        frontier = neighbors & mask & ~seen
    return seen == mask


@lru_cache(maxsize=2)
def _mask_pool(span):
    allowed = sum(1 << (4*r+c) for r in range(span) for c in range(span))
    return tuple(mask for mask in range(1, 65536)
                 if not mask & ~allowed and 3 <= mask.bit_count() <= 8
                 and mask & 15 and mask & 0x1111 and _connected(mask))


@lru_cache(maxsize=1)
def _disjoint_pairs():
    small = _mask_pool(3)
    return tuple((a, b) for a in small for b in small if not a & b)


def _combine(a, b, operation):
    return a | b if operation == 4 else a & b if operation == 5 else a ^ b


def _render(mask):
    mask = _normalize(mask)
    if not mask:
        return [[0]]
    cells = _cells(mask)
    return [[8 if mask & (1 << (4*r+c)) else 0
             for c in range(max(c for r, c in cells) + 1)]
            for r in range(max(r for r, c in cells) + 1)]


def _strong_pair(a, b, transform, operation):
    variants = _transforms(a)
    wanted_transform = _T_INDEX[transform]
    transformed = variants[wanted_transform]
    if not (transformed & b and transformed & ~b and b & ~transformed):
        return False
    answer = _normalize(_combine(transformed, b, operation))
    for ti, candidate in enumerate(variants):
        for oi in (4, 5, 6):
            if (ti, oi) != (wanted_transform, operation):
                if _normalize(_combine(candidate, b, oi)) == answer:
                    return False
    if _normalize(_combine(a, _transforms(b)[wanted_transform], operation)) == answer:
        return False
    if operation == 4 and all(v for row in _render(answer) for v in row):
        return False
    return True


def _draw_pair(rng, transform, operation, relation, strong, span):
    if relation == "disjoint":
        transformed, b = rng.choice(_disjoint_pairs())
        inverse = 3 if transform == 1 else _T_INDEX[transform]
        return _transforms(transformed)[inverse], b
    pool = _mask_pool(span)
    for _ in range(2048):
        a = rng.choice(pool)
        b = _transforms(a)[_T_INDEX[transform]] if relation == "equal" else rng.choice(pool)
        transformed = _transforms(a)[_T_INDEX[transform]]
        if relation == "overlap" and (transformed == b or not transformed & b):
            continue
        if not strong or _strong_pair(a, b, transform, operation):
            return a, b
    raise RuntimeError("bounded motif search exhausted; no silent fallback")


def _scheduled_choice(ctx, name, choices, scheduled=None):
    # Scheduled defaults and full-domain explicit overrides both retain actual
    # keyed provenance, following the existing shared-context contract.
    return ctx.draw_choice(name, choices if ctx.overrides.get(name) is not None or scheduled is None else (scheduled,))


def _profile(seed, sample_index):
    phase = stable_rng(seed, f"{TASK_ID}|lesson-phase", VERSION).randrange(9)
    return (sample_index + phase) % 9


@lru_cache(maxsize=32768)
def _offset_result(a, b, transform, operation, delta):
    """Rival output retaining a relative row offset, after its own final crop."""
    aa = {(r + max(0, -delta), c) for r, c in _cells(_transforms(a)[_T_INDEX[transform]])}
    bb = {(r + max(0, delta), c) for r, c in _cells(b)}
    cells = aa | bb if operation == 4 else aa & bb if operation == 5 else aa ^ bb
    if not cells:
        return ((0,),)
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(tuple(8 if (r, c) in cells else 0 for c in range(c0, max(c for r, c in cells)+1))
                 for r in range(r0, max(r for r, c in cells)+1))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "transform_key", "operation_key"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer, not bool or a coerced value")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = _profile(seed, sample_index)
    core = profile in (0, 4, 8)
    permutation = stable_rng(seed, f"{TASK_ID}|nuisance-order", VERSION).sample(range(6), 6)
    rank = permutation[_OFF_DIAGONAL.index(profile)] if not core else 0
    height = _scheduled_choice(ctx, "grid_h", tuple(range(8, 15)), 8 if core else None)
    width = _scheduled_choice(ctx, "grid_w", tuple(range(10, 17)), 12 if core else None)
    transform = _scheduled_choice(ctx, "transform_key", (1, 2, 3), profile // 3 + 1)
    operation = _scheduled_choice(ctx, "operation_key", (4, 5, 6), profile % 3 + 4)
    kind = _scheduled_choice(ctx, "palette_kind", ("canonical", "reversed", "varied"),
                             "canonical" if core else "reversed" if rank == 0 else "varied")
    relation = _scheduled_choice(ctx, "relation", ("overlap", "equal", "disjoint"),
                                 None if core else "overlap")
    strong = not core and relation == "overlap"
    span = 3 if core or difficulty == "easy" else 4
    motif_rng = ctx.draw_rng("motifs")
    for _ in range(128):
        a, b = _draw_pair(motif_rng, transform, operation, relation, strong, span)
        ah, aw = max(r for r, c in _cells(a)) + 1, max(c for r, c in _cells(a)) + 1
        bh, bw = max(r for r, c in _cells(b)) + 1, max(c for r, c in _cells(b)) + 1
        rows = [(ra, rb) for ra in range(2, height-ah+1) for rb in range(2, height-bh+1)
                if core or (ra > rb if rank in (0, 1, 3) else ra < rb)]
        if strong:
            answer = tuple(map(tuple, _render(_combine(_transforms(a)[_T_INDEX[transform]], b, operation))))
            informative = {delta for delta in {rb-ra for ra, rb in rows}
                           if _offset_result(a, b, transform, operation, delta) != answer}
            rows = [(ra, rb) for ra, rb in rows if rb-ra in informative]
        if rows:
            break
    else:
        raise RuntimeError("bounded search found no informative vertical placement")
    if kind == "canonical":
        ca, cb = 2, 3
    elif kind == "reversed":
        ca, cb = 3, 2
    else:
        ca, cb = ctx.draw_rng("colors").choice([(x, y) for x in range(1, 10) for y in range(x+1, 10) if (x, y) != (2, 3)])
        descending = rank in (0, 2, 4)
        if core or overrides.get("palette_kind") is not None:
            descending = ctx.draw_rng("color_order").choice((False, True))
        if descending:
            ca, cb = cb, ca
    rng = ctx.draw_rng("placement")
    horizontal = [(left, right) for left in range(width-aw+1)
                  for right in range(left+aw+1, width-bw+1)]
    left, right = rng.choice(horizontal)
    ra, rb = rng.choice(rows)
    key_positions = [(ct, co) for ct in range(width) for co in range(width) if ct != co
                     and (core or ((ct > co) == (rank in (1, 2, 5)) and (ct, co) != (1, 3)))]
    ct, co = rng.choice(key_positions)
    grid = full_grid(height, width, 0)
    grid[0][ct], grid[0][co] = transform, operation
    for mask, r0, c0, color in ((a, ra, left, ca), (b, rb, right, cb)):
        for r, c in _cells(mask):
            grid[r0+r][c0+c] = color
    return grid


def _parts(grid):
    tkey = next(v for v in grid[0] if v in (1, 2, 3))
    okey = next(v for v in grid[0] if v in (4, 5, 6))
    objs = sorted(components(grid[2:]), key=lambda o: (o["bbox"][1], o["bbox"][0], o["color"]))
    return tkey, okey, objs


def _object_mask(obj):
    return sum(1 << (4*r+c) for r, c in obj["norm"])


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    if len(grid) < 4 or width < 3:
        return ["grid too small for separated body motifs"]
    nonzero = [v for v in grid[0] if v]
    if len(nonzero) != 2 or sum(v in (1, 2, 3) for v in nonzero) != 1 or sum(v in (4, 5, 6) for v in nonzero) != 1:
        return ["header must contain only one transform key and one operation key"]
    if any(grid[1]):
        return ["row 1 must be a blank separator"]
    objs = components(grid[2:])
    if len(objs) != 2:
        return ["body must contain exactly two monochrome connected motifs"]
    if objs[0]["color"] == objs[1]["color"]:
        return ["motifs must have distinct colors"]
    objs.sort(key=lambda o: o["bbox"][1])
    if objs[0]["bbox"][3] + 1 >= objs[1]["bbox"][1]:
        return ["motif bounding boxes need disjoint column ranges and a blank column"]
    if any(o["bbox"][2]-o["bbox"][0] >= 4 or o["bbox"][3]-o["bbox"][1] >= 4 for o in objs):
        return ["declared motif bounding boxes are at most 4 by 4"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    transform, operation, objs = _parts(grid)
    colors = tuple(obj["color"] for obj in objs)
    a = _transforms(_object_mask(objs[0]))[_T_INDEX[transform]]
    b = _object_mask(objs[1])
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "transform_key": transform, "operation_key": operation,
        "palette_kind": "canonical" if colors == (2, 3) else "reversed" if colors == (3, 2) else "varied",
        "relation": "equal" if a == b else "disjoint" if not a & b else "overlap",
    }


def predict_for_authoring(grid, *, changed_key=None, changed_transform=None,
                           changed_operation_key=None, changed_operation=None,
                           source_order=None, second=False, header_order=False,
                           fixed_header=False, union_b=False, union_rectangle=False):
    """Pure authoring comparator/rival; reference labels still come from Racket."""
    transform, operation, objs = _parts(grid)
    if header_order:
        transform, operation = [v for v in grid[0] if v]
    if fixed_header:
        transform, operation = grid[0][1], grid[0][3]
    if source_order == "color":
        objs.sort(key=lambda o: (o["color"], o["bbox"][1], o["bbox"][0]))
    elif source_order == "reading":
        objs.sort(key=lambda o: (o["bbox"][0], o["bbox"][1], o["color"]))
    a, b = map(_object_mask, objs)
    ti = _D4_NAMES.index(changed_transform) if transform == changed_key else _T_INDEX.get(transform, 0)
    if second:
        b = _transforms(b)[ti]
    else:
        a = _transforms(a)[ti]
    if operation == changed_operation_key:
        operation = changed_operation
    if operation not in (4, 5, 6):
        return [[0]]
    if operation == 4 and union_b:
        return _render(b)
    out = _render(_combine(a, b, operation))
    if operation == 4 and union_rectangle:
        return [[8] * len(out[0]) for _ in out]
    return out


def _relative_vertical_offset(grid):
    transform, operation, objs = _parts(grid)
    a, b = map(_object_mask, objs)
    return [list(row) for row in _offset_result(a, b, transform, operation,
                                               objs[1]["bbox"][0] - objs[0]["bbox"][0])]


LESSON_COMPETITORS = {
    f"key_{key}_means_{name}": partial(predict_for_authoring, changed_key=key, changed_transform=name)
    for key in (1, 2, 3) for name in _D4_NAMES if name != _D4_NAMES[_T_INDEX[key]]
}
LESSON_COMPETITORS.update({
    f"operation_{key}_means_{alternative}": partial(predict_for_authoring, changed_operation_key=key, changed_operation=alternative)
    for key in (4, 5, 6) for alternative in (4, 5, 6) if key != alternative
})
LESSON_COMPETITORS.update({
    "min_color_source": partial(predict_for_authoring, source_order="color"),
    "reading_order_source": partial(predict_for_authoring, source_order="reading"),
    "header_position_order": partial(predict_for_authoring, header_order=True),
    "fixed_header_columns_1_3": partial(predict_for_authoring, fixed_header=True),
    "union_is_second_motif": partial(predict_for_authoring, union_b=True),
    "union_is_filled_rectangle": partial(predict_for_authoring, union_rectangle=True),
    "retain_relative_vertical_offset": _relative_vertical_offset,
    "transform_second": partial(predict_for_authoring, second=True),
})
CANONICAL_SHORTCUTS = {name: LESSON_COMPETITORS[name] for name in (
    "key_1_means_ccw", "min_color_source", "reading_order_source", "header_position_order",
    "fixed_header_columns_1_3", "union_is_second_motif", "union_is_filled_rectangle", "retain_relative_vertical_offset",
)}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)


def _refutes(grid, name):
    return predict_for_authoring(grid) != SEMANTIC_RIVALS[name](grid)


SEMANTIC_WITNESSES = {name: partial(_refutes, name=name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}
