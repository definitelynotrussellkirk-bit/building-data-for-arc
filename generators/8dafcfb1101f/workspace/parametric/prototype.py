"""Signed anchor-vector parametric episodes for 8dafcfb1101f.

The hidden setting chooses which marker-to-marker direction supplies the signed
translation vector.  Input sampling is setting-neutral and keeps both directions
lawful, so only executed labels reveal the episode rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "8dafcfb1101f"
SCHEMA = "arcpuzzles-signed-anchor-translation-v1"
HOME = Path(__file__).resolve().parent
DIRECTIONS = ("src_to_dst", "dst_to_src")
DEFAULT = {"vector_direction": "src_to_dst"}
SETTING_OBJECTS = tuple({"vector_direction": value} for value in DIRECTIONS)
MIN_DEMOS = 3
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1

# height, width, signed source->destination vector, content profile
TRAIN_PROFILES = (
    (9, 11, 2, 3, "sparse"),
    (12, 13, -3, 2, "balanced"),
    (14, 16, 3, -4, "balanced"),
    (17, 18, -4, -3, "dense"),
    (21, 23, 5, 4, "dense"),
    (25, 27, -5, 5, "dense"),
)
QUERY_PROFILES = (
    (8, 10, 1, -2, "sparse"),
    (16, 18, -3, 4, "balanced"),
    (24, 27, 5, -6, "dense"),
    (30, 30, -6, -5, "stress"),
)
PAYLOAD_COLORS = (3, 4, 5, 6, 7, 8, 9)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def settings_value(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"vector_direction"}:
        raise ValueError("settings must contain exactly vector_direction")
    value = settings["vector_direction"]
    if type(value) is not str or value not in DIRECTIONS:
        raise ValueError(f"vector_direction must be one of {DIRECTIONS!r}")
    return value


def program(settings: dict[str, str]) -> str:
    direction = settings_value(settings)
    filename = "canonical.rkt" if direction == "src_to_dst" else "reverse.rkt"
    return (HOME / filename).read_text(encoding="utf-8")


def strict_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != w
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors 0..9")
    return h, w


def marker_vector(grid: list[list[int]]) -> tuple[tuple[int, int], tuple[int, int], int, int]:
    strict_grid(grid)
    src = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    dst = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(src) != 1 or len(dst) != 1:
        raise ValueError("input requires exactly one color-1 source and one color-2 destination")
    dr, dc = dst[0][0] - src[0][0], dst[0][1] - src[0][1]
    if dr == 0 or dc == 0:
        raise ValueError("parametric grammar requires both vector components nonzero")
    return src[0], dst[0], dr, dc


def _translate(grid: list[list[int]], dr: int, dc: int, *, include_markers: bool = False) -> list[list[int]]:
    h, w = strict_grid(grid)
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            movable = value != 0 if include_markers else value not in (0, 1, 2)
            rr, cc = r + dr, c + dc
            if movable and 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def apply_rule(grid: list[list[int]], settings: dict[str, str]) -> list[list[int]]:
    direction = settings_value(settings)
    _, _, dr, dc = marker_vector(grid)
    if direction == "dst_to_src":
        dr, dc = -dr, -dc
    return _translate(grid, dr, dc)


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, SCHEMA, seed, split, index], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:16], "big"))


def _marker_positions(h: int, w: int, dr: int, dc: int, rng: random.Random, index: int) -> tuple[tuple[int, int], tuple[int, int]]:
    rlo, rhi = max(0, -dr), min(h - 1, h - 1 - dr)
    clo, chi = max(0, -dc), min(w - 1, w - 1 - dc)
    candidates = [
        (rlo, clo), (rlo, chi), (rhi, clo), (rhi, chi),
        ((rlo + rhi) // 2, clo), (rhi, (clo + chi) // 2),
        ((rlo + rhi) // 2, chi), (rlo, (clo + chi) // 2),
    ]
    start = (index + rng.randrange(len(candidates))) % len(candidates)
    src = candidates[start]
    dst = (src[0] + dr, src[1] + dc)
    return src, dst


def _safe_payload_cells(h: int, w: int, dr: int, dc: int) -> list[tuple[int, int]]:
    ar, ac = abs(dr), abs(dc)
    return [(r, c) for r in range(ar, h - ar) for c in range(ac, w - ac)]


def _target_count(profile: str, area: int) -> int:
    if profile == "sparse":
        return max(8, min(area, area // 7))
    if profile == "balanced":
        return max(18, min(area, area // 4))
    if profile == "dense":
        return max(32, min(area, area // 3))
    if profile == "stress":
        return min(area, max(90, area // 3))
    raise ValueError(f"unknown profile {profile!r}")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    if split not in {"train", "test"} or not 0 <= index < len(profiles):
        raise ValueError("invalid split/index")
    h, w, dr, dc, profile = profiles[index]
    rng = _rng(seed, split, index)
    src, dst = _marker_positions(h, w, dr, dc, rng, index)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[src[0]][src[1]] = 1
    grid[dst[0]][dst[1]] = 2

    safe = _safe_payload_cells(h, w, dr, dc)
    forbidden = {src, dst}
    available = [cell for cell in safe if cell not in forbidden]
    if len(available) < 8:
        raise RuntimeError("profile has insufficient bidirectionally safe payload cells")

    # Pin boundary witnesses first.  For either direction, one of each opposite
    # safe-region edges lands on the actual grid boundary.
    ar, ac = abs(dr), abs(dc)
    edge_candidates = [
        (ar, c) for c in range(ac, w - ac)
    ] + [
        (h - ar - 1, c) for c in range(ac, w - ac)
    ] + [
        (r, ac) for r in range(ar, h - ar)
    ] + [
        (r, w - ac - 1) for r in range(ar, h - ar)
    ]
    chosen: list[tuple[int, int]] = []
    for cell in edge_candidates:
        if cell not in forbidden and cell not in chosen:
            chosen.append(cell)
        if len(chosen) == 8:
            break

    remaining = [cell for cell in available if cell not in chosen]
    rng.shuffle(remaining)
    target = min(len(available), _target_count(profile, len(available)))
    chosen.extend(remaining[: max(0, target - len(chosen))])
    colors = list(PAYLOAD_COLORS)
    rng.shuffle(colors)
    for ordinal, (r, c) in enumerate(chosen):
        # A deterministic multicolor texture with local runs and scattered cells.
        color = colors[(ordinal + r + 2 * c) % len(colors)]
        grid[r][c] = color

    marker_vector(grid)
    # Both settings must be total over every admitted input.
    for settings in SETTING_OBJECTS:
        output = apply_rule(grid, settings)
        if sum(value != 0 for row in output for value in row) != len(chosen):
            raise RuntimeError("payload was not preserved under both direction settings")
    return grid


def _candidate_output(grid: list[list[int]], name: str) -> list[list[int]]:
    _, _, dr, dc = marker_vector(grid)
    if name == "identity_payload":
        return _translate(grid, 0, 0)
    if name == "absolute_vector":
        return _translate(grid, abs(dr), abs(dc))
    if name == "row_only":
        return _translate(grid, dr, 0)
    if name == "column_only":
        return _translate(grid, 0, dc)
    if name == "swapped_components":
        return _translate(grid, dc, dr)
    if name == "fixed_down_right":
        return _translate(grid, 2, 2)
    if name == "move_markers_too":
        return _translate(grid, dr, dc, include_markers=True)
    raise KeyError(name)


SHORTCUTS = (
    "identity_payload",
    "absolute_vector",
    "row_only",
    "column_only",
    "swapped_components",
    "fixed_down_right",
    "move_markers_too",
)


def certify(train: list[dict[str, Any]], settings: dict[str, str]) -> dict[str, Any]:
    selected = {"vector_direction": settings_value(settings)}
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pairs require exactly input/output")
        marker_vector(pair["input"])
        strict_grid(pair["output"])

    survivors = [
        candidate
        for candidate in SETTING_OBJECTS
        if all(apply_rule(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    shortcut_survivors = [
        name
        for name in SHORTCUTS
        if all(_candidate_output(pair["input"], name) == pair["output"] for pair in train)
    ]
    if survivors != [selected] or shortcut_survivors:
        raise ValueError(
            f"demonstrations do not identify {selected}; "
            f"settings={survivors}, shortcuts={shortcut_survivors}"
        )
    return {
        "fit_scope": "demonstrations_only",
        "survivors": survivors,
        "declared_shortcuts": list(SHORTCUTS),
        "shortcut_survivors": shortcut_survivors,
    }


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    normalized = {"vector_direction": settings_value(settings)}

    train = []
    for index in range(demos):
        grid = sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, normalized)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, normalized)})

    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in [*train, *test]]
    if len(encoded) != len(set(encoded)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    certificate = certify(train, normalized)
    return {
        "train": train,
        "test": test,
        "program_solution": program(normalized),
        "settings": normalized,
        "certificate": certificate,
    }
