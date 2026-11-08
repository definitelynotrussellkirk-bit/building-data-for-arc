"""Generator for ARC task ba97ae07 / content id 2f0a4d589c58.

A single horizontal rectangular bar and a single vertical rectangular bar
cross on a zero background.  Their two nonzero colors are distinct.  In the
input, the whole overlap rectangle has one bar's color, so that bar appears in
front.  The output recolors only the overlap to the other bar's color, swapping
which bar appears in front.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f0a4d589c58"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "70d63db0a1f2"
SUMMARY = (
    "On background 0, one full-width horizontal bar and one full-height "
    "vertical bar cross. Their colors differ. The overlap is uniformly the "
    "color of the visually front bar. Recolor the complete overlap rectangle "
    "with the other bar color, leaving every non-overlap cell unchanged."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the background is exactly color 0",
    "there is exactly one contiguous full-width horizontal bar, thickness 1..3",
    "there is exactly one contiguous full-height vertical bar, thickness 1..2",
    "the horizontal and vertical bar colors are distinct nonzero ARC colors",
    "every nonzero cell belongs to the union of the two bars",
    "the complete overlap rectangle is uniform and equals one bar color",
    "the output changes only the overlap to the other bar color",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

_HORIZONTAL_POSITIONS = ("top", "center", "bottom")
_VERTICAL_POSITIONS = ("left", "center", "right")
_OCCLUDERS = ("horizontal", "vertical")
_HORIZONTAL_SCHEDULE = ("center", "top", "bottom")
_VERTICAL_SCHEDULE = ("center", "right", "left")
_HORIZONTAL_THICKNESS_SCHEDULE = (1, 1, 2, 1, 3, 2)
_VERTICAL_THICKNESS_SCHEDULE = (1, 1, 1, 2, 2, 2)
SCHEDULE_PROFILES = tuple(
    f"geometry_phase_{phase}_{occluder}_front"
    for phase in range(6)
    for occluder in _OCCLUDERS
)
_SIZE_PROFILES = ((8, 7), (7, 9), (8, 6), (13, 13), (11, 6))
_BAND_OFFSETS = {"easy": 0, "medium": 2, "hard": 4}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical size profile",
        "valid": "7..13",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical size profile",
        "valid": "6..13",
    },
    "horizontal_thickness": {
        "type": "int",
        "default": "scheduled 1..3",
        "valid": "1..3",
    },
    "vertical_thickness": {
        "type": "int",
        "default": "scheduled 1..2",
        "valid": "1..2",
    },
    "horizontal_position": {
        "type": "str",
        "default": "scheduled top|center|bottom",
        "valid": "top|center|bottom",
    },
    "vertical_position": {
        "type": "str",
        "default": "scheduled left|center|right",
        "valid": "left|center|right",
    },
    "horizontal_color": {
        "type": "color",
        "default": "keyed rng",
        "valid": "1..9",
    },
    "vertical_color_offset": {
        "type": "int",
        "default": "keyed rng cyclic offset from horizontal_color",
        "valid": "1..8",
    },
    "occluder": {
        "type": "str",
        "default": "scheduled horizontal|vertical",
        "valid": "horizontal|vertical",
    },
}


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    """Return a plain rectangular ARC grid, or exact structural errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["rows must be non-empty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return None, ["grid must be rectangular"]
        clean: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, ["cells must be integer ARC colors in 0..9"]
            clean.append(int(value))
        converted.append(clean)
    return converted, []


def _contiguous(indices: list[int]) -> bool:
    return bool(indices) and indices == list(range(indices[0], indices[-1] + 1))


def _position_start(size: int, thickness: int, position: str) -> int:
    if position in ("top", "left"):
        return 0
    if position in ("bottom", "right"):
        return size - thickness
    if position == "center":
        return (size - thickness) // 2
    raise ValueError(f"unknown position: {position!r}")


def _position_name(size: int, thickness: int, start: int, *, vertical: bool) -> str | None:
    names = _VERTICAL_POSITIONS if vertical else _HORIZONTAL_POSITIONS
    for name in names:
        if _position_start(size, thickness, name) == start:
            return name
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {"errors": errors}
    if converted is None:
        return facts

    h, w = len(converted), len(converted[0])
    facts.update({"grid": converted, "grid_h": h, "grid_w": w})
    if not 7 <= h <= 13:
        errors.append("grid height must be in 7..13")
    if not 6 <= w <= 13:
        errors.append("grid width must be in 6..13")

    palette = sorted({value for row in converted for value in row})
    if palette[0:1] != [0] or len(palette) != 3:
        errors.append("palette must be exactly 0 plus two distinct nonzero colors")

    full_rows = [r for r in range(h) if all(converted[r][c] != 0 for c in range(w))]
    full_cols = [c for c in range(w) if all(converted[r][c] != 0 for r in range(h))]
    if not (1 <= len(full_rows) <= 3 and _contiguous(full_rows)):
        errors.append("horizontal bar must be 1..3 contiguous full-width rows")
    if not (1 <= len(full_cols) <= 2 and _contiguous(full_cols)):
        errors.append("vertical bar must be 1..2 contiguous full-height columns")

    if errors:
        return facts

    row_set, col_set = set(full_rows), set(full_cols)
    outside_nonzero = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if r not in row_set and c not in col_set and converted[r][c] != 0
    ]
    if outside_nonzero:
        errors.append("nonzero cells may occur only in the union of the two bars")

    horizontal_flank = {
        converted[r][c] for r in full_rows for c in range(w) if c not in col_set
    }
    vertical_flank = {
        converted[r][c] for c in full_cols for r in range(h) if r not in row_set
    }
    overlap = {converted[r][c] for r in full_rows for c in full_cols}
    if len(horizontal_flank) != 1 or 0 in horizontal_flank:
        errors.append("horizontal bar flanks must have one nonzero color")
    if len(vertical_flank) != 1 or 0 in vertical_flank:
        errors.append("vertical bar flanks must have one nonzero color")
    if len(overlap) != 1 or 0 in overlap:
        errors.append("the complete overlap rectangle must be one nonzero color")
    if errors:
        return facts

    horizontal_color = next(iter(horizontal_flank))
    vertical_color = next(iter(vertical_flank))
    overlap_color = next(iter(overlap))
    if horizontal_color == vertical_color:
        errors.append("horizontal and vertical bars must have different colors")
    if overlap_color not in (horizontal_color, vertical_color):
        errors.append("overlap color must equal one of the two bar colors")
    if errors:
        return facts

    horizontal_start = full_rows[0]
    vertical_start = full_cols[0]
    horizontal_position = _position_name(
        h, len(full_rows), horizontal_start, vertical=False
    )
    vertical_position = _position_name(
        w, len(full_cols), vertical_start, vertical=True
    )
    # Canonical source rows use arbitrary legal starts; generated scenes use
    # the declared named positions so every placement override remains exactly
    # observable.  Preserve arbitrary canonical starts as "other" rather than
    # rejecting a valid crossing-bar task.
    if horizontal_position is None:
        horizontal_position = "other"
    if vertical_position is None:
        vertical_position = "other"

    occluder = "horizontal" if overlap_color == horizontal_color else "vertical"
    other_color = vertical_color if occluder == "horizontal" else horizontal_color
    output = deepcopy(converted)
    for r in full_rows:
        for c in full_cols:
            output[r][c] = other_color

    vertical_color_offset = (vertical_color - horizontal_color) % 9
    if vertical_color_offset == 0:
        errors.append("bar colors must have a nonzero cyclic offset")
        return facts

    facts.update(
        {
            "errors": errors,
            "horizontal_rows": tuple(full_rows),
            "vertical_cols": tuple(full_cols),
            "horizontal_start": horizontal_start,
            "vertical_start": vertical_start,
            "horizontal_thickness": len(full_rows),
            "vertical_thickness": len(full_cols),
            "horizontal_position": horizontal_position,
            "vertical_position": vertical_position,
            "horizontal_color": horizontal_color,
            "vertical_color": vertical_color,
            "vertical_color_offset": vertical_color_offset,
            "occluder": occluder,
            "overlap_area": len(full_rows) * len(full_cols),
            "output": output,
        }
    )
    return facts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject every shape outside the exact two-bar task grammar."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """All generated scenes intentionally live in the canonical task family."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared axis exactly from the emitted grid."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "horizontal_thickness": info["horizontal_thickness"],
        "vertical_thickness": info["vertical_thickness"],
        "horizontal_position": info["horizontal_position"],
        "vertical_position": info["vertical_position"],
        "horizontal_color": info["horizontal_color"],
        "vertical_color_offset": info["vertical_color_offset"],
        "occluder": info["occluder"],
    }


