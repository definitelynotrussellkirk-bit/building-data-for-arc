"""Generator for e4075551 — extrema markers build a frame and 5-cross.

The first color-2 cell is the center.  Among every other non-zero cell, the
minimum/maximum row markers supply the top/bottom frame rows and colors, while
the minimum/maximum column markers supply the left/right frame columns and
colors.  The output is rebuilt from scratch with edge precedence
(top > bottom > left > right), then a color-5 cross through the center, then the
center color 2 when it is not covered by an edge.  Unselected input markers are
erased.

This sampler keeps the canonical four-marker regime dense, but schedules three
small counterexamples needed to identify the exact rule: a top-left marker may
serve two extrema roles, the center may lie on an edge and disappear, and an
extra non-extreme marker may be ignored.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a9926d504f3"
TASK_ID = GENERATOR_ID
RULE_HASH = "b54594bcf310"
VERSION = "3.0.0"

SUMMARY = (
    "Sparse extrema markers define a colored rectangular frame around a "
    "color-2 center; a color-5 cross is drawn through the center and every "
    "non-extreme marker is erased.  Scheduled shared-corner, center-on-edge, "
    "and ignored-extra-marker examples refute the canonical-fitting shortcuts."
)

INVARIANTS = [
    "grid is 10..22 by 10..22 with integer ARC colors",
    "there is exactly one color-2 center and each extrema direction is unique",
    "the extrema define a positive-area frame containing the center",
    "shared_corner has exactly one top-left dual-role marker",
    "extra_marker has exactly one strictly interior marker off the center cross",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES = (
    "plain",
    "shared_corner",
    "center_edge",
    "extra_marker",
    "same_color",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted 10..22",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted 10..22",
        "valid": "10..22",
    },
    "texture": {
        "type": "str",
        "default": "scheduled helpful",
        "valid": "plain|shared_corner|center_edge|extra_marker|same_color",
        "doc": (
            "shared_corner: one marker is min-row AND min-col; "
            "center_edge: the 2 sits on an edge and vanishes; "
            "extra_marker: interior non-extreme dot erased."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Public canonical shapes first; broader anchors keep the advertised domain
# genuinely populated.  The full 10..22 domain is present in every draw, so an
# override remains legal in every difficulty band.
_CANONICAL_SHAPES = (
    (15, 14),
    (14, 15),
    (15, 15),
    (16, 15),
)
_PROFILE_ANCHORS = _CANONICAL_SHAPES * 4 + (
    (10, 10),
    (22, 22),
    (12, 18),
    (18, 12),
    (11, 17),
    (17, 11),
    (20, 20),
    (13, 19),
    (19, 13),
)
_AXIS_WEIGHT = 96
_COLORS = (1, 3, 4, 6, 7, 8, 9)

SCHEDULE_PROFILES = HELPFUL_TEXTURES
EXAMPLES_NEEDED = 4


def schedule_profile(seed, sample_index, difficulty=None):
    """Deterministic curriculum branch; every four consecutive draws teach all rivals."""
    del seed, difficulty
    residue = sample_index % 4
    if residue == 0:
        return "shared_corner"
    if residue == 1:
        return "center_edge"
    if residue == 2:
        return "extra_marker"
    return "plain" if (sample_index // 4) % 2 == 0 else "same_color"


def _weighted_axis(ctx, name: str, anchor: int, difficulty) -> int:
    domain = list(range(10, 23))
    if difficulty == "easy":
        band = list(range(10, 15))
    elif difficulty == "medium":
        band = list(range(14, 19))
    elif difficulty == "hard":
        band = list(range(18, 23))
    else:
        band = domain
    options = [anchor] * _AXIS_WEIGHT + domain + band * 2
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    texture = overrides.get("texture")
    if texture is not None:
        if type(texture) is not str:
            raise ValueError(f"texture must be a string, not {type(texture).__name__}")
        if texture not in HELPFUL_TEXTURES:
            raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}, not {texture!r}")


def _validate_call_controls(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject malformed scalar controls before they reach deterministic sampling."""
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, not {sample_index}")
    if difficulty is not None:
        if type(difficulty) is not str:
            raise TypeError(
                f"difficulty must be a string or None, not {type(difficulty).__name__}"
            )
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError(
                "difficulty must be one of ('easy', 'medium', 'hard') or None, "
                f"not {difficulty!r}"
            )


