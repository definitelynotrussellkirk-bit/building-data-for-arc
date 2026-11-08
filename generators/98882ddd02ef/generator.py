"""Generator for ARC task c6e1b8da (content hash 98882ddd02ef).

Each nonzero colour is interpreted independently.  Its largest filled axis-
aligned rectangle is the body and any remaining cells are a possible tail.
A complete one-cell-wide tail of length at least two makes the body jump by
exactly that length in the tail direction; the tail disappears.  Every other
shape settles as its filled bounding box.  Settlers are painted first and
jumpers second, so jumpers win output collisions.

The ordinary curriculum deliberately contains all important branches in every
scene: two perpendicular valid jumpers, a solid settler, a length-one tail,
a thick tail, and a jumper/settler output collision.  A 24-role schedule covers
three exact size classes under every dihedral symmetry of the square.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "98882ddd02ef"
TASK_ID = GENERATOR_ID
RULE_HASH = "62785307ce7a"
VERSION = "4.0.0"

SUMMARY = (
    "For each colour, find its largest filled rectangle. A complete straight "
    "one-cell-wide tail of length 2+ launches that rectangle by the tail "
    "length in the tail direction and then vanishes. Otherwise fill the "
    "shape's bounding box in place. Paint all settlers before all jumpers, "
    "so moved rectangles overwrite settled boxes on collisions."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is colour 0 and each foreground colour is one connected shape",
    "the largest filled rectangle of a colour is its body",
    "only a full one-cell-wide straight tail of length at least two launches",
    "a launched body moves by exactly the tail length in the tail direction",
    "tails vanish; every non-launching shape becomes its filled bounding box",
    "all settlers paint before all jumpers, so jumpers win output collisions",
]

COUNTER_HYPOTHESES = [
    "leave the input unchanged",
    "rectangularize every shape without moving any body",
    "move every protruding shape, including short or thick tails",
    "move valid bodies opposite the tail direction",
    "move by the body span instead of the tail length",
    "paint settlers after jumpers",
    "preserve the original tail after moving the body",
    "apply the launch rule only to horizontal or only to vertical tails",
]

SIZE_CLASSES = ("small", "canonical", "large")
SIZE_BY_CLASS = {"small": 18, "canonical": 20, "large": 24}
CLASS_BY_SIZE = {size: name for name, size in SIZE_BY_CLASS.items()}
TRANSFORMS = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "flip_horizontal",
    "flip_vertical",
    "transpose",
    "anti_transpose",
)
_SCHEDULE = tuple(
    (size_class, transform)
    for transform in TRANSFORMS
    for size_class in SIZE_CLASSES
)
SCHEDULE_PROFILES = tuple(f"{size_class}/{transform}" for size_class, transform in _SCHEDULE)

AXES = {
    "size_class": {
        "type": "str",
        "default": "24-role curriculum schedule",
        "valid": "|".join(SIZE_CLASSES),
        "doc": "Exact square canvas and scale: small=18, canonical=20, large=24.",
    },
}

# Every exact override is supported in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
BBox = tuple[int, int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the deterministic size/symmetry curriculum role."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))
    size_class = overrides.get("size_class")
    if size_class is not None and size_class not in SIZE_CLASSES:
        raise ValueError(f"size_class must be one of {SIZE_CLASSES}")


def _rect_cells(top: int, left: int, height: int, width: int) -> set[Cell]:
    return {
        (row, col)
        for row in range(top, top + height)
        for col in range(left, left + width)
    }


def _bbox(cells: Iterable[Cell]) -> BBox:
    cells = tuple(cells)
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _bbox_cells(box: BBox) -> set[Cell]:
    top, left, bottom, right = box
    return _rect_cells(top, left, bottom - top + 1, right - left + 1)


def _paint_new(grid: Grid, cells: Iterable[Cell], color: int, label: str) -> None:
    height, width = len(grid), len(grid[0])
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width):
            raise AssertionError(f"internal layout bug: {label} leaves the canvas")
        if grid[row][col] != 0:
            raise AssertionError(
                f"internal layout bug: {label} overlaps input colour {grid[row][col]}"
            )
        grid[row][col] = color


def _transform_cell(row: int, col: int, size: int, transform: str) -> Cell:
    if transform == "identity":
        return row, col
    if transform == "rot90":
        return col, size - 1 - row
    if transform == "rot180":
        return size - 1 - row, size - 1 - col
    if transform == "rot270":
        return size - 1 - col, row
    if transform == "flip_horizontal":
        return row, size - 1 - col
    if transform == "flip_vertical":
        return size - 1 - row, col
    if transform == "transpose":
        return col, row
    if transform == "anti_transpose":
        return size - 1 - col, size - 1 - row
    raise ValueError(f"unknown transform {transform!r}")


def _transform_grid(grid: Sequence[Sequence[int]], transform: str) -> Grid:
    size = len(grid)
    out = full_grid(size, size, 0)
    for row in range(size):
        for col in range(size):
            nr, nc = _transform_cell(row, col, size, transform)
            out[nr][nc] = int(grid[row][col])
    return out


def _scene_config(size_class: str) -> dict[str, tuple[int, ...]]:
    """Canonical-like hand-packed grammar before a D4 transform.

    Roles are intentionally spatially separated in the input.  The solid
    settler occupies cells in the first jumper's *future* rectangle but avoids
    its one-row input tail, creating a genuine output collision.
    """
    if size_class == "small":
        return {
            "jumper_h": (1, 1, 5, 5, 2),
            "solid": (1, 6, 3, 4),
            "jumper_v": (9, 1, 4, 5, 3),
            "short": (7, 12, 4, 5),
            "thick": (13, 11, 4, 5),
        }
    if size_class == "canonical":
        return {
            "jumper_h": (1, 1, 6, 6, 3),
            "solid": (1, 7, 4, 5),
            "jumper_v": (10, 1, 5, 6, 4),
            "short": (8, 14, 4, 5),
            "thick": (14, 12, 5, 7),
        }
    if size_class == "large":
        return {
            "jumper_h": (1, 1, 6, 7, 3),
            "solid": (1, 8, 4, 6),
            "jumper_v": (12, 1, 6, 8, 4),
            "short": (9, 17, 5, 6),
            "thick": (17, 15, 6, 8),
        }
    raise ValueError(f"unknown size class {size_class!r}")


def _build_base_scene(size_class: str, colors: Sequence[int], difficulty: Any) -> Grid:
    del difficulty  # every band uses the full semantic grammar; scale is scheduled separately
    size = SIZE_BY_CLASS[size_class]
    config = _scene_config(size_class)
    grid = full_grid(size, size, 0)
    color_h, color_solid, color_v, color_short, color_thick = colors

    # Horizontal valid jumper: body plus a full one-row right tail.  Attach the
    # tail to the body's bottom row so the solid settler can occupy other rows
    # of the future body without overlapping the input.
    top, left, height, width, tail_len = config["jumper_h"]
    body_h = _rect_cells(top, left, height, width)
    tail_h = _rect_cells(top + height - 1, left + width, 1, tail_len)
    _paint_new(grid, body_h | tail_h, color_h, "horizontal jumper")

    # Solid no-tail settler; its right edge survives while its left part is
    # overwritten by the horizontal jumper in the output.
    top, left, height, width = config["solid"]
    _paint_new(grid, _rect_cells(top, left, height, width), color_solid, "solid settler")

    # Vertical valid jumper: body plus a full one-column down tail.
    top, left, height, width, tail_len = config["jumper_v"]
    body_v = _rect_cells(top, left, height, width)
    tail_v = _rect_cells(top + height, left + width - 1, tail_len, 1)
    _paint_new(grid, body_v | tail_v, color_v, "vertical jumper")

    # Invalid short tail: exactly one cell beyond the right side.
    top, left, height, width = config["short"]
    short_body = _rect_cells(top, left, height, width)
    short_tail = {(top, left + width)}
    _paint_new(grid, short_body | short_tail, color_short, "short-tail settler")

    # Invalid thick tail: a 2x2 block beyond the left side.  The body is much
    # larger than every rectangle involving the protrusion, making the intended
    # body unambiguous under the canonical strict-`>` tiebreak.
    top, left, height, width = config["thick"]
    thick_body = _rect_cells(top, left, height, width)
    thick_tail = _rect_cells(top + height - 2, left - 2, 2, 2)
    _paint_new(grid, thick_body | thick_tail, color_thick, "thick-tail settler")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    slot = int(sample_index) % len(_SCHEDULE)
    scheduled_size, transform = _SCHEDULE[slot]
    effective = dict(overrides)
    effective.setdefault("size_class", scheduled_size)

    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    size_class = ctx.draw_choice("size_class", SIZE_CLASSES)
    colors = ctx.draw_distinct_colors("role_colors", n=5, exclude={0})
    # Difficulty changes a nuisance colour-to-role permutation while preserving
    # the complete semantic grammar and every exact override domain. This makes
    # the bands observably distinct without conflating difficulty with the task.
    band_shift = {None: 0, "easy": 1, "medium": 2, "hard": 3}[difficulty]
    colors = colors[band_shift:] + colors[:band_shift]
    grid = _transform_grid(
        _build_base_scene(size_class, colors, difficulty), transform
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"size_class": size_class}:
        raise AssertionError(
            f"observable axis mismatch: expected {size_class!r}, got {observed!r}"
        )
    facts = semantic_observables(grid)
    if facts["output_collision_cells"] <= 0:
        raise AssertionError("internal layout bug: scheduled output collision vanished")
    return grid


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], len(grid), 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width
    for row in grid:
        for value in row:
            if type(value) is not int or isinstance(value, bool) or not 0 <= value <= 9:
                return ["cells must be integer ARC colours 0..9"], len(grid), width
    return [], len(grid), width


def _connected(cells: set[Cell]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = row + dr, col + dc
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _largest_filled_rect(cells: set[Cell]) -> BBox:
    """Mirror the Racket r1/c1/r2/c2 scan and strict `>` tiebreak exactly."""
    top, left, bottom, right = _bbox(cells)
    height = bottom - top + 1
    width = right - left + 1
    prefix = [[0] * (width + 1) for _ in range(height + 1)]
    for row in range(height):
        running = 0
        for col in range(width):
            running += int((top + row, left + col) in cells)
            prefix[row + 1][col + 1] = prefix[row][col + 1] + running

    def count(r1: int, c1: int, r2: int, c2: int) -> int:
        rr1, cc1 = r1 - top, c1 - left
        rr2, cc2 = r2 - top + 1, c2 - left + 1
        return (
            prefix[rr2][cc2]
            - prefix[rr1][cc2]
            - prefix[rr2][cc1]
            + prefix[rr1][cc1]
        )

    best_area = 1
    best = (top, left, top, left)
    for r1 in range(top, bottom + 1):
        for c1 in range(left, right + 1):
            for r2 in range(top, bottom + 1):
                if r2 < r1:
                    continue
                for c2 in range(left, right + 1):
                    if c2 < c1:
                        continue
                    area = (r2 - r1 + 1) * (c2 - c1 + 1)
                    if area > best_area and count(r1, c1, r2, c2) == area:
                        best_area = area
                        best = (r1, c1, r2, c2)
    return best


def _direction_and_length(body: BBox, tail: set[Cell]) -> tuple[str | None, int, BBox | None]:
    if not tail:
        return None, 0, None
    tail_box = _bbox(tail)
    tr1, tc1, tr2, tc2 = tail_box
    br1, bc1, br2, bc2 = body
    if tr1 > br2:
        direction = "down"
    elif tr2 < br1:
        direction = "up"
    elif tc1 > bc2:
        direction = "right"
    elif tc2 < bc1:
        direction = "left"
    else:
        direction = "none"
    tail_h = tr2 - tr1 + 1
    tail_w = tc2 - tc1 + 1
    tail_len = tail_h if direction in ("down", "up") else tail_w
    return direction, tail_len, tail_box


def _process_color(grid: Sequence[Sequence[int]], color: int) -> dict[str, Any]:
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    box = _bbox(cells)
    body = _largest_filled_rect(cells)
    body_cells = _bbox_cells(body)
    tail = cells - body_cells
    direction, tail_len, tail_box = _direction_and_length(body, tail)
    valid_tail = False
    if tail:
        assert tail_box is not None
        tr1, tc1, tr2, tc2 = tail_box
        tail_h = tr2 - tr1 + 1
        tail_w = tc2 - tc1 + 1
        vertical = direction in ("down", "up")
        valid_tail = (
            direction != "none"
            and (tail_w if vertical else tail_h) == 1
            and len(tail) == tail_h * tail_w
            and tail_len >= 2
        )

    if valid_tail:
        dr = tail_len if direction == "down" else -tail_len if direction == "up" else 0
        dc = tail_len if direction == "right" else -tail_len if direction == "left" else 0
        result_cells = {(row + dr, col + dc) for row, col in body_cells}
        kind = "jumper"
    else:
        result_cells = _bbox_cells(box)
        if not tail:
            kind = "settler_no_tail"
        else:
            assert tail_box is not None
            tr1, tc1, tr2, tc2 = tail_box
            tail_h = tr2 - tr1 + 1
            tail_w = tc2 - tc1 + 1
            vertical = direction in ("down", "up")
            perpendicular = tail_w if vertical else tail_h
            if direction != "none" and tail_len == 1:
                kind = "settler_short_tail"
            elif direction != "none" and perpendicular > 1:
                kind = "settler_thick_tail"
            else:
                kind = "settler_sparse_or_bent_tail"

    br1, bc1, br2, bc2 = body
    return {
        "color": color,
        "cells": cells,
        "connected": _connected(cells),
        "bbox": box,
        "body": body,
        "body_cells": body_cells,
        "body_area": len(body_cells),
        "body_height": br2 - br1 + 1,
        "body_width": bc2 - bc1 + 1,
        "tail": tail,
        "tail_box": tail_box,
        "tail_length": tail_len,
        "direction": direction,
        "valid_tail": valid_tail,
        "moved": valid_tail,
        "kind": kind,
        "result_cells": result_cells,
    }


@lru_cache(maxsize=4096)
def _analyze_grid_key(key: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    height = len(key)
    width = len(key[0])
    colors = sorted({value for row in key for value in row if value > 0})
    shapes = [_process_color(key, color) for color in colors]
    return {
        "errors": [],
        "height": height,
        "width": width,
        "colors": colors,
        "shapes": shapes,
    }


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors, height, width = _validate_grid(grid)
    if errors:
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "colors": [],
            "shapes": [],
        }
    key = tuple(tuple(int(value) for value in row) for row in grid)
    return _analyze_grid_key(key)


def _paint_result(output: Grid, cells: Iterable[Cell], color: int) -> None:
    height, width = len(output), len(output[0])
    for row, col in cells:
        # Canonical Racket paint-cells ignores off-canvas coordinates.
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = color


def rule_mirror(grid: Any) -> Grid:
    """Pure Python mirror of the selected canonical Racket program."""
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    settlers = [obj for obj in analysis["shapes"] if not obj["moved"]]
    jumpers = [obj for obj in analysis["shapes"] if obj["moved"]]
    for obj in [*settlers, *jumpers]:
        _paint_result(output, obj["result_cells"], obj["color"])
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete empirical task grammar; accepts every canonical input."""
    del meta
    errors: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        return errors + list(analysis["errors"])
    height, width = analysis["height"], analysis["width"]
    if height != width or height not in CLASS_BY_SIZE:
        errors.append("task inputs must be square with side 18, 20, or 24")
    if len(analysis["colors"]) not in (3, 5):
        errors.append(
            f"expected 3 or 5 foreground colours, found {len(analysis['colors'])}"
        )

    jumpers = 0
    settlers = 0
    for obj in analysis["shapes"]:
        color = obj["color"]
        if not obj["connected"]:
            errors.append(f"colour {color} must form one 4-connected shape")
        if obj["body_area"] < 10 or min(obj["body_height"], obj["body_width"]) < 2:
            errors.append(
                f"colour {color} has no canonical-size rectangular body "
                f"(area={obj['body_area']}, shape={obj['body_height']}x{obj['body_width']})"
            )
        if obj["tail"] and obj["direction"] == "none":
            errors.append(
                f"colour {color} has residual cells on or around multiple body sides"
            )
        if obj["valid_tail"]:
            jumpers += 1
            if not 2 <= obj["tail_length"] <= 6:
                errors.append(
                    f"colour {color} has launch tail length {obj['tail_length']}, expected 2..6"
                )
            if any(
                not (0 <= row < height and 0 <= col < width)
                for row, col in obj["result_cells"]
            ):
                errors.append(f"colour {color}'s launched body leaves the canvas")
        else:
            settlers += 1

    if jumpers not in (2, 3):
        errors.append(f"expected 2 or 3 valid jumpers, found {jumpers}")
    if settlers not in (1, 2, 3):
        errors.append(f"expected 1 to 3 settlers, found {settlers}")
    if not errors and rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("the rule must change the input")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Empirical strict manifold shared by all eight canonical rows/pairs."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze_scene(grid)
    if (analysis["height"], analysis["width"]) != (20, 20):
        errors.append("strict canonical inputs are exactly 20x20")
    if len(analysis["colors"]) not in (3, 5):
        errors.append("strict canonical inputs use 3 or 5 foreground colours")
    for obj in analysis["shapes"]:
        if not 10 <= obj["body_area"] <= 72:
            errors.append(
                f"colour {obj['color']} body area {obj['body_area']} is outside 10..72"
            )
    return errors


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    size_class = CLASS_BY_SIZE.get(analysis["height"]) if analysis["height"] == analysis["width"] else None
    jumpers = [obj for obj in analysis["shapes"] if obj["moved"]]
    settlers = [obj for obj in analysis["shapes"] if not obj["moved"]]
    settled_cells = set().union(*(obj["result_cells"] for obj in settlers)) if settlers else set()
    collision_cells = sum(
        len(obj["result_cells"] & settled_cells)
        for obj in jumpers
    )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "size_class": size_class,
        "foreground_colors": len(analysis["colors"]),
        "jumpers": len(jumpers),
        "settlers": len(settlers),
        "directions": dict(Counter(obj["direction"] for obj in jumpers)),
        "tail_lengths": dict(Counter(obj["tail_length"] for obj in jumpers)),
        "settler_kinds": dict(Counter(obj["kind"] for obj in settlers)),
        "output_collision_cells": collision_cells,
        "jumper_tail_cells": sum(len(obj["tail"]) for obj in jumpers),
        "body_areas": sorted(obj["body_area"] for obj in analysis["shapes"]),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts["size_class"] is None:
        raise ValueError("grid dimensions do not encode a declared size_class")
    return {"size_class": facts["size_class"]}


