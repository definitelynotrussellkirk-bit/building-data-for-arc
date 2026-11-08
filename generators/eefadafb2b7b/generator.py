"""Adversarial curriculum generator for ARC task 239be575 / eefadafb2b7b.

The authoritative rule returns ``[[8]]`` exactly when one 8-connected cyan
component touches the one-cell ring around each of the two red 2x2 blocks;
otherwise it returns ``[[0]]``.

The public examples leave two especially plausible shortcuts unfalsified:
4-connectivity and component-bounding-box overlap.  Ordinary examples are
therefore scheduled as four constructive lesson profiles.  Every consecutive
four-example window contains a direct counterexample to those shortcuts plus
counterexamples to "any cyan touches each block" and "only inspect the largest
cyan component".  Noise is added only when it preserves the selected semantic
profile; no output branch is manufactured by deleting an accidental bridge.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from numbers import Real
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "eefadafb2b7b"
TASK_ID = "eefadafb2b7b"
VERSION = "3.0.0"
RULE_HASH = "1d44fc0f4360"
EXPECTED_OUTPUT_CODOMAIN = 2

SUMMARY = (
    "Two exact red 2x2 blocks in canonical-scale noisy cyan scenes. Return 8 "
    "iff one 8-connected cyan component touches both block rings, else 0. "
    "A four-profile cyclic curriculum constructively refutes 4-connectivity, "
    "bounding-box, any-contact, and largest-component shortcuts."
)

INVARIANTS = [
    "grid uses only background 0, red 2, and cyan 8",
    "exactly two non-overlapping red 2x2 blocks and exactly eight red cells",
    "cyan cells touch the ring of each block somewhere",
    "the selected lesson_profile is recoverable from the returned grid",
    "every four consecutive default examples contain all decisive profiles",
]

LESSON_PROFILES = (
    "diagonal_bridge",
    "bbox_decoy",
    "small_bridge",
    "split_contacts",
)
SCHEDULE_PROFILES = LESSON_PROFILES
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_CANONICAL_DIMS = ((5, 5), (5, 7), (6, 6), (6, 7), (8, 6))
_ALLOWED_OVERRIDES = frozenset(("grid_h", "grid_w", "lesson_profile"))
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule",
        "valid": "5..7",
    },
    "lesson_profile": {
        "type": "str",
        "default": "cyclic adversarial schedule",
        "valid": "diagonal_bridge|bbox_decoy|small_bridge|split_contacts",
    },
}

# Five-by-five constructive cores.  Red blocks occupy opposite corners at
# (0,0) and (3,3); coordinates listed here are cyan.  The whole core is then
# reflected/transposed and embedded in the selected canvas.
_CORE_CYAN = {
    # A single 8-connected path touches both rings, but its two cells are only
    # diagonally adjacent.  Four-connectivity therefore predicts 0.
    "diagonal_bridge": {(2, 1), (3, 2)},
    # No cyan component touches both rings.  One component's bounding box does,
    # because the missing (2,2) corner lies in the overlap of the two rings.
    "bbox_decoy": {(2, 0), (2, 1), (1, 2), (0, 2), (4, 2)},
    # A three-cell bridge exists, while a separate four-cell decoy is larger.
    "small_bridge": {(2, 1), (2, 2), (3, 2), (0, 2), (0, 3), (0, 4), (1, 4)},
    # Different components touch the two rings; no single component bridges.
    "split_contacts": {(0, 2), (0, 3), (4, 2)},
}


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))


def _validate_request(seed, sample_index, difficulty, overrides: dict) -> None:
    """Reject malformed scalars before permissive RNG helpers can coerce them."""
    if type(seed) is not int:
        raise ValueError("seed must be a plain Python int (bool is not accepted)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative plain Python int")
    if difficulty is not None and (
        type(difficulty) is not str
        or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )

    _validate_override_keys(overrides)
    integer_bounds = {"grid_h": (5, 8), "grid_w": (5, 7)}
    for name, (lo, hi) in integer_bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be a plain Python int")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} is outside [{lo}, {hi}]")

    profile = overrides.get("lesson_profile")
    if profile is not None and (
        type(profile) is not str or profile not in LESSON_PROFILES
    ):
        raise ValueError(
            f"lesson_profile must be one of {LESSON_PROFILES}, got {profile!r}"
        )


def _rectangular_grid_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list"
    if not isinstance(grid[0], list) or not grid[0]:
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _blocks(grid) -> list[tuple[int, int]]:
    """Top-left coordinates of exact 2x2 all-red windows, row-major."""
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if all(grid[r + dr][c + dc] == 2 for dr in (0, 1) for dc in (0, 1))
    ]


def _touches(cell: tuple[int, int], block: tuple[int, int]) -> bool:
    r, c = cell
    br, bc = block
    return (
        br - 1 <= r <= br + 2
        and bc - 1 <= c <= bc + 2
        and not (br <= r <= br + 1 and bc <= c <= bc + 1)
    )


def _cyan_components(grid, *, connectivity: int = 8) -> list[frozenset[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    if connectivity == 8:
        steps = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    elif connectivity == 4:
        steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    else:
        raise ValueError("connectivity must be 4 or 8")

    seen: set[tuple[int, int]] = set()
    components: list[frozenset[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while queue:
                cell = queue.popleft()
                cells.add(cell)
                for dr, dc in steps:
                    nxt = (cell[0] + dr, cell[1] + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == 8
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            components.append(frozenset(cells))
    return components


def _component_touches_both(
    component: Iterable[tuple[int, int]], blocks: list[tuple[int, int]]
) -> bool:
    return len(blocks) >= 2 and all(
        any(_touches(cell, block) for cell in component) for block in blocks[:2]
    )


def _has_bridge(grid, *, connectivity: int = 8) -> bool:
    blocks = _blocks(grid)
    if len(blocks) != 2:
        return False
    return any(
        _component_touches_both(component, blocks)
        for component in _cyan_components(grid, connectivity=connectivity)
    )


def _bbox_spans_both_rings(grid) -> bool:
    blocks = _blocks(grid)
    if len(blocks) != 2:
        return False
    for component in _cyan_components(grid, connectivity=8):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        bbox = (
            (r, c)
            for r in range(min(rows), max(rows) + 1)
            for c in range(min(cols), max(cols) + 1)
        )
        cells = tuple(bbox)
        if all(any(_touches(cell, block) for cell in cells) for block in blocks):
            return True
    return False


def _both_rings_have_any_cyan(grid) -> bool:
    blocks = _blocks(grid)
    if len(blocks) != 2:
        return False
    cyan = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    return all(any(_touches(cell, block) for cell in cyan) for block in blocks)


def _largest_component_bridges(grid) -> bool:
    blocks = _blocks(grid)
    components = _cyan_components(grid, connectivity=8)
    if len(blocks) != 2 or not components:
        return False
    largest_size = max(map(len, components))
    # A tie is treated charitably for the rival: if any largest component is a
    # bridge, the shortcut may return 8.  Our witness therefore has a strictly
    # larger non-bridge distractor, not an order-dependent tie.
    return any(
        len(component) == largest_size
        and _component_touches_both(component, blocks)
        for component in components
    )


def rule_mirror(grid) -> list[list[int]]:
    """Python diagnostic mirror of the selected canonical Racket rule."""
    return [[8 if _has_bridge(grid, connectivity=8) else 0]]


def _rival_four_connected_bridge(grid) -> list[list[int]]:
    return [[8 if _has_bridge(grid, connectivity=4) else 0]]


def _rival_bounding_box_bridge(grid) -> list[list[int]]:
    return [[8 if _bbox_spans_both_rings(grid) else 0]]


def _rival_any_ring_contacts(grid) -> list[list[int]]:
    return [[8 if _both_rings_have_any_cyan(grid) else 0]]


def _rival_largest_component_bridge(grid) -> list[list[int]]:
    return [[8 if _largest_component_bridges(grid) else 0]]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "four_connected_bridge": _rival_four_connected_bridge,
    "bounding_box_bridge": _rival_bounding_box_bridge,
    "any_ring_contacts": _rival_any_ring_contacts,
    "largest_component_bridge": _rival_largest_component_bridge,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "four_connected_bridge": _rival_four_connected_bridge,
    "bounding_box_bridge": _rival_bounding_box_bridge,
}


def _classify_lesson_profile(grid) -> str | None:
    bridge8 = _has_bridge(grid, connectivity=8)
    bridge4 = _has_bridge(grid, connectivity=4)
    if bridge8 and not bridge4:
        return "diagonal_bridge"
    if not bridge8 and _bbox_spans_both_rings(grid):
        return "bbox_decoy"
    if bridge8 and bridge4 and not _largest_component_bridges(grid):
        return "small_bridge"
    if (
        not bridge8
        and not _bbox_spans_both_rings(grid)
        and _both_rings_have_any_cyan(grid)
    ):
        return "split_contacts"
    return None


def observe_overrides(grid) -> dict[str, int | str]:
    error = _rectangular_grid_error(grid)
    if error:
        raise ValueError(error)
    profile = _classify_lesson_profile(grid)
    if profile is None:
        raise ValueError("grid does not realize a declared lesson_profile")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "lesson_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the public task grammar without requiring a teaching profile."""
    del difficulty, meta
    error = _rectangular_grid_error(grid)
    if error:
        return [error]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (5 <= h <= 8 and 5 <= w <= 7):
        errors.append(f"grid dimensions {h}x{w} are outside canonical envelope")
    invalid = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or value not in (0, 2, 8)
        },
        key=repr,
    )
    if invalid:
        errors.append(f"unexpected cell values: {invalid}")
        return errors

    red_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }
    blocks = _blocks(grid)
    if len(red_cells) != 8:
        errors.append(f"expected exactly eight red cells, found {len(red_cells)}")
    if len(blocks) != 2:
        errors.append(f"expected exactly two red 2x2 blocks, found {len(blocks)}")
    if len(blocks) == 2:
        expected_red = {
            (br + dr, bc + dc)
            for br, bc in blocks
            for dr in (0, 1)
            for dc in (0, 1)
        }
        if red_cells != expected_red:
            errors.append("red cells are not exactly the two detected 2x2 blocks")
    if not any(value == 8 for row in grid for value in row):
        errors.append("at least one cyan cell is required")
    elif len(blocks) == 2 and not _both_rings_have_any_cyan(grid):
        errors.append("cyan must visibly contact each red block ring")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public envelope and exact three-color grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 8}:
        return [f"expected exact public palette {{0, 2, 8}}, found {sorted(palette)}"]
    return []


