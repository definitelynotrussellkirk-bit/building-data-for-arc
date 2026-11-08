"""Generate rich examples of completing same-colour adjacent diagonals.

The canonical rule examines each non-zero colour independently.  Whenever two
cells of that colour occupy opposite corners of an adjacent 2x2 window, the
whole window is painted that colour.  The source cells are read from the
original input while writes accumulate in first-colour-appearance order.

The public ARC examples contain only isolated pairs with empty companion
corners.  Every generated teaching scene deliberately also contains:

* a colour participating in two adjacent diagonal pairs,
* another colour in companion corners that the rule must overwrite, and
* a diagonally adjacent unequal-colour control that must not trigger.

Those witnesses distinguish the authority from the strongest shortcuts that
fit all published examples while retaining the three canonical
(height, width, palette-size) profiles in every difficulty band.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b37eb391ddc0"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "24318a9ceacd"

SUMMARY = (
    "Complete every adjacent 2x2 whose opposite corners have the same nonzero "
    "colour, overwriting either companion corner; unequal-colour diagonals are "
    "controls and remain inactive."
)

INVARIANTS = [
    "background is colour 0 and all cells are literal ARC integers 0..9",
    "at least one same-colour adjacent diagonal changes the output",
    "generated scenes contain both diagonal orientations",
    "generated scenes include occupied companions, repeated-pair colours, and unequal-colour diagonal controls",
]

_PROFILE_ROWS = (
    ("rich_7x8_p3", 7, 8, 3),
    ("rich_8x8_p3", 8, 8, 3),
    ("rich_8x9_p4", 8, 9, 4),
)
_PROFILE_BY_NAME = {
    name: (height, width, palette_size)
    for name, height, width, palette_size in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (height, width, palette_size): name
    for name, height, width, palette_size in _PROFILE_ROWS
}
SCENE_PROFILES = tuple(name for name, _height, _width, _palette in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic three-profile canonical-scale curriculum",
        "valid": "rich_7x8_p3|rich_8x8_p3|rich_8x9_p4",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 2

Grid = list[list[int]]
Cell = tuple[int, int]
Pair = dict[str, Any]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact linked profile at this curriculum position."""
    del seed
    band = _band(difficulty)
    offset = {"easy": 0, "medium": 1, "hard": 2}[band]
    return SCENE_PROFILES[(int(sample_index) + offset) % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides:
        profile = overrides["scene_profile"]
        if not isinstance(profile, str) or profile not in _PROFILE_BY_NAME:
            raise ValueError(f"unknown scene_profile: {profile!r}")


def _transform_local(row: int, col: int, *, flip_v: bool, flip_h: bool) -> Cell:
    if flip_v:
        row = 1 - row
    if flip_h:
        col = 3 - col
    return row, col


def _safe_singleton_cells(grid: Grid, occupied: set[Cell]) -> list[Cell]:
    height, width = len(grid), len(grid[0])
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
        and all(max(abs(row - rr), abs(col - cc)) > 1 for rr, cc in occupied)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the selected Racket rule owns labels."""
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    scheduled = overrides.get("scene_profile") or schedule_profile(
        seed, sample_index, difficulty=band
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", (scheduled,))
    height, width, palette_size = _PROFILE_BY_NAME[profile]

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(tuple(range(1, 10)), palette_size - 1)
    target_color, companion_color = colors[:2]

    # A 2x4 motif.  A occupies a shallow V and therefore makes one main- and
    # one anti-diagonal target.  B occupies one missing companion and the lower
    # outside corner.  The former must be overwritten; the latter is an
    # unequal-colour diagonal control.  Keeping the second companion empty
    # avoids collapsing all foreground cells into one 4-connected object.
    target_cells = ((0, 0), (0, 2), (1, 1))
    companion_cells = ((1, 0), (1, 3))
    flip_v = bool(layout_rng.getrandbits(1))
    flip_h = bool(layout_rng.getrandbits(1))
    anchor_row = layout_rng.randint(1, height - 3)
    anchor_col = layout_rng.randint(1, width - 5)

    grid = full_grid(height, width, 0)
    occupied: set[Cell] = set()
    for local_cells, color in (
        (target_cells, target_color),
        (companion_cells, companion_color),
    ):
        for local_row, local_col in local_cells:
            dr, dc = _transform_local(
                local_row, local_col, flip_v=flip_v, flip_h=flip_h
            )
            row, col = anchor_row + dr, anchor_col + dc
            grid[row][col] = color
            occupied.add((row, col))

    # The p4 profile needs one additional foreground colour.  Keep it outside
    # the motif's one-cell halo so it cannot create an accidental diagonal.
    for color in colors[2:]:
        candidates = _safe_singleton_cells(grid, occupied)
        if not candidates:
            raise AssertionError("profile left no safe singleton location")
        row, col = layout_rng.choice(candidates)
        grid[row][col] = color
        occupied.add((row, col))

    # Match the canonical foreground-component morphology without weakening the
    # semantic motif.  Safe singletons are more than one Chebyshev step from all
    # existing cells, so each is a separate 4-connected object and cannot form
    # an accidental adjacent diagonal.  Canonical p3 inputs have four objects;
    # the p4 input has six.
    extra_singletons = 1 if palette_size == 3 else 2
    for index in range(extra_singletons):
        candidates = _safe_singleton_cells(grid, occupied)
        if not candidates:
            raise AssertionError("profile left no safe morphology singleton")
        row, col = layout_rng.choice(candidates)
        grid[row][col] = colors[index % len(colors)]
        occupied.add((row, col))

    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise AssertionError(f"constructed {profile!r}, observed {observed!r}")
    findings = teaching_check(grid)
    if findings:
        raise AssertionError("constructed invalid teaching scene: " + "; ".join(findings))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _colour_order(grid: Grid) -> list[int]:
    seen: set[int] = set()
    order: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in seen:
                seen.add(value)
                order.append(value)
    return order


def _positions_by_colour(grid: Grid) -> dict[int, list[Cell]]:
    positions: dict[int, list[Cell]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions.setdefault(value, []).append((row, col))
    return positions


def _pair_record(grid: Grid, color: int, p: Cell, q: Cell, orientation: str) -> Pair:
    row0, row1 = sorted((p[0], q[0]))
    col0, col1 = sorted((p[1], q[1]))
    box = ((row0, col0), (row0, col1), (row1, col0), (row1, col1))
    endpoints = {p, q}
    companions = tuple(cell for cell in box if cell not in endpoints)
    companion_values = tuple(grid[row][col] for row, col in companions)
    return {
        "color": color,
        "p": p,
        "q": q,
        "orientation": orientation,
        "box": box,
        "companions": companions,
        "companion_values": companion_values,
        "productive": any(value != color for value in companion_values),
    }


def _matching_pairs(grid: Grid) -> list[Pair]:
    positions = _positions_by_colour(grid)
    records: list[Pair] = []
    for color in _colour_order(grid):
        cells = positions[color]
        cell_set = set(cells)
        for row, col in cells:
            for dr, dc, orientation in ((1, 1, "main"), (1, -1, "anti")):
                q = (row + dr, col + dc)
                if q in cell_set:
                    records.append(
                        _pair_record(grid, color, (row, col), q, orientation)
                    )
    return records


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "pairs": [], "positions": {}, "profile": None}
    copied = _copy_grid(grid)
    height, width = len(copied), len(copied[0])
    positions = _positions_by_colour(copied)
    pairs = _matching_pairs(copied)
    palette_size = len({value for row in copied for value in row})
    profile = _PROFILE_BY_SIGNATURE.get((height, width, palette_size))
    if 0 not in {value for row in copied for value in row}:
        errors.append("background colour 0 must be present")
    if not pairs:
        errors.append("expected at least one same-colour adjacent diagonal pair")
    elif not any(pair["productive"] for pair in pairs):
        errors.append("every matching diagonal is already a solid same-colour 2x2")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "positions": positions,
        "pairs": pairs,
        "profile": profile,
        "palette_size": palette_size,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad authority-level input grammar."""
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


def _has_occupied_companion(grid: Grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(
        any(value not in (0, pair["color"]) for value in pair["companion_values"])
        for pair in analysis["pairs"]
    )


def _has_multi_pair_color(grid: Grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    counts = Counter(pair["color"] for pair in analysis["pairs"])
    return any(
        count >= 2 and len(analysis["positions"].get(color, ())) >= 3
        for color, count in counts.items()
    )


def _has_nonmatching_diagonal(grid: Grid) -> bool:
    if _rectangular_errors(grid):
        return False
    height, width = len(grid), len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            tl, tr = grid[row][col], grid[row][col + 1]
            bl, br = grid[row + 1][col], grid[row + 1][col + 1]
            if tl != 0 and br != 0 and tl != br:
                return True
            if tr != 0 and bl != 0 and tr != bl:
                return True
    return False


def _has_both_orientations(grid: Grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and {
        pair["orientation"] for pair in analysis["pairs"]
    } == {"main", "anti"}


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrower, shortcut-refuting production distribution."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["profile"] is None:
        errors.append(
            "teaching scene must match one declared (height,width,palette) profile"
        )
    if not _has_occupied_companion(grid):
        errors.append("teaching scene needs a nonzero wrong-colour companion")
    if not _has_multi_pair_color(grid):
        errors.append("teaching scene needs a colour participating in multiple pairs")
    if not _has_nonmatching_diagonal(grid):
        errors.append("teaching scene needs an unequal-colour diagonal control")
    if not _has_both_orientations(grid):
        errors.append("teaching scene needs both diagonal orientations")
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the complete exact public axis from the returned grid."""
    if _rectangular_errors(grid):
        return {}
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )
    return {"scene_profile": _PROFILE_BY_SIGNATURE.get(signature)}


def canonical_profile_index(grid) -> int | None:
    profile = observe_overrides(grid).get("scene_profile")
    try:
        return SCENE_PROFILES.index(profile)
    except (ValueError, TypeError):
        return None


def _paint_box(output: Grid, record: Pair, color: int) -> None:
    for row, col in record["box"]:
        output[row][col] = color


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror; selected Racket remains label authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    positions = _positions_by_colour(source)
    for color in _colour_order(source):
        cells = positions[color]
        cell_set = set(cells)
        for row, col in cells:
            for dr, dc, orientation in ((1, 1, "main"), (1, -1, "anti")):
                q = (row + dr, col + dc)
                if q in cell_set:
                    _paint_box(
                        output,
                        _pair_record(source, color, (row, col), q, orientation),
                        color,
                    )
    return output


def _rival_isolated_pairs_only(grid: Grid) -> Grid:
    """Old-generator shortcut: act only when both companion corners are zero."""
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    for record in _matching_pairs(source):
        if record["companion_values"] == (0, 0):
            _paint_box(output, record, record["color"])
    return output


def _rival_preserve_occupied(grid: Grid) -> Grid:
    """Complete pairs without overwriting any originally occupied wrong colour."""
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    for record in _matching_pairs(source):
        color = record["color"]
        for row, col in record["box"]:
            if source[row][col] in (0, color):
                output[row][col] = color
    return output


def _rival_first_pair_per_color(grid: Grid) -> Grid:
    """Use only the first row-major diagonal found for each colour."""
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    used: set[int] = set()
    for record in _matching_pairs(source):
        color = record["color"]
        if color in used:
            continue
        used.add(color)
        _paint_box(output, record, color)
    return output


def _rival_exactly_two_occurrences(grid: Grid) -> Grid:
    """Apply the rule only to colours appearing exactly twice."""
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    positions = _positions_by_colour(source)
    for record in _matching_pairs(source):
        color = record["color"]
        if len(positions[color]) == 2:
            _paint_box(output, record, color)
    return output


def _rival_any_nonzero_diagonal(grid: Grid) -> Grid:
    """Wrongly treat unequal nonzero diagonal corners as a triggering pair."""
    source = _copy_grid(grid)
    output = _copy_grid(grid)
    height, width = len(source), len(source[0])
    for row in range(height - 1):
        for col in range(width - 1):
            tl, tr = source[row][col], source[row][col + 1]
            bl, br = source[row + 1][col], source[row + 1][col + 1]
            if tl != 0 and br != 0:
                for rr in (row, row + 1):
                    for cc in (col, col + 1):
                        output[rr][cc] = tl
            if tr != 0 and bl != 0:
                for rr in (row, row + 1):
                    for cc in (col, col + 1):
                        output[rr][cc] = tr
    return output


def strict_canonical_like(grid) -> list[str]:
    """Generated scenes and all published inputs lie in the authority grammar."""
    return self_check(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "occupied_companion": _has_occupied_companion,
    "multi_pair_color": _has_multi_pair_color,
    "nonmatching_diagonal": _has_nonmatching_diagonal,
    "both_orientations": _has_both_orientations,
}
SEMANTIC_RIVALS = {
    "isolated_pairs_only": _rival_isolated_pairs_only,
    "preserve_occupied": _rival_preserve_occupied,
    "first_pair_per_color": _rival_first_pair_per_color,
    "exactly_two_occurrences": _rival_exactly_two_occurrences,
    "any_nonzero_diagonal": _rival_any_nonzero_diagonal,
}
WITNESS_RIVALS = {
    "occupied_companion": ["isolated_pairs_only", "preserve_occupied"],
    "multi_pair_color": ["first_pair_per_color", "exactly_two_occurrences"],
    "nonmatching_diagonal": ["any_nonzero_diagonal"],
}
BRANCH_WITNESSES = ("both_orientations",)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require two correctly labelled rich demos to refute every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = teaching_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the diagonal-completion rule")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = teaching_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the intended rule")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