def _render_with_policy(
    grid: Any,
    *,
    move_invalid: bool = False,
    opposite: bool = False,
    body_span: bool = False,
    settlers_last: bool = False,
    preserve_tails: bool = False,
    axis_only: str | None = None,
) -> Grid:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    processed: list[dict[str, Any]] = []
    for obj in analysis["shapes"]:
        should_move = obj["valid_tail"]
        if axis_only == "horizontal" and obj["direction"] in ("up", "down"):
            should_move = False
        if axis_only == "vertical" and obj["direction"] in ("left", "right"):
            should_move = False
        if move_invalid and obj["tail"] and obj["direction"] != "none":
            should_move = True
        if should_move:
            distance = obj["tail_length"]
            if body_span:
                distance = (
                    obj["body_height"]
                    if obj["direction"] in ("up", "down")
                    else obj["body_width"]
                )
            if opposite:
                distance = -distance
            dr = distance if obj["direction"] == "down" else -distance if obj["direction"] == "up" else 0
            dc = distance if obj["direction"] == "right" else -distance if obj["direction"] == "left" else 0
            cells = {(row + dr, col + dc) for row, col in obj["body_cells"]}
            if preserve_tails and obj["valid_tail"]:
                # Wrong rival: translate the tail along with the body instead
                # of discarding it. Keeping the tail at its old coordinates is
                # often answer-equivalent because the shifted body covers that
                # corridor; translating it creates the genuinely distinct
                # "move the whole arrow" hypothesis.
                cells |= {(row + dr, col + dc) for row, col in obj["tail"]}
            processed.append({"color": obj["color"], "cells": cells, "moved": True})
        else:
            processed.append(
                {"color": obj["color"], "cells": _bbox_cells(obj["bbox"]), "moved": False}
            )
    first = [item for item in processed if item["moved"] == settlers_last]
    second = [item for item in processed if item["moved"] != settlers_last]
    for item in [*first, *second]:
        _paint_result(output, item["cells"], item["color"])
    return output


