"""Semantic curriculum for the framed transform-transfer ARC task.

Each 6x20 input contains three 6x6 color-5 frames separated by blank
columns.  The 4x4 interior of panel B is one supported dihedral transform of
panel A.  The answer is the same transform applied to panel C's interior.

The public generator surface deliberately exposes one axis only:
``scene_profile``.  A ten-draw schedule redundantly places the two critical
disambiguation profiles, so every four-demo subset of any five consecutive
pairs still refutes the declared shortcuts when the query position rotates.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "85782e8a5dc9"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "8de2ee81f8fa"

SUMMARY = (
    "Three fixed 6x6 color-5 frames contain 4x4 motifs A, B, and C. "
    "Infer the unique supported dihedral transform mapping A to B, then "
    "apply it to C and emit the transformed 4x4 motif."
)
INVARIANTS = [
    "input is exactly 6x20 with three framed 4x4 interiors",
    "columns 6 and 13 are entirely blank separators",
    "A:B identifies exactly one supported non-identity transform",
    "the answer is that same transform applied to C",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCENE_PROFILES = (
    "quarter_turn",
    "half_turn_color_key",
    "axis_reflection",
    "diagonal_reflection",
)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_SCHEDULE = (
    "quarter_turn",
    "half_turn_color_key",
    "quarter_turn",
    "half_turn_color_key",
    "axis_reflection",
    "quarter_turn",
    "half_turn_color_key",
    "quarter_turn",
    "half_turn_color_key",
    "diagonal_reflection",
)
_REQUIRED_LESSON_PROFILES = frozenset(
    ("quarter_turn", "half_turn_color_key")
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-example semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

_HEIGHT = 6
_WIDTH = 20
_PANEL_STARTS = (0, 7, 14)
_INTERIOR_SIZE = 4
_SEPARATOR_COLUMNS = (6, 13)
_TRANSFORM_ORDER = (
    "identity",
    "rot90",
    "rot180",
    "transpose",
    "flip_lr",
    "flip_ud",
    "anti_transpose",
)
_GENERATED_TRANSFORMS = (
    "rot90",
    "rot180",
    "flip_lr",
    "flip_ud",
    "transpose",
    "anti_transpose",
)
_INVERSE_TRANSFORM = {
    "identity": "identity",
    "rot90": "rot270",
    "rot180": "rot180",
    "rot270": "rot90",
    "transpose": "transpose",
    "flip_lr": "flip_lr",
    "flip_ud": "flip_ud",
    "anti_transpose": "anti_transpose",
}
_CANONICAL_SIGNATURES = {(6, 20, 3), (6, 20, 4), (6, 20, 5)}
_COLOR_POOL = (1, 2, 3, 4, 6, 7, 8, 9)

# These two five-cell supports are in different D4 orbits and each has all
# eight distinct orientations.  Therefore C, T(C), A, and T(A) cannot collide
# merely because a one-color motif was selected.
_A_SUPPORT = ((0, 0), (0, 1), (1, 0), (2, 0), (2, 2))
_C_SUPPORT = ((0, 0), (0, 1), (1, 2), (2, 0), (3, 1))

# This support is invariant under a half turn but not under the other
# reflection families.  Its colors, rather than occupancy, identify rot180.
_HALF_TURN_SUPPORT = ((0, 0), (0, 1), (3, 2), (3, 3))


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _map_pattern(grid: Sequence[Sequence[int]], transform_name: str) -> list[list[int]]:
    """Apply one D4 operation without importing rule-primitive helpers."""
    source = _copy_grid(grid)
    size = len(source)
    if size == 0 or any(len(row) != size for row in source):
        raise ValueError("transform input must be a non-empty square grid")
    output = [[0 for _column in range(size)] for _row in range(size)]
    for row_index in range(size):
        for column_index in range(size):
            if transform_name == "identity":
                target = (row_index, column_index)
            elif transform_name == "rot90":
                target = (column_index, size - 1 - row_index)
            elif transform_name == "rot180":
                target = (size - 1 - row_index, size - 1 - column_index)
            elif transform_name == "rot270":
                target = (size - 1 - column_index, row_index)
            elif transform_name == "transpose":
                target = (column_index, row_index)
            elif transform_name == "flip_lr":
                target = (row_index, size - 1 - column_index)
            elif transform_name == "flip_ud":
                target = (size - 1 - row_index, column_index)
            elif transform_name == "anti_transpose":
                target = (size - 1 - column_index, size - 1 - row_index)
            else:
                raise ValueError(f"unknown transform: {transform_name!r}")
            output[target[0]][target[1]] = source[row_index][column_index]
    return output


def _transform_points(
    points: Sequence[tuple[int, int]], transform_name: str
) -> tuple[tuple[int, int], ...]:
    marker = [[0 for _column in range(_INTERIOR_SIZE)] for _row in range(_INTERIOR_SIZE)]
    for index, (row_index, column_index) in enumerate(points, start=1):
        marker[row_index][column_index] = index
    moved = _map_pattern(marker, transform_name)
    locations: dict[int, tuple[int, int]] = {}
    for row_index, row in enumerate(moved):
        for column_index, value in enumerate(row):
            if value:
                locations[value] = (row_index, column_index)
    return tuple(locations[index] for index in range(1, len(points) + 1))


def _mask(pattern: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in pattern]


def _palette_signature(grid: Sequence[Sequence[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    return str(difficulty)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Redundantly schedule the two profiles required by every rotated lesson."""
    del seed
    _band(difficulty)
    return _PROFILE_SCHEDULE[int(sample_index) % len(_PROFILE_SCHEDULE)]


