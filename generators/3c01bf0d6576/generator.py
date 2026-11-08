"""Generator for arc_additional_puzzles_21_set18_bundle:H121 — transform by example.

The selected rule sorts all 4-connected non-zero components by bounding-box
(top, left).  It crops the first three *from the original grid*, infers which
of six visible dihedral transforms maps crop A to crop A', and applies that
same transform to crop B.  Cropping from the original grid matters: one
canonical demonstration contains a fourth isolated cell inside B's bounding
box, so that satellite is part of the transformed B crop even though it is not
part of B's connected component.

The teaching schedule preserves that edge case, plus a canonical case where
A's binary geometry is fully symmetric and only the colours identify the
transform.  Four consecutive samples therefore refute three tempting wrong
rules: leave B unchanged, infer the transform from shape only, or transform
only B's connected component instead of its full crop.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3c01bf0d6576"
TASK_ID = GENERATOR_ID
RULE_HASH = "3722dcd853de"  # canonical hash after task-scoped source synchronization
VERSION = "3.0.0"

SUMMARY = (
    "Read non-zero 4-connected components in bounding-box reading order. "
    "The first two crops A and A' demonstrate one non-identity transform from "
    "{rotate 90 CW, rotate 180, transpose, flip LR, flip UD}. Infer that "
    "transform from the full coloured crops, then apply it to the full "
    "bounding-box crop of the third component B and output only that "
    "transformed crop. A disconnected satellite inside B's bbox is therefore "
    "included."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.30

INVARIANTS = [
    "background is 0 and the grid is rectangular",
    "there are exactly three main non-zero 4-connected components in reading order, optionally plus one single-cell satellite inside B's bbox",
    "the full coloured A crop maps to A' by exactly one supported non-identity transform",
    "B's transformed crop differs from its input crop",
    "the ordinary palette contains exactly 3..5 non-zero colours",
]

HELPFUL_TEXTURES = ("standard", "query_satellite", "color_disambiguation")
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 11/12 or difficulty-aware 11..14",
        "valid": "11..14",
        "doc": "Exact input height; overrides are honoured in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 15/16 or difficulty-aware 15..18",
        "valid": "15..18",
        "doc": "Exact input width; overrides are honoured in every band.",
    },
    "transform": {
        "type": "int",
        "default": "scheduled 1,4,2,5,3",
        "valid": "1..5",
        "doc": "Exact supported A->A' transform code (0 identity is not an ordinary lesson).",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 3 or 5, otherwise rng 3..5",
        "valid": "3..5",
        "doc": "Exact number of distinct non-zero colours in the input.",
    },
    "texture": {
        "type": "str",
        "default": "four-slot standard|query_satellite|color_disambiguation|standard schedule",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": "Which decisive semantic branch is made visible in the input.",
    },
}

# Transform codes deliberately mirror the selected Racket program, not the
# generic helpers' 8-code D4 numbering.
_TRANSFORM_SCHEDULE = (1, 4, 2, 5, 3)

# A 5-cell asymmetric connected shape whose binary support has no ambiguity
# under the six supported transforms. Variants are sampled to avoid a single
# memorisable silhouette while retaining a 3x3 canonical crop.
_STANDARD_A_SHAPES = (
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
)

# Binary support is D4-symmetric.  The coloured cells, not the geometry, must
# identify the transform. This mirrors canonical demonstration #3.
_COLOR_DISAMBIG_SHAPE = (
    (0, 1),
    (1, 0), (1, 1), (1, 2),
    (2, 1),
)

_CONNECTED_B_SHAPES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (2, 0)),
)

# The main component spans the 3x3 bbox; (0,2) is an isolated satellite inside
# that bbox. This is the canonical crop-vs-component discriminator.
_SATELLITE_B_MAIN = ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2))
_SATELLITE_CELL = (0, 2)

_RECT_B_SHAPES = (
    ((0, 0), (0, 1), (1, 1), (1, 2)),           # 2x3 zig-zag
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3)),  # 2x4
)


def _xform_grid(g: list[list[int]], t: int) -> list[list[int]]:
    if t == 0:
        return [row[:] for row in g]
    if t == 1:
        h, w = len(g), len(g[0])
        return [[g[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if t == 2:
        return [row[::-1] for row in g[::-1]]
    if t == 3:
        h, w = len(g), len(g[0])
        return [[g[r][c] for r in range(h)] for c in range(w)]
    if t == 4:
        return [row[::-1] for row in g]
    if t == 5:
        return g[::-1]
    raise ValueError(f"unsupported transform code {t}")


def _binary(g: list[list[int]]) -> list[list[int]]:
    return [[1 if v else 0 for v in row] for row in g]


def _matching_codes(a: list[list[int]], ap: list[list[int]], *, shape_only: bool = False) -> list[int]:
    left = _binary(a) if shape_only else a
    right = _binary(ap) if shape_only else ap
    return [t for t in range(6) if _xform_grid(left, t) == right]


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _grid_from_cells(cells: Iterable[tuple[int, int]], colors: list[int]) -> list[list[int]]:
    cells = _normalize_cells(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    g = full_grid(h, w, 0)
    for (r, c), color in zip(cells, colors):
        g[r][c] = color
    return g


def _assign_colors(
    rng: Any,
    cells: Iterable[tuple[int, int]],
    palette: list[int],
    *,
    require_all: bool = True,
) -> list[int]:
    cells = tuple(cells)
    if require_all and len(palette) > len(cells):
        raise ValueError("palette larger than motif")
    out = list(palette if require_all else [])
    while len(out) < len(cells):
        out.append(rng.choice(palette))
    rng.shuffle(out)
    return out[:len(cells)]


def _has_override(ctx: Any, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _draw_int_axis(
    ctx: Any,
    label: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    return ctx.draw_int(label, *(valid_bounds if _has_override(ctx, label) else default_bounds))


def _draw_choice_axis(
    ctx: Any,
    label: str,
    default_options: tuple[str, ...],
    valid_options: tuple[str, ...],
) -> str:
    return ctx.draw_choice(label, valid_options if _has_override(ctx, label) else default_options)


def _scheduled_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    slot = sample_index % 4
    anchored = sample_index % 8 < 4
    texture = ("standard", "query_satellite", "color_disambiguation", "standard")[slot]

    if anchored:
        if slot in (0, 1):
            h_bounds, w_bounds = (11, 11), (15, 15)
        else:
            h_bounds, w_bounds = (12, 12), (16, 16)
        palette_bounds = (3, 3) if slot == 1 else (5, 5)
    else:
        if difficulty == "easy":
            h_bounds, w_bounds = (11, 12), (15, 16)
        elif difficulty == "hard":
            h_bounds, w_bounds = (13, 14), (17, 18)
        else:
            h_bounds, w_bounds = (12, 13), (16, 17)
        palette_bounds = (3, 5)

    t = _TRANSFORM_SCHEDULE[sample_index % len(_TRANSFORM_SCHEDULE)]
    return {
        "grid_h": h_bounds,
        "grid_w": w_bounds,
        "transform": (t, t),
        "palette_size": palette_bounds,
        "texture": (texture,),
    }


def _make_a(rng: Any, transform: int, palette: list[int], texture: str) -> list[list[int]]:
    candidates = (
        [_COLOR_DISAMBIG_SHAPE]
        if texture == "color_disambiguation"
        else list(_STANDARD_A_SHAPES)
    )
    rng.shuffle(candidates)

    # A uses up to three colours, matching the canonical role split where B
    # often introduces additional colours not present in A.
    a_palette = palette[: min(3, len(palette))]
    for cells in candidates:
        for _ in range(80):
            colors = _assign_colors(rng, cells, a_palette, require_all=True)
            a = _grid_from_cells(cells, colors)
            ap = _xform_grid(a, transform)
            if _matching_codes(a, ap) != [transform]:
                continue
            shape_codes = _matching_codes(a, ap, shape_only=True)
            if texture == "color_disambiguation":
                if len(shape_codes) <= 1:
                    continue
            elif shape_codes != [transform]:
                continue
            return a
    raise ValueError("could not color A so the requested transform is uniquely visible")


def _make_b(
    rng: Any,
    transform: int,
    palette: list[int],
    texture: str,
    sample_index: int,
) -> list[list[int]]:
    # For palettes wider than A's three colours, force B to expose every extra
    # colour so palette_size is exactly observable from the returned grid.
    if len(palette) <= 3:
        b_palette = palette[-2:]
    else:
        b_palette = palette[3:] + [palette[0]]

    if texture == "query_satellite":
        main = _SATELLITE_B_MAIN
        all_cells = tuple(main) + (_SATELLITE_CELL,)
        for _ in range(80):
            colors = _assign_colors(rng, all_cells, b_palette, require_all=True)
            b = _grid_from_cells(all_cells, colors)
            if _xform_grid(b, transform) != b:
                return b
        raise ValueError("could not color satellite B nontrivially")

    shapes = list(_RECT_B_SHAPES if sample_index % 4 == 3 else _CONNECTED_B_SHAPES)
    rng.shuffle(shapes)
    for cells in shapes:
        for _ in range(40):
            colors = _assign_colors(rng, cells, b_palette, require_all=True)
            b = _grid_from_cells(cells, colors)
            if _xform_grid(b, transform) != b:
                return b
    raise ValueError("could not construct a query crop changed by the transform")


def _nonzero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            comps.append(comp)
    return sorted(comps, key=lambda comp: _bbox_key(comp))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _bbox_key(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, _r1, _c1 = _bbox(cells)
    return r0, c0


def _crop(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _free(g: list[list[int]], top: int, left: int, motif: list[list[int]]) -> bool:
    h, w = len(g), len(g[0])
    sh, sw = len(motif), len(motif[0])
    if top < 0 or left < 0 or top + sh > h or left + sw > w:
        return False
    for r in range(max(0, top - 1), min(h, top + sh + 1)):
        for c in range(max(0, left - 1), min(w, left + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g: list[list[int]], top: int, left: int, motif: list[list[int]]) -> None:
    for r, row in enumerate(motif):
        for c, value in enumerate(row):
            if value:
                g[top + r][left + c] = value


def _place_scene(
    rng: Any,
    h: int,
    w: int,
    a: list[list[int]],
    ap: list[list[int]],
    b: list[list[int]],
) -> list[list[int]]:
    # Structured zones make every declared override combination reliable while
    # retaining positional diversity inside those zones.
    for _ in range(160):
        g = full_grid(h, w, 0)
        ah, aw = len(a), len(a[0])
        ph, pw = len(ap), len(ap[0])
        bh, bw = len(b), len(b[0])

        top_cap = max(0, min(h - max(ah, ph) - 5, 3))
        ar = rng.randint(0, top_cap)
        pr = ar
        a_left_hi = max(0, min(3, w // 3 - aw))
        ac = rng.randint(0, a_left_hi)
        p_left_lo = max(ac + aw + 2, w - pw - 4)
        p_left_hi = w - pw
        if p_left_lo > p_left_hi:
            continue
        pc = rng.randint(p_left_lo, p_left_hi)

        b_row_lo = max(ar + max(ah, ph) + 2, h - bh - 3)
        b_row_hi = h - bh
        if b_row_lo > b_row_hi:
            continue
        br = rng.randint(b_row_lo, b_row_hi)
        bc = rng.randint(0, w - bw)

        placements = ((ar, ac, a), (pr, pc, ap), (br, bc, b))
        positions: list[tuple[int, int]] = []
        ok = True
        for r0, c0, motif in placements:
            if positions and (r0, c0) <= positions[-1]:
                ok = False
                break
            if not _free(g, r0, c0, motif):
                ok = False
                break
            _paint(g, r0, c0, motif)
            positions.append((r0, c0))
        if ok:
            return g
    raise ValueError(f"incompatible axis combination: could not place A/A'/B on {h}x{w}")


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(sample_index, difficulty)
    h = _draw_int_axis(ctx, "grid_h", defaults["grid_h"], (11, 14))
    w = _draw_int_axis(ctx, "grid_w", defaults["grid_w"], (15, 18))
    transform = _draw_int_axis(ctx, "transform", defaults["transform"], (1, 5))
    palette_size = _draw_int_axis(ctx, "palette_size", defaults["palette_size"], (3, 5))
    texture = _draw_choice_axis(ctx, "texture", defaults["texture"], HELPFUL_TEXTURES)

    rng = ctx.draw_rng("content")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], palette_size)
    a = _make_a(rng, transform, palette, texture)
    ap = _xform_grid(a, transform)
    b = _make_b(rng, transform, palette, texture, sample_index)
    return _place_scene(rng, h, w, a, ap, b)


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {}, ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {}, ["grid rows must be rectangular lists"]
    bad_values = [v for row in grid for v in row if not isinstance(v, int) or not (0 <= v <= 9)]
    if bad_values:
        errors.append("grid values must be integer ARC colours 0..9")
        return {"grid_h": h, "grid_w": w}, errors

    comps = _nonzero_components(grid)
    if len(comps) not in (3, 4):
        errors.append(f"expected 3 main components plus at most one B satellite; found {len(comps)}")
        return {"grid_h": h, "grid_w": w, "components": comps}, errors

    a_cells, ap_cells, b_cells = comps[:3]
    a = _crop(grid, a_cells)
    ap = _crop(grid, ap_cells)
    b = _crop(grid, b_cells)

    # A and A' are pure connected-component crops. A hidden extra component in
    # either bbox would change the selected rule's comparison in a way absent
    # from every canonical example.
    owner = {cell: i for i, comp in enumerate(comps) for cell in comp}
    for name, cells, crop_grid in (("A", a_cells, a), ("A'", ap_cells, ap)):
        r0, c0, r1, c1 = _bbox(cells)
        foreign = [
            (r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if grid[r][c] != 0 and owner.get((r, c)) not in (0 if name == "A" else 1,)
        ]
        if foreign:
            errors.append(f"{name} bbox contains a foreign disconnected component")

    matches = _matching_codes(a, ap)
    if len(matches) != 1 or matches[0] == 0:
        errors.append(f"A->A' must identify one non-identity supported transform; matches={matches}")
        transform = None
    else:
        transform = matches[0]

    satellite = comps[3:] if len(comps) == 4 else []
    b_box = _bbox(b_cells)
    for extra in satellite:
        er0, ec0, er1, ec1 = _bbox(extra)
        if len(extra) != 1:
            errors.append("B satellite must be a single isolated cell")
        if not (b_box[0] <= er0 <= er1 <= b_box[2] and b_box[1] <= ec0 <= ec1 <= b_box[3]):
            errors.append("extra component must lie inside B's bounding box")
        if _bbox_key(extra) <= _bbox_key(b_cells):
            errors.append("B satellite must sort after the main B component")

    b_nonzero = [v for row in b for v in row if v != 0]
    if len(b_nonzero) < 4:
        errors.append(f"B crop is too small to teach the transform: {len(b_nonzero)} non-zero cells")
    if len(set(b_nonzero)) < 2:
        errors.append("B crop must use at least two colours")
    if transform is not None and _xform_grid(b, transform) == b:
        errors.append("B crop is invariant under the inferred transform")

    shape_matches = _matching_codes(a, ap, shape_only=True) if not errors or a and ap else []
    if satellite:
        texture = "query_satellite"
    elif len(shape_matches) > 1:
        texture = "color_disambiguation"
    else:
        texture = "standard"

    palette = sorted({v for row in grid for v in row if v != 0})
    info = {
        "grid_h": h,
        "grid_w": w,
        "components": comps,
        "A": a,
        "Aprime": ap,
        "B": b,
        "transform": transform,
        "shape_matches": shape_matches,
        "palette": palette,
        "palette_size": len(palette),
        "texture": texture,
        "satellite_count": len(satellite),
        "B_shape": (len(b), len(b[0])),
    }
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "transform": info["transform"],
        "palette_size": info["palette_size"],
        "texture": info["texture"],
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    info, errors = _analyze(grid)
    if errors:
        return errors
    if not (11 <= info["grid_h"] <= 14):
        errors.append(f"grid_h outside 11..14: {info['grid_h']}")
    if not (15 <= info["grid_w"] <= 18):
        errors.append(f"grid_w outside 15..18: {info['grid_w']}")
    if not (3 <= info["palette_size"] <= 5):
        errors.append(f"palette_size outside 3..5: {info['palette_size']}")
    if info["texture"] not in HELPFUL_TEXTURES:
        errors.append(f"unrecognised semantic texture {info['texture']!r}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (info["grid_h"], info["grid_w"]) not in {(11, 15), (12, 16)}:
        reasons.append("canonical inputs are 11x15 or 12x16")
    if len(info["A"]) != 3 or len(info["A"][0]) != 3:
        reasons.append("canonical A crop is 3x3")
    if len(info["Aprime"]) != 3 or len(info["Aprime"][0]) != 3:
        reasons.append("canonical A' crop is 3x3")
    if info["B_shape"] != (3, 3):
        reasons.append("canonical B crop is 3x3")
    if info["palette_size"] not in (3, 5):
        reasons.append("canonical inputs use 3 or 5 non-zero colours")
    return reasons


def _witness_nonidentity(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and info["transform"] in range(1, 6) and _xform_grid(info["B"], info["transform"]) != info["B"]


def _witness_satellite(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and info["texture"] == "query_satellite"


def _witness_color_disambiguation(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and info["texture"] == "color_disambiguation" and len(info["shape_matches"]) > 1


def _witness_rectangular_query(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return not errors and info["B_shape"][0] != info["B_shape"][1]


def _transform_witness(code: int):
    def witness(grid: Any) -> bool:
        info, errors = _analyze(grid)
        return not errors and info["transform"] == code
    return witness


SEMANTIC_WITNESSES = {
    "nonidentity_query_transform": _witness_nonidentity,
    "query_satellite_in_crop": _witness_satellite,
    "color_disambiguates_transform": _witness_color_disambiguation,
    "rectangular_query_crop": _witness_rectangular_query,
    "rotate_90": _transform_witness(1),
    "rotate_180": _transform_witness(2),
    "transpose": _transform_witness(3),
    "flip_lr": _transform_witness(4),
    "flip_ud": _transform_witness(5),
}


def _solve_python(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _xform_grid(info["B"], info["transform"])


def _rival_identity_query(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return [row[:] for row in info["B"]]


def _rival_shape_only(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    codes = info["shape_matches"]
    code = codes[0] if codes else 0
    return _xform_grid(info["B"], code)


def _rival_connected_query_only(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    b_cells = info["components"][2]
    norm = _normalize_cells(b_cells)
    h = max(r for r, _ in norm) + 1
    w = max(c for _, c in norm) + 1
    b = full_grid(h, w, 0)
    r0, c0, _r1, _c1 = _bbox(b_cells)
    for r, c in b_cells:
        b[r - r0][c - c0] = grid[r][c]
    return _xform_grid(b, info["transform"])


def _rival_square_query_only(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["B_shape"][0] != info["B_shape"][1]:
        # Shortcut: only trusts square query crops and leaves rectangular ones
        # untouched instead of allowing rotate/transpose to swap dimensions.
        return [row[:] for row in info["B"]]
    return _xform_grid(info["B"], info["transform"])


SEMANTIC_RIVALS = {
    "identity_query": _rival_identity_query,
    "shape_only_transform": _rival_shape_only,
    "connected_query_only": _rival_connected_query_only,
    "square_query_only": _rival_square_query_only,
}

WITNESS_RIVALS = {
    "nonidentity_query_transform": ["identity_query"],
    "color_disambiguates_transform": ["shape_only_transform"],
    "query_satellite_in_crop": ["connected_query_only"],
    "rectangular_query_crop": ["square_query_only"],
    "rotate_90": ["identity_query"],
    "rotate_180": ["identity_query"],
    "transpose": ["identity_query"],
    "flip_lr": ["identity_query"],
    "flip_ud": ["identity_query"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    infos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, bad = _analyze(pair["input"])
        if bad:
            reasons.append(f"demo {index} malformed: {bad[0]}")
            continue
        if pair["output"] != _xform_grid(info["B"], info["transform"]):
            reasons.append(f"demo {index} output does not apply A->A' transform to the full B crop")
        infos.append(info)
    if len(infos) != len(demos):
        return reasons

    transforms = {info["transform"] for info in infos}
    textures = {info["texture"] for info in infos}
    if len(transforms) < 3:
        reasons.append(f"transform is too fixed across demonstrations: {sorted(transforms)}")
    if "query_satellite" not in textures:
        reasons.append("no demo distinguishes B's full bbox crop from B's connected component")
    if "color_disambiguation" not in textures:
        reasons.append("no demo requires colours to disambiguate a shape-symmetric A->A' transform")
    if not any(info["B_shape"][0] != info["B_shape"][1] for info in infos):
        reasons.append("all B crops are square, leaving output-dimension swapping under-tested")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qinfo, qbad = _analyze(query["input"])
        if qbad:
            reasons.append(f"query malformed: {qbad[0]}")
        elif _xform_grid(qinfo["B"], qinfo["transform"]) == qinfo["B"]:
            reasons.append("query does not visibly require applying the inferred transform")
    return reasons
