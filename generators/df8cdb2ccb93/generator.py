"""Generate lessons for growing blue crosses from isolated red seeds.

The authoritative rule keeps every red cell and paints each in-bounds blank
orthogonal neighbour blue.  The ordinary eight-slot schedule alternates exact
canonical linked profiles with boundary-plus-shared-arm controls.  Every three
consecutive demonstrations therefore contains a scene that simultaneously
refutes ``skip boundary seeds`` and ``skip shared arm cells`` shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "df8cdb2ccb93"
TASK_ID = "df8cdb2ccb93"
VERSION = "2.0.0"
RULE_HASH = "036ea461f9e6"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Keep every red seed and paint each in-bounds blank orthogonal neighbour "
    "blue. Lessons include interior, clipped-edge, and shared-arm layouts; "
    "the latter two co-occur often enough to make every three-demo window "
    "identify the local four-neighbour rule."
)

INVARIANTS = [
    "the input palette is exactly background 0 and red seed colour 2",
    "there are 2..4 red seeds on a 7..10 by 7..10 grid",
    "red seeds are never orthogonally adjacent",
    "ordinary layouts are interior, one-edge-seed, or one-edge-seed plus exactly one shared arm",
    "the output preserves red centers and changes only blank orthogonal neighbours to blue 1",
]

LAYOUT_KINDS = ("interior", "edge", "boundary_shared")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "eight-slot linked schedule", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "eight-slot linked schedule", "valid": "7..10"},
    "seeds": {"type": "int", "default": "eight-slot linked schedule", "valid": "2..4"},
    "layout_kind": {
        "type": "enum",
        "default": "eight-slot interior/edge/boundary_shared schedule",
        "valid": LAYOUT_KINDS,
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"layout_kind": "boundary_shared", "seeds": 2},
]

# Four of eight ordinary slots use the exact linked canonical
# (height, width, seed-count, boundary/shared-arm class) profiles.
MIN_STRICT_FRAC = 0.45
SCHEDULE_PROFILES = tuple(range(8))
_CANONICAL_LINKED_PROFILES = frozenset(
    {
        (7, 7, 2, "interior"),
        (8, 9, 3, "interior"),
        (9, 9, 3, "edge"),
        (8, 8, 2, "interior"),
    }
)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Expose the deterministic eight-slot curriculum schedule."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _incompatible(message: str, *axes: str) -> ValueError:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    return exc


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "seeds"):
        value = overrides.get(label)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{label} must be an integer")
    value = overrides.get("layout_kind")
    if value is not None and type(value) is not str:
        raise ValueError("layout_kind must be a string")
    if overrides.get("layout_kind") == "boundary_shared" and overrides.get("seeds") == 2:
        raise _incompatible(
            "boundary_shared requires at least three seeds",
            "layout_kind",
            "seeds",
        )


def _draw_exact_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _draw_exact_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_defaults(profile: int, difficulty: Any) -> dict[str, int | str]:
    canonical = {
        0: (7, 7, 2, "interior"),
        3: (9, 9, 3, "edge"),
        4: (8, 8, 2, "interior"),
        7: (8, 9, 3, "interior"),
    }
    if profile in canonical:
        h, w, seeds, layout = canonical[profile]
        return {"grid_h": h, "grid_w": w, "seeds": seeds, "layout_kind": layout}

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    table = {
        "easy": {
            1: (7, 8, 3, "boundary_shared"),
            2: (8, 7, 4, "boundary_shared"),
            5: (8, 8, 3, "boundary_shared"),
            6: (7, 9, 4, "boundary_shared"),
        },
        "medium": {
            1: (8, 9, 3, "boundary_shared"),
            2: (9, 8, 4, "boundary_shared"),
            5: (9, 9, 3, "boundary_shared"),
            6: (8, 10, 4, "boundary_shared"),
        },
        "hard": {
            1: (9, 10, 3, "boundary_shared"),
            2: (10, 9, 4, "boundary_shared"),
            5: (10, 10, 3, "boundary_shared"),
            6: (9, 9, 4, "boundary_shared"),
        },
    }
    h, w, seeds, layout = table[band][profile]
    return {"grid_h": h, "grid_w": w, "seeds": seeds, "layout_kind": layout}


def _is_boundary(cell: tuple[int, int], h: int, w: int) -> bool:
    r, c = cell
    return r in (0, h - 1) or c in (0, w - 1)


def _is_corner(cell: tuple[int, int], h: int, w: int) -> bool:
    r, c = cell
    return r in (0, h - 1) and c in (0, w - 1)


def _shared_midpoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int] | None:
    ar, ac = a
    br, bc = b
    if ar == br and abs(ac - bc) == 2:
        return ar, (ac + bc) // 2
    if ac == bc and abs(ar - br) == 2:
        return (ar + br) // 2, ac
    return None


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _seed_facts(grid: list[list[int]]) -> dict[str, Any]:
    h = len(grid)
    w = len(grid[0]) if grid else 0
    seeds = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
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
    )

    layout_kind = "invalid"
    if not adjacent and not corners:
        if not boundary and not shared:
            layout_kind = "interior"
        elif len(boundary) == 1 and not shared:
            layout_kind = "edge"
        elif (
            len(boundary) == 1
            and len(shared) == 1
            and not _is_boundary(shared[0][0], h, w)
            and not _is_boundary(shared[0][1], h, w)
        ):
            layout_kind = "boundary_shared"

    return {
        "grid_h": h,
        "grid_w": w,
        "seeds": seeds,
        "seed_count": len(seeds),
        "boundary": boundary,
        "corners": corners,
        "adjacent": adjacent,
        "shared": shared,
        "layout_kind": layout_kind,
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
    if not 7 <= h <= 10 or not 7 <= width <= 10:
        errors.append(f"grid dimensions {h}x{width} outside supported 7..10")
    values = {value for row in grid for value in row}
    if not values <= {0, 2}:
        errors.append(f"input may contain only background 0 and red seeds 2; found {sorted(values)}")

    facts = _seed_facts(grid)
    if not 2 <= facts["seed_count"] <= 4:
        errors.append(f"expected 2..4 red seeds; found {facts['seed_count']}")
    if facts["adjacent"]:
        errors.append("red seeds may not be orthogonally adjacent")
    if facts["corners"]:
        errors.append("corner seeds are outside the supported teaching grammar")
    if len(facts["boundary"]) > 1:
        errors.append("at most one red seed may lie on the boundary")
    if len(facts["shared"]) > 1:
        errors.append("at most one pair may share an orthogonal arm cell")
    if facts["layout_kind"] == "invalid":
        errors.append("seed geometry is not interior, edge, or boundary_shared")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    facts = _seed_facts(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "seeds": facts["seed_count"],
        "layout_kind": facts["layout_kind"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Match the exact linked dimension/count/layout profiles in all canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = observe_overrides(grid)
    linked = (facts["grid_h"], facts["grid_w"], facts["seeds"], facts["layout_kind"])
    if linked not in _CANONICAL_LINKED_PROFILES:
        reasons.append(
            "linked (height, width, seed-count, layout) profile is outside the four canonical inputs"
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
    selected = list(existing)
    for cell in cells:
        if all(_manhattan(cell, other) >= 3 for other in selected):
            selected.append(cell)
            if len(selected) == len(tuple(existing)) + count:
                return selected[-count:]
    raise ValueError("could not place the requested number of separated seeds")


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
    raise ValueError("could not place one boundary seed plus separated interior seeds")


def _place_boundary_shared(rng, h: int, w: int, count: int) -> list[tuple[int, int]]:
    if count < 3:
        raise _incompatible(
            "boundary_shared requires at least three seeds",
            "layout_kind",
            "seeds",
        )
    shared_pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if c + 2 < w - 1:
                shared_pairs.append(((r, c), (r, c + 2)))
            if r + 2 < h - 1:
                shared_pairs.append(((r, c), (r + 2, c)))
    rng.shuffle(shared_pairs)

    edge = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if _is_boundary((r, c), h, w) and not _is_corner((r, c), h, w)
    ]
    rng.shuffle(edge)
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]

    for first, second in shared_pairs:
        for boundary_seed in edge:
            if _manhattan(boundary_seed, first) < 3 or _manhattan(boundary_seed, second) < 3:
                continue
            selected = [boundary_seed, first, second]
            if count == 3:
                return selected
            try:
                extra = _choose_spaced(rng, interior, count - 3, selected)
            except ValueError:
                continue
            return [*selected, *extra]
    raise ValueError("could not place boundary_shared seed geometry")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = _scheduled_defaults(profile, difficulty)

    # Single-axis overrides remain useful even when their scheduled partner is
    # incompatible; only an explicitly requested incompatible pair is rejected.
    if overrides.get("layout_kind") == "boundary_shared" and "seeds" not in overrides:
        scheduled["seeds"] = max(3, int(scheduled["seeds"]))
    if overrides.get("seeds") == 2 and "layout_kind" not in overrides:
        scheduled["layout_kind"] = "interior"

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_exact_int(ctx, "grid_h", 7, 10, int(scheduled["grid_h"]))
    w = _draw_exact_int(ctx, "grid_w", 7, 10, int(scheduled["grid_w"]))
    count = _draw_exact_int(ctx, "seeds", 2, 4, int(scheduled["seeds"]))
    layout = _draw_exact_choice(
        ctx,
        "layout_kind",
        LAYOUT_KINDS,
        str(scheduled["layout_kind"]),
    )
    if layout == "boundary_shared" and count < 3:
        raise _incompatible(
            "boundary_shared requires at least three seeds",
            "layout_kind",
            "seeds",
        )

    rng = ctx.draw_rng("layout")
    if layout == "interior":
        seeds = _place_interior(rng, h, w, count)
    elif layout == "edge":
        seeds = _place_edge(rng, h, w, count)
    else:
        seeds = _place_boundary_shared(rng, h, w, count)

    grid = full_grid(h, w, 0)
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
                output[rr][cc] = 1
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
                    output[r][cc] = 1
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
                    output[rr][c] = 1
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
                    output[rr][cc] = 1
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
                output[rr][cc] = 1
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "skip_boundary_seeds": _rival_skip_boundary_seeds,
    "skip_shared_arm": _rival_skip_shared_arm,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"skip_shared_arm": _rival_skip_shared_arm}


def _differs_from(rival: Callable[[list[list[int]]], list[list[int]]]):
    return lambda grid: not self_check(grid) and rule_mirror(grid) != rival(grid)


SEMANTIC_WITNESSES = {
    "horizontal_arms": _differs_from(_rival_vertical_only),
    "vertical_arms": _differs_from(_rival_horizontal_only),
    "boundary_clipping": _differs_from(_rival_skip_boundary_seeds),
    "shared_arm_cell": _differs_from(_rival_skip_shared_arm),
}
WITNESS_RIVALS = {
    "horizontal_arms": ["vertical_only"],
    "vertical_arms": ["horizontal_only"],
    "boundary_clipping": ["skip_boundary_seeds"],
    "shared_arm_cell": ["skip_shared_arm"],
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