def _select_transform(profile: str, seed: int, sample_index: int, band: str) -> str:
    phase = (int(seed) + int(sample_index) + {"easy": 0, "medium": 1, "hard": 2}[band]) % 2
    if profile == "quarter_turn":
        return "rot90"
    if profile == "half_turn_color_key":
        return "rot180"
    if profile == "axis_reflection":
        return ("flip_lr", "flip_ud")[phase]
    if profile == "diagonal_reflection":
        return ("transpose", "anti_transpose")[phase]
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _palette_size(profile: str, band: str) -> int:
    size = {"easy": 1, "medium": 2, "hard": 3}[band]
    if profile == "half_turn_color_key":
        return max(2, size)
    return size


def _colored_pattern(
    points: Sequence[tuple[int, int]], colors: Sequence[int]
) -> list[list[int]]:
    pattern = [[0 for _column in range(_INTERIOR_SIZE)] for _row in range(_INTERIOR_SIZE)]
    for index, (row_index, column_index) in enumerate(points):
        pattern[row_index][column_index] = colors[index % len(colors)]
    return pattern


def _render(a_pattern, b_pattern, c_pattern) -> list[list[int]]:
    grid = [[0 for _column in range(_WIDTH)] for _row in range(_HEIGHT)]
    for panel_index, pattern in enumerate((a_pattern, b_pattern, c_pattern)):
        start = _PANEL_STARTS[panel_index]
        stop = start + 5
        for column_index in range(start, stop + 1):
            grid[0][column_index] = 5
            grid[5][column_index] = 5
        for row_index in range(_HEIGHT):
            grid[row_index][start] = 5
            grid[row_index][stop] = 5
        for row_index in range(_INTERIOR_SIZE):
            for column_index in range(_INTERIOR_SIZE):
                grid[row_index + 1][start + column_index + 1] = pattern[row_index][column_index]
    return grid


def _extract_interiors(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], ...]:
    return tuple(
        [list(row[start + 1 : start + 5]) for row in grid[1:5]]
        for start in _PANEL_STARTS
    )


