"""Semantic generator for ARC task ``68b0ca39134c``.

The rule keeps the uniquely largest 4-connected nonzero component, preserving
its cells and color, and erases every smaller component to background 0.

Ordinary draws alternate between complete canonical-linked morphology and a
shortcut-killing generalized profile.  Every generalized profile puts a
smaller component above and to the left of the true target and reuses the
target color on that distractor.  This refutes both public-fitting shortcuts:
"keep the leftmost component" and "keep every cell of the modal color".
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "68b0ca39134c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3f1cd489429c"
MIN_STRICT_FRAC = 0.30
EXAMPLES_NEEDED = 3

SUMMARY = (
    "An 8..16 by 8..16 zero-background grid contains two to four separated, "
    "monochrome 4-connected components. Exactly one component has the largest "
    "area (4..6 cells); every other component is strictly smaller. The output "
    "copies only that uniquely largest component in its original position and "
    "color and turns every smaller component into background 0."
)

INVARIANTS = [
    "background is 0 and every foreground value is an ARC color 1..9",
    "there are 2..4 monochrome 4-connected nonzero components",
    "one component is uniquely largest with 4..6 cells",
    "every smaller component has fewer cells than the largest",
    "normal draws are non-identity because at least one distractor is erased",
]

COUNTER_HYPOTHESES = [
    "keep the leftmost or topmost component",
    "keep every cell of the most frequent foreground color",
    "keep a fixed color or a fixed five-cell template",
    "keep the component with the largest bounding box rather than area",
    "erase a fixed position or memorize the public canvas sizes",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 8/9 or difficulty-aware rng 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 8/9 or difficulty-aware rng 8..16",
        "valid": "8..16",
    },
    "component_count": {
        "type": "int",
        "default": "canonical 2/3 or difficulty-aware rng 2..4",
        "valid": "2..4",
    },
    "largest_size": {
        "type": "int",
        "default": "canonical 4/5/6 or difficulty-aware rng 4..6",
        "valid": "4..6",
    },
    "color_mode": {
        "type": "str",
        "default": "distinct on canonical profiles; shared on generalized profiles",
        "valid": "distinct|shared",
    },
    "largest_shape_kind": {
        "type": "str",
        "default": "bent on canonical profiles; rng compact|bent otherwise",
        "valid": "compact|bent",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)

# Train[0], train[1], test[0], normalized to their own bounding boxes.  Object
# locations and colors are nuisance factors; the linked profile keeps canvas
# dimensions and the complete multiset of rule-relevant object signatures.
_CANONICAL_COMPONENT_SHAPES = (
    (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (0, 1), (1, 1)),
    ),
)
_CANONICAL_DIMS = ((8, 8), (9, 9), (9, 9))

# (h, w, distinct-color-count, linked sorted object signatures), where each
# object signature is (cell_count, min_bbox_dim, max_bbox_dim, bbox_holes).
_CANONICAL_SIGNATURES = frozenset(
    {
        (8, 8, 2, ((6, 3, 3, 3), (3, 2, 2, 1))),
        (9, 9, 3, ((4, 2, 3, 2), (3, 2, 2, 1), (3, 2, 2, 1))),
        (9, 9, 3, ((5, 2, 4, 3), (3, 2, 2, 1), (3, 2, 2, 1))),
    }
)

SCHEDULE_PROFILES = (
    "canonical_size6",
    "generalized",
    "canonical_size4",
    "canonical_size5",
)


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    bounds = {
        "grid_h": (8, 16),
        "grid_w": (8, 16),
        "component_count": (2, 4),
        "largest_size": (4, 6),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in bounds:
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"override {name!r} must be an integer")
            lo, hi = bounds[name]
            if not lo <= value <= hi:
                raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
        elif name == "color_mode" and value not in ("distinct", "shared"):
            raise ValueError("override 'color_mode' must be 'distinct' or 'shared'")
        elif name == "largest_shape_kind" and value not in ("compact", "bent"):
            raise ValueError(
                "override 'largest_shape_kind' must be 'compact' or 'bent'"
            )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every three consecutive sample indexes include a generalized witness."""
    del seed, difficulty
    slot = sample_index % 6
    if slot % 2:
        return "generalized"
    return ("canonical_size6", "canonical_size4", "canonical_size5")[slot // 2]


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _normalize_shape(cells)
    h = max(r for r, _ in norm) + 1
    return _normalize_shape((c, h - 1 - r) for r, c in norm)


def _flip_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    norm = _normalize_shape(cells)
    w = max(c for _, c in norm) + 1
    return _normalize_shape((r, w - 1 - c) for r, c in norm)


def _d4_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: list[tuple[tuple[int, int], ...]] = []
    cur = _normalize_shape(cells)
    for _ in range(4):
        for candidate in (cur, _flip_shape(cur)):
            if candidate not in variants:
                variants.append(candidate)
        cur = _rotate_shape(cur)
    return tuple(variants)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    norm = _normalize_shape(cells)
    return max(r for r, _ in norm) + 1, max(c for _, c in norm) + 1


def _largest_shape(size: int, kind: str) -> tuple[tuple[int, int], ...]:
    if kind == "compact":
        return {
            4: ((0, 0), (0, 1), (1, 0), (1, 1)),
            5: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
            6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        }[size]
    return {
        4: ((0, 0), (0, 1), (0, 2), (1, 0)),
        5: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
        6: ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    }[size]


_SMALL_SHAPES_BY_SIZE = {
    1: (((0, 0),),),
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
}


def _components_4conn(grid: Any) -> list[dict[str, Any]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                colors.add(grid[rr][cc])
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (rr + dr, cc + dc)
                    nr, nc = nxt
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            comps.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": frozenset(colors),
                    "color": grid[r][c],
                    "bbox": (r0, r1, c0, c1),
                }
            )
    return comps


