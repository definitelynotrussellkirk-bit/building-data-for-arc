"""Semantic generator for ARC task 563e1df172df.

A lawful input has one red cell and one green cell on different rows and
columns.  The output preserves both endpoints and paints color 8 along the
red row to the green column, then along that column to the green cell.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "563e1df172df"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "a29452f21143"

SUMMARY = (
    "Connect the unique red(2) and green(3) cells with an 8-colored L: "
    "paint horizontally from red to green's column, then vertically to green."
)

INVARIANTS = [
    "background is color 0",
    "the input contains exactly one red(2) cell and one green(3) cell",
    "the endpoints occupy different rows and different columns",
    "the output preserves both endpoints and changes only the intended L-path to 8",
]

_GRID_SHAPES = {
    "10x16": (10, 16),
    "12x14": (12, 14),
    "15x15": (15, 15),
}
_DIRECTIONS = ("northwest", "northeast", "southwest", "southeast")
_DISTANCE_BANDS = ("near", "medium", "far")
_DISTANCE_LIMITS = {
    "near": (2, 5),
    "medium": (6, 10),
    "far": (11, 18),
}

# The five-slot gap cycle is coprime to the four endpoint quadrants. This
# prevents a quadrant from always receiving the same degenerate arm geometry.
# The initial strong northwest case also supports older four-demo consumers.
_GAP_MODES = (
    "both_nontrivial",
    "unit_row_gap",
    "unit_column_gap",
    "both_nontrivial",
    "both_nontrivial",
)

# One exact caller-facing control.  Each value names a recoverable combination
# of grid profile, relative endpoint quadrant, and Manhattan-distance band.
_PROFILE_ROWS = (
    ("10x16_northwest_near", "10x16", "northwest", "near"),
    ("15x15_northeast_medium", "15x15", "northeast", "medium"),
    ("12x14_southwest_far", "12x14", "southwest", "far"),
    ("10x16_southeast_near", "10x16", "southeast", "near"),
    ("12x14_northwest_medium", "12x14", "northwest", "medium"),
    ("10x16_northeast_far", "10x16", "northeast", "far"),
    ("15x15_southwest_near", "15x15", "southwest", "near"),
    ("12x14_southeast_medium", "12x14", "southeast", "medium"),
    ("15x15_northwest_far", "15x15", "northwest", "far"),
    ("12x14_northeast_near", "12x14", "northeast", "near"),
    ("10x16_southwest_medium", "10x16", "southwest", "medium"),
    ("15x15_southeast_far", "15x15", "southeast", "far"),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
# Semantic schedule period: lcm(twelve profiles, five gap modes).
# Exact positions still depend on the seed and sample index, not just residue.
LESSON_SCHEDULE_PERIOD = 60
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {row[1:]: row[0] for row in _PROFILE_ROWS}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic twelve-profile curriculum",
        "valid": "10x16_northwest_near|15x15_northeast_medium|12x14_southwest_far|10x16_southeast_near|12x14_northwest_medium|10x16_northeast_far|15x15_southwest_near|12x14_southeast_medium|15x15_northwest_far|12x14_northeast_near|10x16_southwest_medium|15x15_southeast_far",
    }
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
MIN_STRICT_FRAC = 1.0
# Twelve consecutive pairs contain three of each quadrant. A quadrant's gap
# residues step by four modulo five, so at most one of its three pairs has a
# unit row gap, and at most one has a unit column gap. Any single query holdout
# therefore leaves an interior witness for both arms in every quadrant.
EXAMPLES_NEEDED = 11
MIN_IDENTIFYING_DEMONSTRATIONS = 4


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle profiles so every four consecutive demos cover all quadrants."""
    del seed
    offset = {"easy": 0, "medium": 4, "hard": 8}[_band(difficulty)]
    return SCENE_PROFILES[(int(sample_index) + offset) % len(SCENE_PROFILES)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 2 <= len(grid) <= 30 or not 2 <= width <= 30:
        return [f"grid dimensions must be in 2..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _direction(rr: int, rc: int, gr: int, gc: int) -> str:
    vertical = "north" if rr < gr else "south"
    horizontal = "west" if rc < gc else "east"
    return vertical + horizontal


def _distance_band(distance: int) -> str | None:
    for name, (lo, hi) in _DISTANCE_LIMITS.items():
        if lo <= distance <= hi:
            return name
    return None


def _shape_name(height: int, width: int) -> str | None:
    for name, shape in _GRID_SHAPES.items():
        if shape == (height, width):
            return name
    return None


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    reds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    greens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    extras = sorted({value for row in grid for value in row if value not in (0, 2, 3)})
    if len(reds) != 1:
        errors.append(f"expected exactly one red(2) cell, found {len(reds)}")
    if len(greens) != 1:
        errors.append(f"expected exactly one green(3) cell, found {len(greens)}")
    if extras:
        errors.append(f"unexpected input colors: {extras}")
    if len(reds) != 1 or len(greens) != 1:
        return {"errors": errors, "height": height, "width": width}
    rr, rc = reds[0]
    gr, gc = greens[0]
    if rr == gr:
        errors.append("red and green must occupy different rows")
    if rc == gc:
        errors.append("red and green must occupy different columns")
    distance = abs(rr - gr) + abs(rc - gc)
    direction = _direction(rr, rc, gr, gc) if rr != gr and rc != gc else None
    distance_band = _distance_band(distance)
    shape_name = _shape_name(height, width)
    profile = _PROFILE_BY_SIGNATURE.get((shape_name, direction, distance_band))
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "red": (rr, rc),
        "green": (gr, gc),
        "direction": direction,
        "distance": distance,
        "distance_band": distance_band,
        "shape_name": shape_name,
        "scene_profile": profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority-valid grammar and reject malformed/ambiguous inputs."""
    del difficulty
    analysis = _analysis(grid)
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


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the declared exact profile from a returned generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def strict_canonical_like(grid) -> list[str]:
    """Generated lessons stay on the three grid profiles present canonically."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["shape_name"] is None:
        return ["grid shape is outside the canonical 10x16/12x14/15x15 profiles"]
    return []


def rule_mirror(grid):
    """Independent Python mirror; the synchronized Racket rule remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    rr, rc = analysis["red"]
    gr, gc = analysis["green"]
    output = [list(row) for row in grid]
    for col in range(min(rc, gc), max(rc, gc) + 1):
        if col != rc:
            output[rr][col] = 8
    for row in range(min(rr, gr), max(rr, gr) + 1):
        if row != gr:
            output[row][gc] = 8
    return output


def _rival_vertical_first(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    rr, rc = analysis["red"]
    gr, gc = analysis["green"]
    output = [list(row) for row in grid]
    for row in range(min(rr, gr), max(rr, gr) + 1):
        if row != rr:
            output[row][rc] = 8
    for col in range(min(rc, gc), max(rc, gc) + 1):
        if col != gc:
            output[gr][col] = 8
    return output


def _rival_horizontal_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    rr, rc = analysis["red"]
    _gr, gc = analysis["green"]
    output = [list(row) for row in grid]
    for col in range(min(rc, gc), max(rc, gc) + 1):
        if col != rc:
            output[rr][col] = 8
    return output


def _rival_vertical_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    rr, _rc = analysis["red"]
    gr, gc = analysis["green"]
    output = [list(row) for row in grid]
    for row in range(min(rr, gr), max(rr, gr) + 1):
        if row != gr:
            output[row][gc] = 8
    return output


def _rival_northwest_horizontal_only(grid):
    if _analysis(grid).get("direction") == "northwest":
        return _rival_horizontal_only(grid)
    return rule_mirror(grid)


def _rival_northeast_vertical_only(grid):
    if _analysis(grid).get("direction") == "northeast":
        return _rival_vertical_only(grid)
    return rule_mirror(grid)


def _rival_horizontal_first_only_when_far(grid):
    if _analysis(grid).get("distance_band") == "far":
        return rule_mirror(grid)
    return _rival_vertical_first(grid)


def _rival_southeast_vertical_first(grid):
    if _analysis(grid).get("direction") == "southeast":
        return _rival_vertical_first(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "green_row_elbow_vertical_first": _rival_vertical_first,
    "horizontal_arm_only": _rival_horizontal_only,
    "vertical_arm_only": _rival_vertical_only,
    "northwest_horizontal_arm_only": _rival_northwest_horizontal_only,
    "northeast_vertical_arm_only": _rival_northeast_vertical_only,
}
# Canonical pairs are all far apart and contain no southeast red endpoint.
# Direct arm-only and unconditional opposite-elbow rivals do NOT fit them.
CANONICAL_SHORTCUTS = {
    "horizontal_first_only_when_far": _rival_horizontal_first_only_when_far,
    "southeast_vertical_first": _rival_southeast_vertical_first,
}
SEMANTIC_RIVALS.update(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**SEMANTIC_RIVALS, **CANONICAL_SHORTCUTS}
WITNESS_RIVALS = {
    "red_northwest": ["green_row_elbow_vertical_first"],
    "red_northeast": ["green_row_elbow_vertical_first"],
    "red_southwest": ["green_row_elbow_vertical_first"],
    "red_southeast": ["green_row_elbow_vertical_first", "southeast_vertical_first"],
    "nonfar_elbow": ["horizontal_first_only_when_far"],
}


def _witness_direction(name: str):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and analysis["direction"] == name
    return witness


def _witness_distance(name: str):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and analysis["distance_band"] == name
    return witness


def _witness_nonfar_elbow(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["distance_band"] in ("near", "medium")


SEMANTIC_WITNESSES = {
    "red_northwest": _witness_direction("northwest"),
    "red_northeast": _witness_direction("northeast"),
    "red_southwest": _witness_direction("southwest"),
    "red_southeast": _witness_direction("southeast"),
    "near_distance": _witness_distance("near"),
    "medium_distance": _witness_distance("medium"),
    "far_distance": _witness_distance("far"),
    "nonfar_elbow": _witness_nonfar_elbow,
}

# These predicates prove the scheduled distance branches are present.  They do
# not, by themselves, assert that a named rival must disagree on every firing.
BRANCH_WITNESSES = {"near_distance", "medium_distance", "far_distance"}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut survives every demonstration."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < MIN_IDENTIFYING_DEMONSTRATIONS:
        return [f"need at least {MIN_IDENTIFYING_DEMONSTRATIONS} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the red-row-elbow rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the red-row-elbow rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def _gap_mode(sample_index: int) -> str:
    return _GAP_MODES[int(sample_index) % len(_GAP_MODES)]


def _pick_gaps(
    distance_band: str,
    height: int,
    width: int,
    gap_mode: str,
    rng,
):
    lo, hi = _DISTANCE_LIMITS[distance_band]

    def feasible_for(mode: str) -> list[tuple[int, int]]:
        return [
            (dr, dc)
            for dr in range(1, height)
            for dc in range(1, width)
            if lo <= dr + dc <= hi
            and (
                (mode == "unit_row_gap" and dr == 1 and dc > 1)
                or (mode == "unit_column_gap" and dr > 1 and dc == 1)
                or (mode == "both_nontrivial" and dr > 1 and dc > 1)
            )
        ]

    feasible = feasible_for(gap_mode)
    if not feasible and gap_mode != "both_nontrivial":
        # Some rectangular far-distance profiles cannot realize one orientation
        # of unit arm.  A strong two-arm witness is always the safe replacement.
        feasible = feasible_for("both_nontrivial")
    if not feasible:
        raise ValueError(
            f"no endpoint gaps for {height}x{width} in distance band "
            f"{distance_band} and gap mode {gap_mode}"
        )
    return rng.choice(feasible)


def _place_endpoints(direction: str, height: int, width: int, dr: int, dc: int, rng):
    top = rng.randint(0, height - dr - 1)
    left = rng.randint(0, width - dc - 1)
    bottom = top + dr
    right = left + dc
    if direction == "northwest":
        return top, left, bottom, right
    if direction == "northeast":
        return top, right, bottom, left
    if direction == "southwest":
        return bottom, left, top, right
    if direction == "southeast":
        return bottom, right, top, left
    raise ValueError(f"unknown direction: {direction!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    shape_name, direction, distance_band = _PROFILE_BY_NAME[profile]
    height, width = _GRID_SHAPES[shape_name]
    rng = ctx.draw_rng("placement")
    gap_mode = _gap_mode(sample_index)
    dr, dc = _pick_gaps(distance_band, height, width, gap_mode, rng)
    rr, rc, gr, gc = _place_endpoints(direction, height, width, dr, dc, rng)
    grid = full_grid(height, width, 0)
    grid[rr][rc] = 2
    grid[gr][gc] = 3
    return grid