def _validate_grid(grid: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)):
        return ["grid must be a row sequence"]
    if len(grid) != _HEIGHT:
        return [f"grid must have exactly {_HEIGHT} rows"]
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)):
            errors.append(f"row {row_index} must be a sequence")
            continue
        if len(row) != _WIDTH:
            errors.append(f"row {row_index} must have exactly {_WIDTH} cells")
            continue
        for column_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(
                    f"cell ({row_index},{column_index}) must be a non-boolean integer"
                )
            elif not 0 <= value <= 9:
                errors.append(f"cell ({row_index},{column_index}) is outside color range 0..9")
    return errors


def _frame_errors(grid: Sequence[Sequence[int]]) -> list[str]:
    errors: list[str] = []
    for separator in _SEPARATOR_COLUMNS:
        if any(grid[row_index][separator] != 0 for row_index in range(_HEIGHT)):
            errors.append(f"separator column {separator} must be all zero")
    for panel_index, start in enumerate(_PANEL_STARTS):
        stop = start + 5
        if any(grid[0][column_index] != 5 for column_index in range(start, stop + 1)):
            errors.append(f"panel {panel_index} top frame must be color 5")
        if any(grid[5][column_index] != 5 for column_index in range(start, stop + 1)):
            errors.append(f"panel {panel_index} bottom frame must be color 5")
        if any(grid[row_index][start] != 5 for row_index in range(_HEIGHT)):
            errors.append(f"panel {panel_index} left frame must be color 5")
        if any(grid[row_index][stop] != 5 for row_index in range(_HEIGHT)):
            errors.append(f"panel {panel_index} right frame must be color 5")
    return errors


def _matching_transforms(a_pattern, b_pattern, *, occupancy_only: bool = False) -> list[str]:
    source = _mask(a_pattern) if occupancy_only else _copy_grid(a_pattern)
    target = _mask(b_pattern) if occupancy_only else _copy_grid(b_pattern)
    return [
        name for name in _TRANSFORM_ORDER if _map_pattern(source, name) == target
    ]


