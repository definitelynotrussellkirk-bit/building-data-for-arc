"""Generator for ARC rule family 3738824c88c4 (source task 6cbe9eb8).

The answer-bearing unit is the complete periodic-noise scene: a linked set of
three or four colored rectangle components whose bounding boxes, fill/frame
states, and occlusions determine the nested output.  This generator preserves
one of the four complete published scene structures.  It varies only a global
D4 orientation and an injective color relabeling that keeps every extracted
rectangle color nonzero.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "3738824c88c4"
TASK_ID = "3738824c88c4"
VERSION = "3.0.0"
RULE_HASH = "fa86d6db81a7"

SUMMARY = (
    "Extract every same-color 4-connected component with a two-dimensional "
    "bounding box, sort those records by bounding-box area, and redraw them "
    "inside the largest rectangle from largest to smallest. Hollow or "
    "occluded records become frames, solid records stay solid, and each next "
    "record is bottom-left aligned within the preceding record."
)

INVARIANTS = [
    "the periodic noise contributes no two-dimensional qualifying component",
    "one complete linked published scene structure is preserved under color isomorphism",
    "every extracted rectangle color is nonzero and distinct from every noise color",
    "the three-or-four rectangle sequence fits recursively without clipping",
    "global D4 and injective color relabeling are the only generated nuisances",
]

SCENE_PROFILES = (
    "profile_14x22_4rect",
    "profile_13x23_4rect",
    "profile_16x23_3rect",
    "profile_19x27_4rect",
)
ORIENTATIONS = (
    "identity",
    "rot90",
    "rot180",
    "rot270",
    "mirror",
    "mirror_rot90",
    "mirror_rot180",
    "mirror_rot270",
)
PALETTE_MODES = ("canonical", "remapped")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked scene profile",
        "valid": (
            "profile_14x22_4rect|profile_13x23_4rect|"
            "profile_16x23_3rect|profile_19x27_4rect"
        ),
    },
    "orientation": {
        "type": "str",
        "default": "uniform global D4 transform",
        "valid": (
            "identity|rot90|rot180|rot270|mirror|mirror_rot90|"
            "mirror_rot180|mirror_rot270"
        ),
    },
    "palette_mode": {
        "type": "str",
        "default": "3% canonical and 97% injectively remapped",
        "valid": "canonical|remapped",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# Compact encodings of the four unique inputs across the linked training and
# augmented canonical rows.  Outputs are never embedded; rule_mirror derives
# them from the returned input.
_PROFILE_ROWS = {
    "profile_14x22_4rect": (
        "0123012301230123012301",
        "1888888888881230123012",
        "0823012301280123012301",
        "1830123044444440123012",
        "0823012345555543012301",
        "1830123045555540123012",
        "0823012345555543012301",
        "1830123045555540123012",
        "0823012344444443066301",
        "1830123012381230166012",
        "0823012301280123012301",
        "1830123012381230123012",
        "0888888888880123012301",
        "1230123012301230123012",
    ),
    "profile_13x23_4rect": (
        "01201201201201201441201",
        "12012012012012888442012",
        "12012012012012866682012",
        "01201333333333866681201",
        "12012312012012866682012",
        "12012312012012888882012",
        "01201301201201203201201",
        "12012312012012013012012",
        "12012312012012013012012",
        "01201301201201203201201",
        "12012312012012013012012",
        "12012333333333333012012",
        "01201201201201201201201",
    ),
    "profile_16x23_3rect": (
        "01010101010101010101010",
        "10333333331010101010101",
        "01388888830101010101010",
        "10388888831010101010101",
        "01388888830144410101010",
        "10388888831044401010101",
        "01388888830144410101010",
        "10388888831010101010101",
        "01333333330101010101010",
        "10101010101010101010101",
        "01010101010101010101010",
        "10101010101010101010101",
        "01010101010101010101010",
        "10101010101010101010101",
        "01010101010101010101010",
        "10101010101010101010101",
    ),
    "profile_19x27_4rect": (
        "233233233233233233233233233",
        "122122122122122122122122122",
        "311888888888888811311991311",
        "233833233233233833233993233",
        "122822122122122822122122122",
        "311811311311311811311311311",
        "233833233266666666633233233",
        "122822122162122822622122122",
        "311811311361344441611311311",
        "233833233263244443633233233",
        "122822122162144442622122122",
        "311811311361311811611311311",
        "233833233266666666633233233",
        "122822122122122822122122122",
        "311811311311311811311311311",
        "233833233233233833233233233",
        "122888888888888822122122122",
        "311311311311311311311311311",
        "233233233233233233233233233",
    ),
}

_OBJECT_COLORS = {
    "profile_14x22_4rect": frozenset({4, 5, 6, 8}),
    "profile_13x23_4rect": frozenset({3, 4, 6, 8}),
    "profile_16x23_3rect": frozenset({3, 4, 8}),
    "profile_19x27_4rect": frozenset({4, 6, 8, 9}),
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
}


def _profile_grid(profile):
    return [
        [int(value) for value in row]
        for row in _PROFILE_ROWS[profile]
    ]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


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


def _transform(grid, orientation):
    transformed = [list(row) for row in grid]
    if orientation.startswith("mirror"):
        transformed = [list(reversed(row)) for row in transformed]
    turns = {
        "identity": 0,
        "rot90": 1,
        "rot180": 2,
        "rot270": 3,
        "mirror": 0,
        "mirror_rot90": 1,
        "mirror_rot180": 2,
        "mirror_rot270": 3,
    }[orientation]
    for _turn in range(turns):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


@lru_cache(maxsize=None)
def _profile_variant(profile, orientation):
    return tuple(
        tuple(row)
        for row in _transform(_profile_grid(profile), orientation)
    )


def _color_isomorphism(template, candidate):
    if (
        len(template) != len(candidate)
        or len(template[0]) != len(candidate[0])
    ):
        return None
    forward = {}
    reverse = {}
    for template_row, candidate_row in zip(template, candidate):
        for source, target in zip(template_row, candidate_row):
            if source in forward and forward[source] != target:
                return None
            if target in reverse and reverse[target] != source:
                return None
            forward[source] = target
            reverse[target] = source
    return forward


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    matches = []
    for profile in SCENE_PROFILES:
        for orientation in ORIENTATIONS:
            template = _profile_variant(profile, orientation)
            mapping = _color_isomorphism(template, coerced)
            if mapping is None:
                continue
            if any(mapping[color] == 0 for color in _OBJECT_COLORS[profile]):
                continue
            matches.append((profile, orientation, mapping))
    if len(matches) != 1:
        return None
    profile, orientation, mapping = matches[0]
    palette_mode = (
        "canonical"
        if all(source == target for source, target in mapping.items())
        else "remapped"
    )
    return {
        "scene_profile": profile,
        "orientation": orientation,
        "palette_mode": palette_mode,
        "color_mapping": mapping,
    }


def canonical_profile_index(grid):
    """Return the complete linked public scene index, ignoring safe nuisances."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a returned valid grid."""
    signature = _semantic_signature(grid)
    if signature is None:
        return {}
    return {
        axis: signature[axis]
        for axis in ("scene_profile", "orientation", "palette_mode")
    }


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            ("profile_14x22_4rect",) * 26
            + ("profile_13x23_4rect",) * 34
            + ("profile_16x23_3rect",) * 17
            + ("profile_19x27_4rect",) * 23
        )
    if difficulty == "hard":
        return (
            ("profile_14x22_4rect",) * 29
            + ("profile_13x23_4rect",) * 29
            + ("profile_16x23_3rect",) * 12
            + ("profile_19x27_4rect",) * 30
        )
    return (
        ("profile_14x22_4rect",) * 28
        + ("profile_13x23_4rect",) * 29
        + ("profile_16x23_3rect",) * 15
        + ("profile_19x27_4rect",) * 28
    )


