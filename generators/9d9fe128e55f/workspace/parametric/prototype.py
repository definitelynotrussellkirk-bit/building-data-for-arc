"""Native parametric family for 9d9fe128e55f.

The exact canonical default recolors every color-8 component by increasing
occupied area.  The alternative first selects the component whose rightmost
cell is closest to the separator, binds that component's occupied area, then
recolors only components at least that large.  The selected anchor therefore
changes eligibility as well as the palette-to-component assignment.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from reviewer_support import find_root


TASK_ID = "9d9fe128e55f"
MODES = ("all_by_size", "right_anchor_threshold")
DEFAULT_MODE = "all_by_size"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.0.0"
HOME = Path(__file__).resolve().parent
ROOT = find_root(__file__)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if not (dr == 0 and dc == 0)
)

_CANONICAL_COMPONENT_BINDING = (
    "(comps (sort (filter (lambda (obj) (= (obj-color obj) 8)) "
    "(objects left 0)) (lambda (a b) (< (obj-size a) (obj-size b)))))"
)
_THRESHOLD_COMPONENT_BINDINGS = (
    "(all-comps (filter (lambda (obj) (= (obj-color obj) 8)) (objects left 0))) "
    "(anchor (first (sort all-comps (lambda (a b) (> (max-of snd (obj-cells a)) "
    "(max-of snd (obj-cells b))))))) "
    "(threshold (obj-size anchor)) "
    "(comps (sort (filter (lambda (obj) (>= (obj-size obj) threshold)) all-comps) "
    "(lambda (a b) (< (obj-size a) (obj-size b)))))"
)


def _mode(mode: str) -> str:
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"rank_policy must be one of {MODES}, got {mode!r}")
    return mode


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def canonical_source() -> str:
    """Return the exact selected canonical Racket bytes retained task-locally."""
    return (HOME / "canonical.rkt").read_bytes().decode("utf-8")


def program_for(mode: str = DEFAULT_MODE) -> str:
    """Return one complete Racket program for the episode-fixed setting."""
    mode = _mode(mode)
    source = canonical_source()
    if mode == DEFAULT_MODE:
        return source
    if source.count(_CANONICAL_COMPONENT_BINDING) != 1:
        raise ValueError("canonical source no longer matches the guarded component binding")
    return source.replace(_CANONICAL_COMPONENT_BINDING, _THRESHOLD_COMPONENT_BINDINGS)


def fixed_threshold_program(threshold: int) -> str:
    """Counterfactual program used only for protected causal evidence."""
    if type(threshold) is not int or not 1 <= threshold <= 30:
        raise ValueError("threshold must be an exact integer in 1..30")
    source = program_for("right_anchor_threshold")
    needle = "(threshold (obj-size anchor))"
    if source.count(needle) != 1:
        raise ValueError("threshold program no longer matches guarded intermediate binding")
    return source.replace(needle, f"(threshold {threshold})")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return len(grid), width


def _components(
    grid: list[list[int]],
    color: int,
    *,
    neighbors: tuple[tuple[int, int], ...] = _CARDINAL,
) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in neighbors:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def _colored_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Racket-like same-color non-background objects for shortcut probes."""
    out: list[list[tuple[int, int]]] = []
    for color in sorted({cell for row in grid for cell in row if cell != 0}):
        out.extend(_components(grid, color))
    return sorted(out, key=lambda cells: min(cells))


