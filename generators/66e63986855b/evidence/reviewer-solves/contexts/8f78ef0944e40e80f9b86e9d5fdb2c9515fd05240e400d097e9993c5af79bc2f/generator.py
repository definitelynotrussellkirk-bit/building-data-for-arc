"""Semantic generator for ARC task 66e63986855b.

A single-color outline is described by the rightmost occupied cell in each
occupied row.  The canonical rule clears the input, skips the first and last
occupied rows, and fills each remaining row from just right of its frontier
through the reflected frontier across the global rightmost column.

The curriculum deliberately varies four source morphologies and four canvas
placements.  All construction choices preserve the broad Racket rule's true
preconditions: contiguous occupied rows, endpoint rows on the global right
frontier, a visible interior concavity, and enough room for every reflection.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "66e63986855b"
TASK_ID = "66e63986855b"
VERSION = "4.0.0"
RULE_HASH = "e9ecd02cbe2e"
EXAMPLES_NEEDED = 3
# Two independent schedule periods: every other input distinguishes vertical
# half-copy rivals; every third uses a canonical canvas size. RNG-keyed geometry,
# placement and color stay variable, and explicit axis overrides take priority.
SCHEDULE_PROFILES = tuple(range(6))
CANONICAL_CANVASES = ((6, 6), (8, 8), (10, 10))

SUMMARY = (
    "Clear a one-color row-front outline, then fill each interior occupied "
    "row from its frontier through the point mirrored across the outline's "
    "global rightmost column."
)

INVARIANTS = [
    "literal 0 is background and exactly one nonzero ARC color is used",
    "occupied rows form one contiguous run of at least five rows",
    "the first and last occupied rows reach the global rightmost column",
    "every interior row ends left of that column",
    "at least one interior row is two or more columns shallower",
    "every reflected fill interval fits inside the canvas",
]

PROFILES = (
    "connected_c",
    "sparse_symmetric",
    "thick_symmetric",
    "asymmetric_front",
)
PLACEMENTS = (
    "top_left",
    "top_margin",
    "left_margin",
    "floating",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-canvas lane mixed with difficulty-aware keyed draw",
        "valid": "6..14",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-canvas lane mixed with difficulty-aware keyed draw",
        "valid": "6..18",
        "doc": "Exact returned grid width.",
    },
    "color": {
        "type": "color",
        "default": "keyed nonzero ARC color",
        "valid": "1..9",
        "doc": "Exact unique nonzero color in the returned grid.",
    },
    "profile": {
        "type": "str",
        "default": "alternating asymmetric witness and difficulty-weighted morphology",
        "valid": "connected_c|sparse_symmetric|thick_symmetric|asymmetric_front",
        "doc": "Exact row-front morphology recovered from the returned grid.",
    },
    "placement": {
        "type": "str",
        "default": "keyed top/left margin category",
        "valid": "top_left|top_margin|left_margin|floating",
        "doc": "Exact occupied-bbox relation to the top and left canvas edges.",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    """Return a copied ARC grid, or precise shape/color errors."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    height = len(grid)
    width = len(grid[0])
    if height > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    copied: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        copied_row: list[int] = []
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                copied_row.append(0)
            else:
                copied_row.append(value)
        copied.append(copied_row)
    if errors:
        return None, errors
    return copied, []


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = [start]
        for row, col in queue:
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
    return count


