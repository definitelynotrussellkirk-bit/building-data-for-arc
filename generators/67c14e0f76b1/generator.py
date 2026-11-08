"""Generator for arc_additional_puzzle_bank_volume19:E128.

Rule: recolor a zero cell to 2 exactly when its immediate horizontal
neighbours in the input are both color 1.  Everything else is preserved.
"""
from __future__ import annotations

from typing import Any, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67c14e0f76b1"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "8178a08365e6"

SUMMARY = (
    "On a 0-background grid, recolor every 0 whose immediate left and right "
    "neighbours are both color 1 to color 2. The test is horizontal, local, "
    "and evaluated from the input grid. Longer horizontal gaps, pure vertical "
    "1-0-1 triples, and unrelated colored cells stay unchanged. Generated "
    "lessons rotate through isolated targets, overlapping 1-0-1-0-1 chains, "
    "left/right boundary targets, and a mixed scene; every scene also contains "
    "a wider horizontal-gap control and a vertical control."
)

INVARIANTS = [
    "the input contains at least one immediate horizontal 1-0-1 target",
    "ordinary generated scenes contain a pure vertical 1-0-1 control",
    "ordinary generated scenes contain a wider 1-0-0-1 horizontal control",
    "input color 2 is absent and all unrelated colors are preserved",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = ("isolated", "overlap", "edges", "mixed")
SCHEDULE_PROFILES = SCENE_PROFILES

# The named palettes include all five canonical (height, width, palette)
# profiles, plus two nuisance palettes that prevent fixed-color shortcuts.
_PALETTE_BY_PROFILE = {
    "single_3": (3,),
    "single_8": (8,),
    "dual_3_8": (3, 8),
    "dual_4_6": (4, 6),
    "dual_4_7": (4, 7),
    "dual_4_9": (4, 9),
    "dual_5_6": (5, 6),
    "dual_6_9": (6, 9),
}
_PROFILE_BY_PALETTE = {
    tuple(sorted(colors)): name for name, colors in _PALETTE_BY_PROFILE.items()
}
PALETTE_PROFILES = tuple(_PALETTE_BY_PROFILE)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical profile every fourth sample; otherwise difficulty-banded",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical profile every fourth sample; otherwise difficulty-banded",
        "valid": "10..16",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-slot sample_index schedule",
        "valid": "isolated|overlap|edges|mixed",
    },
    "palette_profile": {
        "type": "str",
        "default": "canonical palette on canonical slots; otherwise varied",
        "valid": "single_3|single_8|dual_3_8|dual_4_6|dual_4_7|dual_4_9|dual_5_6|dual_6_9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CANONICAL_LINKED_PROFILES = (
    (7, 12, "dual_4_7"),
    (8, 11, "dual_5_6"),
    (9, 13, "dual_3_8"),
    (8, 10, "dual_4_9"),
    (8, 12, "dual_4_6"),
)
_CANONICAL_STRICT_SIGNATURES = {
    (7, 12, (4, 7), 3),
    (8, 11, (5, 6), 3),
    (9, 13, (3, 8), 3),
    (8, 10, (4, 9), 3),
    (8, 12, (4, 6), 4),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the exact four-slot teaching schedule to the semantic gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _draw_scheduled_int(
    ctx,
    label: str,
    lo: int,
    hi: int,
    scheduled: int,
    overrides: dict[str, Any],
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, [scheduled])


def _draw_scheduled_choice(
    ctx,
    label: str,
    options: Sequence[str],
    scheduled: str,
    overrides: dict[str, Any],
) -> str:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, [scheduled])


