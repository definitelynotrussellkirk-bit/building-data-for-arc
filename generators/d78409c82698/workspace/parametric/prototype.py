"""Connectivity-parametric episodes for d78409c82698.

The hidden setting selects whether red-component isolation is evaluated with
4-neighbor or 8-neighbor connectivity.  Inputs are sampled independently of
that setting and deliberately contain isolated red cells, diagonal-only red
groups, cardinal red components, and inert non-red distractors.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "d78409c82698"
SCHEMA = "arcpuzzles-red-connectivity-v1"
HOME = Path(__file__).resolve().parent
CONNECTIVITIES = (4, 8)
DEFAULT = {"connectivity": 4}
SETTING_OBJECTS = tuple({"connectivity": value} for value in CONNECTIVITIES)
MIN_DEMOS = 3
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
EIGHT = CARDINAL + DIAGONAL
DISTRACTOR_COLORS = (1, 4, 5, 6, 7, 8, 9)

# height, width, density profile
TRAIN_PROFILES = (
    (9, 10, "sparse"),
    (12, 13, "balanced"),
    (15, 16, "balanced"),
    (18, 19, "dense"),
    (22, 24, "dense"),
    (26, 27, "dense"),
)
QUERY_PROFILES = (
    (8, 9, "sparse"),
    (14, 16, "balanced"),
    (23, 25, "dense"),
    (30, 30, "stress"),
)

# Local red-cell motifs.  Every motif is connected under 8-neighbor
# connectivity.  The diagonal motifs have no cardinal edge internally.
MOTIFS = {
    "isolated": ((0, 0),),
    "diag_pair": ((0, 0), (1, 1)),
    "diag_chain": ((0, 0), (1, 1), (2, 2)),
    "h_pair": ((0, 0), (0, 1)),
    "v_three": ((0, 0), (1, 0), (2, 0)),
    "l_three": ((0, 0), (1, 0), (1, 1)),
    "square": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "zigzag": ((0, 0), (0, 1), (1, 1), (1, 2)),
}


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def settings_value(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"connectivity"}:
        raise ValueError("settings must contain exactly connectivity")
    value = settings["connectivity"]
    if type(value) is not int or value not in CONNECTIVITIES:
        raise ValueError(f"connectivity must be one of {CONNECTIVITIES!r}")
    return value


def program(settings: dict[str, int]) -> str:
    connectivity = settings_value(settings)
    filename = "canonical.rkt" if connectivity == 4 else "eight-neighbor.rkt"
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


def _deltas(connectivity: int) -> tuple[tuple[int, int], ...]:
    if connectivity == 4:
        return CARDINAL
    if connectivity == 8:
        return EIGHT
    raise ValueError("connectivity must be 4 or 8")


def apply_rule(grid: list[list[int]], settings: dict[str, int]) -> list[list[int]]:
    h, w = strict_grid(grid)
    deltas = _deltas(settings_value(settings))
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            supported = any(
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 2
                for dr, dc in deltas
            )
            if not supported:
                out[r][c] = 3
    return out


def _components(grid: list[list[int]], deltas: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    h, w = strict_grid(grid)
    delta_tuple = tuple(deltas)
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in delta_tuple:
                nxt = (r + dr, c + dc)
                if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        components.append(sorted(component))
    return sorted(components, key=lambda cells: cells[0])


def analyze(grid: list[list[int]]) -> dict[str, list[Any]]:
    h, w = strict_grid(grid)
    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    four_components = _components(grid, CARDINAL)
    eight_components = _components(grid, EIGHT)
    isolated_both = [
        cell
        for cell in sorted(red)
        if not any((cell[0] + dr, cell[1] + dc) in red for dr, dc in EIGHT)
    ]
    diagonal_only_groups = [
        component
        for component in eight_components
        if len(component) > 1
        and all(
            not any((r + dr, c + dc) in red for dr, dc in CARDINAL)
            for r, c in component
        )
    ]
    cardinal_components = [component for component in four_components if len(component) > 1]
    non_red_distractors = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    ]
    return {
        "isolated_both": isolated_both,
        "diagonal_only_groups": diagonal_only_groups,
        "cardinal_components": cardinal_components,
        "non_red_distractors": non_red_distractors,
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = json.dumps([TASK_ID, SCHEMA, seed, split, index], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:16], "big"))


def _cells_for(anchor: tuple[int, int], motif_name: str) -> tuple[tuple[int, int], ...]:
    ar, ac = anchor
    return tuple((ar + dr, ac + dc) for dr, dc in MOTIFS[motif_name])


def _can_place(
    cells: tuple[tuple[int, int], ...],
    h: int,
    w: int,
    occupied: set[tuple[int, int]],
) -> bool:
    proposed = set(cells)
    if len(proposed) != len(cells):
        return False
    if any(not (0 <= r < h and 0 <= c < w) for r, c in proposed):
        return False
    if proposed & occupied:
        return False
    # Different motifs stay separated under 8-connectivity.  Internal motif
    # adjacency is intentionally unrestricted.
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in proposed
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    anchor: tuple[int, int],
    motif_name: str,
) -> bool:
    cells = _cells_for(anchor, motif_name)
    if not _can_place(cells, len(grid), len(grid[0]), occupied):
        return False
    for r, c in cells:
        grid[r][c] = 2
        occupied.add((r, c))
    return True


def _profile_targets(profile: str) -> tuple[int, int]:
    if profile == "sparse":
        return 10, 8
    if profile == "balanced":
        return 22, 14
    if profile == "dense":
        return 40, 22
    if profile == "stress":
        return 68, 32
    raise ValueError(f"unknown profile {profile!r}")


def _seed_required_roles(grid: list[list[int]], occupied: set[tuple[int, int]]) -> None:
    h, w = len(grid), len(grid[0])
    required = (
        ((0, 0), "isolated"),                         # top + left boundary
        ((0, w - 2), "diag_pair"),                   # top + right boundary
        ((h - 2, 0), "l_three"),                     # bottom + left boundary
        ((h - 3, w - 3), "h_pair"),
    )
    for anchor, motif in required:
        if not _place(grid, occupied, anchor, motif):
            raise RuntimeError(f"required motif {motif} did not fit at {anchor}")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = TRAIN_PROFILES if split == "train" else QUERY_PROFILES
    if split not in {"train", "test"} or not 0 <= index < len(profiles):
        raise ValueError("invalid split/index")
    h, w, profile = profiles[index]
    rng = _rng(seed, split, index)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    occupied: set[tuple[int, int]] = set()
    _seed_required_roles(grid, occupied)

    target_red, target_distractors = _profile_targets(profile)
    motif_cycle = [
        "diag_chain", "square", "isolated", "v_three", "diag_pair",
        "zigzag", "h_pair", "l_three",
    ]
    rng.shuffle(motif_cycle)
    anchors = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(anchors)
    cursor = 0
    while len(occupied) < target_red and cursor < len(anchors) * len(motif_cycle):
        anchor = anchors[cursor % len(anchors)]
        motif = motif_cycle[(cursor // len(anchors) + cursor) % len(motif_cycle)]
        _place(grid, occupied, anchor, motif)
        cursor += 1
    if len(occupied) < target_red:
        raise RuntimeError(f"could not place target red mass: {len(occupied)} < {target_red}")

    available = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
    rng.shuffle(available)
    if len(available) < target_distractors:
        raise RuntimeError("not enough cells for distractors")
    colors = list(DISTRACTOR_COLORS)
    rng.shuffle(colors)
    for ordinal, (r, c) in enumerate(available[:target_distractors]):
        grid[r][c] = colors[(ordinal + r + 2 * c) % len(colors)]

    roles = analyze(grid)
    if not all(roles[name] for name in ("isolated_both", "diagonal_only_groups", "cardinal_components", "non_red_distractors")):
        raise RuntimeError(f"scene is missing a required semantic role: {roles}")
    for settings in SETTING_OBJECTS:
        apply_rule(grid, settings)
    return grid


def _candidate_output(grid: list[list[int]], name: str) -> list[list[int]]:
    h, w = strict_grid(grid)
    out = [row[:] for row in grid]
    if name == "identity":
        return out
    if name == "recolor_all_red":
        return [[3 if value == 2 else value for value in row] for row in grid]
    if name == "wrong_target_color":
        canonical = apply_rule(grid, DEFAULT)
        return [[4 if canonical[r][c] == 3 and grid[r][c] == 2 else canonical[r][c] for c in range(w)] for r in range(h)]
    if name == "diagonal_neighbors_only":
        deltas = DIAGONAL
    elif name == "cardinal_endpoints":
        out = [row[:] for row in grid]
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 2:
                    continue
                neighbors = sum(
                    0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 2
                    for dr, dc in CARDINAL
                )
                if neighbors <= 1:
                    out[r][c] = 3
        return out
    elif name == "border_only":
        out = [row[:] for row in grid]
        canonical = apply_rule(grid, DEFAULT)
        for r in range(h):
            for c in range(w):
                if (r in (0, h - 1) or c in (0, w - 1)) and canonical[r][c] == 3 and grid[r][c] == 2:
                    out[r][c] = 3
        return out
    else:
        raise KeyError(name)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            if not any(
                0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 2
                for dr, dc in deltas
            ):
                out[r][c] = 3
    return out


SHORTCUTS = (
    "identity",
    "recolor_all_red",
    "wrong_target_color",
    "diagonal_neighbors_only",
    "cardinal_endpoints",
    "border_only",
)


def certify(train: list[dict[str, Any]], settings: dict[str, int]) -> dict[str, Any]:
    selected = {"connectivity": settings_value(settings)}
    if type(train) is not list or not train:
        raise ValueError("teaching requires demonstrations")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("teaching pairs require exactly input/output")
        strict_grid(pair["input"])
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


def generate(seed: int, settings: dict[str, int], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    normalized = {"connectivity": settings_value(settings)}

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
