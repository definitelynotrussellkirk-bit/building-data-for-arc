"""Generator for ``079291c08c15`` — swap two objects' anchors.

The authoritative task contains exactly two monochrome, 4-connected objects.
On a blank canvas, each object is translated so its bounding-box top-left
anchor becomes the other object's original anchor; shape, orientation, and
color are preserved.

Generated lessons deliberately exclude three implementation artifacts that are
not supported by the canonical description or examples: a third object being
dropped, clipping at an incompatible destination, and paint-order overlap.
Those are useful negative probes, not lawful training examples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "079291c08c15"
TASK_ID = "079291c08c15"
VERSION = "4.0.0"
RULE_HASH = "5094a920e351"

SUMMARY = (
    "Exactly two horizontally separated objects exchange their bounding-box "
    "top-left anchors on a blank canvas. Each object keeps its shape, "
    "orientation, and color; both translated footprints fit fully and remain "
    "disjoint."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly two non-background 4-connected monochrome objects",
    "the objects use distinct colors and occupy strictly left/right bboxes",
    "their normalized shapes differ, refuting a color-swap-in-place shortcut",
    "both anchor-swapped footprints fit fully and do not overlap",
    "the anchor exchange changes the grid",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..18",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 10..20",
        "valid": "10..20",
    },
}


class _Component:
    __slots__ = (
        "color",
        "cells",
        "top",
        "left",
        "bottom",
        "right",
        "normalized",
    )

    def __init__(
        self,
        *,
        color: int,
        cells: frozenset[tuple[int, int]],
        top: int,
        left: int,
        bottom: int,
        right: int,
        normalized: frozenset[tuple[int, int]],
    ) -> None:
        self.color = color
        self.cells = cells
        self.top = top
        self.left = left
        self.bottom = bottom
        self.right = right
        self.normalized = normalized

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1

    @property
    def width(self) -> int:
        return self.right - self.left + 1


def _grow(rng, count: int, *, max_h: int, max_w: int) -> list[tuple[int, int]]:
    """Grow one normalized 4-connected polyomino with bounded dimensions."""
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(600):
        if len(cells) >= count:
            break
        row, col = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        candidate = (row + dr, col + dc)
        if candidate in seen:
            continue
        rows = [r for r, _ in seen] + [candidate[0]]
        cols = [c for _, c in seen] + [candidate[1]]
        if max(rows) - min(rows) + 1 > max_h:
            continue
        if max(cols) - min(cols) + 1 > max_w:
            continue
        seen.add(candidate)
        cells.append(candidate)
    if len(cells) != count:
        raise ValueError("could not grow requested bounded shape")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return sorted((row - min_row, col - min_col) for row, col in cells)


def _components(grid: list[list[int]]) -> list[_Component]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[_Component] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (row + dr, col + dc)
                    nr, nc = neighbor
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if neighbor in seen or grid[nr][nc] != color:
                        continue
                    seen.add(neighbor)
                    stack.append(neighbor)
            top = min(row for row, _ in cells)
            left = min(col for _, col in cells)
            bottom = max(row for row, _ in cells)
            right = max(col for _, col in cells)
            normalized = frozenset(
                (row - top, col - left) for row, col in cells
            )
            found.append(
                _Component(
                    color=color,
                    cells=frozenset(cells),
                    top=top,
                    left=left,
                    bottom=bottom,
                    right=right,
                    normalized=normalized,
                )
            )
    return sorted(found, key=lambda component: (component.left, component.top))


def _translated_cells(
    component: _Component, top: int, left: int
) -> set[tuple[int, int]]:
    return {
        (top + row, left + col)
        for row, col in component.normalized
    }


def _paint_rule_result(
    grid: list[list[int]], components: list[_Component]
) -> list[list[int]] | None:
    """Mirror the executable Racket rule, including its edge-case behavior."""
    if len(components) < 2:
        return None
    height, width = len(grid), len(grid[0])
    left_component, right_component = components[:2]
    output = full_grid(height, width, 0)
    for row, col in _translated_cells(
        left_component, right_component.top, right_component.left
    ):
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = left_component.color
    for row, col in _translated_cells(
        right_component, left_component.top, left_component.left
    ):
        if 0 <= row < height and 0 <= col < width:
            output[row][col] = right_component.color
    return output


def _analyze(grid) -> dict:
    errors: list[str] = []
    facts: dict = {}
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a nonempty list"], "facts": facts}
    if not all(isinstance(row, list) for row in grid):
        return {"errors": ["every row must be a list"], "facts": facts}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": facts}
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                return {"errors": errors, "facts": facts}

    height = len(grid)
    components = _components(grid)
    facts.update({
        "height": height,
        "width": width,
        "components": components,
        "component_count": len(components),
    })
    if len(components) != 2:
        errors.append(
            f"found {len(components)} objects; the task requires exactly two"
        )
        return {"errors": errors, "facts": facts}

    left_component, right_component = components
    if left_component.color == right_component.color:
        errors.append("the two objects must use distinct colors")
    if left_component.left == right_component.left:
        errors.append("the objects share a bbox-left anchor")
    if left_component.right >= right_component.left:
        errors.append("the objects must occupy strictly separated left/right bboxes")
    if left_component.normalized == right_component.normalized:
        errors.append(
            "the normalized shapes match, leaving color-swap-in-place answer-equivalent"
        )

    left_at_right = _translated_cells(
        left_component, right_component.top, right_component.left
    )
    right_at_left = _translated_cells(
        right_component, left_component.top, left_component.left
    )
    swap_fits = all(
        0 <= row < height and 0 <= col < width
        for row, col in left_at_right | right_at_left
    )
    if not swap_fits:
        errors.append("at least one anchor-swapped footprint would clip")
    if left_at_right & right_at_left:
        errors.append("the anchor-swapped footprints overlap")

    output = _paint_rule_result(grid, components)
    if output == grid:
        errors.append("the anchor exchange is an identity transformation")

    facts.update({
        "left": left_component,
        "right": right_component,
        "left_at_right": left_at_right,
        "right_at_left": right_at_left,
        "swap_fits": swap_fits,
        "swap_overlap": bool(left_at_right & right_at_left),
        "output": output,
        "top_relation": (
            "left_higher"
            if left_component.top < right_component.top
            else "left_lower"
            if left_component.top > right_component.top
            else "same_top"
        ),
        "size_relation": (
            "left_larger"
            if left_component.size > right_component.size
            else "right_larger"
            if left_component.size < right_component.size
            else "equal_size"
        ),
    })
    return {"errors": errors, "facts": facts}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 8, 18)
    width = ctx.draw_int_diff("grid_w", 10, 20)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        size_lo, size_hi = 3, 5
    elif difficulty == "hard":
        size_lo, size_hi = 5, 9
    elif difficulty == "medium":
        size_lo, size_hi = 4, 7
    else:
        size_lo, size_hi = 3, 8

    max_shape_height = min(6, height)
    max_shape_width = min(5, (width - 1) // 2)
    for _attempt in range(300):
        left_size = rng.randint(size_lo, size_hi)
        right_size = rng.randint(size_lo, size_hi)
        left_shape = _grow(
            rng,
            left_size,
            max_h=max_shape_height,
            max_w=max_shape_width,
        )
        right_shape = _grow(
            rng,
            right_size,
            max_h=max_shape_height,
            max_w=max_shape_width,
        )
        left_normalized = frozenset(left_shape)
        right_normalized = frozenset(right_shape)
        if left_normalized == right_normalized:
            continue
        left_h = max(row for row, _ in left_shape) + 1
        left_w = max(col for _, col in left_shape) + 1
        right_h = max(row for row, _ in right_shape) + 1
        right_w = max(col for _, col in right_shape) + 1
        common_h = max(left_h, right_h)
        common_w = max(left_w, right_w)
        if common_h > height or 2 * common_w + 1 > width:
            continue

        left_top = rng.randint(0, height - common_h)
        right_top = rng.randint(0, height - common_h)
        left_col = rng.randint(0, width - (2 * common_w + 1))
        right_col = rng.randint(left_col + common_w + 1, width - common_w)
        left_color, right_color = rng.sample(range(1, 10), 2)

        grid = full_grid(height, width, 0)
        for row, col in left_shape:
            grid[left_top + row][left_col + col] = left_color
        for row, col in right_shape:
            grid[right_top + row][right_col + col] = right_color

        analysis = _analyze(grid)
        if not analysis["errors"]:
            return grid
    raise ValueError("could not realize a lawful two-object anchor swap")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not teach the canonical two-object anchor swap."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis directly from the rendered grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}
    return {"grid_h": len(grid), "grid_w": width}


def semantic_signature(grid) -> dict[str, str | int | bool]:
    """Return linked task semantics for coverage/stability audits."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"valid": False, "error_count": len(analysis["errors"])}
    facts = analysis["facts"]
    left_component = facts["left"]
    right_component = facts["right"]
    return {
        "valid": True,
        "top_relation": facts["top_relation"],
        "size_relation": facts["size_relation"],
        "left_size": left_component.size,
        "right_size": right_component.size,
        "left_color": left_component.color,
        "right_color": right_component.color,
        "swap_fits": facts["swap_fits"],
        "swap_overlap": facts["swap_overlap"],
    }


def rule_mirror(grid):
    """Independent Python test mirror; Racket remains output authority."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    return _paint_rule_result(grid, _components(grid))


# Backward-compatible private name used by existing diagnostics.
_mirror = rule_mirror
