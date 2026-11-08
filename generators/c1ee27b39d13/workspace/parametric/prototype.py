"""Two-rule native family for row/column submatrix extraction.

``source`` is the exact canonical authority. ``first_row_rank`` first performs
that extraction, then uses the first extracted row as an input-derived key and
stably reorders every extracted column by ascending key value. Inputs are shared
between settings and every retained scene makes the two rules and declared
shortcuts observationally distinct.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes

TASK_ID = "c1ee27b39d13"
HERE = Path(__file__).resolve().parent
MODES = ("source", "first_row_rank")
HYPOTHESES = MODES + (
    "reverse_columns",
    "first_row_descending",
    "last_row_rank",
    "second_row_rank",
    "column_sum_rank",
    "row_rank",
    "transpose",
)

# Height, width, selected row count, selected column count.  Prefixes are fixed,
# but positions, payloads, and key permutations vary deterministically by seed.
_DEMO_PROFILES = (
    (8, 9, 3, 4),
    (10, 12, 4, 5),
    (12, 14, 3, 6),
    (16, 18, 5, 6),
    (20, 22, 6, 7),
    (24, 26, 5, 8),
)
_QUERY_PROFILES = (
    (13, 15, 4, 5),
    (18, 21, 5, 6),
    (24, 27, 6, 7),
    (30, 30, 7, 8),
)
_KEY_PALETTE = (0, 4, 5, 9, 2, 7, 1, 8)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"column_order"}
        or type(settings["column_order"]) is not str
        or settings["column_order"] not in MODES
    ):
        raise ValueError(
            "settings must be exactly {'column_order': 'source'|'first_row_rank'}"
        )
    return settings["column_order"]


def program(settings: Any) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "source" else "first_row_rank.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError(
            "grid must be rectangular 1..30 with exact integer colors 0..9"
        )
    return value


def _selector_facts(value: Any):
    source = _grid(value)
    selected_cols = [
        col for col in range(1, len(source[0])) if source[0][col] == 4
    ]
    selected_rows = [
        row for row in range(1, len(source)) if source[row][0] == 5
    ]
    if len(selected_rows) < 2 or len(selected_cols) < 2:
        raise ValueError("scene needs at least two selected rows and columns")
    return source, selected_rows, selected_cols


def extract(value: Any) -> list[list[int]]:
    source, selected_rows, selected_cols = _selector_facts(value)
    return [
        [source[row][col] for col in selected_cols]
        for row in selected_rows
    ]


def _column_order(matrix: list[list[int]], hypothesis: str) -> list[int]:
    width = len(matrix[0])
    if hypothesis == "source":
        return list(range(width))
    if hypothesis == "first_row_rank":
        return sorted(range(width), key=lambda col: matrix[0][col])
    if hypothesis == "reverse_columns":
        return list(reversed(range(width)))
    if hypothesis == "first_row_descending":
        return sorted(range(width), key=lambda col: matrix[0][col], reverse=True)
    if hypothesis == "last_row_rank":
        return sorted(range(width), key=lambda col: matrix[-1][col])
    if hypothesis == "second_row_rank":
        return sorted(range(width), key=lambda col: matrix[1][col])
    if hypothesis == "column_sum_rank":
        return sorted(range(width), key=lambda col: sum(row[col] for row in matrix))
    raise ValueError(f"hypothesis does not define a column order: {hypothesis}")


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis: {hypothesis}")
    matrix = extract(value)
    if hypothesis == "row_rank":
        return sorted((row[:] for row in matrix), key=lambda row: row[0])
    if hypothesis == "transpose":
        return [list(row) for row in zip(*matrix, strict=True)]
    order = _column_order(matrix, hypothesis)
    return [[row[col] for col in order] for row in matrix]


def transform(value: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    return predict(value, mode)


def observe(value: Any) -> dict[str, Any]:
    source, selected_rows, selected_cols = _selector_facts(value)
    matrix = extract(source)
    return {
        "height": len(source),
        "width": len(source[0]),
        "selected_rows": len(selected_rows),
        "selected_cols": len(selected_cols),
        "first_row_key": matrix[0][:],
        "rank_order": _column_order(matrix, "first_row_rank"),
    }


def _derived_seed(seed: int, split: str, index: int) -> int:
    raw = json.dumps(
        [TASK_ID, "submatrix-rank-input-v1", seed, split, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _matrix_is_decisive(matrix: list[list[int]]) -> bool:
    # Test the matrix directly; this is the same transformation after extraction.
    outputs: dict[str, list[list[int]]] = {}
    for name in HYPOTHESES:
        if name == "row_rank":
            outputs[name] = sorted((row[:] for row in matrix), key=lambda row: row[0])
        elif name == "transpose":
            outputs[name] = [list(row) for row in zip(*matrix, strict=True)]
        else:
            order = _column_order(matrix, name)
            outputs[name] = [[row[col] for col in order] for row in matrix]
    return all(
        outputs[mode] != outputs[rival]
        for mode in MODES
        for rival in HYPOTHESES
        if rival != mode
    )


def _decisive_matrix(rng: random.Random, rows: int, cols: int) -> list[list[int]]:
    key_values = list(_KEY_PALETTE[:cols])
    for _attempt in range(512):
        first = key_values[:]
        rng.shuffle(first)
        if first in (sorted(first), sorted(first, reverse=True)):
            continue
        matrix = [first]
        for _ in range(rows - 1):
            matrix.append([rng.randrange(10) for _ in range(cols)])
        if _matrix_is_decisive(matrix):
            return matrix
    raise RuntimeError("failed to construct a decisive extracted matrix")


def _outside_selected_cell(
    height: int,
    width: int,
    selected_rows: set[int],
    selected_cols: set[int],
    *,
    used: set[tuple[int, int]],
) -> tuple[int, int]:
    for row in range(1, height):
        for col in range(1, width):
            if (row, col) in used:
                continue
            if row not in selected_rows or col not in selected_cols:
                used.add((row, col))
                return row, col
    raise AssertionError("profile has no payload distractor cell")


def sample_input(seed: int, index: int, *, split: str) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES if split == "test" else None
    if profiles is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, n_rows, n_cols = profiles[index]
    rng = random.Random(_derived_seed(seed, split, index))

    selected_rows = sorted(rng.sample(range(1, height), n_rows))
    selected_cols = sorted(rng.sample(range(1, width), n_cols))
    grid = [[0] * width for _ in range(height)]

    # Dense, seed-varying payload gives the 30x30 case substantive content.
    for row in range(1, height):
        for col in range(1, width):
            grid[row][col] = 0 if rng.random() < 0.16 else rng.randrange(1, 10)

    matrix = _decisive_matrix(rng, n_rows, n_cols)
    for row_index, row in enumerate(selected_rows):
        for col_index, col in enumerate(selected_cols):
            grid[row][col] = matrix[row_index][col_index]

    for col in selected_cols:
        grid[0][col] = 4
    selected_row_set = set(selected_rows)
    selected_col_set = set(selected_cols)
    for row in selected_rows:
        grid[row][0] = 5
    unselected_rows = [row for row in range(1, height) if row not in selected_row_set]
    for row in unselected_rows:
        grid[row][0] = rng.choice((0, 0, 1, 2, 3, 4, 6, 7, 8, 9))
    if not any(grid[row][0] not in (0, 5) for row in unselected_rows):
        grid[unselected_rows[0]][0] = 7

    # Make marker colors ordinary payload values without disturbing the decisive matrix.
    used: set[tuple[int, int]] = set()
    for color in (4, 5):
        row, col = _outside_selected_cell(
            height,
            width,
            selected_row_set,
            selected_col_set,
            used=used,
        )
        grid[row][col] = color

    # Force all four borders to carry meaningful content in the 30x30 stress case.
    if (height, width) == (30, 30):
        grid[height - 1][width - 1] = 9
        grid[height - 1][1] = 8
        grid[1][width - 1] = 7

    # Construction invariants and rule separation are checked before release.
    source, rows_found, cols_found = _selector_facts(grid)
    if rows_found != selected_rows or cols_found != selected_cols:
        raise AssertionError("selector construction drifted")
    extracted = extract(source)
    if not _matrix_is_decisive(extracted):
        raise AssertionError("selected submatrix lost rule separation")
    return grid


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
    }
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            source = sample_input(seed, index, split=split)
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            episode[split].append(
                {"input": source, "output": transform(source, mode)}
            )
    episode["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return episode


def teaching_certificate(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain a train list")
    train = episode["train"]
    tests = episode.get("test", [])
    survivors = []
    rejected: dict[str, int] = {}
    for name in HYPOTHESES:
        mismatch = next(
            (
                index
                for index, pair in enumerate(train)
                if predict(pair["input"], name) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            survivors.append(name)
        else:
            rejected[name] = mismatch
    return {
        "schema": "c1ee27b39d13-teaching-certificate-v1",
        "demos": len(train),
        "queries": len(tests),
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "rejected_at_demo": rejected,
    }


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = episode.get("train")
    tests = episode.get("test")
    if type(train) is not list or type(tests) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(query_index, 0, len(tests) - 1, "query_index")
    visible = {"train": train, "test": [tests[query_index]]}
    return json.loads(public_challenge_bytes(visible))


__all__ = [
    "HYPOTHESES",
    "MODES",
    "extract",
    "generate",
    "observe",
    "predict",
    "program",
    "public_turn",
    "sample_input",
    "teaching_certificate",
    "transform",
]
