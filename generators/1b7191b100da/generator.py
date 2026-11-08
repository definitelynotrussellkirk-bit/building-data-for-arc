"""Generator for ``repeat_the_template_by_marker_count``.

A lawful scene has one sparse, connected non-maroon template object and one to
four maroon marker cells.  The output is the cropped template repeated
horizontally once per marker cell, with exactly one background column between
copies.

The marker schedule deliberately includes adjacent marker cells.  That is the
load-bearing counterexample to the tempting shortcut "repeat once per marker
component"; the canonical task counts marker *cells*, not components.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b7191b100da"
TASK_ID = "1b7191b100da"
VERSION = "3.0.1"
RULE_HASH = "90961ca428e3"

SUMMARY = (
    "On a 0-background grid, find the single connected non-9 template object. "
    "Crop its bounding box, count every color-9 marker cell, and repeat the "
    "cropped template horizontally that many times with one zero column "
    "between consecutive copies. Marker adjacency is irrelevant: count cells, "
    "not marker components."
)

INVARIANTS = [
    "background is color 0",
    "there are 1-4 color-9 marker cells outside the template bbox",
    "all nonzero non-9 cells form exactly one 4-connected monochrome template",
    "the template bbox is 2-4 rows by 2-4 columns and contains at least one zero",
    "the output preserves the cropped template's internal zeros and uses one-column gaps",
]

# Any four consecutive ordinary sample indices contain marker counts 2, 3, 4,
# and 1, including both separated and adjacent-marker scenes.  The materialized
# lesson gate therefore cannot alias onto a fixed-count or component-count rule.
EXAMPLES_NEEDED = 4

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed draw over 8..11",
        "valid": "8..11",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed draw over 9..12",
        "valid": "9..12",
    },
    "n_9": {
        "type": "int",
        "default": "four-slot schedule 2,3,4,1",
        "valid": "1..4",
    },
    "template_h": {
        "type": "int",
        "default": "seed/sample-index schedule over 2..4",
        "valid": "2..4",
    },
    "template_w": {
        "type": "int",
        "default": "seed/sample-index schedule over 2..4",
        "valid": "2..4",
    },
    "template_color": {
        "type": "color",
        "default": "keyed draw over 1..8",
        "valid": "1..8",
    },
}

# Every Cartesian product of the declared boundary values is feasible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_TEMPLATE_COLORS = {3, 4, 6}
_MARKER_SCHEDULE = (2, 3, 4, 1)
_CANONICAL_PROFILE_SCHEDULE = (
    (8, 10, 4),
    (9, 12, 6),
    (8, 11, 3),
    None,
    None,
    None,
    None,
    None,
)


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_int(ctx, name: str, value: int, lo: int, hi: int) -> int:
    """Record a deterministic schedule value while keeping exact overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (value,))


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _spans_box(cells: set[tuple[int, int]], h: int, w: int) -> bool:
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return 0 in rows and h - 1 in rows and 0 in cols and w - 1 in cols


def _make_template(rng, h: int, w: int) -> set[tuple[int, int]]:
    """Return a connected, bbox-spanning, non-solid small polyomino."""
    area = h * w
    for _ in range(512):
        keep_probability = rng.uniform(0.42, 0.72)
        cells = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if rng.random() < keep_probability
        }
        if not (3 <= len(cells) < area):
            continue
        if _spans_box(cells, h, w) and _connected(cells):
            return cells

    # Deterministic sparse fallback: an L spanning the whole bbox, rotated by
    # the caller's later placement randomness only through the rejection path.
    cells = {(0, c) for c in range(w)} | {(r, w - 1) for r in range(h)}
    if len(cells) == area:  # only possible for 2x2; remove one non-corner arm.
        cells.remove((0, 0))
        cells.add((1, 0))
    return cells


def _marker_components(grid: list[list[int]]) -> int:
    marker_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    components = 0
    while marker_cells:
        components += 1
        start = marker_cells.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIR4:
                nxt = (r + dr, c + dc)
                if nxt in marker_cells:
                    marker_cells.remove(nxt)
                    queue.append(nxt)
    return components


