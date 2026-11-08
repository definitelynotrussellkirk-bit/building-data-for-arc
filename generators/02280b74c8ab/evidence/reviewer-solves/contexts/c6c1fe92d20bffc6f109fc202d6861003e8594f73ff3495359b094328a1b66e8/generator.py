"""Inputs for the two-template rotation mosaic; labels stay with Racket.

Largest color-6 and color-7 components supply equal square templates. Other
1..8 cells delimit the index rectangle: 1..4 rotate A, 5..8 rotate B, and
internal zeros leave empty tiles. Keep 9-decor outside all three rectangles;
the authority processes the WHOLE code crop. Symmetric templates are lawful.

Every five consecutive draws include two small templates, two dense rotation
witnesses, and one canonical sparse/symmetric pair. Size, gaps and decoration
are crossed. Four demonstrations retain each declared rival's evidence after
any single query holdout. Explicit controls may replace this teaching schedule.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02280b74c8ab"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "a7b2395a133e"
SUMMARY = (
    "Largest magenta/orange components define equal square templates. "
    "An independently placed 1..8 index rectangle selects and rotates them; "
    "zero slots stay blank. Canonical symmetric and dense asymmetric shapes, "
    "2/3-cell tile sizes, internal gaps, and exterior 9-decor are supported."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("small_gapped", "dense_full", "small_full", "dense_gapped", "canonical_sparse")

INVARIANTS = [
    "unique largest color-6 and color-7 4-components, each at least three cells",
    "equal square 2x2 or 3x3 template bboxes containing only their own color and zero",
    "template bboxes and the nonempty 1..8 code bbox are pairwise disjoint",
    "code crop contains only 0..8; exterior color-9 decor is never inside a crop",
    "default helpful codes use both templates; symmetric templates remain lawful",
    "exact controls are honored or rejected explicitly; output fits 30x30",
]
CODE_SHAPES = ("2x4", "2x3", "3x2", "3x3", "gapped")
HELPFUL_TEXTURES = CODE_SHAPES
DEGENERATE_TEXTURES = ("monotone_code", "single_index")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
AXES = {
    "grid_h": {"type": "int", "default": "10..20; canonical profile favors 13/14", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "12..22; canonical profile favors 15/16", "valid": "12..22"},
    "tpl_size": {"type": "int", "default": "2 at residues 0/2 of 5; otherwise 3", "valid": "2..3"},
    "code_shape": {"type": "enum", "default": "gapped at residues 0/3 of 5; otherwise 2x3 or 3x2", "valid": "2x4|2x3|3x2|3x3|gapped"},
    "decor_9": {"type": "bool", "default": "seed-flipped two-of-four schedule; canonical profile has none", "valid": "0|1"},
    "texture": {"type": "enum", "default": "same as code_shape", "valid": "2x4|2x3|3x2|3x3|gapped|monotone_code|single_index"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": texture, "code_shape": shape}
    for texture in CODE_SHAPES for shape in CODE_SHAPES if texture != shape
] + [{"texture": "single_index", "code_shape": None}]


def schedule_profile(seed, sample_index, difficulty=None):
    """Default schedule only; controls can deliberately replace a profile."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _bbox(cells):
    if not cells:
        raise ValueError("no code cells outside the selected templates")
    rs, cs = zip(*cells)
    return min(rs), min(cs), max(rs) + 1, max(cs) + 1


def _crop(grid, box):
    r0, c0, r1, c1 = box
    return [list(row[c0:c1]) for row in grid[r0:r1]]


def _inside(point, box):
    r, c = point
    return box[0] <= r < box[2] and box[1] <= c < box[3]


def _overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def _components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}
    found = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        found.append(cells)
    return sorted(found, key=lambda cells: (-len(cells), min(cells)))