def canonical_profile_signature(grid: Any) -> tuple[Any, ...] | None:
    """A compact exact-family signature used by profile diagnostics."""
    info = _analyze(grid)
    if info["errors"]:
        return None
    return (
        info["grid_h"],
        info["grid_w"],
        info["horizontal_thickness"],
        info["vertical_thickness"],
        info["occluder"],
    )


def rule_mirror(grid: Any) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return deepcopy(info["output"])


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_OFFSETS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_scheduled_int(ctx: Any, label: str, scheduled: int, lo: int, hi: int) -> int:
    bounds = (lo, hi) if label in ctx.overrides and ctx.overrides[label] is not None else (scheduled, scheduled)
    return ctx.draw_int(label, *bounds)


def _draw_scheduled_choice(
    ctx: Any, label: str, scheduled: str, options: tuple[str, ...]
) -> str:
    choices = options if label in ctx.overrides and ctx.overrides[label] is not None else (scheduled,)
    return str(ctx.draw_choice(label, choices))


def _scheduled_values(sample_index: int, band: str) -> tuple[Any, ...]:
    """Pair identical nuisance geometry with opposite overlap occluders."""
    offset = _BAND_OFFSETS[band]
    pair_group = int(sample_index) // 2
    h, w = _SIZE_PROFILES[(pair_group + offset) % len(_SIZE_PROFILES)]
    phase = pair_group % 6
    return (
        band,
        h,
        w,
        _HORIZONTAL_THICKNESS_SCHEDULE[phase],
        _VERTICAL_THICKNESS_SCHEDULE[phase],
        _HORIZONTAL_SCHEDULE[phase % 3],
        _VERTICAL_SCHEDULE[phase % 3],
        _OCCLUDERS[int(sample_index) % 2],
    )