def _pick_scattered(
    rng, candidates: list[tuple[int, int]], count: int,
    *, forbidden_adjacent: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]] | None:
    """Choose pairwise non-adjacent cells, also isolated from a fixed cluster."""
    forbidden_adjacent = set(forbidden_adjacent or ())
    pool = list(candidates)
    rng.shuffle(pool)
    chosen: list[tuple[int, int]] = []
    for cell in pool:
        r, c = cell
        if any(abs(r - rr) + abs(c - cc) <= 1 for rr, cc in forbidden_adjacent):
            continue
        if any(abs(r - rr) + abs(c - cc) <= 1 for rr, cc in chosen):
            continue
        chosen.append(cell)
        if len(chosen) == count:
            return chosen
    return None


def _pick_clustered(
    rng, candidates: list[tuple[int, int]], count: int,
) -> list[tuple[int, int]] | None:
    """Pick one adjacent cluster plus, when possible, one isolated marker."""
    available = set(candidates)
    cluster_size = count if count == 2 else count - 1
    segments: list[list[tuple[int, int]]] = []
    for r, c in sorted(available):
        for dr, dc in ((0, 1), (1, 0)):
            segment = [(r + i * dr, c + i * dc) for i in range(cluster_size)]
            if all(cell in available for cell in segment):
                segments.append(segment)
    rng.shuffle(segments)
    for cluster in segments:
        if cluster_size == count:
            return cluster
        remaining = [cell for cell in candidates if cell not in cluster]
        isolated = _pick_scattered(
            rng, remaining, count - cluster_size,
            forbidden_adjacent=set(cluster),
        )
        if isolated is not None:
            return cluster + isolated
    return None