def _frame_bounds(rng, h: int, w: int) -> tuple[int, int, int, int]:
    # A span of at least four leaves three interior coordinates, enough to
    # choose edge markers, centers, and ignored dots constructively.
    tr_max = min(h // 3, h - 6)
    tr = rng.randint(1, tr_max)
    br = rng.randint(max(tr + 4, (2 * h) // 3), h - 2)
    lc_max = min(w // 3, w - 6)
    lc = rng.randint(1, lc_max)
    rc = rng.randint(max(lc + 4, (2 * w) // 3), w - 2)
    return tr, br, lc, rc


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_controls(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_h, anchor_w = _PROFILE_ANCHORS[sample_index % len(_PROFILE_ANCHORS)]
    h = _weighted_axis(ctx, "grid_h", anchor_h, difficulty)
    w = _weighted_axis(ctx, "grid_w", anchor_w, difficulty)

    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        # Record the public axis without weakening the exact curriculum schedule.
        texture = ctx.draw_choice("texture", (scheduled,))

    rng = ctx.draw_rng("layout")
    tr, br, lc, rc = _frame_bounds(rng, h, w)
    interior_rows = list(range(tr + 1, br))
    interior_cols = list(range(lc + 1, rc))

    if texture == "center_edge":
        center_row = rng.choice((tr, br))
        center_col = rng.choice(interior_cols)
    else:
        center_row = rng.choice(interior_rows)
        center_col = rng.choice(interior_cols)

    grid = full_grid(h, w, 0)
    if texture == "shared_corner":
        role_colors = rng.sample(_COLORS, 3)
        grid[tr][lc] = role_colors[0]
        grid[br][rng.choice(interior_cols)] = role_colors[1]
        grid[rng.choice(interior_rows)][rc] = role_colors[2]
    else:
        if texture == "same_color":
            color = rng.choice(_COLORS)
            role_colors = [color] * 4
        else:
            role_colors = rng.sample(_COLORS, 4)

        top_candidates = list(interior_cols)
        bottom_candidates = list(interior_cols)
        if texture == "center_edge":
            if center_row == tr:
                top_candidates.remove(center_col)
            else:
                bottom_candidates.remove(center_col)
        grid[tr][rng.choice(top_candidates)] = role_colors[0]
        grid[br][rng.choice(bottom_candidates)] = role_colors[1]
        grid[rng.choice(interior_rows)][lc] = role_colors[2]
        grid[rng.choice(interior_rows)][rc] = role_colors[3]

    grid[center_row][center_col] = 2

    if texture == "extra_marker":
        candidates = [
            (r, c)
            for r in interior_rows
            for c in interior_cols
            if r != center_row and c != center_col and grid[r][c] == 0
        ]
        if not candidates:  # impossible for the declared geometry; fail loudly if changed
            raise RuntimeError("no legal location for the ignored extra marker")
        r, c = rng.choice(candidates)
        grid[r][c] = rng.choice(_COLORS)
    return grid


def _validated_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]
    return [list(row) for row in grid], []


def _analysis(checked: list[list[int]]) -> dict[str, Any]:
    cells = [
        (r, c)
        for r, row in enumerate(checked)
        for c, value in enumerate(row)
        if value != 0
    ]
    centers = [(r, c) for r, c in cells if checked[r][c] == 2]
    others = [(r, c) for r, c in cells if checked[r][c] != 2]
    if len(centers) != 1 or not others:
        return {"centers": centers, "others": others}
    center = centers[0]
    top = min(others, key=lambda p: p[0])
    bottom = max(others, key=lambda p: p[0])
    left = min(others, key=lambda p: p[1])
    right = max(others, key=lambda p: p[1])
    tr, br, lc, rc = top[0], bottom[0], left[1], right[1]
    return {
        "centers": centers,
        "center": center,
        "others": others,
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
        "top_row": tr,
        "bottom_row": br,
        "left_col": lc,
        "right_col": rc,
        "role_positions": {top, bottom, left, right},
        "role_candidates": {
            "top": [p for p in others if p[0] == tr],
            "bottom": [p for p in others if p[0] == br],
            "left": [p for p in others if p[1] == lc],
            "right": [p for p in others if p[1] == rc],
        },
    }


def _texture_and_errors(checked: list[list[int]], info: dict[str, Any]):
    errors: list[str] = []
    others = info["others"]
    count = len(others)
    if count not in (3, 4, 5):
        return None, [f"expected 3..5 non-center markers, found {count}"]

    role_positions = info["role_positions"]
    role_colors = [checked[r][c] for r, c in role_positions]
    cr, cc = info["center"]
    tr, br = info["top_row"], info["bottom_row"]
    lc, rc = info["left_col"], info["right_col"]

    if count == 3:
        texture = "shared_corner"
        if len(role_positions) != 3 or info["top"] != info["left"]:
            errors.append("shared_corner must have exactly one top-left dual-role marker")
        if len(set(role_colors)) != 3:
            errors.append("shared_corner role markers must use three distinct colors")
        if not (tr < cr < br and lc < cc < rc):
            errors.append("shared_corner center must be strictly inside the frame")
    elif count == 5:
        texture = "extra_marker"
        if len(role_positions) != 4:
            errors.append("extra_marker must retain four distinct extrema positions")
        if len(set(role_colors)) != 4:
            errors.append("extra_marker extrema must use four distinct colors")
        extras = [p for p in others if p not in role_positions]
        if len(extras) != 1:
            errors.append(f"extra_marker must have one non-role marker, found {len(extras)}")
        else:
            er, ec = extras[0]
            if not (tr < er < br and lc < ec < rc):
                errors.append("extra marker must be strictly inside the frame")
            if er == cr or ec == cc:
                errors.append("extra marker must be off the center row and column")
        if not (tr < cr < br and lc < cc < rc):
            errors.append("extra_marker center must be strictly inside the frame")
    else:
        marker_colors = [checked[r][c] for r, c in others]
        all_same = len(set(marker_colors)) == 1
        on_edge = cr in (tr, br)
        if all_same:
            texture = "same_color"
        elif on_edge:
            texture = "center_edge"
        else:
            texture = "plain"
        if len(role_positions) != 4:
            errors.append(f"{texture} must have four distinct extrema positions")
        if texture == "same_color":
            if not (tr < cr < br and lc < cc < rc):
                errors.append("same_color center must be strictly inside the frame")
        else:
            if len(set(role_colors)) != 4:
                errors.append(f"{texture} extrema must use four distinct colors")
            if texture == "center_edge":
                if not (lc < cc < rc):
                    errors.append("center_edge center column must be inside the frame")
            elif not (tr < cr < br and lc < cc < rc):
                errors.append("plain center must be strictly inside the frame")
    return texture, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    checked, errors = _validated_grid(grid)
    if errors:
        return errors
    h, w = len(checked), len(checked[0])
    if not 10 <= h <= 22:
        errors.append("grid_h must be in 10..22")
    if not 10 <= w <= 22:
        errors.append("grid_w must be in 10..22")

    info = _analysis(checked)
    centers = info["centers"]
    if len(centers) != 1:
        errors.append(f"expected exactly one color-2 center, found {len(centers)}")
        return sorted(set(errors))
    if not info["others"]:
        errors.append("expected non-center extrema markers")
        return sorted(set(errors))

    tr, br = info["top_row"], info["bottom_row"]
    lc, rc = info["left_col"], info["right_col"]
    if not (tr < br and lc < rc):
        errors.append("extrema do not define a positive-area frame")
    cr, cc = info["center"]
    if not (tr <= cr <= br and lc <= cc <= rc):
        errors.append("center lies outside the extrema-defined frame")
    for name, candidates in info["role_candidates"].items():
        if len(candidates) != 1:
            errors.append(f"{name} extrema role must be unique, found {len(candidates)} candidates")

    _texture, texture_errors = _texture_and_errors(checked, info)
    errors.extend(texture_errors)
    if not errors:
        try:
            output = rule_mirror(checked)
        except Exception as exc:
            errors.append(f"rule mirror failed: {type(exc).__name__}: {exc}")
        else:
            if len(output) != h or any(len(row) != w for row in output):
                errors.append("rule mirror changed grid dimensions")
            if not any(value != 0 for row in output for value in row):
                errors.append("rule mirror produced an empty output")
    return sorted(set(errors))


def strict_canonical_like(grid):
    """All generated textures are lawful cases of the selected canonical rule."""
    return self_check(grid)


def observe_overrides(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    diagnostics = self_check(checked)
    if diagnostics:
        raise ValueError("; ".join(diagnostics))
    info = _analysis(checked)
    texture, texture_errors = _texture_and_errors(checked, info)
    if texture_errors or texture is None:
        raise ValueError("; ".join(texture_errors or ["texture could not be inferred"]))
    return {"grid_h": len(checked), "grid_w": len(checked[0]), "texture": texture}


def rule_mirror(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _analysis(checked)
    if len(info.get("centers", ())) != 1 or not info.get("others"):
        raise ValueError("rule requires exactly one center and at least one other marker")
    h, w = len(checked), len(checked[0])
    cr, cc = info["center"]
    tr, br = info["top_row"], info["bottom_row"]
    lc, rc = info["left_col"], info["right_col"]
    top_color = checked[info["top"][0]][info["top"][1]]
    bottom_color = checked[info["bottom"][0]][info["bottom"][1]]
    left_color = checked[info["left"][0]][info["left"][1]]
    right_color = checked[info["right"][0]][info["right"][1]]
    output = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if r == tr and lc <= c <= rc:
                output[r][c] = top_color
            elif r == br and lc <= c <= rc:
                output[r][c] = bottom_color
            elif c == lc and tr <= r <= br:
                output[r][c] = left_color
            elif c == rc and tr <= r <= br:
                output[r][c] = right_color
            elif r == cr and c == cc:
                output[r][c] = 2
            elif r == cr and lc < c < rc:
                output[r][c] = 5
            elif c == cc and tr < r < br:
                output[r][c] = 5
    return output


# Backward-compatible private name retained for any existing review scripts.
_mirror = rule_mirror


def _exactly_four_markers(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _analysis(checked)
    if len(info.get("others", ())) == 4:
        return rule_mirror(checked)
    return deepcopy(checked)


def _center_always_visible(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = rule_mirror(checked)
    cr, cc = _analysis(checked)["center"]
    output[cr][cc] = 2
    return output


def _preserve_nonrole_markers(grid):
    checked, errors = _validated_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _analysis(checked)
    output = rule_mirror(checked)
    selected = set(info["role_positions"]) | {info["center"]}
    for r, c in info["others"]:
        if (r, c) not in selected:
            output[r][c] = checked[r][c]
    return output


def _has_texture(name: str):
    def predicate(grid):
        try:
            return observe_overrides(grid)["texture"] == name
        except Exception:
            return False

    return predicate


SEMANTIC_WITNESSES = {
    "shared_corner_dual_role": _has_texture("shared_corner"),
    "center_hidden_by_edge": _has_texture("center_edge"),
    "ignored_non_extreme_marker": _has_texture("extra_marker"),
}
SEMANTIC_RIVALS = {
    "exactly_four_markers": _exactly_four_markers,
    "center_always_visible": _center_always_visible,
    "preserve_nonrole_markers": _preserve_nonrole_markers,
}
WITNESS_RIVALS = {
    "shared_corner_dual_role": ["exactly_four_markers"],
    "center_hidden_by_edge": ["center_always_visible"],
    "ignored_non_extreme_marker": ["preserve_nonrole_markers"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report any declared rival that survives demos but changes the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
