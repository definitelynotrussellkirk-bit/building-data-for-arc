"""Semantic generator for ARC task ``32a376372541``.

The selected rule copies every non-zero LEFT-half cell to its horizontal
mirror across the vertical midline while preserving the source.  Canonical
inputs leave the right half empty.  The curriculum also schedules a small,
non-colliding right-half decoy on alternating profiles; the selected Racket
rule preserves that decoy and never copies it back to the left.  This makes
the one-way direction observable instead of teaching a bidirectional-mirror
shortcut that is answer-equivalent on every canonical pair.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "32a376372541"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8022db4c5a5f"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Copy every non-zero cell in the left half to the horizontally mirrored "
    "cell in the right half, preserving the left source. Alternating teaching "
    "profiles add one unrelated right-half decoy on a non-target cell; that "
    "decoy is preserved and is not mirrored back left, exposing that the rule "
    "is one-directional."
)

INVARIANTS = [
    "background is 0 and grid width is even, so the vertical midline lies between two columns",
    "the left half contains a sparse multicolor source spanning multiple rows and mirror distances",
    "every left source cell has an initially empty horizontally mirrored destination",
    "ordinary profiles contain either zero or one non-colliding right-half decoy",
    "right-half decoys are preserved by the oracle and are never copied back into the left half",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Profiles are deliberately finite and grid-observable.  Slots 0/2 are
# canonical-clean and slots 1/3 contain a one-way decoy.  Therefore every
# consecutive EXAMPLES_NEEDED=2 demonstration window contains a decoy witness
# while also remaining anchored to the canonical empty-right-half grammar.
_PROFILE_ROWS = (
    # name, band, h, half_w, left_cells, left_palette, right_decoys
    ("e6x8_c4_p4_clean", "easy", 6, 4, 4, 4, 0),
    ("e6x8_c6_p4_decoy", "easy", 6, 4, 6, 4, 1),
    ("e7x8_c6_p5_clean", "easy", 7, 4, 6, 5, 0),
    ("e7x10_c7_p4_decoy", "easy", 7, 5, 7, 4, 1),
    ("m7x10_c5_p5_clean", "medium", 7, 5, 5, 5, 0),
    ("m7x10_c6_p5_decoy", "medium", 7, 5, 6, 5, 1),
    ("m8x10_c7_p4_clean", "medium", 8, 5, 7, 4, 0),
    ("m8x12_c8_p5_decoy", "medium", 8, 6, 8, 5, 1),
    ("h8x12_c4_p4_clean", "hard", 8, 6, 4, 4, 0),
    ("h8x12_c7_p5_decoy", "hard", 8, 6, 7, 5, 1),
    ("h9x12_c8_p4_clean", "hard", 9, 6, 8, 4, 0),
    ("h9x10_c7_p5_decoy", "hard", 9, 5, 7, 5, 1),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {
    (row[2], row[3], row[4], row[5], row[6]): row[0] for row in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-slot curriculum for the selected difficulty band",
        "valid": "e6x8_c4_p4_clean|e6x8_c6_p4_decoy|e7x8_c6_p5_clean|e7x10_c7_p4_decoy|m7x10_c5_p5_clean|m7x10_c6_p5_decoy|m8x10_c7_p4_clean|m8x12_c8_p5_decoy|h8x12_c4_p4_clean|h8x12_c7_p5_decoy|h9x12_c8_p4_clean|h9x10_c7_p5_decoy",
    }
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 16 or not 4 <= width <= 18:
        return [f"grid dimensions must be within 3..16 by 4..18, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if width % 2:
        return {
            "errors": [f"width {width} is odd; the task requires equal left/right halves"],
            "height": height,
            "width": width,
        }
    half = width // 2
    left = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(half)
        if grid[r][c] != 0
    ]
    right = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(half, width)
        if grid[r][c] != 0
    ]
    if len(left) < 3:
        errors.append(f"left half needs at least three source cells, found {len(left)}")
    left_rows = {r for r, _c, _v in left}
    left_cols = {c for _r, c, _v in left}
    if left and len(left_rows) < 3:
        errors.append("left source must span at least three rows")
    if left and len(left_cols) < 3:
        errors.append("left source must span at least three columns")

    collisions = [
        (r, c)
        for r, c, _value in right
        if grid[r][width - 1 - c] != 0
    ]
    if collisions:
        errors.append(
            f"right half pre-fills {len(collisions)} mirror destination(s); teaching inputs keep targets empty"
        )
    if len(right) > 2:
        errors.append(f"at most two non-colliding right decoys are allowed, found {len(right)}")

    source_colors = {value for _r, _c, value in left}
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "half_w": half,
        "left": left,
        "right_decoys": right,
        "left_rows": left_rows,
        "left_cols": left_cols,
        "source_colors": source_colors,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the task grammar and reject malformed/rule-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared profile directly from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    signature = (
        analysis["height"],
        analysis["half_w"],
        len(analysis["left"]),
        len(analysis["source_colors"]),
        len(analysis["right_decoys"]),
    )
    return {"scene_profile": _PROFILE_BY_SIGNATURE.get(signature)}


def _witness_multiple_mirror_distances(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    half = analysis["half_w"]
    cols = analysis["left_cols"]
    return 0 in cols and half - 1 in cols and len(cols) >= 3


def _witness_multiple_source_rows(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["left_rows"]) >= 3


def _witness_multicolor_source(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["source_colors"]) >= 4


def _witness_one_way_decoy(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["right_decoys"]) == 1


def strict_canonical_like(grid) -> list[str]:
    """Strict task-linked teaching predicate used by the semantic census."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = observe_overrides(grid).get("scene_profile")
    if profile is None:
        reasons.append("scene is outside the declared observable curriculum profiles")
    if not _witness_multiple_mirror_distances(grid):
        reasons.append("source must span outer, inner, and a third mirror distance")
    if not _witness_multiple_source_rows(grid):
        reasons.append("source must span at least three rows")
    if not _witness_multicolor_source(grid):
        reasons.append("source must contain at least four distinct colors")
    return reasons


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid mirror scene: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    width = analysis["width"]
    for row, col, value in analysis["left"]:
        output[row][width - 1 - col] = value
    return output