def _palette_options():
    return ("canonical",) * 3 + ("remapped",) * 97


def _permutation_count(available, length):
    result = 1
    for offset in range(length):
        result *= available - offset
    return result


def _unrank_permutation(values, length, index):
    options = list(values)
    result = []
    remainder = index % _permutation_count(len(options), length)
    for offset in range(length):
        block = _permutation_count(
            len(options) - 1,
            length - offset - 1,
        )
        choice = remainder // block if block else 0
        remainder = remainder % block if block else 0
        result.append(options.pop(choice))
    return result


def _palette_mapping(
    ctx,
    profile,
    palette_mode,
    seed,
    sample_index,
):
    values = sorted(
        {value for row in _PROFILE_ROWS[profile] for value in map(int, row)}
    )
    if palette_mode == "canonical":
        return {value: value for value in values}
    object_values = sorted(_OBJECT_COLORS[profile])
    noise_values = [
        value for value in values if value not in _OBJECT_COLORS[profile]
    ]
    object_state_count = _permutation_count(9, len(object_values))
    object_index = (
        2 * int(seed) + int(sample_index)
    ) % object_state_count
    object_targets = _unrank_permutation(
        range(1, 10),
        len(object_values),
        object_index,
    )
    remaining = [
        value for value in range(10) if value not in object_targets
    ]
    rng = ctx.draw_rng("noise_palette_assignment")
    noise_targets = rng.sample(remaining, len(noise_values))
    mapping = dict(zip(object_values, object_targets))
    mapping.update(zip(noise_values, noise_targets))
    if all(mapping[value] == value for value in values):
        first, second = object_values[:2]
        mapping[first], mapping[second] = mapping[second], mapping[first]
    return mapping


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    orientation = ctx.draw_choice("orientation", ORIENTATIONS)
    palette_mode = ctx.draw_choice("palette_mode", _palette_options())
    mapping = _palette_mapping(
        ctx,
        profile,
        palette_mode,
        seed,
        sample_index,
    )
    recolored = [
        [mapping[value] for value in row]
        for row in _profile_grid(profile)
    ]
    return _transform(recolored, orientation)


