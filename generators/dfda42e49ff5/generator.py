"""Generator for ARC task dfda42e49ff5 — fill each object's row gaps.

For every same-color four-connected object, independently fill each occupied
row from that object's leftmost cell through its rightmost cell.  The schedule
contains one canonical-scale single-object scene and three richer scenes with
disconnected same-color objects.  Those richer scenes are decisive against the
strong canonical shortcut "treat each color as one object".
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import (
    components,
    components_have_clearance,
    has_row_gap,
)

GENERATOR_ID = "dfda42e49ff5"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "2241d1285117"

SUMMARY = (
    "Fill horizontal gaps independently inside every same-color four-connected "
    "object.  A four-scene schedule preserves canonical one-object examples and "
    "adds disconnected same-color witnesses and row-varying object boundaries "
    "that separate the intended rule from color-merging and right-alignment shortcuts."
)

INVARIANTS = [
    "background is literal color 0 and every foreground value is an ARC color 1..9",
    "foreground objects are same-color four-connected components separated by a one-cell moat",
    "every object has at least one occupied row with a genuine horizontal internal gap",
    "row spans are filled per connected object, never across disconnected objects that share a color",
    "generated objects vary their occupied-row right boundary, so rows are not extended to a component-wide edge",
    "every four consecutive samples contain one canonical single-object scene and three decisive multi-object scenes",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical_single",
    "same_color_pair",
    "same_color_trio",
    "mixed_cluster",
)
SCHEDULE_PROFILES = SCENE_PROFILES
CANONICAL_PROFILES = ((5, 7), (5, 8), (5, 9))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile sample-index cycle",
        "valid": "canonical_single|same_color_pair|same_color_trio|mixed_cluster",
        "doc": (
            "canonical_single has one canonical-scale object; same_color_pair "
            "and same_color_trio contain disconnected objects of one color on "
            "overlapping rows; mixed_cluster adds a second color."
        ),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the public four-slot curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _component_rows(component: dict[str, Any]) -> dict[int, list[int]]:
    by_row: dict[int, list[int]] = defaultdict(list)
    for row, column in component["cells"]:
        by_row[row].append(column)
    return dict(by_row)


def _fill_component_rows(output: list[list[int]], component: dict[str, Any]) -> None:
    for row, columns in _component_rows(component).items():
        for column in range(min(columns), max(columns) + 1):
            output[row][column] = component["color"]


def _profile_from_components(found: Sequence[dict[str, Any]]) -> str | None:
    signature = (len(found), len({component["color"] for component in found}))
    return {
        (1, 1): "canonical_single",
        (2, 1): "same_color_pair",
        (3, 1): "same_color_trio",
        (3, 2): "mixed_cluster",
    }.get(signature)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "components": (), "scene_profile": None}

    height, width = len(grid), len(grid[0])
    found = components(grid, same_color=True, connectivity=4)
    if not found:
        errors.append("at least one foreground object is required")
    if len(found) > 6:
        errors.append("at most six foreground objects are supported")
    if found and not components_have_clearance(grid, found, diagonal=True):
        errors.append("distinct objects must have a one-cell zero moat, including diagonals")
    for index, component in enumerate(found):
        if not has_row_gap(component["cells"]):
            errors.append(f"object {index} has no horizontal internal gap")

    output = [list(row) for row in grid]
    for component in found:
        _fill_component_rows(output, component)

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "components": tuple(found),
        "component_count": len(found),
        "color_count": len({component["color"] for component in found}),
        "scene_profile": _profile_from_components(found),
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the live rule domain, including canonical one-object inputs."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["unknown difficulty"]
    info = _analysis(grid)
    errors = list(info["errors"])
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is not None and not errors and info["scene_profile"] != requested:
        errors.append(
            f"scene profile drifted from {requested!r} to {info['scene_profile']!r}"
        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The canonical rule grammar is exactly the live self-check grammar."""
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, str]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    profile = info["scene_profile"]
    if profile is None:
        raise ValueError(
            f"component/color signature {(info['component_count'], info['color_count'])} "
            "does not identify a declared scene profile"
        )
    return {"scene_profile": profile}