def _horizontal_targets(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    if not grid or not grid[0]:
        return ()
    h, w = len(grid), len(grid[0])
    return tuple(
        (r, c)
        for r in range(h)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and grid[r][c - 1] == 1
        and grid[r][c + 1] == 1
    )


def _wide_gap_controls(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    """Return starts of exact 1-0-0-1 controls."""
    if not grid or not grid[0]:
        return ()
    h, w = len(grid), len(grid[0])
    return tuple(
        (r, c)
        for r in range(h)
        for c in range(w - 3)
        if tuple(grid[r][c : c + 4]) == (1, 0, 0, 1)
    )


def _pure_vertical_controls(
    grid: Sequence[Sequence[int]],
    targets: set[tuple[int, int]] | None = None,
) -> tuple[tuple[int, int], ...]:
    """Vertical 1-0-1 centers which are not horizontal targets."""
    if not grid or not grid[0]:
        return ()
    h, w = len(grid), len(grid[0])
    target_set = targets if targets is not None else set(_horizontal_targets(grid))
    return tuple(
        (r, c)
        for r in range(1, h - 1)
        for c in range(w)
        if grid[r][c] == 0
        and grid[r - 1][c] == 1
        and grid[r + 1][c] == 1
        and (r, c) not in target_set
    )


def _scene_profile(
    targets: Sequence[tuple[int, int]], h: int, w: int
) -> str | None:
    target_set = set(targets)
    overlap = any((r, c + 2) in target_set for r, c in target_set)
    left = any(c == 1 for _, c in target_set)
    right = any(c == w - 2 for _, c in target_set)
    key = (len(targets), overlap, left, right)
    return {
        (3, False, False, False): "isolated",
        (4, True, False, False): "overlap",
        (4, False, True, True): "edges",
        (7, True, True, True): "mixed",
    }.get(key)


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return h, w, ["grid must be rectangular"]
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC bounds: {h}x{w}")
    bad = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad:
        errors.append("grid contains a non-integer or value outside ARC palette 0..9")
    if any(value == 2 for row in grid for value in row):
        errors.append("input already contains output color 2")
    return h, w, errors


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    h, w, errors = _validate_grid(grid)
    info: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return info, errors
    targets = _horizontal_targets(grid)
    target_set = set(targets)
    distractor_colors = tuple(
        sorted({value for row in grid for value in row if value not in (0, 1, 2)})
    )
    info.update(
        {
            "targets": targets,
            "target_count": len(targets),
            "scene_profile": _scene_profile(targets, h, w),
            "wide_gap_controls": _wide_gap_controls(grid),
            "vertical_controls": _pure_vertical_controls(grid, target_set),
            "distractor_colors": distractor_colors,
            "palette_profile": _PROFILE_BY_PALETTE.get(distractor_colors),
            "distractor_cells": sum(
                value not in (0, 1, 2) for row in grid for value in row
            ),
        }
    )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept every canonical input and reject malformed/rule-hiding scenes."""
    del difficulty, meta
    info, errors = _analyse(grid)
    if errors:
        return errors
    if info["target_count"] == 0:
        errors.append("input has no immediate horizontal 1-0-1 target")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept the official inputs and the task-linked generated curriculum."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    if info["target_count"] == 0:
        return ["input has no immediate horizontal 1-0-1 target"]

    signature = (
        info["grid_h"],
        info["grid_w"],
        info["distractor_colors"],
        info["target_count"],
    )
    if signature in _CANONICAL_STRICT_SIGNATURES:
        return []

    if not (7 <= info["grid_h"] <= 14 and 10 <= info["grid_w"] <= 16):
        errors.append("generated curriculum dimensions must be within 7..14 by 10..16")
    if info["scene_profile"] not in SCENE_PROFILES:
        errors.append("target layout does not match a declared scene_profile")
    if info["palette_profile"] not in PALETTE_PROFILES:
        errors.append("distractor palette does not match a declared palette_profile")
    if not info["wide_gap_controls"]:
        errors.append("missing a 1-0-0-1 wider-gap control")
    if not info["vertical_controls"]:
        errors.append("missing a pure vertical 1-0-1 control")
    return errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    strict_errors = strict_canonical_like(grid)
    if errors or strict_errors:
        raise ValueError("; ".join(errors + strict_errors))
    if info["scene_profile"] is None or info["palette_profile"] is None:
        raise ValueError("grid has no recoverable declared profile")
    return {name: info[name] for name in AXES}


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror; synchronized Racket remains sole authority."""
    _, _, errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = _copy_grid(grid)
    for r, c in _horizontal_targets(grid):
        out[r][c] = 2
    return out


def _place_target_rows(
    grid: list[list[int]],
    profile: str,
    rows: Sequence[int],
    rng,
) -> tuple[int, int]:
    """Place target rows plus one dedicated wider-gap row.

    Returns the wider-gap row and its start column so later distractors can
    preserve the decisive zeros.
    """
    h, w = len(grid), len(grid[0])
    del h
    pattern_names = {
        "isolated": ("isolated", "isolated", "isolated"),
        "overlap": ("overlap", "isolated", "isolated"),
        "edges": ("left", "right", "isolated", "isolated"),
        "mixed": ("left", "right", "overlap", "isolated", "isolated", "isolated"),
    }[profile]
    if len(rows) < len(pattern_names) + 1:
        raise ValueError("grid height is too small for the requested scene_profile")

    for row, name in zip(rows, pattern_names):
        if name == "left":
            endpoints = (0, 2)
        elif name == "right":
            endpoints = (w - 3, w - 1)
        elif name == "overlap":
            start = rng.randint(1, w - 6)
            endpoints = (start, start + 2, start + 4)
        else:
            start = rng.randint(1, w - 4)
            endpoints = (start, start + 2)
        for col in endpoints:
            grid[row][col] = 1

    gap_row = rows[len(pattern_names)]
    gap_start = rng.randint(0, w - 4)
    grid[gap_row][gap_start] = 1
    grid[gap_row][gap_start + 3] = 1
    return gap_row, gap_start


def _add_vertical_control(grid: list[list[int]], rng) -> tuple[int, int]:
    """Add a pure vertical control without changing any horizontal target."""
    h, w = len(grid), len(grid[0])
    original_targets = _horizontal_targets(grid)
    candidates = [(r, c) for r in range(1, h - 1) for c in range(w)]
    rng.shuffle(candidates)
    for r, c in candidates:
        if grid[r][c] != 0 or (r, c) in original_targets:
            continue
        trial = _copy_grid(grid)
        trial[r - 1][c] = 1
        trial[r + 1][c] = 1
        if _horizontal_targets(trial) != original_targets:
            continue
        if not _pure_vertical_controls(trial, set(original_targets)):
            continue
        grid[r - 1][c] = 1
        grid[r + 1][c] = 1
        return r, c
    raise RuntimeError("could not place a pure vertical 1-0-1 control")


def _add_distractors(
    grid: list[list[int]],
    palette_profile: str,
    protected: set[tuple[int, int]],
    rng,
) -> None:
    colors = _PALETTE_BY_PROFILE[palette_profile]
    count = rng.randint(max(2, len(colors)), 6)
    candidates = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0 and (r, c) not in protected
    ]
    rng.shuffle(candidates)
    if len(candidates) < count:
        raise RuntimeError("not enough safe cells for distractors")
    chosen = candidates[:count]
    for index, (r, c) in enumerate(chosen):
        grid[r][c] = colors[index % len(colors)]


def _build_grid(
    h: int,
    w: int,
    scene_profile: str,
    palette_profile: str,
    rng,
) -> list[list[int]]:
    for _attempt in range(64):
        grid = full_grid(h, w, 0)
        rows = rng.sample(range(h), h)
        gap_row, gap_start = _place_target_rows(grid, scene_profile, rows, rng)
        vertical_center = _add_vertical_control(grid, rng)
        targets = set(_horizontal_targets(grid))
        protected = set(targets)
        protected.add(vertical_center)
        protected.update({(gap_row, gap_start + 1), (gap_row, gap_start + 2)})
        protected.update(_pure_vertical_controls(grid, targets))
        _add_distractors(grid, palette_profile, protected, rng)
        info, errors = _analyse(grid)
        if errors:
            continue
        if info["scene_profile"] != scene_profile:
            continue
        if info["palette_profile"] != palette_profile:
            continue
        if not info["wide_gap_controls"] or not info["vertical_controls"]:
            continue
        return grid
    raise RuntimeError("failed to construct a strict task-linked scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    canonical_slot = int(sample_index) % 4 == 0
    if canonical_slot:
        profile_rng = ctx.draw_rng("canonical_profile_schedule")
        scheduled_h, scheduled_w, scheduled_palette = profile_rng.choice(
            _CANONICAL_LINKED_PROFILES
        )
    else:
        height_options = {
            "easy": tuple(range(7, 10)),
            "medium": tuple(range(8, 12)),
            "hard": tuple(range(10, 15)),
        }[band]
        width_options = {
            "easy": tuple(range(10, 14)),
            "medium": tuple(range(11, 15)),
            "hard": tuple(range(12, 17)),
        }[band]
        scheduled_h = ctx.draw_rng("height_schedule").choice(height_options)
        scheduled_w = ctx.draw_rng("width_schedule").choice(width_options)
        # Cycle the palette by sample index so every four-example teaching
        # window necessarily varies this irrelevant feature.  A keyed random
        # draw could repeat the same palette across an entire window and let
        # fixed-palette shortcuts survive the lesson gate.
        scheduled_palette = PALETTE_PROFILES[(int(seed) + int(sample_index)) % len(PALETTE_PROFILES)]

    scheduled_scene = schedule_profile(seed, sample_index, band)
    h = _draw_scheduled_int(ctx, "grid_h", 7, 14, scheduled_h, overrides)
    w = _draw_scheduled_int(ctx, "grid_w", 10, 16, scheduled_w, overrides)
    scene_profile = _draw_scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, scheduled_scene, overrides
    )
    palette_profile = _draw_scheduled_choice(
        ctx, "palette_profile", PALETTE_PROFILES, scheduled_palette, overrides
    )
    grid = _build_grid(h, w, scene_profile, palette_profile, ctx.draw_rng("layout"))

    observed = observe_overrides(grid)
    for name, value in ctx.recorded_draws().items():
        if name in AXES and observed.get(name) != value:
            raise RuntimeError(
                f"axis {name} requested {value!r} but grid realizes {observed.get(name)!r}"
            )
    return grid


# ---- task-linked witnesses and executable rivals --------------------------

def _info_if_strict(grid: Any) -> dict[str, Any] | None:
    if strict_canonical_like(grid):
        return None
    return _analyse(grid)[0]


def _witness_isolated(grid: Any) -> bool:
    info = _info_if_strict(grid)
    return bool(info and info["scene_profile"] == "isolated")


def _witness_overlap(grid: Any) -> bool:
    info = _info_if_strict(grid)
    return bool(info and info["scene_profile"] in ("overlap", "mixed"))


def _witness_edges(grid: Any) -> bool:
    info = _info_if_strict(grid)
    return bool(info and info["scene_profile"] in ("edges", "mixed"))


def _witness_wide_gap(grid: Any) -> bool:
    info = _info_if_strict(grid)
    return bool(info and info["wide_gap_controls"])


def _witness_vertical(grid: Any) -> bool:
    info = _info_if_strict(grid)
    return bool(info and info["vertical_controls"])


SEMANTIC_WITNESSES = {
    "isolated_immediate_targets": _witness_isolated,
    "overlapping_targets": _witness_overlap,
    "left_and_right_boundary_targets": _witness_edges,
    "wider_horizontal_gap_untouched": _witness_wide_gap,
    "vertical_1_0_1_untouched": _witness_vertical,
}


def _rival_identity(grid: Any) -> list[list[int]]:
    return _copy_grid(grid)


def _rival_fill_any_horizontal_span(grid: Any) -> list[list[int]]:
    out = _copy_grid(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and 1 in grid[r][:c] and 1 in grid[r][c + 1 :]:
                out[r][c] = 2
    return out


def _rival_fill_horizontal_and_vertical(grid: Any) -> list[list[int]]:
    out = rule_mirror(grid)
    targets = set(_horizontal_targets(grid))
    for r, c in _pure_vertical_controls(grid, targets):
        out[r][c] = 2
    return out


def _rival_skip_overlapping_targets(grid: Any) -> list[list[int]]:
    targets = set(_horizontal_targets(grid))
    out = _copy_grid(grid)
    for r, c in targets:
        if (r, c - 2) in targets or (r, c + 2) in targets:
            continue
        out[r][c] = 2
    return out


def _rival_skip_boundary_targets(grid: Any) -> list[list[int]]:
    out = _copy_grid(grid)
    w = len(grid[0])
    for r, c in _horizontal_targets(grid):
        if c not in (1, w - 2):
            out[r][c] = 2
    return out


def _rival_fill_with_one(grid: Any) -> list[list[int]]:
    out = _copy_grid(grid)
    for r, c in _horizontal_targets(grid):
        out[r][c] = 1
    return out


SEMANTIC_RIVALS = {
    "identity_no_fill": _rival_identity,
    "fill_any_horizontal_span": _rival_fill_any_horizontal_span,
    "fill_horizontal_and_vertical": _rival_fill_horizontal_and_vertical,
    "skip_overlapping_targets": _rival_skip_overlapping_targets,
    "skip_boundary_targets": _rival_skip_boundary_targets,
    "fill_with_color_1": _rival_fill_with_one,
}
WITNESS_RIVALS = {
    "isolated_immediate_targets": ["identity_no_fill", "fill_with_color_1"],
    "overlapping_targets": ["skip_overlapping_targets"],
    "left_and_right_boundary_targets": ["skip_boundary_targets"],
    "wider_horizontal_gap_untouched": ["fill_any_horizontal_span"],
    "vertical_1_0_1_untouched": ["fill_horizontal_and_vertical"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These three shortcuts fit every canonical training pair.  The generated
# curriculum deliberately includes decisive counterexamples for each one.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "fill_any_horizontal_span",
        "fill_horizontal_and_vertical",
        "skip_overlapping_targets",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    seen_profiles: set[str] = set()
    seen_palettes: set[str] = set()
    seen_shapes: set[tuple[int, int]] = set()
    valid_demo_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        strict_errors = strict_canonical_like(pair["input"])
        if errors or strict_errors:
            reasons.append(
                f"demo {index} is outside the task-linked curriculum: "
                f"{(errors + strict_errors)[0]}"
            )
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the immediate-horizontal rule")
            continue
        if not info["wide_gap_controls"]:
            reasons.append(f"demo {index} lacks a wider-gap control")
        if not info["vertical_controls"]:
            reasons.append(f"demo {index} lacks a vertical control")
        if info["scene_profile"]:
            seen_profiles.add(info["scene_profile"])
        if info["palette_profile"]:
            seen_palettes.add(info["palette_profile"])
        seen_shapes.add((info["grid_h"], info["grid_w"]))
        valid_demo_pairs.append(pair)

    if seen_profiles != set(SCENE_PROFILES):
        reasons.append(
            "demonstrations do not cover isolated, overlap, edges, and mixed "
            f"profiles: {sorted(seen_profiles)}"
        )
    if len(seen_palettes) < 2:
        reasons.append("demonstrations do not vary the irrelevant distractor palette")
    if len(seen_shapes) < 2:
        reasons.append("demonstrations do not vary grid shape")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demo_pairs and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demo_pairs
        ):
            reasons.append(f"named rival {name!r} fits every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        q_errors = strict_canonical_like(query["input"])
        if q_errors:
            reasons.append(f"query is outside the task-linked curriculum: {q_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the immediate-horizontal rule")
    return reasons
