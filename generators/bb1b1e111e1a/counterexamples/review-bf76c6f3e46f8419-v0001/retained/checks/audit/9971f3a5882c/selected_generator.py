"""Sparse rectangular-lattice stretch generator for ARC task 9971f3a5882c.

The unchanged Racket authority treats color 3 as a rectangular grid made from
complete rows and columns.  Exterior color-6 markers redefine one or more
bounding-box sides: the nearest marker on a side sits one cell beyond the new
boundary.  Source boundary lines move to those new boundaries, internal full
rows/columns stay at their original coordinates, and the markers are restored.

The legacy generator sampled a *filled* color-3 rectangle and therefore rejected
all canonical examples.  This version generates the actual sparse grammar,
exposes only exact observable profile controls, and schedules decisive examples
against two canonical-fitting rival rules:

* ``ignore_top_markers`` -- canonical data never places a marker above the grid;
* ``farthest_same_side_marker`` -- canonical data has at most one marker/side.

Every cyclic three-example default window contains a top-marker witness and a
multiple-marker-on-one-side witness.  Stronger still, every four-example cyclic
window contains two joint witnesses, so holding out any member as the query
still leaves demonstrations that refute both shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9971f3a5882c"
TASK_ID = GENERATOR_ID
RULE_HASH = "f753f2c684d9"
VERSION = "2.0.0"
SUMMARY = (
    "A sparse color-3 rectangular lattice is stretched outward to boundaries "
    "implied by exterior color-6 markers. Boundary rows/columns move, internal "
    "complete rows/columns stay fixed, and markers remain color 6. Exact canvas, "
    "lattice, and marker profiles are observable from every returned input."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "input colors are exactly a subset of {0,3,6}",
    "color 3 is the union of complete rows and columns in one rectangular bbox",
    "all four source-bbox edges are complete color-3 lines",
    "every color-6 marker is outside the source bbox and names one bbox side",
    "the nearest marker on each occupied side leaves at least one-cell expansion",
    "the authoritative output preserves markers and moves only boundary lines",
]

CANVAS_PROFILES: dict[str, tuple[int, int]] = {
    # The first four profiles are the four canonical (height, width) profiles.
    "c8x17": (8, 17),
    "c11x15": (11, 15),
    "c15x15": (15, 15),
    "c16x17": (16, 17),
    # One lawful broader profile prevents a fixed-canonical-dimensions shortcut.
    "broad18x19": (18, 19),
}

# (bbox height, bbox width, full-row offsets, full-column offsets)
LATTICE_PROFILES: dict[str, tuple[int, int, tuple[int, ...], tuple[int, ...]]] = {
    "frame3x3": (3, 3, (0, 2), (0, 2)),
    "cols3x5": (3, 5, (0, 2), (0, 2, 4)),
    "rows4x3": (4, 3, (0, 2, 3), (0, 2)),
    "lattice4x6": (4, 6, (0, 2, 3), (0, 3, 5)),
}

# Side -> marker count.  A count of two means a near marker and an additional
# farther marker on the same side.  The intended rule uses the nearest one.
MARKER_PROFILES: dict[str, dict[str, int]] = {
    "left_bottom": {"left": 1, "bottom": 1},
    "right_bottom": {"right": 1, "bottom": 1},
    "left_right_bottom": {"left": 1, "right": 1, "bottom": 1},
    "top_left": {"top": 1, "left": 1},
    "top_right": {"top": 1, "right": 1},
    "top_bottom": {"top": 1, "bottom": 1},
    "all_sides": {"top": 1, "bottom": 1, "left": 1, "right": 1},
    "double_left_bottom": {"left": 2, "bottom": 1},
    "top_double_right": {"top": 1, "right": 2},
    "top_double_left": {"top": 1, "left": 2},
}

_CANVAS_NAMES = tuple(CANVAS_PROFILES)
_LATTICE_NAMES = tuple(LATTICE_PROFILES)
_MARKER_NAMES = tuple(MARKER_PROFILES)

AXES = {
    "canvas_profile": {
        "type": "str",
        "default": "five-slot schedule including all canonical dimensions",
        "valid": "c8x17|c11x15|c15x15|c16x17|broad18x19",
    },
    "lattice_profile": {
        "type": "str",
        "default": "four-slot sparse-lattice schedule",
        "valid": "frame3x3|cols3x5|rows4x3|lattice4x6",
    },
    "marker_profile": {
        "type": "str",
        "default": "twelve-slot semantic-teaching schedule",
        "valid": (
            "left_bottom|right_bottom|left_right_bottom|top_left|top_right|"
            "top_bottom|all_sides|double_left_bottom|top_double_right|"
            "top_double_left"
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[()] = ()

# J/C alternation: every even slot is a joint witness (top marker plus two
# markers on one lateral side), while odd slots retain simpler one-per-side
# profiles.  Any cyclic four-slot window contains two J slots; after any one
# pair is held out as query, the remaining three demonstrations still contain
# a joint witness that refutes both declared canonical-fitting rivals.
SCHEDULE_PROFILES = tuple(range(12))
_MARKER_SCHEDULE = (
    "top_double_right", "left_bottom",
    "top_double_left", "right_bottom",
    "top_double_right", "left_right_bottom",
    "top_double_left", "top_left",
    "top_double_right", "top_right",
    "top_double_left", "top_bottom",
)
assert len(_MARKER_SCHEDULE) == len(SCHEDULE_PROFILES)


class IncompatibleOverrides(ValueError):
    """Structured rejection for future cross-axis constraints."""

    def __init__(self, message: str, *axes: str) -> None:
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic curriculum slot; independent of call order."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    # Replay identifiers are exact integers. In particular, bool is an int
    # subclass and int(1.75) silently changes the requested curriculum slot.
    if type(seed) is not int:
        raise ValueError("seed must be a Python int (not bool, float, or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python int")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    domains = {
        "canvas_profile": CANVAS_PROFILES,
        "lattice_profile": LATTICE_PROFILES,
        "marker_profile": MARKER_PROFILES,
    }
    for name, domain in domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(
                f"{name} override {value!r} is invalid; expected one of "
                f"{', '.join(domain)}"
            )


def _effective_profiles(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> dict[str, str]:
    del seed, difficulty
    defaults = {
        "canvas_profile": _CANVAS_NAMES[int(sample_index) % len(_CANVAS_NAMES)],
        "lattice_profile": _LATTICE_NAMES[int(sample_index) % len(_LATTICE_NAMES)],
        "marker_profile": _MARKER_SCHEDULE[int(sample_index) % len(_MARKER_SCHEDULE)],
    }
    defaults.update({key: value for key, value in overrides.items() if value is not None})
    return defaults


def _side_counts_from_marks(
    bbox: tuple[int, int, int, int],
    marks: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> dict[str, int]:
    """Classify markers with the same precedence as the Racket authority."""
    r0, r1, c0, c1 = bbox
    counts = Counter({side: 0 for side in ("top", "bottom", "left", "right")})
    for row, column in marks:
        if row < r0 and c0 <= column <= c1:
            counts["top"] += 1
        elif row > r1 and c0 <= column <= c1:
            counts["bottom"] += 1
        elif column < c0:
            counts["left"] += 1
        elif column > c1:
            counts["right"] += 1
        else:  # pragma: no cover - guarded by _analyze_lattice
            raise ValueError(f"marker {(row, column)} does not define a bbox side")
    return dict(counts)


def _target_bbox(
    bbox: tuple[int, int, int, int],
    marks: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    *,
    ignore_top: bool = False,
    farthest: bool = False,
) -> tuple[int, int, int, int]:
    r0, r1, c0, c1 = bbox
    above = [(r, c) for r, c in marks if r < r0 and c0 <= c <= c1]
    below = [(r, c) for r, c in marks if r > r1 and c0 <= c <= c1]
    left = [(r, c) for r, c in marks if c < c0]
    right = [(r, c) for r, c in marks if c > c1]
    if ignore_top:
        above = []

    # Nearest is max for top/left and min for bottom/right. Farthest reverses it.
    nr0 = r0 if not above else (min if farthest else max)(r for r, _ in above) + 1
    nr1 = r1 if not below else (max if farthest else min)(r for r, _ in below) - 1
    nc0 = c0 if not left else (min if farthest else max)(c for _, c in left) + 1
    nc1 = c1 if not right else (max if farthest else min)(c for _, c in right) - 1
    return nr0, nr1, nc0, nc1


def _analyze_lattice(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError(f"grid dimensions {height}x{width} are outside ARC bounds 1..30")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("grid cells must be integers")
    colors = {value for row in grid for value in row}
    if not colors <= {0, 3, 6}:
        raise ValueError(f"unexpected colors: {sorted(colors - {0, 3, 6})}")

    cells3 = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 3
    ]
    marks = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 6
    ]
    if not cells3:
        raise ValueError("no color-3 lattice")
    if not marks:
        raise ValueError("no color-6 markers")

    r0 = min(row for row, _ in cells3)
    r1 = max(row for row, _ in cells3)
    c0 = min(column for _, column in cells3)
    c1 = max(column for _, column in cells3)
    bbox = (r0, r1, c0, c1)
    full_rows = tuple(
        row
        for row in range(r0, r1 + 1)
        if all(grid[row][column] == 3 for column in range(c0, c1 + 1))
    )
    full_cols = tuple(
        column
        for column in range(c0, c1 + 1)
        if all(grid[row][column] == 3 for row in range(r0, r1 + 1))
    )
    expected = {
        (row, column)
        for row in range(r0, r1 + 1)
        for column in range(c0, c1 + 1)
        if row in full_rows or column in full_cols
    }
    if set(cells3) != expected:
        raise ValueError(
            "color-3 cells must be exactly a union of complete bbox rows and columns"
        )
    if all(
        grid[row][column] == 3
        for row in range(r0, r1 + 1)
        for column in range(c0, c1 + 1)
    ):
        raise ValueError("color-3 source must be a sparse lattice, not a filled rectangle")
    if not ({r0, r1} <= set(full_rows) and {c0, c1} <= set(full_cols)):
        raise ValueError("lattice bbox edges must be complete color-3 rows and columns")
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        raise ValueError("lattice bbox must be at least 3x3")

    mark_tuple = tuple(marks)
    # Classification itself rejects markers that cannot name a side.
    side_counts = _side_counts_from_marks(bbox, mark_tuple)
    if any(count > 2 for count in side_counts.values()):
        raise ValueError(f"at most two markers are allowed per side, got {side_counts}")

    nr0, nr1, nc0, nc1 = _target_bbox(bbox, mark_tuple)
    if not (0 <= nr0 <= r0 <= r1 <= nr1 < height):
        raise ValueError(
            f"vertical target bbox {(nr0, nr1)} is invalid for source {(r0, r1)}"
        )
    if not (0 <= nc0 <= c0 <= c1 <= nc1 < width):
        raise ValueError(
            f"horizontal target bbox {(nc0, nc1)} is invalid for source {(c0, c1)}"
        )
    if (nr0, nr1, nc0, nc1) == bbox:
        raise ValueError("markers do not expand any source boundary")

    # A marker immediately adjacent to its source edge creates a zero-distance
    # side cue.  Canonical examples and generated lessons all leave a visible
    # one-cell target boundary between source and marker.
    nearest = {
        "top": max((r for r, c in marks if r < r0 and c0 <= c <= c1), default=None),
        "bottom": min((r for r, c in marks if r > r1 and c0 <= c <= c1), default=None),
        "left": max((c for r, c in marks if c < c0), default=None),
        "right": min((c for r, c in marks if c > c1), default=None),
    }
    if nearest["top"] is not None and nearest["top"] + 1 >= r0:
        raise ValueError("top marker must leave at least one expansion row")
    if nearest["bottom"] is not None and nearest["bottom"] - 1 <= r1:
        raise ValueError("bottom marker must leave at least one expansion row")
    if nearest["left"] is not None and nearest["left"] + 1 >= c0:
        raise ValueError("left marker must leave at least one expansion column")
    if nearest["right"] is not None and nearest["right"] - 1 <= c1:
        raise ValueError("right marker must leave at least one expansion column")

    return {
        "height": height,
        "width": width,
        "bbox": bbox,
        "target_bbox": (nr0, nr1, nc0, nc1),
        "full_rows": full_rows,
        "full_cols": full_cols,
        "marks": mark_tuple,
        "side_counts": side_counts,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete sparse-lattice input grammar."""
    del difficulty, meta
    try:
        _analyze_lattice(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """Recognize the task's canonical sparse-lattice manifold.

    This predicate is intentionally structural rather than dimension-exact: the
    canonical rows demonstrate the grammar, while the generator lawfully varies
    dimensions and marker configurations to disambiguate the rule.
    """
    return self_check(grid)


def _solve_with_policy(
    grid: list[list[int]],
    *,
    ignore_top: bool = False,
    farthest: bool = False,
) -> list[list[int]]:
    analysis = _analyze_lattice(grid)
    r0, r1, c0, c1 = analysis["bbox"]
    nr0, nr1, nc0, nc1 = _target_bbox(
        analysis["bbox"],
        analysis["marks"],
        ignore_top=ignore_top,
        farthest=farthest,
    )

    out = full_grid(analysis["height"], analysis["width"], 0)
    for row, column in analysis["marks"]:
        out[row][column] = 6

    for row in analysis["full_rows"]:
        mapped = nr0 if row == r0 else nr1 if row == r1 else row
        for column in range(nc0, nc1 + 1):
            out[mapped][column] = 3
    for column in analysis["full_cols"]:
        mapped = nc0 if column == c0 else nc1 if column == c1 else column
        for row in range(nr0, nr1 + 1):
            out[row][mapped] = 3

    # Markers win if a rival policy happens to move a boundary through one.
    for row, column in analysis["marks"]:
        out[row][column] = 6
    return out


def solve_python(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used for tests; Racket remains authoritative."""
    return _solve_with_policy(grid)


def _ignore_top_markers(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_policy(grid, ignore_top=True)


def _farthest_same_side_marker(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_policy(grid, farthest=True)


def _marker_profile_name(side_counts: dict[str, int]) -> str:
    target = {side: count for side, count in side_counts.items() if count}
    matches = [name for name, profile in MARKER_PROFILES.items() if profile == target]
    if len(matches) != 1:
        raise ValueError(f"marker side-count profile {target} is not declared")
    return matches[0]


def observe_overrides(grid) -> dict[str, str]:
    """Recover every exact declared profile from returned pixels."""
    analysis = _analyze_lattice(grid)
    dimensions = (analysis["height"], analysis["width"])
    canvas_matches = [name for name, value in CANVAS_PROFILES.items() if value == dimensions]
    if len(canvas_matches) != 1:
        raise ValueError(f"canvas dimensions {dimensions} are not a declared profile")

    r0, r1, c0, c1 = analysis["bbox"]
    signature = (
        r1 - r0 + 1,
        c1 - c0 + 1,
        tuple(row - r0 for row in analysis["full_rows"]),
        tuple(column - c0 for column in analysis["full_cols"]),
    )
    lattice_matches = [
        name for name, value in LATTICE_PROFILES.items() if value == signature
    ]
    if len(lattice_matches) != 1:
        raise ValueError(f"lattice signature {signature} is not a declared profile")

    return {
        "canvas_profile": canvas_matches[0],
        "lattice_profile": lattice_matches[0],
        "marker_profile": _marker_profile_name(analysis["side_counts"]),
    }


def _minimum_padding(marker_counts: dict[str, int]) -> dict[str, int]:
    # 1 cell of actual expansion + N longitudinal marker cells.
    return {
        side: (1 + marker_counts.get(side, 0) if marker_counts.get(side, 0) else 0)
        for side in ("top", "bottom", "left", "right")
    }


def _distribute_slack(
    base: dict[str, int],
    vertical_slack: int,
    horizontal_slack: int,
    rng,
    difficulty: str | None,
) -> dict[str, int]:
    pads = dict(base)
    if difficulty == "easy":
        # Balanced placement keeps every cue near the source and minimizes the
        # amount of blank search space.
        pads["top"] += vertical_slack // 2
        pads["bottom"] += vertical_slack - vertical_slack // 2
        pads["left"] += horizontal_slack // 2
        pads["right"] += horizontal_slack - horizontal_slack // 2
        return pads
    if difficulty == "hard":
        # Put spare space on one keyed side per axis, creating deliberately
        # off-center scenes while preserving the same observable profile.
        pads[rng.choice(("top", "bottom"))] += vertical_slack
        pads[rng.choice(("left", "right"))] += horizontal_slack
        return pads
    for _ in range(vertical_slack):
        pads[rng.choice(("top", "bottom"))] += 1
    for _ in range(horizontal_slack):
        pads[rng.choice(("left", "right"))] += 1
    return pads


def _side_markers(
    *,
    side: str,
    count: int,
    bbox: tuple[int, int, int, int],
    pad: int,
    rng,
    difficulty: str | None,
) -> list[tuple[int, int]]:
    if count == 0:
        return []
    r0, r1, c0, c1 = bbox
    # Reserve `count` cells for markers and at least one cell for expansion.
    max_expansion = pad - count
    if max_expansion < 1:
        raise RuntimeError(f"insufficient {side} padding {pad} for {count} marker(s)")
    if difficulty == "easy":
        expansion = 1
    elif difficulty == "hard":
        expansion = max_expansion
    else:
        expansion = rng.randint(1, max_expansion)

    if side == "top":
        near = r0 - expansion - 1
        return [(near - offset, rng.randint(c0, c1)) for offset in range(count)]
    if side == "bottom":
        near = r1 + expansion + 1
        return [(near + offset, rng.randint(c0, c1)) for offset in range(count)]
    if side == "left":
        near = c0 - expansion - 1
        return [(rng.randint(r0, r1), near - offset) for offset in range(count)]
    if side == "right":
        near = c1 + expansion + 1
        return [(rng.randint(r0, r1), near + offset) for offset in range(count)]
    raise ValueError(f"unknown side {side!r}")


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    effective = _effective_profiles(seed, sample_index, difficulty, overrides)

    # Scheduled defaults are supplied as effective overrides so every AXES key
    # is still consumed by a typed GenCtx draw with complete option provenance.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    canvas_profile = ctx.draw_choice("canvas_profile", _CANVAS_NAMES)
    lattice_profile = ctx.draw_choice("lattice_profile", _LATTICE_NAMES)
    marker_profile = ctx.draw_choice("marker_profile", _MARKER_NAMES)

    height, width = CANVAS_PROFILES[canvas_profile]
    lattice_h, lattice_w, row_offsets, col_offsets = LATTICE_PROFILES[lattice_profile]
    marker_counts = MARKER_PROFILES[marker_profile]
    minimum = _minimum_padding(marker_counts)
    vertical_slack = height - lattice_h - minimum["top"] - minimum["bottom"]
    horizontal_slack = width - lattice_w - minimum["left"] - minimum["right"]
    if vertical_slack < 0 or horizontal_slack < 0:
        raise IncompatibleOverrides(
            "canvas/lattice/marker profile combination does not fit",
            "canvas_profile",
            "lattice_profile",
            "marker_profile",
        )

    layout_rng = ctx.draw_rng(
        f"layout:{canvas_profile}:{lattice_profile}:{marker_profile}"
    )
    pads = _distribute_slack(
        minimum, vertical_slack, horizontal_slack, layout_rng, difficulty
    )
    r0 = pads["top"]
    c0 = pads["left"]
    r1 = r0 + lattice_h - 1
    c1 = c0 + lattice_w - 1
    bbox = (r0, r1, c0, c1)

    grid = full_grid(height, width, 0)
    full_rows = {r0 + offset for offset in row_offsets}
    full_cols = {c0 + offset for offset in col_offsets}
    for row in range(r0, r1 + 1):
        for column in range(c0, c1 + 1):
            if row in full_rows or column in full_cols:
                grid[row][column] = 3

    marks: list[tuple[int, int]] = []
    for side in ("top", "bottom", "left", "right"):
        marks.extend(
            _side_markers(
                side=side,
                count=marker_counts.get(side, 0),
                bbox=bbox,
                pad=pads[side],
                rng=layout_rng,
                difficulty=difficulty,
            )
        )
    if len(marks) != len(set(marks)):
        # Longitudinal positions are unique per side and side marker regions do
        # not overlap, so this is an internal invariant rather than retry logic.
        raise RuntimeError(f"constructed duplicate marker coordinates: {marks}")
    for row, column in marks:
        grid[row][column] = 6

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid sparse-lattice input: {errors}")
    observed = observe_overrides(grid)
    if observed != {
        "canvas_profile": canvas_profile,
        "lattice_profile": lattice_profile,
        "marker_profile": marker_profile,
    }:
        raise RuntimeError(f"constructed profile is not observable: {observed}")
    return [row[:] for row in grid]


def _has_top_marker(grid) -> bool:
    try:
        return _analyze_lattice(grid)["side_counts"]["top"] > 0
    except (TypeError, ValueError):
        return False


def _has_multiple_same_side_markers(grid) -> bool:
    try:
        return max(_analyze_lattice(grid)["side_counts"].values()) >= 2
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_top_markers": _ignore_top_markers,
    "farthest_same_side_marker": _farthest_same_side_marker,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "top_marker": _has_top_marker,
    "multiple_same_side_markers": _has_multiple_same_side_markers,
}
WITNESS_RIVALS = {
    "top_marker": ["ignore_top_markers"],
    "multiple_same_side_markers": ["farthest_same_side_marker"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to refute every declared plausible competitor."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survived = True
        for pair in demos:
            try:
                predicted = competitor(deepcopy(pair["input"]))
                expected = pair["output"]
            except Exception as exc:
                reasons.append(
                    f"competitor {name!r} raised {type(exc).__name__}: {exc}"
                )
                survived = False
                break
            if predicted != expected:
                survived = False
                break
        if survived:
            reasons.append(f"competitor {name!r} fits every demonstration")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    return reasons