def _rival_identity(grid: Any) -> Grid:
    return [list(row) for row in grid]


def _rival_rectangularize_all(grid: Any) -> Grid:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["shapes"]:
        _paint_result(output, _bbox_cells(obj["bbox"]), obj["color"])
    return output


def _rival_move_any_protrusion(grid: Any) -> Grid:
    return _render_with_policy(grid, move_invalid=True)


def _rival_move_valid_opposite(grid: Any) -> Grid:
    return _render_with_policy(grid, opposite=True)


def _rival_move_by_body_span(grid: Any) -> Grid:
    return _render_with_policy(grid, body_span=True)


def _rival_settlers_paint_last(grid: Any) -> Grid:
    return _render_with_policy(grid, settlers_last=True)


def _rival_preserve_tails(grid: Any) -> Grid:
    return _render_with_policy(grid, preserve_tails=True)


def _rival_horizontal_only(grid: Any) -> Grid:
    return _render_with_policy(grid, axis_only="horizontal")


def _rival_vertical_only(grid: Any) -> Grid:
    return _render_with_policy(grid, axis_only="vertical")


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "identity": _rival_identity,
    "rectangularize_all": _rival_rectangularize_all,
    "move_any_protrusion": _rival_move_any_protrusion,
    "move_valid_opposite": _rival_move_valid_opposite,
    "move_by_body_span": _rival_move_by_body_span,
    "settlers_paint_last": _rival_settlers_paint_last,
    "preserve_tails": _rival_preserve_tails,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Grid]] = {}


