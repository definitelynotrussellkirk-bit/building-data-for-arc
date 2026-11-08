"""Input sampler for Connect Aligned Pairs (97dd5f3c96b9).

The selected Racket authority starts from an empty grid and paints the inclusive
horizontal or vertical segment joining each color's two markers.  This sampler
stays on a deliberately clear teaching manifold: exactly three colors, mixed
orientations, a real gap in every pair, and pair segments that never overlap.
The non-overlap condition prevents paint order from changing another pair's
original marker, the defect retained in review-ac4e298e7e8909d2:v0001.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "97dd5f3c96b9"
TASK_ID = GENERATOR_ID
RULE_HASH = "8d1d1f690046"
VERSION = "2.0.0"
SUMMARY = (
    "Exactly three nonzero colors appear twice each. Every pair is separated "
    "and row- or column-aligned; the inclusive pair segments are disjoint and "
    "the scene always contains both horizontal and vertical examples."
)

INVARIANTS = [
    "background is integer color 0 on one of the three canonical canvas profiles",
    "exactly three nonzero integer colors appear exactly twice each",
    "every pair is horizontal or vertical with at least one background cell between its markers",
    "the three inclusive pair segments are pairwise disjoint",
    "each scene contains at least one horizontal and at least one vertical pair",
]

SCENE_PROFILES = ("p8x10", "p9x11", "p8x12")
_PROFILE_DIMS = {
    "p8x10": (8, 10),
    "p9x11": (9, 11),
    "p8x12": (8, 12),
}
_DIMS_PROFILE = {dims: profile for profile, dims in _PROFILE_DIMS.items()}
_ORIENTATION_MIXES = (("horizontal", "horizontal", "vertical"),
                      ("horizontal", "vertical", "vertical"))

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "keyed choice among the three canonical size profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 1
MIN_STRICT_FRAC = 1.0


def _copy_grid(grid):
    return [list(row) for row in grid]


def _positions(grid) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color:
                positions[color].append((row_index, column_index))
    return dict(positions)


def _span(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]):
    """Return (orientation, ordered inclusive cells) for one aligned pair."""
    if len(cells) != 2:
        raise ValueError(f"expected two marker cells, found {len(cells)}")
    (row0, column0), (row1, column1) = cells
    if row0 == row1 and column0 != column1:
        lo, hi = sorted((column0, column1))
        return "horizontal", tuple((row0, column) for column in range(lo, hi + 1))
    if column0 == column1 and row0 != row1:
        lo, hi = sorted((row0, row1))
        return "vertical", tuple((row, column0) for row in range(lo, hi + 1))
    raise ValueError(
        f"marker pair {cells!r} must share exactly one row or column"
    )


def _analyze(grid) -> tuple[list[str], dict[str, Any] | None]:
    """Parse the declared input grammar without mutating or throwing."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"], None
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (booleans are not colors)"], None

    height = len(grid)
    errors: list[str] = []
    if (height, width) not in _DIMS_PROFILE:
        errors.append(
            f"canvas {(height, width)} is outside canonical profiles "
            f"{sorted(_DIMS_PROFILE)}"
        )

    positions = _positions(grid)
    if len(positions) != 3:
        errors.append(f"expected exactly 3 nonzero colors, found {len(positions)}")

    parsed: list[dict[str, Any]] = []
    for color in sorted(positions):
        cells = positions[color]
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times; expected 2")
            continue
        try:
            orientation, span = _span(cells)
        except ValueError as exc:
            errors.append(f"color {color}: {exc}")
            continue
        if len(span) < 3:
            errors.append(
                f"color {color} markers are adjacent; expected at least one interior cell"
            )
        parsed.append(
            {
                "color": color,
                "markers": tuple(cells),
                "orientation": orientation,
                "span": span,
                "span_set": frozenset(span),
            }
        )

    if len(parsed) == 3:
        orientations = {item["orientation"] for item in parsed}
        if orientations != {"horizontal", "vertical"}:
            errors.append("scene must contain both horizontal and vertical pairs")
        for index, first in enumerate(parsed):
            for second in parsed[index + 1 :]:
                overlap = sorted(first["span_set"] & second["span_set"])
                if overlap:
                    errors.append(
                        f"segments for colors {first['color']} and {second['color']} "
                        f"overlap at {overlap}"
                    )

    if errors:
        return errors, None
    return [], {
        "height": height,
        "width": width,
        "scene_profile": _DIMS_PROFILE[(height, width)],
        "pairs": parsed,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return violations of the sampler's lawful, marker-preserving grammar."""
    del difficulty
    errors, scene = _analyze(grid)
    if errors:
        return errors
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = {
            name: value
            for name, value in meta["overrides"].items()
            if value is not None and name in AXES
        }
        observed = {"scene_profile": scene["scene_profile"]}
        for name, value in requested.items():
            if observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generator's whole declared manifold is canonical-like."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    """Recover the sole exact axis from returned pixels, not RNG metadata."""
    errors, scene = _analyze(grid)
    if errors:
        raise ValueError("cannot observe invalid scene: " + "; ".join(errors))
    return {"scene_profile": scene["scene_profile"]}


def _all_spans(height: int, width: int, orientation: str):
    candidates: list[tuple[tuple[tuple[int, int], tuple[int, int]], frozenset[tuple[int, int]]]] = []
    if orientation == "horizontal":
        for row in range(height):
            for start in range(width - 2):
                for end in range(start + 2, width):
                    cells = frozenset((row, column) for column in range(start, end + 1))
                    candidates.append((((row, start), (row, end)), cells))
    elif orientation == "vertical":
        for column in range(width):
            for start in range(height - 2):
                for end in range(start + 2, height):
                    cells = frozenset((row, column) for row in range(start, end + 1))
                    candidates.append((((start, column), (end, column)), cells))
    else:
        raise ValueError(f"unknown orientation {orientation!r}")
    return candidates


def _ordered_candidates(height: int, width: int, orientation: str, rng, difficulty):
    candidates = _all_spans(height, width, orientation)
    rng.shuffle(candidates)
    if difficulty == "easy":
        candidates.sort(key=lambda item: len(item[1]))
    elif difficulty == "hard":
        candidates.sort(key=lambda item: -len(item[1]))
    return candidates


def _choose_disjoint_spans(ctx, height: int, width: int, orientations, difficulty):
    rng = ctx.draw_rng("layout")
    # Fixed iteration order is part of replay determinism: using a set here
    # made the shared RNG consume the two shuffles in PYTHONHASHSEED order.
    choices = {
        orientation: _ordered_candidates(height, width, orientation, rng, difficulty)
        for orientation in ("horizontal", "vertical")
    }

    def search(index: int, occupied: frozenset[tuple[int, int]], chosen):
        if index == len(orientations):
            return tuple(chosen)
        orientation = orientations[index]
        for endpoints, cells in choices[orientation]:
            if occupied.isdisjoint(cells):
                result = search(index + 1, occupied | cells, (*chosen, (endpoints, cells)))
                if result is not None:
                    return result
        return None

    result = search(0, frozenset(), ())
    if result is None:
        raise RuntimeError(
            f"no three disjoint mixed-orientation spans fit in {(height, width)}"
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    profile_override = overrides.get("scene_profile")
    if profile_override is not None and type(profile_override) is not str:
        raise TypeError("scene_profile override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    height, width = _PROFILE_DIMS[profile]
    orientations = ctx.draw_choice("orientation_mix", _ORIENTATION_MIXES)
    spans = _choose_disjoint_spans(ctx, height, width, orientations, difficulty)
    colors = ctx.draw_distinct_colors("marker_colors", n=3, exclude=(0,))

    grid = full_grid(height, width, 0)
    for color, (endpoints, _cells) in zip(colors, spans):
        for row, column in endpoints:
            grid[row][column] = color
    return grid


def rule_mirror(grid):
    """Independent Python audit mirror of the selected Racket authority."""
    errors, scene = _analyze(grid)
    if errors:
        raise ValueError("invalid Connect Aligned Pairs input: " + "; ".join(errors))
    output = full_grid(scene["height"], scene["width"], 0)
    for pair in scene["pairs"]:
        for row, column in pair["span"]:
            output[row][column] = pair["color"]
    return output


def _paint_selected(grid, predicate: Callable[[dict[str, Any], int], bool]):
    errors, scene = _analyze(grid)
    if errors:
        return _copy_grid(grid)
    output = _copy_grid(grid)
    for index, pair in enumerate(scene["pairs"]):
        if predicate(pair, index):
            for row, column in pair["span"]:
                output[row][column] = pair["color"]
    return output


def _identity(grid):
    return _copy_grid(grid)


def _horizontal_only(grid):
    return _paint_selected(grid, lambda pair, _index: pair["orientation"] == "horizontal")


def _vertical_only(grid):
    return _paint_selected(grid, lambda pair, _index: pair["orientation"] == "vertical")


def _first_pair_only(grid):
    return _paint_selected(grid, lambda _pair, index: index == 0)


def _has_gap(grid) -> bool:
    errors, scene = _analyze(grid)
    return not errors and all(len(pair["span"]) >= 3 for pair in scene["pairs"])


def _has_mixed_orientations(grid) -> bool:
    errors, scene = _analyze(grid)
    return not errors and {
        pair["orientation"] for pair in scene["pairs"]
    } == {"horizontal", "vertical"}


def _has_multiple_pairs(grid) -> bool:
    errors, scene = _analyze(grid)
    return not errors and len(scene["pairs"]) >= 2


SEMANTIC_WITNESSES = {
    "gapped_pairs": _has_gap,
    "mixed_orientations": _has_mixed_orientations,
    "multiple_pairs": _has_multiple_pairs,
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "first_pair_only": _first_pair_only,
}
WITNESS_RIVALS = {
    "gapped_pairs": ["identity"],
    "mixed_orientations": ["horizontal_only", "vertical_only"],
    "multiple_pairs": ["first_pair_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable] = {}


def _pair_errors(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is malformed"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input is outside the declared grammar: {errors[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output disagrees with the selected-rule audit mirror"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a declared wrong rule survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstration"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    survivors = set(LESSON_COMPETITORS)
    for pair in demos:
        survivors &= {
            name
            for name, competitor in LESSON_COMPETITORS.items()
            if competitor(pair["input"]) == pair["output"]
        }
    for name in sorted(survivors):
        if LESSON_COMPETITORS[name](query["input"]) != query["output"]:
            errors.append(
                f"competitor {name!r} fits every demo but gives a different query answer"
            )
    return errors


def mutation_fixtures():
    """Near-misses covering the previous overlap defect and weak-validator cases."""
    valid = generate(991, 0, difficulty="medium", scene_profile="p8x10")
    missing_endpoint = _copy_grid(valid)
    row, column = next(
        (r, c)
        for r, values in enumerate(missing_endpoint)
        for c, value in enumerate(values)
        if value
    )
    missing_endpoint[row][column] = 0

    third_marker = _copy_grid(valid)
    positions = _positions(valid)
    color = min(positions)
    occupied = {point for cells in positions.values() for point in cells}
    extra = next(
        (r, c)
        for r in range(len(valid))
        for c in range(len(valid[0]))
        if (r, c) not in occupied
    )
    third_marker[extra[0]][extra[1]] = color

    overlapping = full_grid(8, 10, 0)
    overlapping[3][1] = overlapping[3][6] = 7
    overlapping[3][4] = overlapping[3][8] = 4
    overlapping[0][0] = overlapping[2][0] = 2

    all_horizontal = full_grid(8, 10, 0)
    for color, row, left, right in ((2, 1, 0, 3), (3, 3, 4, 8), (4, 6, 1, 5)):
        all_horizontal[row][left] = all_horizontal[row][right] = color

    return [
        ("missing_endpoint", missing_endpoint),
        ("third_marker", third_marker),
        ("overlapping_segments", overlapping),
        ("missing_vertical_orientation", all_horizontal),
    ]
