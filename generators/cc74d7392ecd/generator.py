"""Generator for ``cc74d7392ecd`` (Sprout Plus Seeds).

The selected Racket rule treats every non-zero input cell as a seed.  Each seed
keeps its own color and paints its four Manhattan-distance-one neighbours,
clipped by the canvas boundary.  Ordinary generated scenes use two or three
well-separated, differently colored seeds so every plus is visible without
neighbourhood overlap.  A four-draw schedule alternates canonical-scale
interior scenes with mixed boundary scenes containing one corner seed, one
non-corner edge seed, and one interior seed.  Every consecutive three-demo
window therefore teaches both one-edge and two-edge clipping.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cc74d7392ecd"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "e685ca8a450d"

SUMMARY = (
    "Every non-zero input cell is a colored seed. Preserve each seed and paint "
    "its up, down, left, and right neighbours with that seed's color; cells "
    "outside the grid are simply clipped and all other background stays 0. "
    "Generated lessons contain two or three separated, distinctly colored "
    "seeds. A four-profile schedule alternates interior canonical anchors with "
    "mixed boundary scenes, so every three demonstrations show a complete "
    "five-cell plus, a one-edge clip, and a two-edge corner clip."
)

INVARIANTS = [
    "input is a rectangular 6..10 by 6..10 ARC grid with background 0",
    "there are exactly 2 or 3 non-zero singleton seeds in distinct colors",
    "seed centers are pairwise Manhattan-separated by at least 3, so their plus neighbourhoods do not overlap",
    "scheduled boundary draws contain one corner seed, one non-corner edge seed, and one full interior plus",
    "the canonical Racket program is the sole output authority",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6..10", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "scheduled 6..10", "valid": "6..10"},
    "n_seeds": {"type": "int", "default": "scheduled 2..3", "valid": "2..3"},
    "edge_seed_count": {"type": "int", "default": "scheduled 0 or 2", "valid": "0..2"},
}

# Every Cartesian combination of the four exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "canonical_two_interior",
    "mixed_boundary_a",
    "canonical_three_interior",
    "mixed_boundary_b",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

_CANONICAL_PROFILES = {
    (7, 7, 3),
    (8, 8, 3),
    (6, 9, 3),
    (9, 6, 3),
    (8, 9, 4),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _profile_defaults(profile: str, difficulty) -> dict[str, int]:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'; "
            f"got {difficulty!r}"
        )

    # Profiles 0 and 2 are exact canonical (shape, palette-size) anchors in
    # every band. Profiles 1 and 3 carry the clipping branch and expand with
    # difficulty while staying inside the declared exact axis domains.
    edge_shapes = {
        None: ((8, 10), (10, 7)),
        "easy": ((6, 8), (7, 6)),
        "medium": ((8, 10), (10, 7)),
        "hard": ((10, 10), (9, 10)),
    }
    clipped_two_shape, clipped_three_shape = edge_shapes[difficulty]
    table = {
        "canonical_two_interior": {
            "grid_h": 7,
            "grid_w": 7,
            "n_seeds": 2,
            "edge_seed_count": 0,
        },
        "mixed_boundary_a": {
            "grid_h": clipped_two_shape[0],
            "grid_w": clipped_two_shape[1],
            "n_seeds": 3,
            "edge_seed_count": 2,
        },
        "canonical_three_interior": {
            "grid_h": 8,
            "grid_w": 9,
            "n_seeds": 3,
            "edge_seed_count": 0,
        },
        "mixed_boundary_b": {
            "grid_h": clipped_three_shape[0],
            "grid_w": clipped_three_shape[1],
            "n_seeds": 3,
            "edge_seed_count": 2,
        },
    }
    return table[profile]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def _seed_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _is_edge(r: int, c: int, height: int, width: int) -> bool:
    return r in (0, height - 1) or c in (0, width - 1)


def _is_corner(r: int, c: int, height: int, width: int) -> bool:
    return r in (0, height - 1) and c in (0, width - 1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, overlap-ambiguous, and rule-hiding input scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not 6 <= height <= 10:
        errors.append(f"height {height} outside 6..10")
    if not 6 <= width <= 10:
        errors.append(f"width {width} outside 6..10")

    seeds = _seed_cells(grid)
    if not 2 <= len(seeds) <= 3:
        errors.append(f"expected exactly 2 or 3 seeds, found {len(seeds)}")
    colors = [color for _, _, color in seeds]
    if len(set(colors)) != len(colors):
        errors.append("seed colors must be pairwise distinct")

    boundary = [
        seed for seed in seeds if _is_edge(seed[0], seed[1], height, width)
    ]
    if len(boundary) > 2:
        errors.append(f"at most 2 boundary seeds are supported, found {len(boundary)}")
    if len(boundary) == 2:
        corner_count = sum(
            _is_corner(r, c, height, width) for r, c, _ in boundary
        )
        if corner_count != 1:
            errors.append(
                "two-boundary scenes must contain exactly one corner seed "
                "and one non-corner edge seed"
            )

    for i, (r1, c1, _) in enumerate(seeds):
        for r2, c2, _ in seeds[i + 1 :]:
            distance = abs(r1 - r2) + abs(c1 - c2)
            if distance < 3:
                errors.append(
                    "seed centers must be Manhattan-separated by at least 3; "
                    f"found distance {distance} between ({r1},{c1}) and ({r2},{c2})"
                )
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The exact empirical canonical profile plus its non-overlap grammar."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    height, width = len(grid), len(grid[0])
    palette_size = len({value for row in grid for value in row})
    if (height, width, palette_size) not in _CANONICAL_PROFILES:
        reasons.append(
            "canonical (height,width,palette-size) profile must be one of "
            f"{sorted(_CANONICAL_PROFILES)}, found {(height, width, palette_size)}"
        )
    edge_count = sum(
        _is_edge(r, c, height, width) for r, c, _ in _seed_cells(grid)
    )
    if edge_count:
        reasons.append(f"canonical seeds are interior; found {edge_count} boundary seed(s)")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    height = len(grid)
    width = len(grid[0])
    seeds = _seed_cells(grid)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": len(seeds),
        "edge_seed_count": sum(
            _is_edge(r, c, height, width) for r, c, _ in seeds
        ),
    }


def _candidate_cells(
    height: int,
    width: int,
    *,
    role: str,
) -> list[tuple[int, int]]:
    if role == "corner":
        return [
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        ]
    if role == "edge":
        return [
            (r, c)
            for r in range(height)
            for c in range(width)
            if _is_edge(r, c, height, width)
            and not _is_corner(r, c, height, width)
        ]
    if role == "interior":
        return [
            (r, c)
            for r in range(1, height - 1)
            for c in range(1, width - 1)
        ]
    raise ValueError(f"unknown seed placement role: {role!r}")


def _place_seeds(
    height: int,
    width: int,
    n_seeds: int,
    edge_seed_count: int,
    rng,
) -> list[tuple[int, int]]:
    if not 0 <= edge_seed_count <= min(2, n_seeds):
        raise ValueError(
            "edge_seed_count must be in 0..2 and cannot exceed n_seeds; "
            f"got n_seeds={n_seeds}, edge_seed_count={edge_seed_count}"
        )
    roles: list[str] = []
    if edge_seed_count == 1:
        roles.append("edge")
    elif edge_seed_count == 2:
        roles.extend(("corner", "edge"))
    roles.extend(["interior"] * (n_seeds - edge_seed_count))
    pools = {
        role: _candidate_cells(height, width, role=role)
        for role in ("corner", "edge", "interior")
    }
    for pool in pools.values():
        rng.shuffle(pool)
    placed: list[tuple[int, int]] = []

    def search(index: int) -> bool:
        if index == len(roles):
            return True
        for position in pools[roles[index]]:
            if position in placed:
                continue
            if any(
                abs(position[0] - r) + abs(position[1] - c) < 3
                for r, c in placed
            ):
                continue
            placed.append(position)
            if search(index + 1):
                return True
            placed.pop()
        return False

    if not search(0):
        raise RuntimeError(
            "unable to place requested separated seeds for "
            f"grid={height}x{width}, n_seeds={n_seeds}, "
            f"edge_seed_count={edge_seed_count}"
        )
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))

    profile = schedule_profile(seed, sample_index, difficulty)
    effective_overrides = _profile_defaults(profile, difficulty)
    effective_overrides.update(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    height = ctx.draw_int_strict("grid_h", 6, 10)
    width = ctx.draw_int_strict("grid_w", 6, 10)
    n_seeds = ctx.draw_int_strict("n_seeds", 2, 3)
    edge_seed_count = ctx.draw_int_strict("edge_seed_count", 0, 2)

    layout_rng = ctx.draw_rng("seed_layout")
    positions = _place_seeds(
        height,
        width,
        n_seeds,
        edge_seed_count,
        layout_rng,
    )
    colors = ctx.draw_distinct_colors("seed_colors", n=n_seeds, exclude={0})
    grid = full_grid(height, width, 0)
    for (r, c), color in zip(positions, colors):
        grid[r][c] = color

    findings = self_check(grid)
    if findings:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(findings))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": n_seeds,
        "edge_seed_count": edge_seed_count,
    }
    if observed != requested:
        raise RuntimeError(
            f"realized exact axes {observed} disagree with requested {requested}"
        )
    return grid


def _apply_seed_rule(
    grid: Sequence[Sequence[int]],
    covers: Callable[[int, int, int, int], bool],
    *,
    seeds: Sequence[tuple[int, int, int]] | None = None,
    force_color: int | None = None,
) -> list[list[int]]:
    source_seeds = list(_seed_cells(grid) if seeds is None else seeds)
    height, width = len(grid), len(grid[0])
    out = full_grid(height, width, 0)
    for r in range(height):
        for c in range(width):
            for sr, sc, color in source_seeds:
                if covers(sr, sc, r, c):
                    out[r][c] = color if force_color is None else force_color
                    break
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains authoritative."""
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
    )


