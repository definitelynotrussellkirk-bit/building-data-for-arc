"""Generator for ARC task 6098a755202d — nearest-colour chamber fill.

A rectangular colour-5 frame contains two or three single-cell seeds.  Every
zero inside the frame takes the colour of the nearest seed by Manhattan
distance.  The canonical rule resolves ties by *distinct nearest colours*, not
by seed count: two equally near seeds of the same colour still fill the cell.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "6098a755202d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "5ede5108ff10"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An inset rectangular colour-5 frame contains two or three single-cell "
    "seeds. Fill each zero inside the frame with the colour among the nearest "
    "Manhattan-distance seeds when that nearest colour is unique. A tie between "
    "different colours stays 0; equally near seeds of the same colour still "
    "fill with that colour. Three scheduled profiles cover two distinct seeds, "
    "three distinct seeds, and the decisive repeated-colour tie case."
)

INVARIANTS = [
    "exactly one closed rectangular colour-5 frame with a background margin",
    "the frame contains two or three single-cell non-{0,5} seeds",
    "ordinary lessons include distinct-colour ties and repeated-colour seed ties",
    "ties are deduplicated by colour before deciding whether a cell stays 0",
]

PROFILES = ("distinct_pair", "same_color_tie", "distinct_triple")
SCHEDULE_PROFILES = (0, 1, 2)
SEED_COLORS = (2, 3, 4, 6, 7, 8, 9)
CANONICAL_SHAPES = (
    (9, 11, 1, 1),
    (8, 10, 1, 2),
    (10, 12, 2, 1),
    (9, 9, 1, 1),
    (10, 11, 1, 1),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-shape schedule; overrides 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-shape schedule; overrides 9..14",
        "valid": "9..14",
    },
    "frame_top": {
        "type": "int",
        "default": "canonical schedule over 1..2",
        "valid": "1..2",
    },
    "frame_left": {
        "type": "int",
        "default": "canonical schedule over 1..2",
        "valid": "1..2",
    },
    "profile": {
        "type": "str",
        "default": "sample_index schedule over distinct_pair|same_color_tie|distinct_triple",
        "valid": "|".join(PROFILES),
        "doc": (
            "same_color_tie contains two same-colour seeds whose shared nearest "
            "cells distinguish colour-deduplicated ties from any-seed ties"
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Three consecutive sample indices cover every semantic profile."""
    del seed
    _difficulty_band(difficulty)
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _scheduled_profile(seed: int, sample_index: int, difficulty: Any) -> str:
    return PROFILES[schedule_profile(seed, sample_index, difficulty)]


def _scheduled_shape(
    seed: int, sample_index: int, difficulty: Any
) -> tuple[int, int, int, int]:
    band_offset = {"easy": 0, "medium": 1, "hard": 2}[
        _difficulty_band(difficulty)
    ]
    return CANONICAL_SHAPES[
        (int(seed) + int(sample_index) + band_offset) % len(CANONICAL_SHAPES)
    ]


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list"]
    rows: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            if not row:
                return None, ["grid rows must be nonempty"]
            try:
                values = [int(cell) for cell in row]
            except ValueError:
                return None, ["string rows must contain ARC digits"]
        elif isinstance(row, list) and row:
            values = list(row)
        else:
            return None, ["grid rows must be nonempty lists or digit strings"]
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            return None, ["grid contains a non-ARC colour"]
        rows.append(values)
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return None, ["grid is ragged"]
    return rows, []


def _frame_bbox_normalized(
    grid: list[list[int]],
) -> tuple[tuple[int, int, int, int] | None, list[str]]:
    h, w = len(grid), len(grid[0])
    fives = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    if not fives:
        return None, ["missing colour-5 frame"]
    r1 = min(r for r, _ in fives)
    r2 = max(r for r, _ in fives)
    c1 = min(c for _, c in fives)
    c2 = max(c for _, c in fives)
    if r2 - r1 < 2 or c2 - c1 < 2:
        return None, ["colour-5 bounding box is too small to enclose seeds"]
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    if fives != border:
        return None, [
            "colour-5 cells do not form one closed rectangle "
            f"(missing={len(border - fives)}, extra={len(fives - border)})"
        ]
    if not (0 < r1 < r2 < h - 1 and 0 < c1 < c2 < w - 1):
        return None, ["colour-5 frame must have a background margin on every side"]
    return (r1, c1, r2, c2), []


