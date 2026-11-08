"""Input generator for task 017f1406edaf: select the area matching row 0.

The unchanged Racket authority counts blue(1) cells in row 0.  It scans
monochrome objects in row-major order, excludes color-1 objects and objects that
touch row 0, selects the first remaining object with that many cells, and paints
only that object cyan(8) on a blank grid.

Default lessons alternate two profiles:

* ``canonical`` recreates the three canonical size/palette profiles while still
  varying marker positions and blob geometry.
* ``counterexample`` combines three independently meaningful witnesses: a blue
  size-K object below row 0, a nonblue size-K object touching row 0, and an
  eligible size-K target that is not the median-sized candidate.  One grid thus
  refutes the plausible ``count all blue``, ``allow row-0 objects``, and
  ``choose the median-sized candidate`` shortcuts.

All advertised controls are exact in every difficulty band.  Difficulty only
reweights defaults; it never narrows an override's valid domain.  Outputs remain
owned by the canonical Racket rule and are not generated here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "017f1406edaf"
TASK_ID = GENERATOR_ID
RULE_HASH = "e05af36c455d"
VERSION = "4.0.0"
SUMMARY = (
    "Count blue markers in row 0, then retain only the nonblue, non-row-0 "
    "object with matching area and recolor it cyan. Alternating canonical and "
    "combined-counterexample profiles teach the row-only count and both object "
    "exclusions while varying blob geometry, order, size rank, and palette."
)

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = ("canonical", "counterexample")
MIN_STRICT_FRAC = 0.50
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "9..14 by 10..14 integer grid on background 0",
    "row 0 contains K=2..6 blue marker cells",
    "2..4 isolated eligible nonblue blobs have pairwise-distinct sizes and colors",
    "exactly one eligible blob has area K",
    "blue and row-0 size-K decoys are realized exactly when requested",
    "every four consecutive default demonstrations include two combined shortcut counterexamples",
]

DECOYS = ("none", "blue", "row0", "both")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 9; broad 9..14 with difficulty weighting",
        "valid": "9..14",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 10 or 11; broad 10..14 with difficulty weighting",
        "valid": "10..14",
        "doc": "Grid width.",
    },
    "K": {
        "type": "int",
        "default": "canonical 4..6; broad 2..6 with difficulty weighting",
        "valid": "2..6",
        "doc": "Number of blue row-0 markers and target area.",
    },
    "n_blobs": {
        "type": "int",
        "default": "3; broad occasionally 2 or 4",
        "valid": "2..4",
        "doc": "Number of eligible nonblue candidate blobs below row 0.",
    },
    "decoy": {
        "type": "enum",
        "default": "none on canonical profile; both on counterexample profile",
        "valid": "none|blue|row0|both",
        "doc": "Exact excluded size-K decoys to include.",
    },
}

# Exact canonical (height, width, K, color->area) profiles.  These reproduce
# profile statistics, not canonical pixels.
_CANONICAL_PROFILES = (
    (9, 10, 5, ((2, 5), (3, 4), (4, 6))),
    (9, 10, 4, ((2, 4), (3, 5), (4, 3))),
    (9, 11, 6, ((2, 5), (3, 6), (4, 4))),
)

_FAVORED = {
    "grid_h": {
        "easy": (9, 9, 10),
        "medium": (9, 10, 11, 12),
        "hard": (11, 12, 13, 14),
    },
    "grid_w": {
        "easy": (10, 10, 11),
        "medium": (10, 11, 12, 13),
        "hard": (12, 13, 14),
    },
    "K": {
        "easy": (2, 3, 3, 4),
        "medium": (3, 4, 4, 5),
        "hard": (4, 5, 5, 6),
    },
    "n_blobs": {
        "easy": (2, 3, 3),
        "medium": (3, 3, 4),
        "hard": (3, 4, 4),
    },
}


@dataclass(frozen=True)
class _Component:
    color: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def touches_row0(self) -> bool:
        return any(row == 0 for row, _ in self.cells)

    @property
    def first(self) -> tuple[int, int]:
        return min(self.cells)


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternate canonical and combined-counterexample teaching profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(sample_index, difficulty, overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    integer_bounds = {
        "grid_h": (9, 14),
        "grid_w": (10, 14),
        "K": (2, 6),
        "n_blobs": (2, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in integer_bounds:
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
            low, high = integer_bounds[name]
            if not low <= value <= high:
                raise ValueError(f"{name} must be in {low}..{high}")
        elif name == "decoy" and value not in DECOYS:
            raise ValueError(f"decoy must be one of {DECOYS}, got {value!r}")


def _axis_int(ctx, name, low, high, defaults):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, tuple(defaults))


def _axis_choice(ctx, name, legal, defaults):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, tuple(legal))
    return ctx.draw_choice(name, tuple(defaults))


def _weighted_domain(name, low, high, difficulty):
    band = difficulty or "medium"
    favored = _FAVORED[name][band]
    return tuple(range(low, high + 1)) + tuple(value for value in favored for _ in range(10))


def _components(grid) -> list[_Component]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    found: list[_Component] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            found.append(_Component(color, tuple(sorted(cells))))
    return found


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def _paint(grid, component: _Component | None):
    output = _blank_like(grid)
    if component is not None:
        for row, col in component.cells:
            output[row][col] = 8
    return output


def _row0_target(grid) -> int:
    return sum(value == 1 for value in grid[0])


def _intended_output(grid):
    target = _row0_target(grid)
    selected = next(
        (
            component
            for component in _components(grid)
            if component.color != 1
            and not component.touches_row0
            and component.size == target
        ),
        None,
    )
    return _paint(grid, selected)


def _rival_count_all_blue(grid):
    target = sum(value == 1 for row in grid for value in row)
    selected = next(
        (
            component
            for component in _components(grid)
            if component.color != 1
            and not component.touches_row0
            and component.size == target
        ),
        None,
    )
    return _paint(grid, selected)


def _rival_include_row0(grid):
    target = _row0_target(grid)
    selected = next(
        (
            component
            for component in _components(grid)
            if component.color != 1 and component.size == target
        ),
        None,
    )
    return _paint(grid, selected)


def _rival_median_candidate(grid):
    candidates = [
        component
        for component in _components(grid)
        if component.color != 1 and not component.touches_row0
    ]
    candidates.sort(key=lambda component: (component.size, component.first))
    selected = candidates[(len(candidates) - 1) // 2] if candidates else None
    return _paint(grid, selected)


def _balanced_sizes(target: int, count: int) -> list[int]:
    choices = sorted(
        (size for size in range(1, 9) if size != target),
        key=lambda size: (abs(size - target), size),
    )
    return [target] + choices[: count - 1]


def _counterexample_sizes(target: int, count: int, rng) -> list[int]:
    below = list(range(1, target))
    above = list(range(target + 1, 9))
    sides = [values for values in (below, above) if len(values) >= count - 1]
    # The declared median rival uses the lower median.  With two candidates,
    # placing every distractor above K would make K itself that lower median.
    # Force the other candidate below K; for 3--4 candidates, either extreme
    # already differs from the rival's middle-ranked choice.
    side = below if count == 2 else rng.choice(sides)
    others = rng.sample(side, count - 1)
    sizes = [target, *others]
    rng.shuffle(sizes)
    return sizes


def _generic_specs(profile, target, count, rng):
    if profile == "counterexample":
        sizes = _counterexample_sizes(target, count, rng)
    else:
        sizes = _balanced_sizes(target, count)
        rng.shuffle(sizes)
    colors = rng.sample(list(range(2, 10)), count)
    return list(zip(colors, sizes))


def _requested_decoy(components, target) -> str:
    blue = any(
        component.color == 1
        and not component.touches_row0
        and component.size == target
        for component in components
    )
    row0 = any(
        component.color != 1
        and component.touches_row0
        and component.size == target
        for component in components
    )
    if blue and row0:
        return "both"
    if blue:
        return "blue"
    if row0:
        return "row0"
    return "none"


def observe_overrides(grid):
    """Recover every advertised semantic control from returned pixels."""
    target = _row0_target(grid)
    found = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "K": target,
        "n_blobs": sum(
            component.color != 1 and not component.touches_row0
            for component in found
        ),
        "decoy": _requested_decoy(found, target),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    core_index = (sample_index // len(SCHEDULE_PROFILES)) % len(_CANONICAL_PROFILES)
    core_h, core_w, core_target, core_specs = _CANONICAL_PROFILES[core_index]

    if profile == "canonical":
        height = _axis_int(ctx, "grid_h", 9, 14, (core_h,))
        width = _axis_int(ctx, "grid_w", 10, 14, (core_w,))
        target = _axis_int(ctx, "K", 2, 6, (core_target,))
        count = _axis_int(ctx, "n_blobs", 2, 4, (3,))
        decoy = _axis_choice(ctx, "decoy", DECOYS, ("none",))
    else:
        height = _axis_int(ctx, "grid_h", 9, 14, _weighted_domain("grid_h", 9, 14, difficulty))
        width = _axis_int(ctx, "grid_w", 10, 14, _weighted_domain("grid_w", 10, 14, difficulty))
        target = _axis_int(ctx, "K", 2, 6, _weighted_domain("K", 2, 6, difficulty))
        count = _axis_int(ctx, "n_blobs", 2, 4, _weighted_domain("n_blobs", 2, 4, difficulty))
        decoy = _axis_choice(ctx, "decoy", DECOYS, ("both",))

    layout_rng = ctx.draw_rng("layout")
    exact_core = (
        profile == "canonical"
        and target == core_target
        and count == 3
        and not any(overrides.get(name) is not None for name in ("K", "n_blobs"))
    )
    candidate_specs = list(core_specs) if exact_core else _generic_specs(
        profile, target, count, layout_rng
    )
    candidate_colors = {color for color, _ in candidate_specs}
    remaining_colors = [color for color in range(2, 10) if color not in candidate_colors]
    row0_decoy_color = layout_rng.choice(remaining_colors) if decoy in ("row0", "both") else None

    expected = {
        "grid_h": height,
        "grid_w": width,
        "K": target,
        "n_blobs": count,
        "decoy": decoy,
    }

    for _attempt in range(200):
        grid = full_grid(height, width, 0)
        row0_decoy_cells: set[tuple[int, int]] = set()
        if row0_decoy_color is not None:
            decoy_col = layout_rng.randrange(width)
            row0_decoy_cells = {(row, decoy_col) for row in range(target)}
            for row, col in row0_decoy_cells:
                grid[row][col] = row0_decoy_color
            excluded = {decoy_col - 1, decoy_col, decoy_col + 1}
            marker_options = [col for col in range(width) if col not in excluded]
        else:
            marker_options = list(range(width))
        if len(marker_options) < target:
            continue
        for col in layout_rng.sample(marker_options, target):
            grid[0][col] = 1

        # Reserving rows 0 and 1 makes every grown lower object at least one
        # blank row away from the marker row.  The row-0 decoy itself is added
        # to `used`, so lower objects also remain isolated from its tail.
        used = {(0, col) for col in range(width)} | {(1, col) for col in range(width)}
        used |= row0_decoy_cells
        specs: list[tuple[str, int, int]] = [
            (f"candidate_{index}", color, size)
            for index, (color, size) in enumerate(candidate_specs)
        ]
        if decoy in ("blue", "both"):
            specs.append(("blue_decoy", 1, target))
        layout_rng.shuffle(specs)
        specs.sort(key=lambda item: item[2], reverse=True)

        placed_all = True
        for _name, color, size in specs:
            cells = grow_blob(
                layout_rng,
                height,
                width,
                used,
                size,
                max_attempts=400,
            )
            if cells is None:
                placed_all = False
                break
            for row, col in cells:
                grid[row][col] = color
            used |= cells
        if not placed_all:
            continue
        if self_check(grid):
            continue
        if observe_overrides(grid) != expected:
            continue
        return grid

    raise RuntimeError(
        "could not construct the requested isolated object layout after 200 attempts"
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty rectangular 2D sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    height = len(grid)
    if not 9 <= height <= 14:
        errors.append(f"grid height {height} outside 9..14")
    if not 10 <= width <= 14:
        errors.append(f"grid width {width} outside 10..14")
    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append(f"cells must be integer ARC colors 0..9; first bad cell {bad_cells[0]}")
        return errors

    target = _row0_target(grid)
    if not 2 <= target <= 6:
        errors.append(f"row 0 must contain K=2..6 blue markers, got {target}")
    found = _components(grid)
    for component in found:
        if component.color == 1 and component.touches_row0:
            if any(row != 0 for row, _ in component.cells):
                errors.append("blue marker objects touching row 0 must stay in row 0")

    candidates = [
        component
        for component in found
        if component.color != 1 and not component.touches_row0
    ]
    if not 2 <= len(candidates) <= 4:
        errors.append(f"expected 2..4 eligible nonblue blobs, got {len(candidates)}")
    sizes = [component.size for component in candidates]
    if len(sizes) != len(set(sizes)):
        errors.append("eligible blob sizes must be pairwise distinct")
    colors = [component.color for component in candidates]
    if len(colors) != len(set(colors)):
        errors.append("eligible blob colors must be pairwise distinct")
    matches = [component for component in candidates if component.size == target]
    if len(matches) != 1:
        errors.append(f"expected exactly one eligible size-K blob, got {len(matches)}")

    blue_decoys = [
        component
        for component in found
        if component.color == 1 and not component.touches_row0
    ]
    if len(blue_decoys) > 1:
        errors.append(f"expected at most one blue lower decoy, got {len(blue_decoys)}")
    if blue_decoys and blue_decoys[0].size != target:
        errors.append(
            f"blue lower decoy must have K={target} cells, got {blue_decoys[0].size}"
        )
    row0_decoys = [
        component
        for component in found
        if component.color != 1 and component.touches_row0
    ]
    if len(row0_decoys) > 1:
        errors.append(f"expected at most one nonblue row-0 decoy, got {len(row0_decoys)}")
    if row0_decoys and row0_decoys[0].size != target:
        errors.append(
            f"nonblue row-0 decoy must have K={target} cells, got {row0_decoys[0].size}"
        )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _blue_witness(grid):
    observed = observe_overrides(grid)["decoy"]
    return observed in ("blue", "both") and _rival_count_all_blue(grid) != _intended_output(grid)


def _row0_witness(grid):
    observed = observe_overrides(grid)["decoy"]
    return observed in ("row0", "both") and _rival_include_row0(grid) != _intended_output(grid)


def _median_witness(grid):
    return _rival_median_candidate(grid) != _intended_output(grid)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "count_all_blue": _rival_count_all_blue,
    "include_row0_size_match": _rival_include_row0,
    "median_candidate_size": _rival_median_candidate,
}
SEMANTIC_WITNESSES = {
    "blue_count_decoy": _blue_witness,
    "row0_size_decoy": _row0_witness,
    "non_median_match": _median_witness,
}
WITNESS_RIVALS = {
    "blue_count_decoy": ["count_all_blue"],
    "row0_size_decoy": ["include_row0_size_match"],
    "non_median_match": ["median_candidate_size"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # pragma: no cover - gate reports exact failure
            reasons.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
