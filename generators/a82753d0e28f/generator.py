"""Generator for task a82753d0e28f: row-major chess-knight halos.

Each nonzero input cell is a seed.  Scanning seeds in row-major order, the
selected rule paints the seed and every in-bounds chess-knight destination in
that seed's color.  Later seeds therefore overwrite earlier paint at
collisions.  Ordinary draws deliberately include a collision where a later,
lower-colored seed overwrites an earlier, higher-colored seed; this refutes the
plausible canonical-fitting shortcut "highest color wins".
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a82753d0e28f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bf05263117e5"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background 7..10 by 8..12 grid contains 2..4 singleton seeds in "
    "exactly two nonzero colors. Scan seeds in row-major order: each seed "
    "paints itself and every in-bounds chess-knight destination in its color, "
    "with later seeds overwriting earlier paint. Ordinary draws include an "
    "overlap where a later lower color defeats an earlier higher color, while "
    "also varying clipped and fully visible halos."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "inputs are 7..10 rows by 8..12 columns with 2..4 singleton seeds",
    "exactly two distinct nonzero seed colors are present",
    "the seed and the eight chess-knight offsets are painted in bounds",
    "seeds are processed row-major and later paint overwrites earlier paint",
]

# These are the only public controls.  Every value is exactly recoverable from
# the returned grid and every declared value is accepted in every difficulty
# band.  Difficulty changes only the default weighting, never the legal domain.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted rng 7..10",
        "valid": "7..10",
        "doc": "Number of rows; exactly observable as len(grid).",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted rng 8..12",
        "valid": "8..12",
        "doc": "Number of columns; exactly observable as len(grid[0]).",
    },
    "seeds": {
        "type": "int",
        "default": "difficulty-weighted rng 2..4",
        "valid": "2..4",
        "doc": "Number of nonzero singleton seeds.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

Grid = list[list[int]]
Cell = tuple[int, int]

_KNIGHT: tuple[Cell, ...] = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)


def _validate_call_arguments(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _validate_difficulty(difficulty: Any) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")


def _axis_options(difficulty: Any) -> dict[str, tuple[int, ...]]:
    """Full-domain weighted defaults; duplicates change probability only."""
    if difficulty == "easy":
        return {
            "grid_h": (7, 7, 8, 8, 9, 10),
            "grid_w": (8, 9, 9, 10, 10, 11, 12),
            "seeds": (2, 2, 2, 3, 3, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (7, 8, 9, 9, 10, 10),
            "grid_w": (8, 9, 10, 10, 11, 11, 12),
            "seeds": (2, 3, 3, 4, 4, 4),
        }
    return {
        "grid_h": (7, 7, 8, 8, 9, 9, 10),
        "grid_w": (8, 9, 9, 10, 10, 11, 12),
        "seeds": (2, 3, 3, 3, 4),
    }


def _in_bounds(h: int, w: int, cell: Cell) -> bool:
    r, c = cell
    return 0 <= r < h and 0 <= c < w


@lru_cache(maxsize=None)
def _halo(h: int, w: int, cell: Cell) -> frozenset[Cell]:
    r, c = cell
    return frozenset(
        (r + dr, c + dc)
        for dr, dc in _KNIGHT
        if 0 <= r + dr < h and 0 <= c + dc < w
    )


@lru_cache(maxsize=None)
def _painted_cells(h: int, w: int, cell: Cell) -> frozenset[Cell]:
    return frozenset((cell, *_halo(h, w, cell)))


def _knight_related(first: Cell, second: Cell) -> bool:
    return (second[0] - first[0], second[1] - first[1]) in _KNIGHT


@lru_cache(maxsize=None)
def _pair_candidates(h: int, w: int, profile: str) -> tuple[tuple[Cell, Cell, tuple[Cell, ...]], ...]:
    cells = [(r, c) for r in range(h) for c in range(w)]
    candidates: list[tuple[Cell, Cell, tuple[Cell, ...]]] = []
    for index, first in enumerate(cells):
        first_halo = _halo(h, w, first)
        for second in cells[index + 1 :]:
            if _knight_related(first, second):
                # Keep each input seed stable at its own location; the intended
                # ambiguity is halo/halo precedence rather than seed erasure.
                continue
            second_halo = _halo(h, w, second)
            shared = tuple(sorted((first_halo & second_halo) - {first, second}))
            if not shared:
                continue
            if profile == "full" and not (
                len(first_halo) == 8 and len(second_halo) == 8
            ):
                continue
            if profile == "clipped" and not (
                len(first_halo) < 8 or len(second_halo) < 8
            ):
                continue
            candidates.append((first, second, shared))
    return tuple(candidates)


def _extra_seeds(
    rng,
    h: int,
    w: int,
    chosen_pair: tuple[Cell, Cell],
    witness: Cell,
    count: int,
) -> list[Cell] | None:
    if count == 0:
        return []
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in chosen_pair
        and witness not in _painted_cells(h, w, (r, c))
    ]
    rng.shuffle(candidates)

    def search(start: int, chosen: list[Cell]) -> list[Cell] | None:
        if len(chosen) == count:
            return list(chosen)
        if len(candidates) - start < count - len(chosen):
            return None
        occupied = [*chosen_pair, *chosen]
        for index in range(start, len(candidates)):
            cell = candidates[index]
            if any(_knight_related(cell, other) or _knight_related(other, cell)
                   for other in occupied):
                continue
            result = search(index + 1, [*chosen, cell])
            if result is not None:
                return result
        return None

    return search(0, [])


def _pick_layout(rng, h: int, w: int, target: int, profile: str) -> tuple[list[Cell], Cell, Cell, Cell]:
    candidates = list(_pair_candidates(h, w, profile))
    rng.shuffle(candidates)
    for first, second, shared in candidates:
        witness_cells = list(shared)
        rng.shuffle(witness_cells)
        for witness in witness_cells:
            extras = _extra_seeds(
                rng, h, w, (first, second), witness, target - 2
            )
            if extras is not None:
                return [first, second, *extras], first, second, witness
    raise ValueError(
        f"could not place {target} seeds with a {profile} overlapping-halo witness "
        f"on {h}x{w}"
    )


def _grid_facts(grid: Any) -> tuple[list[str], int | None, int | None, list[tuple[int, int, int]]]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"], None, None, []
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"], None, None, []
    if not grid[0]:
        return ["grid rows must be non-empty"], None, None, []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"], None, None, []

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 10:
        errors.append(f"grid height {height} is outside 7..10")
    if not 8 <= width <= 12:
        errors.append(f"grid width {width} is outside 8..12")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors, height, width, []

    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not 2 <= len(seeds) <= 4:
        errors.append(f"expected 2..4 seeds, found {len(seeds)}")
    colors = {color for _, _, color in seeds}
    if len(colors) != 2:
        errors.append(
            f"expected exactly two distinct nonzero seed colors, found {len(colors)}"
        )
    return errors, height, width, seeds


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad lawful manifold, including all canonical inputs."""
    del difficulty
    errors, _, _, _ = _grid_facts(grid)
    if errors:
        return errors

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict):
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and expected is not None and observed[name] != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The canonical-like grammar is exactly the structural task manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors, height, width, seeds = _grid_facts(grid)
    if errors or height is None or width is None:
        raise ValueError("; ".join(errors) or "invalid grid")
    return {"grid_h": height, "grid_w": width, "seeds": len(seeds)}


