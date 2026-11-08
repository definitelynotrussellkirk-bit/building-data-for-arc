"""Generate identifiable lessons for painting magenta orthogonal halos.

The authoritative rule keeps every red(2) cell and paints each in-bounds blank
orthogonal neighbour magenta(6).  Non-blank neighbours are preserved.  The
ordinary four-slot schedule is ``anchor / combined_controls /
combined_controls / anchor`` so every three-demo window contains a scene that
simultaneously exposes clipping, shared-arm, adjacent-seed, no-overwrite, and
non-red-decoy behavior.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ba9f2a08016"
TASK_ID = "1ba9f2a08016"
VERSION = "3.0.1"
RULE_HASH = "814d01ffdbb0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Keep every red(2) seed. Paint each in-bounds blank orthogonal neighbour "
    "magenta(6), while preserving red seeds and every other non-zero cell. "
    "Lessons mix canonical-scale interior/edge/corner anchors with combined "
    "controls containing boundary clipping, adjacent seeds, a shared arm, a "
    "blocked neighbour, and a remote non-red decoy."
)

INVARIANTS = [
    "inputs are rectangular 6..10 by 6..10 ARC grids",
    "every input has exactly 3 or 4 red(2) seeds",
    "ordinary scene_profile is interior, edge, corner, or combined_controls",
    "clean profiles contain only background 0 and red seeds 2",
    "combined_controls has one corner chain, a shared blank arm, one blocked neighbour, and one remote non-red decoy",
    "the output changes only blank orthogonal neighbours of red seeds to magenta 6",
]

SCENE_PROFILES = ("interior", "edge", "corner", "combined_controls")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "four-slot linked schedule", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "four-slot linked schedule", "valid": "6..10"},
    "n_seeds": {"type": "int", "default": "four-slot linked schedule", "valid": "3..4"},
    "scene_profile": {
        "type": "enum",
        "default": "anchor / combined_controls / combined_controls / anchor",
        "valid": SCENE_PROFILES,
    },
}

# Two of four ordinary slots are exact linked canonical profiles.
MIN_STRICT_FRAC = 0.45
SCHEDULE_PROFILES = tuple(range(4))
_CANONICAL_LINKED_PROFILES = frozenset(
    {
        (6, 6, 3, "corner"),
        (7, 7, 3, "interior"),
        (8, 8, 4, "edge"),
    }
)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NONRED_COLORS = (1, 3, 4, 5, 7, 8, 9)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Expose the deterministic four-slot curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_nonnegative_exact_integer(value: Any, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative exact integer")


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _validate_nonnegative_exact_integer(seed, "seed")
    _validate_nonnegative_exact_integer(sample_index, "sample_index")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "n_seeds"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    value = overrides.get("scene_profile")
    if value is not None and type(value) is not str:
        raise ValueError("scene_profile must be a string")


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(profile: int, difficulty: Any) -> dict[str, int | str]:
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    anchors = {
        "easy": ((6, 6, 3, "corner"), (7, 7, 3, "interior")),
        "medium": ((7, 7, 3, "interior"), (8, 8, 4, "edge")),
        "hard": ((8, 8, 4, "edge"), (6, 6, 3, "corner")),
    }
    controls = {
        "easy": (6, 7, 3, "combined_controls"),
        "medium": (8, 8, 4, "combined_controls"),
        "hard": (10, 9, 4, "combined_controls"),
    }
    if profile == 0:
        h, w, count, scene = anchors[band][0]
    elif profile == 3:
        h, w, count, scene = anchors[band][1]
    else:
        h, w, count, scene = controls[band]
    return {"grid_h": h, "grid_w": w, "n_seeds": count, "scene_profile": scene}


def _is_boundary(cell: tuple[int, int], h: int, w: int) -> bool:
    r, c = cell
    return r in (0, h - 1) or c in (0, w - 1)


def _is_corner(cell: tuple[int, int], h: int, w: int) -> bool:
    r, c = cell
    return r in (0, h - 1) and c in (0, w - 1)


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _shared_midpoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int] | None:
    ar, ac = a
    br, bc = b
    if ar == br and abs(ac - bc) == 2:
        return ar, (ac + bc) // 2
    if ac == bc and abs(ar - br) == 2:
        return (ar + br) // 2, ac
    return None


def _seed_facts(grid: list[list[int]]) -> dict[str, Any]:
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seeds = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    )
    others = tuple(
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    )
    boundary = tuple(cell for cell in seeds if _is_boundary(cell, h, w))
    corners = tuple(cell for cell in seeds if _is_corner(cell, h, w))
    adjacent = tuple(
        (a, b)
        for index, a in enumerate(seeds)
        for b in seeds[index + 1 :]
        if _manhattan(a, b) == 1
    )
    shared = tuple(
        (a, b, midpoint)
        for index, a in enumerate(seeds)
        for b in seeds[index + 1 :]
        if (midpoint := _shared_midpoint(a, b)) is not None
        and grid[midpoint[0]][midpoint[1]] == 0
    )
    adjacent_other = tuple(
        item
        for item in others
        if any(_manhattan((item[0], item[1]), seed) == 1 for seed in seeds)
    )
    remote_other = tuple(item for item in others if item not in adjacent_other)

    scene_profile = "invalid"
    if not others and not adjacent and not shared:
        if not boundary:
            scene_profile = "interior"
        elif len(boundary) == 1 and len(corners) == 0:
            scene_profile = "edge"
        elif len(boundary) == 1 and len(corners) == 1:
            scene_profile = "corner"
    elif (
        len(others) == 2
        and len(adjacent_other) == 1
        and len(remote_other) == 1
        and len(corners) == 1
        and adjacent
        and shared
    ):
        scene_profile = "combined_controls"

    return {
        "grid_h": h,
        "grid_w": w,
        "seeds": seeds,
        "seed_count": len(seeds),
        "others": others,
        "boundary": boundary,
        "corners": corners,
        "adjacent": adjacent,
        "shared": shared,
        "adjacent_other": adjacent_other,
        "remote_other": remote_other,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the supported lesson grammar and reject rule-hiding scenes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid value"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colours 0..9"]

    errors: list[str] = []
    h = len(grid)
    if not 6 <= h <= 10 or not 6 <= width <= 10:
        errors.append(f"grid dimensions {h}x{width} outside supported 6..10")
    if any(value == 6 for row in grid for value in row):
        errors.append("input may not contain output colour 6")

    facts = _seed_facts(grid)
    if not 3 <= facts["seed_count"] <= 4:
        errors.append(f"expected 3..4 red seeds; found {facts['seed_count']}")
    if facts["scene_profile"] == "invalid":
        errors.append(
            "scene must be a clean interior/edge/corner profile or the exact combined_controls grammar"
        )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = _seed_facts(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_seeds": facts["seed_count"],
        "scene_profile": facts["scene_profile"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Match the exact linked dimension/count/geometry profiles in canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = observe_overrides(grid)
    linked = (
        facts["grid_h"],
        facts["grid_w"],
        facts["n_seeds"],
        facts["scene_profile"],
    )
    if linked not in _CANONICAL_LINKED_PROFILES:
        reasons.append(
            "linked (height, width, seed-count, scene-profile) is outside the three canonical inputs"
        )
    return reasons


def _choose_spaced(
    rng,
    candidates: Iterable[tuple[int, int]],
    count: int,
    existing: Iterable[tuple[int, int]] = (),
) -> list[tuple[int, int]]:
    cells = list(candidates)
    rng.shuffle(cells)
    base = list(existing)

    def search(start: int, chosen: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return chosen
        for index in range(start, len(cells)):
            cell = cells[index]
            if all(_manhattan(cell, other) >= 3 for other in (*base, *chosen)):
                found = search(index + 1, [*chosen, cell])
                if found is not None:
                    return found
        return None

    result = search(0, [])
    if result is None:
        raise ValueError("could not place the requested separated seeds")
    return result


def _place_interior(rng, h: int, w: int, count: int) -> list[tuple[int, int]]:
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    return _choose_spaced(rng, candidates, count)


def _place_edge(rng, h: int, w: int, count: int) -> list[tuple[int, int]]:
    edge = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if _is_boundary((r, c), h, w) and not _is_corner((r, c), h, w)
    ]
    rng.shuffle(edge)
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for boundary_seed in edge:
        try:
            rest = _choose_spaced(rng, interior, count - 1, (boundary_seed,))
        except ValueError:
            continue
        return [boundary_seed, *rest]
    raise ValueError("could not place one edge seed plus separated interior seeds")


def _place_corner(rng, h: int, w: int, count: int) -> list[tuple[int, int]]:
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    rng.shuffle(corners)
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for corner in corners:
        try:
            rest = _choose_spaced(rng, interior, count - 1, (corner,))
        except ValueError:
            continue
        return [corner, *rest]
    raise ValueError("could not place one corner seed plus separated interior seeds")


def _combined_layout(
    rng, h: int, w: int, count: int
) -> tuple[list[tuple[int, int]], tuple[int, int], tuple[int, int]]:
    # Each orientation is (corner, direction along one boundary, inward normal).
    orientations = [
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (0, 1)),
        ((0, w - 1), (0, -1), (1, 0)),
        ((0, w - 1), (1, 0), (0, -1)),
        ((h - 1, 0), (0, 1), (-1, 0)),
        ((h - 1, 0), (-1, 0), (0, 1)),
        ((h - 1, w - 1), (0, -1), (-1, 0)),
        ((h - 1, w - 1), (-1, 0), (0, -1)),
    ]
    rng.shuffle(orientations)
    for corner, direction, inward in orientations:
        cr, cc = corner
        dr, dc = direction
        seeds = [corner, (cr + dr, cc + dc), (cr + 3 * dr, cc + 3 * dc)]
        blocker = (seeds[2][0] + inward[0], seeds[2][1] + inward[1])
        if not (0 <= blocker[0] < h and 0 <= blocker[1] < w):
            continue
        if count == 4:
            candidates = [
                (r, c)
                for r in range(1, h - 1)
                for c in range(1, w - 1)
                if (r, c) != blocker
                and all(_manhattan((r, c), seed) >= 3 for seed in seeds)
            ]
            rng.shuffle(candidates)
            if not candidates:
                continue
            seeds.append(candidates[0])

        remote = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if (r, c) not in seeds
            and (r, c) != blocker
            and all(_manhattan((r, c), seed) >= 2 for seed in seeds)
        ]
        rng.shuffle(remote)
        if remote:
            return seeds, blocker, remote[0]
    raise ValueError("could not place combined_controls geometry")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = _scheduled_defaults(profile, difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, "grid_h", 6, 10, int(scheduled["grid_h"]))
    w = _draw_exact_int(ctx, "grid_w", 6, 10, int(scheduled["grid_w"]))
    count = _draw_exact_int(ctx, "n_seeds", 3, 4, int(scheduled["n_seeds"]))
    scene = _draw_exact_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        str(scheduled["scene_profile"]),
    )

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    if scene == "interior":
        seeds = _place_interior(rng, h, w, count)
    elif scene == "edge":
        seeds = _place_edge(rng, h, w, count)
    elif scene == "corner":
        seeds = _place_corner(rng, h, w, count)
    else:
        seeds, blocker, remote = _combined_layout(rng, h, w, count)
        colors = list(_NONRED_COLORS)
        rng.shuffle(colors)
        grid[blocker[0]][blocker[1]] = colors[0]
        grid[remote[0]][remote[1]] = colors[1]

    for r, c in seeds:
        grid[r][c] = 2
    return grid


def rule_mirror(grid):
    """Independent Python mirror; canonical Racket remains output authority."""
    output = [list(row) for row in grid]
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    for r, c in seeds:
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < len(output) and 0 <= cc < len(output[0]) and output[rr][cc] == 0:
                output[rr][cc] = 6
    return output


def _rival_horizontal_only(grid):
    output = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            for dc in (-1, 1):
                cc = c + dc
                if 0 <= cc < len(row) and output[r][cc] == 0:
                    output[r][cc] = 6
    return output


def _rival_vertical_only(grid):
    output = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            for dr in (-1, 1):
                rr = r + dr
                if 0 <= rr < len(grid) and output[rr][c] == 0:
                    output[rr][c] = 6
    return output


def _rival_skip_boundary_seeds(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2 or _is_boundary((r, c), h, w):
                continue
            for dr, dc in _CARDINALS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and output[rr][cc] == 0:
                    output[rr][cc] = 6
    return output


def _rival_skip_shared_arm(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    seeds = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    for r, c in seeds:
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or output[rr][cc] != 0:
                continue
            touching = sum((rr + ddr, cc + ddc) in seeds for ddr, ddc in _CARDINALS)
            if touching == 1:
                output[rr][cc] = 6
    return output


def _rival_overwrite_nonzero(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            for dr, dc in _CARDINALS:
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w:
                    output[rr][cc] = 6
    return output


def _rival_all_nonzero_beacons(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    beacons = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    for r, c in beacons:
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and output[rr][cc] == 0:
                output[rr][cc] = 6
    return output


def _rival_eight_neighbors(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and output[rr][cc] == 0:
                        output[rr][cc] = 6
    return output


def _rival_first_seed_only(grid):
    output = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if seeds:
        r, c = seeds[0]
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and output[rr][cc] == 0:
                output[rr][cc] = 6
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "skip_boundary_seeds": _rival_skip_boundary_seeds,
    "skip_shared_arm": _rival_skip_shared_arm,
    "overwrite_nonzero": _rival_overwrite_nonzero,
    "all_nonzero_beacons": _rival_all_nonzero_beacons,
    "eight_neighbors": _rival_eight_neighbors,
    "first_seed_only": _rival_first_seed_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "skip_shared_arm": _rival_skip_shared_arm,
    "overwrite_nonzero": _rival_overwrite_nonzero,
    "all_nonzero_beacons": _rival_all_nonzero_beacons,
}


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    return lambda grid: not self_check(grid) and rule_mirror(grid) != rival(grid)


SEMANTIC_WITNESSES = {
    "horizontal_arms": _differs_from(_rival_vertical_only),
    "vertical_arms": _differs_from(_rival_horizontal_only),
    "boundary_clipping": _differs_from(_rival_skip_boundary_seeds),
    "shared_arm_cell": _differs_from(_rival_skip_shared_arm),
    "preserve_nonzero_neighbor": _differs_from(_rival_overwrite_nonzero),
    "ignore_nonred_decoys": _differs_from(_rival_all_nonzero_beacons),
    "orthogonal_not_diagonal": _differs_from(_rival_eight_neighbors),
    "every_red_seed": _differs_from(_rival_first_seed_only),
}
WITNESS_RIVALS = {
    "horizontal_arms": ["vertical_only"],
    "vertical_arms": ["horizontal_only"],
    "boundary_clipping": ["skip_boundary_seeds"],
    "shared_arm_cell": ["skip_shared_arm"],
    "preserve_nonzero_neighbor": ["overwrite_nonzero"],
    "ignore_nonred_decoys": ["all_nonzero_beacons"],
    "orthogonal_not_diagonal": ["eight_neighbors"],
    "every_red_seed": ["first_seed_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is malformed: {'; '.join(errors)}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the rule")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append("query is malformed: " + "; ".join(errors))
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output does not match the rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons
