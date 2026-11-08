"""Native parametric family for bf47583ab6e3.

The canonical setting grows a color-8 plus from every nonzero seed.  The
alternative first performs that exact growth, then finds the 4-connected
components of the grown mask and fills each component's bounding box.  Deliberate
bent seed chains make the second stage impossible to replace with independent
3x3 squares around the original seeds.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "bf47583ab6e3"
MODES = ("plus_union", "component_boxes")
HERE = Path(__file__).resolve().parent
PROGRAM_PATHS = {
    "plus_union": HERE / "canonical.rkt",
    "component_boxes": HERE / "component-boxes.rkt",
}

Grid = list[list[int]]
Coord = tuple[int, int]
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)


@dataclass(frozen=True)
class Profile:
    height: int
    width: int
    seeds: tuple[Coord, ...]
    allow_flip: bool = True


TRAIN_PROFILES = (
    Profile(11, 14, ((1, 1), (3, 2), (5, 3), (2, 10))),
    Profile(13, 15, ((0, 3), (2, 4), (4, 5), (6, 6), (10, 12))),
    Profile(14, 17, ((2, 2), (4, 3), (9, 2), (11, 3), (6, 13))),
    Profile(15, 18, ((1, 16), (3, 15), (5, 14), (12, 0), (10, 1))),
    Profile(18, 20, ((2, 2), (4, 3), (6, 4), (2, 14), (4, 15), (15, 10))),
    Profile(20, 18, ((1, 1), (3, 2), (5, 3), (7, 4), (16, 2), (16, 14))),
)
TEST_PROFILES = (
    Profile(12, 16, ((1, 1), (3, 2), (5, 3), (8, 12))),
    Profile(16, 19, ((0, 0), (2, 1), (4, 2), (8, 9), (10, 10), (15, 18))),
    Profile(22, 24, ((2, 2), (4, 3), (6, 4), (8, 5), (3, 18), (18, 20))),
    Profile(30, 30, ((2, 2), (4, 3), (6, 4), (8, 5), (10, 6), (12, 7), (25, 25), (0, 20))),
)


def _exact_int(value: Any, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise TypeError(f"{name} must be an exact integer in {lo}..{hi}; bool is forbidden")
    return value


def validate_mode(value: Any) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"output_mode must be one of {MODES}")
    return value


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)


def program_for(mode: str) -> str:
    return PROGRAM_PATHS[validate_mode(mode)].read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> Grid:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


def seed_cells(grid: Any) -> list[Coord]:
    g = _validate_grid(grid)
    return [(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value != 0]


def grow_plus(grid: Any) -> Grid:
    g = _validate_grid(grid)
    h, w = len(g), len(g[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in seed_cells(g):
        for dr, dc in PLUS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 8
    return out


def _components_of_nonzero(grid: Any) -> list[list[Coord]]:
    g = _validate_grid(grid)
    h, w = len(g), len(g[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    components: list[list[Coord]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in DIR4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
                    component.append(nxt)
        components.append(sorted(component))
    return components


def _fill_boxes(height: int, width: int, components: list[list[Coord]]) -> Grid:
    out = [[0 for _ in range(width)] for _ in range(height)]
    for component in components:
        if not component:
            continue
        r0 = min(r for r, _ in component)
        r1 = max(r for r, _ in component)
        c0 = min(c for _, c in component)
        c1 = max(c for _, c in component)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = 8
    return out


def box_grown_components(grown: Any) -> Grid:
    g = _validate_grid(grown)
    return _fill_boxes(len(g), len(g[0]), _components_of_nonzero(g))


def box_seed_components(grid: Any) -> Grid:
    g = _validate_grid(grid)
    return _fill_boxes(len(g), len(g[0]), _components_of_nonzero(g))


def solve_direct_seed_squares(grid: Any) -> Grid:
    g = _validate_grid(grid)
    h, w = len(g), len(g[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in seed_cells(g):
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                out[rr][cc] = 8
    return out


def solve_global_box(grid: Any) -> Grid:
    grown = grow_plus(grid)
    cells = seed_cells(grown)
    if not cells:
        return grown
    return _fill_boxes(len(grown), len(grown[0]), [cells])


def solve_largest_component_only(grid: Any) -> Grid:
    grown = grow_plus(grid)
    components = _components_of_nonzero(grown)
    if not components:
        return grown
    largest = max(components, key=lambda comp: (len(comp), -min(comp)[0], -min(comp)[1]))
    return _fill_boxes(len(grown), len(grown[0]), [largest])


def solve(grid: Any, mode: str) -> Grid:
    mode = validate_mode(mode)
    intermediate = grow_plus(grid)
    return intermediate if mode == "plus_union" else box_grown_components(intermediate)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(seed: int, split: str, index: int, profile: Profile) -> Grid:
    rng = _rng(seed, split, index)
    coords = list(profile.seeds)
    if profile.allow_flip and rng.random() < 0.5:
        coords = [(profile.height - 1 - r, c) for r, c in coords]
    if profile.allow_flip and rng.random() < 0.5:
        coords = [(r, profile.width - 1 - c) for r, c in coords]
    colors = rng.sample(list(PALETTE), len(coords))
    grid = [[0 for _ in range(profile.width)] for _ in range(profile.height)]
    for (r, c), color in zip(coords, colors):
        if grid[r][c] != 0:
            raise AssertionError("duplicate profile seed")
        grid[r][c] = color
    return grid


def episode_inputs(seed: int) -> dict[str, list[Grid]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    train = [_scene(seed, "train", i, profile) for i, profile in enumerate(TRAIN_PROFILES)]
    test = [_scene(seed, "test", i, profile) for i, profile in enumerate(TEST_PROFILES)]
    frozen = {json.dumps(grid, separators=(",", ":")) for grid in train + test}
    if len(frozen) != len(train) + len(test):
        raise RuntimeError("constructed duplicate inputs")
    return {"train": train, "test": test}


def generate_episode(seed: int, mode: str, demos: int = 2, queries: int = 4) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    mode = validate_mode(mode)
    bank = episode_inputs(seed)
    return {
        "train": [
            {"input": grid, "output": solve(grid, mode)}
            for grid in bank["train"][:demos]
        ],
        "test": [
            {"input": grid, "output": solve(grid, mode)}
            for grid in bank["test"][:queries]
        ],
        "program_solution": program_for(mode),
    }


def teaching_survivors(train: list[dict[str, Grid]]) -> list[str]:
    return [
        mode
        for mode in MODES
        if all(solve(pair["input"], mode) == pair["output"] for pair in train)
    ]


RIVAL_SOLVERS: dict[str, Callable[[Any], Grid]] = {
    "direct_seed_squares": solve_direct_seed_squares,
    "global_grown_bbox": solve_global_box,
    "largest_grown_component_only": solve_largest_component_only,
    "seed_component_boxes": box_seed_components,
    "canonical_plus": grow_plus,
    "grown_component_boxes": lambda grid: box_grown_components(grow_plus(grid)),
}


def finite_rival_holes(
    train: list[dict[str, Grid]], test: list[dict[str, Grid]], selected_mode: str
) -> list[dict[str, Any]]:
    selected_mode = validate_mode(selected_mode)
    holes: list[dict[str, Any]] = []
    for name, rival in RIVAL_SOLVERS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in train):
            disagreements = [
                index
                for index, pair in enumerate(test)
                if rival(pair["input"]) != pair["output"]
            ]
            if disagreements:
                holes.append({"rival": name, "query_disagreements": disagreements})
    return holes