def _parts(grid, *, topmost=False, include_nine=False):
    chosen = []
    for color in (6, 7):
        groups = _components(grid, color)
        if not groups:
            raise ValueError(f"missing color-{color} template")
        chosen.append(min(groups, key=lambda cells: min(cells)) if topmost else groups[0])
    boxes = [_bbox(cells) for cells in chosen]
    used = chosen[0] | chosen[1]
    codes = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if 1 <= v <= (9 if include_nine else 8) and (r, c) not in used]
    code_box = _bbox(codes)
    return [_crop(grid, box) for box in boxes], _crop(grid, code_box), boxes, code_box


def _rotate(pattern, turns=1):
    result = [list(row) for row in pattern]
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


@lru_cache(maxsize=8)
def _template_library(size, kind):
    """Finite constructive shapes: no rejection limit or wrong-size fallback."""
    shapes = []
    for mask in range(1, 1 << (size * size)):
        cells = {(r, c) for r in range(size) for c in range(size)
                 if mask & (1 << (r * size + c))}
        if len(cells) < 3 or _bbox(cells) != (0, 0, size, size):
            continue
        grid = [[int((r, c) in cells) for c in range(size)] for r in range(size)]
        if len(_components(grid, 1)) != 1:
            continue
        rotations = {tuple(tuple(row) for row in _rotate(grid, k)) for k in range(4)}
        if kind == "asymmetric" and len(rotations) != 4:
            continue
        if kind == "dense" and (len(rotations) != 4 or len(cells) != size * size - 1):
            continue
        if kind == "sparse" and (len(rotations) != 4 or len(cells) not in (5, 6)):
            continue
        if kind == "symmetric" and (len(rotations) != 1 or len(cells) not in (5, 8)):
            continue
        shapes.append(tuple(sorted(cells)))
    if not shapes:
        raise ValueError(f"no {kind} templates of size {size}")
    return tuple(shapes)


