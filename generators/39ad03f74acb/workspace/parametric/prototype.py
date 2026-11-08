"""All straight-segment interiors, or only interiors of the longest segment(s)."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "39ad03f74acb"
VERSION = "selection-mode-v1"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"selection_mode": "all"},
    {"selection_mode": "longest"},
)
MODES = tuple(setting["selection_mode"] for setting in SETTINGS)

# Every profile contains multiple horizontal and vertical segments, a unique
# maximum, and at least one shorter interior-bearing segment in each orientation.
DEMO_PROFILES = (
    (12, 12, (3, 5), (4, 3)),
    (13, 14, (6, 3), (5, 4)),
    (15, 14, (4, 7), (3, 6)),
    (17, 16, (8, 4, 5), (7, 3)),
    (19, 18, (9, 6), (4, 8, 3)),
    (20, 20, (10, 5, 7), (9, 4, 6)),
)
QUERY_PROFILES = (
    (14, 15, (4, 7), (3, 6)),
    (18, 20, (8, 4, 6), (9, 5)),
    (24, 24, (12, 7, 5), (10, 6, 4)),
    (30, 30, (15, 11, 7, 5), (14, 10, 8, 6)),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"selection_mode"}:
        raise ValueError("settings must name exactly selection_mode")
    mode = value["selection_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"selection_mode must be one of {MODES}")
    return {"selection_mode": mode}


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not value or len(value) > 30 or type(value[0]) is not list
            or not value[0] or len(value[0]) > 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    mode = _settings(settings)["selection_mode"]
    filename = "canonical.rkt" if mode == "all" else "longest_only.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def _segments(grid: Any) -> list[tuple[str, tuple[tuple[int, int], ...]]]:
    data = _grid(grid)
    h, w = len(data), len(data[0])
    found: list[tuple[str, tuple[tuple[int, int], ...]]] = []
    for r in range(h):
        c = 0
        while c < w:
            if data[r][c] != 1:
                c += 1
                continue
            start = c
            while c < w and data[r][c] == 1:
                c += 1
            if c - start >= 3:
                found.append(("h", tuple((r, col) for col in range(start, c))))
    for c in range(w):
        r = 0
        while r < h:
            if data[r][c] != 1:
                r += 1
                continue
            start = r
            while r < h and data[r][c] == 1:
                r += 1
            if r - start >= 3:
                found.append(("v", tuple((row, c) for row in range(start, r))))
    if not found:
        raise ValueError("input must contain at least one straight blue segment")
    covered = [cell for _, cells in found for cell in cells]
    if len(covered) != len(set(covered)):
        raise ValueError("segments must not cross or branch")
    blue = {(r, c) for r, row in enumerate(data) for c, value in enumerate(row) if value == 1}
    if blue != set(covered):
        raise ValueError("every blue cell must belong to one straight segment of length at least three")
    return found


def segment_lengths(grid: Any) -> list[int]:
    return [len(cells) for _, cells in _segments(grid)]


def longest_length(grid: Any) -> int:
    return max(segment_lengths(grid))


def transform(grid: Any, settings: Any) -> list[list[int]]:
    mode = _settings(settings)["selection_mode"]
    data = _grid(grid)
    segments = _segments(data)
    longest = max(len(cells) for _, cells in segments)
    for _, cells in segments:
        if mode == "all" or len(cells) == longest:
            for r, c in cells[1:-1]:
                data[r][c] = 2
    return data


def orientation_only(grid: Any, orientation: str) -> list[list[int]]:
    if orientation not in {"h", "v"}:
        raise ValueError("orientation must be h or v")
    data = _grid(grid)
    for current, cells in _segments(data):
        if current == orientation:
            for r, c in cells[1:-1]:
                data[r][c] = 2
    return data


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile_order(seed: int, split: str) -> list[tuple[int, int, tuple[int, ...], tuple[int, ...]]]:
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    _rng(seed, split, 0, "profile-order").shuffle(profiles)
    return profiles


def _can_place(cells: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    if cells & occupied:
        return False
    return not any(
        neighbor in occupied
        for r, c in cells
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if neighbor not in cells
    )


def _candidate_cells(h: int, w: int, orientation: str, length: int) -> list[set[tuple[int, int]]]:
    if orientation == "h":
        return [set((r, c + delta) for delta in range(length))
                for r in range(h) for c in range(w - length + 1)]
    return [set((r + delta, c) for delta in range(length))
            for r in range(h - length + 1) for c in range(w)]


def _draw_profile(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, horizontal, vertical = _profile_order(seed, split)[index]
    specs = [("h", length) for length in horizontal] + [("v", length) for length in vertical]
    rng = _rng(seed, split, index, "placement")
    # Long segments are the tightest constraints. Randomize equal-length ties.
    rng.shuffle(specs)
    specs.sort(key=lambda item: item[1], reverse=True)
    for restart in range(32):
        occupied: set[tuple[int, int]] = set()
        placed: list[set[tuple[int, int]]] = []
        local = _rng(seed, split, index, f"placement-{restart}")
        ok = True
        for orientation, length in specs:
            candidates = _candidate_cells(h, w, orientation, length)
            local.shuffle(candidates)
            chosen = next((cells for cells in candidates if _can_place(cells, occupied)), None)
            if chosen is None:
                ok = False
                break
            occupied.update(chosen)
            placed.append(chosen)
        if ok:
            grid = [[0] * w for _ in range(h)]
            for cells in placed:
                for r, c in cells:
                    grid[r][c] = 1
            lengths = segment_lengths(grid)
            if sorted(lengths) != sorted(horizontal + vertical):
                raise AssertionError("constructed segment profile changed during placement")
            return grid
    raise RuntimeError(f"could not place lawful {h}x{w} segment profile")


def _pair(grid: list[list[int]], settings: dict[str, str]) -> dict[str, Any]:
    return {"input": deepcopy(grid), "output": transform(grid, settings)}


def fit_settings(demos: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    pairs = list(demos)
    survivors = []
    for candidate in SETTINGS:
        try:
            if pairs and all(
                type(pair) is dict and pair.get("output") == transform(pair.get("input"), candidate)
                for pair in pairs
            ):
                survivors.append(dict(candidate))
        except (TypeError, ValueError):
            continue
    return survivors


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    chosen = _settings(settings)
    train = [_pair(_draw_profile(seed, "train", index), chosen) for index in range(demos)]
    test = [_pair(_draw_profile(seed, "test", index), chosen) for index in range(queries)]
    if fit_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not uniquely identify selection_mode")
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(serial) != len(set(serial)):
        raise RuntimeError("episode contains duplicate inputs")
    return {
        "train": train,
        "test": test,
        "settings": chosen,
        "seed": seed,
        "program_solution": program(chosen),
        "certificate": {
            "finite_rivals": [dict(setting) for setting in SETTINGS],
            "survivors": fit_settings(train),
            "racket_checked": False,
            "dependency": "compute maximum segment length, then select interiors with that length",
        },
    }