def analyze_grid(grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if not errors:
        errors.extend(_frame_errors(grid))
    if errors:
        raise ValueError(errors[0])
    a_pattern, b_pattern, c_pattern = _extract_interiors(grid)
    matches = _matching_transforms(a_pattern, b_pattern)
    transform_name = matches[0] if len(matches) == 1 else None
    answer = (
        _map_pattern(c_pattern, transform_name)
        if transform_name is not None
        else None
    )
    return {
        "a": a_pattern,
        "b": b_pattern,
        "c": c_pattern,
        "a_mask": _mask(a_pattern),
        "b_mask": _mask(b_pattern),
        "c_mask": _mask(c_pattern),
        "matching_transforms": matches,
        "transform": transform_name,
        "answer": answer,
        "signature": _palette_signature(grid),
    }


def _profile_from_analysis(analysis: dict[str, Any]) -> str | None:
    transform_name = analysis.get("transform")
    if transform_name == "rot90":
        return "quarter_turn"
    if transform_name == "rot180":
        return "half_turn_color_key"
    if transform_name in ("flip_lr", "flip_ud"):
        return "axis_reflection"
    if transform_name in ("transpose", "anti_transpose"):
        return "diagonal_reflection"
    return None


def observe_overrides(grid) -> dict[str, str | None]:
    try:
        analysis = analyze_grid(grid)
    except (TypeError, ValueError, IndexError):
        return {"scene_profile": None}
    return {"scene_profile": _profile_from_analysis(analysis)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostics for malformed, off-manifold, or ambiguous inputs."""
    del meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    errors.extend(_frame_errors(grid))
    if errors:
        return errors

    if difficulty is not None:
        try:
            _band(difficulty)
        except ValueError as exc:
            errors.append(str(exc))

    signature = _palette_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        errors.append(
            f"shape/palette signature {signature} is outside canonical signatures "
            f"{sorted(_CANONICAL_SIGNATURES)}"
        )

    palette = {value for row in grid for value in row}
    if 0 not in palette or 5 not in palette:
        errors.append("grid must contain background 0 and frame color 5")

    a_pattern, b_pattern, c_pattern = _extract_interiors(grid)
    if not any(value != 0 for row in a_pattern for value in row):
        errors.append("panel A interior must contain a motif")
    if not any(value != 0 for row in c_pattern for value in row):
        errors.append("panel C interior must contain a motif")

    matches = _matching_transforms(a_pattern, b_pattern)
    if len(matches) != 1:
        errors.append(
            "A:B must identify exactly one supported transform; "
            f"observed {matches}"
        )
        return errors
    transform_name = matches[0]
    if transform_name == "identity":
        errors.append("ordinary examples must use a non-identity transform")
        return errors
    if transform_name not in _GENERATED_TRANSFORMS:
        errors.append(f"unsupported transform: {transform_name}")
        return errors

    answer = _map_pattern(c_pattern, transform_name)
    if answer == c_pattern:
        errors.append("panel C must visibly change under the inferred transform")
    if answer in (a_pattern, b_pattern):
        errors.append("answer must transfer the rule to a distinct C motif")
    if {
        value for row in answer for value in row if value != 0
    } != {
        value for row in c_pattern for value in row if value != 0
    }:
        errors.append("transform must preserve C's nonzero color palette")
    if _profile_from_analysis(
        {
            "transform": transform_name,
            "a_mask": _mask(a_pattern),
            "b_mask": _mask(b_pattern),
        }
    ) is None:
        errors.append("input does not match a declared scene profile")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Input-pure Python diagnostic mirror of the selected Racket rule."""
    analysis = analyze_grid(grid)
    transform_name = analysis["transform"]
    if transform_name is None:
        raise ValueError(
            "A:B does not identify exactly one supported transform: "
            f"{analysis['matching_transforms']}"
        )
    return _map_pattern(analysis["c"], transform_name)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)

    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    transform_name = _select_transform(profile, seed, sample_index, band)
    palette_size = _palette_size(profile, band)
    colors = ctx.draw_distinct_colors(
        "motif_colors", n=palette_size, exclude=(0, 5)
    )
    layout_rng = ctx.draw_rng(f"layout_{profile}_{band}")
    orientations = tuple(_TRANSFORM_ORDER) + ("rot270",)
    a_orientation = layout_rng.choice(orientations)
    c_orientation = layout_rng.choice(orientations)

    if profile == "half_turn_color_key":
        a_points = _transform_points(_HALF_TURN_SUPPORT, a_orientation)
    else:
        a_points = _transform_points(_A_SUPPORT, a_orientation)
    c_points = _transform_points(_C_SUPPORT, c_orientation)

    # Rotate the palette order independently of support orientation.  Every
    # selected color is realized in C, so palette size is an observable fact.
    color_order = list(colors)
    layout_rng.shuffle(color_order)
    a_pattern = _colored_pattern(a_points, color_order)
    c_pattern = _colored_pattern(c_points, tuple(reversed(color_order)))
    b_pattern = _map_pattern(a_pattern, transform_name)
    grid = _render(a_pattern, b_pattern, c_pattern)

    observed = observe_overrides(grid)["scene_profile"]
    if observed != profile:
        raise RuntimeError(
            f"rendered profile {profile!r} is not observable; observed {observed!r}"
        )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError(f"generated invalid scene: {errors}")
    return grid


def _rival_return_c(grid):
    return analyze_grid(grid)["c"]


def _rival_return_b(grid):
    return analyze_grid(grid)["b"]


def _rival_always_quarter_turn(grid):
    return _map_pattern(analyze_grid(grid)["c"], "rot90")


def _rival_apply_inverse(grid):
    analysis = analyze_grid(grid)
    transform_name = analysis["transform"]
    if transform_name is None:
        raise ValueError("cannot infer transform")
    return _map_pattern(analysis["c"], _INVERSE_TRANSFORM[transform_name])


def _rival_occupancy_only(grid):
    analysis = analyze_grid(grid)
    matches = _matching_transforms(
        analysis["a"], analysis["b"], occupancy_only=True
    )
    selected = matches[0] if matches else "identity"
    return _map_pattern(analysis["c"], selected)


def _rival_collapse_colors(grid):
    answer = rule_mirror(grid)
    colors = sorted({value for row in answer for value in row if value != 0})
    if not colors:
        return answer
    replacement = colors[0]
    return [
        [replacement if value != 0 else 0 for value in row]
        for row in answer
    ]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "return_c_unchanged": _rival_return_c,
    "return_visible_b": _rival_return_b,
    "always_rotate_90": _rival_always_quarter_turn,
    "apply_inverse_transform": _rival_apply_inverse,
    "infer_transform_from_occupancy_only": _rival_occupancy_only,
    "collapse_transformed_colors": _rival_collapse_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "infer_transform_from_occupancy_only": _rival_occupancy_only,
}


