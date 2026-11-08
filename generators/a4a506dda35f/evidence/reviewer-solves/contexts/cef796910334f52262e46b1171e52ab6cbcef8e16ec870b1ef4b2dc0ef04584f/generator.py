"""Curriculum generator for Frequency-Sorted Color Bar.

The authoritative Racket rule counts every non-background cell, sorts colors by
(count descending, numeric color ascending), and emits those cells as one row.
The sampler deliberately includes two distinctions absent from the canonical
bank: adjacent same-color cells (cell count, not component count) and tied
frequencies whose row-major first-seen order conflicts with the numeric tie
break.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import permutations
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "a4a506dda35f"
RULE_HASH = "639443b5cb4a"
VERSION = "3.1.0"
SUMMARY = (
    "Sparse 0-background grids with three or four colors. Count every painted "
    "cell by color, sort by frequency descending and numeric color ascending "
    "on ties, then emit one row containing each color once per painted cell. "
    "Ordinary examples include an adjacent same-color pair, vary frequency "
    "assignments independently of shape and palette, and alternate between "
    "tied and distinct frequencies so component-count, profile-lookup, and "
    "first-seen tie-break shortcuts are explicitly refuted."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
# Across four palettes, the supported frequency assignments yield 552 bars.
EXPECTED_OUTPUT_CODOMAIN = 552

SCHEDULE_PROFILES = (
    "canonical_7x9_tie",
    "canonical_7x10_distinct",
    "canonical_7x11_tie",
    "canonical_8x10_distinct",
    "expanded_10x14_four_tie",
    "expanded_9x12_four_distinct",
)
PALETTE_PROFILES = ("low", "warm", "cool", "mixed")

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "deterministic six-position lesson schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
    "palette_profile": {
        "type": "str",
        "default": "keyed choice",
        "valid": "|".join(PALETTE_PROFILES),
    },
}

INVARIANTS = [
    "background is color 0",
    "canonical-shape profiles use three nonzero colors; expanded profiles use four",
    "every nonzero color occurs 1..4 times and the output length fits the input width",
    "frequency signatures and their color assignments vary independently of shape and palette",
    "every ordinary draw contains adjacent same-color cells",
    "every even schedule position contains a frequency tie with reverse first-seen order",
]

# Layout controls only shape, color count, and whether a tie is guaranteed.
# Frequency signatures and assignments to colors are sampled independently.
_LAYOUTS: dict[str, tuple[int, int, int, str]] = {
    "canonical_7x9_tie": (7, 9, 3, "tie"),
    "canonical_7x10_distinct": (7, 10, 3, "distinct"),
    "canonical_7x11_tie": (7, 11, 3, "tie"),
    "canonical_8x10_distinct": (8, 10, 3, "distinct"),
    "expanded_10x14_four_tie": (10, 14, 4, "tie"),
    "expanded_9x12_four_distinct": (9, 12, 4, "distinct"),
}
_COUNT_SIGNATURES: dict[tuple[int, str], tuple[tuple[int, ...], ...]] = {
    (3, "tie"): (
        (4, 2, 2),
        (3, 3, 2),
        (3, 2, 2),
        (3, 3, 1),
        (2, 2, 1),
        (4, 1, 1),
    ),
    (3, "distinct"): (
        (4, 3, 2),
        (4, 3, 1),
        (4, 2, 1),
        (3, 2, 1),
    ),
    (4, "tie"): (
        (4, 2, 2, 1),
        (3, 2, 2, 1),
        (4, 3, 1, 1),
        (3, 3, 2, 1),
        (4, 3, 2, 2),
        (3, 2, 1, 1),
    ),
    (4, "distinct"): ((4, 3, 2, 1),),
}
_PALETTES: dict[str, tuple[int, ...]] = {
    "low": (1, 2, 3, 4),
    "warm": (2, 4, 6, 9),
    "cool": (1, 5, 7, 8),
    "mixed": (2, 3, 7, 8),
}
_SHAPE_TO_LAYOUT = {
    (height, width): name
    for name, (height, width, _n_colors, _mode) in _LAYOUTS.items()
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the position-stable lesson profile; seed/band do not alter semantics."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not str:
            raise TypeError(f"{name} must be a string")
        options = SCHEDULE_PROFILES if name == "layout_profile" else PALETTE_PROFILES
        if value not in options:
            raise ValueError(f"unknown {name}: {value!r}")


def _tie_colors(colors: tuple[int, ...], counts: tuple[int, ...]) -> tuple[int, int] | None:
    groups: dict[int, list[int]] = {}
    for color, count in zip(colors, counts):
        groups.setdefault(count, []).append(color)
    tied = [values for values in groups.values() if len(values) >= 2]
    if not tied:
        return None
    values = sorted(tied[0])
    return values[0], values[-1]


def _draw_grid(
    height: int,
    width: int,
    colors: tuple[int, ...],
    counts: tuple[int, ...],
    rng,
) -> list[list[int]]:
    """Place exact counts while forcing the two intended semantic witnesses."""
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()
    remaining = dict(zip(colors, counts))

    tied = _tie_colors(colors, counts)
    if tied is not None:
        lower, higher = tied
        # Absolute first painted cell is the numerically higher tied color.
        # A row-major first-seen tie-break therefore disagrees with the rule.
        grid[0][0] = higher
        occupied.add((0, 0))
        remaining[higher] -= 1

    dominant = colors[counts.index(max(counts))]
    dominoes = [
        ((row, col), (row, col + 1))
        for row in range(height)
        for col in range(width - 1)
        if (row, col) not in occupied and (row, col + 1) not in occupied
    ]
    first, second = rng.choice(dominoes)
    for row, col in (first, second):
        grid[row][col] = dominant
        occupied.add((row, col))
    remaining[dominant] -= 2

    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in occupied
    ]
    rng.shuffle(cells)
    cursor = 0
    # Interleave colors so the examples remain sparse rather than forming bars.
    while any(value > 0 for value in remaining.values()):
        for color in colors:
            if remaining[color] <= 0:
                continue
            row, col = cells[cursor]
            cursor += 1
            grid[row][col] = color
            remaining[color] -= 1
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    layout_options = SCHEDULE_PROFILES if overrides.get("layout_profile") is not None else (scheduled,)
    layout_profile = ctx.draw_choice("layout_profile", layout_options)
    palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)

    height, width, n_colors, mode = _LAYOUTS[layout_profile]
    colors = tuple(sorted(_PALETTES[palette_profile][:n_colors]))
    frequency_rng = ctx.draw_rng("frequency_assignment")
    signature = frequency_rng.choice(_COUNT_SIGNATURES[(n_colors, mode)])
    assignments = tuple(sorted(set(permutations(signature))))
    counts = frequency_rng.choice(assignments)
    band = difficulty or "unspecified"
    return _draw_grid(height, width, colors, counts, ctx.draw_rng(f"placement_{band}"))


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["ARC grid dimensions must be at most 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not bool or float)"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the supported canonical-shaped curriculum manifold."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    shape = (len(grid), len(grid[0]))
    if shape not in _SHAPE_TO_LAYOUT:
        return [f"unsupported input shape {shape}"]
    counts = Counter(value for row in grid for value in row if value != 0)
    expected_colors = _LAYOUTS[_SHAPE_TO_LAYOUT[shape]][2]
    if len(counts) != expected_colors:
        errors.append(f"expected {expected_colors} nonzero colors, found {len(counts)}")
    if counts and (min(counts.values()) < 1 or max(counts.values()) > 4):
        errors.append(f"color counts must be in 1..4, found {sorted(counts.values())}")
    if sum(counts.values()) > shape[1]:
        errors.append("single-row output would be wider than the input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Strictly accept canonical examples and generated curriculum examples."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover both advertised controls from a generated return."""
    errors = _grid_errors(grid)
    if errors:
        return {"layout_profile": None, "palette_profile": None}
    layout = _SHAPE_TO_LAYOUT.get((len(grid), len(grid[0])))
    colors = frozenset(value for row in grid for value in row if value != 0)
    palette = None
    if layout is not None:
        n_colors = _LAYOUTS[layout][2]
        for name, values in _PALETTES.items():
            if colors == frozenset(values[:n_colors]):
                palette = name
                break
    return {"layout_profile": layout, "palette_profile": palette}


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror used only for diagnostics; Racket remains label authority."""
    counts = Counter(value for row in grid for value in row if value != 0)
    output: list[int] = []
    for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        output.extend([color] * count)
    return [output]


def _component_count_sort(grid) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    counts: Counter[int] = Counter()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            counts[color] += 1
            seen.add((row, col))
            pending = deque([(row, col)])
            while pending:
                rr, cc = pending.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
    output: list[int] = []
    for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        output.extend([color] * count)
    return [output]


def _first_seen_tie_break(grid) -> list[list[int]]:
    counts: Counter[int] = Counter()
    first: dict[int, int] = {}
    width = len(grid[0])
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            counts[color] += 1
            first.setdefault(color, row * width + col)
    output: list[int] = []
    for color in sorted(counts, key=lambda value: (-counts[value], first[value])):
        output.extend([color] * counts[color])
    return [output]


def _cell_count_not_component_count(grid) -> bool:
    return rule_mirror(grid) != _component_count_sort(grid)


def _numeric_tie_break_not_first_seen(grid) -> bool:
    return rule_mirror(grid) != _first_seen_tie_break(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "cell_count_not_component_count": _cell_count_not_component_count,
    "numeric_tie_break_not_first_seen": _numeric_tie_break_not_first_seen,
}
_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "component_count_sort": _component_count_sort,
    "first_seen_tie_break": _first_seen_tie_break,
}
SEMANTIC_RIVALS = _RIVALS
CANONICAL_SHORTCUTS = _RIVALS
LESSON_COMPETITORS = _RIVALS
WITNESS_RIVALS = {
    "cell_count_not_component_count": ["component_count_sort"],
    "numeric_tie_break_not_first_seen": ["first_seen_tie_break"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared canonical shortcut survives demos."""
    return [
        f"{name} fits all demonstrations but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