def _validate_controls(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w", "tpl_size"):
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer")
            lo, hi = {"grid_h": (10, 20), "grid_w": (12, 22), "tpl_size": (2, 3)}[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} outside [{lo}, {hi}]")
        elif name == "decor_9":
            if type(value) not in (int, bool) or value not in (0, 1):
                raise ValueError("decor_9 must be 0 or 1")
        elif type(value) is not str or value not in (CODE_SHAPES if name == "code_shape" else CODE_SHAPES + DEGENERATE_TEXTURES):
            raise ValueError(f"invalid {name}: {value!r}")
    shape, texture = overrides.get("code_shape"), overrides.get("texture")
    if shape is not None and texture is not None and (texture == "single_index" or (texture in CODE_SHAPES and texture != shape)):
        exc = ValueError("incompatible code_shape and texture overrides")
        exc.incompatible_axes = ("code_shape", "texture")
        raise exc


def _layout(rng, h, w, side, ch, cw, *, witness):
    mode = "above" if witness else rng.choice(("above", "below", "left", "right"))
    swap = True if witness else bool(rng.randrange(2))
    if mode in ("above", "below"):
        top_h, bottom_h = (ch, side) if mode == "above" else (side, ch)
        split = rng.randint(top_h, h - bottom_h - 1)
        left = rng.randint(0, w - 2 * side - 1)
        right = rng.randint(left + side + 1, w - side)
        if mode == "above":
            code = (rng.randint(0, split - ch), rng.randint(0, w - cw))
            origins = [(rng.randint(split + 1, h - side), c) for c in (left, right)]
        else:
            code = (rng.randint(split + 1, h - ch), rng.randint(0, w - cw))
            origins = [(rng.randint(0, split - side), c) for c in (left, right)]
    else:
        left_w, right_w = (cw, side) if mode == "left" else (side, cw)
        split = rng.randint(left_w, w - right_w - 1)
        top = rng.randint(0, h - 2 * side - 1)
        bottom = rng.randint(top + side + 1, h - side)
        if mode == "left":
            code = (rng.randint(0, h - ch), rng.randint(0, split - cw))
            origins = [(r, rng.randint(split + 1, w - side)) for r in (top, bottom)]
        else:
            code = (rng.randint(0, h - ch), rng.randint(split + 1, w - cw))
            origins = [(r, rng.randint(0, split - side)) for r in (top, bottom)]
    if swap:
        origins.reverse()
    return origins, code


def _code(rng, shape, texture, *, core):
    if texture == "single_index":
        return [[rng.randint(1, 8)]]
    ch, cw = (2, 4) if shape == "gapped" else tuple(map(int, shape.split("x")))
    # A whole internal zero column distinguishes keeping empty axes from
    # compressing them. Edge columns stay nonzero, preserving exact bounds.
    gap_column = rng.choice((1, 2)) if shape == "gapped" else None
    positions = [(r, c) for r in range(ch) for c in range(cw) if c != gap_column]
    count = len(positions)
    if texture == "monotone_code":
        values = [rng.randint(1, 4) for _ in positions]
    elif count == 6 and core:
        values = [rng.choice((6, 7))] + rng.sample((1, 2, 3, 4, 5, 8), 5)
    elif count == 6:
        low = rng.sample((2, 3, 4), 2)
        values = [6, 7] + low + rng.sample([v for v in (1, 2, 3, 4, 5, 8) if v not in low], 2)
    else:
        values = list(range(1, 9))
        values += [rng.choice((1, 2, 3, 4, 5, 8)) for _ in range(count - 8)]
    rng.shuffle(values)
    code = full_grid(ch, cw, 0)
    for (r, c), v in zip(positions, values):
        code[r][c] = v
    return code


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(overrides)
    # Build the episode-level draw before the per-grid context: public draw
    # observers consume the last context as this grid's exact-axis provenance.
    family = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                     task_id=TASK_ID, difficulty=difficulty)
    flip = family.draw_choice("decor_phase_flip", (0, 1))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % len(SCHEDULE_PROFILES)
    small = phase in (0, 2)
    core = not small
    # Preserve canonical profiles, while spatial search grows across bands.
    # Every advertised dimension remains available to every exact override.
    favored_h, favored_w = {
        "easy": ((10, 11, 12), (12, 13, 14)),
        "hard": ((18, 19, 20), (20, 21, 22)),
    }.get(difficulty, ((13, 14, 15, 16), (15, 16, 17, 18)))
    h_bias = (14,) * 100 if phase == 2 else ((13, 14) * 100 if core else favored_h * 8)
    w_bias = (16,) * 100 if phase == 2 else ((15, 16) * 100 if core else favored_w * 8)
    h = ctx.draw_choice("grid_h", tuple(range(10, 21)) + h_bias)
    w = ctx.draw_choice("grid_w", tuple(range(12, 23)) + w_bias)
    side = ctx.draw_choice("tpl_size", (2, 3) if overrides.get("tpl_size") is not None else ((3,) if core else (2,)))
    requested_texture = overrides.get("texture")
    if requested_texture == "single_index":
        shape = "1x1"
    elif overrides.get("code_shape") is not None:
        shape = ctx.draw_choice("code_shape", CODE_SHAPES)
    elif requested_texture in CODE_SHAPES:
        shape = ctx.draw_choice("code_shape", (requested_texture,))
    else:
        choices = ("gapped",) if phase in (0, 3) else ("2x3", "3x2")
        shape = ctx.draw_choice("code_shape", choices)
    texture = ctx.draw_choice("texture", (requested_texture,) if requested_texture is not None else (shape,))
    # Seed-only flip keeps this pattern fixed across an episode's indices.
    # Both sizes occur with and without decor; decor does not imply gaps.
    default_decor = int((phase < 2) != bool(flip)) if phase < 4 else 0
    decor = ctx.draw_choice("decor_9", (0, 1) if overrides.get("decor_9") is not None else (default_decor,))
    code = _code(ctx.draw_rng("code_values"), shape, texture, core=core)
    ch, cw = len(code), len(code[0])
    origins, code_origin = _layout(ctx.draw_rng("layout"), h, w, side, ch, cw, witness=small)
    grid = full_grid(h, w, 0)
    boxes = []
    dense_color = ctx.draw_choice("dense_color", (6, 7))
    for color, (r0, c0) in zip((6, 7), origins):
        if core and side == 3:
            kind = ("sparse" if phase == 4 else "dense") if color == dense_color else "symmetric"
        else:
            kind = "asymmetric"
        cells = ctx.draw_rng(f"template_{color}").choice(_template_library(side, kind))
        for r, c in cells:
            grid[r0 + r][c0 + c] = color
        boxes.append((r0, c0, r0 + side, c0 + side))
    r0, c0 = code_origin
    for r, row in enumerate(code):
        for c, value in enumerate(row):
            grid[r0 + r][c0 + c] = value
    boxes.append((r0, c0, r0 + ch, c0 + cw))
    if decor:
        exterior = [(r, c) for r in range(h) for c in range(w)
                    if all(not _inside((r, c), box) for box in boxes)]
        r, c = ctx.draw_rng("decor_position").choice(exterior)
        grid[r][c] = 9
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30):
        return ["input dimensions must be in 1..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9"]
    try:
        for color in (6, 7):
            groups = _components(grid, color)
            if not groups or len(groups[0]) < 3:
                raise ValueError(f"color-{color} template needs at least three cells")
            if len(groups) > 1 and len(groups[0]) == len(groups[1]):
                raise ValueError(f"color-{color} largest template must be unique")
        templates, code, boxes, code_box = _parts(grid)
        size = len(templates[0])
        if size not in (2, 3) or any(len(p) != size or len(p[0]) != size for p in templates):
            raise ValueError("templates must have equal square 2x2 or 3x3 bboxes")
        for color, template in zip((6, 7), templates):
            if any(v not in (0, color) for row in template for v in row):
                raise ValueError("template crop contains a foreign color")
        all_boxes = boxes + [code_box]
        if any(_overlap(a, b) for i, a in enumerate(all_boxes) for b in all_boxes[i+1:]):
            raise ValueError("template and code bboxes must be disjoint")
        if any(v == 9 for row in code for v in row):
            raise ValueError("decor_9 must be outside the code bbox")
        if len(code) * size > 30 or len(code[0]) * size > 30:
            raise ValueError("output mosaic exceeds 30x30")
    except ValueError as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """Structural clean-mosaic domain; exact size/palette is measured separately."""
    return self_check(grid)


