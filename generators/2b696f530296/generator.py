"""Generator for ARC task ``2b696f530296`` (legacy ``c8cbb738``).

Each non-background color marks four cells around an integer centroid.  The
Racket authority sorts foreground colors numerically, uses the lowest color's
Chebyshev radius ``R`` to size a ``(2R+1)`` square, translates every group to
that common center, clips cells outside the square, and keeps the first
(lowest-color) value at normalized collisions.

The four-step ordinary schedule is deliberate: every four consecutive samples
contains a radius-1 collision, a radius-2 disjoint scene, a mixed-radius scene
that kills the tempting max-radius shortcut, and the canonical radius-3 branch.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b696f530296"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "b3149de64a85"

SUMMARY = (
    "Every non-modal color has four cells with an integer centroid. Sort those "
    "colors numerically; let R be the Chebyshev radius of the lowest color. "
    "Translate every four-cell group to the center of a (2R+1)-square output, "
    "clip outside cells, and resolve normalized collisions in ascending-color "
    "order (the lower color remains)."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the unique modal nonzero color is background",
    "there are two through four foreground colors and each occurs four times",
    "every foreground group has an integer centroid and Chebyshev radius 1..3",
    "every foreground group spans at least two rows and two columns",
    "foreground centroids are distinct",
]

SCENE_PROFILES = (
    "uniform_overlap_r1",
    "uniform_disjoint_r2",
    "mixed_max_killer_r1",
    "uniform_overlap_r3",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 4 schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "group_count": {
        "type": "int",
        "default": "profile schedule 2|4|3|4",
        "valid": "2..4",
    },
    "bg_color": {
        "type": "color",
        "default": "rng !0",
        "valid": "1..9",
    },
}

# Every exact axis combination is supported; no structured incompatibilities.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Balanced four-cell motifs.  Every offset set sums to (0, 0), so the displayed
# center is the true integer centroid rather than a quotient-rounded surrogate.
_MOTIFS_BY_RADIUS: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (
        ((-1, 0), (0, -1), (0, 1), (1, 0)),
        ((-1, -1), (-1, 1), (1, -1), (1, 1)),
        ((-1, -1), (-1, 0), (1, 0), (1, 1)),
        ((-1, 1), (-1, 0), (1, 0), (1, -1)),
    ),
    2: (
        ((-2, 0), (0, -2), (0, 2), (2, 0)),
        ((-2, -2), (-2, 2), (2, -2), (2, 2)),
        ((-2, -1), (-1, -2), (1, 2), (2, 1)),
        ((-2, 1), (-1, -1), (1, -1), (2, 1)),
        ((-2, -1), (-2, 1), (2, -1), (2, 1)),
        ((-1, -2), (-1, 2), (1, -2), (1, 2)),
    ),
    3: (
        ((-3, 0), (0, -3), (0, 3), (3, 0)),
        ((-3, -3), (-3, 3), (3, -3), (3, 3)),
        ((-3, -1), (-3, 1), (3, -1), (3, 1)),
        ((-1, -3), (-1, 3), (1, -3), (1, 3)),
        ((-3, 0), (-1, 0), (1, 0), (3, 0)),
        ((0, -3), (0, -1), (0, 1), (0, 3)),
        ((-3, -1), (-1, -3), (1, 3), (3, 1)),
        ((-3, 1), (-1, 3), (1, -3), (3, -1)),
    ),
}


# Three pairwise-disjoint, balanced radius-2 motifs that also avoid the corner
# anchor.  Rotating their color assignment by difficulty makes the band knob
# observable without changing the semantic profile or canonical dimensions.
_DISJOINT_R2_MOTIFS = (
    _MOTIFS_BY_RADIUS[2][0],
    _MOTIFS_BY_RADIUS[2][2],
    ((-2, 1), (-1, 1), (1, -1), (2, -1)),
)

_PROFILE_DEFAULT_GROUP_COUNT = {
    "uniform_overlap_r1": 2,
    "uniform_disjoint_r2": 4,
    "mixed_max_killer_r1": 3,
    "uniform_overlap_r3": 4,
}

# Canonical-scale anchors.  These dimensions/palette sizes exactly reproduce
# profiles present in the two canonical source rows when the default count is
# used, while override counts fall back to the generic fitter below.
_PROFILE_CANVAS = {
    "uniform_overlap_r1": (10, 8),
    "uniform_disjoint_r2": (12, 11),
    "uniform_overlap_r3": (18, 19),
}

_PROFILE_CENTERS = {
    "uniform_overlap_r1": ((2, 2), (6, 4)),
    "uniform_disjoint_r2": ((2, 2), (2, 8), (8, 2), (8, 8)),
    "uniform_overlap_r3": ((3, 3), (3, 15), (14, 3), (14, 15)),
}


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        return []
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                out.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, list):
            out.append(list(row))
        else:
            return []
    return out


def _scene_facts(grid) -> dict[str, object]:
    coerced = _coerce_grid(grid)
    errors: list[str] = []
    if not coerced or not coerced[0]:
        return {"errors": ["grid must be nonempty and rectangular"]}
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return {"errors": ["grid must be nonempty and rectangular"]}
    height = len(coerced)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within ARC bounds 1..30")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")

    counts = Counter(value for row in coerced for value in row)
    max_count = max(counts.values())
    modal = sorted(color for color, count in counts.items() if count == max_count)
    if len(modal) != 1:
        errors.append("background must be the unique modal color")
    bg = modal[0]
    if bg == 0:
        errors.append("background must be nonzero")

    colors = sorted(color for color in counts if color != bg)
    if not 2 <= len(colors) <= 4:
        errors.append("expected 2..4 foreground colors")

    groups: list[dict[str, object]] = []
    centroids: list[tuple[int, int]] = []
    for color in colors:
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(coerced)
            for col_index, value in enumerate(row)
            if value == color
        ]
        if len(cells) != 4:
            errors.append(f"color {color} has {len(cells)} cells (expected 4)")
            continue
        row_sum = sum(row for row, _col in cells)
        col_sum = sum(col for _row, col in cells)
        if row_sum % 4 or col_sum % 4:
            errors.append(f"color {color} does not have an integer centroid")
        center = (row_sum // 4, col_sum // 4)
        offsets = tuple(sorted((row - center[0], col - center[1]) for row, col in cells))
        radius = max(max(abs(dr), abs(dc)) for dr, dc in offsets)
        if not 1 <= radius <= 3:
            errors.append(f"color {color} radius {radius} is outside 1..3")
        if len({row for row, _col in cells}) < 2 or len({col for _row, col in cells}) < 2:
            errors.append(f"color {color} must span at least two rows and columns")
        if center in centroids:
            errors.append(f"color {color} shares a centroid with another group")
        centroids.append(center)
        groups.append(
            {
                "color": color,
                "cells": tuple(cells),
                "center": center,
                "offsets": offsets,
                "radius": radius,
            }
        )

    # The background must dominate each four-cell foreground group, not merely
    # win a tie by implementation-specific iteration order.
    if max_count <= 4:
        errors.append("background must occur more than four times")

    first_overlap = False
    if groups:
        anchor_offsets = set(groups[0]["offsets"])
        first_overlap = any(
            bool(anchor_offsets & set(group["offsets"])) for group in groups[1:]
        )

    return {
        "errors": errors,
        "grid": coerced,
        "height": height,
        "width": width,
        "bg_color": bg,
        "colors": tuple(colors),
        "group_count": len(colors),
        "groups": tuple(groups),
        "radii": tuple(group["radius"] for group in groups),
        "first_overlap": first_overlap,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes; accept all canonical inputs."""
    del difficulty, meta
    return list(_scene_facts(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked grammar used by the strict semantic census."""
    return self_check(grid)


def _classify_profile(facts: dict[str, object]) -> str:
    groups = facts.get("groups") or ()
    if not groups:
        return "invalid"
    radii = tuple(int(group["radius"]) for group in groups)
    anchor_radius = radii[0]
    uniform = len(set(radii)) == 1
    overlap = bool(facts.get("first_overlap"))
    if anchor_radius == 1 and uniform and overlap:
        return "uniform_overlap_r1"
    if anchor_radius == 2 and uniform and not overlap:
        return "uniform_disjoint_r2"
    if anchor_radius == 1 and 3 in radii[1:] and not overlap:
        return "mixed_max_killer_r1"
    if anchor_radius == 3 and uniform and overlap:
        return "uniform_overlap_r3"
    return "other"


def observe_overrides(grid) -> dict[str, object]:
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(facts["errors"]))
    return {
        "scene_profile": _classify_profile(facts),
        "group_count": facts["group_count"],
        "bg_color": facts["bg_color"],
    }


def _difficulty_band(difficulty) -> int:
    if isinstance(difficulty, str):
        return {"easy": 0, "medium": 1, "hard": 2}.get(difficulty.lower(), 1)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = float(difficulty)
        return 0 if value < 1 / 3 else 1 if value < 2 / 3 else 2
    return 1


def _profile_motifs(
    profile: str, group_count: int, rng, band_index: int
) -> list[tuple[tuple[int, int], ...]]:
    if profile == "uniform_overlap_r1":
        base = _MOTIFS_BY_RADIUS[1][0]
        motifs = [base, base]
        motifs.extend(rng.choice(_MOTIFS_BY_RADIUS[1]) for _ in range(group_count - 2))
        return motifs[:group_count]
    if profile == "uniform_disjoint_r2":
        anchor = _MOTIFS_BY_RADIUS[2][1]  # corners
        ordered = list(_DISJOINT_R2_MOTIFS[band_index:] + _DISJOINT_R2_MOTIFS[:band_index])
        return [anchor] + ordered[: group_count - 1]
    if profile == "mixed_max_killer_r1":
        anchor = _MOTIFS_BY_RADIUS[1][1]  # radius-1 corners
        larger = _MOTIFS_BY_RADIUS[3][6]  # radius-3 diagonal, clipped by radius-1 anchor
        motifs = [anchor, larger]
        options = (
            (_MOTIFS_BY_RADIUS[2][0],),
            (_MOTIFS_BY_RADIUS[3][7],),
            (_MOTIFS_BY_RADIUS[2][0], _MOTIFS_BY_RADIUS[3][7]),
        )[band_index]
        motifs.extend(rng.choice(options) for _ in range(group_count - 2))
        return motifs[:group_count]
    if profile == "uniform_overlap_r3":
        base = _MOTIFS_BY_RADIUS[3][0]
        motifs = [base, base]
        valid_by_band = (
            (_MOTIFS_BY_RADIUS[3][1], _MOTIFS_BY_RADIUS[3][2]),
            (_MOTIFS_BY_RADIUS[3][3], _MOTIFS_BY_RADIUS[3][6]),
            (_MOTIFS_BY_RADIUS[3][7], _MOTIFS_BY_RADIUS[3][1]),
        )
        motifs.extend(rng.choice(valid_by_band[band_index]) for _ in range(group_count - 2))
        return motifs[:group_count]
    raise ValueError(f"unknown scene_profile {profile!r}")


def _generic_canvas_and_centers(
    motifs: list[tuple[tuple[int, int], ...]], group_count: int, rng
) -> tuple[int, int, list[tuple[int, int]]]:
    max_radius = max(max(max(abs(dr), abs(dc)) for dr, dc in motif) for motif in motifs)
    cols = 2 if group_count <= 4 else 3
    rows = (group_count + cols - 1) // cols
    pad = max_radius + 1
    spacing = 2 * max_radius + 2
    height = 2 * pad + (rows - 1) * spacing + 1
    width = 2 * pad + (cols - 1) * spacing + 1
    height += rng.randint(0, min(2, 30 - height))
    width += rng.randint(0, min(2, 30 - width))
    centers = [
        (pad + (index // cols) * spacing, pad + (index % cols) * spacing)
        for index in range(group_count)
    ]
    return height, width, centers


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))

    scheduled_profile = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
    effective_overrides = dict(overrides)
    effective_overrides.setdefault("scene_profile", scheduled_profile)
    effective_overrides.setdefault(
        "group_count", _PROFILE_DEFAULT_GROUP_COUNT[effective_overrides["scene_profile"]]
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    rng = ctx.draw_rng("layout")
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    group_count = ctx.draw_int("group_count", 2, 4)
    bg_color = ctx.draw_color("bg_color", exclude={0})
    colors = sorted(
        ctx.draw_distinct_colors("colors", n=group_count, exclude={0, bg_color})
    )
    band_index = _difficulty_band(difficulty)
    motifs = _profile_motifs(profile, group_count, rng, band_index)

    if (
        group_count == _PROFILE_DEFAULT_GROUP_COUNT[profile]
        and profile in _PROFILE_CANVAS
    ):
        height, width = _PROFILE_CANVAS[profile]
        centers = list(_PROFILE_CENTERS[profile])
        if profile == "uniform_overlap_r1":
            centers = [
                ((2, 2), (6, 4)),
                ((2, 3), (6, 4)),
                ((2, 2), (6, 5)),
            ][band_index]
            centers = list(centers)
    else:
        height, width, centers = _generic_canvas_and_centers(motifs, group_count, rng)

    grid = full_grid(height, width, bg_color)
    for color, center, motif in zip(colors, centers, motifs):
        for dr, dc in motif:
            row = center[0] + dr
            col = center[1] + dc
            if not (0 <= row < height and 0 <= col < width):
                raise AssertionError("internal layout bug: motif escaped canvas")
            if grid[row][col] != bg_color:
                raise AssertionError("internal layout bug: input motifs overlap")
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "scene_profile": profile,
        "group_count": group_count,
        "bg_color": bg_color,
    }
    if observed != expected:
        raise AssertionError(f"observable axis mismatch: expected {expected}, got {observed}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror used only for tests and adversarial analysis."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid source grid: " + "; ".join(facts["errors"]))
    groups = facts["groups"]
    bg_color = int(facts["bg_color"])
    anchor_radius = int(groups[0]["radius"])
    size = 2 * anchor_radius + 1
    output = full_grid(size, size, bg_color)
    for group in groups:
        color = int(group["color"])
        for dr, dc in group["offsets"]:
            row = dr + anchor_radius
            col = dc + anchor_radius
            if 0 <= row < size and 0 <= col < size and output[row][col] == bg_color:
                output[row][col] = color
    return output


def rival_max_radius(grid) -> list[list[int]]:
    """Tempting rival: size the output by the largest group, not the first."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid source grid")
    groups = facts["groups"]
    bg_color = int(facts["bg_color"])
    radius = max(int(group["radius"]) for group in groups)
    output = full_grid(2 * radius + 1, 2 * radius + 1, bg_color)
    for group in groups:
        for dr, dc in group["offsets"]:
            row, col = dr + radius, dc + radius
            if output[row][col] == bg_color:
                output[row][col] = int(group["color"])
    return output


def rival_high_color_overwrites(grid) -> list[list[int]]:
    """Tempting rival: later/higher colors overwrite normalized collisions."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid source grid")
    groups = facts["groups"]
    bg_color = int(facts["bg_color"])
    radius = int(groups[0]["radius"])
    output = full_grid(2 * radius + 1, 2 * radius + 1, bg_color)
    for group in groups:
        for dr, dc in group["offsets"]:
            row, col = dr + radius, dc + radius
            if 0 <= row < len(output) and 0 <= col < len(output[0]):
                output[row][col] = int(group["color"])
    return output


def rival_fixed_radius_one(grid) -> list[list[int]]:
    """Tempting rival: every output is the 3x3 radius-one normalization."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid source grid")
    groups = facts["groups"]
    bg_color = int(facts["bg_color"])
    radius = 1
    output = full_grid(3, 3, bg_color)
    for group in groups:
        for dr, dc in group["offsets"]:
            row, col = dr + radius, dc + radius
            if 0 <= row < 3 and 0 <= col < 3 and output[row][col] == bg_color:
                output[row][col] = int(group["color"])
    return output


