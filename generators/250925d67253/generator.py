"""Sampler for centroid-directed permutation of a 3x3 panel array.

The 19x19 input contains nine 5x5 panels separated by zero rows/columns.
Within each panel, every non-background marker contributes to a centroid. The
centroid's threshold bucket names the panel's destination, and the complete
5x5 panel is copied there. The sampler deliberately uses independent,
non-affine permutations and asymmetric marker motifs so that generated lessons
cannot be solved by one global shift or by replacing the centroid with a
bounding-box, nearest-anchor, or median heuristic.
"""
from __future__ import annotations

from collections import Counter
from statistics import median

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "250925d67253"
TASK_ID = GENERATOR_ID
RULE_HASH = "9f1390aa0494"
VERSION = "3.0.0"
SUMMARY = (
    "A fixed 19x19 zero lattice separates nine 5x5 two-color panels. In each "
    "source panel, the arithmetic centroid of all non-background markers is "
    "thresholded into one of nine destination buckets. The nine buckets form "
    "a bijection, and each complete 5x5 source panel is copied to its encoded "
    "destination. Generated mappings are independent non-cyclic permutations; "
    "asymmetric motifs distinguish the true centroid from common proxies."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the grid is 19x19 with zero separator rows and columns at 0, 6, 12, and 18",
    "all nine 5x5 panels share one nonzero background and one nonzero marker color",
    "the arithmetic marker centroid in each panel selects a distinct target bucket",
    "the output copies each complete 5x5 panel into its centroid-selected target",
    "training mappings are non-cyclic and marker motifs touch the separator lattice",
]

AXES = {
    "permutation_kind": {
        "type": "str",
        "default": "balanced; non-cyclic",
        "valid": "derangement|mixed_fixed",
    },
    "marker_density": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "sparse|dense",
    },
    "palette_band": {
        "type": "str",
        "default": "balanced",
        "valid": "low|high",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_SEPARATORS = (0, 6, 12, 18)
_LOW_COLORS = (1, 2, 3, 4)
_HIGH_COLORS = (6, 7, 8, 9)

# Every component in every motif touches a local panel boundary, so all
# non-background pixels connect to the zero separator lattice. Every motif has
# at most two row-0 cells, keeping the Racket authority's row-1 background vote
# unambiguous even when all three top panels use dense motifs.
#
# Target-0 motifs are deliberately asymmetric: their arithmetic centroid is in
# bucket 0 while their bounding-box center, nearest 0/2/4 anchor, and coordinate
# median are not. Thus every generated grid is a counterexample to all three
# canonical-fitting centroid proxies.
_MOTIFS = {
    "sparse": {
        0: (
            ((0, 1), (0, 3), (1, 0), (2, 0), (2, 1), (3, 1)),
            ((0, 0), (0, 1), (2, 0), (2, 1), (3, 1)),
        ),
        1: (
            ((0, 1), (0, 3), (1, 1), (1, 2), (1, 3), (2, 1), (4, 1)),
            ((0, 1), (0, 3), (1, 2), (1, 3), (2, 3), (3, 3)),
        ),
        2: (
            ((0, 0), (0, 4), (1, 3), (1, 4), (2, 4)),
            ((0, 0), (0, 3), (1, 3), (1, 4), (2, 3), (2, 4), (3, 3)),
        ),
        3: (
            ((0, 0), (1, 1), (2, 0), (2, 1), (3, 0), (4, 0)),
            ((1, 0), (2, 0), (2, 1), (2, 2), (3, 1), (3, 4)),
        ),
        4: (
            ((0, 2), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2), (4, 2)),
            ((0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3), (4, 3)),
        ),
        5: (
            ((0, 3), (1, 0), (1, 3), (1, 4), (3, 3), (3, 4)),
            ((0, 1), (1, 4), (2, 3), (2, 4), (3, 3), (3, 4)),
        ),
        6: (
            ((1, 1), (2, 1), (3, 0), (3, 1), (4, 0), (4, 1), (4, 4)),
            ((1, 0), (3, 0), (3, 1), (3, 2), (4, 0), (4, 1)),
        ),
        7: (
            ((1, 2), (2, 2), (3, 2), (3, 3), (4, 0), (4, 2)),
            ((0, 2), (3, 1), (3, 2), (3, 3), (4, 1), (4, 2), (4, 3)),
        ),
        8: (
            ((2, 3), (3, 3), (3, 4), (4, 0), (4, 3), (4, 4)),
            ((3, 2), (3, 3), (3, 4), (4, 1), (4, 3), (4, 4)),
        ),
    },
    "dense": {
        0: (
            ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0)),
            ((0, 0), (0, 1), (1, 0), (1, 1), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1)),
        ),
        1: (
            ((0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (3, 2)),
            ((0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 3), (3, 1)),
        ),
        2: (
            ((0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4), (4, 4)),
            ((0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 3), (3, 4)),
        ),
        3: (
            ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 4), (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (4, 0)),
            ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (3, 0), (3, 1), (4, 0), (4, 1)),
        ),
        4: (
            ((0, 2), (1, 2), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4)),
            ((1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (2, 4), (3, 1), (3, 2), (3, 3), (4, 2), (4, 3)),
        ),
        5: (
            ((0, 4), (1, 0), (1, 3), (1, 4), (2, 0), (2, 1), (2, 3), (2, 4), (3, 2), (3, 4), (4, 2), (4, 4)),
            ((1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 2), (2, 3), (2, 4), (3, 2), (3, 4), (4, 4)),
        ),
        6: (
            ((0, 0), (1, 0), (1, 1), (3, 0), (3, 2), (3, 4), (4, 0), (4, 1), (4, 2), (4, 4)),
            ((0, 0), (0, 1), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1), (4, 2), (4, 3)),
        ),
        7: (
            ((0, 1), (1, 1), (1, 2), (2, 2), (3, 2), (3, 3), (4, 0), (4, 1), (4, 2), (4, 3)),
            ((0, 2), (0, 3), (1, 2), (3, 1), (3, 2), (3, 3), (3, 4), (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)),
        ),
        8: (
            ((0, 4), (1, 3), (1, 4), (2, 3), (2, 4), (3, 1), (3, 3), (3, 4), (4, 1), (4, 2), (4, 3), (4, 4)),
            ((0, 3), (0, 4), (2, 4), (3, 1), (3, 2), (3, 3), (3, 4), (4, 2), (4, 3), (4, 4)),
        ),
    },
}