def _rival_bidirectional_mirror(grid):
    """Wrong shortcut: mirror every nonzero from either half into the other."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    original = [list(row) for row in grid]
    output = [list(row) for row in grid]
    width = analysis["width"]
    for row in range(analysis["height"]):
        for col in range(width):
            value = original[row][col]
            if value != 0:
                output[row][width - 1 - col] = value
    return output


def _rival_translate_left_half(grid):
    """Wrong shortcut: copy the left half rightward without reversing columns."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    half = analysis["half_w"]
    for row, col, value in analysis["left"]:
        output[row][col + half] = value
    return output


def _rival_move_instead_of_copy(grid):
    """Wrong shortcut: move source cells to their mirrors instead of copying."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    width = analysis["width"]
    for row, col, value in analysis["left"]:
        output[row][col] = 0
        output[row][width - 1 - col] = value
    return output


def _rival_copy_first_color_only(grid):
    """Wrong shortcut: mirror only the first source color encountered."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    output = [list(row) for row in grid]
    first_color = analysis["left"][0][2]
    width = analysis["width"]
    for row, col, value in analysis["left"]:
        if value == first_color:
            output[row][width - 1 - col] = value
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "bidirectional_mirror": _rival_bidirectional_mirror,
    "translate_left_half_without_reversal": _rival_translate_left_half,
    "move_instead_of_copy": _rival_move_instead_of_copy,
    "copy_first_color_only": _rival_copy_first_color_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "one_way_right_decoy": _witness_one_way_decoy,
    "multiple_mirror_distances": _witness_multiple_mirror_distances,
    "multiple_source_rows": _witness_multiple_source_rows,
    "multicolor_source": _witness_multicolor_source,
}
WITNESS_RIVALS = {
    "one_way_right_decoy": ["bidirectional_mirror"],
    "multiple_mirror_distances": ["translate_left_half_without_reversal"],
    "multiple_source_rows": ["move_instead_of_copy"],
    "multicolor_source": ["copy_first_color_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the left-to-right mirror-copy rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the left-to-right mirror-copy rule")
    if not any(_witness_one_way_decoy(pair["input"]) for pair in demos):
        reasons.append("demonstrations need a right-side decoy to falsify bidirectional mirroring")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _source_cells(height: int, half: int, count: int, rng) -> list[tuple[int, int]]:
    """Draw sparse sources with guaranteed row/column and reflection witnesses."""
    far_row = rng.randrange(height)
    near_row = rng.randrange(height - 1)
    if near_row >= far_row:
        near_row += 1
    remaining_rows = [row for row in range(height) if row not in (far_row, near_row)]
    interior_row = rng.choice(remaining_rows)
    interior_col = rng.choice(list(range(1, half - 1)))
    chosen = [(far_row, 0), (near_row, half - 1), (interior_row, interior_col)]
    used = set(chosen)
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(half)
        if (row, col) not in used
    ]
    rng.shuffle(candidates)
    chosen.extend(candidates[: count - len(chosen)])
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    _profile_band, height, half, left_count, palette_size, right_decoys = _PROFILE_BY_NAME[profile]
    width = half * 2
    placement_rng = ctx.draw_rng("source-placement")
    palette_rng = ctx.draw_rng("source-palette")
    decoy_rng = ctx.draw_rng("right-decoy")

    grid = full_grid(height, width, 0)
    source_cells = _source_cells(height, half, left_count, placement_rng)
    palette = palette_rng.sample(list(range(1, 10)), palette_size)
    colors = list(palette)
    colors.extend(palette_rng.choice(palette) for _ in range(left_count - palette_size))
    palette_rng.shuffle(colors)
    for (row, col), color in zip(source_cells, colors):
        grid[row][col] = color

    if right_decoys:
        source_set = set(source_cells)
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(half, width)
            if (row, width - 1 - col) not in source_set
        ]
        if not candidates:
            raise ValueError("profile leaves no non-colliding right-decoy position")
        row, col = decoy_rng.choice(candidates)
        grid[row][col] = decoy_rng.choice(palette)

    return grid