def _valid_and_refutes(grid: Any, rival: str) -> bool:
    try:
        return not self_check(grid) and SEMANTIC_RIVALS[rival](grid) != rule_mirror(grid)
    except Exception:
        return False


def _facts_if_valid(grid: Any) -> dict[str, Any] | None:
    try:
        if self_check(grid):
            return None
        return semantic_observables(grid)
    except Exception:
        return None


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "valid_tails_launch": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and facts["jumpers"] >= 2
        and _valid_and_refutes(grid, "identity")
        and _valid_and_refutes(grid, "rectangularize_all")
    ),
    "invalid_short_tail_settles": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and facts["settler_kinds"].get("settler_short_tail", 0) >= 1
        and _valid_and_refutes(grid, "move_any_protrusion")
    ),
    "invalid_thick_tail_settles": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and facts["settler_kinds"].get("settler_thick_tail", 0) >= 1
        and _valid_and_refutes(grid, "move_any_protrusion")
    ),
    "tail_length_is_distance": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and len(facts["tail_lengths"]) >= 2
        and _valid_and_refutes(grid, "move_by_body_span")
    ),
    "tail_direction_is_vector": lambda grid: _valid_and_refutes(grid, "move_valid_opposite"),
    "both_axis_families": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and any(name in facts["directions"] for name in ("left", "right"))
        and any(name in facts["directions"] for name in ("up", "down"))
        and _valid_and_refutes(grid, "horizontal_only")
        and _valid_and_refutes(grid, "vertical_only")
    ),
    "jumpers_overwrite_settlers": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and facts["output_collision_cells"] > 0
        and _valid_and_refutes(grid, "settlers_paint_last")
    ),
    "tails_vanish": lambda grid: (
        (facts := _facts_if_valid(grid)) is not None
        and facts["jumper_tail_cells"] > 0
        and _valid_and_refutes(grid, "preserve_tails")
    ),
}