def _knight_output(grid: Sequence[Sequence[int]]) -> Grid:
    """Pure-Python diagnostic mirror of the selected row-major rule."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            output[r][c] = int(color)
            for rr, cc in _halo(h, w, (r, c)):
                output[rr][cc] = int(color)
    return output


def _max_color_halo(grid: Sequence[Sequence[int]]) -> Grid:
    """Canonical-fitting rival: collision cells keep the greatest color."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            for rr, cc in _painted_cells(h, w, (r, c)):
                output[rr][cc] = max(output[rr][cc], int(color))
    return output


def _later_lower_overlap(grid: Sequence[Sequence[int]]) -> bool:
    try:
        if self_check([list(row) for row in grid]):
            return False
        return _knight_output(grid) != _max_color_halo(grid)
    except (TypeError, ValueError, IndexError):
        return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, lawful, shortcut-refuting input grid."""
    _validate_call_arguments(seed, sample_index)
    _validate_difficulty(difficulty)
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    options = _axis_options(difficulty)
    h = ctx.draw_choice("grid_h", options["grid_h"])
    w = ctx.draw_choice("grid_w", options["grid_w"])
    target = ctx.draw_choice("seeds", options["seeds"])

    if difficulty == "easy":
        profile_options = ("clipped", "clipped", "mixed", "full")
    elif difficulty == "hard":
        profile_options = ("clipped", "mixed", "full", "full")
    else:
        profile_options = ("clipped", "mixed", "full")
    profile = ctx.draw_choice("layout_profile", profile_options)

    layout_rng = ctx.draw_rng("layout")
    cells, earlier, later, witness = _pick_layout(
        layout_rng, h, w, target, profile
    )
    color_rng = ctx.draw_rng("seed_colors")
    high, low = sorted(color_rng.sample(range(1, 10), 2), reverse=True)

    grid = full_grid(h, w, 0)
    grid[earlier[0]][earlier[1]] = high
    grid[later[0]][later[1]] = low
    for index, cell in enumerate(cells[2:]):
        grid[cell[0]][cell[1]] = (high, low)[index % 2]

    # This assertion protects the constructive contract from later refactors.
    if _knight_output(grid)[witness[0]][witness[1]] != low:
        raise AssertionError("designated overlap was not won by the later seed")
    if not _later_lower_overlap(grid):
        raise AssertionError("generated grid did not refute max-color collision rule")
    return grid


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], Grid]] = {
    "max_color_wins": _max_color_halo,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "later_lower_overlap": _later_lower_overlap,
}
WITNESS_RIVALS = {
    "later_lower_overlap": ["max_color_wins"],
}


def _labeled_pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    try:
        expected = _knight_output(pair["input"])
    except (TypeError, ValueError, IndexError) as exc:
        return [f"{label} rule evaluation failed: {exc}"]
    if pair["output"] != expected:
        return [f"{label} output does not follow row-major knight-halo painting"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require lawful labels and a demonstration refuting every named rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_labeled_pair_errors(demo, f"demo {index}"))
    reasons.extend(_labeled_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
