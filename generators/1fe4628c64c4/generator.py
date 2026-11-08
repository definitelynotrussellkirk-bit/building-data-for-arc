"""Generator for ARC task 34cfa167 / content hash 1fe4628c64c4.

Two same-size blue anchor squares mark opposite corners of a rectangular
truss.  Four bars around the upper-left anchor encode the top, horizontal,
side, and inner colors.  The output rebuilds the complete four-corner truss
with period-four horizontal and vertical patterns.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "1fe4628c64c4"
TASK_ID = GENERATOR_ID
RULE_HASH = "f16f8c2a4341"
# 4.0.0: restore the canonical 1..4 anchor sizes and bar-shaped clue grammar;
# link inner==horizontal; add deterministic canonical-profile scheduling,
# exact observable overrides, strict semantic witnesses/rivals, and a
# mutation-sensitive structural analyzer shared by self_check and tests.
VERSION = "4.0.0"

SUMMARY = (
    "A modal-background grid contains two solid blue square anchors of size "
    "1..4, with the second strictly below-right.  Two vertical clue bars to "
    "the right of the first anchor encode the top and horizontal-band colors; "
    "two horizontal clue bars below it encode the side and inner-rung colors, "
    "with the inner color equal to the horizontal-band color.  Rebuild the "
    "four-corner rectangular truss: solid outer chords, period-four dashed "
    "anchor bands, and period-four side rails/rungs."
)

INVARIANTS = [
    "the modal color is the background and the grid palette has exactly five colors",
    "color 1 forms exactly two same-size solid square anchors of size 1..4",
    "the lower-right anchor leaves one-cell room for the bottom chord and right rail",
    "four size-matched clue bars occupy the canonical adjacent / one-gap offsets",
    "the inner clue equals the horizontal clue; all other semantic role colors differ",
    "both frame gaps are at least four cells so every period-four phase is visible",
]

# Four consecutive sample indexes cover all four anchor sizes.  Eight cover
# both exact canonical profiles and expanded profiles for every size.
SCENE_PROFILES = (
    "canonical_s1",
    "canonical_s2",
    "canonical_s3",
    "canonical_s4",
    "expanded_s1",
    "expanded_s2",
    "expanded_s3",
    "expanded_s4",
)
SCENE_SCHEDULE = SCENE_PROFILES
CANONICAL_LAYOUTS = {
    1: (19, 16),
    2: (18, 22),
    3: (24, 26),
    4: (30, 30),
}

# (background, anchor, top, horizontal/inner, side).  The first four are the
# four public palettes; the rest are color-permuted lawful augmentations.
PALETTE_PROFILES = {
    "canonical_train0": (0, 1, 4, 2, 8),
    "canonical_train1": (4, 1, 2, 8, 3),
    "canonical_test0": (0, 1, 2, 8, 4),
    "canonical_test1": (8, 1, 3, 6, 4),
    "aug_0": (0, 1, 5, 7, 9),
    "aug_1": (7, 1, 9, 2, 6),
    "aug_2": (0, 1, 4, 7, 2),
    "aug_3": (6, 1, 8, 3, 5),
}
PALETTE_SCHEDULE = tuple(PALETTE_PROFILES)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index schedule covering canonical_s1..s4 and expanded_s1..s4",
        "valid": "canonical_s1|canonical_s2|canonical_s3|canonical_s4|expanded_s1|expanded_s2|expanded_s3|expanded_s4",
    },
    "palette_profile": {
        "type": "str",
        "default": "sample_index schedule covering four canonical and four augmented palettes",
        "valid": "canonical_train0|canonical_train1|canonical_test0|canonical_test1|aug_0|aug_1|aug_2|aug_3",
    },
    "anchor_r": {"type": "int", "default": "keyed 1..4", "valid": "1..4"},
    "anchor_c": {"type": "int", "default": "keyed 1..4", "valid": "1..4"},
}

# Every declared axis combination is supported.  Declaring the empty matrix
# opts the v7 override checker into strict mode rather than the legacy warning
# policy.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], index: int) -> str:
    """Consume an exact override or record the deterministic schedule value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (options[index % len(options)],))


