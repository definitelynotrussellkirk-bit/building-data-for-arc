"""Generator for 8a82ec149798 — mirror left sources across a gray axis.

The selected Racket rule reconstructs a clean output from three ingredients:
all gray (5) cells, every non-{0,5} source left of the first full gray column,
and the horizontal reflection of each source across that column.  Consequently
right-side input marks are distractors: unrelated marks disappear and marks on
mirror targets are overwritten by the reflected source color.

This generator exposes only controls that are exactly observable in the input.
A five-profile rotating curriculum always includes clean/noisy, centered/
off-center, single-/multi-color evidence so a lesson can falsify the main
shortcut rules instead of merely exercising the reference program.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from hashlib import blake2s
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a82ec149798"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "40243de2441c"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.30

SUMMARY = (
    "A 6-8 by 9-11 zero-background grid has one full gray (5) vertical axis, "
    "2-7 colored source cells on its mirrorable left side, and optional "
    "right-side distractors. Rebuild a clean grid: preserve the gray axis and "
    "left sources, reflect every source across the gray column, erase unrelated "
    "right marks, and overwrite occupied mirror targets with the source color."
)

INVARIANTS = [
    "integer ARC grid, 6..8 rows by 9..11 columns",
    "exactly one full color-5 column and no other color-5 cells",
    "2..7 non-{0,5} source cells lie left of the axis and have in-bounds mirrors",
    "source cells use exactly 1 or 2 colors",
    "right-side distractors are absent or form one explicit two-cell control",
    "the output is reconstructed from the axis and left sources, not copied from the right input",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXIS_PROFILES = ("centered", "left_offset", "right_offset")
DISTRACTOR_MODES = ("none", "erase", "overwrite", "mixed")
SOURCE_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile schedule",
        "valid": "6..8",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile schedule",
        "valid": "9..11",
    },
    "n_sources": {
        "type": "int",
        "default": "profile-keyed 4..7",
        "valid": "2..7",
    },
    "n_source_colors": {
        "type": "int",
        "default": "one canonical color or two-color counterexample",
        "valid": "1..2",
    },
    "axis_profile": {
        "type": "str",
        "default": "centered|left_offset|right_offset schedule",
        "valid": "|".join(AXIS_PROFILES),
    },
    "distractor_mode": {
        "type": "str",
        "default": "none|erase|overwrite|mixed schedule",
        "valid": "|".join(DISTRACTOR_MODES),
    },
}

# Every boundary and cross-product used by the override checker is realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PROFILE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "name": "canonical_erase_noise",
        "grid_h": 7,
        "grid_w": 9,
        "n_sources": 5,
        "n_source_colors": 1,
        "axis_profile": "centered",
        "distractor_mode": "erase",
    },
    {
        "name": "left_offset_clean",
        "grid_h": 6,
        "grid_w": 11,
        "n_sources": 6,
        "n_source_colors": 1,
        "axis_profile": "left_offset",
        "distractor_mode": "none",
    },
    {
        "name": "overwrite_targets",
        "grid_h": 8,
        "grid_w": 9,
        "n_sources": 7,
        "n_source_colors": 1,
        "axis_profile": "centered",
        "distractor_mode": "overwrite",
    },
    {
        "name": "canonical_clean",
        "grid_h": 7,
        "grid_w": 11,
        "n_sources": 6,
        "n_source_colors": 1,
        "axis_profile": "centered",
        "distractor_mode": "none",
    },
    {
        "name": "right_offset_multicolor_mixed",
        "grid_h": 8,
        "grid_w": 11,
        "n_sources": 4,
        "n_source_colors": 2,
        "axis_profile": "right_offset",
        "distractor_mode": "mixed",
    },
)
SCHEDULE_PROFILES = tuple(row["name"] for row in _PROFILE_ROWS)
_PROFILE_BY_NAME = {row["name"]: row for row in _PROFILE_ROWS}


def _seed_phase(seed: int) -> int:
    digest = blake2s(str(int(seed)).encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Return the curriculum slot; every five consecutive indices cover all."""
    del difficulty
    offset = (_seed_phase(int(seed)) + int(sample_index)) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[offset]


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            type(value) is int and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _axis_for(width: int, profile: str) -> int:
    center = (width - 1) // 2
    return {
        "centered": center,
        "left_offset": center - 1,
        "right_offset": center + 1,
    }[profile]