def _identity(grid):
    return [list(row) for row in grid]


def _square_radius_one(grid):
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: max(abs(sr - r), abs(sc - c)) <= 1,
    )


def _diagonal_x(grid):
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: (r == sr and c == sc)
        or (abs(sr - r) == 1 and abs(sc - c) == 1),
    )


def _horizontal_only(grid):
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: r == sr and abs(sc - c) <= 1,
    )


def _vertical_only(grid):
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: c == sc and abs(sr - r) <= 1,
    )


def _only_first_seed(grid):
    seeds = _seed_cells(grid)
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=seeds[:1],
    )


def _first_seed_color_for_all(grid):
    seeds = _seed_cells(grid)
    if not seeds:
        return [list(row) for row in grid]
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        force_color=seeds[0][2],
    )


def _ignore_boundary_seeds(grid):
    height, width = len(grid), len(grid[0])
    interior = [
        seed
        for seed in _seed_cells(grid)
        if not _is_edge(seed[0], seed[1], height, width)
    ]
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=interior,
    )


def _ignore_corner_seeds(grid):
    height, width = len(grid), len(grid[0])
    retained = [
        seed
        for seed in _seed_cells(grid)
        if not _is_corner(seed[0], seed[1], height, width)
    ]
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=retained,
    )


def _ignore_noncorner_boundary_seeds(grid):
    height, width = len(grid), len(grid[0])
    retained = [
        seed
        for seed in _seed_cells(grid)
        if not (
            _is_edge(seed[0], seed[1], height, width)
            and not _is_corner(seed[0], seed[1], height, width)
        )
    ]
    return _apply_seed_rule(
        grid,
        lambda sr, sc, r, c: abs(sr - r) + abs(sc - c) <= 1,
        seeds=retained,
    )


