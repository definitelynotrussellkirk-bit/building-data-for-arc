#!/usr/bin/env python3
"""Episode-fixed scan-order family for ARC task 092360ee834f.

Both settings first count blue (1) cells in row 0, producing the
input-dependent target area ``k``.  They then keep only green (3) body
components of area ``k``.  The hidden episode setting chooses the first or
last such component in row-major scan order and paints it cyan (8) on a blank
canvas.  ``first`` is the exact canonical Racket program.
"""
from __future__ import annotations

import argparse
from collections import deque
from functools import lru_cache
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable, Iterable

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "092360ee834f"
SETTINGS = ({"match_order": "first"}, {"match_order": "last"})
DEFAULT_SETTINGS = SETTINGS[0]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 8)


def _canonical_program() -> str:
    root = find_root(__file__)
    programs: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}")
    return programs[0]


CANONICAL_PROGRAM = _canonical_program()
_OBJECTS_EXPR = "(objects (keep-only body 3) 0)"
if CANONICAL_PROGRAM.count(_OBJECTS_EXPR) != 1:
    raise RuntimeError("canonical object-list patch point changed")
LAST_PROGRAM = CANONICAL_PROGRAM.replace(_OBJECTS_EXPR, f"(reverse {_OBJECTS_EXPR})")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer (bool is forbidden)")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: dict[str, Any] | None, *, seed: int | None = None) -> dict[str, str]:
    if value is None:
        if seed is None:
            value = dict(DEFAULT_SETTINGS)
        else:
            value = dict(SETTINGS[_rng(seed, "setting").randrange(len(SETTINGS))])
    if type(value) is not dict or set(value) != {"match_order"}:
        raise ValueError("settings must contain exactly match_order")
    order = value["match_order"]
    if order not in {"first", "last"}:
        raise ValueError("match_order must be first or last")
    return {"match_order": order}


def program(settings: dict[str, Any] | None = None) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["match_order"] == "first" else LAST_PROGRAM


def digest(value: Any) -> str:
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = f"{TASK_ID}|{seed}|{stream}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    for row in grid:
        if type(row) is not list or len(row) != w:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid cells must be exact integers in 0..9")
    return h, w


def _neighbors4(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r, c - 1), (r, c + 1), (r + 1, c))


