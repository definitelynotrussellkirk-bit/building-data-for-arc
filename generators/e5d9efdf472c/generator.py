"""Generator for arc_additional_puzzle_bank_volume15:E103.

Two magenta (6) markers are horizontally or vertically aligned.  The canonical
Racket rule preserves the input and paints only the zero cells strictly between
those markers cyan (8).  Sparse non-{0,6,8} decorations are deliberately kept
in the teaching distribution; one profile uses a separated same-color pair so
the shortcuts "connect every repeated color" and "connect only the longest
repeated pair" cannot survive.  In that profile the non-magenta pair is
deliberately farther apart than the magenta markers, making color—not length—
the causal selector.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e5d9efdf472c"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"  # decorrelated semantic profiles + causal shortcut-refuting curriculum
RULE_HASH = "29bed64c5255"  # sha256[:12] of whitespace-normalized selected rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Exactly two magenta (6) markers share a row or column with at least one "
    "empty cell between them. Paint only those strict-interior cells cyan (8), "
    "preserving both magenta endpoints and every off-segment decoration."
)

INVARIANTS = [
    "background is 0 and input color 8 is absent",
    "exactly two magenta (6) markers are horizontally or vertically aligned",
    "the marker gap contains 1..5 zero cells before transformation",
    "off-segment decorations use colors outside {0, 6, 8} and are preserved",
    "the Racket oracle paints only the strict interior of the magenta segment cyan (8)",
]

ORIENTATIONS = ("horizontal", "vertical")
DECOR_PATTERNS = ("single", "adjacent_pair", "separated_pair")
DECOR_COLORS = (1, 2, 3, 4, 5, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked profile",
        "valid": "7..11",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked profile",
        "valid": "8..12",
        "doc": "Input-grid width.",
    },
    "orientation": {
        "type": "enum",
        "default": "linked profile",
        "valid": ["horizontal", "vertical"],
        "doc": "Axis joining the two magenta markers.",
    },
    "gap": {
        "type": "int",
        "default": "linked profile",
        "valid": "1..5",
        "doc": "Number of zero cells strictly between the magenta endpoints.",
    },
    "decor_pattern": {
        "type": "enum",
        "default": "linked profile",
        "valid": ["single", "adjacent_pair", "separated_pair"],
        "doc": (
            "One preserved decoration cell, an adjacent same-color pair, or a "
            "separated same-color pair that must NOT be connected."
        ),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every consecutive four draws still contain both marker orientations, short,
# middle and long gaps, and all three decoration roles.  Unlike v3, however,
# seed changes also vary the semantic axes instead of selecting one of only
# four hard-coded tuples per band.  One residue remains an exact canonical
# anchor; the other three sample within the same sparse scene family.
_CANONICAL_LINKED_PROFILES = (
    (7, 9, "horizontal", 5, "single"),
    (8, 8, "vertical", 3, "adjacent_pair"),
    (9, 10, "vertical", 4, "single"),
    (7, 11, "horizontal", 5, "single"),
    (8, 10, "vertical", 4, "single"),
)

_CANONICAL_LINKED_KEYS = frozenset(_CANONICAL_LINKED_PROFILES)

_GRID_RANGES_BY_BAND = {
    "easy": {"grid_h": (7, 8), "grid_w": (8, 10)},
    "medium": {"grid_h": (7, 10), "grid_w": (8, 11)},
    "hard": {"grid_h": (8, 11), "grid_w": (9, 12)},
}

_SCHEDULE_ROLES = (
    "long_single",
    "canonical_anchor",
    "short_separated",
    "middle_adjacent",
)

SCHEDULE_PROFILES = _SCHEDULE_ROLES


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-slot causal curriculum to the semantic gate."""
    del seed, difficulty
    return _SCHEDULE_ROLES[sample_index % 4]


def _other_orientation(orientation: str) -> str:
    return "vertical" if orientation == "horizontal" else "horizontal"


