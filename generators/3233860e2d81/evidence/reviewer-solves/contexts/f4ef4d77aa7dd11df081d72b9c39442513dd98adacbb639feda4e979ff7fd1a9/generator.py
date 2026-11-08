"""Generator for ARC task f8ff0b80 / canonical task 3233860e2d81.

The input contains several non-background colors with pairwise-distinct cell
counts.  The Racket oracle returns the three most frequent colors, in descending
count order, as a 3x1 column.

Most generated lessons use four to seven colors so selecting the top three is
not equivalent to returning the whole palette.  A fixed, source-independent
curriculum schedule also emits 12x12 three-color inputs to preserve exact
canonical-profile support.  The most frequent color and one non-winning decoy
are deliberately fragmented, so neither largest-component size nor the mere
presence of fragmentation can substitute for total-frequency ranking.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "3233860e2d81"
TASK_ID = GENERATOR_ID
VERSION = "4.0.2"
RULE_HASH = "3087638f0586"
SUMMARY = (
    "A sparse grid contains 3-7 non-background colors with pairwise-distinct "
    "cell counts. The answer is the three most frequent colors, descending, "
    "as a 3x1 column. A periodic 12x12 three-color branch anchors the exact "
    "canonical profile; broad lessons include at least one lower-ranked distractor."
)

COUNT_DISTRIBUTIONS = ("ascending", "tight_spread", "wide_spread")
DIFFICULTIES = (None, "easy", "medium", "hard")
INT_AXIS_BOUNDS = {
    "grid_h": (5, 18),
    "grid_w": (5, 18),
    "n_colors": (3, 7),
    "min_count": (2, 4),
    "min_count_gap": (1, 3),
}
# An empty declaration opts into the strict override checker policy.  Actual
# geometry conflicts are reported by a ValueError carrying the exact axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "background is color 0 and occupies at least one quarter of the grid",
    "canonical-profile draws use 3 colors; broad generated inputs use 4-7 colors",
    "every non-background color occurs at least twice",
    "all non-background cell counts are pairwise distinct",
    "normal generated inputs contain at least one color below the top three",
    "the highest-count color has 2-3 components; one non-winning decoy has 2; all others have one",
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
        "valid": "3..7",
        "doc": "number of generated non-background colors; three-color draws anchor the canonical profile",
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


def _validate_generate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in DIFFICULTIES:
        if difficulty is not None and type(difficulty) is not str:
            raise TypeError(
                "difficulty must be None or one of easy, medium, hard, "
                f"not {type(difficulty).__name__}"
            )
        raise ValueError(
            f"difficulty must be one of easy, medium, hard, or None; got {difficulty!r}"
        )

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    cleaned = {}
    for axis, value in overrides.items():
        # Public generator convention: an explicit None is the same as omitting
        # a control, which lets callers build a stable options dictionary.
        if value is None:
            continue
        if axis in INT_AXIS_BOUNDS:
            if type(value) is not int:
                raise TypeError(
                    f"{axis} override must be an integer, not {type(value).__name__}"
                )
            low, high = INT_AXIS_BOUNDS[axis]
            if not low <= value <= high:
                raise ValueError(f"{axis} override must be in {low}..{high}, got {value}")
        elif axis == "count_distribution":
            if type(value) is not str:
                raise TypeError(
                    "count_distribution override must be a string, "
                    f"not {type(value).__name__}"
                )
            if value not in COUNT_DISTRIBUTIONS:
                raise ValueError(
                    "count_distribution override must be one of "
                    f"{COUNT_DISTRIBUTIONS}, got {value!r}"
                )
        cleaned[axis] = value
    return cleaned


def _incompatible(overrides, message):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


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
        # Keep this profile observably distinct from tight_spread even when
        # n_colors=3: [g, g+2] versus [g, g+1].
        gaps = [min_gap + 2 * index for index in range(n_colors - 1)]
    else:
        raise ValueError(f"unknown count_distribution {distribution!r}")

    counts = [min_count]
    for gap in gaps:
        counts.append(counts[-1] + gap)
    return counts


def _top_piece_count(counts):
    ordered = sorted(counts)
    if len(ordered) < 3:
        raise ValueError("at least three color counts are required")
    top, runner_up = ordered[-1], ordered[-2]
    # Two pieces usually suffice.  Use three when a two-way split would fail
    # to make every winner fragment smaller than the runner-up's total count.
    return 2 if math.ceil(top / 2) < runner_up else 3


def _split_evenly(total, pieces):
    quotient, remainder = divmod(total, pieces)
    values = [quotient + (index < remainder) for index in range(pieces)]
    if any(value <= 0 for value in values):
        raise ValueError(f"cannot split {total} cells into {pieces} positive pieces")
    return values


def _mandatory_gap_count(n_colors, counts):
    # One segment per color, the extra winner pieces, and one extra piece for a
    # non-winning decoy; every adjacent pair receives a background separator.
    segment_count = n_colors + _top_piece_count(counts)
    return segment_count - 1


def _fits(area, n_colors, counts):
    background_reserve = max(2, math.ceil(area / 4))
    mandatory_gaps = _mandatory_gap_count(n_colors, counts)
    return sum(counts) + background_reserve + mandatory_gaps <= area


@lru_cache(maxsize=None)
def _minimum_area(n_colors, counts):
    fixed_cells = sum(counts) + _mandatory_gap_count(n_colors, counts)
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



def _largest_component_output(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    ranked = sorted(
        counts,
        key=lambda color: (-max(_component_sizes(grid, color)), color),
    )
    if len(ranked) < 3:
        raise ValueError("expected at least three non-background colors")
    return [[ranked[index]] for index in range(3)]


def _fragment_count_then_size_output(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    ranked = sorted(
        counts,
        key=lambda color: (
            -len(_component_sizes(grid, color)),
            -max(_component_sizes(grid, color)),
            color,
        ),
    )
    if len(ranked) < 3:
        raise ValueError("expected at least three non-background colors")
    return [[ranked[index]] for index in range(3)]


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
        "largest_component": tuple(
            value[0] for value in _largest_component_output(grid)
        ),
        "fragment_count_then_size": tuple(
            value[0] for value in _fragment_count_then_size_output(grid)
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
    if any(len(sizes) > 3 for sizes in component_sizes.values()):
        errors.append(
            "no color may fragment into more than three 4-connected components: "
            f"{component_sizes}"
        )
    if component_count > n_colors + 3:
        errors.append(
            f"too many colored components for the canonical grammar: {component_count} > {n_colors + 3}"
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
        elif gaps == [min_gap + 2 * index for index in range(len(gaps))]:
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


def strict_canonical_like(grid):
    """Recognize the declared count-ranking input manifold."""
    return self_check(grid)


def _total_count_not_largest_component(grid):
    try:
        return _largest_component_output(grid) != expected_output(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _total_count_not_fragment_count(grid):
    try:
        return _fragment_count_then_size_output(grid) != expected_output(grid)
    except (TypeError, ValueError, IndexError):
        return False


def lesson_identifiable(demos, query):
    """Report a declared rival that survives every visible demonstration."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            query_differs = rival(query["input"]) != query["output"]
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(f"{name} evaluation failed: {type(exc).__name__}: {exc}")
            continue
        if query_differs and fits_demos:
            reasons.append(
                f"{name} fits every demonstration but predicts a different query"
            )
    return reasons


