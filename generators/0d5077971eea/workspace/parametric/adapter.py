"""Native parametric adapter for 0d5077971eea.

The canonical setting keeps the exact row-local header rule.  The alternate
selects the eligible row with the most interior cyan markers, carries that
row's header color as an input-dependent intermediate, and uses it to recolor
all interior cyan markers.  Input generation is setting-neutral and count-
prefix stable, with a substantive 30x30 query.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "row_local": _HOME / "canonical.rkt",
    "densest_source": _HOME / "densest_source.rkt",
}
_NON_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

_DEMO_SPECS = (
    (7, 9, "compact"),
    (8, 11, "wide"),
    (9, 13, "dense"),
    (10, 15, "wide"),
    (11, 16, "dense"),
    (12, 16, "boundary"),
)
_QUERY_SPECS = (
    (8, 10, "transfer"),
    (12, 16, "boundary"),
    (18, 24, "dense"),
    (30, 30, "stress"),
)


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"header_policy"}:
        raise ValueError("settings must contain exactly header_policy")
    value = settings["header_policy"]
    if type(value) is not str or value not in _PROGRAM_FILES:
        raise ValueError("header_policy must be row_local or densest_source")
    return value


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    """Return the exact Racket source for one private setting."""
    policy = _validate_settings(settings)
    return _PROGRAM_FILES[policy].read_text(encoding="utf-8")


def _mix_seed(seed: int, role: str, index: int) -> int:
    payload = f"0d5077971eea|{seed}|{role}|{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _put_values(row: list[int], value: int, count: int, rng: random.Random) -> None:
    free = [col for col in range(1, len(row)) if row[col] == 0]
    if count > len(free):
        raise RuntimeError("row capacity exhausted")
    for col in rng.sample(free, count):
        row[col] = value


def _source_colors(seed: int, role: str, index: int) -> tuple[int, list[int]]:
    ordinal = index if role == "demo" else len(_DEMO_SPECS) + index
    offset = (seed + 3 * ordinal) % len(_NON_MARKER_COLORS)
    ordered = list(_NON_MARKER_COLORS[offset:] + _NON_MARKER_COLORS[:offset])
    return ordered[0], ordered[1:]


def _build_input(seed: int, role: str, index: int, spec: tuple[int, int, str]) -> list[list[int]]:
    height, width, profile = spec
    rng = random.Random(_mix_seed(seed, role, index))
    source_color, other_colors = _source_colors(seed, role, index)
    rows = list(range(height))
    rng.shuffle(rows)

    zero_row = rows.pop()
    eight_row = rows.pop()
    markerless_row = rows.pop()
    eligible_rows = rows
    if len(eligible_rows) < 4:
        raise RuntimeError("parametric row scene needs at least four eligible rows")
    source_row = eligible_rows[(seed + index) % len(eligible_rows)]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    source_peak = min(width - 1, max(5, width // 2 + 4))
    for order, row_index in enumerate(eligible_rows):
        color = source_color if row_index == source_row else other_colors[order % len(other_colors)]
        if color == source_color and row_index != source_row:
            color = other_colors[(order + 1) % len(other_colors)]
        grid[row_index][0] = color
        if row_index == source_row:
            count = source_peak
        else:
            spread = max(1, source_peak - 1)
            count = 1 + ((order * 5 + index * 3 + seed) % spread)
            count = min(count, source_peak - 1)
        _put_values(grid[row_index], 8, count, rng)

        # Foreign spectators make row scope and marker identity observable.
        spectator_count = 1 if profile == "compact" else min(3, max(1, width // 10))
        for spectator in other_colors[order % len(other_colors):]:
            if spectator_count <= 0:
                break
            if 0 in grid[row_index][1:]:
                _put_values(grid[row_index], spectator, 1, rng)
                spectator_count -= 1

    # A zero-header marker row separates row-local preservation from the global
    # selected-color rule; an 8-header row covers the canonical identity branch.
    _put_values(grid[zero_row], other_colors[0], 1, rng)
    _put_values(grid[zero_row], 8, min(4, width - 2), rng)
    grid[eight_row][0] = 8
    _put_values(grid[eight_row], other_colors[1], 1, rng)
    _put_values(grid[eight_row], 8, min(5, width - 2), rng)

    grid[markerless_row][0] = other_colors[2]
    markerless_fill = min(width - 1, 2 + width // 4)
    for color in other_colors[3:] + [source_color]:
        if markerless_fill <= 0 or 0 not in grid[markerless_row][1:]:
            break
        _put_values(grid[markerless_row], color, 1, rng)
        markerless_fill -= 1

    # Large scenes carry substantial distributed inert content without changing
    # the unique marker-count selector.
    target_nonzero = 120 if (height, width) == (30, 30) else max(0, (height * width) // 5)
    free = [(r, c) for r in range(height) for c in range(1, width) if grid[r][c] == 0]
    rng.shuffle(free)
    palette_cycle = list(other_colors) + [source_color]
    current_nonzero = sum(value != 0 for row in grid for value in row)
    for offset, (row_index, col_index) in enumerate(free):
        if current_nonzero >= target_nonzero:
            break
        grid[row_index][col_index] = palette_cycle[offset % len(palette_cycle)]
        current_nonzero += 1

    # Constructive assertion: one eligible row is strictly densest.
    marker_counts = [
        (sum(value == 8 for value in grid[r][1:]), r)
        for r in eligible_rows
    ]
    peak = max(count for count, _ in marker_counts)
    winners = [row for count, row in marker_counts if count == peak]
    if winners != [source_row]:
        raise RuntimeError(f"densest-row construction failed: {marker_counts!r}")
    return grid


def _row_local_output(grid: list[list[int]]) -> list[list[int]]:
    return [
        [
            row[0] if col > 0 and value == 8 and row[0] != 0 else value
            for col, value in enumerate(row)
        ]
        for row in grid
    ]


def _densest_source_output(grid: list[list[int]]) -> list[list[int]]:
    candidates = []
    for row_index, row in enumerate(grid):
        count = sum(value == 8 for value in row[1:])
        if row[0] not in (0, 8) and count:
            candidates.append((count, row_index, row[0]))
    if not candidates:
        return deepcopy(grid)
    peak = max(count for count, _, _ in candidates)
    winners = [(row_index, color) for count, row_index, color in candidates if count == peak]
    if len(winners) != 1:
        raise RuntimeError("episode input does not have a unique densest eligible row")
    color = winners[0][1]
    return [
        [color if col > 0 and value == 8 else value for col, value in enumerate(row)]
        for row in grid
    ]


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    output = _row_local_output(grid) if policy == "row_local" else _densest_source_output(grid)
    return {"input": deepcopy(grid), "output": output}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    """Generate one setting-neutral, count-prefix-stable parametric episode."""
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    policy = _validate_settings(settings)

    demo_inputs = [
        _build_input(seed, "demo", index, spec)
        for index, spec in enumerate(_DEMO_SPECS[:demos])
    ]
    query_bank = [
        _build_input(seed, "query", index, spec)
        for index, spec in enumerate(_QUERY_SPECS)
    ]
    selected_queries = query_bank[:queries]
    all_inputs = demo_inputs + selected_queries
    if len({repr(grid) for grid in all_inputs}) != len(all_inputs):
        raise RuntimeError("episode inputs are not distinct")

    return {
        "train": [_pair(grid, policy) for grid in demo_inputs],
        "test": [_pair(grid, policy) for grid in selected_queries],
        "program_solution": program(settings),
    }
