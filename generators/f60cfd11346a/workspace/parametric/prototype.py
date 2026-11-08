"""Native parametric family for f60cfd11346a.

The canonical setting preserves the selected flood-fill rule byte-for-byte.  The
alternate first computes that same red-seed reachable component, counts the
color-1 ports cardinally adjacent to it, and uses the resulting key in {1,2,3}
to select one of three row-major green-anchored remote chambers to fill.
"""
from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path
from random import Random
from typing import Any, Callable

_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
RELAY_PROGRAM = (_HERE / "relay.rkt").read_text(encoding="utf-8")

MODES = ("canonical", "reachable_port_relay")
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# First two demonstrations always carry different keys; the first three cover
# all keys.  Sizes are independently prefix-stable and culminate in a real 30x30
# query rather than padding a tiny scene.
_DEMO_SPECS = (
    (12, 18, 1),
    (13, 20, 3),
    (15, 22, 2),
    (18, 24, 1),
    (22, 26, 3),
    (26, 28, 2),
)
_QUERY_SPECS = (
    (14, 19, 2),
    (17, 23, 1),
    (24, 27, 3),
    (30, 30, 2),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    return {"mode": mode}


def program_for(mode: str) -> str:
    if mode == "canonical":
        return CANONICAL_PROGRAM
    if mode == "reachable_port_relay":
        return RELAY_PROGRAM
    raise ValueError(f"unknown mode {mode!r}")


def _neighbors(row: int, col: int) -> Iterable[tuple[int, int]]:
    for dr, dc in _CARDINAL:
        yield row + dr, col + dc


def _region(grid: list[list[int]], start: tuple[int, int], passable: Callable[[int], bool]) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    if not passable(grid[start[0]][start[1]]):
        raise ValueError("region start is not passable")
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for nr, nc in _neighbors(row, col):
            if (
                0 <= nr < height
                and 0 <= nc < width
                and (nr, nc) not in seen
                and passable(grid[nr][nc])
            ):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return seen


def _positions(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    if (
        type(grid) is not list
        or not grid
        or type(grid[0]) is not list
        or not grid[0]
        or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row)
    ):
        raise ValueError("grid must be a nonempty rectangular ARC integer grid")
    seeds = _positions(grid, 2)
    if len(seeds) != 1:
        raise ValueError("expected exactly one red seed")
    source_region = _region(grid, seeds[0], lambda value: value in (0, 2))
    all_ports = sorted(_positions(grid, 1))
    active_ports = [
        port
        for port in all_ports
        if any(neighbor in source_region for neighbor in _neighbors(*port))
    ]
    if not 1 <= len(active_ports) <= 3:
        raise ValueError("expected one to three source-adjacent ports")
    anchors = sorted(_positions(grid, 3))
    if len(anchors) != 3:
        raise ValueError("expected exactly three green target anchors")
    selected_anchor = anchors[len(active_ports) - 1]
    target_region = _region(grid, selected_anchor, lambda value: value in (0, 3))
    source_zeros = {cell for cell in source_region if grid[cell[0]][cell[1]] == 0}
    target_zeros = {cell for cell in target_region if grid[cell[0]][cell[1]] == 0}
    if not source_zeros or not target_zeros or source_region & target_region:
        raise ValueError("source and target must be nonempty disjoint regions")
    return {
        "seed": seeds[0],
        "source_region": tuple(sorted(source_region)),
        "source_zeros": tuple(sorted(source_zeros)),
        "all_ports": tuple(all_ports),
        "active_ports": tuple(active_ports),
        "active_port_count": len(active_ports),
        "anchors": tuple(anchors),
        "selected_anchor": selected_anchor,
        "target_region": tuple(sorted(target_region)),
        "target_zeros": tuple(sorted(target_zeros)),
    }


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    out = deepcopy(grid)
    for row, col in cells:
        out[row][col] = color
    return out


def _apply_target_rank(grid: list[list[int]], rank: int) -> list[list[int]]:
    analysis = analyze_scene(grid)
    if type(rank) is not int or not 1 <= rank <= 3:
        raise ValueError("target rank must be 1..3")
    source = _paint(grid, analysis["source_zeros"], 8)
    anchor = analysis["anchors"][rank - 1]
    target = _region(grid, anchor, lambda value: value in (0, 3))
    target_zeros = [cell for cell in target if grid[cell[0]][cell[1]] == 0]
    return _paint(source, target_zeros, 8)


def apply_mode(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    analysis = analyze_scene(grid)
    source = _paint(grid, analysis["source_zeros"], 8)
    if mode == "canonical":
        return source
    return _paint(source, analysis["target_zeros"], 8)


def apply_global_port_count_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong intermediate: count every color-1 cell, not source-adjacent ports."""
    return _apply_target_rank(grid, min(3, len(_positions(grid, 1))))


def _apply_reverse_port_count(grid: list[list[int]]) -> list[list[int]]:
    count = analyze_scene(grid)["active_port_count"]
    return _apply_target_rank(grid, 4 - count)


def _apply_source_area_modulo(grid: list[list[int]]) -> list[list[int]]:
    size = len(analyze_scene(grid)["source_zeros"])
    return _apply_target_rank(grid, (size % 3) + 1)


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in reversed(grid)]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return _flip_ud(_flip_lr(grid))


def _key(base_key: int, seed: int) -> int:
    return ((base_key - 1 + seed % 3) % 3) + 1



def _tune_source_area_decoy(grid: list[list[int]], key: int, rng: Random) -> None:
    """Make the source-area-modulo shortcut choose the next, wrong target.

    Blocking one non-articulation source zero changes the modulo without changing
    the actual reachable-port count.  The retained scene therefore teaches that
    component area is not the relay key.
    """
    desired_modulo = key % 3
    for _ in range(3):
        analysis = analyze_scene(grid)
        current_size = len(analysis["source_zeros"])
        if current_size % 3 == desired_modulo:
            return
        candidates = list(analysis["source_zeros"])
        rng.shuffle(candidates)
        changed = False
        for row, col in candidates:
            if any(grid[nr][nc] == 1 for nr, nc in _neighbors(row, col)
                   if 0 <= nr < len(grid) and 0 <= nc < len(grid[0])):
                continue
            trial = deepcopy(grid)
            trial[row][col] = 6
            try:
                after = analyze_scene(trial)
            except ValueError:
                continue
            if (
                after["active_port_count"] == key
                and len(after["source_zeros"]) == current_size - 1
            ):
                grid[row][col] = 6
                changed = True
                break
        if not changed:
            raise RuntimeError("could not tune source-area decoy without changing reachability")
    raise RuntimeError("source-area decoy tuning did not converge")

def _draw_scene(seed: int, split: str, index: int, spec: tuple[int, int, int]) -> list[list[int]]:
    height, width, base_key = spec
    if height < 12 or width < 18 or height > 30 or width > 30:
        raise ValueError("scene dimensions outside supported construction")
    salt = 0x6D2B79F5 if split == "demo" else 0x1B873593
    rng = Random(seed * 1_000_003 + index * 97_409 + salt)
    key = _key(base_key, seed)

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5

    split_col = max(7, min(width - 7, width // 2 + rng.choice((-1, 0, 1))))
    for row in range(1, height - 1):
        grid[row][split_col] = 5

    divider_1 = max(4, height // 3)
    divider_2 = min(height - 4, max(divider_1 + 3, (2 * height) // 3))
    for divider in (divider_1, divider_2):
        for col in range(split_col + 1, width - 1):
            grid[divider][col] = 5

    pocket_wall = height - 4
    for col in range(1, split_col):
        grid[pocket_wall][col] = 5

    # Alternating teeth make the source component a real wall-aware flood.  The
    # rightmost source corridor remains open so all active port candidates are
    # reachable, while the lower pocket is deliberately disconnected.
    tooth_cols = list(range(3, max(3, split_col - 2), 3))
    for tooth_index, col in enumerate(tooth_cols):
        color = (6, 7, 9)[(tooth_index + seed + index) % 3]
        if tooth_index % 2 == 0:
            rows = range(1, max(1, pocket_wall - 2))
        else:
            rows = range(3, pocket_wall)
        for row in rows:
            grid[row][col] = color

    seed_candidates = [
        (row, col)
        for row in range(1, pocket_wall)
        for col in range(1, min(3, split_col))
        if grid[row][col] == 0
    ]
    if not seed_candidates:
        raise RuntimeError("no legal seed cell")
    seed_row, seed_col = rng.choice(seed_candidates)
    grid[seed_row][seed_col] = 2

    active_candidates = [
        row
        for row in range(1, pocket_wall)
        if grid[row][split_col - 1] == 0
    ]
    inactive_candidates = [
        row
        for row in range(pocket_wall + 1, height - 1)
        if grid[row][split_col - 1] == 0
    ]
    if len(active_candidates) < 3 or len(inactive_candidates) < 2:
        raise RuntimeError("insufficient active/inactive port rows")
    active_rows = rng.sample(active_candidates, key)
    inactive_rows = rng.sample(inactive_candidates, 3 - key)
    for row in active_rows + inactive_rows:
        grid[row][split_col] = 1

    room_ranges = (
        (1, divider_1 - 1),
        (divider_1 + 1, divider_2 - 1),
        (divider_2 + 1, height - 2),
    )
    target_left, target_right = split_col + 1, width - 2
    for room_index, (top, bottom) in enumerate(room_ranges):
        if top > bottom:
            raise RuntimeError("target room collapsed")
        obstacle_col = min(target_right - 1, target_left + 2 + room_index)
        gap_row = top + ((seed + index + room_index) % (bottom - top + 1))
        if target_left + 2 <= target_right - 1:
            for row in range(top, bottom + 1):
                if row != gap_row:
                    grid[row][obstacle_col] = (4, 7, 9)[room_index]
        anchor_candidates = [
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(target_left, target_right + 1)
            if grid[row][col] == 0
        ]
        if not anchor_candidates:
            raise RuntimeError("target room has no anchor cell")
        # Alternate near/far anchor placements without revealing the selected rank.
        anchor = anchor_candidates[(seed * 7 + index * 5 + room_index * 11) % len(anchor_candidates)]
        grid[anchor[0]][anchor[1]] = 3

    _tune_source_area_decoy(grid, key, rng)

    transforms = (
        lambda value: value,
        _flip_lr,
        _flip_ud,
        _rotate_180,
    )
    grid = transforms[(seed + index + (0 if split == "demo" else 2)) % 4](grid)
    analysis = analyze_scene(grid)
    if analysis["active_port_count"] != key:
        raise RuntimeError("constructed port key changed under validation")
    return grid


def _pair(seed: int, split: str, index: int, spec: tuple[int, int, int], mode: str) -> dict[str, list[list[int]]]:
    grid = _draw_scene(seed, split, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, mode: str, demos: int, queries: int) -> dict[str, Any]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    train = [_pair(seed, "demo", index, _DEMO_SPECS[index], mode) for index in range(demos)]
    test = [_pair(seed, "query", index, _QUERY_SPECS[index], mode) for index in range(queries)]
    return {"train": train, "test": test, "program_solution": program_for(mode)}


def _rivals() -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return {
        "canonical_only": lambda grid: apply_mode(grid, "canonical"),
        "fixed_target_1": lambda grid: _apply_target_rank(grid, 1),
        "fixed_target_2": lambda grid: _apply_target_rank(grid, 2),
        "fixed_target_3": lambda grid: _apply_target_rank(grid, 3),
        "global_port_count": apply_global_port_count_rival,
        "reverse_port_count": _apply_reverse_port_count,
        "source_area_modulo": _apply_source_area_modulo,
    }


def audit_python(*, seeds: Iterable[int], demo_counts: Iterable[int]) -> dict[str, Any]:
    ambiguities: list[dict[str, Any]] = []
    rivals = _rivals()
    rival_stats = {name: {"demo_refutations": 0, "query_disagreements": 0} for name in rivals}
    serialized_inputs: set[str] = set()
    episodes = 0
    stress = 0
    for seed in seeds:
        for demos in demo_counts:
            for mode in MODES:
                episode = generate_episode(seed, mode=mode, demos=demos, queries=4)
                episodes += 1
                stress += int(len(episode["test"][3]["input"]) == 30 and len(episode["test"][3]["input"][0]) == 30)
                for pair in episode["train"] + episode["test"]:
                    serialized_inputs.add(repr(pair["input"]))
                for name, rival in rivals.items():
                    demo_matches = [rival(pair["input"]) == pair["output"] for pair in episode["train"]]
                    query_differs = [rival(pair["input"]) != pair["output"] for pair in episode["test"]]
                    if not all(demo_matches):
                        rival_stats[name]["demo_refutations"] += 1
                    if any(query_differs):
                        rival_stats[name]["query_disagreements"] += 1
                    if all(demo_matches) and any(query_differs):
                        ambiguities.append({
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "rival": name,
                        })
    return {
        "episodes": episodes,
        "pairs": len(serialized_inputs),
        "pair_instances": sum((demos + 4) * len(MODES) for _ in seeds for demos in demo_counts),
        "distinct_inputs": len(serialized_inputs),
        "stress_30x30": stress,
        "rivals": rival_stats,
        "ambiguities": ambiguities,
    }