def _expanded_dims(ctx, size: int, difficulty: str | None) -> tuple[int, int]:
    """Draw non-canonical dimensions while keeping every axis combination valid."""
    if difficulty == "easy":
        lo, hi = 16, 22
    elif difficulty == "hard":
        lo, hi = 24, 30
    else:
        lo, hi = 18, 28
    # Size four needs at least 18 cells to support anchor_r/c=4, four visible
    # phases, and the outside chord/rail.  The other sizes also use >=16.
    lo = max(lo, 18 if size == 4 else 16)
    h = ctx.draw_int("expanded_h", lo, hi)
    w = ctx.draw_int("expanded_w", lo, hi)
    canonical = CANONICAL_LAYOUTS[size]
    if (h, w) == canonical:
        # Deterministic one-cell nudge, still inside 16..30 and never changing
        # a declared exact axis.
        w = w + 1 if w < hi else w - 1
    return h, w


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, int(sample_index)
    )
    palette_profile = _scheduled_choice(
        ctx, "palette_profile", PALETTE_SCHEDULE, int(sample_index)
    )

    size = int(scene_profile.rsplit("s", 1)[1])
    if scene_profile.startswith("canonical_"):
        h, w = CANONICAL_LAYOUTS[size]
    else:
        h, w = _expanded_dims(ctx, size, difficulty)

    ar = ctx.draw_int("anchor_r", 1, 4)
    ac = ctx.draw_int("anchor_c", 1, 4)
    min_br = ar + size + 4
    min_bc = ac + size + 4
    max_br = h - size - 1
    max_bc = w - size - 1
    if min_br > max_br or min_bc > max_bc:
        raise ValueError(
            "scene_profile, anchor_r, and anchor_c leave insufficient room "
            "for four period phases and the outside chord/rail"
        )
    br = ctx.draw_int("second_anchor_r", min_br, max_br)
    bc = ctx.draw_int("second_anchor_c", min_bc, max_bc)

    bg, anchor, top, horiz, side = PALETTE_PROFILES[palette_profile]
    g = full_grid(h, w, bg)
    draw_rect(g, ar, ac, size, size, anchor)
    draw_rect(g, br, bc, size, size, anchor)

    # Canonical clue grammar: size-high vertical bars immediately/right-with-
    # one-gap, and size-wide horizontal bars immediately/below-with-one-gap.
    draw_rect(g, ar, ac + size, size, 1, top)
    draw_rect(g, ar, ac + size + 2, size, 1, horiz)
    draw_rect(g, ar + size, ac, 1, size, side)
    draw_rect(g, ar + size + 2, ac, 1, size, horiz)
    return g


