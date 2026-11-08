"""Odd-tile row extraction and a sequential difference-ranked stack variant."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random

BASE = Path(__file__).resolve().parent
SETTINGS = ("source_rows", "difference_desc")
RIVALS = (
    "source_rows",
    "difference_desc",
    "difference_asc",
    "foreground_desc",
    "foreground_asc",
    "reverse_rows",
    "unique_column_asc",
    "majority_tiles",
    "first_tiles",
    "last_tiles",
)

DEMO_PROFILES = (
    (3, 3, 5, 5, 1),
    (3, 4, 5, 5, 1),
    (4, 3, 4, 5, 1),
    (4, 4, 4, 4, 1),
    (5, 3, 4, 5, 1),
    (5, 4, 4, 4, 1),
)
QUERY_PROFILES = (
    (4, 4, 5, 5, 1),
    (4, 3, 6, 5, 1),
    (3, 5, 6, 4, 1),
    (4, 4, 5, 5, 2),
)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")


def _runs(indices):
    if not indices:
        return []
    result = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value != previous + 1:
            result.append((start, previous))
            start = value
        previous = value
    result.append((start, previous))
    return result


def _gaps(runs):
    return [
        (left[1] + 1, right[0] - 1)
        for left, right in zip(runs, runs[1:])
        if left[1] + 1 <= right[0] - 1
    ]


def _tile(grid, row_interval, col_interval):
    r0, r1 = row_interval
    c0, c1 = col_interval
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _key(tile):
    return tuple(tuple(row) for row in tile)


def analyze(grid):
    """Parse separator lattice and identify the sole non-repeated tile per row."""
    validate_grid(grid)
    height, width = len(grid), len(grid[0])
    separator = grid[0][0]
    row_runs = _runs(
        [r for r in range(height) if all(grid[r][c] == separator for c in range(width))]
    )
    col_runs = _runs(
        [c for c in range(width) if all(grid[r][c] == separator for r in range(height))]
    )
    if (
        len(row_runs) < 3
        or len(col_runs) < 4
        or row_runs[0][0] != 0
        or row_runs[-1][1] != height - 1
        or col_runs[0][0] != 0
        or col_runs[-1][1] != width - 1
    ):
        raise ValueError("need outer separator frame and at least two tile rows by three columns")
    row_intervals, col_intervals = _gaps(row_runs), _gaps(col_runs)
    if len(row_intervals) != len(row_runs) - 1 or len(col_intervals) != len(col_runs) - 1:
        raise ValueError("separator runs must alternate with nonempty tile bands")
    row_heights = {r1 - r0 + 1 for r0, r1 in row_intervals}
    col_widths = {c1 - c0 + 1 for c0, c1 in col_intervals}
    if len(row_heights) != 1 or len(col_widths) != 1:
        raise ValueError("all tile bands must have a common shape")
    tile_height, tile_width = next(iter(row_heights)), next(iter(col_widths))
    if tile_height < 2 or tile_width < 2:
        raise ValueError("tiles must be at least 2x2")

    records = []
    for row_index, row_interval in enumerate(row_intervals):
        tiles = [_tile(grid, row_interval, interval) for interval in col_intervals]
        keys = [_key(tile) for tile in tiles]
        counts = Counter(keys)
        unique_keys = [key for key, count in counts.items() if count == 1]
        repeated_keys = [key for key, count in counts.items() if count == len(tiles) - 1]
        if len(counts) != 2 or len(unique_keys) != 1 or len(repeated_keys) != 1:
            raise ValueError("each tile row must contain one outlier and otherwise identical tiles")
        unique_key, repeated_key = unique_keys[0], repeated_keys[0]
        unique_column = keys.index(unique_key)
        difference_count = sum(
            a != b
            for row_a, row_b in zip(unique_key, repeated_key)
            for a, b in zip(row_a, row_b)
        )
        if difference_count <= 0:
            raise ValueError("outlier must differ from repeated tile")
        repeated_frequency = Counter(value for row in repeated_key for value in row)
        maximum = max(repeated_frequency.values())
        backgrounds = sorted(
            color for color, count in repeated_frequency.items() if count == maximum
        )
        if len(backgrounds) != 1:
            raise ValueError("repeated tile background must be uniquely modal")
        background = backgrounds[0]
        foreground_count = sum(value != background for row in unique_key for value in row)
        records.append(
            {
                "row_index": row_index,
                "unique_column": unique_column,
                "unique": [list(row) for row in unique_key],
                "repeated": [list(row) for row in repeated_key],
                "difference_count": difference_count,
                "foreground_count": foreground_count,
                "background": background,
                "tiles": tiles,
            }
        )
    return {
        "separator": separator,
        "row_runs": row_runs,
        "col_runs": col_runs,
        "row_intervals": row_intervals,
        "col_intervals": col_intervals,
        "tile_height": tile_height,
        "tile_width": tile_width,
        "left_separator_width": col_runs[0][1] - col_runs[0][0] + 1,
        "right_separator_width": col_runs[-1][1] - col_runs[-1][0] + 1,
        "rows": records,
        "height": height,
        "width": width,
    }


def _ordered(records, policy):
    records = list(records)
    if policy in ("source_rows", "majority_tiles", "first_tiles", "last_tiles"):
        return records
    if policy == "difference_desc":
        return sorted(records, key=lambda row: (-row["difference_count"], row["row_index"]))
    if policy == "difference_asc":
        return sorted(records, key=lambda row: (row["difference_count"], row["row_index"]))
    if policy == "foreground_desc":
        return sorted(records, key=lambda row: (-row["foreground_count"], row["row_index"]))
    if policy == "foreground_asc":
        return sorted(records, key=lambda row: (row["foreground_count"], row["row_index"]))
    if policy == "reverse_rows":
        return list(reversed(records))
    if policy == "unique_column_asc":
        return sorted(records, key=lambda row: (row["unique_column"], row["row_index"]))
    raise ValueError("unknown stack policy or rival")


def render(grid, policy="source_rows"):
    if type(policy) is not str or policy not in RIVALS:
        raise ValueError("unknown stack policy or rival")
    info = analyze(grid)
    records = _ordered(info["rows"], policy)
    output_width = (
        info["left_separator_width"] + info["tile_width"] + info["right_separator_width"]
    )
    out = [[info["separator"]] * output_width for _ in range(info["height"])]
    left = info["left_separator_width"]
    for destination_index, row_interval in enumerate(info["row_intervals"]):
        record = records[destination_index]
        if policy == "majority_tiles":
            chosen = record["repeated"]
        elif policy == "first_tiles":
            chosen = record["tiles"][0]
        elif policy == "last_tiles":
            chosen = record["tiles"][-1]
        else:
            chosen = record["unique"]
        r0, r1 = row_interval
        for dr, source_row in enumerate(chosen):
            out[r0 + dr][left : left + info["tile_width"]] = source_row[:]
    return out


def solve(grid, stack_order="source_rows"):
    if stack_order not in SETTINGS:
        raise ValueError("stack_order must be source_rows or difference_desc")
    return render(grid, stack_order)


def harmful_survivors(episode, selected):
    survivors = []
    for rival in RIVALS:
        if rival == selected:
            continue
        if all(render(pair["input"], rival) == pair["output"] for pair in episode["train"]):
            if any(render(pair["input"], rival) != pair["output"] for pair in episode["test"]):
                survivors.append(rival)
    return survivors


def _rng(seed, index):
    raw = hashlib.sha256(f"38007db0-row-outlier-v1:{seed}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _rank_order(values, reverse=True):
    return tuple(sorted(range(len(values)), key=lambda i: ((-values[i]) if reverse else values[i], i)))


def make_scene(seed, index, profile):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    rows_count, cols_count, tile_height, tile_width, separator_width = profile
    for value, low, high, name in (
        (rows_count, 2, 5, "rows_count"),
        (cols_count, 3, 5, "cols_count"),
        (tile_height, 3, 6, "tile_height"),
        (tile_width, 3, 6, "tile_width"),
        (separator_width, 1, 2, "separator_width"),
    ):
        integer(value, low, high, name)
    height = rows_count * tile_height + (rows_count + 1) * separator_width
    width = cols_count * tile_width + (cols_count + 1) * separator_width
    if height > 30 or width > 30:
        raise ValueError("profile exceeds ARC limits")
    rng = _rng(seed, index)
    separator, background, ink = rng.sample(range(10), 3)
    area = tile_height * tile_width
    foreground_limit = max(3, area // 2 - 1)

    # Choose distinct deltas and unique-foreground counts with deliberately
    # different rankings; alternate whether the outlier adds or removes ink.
    for _ in range(10000):
        deltas = list(range(1, rows_count + 1))
        rng.shuffle(deltas)
        if _rank_order(deltas) in (tuple(range(rows_count)), tuple(reversed(range(rows_count)))):
            continue
        foregrounds = rng.sample(range(2, foreground_limit + 1), rows_count)
        directions = [1 if (row + index) % 2 == 0 else -1 for row in range(rows_count)]
        valid = True
        repeated_counts = []
        for fg, delta, direction in zip(foregrounds, deltas, directions):
            repeated = fg - delta if direction == 1 else fg + delta
            if not 1 <= repeated <= foreground_limit:
                valid = False
                break
            repeated_counts.append(repeated)
        if not valid:
            continue
        difference_order = _rank_order(deltas)
        foreground_desc_order = _rank_order(foregrounds)
        foreground_asc_order = tuple(
            sorted(range(rows_count), key=lambda row: (foregrounds[row], row))
        )
        if difference_order in (foreground_desc_order, foreground_asc_order):
            continue
        if foreground_desc_order in (
            tuple(range(rows_count)),
            tuple(reversed(range(rows_count))),
        ):
            continue
        break
    else:
        raise RuntimeError("unable to construct independent difference/foreground rankings")

    positions = [(r, c) for r in range(tile_height) for c in range(tile_width)]
    difference_order = _rank_order(deltas)
    for _ in range(1000):
        unique_columns = list(range(cols_count))
        rng.shuffle(unique_columns)
        while len(unique_columns) < rows_count:
            extra = list(range(cols_count))
            rng.shuffle(extra)
            unique_columns.extend(extra)
        unique_columns = unique_columns[:rows_count]
        column_order = tuple(
            sorted(range(rows_count), key=lambda row: (unique_columns[row], row))
        )
        if column_order not in (tuple(range(rows_count)), difference_order):
            break
    else:
        raise RuntimeError("unable to separate source, difference, and column rankings")

    row_tiles = []
    seen = set()
    seen_unique = set()
    for row_index in range(rows_count):
        delta = deltas[row_index]
        unique_fg = foregrounds[row_index]
        direction = directions[row_index]
        for _ in range(1000):
            unique_mask = set(rng.sample(positions, unique_fg))
            if direction == 1:
                changed = set(rng.sample(sorted(unique_mask), delta))
                repeated_mask = unique_mask - changed
            else:
                zeros = sorted(set(positions) - unique_mask)
                changed = set(rng.sample(zeros, delta))
                repeated_mask = unique_mask | changed
            unique_key = tuple(sorted(unique_mask))
            key = (unique_key, tuple(sorted(repeated_mask)))
            if key not in seen and unique_key not in seen_unique:
                seen.add(key)
                seen_unique.add(unique_key)
                break
        else:
            raise RuntimeError("tile mask construction exhausted")
        unique_tile = [
            [ink if (r, c) in unique_mask else background for c in range(tile_width)]
            for r in range(tile_height)
        ]
        repeated_tile = [
            [ink if (r, c) in repeated_mask else background for c in range(tile_width)]
            for r in range(tile_height)
        ]
        tiles = [copy.deepcopy(repeated_tile) for _ in range(cols_count)]
        tiles[unique_columns[row_index]] = unique_tile
        row_tiles.append(tiles)

    grid = [[separator] * width for _ in range(height)]
    for tile_row, tiles in enumerate(row_tiles):
        r0 = separator_width + tile_row * (tile_height + separator_width)
        for tile_col, tile in enumerate(tiles):
            c0 = separator_width + tile_col * (tile_width + separator_width)
            for dr, row in enumerate(tile):
                grid[r0 + dr][c0 : c0 + tile_width] = row

    info = analyze(grid)
    observed_deltas = [row["difference_count"] for row in info["rows"]]
    observed_foregrounds = [row["foreground_count"] for row in info["rows"]]
    if observed_deltas != deltas or observed_foregrounds != foregrounds:
        raise RuntimeError("constructed intermediate differs from parser")
    if render(grid, "source_rows") == render(grid, "difference_desc"):
        raise RuntimeError("setting contrast absent")
    if render(grid, "difference_desc") == render(grid, "foreground_desc"):
        raise RuntimeError("causal counterfactual contrast absent")
    return grid


def sample_input(seed, index, profile):
    return make_scene(seed, index, profile)


def program(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"stack_order"}
        or type(settings["stack_order"]) is not str
        or settings["stack_order"] not in SETTINGS
    ):
        raise ValueError("settings must be exactly stack_order=source_rows|difference_desc")
    filename = "canonical.rkt" if settings["stack_order"] == "source_rows" else "difference_desc.rkt"
    return (BASE / filename).read_text()


def generate(seed, settings, demos=2, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    selected = program(settings)
    mode = settings["stack_order"]

    def pair(index, profile):
        grid = sample_input(seed, index, profile)
        return {"input": grid, "output": solve(grid, mode)}

    train = [pair(index, DEMO_PROFILES[index]) for index in range(demos)]
    bank = [pair(100 + index, profile) for index, profile in enumerate(QUERY_PROFILES)]
    return {
        "train": train,
        "test": copy.deepcopy(bank[:queries]),
        "private_query_bank": bank,
        "program_solution": selected,
        "settings": copy.deepcopy(settings),
    }