def _analysis(grid: Any) -> dict[str, Any]:
    """Strictly recognize the calibrated curriculum and expose exact axes."""
    original, errors = _coerce_grid(grid)
    if errors or original is None:
        return {"errors": errors, "profile": None, "placement": None}

    height, width = len(original), len(original[0])
    colors = {
        value
        for row in original
        for value in row
        if value != 0
    }
    if len(colors) != 1:
        if not colors:
            errors.append("exactly one nonzero color is required; found none")
        else:
            errors.append(
                "exactly one nonzero color is required; found "
                f"{sorted(colors)}"
            )
        return {"errors": errors, "profile": None, "placement": None}
    color = next(iter(colors))

    occupied_rows: list[int] = []
    row_columns: dict[int, list[int]] = {}
    cells: set[tuple[int, int]] = set()
    for row in range(height):
        columns = [
            col
            for col in range(width)
            if original[row][col] != 0
        ]
        if columns:
            occupied_rows.append(row)
            row_columns[row] = columns
            cells.update((row, col) for col in columns)

    if len(occupied_rows) < 5:
        errors.append(
            "occupied row-front profile must span at least five rows"
        )
        return {"errors": errors, "profile": None, "placement": None}
    first_row, last_row = occupied_rows[0], occupied_rows[-1]
    if occupied_rows != list(range(first_row, last_row + 1)):
        errors.append("occupied rows must form one contiguous run")

    starts: list[int] = []
    fronts: list[int] = []
    lengths: list[int] = []
    for row in occupied_rows:
        columns = row_columns[row]
        start, front = columns[0], columns[-1]
        if columns != list(range(start, front + 1)):
            errors.append(f"occupied cells in row {row} must be contiguous")
        starts.append(start)
        fronts.append(front)
        lengths.append(len(columns))

    minimum_col = min(starts)
    maximum_col = max(fronts)
    local_fronts = [front - minimum_col for front in fronts]
    local_starts = [start - minimum_col for start in starts]
    mirror_ends = [
        2 * maximum_col - front
        for front in fronts[1:-1]
    ]

    if fronts[0] != maximum_col or fronts[-1] != maximum_col:
        errors.append(
            "first and last occupied rows must reach the global rightmost column"
        )
    if any(front >= maximum_col for front in fronts[1:-1]):
        errors.append(
            "every interior occupied row must end left of the global rightmost column"
        )
    if not any(
        maximum_col - front >= 2
        for front in fronts[1:-1]
    ):
        errors.append(
            "at least one interior row must expose mirror depth two or greater"
        )
    if any(end >= width for end in mirror_ends):
        errors.append("a reflected interior frontier would leave the canvas")

    symmetric = fronts == list(reversed(fronts))
    profile: str | None
    if all(start == minimum_col for start in starts):
        profile = "connected_c"
    elif all(length == 1 for length in lengths) and symmetric:
        profile = "sparse_symmetric"
    elif (
        symmetric
        and all(length in (1, 2) for length in lengths)
        and any(length == 2 for length in lengths[1:-1])
    ):
        profile = "thick_symmetric"
    elif (
        not symmetric
        and all(length in (1, 2) for length in lengths)
    ):
        profile = "asymmetric_front"
    else:
        profile = None
        errors.append("row-front morphology does not match a declared profile")

    if first_row == 0 and minimum_col == 0:
        placement = "top_left"
    elif first_row == 0:
        placement = "top_margin"
    elif minimum_col == 0:
        placement = "left_margin"
    else:
        placement = "floating"

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "color": color,
        "profile": profile,
        "placement": placement,
        "first_row": first_row,
        "last_row": last_row,
        "minimum_col": minimum_col,
        "maximum_col": maximum_col,
        "shape_h": len(occupied_rows),
        "starts": starts,
        "fronts": fronts,
        "local_starts": local_starts,
        "local_fronts": local_fronts,
        "lengths": lengths,
        "mirror_ends": mirror_ends,
        "mirror_depth": max(
            maximum_col - front
            for front in fronts[1:-1]
        ),
        "component_count": _component_count(cells),
    }


