"""Deterministic native parametric family for ARC task 4de2bae05c7d.

Step A is the exact canonical operation: recolor yellow four-connected exact
three-cell L components blue.  The two nondefault settings then recompute blue
components on that intermediate and recolor either the unique largest or unique
smallest whole component red.  Generated scenes force both ranks to change from
the original blue-component ranks, so ranking before step A is observably wrong.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
import copy
import hashlib
import json
import random
from typing import Any


MODES = ("canonical", "largest", "smallest")
L_ORIENTATIONS = ("missing_nw", "missing_ne", "missing_sw", "missing_se")
_SEMANTIC_ANCHOR_CYCLE = ("tl", "br", "center", "tr", "bl")
_L_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "missing_nw": ((0, 1), (1, 0), (1, 1)),
    "missing_ne": ((0, 0), (1, 0), (1, 1)),
    "missing_sw": ((0, 0), (0, 1), (1, 1)),
    "missing_se": ((0, 0), (0, 1), (1, 0)),
}
_L_BY_CELLS = {cells: name for name, cells in _L_SHAPES.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ALL8 = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
)

Grid = list[list[int]]
Cell = tuple[int, int]
ColoredCell = tuple[int, int, int]


def _derive_seed(seed: int, label: str) -> int:
    payload = f"4de2bae05c7d:{seed}:{label}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _rng(seed: int, label: str) -> random.Random:
    return random.Random(_derive_seed(seed, label))


def _normalize(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    values = tuple(cells)
    if not values:
        return ()
    r0 = min(row for row, _ in values)
    c0 = min(col for _, col in values)
    return tuple(sorted((row - r0, col - c0) for row, col in values))


def _normalize_motif(cells: Iterable[ColoredCell]) -> tuple[ColoredCell, ...]:
    values = tuple(cells)
    if not values:
        return ()
    r0 = min(row for row, _, _ in values)
    c0 = min(col for _, col, _ in values)
    return tuple(sorted((row - r0, col - c0, color) for row, col, color in values))


def _transform_motif(cells: Iterable[ColoredCell], code: int) -> tuple[ColoredCell, ...]:
    values = list(cells)
    if code >= 4:
        values = [(row, -col, color) for row, col, color in values]
    for _ in range(code % 4):
        values = [(col, -row, color) for row, col, color in values]
    return _normalize_motif(values)


def _motif_dims(cells: Iterable[ColoredCell]) -> tuple[int, int]:
    values = tuple(cells)
    return (
        max(row for row, _, _ in values) + 1,
        max(col for _, col, _ in values) + 1,
    )


def _staircase_with_diagonal_minimum(area: int) -> tuple[ColoredCell, ...]:
    if area not in (11, 13, 15):
        raise ValueError("staircase area must be 11, 13, or 15")
    side = (area + 1) // 2
    cells: list[ColoredCell] = []
    for index in range(side - 1):
        cells.append((index, index, 1))
        cells.append((index + 1, index, 1))
    cells.append((side - 1, side - 1, 1))
    # A separate size-three blue strip touches the staircase only diagonally.
    # Four-connectivity keeps it the unique smallest component after step A;
    # eight-connectivity merges it into the staircase and changes the largest.
    cells.extend((0, col, 1) for col in (2, 3, 4))
    return _normalize_motif(cells)


def _compact_blue_seed(area: int) -> set[Cell]:
    if area == 7:
        return {(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)}
    if area == 9:
        return {(row, col) for row in range(3) for col in range(3)}
    if area == 11:
        return {
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 0),
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 0),
            (2, 1),
            (2, 2),
            (2, 3),
        }
    raise ValueError("compact seed area must be 7, 9, or 11")


def _growing_rank_cluster(staircase_area: int) -> tuple[ColoredCell, ...]:
    seed_area = staircase_area - 4
    seed = _compact_blue_seed(seed_area)
    min_col = min(col for _, col in seed)
    max_col = max(col for _, col in seed)
    width = max_col - min_col + 1
    anchor_col = min_col + width // 2
    shifted = {(row + 2, col + 1) for row, col in seed}
    top_anchor = anchor_col + 1
    bottom_anchor = anchor_col + 1
    cells: list[ColoredCell] = [(row, col, 1) for row, col in shifted]
    # Two separate yellow Ls attach to the blue seed from opposite sides.
    cells.extend(
        [
            (0, top_anchor - 1, 4),
            (0, top_anchor, 4),
            (1, top_anchor, 4),
            (5, bottom_anchor, 4),
            (6, bottom_anchor, 4),
            (6, bottom_anchor + 1, 4),
        ]
    )
    return _normalize_motif(cells)


def _small_rank_flip_cluster() -> tuple[ColoredCell, ...]:
    # The original blue singleton is smallest. Two four-disconnected yellow Ls
    # touch one another only diagonally while both attach to that singleton.
    # Step A therefore creates one seven-cell blue component, making the
    # separate size-three strip the new smallest and simultaneously teaching
    # four- versus eight-neighbor yellow connectivity.
    return _normalize_motif(
        (
            (2, 2, 1),
            (0, 1, 4),
            (1, 1, 4),
            (1, 2, 4),
            (2, 3, 4),
            (3, 3, 4),
            (3, 4, 4),
        )
    )


def _line(color: int, length: int) -> tuple[ColoredCell, ...]:
    return tuple((0, col, color) for col in range(length))


def _square(color: int, side: int = 2) -> tuple[ColoredCell, ...]:
    return tuple((row, col, color) for row in range(side) for col in range(side))


def _l_decoy(color: int) -> tuple[ColoredCell, ...]:
    return ((0, 0, color), (0, 1, color), (1, 0, color))


def _zigzag(color: int, length: int = 5) -> tuple[ColoredCell, ...]:
    path: list[ColoredCell] = []
    row = col = 0
    path.append((row, col, color))
    for index in range(1, length):
        if index % 2:
            col += 1
        else:
            row += 1
        path.append((row, col, color))
    return tuple(path)


def _candidate_positions(
    h: int,
    w: int,
    cells: tuple[ColoredCell, ...],
    *,
    edge: bool,
    interior: bool,
    anchor: str,
    rng: random.Random,
) -> list[tuple[int, int]]:
    mh, mw = _motif_dims(cells)
    candidates: list[tuple[int, int]] = []
    for row0 in range(h - mh + 1):
        for col0 in range(w - mw + 1):
            touches_edge = row0 == 0 or col0 == 0 or row0 + mh == h or col0 + mw == w
            if edge and not touches_edge:
                continue
            if interior and touches_edge:
                continue
            candidates.append((row0, col0))
    rng.shuffle(candidates)
    targets = {
        "tl": (0, 0),
        "tr": (0, max(0, w - mw)),
        "bl": (max(0, h - mh), 0),
        "br": (max(0, h - mh), max(0, w - mw)),
        "center": (max(0, (h - mh) // 2), max(0, (w - mw) // 2)),
    }
    target = targets[anchor]
    candidates.sort(key=lambda pos: abs(pos[0] - target[0]) + abs(pos[1] - target[1]))
    return candidates


def _can_place(cells: Iterable[Cell], occupied: set[Cell]) -> bool:
    cells = tuple(cells)
    if any(cell in occupied for cell in cells):
        return False
    # An eight-neighbor moat prevents accidental cross-motif mergers.  The
    # deliberate diagonal merger rival lives wholly inside the A+D motif.
    return all(
        (row + drow, col + dcol) not in occupied
        for row, col in cells
        for drow, dcol in _ALL8
    )


def _pack(h: int, w: int, motifs: list[dict[str, Any]], rng: random.Random) -> Grid:
    prepared = []
    for index, motif in enumerate(motifs):
        cells = _transform_motif(motif["cells"], motif["transform"])
        positions = _candidate_positions(
            h,
            w,
            cells,
            edge=bool(motif.get("edge")),
            interior=bool(motif.get("interior")),
            anchor=motif.get("anchor", "center"),
            rng=rng,
        )
        prepared.append((index, motif, cells, positions))
    prepared.sort(
        key=lambda item: (
            not bool(item[1].get("edge")),
            -(_motif_dims(item[2])[0] * _motif_dims(item[2])[1]),
            -len(item[2]),
            item[0],
        )
    )
    grid = [[0 for _ in range(w)] for _ in range(h)]
    occupied: set[Cell] = set()
    nodes = 0

    def search(depth: int) -> bool:
        nonlocal nodes
        if depth == len(prepared):
            return True
        _, _, motif_cells, positions = prepared[depth]
        for row0, col0 in positions:
            nodes += 1
            if nodes > 750_000:
                return False
            absolute = tuple((row0 + row, col0 + col) for row, col, _ in motif_cells)
            if not _can_place(absolute, occupied):
                continue
            occupied.update(absolute)
            for row, col, color in motif_cells:
                grid[row0 + row][col0 + col] = color
            if search(depth + 1):
                return True
            for row, col, _ in motif_cells:
                grid[row0 + row][col0 + col] = 0
            occupied.difference_update(absolute)
        return False

    if not search(0):
        raise ValueError(f"could not pack {len(motifs)} motifs on {h}x{w}")
    return grid


def _profile_spec(role: str, rng: random.Random) -> tuple[int, int, bool, int]:
    if role == "minimum":
        return 15, 15, False, 2
    if role == "boundary":
        return 20, 20, True, 5
    if role == "wide":
        return 15, 30, False, 7
    if role == "tall":
        return 30, 15, False, 7
    if role == "dense":
        return 30, 30, True, 16
    if role == "standard":
        side = rng.choice((18, 19, 21, 22))
        return side, side + rng.choice((-1, 0, 1)), False, 5
    raise ValueError(f"unknown role: {role}")


def _extra_motifs(count: int, rng: random.Random, start_transform: int) -> list[dict[str, Any]]:
    palette = [3, 5, 6, 7, 8, 9]
    motifs: list[dict[str, Any]] = [
        {
            "name": "yellow-non-l",
            # A straight yellow triomino is the minimum witness that
            # distinguishes exact L-shape recognition from a size-only rule.
            "cells": _line(4, 3),
            "transform": start_transform % 8,
            "anchor": "br",
        },
        {
            "name": "colored-l",
            "cells": _l_decoy(rng.choice(palette)),
            "transform": (start_transform + 1) % 8,
            "anchor": "br",
        },
    ]
    anchors = ("tl", "tr", "bl", "br", "center")
    for index in range(max(0, count - 2)):
        color = rng.choice((2, 3, 5, 6, 7, 8, 9, 4))
        shape_kind = index % 4
        if color == 4:
            # Never create another exact yellow L target.
            cells = _line(4, 2 + (index % 4)) if index % 2 else _square(4, 2)
        elif shape_kind == 0:
            cells = _line(color, 2 + (index % 4))
        elif shape_kind == 1:
            cells = _square(color, 2)
        elif shape_kind == 2:
            cells = _zigzag(color, 4 + (index % 3))
        else:
            cells = _l_decoy(color)
        motifs.append(
            {
                "name": f"extra-{index}",
                "cells": cells,
                "transform": (start_transform + 2 + index) % 8,
                "anchor": anchors[index % len(anchors)],
            }
        )
    return motifs


def _generate_scene(seed: int, role: str, ordinal: int, phase: str) -> Grid:
    rng = _rng(seed, f"{phase}:{ordinal}:{role}")
    h, w, boundary, extra_count = _profile_spec(role, rng)
    staircase_area = (11, 13, 15)[(seed + ordinal + (0 if phase == "demo" else 1)) % 3]
    transform_base = (ordinal * 3 + (seed % 8)) % 8
    anchor_offset = _derive_seed(seed, f"{phase}:semantic-anchor-cycle") % len(
        _SEMANTIC_ANCHOR_CYCLE
    )
    semantic_anchors = tuple(
        _SEMANTIC_ANCHOR_CYCLE[(anchor_offset + ordinal + shift) % len(_SEMANTIC_ANCHOR_CYCLE)]
        for shift in (0, 2, 4)
    )
    motifs: list[dict[str, Any]] = [
        {
            "name": "sparse-largest-original-plus-diagonal-smallest",
            "cells": _staircase_with_diagonal_minimum(staircase_area),
            "transform": transform_base,
            "anchor": semantic_anchors[0],
            "edge": boundary,
        },
        {
            "name": "growing-largest-after-a",
            "cells": _growing_rank_cluster(staircase_area),
            "transform": (transform_base + 1 + ordinal) % 8,
            "anchor": semantic_anchors[1],
        },
        {
            "name": "original-smallest-grows-after-a",
            "cells": _small_rank_flip_cluster(),
            "transform": (transform_base + 2 + 2 * ordinal) % 8,
            "anchor": semantic_anchors[2],
        },
    ]
    motifs.extend(_extra_motifs(extra_count, rng, transform_base + 3))
    if role == "standard":
        for motif in motifs:
            motif["interior"] = True
    grid = _pack(h, w, motifs, rng)
    errors = validate_scene(grid)
    if errors:
        raise ValueError(f"constructed invalid scene for {role}: {errors}")
    return grid


def _validate_grid(grid: Any) -> list[str]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return ["grid must contain 1..30 rows"]
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        return ["grid rows must contain 1..30 cells"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular lists"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integers 0..9"]
    return []


def _components(grid: Grid, color: int | None = None, *, connectivity: int = 4) -> list[dict[str, Any]]:
    deltas = _CARDINAL if connectivity == 4 else _ALL8
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            value = grid[row][col]
            if value == 0 or (color is not None and value != color) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            ordered = tuple(sorted(cells))
            normalized = _normalize(ordered)
            r0 = min(r for r, _ in ordered)
            c0 = min(c for _, c in ordered)
            r1 = max(r for r, _ in ordered)
            c1 = max(c for _, c in ordered)
            result.append(
                {
                    "color": value,
                    "cells": ordered,
                    "size": len(ordered),
                    "normalized": normalized,
                    "orientation": _L_BY_CELLS.get(normalized),
                    "bbox": (r0, c0, r1, c1),
                    "bbox_area": (r1 - r0 + 1) * (c1 - c0 + 1),
                }
            )
    return result


def _paint(grid: Grid, cells: Iterable[Cell], color: int) -> Grid:
    out = [row[:] for row in grid]
    for row, col in cells:
        out[row][col] = color
    return out


def canonical_stage(grid: Grid) -> Grid:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    out = [row[:] for row in grid]
    for component in _components(grid, 4, connectivity=4):
        if component["size"] == 3 and component["orientation"] is not None:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _ranked_blue(grid: Grid, rank: str, *, connectivity: int = 4, key: str = "size"):
    blue = _components(grid, 1, connectivity=connectivity)
    if not blue:
        return None
    chooser = max if rank == "largest" else min
    return chooser(blue, key=lambda component: component[key])


def apply_mode(grid: Grid, mode: str) -> Grid:
    if mode not in MODES:
        raise ValueError(f"unknown postprocess mode: {mode!r}")
    stage = canonical_stage(grid)
    if mode == "canonical":
        return stage
    selected = _ranked_blue(stage, mode)
    return stage if selected is None else _paint(stage, selected["cells"], 2)


def rank_original_then_recolor(grid: Grid, rank: str) -> Grid:
    if rank not in ("largest", "smallest"):
        raise ValueError(rank)
    selected = _ranked_blue(grid, rank)
    stage = canonical_stage(grid)
    return stage if selected is None else _paint(stage, selected["cells"], 2)


def rank_after_bbox(grid: Grid, rank: str) -> Grid:
    stage = canonical_stage(grid)
    selected = _ranked_blue(stage, rank, key="bbox_area")
    return stage if selected is None else _paint(stage, selected["cells"], 2)


def rank_after_eight_connectivity(grid: Grid, rank: str) -> Grid:
    stage = canonical_stage(grid)
    selected = _ranked_blue(stage, rank, connectivity=8)
    return stage if selected is None else _paint(stage, selected["cells"], 2)


def recolor_only_new_targets(grid: Grid, rank: str) -> Grid:
    stage = canonical_stage(grid)
    selected = _ranked_blue(stage, rank)
    if selected is None:
        return stage
    new_cells = [cell for cell in selected["cells"] if grid[cell[0]][cell[1]] == 4]
    return _paint(stage, new_cells, 2)


def _all_yellow(grid: Grid) -> Grid:
    return [[1 if cell == 4 else cell for cell in row] for row in grid]


def _yellow_size_three(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    for component in _components(grid, 4):
        if component["size"] == 3:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _all_l_any_color(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    for component in _components(grid):
        if component["size"] == 3 and component["orientation"] is not None:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _yellow_l_eight(grid: Grid) -> Grid:
    out = [row[:] for row in grid]
    for component in _components(grid, 4, connectivity=8):
        if component["size"] == 3 and component["orientation"] is not None:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _fixed_top_left_blue(grid: Grid, rank: str) -> Grid:
    del rank
    stage = canonical_stage(grid)
    blue = _components(stage, 1)
    return stage if not blue else _paint(stage, blue[0]["cells"], 2)


def _positional_blue(grid: Grid, direction: str) -> Grid:
    stage = canonical_stage(grid)
    blue = _components(stage, 1)
    if not blue:
        return stage
    selectors = {
        "topmost": lambda component: (component["bbox"][0], component["bbox"][1]),
        "bottommost": lambda component: (-component["bbox"][2], component["bbox"][1]),
        "leftmost": lambda component: (component["bbox"][1], component["bbox"][0]),
        "rightmost": lambda component: (-component["bbox"][3], component["bbox"][0]),
    }
    if direction not in selectors:
        raise ValueError(direction)
    selected = min(blue, key=selectors[direction])
    return _paint(stage, selected["cells"], 2)


RIVALS: dict[str, dict[str, Callable[[Grid], Grid]]] = {
    "canonical": {
        "recolor every yellow cell": _all_yellow,
        "recolor every yellow size-three component": _yellow_size_three,
        "recolor every L regardless of color": _all_l_any_color,
        "use eight-neighbor yellow components": _yellow_l_eight,
    },
    "largest": {
        "skip step B": canonical_stage,
        "rank original blue components": lambda grid: rank_original_then_recolor(grid, "largest"),
        "rank post-step bounding boxes": lambda grid: rank_after_bbox(grid, "largest"),
        "use eight-neighbor post-step blue components": lambda grid: rank_after_eight_connectivity(grid, "largest"),
        "recolor only the newly blue target cells": lambda grid: recolor_only_new_targets(grid, "largest"),
        "paint the first blue component": lambda grid: _fixed_top_left_blue(grid, "largest"),
        "select topmost post-step blue component": lambda grid: _positional_blue(grid, "topmost"),
        "select bottommost post-step blue component": lambda grid: _positional_blue(grid, "bottommost"),
        "select leftmost post-step blue component": lambda grid: _positional_blue(grid, "leftmost"),
        "select rightmost post-step blue component": lambda grid: _positional_blue(grid, "rightmost"),
    },
    "smallest": {
        "skip step B": canonical_stage,
        "rank original blue components": lambda grid: rank_original_then_recolor(grid, "smallest"),
        "use eight-neighbor post-step blue components": lambda grid: rank_after_eight_connectivity(grid, "smallest"),
        "recolor only the newly blue target cells": lambda grid: recolor_only_new_targets(grid, "smallest"),
        "paint the first blue component": lambda grid: _fixed_top_left_blue(grid, "smallest"),
        "select topmost post-step blue component": lambda grid: _positional_blue(grid, "topmost"),
        "select bottommost post-step blue component": lambda grid: _positional_blue(grid, "bottommost"),
        "select leftmost post-step blue component": lambda grid: _positional_blue(grid, "leftmost"),
        "select rightmost post-step blue component": lambda grid: _positional_blue(grid, "rightmost"),
    },
}


def _component_id(component: dict[str, Any] | None):
    return None if component is None else component["cells"]


def scene_facts(grid: Grid) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    original_blue = _components(grid, 1)
    stage = canonical_stage(grid)
    post_blue = _components(stage, 1)
    post_blue8 = _components(stage, 1, connectivity=8)
    targets = [
        component
        for component in _components(grid, 4)
        if component["size"] == 3 and component["orientation"] is not None
    ]
    nonzero = [(row, col) for row in range(h) for col in range(w) if grid[row][col] != 0]
    touches = any(row in (0, h - 1) or col in (0, w - 1) for row, col in nonzero)
    if h == w == 30:
        profile = "dense"
    elif (h, w) == (15, 30):
        profile = "wide"
    elif (h, w) == (30, 15):
        profile = "tall"
    elif h == w == 15:
        profile = "minimum"
    elif touches:
        profile = "boundary"
    else:
        profile = "standard"
    return {
        "errors": [],
        "height": h,
        "width": w,
        "profile": profile,
        "touches_boundary": touches,
        "nonzero": len(nonzero),
        "row_span": 0 if not nonzero else max(r for r, _ in nonzero) - min(r for r, _ in nonzero) + 1,
        "col_span": 0 if not nonzero else max(c for _, c in nonzero) - min(c for _, c in nonzero) + 1,
        "target_count": len(targets),
        "target_orientations": sorted(component["orientation"] for component in targets),
        "original_blue_sizes": sorted(component["size"] for component in original_blue),
        "post_blue_sizes": sorted(component["size"] for component in post_blue),
        "original_largest_blue": _component_id(max(original_blue, key=lambda x: x["size"])),
        "original_smallest_blue": _component_id(min(original_blue, key=lambda x: x["size"])),
        "post_largest_blue": _component_id(max(post_blue, key=lambda x: x["size"])),
        "post_smallest_blue": _component_id(min(post_blue, key=lambda x: x["size"])),
        "post_largest_bbox_blue": _component_id(max(post_blue, key=lambda x: x["bbox_area"])),
        "post_largest_blue_8": _component_id(max(post_blue8, key=lambda x: x["size"])),
        "yellow_non_l_count": sum(
            1
            for component in _components(grid, 4)
            if not (component["size"] == 3 and component["orientation"] is not None)
        ),
        "colored_l_count": sum(
            1
            for component in _components(grid)
            if component["color"] not in (1, 4)
            and component["size"] == 3
            and component["orientation"] is not None
        ),
    }


def validate_scene(grid: Grid) -> list[str]:
    errors = _validate_grid(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (15 <= h <= 30 and 15 <= w <= 30):
        errors.append("parametric scene dimensions must be 15..30")
        return errors
    facts = scene_facts(grid)
    if facts["target_count"] != 4:
        errors.append(f"expected exactly four yellow L targets, found {facts['target_count']}")
    if set(facts["target_orientations"]) - set(L_ORIENTATIONS):
        errors.append("unknown L orientation")
    if facts["yellow_non_l_count"] < 1:
        errors.append("missing yellow non-L decoy")
    if facts["colored_l_count"] < 1:
        errors.append("missing non-yellow L decoy")
    if len(facts["original_blue_sizes"]) != 4 or len(set(facts["original_blue_sizes"])) != 4:
        errors.append(f"expected four uniquely sized original blue components, got {facts['original_blue_sizes']}")
    if len(facts["post_blue_sizes"]) != 4 or len(set(facts["post_blue_sizes"])) != 4:
        errors.append(f"expected four uniquely sized post-step blue components, got {facts['post_blue_sizes']}")
    if facts["original_largest_blue"] == facts["post_largest_blue"]:
        errors.append("largest blue component did not change after step A")
    if facts["original_smallest_blue"] == facts["post_smallest_blue"]:
        errors.append("smallest blue component did not change after step A")
    if facts["post_largest_blue"] == facts["post_largest_bbox_blue"]:
        errors.append("largest-area and largest-bbox rivals were not separated")
    if facts["post_largest_blue"] == facts["post_largest_blue_8"]:
        errors.append("four- and eight-connected post-step largest components were not separated")
    return errors


def lesson_identifiable(demos: list[dict[str, Grid]], query_input: Grid, mode: str) -> list[str]:
    if mode not in MODES:
        return [f"unknown mode {mode!r}"]
    if type(demos) is not list or len(demos) < 3:
        return ["at least three demonstrations are required"]
    reasons: list[str] = []
    orientations: set[str] = set()
    demo_keys: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = validate_scene(pair["input"])
        if errors:
            reasons.append(f"demo {index} is invalid: {errors[0]}")
            continue
        key = grid_key(pair["input"])
        if key in demo_keys:
            reasons.append(f"demo {index} duplicates an earlier input")
        demo_keys.add(key)
        expected = apply_mode(pair["input"], mode)
        if pair["output"] != expected:
            reasons.append(f"demo {index} output is mislabeled")
        orientations.update(scene_facts(pair["input"])["target_orientations"])
    query_errors = validate_scene(query_input)
    if query_errors:
        reasons.append(f"query is invalid: {query_errors[0]}")
    elif grid_key(query_input) in demo_keys:
        reasons.append("query duplicates a demonstration input")
    if reasons:
        return reasons
    if orientations != set(L_ORIENTATIONS):
        reasons.append(f"demonstrations omit L orientations {sorted(set(L_ORIENTATIONS) - orientations)}")
    truth = apply_mode(query_input, mode)
    for name, rival in RIVALS[mode].items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query_input) != truth:
                reasons.append(f"demos remain compatible with rival {name!r}")
    return reasons


def grid_key(grid: Grid) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _validate_request(seed: int, mode: str, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2^63-1")
    if mode not in MODES:
        raise ValueError(f"unknown postprocess mode: {mode!r}")
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 3..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")


def generate_episode(seed: int, mode: str, demos: int, queries: int) -> dict[str, Any]:
    _validate_request(seed, mode, demos, queries)
    demo_roles = ["minimum", "boundary", "standard", "wide", "tall", "dense"]
    query_roles = ["minimum", "boundary", "dense", "wide" if seed % 2 == 0 else "tall"]
    _rng(seed, "demo-role-order").shuffle(demo_roles)
    _rng(seed, "query-role-order").shuffle(query_roles)
    inputs: list[Grid] = []
    pairs: list[dict[str, Grid]] = []
    for phase, count, roles in (("demo", demos, demo_roles), ("query", queries, query_roles)):
        for ordinal in range(count):
            role = roles[ordinal]
            grid = _generate_scene(seed, role, ordinal, phase)
            key = grid_key(grid)
            if key in {grid_key(existing) for existing in inputs}:
                raise ValueError("duplicate generated input")
            inputs.append(grid)
            pairs.append({"input": grid, "output": apply_mode(grid, mode)})
    train = copy.deepcopy(pairs[:demos])
    test = copy.deepcopy(pairs[demos:])
    return {"train": train, "test": test}
