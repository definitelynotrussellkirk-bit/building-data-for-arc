"""Generator for ARC rule family 9d488d6a3875 (bank task E137).

For each row and column independently, a color occurring exactly twice with
only background between the two cells is extended across that inclusive
span.  The calibrated training distribution contains two distinct-color,
noncrossing endpoint pairs on one of the five public canvases.  Exact public
span signatures remain a substantial prior; a bounded varied regime changes
only lawful nuisance geometry.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from itertools import combinations_with_replacement

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9d488d6a3875"
TASK_ID = "9d488d6a3875"
VERSION = "3.0.0"
RULE_HASH = "f60c7e85088e"

SUMMARY = (
    "On every row and column, fill the inclusive span between exactly two "
    "same-color cells when the original span contains only zero and that "
    "color; row fills happen before column fills."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the canvas matches one complete public scene profile",
    "zero is background and exactly two distinct nonzero colors are present",
    "each color has exactly two aligned endpoints at least four cells apart",
    "the two inclusive spans are clear and do not cross",
    "the output is recomputed by the broad row-then-column semantic rule",
]

SCENE_PROFILES = (
    "mixed_7x9_h6_v5",
    "horizontal_8x8_h4_h6",
    "vertical_9x9_v5_v7",
    "mixed_7x10_h9_v5",
    "mixed_8x10_h6_v6",
)
SPAN_REGIMES = ("canonical", "varied")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform complete public canvas/span family",
        "valid": (
            "mixed_7x9_h6_v5|horizontal_8x8_h4_h6|"
            "vertical_9x9_v5_v7|mixed_7x10_h9_v5|mixed_8x10_h6_v6"
        ),
    },
    "span_regime": {
        "type": "str",
        "default": "40% canonical, 60% bounded varied clear spans",
        "valid": "canonical|varied",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_PROFILE_DATA = {
    "mixed_7x9_h6_v5": {
        "canvas": (7, 9),
        "canonical": (("H", 6), ("V", 5)),
    },
    "horizontal_8x8_h4_h6": {
        "canvas": (8, 8),
        "canonical": (("H", 4), ("H", 6)),
    },
    "vertical_9x9_v5_v7": {
        "canvas": (9, 9),
        "canonical": (("V", 5), ("V", 7)),
    },
    "mixed_7x10_h9_v5": {
        "canvas": (7, 10),
        "canonical": (("H", 9), ("V", 5)),
    },
    "mixed_8x10_h6_v6": {
        "canvas": (8, 10),
        "canonical": (("H", 6), ("V", 6)),
    },
}

_PROFILE_BY_CANVAS = {
    data["canvas"]: profile
    for profile, data in _PROFILE_DATA.items()
}

_PROFILE_INDEX = {
    profile: index
    for index, profile in enumerate(SCENE_PROFILES)
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _grouped_cells(grid):
    grouped = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                grouped[value].append((row_index, col_index))
    return dict(grouped)


def _pair_record(grid, color, cells):
    if len(cells) != 2:
        return None
    (row_a, col_a), (row_b, col_b) = cells
    if row_a == row_b:
        start, end = sorted((col_a, col_b))
        span = tuple((row_a, col) for col in range(start, end + 1))
        orientation = "H"
    elif col_a == col_b:
        start, end = sorted((row_a, row_b))
        span = tuple((row, col_a) for row in range(start, end + 1))
        orientation = "V"
    else:
        return None
    if not all(
        grid[row][col] in (0, color)
        for row, col in span
    ):
        return None
    return {
        "color": color,
        "orientation": orientation,
        "length": len(span),
        "span": span,
        "endpoints": tuple(cells),
    }


def _descriptor_signature(records):
    return tuple(sorted(
        (record["orientation"], record["length"])
        for record in records
    ))


def _analyze_scene(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    height = len(coerced)
    width = len(coerced[0])
    profile = _PROFILE_BY_CANVAS.get((height, width))
    if profile is None:
        return None
    grouped = _grouped_cells(coerced)
    if len(grouped) != 2:
        return None
    records = []
    for color, cells in grouped.items():
        record = _pair_record(coerced, color, cells)
        if record is None or record["length"] < 4:
            return None
        records.append(record)
    if set(records[0]["span"]) & set(records[1]["span"]):
        return None
    signature = _descriptor_signature(records)
    regime = (
        "canonical"
        if signature == _PROFILE_DATA[profile]["canonical"]
        else "varied"
    )
    return {
        "scene_profile": profile,
        "span_regime": regime,
        "records": tuple(records),
        "signature": signature,
    }


def _semantic_signature(grid):
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    return {
        "scene_profile": analysis["scene_profile"],
        "span_regime": analysis["span_regime"],
    }


def canonical_profile_index(grid):
    """Return the complete public canvas/span-profile index."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid."""
    signature = _semantic_signature(grid)
    return {} if signature is None else dict(signature)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")
    if (
        "span_regime" in overrides
        and overrides["span_regime"] not in SPAN_REGIMES
    ):
        raise ValueError("unknown span_regime")