def _neighbors8(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return tuple(
        (r + dr, c + dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if dr or dc
    )


def _components(
    grid: list[list[int]],
    *,
    color: int | None = 3,
    connectivity: int = 4,
    body_only: bool = True,
) -> list[list[tuple[int, int]]]:
    h, w = _validate_grid(grid)
    row_lo = 1 if body_only else 0
    if color is None:
        cells = {(r, c) for r in range(row_lo, h) for c in range(w) if grid[r][c] != 0}
    else:
        cells = {(r, c) for r in range(row_lo, h) for c in range(w) if grid[r][c] == color}
    neighbors = _neighbors4 if connectivity == 4 else _neighbors8
    result: list[list[tuple[int, int]]] = []
    while cells:
        first = min(cells)
        cells.remove(first)
        queue = deque([first])
        component: list[tuple[int, int]] = []
        while queue:
            cell = queue.popleft()
            component.append(cell)
            for nxt in neighbors(cell):
                if nxt in cells:
                    cells.remove(nxt)
                    queue.append(nxt)
        result.append(sorted(component))
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _side(cells: Iterable[tuple[int, int]], width: int) -> str:
    _, c0, _, c1 = _bbox(cells)
    return "left" if c0 + c1 < width - 1 else "right"


def _diagonal_traps(components: list[list[tuple[int, int]]], target: int) -> list[tuple[int, int]]:
    traps: list[tuple[int, int]] = []
    sets = [set(cells) for cells in components]
    for i, left in enumerate(sets):
        for j in range(i + 1, len(sets)):
            right = sets[j]
            if len(left) + len(right) != target:
                continue
            if any(
                abs(r1 - r2) == 1 and abs(c1 - c2) == 1
                for r1, c1 in left
                for r2, c2 in right
            ):
                traps.append((i, j))
    return traps


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    h, w = _validate_grid(grid)
    target = sum(value == 1 for value in grid[0])
    green = _components(grid, color=3, connectivity=4)
    matches = [cells for cells in green if len(cells) == target]
    body_nonzero = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if body_nonzero:
        r0, c0, r1, c1 = _bbox(body_nonzero)
        bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
    else:
        bbox_h = bbox_w = 0
    return {
        "grid_h": h,
        "grid_w": w,
        "target_size": target,
        "green_components": green,
        "green_component_sizes": [len(cells) for cells in green],
        "green_component_count": len(green),
        "matching_green_components": matches,
        "matching_green_count": len(matches),
        "first_match_side": _side(matches[0], w) if matches else None,
        "last_match_side": _side(matches[-1], w) if matches else None,
        "body_nonzero_count": len(body_nonzero),
        "body_bbox_height": bbox_h,
        "body_bbox_width": bbox_w,
        "body_blue_count": sum(grid[r][c] == 1 for r in range(1, h) for c in range(w)),
        "row0_nonblue_distractors": sum(value not in (0, 1) for value in grid[0]),
        "diagonal_trap_count": len(_diagonal_traps(green, target)),
    }


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    selected = _settings(settings)
    facts = analyze_scene(grid)
    out = [[0] * facts["grid_w"] for _ in range(facts["grid_h"])]
    matches = facts["matching_green_components"]
    if not matches:
        return out
    chosen = matches[0] if selected["match_order"] == "first" else matches[-1]
    for r, c in chosen:
        out[r][c] = 8
    return out


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _grow_shape(rng: random.Random, size: int, *, max_h: int = 4, max_w: int = 5) -> tuple[tuple[int, int], ...]:
    for _ in range(256):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = sorted(
                nxt
                for cell in cells
                for nxt in _neighbors4(cell)
                if nxt not in cells
            )
            cells.add(frontier[rng.randrange(len(frontier))])
        shape = _normalize_shape(cells)
        if max(r for r, _ in shape) < max_h and max(c for _, c in shape) < max_w:
            return shape
    raise ValueError(f"could not grow compact shape of size {size}")


def _diagonal_group(target: int) -> tuple[tuple[int, int], ...]:
    left = max(1, target // 2)
    right = target - left
    cells = [(0, c) for c in range(left)]
    cells.extend((1, left + c) for c in range(right))
    return tuple(cells)


def _place_group(
    grid: list[list[int]],
    rng: random.Random,
    shape: tuple[tuple[int, int], ...],
    color: int,
    occupied: set[tuple[int, int]],
    green: set[tuple[int, int]],
    region: tuple[int, int, int, int],
) -> set[tuple[int, int]] | None:
    h, w = len(grid), len(grid[0])
    rlo, rhi, clo, chi = region
    rlo, rhi = max(1, rlo), min(h, rhi)
    clo, chi = max(0, clo), min(w, chi)
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    candidates = [
        (r0, c0)
        for r0 in range(rlo, rhi - sh + 1)
        for c0 in range(clo, chi - sw + 1)
    ]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        cells = {(r0 + r, c0 + c) for r, c in shape}
        if cells & occupied:
            continue
        # Keep every visible object 4-disconnected.  This is stronger than the
        # rule needs for green components, but it makes the deliberate non-green
        # same-area sentinel an independently testable object for color-filter
        # shortcuts.  Green groups additionally remain 8-disconnected so the
        # diagonal trap is the only intended 4-vs-8 ambiguity.
        orthogonal_halo = {
            nxt for cell in cells for nxt in _neighbors4(cell) if nxt not in cells
        }
        if orthogonal_halo & occupied:
            continue
        if color == 3:
            halo8 = {nxt for cell in cells for nxt in _neighbors8(cell) if nxt not in cells}
            if halo8 & green:
                continue
        for r, c in cells:
            grid[r][c] = color
        occupied.update(cells)
        if color == 3:
            green.update(cells)
        return cells
    return None


def _header(rng: random.Random, grid: list[list[int]], target: int, *, stress: bool) -> None:
    width = len(grid[0])
    available = list(range(width))
    chosen: set[int] = set()
    if target >= 2:
        chosen.add(rng.choice(range(0, max(1, width // 3))))
        chosen.add(rng.choice(range(max(0, 2 * width // 3), width)))
    while len(chosen) < target:
        chosen.add(rng.choice(available))
    for c in chosen:
        grid[0][c] = 1
    unused = [c for c in available if c not in chosen]
    rng.shuffle(unused)
    for color, c in zip((2, 4), unused[:2]):
        grid[0][c] = color
    if stress and unused:
        # Make the visible header span the full width without changing k.
        if 0 not in chosen:
            grid[0][0] = 2
        if width - 1 not in chosen:
            grid[0][width - 1] = 4


def _side_region(h: int, w: int, *, vertical: str, side: str) -> tuple[int, int, int, int]:
    band_h = max(5, h // 4)
    band_w = max(6, w // 2)
    if vertical == "top":
        rlo, rhi = 2, min(h, 2 + band_h)
    elif vertical == "bottom":
        rlo, rhi = max(2, h - band_h), h
    else:
        rlo, rhi = max(2, h // 3 - 1), min(h, 2 * h // 3 + 2)
    if side == "left":
        clo, chi = 0, min(w, band_w)
    elif side == "right":
        clo, chi = max(0, w - band_w), w
    else:
        clo, chi = 0, w
    return rlo, rhi, clo, chi


# h, w, target, first-match side.  The final four query entries deliberately
# cross side with target/size and culminate in a substantive 30x30 scene.
_DEMO_PROFILES = (
    (14, 16, 3, "right"),
    (14, 16, 4, "left"),
    (16, 18, 5, "right"),
    (13, 15, 2, "left"),
    (18, 20, 6, "right"),
    (20, 22, 7, "left"),
)
_QUERY_PROFILES = (
    (12, 14, 4, "left"),
    (18, 20, 6, "right"),
    (24, 27, 3, "left"),
    (30, 30, 8, "right"),
    (14, 18, 5, "right"),
    (20, 22, 7, "left"),
    (26, 29, 4, "right"),
    (29, 30, 6, "left"),
)


def _line(size: int) -> tuple[tuple[int, int], ...]:
    return tuple((0, c) for c in range(size))


def _compact_block(size: int, *, width: int = 4) -> tuple[tuple[int, int], ...]:
    """Deterministic compact object used where a long edge line cannot fit."""
    width = min(width, size)
    return tuple((index // width, index % width) for index in range(size))


def _edge_region(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    *,
    edge: str,
    side: str,
    row_offset: int = 0,
) -> tuple[int, int, int, int]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if edge == "top":
        rlo = 1 + row_offset
    else:
        rlo = h - row_offset - sh
    rhi = rlo + sh
    if side == "left":
        clo, chi = 0, min(w, max(sw, w // 2))
    else:
        clo, chi = max(0, w - max(sw, w // 2)), w
    return rlo, rhi, clo, chi


def _construct_input(seed: int, split: str, index: int, profile: tuple[int, int, int, str]) -> list[list[int]]:
    h, w, target, first_side = profile
    last_side = "left" if first_side == "right" else "right"
    stress = h == 30 and w == 30
    # Alternating edge challenges make the minimum two-demo lesson reject
    # both pre-selection and post-selection shortcuts.
    edge_mode = "pre" if index % 2 == 0 else "post"
    for attempt in range(512):
        rng = _rng(seed, f"{split}-scene-{index}", attempt)
        grid = [[0] * w for _ in range(h)]
        _header(rng, grid, target, stress=stress)
        occupied: set[tuple[int, int]] = set()
        green: set[tuple[int, int]] = set()
        failed = False

        edge = "top" if edge_mode == "pre" else "bottom"
        # Wrong-area green sentinel: placed before all matches in even scenes
        # and after all matches in odd scenes. It is also larger than k, so a
        # largest-object shortcut cannot fit the demonstrations.
        wrong_area = _line(target + 1)
        if _place_group(
            grid,
            rng,
            wrong_area,
            3,
            occupied,
            green,
            _edge_region(h, w, wrong_area, edge=edge, side="left"),
        ) is None:
            continue

        # Same-area non-green sentinel defeats ignoring keep-only color 3.
        wrong_color = _compact_block(target)
        if _place_group(
            grid,
            rng,
            wrong_color,
            (2, 5, 6, 7, 9)[index % 5],
            occupied,
            green,
            _edge_region(h, w, wrong_color, edge=edge, side="right", row_offset=1),
        ) is None:
            continue

        # Two diagonal green components whose combined 8-connected area is k.
        # They precede all matches in even scenes and follow them in odd scenes.
        diagonal = _diagonal_group(target)
        if _place_group(
            grid,
            rng,
            diagonal,
            3,
            occupied,
            green,
            _edge_region(
                h,
                w,
                diagonal,
                edge=edge,
                side="left",
                row_offset=2,
            ),
        ) is None:
            continue

        match_count = 4 if stress else (3 if h >= 18 else 2)
        match_specs = [("top", first_side), ("bottom", last_side)]
        for mid in range(match_count - 2):
            match_specs.insert(1 + mid, ("middle", "right" if (mid + index) % 2 else "left"))
        match_cells: list[set[tuple[int, int]]] = []
        for vertical, side in match_specs:
            region = list(_side_region(h, w, vertical=vertical, side=side))
            if edge_mode == "pre":
                region[0] = max(region[0], 6)
                region[1] = max(region[1], min(h, region[0] + 6))
            else:
                region[1] = min(region[1], h - 5)
                region[0] = min(region[0], max(2, region[1] - 6))
            # Compact matches keep the edge challenge spatially separate.
            shape = _grow_shape(rng, target, max_h=3 if target <= 6 else 4, max_w=5)
            cells = _place_group(
                grid,
                rng,
                shape,
                3,
                occupied,
                green,
                tuple(region),
            )
            if cells is None:
                failed = True
                break
            match_cells.append(cells)
        if failed:
            continue

        # Additional smaller/larger area decoys vary topology and density.
        decoy_sizes: list[int] = []
        for size in (max(1, target - 1), target + 2, max(1, target - 2), 1, 2, 9, 10):
            if 1 <= size <= 10 and size != target and size not in decoy_sizes:
                decoy_sizes.append(size)
        need_decoys = 3 if stress else (2 if h >= 18 else 1)
        placed_decoys = 0
        edge_regions = [
            _side_region(h, w, vertical="top", side=last_side),
            _side_region(h, w, vertical="bottom", side=first_side),
            _side_region(h, w, vertical="middle", side="left"),
            _side_region(h, w, vertical="middle", side="right"),
        ]
        for size, region in zip(decoy_sizes, edge_regions * 3):
            adjusted = list(region)
            if edge_mode == "pre":
                adjusted[0] = max(adjusted[0], 6)
                adjusted[1] = max(adjusted[1], min(h, adjusted[0] + 6))
            else:
                adjusted[1] = min(adjusted[1], h - 5)
                adjusted[0] = min(adjusted[0], max(2, adjusted[1] - 6))
            if _place_group(
                grid,
                rng,
                _grow_shape(rng, size),
                3,
                occupied,
                green,
                tuple(adjusted),
            ):
                placed_decoys += 1
                if placed_decoys >= need_decoys:
                    break
        if placed_decoys < need_decoys:
            continue

        # More same-area non-green objects vary nuisance geometry beyond the
        # forced edge sentinel.
        other_count = 2 if stress else (1 if h >= 18 else 0)
        for n in range(other_count):
            color = (2, 5, 6, 7, 9)[(index + n + 1) % 5]
            region = _side_region(
                h,
                w,
                vertical=("top", "middle", "bottom")[n % 3],
                side=("left", "right")[n % 2],
            )
            adjusted = list(region)
            if edge_mode == "pre":
                adjusted[0] = max(adjusted[0], 6)
                adjusted[1] = max(adjusted[1], min(h, adjusted[0] + 6))
            else:
                adjusted[1] = min(adjusted[1], h - 5)
                adjusted[0] = min(adjusted[0], max(2, adjusted[1] - 6))
            if _place_group(
                grid,
                rng,
                _grow_shape(rng, target),
                color,
                occupied,
                green,
                tuple(adjusted),
            ) is None:
                failed = True
                break
        if failed:
            continue

        # Body blue cells refute counting all 1s rather than row-0 1s.
        body_blue_needed = 4 if stress else 2
        for n in range(body_blue_needed):
            region = list(
                _side_region(
                    h,
                    w,
                    vertical=("top", "bottom")[n % 2],
                    side=("right", "left")[n % 2],
                )
            )
            if edge_mode == "pre":
                region[0] = max(region[0], 6)
                region[1] = max(region[1], min(h, region[0] + 6))
            else:
                region[1] = min(region[1], h - 5)
                region[0] = min(region[0], max(2, region[1] - 6))
            if _place_group(grid, rng, ((0, 0),), 1, occupied, green, tuple(region)) is None:
                failed = True
                break
        if failed:
            continue

        if stress:
            # Keep the 30x30 profile substantive for every accepted target
            # override, including tiny k values whose semantic objects alone do
            # not occupy 70 cells.  Non-green filler is rule-irrelevant and is
            # added only after every object-level invariant has been built.
            body_nonzero = sum(cell != 0 for row in grid[1:] for cell in row)
            candidates = [
                (r, c)
                for r in range(1, h)
                for c in range(w)
                if grid[r][c] == 0
            ]
            rng.shuffle(candidates)
            filler_colors = (2, 4, 5, 6, 7, 9)
            for n, (r, c) in enumerate(candidates[: max(0, 70 - body_nonzero)]):
                grid[r][c] = filler_colors[n % len(filler_colors)]

        facts = analyze_scene(grid)
        matches = facts["matching_green_components"]
        if facts["target_size"] != target or len(matches) != match_count:
            continue
        if facts["first_match_side"] != first_side or facts["last_match_side"] != last_side:
            continue
        if facts["diagonal_trap_count"] < 1 or facts["body_blue_count"] < body_blue_needed:
            continue
        if max(facts["green_component_sizes"]) <= target:
            continue
        if stress and (
            facts["body_nonzero_count"] < 70
            or facts["body_bbox_height"] < 26
            or facts["body_bbox_width"] < 26
            or facts["green_component_count"] < 8
        ):
            continue
        return grid
    raise ValueError(f"could not construct {split}[{index}] profile={profile}")


@lru_cache(maxsize=1024)
def _input_tuple(seed: int, split: str, index: int, target_override: int | None = None) -> tuple[tuple[int, ...], ...]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    if type(index) is not int or not 0 <= index < len(profiles):
        raise ValueError(f"{split} index outside supported profile bank")
    profile = profiles[index]
    if target_override is not None:
        target_override = _integer(target_override, "target_size", 2, 8)
        profile = (profile[0], profile[1], target_override, profile[3])
    grid = _construct_input(seed, split, index, profile)
    return tuple(tuple(row) for row in grid)


def sample_input(seed: int, split: str, index: int, *, target_size: int | None = None) -> list[list[int]]:
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    _integer(seed, "seed", 0, 2**63 - 1)
    return [list(row) for row in _input_tuple(seed, split, index, target_size)]


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge

    _validate_grid(grid)
    own = bridge is None
    bridge = RacketBridge(timeout=60) if own else bridge
    try:
        value = bridge.eval_text(f"({wrap_rule(source)} {_datum(grid)})")
        _validate_grid(value)
        return value
    finally:
        if own:
            bridge.close()


def certify(
    episode: dict[str, Any],
    *,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("private program does not match selected setting")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode requires nonempty train and test lists")
    all_pairs = train + test
    try:
        input_ids = [digest(pair["input"]) for pair in all_pairs]
    except (KeyError, TypeError) as exc:
        raise ValueError("malformed pair") from exc
    if len(input_ids) != len(set(input_ids)):
        raise ValueError("all episode inputs must be distinct")

    def predict(candidate: dict[str, Any], grid: list[list[int]]) -> list[list[int]]:
        return transform(grid, candidate) if execute is None else execute(program(candidate), grid)

    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            try:
                observed = predict(selected, pair["input"])
            except (KeyError, TypeError) as exc:
                raise ValueError(f"malformed {split_name} pair {index}") from exc
            if observed != pair.get("output"):
                raise ValueError(f"label mismatch in {split_name} pair {index}")
    survivors = [
        dict(candidate)
        for candidate in SETTINGS
        if all(predict(candidate, pair["input"]) == pair["output"] for pair in train)
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")
    return {
        "survivors": survivors,
        "demo_only": True,
        "queries": [
            {"index": index, "output_sha256": digest(pair["output"])}
            for index, pair in enumerate(test)
        ],
    }


def generate(
    seed: int,
    settings: dict[str, Any] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", *QUERY_LIMITS)
    selected = _settings(settings, seed=seed)
    train_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    test_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    if len({digest(grid) for grid in train_inputs + test_inputs}) != demos + queries:
        raise ValueError("episode inputs must be distinct")
    episode = {
        "schema": f"{TASK_ID}-parametric-scan-order-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs],
        "program_solution": program(selected),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return json.loads(public_challenge_bytes(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, default=[])
    parser.add_argument("--match-order", choices=("first", "last"))
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    rows = list(SETTINGS) if args.all_settings else [{"match_order": args.match_order or "first"}]
    seeds = args.seed or [0]
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    private_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=60, max_calls_before_restart=256) as bridge:
        for selected in rows:
            for seed in seeds:
                episode = generate(seed, selected, args.demos, args.queries)
                certificate = certify(
                    episode,
                    execute=lambda source, grid: execute_rule(source, grid, bridge=bridge),
                )
                identifier = public_id(episode)
                if identifier in seen:
                    raise ValueError(f"duplicate public challenge {identifier}")
                seen.add(identifier)
                (public_dir / f"{identifier}.json").write_bytes(public_challenge_bytes(episode))
                private_rows.append(
                    {
                        "public_id": identifier,
                        "seed": seed,
                        "settings": selected,
                        "program_solution": episode["program_solution"],
                        "program_sha256": digest(episode["program_solution"]),
                        "query_outputs": [pair["output"] for pair in episode["test"]],
                        "certificate": certificate,
                    }
                )
        runtime = bridge.runtime_identity
    (args.out / "private.json").write_text(
        json.dumps(
            {
                "schema": f"{TASK_ID}-parametric-private-evidence-v1",
                "task_id": TASK_ID,
                "episodes": private_rows,
                "runtime": runtime,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    manifest = {
        "schema": "arcpuzzles-parametric-prototype-export-v1",
        "task_id": TASK_ID,
        "episode_count": len(private_rows),
        "public_ids": sorted(seen),
        "files": {
            str(path.relative_to(args.out)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(args.out.rglob("*"))
            if path.is_file()
        },
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "episodes": len(private_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