def _axis_profile(width: int, axis: int) -> str | None:
    for profile in AXIS_PROFILES:
        if _axis_for(width, profile) == axis:
            return profile
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "axis": None,
        "axis_profile": None,
        "sources": [],
        "source_colors": set(),
        "right_distractors": [],
        "overlap_distractors": [],
        "erase_distractors": [],
        "distractor_mode": None,
        "output": None,
    }
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    facts["height"], facts["width"] = h, w
    if not 6 <= h <= 8:
        errors.append(f"grid height must be 6..8, got {h}")
    if not 9 <= w <= 11:
        errors.append(f"grid width must be 9..11, got {w}")
    if errors:
        return facts

    full_gray = [
        col
        for col in range(w)
        if all(grid[row][col] == 5 for row in range(h))
    ]
    if len(full_gray) != 1:
        errors.append(f"expected exactly one full gray column, got {full_gray}")
        return facts
    axis = full_gray[0]
    facts["axis"] = axis
    profile = _axis_profile(w, axis)
    facts["axis_profile"] = profile
    if profile is None:
        errors.append(
            f"gray axis column {axis} is not centered or one column offset for width {w}"
        )

    extra_gray = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if col != axis and grid[row][col] == 5
    ]
    if extra_gray:
        errors.append(f"gray 5 is reserved for the axis; extra cells include {extra_gray[:3]}")

    sources = [
        (row, col, grid[row][col])
        for row in range(h)
        for col in range(axis)
        if grid[row][col] not in (0, 5)
    ]
    right = [
        (row, col, grid[row][col])
        for row in range(h)
        for col in range(axis + 1, w)
        if grid[row][col] not in (0, 5)
    ]
    facts["sources"] = sources
    facts["right_distractors"] = right
    source_colors = {color for _row, _col, color in sources}
    facts["source_colors"] = source_colors

    if not 2 <= len(sources) <= 7:
        errors.append(f"expected 2..7 left source cells, got {len(sources)}")
    if not 1 <= len(source_colors) <= 2:
        errors.append(f"expected 1..2 left source colors, got {sorted(source_colors)}")

    target_colors: dict[tuple[int, int], int] = {}
    for row, col, color in sources:
        mirror_col = 2 * axis - col
        if not axis < mirror_col < w:
            errors.append(
                f"source ({row},{col}) has out-of-bounds mirror column {mirror_col}"
            )
        else:
            target_colors[(row, mirror_col)] = color

    overlap = [cell for cell in right if (cell[0], cell[1]) in target_colors]
    erase = [cell for cell in right if (cell[0], cell[1]) not in target_colors]
    facts["overlap_distractors"] = overlap
    facts["erase_distractors"] = erase

    if not right:
        mode = "none"
    elif len(right) == 2 and len(erase) == 2:
        mode = "erase"
    elif len(right) == 2 and len(overlap) == 2:
        mode = "overwrite"
    elif len(right) == 2 and len(overlap) == 1 and len(erase) == 1:
        mode = "mixed"
    else:
        mode = None
        errors.append(
            "right distractors must be absent or exactly two cells in erase, "
            f"overwrite, or mixed configuration; got overlap={len(overlap)}, "
            f"erase={len(erase)}"
        )
    facts["distractor_mode"] = mode

    if right:
        distractor_colors = {color for _row, _col, color in right}
        if len(distractor_colors) != 1:
            errors.append(
                f"right distractors must use one control color, got {sorted(distractor_colors)}"
            )
        if distractor_colors & source_colors:
            errors.append("right distractor color must differ from every source color")

    if errors:
        return facts

    out = full_grid(h, w, 0)
    for row in range(h):
        out[row][axis] = 5
    for row, col, color in sources:
        out[row][col] = color
        out[row][2 * axis - col] = color
    facts["output"] = out
    if out == grid:
        errors.append("the mirror reconstruction must change the input")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful teaching grammar, including right noise."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_sources": len(facts["sources"]),
        "n_source_colors": len(facts["source_colors"]),
        "axis_profile": facts["axis_profile"],
        "distractor_mode": facts["distractor_mode"],
    }