def _default_profile(seed: int, sample_index: int, band: str) -> dict[str, object]:
    """Return a role-constrained but seed-varying semantic profile."""
    role = _SCHEDULE_ROLES[sample_index % 4]
    ranges = _GRID_RANGES_BY_BAND[band]
    cycle_orientation = stable_rng(
        seed,
        f"{TASK_ID}|curriculum-orientation",
        VERSION,
    ).choice(ORIENTATIONS)

    if role == "canonical_anchor":
        anchor = stable_rng(
            seed,
            f"{TASK_ID}|canonical-anchor|{sample_index // 4}",
            VERSION,
        ).choice(_CANONICAL_LINKED_PROFILES)
        h, w, orientation, gap, decor_pattern = anchor
        return {
            "grid_h": h,
            "grid_w": w,
            "orientation": orientation,
            "gap": gap,
            "decor_pattern": decor_pattern,
        }

    if role == "long_single":
        orientation = cycle_orientation
        gap: int | tuple[int, int] = (4, 5)
        decor_pattern = "single"
    elif role == "short_separated":
        orientation = _other_orientation(cycle_orientation)
        gap = 1
        decor_pattern = "separated_pair"
    elif role == "middle_adjacent":
        orientation = stable_rng(
            seed,
            f"{TASK_ID}|middle-orientation|{sample_index // 4}",
            VERSION,
        ).choice(ORIENTATIONS)
        gap = (2, 3)
        decor_pattern = "adjacent_pair"
    else:  # pragma: no cover - role table and schedule are module constants
        raise ValueError(f"unsupported schedule role {role!r}")

    return {
        "grid_h": ranges["grid_h"],
        "grid_w": ranges["grid_w"],
        "orientation": orientation,
        "gap": gap,
        "decor_pattern": decor_pattern,
    }


