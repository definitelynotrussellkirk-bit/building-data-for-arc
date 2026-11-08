"""Generator for ARC task 0c1bec3fcbdc — cap vertical run endpoints.

For every maximal vertical run of magenta (6) whose length is at least three,
recolor only its top and bottom cells blue (1).  Short magenta runs, horizontal
magenta lines, and runs of other colors stay unchanged.  Separated qualifying
runs in the same column are handled independently.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0c1bec3fcbdc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "cbc30556d505"

SUMMARY = (
    "Find each maximal vertical magenta (6) run. If its length is at least "
    "three, recolor exactly the top and bottom cells blue (1), preserving the "
    "interior. Length-one/two magenta runs, horizontal magenta lines, and "
    "non-magenta runs are unchanged; separated runs in one column are capped "
    "independently."
)

INVARIANTS = [
    "inputs use sparse zero background with straight nonzero line components",
    "every ordinary scene has 2..4 qualifying vertical magenta runs",
    "every ordinary scene has a length-two magenta control that must stay unchanged",
    "qualifying runs include both length three and length at least four",
    "horizontal, non-magenta, and stacked controls are mutually observable profiles",
    "the canonical Racket rule is the sole output authority",
]

SIZE_PROFILES = (
    "canonical_8x10",
    "canonical_10x11",
    "expanded_12x13",
)
_SIZE_BY_PROFILE = {
    "canonical_8x10": (8, 10),
    "canonical_10x11": (10, 11),
    "expanded_12x13": (12, 13),
}
_PROFILE_BY_SIZE = {value: key for key, value in _SIZE_BY_PROFILE.items()}

SCENE_PROFILES = (
    "canonical",
    "horizontal",
    "other_color",
    "stacked",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

AXES = {
    "size_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(SIZE_PROFILES),
        "doc": "two exact canonical sizes plus one expanded generalization size",
    },
    "n_runs": {
        "type": "int",
        "default": "sample-index schedule 2..4",
        "valid": "2..4",
        "doc": "exact number of qualifying vertical magenta runs",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "canonical has only separated vertical magenta runs; horizontal adds "
            "one horizontal magenta control; other_color adds one long non-magenta "
            "vertical control; stacked puts two qualifying runs in one column"
        ),
    },
}

# Every Cartesian product of the exact domains above is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

_VALID_DIFFICULTIES = (None, "default", "easy", "medium", "hard")
_OTHER_COLORS = (2, 3, 4, 5, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Any four consecutive draws expose every decisive semantic profile."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _scheduled_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, default, default))


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return len(grid), 0, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append(
                    f"cell ({row_index},{col_index}) is not an ARC color 0..9"
                )
                return len(grid), width, errors
    return len(grid), width, errors


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    components: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        colors = {grid[row][col] for row, col in cells}
        rows = {row for row, _ in cells}
        cols = {col for _, col in cells}
        if len(rows) == 1:
            orientation = "horizontal"
        elif len(cols) == 1:
            orientation = "vertical"
        else:
            orientation = "nonlinear"
        components.append(
            {
                "cells": frozenset(cells),
                "colors": frozenset(colors),
                "orientation": orientation,
                "length": len(cells),
            }
        )
    return components


def _vertical_runs(grid: list[list[int]]) -> list[dict[str, int]]:
    height, width = len(grid), len(grid[0])
    runs: list[dict[str, int]] = []
    for col in range(width):
        row = 0
        while row < height:
            color = grid[row][col]
            if color == 0:
                row += 1
                continue
            end = row
            while end + 1 < height and grid[end + 1][col] == color:
                end += 1
            runs.append(
                {
                    "col": col,
                    "start": row,
                    "end": end,
                    "color": color,
                    "length": end - row + 1,
                }
            )
            row = end + 1
    return runs


def _analyze(grid: Any) -> dict[str, Any]:
    height, width, errors = _validate_grid(grid)
    if errors:
        return {"errors": errors, "facts": None}

    normalized = [list(row) for row in grid]
    size_profile = _PROFILE_BY_SIZE.get((height, width))
    if size_profile is None:
        errors.append(
            f"dimensions {height}x{width} are not one of {sorted(_PROFILE_BY_SIZE)}"
        )

    palette = {value for row in normalized for value in row}
    if 0 not in palette:
        errors.append("zero background must be present")
    if 1 in palette:
        errors.append("blue (1) is an output marker and may not appear in the input")
    unexpected = palette - {0, 6, *_OTHER_COLORS}
    if unexpected:
        errors.append(f"unexpected input colors: {sorted(unexpected)}")
    other_colors = palette - {0, 6}
    if len(other_colors) > 1:
        errors.append("at most one non-magenta decoy color is allowed")

    components = _components(normalized)
    horizontal_components: list[dict[str, Any]] = []
    other_components: list[dict[str, Any]] = []
    for index, component in enumerate(components):
        if len(component["colors"]) != 1:
            errors.append(f"component {index} mixes colors")
            continue
        color = next(iter(component["colors"]))
        orientation = component["orientation"]
        length = component["length"]
        if orientation == "nonlinear":
            errors.append(f"component {index} is not a straight line")
        elif orientation == "horizontal" and length > 1:
            if color != 6:
                errors.append("only magenta may form a horizontal control line")
            if not 3 <= length <= 6:
                errors.append("horizontal magenta controls must have length 3..6")
            horizontal_components.append(component)
        elif orientation == "vertical" and length > 6:
            errors.append("vertical line components may not exceed length 6")
        if color != 6:
            other_components.append(component)

    runs = _vertical_runs(normalized)
    qualifying = [run for run in runs if run["color"] == 6 and run["length"] >= 3]
    short_magenta = [run for run in runs if run["color"] == 6 and run["length"] < 3]
    if not qualifying:
        errors.append("at least one qualifying vertical magenta run is required")

    qualifying_by_col: dict[int, list[dict[str, int]]] = defaultdict(list)
    for run in qualifying:
        qualifying_by_col[run["col"]].append(run)
    stacked_cols = sorted(
        col for col, col_runs in qualifying_by_col.items() if len(col_runs) >= 2
    )

    if len(horizontal_components) > 1:
        errors.append("at most one horizontal magenta control is allowed")
    if other_components:
        if len(other_components) != 1:
            errors.append("other-color profile must contain exactly one decoy component")
        else:
            component = other_components[0]
            if component["orientation"] != "vertical" or component["length"] < 3:
                errors.append("other-color decoy must be one vertical run of length at least 3")
        if horizontal_components or stacked_cols:
            errors.append("other-color, horizontal, and stacked profile cues may not overlap")
        scene_profile = "other_color"
    elif horizontal_components:
        if horizontal_components[0]["length"] != 4:
            errors.append("generated horizontal control must have exactly four cells")
        if stacked_cols:
            errors.append("horizontal and stacked profile cues may not overlap")
        scene_profile = "horizontal"
    elif stacked_cols:
        if len(stacked_cols) != 1 or len(qualifying_by_col[stacked_cols[0]]) != 2:
            errors.append("stacked profile must have exactly two qualifying runs in one column")
        scene_profile = "stacked"
    else:
        scene_profile = "canonical"

    facts = {
        "height": height,
        "width": width,
        "size_profile": size_profile,
        "palette": frozenset(palette),
        "components": tuple(components),
        "runs": tuple(runs),
        "qualifying": tuple(qualifying),
        "short_magenta": tuple(short_magenta),
        "horizontal_components": tuple(horizontal_components),
        "other_components": tuple(other_components),
        "stacked_cols": tuple(stacked_cols),
        "scene_profile": scene_profile,
        "n_runs": len(qualifying),
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, non-sparse, nonlinear, and profile-ambiguous inputs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Sparse 0/6 vertical-run manifold shared by all four canonical inputs."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    facts = analysis["facts"]
    if facts["size_profile"] not in {"canonical_8x10", "canonical_10x11"}:
        reasons.append("canonical dimensions are 8x10 or 10x11")
    if facts["palette"] != frozenset({0, 6}):
        reasons.append("canonical inputs use exactly colors 0 and 6")
    if facts["scene_profile"] != "canonical":
        reasons.append("canonical inputs contain separated vertical components only")
    lengths = [run["length"] for run in facts["runs"] if run["color"] == 6]
    if any(length not in (2, 3, 4, 5) for length in lengths):
        reasons.append("canonical magenta run lengths are in 2..5 with no singletons")
    if 2 not in lengths:
        reasons.append("canonical inputs include a length-two unchanged control")
    if not 2 <= facts["n_runs"] <= 4:
        reasons.append("canonical-like scenes contain 2..4 qualifying runs")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "size_profile": facts["size_profile"],
        "n_runs": facts["n_runs"],
        "scene_profile": facts["scene_profile"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    out = [list(row) for row in grid]
    for run in _vertical_runs([list(row) for row in grid]):
        if run["color"] == 6 and run["length"] >= 3:
            out[run["start"]][run["col"]] = 1
            out[run["end"]][run["col"]] = 1
    return out


def _rival_cap_short_runs(grid):
    out = [list(row) for row in grid]
    for run in _vertical_runs([list(row) for row in grid]):
        if run["color"] == 6:
            out[run["start"]][run["col"]] = 1
            out[run["end"]][run["col"]] = 1
    return out


def _rival_cap_any_color(grid):
    out = [list(row) for row in grid]
    for run in _vertical_runs([list(row) for row in grid]):
        if run["length"] >= 3:
            out[run["start"]][run["col"]] = 1
            out[run["end"]][run["col"]] = 1
    return out


def _rival_cap_horizontal_too(grid):
    out = rule_mirror(grid)
    for component in _components([list(row) for row in grid]):
        if (
            component["colors"] == frozenset({6})
            and component["orientation"] == "horizontal"
            and component["length"] >= 3
        ):
            left = min(component["cells"], key=lambda cell: cell[1])
            right = max(component["cells"], key=lambda cell: cell[1])
            out[left[0]][left[1]] = 1
            out[right[0]][right[1]] = 1
    return out


def _rival_merge_stacked_runs(grid):
    out = [list(row) for row in grid]
    by_col: dict[int, list[dict[str, int]]] = defaultdict(list)
    for run in _vertical_runs([list(row) for row in grid]):
        if run["color"] == 6 and run["length"] >= 3:
            by_col[run["col"]].append(run)
    for col, runs in by_col.items():
        ordered = sorted(runs, key=lambda run: run["start"])
        if len(ordered) == 1:
            out[ordered[0]["start"]][col] = 1
            out[ordered[0]["end"]][col] = 1
        else:
            out[ordered[0]["start"]][col] = 1
            out[ordered[-1]["end"]][col] = 1
    return out


def _rival_cap_only_longest(grid):
    out = [list(row) for row in grid]
    qualifying = [
        run
        for run in _vertical_runs([list(row) for row in grid])
        if run["color"] == 6 and run["length"] >= 3
    ]
    if qualifying:
        chosen = min(
            qualifying,
            key=lambda run: (-run["length"], run["col"], run["start"]),
        )
        out[chosen["start"]][chosen["col"]] = 1
        out[chosen["end"]][chosen["col"]] = 1
    return out


def _rival_cap_exactly_three(grid):
    out = [list(row) for row in grid]
    for run in _vertical_runs([list(row) for row in grid]):
        if run["color"] == 6 and run["length"] == 3:
            out[run["start"]][run["col"]] = 1
            out[run["end"]][run["col"]] = 1
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "cap_short_magenta_runs": _rival_cap_short_runs,
    "cap_long_runs_of_any_color": _rival_cap_any_color,
    "cap_horizontal_magenta_lines": _rival_cap_horizontal_too,
    "merge_separated_runs_in_one_column": _rival_merge_stacked_runs,
    "cap_only_the_longest_run": _rival_cap_only_longest,
    "cap_only_length_three_runs": _rival_cap_exactly_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "cap_long_runs_of_any_color": _rival_cap_any_color,
    "cap_horizontal_magenta_lines": _rival_cap_horizontal_too,
    "merge_separated_runs_in_one_column": _rival_merge_stacked_runs,
}


def _valid_facts(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis["facts"]


def _witness_short_control(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and any(run["length"] == 2 for run in facts["short_magenta"]))


def _witness_other_color(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["scene_profile"] == "other_color")


def _witness_horizontal(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["scene_profile"] == "horizontal")


def _witness_stacked(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["scene_profile"] == "stacked")


def _witness_multiple_targets(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["n_runs"] >= 2)


def _witness_mixed_lengths(grid) -> bool:
    facts = _valid_facts(grid)
    if not facts:
        return False
    lengths = {run["length"] for run in facts["qualifying"]}
    return 3 in lengths and any(length >= 4 for length in lengths)


SEMANTIC_WITNESSES = {
    "length_two_magenta_run_stays_unchanged": _witness_short_control,
    "long_non_magenta_run_stays_unchanged": _witness_other_color,
    "horizontal_magenta_line_stays_unchanged": _witness_horizontal,
    "separated_same_column_runs_are_independent": _witness_stacked,
    "all_qualifying_runs_are_targets": _witness_multiple_targets,
    "threshold_includes_lengths_above_three": _witness_mixed_lengths,
}

WITNESS_RIVALS = {
    "length_two_magenta_run_stays_unchanged": ["cap_short_magenta_runs"],
    "long_non_magenta_run_stays_unchanged": ["cap_long_runs_of_any_color"],
    "horizontal_magenta_line_stays_unchanged": ["cap_horizontal_magenta_lines"],
    "separated_same_column_runs_are_independent": [
        "merge_separated_runs_in_one_column"
    ],
    "all_qualifying_runs_are_targets": ["cap_only_the_longest_run"],
    "threshold_includes_lengths_above_three": ["cap_only_length_three_runs"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Four consecutive demonstrations must eliminate every named rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    seen_profiles: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
        facts = _analyze(demo["input"])["facts"]
        seen_profiles.add(facts["scene_profile"])
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    missing_profiles = set(SCENE_PROFILES) - seen_profiles
    if missing_profiles:
        reasons.append(f"demonstrations miss profiles {sorted(missing_profiles)}")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _neighbors(row: int, col: int) -> Iterable[tuple[int, int]]:
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _can_place(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    cell_set = set(cells)
    if not cell_set:
        return False
    for row, col in cell_set:
        if not (0 <= row < height and 0 <= col < width):
            return False
        if grid[row][col] != 0:
            return False
        for n_row, n_col in _neighbors(row, col):
            if (
                0 <= n_row < height
                and 0 <= n_col < width
                and (n_row, n_col) not in cell_set
                and grid[n_row][n_col] != 0
            ):
                return False
    return True


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


def _place_vertical(grid, rng, length: int, color: int = 6) -> bool:
    height, width = len(grid), len(grid[0])
    for _ in range(240):
        col = rng.randrange(width)
        start = rng.randint(0, height - length)
        cells = [(row, col) for row in range(start, start + length)]
        if _can_place(grid, cells):
            _paint(grid, cells, color)
            return True
    return False


def _place_horizontal(grid, rng, length: int = 4) -> bool:
    height, width = len(grid), len(grid[0])
    for _ in range(240):
        row = rng.randrange(height)
        start = rng.randint(0, width - length)
        cells = [(row, col) for col in range(start, start + length)]
        if _can_place(grid, cells):
            _paint(grid, cells, 6)
            return True
    return False


def _place_stacked_pair(grid, rng) -> bool:
    height, width = len(grid), len(grid[0])
    lengths = (3, 4)
    for _ in range(240):
        first, second = lengths if rng.randrange(2) == 0 else tuple(reversed(lengths))
        max_gap = height - first - second
        if max_gap < 1:
            return False
        gap = rng.randint(1, max_gap)
        start = rng.randint(0, height - first - gap - second)
        col = rng.randrange(width)
        cells = [
            *((row, col) for row in range(start, start + first)),
            *((row, col) for row in range(start + first + gap, start + first + gap + second)),
        ]
        if _can_place(grid, cells):
            _paint(grid, cells, 6)
            return True
    return False


def _build_scene(
    *, height: int, width: int, n_runs: int, scene_profile: str, rng
) -> list[list[int]] | None:
    grid = full_grid(height, width, 0)

    if scene_profile == "horizontal" and not _place_horizontal(grid, rng):
        return None
    if scene_profile == "other_color":
        decoy_color = rng.choice(_OTHER_COLORS)
        if not _place_vertical(grid, rng, rng.randint(3, 5), decoy_color):
            return None

    placed_qualifying = 0
    if scene_profile == "stacked":
        if not _place_stacked_pair(grid, rng):
            return None
        placed_qualifying = 2

    # Every scene contains a decisive length-two control.
    if not _place_vertical(grid, rng, 2, 6):
        return None

    remaining_lengths = [3, 4, 5, 3]
    if scene_profile == "stacked":
        remaining_lengths = [5, 3]
    for length in remaining_lengths[: n_runs - placed_qualifying]:
        if not _place_vertical(grid, rng, length, 6):
            return None
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_size = SIZE_PROFILES[int(sample_index) % len(SIZE_PROFILES)]
    size_profile = _scheduled_choice(ctx, "size_profile", SIZE_PROFILES, default_size)
    default_runs = 2 + int(sample_index) % 3
    n_runs = _scheduled_int(ctx, "n_runs", default_runs, 2, 4)
    default_scene = schedule_profile(seed, sample_index, difficulty)
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, default_scene
    )
    height, width = _SIZE_BY_PROFILE[size_profile]
    band_salt = "default" if difficulty in (None, "default") else str(difficulty)
    rng = ctx.draw_rng(f"layout_{band_salt}")

    for _ in range(256):
        grid = _build_scene(
            height=height,
            width=width,
            n_runs=n_runs,
            scene_profile=scene_profile,
            rng=rng,
        )
        if grid is None:
            continue
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        observed = observe_overrides(grid)
        expected = {
            "size_profile": size_profile,
            "n_runs": n_runs,
            "scene_profile": scene_profile,
        }
        if observed == expected and _witness_short_control(grid) and _witness_mixed_lengths(grid):
            return grid
    raise RuntimeError(
        "could not construct the requested observable run-endpoint scene "
        f"after 256 attempts: {size_profile=}, {n_runs=}, {scene_profile=}"
    )