def canonical_profile_signature(grid) -> tuple[int, int, int]:
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def semantic_signature(grid) -> dict[str, object]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = _cyan_components(grid, connectivity=8)
    return {
        **observe_overrides(grid),
        "output": rule_mirror(grid)[0][0],
        "cyan_components_8": len(components),
        "cyan_cells": sum(map(len, components)),
        "bridge_4": _has_bridge(grid, connectivity=4),
        "bridge_8": _has_bridge(grid, connectivity=8),
        "bbox_bridge": _bbox_spans_both_rings(grid),
        "largest_component_bridge": _largest_component_bridges(grid),
    }


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return LESSON_PROFILES[int(sample_index) % len(LESSON_PROFILES)]


def _anchor_dims(seed: int, sample_index: int) -> tuple[int, int]:
    # Stable arithmetic only; no process-randomized hash().
    index = (abs(int(seed)) * 7 + int(sample_index)) % len(_CANONICAL_DIMS)
    return _CANONICAL_DIMS[index]


def _draw_axis(ctx, name: str, lo: int, hi: int, default: int, overrides: dict) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_profile(ctx, seed: int, sample_index: int, difficulty, overrides: dict) -> str:
    if overrides.get("lesson_profile") is not None:
        return str(ctx.draw_choice("lesson_profile", LESSON_PROFILES))
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return str(ctx.draw_choice("lesson_profile", (scheduled,)))


