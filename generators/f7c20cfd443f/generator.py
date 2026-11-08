"""Curriculum generator for ARC task ``f7c20cfd443f`` / ``ce22a75a``.

The selected rule is a clipped Chebyshev-radius-one dilation: every gray
(color 5) seed becomes a 3x3 block of blue (color 1), clipped at the grid
boundary; all other output cells are black (color 0).

The public examples place isolated singleton seeds at 3x3 macrocell centers.
That presentation is ambiguous with a wrong "fill the containing macrocell"
rule.  This generator preserves one exact 9x9 canonical anchor in every four
examples, then adds controlled size extrapolation while cycling through
four deterministic lesson profiles: canonical lattice, off-lattice seeds,
boundary clipping, and overlapping output halos.  Any four consecutive
examples therefore retain the public distribution while supplying
counterexamples to the principal shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f7c20cfd443f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "89548e944e39"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A black grid contains one to four isolated singleton gray (5) seeds. "
    "Replace every seed by a clipped 3x3 blue (1) block centered on that "
    "seed; overlapping blocks merge. Default lessons stay at the canonical "
    "9x9 scale with three or four seeds and cycle through canonical-lattice, "
    "off-lattice, edge-clipping, and overlapping-halo profiles."
)

INVARIANTS = [
    "grid dimensions are 7..15; every four ordinary draws include a 9x9 anchor",
    "the input palette is exactly black 0 plus gray 5",
    "there are 1..4 singleton gray seeds; ordinary draws use 3 or 4",
    "seed cells are not 8-neighbours, so every input object is a singleton",
    "the output is the clipped union of Chebyshev-radius-one blue halos",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile/difficulty schedule; canonical anchor is 9",
        "valid": "7..15",
        "doc": "input height",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile/difficulty schedule; canonical anchor is 9",
        "valid": "7..15",
        "doc": "input width",
    },
    "n_seeds": {
        "type": "int",
        "default": "scheduled 3 or 4; difficulty shifts mass only",
        "valid": "1..4",
        "doc": "number of isolated singleton gray seeds",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "off_lattice",
    "edge_clip",
    "overlap",
)

# Dimensions align positionally with SCHEDULE_PROFILES.  Each band has one
# exact 9x9 anchor plus a 9x9 overlap case and controlled breadth; pooled
# ordinary draws exercise both public override boundaries without the baseline's
# 4x4..24x24 scale drift.  Half the curriculum remains exact-profile support.
PROFILE_DIMENSIONS = {
    None: ((9, 9), (10, 8), (9, 11), (9, 9)),
    "easy": ((9, 9), (7, 8), (8, 7), (9, 9)),
    "medium": ((9, 9), (10, 8), (9, 11), (9, 9)),
    "hard": ((9, 9), (15, 12), (12, 15), (9, 9)),
}

_DEFAULT_SEED_COUNTS = {
    None: (4, 3, 4, 3),
    "easy": (3, 4, 3, 4),
    "medium": (4, 3, 4, 3),
    "hard": (4, 4, 3, 4),
}

Grid = list[list[int]]
Cell = tuple[int, int]
Rule = Callable[[Any], Grid]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the four-step deterministic curriculum schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record scheduled defaults while preserving the full exact override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _chebyshev(a: Cell, b: Cell) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def _spaced_from(
    candidates: Sequence[Cell],
    count: int,
    rng,
    *,
    required: Sequence[Cell] = (),
    min_distance: int = 2,
    required_min_distance: int | None = None,
) -> list[Cell]:
    """Choose separated cells while preserving profile-defining requirements.

    ``required_min_distance`` may be lower than ``min_distance`` for the overlap
    profile: its required pair is exactly two cells apart, while every added
    seed must remain at least three cells from that pair and from other extras.
    """
    if not 0 <= len(required) <= count:
        raise ValueError("required seed count exceeds requested n_seeds")
    chosen = list(dict.fromkeys(required))
    if len(chosen) != len(required):
        raise ValueError("profile supplied duplicate required seeds")
    required_floor = min_distance if required_min_distance is None else required_min_distance
    if any(
        _chebyshev(a, b) < required_floor
        for i, a in enumerate(chosen)
        for b in chosen[i + 1 :]
    ):
        raise ValueError("profile supplied required seeds that are too close")
    if len(chosen) == count:
        return chosen

    pool = [cell for cell in dict.fromkeys(candidates) if cell not in chosen]
    for attempt in range(32):
        ordered = list(pool)
        if attempt < 31:
            rng.shuffle(ordered)
        else:
            ordered.sort()
        trial = list(chosen)
        for cell in ordered:
            if all(_chebyshev(cell, other) >= min_distance for other in trial):
                trial.append(cell)
                if len(trial) == count:
                    return trial
    raise ValueError(
        f"could not place {count} separated seeds with {len(required)} required"
    )


def _all_cells(height: int, width: int) -> list[Cell]:
    return [(row, col) for row in range(height) for col in range(width)]


def _lattice_cells(height: int, width: int) -> list[Cell]:
    """Canonical 3x3-macrocell centers, generalized to override dimensions."""
    return [
        (row, col)
        for row in range(1, height, 3)
        for col in range(1, width, 3)
    ]


def _try_required_options(
    candidates: Sequence[Cell],
    count: int,
    rng,
    required_options: Sequence[Sequence[Cell]],
    *,
    min_distance: int,
    required_min_distance: int | None = None,
) -> list[Cell]:
    """Try semantic anchors until one leaves room for the requested seed count."""
    options = [tuple(option) for option in required_options]
    rng.shuffle(options)
    last_error: ValueError | None = None
    for required in options:
        try:
            return _spaced_from(
                candidates,
                count,
                rng,
                required=required,
                min_distance=min_distance,
                required_min_distance=required_min_distance,
            )
        except ValueError as exc:
            last_error = exc
    raise ValueError("no profile anchor supports the requested override tuple") from last_error


def _canonical_seeds(height: int, width: int, count: int, rng) -> list[Cell]:
    return _spaced_from(
        _lattice_cells(height, width), count, rng, min_distance=3
    )


def _off_lattice_seeds(height: int, width: int, count: int, rng) -> list[Cell]:
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    off_lattice = [
        cell for cell in interior if cell[0] % 3 != 1 or cell[1] % 3 != 1
    ]
    return _try_required_options(
        interior,
        count,
        rng,
        [(cell,) for cell in off_lattice],
        min_distance=3,
    )


def _edge_seeds(height: int, width: int, count: int, rng) -> list[Cell]:
    border = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ]
    return _try_required_options(
        _all_cells(height, width),
        count,
        rng,
        [(cell,) for cell in border],
        min_distance=3,
    )


def _overlap_seeds(height: int, width: int, count: int, rng) -> list[Cell]:
    """Require two nonadjacent seeds whose radius-one halos overlap."""
    pairs: list[tuple[Cell, Cell]] = []
    for row in range(1, height - 1):
        for col in range(1, width - 3):
            pairs.append(((row, col), (row, col + 2)))
    for row in range(1, height - 3):
        for col in range(1, width - 1):
            pairs.append(((row, col), (row + 2, col)))
    if not pairs:
        raise ValueError("override dimensions cannot host an overlap profile")
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    required_options = [pair[: min(count, 2)] for pair in pairs]
    return _try_required_options(
        interior,
        count,
        rng,
        required_options,
        min_distance=3,
        required_min_distance=2,
    )


_PROFILE_BUILDERS = {
    "canonical_anchor": _canonical_seeds,
    "off_lattice": _off_lattice_seeds,
    "edge_clip": _edge_seeds,
    "overlap": _overlap_seeds,
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; canonical Racket remains the authority."""
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    profile_index = SCHEDULE_PROFILES.index(profile)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_height, default_width = PROFILE_DIMENSIONS[difficulty][profile_index]
    height = _scheduled_int(ctx, "grid_h", 7, 15, default_height)
    width = _scheduled_int(ctx, "grid_w", 7, 15, default_width)
    n_seeds = _scheduled_int(
        ctx,
        "n_seeds",
        1,
        4,
        _DEFAULT_SEED_COUNTS[difficulty][profile_index],
    )

    rng = ctx.draw_rng(f"placement:{profile}:{difficulty or 'default'}")
    seeds = _PROFILE_BUILDERS[profile](height, width, n_seeds, rng)
    grid = full_grid(height, width, 0)
    for row, col in seeds:
        grid[row][col] = 5
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _seed_cells(grid: Any) -> list[Cell]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and seed grammars that hide object identity."""
    del difficulty, meta
    errors = _rectangular_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 15:
        errors.append(f"grid height must be 7..15, found {height}")
    if not 7 <= width <= 15:
        errors.append(f"grid width must be 7..15, found {width}")

    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 5})
    if unexpected:
        errors.append(f"input palette must be a subset of {{0,5}}, found {unexpected}")

    seeds = _seed_cells(grid)
    if not 1 <= len(seeds) <= 4:
        errors.append(f"expected 1..4 gray singleton seeds, found {len(seeds)}")
    if 0 not in palette:
        errors.append("input must retain black background cells")
    if 5 not in palette:
        errors.append("input must contain at least one gray seed")

    adjacent = [
        (left, right)
        for index, left in enumerate(seeds)
        for right in seeds[index + 1 :]
        if _chebyshev(left, right) < 2
    ]
    if adjacent:
        errors.append(
            "gray cells must be isolated singleton objects; adjacent pairs "
            f"include {adjacent[:3]}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate for the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every public exact axis from the returned input."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_seeds": len(_seed_cells(grid)),
    }


def _require_rule_input(grid: Any) -> tuple[int, int, list[Cell]]:
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    palette = {value for row in grid for value in row}
    if not palette <= {0, 5}:
        raise ValueError(f"invalid rule input palette: {sorted(palette)}")
    return len(grid), len(grid[0]), _seed_cells(grid)


def _paint_halos(height: int, width: int, seeds: Sequence[Cell]) -> Grid:
    output = full_grid(height, width, 0)
    for seed_row, seed_col in seeds:
        for row in range(max(0, seed_row - 1), min(height, seed_row + 2)):
            for col in range(max(0, seed_col - 1), min(width, seed_col + 2)):
                output[row][col] = 1
    return output


def rule_mirror(grid) -> Grid:
    """Independent Python mirror used for tests; Racket stays authoritative."""
    height, width, seeds = _require_rule_input(grid)
    return _paint_halos(height, width, seeds)


def _rival_aligned_macrocell(grid) -> Grid:
    """Wrong shortcut: fill the 3x3 macrocell containing each seed."""
    height, width, seeds = _require_rule_input(grid)
    output = full_grid(height, width, 0)
    for seed_row, seed_col in seeds:
        row0 = (seed_row // 3) * 3
        col0 = (seed_col // 3) * 3
        for row in range(row0, min(height, row0 + 3)):
            for col in range(col0, min(width, col0 + 3)):
                output[row][col] = 1
    return output


def _rival_ignore_edge_seeds(grid) -> Grid:
    """Wrong shortcut: discard seeds whose centered block would be clipped."""
    height, width, seeds = _require_rule_input(grid)
    interior = [
        (row, col)
        for row, col in seeds
        if 0 < row < height - 1 and 0 < col < width - 1
    ]
    return _paint_halos(height, width, interior)


def _footprint(height: int, width: int, seed: Cell) -> set[Cell]:
    row, col = seed
    return {
        (r, c)
        for r in range(max(0, row - 1), min(height, row + 2))
        for c in range(max(0, col - 1), min(width, col + 2))
    }


def _rival_nonoverlap_only(grid) -> Grid:
    """Wrong shortcut: expand only seeds whose 3x3 blocks stay disjoint."""
    height, width, seeds = _require_rule_input(grid)
    footprints = [_footprint(height, width, seed) for seed in seeds]
    kept = [
        seed
        for index, seed in enumerate(seeds)
        if all(
            footprints[index].isdisjoint(footprints[other])
            for other in range(len(seeds))
            if other != index
        )
    ]
    return _paint_halos(height, width, kept)


def _rival_preserve_gray_centers(grid) -> Grid:
    """Wrong shortcut: expand seeds but leave their centers gray."""
    height, width, seeds = _require_rule_input(grid)
    output = _paint_halos(height, width, seeds)
    for row, col in seeds:
        output[row][col] = 5
    return output


def _rival_orthogonal_plus(grid) -> Grid:
    """Wrong shortcut: use Manhattan radius one rather than a full 3x3."""
    height, width, seeds = _require_rule_input(grid)
    output = full_grid(height, width, 0)
    for row, col in seeds:
        for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = 1
    return output


SEMANTIC_RIVALS: dict[str, Rule] = {
    "aligned_macrocell": _rival_aligned_macrocell,
    "ignore_edge_seeds": _rival_ignore_edge_seeds,
    "nonoverlap_only": _rival_nonoverlap_only,
    "preserve_gray_centers": _rival_preserve_gray_centers,
    "orthogonal_plus": _rival_orthogonal_plus,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("aligned_macrocell", "ignore_edge_seeds", "nonoverlap_only")
}


def _valid_seeds(grid: Any) -> list[Cell] | None:
    return _seed_cells(grid) if self_check(grid) == [] else None


def _witness_off_lattice(grid: Any) -> bool:
    seeds = _valid_seeds(grid)
    return bool(
        seeds is not None
        and any(row % 3 != 1 or col % 3 != 1 for row, col in seeds)
    )


def _witness_edge_clip(grid: Any) -> bool:
    seeds = _valid_seeds(grid)
    if seeds is None:
        return False
    height, width = len(grid), len(grid[0])
    return any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in seeds
    )


def _witness_overlap(grid: Any) -> bool:
    seeds = _valid_seeds(grid)
    return bool(
        seeds is not None
        and any(
            _chebyshev(left, right) == 2
            for index, left in enumerate(seeds)
            for right in seeds[index + 1 :]
        )
    )


def _witness_any_seed(grid: Any) -> bool:
    seeds = _valid_seeds(grid)
    return bool(seeds)


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "off_lattice_seed": _witness_off_lattice,
    "edge_clipping": _witness_edge_clip,
    "overlapping_halos": _witness_overlap,
    "centers_recolored_blue": _witness_any_seed,
    "full_square_not_plus": _witness_any_seed,
}
WITNESS_RIVALS = {
    "off_lattice_seed": ["aligned_macrocell"],
    "edge_clipping": ["ignore_edge_seeds"],
    "overlapping_halos": ["nonoverlap_only"],
    "centers_recolored_blue": ["preserve_gray_centers"],
    "full_square_not_plus": ["orthogonal_plus"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo lesson to falsify every named shortcut rule."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the selected dilation rule")
            continue
        valid_demos.append(demo)

    if len(valid_demos) == len(demos):
        required_evidence = {
            "off-lattice seed": _witness_off_lattice,
            "edge-clipped halo": _witness_edge_clip,
            "overlapping halos": _witness_overlap,
        }
        for label, witness in required_evidence.items():
            if not any(witness(demo["input"]) for demo in valid_demos):
                reasons.append(f"demonstrations never show an {label}")

        for name, competitor in LESSON_COMPETITORS.items():
            if all(
                competitor(demo["input"]) == demo["output"]
                for demo in valid_demos
            ):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons
