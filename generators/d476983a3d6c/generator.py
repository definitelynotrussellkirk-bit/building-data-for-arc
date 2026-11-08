"""Generator for command-selected L paths (task ``d476983a3d6c``).

The top-left cell is a command.  Every color that appears exactly twice is
connected in first-appearance order: command 1 paints the horizontal leg first,
then the vertical leg; command 2 paints the vertical leg first, then the
horizontal leg.  The output starts as a copy of the input, so the command and
singleton colors remain.  Later pair colors overwrite earlier colors where
paths overlap.

The four-slot curriculum deliberately repeats each decisive semantic feature
across at least two profiles.  Therefore any four of five consecutive pairs
still teach both command branches, aligned-pair handling, singleton
preservation, multi-pair iteration, and overlap priority.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d476983a3d6c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c83bfd047bef"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Keep the input grid. Read command 1 or 2 at (0,0). In row-major "
    "first-appearance order, connect every color that has exactly two cells "
    "with an L path of that color: command 1 uses horizontal then vertical; "
    "command 2 uses vertical then horizontal. Singleton colors stay unchanged, "
    "and later pair colors win where paths overlap."
)

INVARIANTS = [
    "the grid is rectangular, uses ARC colors, and belongs to a declared size profile",
    "cell (0,0) is command 1 or 2 and that command color occurs only there",
    "there are two or three paired colors and at most one singleton color",
    "at least one pair is non-aligned, so the command branch is observable",
    "a path interior never passes through an input marker of another color",
    "aligned pairs, singleton colors, and path overlaps are lawful",
]

SCENE_PROFILES = (
    "cmd1_three_pairs",
    "cmd2_two_pairs",
    "cmd1_two_pairs_singleton",
    "cmd2_three_pairs_singleton",
)
GRID_PROFILES = ("small", "canonical", "large")
CANONICAL_DIMS = ((9, 9), (10, 10))
SMALL_DIMS = ((8, 8), (8, 9), (9, 8))
LARGE_DIMS = {
    "easy": ((12, 12), (12, 13), (13, 12)),
    "medium": ((13, 13), (13, 14), (14, 13)),
    "hard": ((15, 15), (15, 16), (16, 15), (16, 16)),
}
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Exact signatures recoverable from a returned grid.  The generated profiles
# carry additional teaching features, but canonical inputs need only satisfy
# these task-faithful structural signatures.
SCENE_SIGNATURES = {
    "cmd1_three_pairs": (1, 3, 0),
    "cmd2_two_pairs": (2, 2, 0),
    "cmd1_two_pairs_singleton": (1, 2, 1),
    "cmd2_three_pairs_singleton": (2, 3, 1),
}
_SIGNATURE_TO_SCENE = {value: key for key, value in SCENE_SIGNATURES.items()}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "exact command, pair count, and singleton count",
    },
    "grid_profile": {
        "type": "str",
        "default": "scheduled canonical|canonical|small|large",
        "valid": "|".join(GRID_PROFILES),
        "doc": "disjoint size family recoverable from the returned grid",
    },
}


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    copied = [list(row) for row in grid]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in copied
        for value in row
    ):
        return None, ["cells must be integer ARC colors 0..9"]
    return copied, []


def _ordered_colors(grid: list[list[int]]) -> list[int]:
    """Canonical nonzero palette after treating only (0,0) as zero."""
    seen: set[int] = set()
    ordered: list[int] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if (row, col) == (0, 0) or value == 0 or value in seen:
                continue
            seen.add(value)
            ordered.append(value)
    return ordered


def _markers(grid: list[list[int]], color: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    )


def _path_cells(
    first: tuple[int, int],
    second: tuple[int, int],
    command: int,
) -> tuple[tuple[int, int], ...]:
    row_a, col_a = first
    row_b, col_b = second
    cells: list[tuple[int, int]] = []
    if command == 1:
        col_step = 1 if col_b >= col_a else -1
        cells.extend((row_a, col) for col in range(col_a, col_b + col_step, col_step))
        row_step = 1 if row_b >= row_a else -1
        cells.extend((row, col_b) for row in range(row_a, row_b + row_step, row_step))
    elif command == 2:
        row_step = 1 if row_b >= row_a else -1
        cells.extend((row, col_a) for row in range(row_a, row_b + row_step, row_step))
        col_step = 1 if col_b >= col_a else -1
        cells.extend((row_b, col) for col in range(col_a, col_b + col_step, col_step))
    else:
        raise ValueError(f"command must be 1 or 2, found {command!r}")
    return tuple(dict.fromkeys(cells))


def _grid_profile(height: int, width: int) -> str | None:
    if (height, width) in CANONICAL_DIMS:
        return "canonical"
    if (height, width) in SMALL_DIMS:
        return "small"
    if 12 <= height <= 16 and 12 <= width <= 16:
        return "large"
    return None


def _scene_profile(command: int, pair_count: int, singleton_count: int) -> str | None:
    return _SIGNATURE_TO_SCENE.get((command, pair_count, singleton_count))


def _rule_with_command(
    grid: Any,
    command: int,
    *,
    max_pairs: int | None = None,
    skip_aligned: bool = False,
    reverse: bool = False,
) -> list[list[int]]:
    """Python mirror with controlled deviations for executable rival rules."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    if command not in (1, 2):
        raise ValueError(f"command must be 1 or 2, found {command!r}")

    output = [row[:] for row in normalized]
    colors = _ordered_colors(normalized)
    if reverse:
        colors = list(reversed(colors))
    painted = 0
    for color in colors:
        positions = _markers(normalized, color)
        if len(positions) != 2:
            continue
        first, second = positions
        if skip_aligned and (first[0] == second[0] or first[1] == second[1]):
            continue
        if max_pairs is not None and painted >= max_pairs:
            continue
        for row, col in _path_cells(first, second, command):
            output[row][col] = color
        painted += 1
    return output