def _scheduled_palette(seed: int, pair_group: int, band: str) -> tuple[int, int]:
    """Return one deterministic palette shared by both members of a pair."""
    rng = stable_rng(
        int(seed), f"{TASK_ID}|pair:{pair_group}|palette:{band}", VERSION
    )
    return rng.randint(1, 9), rng.randint(1, 8)


def _draw_scheduled_color(ctx: Any, label: str, scheduled: int) -> int:
    choices = (
        tuple(range(1, 10))
        if label in ctx.overrides and ctx.overrides[label] is not None
        else (scheduled,)
    )
    return int(ctx.draw_choice(label, choices))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose paired geometry/occluder phases to the audit harness."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    band = _band(difficulty)
    profile = _scheduled_values(sample_index, band)
    (
        _profile_band,
        scheduled_h,
        scheduled_w,
        scheduled_h_thickness,
        scheduled_v_thickness,
        scheduled_h_position,
        scheduled_v_position,
        scheduled_occluder,
    ) = profile

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, "grid_h", scheduled_h, 7, 13)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled_w, 6, 13)
    horizontal_thickness = _draw_scheduled_int(
        ctx, "horizontal_thickness", scheduled_h_thickness, 1, 3
    )
    vertical_thickness = _draw_scheduled_int(
        ctx, "vertical_thickness", scheduled_v_thickness, 1, 2
    )
    horizontal_position = _draw_scheduled_choice(
        ctx,
        "horizontal_position",
        scheduled_h_position,
        _HORIZONTAL_POSITIONS,
    )
    vertical_position = _draw_scheduled_choice(
        ctx,
        "vertical_position",
        scheduled_v_position,
        _VERTICAL_POSITIONS,
    )
    pair_group = int(sample_index) // 2
    scheduled_horizontal_color, scheduled_color_offset = _scheduled_palette(
        int(seed), pair_group, band
    )
    horizontal_color = _draw_scheduled_color(
        ctx, "horizontal_color", scheduled_horizontal_color
    )
    color_offset = _draw_scheduled_int(
        ctx, "vertical_color_offset", scheduled_color_offset, 1, 8
    )
    vertical_color = ((horizontal_color - 1 + color_offset) % 9) + 1
    occluder = _draw_scheduled_choice(
        ctx, "occluder", scheduled_occluder, _OCCLUDERS
    )

    horizontal_start = _position_start(h, horizontal_thickness, horizontal_position)
    vertical_start = _position_start(w, vertical_thickness, vertical_position)
    horizontal_rows = range(horizontal_start, horizontal_start + horizontal_thickness)
    vertical_cols = range(vertical_start, vertical_start + vertical_thickness)

    grid = full_grid(h, w, 0)
    for r in horizontal_rows:
        for c in range(w):
            grid[r][c] = horizontal_color
    for c in vertical_cols:
        for r in range(h):
            grid[r][c] = vertical_color
    overlap_color = horizontal_color if occluder == "horizontal" else vertical_color
    for r in horizontal_rows:
        for c in vertical_cols:
            grid[r][c] = overlap_color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator emitted invalid task scene: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Semantic witnesses and explicit wrong-rule rivals.