def _bucket(value: float) -> int:
    return 0 if value < 1.5 else (1 if value <= 2.5 else 2)


def _nearest_anchor(value: float) -> int:
    return min(range(3), key=lambda index: abs(value - 2 * index))


def _components(points):
    remaining = set(points)
    found = []
    while remaining:
        first = remaining.pop()
        component = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        found.append(component)
    return found


def _validate_templates() -> None:
    for density, targets in _MOTIFS.items():
        if set(targets) != set(range(9)):
            raise RuntimeError(f"{density} motif bank does not cover all targets")
        for target, motifs in targets.items():
            for motif in motifs:
                if len(set(motif)) != len(motif):
                    raise RuntimeError("motif contains duplicate cells")
                if any(not (0 <= r < 5 and 0 <= c < 5) for r, c in motif):
                    raise RuntimeError("motif cell outside 5x5 panel")
                cr = sum(r for r, _ in motif) / len(motif)
                cc = sum(c for _, c in motif) / len(motif)
                if 3 * _bucket(cr) + _bucket(cc) != target:
                    raise RuntimeError(f"motif misses target {target}")
                if sum(r == 0 for r, _ in motif) > 2:
                    raise RuntimeError("motif can break background inference")
                if any(
                    not any(r in (0, 4) or c in (0, 4) for r, c in component)
                    for component in _components(motif)
                ):
                    raise RuntimeError("motif component is detached from separator lattice")

    for density in _MOTIFS:
        for motif in _MOTIFS[density][0]:
            rows = [r for r, _ in motif]
            cols = [c for _, c in motif]
            cr = sum(rows) / len(rows)
            cc = sum(cols) / len(cols)
            bbox = 3 * _bucket((min(rows) + max(rows)) / 2) + _bucket((min(cols) + max(cols)) / 2)
            nearest = 3 * _nearest_anchor(cr) + _nearest_anchor(cc)
            med = 3 * _bucket(float(median(rows))) + _bucket(float(median(cols)))
            if 0 in (bbox, nearest, med):
                raise RuntimeError("target-0 probe does not refute every centroid proxy")


_validate_templates()


def _draw_permutation(ctx, kind: str) -> list[int]:
    """Construct a non-cyclic permutation with the requested fixed-point profile."""
    rng = ctx.draw_rng("permutation")
    if kind == "mixed_fixed":
        fixed_count = rng.choice((1, 2, 3, 4))
        fixed = set(rng.sample(range(9), fixed_count))
        moving = [index for index in range(9) if index not in fixed]
        targets = moving[:]
        # Sattolo's algorithm: one cycle, hence no accidental fixed points.
        for index in range(len(targets) - 1, 0, -1):
            other = rng.randrange(index)
            targets[index], targets[other] = targets[other], targets[index]
        result = list(range(9))
        for source, target in zip(moving, targets):
            result[source] = target
        return result

    # A random 9-cycle is a derangement. Redraw only the six exceptional cycles
    # that happen to be a uniform modular shift.
    for _ in range(32):
        targets = list(range(9))
        for index in range(8, 0, -1):
            other = rng.randrange(index)
            targets[index], targets[other] = targets[other], targets[index]
        if not _is_uniform_cyclic(targets):
            return targets
    raise RuntimeError("failed to construct a non-cyclic derangement")