def _rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authority."""
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    command = normalized[0][0]
    if command not in (1, 2):
        raise ValueError("cell (0,0) must be command 1 or 2")
    return _rule_with_command(normalized, command)


def _reverse_pair_priority(grid: Any) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    return _rule_with_command(normalized, normalized[0][0], reverse=True)


def _drop_singletons(grid: Any) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    output = _rule_mirror(normalized)
    for color in _ordered_colors(normalized):
        positions = _markers(normalized, color)
        if len(positions) == 1:
            row, col = positions[0]
            output[row][col] = 0
    return output


def _clear_command(grid: Any) -> list[list[int]]:
    output = _rule_mirror(grid)
    output[0][0] = 0
    return output


def _input_unchanged(grid: Any) -> list[list[int]]:
    normalized, errors = _normalize_grid(grid)
    if normalized is None or errors:
        raise ValueError("; ".join(errors))
    return normalized


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    result: dict[str, Any] = {"errors": errors, "facts": None}
    if normalized is None:
        return result

    height = len(normalized)
    width = len(normalized[0])
    grid_profile = _grid_profile(height, width)
    if grid_profile is None:
        errors.append("grid dimensions are outside small, canonical, and large profiles")

    command = normalized[0][0]
    if command not in (1, 2):
        errors.append("cell (0,0) must be command 1 or 2")

    counts = Counter(value for row in normalized for value in row if value != 0)
    if command in (1, 2) and counts[command] != 1:
        errors.append("the command color must occur exactly once, at (0,0)")

    ordered_colors = _ordered_colors(normalized)
    pair_colors = tuple(color for color in ordered_colors if counts[color] == 2)
    singleton_colors = tuple(color for color in ordered_colors if counts[color] == 1)
    bad_counts = {color: counts[color] for color in ordered_colors if counts[color] not in (1, 2)}
    if bad_counts:
        errors.append(f"non-command colors must occur once or twice; found {bad_counts}")

    scene_profile = (
        _scene_profile(command, len(pair_colors), len(singleton_colors))
        if command in (1, 2)
        else None
    )
    if scene_profile is None:
        errors.append(
            "command, pair count, and singleton count do not match a declared scene profile"
        )

    all_markers = {
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    }
    pair_markers: dict[int, tuple[tuple[int, int], ...]] = {}
    pair_paths: dict[int, tuple[tuple[int, int], ...]] = {}
    aligned_colors: list[int] = []
    occupied_paths: set[tuple[int, int]] = set()
    overlap_cells: set[tuple[int, int]] = set()
    nonaligned_count = 0

    if command in (1, 2):
        for color in pair_colors:
            positions = _markers(normalized, color)
            pair_markers[color] = positions
            if len(positions) != 2:
                continue
            first, second = positions
            aligned = first[0] == second[0] or first[1] == second[1]
            if aligned:
                aligned_colors.append(color)
            else:
                nonaligned_count += 1
            path = _path_cells(first, second, command)
            pair_paths[color] = path
            interior = set(path) - {first, second}
            collisions = interior.intersection(all_markers - {first, second})
            if collisions:
                errors.append(
                    f"path for color {color} crosses another input marker at "
                    f"{sorted(collisions)}"
                )
            if not interior:
                errors.append(f"pair color {color} has no path interior to paint")
            overlap_cells.update(occupied_paths.intersection(path))
            occupied_paths.update(path)

    if pair_colors and nonaligned_count == 0:
        errors.append("at least one marker pair must differ in both row and column")

    if not errors:
        output = _rule_mirror(normalized)
        changed_cell_count = sum(
            before != after
            for input_row, output_row in zip(normalized, output)
            for before, after in zip(input_row, output_row)
        )
        result["facts"] = {
            "height": height,
            "width": width,
            "command": command,
            "ordered_colors": tuple(ordered_colors),
            "pair_colors": pair_colors,
            "singleton_colors": singleton_colors,
            "pair_count": len(pair_colors),
            "singleton_count": len(singleton_colors),
            "markers": pair_markers,
            "paths": pair_paths,
            "path_cells": frozenset(occupied_paths),
            "overlap_cells": frozenset(overlap_cells),
            "aligned_colors": tuple(aligned_colors),
            "scene_profile": scene_profile,
            "grid_profile": grid_profile,
            "changed_cell_count": changed_cell_count,
            "output": output,
        }
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "scene_profile": facts["scene_profile"],
        "grid_profile": facts["grid_profile"],
    }


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    normalized, _ = _normalize_grid(grid)
    assert normalized is not None
    palette_size = len({value for row in normalized for value in row})
    return facts["height"], facts["width"], palette_size


def _fact_predicate(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def witness(grid: Any) -> bool:
        analysis = _analyze(grid)
        return bool(not analysis["errors"] and predicate(analysis["facts"]))

    return witness


SEMANTIC_WITNESSES = {
    "command_1_horizontal_then_vertical": _fact_predicate(
        lambda facts: facts["command"] == 1
    ),
    "command_2_vertical_then_horizontal": _fact_predicate(
        lambda facts: facts["command"] == 2
    ),
    "multiple_pairs_all_processed": _fact_predicate(
        lambda facts: facts["pair_count"] >= 2
    ),
    "three_pair_iteration": _fact_predicate(
        lambda facts: facts["pair_count"] >= 3
    ),
    "aligned_pair_is_lawful": _fact_predicate(
        lambda facts: bool(facts["aligned_colors"])
    ),
    "singleton_is_preserved": _fact_predicate(
        lambda facts: bool(facts["singleton_colors"])
    ),
    "overlap_uses_first_appearance_priority": _fact_predicate(
        lambda facts: bool(facts["overlap_cells"])
    ),
    "paths_add_cells": _fact_predicate(
        lambda facts: facts["changed_cell_count"] > 0
    ),
    "command_cell_is_preserved": _fact_predicate(lambda facts: True),
}

SEMANTIC_RIVALS = {
    "always_horizontal_then_vertical": lambda grid: _rule_with_command(grid, 1),
    "always_vertical_then_horizontal": lambda grid: _rule_with_command(grid, 2),
    "first_pair_only": lambda grid: _rule_with_command(
        grid, grid[0][0], max_pairs=1
    ),
    "only_first_two_pairs": lambda grid: _rule_with_command(
        grid, grid[0][0], max_pairs=2
    ),
    "skip_aligned_pairs": lambda grid: _rule_with_command(
        grid, grid[0][0], skip_aligned=True
    ),
    "drop_singletons": _drop_singletons,
    "reverse_pair_priority": _reverse_pair_priority,
    "input_unchanged": _input_unchanged,
    "clear_command_cell": _clear_command,
}

WITNESS_RIVALS = {
    "command_1_horizontal_then_vertical": ["always_vertical_then_horizontal"],
    "command_2_vertical_then_horizontal": ["always_horizontal_then_vertical"],
    "multiple_pairs_all_processed": ["first_pair_only"],
    "three_pair_iteration": ["only_first_two_pairs"],
    "aligned_pair_is_lawful": ["skip_aligned_pairs"],
    "singleton_is_preserved": ["drop_singletons"],
    "overlap_uses_first_appearance_priority": ["reverse_pair_priority"],
    "paths_add_cells": ["input_unchanged"],
    "command_cell_is_preserved": ["clear_command_cell"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SCHEDULE_PROFILES = SCENE_PROFILES


def lesson_identifiable(demos, query) -> list[str]:
    del query
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            try:
                predicted = rival(demo["input"])
            except Exception:
                survived = False
                break
            if predicted != demo["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_grid_profile(sample_index: int) -> str:
    return ("canonical", "canonical", "small", "large")[sample_index % 4]


def _draw_dimensions(ctx, profile: str, band: str) -> tuple[int, int]:
    rng = ctx.draw_rng("dimensions")
    if profile == "canonical":
        return rng.choice(CANONICAL_DIMS)
    if profile == "small":
        return rng.choice(SMALL_DIMS)
    return rng.choice(LARGE_DIMS[band])


def _random_aligned_pair(rng, cells: list[tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    by_row: dict[int, list[int]] = {}
    by_col: dict[int, list[int]] = {}
    for row, col in cells:
        by_row.setdefault(row, []).append(col)
        by_col.setdefault(col, []).append(row)
    for _ in range(200):
        if rng.choice((True, False)):
            row = rng.choice(tuple(by_row))
            cols = by_row[row]
            a, b = rng.sample(cols, 2)
            if abs(a - b) >= 2:
                return tuple(sorted(((row, a), (row, b))))  # type: ignore[return-value]
        else:
            col = rng.choice(tuple(by_col))
            rows = by_col[col]
            a, b = rng.sample(rows, 2)
            if abs(a - b) >= 2:
                return tuple(sorted(((a, col), (b, col))))  # type: ignore[return-value]
    raise ValueError("could not draw an aligned pair")


def _place_scene(
    grid: list[list[int]],
    pair_colors: tuple[int, ...],
    singleton_colors: tuple[int, ...],
    command: int,
    *,
    require_aligned: bool,
    require_overlap: bool,
    forbid_overlap: bool,
    rng,
) -> None:
    height = len(grid)
    width = len(grid[0])
    cells = [(row, col) for row in range(1, height) for col in range(width)]

    for _attempt in range(50_000):
        pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
        used: set[tuple[int, int]] = set()

        if require_aligned:
            aligned = _random_aligned_pair(rng, cells)
            pairs.append(aligned)
            used.update(aligned)

        while len(pairs) < len(pair_colors):
            available = [cell for cell in cells if cell not in used]
            if len(available) < 2:
                break
            first, second = rng.sample(available, 2)
            if first[0] == second[0] or first[1] == second[1]:
                continue
            ordered = tuple(sorted((first, second)))
            pairs.append(ordered)  # type: ignore[arg-type]
            used.update(ordered)
        if len(pairs) != len(pair_colors):
            continue

        paths = [_path_cells(first, second, command) for first, second in pairs]
        all_markers = set(used)
        if any(
            (set(path) - {first, second}) & (all_markers - {first, second})
            for path, (first, second) in zip(paths, pairs)
        ):
            continue

        overlap: set[tuple[int, int]] = set()
        occupied: set[tuple[int, int]] = set()
        for path in paths:
            overlap.update(occupied.intersection(path))
            occupied.update(path)
        if require_overlap and not overlap:
            continue
        if forbid_overlap and overlap:
            continue

        singleton_positions: list[tuple[int, int]] = []
        if singleton_colors:
            available = [
                cell
                for cell in cells
                if cell not in all_markers and cell not in occupied
            ]
            if len(available) < len(singleton_colors):
                continue
            singleton_positions = rng.sample(available, len(singleton_colors))

        candidate = full_grid(height, width, 0)
        candidate[0][0] = command
        for color, (first, second) in zip(pair_colors, pairs):
            candidate[first[0]][first[1]] = color
            candidate[second[0]][second[1]] = color
        for color, (row, col) in zip(singleton_colors, singleton_positions):
            candidate[row][col] = color

        canonical_output = _rule_mirror(candidate)
        if require_overlap and _reverse_pair_priority(candidate) == canonical_output:
            continue
        if require_aligned and _rule_with_command(
            candidate, command, skip_aligned=True
        ) == canonical_output:
            continue
        for row in range(height):
            grid[row][:] = candidate[row]
        return
    raise ValueError("could not construct the requested L-path scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = "medium" if difficulty in (None, "default") else difficulty
    if band not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx_overrides = dict(overrides)
    ctx_overrides.setdefault("scene_profile", schedule_profile(seed, sample_index, band))
    ctx_overrides.setdefault("grid_profile", _scheduled_grid_profile(sample_index))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=ctx_overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    grid_profile = ctx.draw_choice("grid_profile", GRID_PROFILES)
    command, pair_count, singleton_count = SCENE_SIGNATURES[scene_profile]
    height, width = _draw_dimensions(ctx, grid_profile, band)

    colors = tuple(
        ctx.draw_distinct_colors(
            "marker_colors",
            n=pair_count + singleton_count,
            exclude={0, command},
        )
    )
    pair_colors = colors[:pair_count]
    singleton_colors = colors[pair_count:]
    grid = full_grid(height, width, 0)
    grid[0][0] = command

    require_aligned = scene_profile in {
        "cmd1_three_pairs",
        "cmd2_three_pairs_singleton",
    }
    require_overlap = scene_profile in {
        "cmd1_three_pairs",
        "cmd2_two_pairs",
        "cmd2_three_pairs_singleton",
    }
    forbid_overlap = scene_profile == "cmd1_two_pairs_singleton"
    _place_scene(
        grid,
        pair_colors,
        singleton_colors,
        command,
        require_aligned=require_aligned,
        require_overlap=require_overlap,
        forbid_overlap=forbid_overlap,
        rng=ctx.draw_rng("layout"),
    )

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generator constructed invalid scene: " + "; ".join(errors))
    return [row[:] for row in grid]
