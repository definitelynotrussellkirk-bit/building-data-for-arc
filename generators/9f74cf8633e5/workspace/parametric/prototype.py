"""Fill centers from equal diagonal neighbors or equal orthogonal neighbors.

The default setting is the exact canonical diagonal rule.  Both settings use
matched scenes containing several valid motifs of each relation and controlled
near-misses, so demonstrations teach which relation is active rather than a
fixed color, count, location, or fill-everything shortcut.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "9f74cf8633e5"
VERSION = "neighbor-mode-v1"
HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"neighbor_mode": "diagonal"},
    {"neighbor_mode": "orthogonal"},
)
MODES = tuple(setting["neighbor_mode"] for setting in SETTINGS)

DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
OFFSETS = {"diagonal": DIAGONAL, "orthogonal": ORTHOGONAL}

# (height, width, diagonal positives, orthogonal positives, negative controls)
DEMO_PROFILES = (
    (12, 12, 2, 2, 2),
    (13, 14, 3, 2, 2),
    (15, 15, 2, 3, 3),
    (17, 16, 4, 3, 3),
    (19, 18, 4, 4, 4),
    (20, 20, 5, 4, 4),
)
QUERY_PROFILES = (
    (14, 15, 3, 3, 2),
    (18, 20, 5, 4, 3),
    (24, 24, 7, 6, 4),
    (30, 30, 10, 10, 6),
)


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"neighbor_mode"}:
        raise ValueError("settings must name exactly neighbor_mode")
    mode = value["neighbor_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"neighbor_mode must be one of {MODES}")
    return {"neighbor_mode": mode}


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not value
        or len(value) > 30
        or type(value[0]) is not list
        or not value[0]
        or len(value[0]) > 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return deepcopy(value)


def program(settings: Any) -> str:
    mode = _settings(settings)["neighbor_mode"]
    filename = "canonical.rkt" if mode == "diagonal" else "orthogonal.rkt"
    return (HERE / filename).read_bytes().decode("utf-8")


def _active(grid: list[list[int]], offsets: tuple[tuple[int, int], ...]) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    found: list[tuple[int, int, int]] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            values = [grid[r + dr][c + dc] for dr, dc in offsets]
            if grid[r][c] == 0 and values[0] != 0 and all(value == values[0] for value in values):
                found.append((r, c, values[0]))
    return found


def _near_miss(grid: list[list[int]], offsets: tuple[tuple[int, int], ...]) -> int:
    h, w = len(grid), len(grid[0])
    total = 0
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            values = [grid[r + dr][c + dc] for dr, dc in offsets]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                total += 1
            elif len(nonzero) == 4 and len(set(nonzero)) > 1:
                total += 1
    return total


def analyze(grid: Any) -> dict[str, Any]:
    data = _grid(grid)
    diagonal = _active(data, DIAGONAL)
    orthogonal = _active(data, ORTHOGONAL)
    return {
        "diagonal": diagonal,
        "orthogonal": orthogonal,
        "negative_controls": _near_miss(data, DIAGONAL) + _near_miss(data, ORTHOGONAL),
    }


def transform(grid: Any, settings: Any) -> list[list[int]]:
    chosen = _settings(settings)
    data = _grid(grid)
    out = deepcopy(data)
    for r, c, color in _active(data, OFFSETS[chosen["neighbor_mode"]]):
        out[r][c] = color
    return out


def fill_every_relation(grid: Any) -> list[list[int]]:
    data = _grid(grid)
    out = deepcopy(data)
    for relation in (DIAGONAL, ORTHOGONAL):
        for r, c, color in _active(data, relation):
            out[r][c] = color
    return out


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}:{purpose}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _profile_order(seed: int, split: str) -> list[tuple[int, int, int, int, int]]:
    profiles = list(DEMO_PROFILES if split == "train" else QUERY_PROFILES)
    _rng(seed, split, 0, "profile-order").shuffle(profiles)
    return profiles


def _select_centers(h: int, w: int, count: int, rng: random.Random) -> list[tuple[int, int]]:
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for _ in range(128):
        rng.shuffle(candidates)
        chosen: list[tuple[int, int]] = []
        for center in candidates:
            if all(max(abs(center[0] - r), abs(center[1] - c)) >= 4 for r, c in chosen):
                chosen.append(center)
                if len(chosen) == count:
                    return chosen
    raise RuntimeError(f"could not place {count} separated motifs in {h}x{w}")


def _paint_offsets(
    grid: list[list[int]], center: tuple[int, int], offsets: tuple[tuple[int, int], ...], colors: list[int]
) -> None:
    r, c = center
    for (dr, dc), color in zip(offsets, colors):
        grid[r + dr][c + dc] = color


def _draw_profile(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, n_diag, n_orth, n_negative = _profile_order(seed, split)[index]
    for attempt in range(128):
        rng = _rng(seed, split, index, f"scene-{attempt}")
        centers = _select_centers(h, w, n_diag + n_orth + n_negative, rng)
        rng.shuffle(centers)
        grid = [[0] * w for _ in range(h)]
        palette = list(range(1, 10))
        rng.shuffle(palette)
        expected_diag: list[tuple[int, int, int]] = []
        expected_orth: list[tuple[int, int, int]] = []
        cursor = 0
        for relation, count, expected in (
            (DIAGONAL, n_diag, expected_diag),
            (ORTHOGONAL, n_orth, expected_orth),
        ):
            for _ in range(count):
                center = centers[cursor]
                color = palette[cursor % len(palette)]
                cursor += 1
                _paint_offsets(grid, center, relation, [color] * 4)
                expected.append((center[0], center[1], color))
        for control_index in range(n_negative):
            center = centers[cursor]
            cursor += 1
            relation = DIAGONAL if control_index % 2 == 0 else ORTHOGONAL
            first = palette[(cursor + control_index) % len(palette)]
            second = palette[(cursor + control_index + 3) % len(palette)]
            if second == first:
                second = 1 + (first % 9)
            if control_index % 4 < 2:
                colors = [first, first, first, 0]
                rng.shuffle(colors)
            else:
                colors = [first, first, second, second]
                rng.shuffle(colors)
            _paint_offsets(grid, center, relation, colors)
        observed = analyze(grid)
        if (
            observed["diagonal"] == sorted(expected_diag)
            and observed["orthogonal"] == sorted(expected_orth)
            and observed["negative_controls"] >= n_negative
        ):
            return grid
    raise RuntimeError(f"could not construct clean relation scene for {split}[{index}]")


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
        raise RuntimeError("demonstrations do not uniquely identify neighbor_mode")
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
            "dependency": "detect relation-specific center/color assignments, then paint those derived centers",
        },
    }