def _is_uniform_cyclic(mapping) -> bool:
    return len({(target - source) % 9 for source, target in enumerate(mapping)}) == 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if any(value is None for value in overrides.values()):
        raise ValueError("explicit override values may not be None")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    permutation_kind = ctx.draw_choice(
        "permutation_kind", ("derangement", "mixed_fixed")
    )
    density_options = {
        "easy": ("sparse", "sparse", "dense"),
        "medium": ("sparse", "dense"),
        "hard": ("sparse", "dense", "dense"),
        None: ("sparse", "dense"),
    }[difficulty]
    marker_density = ctx.draw_choice("marker_density", density_options)
    palette_band = ctx.draw_choice("palette_band", ("low", "high"))

    mapping = _draw_permutation(ctx, permutation_kind)
    palette = _LOW_COLORS if palette_band == "low" else _HIGH_COLORS
    background, marker = ctx.draw_rng("palette_colors").sample(palette, 2)

    grid = full_grid(19, 19, 0)
    for source, target in enumerate(mapping):
        br, bc = divmod(source, 3)
        r0, c0 = 1 + 6 * br, 1 + 6 * bc
        for r in range(r0, r0 + 5):
            for c in range(c0, c0 + 5):
                grid[r][c] = background
        motif = ctx.draw_rng(f"motif_{source}").choice(_MOTIFS[marker_density][target])
        for r, c in motif:
            grid[r0 + r][c0 + c] = marker
    return grid


def _shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) != 19 or width != 19:
        return [f"expected 19x19 grid, got {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _infer_background(grid) -> int:
    values = [grid[1][c] for c in range(1, 18) if grid[1][c] != 0]
    if not values:
        raise ValueError("row 1 has no nonzero panel colors")
    counts = Counter(values)
    best = max(counts.values())
    winners = [color for color, count in counts.items() if count == best]
    if len(winners) != 1:
        raise ValueError("row-1 background vote is tied")
    return winners[0]


def _marker_positions(grid, source: int, background: int):
    br, bc = divmod(source, 3)
    r0, c0 = 1 + 6 * br, 1 + 6 * bc
    return [
        (r, c)
        for r in range(5)
        for c in range(5)
        if grid[r0 + r][c0 + c] != background
    ]


def _target_mapping(grid, method: str = "centroid") -> list[int]:
    background = _infer_background(grid)
    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, background)
        if not points:
            raise ValueError(f"panel {source} has no marker")
        rows = [r for r, _ in points]
        cols = [c for _, c in points]
        if method == "centroid":
            row = sum(rows) / len(rows)
            col = sum(cols) / len(cols)
            tr, tc = _bucket(row), _bucket(col)
        elif method == "bounding_box_center":
            row = (min(rows) + max(rows)) / 2
            col = (min(cols) + max(cols)) / 2
            tr, tc = _bucket(row), _bucket(col)
        elif method == "nearest_anchor":
            row = sum(rows) / len(rows)
            col = sum(cols) / len(cols)
            tr, tc = _nearest_anchor(row), _nearest_anchor(col)
        elif method == "median_marker":
            tr = _bucket(float(median(rows)))
            tc = _bucket(float(median(cols)))
        else:
            raise ValueError(f"unknown mapping method {method!r}")
        mapping.append(3 * tr + tc)
    return mapping


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _shape_errors(grid)
    if errors:
        return errors

    for index in _SEPARATORS:
        if any(grid[index][c] != 0 for c in range(19)):
            errors.append(f"separator row {index} must be all zero")
        if any(grid[r][index] != 0 for r in range(19)):
            errors.append(f"separator column {index} must be all zero")
    if errors:
        return errors

    panel_values = [
        grid[r][c]
        for r in range(19)
        for c in range(19)
        if r not in _SEPARATORS and c not in _SEPARATORS
    ]
    if any(value == 0 for value in panel_values):
        errors.append("panel interiors may not contain separator color 0")
    colors = set(panel_values)
    if len(colors) != 2:
        errors.append(f"expected exactly two nonzero panel colors, found {sorted(colors)}")
        return errors

    try:
        background = _infer_background(grid)
    except ValueError as exc:
        return errors + [str(exc)]
    if background not in colors:
        errors.append("inferred background is not a panel color")
        return errors

    marker_colors = colors - {background}
    if len(marker_colors) != 1:
        errors.append("expected one marker color shared by all panels")
        return errors

    mapping = []
    for source in range(9):
        points = _marker_positions(grid, source, background)
        if not 2 <= len(points) <= 16:
            errors.append(f"panel {source} marker count {len(points)} outside [2,16]")
            continue
        row = sum(r for r, _ in points) / len(points)
        col = sum(c for _, c in points) / len(points)
        mapping.append(3 * _bucket(row) + _bucket(col))
    if len(mapping) != 9:
        return errors
    if sorted(mapping) != list(range(9)):
        errors.append(f"centroid targets must be a permutation of 0..8, got {mapping}")
    elif _is_uniform_cyclic(mapping):
        errors.append("uniform cyclic mappings are outside the training sampler domain")
    return errors


