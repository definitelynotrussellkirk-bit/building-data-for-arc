"""Generator for arc_puzzle_bank_fifth21:H34 — outline analogy.

A full color-9 row and column split the grid into four quadrants.  The top
left/top right pair is a worked example: a solid shape becomes its cardinal
outline at the same local offset.  Apply that operation to the bottom-left
shape and stamp the result into the bottom-right quadrant, using the first
bottom-left cell in row-major order as the output color.  Existing bottom-right
cells survive unless an outline cell overwrites them, and out-of-grid stamp
cells are clipped by the Racket oracle.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0994294912bf"
TASK_ID = "0994294912bf"
VERSION = "4.1.0"
RULE_HASH = "ebb564e19380"

SUMMARY = (
    "A color-9 cross forms four quadrants. TL->TR is always a worked solid-to-"
    "cardinal-outline example. The BL union is outlined and stamped into BR at "
    "the same local offset in the BL row-major first color. Solid, multicolor, "
    "pre-filled-BR, and clipped variants rebut whole-copy, per-cell/modal-color, "
    "empty-target, fixed-size, and must-fit shortcuts. Version 4.1.0 makes the "
    "four decisive profiles match the four-demo lesson budget, and adjacent "
    "profiles deliberately overlap their causal witnesses so every allowed "
    "query rotation remains identifiable. It preserves the "
    "mandatory worked analogy, exact 8..20 dimension envelope, and observable axes."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.08

INVARIANTS = [
    "exactly one full color-9 row and column, with no off-cross color-9 cells",
    "all four quadrants are at least 3x3",
    "TL is a one-color solid rectangle and TR is its same-offset cardinal outline",
    "BL is empty only for the explicit lawful no_shape edge case; otherwise its union is 4-connected",
    "every four consecutive ordinary samples contain solid, multicolor, br_decoy, and clip profiles exactly once",
    "interior, multicolor, pre-filled-target, and clipping witnesses each occur in two adjacent schedule profiles",
]

DEGENERATE_TEXTURES = ("no_shape",)
LAWFUL_DEGENERATE_TEXTURES = ("no_shape",)
HELPFUL_TEXTURES = ("plain", "solid", "multicolor", "br_decoy", "clip")
_ALL_TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..20 with 1/4 strict and 1/4 envelope anchors",
        "valid": "8..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 8..20 with 1/4 strict and 1/4 envelope anchors",
        "valid": "8..20",
    },
    "texture": {
        "type": "str",
        "default": "four-slot lesson cycle solid|multicolor|br_decoy|clip",
        "valid": "plain|solid|multicolor|br_decoy|clip|no_shape",
        "doc": (
            "solid has a true interior; multicolor adds first-scan color and a "
            "pre-filled target; br_decoy combines target collisions with clipping; "
            "clip combines clipping with a multicolor source; these overlaps keep "
            "all five query rotations identifiable. "
            "plain and no_shape remain explicit override-only cases."
        ),
    },
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_LESSON_TEXTURES = ("solid", "multicolor", "br_decoy", "clip")
SCHEDULE_PROFILES = _LESSON_TEXTURES


def _full_cross(grid) -> tuple[int | None, int | None]:
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return None, None
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return None, None
    rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        return None, None
    return rows[0], cols[0]


def _quad_cells(grid, gr: int, gc: int, quad: str) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    if quad == "TL":
        r0, r1, c0, c1 = 0, gr, 0, gc
    elif quad == "TR":
        r0, r1, c0, c1 = 0, gr, gc + 1, w
    elif quad == "BL":
        r0, r1, c0, c1 = gr + 1, h, 0, gc
    elif quad == "BR":
        r0, r1, c0, c1 = gr + 1, h, gc + 1, w
    else:  # pragma: no cover - internal misuse
        raise ValueError(f"unknown quadrant {quad!r}")
    return [
        (r - r0, c - c0, grid[r][c])
        for r in range(r0, r1)
        for c in range(c0, c1)
        if grid[r][c] not in (0, 9)
    ]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[list[tuple[int, int]], int, int]:
    cells = sorted(set(cells))
    if not cells:
        return [], 0, 0
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return sorted((r - rmin, c - cmin) for r, c in cells), rmin, cmin


def _outline(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = sorted(set(cells))
    occupied = set(cells)
    return [
        p
        for p in cells
        if any((p[0] + dr, p[1] + dc) not in occupied for dr, dc in _DIR4)
    ]


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return True
    queue = deque([next(iter(remaining))])
    seen = {queue[0]}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            q = (r + dr, c + dc)
            if q in remaining and q not in seen:
                seen.add(q)
                queue.append(q)
    return seen == remaining


def _is_filled_rectangle(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return len(cells) == (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def _analyze(grid) -> dict:
    result = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        result["errors"].append("grid must be a nonempty list of rows")
        return result
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        result["errors"].append("grid must be rectangular with nonempty rows")
        return result
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        result["errors"].append("grid colors must be integers in 0..9")
    gr, gc = _full_cross(grid)
    if gr is None or gc is None:
        result["errors"].append("expected exactly one full color-9 row and column")
        return result
    result.update({"h": h, "w": w, "gr": gr, "gc": gc})
    if min(gr, gc, h - gr - 1, w - gc - 1) < 3:
        result["errors"].append("every quadrant must be at least 3 cells per side")
    off_cross_nines = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 9 and r != gr and c != gc
    ]
    if off_cross_nines:
        result["errors"].append("color 9 may occur only on the splitting cross")

    tl = _quad_cells(grid, gr, gc, "TL")
    tr = _quad_cells(grid, gr, gc, "TR")
    bl = _quad_cells(grid, gr, gc, "BL")
    br = _quad_cells(grid, gr, gc, "BR")
    result.update({"tl": tl, "tr": tr, "bl": bl, "br": br})

    tl_coords = [(r, c) for r, c, _ in tl]
    tr_coords = [(r, c) for r, c, _ in tr]
    if not tl or not tr:
        result["errors"].append("TL and TR must contain the worked analogy")
    else:
        tl_colors = {v for _, _, v in tl}
        tr_colors = {v for _, _, v in tr}
        if len(tl_colors) != 1 or tr_colors != tl_colors:
            result["errors"].append("worked analogy must use one shared non-9 color")
        if not _is_filled_rectangle(tl_coords):
            result["errors"].append("TL worked-example source must be a solid rectangle")
        ntl, tl_r0, tl_c0 = _normalize(tl_coords)
        expected_tr = {(tl_r0 + r, tl_c0 + c) for r, c in _outline(ntl)}
        if set(tr_coords) != expected_tr:
            result["errors"].append("TR must be the same-offset cardinal outline of TL")

    bl_coords = [(r, c) for r, c, _ in bl]
    if bl_coords and not _connected(bl_coords):
        result["errors"].append("BL nonzero union must be 4-connected")
    if len({v for _, _, v in bl}) > 2:
        result["errors"].append("BL may use at most two nonzero colors")

    if not bl:
        result.update(
            {
                "source_multicolor": False,
                "clipped": False,
                "br_prefilled": bool(br),
                "has_interior": False,
            }
        )
        texture = "no_shape"
    else:
        normalized, rmin, cmin = _normalize(bl_coords)
        result.update(
            {
                "bl_normalized": normalized,
                "bl_rmin": rmin,
                "bl_cmin": cmin,
                "bl_outline": _outline(normalized),
            }
        )
        sh = max(r for r, _ in normalized) + 1
        sw = max(c for _, c in normalized) + 1
        source_multicolor = len({v for _, _, v in bl}) > 1
        clipped = cmin + sw > w - gc - 1
        br_prefilled = bool(br)
        has_interior = len(_outline(normalized)) < len(normalized)
        result.update(
            {
                "shape_h": sh,
                "shape_w": sw,
                "source_multicolor": source_multicolor,
                "clipped": clipped,
                "br_prefilled": br_prefilled,
                "has_interior": has_interior,
            }
        )

        # The four ordinary profiles are intentionally overlapping feature
        # bundles.  These exact signatures keep the axis observable while each
        # causal witness appears twice across the four-slot schedule.
        if source_multicolor and br_prefilled and not clipped:
            texture = "multicolor"
        elif not source_multicolor and br_prefilled and clipped:
            texture = "br_decoy"
        elif source_multicolor and not br_prefilled and clipped:
            texture = "clip"
        elif (
            not source_multicolor
            and not br_prefilled
            and not clipped
            and _is_filled_rectangle(normalized)
            and sh >= 3
            and sw >= 3
        ):
            texture = "solid"
        elif source_multicolor:
            texture = "multicolor"
        elif clipped:
            texture = "clip"
        elif br_prefilled:
            texture = "br_decoy"
        else:
            texture = "plain"
    result["texture"] = texture
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete teaching grammar, including the worked analogy."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict:
    """Return exact declared-axis values recoverable from the emitted grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["h"],
        "grid_w": analysis["w"],
        "texture": analysis["texture"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the narrow canonical analogy manifold, not all teaching variants."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    h, w, gr, gc = analysis["h"], analysis["w"], analysis["gr"], analysis["gc"]
    if (h, w) not in {(9, 9), (11, 11)}:
        reasons.append("dimensions are outside the canonical 9x9/11x11 profiles")
    if (gr, gc) != (h // 2, w // 2):
        reasons.append("cross is not centered as in the canonical examples")
    if analysis["texture"] != "solid":
        reasons.append("canonical query source is a one-color solid rectangle with empty BR")
    if analysis["bl"]:
        colors = {v for _, _, v in analysis["bl"]}
        if len(colors) != 1:
            reasons.append("canonical BL source uses one color")
        if analysis.get("shape_w") != 3 or analysis.get("shape_h") not in {3, 4}:
            reasons.append("canonical BL rectangle is 3 columns by 3 or 4 rows")
    return reasons


def _witness_solid(grid) -> bool:
    a = _analyze(grid)
    return (
        not a["errors"]
        and a.get("has_interior", False)
        and _mode_differs(grid, "whole_shape")
    )


def _witness_multicolor_per_cell(grid) -> bool:
    a = _analyze(grid)
    if a["errors"] or not a.get("source_multicolor", False):
        return False
    colors = [v for _, _, v in a["bl"]]
    return (
        len(set(colors)) == 2
        and colors[0] != Counter(colors).most_common(1)[0][0]
        and _mode_differs(grid, "per_cell_outline")
    )


def _witness_multicolor_modal(grid) -> bool:
    a = _analyze(grid)
    if a["errors"] or not a.get("source_multicolor", False):
        return False
    colors = [v for _, _, v in a["bl"]]
    return (
        len(set(colors)) == 2
        and colors[0] != Counter(colors).most_common(1)[0][0]
        and _mode_differs(grid, "modal_color_outline")
    )


def _witness_br_decoy(grid) -> bool:
    a = _analyze(grid)
    return (
        not a["errors"]
        and a.get("br_prefilled", False)
        and len(a["br"]) >= 2
        and _mode_differs(grid, "require_empty_br")
    )


def _witness_clip(grid) -> bool:
    a = _analyze(grid)
    return (
        not a["errors"]
        and a.get("clipped", False)
        and _mode_differs(grid, "require_fit")
    )


def _witness_count_bar(grid) -> bool:
    a = _analyze(grid)
    return (
        not a["errors"]
        and a["texture"] != "no_shape"
        and _mode_differs(grid, "count_bar")
    )


def _witness_copy_top_right(grid) -> bool:
    a = _analyze(grid)
    return (
        not a["errors"]
        and a["texture"] != "no_shape"
        and _mode_differs(grid, "copy_top_right")
    )


SEMANTIC_WITNESSES = {
    "solid_outline_not_whole_copy": _witness_solid,
    "multicolor_first_scan_not_per_cell": _witness_multicolor_per_cell,
    "multicolor_first_scan_not_modal": _witness_multicolor_modal,
    "pre_filled_br_collision_and_survivor": _witness_br_decoy,
    "clipped_outline_stamp": _witness_clip,
    "outline_geometry_not_count_bar": _witness_count_bar,
    "bottom_left_source_not_fixed_top_right": _witness_copy_top_right,
}


def _draw_dimension(ctx, label: str, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 8, 20)
    return ctx.draw_int(label, default_lo, default_hi)


def _grow(rng, k: int, max_h: int, max_w: int) -> list[tuple[int, int]]:
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(500):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = _DIR4[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    normalized, _, _ = _normalize(cells)
    return normalized


def _grow_nonrectangle(rng, max_h: int, max_w: int) -> list[tuple[int, int]]:
    for _ in range(120):
        shape = _grow(rng, rng.randint(4, min(8, max_h * max_w - 1)), max_h, max_w)
        if len(shape) >= 4 and not _is_filled_rectangle(shape):
            return shape
    # Deterministic boundary fallback; fits every >=3x3 quadrant.
    return [(0, 0), (0, 1), (0, 2), (1, 0)]


def _add_worked_demo(
    grid, gr: int, gc: int, rng, *, excluded=(), color: int | None = None
) -> int:
    """Paint a guaranteed 3x3 solid -> ring analogy in TL/TR."""
    right_w = len(grid[0]) - gc - 1
    r0 = rng.randint(0, gr - 3)
    c0 = rng.randint(0, min(gc, right_w) - 3)
    colors = [color for color in _COLORS if color not in set(excluded)] or list(_COLORS)
    if color is None:
        color = rng.choice(colors)
    elif color not in colors:
        raise ValueError("forced worked-example color conflicts with source colors")
    rect = [(r, c) for r in range(3) for c in range(3)]
    for r, c in rect:
        grid[r0 + r][c0 + c] = color
    for r, c in _outline(rect):
        grid[r0 + r][gc + 1 + c0 + c] = color
    return color


def _mirror(grid, *, mode: str = "outline"):
    """Pure Python semantic mirror used only for validation/candidate audits."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    if not analysis["bl"]:
        return [row[:] for row in grid]
    gr, gc = analysis["gr"], analysis["gc"]
    br_w = analysis["w"] - gc - 1
    source = analysis["bl"]
    first_color = source[0][2]
    normalized = analysis["bl_normalized"]
    rmin, cmin = analysis["bl_rmin"], analysis["bl_cmin"]
    outline = analysis["bl_outline"]

    if mode == "whole_shape":
        stamp = normalized
    else:
        stamp = outline
    if mode == "require_empty_br" and analysis["br"]:
        return [row[:] for row in grid]
    if mode == "require_fit" and any(cmin + c >= br_w for _, c in stamp):
        return [row[:] for row in grid]

    source_color_by_coord = {
        (r - rmin, c - cmin): value for r, c, value in source
    }
    modal_color = Counter(value for _, _, value in source).most_common(1)[0][0]
    out = [row[:] for row in grid]
    for index, (r, c) in enumerate(stamp):
        rr, cc = gr + 1 + rmin + r, gc + 1 + cmin + c
        if not (0 <= rr < len(out) and 0 <= cc < len(out[0])):
            continue
        if mode == "per_cell_outline":
            color = source_color_by_coord[(r, c)]
        elif mode == "modal_color_outline":
            color = modal_color
        elif mode == "count_bar":
            continue
        else:
            color = first_color
        out[rr][cc] = color
    if mode == "count_bar":
        count = sum(cmin + c < br_w for _, c in outline)
        cells = [
            (r, c)
            for r in range(gr + 1, len(out))
            for c in range(gc + 1, len(out[0]))
        ]
        for r, c in cells[:count]:
            out[r][c] = first_color
    if mode == "copy_top_right":
        # Undo the official stamp, then copy the worked answer into BR at origin.
        out = [row[:] for row in grid]
        for r, c, _ in analysis["tr"]:
            rr, cc = gr + 1 + r, gc + 1 + c
            if rr < len(out) and cc < len(out[0]):
                out[rr][cc] = first_color
    return out


def _mode_differs(grid, mode: str) -> bool:
    """Return whether one named audit mode disagrees with the intended mirror."""
    official = _mirror(grid, mode="outline")
    rival = _mirror(grid, mode=mode)
    return official is not None and rival is not None and official != rival


def _copy_whole_bl_shape(grid):
    return _mirror(grid, mode="whole_shape")


def _preserve_per_cell_bl_colors(grid):
    return _mirror(grid, mode="per_cell_outline")


def _use_modal_bl_color(grid):
    return _mirror(grid, mode="modal_color_outline")


def _stamp_only_into_empty_br(grid):
    return _mirror(grid, mode="require_empty_br")


def _refuse_clipped_stamps(grid):
    return _mirror(grid, mode="require_fit")


def _encode_outline_count_only(grid):
    return _mirror(grid, mode="count_bar")


def _copy_worked_top_right_answer(grid):
    return _mirror(grid, mode="copy_top_right")


SEMANTIC_RIVALS = {
    "copy_whole_bl_shape": _copy_whole_bl_shape,
    "preserve_per_cell_bl_colors": _preserve_per_cell_bl_colors,
    "use_modal_bl_color": _use_modal_bl_color,
    "stamp_only_into_empty_br": _stamp_only_into_empty_br,
    "refuse_clipped_stamps": _refuse_clipped_stamps,
    "encode_outline_count_only": _encode_outline_count_only,
    "copy_worked_top_right_answer": _copy_worked_top_right_answer,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "preserve_per_cell_bl_colors",
        "use_modal_bl_color",
        "stamp_only_into_empty_br",
        "refuse_clipped_stamps",
    )
}
WITNESS_RIVALS = {
    "solid_outline_not_whole_copy": ["copy_whole_bl_shape"],
    "multicolor_first_scan_not_per_cell": ["preserve_per_cell_bl_colors"],
    "multicolor_first_scan_not_modal": ["use_modal_bl_color"],
    "pre_filled_br_collision_and_survivor": ["stamp_only_into_empty_br"],
    "clipped_outline_stamp": ["refuse_clipped_stamps"],
    "outline_geometry_not_count_bar": ["encode_outline_count_only"],
    "bottom_left_source_not_fixed_top_right": ["copy_worked_top_right_answer"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Falsify concrete shortcuts against the real four-demo lesson."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    official_mode = "outline"
    for index, pair in enumerate(demos):
        predicted = _mirror(pair["input"], mode=official_mode)
        if predicted != pair["output"]:
            reasons.append(f"official Python audit disagrees with demo {index}")
    query_official = _mirror(query["input"], mode=official_mode)
    if query_official != query["output"]:
        reasons.append("official Python audit disagrees with query")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            rival_query = rival(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def _canonical_profile(seed: int, sample_index: int) -> tuple[int, int] | None:
    # Every solid schedule slot is also a canonical-size anchor.  The remaining
    # three profiles retain broad dimensions and the overlapping witnesses.
    if sample_index % 4 != 0:
        return None
    return (9, 9) if (seed + sample_index // 4) % 2 == 0 else (11, 11)


def _canonical_envelope_profile(seed: int, sample_index: int) -> tuple[int, int] | None:
    """Give br_decoy slots canonical dimensions without claiming strict shape."""
    if sample_index % 4 != 2:
        return None
    return (9, 9) if (seed + sample_index // 4) % 2 == 0 else (11, 11)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-slot ordinary curriculum to the semantic gate."""
    del seed, difficulty
    return _LESSON_TEXTURES[int(sample_index) % len(_LESSON_TEXTURES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    effective = dict(overrides)
    canonical_profile = None if overrides else _canonical_profile(seed, sample_index)
    envelope_profile = (
        None if overrides else _canonical_envelope_profile(seed, sample_index)
    )
    dimension_profile = canonical_profile or envelope_profile
    if dimension_profile is not None:
        effective["grid_h"], effective["grid_w"] = dimension_profile
    effective.setdefault("texture", _LESSON_TEXTURES[sample_index % len(_LESSON_TEXTURES)])

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    texture = ctx.draw_choice("texture", _ALL_TEXTURES)
    if difficulty == "easy":
        h = _draw_dimension(ctx, "grid_h", 8, 11)
        w = _draw_dimension(ctx, "grid_w", 8, 11)
    elif difficulty == "hard":
        h = _draw_dimension(ctx, "grid_h", 13, 20)
        w = _draw_dimension(ctx, "grid_w", 13, 20)
    else:
        h = _draw_dimension(ctx, "grid_h", 9, 15)
        w = _draw_dimension(ctx, "grid_w", 9, 15)

    rng = ctx.draw_rng("layout")
    if canonical_profile is not None:
        gr, gc = h // 2, w // 2
    else:
        gr = rng.randint(3, h - 4)
        legal_cols = list(range(3, w - 3))
        if texture in ("clip", "br_decoy"):
            legal_cols = [c for c in legal_cols if c > w - c - 1]
        if not legal_cols:
            raise ValueError(f"cannot place {texture} cross in {h}x{w}")
        gc = rng.choice(legal_cols)

    bl_h, bl_w = h - gr - 1, gc
    br_w = w - gc - 1
    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[gr][c] = 9
    for r in range(h):
        grid[r][gc] = 9

    if texture == "no_shape":
        _add_worked_demo(grid, gr, gc, rng)
        return grid

    if texture in ("solid", "multicolor"):
        if canonical_profile == (9, 9):
            sh, sw, rmin, cmin = 3, 3, 0, 0
        elif canonical_profile == (11, 11):
            sh, sw = (4, 3) if (seed % 2) else (3, 3)
            rmin, cmin = (0, 0) if sh == 4 else (1, 1)
        else:
            sh = rng.randint(3, min(5, bl_h))
            sw = rng.randint(3, min(5, bl_w, br_w))
            rmin = rng.randint(0, bl_h - sh)
            cmin = rng.randint(0, min(bl_w, br_w) - sw)
        shape = [(r, c) for r in range(sh) for c in range(sw)]
    elif texture in ("clip", "br_decoy"):
        sw = rng.randint(br_w + 1, bl_w)
        sh = rng.randint(2, min(4, bl_h))
        edge = rng.choice((0, sw - 1))
        shape = [(0, c) for c in range(sw)] + [(r, edge) for r in range(1, sh)]
        rmin = rng.randint(0, bl_h - sh)
        # Leave at least two source columns visible in BR.  The clip profile is
        # also the second multicolor witness; one visible cell would make the
        # per-cell-color rival answer-equivalent on that example.
        cmin = rng.randint(0, min(bl_w - sw, br_w - 2))
    else:
        max_w = min(bl_w, br_w)
        shape = _grow_nonrectangle(rng, bl_h, max_w)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        # The lesson slots deliberately alternate origin and far-edge placements
        # so fixed-position shortcuts cannot survive all demonstrations.
        if sample_index % 2:
            rmin, cmin = bl_h - sh, max_w - sw
        else:
            rmin = rng.randint(0, bl_h - sh)
            cmin = rng.randint(0, max_w - sw)

    outline = _outline(shape)
    if texture in ("multicolor", "clip"):
        first_color, modal_color = rng.sample(_COLORS, 2)
        first_coord = min(shape)
        for r, c in shape:
            value = first_color if (r, c) == first_coord else modal_color
            grid[gr + 1 + rmin + r][cmin + c] = value
        source_color = first_color
        excluded = (first_color, modal_color)
    else:
        source_color = rng.choice(_COLORS)
        excluded = (source_color,)
        for r, c in shape:
            grid[gr + 1 + rmin + r][cmin + c] = source_color

    worked_color = None
    if texture in ("multicolor", "br_decoy"):
        stamp_abs = {
            (gr + 1 + rmin + r, gc + 1 + cmin + c)
            for r, c in outline
            if cmin + c < br_w
        }
        br_cells = [
            (r, c)
            for r in range(gr + 1, h)
            for c in range(gc + 1, w)
        ]
        collision = rng.choice(sorted(stamp_abs))
        survivors = [cell for cell in br_cells if cell not in stamp_abs]
        if not survivors:
            raise ValueError("br_decoy has no non-stamp survivor cell")
        survivor = rng.choice(survivors)
        decoy_color = rng.choice([c for c in _COLORS if c != source_color])
        grid[collision[0]][collision[1]] = decoy_color
        grid[survivor[0]][survivor[1]] = decoy_color
        if texture == "br_decoy":
            # Reuse the decoy color in the worked analogy.  Together with
            # {0, 9, source_color}, this gives the br_decoy envelope anchor the
            # canonical four-color palette while preserving both BR witnesses.
            worked_color = decoy_color

    _add_worked_demo(grid, gr, gc, rng, excluded=excluded, color=worked_color)

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("constructed invalid teaching grid: " + "; ".join(analysis["errors"]))
    if analysis["texture"] != texture:
        raise ValueError(
            f"texture realization mismatch: requested {texture!r}, observed {analysis['texture']!r}"
        )
    out = _mirror(grid)
    if out is None or out == grid:
        raise ValueError("ordinary texture produced no visible outline stamp")
    return grid