def analyze_grid(grid: list[list[int]]) -> dict[str, Any]:
    h, w = _validate_grid(grid)
    separators = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(separators) != 1:
        raise ValueError("expected exactly one full-height separator column")
    divider = separators[0]
    if divider == 0 or divider == w - 1:
        raise ValueError("separator must have nonempty panels on both sides")
    left = [row[:divider] for row in grid]
    right = [row[divider + 1 :] for row in grid]
    if any(9 in row for row in left):
        raise ValueError("left panel must reserve color 9 for the separator")
    if any(value != 0 for row in right for value in row[1:]):
        raise ValueError("right-panel padding outside the first column must be zero")
    legend_column = [row[0] for row in right]
    count = 0
    while count < h and legend_column[count] != 0:
        count += 1
    if any(value != 0 for value in legend_column[count:]):
        raise ValueError("legend must be contiguous from row zero")
    palette = legend_column[:count]
    if not palette or len(set(palette)) != len(palette) or any(v in (0, 9) for v in palette):
        raise ValueError("legend must contain distinct nonzero non-separator colors")
    components = _components(left, 8)
    if not 3 <= len(components) <= 7:
        raise ValueError("family grammar requires 3..7 color-8 components")
    sizes = [len(cells) for cells in components]
    if len(set(sizes)) != len(sizes):
        raise ValueError("color-8 component sizes must be distinct")
    if len(palette) != len(components):
        raise ValueError("legend length must equal the color-8 component count")
    right_edges = [max(c for _, c in cells) for cells in components]
    best = max(right_edges)
    anchors = [index for index, value in enumerate(right_edges) if value == best]
    if len(anchors) != 1:
        raise ValueError("the rightmost color-8 component must be unique")
    anchor_index = anchors[0]
    anchor = components[anchor_index]
    component_cells = tuple(tuple(cells) for cells in components)
    foreign = [
        (r, c, left[r][c])
        for r in range(h)
        for c in range(divider)
        if left[r][c] not in (0, 8)
    ]
    return {
        "shape": (h, w),
        "height": h,
        "width": w,
        "divider": divider,
        "left": left,
        "right": right,
        "palette": palette,
        "components": components,
        "component_cells": component_cells,
        "sizes": sizes,
        "anchor_index": anchor_index,
        "anchor": anchor,
        "anchor_size": len(anchor),
        "anchor_right": best,
        "anchor_left": min(c for _, c in anchor),
        "anchor_bbox_area": (
            (max(r for r, _ in anchor) - min(r for r, _ in anchor) + 1)
            * (max(c for _, c in anchor) - min(c for _, c in anchor) + 1)
        ),
        "foreign_cells": foreign,
    }


def anchor_size(grid: list[list[int]]) -> int:
    return int(analyze_grid(grid)["anchor_size"])


def _paint(
    analysis: dict[str, Any],
    components: list[list[tuple[int, int]]],
    palette: list[int],
) -> list[list[int]]:
    out = [[0 for _ in range(analysis["divider"])] for _ in range(analysis["height"])]
    for cells, color in zip(components, palette):
        for r, c in cells:
            out[r][c] = color
    return out


def python_mirror(grid: list[list[int]], mode: str = DEFAULT_MODE) -> list[list[int]]:
    mode = _mode(mode)
    analysis = analyze_grid(grid)
    ranked = sorted(analysis["components"], key=len)
    if mode == "right_anchor_threshold":
        threshold = analysis["anchor_size"]
        ranked = [cells for cells in ranked if len(cells) >= threshold]
    return _paint(analysis, ranked, analysis["palette"])