def _canonical_signature(facts: dict[str, Any]) -> tuple[Any, ...]:
    return (
        facts["height"],
        facts["width"],
        len(facts["sources"]),
        len(facts["source_colors"]),
        facts["axis_profile"],
        facts["distractor_mode"],
    )


_CANONICAL_SIGNATURES = {
    (7, 9, 5, 1, "centered", "erase"),
    (6, 11, 6, 1, "centered", "none"),
    (8, 9, 7, 1, "centered", "none"),
    (7, 11, 6, 1, "centered", "none"),
}


def strict_canonical_like(grid) -> list[str]:
    facts = _analyze(grid)
    if facts["errors"]:
        return list(facts["errors"])
    signature = _canonical_signature(facts)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"joint canonical signature not observed: {signature!r}"]
    return []


def canonical_profile_signature(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return None
    return _canonical_signature(facts)


def semantic_signature(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        **observe_overrides(grid),
        "source_columns": tuple(sorted(col for _row, col, _color in facts["sources"])),
        "overlap_distractors": len(facts["overlap_distractors"]),
        "erase_distractors": len(facts["erase_distractors"]),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")
    limits = {
        "grid_h": (6, 8),
        "grid_w": (9, 11),
        "n_sources": (2, 7),
        "n_source_colors": (1, 2),
    }
    for key, value in overrides.items():
        if key in limits:
            lo, hi = limits[key]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{key} must be an integer in {lo}..{hi}, got {value!r}")
        elif key == "axis_profile":
            if not isinstance(value, str) or value not in AXIS_PROFILES:
                raise ValueError(f"axis_profile must be one of {AXIS_PROFILES}, got {value!r}")
        elif key == "distractor_mode":
            if not isinstance(value, str) or value not in DISTRACTOR_MODES:
                raise ValueError(
                    f"distractor_mode must be one of {DISTRACTOR_MODES}, got {value!r}"
                )


def _draw_exact_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_exact_choice(ctx, overrides, label: str, default: str, options: tuple[str, ...]) -> str:
    if label in overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _difficulty_band(difficulty: str | None) -> str:
    return "medium" if difficulty is None else difficulty


def _choose_source_cells(
    ctx,
    h: int,
    w: int,
    axis: int,
    count: int,
    difficulty: str | None,
) -> list[tuple[int, int]]:
    first_col = max(0, 2 * axis - (w - 1))
    columns = list(range(first_col, axis))
    if len(columns) < 2:
        raise AssertionError("axis profile left fewer than two mirrorable source columns")

    band = _difficulty_band(difficulty)
    rng = ctx.draw_rng(f"source_layout:{band}")
    far_row = rng.randrange(h)
    if band == "easy":
        near_row = far_row
    elif band == "hard":
        near_row = (far_row + max(1, h // 2)) % h
    else:
        near_row = rng.randrange(h)

    far = (far_row, columns[0])
    near = (near_row, columns[-1])
    selected = [far, near]
    candidates = [
        (row, col)
        for row in range(h)
        for col in columns
        if (row, col) not in selected
    ]
    if band == "easy":
        candidates.sort(
            key=lambda cell: (
                abs(cell[0] - far_row),
                columns[-1] - cell[1],
                cell[0],
                cell[1],
            )
        )
    else:
        rng.shuffle(candidates)
    selected.extend(candidates[: count - len(selected)])
    # A seed-dependent permutation keeps the forced edge cells from always
    # receiving the first palette colors while preserving exact membership.
    rng.shuffle(selected)
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lawful scene with exact observable controls."""
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")

    profile_name = schedule_profile(seed, sample_index, difficulty)
    defaults = _PROFILE_BY_NAME[profile_name]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", defaults["grid_h"], 6, 8)
    w = _draw_exact_int(ctx, overrides, "grid_w", defaults["grid_w"], 9, 11)
    n_sources = _draw_exact_int(
        ctx, overrides, "n_sources", defaults["n_sources"], 2, 7
    )
    n_source_colors = _draw_exact_int(
        ctx,
        overrides,
        "n_source_colors",
        defaults["n_source_colors"],
        1,
        2,
    )
    axis_profile = _draw_exact_choice(
        ctx,
        overrides,
        "axis_profile",
        defaults["axis_profile"],
        AXIS_PROFILES,
    )
    distractor_mode = _draw_exact_choice(
        ctx,
        overrides,
        "distractor_mode",
        defaults["distractor_mode"],
        DISTRACTOR_MODES,
    )

    axis = _axis_for(w, axis_profile)
    grid = full_grid(h, w, 0)
    for row in range(h):
        grid[row][axis] = 5

    palette = list(SOURCE_COLORS)
    palette_rng = ctx.draw_rng("source_palette")
    palette_rng.shuffle(palette)
    # Disjoint two-color windows make the three difficulty bands observably
    # different even when two layout strategies happen to select the same cells.
    palette_offset = {"easy": 0, "medium": 2, "hard": 4}[
        _difficulty_band(difficulty)
    ]
    palette = palette[palette_offset:] + palette[:palette_offset]
    source_palette = palette[:n_source_colors]
    distractor_color = next(color for color in palette if color not in source_palette)

    positions = _choose_source_cells(ctx, h, w, axis, n_sources, difficulty)
    color_rng = ctx.draw_rng("source_colors")
    color_cycle = source_palette[:]
    color_rng.shuffle(color_cycle)
    source_records: list[tuple[int, int, int]] = []
    for index, (row, col) in enumerate(positions):
        color = color_cycle[index % len(color_cycle)]
        grid[row][col] = color
        source_records.append((row, col, color))

    target_positions = [(row, 2 * axis - col) for row, col, _color in source_records]
    target_set = set(target_positions)
    non_target_right = [
        (row, col)
        for row in range(h)
        for col in range(axis + 1, w)
        if (row, col) not in target_set
    ]
    noise_rng = ctx.draw_rng("right_distractors")
    noise_rng.shuffle(target_positions)
    noise_rng.shuffle(non_target_right)
    if distractor_mode == "erase":
        distractors = non_target_right[:2]
    elif distractor_mode == "overwrite":
        distractors = target_positions[:2]
    elif distractor_mode == "mixed":
        distractors = [target_positions[0], non_target_right[0]]
    else:
        distractors = []
    for row, col in distractors:
        grid[row][col] = distractor_color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_sources": n_sources,
        "n_source_colors": n_source_colors,
        "axis_profile": axis_profile,
        "distractor_mode": distractor_mode,
    }
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def rule_mirror(grid):
    """Diagnostic Python mirror of the selected Racket rule; not label authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return deepcopy(facts["output"])


def _reconstruct_with_axis(grid, axis: int, *, allowed_colors: set[int] | None = None, first_only=False):
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 5:
                out[row][col] = 5
    sources = [
        (row, col, grid[row][col])
        for row in range(h)
        for col in range(max(0, min(axis, w)))
        if grid[row][col] not in (0, 5)
        and (allowed_colors is None or grid[row][col] in allowed_colors)
    ]
    if first_only:
        sources = sources[:1]
    for row, col, color in sources:
        mirror_col = 2 * axis - col
        if 0 <= mirror_col < w:
            out[row][col] = color
            out[row][mirror_col] = color
    return out


def _fixed_geometric_center(grid):
    if not _is_arc_grid(grid):
        return deepcopy(grid)
    return _reconstruct_with_axis(grid, (len(grid[0]) - 1) // 2)


def _single_source_color(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    first_color = min(facts["source_colors"])
    return _reconstruct_with_axis(grid, facts["axis"], allowed_colors={first_color})


def _preserve_unrelated_right(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    out = deepcopy(grid)
    for row, col, color in facts["sources"]:
        out[row][2 * facts["axis"] - col] = color
    return out


def _do_not_overwrite_right(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    out = full_grid(facts["height"], facts["width"], 0)
    for row in range(facts["height"]):
        out[row][facts["axis"]] = 5
    for row, col, color in facts["sources"]:
        mirror_col = 2 * facts["axis"] - col
        out[row][col] = color
        out[row][mirror_col] = grid[row][mirror_col] or color
    return out


def _first_source_only(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    return _reconstruct_with_axis(grid, facts["axis"], first_only=True)


def _erase_without_mirroring(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        return deepcopy(grid)
    out = full_grid(facts["height"], facts["width"], 0)
    for row in range(facts["height"]):
        out[row][facts["axis"]] = 5
    for row, col, color in facts["sources"]:
        out[row][col] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_geometric_center": _fixed_geometric_center,
    "single_source_color": _single_source_color,
    "preserve_unrelated_right": _preserve_unrelated_right,
    "do_not_overwrite_right": _do_not_overwrite_right,
    "first_source_only": _first_source_only,
}

CANONICAL_SHORTCUTS = {
    "fixed_geometric_center": _fixed_geometric_center,
    "single_source_color": _single_source_color,
}

LESSON_COMPETITORS = {
    "leave_input_unchanged": lambda grid: deepcopy(grid),
    "fixed_geometric_center": _fixed_geometric_center,
    "single_source_color": _single_source_color,
    "preserve_unrelated_right": _preserve_unrelated_right,
    "do_not_overwrite_right": _do_not_overwrite_right,
    "first_source_only": _first_source_only,
    "erase_without_mirroring": _erase_without_mirroring,
}


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    facts = _analyze(pair["input"])
    if facts["errors"]:
        return None, [f"{label}: {error}" for error in facts["errors"]]
    if pair["output"] != facts["output"]:
        return None, [f"{label} output is not the gray-axis reconstruction"]
    return facts, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when the scheduled evidence leaves a named rival alive."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    analyses: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index, pair in enumerate(demos):
        facts, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if facts is not None:
            analyses.append((pair, facts))
    _query_facts, query_errors = _pair_analysis(query, "query")
    reasons.extend(query_errors)
    if reasons:
        return reasons

    modes = {facts["distractor_mode"] for _pair, facts in analyses}
    axis_profiles = {facts["axis_profile"] for _pair, facts in analyses}
    color_counts = {len(facts["source_colors"]) for _pair, facts in analyses}
    missing_modes = set(DISTRACTOR_MODES) - modes
    if missing_modes:
        reasons.append(f"demonstrations miss distractor controls: {sorted(missing_modes)}")
    missing_axes = set(AXIS_PROFILES) - axis_profiles
    if missing_axes:
        reasons.append(f"demonstrations miss axis controls: {sorted(missing_axes)}")
    if color_counts != {1, 2}:
        reasons.append("demonstrations must contain both single- and two-color sources")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(deepcopy(pair["input"])) == pair["output"]
            for pair, _facts in analyses
        )
        if survives and competitor(deepcopy(query["input"])) != query["output"]:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid):
        facts = _analyze(grid)
        return not facts["errors"] and bool(predicate(facts))

    return wrapped


SEMANTIC_WITNESSES = {
    "off_center_axis": _witness(lambda facts: facts["axis_profile"] != "centered"),
    "multiple_source_colors": _witness(lambda facts: len(facts["source_colors"]) == 2),
    "unrelated_right_noise": _witness(
        lambda facts: facts["distractor_mode"] in ("erase", "mixed")
    ),
    "occupied_mirror_target": _witness(
        lambda facts: facts["distractor_mode"] in ("overwrite", "mixed")
    ),
    "multiple_sources": _witness(lambda facts: len(facts["sources"]) >= 2),
}

WITNESS_RIVALS = {
    "off_center_axis": ["fixed_geometric_center"],
    "multiple_source_colors": ["single_source_color"],
    "unrelated_right_noise": ["preserve_unrelated_right"],
    "occupied_mirror_target": ["do_not_overwrite_right"],
    "multiple_sources": ["first_source_only"],
}