def _components(grid: list[list[int]], bg: int) -> dict[int, list[set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    by_color: dict[int, list[set[tuple[int, int]]]] = {}
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == bg or (r, c) in seen:
                continue
            comp: set[tuple[int, int]] = set()
            q = deque([(r, c)])
            seen.add((r, c))
            while q:
                rr, cc = q.popleft()
                comp.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            by_color.setdefault(color, []).append(comp)
    return by_color


def _bbox(comp: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def _solid_rect(comp: set[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    r1, c1, r2, c2 = _bbox(comp)
    if len(comp) != (r2 - r1 + 1) * (c2 - c1 + 1):
        return None
    return r1, c1, r2, c2


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list grid"], "facts": {}}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged or non-list grid"], "facts": {}}
    if not (1 <= h <= 30 and 1 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} outside ARC bounds")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or not (0 <= v <= 9) for v in flat):
        errors.append("grid contains a non-integer or out-of-range color")
        return {"errors": errors, "facts": {}}
    counts = Counter(flat)
    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        errors.append("background mode is tied")
    bg = ranked[0][0]
    components = _components(grid, bg)

    # Match the Racket rule's color-order choice, then enforce the canonical
    # square/two-object specialization instead of accepting arbitrary rects.
    anchor_color = None
    anchor_rects: list[tuple[int, int, int, int]] = []
    for color in sorted(components):
        solids = [rect for comp in components[color] if (rect := _solid_rect(comp))]
        has_pair = any(
            i != j
            and (a[2] - a[0], a[3] - a[1]) == (b[2] - b[0], b[3] - b[1])
            for i, a in enumerate(solids)
            for j, b in enumerate(solids)
        )
        if has_pair:
            anchor_color = color
            anchor_rects = sorted(solids)
            break
    if anchor_color is None:
        return {"errors": errors + ["no color has two same-size solid anchor objects"], "facts": {}}
    if anchor_color != 1:
        errors.append(f"anchor color must be 1, observed {anchor_color}")
    if len(anchor_rects) != 2:
        errors.append(f"anchor color must form exactly two solid objects, observed {len(anchor_rects)}")
        return {"errors": errors, "facts": {}}
    a, b = anchor_rects
    ah, aw = a[2] - a[0] + 1, a[3] - a[1] + 1
    bh, bw = b[2] - b[0] + 1, b[3] - b[1] + 1
    if ah != aw or bh != bw or (ah, aw) != (bh, bw) or not (1 <= ah <= 4):
        errors.append(f"anchors must be equal squares of size 1..4, observed {ah}x{aw} and {bh}x{bw}")
    size = ah
    ar, ac, _, _ = a
    br, bc, _, _ = b
    if not (br > ar and bc > ac):
        errors.append("second anchor must be strictly below-right of the first")
    if ar < 1 or ac < 1 or br + size >= h or bc + size >= w:
        errors.append("anchors must leave room for outside top/bottom chords and side rails")
    if br - (ar + size) < 4 or bc - (ac + size) < 4:
        errors.append("anchor gaps must expose all four horizontal and vertical phases")

    needed = [
        (ar, ac + size),
        (ar, ac + size + 2),
        (ar + size, ac),
        (ar + size + 2, ac),
    ]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in needed):
        errors.append("canonical clue bars do not fit")
        return {"errors": errors, "facts": {}}

    top = grid[ar][ac + size]
    horiz = grid[ar][ac + size + 2]
    side = grid[ar + size][ac]
    inner = grid[ar + size + 2][ac]
    role_colors = (bg, anchor_color, top, horiz, side)
    if len(set(role_colors)) != 5:
        errors.append(f"background/anchor/top/horizontal/side colors must be distinct: {role_colors}")
    if inner != horiz:
        errors.append(f"inner clue must equal horizontal clue ({horiz}), observed {inner}")

    expected_non_bg: set[tuple[int, int]] = set()
    for rr, cc in ((ar, ac), (br, bc)):
        expected_non_bg.update(
            (rr + dr, cc + dc) for dr in range(size) for dc in range(size)
        )
    top_cells = {(ar + dr, ac + size) for dr in range(size)}
    horiz_cells = {(ar + dr, ac + size + 2) for dr in range(size)}
    side_cells = {(ar + size, ac + dc) for dc in range(size)}
    inner_cells = {(ar + size + 2, ac + dc) for dc in range(size)}
    expected_non_bg |= top_cells | horiz_cells | side_cells | inner_cells

    def _uniform(cells, color, name):
        if any(grid[r][c] != color for r, c in cells):
            errors.append(f"{name} clue must be a full size-{size} bar of color {color}")

    _uniform(top_cells, top, "top")
    _uniform(horiz_cells, horiz, "horizontal")
    _uniform(side_cells, side, "side")
    _uniform(inner_cells, inner, "inner")
    if any(grid[ar + dr][ac + size + 1] != bg for dr in range(size)):
        errors.append("vertical clue bars must be separated by one background column")
    if any(grid[ar + size + 1][ac + dc] != bg for dc in range(size)):
        errors.append("horizontal clue bars must be separated by one background row")

    actual_non_bg = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != bg}
    extras = actual_non_bg - expected_non_bg
    missing = expected_non_bg - actual_non_bg
    if extras:
        errors.append(f"unexpected non-background cells outside anchors/clues: {len(extras)}")
    if missing:
        errors.append(f"missing anchor/clue cells: {len(missing)}")
    if len(set(flat)) != 5:
        errors.append(f"grid palette must contain exactly five colors, observed {len(set(flat))}")

    facts = {
        "height": h,
        "width": w,
        "background": bg,
        "anchor_color": anchor_color,
        "top_color": top,
        "horizontal_color": horiz,
        "side_color": side,
        "inner_color": inner,
        "anchor_size": size,
        "anchor_r": ar,
        "anchor_c": ac,
        "second_anchor_r": br,
        "second_anchor_c": bc,
        "vertical_gap": br - (ar + size),
        "horizontal_gap": bc - (ac + size),
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, off-manifold, or rule-hiding scenes."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for axis in AXES:
        if axis in requested and requested[axis] is not None and observed.get(axis) != requested[axis]:
            errors.append(
                f"{axis} requested {requested[axis]!r}, observed {observed.get(axis)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator deliberately stays on the exact task-linked manifold."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    f = analysis["facts"]
    size = f["anchor_size"]
    dims = (f["height"], f["width"])
    scene = (
        f"canonical_s{size}"
        if dims == CANONICAL_LAYOUTS[size]
        else f"expanded_s{size}"
    )
    palette_tuple = (
        f["background"],
        f["anchor_color"],
        f["top_color"],
        f["horizontal_color"],
        f["side_color"],
    )
    palette = next(
        (name for name, values in PALETTE_PROFILES.items() if values == palette_tuple),
        None,
    )
    if palette is None:
        return {}
    return {
        "scene_profile": scene,
        "palette_profile": palette,
        "anchor_r": f["anchor_r"],
        "anchor_c": f["anchor_c"],
    }


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    f = analysis["facts"]
    return {
        **observe_overrides(grid),
        "height": f["height"],
        "width": f["width"],
        "anchor_size": f["anchor_size"],
        "vertical_gap": f["vertical_gap"],
        "horizontal_gap": f["horizontal_gap"],
        "background_is_zero": f["background"] == 0,
        "strict_canonical_like": True,
    }


def _paint_rect(g, r1, c1, r2, c2, color):
    h, w = len(g), len(g[0])
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if 0 <= r < h and 0 <= c < w:
                g[r][c] = color


def _build_output(grid, *, inner_override=None, solid_horizontal=False, solid_sides=False):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    f = analysis["facts"]
    h, w = f["height"], f["width"]
    bg = f["background"]
    anchor = f["anchor_color"]
    top = f["top_color"]
    horiz = f["horizontal_color"]
    side = f["side_color"]
    inner = f["inner_color"] if inner_override is None else inner_override
    size = f["anchor_size"]
    ar, ac = f["anchor_r"], f["anchor_c"]
    br, bc = f["second_anchor_r"], f["second_anchor_c"]
    ar2, ac2 = ar + size - 1, ac + size - 1
    br2, bc2 = br + size - 1, bc + size - 1
    gap_c1, gap_c2 = ac2 + 1, bc - 1

    out = full_grid(h, w, bg)
    _paint_rect(out, ar - 1, gap_c1, ar - 1, gap_c2, top)
    _paint_rect(out, br2 + 1, gap_c1, br2 + 1, gap_c2, top)
    for r in list(range(ar, ar2 + 1)) + list(range(br, br2 + 1)):
        for c in range(gap_c1, gap_c2 + 1):
            if solid_horizontal:
                out[r][c] = top
            else:
                phase = (c - gap_c1) % 4
                out[r][c] = top if phase == 0 else horiz if phase == 2 else bg
    for rr, cc in ((ar, ac), (ar, bc), (br, ac), (br, bc)):
        _paint_rect(out, rr, cc, rr + size - 1, cc + size - 1, anchor)
    for r in range(ar2 + 1, br):
        phase = (r - (ar2 + 1)) % 4
        if solid_sides or phase == 0:
            _paint_rect(out, r, ac - 1, r, ac2, side)
            _paint_rect(out, r, bc, r, bc2 + 1, side)
        elif phase == 2:
            _paint_rect(out, r, ac - 1, r, ac - 1, side)
            _paint_rect(out, r, ac, r, ac2, inner)
            _paint_rect(out, r, bc, r, bc2, inner)
            _paint_rect(out, r, bc2 + 1, r, bc2 + 1, side)
        else:
            out[r][ac - 1] = side
            out[r][bc2 + 1] = side
    return out


def rule_mirror(grid):
    """Pure Python test mirror; the canonical Racket program remains authority."""
    return _build_output(grid)


def _identity(grid):
    return deepcopy(grid)


def _solid_horizontal_rival(grid):
    return _build_output(grid, solid_horizontal=True)


def _solid_side_rival(grid):
    return _build_output(grid, solid_sides=True)


def _inner_uses_top_rival(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    return _build_output(grid, inner_override=analysis["facts"]["top_color"])


def _zero_background_rival(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    out = _build_output(grid)
    bg = analysis["facts"]["background"]
    if bg == 0:
        return out
    return [[0 if v == bg else v for v in row] for row in out]


def _fixed_size_two_rival(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    return _build_output(grid) if analysis["facts"]["anchor_size"] == 2 else deepcopy(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "copy_input": _identity,
    "solid_horizontal_gap": _solid_horizontal_rival,
    "solid_side_rows": _solid_side_rival,
    "inner_uses_top": _inner_uses_top_rival,
    "zero_background_canvas": _zero_background_rival,
    "fixed_anchor_size_two": _fixed_size_two_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_size(size: int):
    def predicate(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and analysis["facts"]["anchor_size"] == size

    return predicate


def _witness_nonzero_bg(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["facts"]["background"] != 0


def _witness_scene(prefix: str):
    def predicate(grid) -> bool:
        return observe_overrides(grid).get("scene_profile", "").startswith(prefix)

    return predicate


def _witness_all_phases(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and min(
        analysis["facts"]["vertical_gap"], analysis["facts"]["horizontal_gap"]
    ) >= 4


def _witness_linked_clues(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and (
        analysis["facts"]["inner_color"] == analysis["facts"]["horizontal_color"]
        and analysis["facts"]["top_color"] != analysis["facts"]["horizontal_color"]
    )


SEMANTIC_WITNESSES = {
    "anchor_size_one": _witness_size(1),
    "anchor_size_four": _witness_size(4),
    "nonzero_background": _witness_nonzero_bg,
    "canonical_dimensions": _witness_scene("canonical_"),
    "expanded_dimensions": _witness_scene("expanded_"),
    "both_period_four_cycles_visible": _witness_all_phases,
    "inner_equals_horizontal_not_top": _witness_linked_clues,
}
WITNESS_RIVALS = {
    "anchor_size_one": ["fixed_anchor_size_two"],
    "anchor_size_four": ["fixed_anchor_size_two"],
    "nonzero_background": ["zero_background_canvas"],
    "canonical_dimensions": ["copy_input"],
    "expanded_dimensions": ["copy_input"],
    "both_period_four_cycles_visible": ["solid_horizontal_gap", "solid_side_rows"],
    "inner_equals_horizontal_not_top": ["inner_uses_top"],
}


def _pair_errors(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label}: pair must contain input and output"]
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return [f"{label}: {error}" for error in analysis["errors"]]
    expected = rule_mirror(pair["input"])
    if pair["output"] != expected:
        return [f"{label}: output does not match the rectangular-truss rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    for i, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {i}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    sizes = {_analyze(pair["input"])["facts"]["anchor_size"] for pair in demos}
    if sizes != {1, 2, 3, 4}:
        reasons.append(f"demos must cover anchor sizes 1..4, observed {sorted(sizes)}")
    bg_zero = {_analyze(pair["input"])["facts"]["background"] == 0 for pair in demos}
    if bg_zero != {False, True}:
        reasons.append("demos must contain both zero and nonzero modal backgrounds")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"named competitor {name!r} fits every demo but changes the query")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return int(sample_index) % len(SCENE_SCHEDULE)


SCHEDULE_PROFILES = tuple(range(len(SCENE_SCHEDULE)))