def _normalize_shape(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _rotate_shape(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    height = max(r for r, _ in cells) + 1
    return _normalize_shape([(c, height - 1 - r) for r, c in cells])


def _reflect_shape(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    width = max(c for _, c in cells) + 1
    return _normalize_shape([(r, width - 1 - c) for r, c in cells])


def _shape(size: int, style: str, variant: int = 0) -> list[tuple[int, int]]:
    if type(size) is not int or size < 1:
        raise ValueError("shape size must be a positive exact integer")
    if style == "horizontal":
        cells = [(0, c) for c in range(size)]
    elif style == "vertical":
        cells = [(r, 0) for r in range(size)]
    elif style == "l":
        vertical = max(2, (size + 2) // 2)
        horizontal = size - vertical + 1
        cells = [(r, 0) for r in range(vertical)] + [
            (vertical - 1, c) for c in range(1, horizontal)
        ]
    elif style == "ring":
        if size < 8 or size % 2:
            raise ValueError("ring style needs an even size at least eight")
        height = 3
        width = (size - 2) // 2
        cells = (
            [(0, c) for c in range(width)]
            + [(height - 1, c) for c in range(width)]
            + [(1, 0), (1, width - 1)]
        )
    elif style in {"snake2", "snake3", "snake4"}:
        width = int(style[-1])
        cells = []
        for index in range(size):
            row, offset = divmod(index, width)
            col = offset if row % 2 == 0 else width - 1 - offset
            cells.append((row, col))
    elif style == "block3":
        width = 3
        cells = [(index // width, index % width) for index in range(size)]
    else:
        raise ValueError(f"unknown shape style {style!r}")
    cells = _normalize_shape(cells)
    for _ in range(variant % 4):
        cells = _rotate_shape(cells)
    if (variant // 4) % 2:
        cells = _reflect_shape(cells)
    if len(set(cells)) != size:
        raise AssertionError("shape constructor lost cells")
    return cells


def _shape_dims(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _candidate_positions(
    slot: str,
    h: int,
    w: int,
    sh: int,
    sw: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    if sh > h or sw > w:
        return []
    rows = list(range(h - sh + 1))
    cols = list(range(w - sw + 1))
    if slot == "anchor_right":
        cols = [w - sw]
        target_r = max(0, min(h - sh, h // 2 - sh // 2))
        rows.sort(key=lambda r: (abs(r - target_r), r))
    elif slot == "top_right_trap":
        col = w - sw - 1
        if col < 0:
            return []
        cols = [col]
        rows.sort()
    elif slot == "top_left":
        rows.sort()
        cols.sort()
    elif slot == "bottom_left":
        rows.sort(reverse=True)
        cols.sort()
    elif slot == "mid_left":
        target_r = max(0, min(h - sh, h // 2 - sh // 2))
        rows.sort(key=lambda r: (abs(r - target_r), r))
        cols.sort()
    elif slot == "bottom_mid":
        rows.sort(reverse=True)
        target_c = max(0, min(w - sw, w // 2 - sw // 2))
        cols.sort(key=lambda c: (abs(c - target_c), c))
    elif slot == "top_mid":
        rows.sort()
        target_c = max(0, min(w - sw, w // 2 - sw // 2))
        cols.sort(key=lambda c: (abs(c - target_c), c))
    else:
        raise ValueError(f"unknown placement slot {slot!r}")
    # Stable bounded jitter changes nuisance geometry without changing slot roles.
    head_rows, tail_rows = rows[:4], rows[4:]
    head_cols, tail_cols = cols[:4], cols[4:]
    rng.shuffle(head_rows)
    rng.shuffle(head_cols)
    rows = head_rows + tail_rows
    cols = head_cols + tail_cols
    return [(r, c) for r in rows for c in cols]


def _can_place(
    cells: list[tuple[int, int]],
    occupied: set[tuple[int, int]],
    h: int,
    w: int,
) -> bool:
    proposed = set(cells)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in proposed):
        return False
    if proposed & occupied:
        return False
    for r, c in proposed:
        for dr, dc in _CARDINAL:
            if (r + dr, c + dc) in occupied:
                return False
    return True


def _place_shape(
    shape: list[tuple[int, int]],
    slot: str,
    occupied: set[tuple[int, int]],
    h: int,
    w: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    sh, sw = _shape_dims(shape)
    for row, col in _candidate_positions(slot, h, w, sh, sw, rng):
        cells = [(row + dr, col + dc) for dr, dc in shape]
        if _can_place(cells, occupied, h, w):
            occupied.update(cells)
            return sorted(cells)
    raise RuntimeError(f"could not place {len(shape)}-cell shape in slot {slot}")


def _place_shape_diagonal_to(
    shape: list[tuple[int, int]],
    slot: str,
    reference: list[tuple[int, int]],
    occupied: set[tuple[int, int]],
    h: int,
    w: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Place a separate 4-connected object with guaranteed diagonal contact."""
    sh, sw = _shape_dims(shape)
    reference_set = set(reference)
    for row, col in _candidate_positions(slot, h, w, sh, sw, rng):
        cells = [(row + dr, col + dc) for dr, dc in shape]
        if not _can_place(cells, occupied, h, w):
            continue
        if not any(
            (r + dr, c + dc) in reference_set
            for r, c in cells
            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
        ):
            continue
        occupied.update(cells)
        return sorted(cells)
    raise RuntimeError(
        f"could not place {len(shape)}-cell shape diagonally to reference in slot {slot}"
    )


def _place_decoys(
    left: list[list[int]],
    occupied: set[tuple[int, int]],
    count: int,
    rng: random.Random,
) -> None:
    h, w = len(left), len(left[0])
    candidates = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(candidates)
    colors = [1, 3, 4, 5, 6, 7]
    placed = 0
    for r, c in candidates:
        if placed >= count:
            break
        if (r, c) in occupied:
            continue
        if any((r + dr, c + dc) in occupied for dr, dc in _CARDINAL):
            continue
        left[r][c] = colors[(placed + rng.randrange(len(colors))) % len(colors)]
        occupied.add((r, c))
        placed += 1
    if placed != count:
        raise RuntimeError("could not place requested distractors")


def _palette(rng: random.Random, count: int, style: str) -> list[int]:
    colors = sorted(rng.sample(list(range(1, 8)), count))
    if style == "descending":
        return list(reversed(colors))
    if style == "mixed":
        shift = 1 + rng.randrange(count - 1)
        result = colors[shift:] + colors[:shift]
        if result == sorted(result) or result == sorted(result, reverse=True):
            result[0], result[1] = result[1], result[0]
        return result
    if style == "zigzag":
        result: list[int] = []
        lo, hi = 0, len(colors) - 1
        while lo <= hi:
            result.append(colors[hi])
            hi -= 1
            if lo <= hi:
                result.append(colors[lo])
                lo += 1
        return result
    raise ValueError(f"unknown palette style {style!r}")


_DEMO_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "h": 14,
        "left_w": 16,
        "right_w": 2,
        "sizes": (5, 2, 8, 7),
        "anchor": 2,
        "slots": ("top_right_trap", "bottom_left", "anchor_right", "top_left"),
        "styles": ("vertical", "l", "ring", "snake3"),
        "palette": "descending",
        "decoys": 2,
        "diagonal_pair": (3, 1),
    },
    {
        "h": 14,
        "left_w": 16,
        "right_w": 2,
        "sizes": (3, 6, 9, 12),
        "anchor": 1,
        "slots": ("top_right_trap", "anchor_right", "top_left", "bottom_left"),
        "styles": ("vertical", "l", "snake3", "block3"),
        "palette": "mixed",
        "decoys": 2,
    },
    {
        "h": 15,
        "left_w": 17,
        "right_w": 1,
        "sizes": (1, 4, 7, 10),
        "anchor": 3,
        "slots": ("top_right_trap", "bottom_left", "top_left", "anchor_right"),
        "styles": ("vertical", "l", "snake3", "ring"),
        "palette": "zigzag",
        "decoys": 1,
    },
    {
        "h": 16,
        "left_w": 18,
        "right_w": 3,
        "sizes": (3, 5, 8, 12),
        "anchor": 2,
        "slots": ("top_right_trap", "top_left", "anchor_right", "bottom_left"),
        "styles": ("vertical", "snake2", "ring", "snake4"),
        "palette": "mixed",
        "decoys": 3,
    },
    {
        "h": 18,
        "left_w": 20,
        "right_w": 2,
        "sizes": (2, 6, 9, 13, 15),
        "anchor": 1,
        "slots": (
            "top_right_trap",
            "anchor_right",
            "mid_left",
            "bottom_mid",
            "top_left",
        ),
        "styles": ("vertical", "l", "snake3", "snake4", "block3"),
        "palette": "descending",
        "decoys": 2,
    },
    {
        "h": 12,
        "left_w": 21,
        "right_w": 1,
        "sizes": (2, 4, 7, 9),
        "anchor": 0,
        "slots": ("anchor_right", "top_mid", "bottom_left", "top_left"),
        "styles": ("horizontal", "snake2", "l", "block3"),
        "palette": "zigzag",
        "decoys": 2,
    },
)

_QUERY_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "h": 13,
        "left_w": 16,
        "right_w": 2,
        "sizes": (2, 4, 7, 11),
        "anchor": 1,
        "slots": ("top_right_trap", "anchor_right", "bottom_left", "top_left"),
        "styles": ("vertical", "l", "snake3", "block3"),
        "palette": "mixed",
        "decoys": 1,
    },
    {
        "h": 17,
        "left_w": 19,
        "right_w": 1,
        "sizes": (1, 5, 8, 10, 14),
        "anchor": 2,
        "slots": (
            "top_right_trap",
            "bottom_left",
            "anchor_right",
            "top_left",
            "bottom_mid",
        ),
        "styles": ("vertical", "l", "ring", "snake3", "snake4"),
        "palette": "descending",
        "decoys": 3,
    },
    {
        "h": 10,
        "left_w": 20,
        "right_w": 3,
        "sizes": (2, 5, 8, 11),
        "anchor": 1,
        "slots": ("top_right_trap", "anchor_right", "bottom_left", "top_left"),
        "styles": ("vertical", "l", "ring", "horizontal"),
        "palette": "zigzag",
        "decoys": 2,
    },
    {
        "h": 30,
        "left_w": 26,
        "right_w": 3,
        "sizes": (3, 6, 9, 12, 15),
        "anchor": 3,
        "slots": (
            "top_right_trap",
            "bottom_left",
            "mid_left",
            "anchor_right",
            "top_left",
        ),
        "styles": ("vertical", "l", "snake3", "ring", "snake4"),
        "palette": "mixed",
        "decoys": 4,
    },
)


def _build_input(seed: int, index: int, profile: dict[str, Any], *, family: str) -> list[list[int]]:
    salt = 0x9D9F if family == "demo" else 0xE55F
    rng = random.Random((seed + 1) * 1_000_003 + index * 65_537 + salt)
    h = int(profile["h"])
    left_w = int(profile["left_w"])
    right_w = int(profile["right_w"])
    sizes = list(profile["sizes"])
    anchor_index = int(profile["anchor"])
    slots = list(profile["slots"])
    styles = list(profile["styles"])
    if not (len(sizes) == len(slots) == len(styles)):
        raise AssertionError("profile component metadata differs in length")

    shapes: list[list[tuple[int, int]]] = []
    for component_index, (size, style, slot) in enumerate(zip(sizes, styles, slots)):
        if slot == "top_right_trap":
            variant = 0
        elif style in {"horizontal", "vertical"}:
            # These names encode the intended orientation. Random quarter-turns
            # can make a long line taller than its profile and are not nuisance
            # variation; reflection normalizes to the same cells anyway.
            variant = 0
        elif component_index == anchor_index and style in {"ring", "l"}:
            variant = 0 if style == "ring" else (4 if seed % 2 else 0)
        else:
            variant = rng.randrange(8)
        shapes.append(_shape(size, style, variant))

    occupied: set[tuple[int, int]] = set()
    placed: list[list[tuple[int, int]] | None] = [None] * len(sizes)
    diagonal_pair = profile.get("diagonal_pair")
    if diagonal_pair is not None:
        if (
            not isinstance(diagonal_pair, (tuple, list))
            or len(diagonal_pair) != 2
            or any(type(value) is not int for value in diagonal_pair)
            or diagonal_pair[0] == diagonal_pair[1]
            or any(not (0 <= value < len(sizes)) for value in diagonal_pair)
        ):
            raise AssertionError("diagonal_pair must name two distinct component indices")
        diagonal_reference, diagonal_mate = diagonal_pair
    else:
        diagonal_reference = diagonal_mate = None

    order = [anchor_index]
    order.extend(
        index
        for index, slot in enumerate(slots)
        if slot == "top_right_trap" and index != anchor_index
    )
    if diagonal_reference is not None:
        order.extend((diagonal_reference, diagonal_mate))
    order.extend(index for index in range(len(sizes)) if index not in order)
    for component_index in order:
        if component_index == diagonal_mate:
            reference = placed[diagonal_reference]
            if reference is None:
                raise AssertionError("diagonal reference must be placed before its mate")
            placed[component_index] = _place_shape_diagonal_to(
                shapes[component_index],
                slots[component_index],
                reference,
                occupied,
                h,
                left_w,
                rng,
            )
        else:
            placed[component_index] = _place_shape(
                shapes[component_index],
                slots[component_index],
                occupied,
                h,
                left_w,
                rng,
            )
    components = [cells for cells in placed if cells is not None]
    if len(components) != len(sizes):
        raise AssertionError("component placement incomplete")

    left = [[0 for _ in range(left_w)] for _ in range(h)]
    for cells in components:
        for r, c in cells:
            left[r][c] = 8
    _place_decoys(left, occupied, int(profile["decoys"]), rng)
    palette = _palette(random.Random(rng.randrange(2**63)), len(sizes), str(profile["palette"]))

    grid = [[0 for _ in range(left_w + 1 + right_w)] for _ in range(h)]
    for r in range(h):
        grid[r][:left_w] = left[r]
        grid[r][left_w] = 9
    for r, color in enumerate(palette):
        grid[r][left_w + 1] = color

    analysis = analyze_grid(grid)
    intended_anchor = set(components[anchor_index])
    if set(analysis["anchor"]) != intended_anchor:
        raise AssertionError("profile did not realize its intended rightmost anchor")
    return grid


def _input_bank(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _validate_seed(seed)
    demos = [
        _build_input(seed, index, profile, family="demo")
        for index, profile in enumerate(_DEMO_PROFILES)
    ]
    queries = [
        _build_input(seed, index, profile, family="query")
        for index, profile in enumerate(_QUERY_PROFILES)
    ]
    encodings = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(encodings) != len(set(encodings)):
        raise AssertionError("profile bank produced duplicate inputs")
    return demos, queries


def generate_claims(
    seed: int,
    mode: str = DEFAULT_MODE,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Return deterministic Python claims for protected qualification replay."""
    _validate_seed(seed)
    mode = _mode(mode)
    _validate_counts(demos, queries)
    _validate_difficulty(difficulty)
    demo_bank, query_bank = _input_bank(seed)
    selected_demos = demo_bank[:demos]
    selected_queries = query_bank[:queries]
    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": python_mirror(grid, mode)}
            for grid in selected_demos
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": python_mirror(grid, mode)}
            for grid in selected_queries
        ],
        "program_solution": program_for(mode),
    }


def _ranked_components(analysis: dict[str, Any]) -> list[list[tuple[int, int]]]:
    return sorted(analysis["components"], key=len)


def _threshold_output(grid: list[list[int]], threshold: int, *, palette_sort: bool = False):
    analysis = analyze_grid(grid)
    components = [cells for cells in _ranked_components(analysis) if len(cells) >= threshold]
    palette = sorted(analysis["palette"]) if palette_sort else analysis["palette"]
    return _paint(analysis, components, palette)


def _reading_order_all(grid):
    analysis = analyze_grid(grid)
    return _paint(analysis, analysis["components"], analysis["palette"])


def _numeric_palette_all(grid):
    analysis = analyze_grid(grid)
    return _paint(analysis, _ranked_components(analysis), sorted(analysis["palette"]))


def _fixed_top_k(grid, k: int):
    analysis = analyze_grid(grid)
    ranked = _ranked_components(analysis)
    return _paint(analysis, ranked[-k:], analysis["palette"])


def _anchor_by(grid, key: Callable[[list[tuple[int, int]]], Any], *, maximize: bool):
    analysis = analyze_grid(grid)
    anchor = (max if maximize else min)(analysis["components"], key=key)
    return _threshold_output(grid, len(anchor))


def _right_anchor_bbox_threshold(grid):
    analysis = analyze_grid(grid)
    return _threshold_output(grid, analysis["anchor_bbox_area"])


def _right_anchor_only(grid):
    analysis = analyze_grid(grid)
    return _paint(analysis, [analysis["anchor"]], analysis["palette"])


def _right_anchor_keep_global_colors(grid):
    analysis = analyze_grid(grid)
    threshold = analysis["anchor_size"]
    out = [[0 for _ in range(analysis["divider"])] for _ in range(analysis["height"])]
    for cells, color in zip(_ranked_components(analysis), analysis["palette"]):
        if len(cells) >= threshold:
            for r, c in cells:
                out[r][c] = color
    return out


def _all_nonzero_by_size(grid):
    analysis = analyze_grid(grid)
    components = sorted(_colored_components(analysis["left"]), key=len)
    return _paint(analysis, components, analysis["palette"])


def _eight_connected_threshold(grid):
    analysis = analyze_grid(grid)
    components = _components(analysis["left"], 8, neighbors=_EIGHT)
    anchor = max(components, key=lambda cells: max(c for _, c in cells))
    threshold = len(anchor)
    ranked = [cells for cells in sorted(components, key=len) if len(cells) >= threshold]
    return _paint(analysis, ranked, analysis["palette"])


def _rival_bank(mode: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    mode = _mode(mode)
    declared_other = "right_anchor_threshold" if mode == "all_by_size" else "all_by_size"
    return {
        f"declared_{declared_other}": lambda grid: python_mirror(grid, declared_other),
        "reading_order": _reading_order_all,
        "numeric_palette": (
            _numeric_palette_all
            if mode == "all_by_size"
            else lambda grid: _threshold_output(grid, anchor_size(grid), palette_sort=True)
        ),
        "fixed_threshold_4": lambda grid: _threshold_output(grid, 4),
        "fixed_threshold_6": lambda grid: _threshold_output(grid, 6),
        "fixed_threshold_8": lambda grid: _threshold_output(grid, 8),
        "fixed_top_two": lambda grid: _fixed_top_k(grid, 2),
        "fixed_top_three": lambda grid: _fixed_top_k(grid, 3),
        "leftmost_anchor": lambda grid: _anchor_by(
            grid, lambda cells: min(c for _, c in cells), maximize=False
        ),
        "rightmost_min_column": lambda grid: _anchor_by(
            grid, lambda cells: min(c for _, c in cells), maximize=True
        ),
        "topmost_anchor": lambda grid: _anchor_by(
            grid, lambda cells: min(r for r, _ in cells), maximize=False
        ),
        "largest_anchor": lambda grid: _anchor_by(grid, len, maximize=True),
        "right_anchor_bbox_area": _right_anchor_bbox_threshold,
        "right_anchor_only": _right_anchor_only,
        "right_anchor_keep_global_colors": _right_anchor_keep_global_colors,
        "all_nonzero_objects": _all_nonzero_by_size,
    }


def adversarial_survivors(demos: list[dict[str, Any]], mode: str) -> list[str]:
    """Return plausible wrong rules that fit all demonstration labels."""
    mode = _mode(mode)
    if type(demos) is not list or len(demos) < 2:
        raise ValueError("at least two demonstrations are required")
    survivors = []
    for name, rival in _rival_bank(mode).items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            survivors.append(name)
    return survivors


def extended_rival_results(demos: list[dict[str, Any]], queries: list[dict[str, Any]], mode: str):
    """Fit a broader wrong-rule bank to demos, then report query disagreements."""
    mode = _mode(mode)
    bank = {**_rival_bank(mode), "eight_connected": _eight_connected_threshold}
    rows = []
    for name, rival in bank.items():
        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
        disagreements = [
            index for index, pair in enumerate(queries) if rival(pair["input"]) != pair["output"]
        ]
        rows.append({"name": name, "fits_demos": fits, "query_disagreements": disagreements})
    return rows


def grid_sha256(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
