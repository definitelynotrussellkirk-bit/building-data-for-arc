"""Semantic generator for ARC task 154e19f36ba8.

The extreme cyan cells define a diagonal direction.  Trace outwards from both
extreme endpoints through zero cells, allowing one reflection when a color-2
edge wall blocks the diagonal.  Paint the strictly longer trace green.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "154e19f36ba8"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "8e0517e0f046"
SUMMARY = (
    "Trace outward from both extreme cyan cells, reflect once from the edge "
    "wall, and paint the strictly longer diagonal path green."
)
INVARIANTS = [
    "background is color 0 and the only foreground colors are wall color 2 and cyan 8",
    "one full color-2 band touches exactly one grid edge",
    "two or three cyan cells form a contiguous unit-step diagonal outside the wall",
    "the two outward traces have unequal lengths",
    "the selected longer trace visibly reflects once from the wall",
    "the selected trace contains at least two cells before and after reflection",
]

WALL_ORIENTATIONS = ("horizontal", "vertical")
CHOSEN_ENDPOINTS = ("forward", "backward")
SEED_COUNTS = (2, 3)
SCENE_PROFILES = tuple(
    f"{orientation}_{chosen}_{seed_count}"
    for orientation in WALL_ORIENTATIONS
    for chosen in CHOSEN_ENDPOINTS
    for seed_count in SEED_COUNTS
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "eight-profile sample_index schedule with a seed-dependent phase",
        "valid": (
            "horizontal_forward_2|horizontal_forward_3|"
            "horizontal_backward_2|horizontal_backward_3|"
            "vertical_forward_2|vertical_forward_3|"
            "vertical_backward_2|vertical_backward_3"
        ),
    }
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = len(SCENE_PROFILES)
SCHEDULE_PROFILES = SCENE_PROFILES
MIN_STRICT_FRAC = 1.0

# Exact public inputs are retained as a canonical-scale anchor.  They are only
# selected when their semantic profile matches the scheduled/requested profile.
_PUBLIC_INPUTS = (
    (
        "000000000000", "000000000000", "800000000000", "080000000000",
        "008000000000", "000000000000", "000000000000", "000000000000",
        "000000000000", "222222222222", "222222222222", "222222222222",
    ),
    (
        "000000000022", "000000000022", "000000000022", "000000000022",
        "000000000022", "000000000022", "000000000022", "000000000022",
        "000000000022", "000000000022", "000800000022", "008000000022",
    ),
    (
        "220000000000", "220000000000", "220000000000", "220000000000",
        "220000000000", "220000000000", "220000000000", "220000000000",
        "220000000000", "220000800000", "220000080000", "220000008000",
    ),
    (
        "000800002222", "000080002222", "000000002222", "000000002222",
        "000000002222", "000000002222", "000000002222", "000000002222",
        "000000002222", "000000002222", "000000002222", "000000002222",
    ),
)
_PUBLIC_GRIDS = tuple(
    tuple(tuple(int(value) for value in row) for row in grid)
    for grid in _PUBLIC_INPUTS
)
_PUBLIC_SIGNATURES = {grid: f"canonical_{index}" for index, grid in enumerate(_PUBLIC_GRIDS)}


def _copy_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _validate_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty 2D sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"], h, w
    errors: list[str] = []
    if not (8 <= h <= 18 and 8 <= w <= 18):
        errors.append(f"grid dimensions {h}x{w} must both lie in 8..18")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append("cells must be integer ARC colors, not bools or other values")
                return errors, h, w
            if value not in (0, 2, 8):
                errors.append(f"unexpected color {value}; expected only 0, 2, and 8")
                return errors, h, w
    return errors, h, w


def _wall_info(grid: Any) -> tuple[str, str, int] | None:
    """Return (side, orientation, thickness) for one exact full edge band."""
    h, w = len(grid), len(grid[0])
    twos = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2}
    candidates: list[tuple[str, str, int]] = []
    for side, orientation, limit in (
        ("top", "horizontal", min(4, h - 1)),
        ("bottom", "horizontal", min(4, h - 1)),
        ("left", "vertical", min(4, w - 1)),
        ("right", "vertical", min(4, w - 1)),
    ):
        for thickness in range(2, limit + 1):
            if side == "top":
                expected = {(r, c) for r in range(thickness) for c in range(w)}
            elif side == "bottom":
                expected = {(r, c) for r in range(h - thickness, h) for c in range(w)}
            elif side == "left":
                expected = {(r, c) for r in range(h) for c in range(thickness)}
            else:
                expected = {(r, c) for r in range(h) for c in range(w - thickness, w)}
            if twos == expected:
                candidates.append((side, orientation, thickness))
    return candidates[0] if len(candidates) == 1 else None


def _seed_info(grid: Any) -> tuple[list[tuple[int, int]], int, int] | None:
    seeds = sorted(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    )
    if len(seeds) not in SEED_COUNTS:
        return None
    dr = seeds[1][0] - seeds[0][0]
    dc = seeds[1][1] - seeds[0][1]
    if dr != 1 or dc not in (-1, 1):
        return None
    expected = [(seeds[0][0] + i, seeds[0][1] + i * dc) for i in range(len(seeds))]
    if seeds != expected:
        return None
    return seeds, dr, dc


def _trace(
    grid: Any,
    start: tuple[int, int],
    step_r: int,
    step_c: int,
    *,
    allow_bounce: bool = True,
) -> dict[str, Any]:
    """Python mirror of the canonical trace helper, with audit metadata."""
    h, w = len(grid), len(grid[0])
    r, c = start
    cr, cc = step_r, step_c
    bounced = False
    cells: list[tuple[int, int]] = []
    turn_index: int | None = None
    for _ in range(h * w):
        nr, nc = r + cr, c + cc
        if not (0 <= nr < h and 0 <= nc < w):
            break
        if grid[nr][nc] == 0:
            r, c = nr, nc
            cells.append((r, c))
            continue
        if bounced or not allow_bounce:
            break
        side_block = not (0 <= c + cc < w) or grid[r][c + cc] != 0
        vert_block = not (0 <= r + cr < h) or grid[r + cr][c] != 0
        ncr = -cr if vert_block else cr
        ncc = -cc if side_block else cc
        rr, rc = r + ncr, c + ncc
        if not (0 <= rr < h and 0 <= rc < w) or grid[rr][rc] != 0:
            break
        turn_index = len(cells)
        r, c, cr, cc = rr, rc, ncr, ncc
        bounced = True
        cells.append((r, c))
    return {
        "cells": tuple(cells),
        "bounced": bounced,
        "turn_index": turn_index,
        "final_step": (cr, cc),
    }


def _paths(grid: Any, *, first_two_only: bool = False, allow_bounce: bool = True) -> dict[str, Any]:
    seed_result = _seed_info(grid)
    if seed_result is None:
        raise ValueError("cyan seeds do not form a lawful two/three-cell unit diagonal")
    seeds, dr, dc = seed_result
    active = seeds[:2] if first_two_only else seeds
    a, b = active[0], active[-1]
    path1 = _trace(grid, b, dr, dc, allow_bounce=allow_bounce)
    path2 = _trace(grid, a, -dr, -dc, allow_bounce=allow_bounce)
    chosen_name = "forward" if len(path1["cells"]) >= len(path2["cells"]) else "backward"
    return {
        "seeds": seeds,
        "dr": dr,
        "dc": dc,
        "forward": path1,
        "backward": path2,
        "chosen_name": chosen_name,
        "chosen": path1 if chosen_name == "forward" else path2,
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors, h, w = _validate_grid(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "height": h,
        "width": w,
        "scene_profile": None,
    }
    if errors:
        return result
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 8}:
        errors.append(f"palette must be exactly {{0, 2, 8}}, got {sorted(palette)}")
    wall = _wall_info(grid)
    if wall is None:
        errors.append("color 2 must form exactly one full 2..4-cell-thick edge band")
    seeds = _seed_info(grid)
    if seeds is None:
        count = sum(value == 8 for row in grid for value in row)
        errors.append(
            f"expected two or three contiguous unit-step diagonal cyan cells, got {count}"
        )
    if errors:
        return result
    assert wall is not None and seeds is not None
    seed_cells, dr, dc = seeds
    if any(grid[r][c] == 2 for r, c in seed_cells):
        errors.append("cyan cells may not overlap the wall")
        return result
    paths = _paths(grid)
    forward_len = len(paths["forward"]["cells"])
    backward_len = len(paths["backward"]["cells"])
    if forward_len == backward_len:
        errors.append(
            "the two outward traces tie, so the lesson exposes an arbitrary tie-break rather than the rule"
        )
    chosen = paths["chosen"]
    if len(chosen["cells"]) < 5:
        errors.append("the selected trace must paint at least five cells")
    if not chosen["bounced"] or chosen["turn_index"] is None:
        errors.append("the selected trace must visibly reflect once from the wall")
    else:
        before = chosen["turn_index"]
        after = len(chosen["cells"]) - before
        if before < 2 or after < 2:
            errors.append(
                f"reflection needs at least two painted cells on both legs, got {before} before and {after} after"
            )
    if paths["forward"]["bounced"] and paths["backward"]["bounced"]:
        errors.append("both outward traces bounce; the endpoint selection cue is unnecessarily cluttered")
    if errors:
        return result
    side, orientation, thickness = wall
    profile = f"{orientation}_{paths['chosen_name']}_{len(seed_cells)}"
    if profile not in SCENE_PROFILES:
        errors.append(f"unrecognized semantic profile {profile!r}")
        return result
    output = _copy_grid(grid)
    for r, c in chosen["cells"]:
        output[r][c] = 3
    result.update({
        "wall_side": side,
        "wall_orientation": orientation,
        "wall_thickness": thickness,
        "seed_count": len(seed_cells),
        "slope": "positive" if dc == 1 else "negative",
        "paths": paths,
        "scene_profile": profile,
        "output": output,
        "canonical_signature": _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid)),
    })
    return result


def canonical_profile_signature(grid: Any) -> str | None:
    info = _analysis(grid)
    if info["errors"]:
        return None
    return info["canonical_signature"]


def strict_canonical_like(grid: Any) -> list[str]:
    return list(_analysis(grid)["errors"])


def observe_overrides(grid: Any) -> dict[str, str]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid: Any) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _copy_grid(info["output"])


def _paint_path(grid: Any, cells: Any) -> list[list[int]]:
    output = _copy_grid(grid)
    for r, c in cells:
        output[r][c] = 3
    return output


def _straight_no_bounce(grid: Any) -> list[list[int]]:
    paths = _paths(grid, allow_bounce=False)
    selected = paths["forward"] if len(paths["forward"]["cells"]) >= len(paths["backward"]["cells"]) else paths["backward"]
    return _paint_path(grid, selected["cells"])


def _always_forward(grid: Any) -> list[list[int]]:
    return _paint_path(grid, _paths(grid)["forward"]["cells"])


def _always_backward(grid: Any) -> list[list[int]]:
    return _paint_path(grid, _paths(grid)["backward"]["cells"])


def _requires_two_seeds(grid: Any) -> list[list[int]]:
    seeds = sum(value == 8 for row in grid for value in row)
    return rule_mirror(grid) if seeds == 2 else _copy_grid(grid)


def _requires_three_seeds(grid: Any) -> list[list[int]]:
    seeds = sum(value == 8 for row in grid for value in row)
    return rule_mirror(grid) if seeds == 3 else _copy_grid(grid)


def _witness(expected: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def check(grid: Any) -> bool:
        info = _analysis(grid)
        return not info["errors"] and expected(info)
    return check


SEMANTIC_WITNESSES = {
    "horizontal_wall_bounce": _witness(lambda info: info["wall_orientation"] == "horizontal"),
    "vertical_wall_bounce": _witness(lambda info: info["wall_orientation"] == "vertical"),
    "forward_endpoint_selected": _witness(lambda info: info["paths"]["chosen_name"] == "forward"),
    "backward_endpoint_selected": _witness(lambda info: info["paths"]["chosen_name"] == "backward"),
    "two_seed_line": _witness(lambda info: info["seed_count"] == 2),
    "three_seed_line": _witness(lambda info: info["seed_count"] == 3),
}
SEMANTIC_RIVALS = {
    "straight_no_bounce": _straight_no_bounce,
    "always_forward": _always_forward,
    "always_backward": _always_backward,
    "requires_two_seeds": _requires_two_seeds,
    "requires_three_seeds": _requires_three_seeds,
}
WITNESS_RIVALS = {
    "horizontal_wall_bounce": ["straight_no_bounce"],
    "vertical_wall_bounce": ["straight_no_bounce"],
    "forward_endpoint_selected": ["always_backward"],
    "backward_endpoint_selected": ["always_forward"],
    "two_seed_line": ["requires_three_seeds"],
    "three_seed_line": ["requires_two_seeds"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a named plausible rival survives the demos and changes the query."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        info = _analysis(pair.get("input"))
        if info["errors"]:
            reasons.append(f"demo {index} is malformed: {'; '.join(info['errors'])}")
    query_info = _analysis(query.get("input"))
    if query_info["errors"]:
        reasons.append(f"query is malformed: {'; '.join(query_info['errors'])}")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
            if survives and competitor(query["input"]) != query["output"]:
                reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    del difficulty
    phase = stable_rng(
        seed, f"{TASK_ID}|0|profile_phase", VERSION
    ).randrange(len(SCENE_PROFILES))
    return SCENE_PROFILES[(phase + sample_index) % len(SCENE_PROFILES)]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _size(rng: Any, band: str) -> tuple[int, int]:
    ranges = {
        "easy": (10, 12),
        "medium": (11, 14),
        "hard": (12, 16),
    }
    lo, hi = ranges[band]
    return rng.randint(lo, hi), rng.randint(lo, hi)


def _make_grid(
    h: int,
    w: int,
    side: str,
    thickness: int,
    seed_count: int,
    dc: int,
    r0: int,
    c0: int,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    if side == "top":
        rows, cols = range(thickness), range(w)
    elif side == "bottom":
        rows, cols = range(h - thickness, h), range(w)
    elif side == "left":
        rows, cols = range(h), range(thickness)
    else:
        rows, cols = range(h), range(w - thickness, w)
    for r in rows:
        for c in cols:
            grid[r][c] = 2
    for i in range(seed_count):
        grid[r0 + i][c0 + dc * i] = 8
    return grid


@lru_cache(maxsize=None)
def _candidate_specs(h: int, w: int, profile: str) -> tuple[tuple[Any, ...], ...]:
    orientation, _, seed_count_text = profile.rsplit("_", 2)
    seed_count = int(seed_count_text)
    sides = ("top", "bottom") if orientation == "horizontal" else ("left", "right")
    candidates: list[tuple[Any, ...]] = []
    for side in sides:
        for thickness in range(2, 5):
            if (orientation == "horizontal" and thickness >= h - 3) or (
                orientation == "vertical" and thickness >= w - 3
            ):
                continue
            for dc in (-1, 1):
                for r0 in range(0, h - seed_count + 1):
                    for c0 in range(w):
                        c_last = c0 + dc * (seed_count - 1)
                        if not (0 <= c_last < w):
                            continue
                        grid = _make_grid(h, w, side, thickness, seed_count, dc, r0, c0)
                        info = _analysis(grid)
                        if not info["errors"] and info["scene_profile"] == profile:
                            candidates.append((side, thickness, seed_count, dc, r0, c0))
    return tuple(candidates)


def _general_grid(rng: Any, profile: str, band: str) -> list[list[int]]:
    requested_size = _size(rng, band)
    sizes = [requested_size]
    for delta in range(0, 7):
        for h in range(max(10, requested_size[0] - delta), min(16, requested_size[0] + delta) + 1):
            for w in range(max(10, requested_size[1] - delta), min(16, requested_size[1] + delta) + 1):
                if (h, w) not in sizes:
                    sizes.append((h, w))
    for h, w in sizes:
        specs = _candidate_specs(h, w, profile)
        if specs:
            side, thickness, seed_count, dc, r0, c0 = rng.choice(specs)
            return _make_grid(h, w, side, thickness, seed_count, dc, r0, c0)
    raise RuntimeError(f"no lawful construction for profile={profile!r}, requested_size={requested_size}")


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested is None:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = ctx.draw_choice("scene_profile", (scheduled,))
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    matching_public = [
        grid for grid in _PUBLIC_GRIDS
        if observe_overrides(grid)["scene_profile"] == profile
    ]
    if matching_public and ctx.draw_rng("canonical_prior").random() < 0.60:
        grid = _copy_grid(ctx.draw_rng("canonical_choice").choice(matching_public))
    else:
        grid = _general_grid(ctx.draw_rng("layout"), profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = sorted(set(overrides) - set(AXES))
        if unknown:
            errors.append(f"unknown override(s): {', '.join(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(
                f"requested scene_profile {requested!r}, observed {info['scene_profile']!r}"
            )
    return errors
