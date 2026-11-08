"""Deterministic midpoint-selection family for task 02fcd49e49d6.

The exact canonical setting paints every eligible midpoint.  The alternative
first reads a unique color-1 cue at an occupied midpoint, then paints only rows
whose endpoint gap matches that input-derived gap.
"""
from __future__ import annotations

import hashlib
import random
from collections import Counter
from pathlib import Path
from typing import Callable

HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "all_pairs": HOME / "canonical.rkt",
    "cue_gap": HOME / "cue_gap.rkt",
}
SETTINGS = tuple(PROGRAM_FILES)
DEMO_SHAPES = ((9, 13), (11, 15), (13, 17), (15, 19), (17, 21), (19, 23))
QUERY_SHAPES = ((10, 14), (16, 20), (23, 27), (30, 30))


def _exact_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _selection(settings: object) -> str:
    if not isinstance(settings, dict) or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    value = settings["selection"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"selection must be one of {SETTINGS}")
    return value


def program(settings: object) -> str:
    return PROGRAM_FILES[_selection(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"02fcd49e49d6|{seed}|{split}|{index}".encode("ascii")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _pair(width: int, gap: int, rng: random.Random, *, edge: str | None = None) -> tuple[int, int]:
    if gap <= 0 or gap >= width or gap % 2:
        raise ValueError("gap must be a positive even distance inside the row")
    if edge == "left":
        start = 0
    elif edge == "right":
        start = width - 1 - gap
    else:
        start = rng.randint(0, width - 1 - gap)
    return start, start + gap


def _paint_pair(row: list[int], gap: int, rng: random.Random, *, edge: str | None = None) -> tuple[int, int]:
    c1, c2 = _pair(len(row), gap, rng, edge=edge)
    row[c1] = 8
    row[c2] = 8
    return c1, c2


def _shape(split: str, index: int) -> tuple[int, int]:
    profiles = DEMO_SHAPES if split == "train" else QUERY_SHAPES
    return profiles[index]


def _teaching_rows(height: int, split: str, index: int) -> tuple[int, list[int], list[int]]:
    if split == "test" and index == 3:
        cue_row = 0
        near_rows = [1, height - 2]
    else:
        cue_row = height // 3 if index % 2 == 0 else (2 * height) // 3
        cue_row = max(2, min(height - 3, cue_row))
        near_rows = [cue_row - 1, cue_row + 1]
    candidate_rows = [
        row for row in range(height) if row != cue_row and row not in near_rows
    ]
    return cue_row, candidate_rows, near_rows


def _guarded_gap_assignment(
    candidate_rows: list[int],
    gaps: list[int],
    cue_row: int,
    cue_gap: int,
    rng: random.Random,
) -> dict[int, int]:
    if len(candidate_rows) != len(gaps):
        raise ValueError("candidate rows and gaps must have equal length")
    above = [row for row in candidate_rows if row < cue_row]
    below = [row for row in candidate_rows if row > cue_row]
    guard_rows = [min(candidate_rows), max(candidate_rows)]
    if above:
        guard_rows.append(max(above))
    if below:
        guard_rows.append(min(below))
    guard_rows = list(dict.fromkeys(guard_rows))

    remaining_gaps = gaps[:]
    rng.shuffle(remaining_gaps)
    assignment: dict[int, int] = {}
    for row in guard_rows:
        index = next(
            (i for i, gap in enumerate(remaining_gaps) if gap != cue_gap),
            None,
        )
        if index is None:
            raise ValueError("not enough non-cue gaps for positional guards")
        assignment[row] = remaining_gaps.pop(index)

    remaining_rows = [row for row in candidate_rows if row not in assignment]
    rng.shuffle(remaining_rows)
    rng.shuffle(remaining_gaps)
    assignment.update(zip(remaining_rows, remaining_gaps))
    if cue_gap not in assignment.values():
        raise ValueError("teaching scene needs at least one cue-matching candidate")
    return assignment


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    height, width = _shape(split, index)
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    even_gaps = list(range(2, min(width, 13), 2))
    if len(even_gaps) < 3:
        raise ValueError("profile needs at least gaps 2, 4, and 6")
    teaching_gaps = even_gaps[1:-1]
    if len(teaching_gaps) < 2:
        raise ValueError("profile needs internal cue gaps")
    cue = teaching_gaps[(seed + index) % len(teaching_gaps)]

    cue_row, candidate_rows, near_rows = _teaching_rows(height, split, index)
    candidate_count = len(candidate_rows)
    if candidate_count < 4 or len(near_rows) != 2:
        raise ValueError("profile cannot allocate the teaching row roles")

    cue_edge = "left" if split == "test" and index == 3 else None
    c1, c2 = _paint_pair(grid[cue_row], cue, rng, edge=cue_edge)
    grid[cue_row][(c1 + c2) // 2] = 1

    decoy = even_gaps[0]
    rare = even_gaps[-1]
    other = decoy
    # The lesson needs a varying number of positive rows, while frequency alone
    # must point somewhere else.  Across profiles the cue has 2, 3, or 4
    # candidates; a non-cue decoy has one more, and another non-cue gap occurs
    # exactly once.  This defeats both frequency and fixed-result-count rules.
    cue_count = 2 + index % 3
    gaps = [cue] * cue_count + [decoy] * (cue_count + 1) + [rare]
    fillers = [
        gap for gap in even_gaps if gap not in {cue, rare, decoy}
    ] + [decoy]
    gaps.extend(
        fillers[offset % len(fillers)]
        for offset in range(candidate_count - len(gaps))
    )
    if len(gaps) != candidate_count:
        raise ValueError("candidate gap schedule has the wrong size")
    assigned_gaps = _guarded_gap_assignment(candidate_rows, gaps, cue_row, cue, rng)
    for row_index in candidate_rows:
        gap = assigned_gaps[row_index]
        edge = None
        if split == "test" and index == 3 and row_index == height - 1:
            edge = "right"
        _paint_pair(grid[row_index], gap, rng, edge=edge)

    # Two non-firing witnesses: an odd-distance pair and an occupied midpoint.
    odd_gap = rng.choice(list(range(1, min(width, 12), 2)))
    odd_start = rng.randint(0, width - 1 - odd_gap)
    grid[near_rows[0]][odd_start] = 8
    grid[near_rows[0]][odd_start + odd_gap] = 8
    filled_gap = other
    f1, f2 = _paint_pair(grid[near_rows[1]], filled_gap, rng)
    grid[near_rows[1]][(f1 + f2) // 2] = rng.choice((3, 4, 5, 6, 7, 9))
    return grid


def _cue_gap(grid: list[list[int]]) -> int:
    gaps = []
    for row in grid:
        hits = [index for index, value in enumerate(row) if value == 8]
        if len(hits) != 2:
            continue
        c1, c2 = hits
        if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 1:
            gaps.append(c2 - c1)
    if len(gaps) != 1:
        raise ValueError(f"expected one cue row, found {len(gaps)}")
    return gaps[0]


def _apply(grid: list[list[int]], selection: str) -> list[list[int]]:
    selected_gap = _cue_gap(grid) if selection == "cue_gap" else None
    output = [row[:] for row in grid]
    for row_index, row in enumerate(grid):
        hits = [index for index, value in enumerate(row) if value == 8]
        if len(hits) != 2:
            continue
        c1, c2 = hits
        if (c1 + c2) % 2:
            continue
        midpoint = (c1 + c2) // 2
        if row[midpoint] != 0:
            continue
        if selection == "all_pairs" or c2 - c1 == selected_gap:
            output[row_index][midpoint] = 2
    return output


def _pair_record(seed: int, split: str, index: int, selection: str) -> dict[str, list[list[int]]]:
    grid = _sample_input(seed, split, index)
    return {"input": grid, "output": _apply(grid, selection)}


def generate(seed: object, settings: object, demos: object, queries: object) -> dict:
    seed = _exact_int("seed", seed, 0, 2**63 - 1)
    demos = _exact_int("demos", demos, 2, 6)
    queries = _exact_int("queries", queries, 1, 4)
    selection = _selection(settings)
    train = [_pair_record(seed, "train", index, selection) for index in range(demos)]
    test = [_pair_record(seed, "test", index, selection) for index in range(queries)]
    return {"train": train, "test": test, "program_solution": program(settings)}


def rival_outputs(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    """Authoring-only rival catalog used by bounded identifiability audits."""
    identity = [row[:] for row in grid]

    def eligible_rows() -> list[tuple[int, int]]:
        rows = []
        for row_index, row in enumerate(grid):
            hits = [index for index, value in enumerate(row) if value == 8]
            if len(hits) != 2:
                continue
            c1, c2 = hits
            if (c1 + c2) % 2 == 0 and row[(c1 + c2) // 2] == 0:
                rows.append((row_index, c2 - c1))
        return rows

    candidates = eligible_rows()
    if not candidates:
        raise ValueError("rival audit needs at least one eligible candidate row")

    def fixed(gap: int | None) -> list[list[int]]:
        if gap is None:
            return [row[:] for row in grid]
        output = [row[:] for row in grid]
        for row_index, candidate_gap in candidates:
            if candidate_gap != gap:
                continue
            hits = [index for index, value in enumerate(grid[row_index]) if value == 8]
            midpoint = sum(hits) // 2
            output[row_index][midpoint] = 2
        return output

    cue = _apply(grid, "cue_gap")

    def limited(count: int, *, reverse: bool = False) -> list[list[int]]:
        output = [row[:] for row in grid]
        changed = [
            index
            for index, (before, after) in enumerate(zip(grid, cue))
            if before != after
        ]
        if reverse:
            changed.reverse()
        for index in changed[:count]:
            output[index] = cue[index][:]
        return output

    gaps = [gap for _row, gap in candidates]
    frequencies = Counter(gaps)

    def frequency_gap(*, most: bool, high_tie: bool) -> int:
        target_count = (max if most else min)(frequencies.values())
        tied = [gap for gap, count in frequencies.items() if count == target_count]
        return (max if high_tie else min)(tied)

    cue_row = next(
        row_index
        for row_index, row in enumerate(grid)
        if (hits := [index for index, value in enumerate(row) if value == 8])
        and len(hits) == 2
        and sum(hits) % 2 == 0
        and row[sum(hits) // 2] == 1
    )

    def positional_gap(kind: str) -> int | None:
        if kind == "top":
            return min(candidates)[1]
        if kind == "bottom":
            return max(candidates)[1]
        if kind == "nearest_above":
            above = [item for item in candidates if item[0] < cue_row]
            return max(above)[1] if above else None
        if kind == "nearest_below":
            below = [item for item in candidates if item[0] > cue_row]
            return min(below)[1] if below else None
        if kind == "nearest":
            return min(candidates, key=lambda item: (abs(item[0] - cue_row), item[0]))[1]
        if kind == "farthest":
            return max(candidates, key=lambda item: (abs(item[0] - cue_row), -item[0]))[1]
        raise ValueError(kind)

    outputs = {
        "identity": identity,
        "all_pairs": _apply(grid, "all_pairs"),
        "cue_gap": cue,
    }
    outputs.update({f"fixed_gap_{gap}": fixed(gap) for gap in range(2, 13, 2)})
    outputs.update({
        "first_only": limited(1),
        "last_only": limited(1, reverse=True),
        "first_two": limited(2),
        "last_two": limited(2, reverse=True),
        "min_gap": fixed(min(gaps)),
        "max_gap": fixed(max(gaps)),
        "modal_gap_min": fixed(frequency_gap(most=True, high_tie=False)),
        "modal_gap_max": fixed(frequency_gap(most=True, high_tie=True)),
        "rarest_gap_min": fixed(frequency_gap(most=False, high_tie=False)),
        "rarest_gap_max": fixed(frequency_gap(most=False, high_tie=True)),
        "top_gap": fixed(positional_gap("top")),
        "bottom_gap": fixed(positional_gap("bottom")),
        "nearest_above_gap": fixed(positional_gap("nearest_above")),
        "nearest_below_gap": fixed(positional_gap("nearest_below")),
        "nearest_gap": fixed(positional_gap("nearest")),
        "farthest_gap": fixed(positional_gap("farthest")),
    })
    return outputs