def _make_motif(
    rng,
    height: int,
    width: int,
    *,
    connector: str = "bottom",
) -> tuple[tuple[int, int], ...]:
    """Build a connected, row-gappy motif with row-specific boundaries.

    A solid connector row joins two vertical anchor runs.  The nonconnector
    rows keep those anchors for four-connectivity but alternate optional outer
    cells, so at least one row ends before the component's global right edge
    and another reaches it.  Random inward extensions preserve a gap of at
    least two cells.  This makes the row bounds, rather than a component-wide
    bounding edge or a fixed template, causally necessary.
    """
    if height < 3 or width < 5:
        raise ValueError("motifs require height >= 3 and width >= 5")
    if connector not in ("top", "bottom"):
        raise ValueError(f"unknown connector side: {connector!r}")

    connector_row = 0 if connector == "top" else height - 1
    cells = {(connector_row, column) for column in range(width)}
    gappy_rows = [row for row in range(height) if row != connector_row]

    # Width five needs the left anchor at the outer edge to retain a two-cell
    # internal gap.  Wider motifs can also vary their left boundary.
    left_anchor = 0 if width == 5 else 1
    right_anchor = width - 2
    inward_slack = right_anchor - left_anchor - 3
    if inward_slack < 0:
        raise AssertionError("motif anchors must leave a two-cell gap")

    for position, row in enumerate(gappy_rows):
        # Force distinct row bounds in every motif; extra rows remain random.
        left_outer = left_anchor > 0 and (position == 0 or (position >= 2 and rng.choice((False, True))))
        right_outer = position == 1 or (position >= 2 and rng.choice((False, True)))

        left_start = left_anchor - int(left_outer)
        right_end = right_anchor + int(right_outer)

        left_extra = rng.randint(0, inward_slack) if inward_slack else 0
        remaining = inward_slack - left_extra
        right_extra = rng.randint(0, remaining) if remaining else 0
        left_end = left_anchor + left_extra
        right_start = right_anchor - right_extra

        for column in range(left_start, left_end + 1):
            cells.add((row, column))
        for column in range(right_start, right_end + 1):
            cells.add((row, column))

    motif = tuple(sorted(cells))
    if not has_row_gap(motif):
        raise AssertionError("constructed motif lost its row gap")
    return motif


def _paint(grid: list[list[int]], motif: Iterable[tuple[int, int]], row0: int, column0: int, color: int) -> None:
    for row, column in motif:
        target_row, target_column = row0 + row, column0 + column
        if grid[target_row][target_column] != 0:
            raise AssertionError("motif placement overlap")
        grid[target_row][target_column] = color


def _rich_dimensions(rng, band: str) -> tuple[int, int]:
    bounds = {
        "easy": ((7, 9), (11, 14)),
        "medium": ((8, 12), (11, 17)),
        "hard": ((10, 16), (14, 20)),
    }[band]
    return rng.randint(*bounds[0]), rng.randint(*bounds[1])


def _pair_widths(rng, width: int) -> tuple[int, int, int, int]:
    separation = rng.randint(1, min(3, width - 10))
    available = width - separation
    max_first = min(8, available - 5)
    first = rng.randint(5, max_first)
    second = rng.randint(5, min(8, available - first))
    slack = width - first - separation - second
    start = rng.randint(0, slack)
    return first, second, separation, start