# ---------------------------------------------------------------------------


def _facts_or_none(grid: Any) -> dict[str, Any] | None:
    info = _analyze(grid)
    return None if info["errors"] else info


def _witness_horizontal_occluder(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and info["occluder"] == "horizontal"


def _witness_vertical_occluder(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and info["occluder"] == "vertical"


def _witness_multi_cell_overlap(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and info["overlap_area"] > 1


def _witness_off_center_crossing(grid: Any) -> bool:
    info = _facts_or_none(grid)
    return info is not None and (
        info["horizontal_position"] != "center"
        or info["vertical_position"] != "center"
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "horizontal_occluder": _witness_horizontal_occluder,
    "vertical_occluder": _witness_vertical_occluder,
    "multi_cell_overlap": _witness_multi_cell_overlap,
    "off_center_crossing": _witness_off_center_crossing,
}


def _validated_copy(grid: Any) -> tuple[list[list[int]], dict[str, Any]]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return deepcopy(info["grid"]), info


def _identity(grid: Any) -> list[list[int]]:
    output, _ = _validated_copy(grid)
    return output


def _always_horizontal(grid: Any) -> list[list[int]]:
    output, info = _validated_copy(grid)
    for r in info["horizontal_rows"]:
        for c in info["vertical_cols"]:
            output[r][c] = info["horizontal_color"]
    return output


def _always_vertical(grid: Any) -> list[list[int]]:
    output, info = _validated_copy(grid)
    for r in info["horizontal_rows"]:
        for c in info["vertical_cols"]:
            output[r][c] = info["vertical_color"]
    return output


def _single_cell_overlap(grid: Any) -> list[list[int]]:
    output, info = _validated_copy(grid)
    other = (
        info["vertical_color"]
        if info["occluder"] == "horizontal"
        else info["horizontal_color"]
    )
    output[info["horizontal_rows"][0]][info["vertical_cols"][0]] = other
    return output


def _center_crossings_only(grid: Any) -> list[list[int]]:
    output, info = _validated_copy(grid)
    if (
        info["horizontal_position"] == "center"
        and info["vertical_position"] == "center"
    ):
        return rule_mirror(grid)
    return output


_LEGACY_GEOMETRY_OCCLUDER = {
    (1, 1, "center", "center"): "horizontal",
    (1, 1, "top", "right"): "vertical",
    (2, 1, "bottom", "left"): "horizontal",
    (1, 2, "center", "center"): "vertical",
    (3, 2, "top", "right"): "horizontal",
    (2, 2, "bottom", "left"): "vertical",
}


def _geometry_only_occluder(grid: Any) -> list[list[int]]:
    """Wrong rule that predicts depth from geometry, not overlap color."""
    output, info = _validated_copy(grid)
    key = (
        info["horizontal_thickness"],
        info["vertical_thickness"],
        info["horizontal_position"],
        info["vertical_position"],
    )
    predicted_occluder = _LEGACY_GEOMETRY_OCCLUDER.get(key, "horizontal")
    predicted_back_color = (
        info["vertical_color"]
        if predicted_occluder == "horizontal"
        else info["horizontal_color"]
    )
    for row in info["horizontal_rows"]:
        for col in info["vertical_cols"]:
            output[row][col] = predicted_back_color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "always_horizontal_on_top": _always_horizontal,
    "always_vertical_on_top": _always_vertical,
    "single_cell_overlap": _single_cell_overlap,
    "center_crossings_only": _center_crossings_only,
}
WITNESS_RIVALS = {
    "horizontal_occluder": ["identity", "always_horizontal_on_top"],
    "vertical_occluder": ["identity", "always_vertical_on_top"],
    "multi_cell_overlap": ["single_cell_overlap"],
    "off_center_crossing": ["center_crossings_only"],
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "geometry_only_occluder": _geometry_only_occluder,
}
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Reject lessons that leave a declared plausible wrong rule alive."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence"]
    episodes = [(f"demo {i}", episode) for i, episode in enumerate(demos)]
    episodes.append(("query", query))

    for label, episode in episodes:
        if not isinstance(episode, dict) or "input" not in episode:
            reasons.append(f"{label}: malformed episode")
            continue
        try:
            truth = rule_mirror(episode["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"{label}: input outside rule domain: {exc}")
            continue
        provided = episode.get("output")
        if label.startswith("demo") and provided != truth:
            reasons.append(f"{label}: output does not match the crossing-bar rule")
        elif label == "query" and provided is not None and provided != truth:
            reasons.append("query: provided output does not match the crossing-bar rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo.get("output") for demo in demos
            )
            competitor_query = competitor(query["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"competing rule {name!r} raised: {exc}")
            continue
        if survives and competitor_query != query_truth:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named task-local impostors proving self_check is mutation-sensitive."""
    valid = generate(
        7001,
        3,
        difficulty="hard",
        grid_h=11,
        grid_w=10,
        horizontal_thickness=2,
        vertical_thickness=2,
        horizontal_position="center",
        vertical_position="center",
        horizontal_color=2,
        vertical_color_offset=3,
        occluder="horizontal",
    )
    info = _analyze(valid)
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_horizontal_cell = deepcopy(valid)
    r = info["horizontal_rows"][0]
    c = next(c for c in range(info["grid_w"]) if c not in info["vertical_cols"])
    missing_horizontal_cell[r][c] = 0
    fixtures.append(("missing_horizontal_cell", missing_horizontal_cell))

    isolated_pixel = deepcopy(valid)
    isolated_pixel[0][0] = 9 if 9 not in (info["horizontal_color"], info["vertical_color"]) else 8
    fixtures.append(("isolated_pixel", isolated_pixel))

    mixed_overlap = deepcopy(valid)
    r0, r1 = info["horizontal_rows"][:2]
    c0 = info["vertical_cols"][0]
    mixed_overlap[r0][c0] = info["horizontal_color"]
    mixed_overlap[r1][c0] = info["vertical_color"]
    fixtures.append(("mixed_overlap", mixed_overlap))

    same_color_bars = deepcopy(valid)
    for c in info["vertical_cols"]:
        for r in range(info["grid_h"]):
            same_color_bars[r][c] = info["horizontal_color"]
    fixtures.append(("same_color_bars", same_color_bars))

    short_vertical_bar = deepcopy(valid)
    c0 = info["vertical_cols"][0]
    short_vertical_bar[0][c0] = 0
    fixtures.append(("short_vertical_bar", short_vertical_bar))

    foreign_overlap_color = deepcopy(valid)
    for r in info["horizontal_rows"]:
        for c in info["vertical_cols"]:
            foreign_overlap_color[r][c] = 9 if 9 not in (info["horizontal_color"], info["vertical_color"]) else 8
    fixtures.append(("foreign_overlap_color", foreign_overlap_color))
    return fixtures