SEMANTIC_RIVALS = {
    "identity": _identity,
    "square_radius_one": _square_radius_one,
    "diagonal_x": _diagonal_x,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "only_first_seed": _only_first_seed,
    "first_seed_color_for_all": _first_seed_color_for_all,
    "ignore_boundary_seeds": _ignore_boundary_seeds,
    "ignore_corner_seeds": _ignore_corner_seeds,
    "ignore_noncorner_boundary_seeds": _ignore_noncorner_boundary_seeds,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The clipping shortcut matches every canonical example because all canonical
# seeds are interior. Declaring it here makes the generated edge witness a
# machine-checked counterexample rather than an informal claim.
CANONICAL_SHORTCUTS = {
    "ignore_boundary_seeds": _ignore_boundary_seeds,
    "ignore_corner_seeds": _ignore_corner_seeds,
    "ignore_noncorner_boundary_seeds": _ignore_noncorner_boundary_seeds,
}


def _valid_and_refutes(grid, rivals: Sequence[str]) -> bool:
    if self_check(grid):
        return False
    expected = rule_mirror(grid)
    return all(SEMANTIC_RIVALS[name](grid) != expected for name in rivals)


def _witness_plus_geometry(grid) -> bool:
    return _valid_and_refutes(
        grid,
        ("identity", "square_radius_one", "diagonal_x", "horizontal_only", "vertical_only"),
    )


def _witness_all_seeds_act(grid) -> bool:
    return _valid_and_refutes(grid, ("only_first_seed",))


def _witness_seed_colors_preserved(grid) -> bool:
    return _valid_and_refutes(grid, ("first_seed_color_for_all",))


def _witness_edge_clipping(grid) -> bool:
    if self_check(grid):
        return False
    height, width = len(grid), len(grid[0])
    if not any(_is_edge(r, c, height, width) for r, c, _ in _seed_cells(grid)):
        return False
    return _valid_and_refutes(grid, ("ignore_boundary_seeds",))


def _witness_corner_clipping(grid) -> bool:
    if self_check(grid):
        return False
    height, width = len(grid), len(grid[0])
    if not any(
        _is_corner(r, c, height, width) for r, c, _ in _seed_cells(grid)
    ):
        return False
    return _valid_and_refutes(grid, ("ignore_corner_seeds",))


def _witness_noncorner_edge_clipping(grid) -> bool:
    if self_check(grid):
        return False
    height, width = len(grid), len(grid[0])
    if not any(
        _is_edge(r, c, height, width) and not _is_corner(r, c, height, width)
        for r, c, _ in _seed_cells(grid)
    ):
        return False
    return _valid_and_refutes(grid, ("ignore_noncorner_boundary_seeds",))


SEMANTIC_WITNESSES = {
    "cardinal_plus_not_square_x_or_line": _witness_plus_geometry,
    "every_seed_expands": _witness_all_seeds_act,
    "each_plus_keeps_its_seed_color": _witness_seed_colors_preserved,
    "boundary_seed_is_clipped_not_ignored": _witness_edge_clipping,
    "corner_seed_is_clipped_not_ignored": _witness_corner_clipping,
    "noncorner_edge_seed_is_clipped_not_ignored": _witness_noncorner_edge_clipping,
}

WITNESS_RIVALS = {
    "cardinal_plus_not_square_x_or_line": [
        "identity",
        "square_radius_one",
        "diagonal_x",
        "horizontal_only",
        "vertical_only",
    ],
    "every_seed_expands": ["only_first_seed"],
    "each_plus_keeps_its_seed_color": ["first_seed_color_for_all"],
    "boundary_seed_is_clipped_not_ignored": ["ignore_boundary_seeds"],
    "corner_seed_is_clipped_not_ignored": ["ignore_corner_seeds"],
    "noncorner_edge_seed_is_clipped_not_ignored": [
        "ignore_noncorner_boundary_seeds"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every named rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_grid = demo["input"]
        input_errors = self_check(input_grid)
        if input_errors:
            reasons.append(f"demo {index} input is invalid: {input_errors[0]}")
            continue
        expected = rule_mirror(input_grid)
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact cardinal-plus transform")
        for name, competitor in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or competitor(input_grid) != expected

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def mutation_fixtures():
    """Task-local malformed scenes that self_check must reject."""
    all_background = full_grid(6, 6, 0)

    singleton = full_grid(6, 6, 0)
    singleton[2][2] = 4

    adjacent_seeds = full_grid(6, 6, 0)
    adjacent_seeds[2][2] = 4
    adjacent_seeds[2][3] = 7

    repeated_color = full_grid(6, 6, 0)
    repeated_color[1][1] = 5
    repeated_color[4][4] = 5

    already_expanded = full_grid(7, 7, 0)
    for r, c in ((3, 3), (2, 3), (4, 3), (3, 2), (3, 4)):
        already_expanded[r][c] = 6

    return [
        ("all_background", all_background),
        ("single_seed_rule_hider", singleton),
        ("overlapping_adjacent_seeds", adjacent_seeds),
        ("repeated_seed_color", repeated_color),
        ("already_expanded_plus_input", already_expanded),
    ]
