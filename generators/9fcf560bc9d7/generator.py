"""Generator for 9fcf560bc9d7: crop the source by mask/source overlap.

A color-5 divider splits the input into equal left MASK and right SOURCE
panels.  The answer is the complete SOURCE subgrid inside the tight bounding
box of panel-relative cells that are nonzero in both panels.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fcf560bc9d7"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "84d3a38174ed"

SUMMARY = (
    "Split the input at its solid color-5 divider into equal MASK and SOURCE "
    "panels. Find panel-relative positions that are nonzero in both panels, "
    "take their tight bounding box, and return the entire SOURCE crop inside "
    "that box, preserving source colors and zeros."
)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "background is 0 and the one-column separator is solid color 5",
    "the separator divides two equal-size panels",
    "each panel's nonzero support is 4-connected and the overlap is nonempty",
    "the overlap bbox is a proper sub-rectangle of the panel",
    "the output preserves every source value inside the overlap bbox",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical-weighted", "valid": "4..6"},
    "panel_w": {"type": "int", "default": "scheduled canonical-weighted", "valid": "4..6"},
    "overlap_cells": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
    "mask_only_cells": {"type": "int", "default": "alternates 0 and 1..2", "valid": "0..2"},
    "src_only_cells": {"type": "int", "default": "alternates 0 and 2..3", "valid": "0..3"},
    "mask_palette_size": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
    "src_palette_size": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# Even profiles stay very close to the three official examples.  Every odd
# profile contains all three decisive decoys: mask-only outside the overlap
# bbox, source-only outside it, and source-only inside it.  Therefore every
# two-consecutive-example lesson contains a rival-killing demonstration.
_PROFILES = (
    {"name": "canonical_four", "h": 4, "pw": 4, "overlap": 4, "mask_only": 0, "src_only": 0, "mp": 1, "sp": 2},
    {"name": "decisive_compact", "h": 4, "pw": 4, "overlap": 4, "mask_only": 1, "src_only": 2, "mp": 1, "sp": 2},
    {"name": "canonical_six", "h": 4, "pw": 4, "overlap": 6, "mask_only": 0, "src_only": 0, "mp": 1, "sp": 2},
    {"name": "decisive_tall", "h": 5, "pw": 4, "overlap": 5, "mask_only": 2, "src_only": 2, "mp": 2, "sp": 3},
    {"name": "canonical_wide", "h": 4, "pw": 5, "overlap": 5, "mask_only": 0, "src_only": 0, "mp": 1, "sp": 2},
    {"name": "decisive_wide", "h": 5, "pw": 5, "overlap": 6, "mask_only": 1, "src_only": 3, "mp": 1, "sp": 3},
    {"name": "canonical_large", "h": 6, "pw": 4, "overlap": 7, "mask_only": 0, "src_only": 0, "mp": 2, "sp": 3},
    {"name": "decisive_large", "h": 6, "pw": 6, "overlap": 7, "mask_only": 2, "src_only": 3, "mp": 2, "sp": 4},
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 2, "hard": 4}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in _BAND_OFFSET:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[(int(sample_index) + _BAND_OFFSET[difficulty]) % len(_PROFILES)]["name"]


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    ranges = {
        "grid_h": (4, 6),
        "panel_w": (4, 6),
        "overlap_cells": (4, 7),
        "mask_only_cells": (0, 2),
        "src_only_cells": (0, 3),
        "mask_palette_size": (1, 2),
        "src_palette_size": (2, 4),
    }
    for name, (lo, hi) in ranges.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _neighbors(cell: tuple[int, int], h: int, w: int) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _CARDINAL:
        rr, cc = r + dr, c + dc
        if 0 <= rr < h and 0 <= cc < w:
            yield rr, cc


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        cell = todo.pop()
        for nxt in _neighbors(cell, 10_000, 10_000):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return seen == cells


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _inside(cell: tuple[int, int], box: tuple[int, int, int, int]) -> bool:
    r, c = cell
    r0, c0, r1, c1 = box
    return r0 <= r <= r1 and c0 <= c <= c1


def _sample_overlap(
    rng,
    h: int,
    w: int,
    count: int,
    need_inner_gap: bool,
) -> tuple[set[tuple[int, int]], tuple[int, int, int, int]] | None:
    candidates = []
    for bh in range(2, h):
        for bw in range(2, w):
            area = bh * bw
            if area < count + int(need_inner_gap):
                continue
            # A proper bbox leaves at least one row or column outside it.
            for r0 in range(h - bh + 1):
                for c0 in range(w - bw + 1):
                    candidates.append((r0, c0, bh, bw))
    rng.shuffle(candidates)
    for r0, c0, bh, bw in candidates:
        local = [(r, c) for r in range(r0, r0 + bh) for c in range(c0, c0 + bw)]
        for _ in range(120):
            cells = set(rng.sample(local, count))
            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            if min(rows) != r0 or max(rows) != r0 + bh - 1:
                continue
            if min(cols) != c0 or max(cols) != c0 + bw - 1:
                continue
            if not _connected(cells):
                continue
            box = (r0, c0, r0 + bh - 1, c0 + bw - 1)
            if need_inner_gap and all(cell in cells for cell in local):
                continue
            return cells, box
    return None


def _grow_cells(
    rng,
    support: set[tuple[int, int]],
    count: int,
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    *,
    outside_box: tuple[int, int, int, int] | None = None,
) -> set[tuple[int, int]] | None:
    chosen: set[tuple[int, int]] = set()
    current = set(support)
    for _ in range(count):
        frontier = {
            nxt
            for cell in current
            for nxt in _neighbors(cell, h, w)
            if nxt not in current and nxt not in forbidden
        }
        if outside_box is not None:
            frontier = {cell for cell in frontier if not _inside(cell, outside_box)}
        if not frontier:
            return None
        pick = rng.choice(sorted(frontier))
        chosen.add(pick)
        current.add(pick)
    return chosen


def _partition_connected_colors(
    rng,
    support: set[tuple[int, int]],
    colors: tuple[int, ...],
    h: int,
    w: int,
) -> dict[tuple[int, int], int]:
    """Partition one connected support into connected monochrome regions."""
    ordered = sorted(support)
    first = rng.choice(ordered)
    seeds = [first]
    occupied = {first}
    while len(seeds) < len(colors):
        frontier = sorted({n for p in occupied for n in _neighbors(p, h, w) if n in support - occupied})
        if not frontier:
            frontier = sorted(support - occupied)
        pick = rng.choice(frontier)
        seeds.append(pick)
        occupied.add(pick)

    assignment = {seed: color for seed, color in zip(seeds, colors)}
    regions = {color: {seed} for seed, color in zip(seeds, colors)}
    remaining = support - set(seeds)
    while remaining:
        choices = []
        for color, cells in regions.items():
            for cell in cells:
                for nxt in _neighbors(cell, h, w):
                    if nxt in remaining:
                        choices.append((color, nxt))
        if not choices:
            raise AssertionError("connected support partition lost its frontier")
        color, cell = rng.choice(choices)
        assignment[cell] = color
        regions[color].add(cell)
        remaining.remove(cell)
    return assignment


def _construct_layout(
    rng,
    h: int,
    panel_w: int,
    overlap_count: int,
    mask_only_count: int,
    src_only_count: int,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]], tuple[int, int, int, int]]:
    for _ in range(300):
        sampled = _sample_overlap(rng, h, panel_w, overlap_count, src_only_count > 0)
        if sampled is None:
            continue
        overlap, box = sampled

        src_only: set[tuple[int, int]] = set()
        if src_only_count:
            inner_frontier = sorted({
                nxt
                for cell in overlap
                for nxt in _neighbors(cell, h, panel_w)
                if nxt not in overlap and _inside(nxt, box)
            })
            if not inner_frontier:
                continue
            src_only.add(rng.choice(inner_frontier))

        mask_only = _grow_cells(
            rng,
            overlap,
            mask_only_count,
            h,
            panel_w,
            forbidden=set(src_only),
            outside_box=box,
        )
        if mask_only is None:
            continue

        remaining_src = src_only_count - len(src_only)
        src_outer = _grow_cells(
            rng,
            overlap | src_only,
            remaining_src,
            h,
            panel_w,
            forbidden=set(mask_only),
            outside_box=box,
        )
        if src_outer is None:
            continue
        src_only |= src_outer

        if (overlap | mask_only) & src_only:
            continue
        if not _connected(overlap | mask_only):
            continue
        if not _connected(overlap | src_only):
            continue
        return overlap, mask_only, src_only, box
    raise ValueError("could not construct a lawful mask/source layout after 300 attempts")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILES[(int(sample_index) + _BAND_OFFSET[difficulty]) % len(_PROFILES)]
    h = _draw_exact_int(ctx, overrides, "grid_h", profile["h"], 4, 6)
    panel_w = _draw_exact_int(ctx, overrides, "panel_w", profile["pw"], 4, 6)
    overlap_count = _draw_exact_int(ctx, overrides, "overlap_cells", profile["overlap"], 4, 7)
    mask_only_count = _draw_exact_int(ctx, overrides, "mask_only_cells", profile["mask_only"], 0, 2)
    src_only_count = _draw_exact_int(ctx, overrides, "src_only_cells", profile["src_only"], 0, 3)
    mask_palette_size = _draw_exact_int(ctx, overrides, "mask_palette_size", profile["mp"], 1, 2)
    src_palette_size = _draw_exact_int(ctx, overrides, "src_palette_size", profile["sp"], 2, 4)

    rng = ctx.draw_rng("layout")
    overlap, mask_only, src_only, _ = _construct_layout(
        rng, h, panel_w, overlap_count, mask_only_count, src_only_count
    )

    available = [1, 2, 3, 4, 6, 7, 8, 9]
    palette = rng.sample(available, mask_palette_size + src_palette_size)
    mask_colors = tuple(palette[:mask_palette_size])
    src_colors = tuple(palette[mask_palette_size:])
    mask_values = _partition_connected_colors(rng, overlap | mask_only, mask_colors, h, panel_w)
    src_values = _partition_connected_colors(rng, overlap | src_only, src_colors, h, panel_w)

    grid = full_grid(h, panel_w * 2 + 1, 0)
    separator = panel_w
    for r in range(h):
        grid[r][separator] = 5
    for (r, c), value in mask_values.items():
        grid[r][c] = value
    for (r, c), value in src_values.items():
        grid[r][separator + 1 + c] = value

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
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
        return ["grid cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, width = len(grid), len(grid[0])
    if width % 2 != 1:
        errors.append(f"expected width 2*panel_w+1, found {width}")
        return {"errors": errors, "h": h, "width": width}
    panel_w = width // 2
    if not 4 <= h <= 6:
        errors.append(f"grid height must be in 4..6, found {h}")
    if not 4 <= panel_w <= 6:
        errors.append(f"panel width must be in 4..6, found {panel_w}")
    if any(grid[r][panel_w] != 5 for r in range(h)):
        errors.append("separator column must be solid color 5")

    mask = {(r, c) for r in range(h) for c in range(panel_w) if grid[r][c] != 0}
    src = {(r, c) for r in range(h) for c in range(panel_w) if grid[r][panel_w + 1 + c] != 0}
    overlap = mask & src
    mask_only = mask - src
    src_only = src - mask
    if not mask:
        errors.append("mask panel is empty")
    if not src:
        errors.append("source panel is empty")
    if mask and not _connected(mask):
        errors.append("mask support must be 4-connected")
    if src and not _connected(src):
        errors.append("source support must be 4-connected")
    box = _bbox(overlap) if overlap else None
    if not overlap:
        errors.append("mask/source overlap is empty")
    elif box == (0, 0, h - 1, panel_w - 1):
        errors.append("overlap bbox may not span the entire panel")

    mask_colors = {grid[r][c] for r, c in mask}
    src_colors = {grid[r][panel_w + 1 + c] for r, c in src}
    if not 1 <= len(mask_colors) <= 2:
        errors.append(f"mask palette size must be in 1..2, found {len(mask_colors)}")
    if not 2 <= len(src_colors) <= 4:
        errors.append(f"source palette size must be in 2..4, found {len(src_colors)}")
    return {
        "errors": errors,
        "h": h,
        "width": width,
        "panel_w": panel_w,
        "mask": mask,
        "src": src,
        "overlap": overlap,
        "mask_only": mask_only,
        "src_only": src_only,
        "box": box,
        "mask_colors": mask_colors,
        "src_colors": src_colors,
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    box = facts["box"]
    return {
        "grid_h": facts["h"],
        "panel_w": facts["panel_w"],
        "overlap_cells": len(facts["overlap"]),
        "mask_only_cells": len(facts["mask_only"]),
        "src_only_cells": len(facts["src_only"]),
        "mask_palette_size": len(facts["mask_colors"]),
        "src_palette_size": len(facts["src_colors"]),
        "mask_only_outside_bbox": sum(not _inside(cell, box) for cell in facts["mask_only"]),
        "src_only_outside_bbox": sum(not _inside(cell, box) for cell in facts["src_only"]),
        "src_only_inside_bbox": sum(_inside(cell, box) for cell in facts["src_only"]),
        "supports_differ": facts["mask"] != facts["src"],
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    return {axis: facts[axis] for axis in AXES} if facts else {}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical profile without imposing curriculum-only decoys."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    if facts["grid_h"] != 4:
        errors.append(f"canonical grid height is 4, found {facts['grid_h']}")
    if facts["panel_w"] != 4:
        errors.append(f"canonical panel width is 4, found {facts['panel_w']}")
    if len({value for row in grid for value in row}) != 5:
        errors.append("canonical examples use exactly five total colors")
    return errors


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("invalid overlap-crop grid: " + "; ".join(facts["errors"]))
    r0, c0, r1, c1 = facts["box"]
    offset = facts["panel_w"] + 1
    return [[grid[r][offset + c] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _crop_panel(grid: list[list[int]], panel: str, cells: set[tuple[int, int]]) -> list[list[int]]:
    if not cells:
        return [[0]]
    facts = _analysis(grid)
    r0, c0, r1, c1 = _bbox(cells)
    offset = 0 if panel == "mask" else facts["panel_w"] + 1
    return [[grid[r][offset + c] for c in range(c0, c1 + 1)] for r in range(r0, r1 + 1)]


def _rival_crop_source_support(grid):
    facts = _analysis(grid)
    return _crop_panel(grid, "src", facts["src"]) if not facts["errors"] else [list(row) for row in grid]


def _rival_crop_mask_support(grid):
    facts = _analysis(grid)
    return _crop_panel(grid, "src", facts["mask"]) if not facts["errors"] else [list(row) for row in grid]


def _rival_zero_nonoverlap(grid):
    facts = _analysis(grid)
    if facts["errors"]:
        return [list(row) for row in grid]
    r0, c0, r1, c1 = facts["box"]
    offset = facts["panel_w"] + 1
    return [
        [grid[r][offset + c] if (r, c) in facts["overlap"] else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "crop_source_support": _rival_crop_source_support,
    "crop_mask_support": _rival_crop_mask_support,
    "zero_nonoverlap_inside_crop": _rival_zero_nonoverlap,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "mask_only_outside_overlap_bbox": lambda grid: semantic_observables(grid).get("mask_only_outside_bbox", 0) > 0,
    "src_only_outside_overlap_bbox": lambda grid: semantic_observables(grid).get("src_only_outside_bbox", 0) > 0,
    "src_only_inside_overlap_bbox": lambda grid: semantic_observables(grid).get("src_only_inside_bbox", 0) > 0,
    "supports_differ": lambda grid: bool(semantic_observables(grid).get("supports_differ")),
    "multicolor_source": lambda grid: semantic_observables(grid).get("src_palette_size", 0) >= 2,
}
WITNESS_RIVALS = {
    "mask_only_outside_overlap_bbox": ["crop_mask_support"],
    "src_only_outside_overlap_bbox": ["crop_source_support"],
    "src_only_inside_overlap_bbox": ["zero_nonoverlap_inside_crop"],
}


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a named canonical-fitting shortcut survives demos."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(_freeze(competitor(d["input"])) == _freeze(d["output"]) for d in demos)
        if survives and _freeze(competitor(query["input"])) != _freeze(query["output"]):
            reasons.append(f"competitor {name!r} fits every demo but changes the query")
    return reasons
