"""Native parametric family for 4dd0b3ed33ee.

The canonical setting preserves the selected authority byte-for-byte: count
blue header markers, scan same-colour body objects in row-major order, choose
the first object with that many 4-connected enclosed background regions, and
return its tight cyan boundary crop.

The alternate setting keeps the same topology filter as stage A but chooses the
unique largest occupied-area member of that input-dependent candidate set
before applying the same boundary renderer.  Inputs are shared across settings.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "4dd0b3ed33ee"
DEFAULT = {"match_selector": "first"}
PARAMETERS = {"match_selector": ["first", "largest_area"]}
SETTINGS = [
    {"match_selector": "first"},
    {"match_selector": "largest_area"},
]
_PROGRAM_FILES = {
    "first": HERE / "canonical.rkt",
    "largest_area": HERE / "largest_area.rkt",
}

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
Shape = tuple[tuple[int, int], ...]

# k, grid height, grid width, top order, middle order, leftmost cue, stress.
# The first two entries are deliberately crossed: lesson zero puts the
# canonical winner to the right while lesson one puts it at the far left; the
# largest-area winner also changes from second to third matching rank.
_DEMO_PROFILES = (
    (1, 29, 28, "AB", "CD", "C", False),
    (2, 25, 30, "BA", "DC", "B", False),
    (3, 28, 29, "AB", "DC", "D", False),
    (1, 24, 27, "BA", "CD", "B", False),
    (2, 26, 29, "AB", "CD", "C", False),
    (3, 29, 30, "BA", "DC", "B", False),
)
_QUERY_PROFILES = (
    (2, 25, 28, "AB", "DC", "D", False),
    (3, 28, 30, "BA", "CD", "B", False),
    (1, 24, 29, "AB", "CD", "C", False),
    (3, 30, 30, "BA", "DC", "C", True),
)

_COLOR_PATTERNS = (
    {"A": 7, "B": 5, "C": 2, "D": 9, "F": 4},
    {"A": 6, "B": 2, "C": 9, "D": 5, "F": 3},
    {"A": 4, "B": 9, "C": 5, "D": 2, "F": 7},
    {"A": 3, "B": 7, "C": 4, "D": 9, "F": 2},
    {"A": 5, "B": 4, "C": 7, "D": 2, "F": 9},
    {"A": 9, "B": 3, "C": 6, "D": 7, "F": 2},
)


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"match_selector"}:
        raise ValueError("settings must name exactly match_selector")
    value = settings["match_selector"]
    if type(value) is not str or value not in PARAMETERS["match_selector"]:
        raise ValueError("match_selector must be first or largest_area")
    return {"match_selector": value}


def program(settings: object) -> str:
    chosen = _settings(settings)
    return _PROGRAM_FILES[chosen["match_selector"]].read_text(encoding="utf-8")


def _grid(value: object) -> list[list[int]]:
    if type(value) is not list or not 2 <= len(value) <= 30:
        raise ValueError("grid must have 2..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return value


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must be nonempty")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _boundary(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cell_set = set(cells)
    return tuple(
        sorted(
            (r, c)
            for r, c in cell_set
            if any((r + dr, c + dc) not in cell_set for dr, dc in _CARD)
        )
    )


def _hole_count(cells: Iterable[tuple[int, int]], connectivity: int = 4) -> int:
    cell_set = set(cells)
    if not cell_set:
        return 0
    r0, r1 = min(r for r, _ in cell_set), max(r for r, _ in cell_set)
    c0, c1 = min(c for _, c in cell_set), max(c for _, c in cell_set)
    background = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cell_set
    }
    deltas = _CARD if connectivity == 4 else _EIGHT
    seen: set[tuple[int, int]] = set()
    holes = 0
    for start in sorted(background):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        touches_edge = False
        while queue:
            r, c = queue.popleft()
            if r in (r0, r1) or c in (c0, c1):
                touches_edge = True
            for dr, dc in deltas:
                nxt = (r + dr, c + dc)
                if nxt in background and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if not touches_edge:
            holes += 1
    return holes


def _output(cells: Iterable[tuple[int, int]], *, whole: bool = False) -> list[list[int]]:
    local = _normalize(cells)
    h, w = _dims(local)
    result = [[0 for _ in range(w)] for _ in range(h)]
    painted = local if whole else _boundary(local)
    for r, c in painted:
        result[r][c] = 8
    return result


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for r0 in range(1, h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color in (0, 1) or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells_t = tuple(sorted(cells))
            local = _normalize(cells_t)
            rows = [r for r, _ in cells_t]
            cols = [c for _, c in cells_t]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            result.append(
                {
                    "color": color,
                    "cells": cells_t,
                    "local": local,
                    "bbox": bbox,
                    "height": bbox[2] - bbox[0] + 1,
                    "width": bbox[3] - bbox[1] + 1,
                    "bbox_area": (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1),
                    "area": len(cells_t),
                    "boundary": _boundary(cells_t),
                    "boundary_size": len(_boundary(cells_t)),
                    "holes": _hole_count(local, 4),
                    "holes8": _hole_count(local, 8),
                    "missing_cells": (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1) - len(cells_t),
                    "output": _output(local),
                    "whole_output": _output(local, whole=True),
                }
            )
    result.sort(key=lambda obj: min(obj["cells"]))
    return result


def _analysis(grid: list[list[int]], *, connectivity: int = 4, missing: bool = False):
    grid = _grid(grid)
    k = sum(value == 1 for value in grid[0])
    objects = _components(grid)
    if missing:
        matches = [obj for obj in objects if obj["missing_cells"] == k]
    elif connectivity == 8:
        matches = [obj for obj in objects if obj["holes8"] == k]
    else:
        matches = [obj for obj in objects if obj["holes"] == k]
    return k, objects, matches


def _choose(matches: list[dict[str, object]], chosen: dict[str, str]):
    if not matches:
        raise ValueError("no body object matches the header topology")
    if chosen["match_selector"] == "first":
        return matches[0]
    return max(matches, key=lambda obj: int(obj["area"]))


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)
    _, _, matches = _analysis(grid)
    return copy.deepcopy(_choose(matches, chosen)["output"])


def scene_summary(grid: list[list[int]]) -> dict[str, object]:
    k, objects, matches = _analysis(grid)
    if not matches:
        raise ValueError("scene has no matching objects")
    indices = [objects.index(obj) for obj in matches]
    largest_area = max(matches, key=lambda obj: int(obj["area"]))
    largest_boundary = max(matches, key=lambda obj: int(obj["boundary_size"]))
    smallest = min(matches, key=lambda obj: int(obj["area"]))
    largest_overall = max(objects, key=lambda obj: int(obj["area"]))
    return {
        "header_count": k,
        "component_count": len(objects),
        "matching_count": len(matches),
        "matching_indices": indices,
        "first_match_index": indices[0],
        "last_match_index": indices[-1],
        "largest_area_match_index": objects.index(largest_area),
        "largest_boundary_match_index": objects.index(largest_boundary),
        "smallest_area_match_index": objects.index(smallest),
        "largest_overall_index": objects.index(largest_overall),
        "components": [
            {
                "index": i,
                "color": int(obj["color"]),
                "bbox": list(obj["bbox"]),
                "area": int(obj["area"]),
                "boundary_size": int(obj["boundary_size"]),
                "bbox_area": int(obj["bbox_area"]),
                "holes4": int(obj["holes"]),
                "holes8": int(obj["holes8"]),
                "missing_cells": int(obj["missing_cells"]),
            }
            for i, obj in enumerate(objects)
        ],
    }


def boundary_contacts(grid: list[list[int]]) -> set[str]:
    grid = _grid(grid)
    h, w = len(grid), len(grid[0])
    occupied = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    contacts: set[str] = set()
    if any(r == 1 for r, _ in occupied):
        contacts.add("top")
    if any(r == h - 1 for r, _ in occupied):
        contacts.add("bottom")
    if any(c == 0 for _, c in occupied):
        contacts.add("left")
    if any(c == w - 1 for _, c in occupied):
        contacts.add("right")
    return contacts


def _reflect_shape(shape: Shape, *, horizontal: bool, vertical: bool) -> Shape:
    h, w = _dims(shape)
    return _normalize(
        (
            (h - 1 - r if vertical else r),
            (w - 1 - c if horizontal else c),
        )
        for r, c in shape
    )


def _transpose_shape(shape: Shape) -> Shape:
    return _normalize((c, r) for r, c in shape)


def _dense_shape(k: int, h: int, w: int, variant: int = 0) -> Shape:
    """Filled object with k holes, including a multi-cell primary hole."""
    variant %= 3
    if variant == 0:
        primary = {(r, c) for r in (1, 2) for c in (1, 2)}
        diagonal = (3, 3)
    elif variant == 1:
        primary = {(r, c) for r in (1, 2) for c in (1, 2, 3)}
        diagonal = (3, 4)
    else:
        primary = {(1, c) for c in (1, 2, 3, 4)}
        diagonal = (2, 5)
    removed = set(primary)
    if k >= 2:
        # Separate under 4-connectivity but joined diagonally under 8-connectivity.
        removed.add(diagonal)
    if k >= 3:
        removed.add((h - 2, w - 2))
    if any(not (0 < r < h - 1 and 0 < c < w - 1) for r, c in removed):
        raise AssertionError((k, h, w, variant, removed))
    cells = {(r, c) for r in range(h) for c in range(w)} - removed
    shape = _normalize(cells)
    if _hole_count(shape, 4) != k:
        raise AssertionError(f"dense shape topology drifted for k={k}, variant={variant}")
    return shape


def _single_cell_holes(k: int, h: int, w: int, variant: int = 0) -> Shape:
    """Compact rival with exactly k isolated one-cell holes."""
    positions = {
        1: [(1, 1)],
        2: [(1, 1), (h - 2, w - 2)],
        3: [(1, 1), (1, w - 2), (h - 2, w // 2)],
    }[k]
    cells = {(r, c) for r in range(h) for c in range(w)} - set(positions)
    shape = _normalize(cells)
    if _hole_count(shape, 4) != k or _hole_count(shape, 8) != k:
        raise AssertionError((k, h, w, positions))
    return shape


def _partition_frame(k: int, h: int, w: int, variant: int = 0) -> Shape:
    cells = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    }
    # Unequal separator positions vary the motif without changing the number of
    # enclosed regions or its deliberately large boundary.
    for index in range(1, k):
        base = round(index * (w - 1) / k)
        shift = (-1, 0, 1)[(variant + index) % 3]
        col = min(w - 2, max(1, base + shift))
        for row in range(1, h - 1):
            cells.add((row, col))
    shape = _normalize(cells)
    if _hole_count(shape, 4) != k:
        raise AssertionError(f"partition frame topology drifted for k={k}")
    return shape


def _large_single_hole(variant: int = 0) -> Shape:
    """8x9 one-hole object: largest by area but not by density/interior."""
    h, w = 8, 9
    patterns = (
        {
            (1, 3), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
            (4, 3), (4, 4), (4, 5), (4, 6),
            (5, 2), (5, 3), (5, 4), (5, 5), (5, 6),
        },
        {
            (2, 1), (2, 4), (3, 1), (3, 2), (3, 4), (3, 6),
            (4, 2), (4, 3), (4, 4), (4, 6),
            (5, 2), (5, 3), (5, 4), (5, 5), (5, 6),
            (6, 2), (6, 3), (6, 4), (6, 5), (6, 6),
        },
        {
            (1, 2), (2, 2), (2, 3),
            (3, 1), (3, 2), (3, 3), (3, 5), (3, 6), (3, 7),
            (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (5, 2), (5, 3), (5, 4), (5, 5), (5, 6),
            (6, 5),
        },
    )
    removed = patterns[variant % len(patterns)]
    shape = _normalize({(r, c) for r in range(h) for c in range(w)} - removed)
    if len(shape) != 52 or _hole_count(shape, 4) != 1 or len(_boundary(shape)) < 46:
        raise AssertionError((variant, len(shape), _hole_count(shape, 4), len(_boundary(shape))))
    return shape

def _special_boundary_rival(variant: int = 0) -> Shape:
    """13x14 one-hole frame with a one-cell inward tooth."""
    h, w = 13, 14
    cells = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    }
    cells.add((1, 2 + variant % (w - 4)))
    shape = _normalize(cells)
    if len(shape) != 51 or _hole_count(shape, 4) != 1:
        raise AssertionError((variant, len(shape), _hole_count(shape, 4)))
    return shape


def _shapes(k: int, variant: int = 0, *, special: bool = False) -> dict[str, Shape]:
    dense_dims = {
        1: ((6, 7), (7, 8)),
        2: ((7, 8), (8, 9)),
        3: ((8, 9), (9, 10)),
    }
    wrong_dims = {1: (8, 8), 2: (9, 9), 3: (10, 10)}
    wide_dims = {1: (8, 13), 2: (8, 13), 3: (9, 13)}
    small_dims = {1: (4, 4), 2: (5, 5), 3: (6, 6)}
    bh, ch = dense_dims[k]
    if special:
        if k != 1:
            raise ValueError("special profile is defined only for k=1")
        result = {
            "A": tuple((r, c) for r in range(9) for c in range(9)),
            "B": _dense_shape(1, *bh, variant=variant),
            "C": _large_single_hole(variant),
            "D": _special_boundary_rival(variant),
            "F": _single_cell_holes(1, *small_dims[1], variant=variant),
        }
    else:
        result = {
            "A": tuple((r, c) for r in range(wrong_dims[k][0]) for c in range(wrong_dims[k][1])),
            "B": _dense_shape(k, *bh, variant=variant),
            "C": _dense_shape(k, *ch, variant=(variant + 1) % 3),
            "D": _partition_frame(k, *wide_dims[k], variant=variant),
            "F": _single_cell_holes(k, *small_dims[k], variant=variant),
        }
    areas = {name: len(shape) for name, shape in result.items()}
    boundaries = {name: len(_boundary(shape)) for name, shape in result.items()}
    if not (
        areas["A"] > areas["C"]
        and areas["C"] > max(areas["B"], areas["D"], areas["F"])
        and areas["B"] > areas["F"]
    ):
        raise AssertionError((k, variant, special, areas))
    if not (boundaries["D"] > boundaries["C"]):
        raise AssertionError((k, variant, special, boundaries))
    if (max(_dims(result["C"])) > 30) or (max(_dims(result["D"])) > 30):
        raise AssertionError("shape exceeds ARC bounds")
    return result

def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _place(grid: list[list[int]], shape: Shape, row: int, col: int, color: int) -> None:
    for dr, dc in shape:
        rr, cc = row + dr, col + dc
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("shape placement out of bounds")
        if grid[rr][cc] != 0:
            raise ValueError("shape placement collision")
        grid[rr][cc] = color


def _pair_positions(
    left_name: str,
    right_name: str,
    shapes: dict[str, Shape],
    width: int,
    rng: random.Random,
    *,
    anchor: str | None = None,
    touch_right: bool = False,
) -> dict[str, int]:
    lw = _dims(shapes[left_name])[1]
    rw = _dims(shapes[right_name])[1]
    needed = lw + 1 + rw
    slack = width - needed
    if slack < 0:
        raise ValueError("pair does not fit")
    if touch_right:
        lead = slack
    elif anchor == left_name:
        lead = 0
    elif anchor == right_name:
        # Put the requested object at the left edge by swapping is handled by
        # the caller; for a right-hand anchor use the smallest legal lead.
        lead = 0
    else:
        lead = rng.randrange(slack + 1)
    return {left_name: lead, right_name: lead + lw + 1}


def _stable_choice(seed: int, split: str, index: int, label: str, modulus: int) -> int:
    payload = json.dumps([TASK_ID, seed, split, index, label], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(payload).digest(), "big") % modulus


def _build_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(profiles) - 1, "index")
    k, height, width, _top_hint, _middle_hint, _left_hint, stress = profiles[index]
    rng = _rng(seed, split, index)
    body_h = height - 1

    variant = _stable_choice(seed, split, index, "shape-variant", 3)
    special = split == "train" and index == 0
    shapes = _shapes(k, variant, special=special)
    # Independent reflections vary the topology motif at fixed dimensions.
    for role in ("B", "C", "D", "F"):
        bits = _stable_choice(seed, split, index, f"reflect-{role}", 4)
        shapes[role] = _reflect_shape(
            shapes[role], horizontal=bool(bits & 1), vertical=bool(bits & 2)
        )
    # The second minimum lesson puts every matching candidate on one shelf.
    # Transposing the deliberately wide boundary rival keeps that shelf within
    # ARC's 30-column limit while preserving area, boundary, and topology.
    if split == "train" and index == 1:
        shapes["D"] = _transpose_shape(shapes["D"])

    if split == "train" and index in (0, 1):
        cross = _stable_choice(seed, "train", 0, "minimum-cross", 2)
        # The two-demo minimum always crosses the largest object's matching
        # rank. Which fixed dimension receives which rank changes by seed.
        first_order = "CD" if cross == 0 else "DC"
        middle_order = first_order if index == 0 else first_order[::-1]
        leftmost = middle_order[0] if index == 0 else "B"
        pattern_index = (index + cross) % 2
    else:
        middle_order = "CD" if _stable_choice(seed, split, index, "middle-order", 2) == 0 else "DC"
        leftmost = "B" if _stable_choice(seed, split, index, "leftmost-shelf", 2) == 0 else middle_order[0]
        pattern_index = _stable_choice(seed, split, index, "color-pattern", len(_COLOR_PATTERNS))
    colors = dict(_COLOR_PATTERNS[pattern_index])

    # When B is the intended leftmost matching object it heads the top shelf;
    # otherwise vary A/B order independently to break absolute object indices.
    if split == "train" and index == 0:
        # Keep a wrong-topology object first in the minimum lesson so that
        # unfiltered first-object selection is explicitly contradicted.
        top_order = "AB"
    elif leftmost == "B":
        top_order = "BA"
    else:
        top_order = "AB" if _stable_choice(seed, split, index, "top-order", 2) == 0 else "BA"

    body = [[0 for _ in range(width)] for _ in range(body_h)]

    if split == "train" and index == 1:
        # Put B/C/D on a common top shelf.  C remains the unique largest-area
        # match, but its vertical shelf is no longer a hidden setting cue.
        top_order = "BCD" if middle_order == "CD" else "BDC"
        top_h = max(_dims(shapes[name])[0] for name in top_order)
        lower_h = max(_dims(shapes[name])[0] for name in "AF")
        minimum = top_h + 1 + lower_h
        if minimum > body_h:
            raise ValueError((profiles[index], minimum, body_h))
        vertical_slack = body_h - minimum
        top_row = rng.randrange(vertical_slack + 1)
        lower_row = top_row + top_h + 1 + (vertical_slack - top_row)

        top_width = sum(_dims(shapes[name])[1] for name in top_order) + len(top_order) - 1
        if top_width > width:
            raise ValueError((top_order, top_width, width))
        top_cols: dict[str, int] = {}
        cursor = 0
        for name in top_order:
            top_cols[name] = cursor
            cursor += _dims(shapes[name])[1] + 1

        lower_order = "AF" if _stable_choice(seed, split, index, "lower-order", 2) == 0 else "FA"
        lower_width = sum(_dims(shapes[name])[1] for name in lower_order) + 1
        lower_lead = rng.randrange(width - lower_width + 1)
        lower_cols: dict[str, int] = {}
        cursor = lower_lead
        for name in lower_order:
            lower_cols[name] = cursor
            cursor += _dims(shapes[name])[1] + 1

        positions = {
            "A": (lower_row, lower_cols["A"]),
            "B": (top_row, top_cols["B"]),
            "C": (top_row, top_cols["C"]),
            "D": (top_row, top_cols["D"]),
            "F": (lower_row, lower_cols["F"]),
        }
    else:
        top_left, top_right = top_order
        mid_left, mid_right = middle_order
        top_h = max(_dims(shapes[top_left])[0], _dims(shapes[top_right])[0])
        mid_h = max(_dims(shapes[mid_left])[0], _dims(shapes[mid_right])[0])
        f_h = _dims(shapes["F"])[0]
        minimum = top_h + 1 + mid_h + 1 + f_h
        if minimum > body_h:
            raise ValueError((profiles[index], minimum, body_h))
        vertical_slack = body_h - minimum

        if stress:
            top_row = 0
            mid_row = top_h + 1 + vertical_slack
            f_row = body_h - f_h
        else:
            top_pad = rng.randrange(vertical_slack + 1)
            remaining = vertical_slack - top_pad
            middle_extra = rng.randrange(remaining + 1)
            top_row = top_pad
            mid_row = top_row + top_h + 1 + middle_extra
            f_row = mid_row + mid_h + 1 + (remaining - middle_extra)

        def pair_columns(order: str, lead: int) -> dict[str, int]:
            left, right = order
            left_w = _dims(shapes[left])[1]
            right_w = _dims(shapes[right])[1]
            slack = width - (left_w + 1 + right_w)
            if not 0 <= lead <= slack:
                raise ValueError((order, lead, slack))
            return {left: lead, right: lead + left_w + 1}

        top_slack = width - (_dims(shapes[top_left])[1] + 1 + _dims(shapes[top_right])[1])
        mid_slack = width - (_dims(shapes[mid_left])[1] + 1 + _dims(shapes[mid_right])[1])
        if min(top_slack, mid_slack) < 0:
            raise ValueError("shelf does not fit")

        if stress:
            # Middle shelf provides left contact; top shelf provides right contact.
            mid_lead = 0
            top_lead = top_slack
        elif leftmost == "B":
            top_lead = 0
            mid_lead = rng.randrange(1, mid_slack + 1) if mid_slack >= 1 else 0
        else:
            mid_lead = 0
            top_lead = rng.randrange(1, top_slack + 1) if top_slack >= 1 else 0
        top_cols = pair_columns(top_order, top_lead)
        mid_cols = pair_columns(middle_order, mid_lead)

        fw = _dims(shapes["F"])[1]
        f_col = 0 if stress else rng.randrange(width - fw + 1)
        positions = {
            "A": (top_row, top_cols["A"]),
            "B": (top_row, top_cols["B"]),
            "C": (mid_row, mid_cols["C"]),
            "D": (mid_row, mid_cols["D"]),
            "F": (f_row, f_col),
        }
    for name in ("A", "B", "C", "D", "F"):
        _place(body, shapes[name], *positions[name], colors[name])

    header = [0 for _ in range(width)]
    candidates = list(range(width))
    rng.shuffle(candidates)
    for col in sorted(candidates[:k]):
        header[col] = 1
    grid = [header, *body]

    summary = scene_summary(grid)
    if summary["matching_count"] != 4:
        raise AssertionError(summary)
    if summary["first_match_index"] == summary["largest_area_match_index"]:
        raise AssertionError(summary)
    if summary["largest_area_match_index"] == summary["last_match_index"]:
        raise AssertionError(summary)
    if summary["largest_overall_index"] in summary["matching_indices"]:
        raise AssertionError(summary)
    if summary["largest_boundary_match_index"] == summary["largest_area_match_index"]:
        raise AssertionError(summary)
    if summary["smallest_area_match_index"] == summary["first_match_index"]:
        raise AssertionError(summary)
    if stress and boundary_contacts(grid) != {"top", "bottom", "left", "right"}:
        raise AssertionError(boundary_contacts(grid))
    return grid

def _select_rank(matches: list[dict[str, object]], rank: int):
    return matches[rank] if len(matches) > rank else None


def _shortcut(name: str, grid: list[list[int]], chosen: object) -> list[list[int]]:
    chosen = _settings(chosen)
    k, objects, matches = _analysis(grid)
    candidate = None
    whole = False
    if name == "first_object":
        candidate = objects[0] if objects else None
    elif name == "largest_object_overall":
        candidate = max(objects, key=lambda obj: int(obj["area"]), default=None)
    elif name == "last_match":
        candidate = matches[-1] if matches else None
    elif name == "smallest_match":
        candidate = min(matches, key=lambda obj: int(obj["area"]), default=None)
    elif name == "largest_boundary_match":
        candidate = max(matches, key=lambda obj: int(obj["boundary_size"]), default=None)
    elif name == "largest_bbox_match":
        candidate = max(matches, key=lambda obj: int(obj["bbox_area"]), default=None)
    elif name == "widest_match":
        candidate = max(matches, key=lambda obj: int(obj["width"]), default=None)
    elif name == "lowest_color_match":
        candidate = min(matches, key=lambda obj: int(obj["color"]), default=None)
    elif name == "highest_color_match":
        candidate = max(matches, key=lambda obj: int(obj["color"]), default=None)
    elif name == "leftmost_match":
        candidate = min(matches, key=lambda obj: int(obj["bbox"][1]), default=None)
    elif name == "rightmost_match":
        candidate = max(matches, key=lambda obj: int(obj["bbox"][3]), default=None)
    elif name == "second_match":
        candidate = _select_rank(matches, 1)
    elif name == "third_match":
        candidate = _select_rank(matches, 2)
    elif name == "fewest_missing_match":
        candidate = min(matches, key=lambda obj: int(obj["missing_cells"]), default=None)
    elif name == "highest_density_match":
        candidate = max(matches, key=lambda obj: float(obj["area"]) / int(obj["bbox_area"]), default=None)
    elif name == "most_interior_match":
        candidate = max(matches, key=lambda obj: int(obj["area"]) - int(obj["boundary_size"]), default=None)
    elif name == "smallest_aspect_match":
        candidate = min(matches, key=lambda obj: float(obj["width"]) / int(obj["height"]), default=None)
    elif name == "top_shelf_largest_match":
        top = min((int(obj["bbox"][0]) for obj in matches), default=None)
        top_matches = [obj for obj in matches if int(obj["bbox"][0]) == top]
        candidate = max(top_matches, key=lambda obj: int(obj["area"]), default=None)
    elif name == "whole_object":
        candidate = _choose(matches, chosen)
        whole = True
    elif name == "missing_cells_equal_header":
        _, _, candidates = _analysis(grid, missing=True)
        candidate = _choose(candidates, chosen) if candidates else None
    elif name == "eight_connected_holes":
        _, _, candidates = _analysis(grid, connectivity=8)
        candidate = _choose(candidates, chosen) if candidates else None
    else:
        raise KeyError(name)
    if candidate is None:
        return [[0]]
    return copy.deepcopy(candidate["whole_output"] if whole else candidate["output"])


SHORTCUTS = (
    "first_object",
    "largest_object_overall",
    "last_match",
    "smallest_match",
    "largest_boundary_match",
    "largest_bbox_match",
    "widest_match",
    "lowest_color_match",
    "highest_color_match",
    "leftmost_match",
    "rightmost_match",
    "second_match",
    "third_match",
    "fewest_missing_match",
    "highest_density_match",
    "most_interior_match",
    "smallest_aspect_match",
    "top_shelf_largest_match",
    "whole_object",
    "missing_cells_equal_header",
    "eight_connected_holes",
)


def certify(
    episode: dict,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be a mapping")
    chosen = _settings(episode.get("settings"))
    source = program(chosen)
    if episode.get("program_solution") != source:
        raise ValueError("program does not match fixed episode settings")
    if episode.get("program_sha256") != hashlib.sha256(source.encode()).hexdigest():
        raise ValueError("program hash does not match fixed episode program")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    for pair in pairs:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("every private pair must contain exactly input/output")
        _grid(pair["input"])
        _grid(pair["output"])
    if len({digest(pair["input"]) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")

    def python_apply(source: str, grid: list[list[int]]) -> list[list[int]]:
        matches = [setting for setting in SETTINGS if program(setting) == source]
        if len(matches) != 1:
            raise ValueError("unknown or ambiguous program source")
        return transform(grid, matches[0])

    apply = execute or python_apply
    records = []
    for setting in SETTINGS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if apply(program(setting), pair["input"]) != pair["output"]
        ]
        records.append({"settings": setting, "disagreeing_demo_indices": disagreements})
    survivors = [dict(row["settings"]) for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")

    shortcut_refutations: dict[str, list[int]] = {}
    shortcut_survivors: list[str] = []
    for name in SHORTCUTS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if _shortcut(name, pair["input"], chosen) != pair["output"]
        ]
        shortcut_refutations[name] = disagreements
        if not disagreements:
            shortcut_survivors.append(name)
    if shortcut_survivors:
        raise ValueError(f"named shortcuts survive: {shortcut_survivors}")

    queries = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with selected setting")
        queries.append(
            {
                "input_sha256": digest(pair["input"]),
                "output_sha256": digest(pair["output"]),
                "survivors": survivors,
            }
        )
    return {
        "scope": f"two match selectors plus {len(SHORTCUTS)} finite shortcuts",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "shortcut_survivors": shortcut_survivors,
        "demo_refutations": records,
        "shortcut_refutations": shortcut_refutations,
        "queries": queries,
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(DEFAULT if settings is None else settings)
    train = []
    for index in range(demos):
        grid = _build_input(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(4):
        grid = _build_input(seed, "test", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    source = program(chosen)
    episode = {
        "schema": "4dd0-match-selector-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    _integer(index, 0, 3, "query index")
    if type(episode) is not dict:
        raise ValueError("episode must be a mapping")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


def public_id(episode: dict, index: int) -> str:
    return public_challenge_id(public_turn(episode, index))


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()