def observe_overrides(grid: Any) -> dict[str, int | str]:
    """Recover every declared axis exactly from a valid returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "color": analysis["color"],
        "profile": analysis["profile"],
        "placement": analysis["placement"],
    }


def canonical_profile_signature(grid: Any) -> str | None:
    """Return the recognized profile for canonical or generated inputs."""
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis["profile"]


def self_check(
    grid: Any,
    *,
    difficulty: str | None = None,
    meta: dict[str, Any] | None = None,
) -> list[str]:
    """Strictly validate the calibrated row-front curriculum."""
    errors: list[str] = []
    if difficulty not in _DIFFICULTIES:
        errors.append("difficulty must be None, easy, medium, or hard")
    analysis = _analysis(grid)
    errors.extend(analysis["errors"])

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        requested = nested if isinstance(nested, dict) else meta
    if not analysis["errors"]:
        observed = observe_overrides(grid)
        for axis in AXES:
            if axis in requested and requested[axis] is not None:
                if observed.get(axis) != requested[axis]:
                    errors.append(
                        f"{axis} requested {requested[axis]!r}, "
                        f"observed {observed.get(axis)!r}"
                    )
    return errors


def rule_mirror(grid: Any) -> list[list[int]]:
    """Broad, input-pure Python mirror of the canonical Racket program."""
    original, errors = _coerce_grid(grid)
    if errors or original is None:
        raise ValueError("; ".join(errors))
    height, width = len(original), len(original[0])
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if original[row][col] != 0
    ]
    if not cells:
        raise ValueError("canonical rule requires at least one nonzero cell")
    color = original[cells[0][0]][cells[0][1]]
    first_row = min(row for row, _col in cells)
    last_row = max(row for row, _col in cells)
    maximum_col = max(col for _row, col in cells)
    output = _blank(height, width)
    for row in range(height):
        row_cells = [col for cell_row, col in cells if cell_row == row]
        if not row_cells or row in (first_row, last_row):
            continue
        frontier = max(row_cells)
        end = 2 * maximum_col - frontier
        for col in range(frontier + 1, end + 1):
            if 0 <= col < width:
                output[row][col] = color
    return output


def _profile_options(difficulty: str | None) -> tuple[str, ...]:
    if difficulty == "easy":
        return (
            "connected_c",
            "connected_c",
            "sparse_symmetric",
            "thick_symmetric",
            "asymmetric_front",
        )
    if difficulty == "hard":
        return (
            "connected_c",
            "sparse_symmetric",
            "thick_symmetric",
            "thick_symmetric",
            "asymmetric_front",
            "asymmetric_front",
        )
    return PROFILES


def _placement_options(difficulty: str | None) -> tuple[str, ...]:
    if difficulty == "easy":
        return (
            "top_left",
            "top_left",
            "top_margin",
            "left_margin",
            "floating",
        )
    if difficulty == "hard":
        return (
            "top_left",
            "top_margin",
            "left_margin",
            "floating",
            "floating",
        )
    return PLACEMENTS


def _shape_height(height: int, difficulty: str | None, rng: Any) -> int:
    preferred = {
        "easy": 6,
        "medium": 9,
        "hard": height - 1,
        None: 9,
    }[difficulty]
    high = max(5, min(height - 1, preferred))
    return rng.randint(5, high)


def _top_row(
    height: int,
    shape_height: int,
    placement: str,
    rng: Any,
) -> int:
    if placement in ("top_left", "top_margin"):
        return 0
    return rng.randint(1, height - shape_height)


def _left_col(width: int, placement: str, rng: Any) -> int:
    if placement in ("top_left", "left_margin"):
        return 0
    # Keeping four columns from the left edge to the right edge guarantees
    # room for a local frontier of at least two and its deepest reflection.
    return rng.randint(1, max(1, min(width - 5, 4)))


def _local_max_front(
    width: int,
    left: int,
    difficulty: str | None,
    rng: Any,
) -> int:
    fit_max = (width - 1 - left) // 2
    preferred = {
        "easy": 3,
        "medium": 5,
        "hard": 7,
        None: 5,
    }[difficulty]
    high = min(fit_max, preferred)
    return rng.randint(2, max(2, high))


def _symmetric_fronts(shape_height: int, maximum: int) -> list[int]:
    fronts = []
    for index in range(shape_height):
        distance = min(index, shape_height - 1 - index)
        fronts.append(max(0, maximum - distance))
    fronts[0] = maximum
    fronts[-1] = maximum
    center = (shape_height - 1) // 2
    fronts[center] = 0
    fronts[shape_height - 1 - center] = 0
    return fronts


def _connected_fronts(
    shape_height: int,
    maximum: int,
    rng: Any,
) -> list[int]:
    fronts = [maximum]
    for _index in range(1, shape_height - 1):
        fronts.append(rng.randint(0, maximum - 1))
    fronts.append(maximum)
    deepest = rng.randint(1, shape_height - 2)
    fronts[deepest] = rng.randint(0, maximum - 2)
    return fronts


def _asymmetric_fronts(
    shape_height: int,
    maximum: int,
    rng: Any,
) -> list[int]:
    fronts = _symmetric_fronts(shape_height, maximum)
    for index in range(1, shape_height - 1):
        if index not in (1, shape_height - 2):
            fronts[index] = rng.randint(0, maximum - 1)
    fronts[1] = maximum - 1
    fronts[-2] = 0
    if rng.randrange(2):
        fronts = list(reversed(fronts))
    return fronts


def _render_profile(
    height: int,
    width: int,
    color: int,
    profile: str,
    placement: str,
    difficulty: str | None,
    rng: Any,
) -> list[list[int]]:
    shape_height = _shape_height(height, difficulty, rng)
    top = _top_row(height, shape_height, placement, rng)
    left = _left_col(width, placement, rng)
    maximum = _local_max_front(width, left, difficulty, rng)

    if profile == "connected_c":
        fronts = _connected_fronts(shape_height, maximum, rng)
    elif profile in ("sparse_symmetric", "thick_symmetric"):
        fronts = _symmetric_fronts(shape_height, maximum)
    else:
        fronts = _asymmetric_fronts(shape_height, maximum, rng)

    grid = _blank(height, width)
    for index, local_front in enumerate(fronts):
        row = top + index
        absolute_front = left + local_front
        if profile == "connected_c":
            start = left
        elif profile == "thick_symmetric" and (
            0 < index < shape_height - 1
            and local_front > 0
            and (index == 1 or index == shape_height - 2 or index % 2 == 1)
        ):
            start = absolute_front - 1
        elif profile == "asymmetric_front" and (
            0 < index < shape_height - 1
            and local_front > 0
            and index % 3 == 0
        ):
            start = absolute_front - 1
        else:
            start = absolute_front
        for col in range(start, absolute_front + 1):
            grid[row][col] = color
    return grid


def _validate_call(
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if (difficulty is not None and not isinstance(difficulty, str)) or difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    # The shared context coerces numeric overrides with int(). Exact observable
    # controls must reject booleans, strings and fractional values BEFORE that.
    for name, lower, upper in (("grid_h", 6, 14), ("grid_w", 6, 18), ("color", 1, 9)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lower <= value <= upper):
            raise ValueError(f"{name} must be an integer in {lower}..{upper}")
    for name, choices in (("profile", PROFILES), ("placement", PLACEMENTS)):
        value = overrides.get(name)
        if value is not None and value not in choices:
            raise ValueError(f"{name} must be one of {choices}")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Joint phase of the default 2-by-3 curriculum; not a visible input axis."""
    return sample_index % len(SCHEDULE_PROFILES)


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    """Construct one deterministic, override-exact curriculum input."""
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Resolve the sampling domain before drawing, so keyed provenance describes
    # the returned axes rather than values later overwritten by the curriculum.
    canonical_canvas = sample_index % 3 == 0
    canonical_h, canonical_w = context.draw_rng("canonical_canvas").choice(CANONICAL_CANVASES)
    if canonical_canvas and overrides.get("grid_h") is None:
        height = context.draw_int("grid_h", canonical_h, canonical_h)
    else:
        height = context.draw_int_diff("grid_h", 6, 14)
    if canonical_canvas and overrides.get("grid_w") is None:
        width = context.draw_int("grid_w", canonical_w, canonical_w)
    else:
        width = context.draw_int_diff("grid_w", 6, 18)
    color = context.draw_color("color", exclude={0})
    profile_choices = _profile_options(difficulty)
    if sample_index % 2 == 1 and overrides.get("profile") is None:
        profile_choices = ("asymmetric_front",)
    profile = context.draw_choice("profile", profile_choices)
    placement = context.draw_choice(
        "placement", _placement_options(difficulty)
    )
    grid = _render_profile(
        height,
        width,
        color,
        profile,
        placement,
        difficulty,
        context.draw_rng("geometry"),
    )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid row-front scene: " + "; ".join(errors)
        )
    return grid


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-domain validity, not exact-size membership or universal identifiability.

    The calibrated row-front manifold includes all canonical inputs, translated
    and resized variants, and asymmetric frontiers that expose row-wise behavior.
    The broader reference is deliberately not restricted to this manifold.
    """
    return self_check(grid)


def _half_copy(grid: Any, *, upper: bool) -> list[list[int]]:
    """Rival: infer both halves' row frontiers from just one vertical half."""
    original, errors = _coerce_grid(grid)
    if original is None or errors:
        raise ValueError("; ".join(errors))
    fronts = {r: max(c for c, value in enumerate(row) if value)
              for r, row in enumerate(original) if any(row)}
    if not fronts:
        raise ValueError("half-copy rival needs a nonempty foreground")
    top, bottom = min(fronts), max(fronts)
    maximum = max(fronts.values())
    color = next(value for row in original for value in row if value)
    output = _blank(len(original), len(original[0]))
    for row in range(top + 1, bottom):
        source = min(row, top + bottom - row) if upper else max(row, top + bottom - row)
        if source not in fronts:
            continue
        front = fronts[source]
        for col in range(front + 1, 2 * maximum - front + 1):
            if 0 <= col < len(original[0]):
                output[row][col] = color
    return output