def _draw_int_axis(
    ctx,
    overrides,
    label: str,
    default: int | tuple[int, int],
    lo: int,
    hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if isinstance(default, tuple):
        default_lo, default_hi = default
        return ctx.draw_int(label, default_lo, default_hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _endpoint_pair(rng, h: int, w: int, orientation: str, gap: int):
    distance = gap + 1
    if orientation == "horizontal":
        row = rng.randrange(h)
        col = rng.randint(0, w - distance - 1)
        return (row, col), (row, col + distance)
    if orientation == "vertical":
        row = rng.randint(0, h - distance - 1)
        col = rng.randrange(w)
        return (row, col), (row + distance, col)
    raise ValueError(f"unsupported orientation {orientation!r}")


def _segment_cells(first: tuple[int, int], second: tuple[int, int]) -> list[tuple[int, int]]:
    r1, c1 = first
    r2, c2 = second
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    distance = max(abs(r2 - r1), abs(c2 - c1))
    return [(r1 + step * dr, c1 + step * dc) for step in range(distance + 1)]


def _candidate_adjacent_pairs(h: int, w: int, forbidden: set[tuple[int, int]]):
    pairs = []
    for row in range(h):
        for col in range(w):
            first = (row, col)
            if first in forbidden:
                continue
            for second in ((row, col + 1), (row + 1, col)):
                rr, cc = second
                if rr < h and cc < w and second not in forbidden:
                    pairs.append((first, second))
    return pairs


def _candidate_separated_pairs(
    h: int,
    w: int,
    forbidden: set[tuple[int, int]],
    *,
    min_distance: int = 2,
):
    pairs = []
    for row in range(h):
        for c1 in range(w):
            for c2 in range(c1 + min_distance, w):
                cells = {(row, col) for col in range(c1, c2 + 1)}
                if cells.isdisjoint(forbidden):
                    pairs.append(((row, c1), (row, c2)))
    for col in range(w):
        for r1 in range(h):
            for r2 in range(r1 + min_distance, h):
                cells = {(row, col) for row in range(r1, r2 + 1)}
                if cells.isdisjoint(forbidden):
                    pairs.append(((r1, col), (r2, col)))
    return pairs


def _place_decorations(
    grid: list[list[int]],
    rng,
    pattern: str,
    forbidden: set[tuple[int, int]],
    *,
    min_separated_distance: int = 2,
) -> None:
    h, w = len(grid), len(grid[0])
    color = rng.choice(DECOR_COLORS)
    free = [(r, c) for r in range(h) for c in range(w) if (r, c) not in forbidden]
    if pattern == "single":
        row, col = rng.choice(free)
        grid[row][col] = color
        return
    if pattern == "adjacent_pair":
        candidates = _candidate_adjacent_pairs(h, w, forbidden)
    elif pattern == "separated_pair":
        candidates = _candidate_separated_pairs(
            h,
            w,
            forbidden,
            min_distance=min_separated_distance,
        )
    else:
        raise ValueError(f"unsupported decor_pattern {pattern!r}")
    if not candidates:
        raise ValueError(f"no placement available for decor_pattern={pattern!r}")
    first, second = rng.choice(candidates)
    grid[first[0]][first[1]] = color
    grid[second[0]][second[1]] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; the canonical Racket rule owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _default_profile(seed, sample_index, band)
    h = _draw_int_axis(ctx, overrides, "grid_h", profile["grid_h"], 7, 11)
    w = _draw_int_axis(ctx, overrides, "grid_w", profile["grid_w"], 8, 12)
    orientation = _draw_choice_axis(
        ctx, overrides, "orientation", profile["orientation"], ORIENTATIONS
    )
    gap = _draw_int_axis(ctx, overrides, "gap", profile["gap"], 1, 5)
    decor_pattern = _draw_choice_axis(
        ctx, overrides, "decor_pattern", profile["decor_pattern"], DECOR_PATTERNS
    )

    distance = gap + 1
    if orientation == "horizontal" and distance >= w:
        raise ValueError(f"gap {gap} does not fit width {w}")
    if orientation == "vertical" and distance >= h:
        raise ValueError(f"gap {gap} does not fit height {h}")

    grid = full_grid(h, w, 0)
    placement_rng = ctx.draw_rng("placement")
    first, second = _endpoint_pair(placement_rng, h, w, orientation, gap)
    grid[first[0]][first[1]] = 6
    grid[second[0]][second[1]] = 6
    forbidden = set(_segment_cells(first, second))
    default_short_counterexample = (
        _SCHEDULE_ROLES[sample_index % 4] == "short_separated"
        and not any(name in overrides for name in AXES)
    )
    _place_decorations(
        grid,
        ctx.draw_rng("decorations"),
        decor_pattern,
        forbidden,
        min_separated_distance=(gap + 2 if default_short_counterexample else 2),
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "orientation": orientation,
        "gap": gap,
        "decor_pattern": decor_pattern,
    }
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return [row[:] for row in grid]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _decoration_pattern(grid, cells: list[tuple[int, int]]) -> str | None:
    if len(cells) == 1:
        return "single"
    if len(cells) != 2:
        return None
    (r1, c1), (r2, c2) = cells
    if grid[r1][c1] != grid[r2][c2]:
        return None
    distance = abs(r1 - r2) + abs(c1 - c2)
    if distance == 1:
        return "adjacent_pair"
    if (r1 == r2 or c1 == c2) and distance >= 2:
        return "separated_pair"
    return None


def _pair_distance(cells: list[tuple[int, int]]) -> int | None:
    if len(cells) != 2:
        return None
    (r1, c1), (r2, c2) = cells
    if r1 != r2 and c1 != c2:
        return None
    return abs(r1 - r2) + abs(c1 - c2)


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 11:
        errors.append(f"grid height {h} outside 7..11")
    if not 8 <= w <= 12:
        errors.append(f"grid width {w} outside 8..12")
    if any(value == 8 for row in grid for value in row):
        errors.append("input must not contain cyan fill color 8")

    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    ]
    if len(markers) != 2:
        errors.append(f"expected exactly two magenta markers, found {len(markers)}")
        return {"errors": errors, "grid_h": h, "grid_w": w, "markers": markers}

    first, second = markers
    r1, c1 = first
    r2, c2 = second
    if r1 == r2 and c1 != c2:
        orientation = "horizontal"
        gap = abs(c2 - c1) - 1
    elif c1 == c2 and r1 != r2:
        orientation = "vertical"
        gap = abs(r2 - r1) - 1
    else:
        orientation = None
        gap = None
        errors.append("the two magenta markers must share exactly one row or column")

    interior: list[tuple[int, int]] = []
    if orientation is not None:
        segment = _segment_cells(first, second)
        interior = segment[1:-1]
        if not 1 <= len(interior) <= 5:
            errors.append(f"marker gap {len(interior)} outside 1..5")
        blocked = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] != 0]
        if blocked:
            errors.append(f"marker interior must be zero before fill; found {blocked[:3]}")

    decorations = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 6, 8)
    ]
    bad_decor = sorted({grid[r][c] for r, c in decorations if grid[r][c] not in DECOR_COLORS})
    if bad_decor:
        errors.append(f"unsupported decoration colors {bad_decor}")
    if len(decorations) > 4:
        errors.append(f"expected at most four sparse decoration cells, found {len(decorations)}")

    pattern = _decoration_pattern(grid, decorations)
    marker_distance = gap + 1 if gap is not None else None
    decor_distance = _pair_distance(decorations)
    outside_segment = False
    if orientation == "horizontal":
        lo, hi = sorted((c1, c2))
        outside_segment = lo > 0 or hi < w - 1
    elif orientation == "vertical":
        lo, hi = sorted((r1, r2))
        outside_segment = lo > 0 or hi < h - 1

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "markers": markers,
        "orientation": orientation,
        "gap": gap,
        "interior": interior,
        "decorations": decorations,
        "decor_pattern": pattern,
        "marker_distance": marker_distance,
        "decor_distance": decor_distance,
        "decor_longer_than_marker": (
            marker_distance is not None
            and decor_distance is not None
            and decor_distance > marker_distance
        ),
        "outside_segment": outside_segment,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural authority grammar; curriculum-only roles live in strict hooks."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact generator axis from a generated grid."""
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts["decor_pattern"] not in DECOR_PATTERNS:
        raise ValueError("decoration layout is outside the exact generated decor_pattern domain")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "orientation": facts["orientation"],
        "gap": facts["gap"],
        "decor_pattern": facts["decor_pattern"],
    }


