"""Native finite bar-chart family for ecd92348e78a.

Step A measures each nonzero color's bounding-box row height and orders the
(height, color) records.  Step B consumes that ordered intermediate to render
one compact output bar per color, anchored at the selected vertical edge.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import find_root, load_selected_generator, normalize_grid


TASK_ID = "ecd92348e78a"
SORT_ORDERS = ("descending", "ascending")
BAR_ALIGNMENTS = ("top", "bottom")
SETTINGS = tuple(
    {"sort_order": sort_order, "bar_alignment": alignment}
    for sort_order in SORT_ORDERS
    for alignment in BAR_ALIGNMENTS
)
_HERE = Path(__file__).resolve().parent
_RULES = {
    (sort_order, alignment): _HERE / "rules" / f"{sort_order}-{alignment}.rkt"
    for sort_order in SORT_ORDERS
    for alignment in BAR_ALIGNMENTS
}


def _checked_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _checked_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"sort_order", "bar_alignment"}:
        raise ValueError("settings must contain exactly sort_order and bar_alignment")
    sort_order = settings["sort_order"]
    alignment = settings["bar_alignment"]
    if type(sort_order) is not str or sort_order not in SORT_ORDERS:
        raise ValueError(f"sort_order must be one of {SORT_ORDERS}")
    if type(alignment) is not str or alignment not in BAR_ALIGNMENTS:
        raise ValueError(f"bar_alignment must be one of {BAR_ALIGNMENTS}")
    return {"sort_order": sort_order, "bar_alignment": alignment}


def _checked_counts(demos: Any, queries: Any) -> tuple[int, int]:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")
    return demos, queries


def _stream_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{label}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & (2**63 - 1)


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in normalize_grid(grid))


def _bbox_stats(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    grid = normalize_grid(grid)
    colors = sorted({cell for row in grid for cell in row if cell != 0})
    result = []
    for color in colors:
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, value in enumerate(row)
            if value == color
        ]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        result.append((color, max(rows) - min(rows) + 1, max(cols) - min(cols) + 1))
    return result


def measured_intermediate(
    grid: list[list[int]], sort_order: str
) -> list[tuple[int, int]]:
    """Return Step A's ordered ``(height, color)`` records."""
    if sort_order not in SORT_ORDERS:
        raise ValueError(f"sort_order must be one of {SORT_ORDERS}")
    measured = [(height, color) for color, height, _width in _bbox_stats(grid)]
    return sorted(measured, key=lambda item: item[0], reverse=sort_order == "descending")


def render_intermediate(
    ordered: list[tuple[int, int]], bar_alignment: str
) -> list[list[int]]:
    """Render Step B from the Step-A intermediate."""
    if bar_alignment not in BAR_ALIGNMENTS:
        raise ValueError(f"bar_alignment must be one of {BAR_ALIGNMENTS}")
    if not ordered:
        raise ValueError("at least one nonzero color is required")
    maximum = max(height for height, _color in ordered)
    output = [[0 for _ in ordered] for _ in range(maximum)]
    for column, (height, color) in enumerate(ordered):
        first_row = 0 if bar_alignment == "top" else maximum - height
        for row in range(first_row, first_row + height):
            output[row][column] = color
    return output


def solve_variant(
    grid: list[list[int]], sort_order: str, bar_alignment: str
) -> list[list[int]]:
    return render_intermediate(measured_intermediate(grid, sort_order), bar_alignment)


def program(settings: dict[str, Any]) -> str:
    checked = _checked_settings(settings)
    path = _RULES[(checked["sort_order"], checked["bar_alignment"])]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"empty Racket rule: {path}")
    return text


def _all_setting_outputs_distinct(grid: list[list[int]]) -> bool:
    outputs = {
        _freeze(solve_variant(grid, setting["sort_order"], setting["bar_alignment"]))
        for setting in SETTINGS
    }
    return len(outputs) == len(SETTINGS)


def _ordinary_inputs(
    seed: int,
    stream: str,
    count: int,
    forbidden: set[tuple[tuple[int, ...], ...]] | None = None,
) -> list[list[list[int]]]:
    root = find_root(__file__)
    module, _source, _digest = load_selected_generator(TASK_ID, root=root)
    seen = set() if forbidden is None else set(forbidden)
    result: list[list[list[int]]] = []
    base_seed = _stream_seed(seed, stream)
    difficulties = ("easy", "medium", "hard", None)
    for attempt in range(320):
        candidate_seed = (base_seed + attempt // 64) & (2**63 - 1)
        sample_index = attempt
        difficulty = difficulties[attempt % len(difficulties)]
        grid = normalize_grid(
            module.generate(candidate_seed, sample_index, difficulty=difficulty)
        )
        if list(module.strict_canonical_like(grid)):
            continue
        frozen = _freeze(grid)
        if frozen in seen or not _all_setting_outputs_distinct(grid):
            continue
        result.append(grid)
        seen.add(frozen)
        if len(result) == count:
            return result
    raise RuntimeError(f"could not construct {count} distinct {stream} inputs")


def _stress_grid(seed: int) -> list[list[int]]:
    """Construct a substantive 30x30 lawful extension of the same rule."""
    rng = random.Random(_stream_seed(seed, "stress"))
    palette = list(range(1, 10))
    rng.shuffle(palette)
    colors = palette[:5]
    heights = [30, 25, 20, 15, 10]
    # Keep bands disjoint in columns so every bbox height is explicit while
    # varying top, bottom and interior contact across the scene.
    columns = [0, 5, 10, 15, 20]
    widths = [4, 4, 4, 4, 4]
    starts = [0, 5, rng.randint(0, 10), rng.randint(0, 15), rng.randint(0, 20)]
    grid = [[0 for _ in range(30)] for _ in range(30)]
    for color, height, column, width, start in zip(
        colors, heights, columns, widths, starts
    ):
        for row in range(start, start + height):
            for col in range(column, column + width):
                grid[row][col] = color
    if not _all_setting_outputs_distinct(grid):
        raise AssertionError("30x30 stress scene failed to distinguish settings")
    return grid


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _checked_seed(seed)
    checked = _checked_settings(settings)
    demos, queries = _checked_counts(demos, queries)

    # Build the full six-demo bank first so changing the requested prefix never
    # changes the four-query bank or any earlier demonstration.
    demo_bank = _ordinary_inputs(seed, "demos", 6)
    forbidden = {_freeze(grid) for grid in demo_bank}
    query_bank = _ordinary_inputs(seed, "queries", 3, forbidden=forbidden)
    query_bank.append(_stress_grid(seed))
    random.Random(_stream_seed(seed, "query-order")).shuffle(query_bank)

    selected_program = program(checked)
    label = lambda grid: solve_variant(
        grid, checked["sort_order"], checked["bar_alignment"]
    )
    return {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": checked,
        "train": [
            {"input": grid, "output": label(grid)} for grid in demo_bank[:demos]
        ],
        "test": [{"input": grid, "output": label(grid)} for grid in query_bank],
        "program_solution": selected_program,
        "private_metadata": {
            "schema": "arcpuzzles-ecd92348e78a-private-v1",
            "sequential_dependency": {
                "step_a": "measure every nonzero color bbox height and sort the (height,color) records",
                "intermediate": "ordered list of (height,color) records",
                "step_b": "render aligned bars by consuming the ordered records",
            },
            "query_roles": [
                "seed-shuffled transfer/boundary/density/stress bank"
            ],
        },
    }