def _object_signature(component: dict[str, Any]) -> tuple[int, int, int, int]:
    r0, r1, c0, c1 = component["bbox"]
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    size = len(component["cells"])
    return size, min(bh, bw), max(bh, bw), bh * bw - size


def canonical_profile_signature(grid: Any):
    errors = _grid_errors(grid)
    if errors:
        return None
    comps = _components_4conn(grid)
    if not comps or any(len(comp["colors"]) != 1 for comp in comps):
        return None
    linked = tuple(sorted((_object_signature(comp) for comp in comps), reverse=True))
    distinct_colors = len({comp["color"] for comp in comps})
    return len(grid), len(grid[0]), distinct_colors, linked


def strict_canonical_like(grid: Any) -> list[str]:
    signature = canonical_profile_signature(grid)
    if signature is None:
        return ["grid has invalid shape/colors or a multicolor connected component"]
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked canonical signature mismatch: {signature!r}"]
    sizes = [part[0] for part in signature[3]]
    if len(sizes) < 2 or sizes[0] == sizes[1]:
        return ["canonical profile must have a unique largest component"]
    return []


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar for nondegenerate largest-component lessons."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 16 and 8 <= w <= 16):
        errors.append(f"dimensions {h}x{w} outside 8..16")
    comps = _components_4conn(grid)
    if not (2 <= len(comps) <= 4):
        errors.append(f"expected 2..4 components, found {len(comps)}")
    if any(len(comp["colors"]) != 1 for comp in comps):
        errors.append("each 4-connected component must be monochrome")
    sizes = sorted((len(comp["cells"]) for comp in comps), reverse=True)
    if not sizes or not 4 <= sizes[0] <= 6:
        errors.append(f"largest component must have 4..6 cells, got sizes={sizes}")
    if len(sizes) >= 2 and sizes[0] == sizes[1]:
        errors.append(f"largest component is not unique: sizes={sizes}")
    if sizes and any(size >= sizes[0] for size in sizes[1:]):
        errors.append(f"distractor is not strictly smaller: sizes={sizes}")
    if all(value != 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    comps = _components_4conn(grid)
    if not comps:
        raise ValueError("cannot observe axes from a grid with no components")
    largest = max(comps, key=lambda comp: len(comp["cells"]))
    largest_color = largest["color"]
    shared = any(
        comp is not largest and comp["color"] == largest_color for comp in comps
    )
    _, _, _, holes = _object_signature(largest)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(comps),
        "largest_size": len(largest["cells"]),
        "color_mode": "shared" if shared else "distinct",
        "largest_shape_kind": "compact" if holes <= 1 else "bent",
    }


