"""Generator for arc_puzzle_bank_sixth21:M36.

Rule: among an odd number of nonzero blobs, keep only the blob whose area is
median. Production lessons use a five/five/three schedule so every two-demo
window, including query rotations, refutes "keep the second-largest".
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c69eb63c11a"
TASK_ID = GENERATOR_ID
VERSION = "2.2.0"
RULE_HASH = "e0d91c9e70a7"
SUMMARY = (
    "Three or five isolated, single-color blobs with strictly distinct areas; "
    "a five/five/three schedule keeps every two-demo lesson identifiable."
)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("five_blobs", "five_blobs", "three_blobs")

INVARIANTS = [
    "background is 0",
    "exactly 3 or 5 nonzero 4-connected blobs",
    "blob areas are strictly distinct",
    "each blob has one color and different blobs have different colors",
    "blobs are separated by at least one orthogonal background cell",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ()

# palette_size and n_distinct_colors were removed: in this family every blob
# necessarily has one unique color, so both were aliases of n_blobs rather than
# independent controls. position_bias and size_spread were also fixed constants.
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 8..14", "valid": "8..14"},
    "n_blobs": {"type": "int", "default": "alternating 3|5", "valid": "3|5"},
    "palette_kind": {
        "type": "str",
        "default": "rng default|warm|cool|varied",
        "valid": "|".join(PALETTE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Fixed color sets make palette_kind recoverable from visible pixels while the
# keyed palette-order draw still varies which area receives which color.
_PALETTES = {
    "default": {
        3: (1, 2, 3),
        5: (1, 2, 3, 4, 5),
    },
    "warm": {
        3: (2, 7, 9),
        5: (2, 4, 6, 7, 9),
    },
    "cool": {
        3: (1, 3, 8),
        5: (1, 3, 5, 6, 8),
    },
    "varied": {
        3: (4, 5, 9),
        5: (1, 4, 5, 7, 9),
    },
}
_PALETTE_LOOKUP = {
    frozenset(colors): kind
    for kind, by_count in _PALETTES.items()
    for colors in by_count.values()
}
_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule; keyed geometry remains independently randomized."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_call_arguments(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _checked_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    controls = {key: value for key, value in overrides.items() if value is not None}
    for key in ("grid_h", "grid_w"):
        if key in controls and (type(controls[key]) is not int or not 8 <= controls[key] <= 14):
            raise ValueError(f"{key} must be an integer in 8..14 (not bool)")
    if "n_blobs" in controls and (
        type(controls["n_blobs"]) is not int or controls["n_blobs"] not in (3, 5)
    ):
        raise ValueError("n_blobs must be the integer 3 or 5 (not bool)")
    if "palette_kind" in controls and controls["palette_kind"] not in PALETTE_KINDS:
        raise ValueError(f"palette_kind must be one of {PALETTE_KINDS}")
    return controls


def _dimension_options(difficulty):
    # Every declared boundary remains legal in every band; weighting only
    # changes the unforced mix.
    if difficulty == "easy":
        return (8, 8, 9, 9, 10, 10, 11, 12, 13, 14)
    if difficulty == "hard":
        return (8, 9, 10, 11, 12, 12, 13, 13, 14, 14)
    return (8, 9, 9, 10, 10, 11, 11, 12, 13, 14)


def _components(grid):
    """Return nonzero 4-connected components with their visible colors."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        colors = set()
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            colors.add(grid[r][c])
            for dr, dc in _DELTAS4:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    queue.append(point)
        out.append({"cells": tuple(cells), "colors": frozenset(colors)})
    return out


