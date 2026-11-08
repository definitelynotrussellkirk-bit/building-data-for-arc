"""Lawful input sampler for ARC task 23220e3be06f.

A command at the upper-left chooses one of six transforms.  After removing the
command, the remaining two-color motif is tightly cropped and transformed:
1 identity, 2 clockwise, 3 half-turn, 4 counter-clockwise, 5 left-right flip,
6 up-down flip.  This module samples inputs only; ``reference_output`` is an
executable mirror used by validation and semantic-rival probes.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "23220e3be06f"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "710976311dfe"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the command at (0,0), erase it, tightly crop the remaining two-color "
    "motif, then apply command 1=id, 2=clockwise, 3=180, 4=counter-clockwise, "
    "5=left-right flip, or 6=up-down flip."
)
INVARIANTS = [
    "the command is the only nonzero cell in row 0 and lies in 1..6",
    "the interior motif has 4..8 cells in exactly two colors",
    "the motif is fully asymmetric under D4, so every command is observable",
    "each default four-item lesson contains two copies of each of two commands",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-specific schedule with canonical-profile support",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-specific schedule with canonical-profile support",
        "valid": "8..11",
    },
    "code": {
        "type": "int",
        "default": "paired teaching cycle seeded across all six commands",
        "valid": "1..6",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-specific schedule",
        "valid": "4..8",
    },
    "palette_mode": {
        "type": "str",
        "default": "canonical-profile schedule",
        "valid": "overlap|distinct",
    },
}

# Every Cartesian combination of the declared axes is supported in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# The first five rows reproduce every exact canonical (height, width,
# palette-size) profile.  Remaining rows extend scale while staying close to
# the selected task.  Band-specific permutations make difficulty observable
# without narrowing any override domain.
_BASE_PROFILES = (
    (8, 9, "overlap"),
    (7, 8, "distinct"),
    (9, 9, "distinct"),
    (8, 10, "distinct"),
    (9, 10, "distinct"),
    (10, 11, "overlap"),
    (7, 10, "distinct"),
    (10, 8, "distinct"),
)
_PROFILE_SCHEDULES = {
    None: _BASE_PROFILES,
    "easy": _BASE_PROFILES,
    "medium": _BASE_PROFILES[2:] + _BASE_PROFILES[:2],
    "hard": _BASE_PROFILES[5:] + _BASE_PROFILES[:5],
}
_CELL_SCHEDULES = {
    None: (4, 5, 4, 7, 6, 8, 5, 7),
    "easy": (4, 4, 5, 5, 6, 7, 8, 6),
    "medium": (5, 6, 7, 4, 8, 6, 5, 7),
    "hard": (8, 7, 6, 5, 4, 8, 7, 6),
}
SCHEDULE_PROFILES = tuple(range(1, 7))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    int_ranges = {
        "grid_h": (7, 10),
        "grid_w": (8, 11),
        "code": (1, 6),
        "n_cells": (4, 8),
    }
    for name, value in overrides.items():
        if name in int_ranges:
            if type(value) is not int:
                raise ValueError(f"{name} override must be an integer")
            lo, hi = int_ranges[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
        elif name == "palette_mode":
            if type(value) is not str or value not in ("overlap", "distinct"):
                raise ValueError("palette_mode override must be 'overlap' or 'distinct'")


def _draw_exact(ctx: Any, name: str, domain: Iterable[Any], defaults: Iterable[Any]) -> Any:
    full_domain = tuple(domain)
    if name in ctx.overrides:
        return ctx.draw_choice(name, full_domain)
    return ctx.draw_choice(name, tuple(defaults))


def _mixed_seed_residue(seed: int) -> int:
    """Stable SplitMix64 finalizer; avoids counter/counter residue aliasing."""
    value = int(seed) & ((1 << 64) - 1)
    value = (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9 & ((1 << 64) - 1)
    value = (value ^ (value >> 27)) * 0x94D049BB133111EB & ((1 << 64) - 1)
    value ^= value >> 31
    return value % 6


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Return the default command profile for semantic-schedule census."""
    del difficulty
    return 1 + ((_mixed_seed_residue(seed) + int(sample_index) % 2) % 6)


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _transform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    source = [list(row) for row in grid]
    if not source or not source[0] or any(len(row) != len(source[0]) for row in source):
        raise ValueError("transform expects a nonempty rectangular grid")
    if code == 1:
        return source
    if code == 2:
        return _rotate_cw(source)
    if code == 3:
        return [list(reversed(row)) for row in reversed(source)]
    if code == 4:
        return _rotate_cw(_rotate_cw(_rotate_cw(source)))
    if code == 5:
        return [list(reversed(row)) for row in source]
    if code == 6:
        return [list(row) for row in reversed(source)]
    raise ValueError(f"unknown command {code}")