def _analysis_or_none(grid):
    try:
        return analyze_grid(grid)
    except (TypeError, ValueError, IndexError):
        return None


def _has_profile(grid, profile: str) -> bool:
    analysis = _analysis_or_none(grid)
    return bool(analysis and _profile_from_analysis(analysis) == profile)


def _is_transfer_witness(grid) -> bool:
    analysis = _analysis_or_none(grid)
    return bool(
        analysis
        and analysis["answer"] is not None
        and analysis["answer"] not in (analysis["b"], analysis["c"])
    )


def _is_multicolor_witness(grid) -> bool:
    analysis = _analysis_or_none(grid)
    return bool(
        analysis
        and len(
            {
                value
                for row in analysis["c"]
                for value in row
                if value != 0
            }
        )
        >= 2
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "quarter_turn_present": lambda grid: _has_profile(grid, "quarter_turn"),
    "half_turn_requires_color_correspondence": lambda grid: (
        _has_profile(grid, "half_turn_color_key")
        and analyze_grid(grid)["a_mask"] == analyze_grid(grid)["b_mask"]
        and analyze_grid(grid)["a"] != analyze_grid(grid)["b"]
    ),
    "axis_reflection_present": lambda grid: _has_profile(grid, "axis_reflection"),
    "diagonal_reflection_present": lambda grid: _has_profile(
        grid, "diagonal_reflection"
    ),
    "rule_transfers_to_c": _is_transfer_witness,
    "multiple_c_colors_are_preserved": _is_multicolor_witness,
}
BRANCH_WITNESSES = (
    "quarter_turn_present",
    "half_turn_requires_color_correspondence",
    "axis_reflection_present",
    "diagonal_reflection_present",
)
WITNESS_RIVALS = {
    "quarter_turn_present": ["apply_inverse_transform"],
    "half_turn_requires_color_correspondence": [
        "infer_transform_from_occupancy_only"
    ],
    "axis_reflection_present": ["always_rotate_90"],
    "diagonal_reflection_present": ["always_rotate_90"],
    "rule_transfers_to_c": ["return_c_unchanged", "return_visible_b"],
    "multiple_c_colors_are_preserved": ["collapse_transformed_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require critical profiles and a direct counterexample to every rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    profiles: set[str] = set()
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        grid = pair["input"]
        check = self_check(grid)
        if check:
            reasons.append(f"pair {index} is outside the lawful grammar: {check[0]}")
            continue
        if rule_mirror(grid) != pair["output"]:
            reasons.append(f"pair {index} disagrees with the selected transfer rule")
        if index < len(demos):
            observed = observe_overrides(grid)["scene_profile"]
            if observed is not None:
                profiles.add(observed)

    if reasons:
        return reasons
    missing = sorted(_REQUIRED_LESSON_PROFILES - profiles)
    if missing:
        reasons.append(
            f"demonstrations are missing critical teaching profiles: {missing}"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