def _components_for_color(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            if (
                (start_row, start_col) in seen
                or grid[start_row][start_col] != color
            ):
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in (
                    (1, 0),
                    (-1, 0),
                    (0, 1),
                    (0, -1),
                ):
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(cells)
    return components


def _qualifying_records(grid):
    records = []
    colors = sorted({value for row in grid for value in row})
    for color in colors:
        for cells in _components_for_color(grid, color):
            if len(cells) < 2:
                continue
            cell_rows = [row for row, _col in cells]
            cell_cols = [col for _row, col in cells]
            height = max(cell_rows) - min(cell_rows) + 1
            width = max(cell_cols) - min(cell_cols) + 1
            if height < 2 or width < 2:
                continue
            records.append(
                {
                    "color": color,
                    "height": height,
                    "width": width,
                    "cells": len(cells),
                    "area": height * width,
                    "frame": len(cells) < height * width,
                }
            )
    return sorted(records, key=lambda record: -record["area"])


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket rule."""
    source, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    records = _qualifying_records(source)
    if not records:
        return [[0]]
    outer = records[0]
    output = [
        [0 for _col in range(outer["width"])]
        for _row in range(outer["height"])
    ]

    def paint(record, top, left):
        for row in range(record["height"]):
            for col in range(record["width"]):
                if record["frame"] and (
                    row not in (0, record["height"] - 1)
                    and col not in (0, record["width"] - 1)
                ):
                    continue
                target_row = top + row
                target_col = left + col
                if (
                    0 <= target_row < len(output)
                    and 0 <= target_col < len(output[0])
                ):
                    output[target_row][target_col] = record["color"]

    paint(outer, 0, 0)
    inner_top = 1 if outer["frame"] else 0
    inner_left = 1 if outer["frame"] else 0
    inner_height = outer["height"] - (2 if outer["frame"] else 0)
    inner_width = outer["width"] - (2 if outer["frame"] else 0)
    for record in records[1:]:
        top = inner_top + inner_height - record["height"]
        left = inner_left
        paint(record, top, left)
        inner_top = top + (1 if record["frame"] else 0)
        inner_left = left + (1 if record["frame"] else 0)
        inner_height = record["height"] - (2 if record["frame"] else 0)
        inner_width = record["width"] - (2 if record["frame"] else 0)
    return output


def self_check(grid, *, difficulty=None, meta=None):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    signature = _semantic_signature(coerced)
    if signature is None:
        return [
            "grid must be one complete published periodic-noise rectangle "
            "scene under global D4 and an injective color relabeling, with "
            "all extracted rectangle colors nonzero"
        ]
    output = rule_mirror(coerced)
    if output == coerced:
        return ["the canonical rule must perform a non-identity nesting"]
    return []
