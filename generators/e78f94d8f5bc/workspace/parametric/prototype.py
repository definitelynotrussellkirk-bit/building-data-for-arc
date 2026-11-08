#!/usr/bin/env python3
"""Source-bound shortest-path / largest-off-path-branch parametric family.

The default ``path_only`` setting returns the selected canonical Racket source
byte-for-byte.  ``largest_branch`` first paints the unique obstacle-aware path;
the painted path then acts as a separator, and the largest remaining zero-region
is marked color 8.  Inputs are sampled independently of the hidden setting.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable, Sequence

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "e78f94d8f5bc"
VERSION = "shortest-path-largest-branch-v1"
PARAMETER_NAME = "branch_policy"
ALLOWED_SETTINGS = ("path_only", "largest_branch")
DEFAULT_SETTING = "path_only"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
GENERATOR_SHA256 = "92d7322e92d454be7e44ee31cdf557008e8faa7e55e3d70a7173dedf4e165bae"
CANONICAL_SHA256 = "b27fc286bf0cb1046d6fad44346c0ba8be2b9cf54168c63f6575aff688ef73c9"
_HOME = Path(__file__).resolve().parent
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_GENERATOR = None

# The first two profiles are deliberately strong teaching cases; later profiles
# diversify geometry without changing the hidden rule.
_DEMO_PROFILES = (
    (10, 10, 4),
    (10, 10, 3),
    (6, 6, 2),
    (10, 10, 2),
    (6, 10, 3),
    (10, 6, 3),
)
_QUERY_PROFILES = ((5, 5, 2), (6, 10, 3), (10, 6, 4))


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _exact_integer(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value) -> str:
    if type(value) is not str or value not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}")
    return value


def validate_settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME}")
    return _setting(settings[PARAMETER_NAME])


def _generator():
    global _GENERATOR
    if _GENERATOR is None:
        module, _, digest = load_selected_generator(TASK_ID, root=find_root(__file__))
        if digest != GENERATOR_SHA256:
            raise ValueError("Production generator changed; re-review the parametric family")
        _GENERATOR = module
    return _GENERATOR


def _canonical_catalog_program() -> str:
    programs = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one exact canonical program for the selected task")
    return programs.pop()


def canonical_program() -> str:
    source = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
    if _sha256(source) != CANONICAL_SHA256 or source != _canonical_catalog_program():
        raise ValueError("Canonical authority changed; re-review exact source binding")
    return source


def program_for(branch_policy: str) -> str:
    setting = _setting(branch_policy)
    if setting == DEFAULT_SETTING:
        return canonical_program()
    source = (_HOME / "largest_branch.rkt").read_text(encoding="utf-8")
    if source.count("(shortest-path-fill ") != 1 or source.count("(find-0-regions filled 0)") != 1:
        raise ValueError("Largest-branch program no longer contains the reviewed two-stage rule")
    return source


def program(settings) -> str:
    return program_for(validate_settings(settings))


def _grid(value) -> list[list[int]]:
    if (
        type(value) is not list
        or not 5 <= len(value) <= 30
        or type(value[0]) is not list
        or not 5 <= len(value[0]) <= 30
    ):
        raise ValueError("grid dimensions must be 5..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or cell not in (0, 1, 2) for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0, 1, 2")
    return [row[:] for row in value]


def _neighbors(cell: tuple[int, int], h: int, w: int) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _CARDINAL:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _shortest_path(grid: list[list[int]]) -> list[tuple[int, int]]:
    endpoints = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(endpoints) != 2:
        raise ValueError("input requires exactly two color-2 endpoints")
    start, goal = endpoints
    h, w = len(grid), len(grid[0])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in _neighbors(cell, h, w):
            if nxt in parent:
                continue
            if grid[nxt[0]][nxt[1]] == 0 or nxt == goal:
                parent[nxt] = cell
                queue.append(nxt)
    if goal not in parent:
        raise ValueError("endpoints are disconnected")
    path = []
    current: tuple[int, int] | None = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def _regions_of_zero(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    regions: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            region: list[tuple[int, int]] = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cell = queue.popleft()
                region.append(cell)
                for nxt in _neighbors(cell, h, w):
                    if nxt not in seen and grid[nxt[0]][nxt[1]] == 0:
                        seen.add(nxt)
                        queue.append(nxt)
            regions.append(region)
    return regions


def _analyze_input(value) -> dict:
    grid = _grid(value)
    endpoints = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(endpoints) != 2:
        raise ValueError("input requires exactly two color-2 endpoints")
    path = _shortest_path(grid)
    walkable = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (0, 2)}
    h, w = len(grid), len(grid[0])
    reached = set()
    queue = deque([endpoints[0]])
    reached.add(endpoints[0])
    while queue:
        cell = queue.popleft()
        for nxt in _neighbors(cell, h, w):
            if nxt in walkable and nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    if reached != walkable:
        raise ValueError("all walkable cells must share the endpoint region")
    edge_count = sum(
        (r + 1, c) in walkable for r, c in walkable
    ) + sum((r, c + 1) in walkable for r, c in walkable)
    if edge_count != len(walkable) - 1:
        raise ValueError("walkable cells must form a tree")
    manhattan = abs(endpoints[0][0] - endpoints[1][0]) + abs(endpoints[0][1] - endpoints[1][1])
    if len(path) - 1 <= manhattan:
        raise ValueError("walls must force a detour between endpoints")
    filled = [row[:] for row in grid]
    for r, c in path:
        filled[r][c] = 4
    regions = _regions_of_zero(filled)
    if not regions:
        raise ValueError("path must leave at least one off-path branch")
    return {
        "grid": grid,
        "endpoints": endpoints,
        "path": path,
        "regions": regions,
        "region_sizes": [len(region) for region in regions],
        "walkable_count": len(walkable),
        "path_distance": len(path) - 1,
        "manhattan_distance": manhattan,
    }


def _paint_path(analysis: dict) -> list[list[int]]:
    output = [row[:] for row in analysis["grid"]]
    for r, c in analysis["path"]:
        output[r][c] = 4
    for r, c in analysis["endpoints"]:
        output[r][c] = 2
    return output


def _choose_region(regions: list[list[tuple[int, int]]], mode: str):
    if mode == "largest":
        return max(regions, key=len)
    if mode == "smallest":
        return min(regions, key=len)
    if mode == "first":
        return regions[0]
    if mode == "last":
        return regions[-1]
    raise ValueError(f"unknown region mode {mode!r}")


def _solve_variant(grid, variant: str) -> list[list[int]]:
    analysis = _analyze_input(grid)
    if variant == "path_only":
        return _paint_path(analysis)
    if variant in ("largest_branch", "smallest_branch", "first_branch", "last_branch"):
        output = _paint_path(analysis)
        region = _choose_region(analysis["regions"], variant.split("_")[0])
        for r, c in region:
            output[r][c] = 8
        return output
    if variant == "all_branches":
        output = _paint_path(analysis)
        for region in analysis["regions"]:
            for r, c in region:
                output[r][c] = 8
        return output
    if variant == "skip_path_largest_zero_region":
        output = [row[:] for row in analysis["grid"]]
        regions = _regions_of_zero(output)
        if regions:
            for r, c in max(regions, key=len):
                output[r][c] = 8
        return output
    raise ValueError(f"unknown variant {variant!r}")


def solve_python(grid, branch_policy: str) -> list[list[int]]:
    return _solve_variant(grid, _setting(branch_policy))


def intermediate_record(grid) -> dict:
    analysis = _analyze_input(grid)
    largest = _choose_region(analysis["regions"], "largest")
    return {
        "path_cells": [list(cell) for cell in analysis["path"]],
        "path_distance": analysis["path_distance"],
        "branch_region_sizes_row_major": analysis["region_sizes"],
        "largest_branch_cells": [list(cell) for cell in largest],
        "largest_branch_size": len(largest),
    }


def _branch_program(selector: str, *, skip_path: bool = False, all_regions: bool = False) -> str:
    if skip_path:
        base = "g"
        filled = "g"
    else:
        base = "filled"
        filled = "(shortest-path-fill g r1 c1 r2 c2 4 0)"
    if all_regions:
        choose = f"(recolor {base} 0 8)"
        bindings = f"(marked {choose})"
    else:
        selector_expr = {
            "largest": "(pick-max regions length)",
            "smallest": "(pick-min regions length)",
            "first": "(first regions)",
            "last": "(last regions)",
        }[selector]
        bindings = f"(regions (find-0-regions {base} 0))\n         (chosen {selector_expr})\n         (marked (if chosen (recolor-cells {base} chosen 8) {base}))"
    return f"""(rule! (lambda (g)
  (let* ((pts (find-color g 2))
         (p1 (first pts))
         (p2 (second pts))
         (r1 (fst p1)) (c1 (snd p1))
         (r2 (fst p2)) (c2 (snd p2))
         (filled {filled})
         {bindings})
    (set-cell (set-cell marked r1 c1 2) r2 c2 2))))"""


def rival_programs(selected_setting: str) -> dict[str, str]:
    selected = _setting(selected_setting)
    alternate = next(setting for setting in ALLOWED_SETTINGS if setting != selected)
    return {
        "alternate_setting": program_for(alternate),
        "all_branches": _branch_program("largest", all_regions=True),
        "smallest_branch": _branch_program("smallest"),
        "first_branch": _branch_program("first"),
        "last_branch": _branch_program("last"),
        "skip_path_largest_zero_region": _branch_program("largest", skip_path=True),
    }


def _rival_output(name: str, grid, selected_setting: str):
    selected = _setting(selected_setting)
    if name == "alternate_setting":
        other = next(setting for setting in ALLOWED_SETTINGS if setting != selected)
        return solve_python(grid, other)
    return _solve_variant(grid, name)


def _derived_seed(seed: int, split: str, slot: int) -> int:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{split}:{slot}".encode()).digest()
    return int.from_bytes(digest[:8], "big") & MAX_SEED


def _qualifies_strong_demo(grid) -> bool:
    try:
        analysis = _analyze_input(grid)
    except ValueError:
        return False
    sizes = analysis["region_sizes"]
    if len(sizes) < 3 or sizes.count(max(sizes)) != 1:
        return False
    max_index = sizes.index(max(sizes))
    if max_index in (0, len(sizes) - 1):
        return False
    selected = solve_python(grid, "largest_branch")
    for name in rival_programs("largest_branch"):
        if _rival_output(name, grid, "largest_branch") == selected:
            return False
    return True


@lru_cache(maxsize=4096)
def _draw_production_scene(seed: int, split: str, slot: int, profile, *, strong=False):
    generator = _generator()
    h, w, turns = profile
    for attempt in range(256):
        draw_seed = _derived_seed(seed, split, slot)
        sample_index = 100_000 * slot + attempt + (0 if split == "demos" else 50_000)
        try:
            grid = generator.generate(
                draw_seed,
                sample_index,
                difficulty="hard",
                grid_h=h,
                grid_w=w,
                route_turns=turns,
            )
            _analyze_input(grid)
        except (AssertionError, RuntimeError, ValueError):
            continue
        if solve_python(grid, "path_only") == solve_python(grid, "largest_branch"):
            continue
        if strong and not _qualifies_strong_demo(grid):
            continue
        return _grid(grid)
    raise ValueError(f"Could not draw {split} scene {slot} with profile {profile}")


def _tree_path(adjacency, start, goal):
    parent = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            break
        for nxt in adjacency[cell]:
            if nxt not in parent:
                parent[nxt] = cell
                queue.append(nxt)
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    return list(reversed(path))


def _turn_count(path):
    directions = [
        (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        for i in range(len(path) - 1)
    ]
    return sum(a != b for a, b in zip(directions, directions[1:]))


@lru_cache(maxsize=512)
def _stress_grid(seed: int) -> list[list[int]]:
    """Construct a dense 30x30 expanded random spanning tree."""
    rng = random.Random(_derived_seed(seed, "stress", 0))
    height = width = 15
    nodes = [(r, c) for r in range(height) for c in range(width)]
    edges = []
    for r, c in nodes:
        if r + 1 < height:
            edges.append(((r, c), (r + 1, c)))
        if c + 1 < width:
            edges.append(((r, c), (r, c + 1)))
    rng.shuffle(edges)
    parent = {node: node for node in nodes}
    rank = {node: 0 for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    tree = []
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        tree.append((a, b))
        if len(tree) == len(nodes) - 1:
            break

    adjacency = {node: [] for node in nodes}
    for a, b in tree:
        adjacency[a].append(b)
        adjacency[b].append(a)
    leaves = [node for node in nodes if len(adjacency[node]) == 1]
    candidates = []
    for i, start in enumerate(leaves):
        for goal in leaves[i + 1:]:
            path = _tree_path(adjacency, start, goal)
            distance = len(path) - 1
            manhattan = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            turns = _turn_count(path)
            off_path = len(nodes) - len(path)
            if distance > manhattan and off_path >= 30 and turns >= 6:
                candidates.append((distance + 2 * (distance - manhattan) + turns, start, goal, path))
    if not candidates:
        raise ValueError("Could not select a detouring stress path")
    _, start, goal, _ = max(candidates)

    phase_r = rng.randrange(2)
    phase_c = rng.randrange(2)
    grid = [[1] * 30 for _ in range(30)]

    def expand(node):
        return phase_r + 2 * node[0], phase_c + 2 * node[1]

    for node in nodes:
        r, c = expand(node)
        grid[r][c] = 0
    for a, b in tree:
        ar, ac = expand(a)
        br, bc = expand(b)
        grid[(ar + br) // 2][(ac + bc) // 2] = 0
    sr, sc = expand(start)
    gr, gc = expand(goal)
    grid[sr][sc] = 2
    grid[gr][gc] = 2
    _analyze_input(grid)
    return grid


@lru_cache(maxsize=1024)
def _sample_inputs(seed: int, demos: int) -> tuple[list[list[list[int]]], list[str]]:
    demo_grids = [
        _draw_production_scene(seed, "demos", slot, _DEMO_PROFILES[slot], strong=(slot == 0))
        for slot in range(demos)
    ]
    query_grids = [
        _draw_production_scene(seed, "queries", slot, profile)
        for slot, profile in enumerate(_QUERY_PROFILES)
    ]
    query_grids.append(_stress_grid(seed))
    grids = demo_grids + query_grids
    keys = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(set(keys)) != len(keys):
        raise ValueError("Episode inputs must be distinct")
    profiles = [f"{h}x{w}_{turns}_turns" for h, w, turns in _DEMO_PROFILES[:demos]]
    profiles += [f"{h}x{w}_{turns}_turns" for h, w, turns in _QUERY_PROFILES]
    profiles.append("30x30_dense_tree_stress")
    return grids, profiles


def build_claimed_episode(seed: int, branch_policy: str, demos: int, queries: int) -> dict:
    seed = _exact_integer(seed, "seed", 0, MAX_SEED)
    setting = _setting(branch_policy)
    demos = _exact_integer(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _exact_integer(queries, "queries", QUERY_COUNT, QUERY_COUNT)
    inputs, profiles = _sample_inputs(seed, demos)
    outputs = [solve_python(grid, setting) for grid in inputs]
    pairs = [
        {"input": [row[:] for row in grid], "output": [row[:] for row in output]}
        for grid, output in zip(inputs, outputs, strict=True)
    ]
    intermediates = [intermediate_record(grid) for grid in inputs]
    source = program_for(setting)
    return {
        "schema": "e78f94d8f5bc-branch-policy-episode-v1",
        "status": "proposed_unapproved",
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: setting},
        "program": source,
        "program_solution": source,
        "program_sha256": _sha256(source),
        "train": pairs[:demos],
        "test": pairs[demos:],
        "input_profiles": {"train": profiles[:demos], "test": profiles[demos:]},
        "intermediates": {"train": intermediates[:demos], "test": intermediates[demos:]},
    }


def teaching_report(episode: dict) -> dict:
    if type(episode) is not dict or type(episode.get("settings")) is not dict:
        raise ValueError("episode must contain private settings")
    selected = validate_settings(episode["settings"])
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode needs train and test lists")
    selected_programs = rival_programs(selected)
    surviving = []
    rejected = []
    query_disagreements = {}
    for name in selected_programs:
        fits = all(_rival_output(name, pair["input"], selected) == pair["output"] for pair in train)
        if fits:
            surviving.append(name)
            query_disagreements[name] = [
                index
                for index, pair in enumerate(test)
                if _rival_output(name, pair["input"], selected) != pair["output"]
            ]
        else:
            rejected.append(name)
    return {
        "selected_setting": selected,
        "demos_identify_declared_setting": not surviving,
        "surviving_rivals": surviving,
        "rejected_rivals": rejected,
        "surviving_rival_query_disagreements": query_disagreements,
        "all_queries_match_selected": all(
            solve_python(pair["input"], selected) == pair["output"] for pair in test
        ),
    }


def public_challenge(episode: dict, query_indices: Sequence[int] | None = None) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not test:
        raise ValueError("episode needs train and nonempty test lists")
    if query_indices is None:
        indices = list(range(len(test)))
    else:
        if not isinstance(query_indices, (list, tuple)):
            raise ValueError("query_indices must be a list or tuple")
        indices = []
        for value in query_indices:
            index = _exact_integer(value, "query index", 0, len(test) - 1)
            if index in indices:
                raise ValueError("query indices must be distinct")
            indices.append(index)
    candidate = {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": deepcopy(test[index]["input"])} for index in indices],
    }
    return json.loads(public_challenge_bytes(candidate))


def sequential_turn(episode: dict, query_index: int) -> dict:
    test = episode.get("test") if type(episode) is dict else None
    if type(test) is not list or not test:
        raise ValueError("episode needs nonempty test pairs")
    index = _exact_integer(query_index, "query_index", 0, len(test) - 1)
    if index == 0:
        return public_challenge(episode, query_indices=[0])
    return {"test": [{"input": deepcopy(test[index]["input"])}]}


def public_id(episode: dict, query_indices: Sequence[int] | None = None) -> str:
    return public_challenge_id(public_challenge(episode, query_indices=query_indices))


__all__ = [
    "ALLOWED_SETTINGS",
    "DEFAULT_SETTING",
    "PARAMETER_NAME",
    "QUERY_COUNT",
    "build_claimed_episode",
    "canonical_program",
    "intermediate_record",
    "program",
    "program_for",
    "public_challenge",
    "public_id",
    "rival_programs",
    "sequential_turn",
    "solve_python",
    "teaching_report",
    "validate_settings",
]