def _transform_core(
    red: set[tuple[int, int]],
    cyan: set[tuple[int, int]],
    rng,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    def transform(cell: tuple[int, int]) -> tuple[int, int]:
        r, c = cell
        if transpose:
            r, c = c, r
        if flip_r:
            r = 4 - r
        if flip_c:
            c = 4 - c
        return r, c

    transpose = bool(rng.randrange(2))
    flip_r = bool(rng.randrange(2))
    flip_c = bool(rng.randrange(2))
    return ({transform(cell) for cell in red}, {transform(cell) for cell in cyan})


def _base_scene(h: int, w: int, profile: str, rng) -> list[list[int]]:
    red = {
        (r, c) for r in (0, 1) for c in (0, 1)
    } | {
        (r, c) for r in (3, 4) for c in (3, 4)
    }
    red, cyan = _transform_core(red, set(_CORE_CYAN[profile]), rng)
    row0 = rng.randint(0, h - 5)
    col0 = rng.randint(0, w - 5)
    grid = full_grid(h, w, 0)
    for r, c in red:
        grid[row0 + r][col0 + c] = 2
    for r, c in cyan:
        grid[row0 + r][col0 + c] = 8
    return grid


def _target_density(difficulty) -> float:
    if difficulty == "easy":
        return 0.28
    if difficulty == "hard":
        return 0.40
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        return 0.28 + 0.12 * float(difficulty)
    return 0.34


def _add_profile_safe_noise(grid, profile: str, rng, difficulty) -> None:
    non_red = sum(value != 2 for row in grid for value in row)
    target = max(
        sum(value == 8 for row in grid for value in row),
        round(_target_density(difficulty) * non_red),
    )
    candidates = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    ]
    rng.shuffle(candidates)
    current = sum(value == 8 for row in grid for value in row)
    for r, c in candidates:
        if current >= target:
            break
        grid[r][c] = 8
        if _classify_lesson_profile(grid) == profile:
            current += 1
        else:
            grid[r][c] = 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    anchor_h, anchor_w = _anchor_dims(seed, sample_index)
    h = _draw_axis(ctx, "grid_h", 5, 8, anchor_h, overrides)
    w = _draw_axis(ctx, "grid_w", 5, 7, anchor_w, overrides)
    profile = _draw_profile(ctx, seed, sample_index, difficulty, overrides)

    grid = _base_scene(h, w, profile, ctx.draw_rng("layout"))
    if _classify_lesson_profile(grid) != profile:
        raise RuntimeError(f"constructive core failed to realize {profile!r}")
    _add_profile_safe_noise(
        grid,
        profile,
        ctx.draw_rng("profile_safe_noise"),
        difficulty,
    )

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "lesson_profile": profile}
    if observed != expected:
        raise RuntimeError(f"generated override mismatch: expected {expected}, got {observed}")
    return grid


# ---------------------------------------------------------------- teaching contract


def _profile_witness(name: str):
    return lambda grid: _classify_lesson_profile(grid) == name


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    profile: _profile_witness(profile) for profile in LESSON_PROFILES
}
WITNESS_RIVALS = {
    "diagonal_bridge": ["four_connected_bridge"],
    "bbox_decoy": ["bounding_box_bridge"],
    "small_bridge": ["largest_component_bridge"],
    "split_contacts": ["any_ring_contacts"],
}


def _validate_pair(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output disagrees with the 8-connected bridge rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Verify a lesson covers all decisive profiles and refutes named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    profiles: set[str] = set()
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
        if isinstance(demo, dict) and "input" in demo:
            profile = _classify_lesson_profile(demo["input"])
            if profile is not None:
                profiles.add(profile)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        reasons.extend(
            f"query input: {error}" for error in self_check(query["input"])
        )
        if "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the 8-connected bridge rule")

    missing = sorted(set(LESSON_PROFILES) - profiles)
    if missing:
        reasons.append("demos miss decisive lesson profiles: " + ", ".join(missing))

    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
