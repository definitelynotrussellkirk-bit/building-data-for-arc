"""Semantic generator for ARC task ``c2f4b540f2fb``.

Two three-color L markers define independent local coordinate frames.  Cyan
points live in the source frame.  The output preserves the input and copies
exactly the source points on the maximum-local-u tier into the target frame.
All ties on that tier are copied.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.local_frame import DIR4, draw_marker_frame, frame_cells, gpos

GENERATOR_ID = "c2f4b540f2fb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2d3609bffb9d"
MIN_STRICT_FRAC = 0.9
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A zero-background grid contains a source local frame marked by colors "
    "2 (origin), 3 (+u), and 4 (+v), and a target frame marked analogously "
    "by 5, 6, and 7. Three or four cyan (8) source points lie within local "
    "radius 3. The output preserves the input and stamps into the target "
    "frame every cyan point whose source-local u coordinate is maximal. "
    "Coordinates are transferred frame-relatively, and every tie on the "
    "maximum-u tier is copied."
)

INVARIANTS = [
    "colors 2..7 occur exactly once and define two unit orthogonal local frames",
    "all input cyan cells are source-motif cells within local radius 3",
    "the motif has at least two distinct local-u levels",
    "the target cells corresponding to the maximum-u tier are blank and in bounds",
    "source and target occupied cells do not overlap",
]

COUNTER_HYPOTHESES = [
    "copy every source motif point",
    "copy the minimum-local-u tier",
    "copy the maximum- or minimum-local-v tier",
    "copy only one point when the maximum-local-u tier is tied",
    "choose the globally rightmost cyan cell instead of using source-local u",
    "copy a fixed local coordinate, fixed orientation, or fixed grid position",
]

SCENE_SIZES_BY_BAND = {
    "easy": ((11, 18), (11, 18), (12, 18), (11, 16)),
    "medium": ((11, 18), (12, 18), (13, 16), (14, 18), (11, 14)),
    "hard": ((12, 18), (14, 18), (16, 18), (16, 14), (11, 18)),
}

MOTIF_PROFILES: dict[str, tuple[tuple[int, int], ...]] = {
    # Canonical train-0 local coordinates.
    "positive_unique": ((-1, 1), (1, 2), (2, 0)),
    # Canonical train-1 local coordinates; the selected u value is zero.
    "zero_unique": ((-2, 1), (-1, 3), (0, 2)),
    # A tied maximum whose maximum local-u value is negative.
    "negative_tie": ((-3, -1), (-2, 2), (-1, -2), (-1, 1)),
    # A tied positive maximum, needed to refute one-point tie breaking.
    "positive_tie": ((-2, -2), (0, 2), (2, -1), (2, 2)),
}
FRAME_RELATIONS = ("parallel", "quarter_turn", "reflected")
LAYOUT_AXES = ("horizontal", "vertical")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed canonical-anchored choice",
        "valid": "11..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed canonical-anchored choice",
        "valid": "14..18",
    },
    "motif_profile": {
        "type": "enum",
        "default": "sample-index cycle",
        "valid": ["positive_unique", "zero_unique", "negative_tie", "positive_tie"],
    },
    "frame_relation": {
        "type": "enum",
        "default": "sample-index cycle",
        "valid": ["parallel", "quarter_turn", "reflected"],
    },
    "layout_axis": {
        "type": "enum",
        "default": "sample-index cycle",
        "valid": ["horizontal", "vertical"],
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _neg(vec: tuple[int, int]) -> tuple[int, int]:
    return -vec[0], -vec[1]


def _relation_basis(
    source_vx: tuple[int, int], source_vy: tuple[int, int], relation: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    if relation == "parallel":
        return source_vx, source_vy
    if relation == "quarter_turn":
        return source_vy, _neg(source_vx)
    if relation == "reflected":
        return source_vx, _neg(source_vy)
    raise ValueError(f"unknown frame relation: {relation!r}")


def _relation_name(
    source_vx: tuple[int, int],
    source_vy: tuple[int, int],
    target_vx: tuple[int, int],
    target_vy: tuple[int, int],
) -> str | None:
    for name in FRAME_RELATIONS:
        if _relation_basis(source_vx, source_vy, name) == (target_vx, target_vy):
            return name
    return None


def _single_color_position(grid: list[list[int]], color: int) -> tuple[int, int] | None:
    positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    return positions[0] if len(positions) == 1 else None


def _frame_from_colors(
    grid: list[list[int]], colors: tuple[int, int, int]
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]] | None:
    origin = _single_color_position(grid, colors[0])
    x_marker = _single_color_position(grid, colors[1])
    y_marker = _single_color_position(grid, colors[2])
    if origin is None or x_marker is None or y_marker is None:
        return None
    vx = x_marker[0] - origin[0], x_marker[1] - origin[1]
    vy = y_marker[0] - origin[0], y_marker[1] - origin[1]
    if vx not in DIR4 or vy not in DIR4:
        return None
    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
        return None
    return origin, vx, vy


def _lpos(
    origin: tuple[int, int],
    vx: tuple[int, int],
    vy: tuple[int, int],
    point: tuple[int, int],
) -> tuple[int, int]:
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def _profile_name(points: tuple[tuple[int, int], ...]) -> str | None:
    normalized = tuple(sorted(points))
    for name, profile in MOTIF_PROFILES.items():
        if normalized == tuple(sorted(profile)):
            return name
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    if not 11 <= h <= 16:
        errors.append(f"height must be within 11..16, found {h}")
    if not 14 <= w <= 18:
        errors.append(f"width must be within 14..18, found {w}")

    allowed = set(range(0, 9))
    extras = sorted({value for row in grid for value in row} - allowed)
    if extras:
        errors.append(f"forbidden colors present: {extras}")

    for color in range(2, 8):
        count = sum(value == color for row in grid for value in row)
        if count != 1:
            errors.append(f"marker color {color} must occur exactly once, found {count}")

    source = _frame_from_colors(grid, (2, 3, 4))
    target = _frame_from_colors(grid, (5, 6, 7))
    if source is None:
        errors.append("colors 2,3,4 do not define one unit orthogonal source frame")
    if target is None:
        errors.append("colors 5,6,7 do not define one unit orthogonal target frame")
    if source is None or target is None:
        return result

    so, svx, svy = source
    to, tvx, tvy = target
    source_frame_cells = set(frame_cells(so, svx, svy))
    target_frame_cells = set(frame_cells(to, tvx, tvy))
    if source_frame_cells & target_frame_cells:
        errors.append("source and target marker frames overlap")

    cyan_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not 3 <= len(cyan_cells) <= 4:
        errors.append(f"source motif must contain 3 or 4 cyan cells, found {len(cyan_cells)}")

    motif: list[tuple[int, int]] = []
    for point in cyan_cells:
        uv = _lpos(so, svx, svy, point)
        if max(abs(uv[0]), abs(uv[1])) > 3:
            errors.append(f"cyan cell {point} lies outside source-local radius 3")
        if point in source_frame_cells or point in target_frame_cells:
            errors.append(f"cyan cell {point} overlaps a frame marker")
        motif.append(uv)
    if len(set(motif)) != len(motif):
        errors.append("motif contains duplicate local coordinates")

    u_values = {u for u, _ in motif}
    if motif and len(u_values) < 2:
        errors.append("motif has no local-u rank contrast")

    chosen = []
    target_cells: list[tuple[int, int]] = []
    if motif:
        max_u = max(u for u, _ in motif)
        chosen = [(u, v) for u, v in motif if u == max_u]
        if len(chosen) == len(motif):
            errors.append("every motif point is on the maximum-u tier")
        for uv in chosen:
            point = gpos(to, tvx, tvy, *uv)
            target_cells.append(point)
            if not (0 <= point[0] < h and 0 <= point[1] < w):
                errors.append(f"target copy cell {point} is out of bounds")
            elif grid[point[0]][point[1]] != 0:
                errors.append(
                    f"target copy cell {point} must be blank in the input, found "
                    f"{grid[point[0]][point[1]]}"
                )

    occupied_source = source_frame_cells | set(cyan_cells)
    occupied_target = target_frame_cells | set(target_cells)
    if occupied_source & occupied_target:
        errors.append("source content overlaps target frame or selected target cells")

    relation = _relation_name(svx, svy, tvx, tvy)
    if relation is None:
        errors.append("target frame relation is outside the declared relation grammar")

    dr, dc = to[0] - so[0], to[1] - so[1]
    if dc > 0 and abs(dc) > abs(dr):
        layout_axis = "horizontal"
    elif dr > 0 and abs(dr) > abs(dc):
        layout_axis = "vertical"
    else:
        layout_axis = None
        errors.append("target origin must be observably right of or below the source origin")

    result.update(
        {
            "height": h,
            "width": w,
            "source": source,
            "target": target,
            "motif": tuple(sorted(motif)),
            "motif_profile": _profile_name(tuple(motif)),
            "chosen": tuple(sorted(chosen)),
            "target_cells": tuple(target_cells),
            "max_u": max((u for u, _ in motif), default=None),
            "frame_relation": relation,
            "layout_axis": layout_axis,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar, including rank visibility."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical-manifold check.

    The canonical examples fix the role colors and local-frame grammar but do
    not make grid size, absolute orientation, or tie cardinality semantic.
    Those lawful variations remain inside this strict manifold.
    """
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    profile = analysis["motif_profile"]
    if profile is None:
        # Canonical test input is lawful but is not one of the generator's
        # finite override profiles.  Observation is used only on generated
        # override cases, so omitting it here avoids inventing a label.
        return {
            "grid_h": analysis["height"],
            "grid_w": analysis["width"],
            "frame_relation": analysis["frame_relation"],
            "layout_axis": analysis["layout_axis"],
        }
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "motif_profile": profile,
        "frame_relation": analysis["frame_relation"],
        "layout_axis": analysis["layout_axis"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket rule is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = deepcopy(grid)
    for r, c in analysis["target_cells"]:
        out[r][c] = 8
    return out


def _selected(points: tuple[tuple[int, int], ...], mode: str) -> tuple[tuple[int, int], ...]:
    if mode == "max_u":
        value = max(u for u, _ in points)
        return tuple((u, v) for u, v in points if u == value)
    if mode == "min_u":
        value = min(u for u, _ in points)
        return tuple((u, v) for u, v in points if u == value)
    if mode == "max_v":
        value = max(v for _, v in points)
        return tuple((u, v) for u, v in points if v == value)
    if mode == "min_v":
        value = min(v for _, v in points)
        return tuple((u, v) for u, v in points if v == value)
    raise ValueError(mode)


def _paint_local_selection(grid: list[list[int]], points: tuple[tuple[int, int], ...]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = deepcopy(grid)
    to, tvx, tvy = analysis["target"]
    for uv in points:
        r, c = gpos(to, tvx, tvy, *uv)
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


def _competitor_all(grid):
    analysis = _analyze(grid)
    return _paint_local_selection(grid, analysis["motif"])


def _competitor_min_u(grid):
    analysis = _analyze(grid)
    return _paint_local_selection(grid, _selected(analysis["motif"], "min_u"))


def _competitor_max_v(grid):
    analysis = _analyze(grid)
    return _paint_local_selection(grid, _selected(analysis["motif"], "max_v"))


def _competitor_min_v(grid):
    analysis = _analyze(grid)
    return _paint_local_selection(grid, _selected(analysis["motif"], "min_v"))


def _competitor_one_max(grid):
    analysis = _analyze(grid)
    points = tuple(sorted(_selected(analysis["motif"], "max_u")))[:1]
    return _paint_local_selection(grid, points)


def _competitor_global_rightmost(grid):
    analysis = _analyze(grid)
    so, svx, svy = analysis["source"]
    cells = [(gpos(so, svx, svy, *uv), uv) for uv in analysis["motif"]]
    rightmost = max(cell[1] for cell, _ in cells)
    points = tuple(uv for cell, uv in cells if cell[1] == rightmost)
    return _paint_local_selection(grid, points)


_COMPETING_RULES: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy_all_motif": _competitor_all,
    "copy_minimum_local_u": _competitor_min_u,
    "copy_maximum_local_v": _competitor_max_v,
    "copy_minimum_local_v": _competitor_min_v,
    "copy_only_one_maximum_u_point": _competitor_one_max,
    "choose_globally_rightmost": _competitor_global_rightmost,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    episodes = list(demos) + [query]
    for i, episode in enumerate(episodes):
        label = f"demo {i}" if i < len(demos) else "query"
        errors = self_check(episode.get("input"))
        if errors:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
    if reasons:
        return reasons
    for i, demo in enumerate(demos):
        if demo.get("output") != rule_mirror(demo["input"]):
            reasons.append(f"demo {i}: output does not match the canonical rule")
    if reasons:
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query: provided output does not match the canonical rule")
    for name, competitor in _COMPETING_RULES.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != truth:
                reasons.append(
                    f"competing rule {name!r} fits every demo but predicts a different query"
                )
    return reasons


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        analysis = _analyze(grid)
        if analysis["errors"]:
            return False
        if name == "unique_maximum_u":
            return len(analysis["chosen"]) == 1
        if name == "tied_maximum_u":
            return len(analysis["chosen"]) >= 2
        if name == "negative_maximum_u":
            return analysis["max_u"] < 0
        if name == "zero_maximum_u":
            return analysis["max_u"] == 0
        if name == "positive_maximum_u":
            return analysis["max_u"] > 0
        if name == "negative_local_coordinate":
            return any(u < 0 or v < 0 for u, v in analysis["motif"])
        if name == "changed_target_basis":
            return analysis["frame_relation"] != "parallel"
        if name == "canonical_width":
            return analysis["width"] == 18
        raise ValueError(name)

    return predicate


SEMANTIC_WITNESSES = {
    name: _witness(name)
    for name in (
        "unique_maximum_u",
        "tied_maximum_u",
        "negative_maximum_u",
        "zero_maximum_u",
        "positive_maximum_u",
        "negative_local_coordinate",
        "changed_target_basis",
        "canonical_width",
    )
}


def _fits(
    h: int,
    w: int,
    origin: tuple[int, int],
    vx: tuple[int, int],
    vy: tuple[int, int],
    local_points: tuple[tuple[int, int], ...],
) -> bool:
    required = set(local_points) | {(0, 0), (1, 0), (0, 1)}
    return all(
        0 <= r < h and 0 <= c < w
        for r, c in (gpos(origin, vx, vy, u, v) for u, v in required)
    )


def _choose_frames(
    h: int,
    w: int,
    motif: tuple[tuple[int, int], ...],
    relation: str,
    layout_axis: str,
    rng: Any,
):
    chosen = _selected(motif, "max_u")
    source_options = []
    for origin_r in range(h):
        for origin_c in range(w):
            origin = (origin_r, origin_c)
            for vx in DIR4:
                for vy in DIR4:
                    if vx[0] * vy[0] + vx[1] * vy[1] != 0:
                        continue
                    if _fits(h, w, origin, vx, vy, motif):
                        source_options.append((origin, vx, vy))
    rng.shuffle(source_options)
    for source in source_options:
        so, svx, svy = source
        tvx, tvy = _relation_basis(svx, svy, relation)
        source_cells = set(frame_cells(so, svx, svy)) | {
            gpos(so, svx, svy, *uv) for uv in motif
        }
        target_options = []
        for tr in range(h):
            for tc in range(w):
                to = (tr, tc)
                dr, dc = tr - so[0], tc - so[1]
                if layout_axis == "horizontal":
                    if not (dc > 0 and abs(dc) > abs(dr)):
                        continue
                elif layout_axis == "vertical":
                    if not (dr > 0 and abs(dr) > abs(dc)):
                        continue
                else:
                    raise ValueError(f"unknown layout_axis: {layout_axis!r}")
                if not _fits(h, w, to, tvx, tvy, chosen):
                    continue
                target_cells = set(frame_cells(to, tvx, tvy)) | {
                    gpos(to, tvx, tvy, *uv) for uv in chosen
                }
                if source_cells & target_cells:
                    continue
                target_options.append((to, tvx, tvy))
        if target_options:
            return source, rng.choice(target_options)
    raise ValueError(
        "no non-overlapping frame placement for "
        f"{h}x{w}, motif={motif}, relation={relation}, layout={layout_axis}"
    )


def _draw_dimensions(ctx, band: str, overrides: dict[str, Any]) -> tuple[int, int]:
    if "grid_h" in overrides:
        h = ctx.draw_int("grid_h", 11, 16)
    else:
        h = ctx.draw_choice("grid_h", tuple(size[0] for size in SCENE_SIZES_BY_BAND[band]))
    if "grid_w" in overrides:
        w = ctx.draw_int("grid_w", 14, 18)
    else:
        w = ctx.draw_choice("grid_w", tuple(size[1] for size in SCENE_SIZES_BY_BAND[band]))
    return h, w


def _scheduled_choice(
    ctx,
    label: str,
    choices: tuple[str, ...],
    scheduled: str,
    explicit_overrides: dict[str, Any],
) -> str:
    if label not in explicit_overrides:
        # Preserve full draw provenance while making consecutive sample indices
        # a deterministic teaching schedule rather than a probabilistic hope.
        ctx.overrides[label] = scheduled
    return ctx.draw_choice(label, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=dict(overrides),
    )
    h, w = _draw_dimensions(ctx, band, overrides)
    motif_names = tuple(MOTIF_PROFILES)
    motif_profile = _scheduled_choice(
        ctx,
        "motif_profile",
        motif_names,
        motif_names[int(sample_index) % len(motif_names)],
        overrides,
    )
    relation = _scheduled_choice(
        ctx,
        "frame_relation",
        FRAME_RELATIONS,
        FRAME_RELATIONS[(int(sample_index) // len(motif_names)) % len(FRAME_RELATIONS)],
        overrides,
    )
    layout_axis = _scheduled_choice(
        ctx,
        "layout_axis",
        LAYOUT_AXES,
        LAYOUT_AXES[
            (int(sample_index) // (len(motif_names) * len(FRAME_RELATIONS)))
            % len(LAYOUT_AXES)
        ],
        overrides,
    )
    motif = MOTIF_PROFILES[motif_profile]
    source, target = _choose_frames(
        h, w, motif, relation, layout_axis, ctx.draw_rng("placement")
    )
    so, svx, svy = source
    to, tvx, tvy = target
    grid = full_grid(h, w, 0)
    draw_marker_frame(grid, so, svx, svy, (2, 3, 4))
    draw_marker_frame(grid, to, tvx, tvy, (5, 6, 7))
    for uv in motif:
        r, c = gpos(so, svx, svy, *uv)
        grid[r][c] = 8
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid


def mutation_fixtures():
    """Task-specific structural near-misses that self_check must reject."""
    base = generate(910_001, 3, difficulty="medium")
    analysis = _analyze(base)
    fixtures = []

    missing_axis = deepcopy(base)
    r, c = _single_color_position(missing_axis, 3)
    missing_axis[r][c] = 0
    fixtures.append(("missing_source_u_marker", missing_axis))

    duplicate_marker = deepcopy(base)
    r, c = _single_color_position(duplicate_marker, 6)
    duplicate_marker[r][c] = 5
    fixtures.append(("duplicate_target_origin_color", duplicate_marker))

    outside_radius = deepcopy(base)
    first_cyan = next(
        (r, c)
        for r, row in enumerate(outside_radius)
        for c, value in enumerate(row)
        if value == 8
    )
    outside_radius[first_cyan[0]][first_cyan[1]] = 0
    so, svx, svy = analysis["source"]
    candidate = gpos(so, svx, svy, 4, 0)
    if not (0 <= candidate[0] < len(base) and 0 <= candidate[1] < len(base[0])):
        candidate = (0, 0)
    outside_radius[candidate[0]][candidate[1]] = 8
    fixtures.append(("motif_outside_local_radius", outside_radius))

    prefilled_target = deepcopy(base)
    r, c = analysis["target_cells"][0]
    prefilled_target[r][c] = 8
    fixtures.append(("selected_target_cell_prefilled", prefilled_target))

    no_rank = deepcopy(base)
    for r, row in enumerate(no_rank):
        for c, value in enumerate(row):
            if value == 8:
                no_rank[r][c] = 0
    to_paint = ((1, -2), (1, 0), (1, 2))
    for uv in to_paint:
        r, c = gpos(so, svx, svy, *uv)
        if 0 <= r < len(no_rank) and 0 <= c < len(no_rank[0]) and no_rank[r][c] == 0:
            no_rank[r][c] = 8
    fixtures.append(("motif_without_u_rank_contrast", no_rank))
    return fixtures