def _place_markers(
    rng,
    candidates: list[tuple[int, int]],
    count: int,
    *,
    clustered: bool,
) -> list[tuple[int, int]]:
    picked = (
        _pick_clustered(rng, candidates, count)
        if clustered and count > 1
        else _pick_scattered(rng, candidates, count)
    )
    if picked is None:
        # The grid/template domains leave ample room, so reaching this fallback
        # indicates a programming error rather than a lawful stochastic miss.
        raise RuntimeError(
            f"unable to place {count} {'clustered' if clustered else 'scattered'} markers"
        )
    return picked


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Three of every eight ordinary draws pin one of the real canonical
    # (height, width, template-color) profiles.  This keeps every difficulty
    # band anchored to the source task instead of letting the hard-band size
    # skew erase canonical support.  Exact caller overrides still win.
    profile = _CANONICAL_PROFILE_SCHEDULE[sample_index % len(_CANONICAL_PROFILE_SCHEDULE)]
    if profile is None:
        grid_h = ctx.draw_int_diff("grid_h", 8, 11)
        grid_w = ctx.draw_int_diff("grid_w", 9, 12)
    else:
        grid_h = _scheduled_int(ctx, "grid_h", profile[0], 8, 11)
        grid_w = _scheduled_int(ctx, "grid_w", profile[1], 9, 12)

    slot = sample_index % len(_MARKER_SCHEDULE)
    n_9 = _scheduled_int(ctx, "n_9", _MARKER_SCHEDULE[slot], 1, 4)
    template_h = _scheduled_int(
        ctx, "template_h", 2 + ((seed + sample_index) % 3), 2, 4
    )
    template_w = _scheduled_int(
        ctx, "template_w", 2 + (((seed // 7) + sample_index // 2) % 3), 2, 4
    )
    template_color = (
        ctx.draw_int("template_color", 1, 8)
        if profile is None
        else _scheduled_int(ctx, "template_color", profile[2], 1, 8)
    )

    shape_rng = ctx.draw_rng("template_shape")
    layout_rng = ctx.draw_rng("layout")
    marker_rng = ctx.draw_rng("marker_layout")
    local_template = _make_template(shape_rng, template_h, template_w)

    # Keep a one-cell zero moat around the template.  This makes the roles
    # visually and structurally separable without changing the Racket rule.
    top = layout_rng.randint(1, grid_h - template_h - 1)
    left = layout_rng.randint(1, grid_w - template_w - 1)
    global_template = {(top + r, left + c) for r, c in local_template}

    grid = full_grid(grid_h, grid_w, 0)
    for r, c in global_template:
        grid[r][c] = template_color

    blocked = {
        (r, c)
        for r in range(max(0, top - 1), min(grid_h, top + template_h + 1))
        for c in range(max(0, left - 1), min(grid_w, left + template_w + 1))
    }
    marker_candidates = [
        (r, c)
        for r in range(grid_h)
        for c in range(grid_w)
        if (r, c) not in blocked
    ]

    # Slots 1 and 2 contain adjacent markers; slots 0 and 3 are separated.
    # Exact n_9 overrides remain legal, and the same slot policy is observable.
    clustered = slot in (1, 2) and n_9 > 1
    markers = _place_markers(
        marker_rng, marker_candidates, n_9, clustered=clustered
    )
    for r, c in markers:
        grid[r][c] = 9

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator defect: {errors}")
    return grid


def _template_info(grid: list[list[int]]):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    colors = {
        grid[r][c]
        for r, c in cells
    }
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    return cells, colors, (r0, c0, r1, c1)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact non-dimension axis from the returned grid."""
    info = _template_info(grid)
    if info is None:
        template_h = template_w = template_color = -1
    else:
        _, colors, (r0, c0, r1, c1) = info
        template_h = r1 - r0 + 1
        template_w = c1 - c0 + 1
        template_color = next(iter(colors)) if len(colors) == 1 else -1
    return {
        "n_9": sum(value == 9 for row in grid for value in row),
        "template_h": template_h,
        "template_w": template_w,
        "template_color": template_color,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lesson grammar and reject shortcut-hiding impostors."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    height = len(grid)
    errors: list[str] = []
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} exceed ARC bounds")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    marker_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    }
    if not 1 <= len(marker_cells) <= 4:
        errors.append(f"expected 1-4 color-9 marker cells, found {len(marker_cells)}")

    info = _template_info(grid)
    if info is None:
        errors.append("no non-9 template cells")
        return errors
    cells_list, colors, (r0, c0, r1, c1) = info
    cells = set(cells_list)
    if len(colors) != 1:
        errors.append(f"template must be monochrome, found colors {sorted(colors)}")
    if not _connected(cells):
        errors.append("non-9 template cells must form one 4-connected object")

    template_h = r1 - r0 + 1
    template_w = c1 - c0 + 1
    if not 2 <= template_h <= 4 or not 2 <= template_w <= 4:
        errors.append(
            f"template bbox must be 2..4 by 2..4, found {template_h}x{template_w}"
        )
    if len(cells) == template_h * template_w:
        errors.append("template bbox is solid; at least one internal zero is required")
    if any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in marker_cells):
        errors.append("marker cell lies inside the template bounding box")
    if any(
        r0 - 1 <= r <= r1 + 1 and c0 - 1 <= c <= c1 + 1
        for r, c in marker_cells
    ):
        errors.append("marker cells must be separated from the template by a zero moat")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical neighborhood, while allowing broader lawful draws."""
    reasons = self_check(grid)
    if reasons:
        return list(reasons)
    observed = observe_overrides(grid)
    if observed["n_9"] not in (2, 3, 4):
        reasons.append("canonical examples use 2-4 marker cells")
    if observed["template_color"] not in _CANONICAL_TEMPLATE_COLORS:
        reasons.append("template color is outside canonical {3,4,6}")
    if observed["template_h"] > 3 or observed["template_w"] > 3:
        reasons.append("canonical template bboxes are at most 3x3")
    return reasons


def _crop_template(grid: list[list[int]]) -> list[list[int]]:
    info = _template_info(grid)
    if info is None:
        return []
    _, _, (r0, c0, r1, c1) = info
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _repeat(
    grid: list[list[int]],
    *,
    count: int | None = None,
    gap: int = 1,
    solid: bool = False,
    crop_2x2: bool = False,
) -> list[list[int]]:
    template = _crop_template(grid)
    if not template:
        return []
    if crop_2x2:
        template = [row[:2] for row in template[:2]]
    if solid:
        colors = {value for row in template for value in row if value != 0}
        color = next(iter(colors)) if len(colors) == 1 else 1
        template = [[color for _ in row] for row in template]
    if count is None:
        count = sum(value == 9 for row in grid for value in row)
    out_h = len(template)
    out_w = count * len(template[0]) + max(0, count - 1) * gap
    out = full_grid(out_h, out_w, 0)
    for index in range(count):
        c0 = index * (len(template[0]) + gap)
        for r, row in enumerate(template):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][c0 + c] = value
    return out


def _true_output(grid):
    return _repeat(grid)


def _fixed_three(grid):
    return _repeat(grid, count=3)


def _single_copy(grid):
    return _repeat(grid, count=1)


def _marker_component_count(grid):
    return _repeat(grid, count=_marker_components(grid))


def _solid_bbox(grid):
    return _repeat(grid, solid=True)


def _separatorless(grid):
    return _repeat(grid, gap=0)


def _fixed_2x2_crop(grid):
    return _repeat(grid, crop_2x2=True)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_three": _fixed_three,
    "single_copy": _single_copy,
    "marker_component_count": _marker_component_count,
    "solid_bbox": _solid_bbox,
    "separatorless": _separatorless,
    "fixed_2x2_crop": _fixed_2x2_crop,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_three": _fixed_three,
    "marker_component_count": _marker_component_count,
    "solid_bbox": _solid_bbox,
}


def _lawful(grid) -> bool:
    return not self_check(grid)


def _observed(grid, name: str) -> int:
    return observe_overrides(grid)[name]


SEMANTIC_WITNESSES = {
    "one_copy": lambda grid: _lawful(grid) and _observed(grid, "n_9") == 1,
    "multiple_copies": lambda grid: _lawful(grid) and _observed(grid, "n_9") >= 2,
    "four_copies": lambda grid: _lawful(grid) and _observed(grid, "n_9") == 4,
    "adjacent_marker_counterexample": lambda grid: (
        _lawful(grid)
        and _observed(grid, "n_9") > _marker_components(grid)
    ),
    "sparse_template_counterexample": lambda grid: (
        _lawful(grid) and _true_output(grid) != _solid_bbox(grid)
    ),
    "large_template": lambda grid: (
        _lawful(grid)
        and (
            _observed(grid, "template_h") == 4
            or _observed(grid, "template_w") == 4
        )
    ),
}

WITNESS_RIVALS = {
    "one_copy": ["fixed_three"],
    "multiple_copies": ["single_copy", "separatorless"],
    "four_copies": ["fixed_three", "single_copy"],
    "adjacent_marker_counterexample": ["marker_component_count"],
    "sparse_template_counterexample": ["solid_bbox"],
    "large_template": ["fixed_2x2_crop"],
}


def _competing_outputs(grid) -> dict[str, list[list[int]]] | None:
    if self_check(grid):
        return None
    outputs = {"true": _true_output(grid)}
    outputs.update({name: fn(grid) for name, fn in LESSON_COMPETITORS.items()})
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named shortcut survives but changes the query."""
    reasons: list[str] = []
    surviving: set[str] | None = None
    for index, demo in enumerate(demos):
        outputs = _competing_outputs(demo.get("input"))
        if outputs is None:
            reasons.append(f"demo {index} is not a lawful task scene")
            continue
        official = demo.get("output")
        consistent = {name for name, output in outputs.items() if output == official}
        if "true" not in consistent:
            reasons.append(f"demo {index} output does not match the marker-count rule")
            continue
        surviving = consistent if surviving is None else surviving & consistent

    query_outputs = _competing_outputs(query.get("input"))
    if query_outputs is None:
        reasons.append("query is not a lawful task scene")
        return reasons
    query_answer = query.get("output")
    if query_outputs["true"] != query_answer:
        reasons.append("query output does not match the marker-count rule")
        return reasons
    if reasons:
        return reasons

    for name in sorted(surviving or set()):
        if name != "true" and query_outputs[name] != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