@lru_cache(maxsize=None)
def _candidate_spans(canvas, descriptor):
    height, width = canvas
    orientation, length = descriptor
    if orientation == "H":
        return tuple(
            tuple((row, col) for col in range(left, left + length))
            for row in range(height)
            for left in range(width - length + 1)
        )
    return tuple(
        tuple((row, col) for row in range(top, top + length))
        for col in range(width)
        for top in range(height - length + 1)
    )


@lru_cache(maxsize=None)
def _all_varied_signatures(profile):
    data = _PROFILE_DATA[profile]
    height, width = data["canvas"]
    descriptors = (
        tuple(("H", length) for length in range(4, width + 1))
        + tuple(("V", length) for length in range(4, height + 1))
    )
    signatures = []
    for first, second in combinations_with_replacement(descriptors, 2):
        signature = tuple(sorted((first, second)))
        if signature == data["canonical"]:
            continue
        if {
            first[0],
            second[0],
        } == {"H", "V"} and (
            ("H", width) in signature
            and ("V", height) in signature
        ):
            continue
        signatures.append(signature)
    return tuple(sorted(set(signatures)))


def _varied_signatures(profile, difficulty):
    signatures = _all_varied_signatures(profile)
    if difficulty is None:
        return signatures
    masses = [sum(length for _axis, length in item) for item in signatures]
    minimum = min(masses)
    maximum = max(masses)
    third = max(1, (maximum - minimum) // 3)
    if difficulty == "easy":
        selected = [
            item
            for item in signatures
            if sum(length for _axis, length in item) <= minimum + third
        ]
    elif difficulty == "hard":
        selected = [
            item
            for item in signatures
            if sum(length for _axis, length in item) >= maximum - third
        ]
    else:
        selected = [
            item
            for item in signatures
            if (
                minimum + third
                < sum(length for _axis, length in item)
                < maximum - third
            )
        ]
    return tuple(selected or signatures)


def _construct_scene(profile, signature, colors, rng):
    canvas = _PROFILE_DATA[profile]["canvas"]
    first_options = list(_candidate_spans(canvas, signature[0]))
    second_options = _candidate_spans(canvas, signature[1])
    rng.shuffle(first_options)
    selected = None
    for first in first_options:
        occupied = set(first)
        compatible = [
            second
            for second in second_options
            if occupied.isdisjoint(second)
        ]
        if compatible:
            selected = (first, rng.choice(compatible))
            break
    if selected is None:
        raise RuntimeError(
            f"no disjoint layout for {profile} signature {signature}"
        )
    height, width = canvas
    grid = [[0 for _col in range(width)] for _row in range(height)]
    for color, span in zip(colors, selected):
        for row, col in (span[0], span[-1]):
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", SCENE_PROFILES)
    regime = context.draw_choice(
        "span_regime",
        (
            "canonical",
            "canonical",
            "varied",
            "varied",
            "varied",
        ),
    )
    if regime == "canonical":
        signature = _PROFILE_DATA[profile]["canonical"]
    else:
        signature = context.draw_rng("span_signature").choice(
            _varied_signatures(profile, difficulty)
        )
    colors = context.draw_distinct_colors(
        "endpoint_colors",
        n=2,
        exclude={0},
    )
    grid = _construct_scene(
        profile,
        signature,
        colors,
        context.draw_rng("layout"),
    )
    expected = {
        "scene_profile": profile,
        "span_regime": regime,
    }
    if observe_overrides(grid) != expected:
        raise AssertionError("constructed scene lost its exact axes")
    return grid


def rule_mirror(grid):
    """Broad input-pure mirror of the canonical row-then-column rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in original]
    height = len(original)
    width = len(original[0])
    for row in range(height):
        colors = list(dict.fromkeys(
            value for value in original[row] if value
        ))
        for color in colors:
            columns = [
                col
                for col in range(width)
                if original[row][col] == color
            ]
            if len(columns) != 2:
                continue
            start, end = min(columns), max(columns)
            if all(
                original[row][col] in (0, color)
                for col in range(start, end + 1)
            ):
                for col in range(start, end + 1):
                    output[row][col] = color
    for col in range(width):
        colors = list(dict.fromkeys(
            original[row][col]
            for row in range(height)
            if original[row][col]
        ))
        for color in colors:
            rows = [
                row
                for row in range(height)
                if original[row][col] == color
            ]
            if len(rows) != 2:
                continue
            start, end = min(rows), max(rows)
            if all(
                original[row][col] in (0, color)
                for row in range(start, end + 1)
            ):
                for row in range(start, end + 1):
                    output[row][col] = color
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only complete calibrated two-pair public-canvas scenes."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _analyze_scene(coerced) is None:
        return [
            "grid must contain exactly two distinct clear, aligned, "
            "noncrossing endpoint pairs of length at least four on one "
            "complete public canvas profile"
        ]
    return []
