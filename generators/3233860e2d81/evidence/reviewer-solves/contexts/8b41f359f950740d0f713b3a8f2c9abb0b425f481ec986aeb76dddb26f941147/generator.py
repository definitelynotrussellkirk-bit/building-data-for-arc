"""Generator for ARC task f8ff0b80 / canonical task 3233860e2d81.

The input contains several non-background colors with pairwise-distinct cell
counts.  The Racket oracle returns the three most frequent colors, in descending
count order, as a 3x1 column.

Generated lessons use four to seven colors so selecting the top three is never
trivially equivalent to returning the whole palette.  Every color is painted as
one connected path segment, which keeps object counts near the canonical data
instead of turning each colored cell into a separate distractor object.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3233860e2d81"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3087638f0586"
SUMMARY = (
    "A sparse grid contains 4-7 non-background colors with pairwise-distinct "
    "cell counts. The answer is the three most frequent colors, descending, "
    "as a 3x1 column. Canonical three-color inputs remain valid, while normal "
    "generated lessons always include at least one lower-ranked distractor."
)

COUNT_DISTRIBUTIONS = ("ascending", "tight_spread", "wide_spread")

INVARIANTS = [
    "background is color 0 and occupies at least one quarter of the grid",
    "canonical inputs use 3 colors; normal generated inputs use 4-7 colors",
    "every non-background color occurs at least twice",
    "all non-background cell counts are pairwise distinct",
    "normal generated inputs contain at least one color below the top three",
    "generated colors are each one 4-connected component; canonical rows may have up to two extra fragments in total",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "5..18",
        "doc": "input height; explicit overrides remain valid in every difficulty band",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "5..18",
        "doc": "input width; explicit overrides remain valid in every difficulty band",
    },
    "n_colors": {
        "type": "int",
        "default": "difficulty-skewed feasible rng",
        "valid": "4..7",
        "doc": "number of generated non-background colors",
    },
    "min_count": {
        "type": "int",
        "default": "feasible rng",
        "valid": "2..4",
        "doc": "exact least non-background cell count",
    },
    "min_count_gap": {
        "type": "int",
        "default": "feasible rng",
        "valid": "1..3",
        "doc": "exact minimum adjacent gap between sorted color counts",
    },
    "count_distribution": {
        "type": "str",
        "default": "feasible rng",
        "valid": "|".join(COUNT_DISTRIBUTIONS),
        "doc": "shape of the increasing count-gap sequence",
    },
}


def _difficulty_range(difficulty, easy, medium, hard):
    if difficulty == "easy":
        return easy
    if difficulty == "hard":
        return hard
    return medium


def _counts_for(n_colors, min_count, min_gap, distribution):
    if distribution == "ascending":
        gaps = [min_gap] * (n_colors - 1)
    elif distribution == "tight_spread":
        gaps = [min_gap + (index % 2) for index in range(n_colors - 1)]
    elif distribution == "wide_spread":
        gaps = [min_gap + index for index in range(n_colors - 1)]
    else:
        raise ValueError(f"unknown count_distribution {distribution!r}")

    counts = [min_count]
    for gap in gaps:
        counts.append(counts[-1] + gap)
    return counts


def _fits(area, n_colors, counts):
    background_reserve = max(2, math.ceil(area / 4))
    mandatory_gaps = n_colors - 1
    return sum(counts) + background_reserve + mandatory_gaps <= area


@lru_cache(maxsize=None)
def _minimum_area(n_colors, counts):
    fixed_cells = sum(counts) + (n_colors - 1)
    for area in range(max(1, fixed_cells), 901):
        if fixed_cells + max(2, math.ceil(area / 4)) <= area:
            return area
    raise ValueError(f"counts cannot fit an ARC grid: {counts}")


def _semantic_candidates(overrides, n_domain):
    """Enumerate complete observable axis tuples before any keyed draw.

    Filtering on the full partial override set prevents an early default draw
    from making a later standalone override spuriously impossible.  Each row
    carries its minimum required area so dimension filtering stays inexpensive.
    """
    candidates = []
    for n_colors in n_domain:
        if "n_colors" in overrides and n_colors != overrides["n_colors"]:
            continue
        for min_count in range(2, 5):
            if "min_count" in overrides and min_count != overrides["min_count"]:
                continue
            for min_gap in range(1, 4):
                if (
                    "min_count_gap" in overrides
                    and min_gap != overrides["min_count_gap"]
                ):
                    continue
                for distribution in COUNT_DISTRIBUTIONS:
                    if (
                        "count_distribution" in overrides
                        and distribution != overrides["count_distribution"]
                    ):
                        continue
                    counts = tuple(_counts_for(
                        n_colors, min_count, min_gap, distribution
                    ))
                    candidates.append(
                        (
                            n_colors,
                            min_count,
                            min_gap,
                            distribution,
                            _minimum_area(n_colors, counts),
                        )
                    )
    return candidates


def _draw_choice(ctx, label, choices):
    choices = tuple(choices)
    if not choices:
        raise ValueError(f"no feasible values remain for {label}")
    return ctx.draw_choice(label, choices)


def _draw_semantic_axes(ctx, tuples):
    remaining = list(tuples)
    n_colors = _draw_choice(
        ctx, "n_colors", sorted({item[0] for item in remaining})
    )
    remaining = [item for item in remaining if item[0] == n_colors]
    min_count = _draw_choice(
        ctx, "min_count", sorted({item[1] for item in remaining})
    )
    remaining = [item for item in remaining if item[1] == min_count]
    min_gap = _draw_choice(
        ctx, "min_count_gap", sorted({item[2] for item in remaining})
    )
    remaining = [item for item in remaining if item[2] == min_gap]
    distribution = _draw_choice(
        ctx,
        "count_distribution",
        [profile for profile in COUNT_DISTRIBUTIONS if any(
            item[3] == profile for item in remaining
        )],
    )
    return n_colors, min_count, min_gap, distribution


def _row_snake(h, w):
    return [
        (row, col)
        for row in range(h)
        for col in (range(w) if row % 2 == 0 else range(w - 1, -1, -1))
    ]


def _col_snake(h, w):
    return [
        (row, col)
        for col in range(w)
        for row in (range(h) if col % 2 == 0 else range(h - 1, -1, -1))
    ]


def _spiral(h, w):
    cells = []
    top, left, bottom, right = 0, 0, h - 1, w - 1
    while top <= bottom and left <= right:
        cells.extend((top, col) for col in range(left, right + 1))
        top += 1
        cells.extend((row, right) for row in range(top, bottom + 1))
        right -= 1
        if top <= bottom:
            cells.extend((bottom, col) for col in range(right, left - 1, -1))
            bottom -= 1
        if left <= right:
            cells.extend((row, left) for row in range(bottom, top - 1, -1))
            left += 1
    return cells


def _path(h, w, rng):
    style = rng.choice(("row_snake", "col_snake", "spiral"))
    cells = (
        _row_snake(h, w)
        if style == "row_snake"
        else _col_snake(h, w)
        if style == "col_snake"
        else _spiral(h, w)
    )
    if rng.random() < 0.5:
        cells = list(reversed(cells))
    flip_h = rng.random() < 0.5
    flip_w = rng.random() < 0.5
    if flip_h or flip_w:
        cells = [
            (h - 1 - row if flip_h else row, w - 1 - col if flip_w else col)
            for row, col in cells
        ]
    return cells


def _component_sizes(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    sizes = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] != color or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            size = 0
            while queue:
                r, c = queue.popleft()
                size += 1
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            sizes.append(size)
    return sizes



def _bbox_metrics(grid, color):
    points = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    return height * width, height + width


def _shortcut_matches(grid, counts):
    colors = set(counts)
    intended = tuple(sorted(colors, key=lambda color: (-counts[color], color))[:3])
    first_seen = []
    for row in grid:
        for value in row:
            if value and value not in first_seen:
                first_seen.append(value)
    bbox = {color: _bbox_metrics(grid, color) for color in colors}
    candidates = {
        "numeric_ascending": tuple(sorted(colors)[:3]),
        "numeric_descending": tuple(sorted(colors, reverse=True)[:3]),
        "scan_first": tuple(first_seen[:3]),
        "scan_last": tuple(reversed(first_seen[-3:])),
        "bbox_area": tuple(
            sorted(colors, key=lambda color: (-bbox[color][0], color))[:3]
        ),
        "bbox_span": tuple(
            sorted(colors, key=lambda color: (-bbox[color][1], color))[:3]
        ),
    }
    return [name for name, output in candidates.items() if output == intended]

def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"], "facts": {}}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty"], "facts": {}}
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC limit: {h}x{w}")
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != w:
            errors.append("grid must be rectangular")
            return {"errors": errors, "facts": {}}
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in row
        ):
            errors.append("grid colors must be integers in 0..9")
            return {"errors": errors, "facts": {}}

    counts = Counter(value for row in grid for value in row if value != 0)
    n_colors = len(counts)
    ordered_counts = sorted(counts.values())
    background_count = sum(value == 0 for row in grid for value in row)
    component_sizes = {
        color: _component_sizes(grid, color) for color in sorted(counts)
    }
    component_count = sum(len(sizes) for sizes in component_sizes.values())

    if not 3 <= n_colors <= 7:
        errors.append(f"expected 3-7 non-background colors, found {n_colors}")
    if background_count < math.ceil(h * w / 4):
        errors.append(
            "background must occupy at least one quarter of the input: "
            f"found {background_count}/{h*w}"
        )
    if ordered_counts and ordered_counts[0] < 2:
        errors.append(
            f"every non-background color must occur at least twice, found minimum {ordered_counts[0]}"
        )
    if len(set(ordered_counts)) != len(ordered_counts):
        errors.append(f"non-background counts must be pairwise distinct: {ordered_counts}")
    if n_colors >= 4 and any(len(sizes) != 1 for sizes in component_sizes.values()):
        errors.append(
            "generated 4-7 color lessons require exactly one 4-connected component per color: "
            f"{component_sizes}"
        )
    if any(len(sizes) > 3 for sizes in component_sizes.values()):
        errors.append(
            "no color may fragment into more than three 4-connected components: "
            f"{component_sizes}"
        )
    if component_count > n_colors + 2:
        errors.append(
            f"too many colored components for the canonical grammar: {component_count} > {n_colors + 2}"
        )

    shortcut_matches = _shortcut_matches(grid, counts) if n_colors >= 4 else []

    gaps = [
        ordered_counts[index + 1] - ordered_counts[index]
        for index in range(len(ordered_counts) - 1)
    ]
    min_gap = min(gaps) if gaps else None
    distribution = "other"
    if gaps:
        if all(gap == min_gap for gap in gaps):
            distribution = "ascending"
        elif gaps == [min_gap + (index % 2) for index in range(len(gaps))]:
            distribution = "tight_spread"
        elif gaps == [min_gap + index for index in range(len(gaps))]:
            distribution = "wide_spread"

    facts = {
        "grid_h": h,
        "grid_w": w,
        "n_colors": n_colors,
        "counts": dict(counts),
        "ordered_counts": ordered_counts,
        "min_count": ordered_counts[0] if ordered_counts else None,
        "min_count_gap": min_gap,
        "count_distribution": distribution,
        "background_count": background_count,
        "component_sizes": component_sizes,
        "component_count": component_count,
        "shortcut_matches": shortcut_matches,
    }
    return {"errors": errors, "facts": facts}


def observe_overrides(grid):
    analysis = _analyze(grid)
    facts = analysis["facts"]
    return {
        axis: facts[axis]
        for axis in AXES
        if axis in facts and facts[axis] is not None
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", {})
        if isinstance(candidate, dict):
            overrides = candidate
    unknown = set(overrides) - set(AXES)
    if unknown:
        errors.append(f"unknown override(s): {sorted(unknown)}")
    if not errors and overrides:
        observed = observe_overrides(grid)
        for axis, requested in overrides.items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed {observed[axis]!r}"
                )
    return errors


def expected_output(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    if len(ranked) < 3:
        raise ValueError("expected at least three non-background colors")
    return [[ranked[index]] for index in range(3)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    semantic_axis_names = {
        "n_colors", "min_count", "min_count_gap", "count_distribution"
    }
    has_semantic_override = bool(semantic_axis_names & set(overrides))
    default_h_bounds = _difficulty_range(
        difficulty, (7, 10), (9, 14), (13, 18)
    )
    default_w_bounds = _difficulty_range(
        difficulty, (7, 10), (9, 14), (13, 18)
    )
    full_dimension_domain = range(5, 19)
    h_domain = (
        full_dimension_domain
        if has_semantic_override or "grid_h" in overrides
        else range(default_h_bounds[0], default_h_bounds[1] + 1)
    )
    w_domain = (
        full_dimension_domain
        if has_semantic_override or "grid_w" in overrides
        else range(default_w_bounds[0], default_w_bounds[1] + 1)
    )
    default_color_domain = _difficulty_range(
        difficulty, range(4, 6), range(4, 7), range(5, 8)
    )
    n_domain = range(4, 8) if "n_colors" in overrides else default_color_domain

    # Choose dimensions only from pairs that admit at least one complete axis
    # tuple.  This keeps every standalone declared override valid in every band
    # while still rejecting genuinely incompatible multi-axis requests.
    semantic_candidates = _semantic_candidates(overrides, n_domain)
    if not semantic_candidates:
        raise ValueError("requested semantic overrides are outside declared domains")
    minimum_required_area = min(item[4] for item in semantic_candidates)
    h_candidates = [
        candidate_h
        for candidate_h in h_domain
        if any(
            candidate_h * candidate_w >= minimum_required_area
            for candidate_w in w_domain
        )
    ]
    h = _draw_choice(ctx, "grid_h", h_candidates)
    w_candidates = [
        candidate_w
        for candidate_w in w_domain
        if h * candidate_w >= minimum_required_area
    ]
    w = _draw_choice(ctx, "grid_w", w_candidates)
    area = h * w

    feasible_tuples = [
        item[:4] for item in semantic_candidates if item[4] <= area
    ]
    n_colors, min_count, min_gap, distribution = _draw_semantic_axes(
        ctx, feasible_tuples
    )
    counts = _counts_for(n_colors, min_count, min_gap, distribution)

    placement_rng = ctx.draw_rng("placement")
    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(range(1, 10), n_colors)

    background_reserve = max(2, math.ceil(area / 4))
    mandatory_gaps = n_colors - 1
    free = area - sum(counts) - background_reserve - mandatory_gaps
    if free < 0:
        raise ValueError(
            "requested axes cannot preserve sparse background and separated color objects: "
            f"shape={h}x{w}, counts={counts}"
        )

    # Search only over deterministic, keyed choices.  The bounded rejection
    # strongly prefers lessons that falsify common non-count shortcuts while
    # retaining a deterministic structurally valid fallback for tight layouts.
    last_errors = []
    fallback_grid = None
    for _attempt in range(12):
        assigned_counts = list(counts)
        placement_rng.shuffle(assigned_counts)
        color_counts = list(zip(palette, assigned_counts))
        placement_rng.shuffle(color_counts)
        path = _path(h, w, placement_rng)

        slots = [0] * (n_colors + 1)
        for _ in range(free):
            slots[placement_rng.randrange(len(slots))] += 1

        grid = full_grid(h, w, 0)
        cursor = slots[0]
        for index, (color, count) in enumerate(color_counts):
            segment = path[cursor : cursor + count]
            if len(segment) != count:
                raise RuntimeError("internal path allocation underflow")
            for row, col in segment:
                grid[row][col] = color
            cursor += count
            if index < n_colors - 1:
                cursor += 1
            cursor += slots[index + 1]

        last_errors = self_check(grid)
        if last_errors:
            continue
        if fallback_grid is None:
            fallback_grid = grid
        if not _shortcut_matches(grid, Counter(value for row in grid for value in row if value)):
            return grid

    if fallback_grid is not None:
        return fallback_grid
    raise RuntimeError(f"could not realize a structurally valid lesson: {last_errors}")