def rival_first_group_only(grid) -> list[list[int]]:
    """Tempting rival: normalize only the lowest-color/anchor group."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid source grid")
    group = facts["groups"][0]
    bg_color = int(facts["bg_color"])
    radius = int(group["radius"])
    output = full_grid(2 * radius + 1, 2 * radius + 1, bg_color)
    for dr, dc in group["offsets"]:
        output[dr + radius][dc + radius] = int(group["color"])
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "max_radius": rival_max_radius,
    "high_color_overwrites": rival_high_color_overwrites,
    "fixed_radius_one": rival_fixed_radius_one,
    "first_group_only": rival_first_group_only,
}

SEMANTIC_WITNESSES = {
    "lowest_color_radius_clips_larger_groups": (
        lambda grid: _classify_profile(_scene_facts(grid)) == "mixed_max_killer_r1"
    ),
    "low_color_wins_normalized_collision": (
        lambda grid: bool(_scene_facts(grid).get("first_overlap"))
    ),
    "radius_three_output_scale": (
        lambda grid: bool(_scene_facts(grid).get("groups"))
        and int(_scene_facts(grid)["groups"][0]["radius"]) == 3
    ),
    "disjoint_overlay_keeps_all_offsets": (
        lambda grid: _classify_profile(_scene_facts(grid)) == "uniform_disjoint_r2"
    ),
}

WITNESS_RIVALS = {
    "lowest_color_radius_clips_larger_groups": ["max_radius"],
    "low_color_wins_normalized_collision": ["high_color_overwrites"],
    "radius_three_output_scale": ["fixed_radius_one"],
    "disjoint_overlay_keeps_all_offsets": ["first_group_only"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
SCHEDULE_PROFILES = SCENE_PROFILES

def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-example lesson to refute both serious rivals."""
    errors: list[str] = []
    profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair:
            errors.append(f"demo {index} is not an input/output pair")
            continue
        facts = _scene_facts(pair["input"])
        if facts["errors"]:
            errors.append(f"demo {index} is structurally invalid")
            continue
        profile = _classify_profile(facts)
        profiles.add(profile)
        if "output" in pair and pair["output"] != rule_mirror(pair["input"]):
            errors.append(f"demo {index} output disagrees with the pinned rule")
    missing = sorted(set(SCENE_PROFILES) - profiles)
    if missing:
        errors.append("demos omit decisive profile(s): " + ", ".join(missing))
    if isinstance(query, dict) and "input" in query:
        facts = _scene_facts(query["input"])
        if facts["errors"]:
            errors.append("query is structurally invalid")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            errors.append("query output disagrees with the pinned rule")
    return errors


def fresh_copy(grid) -> list[list[int]]:
    """Small explicit helper used by focused tests to assert fresh returns."""
    return deepcopy(grid)