def _geometry(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    frame, frame_errors = _frame_bbox_normalized(normalized)
    if frame_errors:
        return {"errors": frame_errors, "grid": normalized}
    assert frame is not None
    r1, c1, r2, c2 = frame
    h, w = len(normalized), len(normalized[0])
    seeds = [
        (r, c, normalized[r][c])
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if normalized[r][c] not in (0, 5)
    ]
    outside = [
        (r, c, normalized[r][c])
        for r in range(h)
        for c in range(w)
        if not (r1 <= r <= r2 and c1 <= c <= c2)
        and normalized[r][c] != 0
    ]
    errors = []
    if outside:
        errors.append(f"non-background cells outside frame: {outside[:4]}")
    if not seeds:
        errors.append("frame contains no seeds")
    return {
        "errors": errors,
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "frame": frame,
        "frame_top": r1,
        "frame_left": c1,
        "frame_bottom_margin": h - 1 - r2,
        "frame_right_margin": w - 1 - c2,
        "seeds": seeds,
    }


def _nearest(
    seeds: list[tuple[int, int, int]], r: int, c: int
) -> tuple[int, list[tuple[int, int, int]], set[int]]:
    distances = [
        (abs(r - sr) + abs(c - sc), (sr, sc, color))
        for sr, sc, color in seeds
    ]
    minimum = min(distance for distance, _ in distances)
    nearest_seeds = [seed for distance, seed in distances if distance == minimum]
    nearest_colors = {color for _, _, color in nearest_seeds}
    return minimum, nearest_seeds, nearest_colors


def _apply_rule(grid: Any, *, tie_by_seed: bool) -> list[list[int]]:
    geometry = _geometry(grid)
    if geometry.get("errors"):
        raise ValueError("; ".join(geometry["errors"]))
    normalized = geometry["grid"]
    r1, c1, r2, c2 = geometry["frame"]
    seeds = geometry["seeds"]
    out = [row[:] for row in normalized]
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if out[r][c] != 0:
                continue
            _, nearest_seeds, nearest_colors = _nearest(seeds, r, c)
            if tie_by_seed:
                if len(nearest_seeds) == 1:
                    out[r][c] = nearest_seeds[0][2]
            elif len(nearest_colors) == 1:
                out[r][c] = next(iter(nearest_colors))
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Apply the authoritative Manhattan rule, deduplicating tied colours."""
    return _apply_rule(grid, tie_by_seed=False)


def _tie_by_seed_rival(grid: Any) -> list[list[int]]:
    """Plausible wrong rule: any tie between seed cells stays background."""
    return _apply_rule(grid, tie_by_seed=True)


def semantic_observables(grid: Any) -> dict[str, Any]:
    geometry = _geometry(grid)
    if geometry.get("errors"):
        return geometry
    normalized = geometry["grid"]
    r1, c1, r2, c2 = geometry["frame"]
    seeds = geometry["seeds"]
    color_counts = Counter(color for _, _, color in seeds)
    profile = None
    if len(seeds) == 2 and len(color_counts) == 2:
        profile = "distinct_pair"
    elif len(seeds) == 3 and len(color_counts) == 3:
        profile = "distinct_triple"
    elif len(seeds) == 3 and sorted(color_counts.values()) == [1, 2]:
        profile = "same_color_tie"

    same_color_tie_cells = 0
    cross_color_tie_cells = 0
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if normalized[r][c] != 0:
                continue
            _, nearest_seeds, nearest_colors = _nearest(seeds, r, c)
            if len(nearest_seeds) > 1 and len(nearest_colors) == 1:
                same_color_tie_cells += 1
            if len(nearest_colors) > 1:
                cross_color_tie_cells += 1

    output = _apply_rule(normalized, tie_by_seed=False)
    interior_counts = Counter(
        output[r][c]
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if output[r][c] not in (0, 5)
    )
    return {
        **geometry,
        "profile": profile,
        "seed_count": len(seeds),
        "distinct_seed_colors": len(color_counts),
        "seed_color_counts": dict(color_counts),
        "same_color_tie_cells": same_color_tie_cells,
        "cross_color_tie_cells": cross_color_tie_cells,
        "territory_counts": dict(interior_counts),
        "rule_output": output,
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generator's canonical-shaped teaching grammar."""
    del difficulty, meta
    obs = semantic_observables(grid)
    errors = list(obs.get("errors", []))
    if errors:
        return errors
    h, w = obs["grid_h"], obs["grid_w"]
    if not (8 <= h <= 12 and 9 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 8..12 by 9..14")
    if obs["frame_top"] not in (1, 2):
        errors.append(f"frame top margin must be 1 or 2, got {obs['frame_top']}")
    if obs["frame_left"] not in (1, 2):
        errors.append(f"frame left margin must be 1 or 2, got {obs['frame_left']}")
    if obs["frame_bottom_margin"] != 1 or obs["frame_right_margin"] != 1:
        errors.append("frame bottom and right margins must each be 1")
    if not (2 <= obs["seed_count"] <= 3):
        errors.append(f"expected 2-3 interior seeds, found {obs['seed_count']}")
    if obs["profile"] not in PROFILES:
        errors.append("seed colours do not realize a declared profile")
    if (
        obs["profile"] == "same_color_tie"
        and obs["same_color_tie_cells"] < 1
    ):
        errors.append("same_color_tie profile has no shared nearest-colour cell")
    seed_colors = set(obs["seed_color_counts"])
    missing_territory = sorted(seed_colors - set(obs["territory_counts"]))
    if missing_territory:
        errors.append(f"seed colours have no output territory: {missing_territory}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def observe_overrides(grid: Any) -> dict[str, Any]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(obs["errors"]))
    return {
        "grid_h": obs["grid_h"],
        "grid_w": obs["grid_w"],
        "frame_top": obs["frame_top"],
        "frame_left": obs["frame_left"],
        "profile": obs["profile"],
    }


def _profile_seed_colors(profile: str, rng) -> list[int]:
    palette = list(SEED_COLORS)
    rng.shuffle(palette)
    if profile == "distinct_pair":
        return palette[:2]
    if profile == "distinct_triple":
        return palette[:3]
    if profile == "same_color_tie":
        return [palette[0], palette[0], palette[1]]
    raise ValueError(f"unknown profile: {profile!r}")


def _candidate_is_lesson(grid: list[list[int]], profile: str) -> bool:
    obs = semantic_observables(grid)
    if obs.get("errors") or obs.get("profile") != profile:
        return False
    if self_check(grid):
        return False
    if profile == "distinct_pair" and obs["cross_color_tie_cells"] < 1:
        return False
    if profile == "same_color_tie":
        if obs["same_color_tie_cells"] < 1:
            return False
        if rule_mirror(grid) == _tie_by_seed_rival(grid):
            return False
    return all(count >= 2 for count in obs["territory_counts"].values())


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    default_h, default_w, default_top, default_left = _scheduled_shape(
        seed, sample_index, difficulty
    )
    effective = dict(overrides)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("frame_top", default_top)
    effective.setdefault("frame_left", default_left)
    effective.setdefault("profile", _scheduled_profile(seed, sample_index, difficulty))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", 8, 12)
    w = ctx.draw_int_diff("grid_w", 9, 14)
    frame_top = ctx.draw_int("frame_top", 1, 2)
    frame_left = ctx.draw_int("frame_left", 1, 2)
    profile = ctx.draw_choice("profile", PROFILES)

    frame_bottom = h - 2
    frame_right = w - 2
    cells = [
        (r, c)
        for r in range(frame_top + 1, frame_bottom)
        for c in range(frame_left + 1, frame_right)
    ]
    n_seeds = 2 if profile == "distinct_pair" else 3
    if len(cells) < n_seeds:
        raise ValueError("selected frame has too few interior cells")

    layout_rng = ctx.draw_rng("layout")
    colors = _profile_seed_colors(profile, ctx.draw_rng("palette"))
    for _attempt in range(512):
        positions = layout_rng.sample(cells, n_seeds)
        layout_rng.shuffle(colors)
        grid = full_grid(h, w, 0)
        draw_frame(
            grid,
            frame_top,
            frame_left,
            frame_bottom,
            frame_right,
            5,
        )
        for (r, c), color in zip(positions, colors):
            grid[r][c] = color
        if _candidate_is_lesson(grid, profile):
            return grid
    raise ValueError(
        f"could not realize profile={profile!r} in {h}x{w} frame "
        f"at top={frame_top}, left={frame_left}"
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "tie_by_seed": _tie_by_seed_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "same_colour_tie_refutes_seed_count_tie": lambda grid: (
        semantic_observables(grid).get("same_color_tie_cells", 0) > 0
        and rule_mirror(grid) != _tie_by_seed_rival(grid)
    ),
}
WITNESS_RIVALS = {
    "same_colour_tie_refutes_seed_count_tie": ["tie_by_seed"],
}

# Every canonical seed has a distinct colour, so this wrong rule matches all
# canonical demonstrations.  The scheduled repeated-colour profile is the
# necessary counterexample.
CANONICAL_SHORTCUTS = {
    "tie_by_seed": _tie_by_seed_rival,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} is missing input/output")
            continue
        check = self_check(demo["input"])
        if check:
            reasons.append(f"demo {index} is outside the teaching grammar: {check}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with nearest-colour rule")
    query_check = self_check(query["input"])
    if query_check:
        reasons.append(f"query is outside the teaching grammar: {query_check}")
    if reasons:
        return reasons

    truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
            else:
                reasons.append(f"competitor {name!r} survives every demo and query")
    return reasons