def copy_upper_half(grid: Any) -> list[list[int]]:
    return _half_copy(grid, upper=True)


def copy_lower_half(grid: Any) -> list[list[int]]:
    return _half_copy(grid, upper=False)


def fill_only_to_axis(grid: Any) -> list[list[int]]:
    """Rival: fill the visible concavity, but omit the reflected right half."""
    output = rule_mirror(grid)
    maximum = max(c for row in grid for c, value in enumerate(row) if value)
    for row in output:
        for col in range(maximum + 1, len(row)):
            row[col] = 0
    return output


def _asymmetric_witness(grid: Any) -> bool:
    info = _analysis(grid)
    return not info["errors"] and info["fronts"] != list(reversed(info["fronts"]))


def _depth_witness(grid: Any) -> bool:
    info = _analysis(grid)
    return not info["errors"] and info["mirror_depth"] >= 2


SEMANTIC_RIVALS = {
    "copy_upper_half": copy_upper_half,
    "copy_lower_half": copy_lower_half,
    "fill_only_to_axis": fill_only_to_axis,
}
CANONICAL_SHORTCUTS = {
    "copy_upper_half": copy_upper_half,
    "copy_lower_half": copy_lower_half,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "unequal_mirrored_row_fronts": _asymmetric_witness,
    "reflected_fill_beyond_axis": _depth_witness,
}
WITNESS_RIVALS = {
    "unequal_mirrored_row_fronts": ["copy_upper_half", "copy_lower_half"],
    "reflected_fill_beyond_axis": ["fill_only_to_axis"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: Any) -> list[str]:
    """Return measured query ambiguity against declared competitors only.

    Demonstration OUTPUTS are evidence. Query output is never read. A competitor
    agreeing on the query is not ambiguity merely because it survived the demos.
    Three consecutive default draws contain an asymmetric witness; four contain
    at least two, so holding out one preserves a witness before any sampler
    rejection. Overrides or arbitrary subsampling remove that schedule guarantee.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["No labelled demonstrations supplied"]
    for pair in demos:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["Each demonstration must contain input and output"]
    query_input = query.get("input") if isinstance(query, dict) else query
    target = rule_mirror(query_input)
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_input) != target:
                reasons.append(f"{name} fits every demonstration but disagrees on the query")
    return reasons
