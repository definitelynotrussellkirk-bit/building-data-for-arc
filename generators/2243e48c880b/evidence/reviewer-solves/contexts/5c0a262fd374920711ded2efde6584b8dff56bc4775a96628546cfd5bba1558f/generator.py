"""Constructive inputs for ``Recolor by size rank`` (2243e48c880b).

The selected Racket authority finds monochromatic 4-connected components in
row-major discovery order, stably sorts them by cell count, and paints the
three ranked objects 2, 4, and 8 on a blank canvas.  Equal-size objects are
therefore ordered by their first row-major cell.  This sampler deliberately
includes ties and disconnected objects sharing an input color, two distinctions
that the previous generator omitted.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2243e48c880b"
TASK_ID = GENERATOR_ID
RULE_HASH = "d78310e1c969"
VERSION = "3.1.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Exactly three separated monochromatic 4-connected objects on background 0. "
    "Object sizes may be distinct or tied; ties use row-major component order. "
    "One, two, or three input colors are possible, so disconnected same-color "
    "objects distinguish component size from total color frequency. The output "
    "authority stably sorts objects by cell count and recolors them 2, 4, 8."
)

INVARIANTS = [
    "exactly three monochromatic 4-connected nonzero components",
    "generated components are non-overlapping; same-color components stay disconnected",
    "each component has 2..6 cells; equal-size components are lawful",
    "one to three nonzero colors may be shared by disconnected components",
    "the Racket authority, not this input sampler, supplies labels",
]

SIZE_PATTERNS = ("distinct", "smallest_tie", "largest_tie", "all_tied")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "8..12; strongly favors canonical heights 8..9",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "9..14; strongly favors canonical widths 9..11",
        "valid": "9..14",
    },
    "size_pattern": {
        "type": "str",
        "default": "3-slot lesson schedule: smallest tie, largest tie, distinct anchor",
        "valid": "|".join(SIZE_PATTERNS),
    },
    "palette_size": {
        "type": "int",
        "default": "3-slot lesson schedule: 2, 2, 3",
        "valid": "1..3",
    },
}

_BOUNDS = {"grid_h": (8, 12), "grid_w": (9, 14), "palette_size": (1, 3)}
_TARGET_COLORS = (2, 4, 8)


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _BOUNDS:
            lo, hi = _BOUNDS[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        elif name == "size_pattern":
            if type(value) is not str or value not in SIZE_PATTERNS:
                raise ValueError(f"size_pattern must be one of {SIZE_PATTERNS}")


def _weighted_choice(ctx, label: str, domain, favored, weight: int):
    """Keep every exact override lawful while biasing ordinary draws."""
    options = list(domain) + list(favored) * weight
    return ctx.draw_choice(label, options)


def _scheduled_choice(ctx, label: str, domain, scheduled):
    """Record a deterministic lesson slot without narrowing exact overrides."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, tuple(domain))
    return ctx.draw_choice(label, (scheduled,))


