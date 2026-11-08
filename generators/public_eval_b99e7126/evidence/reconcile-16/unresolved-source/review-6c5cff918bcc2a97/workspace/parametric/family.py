"""Tile-blueprint completion family for public ARC task b99e7126."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import json
import random
from typing import Iterable

GENERATOR_ID = TASK_ID = "public_eval_b99e7126"
RULE_TASK_ID = 'ee_b99e7126'
VERSION = "1.0.0"
SUMMARY = "Complete a macro-scale pattern from the novel-color mask inside repeated anomalous tiles."
INVARIANTS = [
    "one full-line separator color partitions a square tile lattice",
    "exactly one frequent normal tile and one rarer anomalous tile",
    "the anomalous tile introduces one novel blueprint color",
    "observed anomalous tiles uniquely locate the blueprint",
]
AXES = {}
MODES = ("identity", "rotate_cw", "no_completion", "bounding_box")


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: object) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return value


def _grid(value: object) -> list[list[int]]:
    if type(value) is not list or not 5 <= len(value) <= 30:
        raise ValueError("grid height must be an exact list in 5..30")
    if type(value[0]) is not list or not 5 <= len(value[0]) <= 30:
        raise ValueError("grid width must be in 5..30")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width for row in value):
        raise ValueError("rectangular exact list rows required")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("exact integer ARC colors 0..9 required")
    return [row[:] for row in value]


def rotate_cw(mask: list[list[bool]]) -> list[list[bool]]:
    return [list(row) for row in zip(*mask[::-1], strict=True)]


def rotate_180(mask: list[list[bool]]) -> list[list[bool]]:
    return [row[::-1] for row in mask[::-1]]


def _serialize(tile: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in tile)


def _separator_analysis(grid: list[list[int]]) -> tuple[int, list[int], list[int], int]:
    height, width = len(grid), len(grid[0])
    colors = sorted({cell for row in grid for cell in row})
    candidates = []
    for color in colors:
        rows = [r for r in range(height) if all(grid[r][c] == color for c in range(width))]
        columns = [c for c in range(width) if all(grid[r][c] == color for r in range(height))]
        if len(rows) < 3 or len(columns) < 3:
            continue
        if rows[0] != 0 or rows[-1] != height - 1 or columns[0] != 0 or columns[-1] != width - 1:
            continue
        row_steps = {b - a for a, b in zip(rows, rows[1:])}
        column_steps = {b - a for a, b in zip(columns, columns[1:])}
        if len(row_steps) == len(column_steps) == 1 and row_steps == column_steps:
            step = next(iter(row_steps))
            if 3 <= step <= 6:
                candidates.append((color, rows, columns, step - 1))
    if len(candidates) != 1:
        raise ValueError(f"expected one regular separator lattice, found {len(candidates)}")
    return candidates[0]


def _tiles(grid: list[list[int]], rows: list[int], columns: list[int]) -> list[list[tuple[tuple[int, ...], ...]]]:
    return [
        [
            _serialize([line[columns[j] + 1:columns[j + 1]] for line in grid[rows[i] + 1:rows[i + 1]]])
            for j in range(len(columns) - 1)
        ]
        for i in range(len(rows) - 1)
    ]


def _mask_for_mode(mask: list[list[bool]], mode: str) -> list[list[bool]]:
    if mode in ("identity", "no_completion", "bounding_box"):
        return [row[:] for row in mask]
    if mode == "rotate_cw":
        return rotate_cw(mask)
    raise AssertionError(mode)


def _target_set(mask: list[list[bool]], top: int, left: int, mode: str,
                observed: set[tuple[int, int]]) -> set[tuple[int, int]]:
    if mode == "no_completion":
        return set(observed)
    if mode == "bounding_box":
        points = [(r, c) for r, row in enumerate(mask) for c, value in enumerate(row) if value]
        rows = [r for r, _c in points]
        columns = [c for _r, c in points]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(columns), max(columns)
        return {(top + r, left + c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    return {(top + r, left + c) for r, row in enumerate(mask) for c, value in enumerate(row) if value}


def _placements(mask: list[list[bool]], observed: set[tuple[int, int]], lattice_rows: int,
                lattice_columns: int) -> list[tuple[int, int, set[tuple[int, int]]]]:
    height, width = len(mask), len(mask[0])
    found = []
    for top in range(lattice_rows - height + 1):
        for left in range(lattice_columns - width + 1):
            target = {(top + r, left + c) for r, row in enumerate(mask) for c, value in enumerate(row) if value}
            if observed <= target:
                found.append((top, left, target))
    return found


def analyze(grid: object, mode: str = "identity") -> dict[str, object]:
    selected_mode = _mode(mode)
    copied = _grid(grid)
    separator, row_lines, column_lines, tile_size = _separator_analysis(copied)
    tile_matrix = _tiles(copied, row_lines, column_lines)
    flat = [tile for row in tile_matrix for tile in row]
    counts = Counter(flat)
    if len(counts) != 2:
        raise ValueError("exactly two tile motifs required")
    normal, anomaly = [tile for tile, _count in counts.most_common()]
    if counts[normal] <= counts[anomaly]:
        raise ValueError("normal tile must be strictly more frequent")
    normal_colors = {cell for row in normal for cell in row}
    novel_colors = {cell for row in anomaly for cell in row} - normal_colors
    if len(novel_colors) != 1:
        raise ValueError("anomalous tile must introduce exactly one novel color")
    novel = next(iter(novel_colors))
    base_mask = [[cell == novel for cell in row] for row in anomaly]
    if not 2 <= sum(value for row in base_mask for value in row) < tile_size * tile_size:
        raise ValueError("blueprint mask must be nontrivial")
    observed = {(r, c) for r, row in enumerate(tile_matrix) for c, tile in enumerate(row) if tile == anomaly}
    if not observed:
        raise ValueError("at least one anomalous tile required")
    posed_mask = _mask_for_mode(base_mask, selected_mode)
    placements = _placements(posed_mask, observed, len(tile_matrix), len(tile_matrix[0]))
    if len(placements) != 1:
        raise ValueError(f"observed anomalies must identify one placement, found {len(placements)}")
    top, left, _full = placements[0]
    target = _target_set(posed_mask, top, left, selected_mode, observed)

    output = [row[:] for row in copied]
    anomaly_rows = [list(row) for row in anomaly]
    for macro_row, macro_column in target:
        r0, c0 = row_lines[macro_row] + 1, column_lines[macro_column] + 1
        for r in range(tile_size):
            for c in range(tile_size):
                output[r0 + r][c0 + c] = anomaly_rows[r][c]
    return {
        "height": len(copied), "width": len(copied[0]), "separator": separator,
        "row_lines": row_lines, "column_lines": column_lines, "tile_size": tile_size,
        "normal": [list(row) for row in normal], "anomaly": anomaly_rows, "novel": novel,
        "base_mask": base_mask, "posed_mask": posed_mask, "observed": sorted(observed),
        "placement": [top, left], "target": sorted(target), "mode": selected_mode,
        "output": output,
    }


def solve(grid: object, mode: str = "identity") -> list[list[int]]:
    return analyze(grid, mode)["output"]


def self_check(grid: object) -> list[str]:
    try:
        identity = analyze(grid, "identity")
        rotated = analyze(grid, "rotate_cw")
        if identity["output"] == rotated["output"]:
            return ["identity and rotate_cw must differ on admitted generated inputs"]
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"b99e7126/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _mask_search(rng: random.Random, tile_size: int, lattice: int) -> tuple[list[list[bool]], set[tuple[int, int]], int, int]:
    for _attempt in range(5000):
        mask = [[rng.random() < 0.56 for _ in range(tile_size)] for _ in range(tile_size)]
        count = sum(value for row in mask for value in row)
        if not 4 <= count <= tile_size * tile_size - 2:
            continue
        rotated = rotate_cw(mask)
        if rotated == mask:
            continue
        top = rng.randrange(lattice - tile_size + 1)
        left = rng.randrange(lattice - tile_size + 1)
        identity = {(top + r, left + c) for r, row in enumerate(mask) for c, value in enumerate(row) if value}
        turned = {(top + r, left + c) for r, row in enumerate(rotated) for c, value in enumerate(row) if value}
        intersection = sorted(identity & turned)
        if len(intersection) < 2:
            continue
        sizes = list(range(min(5, len(intersection)), 1, -1))
        rng.shuffle(sizes)
        for size in sizes:
            combos = list(itertools.combinations(intersection, size))
            rng.shuffle(combos)
            for combo in combos[:80]:
                observed = set(combo)
                p0 = _placements(mask, observed, lattice, lattice)
                p1 = _placements(rotated, observed, lattice, lattice)
                if (len(p0) == len(p1) == 1 and p0[0][:2] == (top, left)
                        and p1[0][:2] == (top, left) and p0[0][2] != p1[0][2]
                        and len(observed) < min(len(p0[0][2]), len(p1[0][2]))):
                    return mask, observed, top, left
    raise ValueError("matched blueprint search exhausted")


def _normal_tile(rng: random.Random, size: int, first: int, second: int,
                 mask: list[list[bool]]) -> list[list[int]]:
    phase = rng.randrange(7)
    tile = [[first if (3 * r + 5 * c + phase) % 4 else second for c in range(size)] for r in range(size)]
    exposed = [(r, c) for r in range(size) for c in range(size) if not mask[r][c]]
    if len(exposed) < 2:
        raise ValueError("blueprint must leave two normal-motif cells exposed")
    rng.shuffle(exposed)
    tile[exposed[0][0]][exposed[0][1]] = first
    tile[exposed[1][0]][exposed[1][1]] = second
    return tile


def _build_case(seed: int, profile: int) -> list[list[int]]:
    rng = _rng(seed, f"profile-{profile}")
    if profile % 10 == 9:
        tile_size, lattice = 3, 7
    elif profile % 5 in (3, 4):
        tile_size, lattice = 4, 5
    else:
        tile_size = 3
        lattice = 5 + rng.randrange(3)
    mask, observed, _top, _left = _mask_search(rng, tile_size, lattice)
    separator, first, second, novel = rng.sample(range(10), 4)
    normal = _normal_tile(rng, tile_size, first, second, mask)
    anomaly = [row[:] for row in normal]
    for r in range(tile_size):
        for c in range(tile_size):
            if mask[r][c]:
                anomaly[r][c] = novel
    extent = lattice * (tile_size + 1) + 1
    grid = [[separator] * extent for _ in range(extent)]
    for mr in range(lattice):
        for mc in range(lattice):
            motif = anomaly if (mr, mc) in observed else normal
            r0, c0 = mr * (tile_size + 1) + 1, mc * (tile_size + 1) + 1
            for r in range(tile_size):
                grid[r0 + r][c0:c0 + tile_size] = motif[r]
    if self_check(grid):
        raise ValueError(self_check(grid)[0])
    return grid


def _coverage(inputs: Iterable[list[list[int]]]) -> bool:
    grids = list(inputs)
    for correct in ("identity", "rotate_cw"):
        wanted = [solve(grid, correct) for grid in grids]
        for rival in MODES:
            if rival == correct:
                continue
            if [solve(grid, rival) for grid in grids] == wanted:
                return False
    return True


@lru_cache(maxsize=64)
def _lesson_bank(seed: int) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], tuple[tuple[tuple[int, ...], ...], ...], tuple[int, ...]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    candidates: list[list[list[int]]] = []
    seen = set()
    for index in range(40):
        grid = _build_case(seed + 1000003 * index, index)
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            candidates.append(grid)
        if len(candidates) >= 24:
            break
    if len(candidates) < 10:
        raise ValueError("insufficient distinct lesson candidates")

    selected_pair = None
    for first, second in itertools.combinations(range(min(14, len(candidates))), 2):
        if _coverage((candidates[first], candidates[second])):
            selected_pair = (first, second)
            break
    if selected_pair is None:
        raise ValueError("two-demonstration rival coverage exhausted")

    rng = _rng(seed, "presentation")
    remaining = [index for index in range(len(candidates)) if index not in selected_pair]
    rng.shuffle(remaining)
    train_indices = list(selected_pair) + remaining[:4]
    unused = [index for index in remaining[4:]]
    stress = next((index for index in unused if len(candidates[index]) == 29), None)
    if stress is None:
        raise ValueError("stress query missing")
    query_indices = [stress]
    query_indices.extend(index for index in unused if index != stress and len(query_indices) < 4)
    rng.shuffle(query_indices)

    def freeze(items: list[list[list[int]]]):
        return tuple(tuple(tuple(row) for row in grid) for grid in items)

    return freeze([candidates[index] for index in train_indices]), freeze([candidates[index] for index in query_indices]), tuple(query_indices)


def lesson_inputs(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    train, test, _order = _lesson_bank(seed)
    thaw = lambda bank: [[list(row) for row in grid] for grid in bank]
    return thaw(train), thaw(test)


def lesson_metadata(seed: int) -> dict[str, object]:
    train, test, order = _lesson_bank(seed)
    return {
        "query_permutation": list(order),
        "train_certificates": [analyze([list(row) for row in grid], "identity") for grid in train],
        "query_certificates": [analyze([list(row) for row in grid], "identity") for grid in test],
    }


def generate(seed: int = 0, sample_index: int = 0, difficulty: str = "medium", **kwargs) -> list[list[int]]:
    if kwargs:
        raise ValueError(f"unsupported arguments: {sorted(kwargs)}")
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**31 - 1, "sample_index")
    if type(difficulty) is not str or difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    profile = sample_index % 10
    if difficulty == "hard":
        profile = 9 if sample_index % 2 == 0 else 4
    elif difficulty == "easy":
        profile = sample_index % 3
    return _build_case(seed + 1000003 * sample_index, profile)