def observe_overrides(grid):
    templates, code, _, _ = _parts(grid)
    ch, cw = len(code), len(code[0])
    gapped = any(v == 0 for row in code for v in row)
    shape = "gapped" if (ch, cw) == (2, 4) and gapped else f"{ch}x{cw}"
    texture = ("single_index" if (ch, cw) == (1, 1) else
               "monotone_code" if all(v <= 4 for row in code for v in row) else shape)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "tpl_size": len(templates[0]),
            "code_shape": shape, "decor_9": int(any(9 in row for row in grid)), "texture": texture}


def _rival_decode(grid, mode):
    """Deliberately altered rules for authoring checks; never used for labels."""
    templates, code, boxes, _ = _parts(grid, topmost=mode == "topmost_per_color",
                                      include_nine=mode == "include_9_in_bbox")
    if mode == "source_order_by_left" and boxes[0][1] > boxes[1][1]:
        templates.reverse()
    if mode == "compact_empty_index_axes":
        rows = [row for row in code if any(row)]
        columns = [c for c in range(len(code[0])) if any(row[c] for row in code)]
        code = [[row[c] for c in columns] for row in rows]
    if mode == "fixed3_stride":
        th = tw = 3
    elif mode == "stride_from_decor":
        th = tw = 2 if any(9 in row for row in grid) else 3
    elif mode == "stride_from_gap":
        th = tw = 2 if any(0 in row for row in code) else 3
    else:
        th, tw = len(templates[0]), len(templates[0][0])
    out = full_grid(len(code) * th, len(code[0]) * tw, 0)
    for r, row in enumerate(code):
        for c, value in enumerate(row):
            if value == 0:
                if mode != "gap_fills_A":
                    continue
                value = 1
            template = templates[0 if value <= 4 else 1]
            turns = (value - 1 if value <= 4 else value - 5) % 4
            if mode == "ignore_rotations" or (mode == "dense_templates_ignore_rotation" and sum(v != 0 for line in template for v in line) >= 7):
                turns = 0
            for dr, line in enumerate(_rotate(template, turns)):
                for dc, color in enumerate(line):
                    rr, cc = r * th + dr, c * tw + dc
                    if color and rr < len(out) and cc < len(out[0]):
                        out[rr][cc] = color
    return out