def semantic_observables(grid) -> dict[str, object]:
    facts = _analyze(grid)
    if facts.get("errors"):
        return {"errors": list(facts["errors"])}
    observed = observe_overrides(grid)
    key = (
        observed["grid_h"],
        observed["grid_w"],
        observed["orientation"],
        observed["gap"],
        observed["decor_pattern"],
    )
    return {
        **observed,
        "canonical_linked_profile": key in _CANONICAL_LINKED_KEYS,
        "decor_count": len(facts["decorations"]),
        "marker_distance": facts["marker_distance"],
        "decor_distance": facts["decor_distance"],
        "decor_longer_than_marker": facts["decor_longer_than_marker"],
        "outside_segment": facts["outside_segment"],
    }


def strict_canonical_like(grid) -> list[str]:
    facts = _analyze(grid)
    if facts.get("errors"):
        return list(facts["errors"])
    pattern = facts["decor_pattern"]
    if pattern is None:
        return ["canonical-like scenes use one decoration color in one generated sparse pattern"]
    key = (
        facts["grid_h"], facts["grid_w"], facts["orientation"], facts["gap"], pattern
    )
    if key not in _CANONICAL_LINKED_KEYS:
        return [f"linked semantic profile {key!r} is outside the five canonical profiles"]
    return []


def _interior_from_facts(facts: dict[str, Any]) -> list[tuple[int, int]]:
    return list(facts["interior"])