def _draw_banded_int(
    ctx,
    overrides: dict[str, Any],
    name: str,
    band_range: tuple[int, int],
    full_range: tuple[int, int],
) -> int:
    lo, hi = full_range if name in overrides and overrides[name] is not None else band_range
    return ctx.draw_int(name, lo, hi)


def _is_free_4(grid, shape, top: int, left: int) -> bool:
    h, w = len(grid), len(grid[0])
    coords = {(top + r, left + c) for r, c in shape}
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in coords):
        return False
    for r, c in coords:
        if grid[r][c] != 0:
            return False
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) not in coords and 0 <= nr < h and 0 <= nc < w:
                if grid[nr][nc] != 0:
                    return False
    return True


def _paint(grid, shape, top: int, left: int, color: int) -> None:
    for r, c in shape:
        grid[top + r][left + c] = color


def _place_canonical(shapes, colors, h: int, w: int, rng):
    for _ in range(100):
        grid = full_grid(h, w, 0)
        success = True
        for shape, color in zip(shapes, colors):
            variants = list(_d4_variants(shape))
            rng.shuffle(variants)
            candidates: list[tuple[tuple[tuple[int, int], ...], int, int]] = []
            for variant in variants:
                sh, sw = _shape_dims(variant)
                for top in range(h - sh + 1):
                    for left in range(w - sw + 1):
                        if _is_free_4(grid, variant, top, left):
                            candidates.append((variant, top, left))
            if not candidates:
                success = False
                break
            variant, top, left = rng.choice(candidates)
            _paint(grid, variant, top, left, color)
        if success:
            return grid
    raise ValueError("could not place canonical component profile")


def _place_generalized(shapes, colors, h: int, w: int, rng):
    """Place first distractor top-left and the largest component bottom-right."""
    largest = shapes[0]
    small = list(shapes[1:])
    grid = full_grid(h, w, 0)

    # Every generalized lesson has the public-shortcut discriminator: a smaller
    # component is both topmost/leftmost and shares the target's color.
    first = small[0]
    _paint(grid, first, 0, 0, colors[1])

    lh, lw = _shape_dims(largest)
    _paint(grid, largest, h - lh, w - lw, colors[0])

    anchors = ((0, w), (h, 0))
    for index, (shape, color) in enumerate(zip(small[1:], colors[2:])):
        sh, sw = _shape_dims(shape)
        base_r, base_c = anchors[index]
        preferred = (0 if base_r == 0 else h - sh, w - sw if base_c == w else 0)
        candidates = [preferred]
        candidates.extend(
            (r, c)
            for r in range(h - sh + 1)
            for c in range(w - sw + 1)
            if (r, c) != preferred
        )
        if len(candidates) > 1:
            tail = candidates[1:]
            rng.shuffle(tail)
            candidates = [candidates[0], *tail]
        for top, left in candidates:
            if _is_free_4(grid, shape, top, left):
                _paint(grid, shape, top, left, color)
                break
        else:
            raise ValueError("could not place generalized distractor set")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, band)
    canonical_index = {
        "canonical_size6": 0,
        "canonical_size4": 1,
        "canonical_size5": 2,
    }.get(profile)
    canonical_mode = canonical_index is not None and not overrides

    if canonical_mode:
        h0, w0 = _CANONICAL_DIMS[canonical_index]
        shapes = list(_CANONICAL_COMPONENT_SHAPES[canonical_index])
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        component_count = ctx.draw_int("component_count", len(shapes), len(shapes))
        largest_size = ctx.draw_int("largest_size", len(shapes[0]), len(shapes[0]))
        color_mode = ctx.draw_choice("color_mode", ("distinct",))
        shape_kind = ctx.draw_choice("largest_shape_kind", ("bent",))
        color_rng = ctx.draw_rng("colors")
        colors = color_rng.sample(range(1, 10), component_count)
        grid = _place_canonical(shapes, colors, h, w, ctx.draw_rng("layout"))
    else:
        ranges = {
            "easy": ((8, 10), (8, 10), (2, 3), (4, 5)),
            "medium": ((9, 13), (9, 13), (2, 4), (4, 6)),
            "hard": ((12, 16), (12, 16), (3, 4), (5, 6)),
        }[band]
        h = _draw_banded_int(ctx, overrides, "grid_h", ranges[0], (8, 16))
        w = _draw_banded_int(ctx, overrides, "grid_w", ranges[1], (8, 16))
        component_count = _draw_banded_int(
            ctx, overrides, "component_count", ranges[2], (2, 4)
        )
        largest_size = _draw_banded_int(
            ctx, overrides, "largest_size", ranges[3], (4, 6)
        )
        if "color_mode" in overrides and overrides["color_mode"] is not None:
            color_mode = ctx.draw_choice("color_mode", ("distinct", "shared"))
        else:
            color_mode = ctx.draw_choice("color_mode", ("shared",))
        shape_kind = ctx.draw_choice(
            "largest_shape_kind", ("compact", "bent")
        )
        shape_rng = ctx.draw_rng("shapes")
        largest = _largest_shape(largest_size, shape_kind)
        largest = shape_rng.choice(_d4_variants(largest))
        small_sizes = [3, 2, 1][: component_count - 1]
        small_shapes = [
            shape_rng.choice(_SMALL_SHAPES_BY_SIZE[size]) for size in small_sizes
        ]
        shapes = [largest, *small_shapes]
        color_rng = ctx.draw_rng("colors")
        if color_mode == "distinct":
            colors = color_rng.sample(range(1, 10), component_count)
        else:
            target_color = color_rng.choice(range(1, 10))
            remaining = [color for color in range(1, 10) if color != target_color]
            color_rng.shuffle(remaining)
            colors = [target_color, target_color, *remaining[: component_count - 2]]
        grid = _place_generalized(shapes, colors, h, w, ctx.draw_rng("layout"))

    errors = self_check(grid, difficulty=band)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, "
                f"observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Named public-fitting shortcuts and lesson-level identifiability