def _fixed3_stride(grid):
    return _rival_decode(grid, "fixed3_stride")


def _gap_fills_A(grid):
    return _rival_decode(grid, "gap_fills_A")


def _compact_empty_index_axes(grid):
    return _rival_decode(grid, "compact_empty_index_axes")


def _topmost_per_color(grid):
    return _rival_decode(grid, "topmost_per_color")


def _source_order_by_left(grid):
    return _rival_decode(grid, "source_order_by_left")


def _include_9_in_bbox(grid):
    return _rival_decode(grid, "include_9_in_bbox")


def _dense_templates_ignore_rotation(grid):
    return _rival_decode(grid, "dense_templates_ignore_rotation")


def _ignore_rotations(grid):
    return _rival_decode(grid, "ignore_rotations")


def _stride_from_decor(grid):
    return _rival_decode(grid, "stride_from_decor")


def _stride_from_gap(grid):
    return _rival_decode(grid, "stride_from_gap")


def _refutes(grid, name):
    # The gate independently checks this prediction against Racket output.
    return _rival_decode(grid, name) != _rival_decode(grid, "ordinary_geometry")


def _small_witness(grid):
    return _refutes(grid, "fixed3_stride")


def _gap_witness(grid):
    return _refutes(grid, "gap_fills_A") and _refutes(grid, "compact_empty_index_axes")


def _placement_witness(grid):
    return _refutes(grid, "topmost_per_color") and _refutes(grid, "source_order_by_left")


def _decor_witness(grid):
    return _refutes(grid, "include_9_in_bbox")


def _decor_stride_witness(grid):
    return _refutes(grid, "stride_from_decor")


def _gap_stride_witness(grid):
    return _refutes(grid, "stride_from_gap")


def _dense_witness(grid):
    return _refutes(grid, "dense_templates_ignore_rotation")


CANONICAL_SHORTCUTS = {
    "fixed3_stride": _fixed3_stride,
    "gap_fills_A": _gap_fills_A,
    "compact_empty_index_axes": _compact_empty_index_axes,
    "topmost_per_color": _topmost_per_color,
    "source_order_by_left": _source_order_by_left,
    "include_9_in_bbox": _include_9_in_bbox,
    "dense_templates_ignore_rotation": _dense_templates_ignore_rotation,
    "stride_from_decor": _stride_from_decor,
    "stride_from_gap": _stride_from_gap,
}
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS, "ignore_rotations": _ignore_rotations}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "small_templates": _small_witness, "internal_gaps": _gap_witness,
    "moved_templates": _placement_witness, "exterior_decor": _decor_witness,
    "dense_rotation": _dense_witness, "decor_not_stride": _decor_stride_witness,
    "gap_not_stride": _gap_stride_witness,
}
WITNESS_RIVALS = {
    "small_templates": ["fixed3_stride"],
    "internal_gaps": ["gap_fills_A", "compact_empty_index_axes"],
    "moved_templates": ["topmost_per_color", "source_order_by_left"],
    "exterior_decor": ["include_9_in_bbox"],
    "dense_rotation": ["dense_templates_ignore_rotation"],
    "decor_not_stride": ["stride_from_decor"],
    "gap_not_stride": ["stride_from_gap"],
}