def rule_mirror(grid):
    """Pure Python semantic mirror; the Racket program remains output authority."""
    facts = _analyze(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    out = [list(row) for row in grid]
    for row, col in _interior_from_facts(facts):
        out[row][col] = 8
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _rival_horizontal_only(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return rule_mirror(grid) if facts["orientation"] == "horizontal" else _identity(grid)


def _rival_vertical_only(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return rule_mirror(grid) if facts["orientation"] == "vertical" else _identity(grid)


def _rival_connect_every_repeated_color(grid):
    """Canonical-fitting shortcut: connect every aligned repeated nonzero color."""
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for color in range(1, 10):
        if color == 8:
            continue
        pts = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == color]
        if len(pts) != 2:
            continue
        (r1, c1), (r2, c2) = pts
        if r1 == r2:
            for col in range(min(c1, c2) + 1, max(c1, c2)):
                out[r1][col] = 8
        elif c1 == c2:
            for row in range(min(r1, r2) + 1, max(r1, r2)):
                out[row][c1] = 8
    return out


def _rival_connect_longest_repeated_pair(grid):
    """Canonical-fitting shortcut: connect only the widest aligned color pair."""
    h, w = len(grid), len(grid[0])
    candidates: list[
        tuple[int, tuple[int, int], tuple[int, int]]
    ] = []
    for color in range(1, 10):
        if color == 8:
            continue
        points = [
            (row, col)
            for row in range(h)
            for col in range(w)
            if grid[row][col] == color
        ]
        if len(points) != 2:
            continue
        first, second = points
        if first[0] != second[0] and first[1] != second[1]:
            continue
        distance = abs(first[0] - second[0]) + abs(first[1] - second[1])
        candidates.append((distance, first, second))

    if not candidates:
        return _identity(grid)

    _, first, second = max(candidates, key=lambda item: item[0])
    out = _identity(grid)
    for row, col in _segment_cells(first, second)[1:-1]:
        out[row][col] = 8
    return out


def _rival_erase_decorations(grid):
    out = rule_mirror(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in (0, 6, 8):
                out[row][col] = 0
    return out


def _rival_gap_five_only(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    return rule_mirror(grid) if facts["gap"] == 5 else _identity(grid)


def _rival_extend_to_full_axis(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    out = [list(row) for row in grid]
    (r1, c1), (r2, c2) = facts["markers"]
    if facts["orientation"] == "horizontal":
        for col in range(len(out[0])):
            if col not in (c1, c2):
                out[r1][col] = 8
    else:
        for row in range(len(out)):
            if row not in (r1, r2):
                out[row][c1] = 8
    return out


def _rival_recolor_endpoints(grid):
    facts = _analyze(grid)
    if facts.get("errors"):
        return _identity(grid)
    out = rule_mirror(grid)
    for row, col in facts["markers"]:
        out[row][col] = 8
    return out


SEMANTIC_RIVALS = {
    "horizontal only": _rival_horizontal_only,
    "vertical only": _rival_vertical_only,
    "connect every repeated nonzero color": _rival_connect_every_repeated_color,
    "connect only the longest aligned repeated color": _rival_connect_longest_repeated_pair,
    "erase decorations": _rival_erase_decorations,
    "gap five only": _rival_gap_five_only,
    "extend to full axis": _rival_extend_to_full_axis,
    "recolor endpoints cyan": _rival_recolor_endpoints,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These shortcuts exactly fit the real canonical demos: their only repeated
# decoration is an adjacent 4, whose strict interior is empty and whose pair is
# shorter than the magenta marker pair.  The generated long separated-pair
# profile is therefore required evidence, not decorative variety.
CANONICAL_SHORTCUTS = {
    "connect every repeated nonzero color": _rival_connect_every_repeated_color,
    "connect only the longest aligned repeated color": _rival_connect_longest_repeated_pair,
}


def _witness(**expected):
    def predicate(grid) -> bool:
        facts = semantic_observables(grid)
        return not facts.get("errors") and all(facts.get(k) == v for k, v in expected.items())
    return predicate


SEMANTIC_WITNESSES = {
    "horizontal_branch": _witness(orientation="horizontal"),
    "vertical_branch": _witness(orientation="vertical"),
    "adjacent_decoration_canonical_cue": _witness(decor_pattern="adjacent_pair"),
    "separated_decoration_counterexample": _witness(decor_pattern="separated_pair"),
    "longer_decoration_counterexample": _witness(decor_longer_than_marker=True),
    "short_gap_boundary": lambda grid: (
        not semantic_observables(grid).get("errors")
        and semantic_observables(grid).get("gap") == 1
    ),
    "long_gap_branch": lambda grid: (
        not semantic_observables(grid).get("errors")
        and semantic_observables(grid).get("gap") >= 4
    ),
    "decoration_preserved": lambda grid: (
        not semantic_observables(grid).get("errors")
        and semantic_observables(grid).get("decor_count", 0) >= 1
    ),
    "segment_not_full_axis": _witness(outside_segment=True),
    "visible_fill": lambda grid: (
        not semantic_observables(grid).get("errors")
        and semantic_observables(grid).get("gap", 0) >= 1
    ),
}

BRANCH_WITNESSES = {
    "horizontal_branch",
    "vertical_branch",
    "adjacent_decoration_canonical_cue",
    "short_gap_boundary",
    "long_gap_branch",
}

WITNESS_RIVALS = {
    "horizontal_branch": ["vertical only"],
    "vertical_branch": ["horizontal only"],
    "separated_decoration_counterexample": ["connect every repeated nonzero color"],
    "longer_decoration_counterexample": [
        "connect only the longest aligned repeated color"
    ],
    "short_gap_boundary": ["gap five only"],
    "decoration_preserved": ["erase decorations"],
    "segment_not_full_axis": ["extend to full axis"],
    "visible_fill": ["recolor endpoints cyan"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to eliminate named query-changing shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    orientations: set[str] = set()
    patterns: set[str] = set()
    gaps: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the task grammar: {errors[0]}")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the magenta-to-cyan connection rule")
            continue
        observed = observe_overrides(demo["input"])
        orientations.add(str(observed["orientation"]))
        patterns.add(str(observed["decor_pattern"]))
        gaps.add(int(observed["gap"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the task grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the magenta-to-cyan connection rule")
    if reasons:
        return reasons

    if orientations != set(ORIENTATIONS):
        reasons.append(f"demonstrations do not cover both marker orientations: {sorted(orientations)}")
    if "separated_pair" not in patterns:
        reasons.append("demonstrations omit the separated repeated-color shortcut counterexample")
    if "adjacent_pair" not in patterns:
        reasons.append("demonstrations omit the canonical adjacent-pair distractor cue")
    if min(gaps, default=99) > 2 or max(gaps, default=-1) < 4 or len(gaps) < 3:
        reasons.append(f"demonstrations expose insufficient gap variation: {sorted(gaps)}")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_all = all(competitor(demo["input"]) == demo["output"] for demo in demos)
            query_alt = competitor(query["input"])
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised: {type(exc).__name__}: {exc}")
            continue
        if fits_all and query_alt != query_truth:
            reasons.append(
                f"demos remain compatible with competitor {name!r}, which changes the query answer"
            )
    return reasons
