"""Native sequential family for gated vertical toggles and completed-column relay.

``toggle_only`` is the exact canonical authority. ``toggle_then_relay`` first
applies the canonical gated vertical toggle, then counts marker-colored cells in
each completed active column, selects the unique maximum, and copies that complete
processed column into the blank lane immediately left of a visible bottom cue.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import public_challenge_bytes

TASK_ID = "b38782448e7b"
HERE = Path(__file__).resolve().parent
MODES = ("toggle_only", "toggle_then_relay")
HYPOTHESES = MODES + (
    "identity",
    "relay_first_active",
    "relay_last_active",
    "relay_min_completed",
    "relay_raw_source",
    "relay_right_of_cue",
    "all_top_controls_then_relay",
)

_DEMO_PROFILES = (
    (10, 12, False),
    (12, 10, False),
    (14, 16, False),
    (18, 18, False),
    (22, 24, False),
    (26, 28, False),
)
_QUERY_PROFILES = (
    (13, 15, False),
    (18, 20, False),
    (24, 27, False),
    (30, 30, True),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"finish_rule"}
        or type(settings["finish_rule"]) is not str
        or settings["finish_rule"] not in MODES
    ):
        raise ValueError(
            "settings must be exactly {'finish_rule': "
            "'toggle_only'|'toggle_then_relay'}"
        )
    return settings["finish_rule"]


def program(settings: Any) -> str:
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "toggle_only" else "toggle_then_relay.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 2 <= len(value) <= 30
        or type(value[0]) is not list
        or not 2 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 2..30 with exact integer colors 0..9")
    return value


def background(value: Any) -> int:
    grid = _grid(value)
    counts = Counter(cell for row in grid for cell in row)
    top = max(counts.values())
    winners = [color for color, count in counts.items() if count == top]
    if len(winners) != 1:
        raise ValueError("grid must have a unique modal background")
    return winners[0]


def active_columns(value: Any, *, all_top: bool = False) -> list[int]:
    grid = _grid(value)
    bg = background(grid)
    if all_top:
        return [col for col, cell in enumerate(grid[0]) if cell != bg]
    return [
        col
        for col, cell in enumerate(grid[0])
        if cell != bg and cell != grid[1][col]
    ]


def toggle_only(value: Any, *, all_top: bool = False) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    source = deepcopy(grid)
    bg = background(source)
    for col in active_columns(source, all_top=all_top):
        marker = source[0][col]
        for row in range(1, len(source)):
            grid[row][col] = bg if grid[row][col] == marker else marker
    return grid


def completed_counts(value: Any, *, all_top: bool = False) -> list[dict[str, int]]:
    source = _grid(value)
    completed = toggle_only(source, all_top=all_top)
    return [
        {
            "column": col,
            "marker": source[0][col],
            "count": sum(completed[row][col] == source[0][col] for row in range(len(source))),
        }
        for col in active_columns(source, all_top=all_top)
    ]


def cue_column(value: Any) -> int:
    grid = _grid(value)
    found = [col for col, cell in enumerate(grid[-1]) if cell == 9]
    if len(found) != 1 or found[0] == 0 or found[0] == len(grid[0]) - 1:
        raise ValueError("grid must have one interior bottom cue of color 9")
    return found[0]


def relay_column(value: Any, source_col: int, destination_col: int) -> list[list[int]]:
    grid = deepcopy(_grid(value))
    width = len(grid[0])
    _integer(source_col, 0, width - 1, "source_col")
    _integer(destination_col, 0, width - 1, "destination_col")
    column = [row[source_col] for row in grid]
    for row, cell in enumerate(column):
        grid[row][destination_col] = cell
    return grid


def _winner(rows: list[dict[str, int]], which: str) -> dict[str, int]:
    if not rows:
        raise ValueError("no active columns")
    if which == "max":
        return max(rows, key=lambda row: row["count"])
    if which == "min":
        return min(rows, key=lambda row: row["count"])
    if which == "first":
        return rows[0]
    if which == "last":
        return rows[-1]
    raise ValueError(which)


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis: {hypothesis}")
    source = deepcopy(_grid(value))
    if hypothesis == "identity":
        return source
    completed = toggle_only(source)
    if hypothesis == "toggle_only":
        return completed
    destination = cue_column(source) - 1
    rows = completed_counts(source)
    if hypothesis == "toggle_then_relay":
        winner = _winner(rows, "max")
        return relay_column(completed, winner["column"], destination)
    if hypothesis == "relay_first_active":
        return relay_column(completed, _winner(rows, "first")["column"], destination)
    if hypothesis == "relay_last_active":
        return relay_column(completed, _winner(rows, "last")["column"], destination)
    if hypothesis == "relay_min_completed":
        return relay_column(completed, _winner(rows, "min")["column"], destination)
    if hypothesis == "relay_raw_source":
        winner = _winner(rows, "max")
        result = deepcopy(completed)
        raw_column = [row[winner["column"]] for row in source]
        for row, cell in enumerate(raw_column):
            result[row][destination] = cell
        return result
    if hypothesis == "relay_right_of_cue":
        winner = _winner(rows, "max")
        return relay_column(completed, winner["column"], cue_column(source) + 1)
    if hypothesis == "all_top_controls_then_relay":
        wrong_completed = toggle_only(source, all_top=True)
        wrong_rows = completed_counts(source, all_top=True)
        return relay_column(wrong_completed, _winner(wrong_rows, "max")["column"], destination)
    raise AssertionError(hypothesis)


def transform(value: Any, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    return predict(value, mode)


def observe(value: Any) -> dict[str, Any]:
    source = _grid(value)
    completed = toggle_only(source)
    rows = completed_counts(source)
    counts = [row["count"] for row in rows]
    winner = _winner(rows, "max")
    destination = cue_column(source) - 1
    return {
        "height": len(source),
        "width": len(source[0]),
        "background": background(source),
        "active_columns": [row["column"] for row in rows],
        "completed_marker_counts": counts,
        "unique_winner": counts.count(max(counts)) == 1,
        "winning_source_column": winner["column"],
        "destination_column": destination,
        "cue_column": cue_column(source),
        "raw_source_column": [row[winner["column"]] for row in source],
        "completed_source_column": [row[winner["column"]] for row in completed],
    }


def _derived_seed(seed: int, split: str, index: int) -> int:
    raw = json.dumps(
        [TASK_ID, "toggle-completed-column-relay-v1", seed, split, index],
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _active_positions(width: int, count: int) -> list[int]:
    # Reserve four rightmost columns for destination, cue and a wrong-side lane.
    usable = list(range(1, width - 4))
    if len(usable) < count + 1:
        raise AssertionError((width, count))
    values = [usable[round(index * (len(usable) - 1) / (count - 1))] for index in range(count)]
    if len(set(values)) != count:
        raise AssertionError(values)
    return values


def _paint_stress_blocks(
    grid: list[list[int]], reserved_cols: set[int], bg: int, palette: list[int]
) -> None:
    h, w = len(grid), len(grid[0])
    rectangles = (
        (2, 0, 8, 6),
        (2, w - 8, 8, w),
        (h - 8, 0, h, 6),
        (h - 8, w - 8, h, w),
    )
    color_index = 0
    for r0, c0, r1, c1 in rectangles:
        for r in range(r0, r1):
            for c in range(c0, c1):
                if c in reserved_cols or grid[r][c] != bg:
                    continue
                grid[r][c] = palette[color_index % len(palette)]
        color_index += 1


def _scene(seed: int, height: int, width: int, stress: bool) -> list[list[int]]:
    rng = random.Random(seed)
    backgrounds = [0, 4, 7, 8]
    bg = backgrounds[seed % len(backgrounds)]
    grid = [[bg] * width for _ in range(height)]
    cue = width - 2
    destination = cue - 1
    wrong_side = cue + 1
    active_count = 4 if stress else 3
    active = _active_positions(width, active_count)
    decoy = next(col for col in range(1, width - 4) if col not in active)

    palette = [color for color in (1, 2, 3, 5, 6, 8) if color != bg]
    rng.shuffle(palette)
    markers = palette[:active_count]
    target_counts = [3 + 2 * index for index in range(active_count)]
    winner_index = 1 + (seed % (active_count - 2))
    largest = target_counts[-1]
    remaining = target_counts[:-1]
    rng.shuffle(remaining)
    assigned = remaining[:winner_index] + [largest] + remaining[winner_index:]
    assigned = assigned[:active_count]

    for index, (col, marker, completed_count) in enumerate(zip(active, markers, assigned)):
        grid[0][col] = marker
        third = next(color for color in palette if color != marker)
        grid[1][col] = third
        raw_marker_count = height - completed_count
        marker_rows = list(range(2, 2 + raw_marker_count))
        if marker_rows and marker_rows[-1] >= height:
            raise AssertionError((height, completed_count, marker_rows[-1]))
        for row in marker_rows:
            grid[row][col] = marker
        # One extra third-color witness remains a non-marker and becomes marker.
        witness_row = min(height - 1, 2 + raw_marker_count)
        if witness_row >= 2 and grid[witness_row][col] == bg:
            grid[witness_row][col] = third

    decoy_marker = next(color for color in palette if color not in markers)
    grid[0][decoy] = decoy_marker
    grid[1][decoy] = decoy_marker
    if height > 3:
        grid[2][decoy] = next(color for color in palette if color != decoy_marker)

    grid[-1][cue] = 9
    reserved = set(active) | {decoy, destination, cue}
    if stress:
        _paint_stress_blocks(grid, reserved, bg, palette)
    else:
        # Compact preserved body mosaics on both sides of the controls.
        for row in range(max(3, height - 4), height - 1):
            for col in (0, width - 1):
                if col not in reserved:
                    grid[row][col] = palette[(row + col) % len(palette)]

    observed = observe(grid)
    if not observed["unique_winner"]:
        raise AssertionError(observed)
    if observed["raw_source_column"] == observed["completed_source_column"]:
        raise AssertionError("stage A did not change winning source column")
    if predict(grid, "toggle_then_relay") == predict(grid, "toggle_only"):
        raise AssertionError("stage B had no observable effect")
    for rival in HYPOTHESES:
        if rival not in MODES and predict(grid, rival) == predict(grid, "toggle_then_relay"):
            raise AssertionError(f"declared rival survived scene: {rival}")
    return grid


def sample_input(seed: int, index: int, *, split: str) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES if split == "test" else None
    if profiles is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    h, w, stress = profiles[index]
    return _scene(_derived_seed(seed, split, index), h, w, stress)


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4):
    _integer(seed, 0, 2**63 - 1, "seed")
    mode = _mode(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            source = sample_input(seed, index, split=split)
            key = json.dumps(source, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            episode[split].append({"input": source, "output": transform(source, mode)})
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
        "schema": "b38782448e7b-teaching-certificate-v1",
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
    "active_columns",
    "background",
    "completed_counts",
    "cue_column",
    "generate",
    "observe",
    "predict",
    "program",
    "public_turn",
    "relay_column",
    "sample_input",
    "teaching_certificate",
    "toggle_only",
    "transform",
]