WITNESS_RIVALS = {
    "valid_tails_launch": ["identity", "rectangularize_all"],
    "invalid_short_tail_settles": ["move_any_protrusion"],
    "invalid_thick_tail_settles": ["move_any_protrusion"],
    "tail_length_is_distance": ["move_by_body_span"],
    "tail_direction_is_vector": ["move_valid_opposite"],
    "both_axis_families": ["horizontal_only", "vertical_only"],
    "jumpers_overwrite_settlers": ["settlers_paint_last"],
    "tails_vanish": ["preserve_tails"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful exact pairs whose demonstrations eliminate every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson requires at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} input is outside the task grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the pinned rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if all(competitor(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name!r} survives every demonstration")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Targeted malformed inputs that exercise the self-check boundary."""
    valid = generate(988_820, 1, difficulty="medium", size_class="canonical")
    analysis = _analyze_scene(valid)
    jumpers = [obj for obj in analysis["shapes"] if obj["valid_tail"]]
    fixtures: list[tuple[str, Grid]] = []

    hole_in_body = deepcopy(valid)
    victim = jumpers[0]
    br1, bc1, br2, bc2 = victim["body"]
    hole_in_body[(br1 + br2) // 2][(bc1 + bc2) // 2] = 0
    fixtures.append(("hole_inside_rectangular_body", hole_in_body))

    disconnected_same_color = deepcopy(valid)
    victim = analysis["shapes"][0]
    candidate = next(
        (row, col)
        for row in range(len(valid))
        for col in range(len(valid[0]))
        if valid[row][col] == 0
        and all(abs(row - r) + abs(col - c) > 1 for r, c in victim["cells"])
    )
    disconnected_same_color[candidate[0]][candidate[1]] = victim["color"]
    fixtures.append(("disconnected_same_colour_cell", disconnected_same_color))

    merged_colors = deepcopy(valid)
    source, target = analysis["shapes"][0], analysis["shapes"][1]
    for row, col in target["cells"]:
        merged_colors[row][col] = source["color"]
    fixtures.append(("two_shapes_share_one_colour", merged_colors))

    missing_colour = deepcopy(valid)
    victim = analysis["shapes"][-1]
    for row, col in victim["cells"]:
        missing_colour[row][col] = 0
    fixtures.append(("missing_foreground_role", missing_colour))

    bent_tail = deepcopy(valid)
    victim = jumpers[0]
    tail_end = max(victim["tail"], key=lambda cell: (cell[0], cell[1]))
    bent_tail[tail_end[0]][tail_end[1]] = 0
    # Reattach diagonally/sideways to the penultimate tail cell; the colour
    # remains connected but residual cells no longer lie wholly on one side.
    penultimate = min(victim["tail"], key=lambda cell: abs(cell[0] - tail_end[0]) + abs(cell[1] - tail_end[1]))
    alternatives = (
        (penultimate[0] - 1, penultimate[1]),
        (penultimate[0] + 1, penultimate[1]),
        (penultimate[0], penultimate[1] - 1),
        (penultimate[0], penultimate[1] + 1),
    )
    replacement = next(
        cell
        for cell in alternatives
        if 0 <= cell[0] < len(valid)
        and 0 <= cell[1] < len(valid[0])
        and bent_tail[cell[0]][cell[1]] == 0
    )
    bent_tail[replacement[0]][replacement[1]] = victim["color"]
    fixtures.append(("bent_launch_tail", bent_tail))

    duplicated_row = deepcopy(valid)
    duplicated_row.insert(len(duplicated_row) // 2, list(duplicated_row[len(duplicated_row) // 2]))
    fixtures.append(("noncanonical_21x20_canvas", duplicated_row))
    return fixtures