def _layout(h, w, sizes, colors, rng):
    """Place exact-size, orthogonally isolated blobs or fail explicitly."""
    pairs = list(zip(sizes, colors))
    # Largest-first leaves the most freedom for hard-to-place shapes.
    pairs.sort(key=lambda pair: pair[0], reverse=True)
    for _attempt in range(512):
        grid = full_grid(h, w, 0)
        used = set()
        placed = True
        for size, color in pairs:
            cells = grow_blob(rng, h, w, used, size, max_attempts=320)
            if cells is None:
                placed = False
                break
            for r, c in cells:
                grid[r][c] = color
            used |= cells
        if placed:
            return grid
    raise RuntimeError(
        f"could not place {len(sizes)} isolated blobs with sizes {sorted(sizes)} in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index, difficulty)
    controls = _checked_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    controls.setdefault("n_blobs", 3 if profile == "three_blobs" else 5)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=controls,
    )

    dimensions = _dimension_options(difficulty)
    h = ctx.draw_choice("grid_h", dimensions)
    w = ctx.draw_choice("grid_w", dimensions)
    n_blobs = ctx.draw_choice("n_blobs", (3, 5))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    colors = list(_PALETTES[palette_kind][n_blobs])
    ctx.draw_rng("palette_order").shuffle(colors)

    if n_blobs == 5:
        # Compact exact support keeps the 8x8 boundary constructive while
        # giving a genuine median distinct from the second-largest.
        sizes = [1, 2, 3, 4, 5]
    else:
        sizes = ctx.draw_rng("sizes").sample(range(1, 7), 3)
    grid = _layout(h, w, sizes, colors, ctx.draw_rng("layout"))
    reasons = self_check(grid, difficulty=difficulty)
    if reasons:
        raise RuntimeError(f"constructed invalid median-area lesson: {reasons}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the production domain accepted by the canonical Racket rule."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["expected nonempty grid rows"]
    if len({len(row) for row in grid}) != 1:
        return ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not bool)"]

    reasons = []
    if not any(value == 0 for row in grid for value in row):
        reasons.append("background color 0 is absent")
    components = _components(grid)
    if len(components) not in (3, 5):
        reasons.append(f"expected exactly 3 or 5 blobs, got {len(components)}")
    sizes = [len(component["cells"]) for component in components]
    if len(set(sizes)) != len(sizes):
        reasons.append(f"blob sizes are not all distinct: {sorted(sizes)}")
    if any(len(component["colors"]) != 1 for component in components):
        reasons.append("each blob must be single-color")
    component_colors = [next(iter(component["colors"])) for component in components if component["colors"]]
    if len(set(component_colors)) != len(component_colors):
        reasons.append("different blobs must use different colors")
    return reasons


def strict_canonical_like(grid):
    """Ordinary draws use exactly the grammar accepted by the canonical rule."""
    return self_check(grid)


def _paint_component(grid, component):
    output = full_grid(len(grid), len(grid[0]), 0)
    for r, c in component["cells"]:
        output[r][c] = grid[r][c]
    return output


def rule_mirror(grid):
    """Independent Python mirror; canonical Racket remains output authority."""
    reasons = self_check(grid)
    if reasons:
        raise ValueError("invalid median-area input: " + "; ".join(reasons))
    ranked = sorted(_components(grid), key=lambda component: len(component["cells"]))
    return _paint_component(grid, ranked[len(ranked) // 2])


def _rival_second_largest_object(grid):
    """Canonical-fitting shortcut when every lesson contains only three blobs."""
    reasons = self_check(grid)
    if reasons:
        raise ValueError("invalid median-area input: " + "; ".join(reasons))
    ranked = sorted(_components(grid), key=lambda component: len(component["cells"]))
    return _paint_component(grid, ranked[-2])


SEMANTIC_RIVALS = {"second_largest_object": _rival_second_largest_object}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _five_blobs_refute_second_largest(grid):
    return (
        self_check(grid) == []
        and len(_components(grid)) == 5
        and rule_mirror(grid) != _rival_second_largest_object(grid)
    )


SEMANTIC_WITNESSES = {
    "five_blobs_refute_second_largest": _five_blobs_refute_second_largest,
}
WITNESS_RIVALS = {
    "five_blobs_refute_second_largest": ["second_largest_object"],
}


def lesson_identifiable(demos, query):
    """Require a correctly labeled five-blob demonstration in each lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons = []
    if self_check(query["input"]):
        reasons.append("query input is outside the median-area teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_reasons = self_check(demo["input"])
        if input_reasons:
            reasons.append(f"demo {index} input is outside the median-area teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact median-area selection")
        valid_demos.append(demo)

    if valid_demos and not any(
        _five_blobs_refute_second_largest(demo["input"]) for demo in valid_demos
    ):
        reasons.append(
            "demonstrations never refute the canonical-fitting second-largest-object shortcut"
        )
    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def observe_overrides(grid):
    """Recover exact visible controls for the override-contract checker."""
    components = _components(grid)
    colors = frozenset(
        next(iter(component["colors"]))
        for component in components
        if len(component["colors"]) == 1
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_blobs": len(components),
        "palette_kind": _PALETTE_LOOKUP.get(colors, "unknown"),
    }