# ---------------------------------------------------------------------------

def _keep_component(grid, component):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c in component["cells"]:
        out[r][c] = grid[r][c]
    return out


def _authoritative_python(grid):
    comps = _components_4conn(grid)
    if not comps:
        return full_grid(len(grid), len(grid[0]), 0)
    best = max(
        comps,
        key=lambda comp: (
            len(comp["cells"]),
            -comp["bbox"][0],
            -comp["bbox"][2],
        ),
    )
    return _keep_component(grid, best)


def _rival_keep_leftmost(grid):
    comps = _components_4conn(grid)
    if not comps:
        return full_grid(len(grid), len(grid[0]), 0)
    chosen = min(comps, key=lambda comp: (comp["bbox"][2], comp["bbox"][0]))
    return _keep_component(grid, chosen)


def _rival_keep_modal_color(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return full_grid(len(grid), len(grid[0]), 0)
    color = min(counts, key=lambda value: (-counts[value], value))
    return [[value if value == color else 0 for value in row] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "keep_leftmost_component": _rival_keep_leftmost,
    "keep_modal_color_everywhere": _rival_keep_modal_color,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_largest_not_leftmost(grid) -> bool:
    comps = _components_4conn(grid)
    if len(comps) < 2:
        return False
    largest = max(comps, key=lambda comp: len(comp["cells"]))
    leftmost = min(comps, key=lambda comp: (comp["bbox"][2], comp["bbox"][0]))
    return largest is not leftmost


def _witness_largest_color_reused(grid) -> bool:
    comps = _components_4conn(grid)
    if len(comps) < 2:
        return False
    largest = max(comps, key=lambda comp: len(comp["cells"]))
    return any(
        comp is not largest and comp["color"] == largest["color"] for comp in comps
    )


SEMANTIC_WITNESSES = {
    "largest_not_leftmost": _witness_largest_not_leftmost,
    "largest_color_reused": _witness_largest_color_reused,
}
WITNESS_RIVALS = {
    "largest_not_leftmost": ["keep_leftmost_component"],
    "largest_color_reused": ["keep_modal_color_everywhere"],
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if not all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            ):
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives demos and query")
            else:
                reasons.append(f"competitor {name!r} fits all demos but disagrees on query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