EXAMPLES_NEEDED = 3
SEMANTIC_WITNESSES = {
    "total_count_not_largest_component": _total_count_not_largest_component,
    "total_count_not_fragment_count": _total_count_not_fragment_count,
}
SEMANTIC_RIVALS = {
    "largest_component": _largest_component_output,
    "fragment_count_then_size": _fragment_count_then_size_output,
}
WITNESS_RIVALS = {
    "total_count_not_largest_component": ["largest_component"],
    "total_count_not_fragment_count": ["fragment_count_then_size"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_generate_request(
        seed, sample_index, difficulty, dict(overrides)
    )

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
    dimension_axis_names = {"grid_h", "grid_w"}
    has_semantic_override = bool(semantic_axis_names & set(overrides))
    has_dimension_override = bool(dimension_axis_names & set(overrides))
    canonical_profile = (
        not overrides and sample_index % 13 in {0, 8, 12}
    )
    default_h_bounds = _difficulty_range(
        difficulty, (7, 10), (9, 14), (13, 18)
    )
    default_w_bounds = _difficulty_range(
        difficulty, (7, 10), (9, 14), (13, 18)
    )
    full_dimension_domain = range(5, 19)
    h_domain = (
        (12,)
        if canonical_profile
        else full_dimension_domain
        if has_semantic_override or "grid_h" in overrides
        else range(default_h_bounds[0], default_h_bounds[1] + 1)
    )
    w_domain = (
        (12,)
        if canonical_profile
        else full_dimension_domain
        if has_semantic_override or "grid_w" in overrides
        else range(default_w_bounds[0], default_w_bounds[1] + 1)
    )
    default_color_domain = _difficulty_range(
        difficulty, range(4, 6), range(4, 7), range(5, 8)
    )
    n_domain = (
        (3,)
        if canonical_profile
        else range(3, 8)
        if "n_colors" in overrides or has_dimension_override
        else default_color_domain
    )

    # Choose dimensions only from pairs that admit at least one complete axis
    # tuple.  This keeps every standalone declared override valid in every band
    # while still rejecting genuinely incompatible multi-axis requests.
    semantic_candidates = _semantic_candidates(overrides, n_domain)
    if not semantic_candidates:
        raise ValueError("requested semantic overrides are outside declared domains")
    minimum_required_area = min(item[4] for item in semantic_candidates)
    dimension_pairs = [
        (candidate_h, candidate_w)
        for candidate_h in h_domain
        for candidate_w in w_domain
        if (
            "grid_h" not in overrides
            or candidate_h == overrides["grid_h"]
        )
        and (
            "grid_w" not in overrides
            or candidate_w == overrides["grid_w"]
        )
        and candidate_h * candidate_w >= minimum_required_area
    ]
    if not dimension_pairs:
        message = (
            "requested dimensions and semantic axes have no feasible sparse "
            f"realization: {sorted(overrides)}"
        )
        if len(overrides) >= 2:
            _incompatible(overrides, message)
        raise ValueError(message)
    h = _draw_choice(
        ctx, "grid_h", sorted({candidate_h for candidate_h, _ in dimension_pairs})
    )
    w = _draw_choice(
        ctx,
        "grid_w",
        sorted({
            candidate_w
            for candidate_h, candidate_w in dimension_pairs
            if candidate_h == h
        }),
    )
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
    piece_count = _top_piece_count(counts)
    mandatory_gaps = _mandatory_gap_count(n_colors, counts)
    free = area - sum(counts) - background_reserve - mandatory_gaps
    if free < 0:
        if len(overrides) >= 2:
            _incompatible(
                overrides,
                "incompatible overrides "
                f"{sorted(overrides)} cannot preserve sparse background and "
                f"separated color objects: shape={h}x{w}, counts={counts}",
            )
        raise ValueError(
            "requested axis cannot preserve sparse background and separated "
            f"color objects: shape={h}x{w}, counts={counts}"
        )

    # Search only over deterministic, keyed choices.  The highest-count color
    # is split into two or three pieces, and one randomly chosen non-winner is
    # split into two.  Thus a learner must aggregate fragments but cannot use
    # fragmentation alone as the winner marker.
    last_errors = []
    witness_grid = None
    semantic_shortcuts = {"largest_component", "fragment_count_then_size"}
    for _attempt in range(96):
        assigned_counts = list(counts)
        placement_rng.shuffle(assigned_counts)
        color_counts = list(zip(palette, assigned_counts))
        top_color, top_count = max(color_counts, key=lambda item: item[1])
        runner_up_count = sorted(assigned_counts)[-2]
        decoy_color, decoy_count = placement_rng.choice(
            [item for item in color_counts if item[0] != top_color]
        )
        connected_segments = [
            (color, count)
            for color, count in color_counts
            if color not in {top_color, decoy_color}
        ]
        top_segments = [
            (top_color, count) for count in _split_evenly(top_count, piece_count)
        ]
        decoy_segments = [
            (decoy_color, count) for count in _split_evenly(decoy_count, 2)
        ]
        segments = top_segments + decoy_segments + connected_segments
        placement_rng.shuffle(segments)

        path = _path(h, w, placement_rng)
        slots = [0] * (len(segments) + 1)
        for _ in range(free):
            slots[placement_rng.randrange(len(slots))] += 1

        grid = full_grid(h, w, 0)
        cursor = slots[0]
        for index, (color, count) in enumerate(segments):
            segment = path[cursor : cursor + count]
            if len(segment) != count:
                raise RuntimeError("internal path allocation underflow")
            for row, col in segment:
                grid[row][col] = color
            cursor += count
            if index < len(segments) - 1:
                cursor += 1
            cursor += slots[index + 1]

        last_errors = self_check(grid)
        if last_errors:
            continue
        top_components = _component_sizes(grid, top_color)
        decoy_components = _component_sizes(grid, decoy_color)
        other_component_counts = {
            color: len(_component_sizes(grid, color))
            for color, _ in color_counts
            if color not in {top_color, decoy_color}
        }
        if len(top_components) != piece_count or max(top_components) >= runner_up_count:
            continue
        if len(decoy_components) != 2 or any(
            count != 1 for count in other_component_counts.values()
        ):
            continue
        shortcut_matches = _shortcut_matches(
            grid, Counter(value for row in grid for value in row if value)
        )
        if semantic_shortcuts & set(shortcut_matches):
            continue
        if witness_grid is None:
            witness_grid = grid
        if not shortcut_matches:
            return grid

    if witness_grid is not None:
        return witness_grid
    raise RuntimeError(f"could not realize a structurally valid lesson: {last_errors}")
