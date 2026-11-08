"""Generator for ARC task 419ed66194f2 — relocate each object to its color anchor.

For every nonzero color, the input contains exactly one isolated single-cell
anchor and exactly one connected multi-cell source object.  The output is blank
except that each source object's bounding-box-relative shape is stamped with
its original color at the matching anchor, which denotes the target bounding
box's top-left cell.

The generator deliberately permutes source and target horizontal slots on many
draws, so color matching—not a fixed vertical translation, object order, or
position—is required.  Source objects and their translated targets never
clip or overlap in the lawful teaching distribution.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "419ed66194f2"
TASK_ID = "419ed66194f2"
VERSION = "4.0.0"
RULE_HASH = "80ec33fe7d6c"

SUMMARY = (
    "Pair each isolated one-cell color anchor with that color's connected "
    "multi-cell object, then stamp the object's bounding-box-relative shape "
    "at the anchor on a blank grid."
)

INVARIANTS = [
    "background is 0 and there are 2..5 nonzero colors",
    "each nonzero color has exactly one singleton anchor and one 3..7-cell connected source object",
    "the source object's bounding-box top-left cell is occupied",
    "every translated object fits fully in bounds and translated objects are pairwise disjoint",
    "apart from its own anchor, every translated target lies on input background",
]

PALETTE_PROFILES = ("canonical", "low", "high", "odd")
LAYOUT_PROFILES = ("aligned", "reversed")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..18",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 10..20",
        "valid": "10..20",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-aware 2..5",
        "valid": "2..5",
    },
    "palette_profile": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_PROFILES),
    },
    "layout_profile": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(LAYOUT_PROFILES),
    },
}

_PALETTE_MARKERS = {
    "canonical": 2,
    "low": 1,
    "high": 4,
    "odd": 3,
}
_PALETTE_COMMON = (5, 6, 7, 8, 9)


# All shapes are 4-connected, occupy their bounding-box top-left cell, and fit
# inside a 3x3 box.  The public examples use L, square, and T-like members of
# this family; the larger members increase compositional difficulty without
# changing the rule.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
)

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty in (None, "easy", "medium", "hard"):
        return
    if (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and 0.0 <= float(difficulty) <= 1.0
    ):
        return
    raise ValueError(
        "difficulty must be easy, medium, hard, None, or a number in [0,1]"
    )


def _slot_ranges(width: int, count: int) -> list[tuple[int, int]]:
    """Return count disjoint [start, stop) column slots, each at least 2 wide."""
    if width < 2 * count:
        raise ValueError(f"grid_w={width} cannot realize n_colors={count}")
    base, extra = divmod(width, count)
    slots: list[tuple[int, int]] = []
    start = 0
    for index in range(count):
        slot_width = base + (1 if index < extra else 0)
        slots.append((start, start + slot_width))
        start += slot_width
    return slots


def _shape_size(shape: tuple[tuple[int, int], ...]) -> int:
    return len(shape)


def _shape_bounds(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _shape_candidates(
    *,
    difficulty: Any,
    max_height: int,
    max_width: int,
) -> list[tuple[tuple[int, int], ...]]:
    if difficulty == "easy" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) < 0.34
    ):
        size_lo, size_hi = 3, 4
    elif difficulty == "hard" or (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and float(difficulty) > 0.66
    ):
        size_lo, size_hi = 4, 7
    else:
        size_lo, size_hi = 3, 5
    candidates = [
        shape
        for shape in _SHAPES
        if size_lo <= _shape_size(shape) <= size_hi
        and _shape_bounds(shape)[0] <= max_height
        and _shape_bounds(shape)[1] <= max_width
    ]
    if not candidates:
        # Exact small dimension overrides remain lawful.  Fall back only to a
        # smaller semantic difficulty, never to a different requested axis.
        candidates = [
            shape
            for shape in _SHAPES
            if _shape_bounds(shape)[0] <= max_height
            and _shape_bounds(shape)[1] <= max_width
        ]
    if not candidates:
        raise ValueError(
            f"no source shape fits a {max_height}x{max_width} slot"
        )
    return candidates


def _source_slot_order(count: int, profile: str) -> list[int]:
    if profile == "aligned":
        return list(range(count))
    if profile == "reversed":
        return list(reversed(range(count)))
    raise ValueError(f"unknown layout_profile {profile!r}")


def _palette_colors(profile: str, count: int, rng) -> list[int]:
    if profile not in _PALETTE_MARKERS:
        raise ValueError(f"unknown palette_profile {profile!r}")
    colors = [_PALETTE_MARKERS[profile]]
    colors.extend(rng.sample(list(_PALETTE_COMMON), count - 1))
    rng.shuffle(colors)
    return colors


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be ARC color integers 0..9"]
    height = len(grid)
    if not 7 <= height <= 30 or not 7 <= width <= 30:
        return [f"grid dimensions {height}x{width} outside supported 7..30"]
    return []


def _components_for_color(
    grid: list[list[int]] | tuple[tuple[int, ...], ...], color: int
) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        component: set[tuple[int, int]] = set()
        unseen.remove(start)
        while queue:
            row, col = queue.popleft()
            component.add((row, col))
            for dr, dc in _DIRECTIONS:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors, "colors": {}, "targets": {}}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    colors = sorted({value for row in grid for value in row if value != 0})
    if not 2 <= len(colors) <= 5:
        errors.append(f"expected 2..5 nonzero colors, got {len(colors)}")
        return result

    occupied = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    all_targets: set[tuple[int, int]] = set()

    for color in colors:
        components = _components_for_color(grid, color)
        anchors = [component for component in components if len(component) == 1]
        source_components = [component for component in components if len(component) > 1]
        if len(anchors) != 1 or len(source_components) != 1:
            errors.append(
                f"color {color} must have exactly one singleton anchor and one "
                f"multi-cell object; got {len(anchors)} and {len(source_components)}"
            )
            continue
        anchor = next(iter(anchors[0]))
        source = source_components[0]
        if not 3 <= len(source) <= 7:
            errors.append(
                f"color {color} source size must be 3..7; got {len(source)}"
            )
            continue
        row0 = min(row for row, _ in source)
        col0 = min(col for _, col in source)
        if (row0, col0) not in source:
            errors.append(
                f"color {color} source must occupy its bounding-box top-left"
            )
            continue
        target = {
            (anchor[0] + row - row0, anchor[1] + col - col0)
            for row, col in source
        }
        if any(
            not (0 <= row < height and 0 <= col < width)
            for row, col in target
        ):
            errors.append(f"color {color} translated object leaves the grid")
            continue
        if target & all_targets:
            errors.append(f"color {color} translated object overlaps another target")
            continue
        forbidden = (target - {anchor}) & occupied
        if forbidden:
            errors.append(
                f"color {color} translated target covers {len(forbidden)} "
                "non-anchor input cells"
            )
            continue
        all_targets.update(target)
        result["colors"][color] = {
            "anchor": anchor,
            "source": source,
            "source_bbox": (row0, col0),
            "source_size": len(source),
        }
        result["targets"][color] = target

    if len(result["colors"]) != len(colors):
        return result
    result.update(
        {
            "height": height,
            "width": width,
            "n_colors": len(colors),
            "all_targets": all_targets,
            "all_anchors_above_sources": all(
                facts["anchor"][0] < facts["source_bbox"][0]
                for facts in result["colors"].values()
            ),
            "object_sizes": tuple(
                sorted(facts["source_size"] for facts in result["colors"].values())
            ),
        }
    )
    return result


def _slot_index(slots: list[tuple[int, int]], column: int) -> int:
    for index, (start, stop) in enumerate(slots):
        if start <= column < stop:
            return index
    raise ValueError(f"column {column} does not belong to a slot")


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))

    colors = set(analysis["colors"])
    marker_hits = [
        profile
        for profile, marker in _PALETTE_MARKERS.items()
        if marker in colors
    ]
    if len(marker_hits) != 1:
        raise ValueError(
            "generated palette must contain exactly one profile marker; "
            f"found {marker_hits}"
        )

    slots = _slot_ranges(analysis["width"], analysis["n_colors"])
    source_order: list[int | None] = [None] * analysis["n_colors"]
    for facts in analysis["colors"].values():
        target_index = _slot_index(slots, facts["anchor"][1])
        source_index = _slot_index(slots, facts["source_bbox"][1])
        if source_order[target_index] is not None:
            raise ValueError(f"multiple anchors occupy target slot {target_index}")
        source_order[target_index] = source_index
    if any(index is None for index in source_order):
        raise ValueError("not every target slot contains an anchor")
    realized_order = [int(index) for index in source_order]
    if realized_order == list(range(analysis["n_colors"])):
        layout_profile = "aligned"
    elif realized_order == list(reversed(range(analysis["n_colors"]))):
        layout_profile = "reversed"
    else:
        raise ValueError(f"source-slot order {realized_order} is not declared")

    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_colors": analysis["n_colors"],
        "palette_profile": marker_hits[0],
        "layout_profile": layout_profile,
    }


def semantic_observables(grid: list[list[int]]) -> dict[str, Any]:
    """Task-linked observables used by focused tests and evidence censuses."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    observed = observe_overrides(grid)
    return {
        **observed,
        "object_sizes": analysis["object_sizes"],
        "all_anchors_above_sources": analysis["all_anchors_above_sources"],
        "target_cell_count": len(analysis["all_targets"]),
        "targets_nonoverlapping": True,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete anchor/object teaching grammar."""
    errors = list(_analysis(grid)["errors"])
    if errors:
        return errors

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    if isinstance(overrides, dict) and overrides:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
            return errors
        for axis, requested in overrides.items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"{axis} override requested {requested!r}, "
                    f"observed {observed[axis]!r}"
                )
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the Racket program remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for color, cells in analysis["targets"].items():
        for row, col in cells:
            output[row][col] = color
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_difficulty(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_colors = ctx.draw_int_diff("n_colors", 2, 5)
    height = ctx.draw_int_diff("grid_h", 8, 18)
    width = ctx.draw_int_diff("grid_w", 10, 20)
    palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)
    layout_profile = ctx.draw_choice("layout_profile", LAYOUT_PROFILES)

    slots = _slot_ranges(width, n_colors)
    target_height = height // 2
    source_start = target_height + 1
    source_height = height - source_start
    if target_height < 3 or source_height < 3:
        raise ValueError(f"grid_h={height} leaves insufficient target/source zones")

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    colors = _palette_colors(palette_profile, n_colors, palette_rng)
    source_order = _source_slot_order(n_colors, layout_profile)

    grid = full_grid(height, width, 0)
    for color_index, color in enumerate(colors):
        target_start, target_stop = slots[color_index]
        source_start_col, source_stop_col = slots[source_order[color_index]]
        max_shape_width = min(
            target_stop - target_start,
            source_stop_col - source_start_col,
        )
        candidates = _shape_candidates(
            difficulty=difficulty,
            max_height=min(target_height, source_height),
            max_width=max_shape_width,
        )
        # Offset by the color index so repeated colors within a lesson are not
        # likely to receive identical prototypes even when the RNG repeats.
        shape = candidates[(layout_rng.randrange(len(candidates)) + color_index) % len(candidates)]
        shape_height, shape_width = _shape_bounds(shape)

        target_row = layout_rng.randint(0, target_height - shape_height)
        target_col = target_start + layout_rng.randint(
            0, target_stop - target_start - shape_width
        )
        source_row = source_start + layout_rng.randint(
            0, source_height - shape_height
        )
        source_col = source_start_col + layout_rng.randint(
            0, source_stop_col - source_start_col - shape_width
        )

        # The input carries only the target's top-left marker; the complete
        # translated target is produced by the Racket oracle.
        grid[target_row][target_col] = color
        for row, col in shape:
            grid[source_row + row][source_col + col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid color-relocation scene: " + "; ".join(errors))
    return grid