def strict_canonical_like(grid):
    """Accept lawful canonical inputs and the sampler's declared manifold."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    mapping = _target_mapping(grid)
    fixed = sum(source == target for source, target in enumerate(mapping))
    permutation_kind = "derangement" if fixed == 0 else "mixed_fixed"

    background = _infer_background(grid)
    marker_total = sum(
        len(_marker_positions(grid, source, background)) for source in range(9)
    )
    if marker_total <= 63:
        marker_density = "sparse"
    elif marker_total >= 81:
        marker_density = "dense"
    else:
        raise ValueError(f"marker total {marker_total} is outside generated density bands")

    colors = {value for row in grid for value in row if value != 0}
    if colors <= set(_LOW_COLORS):
        palette_band = "low"
    elif colors <= set(_HIGH_COLORS):
        palette_band = "high"
    else:
        raise ValueError(f"palette {sorted(colors)} is outside generated palette bands")
    return {
        "permutation_kind": permutation_kind,
        "marker_density": marker_density,
        "palette_band": palette_band,
    }


def _apply_mapping(grid, mapping) -> list[list[int]]:
    """Copy panels by a source->target map; resolve rival collisions deterministically."""
    first_source = {}
    for source, target in enumerate(mapping):
        first_source.setdefault(target, source)
    output = full_grid(19, 19, 0)
    for target in range(9):
        source = first_source.get(target, target)
        sbr, sbc = divmod(source, 3)
        tbr, tbc = divmod(target, 3)
        sr0, sc0 = 1 + 6 * sbr, 1 + 6 * sbc
        tr0, tc0 = 1 + 6 * tbr, 1 + 6 * tbc
        for row in range(5):
            output[tr0 + row][tc0 : tc0 + 5] = list(grid[sr0 + row][sc0 : sc0 + 5])
    return output


def rule_mirror(grid):
    """Independent Python mirror used only for tests and semantic diagnostics."""
    mapping = _target_mapping(grid, "centroid")
    if sorted(mapping) != list(range(9)):
        raise ValueError("centroid targets are not a bijection")
    return _apply_mapping(grid, mapping)


def _one_marker_global_shift(grid):
    first_target = _target_mapping(grid, "centroid")[0]
    return _apply_mapping(grid, [(source + first_target) % 9 for source in range(9)])


def _bounding_box_center(grid):
    return _apply_mapping(grid, _target_mapping(grid, "bounding_box_center"))


def _nearest_anchor_rule(grid):
    return _apply_mapping(grid, _target_mapping(grid, "nearest_anchor"))


def _median_marker_rule(grid):
    return _apply_mapping(grid, _target_mapping(grid, "median_marker"))


def _independent_markers(grid) -> bool:
    return not _is_uniform_cyclic(_target_mapping(grid, "centroid"))


def _bbox_probe(grid) -> bool:
    return _target_mapping(grid, "centroid") != _target_mapping(grid, "bounding_box_center")


def _nearest_probe(grid) -> bool:
    return _target_mapping(grid, "centroid") != _target_mapping(grid, "nearest_anchor")


def _median_probe(grid) -> bool:
    return _target_mapping(grid, "centroid") != _target_mapping(grid, "median_marker")


SEMANTIC_WITNESSES = {
    "independent_markers": _independent_markers,
    "bbox_not_centroid": _bbox_probe,
    "nearest_anchor_not_threshold": _nearest_probe,
    "median_not_centroid": _median_probe,
}
SEMANTIC_RIVALS = {
    "one_marker_global_shift": _one_marker_global_shift,
    "bounding_box_center": _bounding_box_center,
    "nearest_anchor": _nearest_anchor_rule,
    "median_marker": _median_marker_rule,
}
WITNESS_RIVALS = {
    "independent_markers": ["one_marker_global_shift"],
    "bbox_not_centroid": ["bounding_box_center"],
    "nearest_anchor_not_threshold": ["nearest_anchor"],
    "median_not_centroid": ["median_marker"],
}
CANONICAL_SHORTCUTS = {
    "bounding_box_center": _bounding_box_center,
    "nearest_anchor": _nearest_anchor_rule,
    "median_marker": _median_marker_rule,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
