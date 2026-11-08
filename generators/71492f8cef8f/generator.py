"""Semantic input generator for ARC task 71492f8cef8f.

Color 5 cells are walls.  Every 4-connected component of non-wall cells is a
chamber.  A chamber is filled exactly when it contains one nonzero seed CELL;
empty chambers and chambers with two or more seed cells stay unchanged.

The curriculum deliberately includes the branches missing from the imported
sampler: empty chambers, multiple same-color seed cells, independent seed
colors, both closed and edge-open chambers, and several wall topologies.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "71492f8cef8f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f88bd76ccafc"
SUMMARY = (
    "Gray 5-cells partition the grid into 4-connected chambers. Fill every "
    "zero in a chamber iff that chamber contains exactly one nonzero seed "
    "cell; leave empty and multi-seed chambers unchanged. Generated lessons "
    "contrast same-color multi-seed conflicts, empty rooms, independent room "
    "colors, edge-open rooms, and multiple wall topologies."
)

INVARIANTS = [
    "background is 0 and chamber walls are color 5",
    "every generated grid has at least two uniquely seeded chambers of different colors",
    "every generated grid has an empty chamber and a multi-seed same-color chamber",
    "edge-open and closed chamber layouts alternate in every two-example lesson window",
]

SCENE_PROFILES = (
    "cross_closed",
    "cross_open",
    "offset_closed",
    "grid_open",
)
OPEN_EDGE_PROFILES = frozenset({"cross_open", "grid_open"})
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-position lesson schedule",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _chambers(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    chambers: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            todo = [(row, col)]
            cells: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                if (
                    not 0 <= rr < height
                    or not 0 <= cc < width
                    or (rr, cc) in seen
                    or grid[rr][cc] == 5
                ):
                    continue
                seen.add((rr, cc))
                cells.add((rr, cc))
                todo.extend((rr + dr, cc + dc) for dr, dc in _DIRS4)
            chambers.append(cells)
    return chambers


def _infer_profile(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> str | None:
    """Recover the exact generated topology from pixels, not RNG bookkeeping."""
    if _validate_grid(grid):
        return None
    height, width = len(grid), len(grid[0])
    full_rows = [
        row
        for row in range(1, height - 1)
        if all(grid[row][col] == 5 for col in range(width))
    ]
    full_cols = [
        col
        for col in range(1, width - 1)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    border = {
        *( (0, col) for col in range(width) ),
        *( (height - 1, col) for col in range(width) ),
        *( (row, 0) for row in range(height) ),
        *( (row, width - 1) for row in range(height) ),
    }
    openings = sum(grid[row][col] != 5 for row, col in border)
    signature = (len(full_rows), len(full_cols), openings)
    return {
        (1, 1, 0): "cross_closed",
        (1, 1, 1): "cross_open",
        (1, 0, 0): "offset_closed",
        (1, 2, 1): "grid_open",
    }.get(signature)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    chambers = _chambers(grid)
    seeds = [
        [(row, col, grid[row][col]) for row, col in sorted(cells) if grid[row][col] != 0]
        for cells in chambers
    ]
    touches_edge = [
        any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells)
        for cells in chambers
    ]
    output = [list(row) for row in grid]
    for cells, chamber_seeds in zip(chambers, seeds):
        if len(chamber_seeds) != 1:
            continue
        color = chamber_seeds[0][2]
        for row, col in cells:
            if grid[row][col] == 0:
                output[row][col] = color

    qualifying = [index for index, chamber_seeds in enumerate(seeds) if len(chamber_seeds) == 1]
    if not any(value == 5 for row in grid for value in row):
        errors.append("at least one color-5 wall is required")
    if len(chambers) < 2:
        errors.append("walls must define at least two chambers")
    if not any(
        len(seeds[index]) == 1 and any(grid[row][col] == 0 for row, col in chambers[index])
        for index in range(len(chambers))
    ):
        errors.append("at least one chamber must have exactly one seed and background to fill")

    unique_colors = {seeds[index][0][2] for index in qualifying}
    result.update(
        {
            "errors": errors,
            "scene_profile": _infer_profile(grid),
            "chambers": chambers,
            "seed_cells": seeds,
            "touches_edge": touches_edge,
            "output": output,
            "qualifying_count": len(qualifying),
            "empty_count": sum(not chamber_seeds for chamber_seeds in seeds),
            "multi_count": sum(len(chamber_seeds) > 1 for chamber_seeds in seeds),
            "same_color_multi_count": sum(
                len(chamber_seeds) > 1
                and len({value for _, _, value in chamber_seeds}) == 1
                for chamber_seeds in seeds
            ),
            "edge_unique_count": sum(
                len(chamber_seeds) == 1 and edge
                for chamber_seeds, edge in zip(seeds, touches_edge)
            ),
            "unique_seed_colors": unique_colors,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def canonical_profile_signature(grid) -> tuple[int, int, int] | None:
    if self_check(grid):
        return None
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    profile = analysis["scene_profile"]
    if profile not in SCENE_PROFILES:
        raise ValueError("grid does not match a declared scene_profile topology")
    return {"scene_profile": profile}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _blank(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _frame(grid: list[list[int]]) -> None:
    height, width = len(grid), len(grid[0])
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5


def _profile_dims(profile: str, band: str) -> tuple[int, int]:
    if profile == "cross_closed":
        return 7, 9  # exact canonical height/width/palette anchor in every band
    table = {
        "cross_open": {"easy": (7, 9), "medium": (8, 10), "hard": (9, 11)},
        "offset_closed": {"easy": (8, 10), "medium": (9, 11), "hard": (10, 12)},
        "grid_open": {"easy": (8, 11), "medium": (9, 12), "hard": (10, 13)},
    }
    return table[profile][band]


def _layout(profile: str, band: str, rng) -> tuple[list[list[int]], tuple[int, int] | None]:
    height, width = _profile_dims(profile, band)
    grid = _blank(height, width)
    _frame(grid)
    split_row = height // 2
    for col in range(width):
        grid[split_row][col] = 5

    opening: tuple[int, int] | None = None
    if profile in ("cross_closed", "cross_open"):
        split_col = width // 2
        for row in range(height):
            grid[row][split_col] = 5
    elif profile == "offset_closed":
        top_col = max(3, width // 2 + 1)
        bottom_col = min(width - 4, width // 2 - 2)
        for row in range(0, split_row + 1):
            grid[row][top_col] = 5
        for row in range(split_row, height):
            grid[row][bottom_col] = 5
    elif profile == "grid_open":
        left_col, right_col = width // 3, (2 * width) // 3
        for col in (left_col, right_col):
            for row in range(height):
                grid[row][col] = 5
    else:  # guarded before this helper is reached
        raise ValueError(f"unknown scene_profile: {profile!r}")

    if profile in OPEN_EDGE_PROFILES:
        candidates = [
            (row, 0)
            for row in range(1, height - 1)
            if row != split_row and grid[row][1] != 5
        ] + [
            (row, width - 1)
            for row in range(1, height - 1)
            if row != split_row and grid[row][width - 2] != 5
        ]
        opening = rng.choice(candidates)
        grid[opening[0]][opening[1]] = 0
    return grid, opening


def _wall_adjacent_cells(grid: list[list[int]], cells: set[tuple[int, int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    candidates = []
    for row, col in sorted(cells):
        if any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] == 5
            for dr, dc in _DIRS4
        ):
            candidates.append((row, col))
    return candidates or sorted(cells)


def _far_pair(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    ordered = sorted(cells)
    return max(
        ((left, right) for i, left in enumerate(ordered) for right in ordered[i + 1 :]),
        key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
    )


def _seed_layout(grid: list[list[int]], opening: tuple[int, int] | None, rng) -> None:
    chambers = _chambers(grid)
    if len(chambers) < 4:
        raise RuntimeError("profile layout produced fewer than four chambers")
    colors = rng.sample(list(_SEED_COLORS), 2)

    indices = list(range(len(chambers)))
    edge_index: int | None = None
    if opening is not None:
        edge_index = next(index for index, cells in enumerate(chambers) if opening in cells)
        indices.remove(edge_index)
    rng.shuffle(indices)

    assignments: dict[int, str] = {}
    if edge_index is not None:
        assignments[edge_index] = "unique_a"
        assignments[indices.pop()] = "unique_b"
    else:
        assignments[indices.pop()] = "unique_a"
        assignments[indices.pop()] = "unique_b"
    assignments[indices.pop()] = "empty"
    assignments[indices.pop()] = "multi_same"
    for index in indices:
        assignments[index] = "empty"

    for index, role in assignments.items():
        cells = chambers[index]
        if role == "empty":
            continue
        if role == "unique_a" and opening is not None and opening in cells:
            row, col = opening
            grid[row][col] = colors[0]
        elif role in ("unique_a", "unique_b"):
            choices = _wall_adjacent_cells(grid, cells)
            row, col = rng.choice(choices)
            grid[row][col] = colors[0 if role == "unique_a" else 1]
        elif role == "multi_same":
            left, right = _far_pair(cells)
            grid[left[0]][left[1]] = colors[0]
            grid[right[0]][right[1]] = colors[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty=band)
    profile = ctx.draw_choice("scene_profile", [requested or scheduled])
    grid, opening = _layout(profile, band, ctx.draw_rng("layout"))
    _seed_layout(grid, opening, ctx.draw_rng("seeds"))
    return [row[:] for row in grid]


def _rival_transform(
    grid,
    choose_color: Callable[[list[tuple[int, int, int]], bool, int | None], int | None],
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    global_seed = next(
        (value for chamber_seeds in analysis["seed_cells"] for _, _, value in chamber_seeds),
        None,
    )
    output = [list(row) for row in grid]
    for cells, chamber_seeds, edge in zip(
        analysis["chambers"], analysis["seed_cells"], analysis["touches_edge"]
    ):
        color = choose_color(chamber_seeds, edge, global_seed)
        if color is None:
            continue
        for row, col in cells:
            if grid[row][col] == 0:
                output[row][col] = color
    return output


def _fill_any_seeded(grid):
    return _rival_transform(
        grid, lambda seeds, edge, global_seed: seeds[0][2] if seeds else None
    )


def _fill_unique_seed_color(grid):
    return _rival_transform(
        grid,
        lambda seeds, edge, global_seed: (
            seeds[0][2] if seeds and len({value for _, _, value in seeds}) == 1 else None
        ),
    )


def _fill_empty_from_first_seed(grid):
    return _rival_transform(
        grid,
        lambda seeds, edge, global_seed: (
            seeds[0][2] if len(seeds) == 1 else global_seed if not seeds else None
        ),
    )


def _global_first_seed(grid):
    return _rival_transform(
        grid,
        lambda seeds, edge, global_seed: global_seed if len(seeds) == 1 else None,
    )


def _closed_rooms_only(grid):
    return _rival_transform(
        grid,
        lambda seeds, edge, global_seed: seeds[0][2] if len(seeds) == 1 and not edge else None,
    )


def _has_multi_seed_room(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["multi_count"] > 0


def _has_same_color_multi_seed(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["same_color_multi_count"] > 0


def _has_empty_room(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["empty_count"] > 0


def _has_multiple_unique_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["unique_seed_colors"]) > 1


def _has_edge_unique_room(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["edge_unique_count"] > 0


SEMANTIC_RIVALS = {
    "fill_any_seeded": _fill_any_seeded,
    "unique_seed_color": _fill_unique_seed_color,
    "fill_empty_from_first_seed": _fill_empty_from_first_seed,
    "global_first_seed": _global_first_seed,
    "closed_rooms_only": _closed_rooms_only,
}
SEMANTIC_WITNESSES = {
    "multi_seed_room": _has_multi_seed_room,
    "same_color_multi_seed": _has_same_color_multi_seed,
    "empty_room": _has_empty_room,
    "multiple_unique_colors": _has_multiple_unique_colors,
    "edge_unique_room": _has_edge_unique_room,
}
WITNESS_RIVALS = {
    "multi_seed_room": ["fill_any_seeded"],
    "same_color_multi_seed": ["unique_seed_color"],
    "empty_room": ["fill_empty_from_first_seed"],
    "multiple_unique_colors": ["global_first_seed"],
    "edge_unique_room": ["closed_rooms_only"],
}
CANONICAL_SHORTCUTS = {
    "fill_any_seeded": _fill_any_seeded,
    "unique_seed_color": _fill_unique_seed_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            query_differs = competitor(query["input"]) != query["output"]
        except Exception as exc:  # loud, bounded contract error
            reasons.append(f"competing rule {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and query_differs:
            reasons.append(f"competing rule {name!r} fits demos but changes the query answer")
    return reasons
