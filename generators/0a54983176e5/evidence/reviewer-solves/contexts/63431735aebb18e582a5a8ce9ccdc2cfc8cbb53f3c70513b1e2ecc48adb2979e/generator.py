"""Generator for ARC task 0a54983176e5: axis-marker reflection completion.

Color-8 markers define one reflection axis.  If every marker is in one column,
the axis is vertical; otherwise the markers are in one row and the axis is
horizontal.  Every non-background, non-marker cell is reflected across that
axis only when the destination is still background.  Occupied destinations and
earlier writes therefore win, and out-of-bounds reflections are clipped.

The default three-example lesson schedule always contains both an occupied-
target counterexample and an off-center-axis counterexample.  Those examples
refute the two strongest rules that fit every canonical pair: overwriting an
occupied target and assuming the axis is the geometric grid center.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a54983176e5"
TASK_ID = "0a54983176e5"
VERSION = "3.0.0"
RULE_HASH = "e266f9b65f93"

SUMMARY = (
    "Color-8 markers identify a vertical or horizontal reflection axis. "
    "Every other colored cell mirrors only into background; occupied targets "
    "block the write and out-of-bounds reflections clip.  Exact controls cover "
    "all declared dimensions, both orientations, and five lawful textures. "
    "Every default three-demo window includes an occupied-target witness and "
    "an off-center-axis witness."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "one to three color-8 markers form exactly one row or one column axis",
    "at least one non-{0,8} cell has a visible empty reflection target",
    "occupied reflection targets remain unchanged (first-writer-wins)",
    "off-grid reflection targets are clipped",
]

HELPFUL_TEXTURES = ("plain", "both_sides", "clip", "on_axis", "dense")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted choice over 5..14",
        "valid": "5..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted choice over 7..16",
        "valid": "7..16",
    },
    "orientation": {
        "type": "int",
        "default": "rng 0..1",
        "valid": "0..1",
        "doc": "0 = vertical marker column; 1 = horizontal marker row",
    },
    "texture": {
        "type": "str",
        "default": "nine-step lesson schedule",
        "valid": "plain|both_sides|clip|on_axis|dense",
        "doc": (
            "both_sides blocks at least one reflection with differently "
            "colored content; clip uses an off-center axis; on_axis places "
            "content on the axis; dense increases content count"
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIFFICULTIES = (None, "easy", "medium", "hard")

# Duplicates are deliberate weights.  Every declared value remains present, so
# every exact dimension override is valid in every difficulty band.  The heavy
# canonical-scale mass keeps each band anchored to the observed task manifold.
_HEIGHT_CHOICES = (
    *(6 for _ in range(40)),
    *(7 for _ in range(40)),
    *range(5, 15),
)
_WIDTH_CHOICES = (
    *(9 for _ in range(30)),
    *(10 for _ in range(20)),
    *(11 for _ in range(30)),
    *range(7, 17),
)
_CELL_RANGES = {
    None: (3, 5),
    "easy": (2, 4),
    "medium": (3, 6),
    "hard": (6, 9),
}

SCHEDULE_PROFILES = HELPFUL_TEXTURES


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Texture assigned to an unoverridden sequential sample.

    Every three consecutive indices contain ``both_sides`` and ``clip``.
    The third slot rotates through ordinary, on-axis, and dense examples.
    """
    del seed, difficulty
    residue = sample_index % EXAMPLES_NEEDED
    if residue == 0:
        return "both_sides"
    if residue == 1:
        return "clip"
    return ("plain", "on_axis", "dense")[(sample_index // 3) % 3]


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _axis_facts(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list of rows"]}
    if not all(isinstance(row, list) and row for row in grid):
        return {"errors": ["grid rows must be nonempty lists"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")

    height = len(grid)
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    contents = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    if not markers:
        errors.append("no color-8 axis marker")
        orientation = axis = None
    else:
        marker_rows = sorted({row for row, _ in markers})
        marker_cols = sorted({col for _, col in markers})
        if len(marker_cols) == 1:
            orientation = 0
            axis = marker_cols[0]
        elif len(marker_rows) == 1:
            orientation = 1
            axis = marker_rows[0]
        else:
            orientation = axis = None
            errors.append("color-8 markers must share exactly one row or column")
    if not contents:
        errors.append("no non-{0,8} content cell")

    facts: dict[str, Any] = {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": tuple(markers),
        "marker_count": len(markers),
        "contents": tuple(contents),
        "content_count": len(contents),
        "orientation": orientation,
        "axis": axis,
    }
    if errors or orientation is None or axis is None:
        facts.update(
            {
                "axis_content_cells": 0,
                "blocked_reflections": 0,
                "clipped_reflections": 0,
                "visible_empty_reflections": 0,
            }
        )
        return facts

    axis_content = blocked = clipped = visible = 0
    for row, col, _ in contents:
        target_row, target_col = (
            (row, 2 * axis - col)
            if orientation == 0
            else (2 * axis - row, col)
        )
        if (row, col) == (target_row, target_col):
            axis_content += 1
        elif not (0 <= target_row < height and 0 <= target_col < width):
            clipped += 1
        elif grid[target_row][target_col] == 0:
            visible += 1
        else:
            blocked += 1
    facts.update(
        {
            "axis_content_cells": axis_content,
            "blocked_reflections": blocked,
            "clipped_reflections": clipped,
            "visible_empty_reflections": visible,
        }
    )
    return facts


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Return rule-relevant facts derived only from visible pixels."""
    facts = _axis_facts(grid)
    if not facts["errors"]:
        official = rule_mirror(grid)
        facts["changed_cells"] = sum(
            official[row][col] != grid[row][col]
            for row in range(len(grid))
            for col in range(len(grid[0]))
        )
    else:
        facts["changed_cells"] = 0
    return facts


def _mirror_about(
    grid: list[list[int]],
    orientation: int,
    axis: int,
    *,
    overwrite: bool,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    output = _copy_grid(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 8):
                continue
            target_row, target_col = (
                (row, 2 * axis - col)
                if orientation == 0
                else (2 * axis - row, col)
            )
            if not (0 <= target_row < height and 0 <= target_col < width):
                continue
            if overwrite or output[target_row][target_col] == 0:
                output[target_row][target_col] = value
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    facts = _axis_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _mirror_about(
        grid,
        int(facts["orientation"]),
        int(facts["axis"]),
        overwrite=False,
    )


# Backward-compatible private spelling retained for prior task-local probes.
def _mirror(grid: Any) -> list[list[int]]:
    return rule_mirror(grid)


def _rival_center_axis(grid: Any) -> list[list[int]]:
    facts = _axis_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    orientation = int(facts["orientation"])
    center = facts["width"] // 2 if orientation == 0 else facts["height"] // 2
    return _mirror_about(grid, orientation, center, overwrite=False)


def _rival_overwrite(grid: Any) -> list[list[int]]:
    facts = _axis_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _mirror_about(
        grid,
        int(facts["orientation"]),
        int(facts["axis"]),
        overwrite=True,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "use_grid_center_axis": _rival_center_axis,
    "overwrite_occupied_target": _rival_overwrite,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "markers_not_grid_center": lambda grid: (
        not _axis_facts(grid)["errors"]
        and _rival_center_axis(grid) != rule_mirror(grid)
    ),
    "occupied_target_blocks": lambda grid: (
        not _axis_facts(grid)["errors"]
        and _rival_overwrite(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "markers_not_grid_center": ("use_grid_center_axis",),
    "occupied_target_blocks": ("overwrite_occupied_target",),
}


def _draw_texture(ctx, seed: int, sample_index: int, difficulty, overrides) -> str:
    if "texture" in overrides:
        return str(ctx.draw_choice("texture", HELPFUL_TEXTURES))
    scheduled = schedule_profile(seed, sample_index, difficulty)
    # A singleton choice records honest GenCtx provenance while the union over
    # the nine-step schedule still spans the complete declared enum.
    return str(ctx.draw_choice("texture", (scheduled,)))


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _assign_color(
    grid: list[list[int]],
    position: tuple[int, int],
    palette: tuple[int, ...],
    index: int,
) -> None:
    row, col = position
    grid[row][col] = palette[index % len(palette)]


def _canonical_palette_size(grid_h: int, grid_w: int) -> int | None:
    if (grid_h, grid_w) == (6, 11):
        return 1
    if (grid_h, grid_w) in {(7, 9), (7, 11)}:
        return 2
    return None


def _construct_work_grid(
    *,
    ctx,
    work_h: int,
    work_w: int,
    original_h: int,
    original_w: int,
    vertical: bool,
    texture: str,
    difficulty,
    attempt: int,
) -> list[list[int]]:
    rng = ctx.draw_rng(f"layout:{attempt}")
    center = work_w // 2
    if texture == "clip":
        axis_candidates = [axis for axis in range(1, work_w - 1) if axis != center]
    elif texture == "both_sides":
        axis_candidates = sorted(
            range(1, work_w - 1),
            key=lambda axis: (-min(axis, work_w - 1 - axis), axis),
        )[: max(1, min(3, work_w - 2))]
    else:
        axis_candidates = list(range(1, work_w - 1))
    if not axis_candidates:
        raise ValueError(f"texture {texture!r} cannot fit width {work_w}")
    axis = rng.choice(axis_candidates)

    grid = full_grid(work_h, work_w, 0)
    marker_count = rng.randint(1 if vertical else 2, min(3, work_h))
    marker_rows = rng.sample(range(work_h), marker_count)
    for row in marker_rows:
        grid[row][axis] = 8

    if texture == "clip":
        source_side = 1 if axis < center else -1
    else:
        source_side = rng.choice((-1, 1))
    source_columns = (
        list(range(0, axis)) if source_side < 0 else list(range(axis + 1, work_w))
    )
    all_source = [(row, col) for row in range(work_h) for col in source_columns]
    visible_source = [
        (row, col)
        for row, col in all_source
        if 0 <= 2 * axis - col < work_w
    ]
    clipped_source = [
        (row, col)
        for row, col in all_source
        if not 0 <= 2 * axis - col < work_w
    ]
    if not visible_source:
        raise ValueError("axis leaves no visible reflection source")

    color_count = _canonical_palette_size(original_h, original_w)
    if color_count is None:
        color_count = 1 + rng.randint(0, 1)
    if texture == "both_sides":
        color_count = 2
    palette = tuple(rng.sample(_COLORS, color_count))

    low, high = _CELL_RANGES[difficulty]
    target_count = rng.randint(low, high)
    if texture == "dense":
        target_count = rng.randint(max(7, low), max(10, high))

    source_positions: list[tuple[int, int]] = []
    blocker: tuple[int, int] | None = None
    blocker_color: int | None = None

    if texture == "clip":
        if not clipped_source:
            raise ValueError("off-center axis did not create a clipped source")
        source_positions.extend((rng.choice(visible_source), rng.choice(clipped_source)))
    elif texture == "both_sides":
        blocked_source = rng.choice(visible_source)
        blocker = (blocked_source[0], 2 * axis - blocked_source[1])
        source_positions.append(blocked_source)
        alternatives = [position for position in visible_source if position != blocked_source]
        if not alternatives:
            raise ValueError("both_sides needs a second visible source")
        source_positions.append(rng.choice(alternatives))
    else:
        source_positions.append(rng.choice(visible_source))

    remaining = [position for position in all_source if position not in source_positions]
    rng.shuffle(remaining)
    desired_sources = max(len(source_positions), min(target_count, len(all_source)))
    source_positions.extend(remaining[: desired_sources - len(source_positions)])

    # Preserve first-occurrence palette observability: if two colors were
    # selected, the first two source cells use different colors.
    for index, position in enumerate(source_positions):
        _assign_color(grid, position, palette, index)

    if blocker is not None:
        source_color = grid[source_positions[0][0]][source_positions[0][1]]
        blocker_color = next(color for color in palette if color != source_color)
        grid[blocker[0]][blocker[1]] = blocker_color

    if texture == "on_axis":
        free_axis_rows = [row for row in range(work_h) if grid[row][axis] == 0]
        if not free_axis_rows:
            raise ValueError("no free axis cell for on_axis texture")
        row = rng.choice(free_axis_rows)
        grid[row][axis] = palette[-1]

    output = rule_mirror(grid)
    if output == grid:
        raise ValueError("constructed board does not demonstrate reflection")
    if texture == "both_sides" and _rival_overwrite(grid) == output:
        raise ValueError("both_sides failed to refute overwrite rival")
    if texture == "clip" and _rival_center_axis(grid) == output:
        raise ValueError("clip failed to refute center-axis rival")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy, medium, hard, or None; got {difficulty!r}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h = int(ctx.draw_choice("grid_h", _HEIGHT_CHOICES))
    grid_w = int(ctx.draw_choice("grid_w", _WIDTH_CHOICES))
    orientation = int(ctx.draw_int("orientation", 0, 1))
    texture = _draw_texture(ctx, seed, sample_index, difficulty, overrides)

    vertical = orientation == 0
    work_h, work_w = (grid_h, grid_w) if vertical else (grid_w, grid_h)
    last_error: Exception | None = None
    for attempt in range(160):
        try:
            grid = _construct_work_grid(
                ctx=ctx,
                work_h=work_h,
                work_w=work_w,
                original_h=grid_h,
                original_w=grid_w,
                vertical=vertical,
                texture=texture,
                difficulty=difficulty,
                attempt=attempt,
            )
            if not vertical:
                grid = _transpose(grid)
            errors = self_check(
                grid,
                difficulty=difficulty,
                meta={"overrides": dict(overrides)},
            )
            if errors:
                raise ValueError("; ".join(errors))
            return grid
        except ValueError as exc:
            last_error = exc
    raise ValueError(f"could not realize lawful mirror board: {last_error}")


def observe_overrides(grid: Any) -> dict[str, int]:
    facts = _axis_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["height"]),
        "grid_w": int(facts["width"]),
        "orientation": int(facts["orientation"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _axis_facts(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    height, width = int(facts["height"]), int(facts["width"])
    if not 5 <= height <= 14:
        errors.append(f"grid height {height} outside declared 5..14")
    if not 7 <= width <= 16:
        errors.append(f"grid width {width} outside declared 7..16")
    if not 1 <= facts["marker_count"] <= 3:
        errors.append("axis must use one to three color-8 markers")
    if facts["orientation"] == 1 and facts["marker_count"] < 2:
        errors.append("horizontal axis needs at least two markers")
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must remain present")
    if facts["visible_empty_reflections"] < 1:
        errors.append("no content cell has a visible empty reflection target")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for name in ("grid_h", "grid_w", "orientation"):
                if name in requested and observed[name] != requested[name]:
                    errors.append(
                        f"override {name}={requested[name]!r} realized as "
                        f"{observed[name]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Complete lawful input grammar for this task's generated distribution."""
    return self_check(grid)


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is malformed"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {errors[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} rule failed: {exc}"]
    if expected != pair["output"]:
        return [f"{label} output does not follow the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require every declared plausible wrong rule to fail on the demos."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"surviving lesson shortcut: {name}")
    return errors