def _draw_axes(ctx, difficulty):
    # Every three consecutive draws form a rotation-safe lesson: two examples
    # refute every declared rival directly, then one canonical-profile anchor
    # keeps ordinary sampling close to the selected demonstrations.
    slot = ctx.sample_index % 3
    if slot == 2:
        anchor_profiles = ((8, 10), (9, 9), (8, 11), (9, 10))
        anchor_h, anchor_w = anchor_profiles[(ctx.sample_index // 3) % len(anchor_profiles)]
        h = _scheduled_choice(ctx, "grid_h", range(8, 13), anchor_h)
        w = _scheduled_choice(ctx, "grid_w", range(9, 15), anchor_w)
        pattern = _scheduled_choice(ctx, "size_pattern", SIZE_PATTERNS, "distinct")
        palette = _scheduled_choice(ctx, "palette_size", (1, 2, 3), 3)
    else:
        h = _weighted_choice(ctx, "grid_h", range(8, 13), (8, 9), 18)
        w = _weighted_choice(ctx, "grid_w", range(9, 15), (9, 10, 11), 14)
        scheduled_pattern = "smallest_tie" if slot == 0 else "largest_tie"
        pattern = _scheduled_choice(ctx, "size_pattern", SIZE_PATTERNS, scheduled_pattern)
        palette = _scheduled_choice(ctx, "palette_size", (1, 2, 3), 2)
    return h, w, pattern, palette


def _draw_sizes(ctx, pattern: str, difficulty) -> list[int]:
    rng = ctx.draw_rng(f"object_sizes_{difficulty or 'all'}")
    # The canonical task uses sizes 3..6.  Including size 2 broadens shape
    # support without stressing the smallest canonical canvases.
    values = list(range(2, 7))
    if pattern == "distinct":
        return sorted(rng.sample(values, 3))
    if pattern == "all_tied":
        upper = 4 if difficulty == "easy" else 6
        value = rng.randint(2, upper)
        return [value, value, value]
    small = rng.randint(2, 5)
    large = rng.randint(small + 1, 6)
    if pattern == "smallest_tie":
        return [small, small, large]
    if pattern == "largest_tie":
        return [small, large, large]
    raise ValueError(f"unknown size pattern: {pattern}")


def _discovery_order(blobs: list[set[tuple[int, int]]]):
    return sorted(blobs, key=lambda cells: min(cells))


def _place_blobs(ctx, h: int, w: int, sizes: list[int], *, require_scrambled: bool):
    """Place all three blobs or fail; never silently drop a requested object."""
    rng = ctx.draw_rng("layout")
    for _attempt in range(96):
        requested = list(sizes)
        rng.shuffle(requested)
        used: set[tuple[int, int]] = set()
        blobs: list[set[tuple[int, int]]] = []
        for size in requested:
            blob = grow_blob(rng, h, w, used, size, max_attempts=160)
            if blob is None:
                break
            blobs.append(blob)
            used |= blob
        if len(blobs) != 3:
            continue
        discovered = _discovery_order(blobs)
        discovered_sizes = [len(cells) for cells in discovered]
        if require_scrambled and discovered_sizes == sorted(discovered_sizes):
            continue
        return blobs
    raise RuntimeError(
        f"could not place three isolated blobs of sizes {sizes} on {h}x{w}"
    )


def _assign_colors(ctx, blobs, palette_size: int):
    colors = list(ctx.draw_distinct_colors("input_colors", n=palette_size, exclude=(0,)))
    discovered = _discovery_order(blobs)
    ranked = sorted(discovered, key=len)  # stable: discovery order breaks ties
    assignment: dict[frozenset[tuple[int, int]], int] = {}
    if palette_size == 1:
        for blob in blobs:
            assignment[frozenset(blob)] = colors[0]
    elif palette_size == 2:
        # Repeat a color on the rank extremes.  Total-frequency ranking then
        # places the unique middle-rank color first, unlike component ranking.
        assignment[frozenset(ranked[0])] = colors[0]
        assignment[frozenset(ranked[1])] = colors[1]
        assignment[frozenset(ranked[2])] = colors[0]
    else:
        # Discovery-order assignment keeps palette independent of size rank.
        for blob, color in zip(discovered, colors):
            assignment[frozenset(blob)] = color
    return assignment


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, pattern, palette_size = _draw_axes(ctx, difficulty)
    sizes = _draw_sizes(ctx, pattern, difficulty)
    # The high-probability two-color/two-level-tie profile is made a direct
    # counterexample to reading-order ranking as well as color-frequency ranking.
    require_scrambled = palette_size == 2 and pattern in ("smallest_tie", "largest_tie")
    blobs = _place_blobs(ctx, h, w, sizes, require_scrambled=require_scrambled)
    assignment = _assign_colors(ctx, blobs, palette_size)
    grid = full_grid(h, w, 0)
    for blob in blobs:
        color = assignment[frozenset(blob)]
        for r, c in blob:
            grid[r][c] = color
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 8 <= len(grid) <= 12 or not 9 <= width <= 14:
        return [f"grid dimensions must be within 8..12 by 9..14, got {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid):
    """Match Racket ``objects``: row-major, monochromatic, 4-connected."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            while queue:
                cr, cc = queue.pop(0)
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _size_pattern(sizes) -> str | None:
    a, b, c = sorted(sizes)
    if a < b < c:
        return "distinct"
    if a == b == c:
        return "all_tied"
    if a == b < c:
        return "smallest_tie"
    if a < b == c:
        return "largest_tie"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler's task domain, including canonical size ties."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    components = _components(grid)
    if len(components) != 3:
        return [f"expected exactly 3 monochromatic components, got {len(components)}"]
    sizes = [obj["size"] for obj in components]
    if any(not 2 <= size <= 6 for size in sizes):
        errors.append(f"component sizes must be in 2..6, got {sorted(sizes)}")
    if _size_pattern(sizes) not in SIZE_PATTERNS:
        errors.append(f"unsupported size relation: {sorted(sizes)}")
    colors = {obj["color"] for obj in components}
    if not 1 <= len(colors) <= 3:
        errors.append(f"expected 1..3 nonzero colors, got {len(colors)}")

    # Different colors may touch orthogonally and remain distinct under the
    # selected monochromatic object primitive; canonical train[1] uses this.
    return errors


def strict_canonical_like(grid):
    """All ordinary draws and all four selected canonical inputs are strict."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "size_pattern": _size_pattern([obj["size"] for obj in components]),
        "palette_size": len({obj["color"] for obj in components}),
    }


def _paint(grid, ordered_components):
    if len(ordered_components) != 3:
        raise ValueError(f"rule domain requires exactly 3 objects, got {len(ordered_components)}")
    out = [[0 for _ in row] for row in grid]
    for target, obj in zip(_TARGET_COLORS, ordered_components):
        for r, c in obj["cells"]:
            out[r][c] = target
    return out


def rule_mirror(grid):
    """Independent Python mirror used only for checks and rival witnesses."""
    components = _components(grid)
    return _paint(grid, sorted(components, key=lambda obj: obj["size"]))


def _color_total_frequency(grid):
    """WRONG: rank every object by the total frequency of its input color."""
    components = _components(grid)
    totals = Counter()
    for obj in components:
        totals[obj["color"]] += obj["size"]
    return _paint(grid, sorted(components, key=lambda obj: totals[obj["color"]]))


def _row_major_only(grid):
    """WRONG: assign 2/4/8 in discovery order and ignore cell count."""
    return _paint(grid, _components(grid))


def _reverse_equal_ties(grid):
    """WRONG: rank by size but reverse row-major order within equal sizes."""
    components = _components(grid)
    indexed = list(enumerate(components))
    ordered = [obj for _, obj in sorted(indexed, key=lambda item: (item[1]["size"], -item[0]))]
    return _paint(grid, ordered)


def _input_color_order(grid):
    """WRONG: assign ranks by the numeric input color."""
    return _paint(grid, sorted(_components(grid), key=lambda obj: obj["color"]))


def _descending_size(grid):
    """WRONG: largest-to-smallest rather than smallest-to-largest."""
    return _paint(grid, sorted(_components(grid), key=lambda obj: obj["size"], reverse=True))


SEMANTIC_RIVALS = {
    "color_total_frequency": _color_total_frequency,
    "row_major_only": _row_major_only,
    "reverse_equal_ties": _reverse_equal_ties,
    "input_color_order": _input_color_order,
    "descending_size": _descending_size,
}


def _differs(name):
    rival = SEMANTIC_RIVALS[name]
    return lambda grid: rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "color_total_counterexample": _differs("color_total_frequency"),
    "row_major_counterexample": _differs("row_major_only"),
    "stable_tie_counterexample": _differs("reverse_equal_ties"),
    "input_color_counterexample": _differs("input_color_order"),
    "descending_counterexample": _differs("descending_size"),
}
WITNESS_RIVALS = {
    "color_total_counterexample": ["color_total_frequency"],
    "row_major_counterexample": ["row_major_only"],
    "stable_tie_counterexample": ["reverse_equal_ties"],
    "input_color_counterexample": ["input_color_order"],
    "descending_counterexample": ["descending_size"],
}
# Every selected canonical input uses one distinct color per object, making total
# color frequency exactly equal to component size. Generated shared-color cases
# are therefore required to distinguish this shortcut.
CANONICAL_SHORTCUTS = {"color_total_frequency": _color_total_frequency}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require every declared rival to fail on at least one demonstration."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    checked = []
    for pair in demos:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["each demonstration needs input and output grids"]
        errors = self_check(pair["input"])
        if errors:
            return errors
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            return ["demonstration output disagrees with the selected stable size rule"]
        checked.append(pair)
    query_input = query.get("input") if isinstance(query, dict) else query
    errors = self_check(query_input)
    if errors:
        return errors

    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        disagreements = sum(rival(pair["input"]) != pair["output"] for pair in checked)
        if disagreements == 0:
            reasons.append(f"unrefuted rival: {name}")
    return reasons
