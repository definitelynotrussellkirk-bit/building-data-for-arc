"""Generator for ARC task 0a9e3d364bb3 / original 58743b76.

A 2x2 key occupies one corner and an (h-2)x(w-2) body occupies the
opposite corner, leaving an L-shaped separator of colour 8.  The first
non-key, non-0/8 body colour in reading order is the marker colour.  Marker
cells are recoloured by their body-bounding-box quadrant using the four key
cells (TL/TR/BL/BR); exact midpoint cells belong to the bottom/right side.
Later body colours are distractors and stay unchanged.

The four-profile curriculum deliberately separates three canonical-fitting
rivals: marker colour must occur in the key, every coloured body cell should
be recoloured, and exact midpoint cells belong to top/left.  One profile in
every four is an exact empirical canonical morphology anchor.  Lessons request
seven demonstrations plus one query, covering two full profile cycles; every
query rotation therefore leaves at least one demonstration of each profile.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a9e3d364bb3"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "debd91c13f07"
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A 2x2 corner key maps the first non-key body marker colour to the four "
    "quadrants of the opposite body rectangle. Exact midpoint cells use the "
    "bottom/right key entry. A later second body colour, when present, is a "
    "distractor and remains unchanged."
)

INVARIANTS = [
    "exactly one corner candidate satisfies the authority's top-edge key test",
    "the full 2x2 key uses four distinct non-0/8 colours",
    "all non-key cells outside the opposite (h-2)x(w-2) body rectangle are 8",
    "the body contains no 8 cells and contains at least one marker cell",
    "marker cells occupy all four body quadrants and at least one must change",
    "normal draws contain at most one later-scan distractor body colour",
]

COUNTER_HYPOTHESES = [
    "the marker colour must be one of the four key colours",
    "every nonzero body colour is recoloured by quadrant",
    "exact midpoint cells belong to the top/left half",
    "the key is always in one fixed corner",
    "the output is identity or can be predicted from colour counts alone",
]

# These are negative fixtures for self_check / defect probing, not ordinary
# axis values.  Both intentionally lie outside the teaching distribution.
DEGENERATE_TEXTURES = ("no_markers", "full_grid")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES = ("plain", "marker_not_in_key", "second_color", "midline")

# Every ordinary axis is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..17", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled 10..18", "valid": "9..18"},
    "corner": {
        "type": "str",
        "default": "scheduled",
        "valid": "tl|tr|bl|br",
    },
    "texture": {
        "type": "str",
        "default": "scheduled",
        "valid": "plain|marker_not_in_key|second_color|midline",
        "doc": (
            "plain: one key-member marker colour away from exact midlines; "
            "marker_not_in_key: the marker is absent from the key; "
            "second_color: a later body colour remains unchanged; "
            "midline: a marker lies on an exact bbox midpoint and therefore "
            "uses bottom/right."
        ),
    },
}

_EVEN_DIMS = (10, 12, 14, 16, 18)
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {
        "texture": "midline",
        "grid_h": _EVEN_DIMS,
        "grid_w": _EVEN_DIMS,
    },
)

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CORNERS = ("tl", "tr", "bl", "br")
_PROFILES = ("canonical_anchor", "marker_not_in_key", "second_color", "midline")
SCHEDULE_PROFILES = _PROFILES

# Exact empirical canonical morphology profiles.  The duplicated canonical
# source rows reduce to these three unique input profiles.
_CANONICAL_PROFILES = {
    (10, 10, "tl", 10),
    (12, 12, "tr", 13),
    (14, 14, "br", 18),
}

# Defaults by difficulty and four-profile residue.  Profile 0 reproduces an
# empirical canonical morphology exactly; profiles 1-3 widen one semantic
# factor at a time.  The corner permutation shifts by band so texture is not
# globally tied to one corner.
_DEFAULTS = {
    "easy": (
        (10, 10, "tl", "plain", 10),
        (9, 11, "tr", "marker_not_in_key", 6),
        (11, 10, "br", "second_color", 7),
        (11, 12, "bl", "midline", 7),
    ),
    "medium": (
        (12, 12, "tr", "plain", 13),
        (11, 13, "br", "marker_not_in_key", 9),
        (13, 12, "bl", "second_color", 10),
        (13, 14, "tl", "midline", 10),
    ),
    "hard": (
        (14, 14, "br", "plain", 18),
        (15, 17, "bl", "marker_not_in_key", 12),
        (16, 15, "tl", "second_color", 14),
        (14, 13, "tr", "midline", 15),
    ),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic profile scheduled by sample-index residue."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _DEFAULTS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _geometry(h: int, w: int, corner: str) -> tuple[int, int, int, int]:
    """Return key row/col and body row/col origin for a corner name."""
    if corner == "tl":
        return 0, 0, 2, 2
    if corner == "tr":
        return 0, w - 2, 2, 0
    if corner == "bl":
        return h - 2, 0, 0, 2
    if corner == "br":
        return h - 2, w - 2, 0, 0
    raise ValueError(f"unknown corner: {corner!r}")


def _corner_slots(h: int, w: int):
    return (
        ("tl", 0, 0),
        ("tr", 0, w - 2),
        ("bl", h - 2, 0),
        ("br", h - 2, w - 2),
    )


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    if len(grid) < 4 or width < 4:
        return ["grid is too small for a 2x2 key plus opposite body"]
    return []


def _quadrant(r: int, c: int, bbox: tuple[int, int, int, int], *, midpoint_top_left=False):
    r1, c1, r2, c2 = bbox
    if midpoint_top_left:
        qr = 0 if 2 * r <= r1 + r2 else 1
        qc = 0 if 2 * c <= c1 + c2 else 1
    else:
        qr = 0 if 2 * r < r1 + r2 else 1
        qc = 0 if 2 * c < c1 + c2 else 1
    return qr, qc


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    authority_candidates = []
    for name, kr, kc in _corner_slots(h, w):
        if grid[kr][kc] not in (0, 8) and grid[kr][kc + 1] not in (0, 8):
            authority_candidates.append((name, kr, kc))
    if len(authority_candidates) != 1:
        result["errors"].append(
            "expected exactly one authority key candidate, found "
            f"{len(authority_candidates)}"
        )
        result.update({"height": h, "width": w, "authority_candidates": authority_candidates})
        return result

    corner, kr, kc = authority_candidates[0]
    key_cells = {(kr + dr, kc + dc) for dr in (0, 1) for dc in (0, 1)}
    key_colors = (
        grid[kr][kc],
        grid[kr][kc + 1],
        grid[kr + 1][kc],
        grid[kr + 1][kc + 1],
    )
    if any(color in (0, 8) for color in key_colors):
        result["errors"].append("all four key cells must be non-0/8")
    if len(set(key_colors)) != 4:
        result["errors"].append("the four key colours must be distinct")

    _, _, br0, bc0 = _geometry(h, w, corner)
    body_cells = {
        (r, c)
        for r in range(br0, br0 + h - 2)
        for c in range(bc0, bc0 + w - 2)
    }
    bbox = (br0, bc0, br0 + h - 3, bc0 + w - 3)
    for r in range(h):
        for c in range(w):
            if (r, c) in key_cells:
                continue
            if (r, c) in body_cells:
                if grid[r][c] == 8:
                    result["errors"].append("body rectangle may not contain separator colour 8")
                    break
            elif grid[r][c] != 8:
                result["errors"].append(
                    "cells outside the key and opposite body rectangle must be colour 8"
                )
                break
        if result["errors"] and result["errors"][-1].startswith("cells outside"):
            break

    body_order = sorted(body_cells)
    body_nonzero = [(r, c, grid[r][c]) for r, c in body_order if grid[r][c] != 0]
    marker = body_nonzero[0][2] if body_nonzero else None
    marker_positions = [
        (r, c) for r, c, value in body_nonzero if marker is not None and value == marker
    ]
    body_colors = []
    for _r, _c, value in body_nonzero:
        if value not in body_colors:
            body_colors.append(value)
    second_colors = body_colors[1:]
    quadrants = {_quadrant(r, c, bbox) for r, c in marker_positions}
    midline_positions = [
        (r, c)
        for r, c in marker_positions
        if 2 * r == bbox[0] + bbox[2] or 2 * c == bbox[1] + bbox[3]
    ]
    key_map = {
        (0, 0): key_colors[0],
        (0, 1): key_colors[1],
        (1, 0): key_colors[2],
        (1, 1): key_colors[3],
    }
    changed_markers = sum(
        key_map[_quadrant(r, c, bbox)] != marker for r, c in marker_positions
    ) if marker is not None else 0

    if not any(grid[r][c] == 0 for r, c in body_cells):
        result["errors"].append("body rectangle must retain at least one background-0 cell")
    if marker is None:
        result["errors"].append("body must contain at least one nonzero marker cell")
    if len(body_colors) > 2:
        result["errors"].append("teaching grammar permits at most two body colours")
    if marker is not None and quadrants != {(0, 0), (0, 1), (1, 0), (1, 1)}:
        result["errors"].append("marker cells must witness all four body quadrants")
    if marker is not None and changed_markers == 0:
        result["errors"].append("marker placement hides the transformation as identity")

    texture = None
    if marker is not None:
        if len(body_colors) >= 2:
            texture = "second_color"
        elif marker not in key_colors:
            texture = "marker_not_in_key"
        elif midline_positions:
            texture = "midline"
        else:
            texture = "plain"

    result.update(
        {
            "height": h,
            "width": w,
            "corner": corner,
            "key_row": kr,
            "key_col": kc,
            "key_cells": key_cells,
            "key_colors": key_colors,
            "key_map": key_map,
            "body_cells": body_cells,
            "bbox": bbox,
            "body_nonzero": body_nonzero,
            "body_colors": tuple(body_colors),
            "marker": marker,
            "marker_positions": tuple(marker_positions),
            "marker_count": len(marker_positions),
            "marker_quadrants": quadrants,
            "midline_positions": tuple(midline_positions),
            "changed_markers": changed_markers,
            "second_colors": tuple(second_colors),
            "texture": texture,
            "authority_candidates": authority_candidates,
        }
    )
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from a returned ordinary grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "corner": analysis["corner"],
        "texture": analysis["texture"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, rule-hiding, and off-contract scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strict empirical-manifold predicate from all canonical train/test inputs."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    profile = (
        analysis["height"],
        analysis["width"],
        analysis["corner"],
        analysis["marker_count"],
    )
    if profile not in _CANONICAL_PROFILES:
        reasons.append(
            "(height,width,corner,marker_count) is outside the three canonical profiles: "
            f"{profile!r}"
        )
    if analysis["texture"] != "plain":
        reasons.append("canonical inputs contain one key-member body marker colour only")
    if analysis["midline_positions"]:
        reasons.append("canonical inputs contain no exact-midpoint marker")
    return reasons


def _render_rule(grid, *, recolor_all=False, midpoint_top_left=False, require_key_marker=False):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    marker = analysis["marker"]
    if require_key_marker and marker not in analysis["key_colors"]:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    for r, c in analysis["body_cells"]:
        value = grid[r][c]
        should_recolor = value != 0 if recolor_all else value == marker
        if not should_recolor:
            continue
        q = _quadrant(r, c, analysis["bbox"], midpoint_top_left=midpoint_top_left)
        out[r][c] = analysis["key_map"][q]
    return out


def rule_mirror(grid):
    """Independent Python mirror for semantic tests; Racket remains authority."""
    return _render_rule(grid)


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_marker_must_be_key(grid):
    return _render_rule(grid, require_key_marker=True)


def _rival_recolor_all_body_colors(grid):
    return _render_rule(grid, recolor_all=True)


def _rival_midpoint_top_left(grid):
    return _render_rule(grid, midpoint_top_left=True)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "marker_must_be_key": _rival_marker_must_be_key,
    "recolor_all_body_colors": _rival_recolor_all_body_colors,
    "midpoint_top_left": _rival_midpoint_top_left,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "marker_must_be_key": _rival_marker_must_be_key,
    "recolor_all_body_colors": _rival_recolor_all_body_colors,
    "midpoint_top_left": _rival_midpoint_top_left,
}


def _lawful(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _witness_canonical_anchor(grid) -> bool:
    return not strict_canonical_like(grid)


def _witness_marker_outside_key(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["texture"] == "marker_not_in_key")


def _witness_second_color(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["texture"] == "second_color")


def _witness_midline(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["texture"] == "midline")


SEMANTIC_WITNESSES = {
    "canonical_anchor": _witness_canonical_anchor,
    "marker_outside_key": _witness_marker_outside_key,
    "second_color_stays_unchanged": _witness_second_color,
    "exact_midline_uses_bottom_right": _witness_midline,
}
WITNESS_RIVALS = {
    "canonical_anchor": ["identity"],
    "marker_outside_key": ["marker_must_be_key"],
    "second_color_stays_unchanged": ["recolor_all_body_colors"],
    "exact_midline_uses_bottom_right": ["midpoint_top_left"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every seven-demo lesson must kill all three canonical-fitting rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    textures: set[str] = set()
    corners: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the quadrant-key rule")
        textures.add(analysis["texture"])
        corners.add(analysis["corner"])

    missing = set(HELPFUL_TEXTURES) - textures
    if missing:
        reasons.append(f"demonstrations omit shortcut-killing textures: {sorted(missing)}")
    if len(corners) < 3:
        reasons.append("demonstrations need at least three key corners")

    q_analysis = _analyze(query["input"])
    if q_analysis["errors"]:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    q_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != q_truth:
        reasons.append("query output disagrees with the quadrant-key rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos) and (
            competitor(query["input"]) != q_truth
        ):
            reasons.append(
                f"competing rule {name!r} fits every demo but predicts a different query"
            )
    return reasons


def _draw_profile_int(ctx, overrides, label: str, default: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, 9, 18)
    return ctx.draw_int(label, default, default)


def _draw_profile_choice(ctx, overrides, label: str, default: str, options: tuple[str, ...]):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _nearest_odd(value: int) -> int:
    if value % 2:
        return value
    if value < 18:
        return value + 1
    return value - 1


def _banned_key_probe_cells(h: int, w: int, key_corner: str) -> set[tuple[int, int]]:
    banned: set[tuple[int, int]] = set()
    for name, r, c in _corner_slots(h, w):
        if name == key_corner:
            continue
        banned.add((r, c))
        banned.add((r, c + 1))
    return banned


def _choose_positions(rng, candidates: list[tuple[int, int]], count: int) -> list[tuple[int, int]]:
    if len(candidates) < count:
        raise ValueError(f"need {count} placement cells, only {len(candidates)} available")
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    return shuffled[:count]


def _draw_normal_grid(
    *,
    ctx,
    h: int,
    w: int,
    corner: str,
    texture: str,
    marker_count: int,
) -> list[list[int]]:
    rng = ctx.draw_rng("layout")
    kr, kc, br0, bc0 = _geometry(h, w, corner)
    keys = rng.sample(_COLORS, 4)
    key_map = {(0, 0): keys[0], (0, 1): keys[1], (1, 0): keys[2], (1, 1): keys[3]}
    if texture == "marker_not_in_key":
        marker = rng.choice([color for color in _COLORS if color not in keys])
    else:
        marker = keys[(int(ctx.sample_index) + int(ctx.seed)) % 4]

    grid = full_grid(h, w, 8)
    body = [
        (r, c)
        for r in range(br0, br0 + h - 2)
        for c in range(bc0, bc0 + w - 2)
    ]
    for r, c in body:
        grid[r][c] = 0
    grid[kr][kc] = keys[0]
    grid[kr][kc + 1] = keys[1]
    grid[kr + 1][kc] = keys[2]
    grid[kr + 1][kc + 1] = keys[3]

    bbox = (br0, bc0, br0 + h - 3, bc0 + w - 3)
    banned = _banned_key_probe_cells(h, w, corner)
    eligible = [(r, c) for r, c in body if (r, c) not in banned]
    if texture != "midline":
        eligible = [
            (r, c)
            for r, c in eligible
            if 2 * r != bbox[0] + bbox[2] and 2 * c != bbox[1] + bbox[3]
        ]

    by_quadrant = {
        q: [(r, c) for r, c in eligible if _quadrant(r, c, bbox) == q]
        for q in ((0, 0), (0, 1), (1, 0), (1, 1))
    }
    mandatory: list[tuple[int, int]] = []
    for q in ((0, 0), (0, 1), (1, 0), (1, 1)):
        choices = by_quadrant[q]
        if not choices:
            raise ValueError(f"no marker placement available for quadrant {q}")
        mandatory.append(rng.choice(choices))

    if texture == "midline":
        midline = [
            (r, c)
            for r, c in eligible
            if 2 * r == bbox[0] + bbox[2] or 2 * c == bbox[1] + bbox[3]
        ]
        if not midline:
            raise ValueError(
                "texture='midline' is incompatible with even grid_h and grid_w"
            )
        midpoint = rng.choice(midline)
        if midpoint not in mandatory:
            mandatory.append(midpoint)

    marker_count = max(marker_count, len(mandatory))
    marker_count = min(marker_count, len(eligible) - 1)
    marker_positions = list(dict.fromkeys(mandatory))
    remaining = [pos for pos in eligible if pos not in marker_positions]
    marker_positions.extend(
        _choose_positions(rng, remaining, marker_count - len(marker_positions))
    )
    for r, c in marker_positions:
        grid[r][c] = marker

    if texture == "second_color":
        first_marker = min(marker_positions)
        other = rng.choice([color for color in _COLORS if color not in keys and color != marker])
        second_candidates = [
            (r, c)
            for r, c in body
            if (r, c) not in banned
            and grid[r][c] == 0
            and (r, c) > first_marker
        ]
        second_count = min(3, max(1, marker_count // 4), len(second_candidates))
        if second_count < 1:
            raise ValueError("no later-scan cell available for second_color texture")
        for r, c in _choose_positions(rng, second_candidates, second_count):
            grid[r][c] = other

    # A final structural check prevents an accidental placement fallback from
    # returning a mislabeled sample.
    errors = self_check(grid)
    if errors:
        raise ValueError("constructed grid failed self_check: " + "; ".join(errors))
    if observe_overrides(grid)["texture"] != texture:
        raise ValueError(
            f"constructed texture {texture!r} observed as {observe_overrides(grid)['texture']!r}"
        )
    return grid


def _draw_from_degenerate(name: str, ctx) -> list[list[int]]:
    """Negative fixtures: both must be rejected by ordinary self_check."""
    texture = ctx.draw_choice("texture", (name,))
    del texture
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("degenerate_layout")
    if name == "full_grid":
        return full_grid(h, w, rng.choice(_COLORS))

    corner = ctx.draw_choice("corner", _CORNERS)
    kr, kc, br0, bc0 = _geometry(h, w, corner)
    grid = full_grid(h, w, 8)
    for r in range(br0, br0 + h - 2):
        for c in range(bc0, bc0 + w - 2):
            grid[r][c] = 0
    keys = rng.sample(_COLORS, 4)
    grid[kr][kc] = keys[0]
    grid[kr][kc + 1] = keys[1]
    grid[kr + 1][kc] = keys[2]
    grid[kr + 1][kc + 1] = keys[3]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the synchronized Racket owns output."""
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    texture_override = overrides.get("texture")
    if texture_override in DEGENERATE_TEXTURES:
        ctx = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides=overrides,
        )
        return _draw_from_degenerate(texture_override, ctx)
    if texture_override is not None and texture_override not in HELPFUL_TEXTURES:
        raise ValueError(f"texture override {texture_override!r} is not in {HELPFUL_TEXTURES}")

    residue = int(sample_index) % len(_PROFILES)
    default_h, default_w, default_corner, default_texture, marker_count = _DEFAULTS[band][residue]

    # Midline is geometrically impossible only when both exact dimensions are
    # even.  If only one dimension is pinned, keep the other default odd so a
    # single-axis override remains satisfiable.  If texture is not explicitly
    # pinned, an even/even pair simply falls back from the scheduled midline
    # profile to plain instead of lying about the realized texture.
    if texture_override == "midline":
        requested_h = overrides.get("grid_h")
        requested_w = overrides.get("grid_w")
        if requested_h is not None and requested_w is not None:
            if int(requested_h) % 2 == 0 and int(requested_w) % 2 == 0:
                raise ValueError(
                    "incompatible overrides grid_h, grid_w, texture: "
                    "texture='midline' needs at least one odd dimension"
                )
        elif requested_h is not None and int(requested_h) % 2 == 0:
            default_w = _nearest_odd(default_w)
        elif requested_w is not None and int(requested_w) % 2 == 0:
            default_h = _nearest_odd(default_h)
        else:
            default_h = _nearest_odd(default_h)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", default_h)
    w = _draw_profile_int(ctx, overrides, "grid_w", default_w)

    if texture_override is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    else:
        realized_default_texture = default_texture
        if realized_default_texture == "midline" and h % 2 == 0 and w % 2 == 0:
            realized_default_texture = "plain"
        texture = ctx.draw_choice("texture", (realized_default_texture,))

    corner = _draw_profile_choice(ctx, overrides, "corner", default_corner, _CORNERS)
    grid = _draw_normal_grid(
        ctx=ctx,
        h=h,
        w=w,
        corner=corner,
        texture=texture,
        marker_count=marker_count,
    )

    observed = observe_overrides(grid)
    for name, requested in overrides.items():
        if observed.get(name) != requested:
            raise ValueError(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return grid