def _construct_canonical_single(ctx, sample_index: int, rng) -> list[list[int]]:
    height, width = CANONICAL_PROFILES[(sample_index // len(SCHEDULE_PROFILES)) % len(CANONICAL_PROFILES)]
    colors = ctx.draw_distinct_colors("foreground_palette", n=2, exclude={0})
    motif_width = width - 2
    motif = _make_motif(rng, 3, motif_width, connector=rng.choice(("top", "bottom")))
    grid = full_grid(height, width, 0)
    _paint(grid, motif, 1, 1, colors[0])
    return grid


def _construct_rich(ctx, profile: str, band: str, rng) -> list[list[int]]:
    height, width = _rich_dimensions(rng, band)
    colors = ctx.draw_distinct_colors("foreground_palette", n=2, exclude={0})
    first_width, second_width, separation, first_column = _pair_widths(rng, width)

    has_third = profile in ("same_color_trio", "mixed_cluster")
    if has_third:
        pair_height = min(rng.randint(3, 5), (height - 1) // 2)
        pair_height = max(3, pair_height)
        vertical_slack = height - (2 * pair_height + 1)
        pair_row = rng.randint(0, vertical_slack)
        third_row = pair_row + pair_height + 1
    else:
        pair_height = rng.randint(3, min(5, height))
        pair_row = rng.randint(0, height - pair_height)
        third_row = -1

    first = _make_motif(rng, pair_height, first_width, connector=rng.choice(("top", "bottom")))
    second = _make_motif(rng, pair_height, second_width, connector=rng.choice(("top", "bottom")))
    second_column = first_column + first_width + separation

    grid = full_grid(height, width, 0)
    _paint(grid, first, pair_row, first_column, colors[0])
    _paint(grid, second, pair_row, second_column, colors[0])

    if has_third:
        third_width = rng.randint(5, min(9, width))
        third_height = pair_height
        third_column = rng.randint(0, width - third_width)
        connector = rng.choice(("top", "bottom"))
        third = _make_motif(rng, third_height, third_width, connector=connector)
        third_color = colors[0] if profile == "same_color_trio" else colors[1]
        _paint(grid, third, third_row, third_column, third_color)

    return grid


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    options = SCENE_PROFILES if overrides.get("scene_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    rng = ctx.draw_rng(f"construction:{profile}:{band}")

    if profile == "canonical_single":
        grid = _construct_canonical_single(ctx, sample_index, rng)
    else:
        grid = _construct_rich(ctx, profile, band, rng)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {"scene_profile": profile}},
    )
    if errors:
        raise RuntimeError(f"constructed invalid {profile!r} scene: {errors}")
    return [row[:] for row in grid]


def rule_mirror(grid: Any) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [list(row) for row in info["output"]]


def _per_color_row_span(grid: Any) -> list[list[int]]:
    """Wrong shortcut: merge disconnected components that share a color."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    by_color_row: dict[tuple[int, int], list[int]] = defaultdict(list)
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color:
                by_color_row[(color, row)].append(column)
    for (color, row), columns in by_color_row.items():
        for column in range(min(columns), max(columns) + 1):
            output[row][column] = color
    return output


def _largest_component_only(grid: Any) -> list[list[int]]:
    """Wrong shortcut: transform only the largest object."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    if info["components"]:
        largest = max(
            info["components"],
            key=lambda component: (len(component["cells"]), tuple(sorted(component["cells"]))),
        )
        _fill_component_rows(output, largest)
    return output


def _component_bbox_fill(grid: Any) -> list[list[int]]:
    """Wrong shortcut: fill each object's whole bounding rectangle."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    for component in info["components"]:
        row1, column1, row2, column2 = component["bbox"]
        for row in range(row1, row2 + 1):
            for column in range(column1, column2 + 1):
                output[row][column] = component["color"]
    return output


def _component_global_right_span(grid: Any) -> list[list[int]]:
    """Wrong shortcut: extend every occupied object row to its global right edge."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    for component in info["components"]:
        right = max(column for _, column in component["cells"])
        for row, columns in _component_rows(component).items():
            for column in range(min(columns), right + 1):
                output[row][column] = component["color"]
    return output


def _one_cell_per_gap(grid: Any) -> list[list[int]]:
    """Wrong shortcut: patch only the first missing cell in each gappy row."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    for component in info["components"]:
        cells = set(component["cells"])
        for row, columns in _component_rows(component).items():
            for column in range(min(columns), max(columns) + 1):
                if (row, column) not in cells:
                    output[row][column] = component["color"]
                    break
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "per_color_row_span": _per_color_row_span,
    "largest_component_only": _largest_component_only,
    "component_bbox_fill": _component_bbox_fill,
    "component_global_right_span": _component_global_right_span,
    "one_cell_per_gap": _one_cell_per_gap,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "per_color_row_span": _per_color_row_span,
    "largest_component_only": _largest_component_only,
    "component_global_right_span": _component_global_right_span,
}


def _same_color_disconnected_row_overlap(grid: Any) -> bool:
    info = _analysis(grid)
    return not info["errors"] and _per_color_row_span(grid) != info["output"]


def _multiple_changed_objects(grid: Any) -> bool:
    info = _analysis(grid)
    if info["errors"]:
        return False
    changed = 0
    for component in info["components"]:
        probe = [list(row) for row in grid]
        _fill_component_rows(probe, component)
        if probe != grid:
            changed += 1
    return changed >= 2


def _row_bounds_not_component_bbox(grid: Any) -> bool:
    info = _analysis(grid)
    return not info["errors"] and _component_bbox_fill(grid) != info["output"]


def _row_right_bound_not_component_right(grid: Any) -> bool:
    info = _analysis(grid)
    return not info["errors"] and _component_global_right_span(grid) != info["output"]


def _wide_row_gap(grid: Any) -> bool:
    info = _analysis(grid)
    if info["errors"]:
        return False
    for component in info["components"]:
        cells = set(component["cells"])
        for row, columns in _component_rows(component).items():
            missing = sum(
                (row, column) not in cells
                for column in range(min(columns), max(columns) + 1)
            )
            if missing >= 2:
                return True
    return False


SEMANTIC_WITNESSES = {
    "same_color_disconnected_row_overlap": _same_color_disconnected_row_overlap,
    "multiple_changed_objects": _multiple_changed_objects,
    "row_bounds_not_component_bbox": _row_bounds_not_component_bbox,
    "row_right_bound_not_component_right": _row_right_bound_not_component_right,
    "wide_row_gap": _wide_row_gap,
}
WITNESS_RIVALS = {
    "same_color_disconnected_row_overlap": ["per_color_row_span"],
    "multiple_changed_objects": ["largest_component_only"],
    "row_bounds_not_component_bbox": ["component_bbox_fill"],
    "row_right_bound_not_component_right": ["component_global_right_span"],
    "wide_row_gap": ["one_cell_per_gap"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a labelled lesson if any declared plausible rival survives."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"pair {index} is not an input/output mapping")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the rule domain: {exc}")
            continue
        if "output" in pair and pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with the object-row-span rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair.get("output") for pair in demos)
        except Exception as exc:  # defensive: semantic diagnostics should report, not crash
            reasons.append(f"competitor {name!r} crashed: {exc}")
            continue
        if survives:
            reasons.append(f"demonstrations fail to refute rival {name!r}")
    return reasons