def _dihedral_images(grid: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    rotations = [[list(row) for row in grid]]
    for _ in range(3):
        rotations.append(_rotate_cw(rotations[-1]))
    reflected = [[list(reversed(row)) for row in image] for image in rotations]
    return tuple(tuple(tuple(row) for row in image) for image in rotations + reflected)


def _colored_components(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    count = 0
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    queue.append(nxt)
        count += 1
    return count


def _crop_motif(grid: list[list[int]]) -> tuple[list[list[int]], tuple[int, int, int, int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) != (0, 0)
    ]
    if not cells:
        raise ValueError("no motif cells")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    crop = [list(values[left : right + 1]) for values in grid[top : bottom + 1]]
    return crop, (top, left, bottom, right)


def _draw_motif(rng: Any, n_cells: int, colors: tuple[int, int]) -> list[list[int]]:
    dims = [
        (height, width)
        for height in range(2, 5)
        for width in range(2, 5)
        if height * width >= n_cells
    ]
    for _ in range(4096):
        height, width = rng.choice(dims)
        cells = rng.sample(
            [(row, col) for row in range(height) for col in range(width)],
            n_cells,
        )
        if ({row for row, _ in cells} & {0}) == set() or max(row for row, _ in cells) != height - 1:
            continue
        if ({col for _, col in cells} & {0}) == set() or max(col for _, col in cells) != width - 1:
            continue
        rng.shuffle(cells)
        values = [colors[0], colors[1]] + [rng.choice(colors) for _ in range(n_cells - 2)]
        rng.shuffle(values)
        motif = [[0] * width for _ in range(height)]
        for (row, col), value in zip(cells, values):
            motif[row][col] = value
        if set(values) != set(colors):
            continue
        if not 2 <= _colored_components(motif) <= 3:
            continue
        if len(set(_dihedral_images(motif))) != 8:
            continue
        return motif
    raise RuntimeError(f"unable to sample a lawful asymmetric {n_cells}-cell motif")


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"], None
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"], None

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 10:
        errors.append(f"grid height {height} outside 7..10")
    if not 8 <= width <= 11:
        errors.append(f"grid width {width} outside 8..11")
    code = grid[0][0]
    if code not in range(1, 7):
        errors.append(f"command {code!r} outside 1..6")
    if any(value != 0 for value in grid[0][1:]):
        errors.append("the command must be the only nonzero cell in row 0")
    if errors:
        return errors, None

    try:
        motif, (top, left, bottom, right) = _crop_motif([list(row) for row in grid])
    except ValueError:
        return ["no motif cells after removing the command"], None

    n_cells = sum(value != 0 for row in motif for value in row)
    colors = {value for row in motif for value in row if value != 0}
    motif_h, motif_w = len(motif), len(motif[0])
    if not 4 <= n_cells <= 8:
        errors.append(f"motif cell count {n_cells} outside 4..8")
    if len(colors) != 2:
        errors.append(f"motif must use exactly two colors, found {sorted(colors)}")
    if not 2 <= motif_h <= 4 or not 2 <= motif_w <= 4:
        errors.append(f"motif crop {motif_h}x{motif_w} outside 2..4 per side")
    if top < 2 or left < 2:
        errors.append("motif must leave at least two blank rows/columns after the command")
    if bottom >= height - 1 or right >= width - 1:
        errors.append("motif must leave at least one blank bottom/right margin")
    components = _colored_components(motif)
    if not 2 <= components <= 4:
        errors.append(f"motif has {components} color-connected components, expected 2..4")
    if len(set(_dihedral_images(motif))) != 8:
        errors.append("motif is not fully asymmetric under D4")
    if errors:
        return errors, None

    palette_mode = "overlap" if code in colors else "distinct"
    return [], {
        "grid_h": height,
        "grid_w": width,
        "code": code,
        "n_cells": n_cells,
        "palette_mode": palette_mode,
        "motif": motif,
        "motif_colors": frozenset(colors),
        "bbox": (top, left, bottom, right),
        "components": components,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {name: analysis[name] for name in AXES}


def reference_output(grid: Any) -> list[list[int]]:
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    return _transform_grid(analysis["motif"], analysis["code"])


rule_mirror = reference_output


def _rotations_only(grid: Any) -> list[list[int]]:
    """Canonical-fitting shortcut that ignores the two hidden flip commands."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside selected rule domain: " + "; ".join(errors))
    code = analysis["code"]
    return _transform_grid(analysis["motif"], code if code <= 4 else 1)


def _witness_flip_command(grid: Any) -> bool:
    errors, analysis = _analyze_grid(grid)
    return not errors and analysis is not None and analysis["code"] in (5, 6)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "flip_command": _witness_flip_command,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "rotations_only": _rotations_only,
}
WITNESS_RIVALS = {"flip_command": ["rotations_only"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require the demos to determine the query command's answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    episodes = list(demos) + [query]
    analyses: list[dict[str, Any]] = []
    for index, episode in enumerate(episodes):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{label} must contain input and output")
            continue
        errors, analysis = _analyze_grid(episode["input"])
        if errors or analysis is None:
            reasons.append(f"{label} is outside the rule domain: {errors[0]}")
            continue
        if episode["output"] != reference_output(episode["input"]):
            reasons.append(f"{label} output disagrees with the selected rule")
        analyses.append(analysis)
    if reasons:
        return reasons

    query_code = analyses[-1]["code"]
    if query_code not in {analysis["code"] for analysis in analyses[:-1]}:
        reasons.append(f"query command {query_code} is absent from the demonstrations")

    truth = reference_output(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != truth:
            reasons.append(f"named competitor {name!r} fits every demo but changes the query")
    return reasons


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    schedule = _PROFILE_SCHEDULES[difficulty]
    scheduled_h, scheduled_w, scheduled_mode = schedule[sample_index % len(schedule)]
    grid_h = int(_draw_exact(ctx, "grid_h", range(7, 11), (scheduled_h,)))
    grid_w = int(_draw_exact(ctx, "grid_w", range(8, 12), (scheduled_w,)))
    code_default = schedule_profile(seed, sample_index, difficulty)
    code = int(_draw_exact(ctx, "code", range(1, 7), (code_default,)))
    cell_default = _CELL_SCHEDULES[difficulty][sample_index % 8]
    n_cells = int(_draw_exact(ctx, "n_cells", range(4, 9), (cell_default,)))
    palette_mode = str(
        _draw_exact(ctx, "palette_mode", ("overlap", "distinct"), (scheduled_mode,))
    )

    rng = ctx.draw_rng("motif")
    nonzero = list(range(1, 10))
    if palette_mode == "overlap":
        other = rng.choice([color for color in nonzero if color != code])
        colors = (code, other)
    else:
        colors = tuple(rng.sample([color for color in nonzero if color != code], 2))
    motif = _draw_motif(rng, n_cells, (int(colors[0]), int(colors[1])))

    motif_h, motif_w = len(motif), len(motif[0])
    top = rng.randint(2, grid_h - motif_h - 1)
    left = rng.randint(2, grid_w - motif_w - 1)
    grid = full_grid(grid_h, grid_w, 0)
    grid[0][0] = code
    for row, values in enumerate(motif):
        for col, value in enumerate(values):
            if value:
                grid[top + row][left + col] = value

    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "code": code,
        "n_cells": n_cells,
        "palette_mode": palette_mode,
    }
    observed = {name: analysis[name] for name in AXES}
    if observed != expected:
        raise RuntimeError(f"internal axis mismatch: expected {expected}, observed {observed}")
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-semantic near misses that the validator must reject."""
    base = generate(
        53,
        11,
        grid_h=8,
        grid_w=9,
        code=2,
        n_cells=6,
        palette_mode="distinct",
    )
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_code = deepcopy(base)
    missing_code[0][0] = 0
    fixtures.append(("missing_code", missing_code))

    extra_top_row = deepcopy(base)
    extra_top_row[0][2] = 7
    fixtures.append(("extra_top_row", extra_top_row))

    monochrome = deepcopy(base)
    _, analysis = _analyze_grid(base)
    assert analysis is not None
    first, second = sorted(analysis["motif_colors"])
    for row in range(len(monochrome)):
        for col in range(len(monochrome[0])):
            if monochrome[row][col] == second:
                monochrome[row][col] = first
    fixtures.append(("monochrome_motif", monochrome))

    symmetric = full_grid(8, 9, 0)
    symmetric[0][0] = 2
    for row, col, color in ((3, 3, 4), (3, 4, 5), (4, 3, 5), (4, 4, 4)):
        symmetric[row][col] = color
    fixtures.append(("d4_symmetric_motif", symmetric))

    edge_touching = full_grid(8, 9, 0)
    edge_touching[0][0] = 2
    for row, col, color in ((1, 0, 4), (1, 1, 5), (2, 0, 5), (3, 1, 4)):
        edge_touching[row][col] = color
    fixtures.append(("edge_touching_motif", edge_touching))

    third_color = deepcopy(base)
    top, left, _, _ = analysis["bbox"]
    replacement = next(color for color in range(1, 10) if color not in analysis["motif_colors"])
    third_color[top][left] = replacement
    fixtures.append(("third_motif_color", third_color))
    return fixtures
