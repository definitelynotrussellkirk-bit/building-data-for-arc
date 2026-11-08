"""Generator for ARC family ``ea32f347`` / task ``fe947dc3e12c``.

The selected rule finds the three non-background 4-connected components,
orders them by *cell count* from largest to smallest, and recolors those ranks
1, 4, and 2.  Canonical examples contain straight color-5 bars, which makes a
bounding-box-area shortcut indistinguishable from the intended measurement.
The ordinary two-slot schedule therefore alternates canonical bar scenes with
lawful non-rectangular witnesses where cell count and bounding-box area rank
objects differently.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fe947dc3e12c"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "0ef10b0042c4"
SUMMARY = (
    "Exactly three separated, differently-sized nonzero components are "
    "recolored by descending cell count as 1/4/2. The default schedule "
    "alternates straight bars with a bounding-box counterexample."
)

INVARIANTS = [
    "background is 0",
    "exactly three non-background 4-connected components",
    "each component is monochromatic and component sizes are strictly distinct",
    "supported size profiles are the three profiles present in the ARC family",
]

PALETTE_MODES = ("canonical", "varied")
TEXTURES = ("bars", "bbox_witness")
SCHEDULE_PROFILES = TEXTURES
LESSON_SCHEDULE_PERIOD = 2
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "every fourth slot 10; otherwise difficulty-aware 9..14",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "every fourth slot 10; otherwise difficulty-aware 9..16",
        "valid": "9..16",
    },
    "palette_mode": {
        "type": "str",
        "default": "canonical",
        "valid": "|".join(PALETTE_MODES),
    },
    "texture": {
        "type": "str",
        "default": "sample_index alternating schedule",
        "valid": "|".join(TEXTURES),
    },
}

_CANONICAL_SIZE_PROFILES = ((6, 5, 3), (6, 4, 2), (7, 5, 4))
_GENERATED_SIZE_PROFILE = (6, 5, 3)
_OUTPUT_COLORS = (1, 4, 2)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_scalars(seed, sample_index, difficulty) -> None:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool/float/string)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError(
            "sample_index must be a nonnegative integer (not bool/float/string)"
        )
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    _validate_scalars(seed, sample_index, difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, (lo, hi) in {"grid_h": (9, 14), "grid_w": (9, 16)}.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(
                f"{name} must be an integer in {lo}..{hi} (not bool/float/string)"
            )
    palette_mode = overrides.get("palette_mode")
    if palette_mode is not None and (
        type(palette_mode) is not str or palette_mode not in PALETTE_MODES
    ):
        raise ValueError(f"palette_mode must be one of {PALETTE_MODES}")
    texture = overrides.get("texture")
    if texture is not None and (type(texture) is not str or texture not in TEXTURES):
        raise ValueError(f"texture must be one of {TEXTURES}")


def schedule_profile(seed, sample_index, difficulty=None):
    """The production lesson schedule: bars, witness, bars, witness, ..."""
    _validate_scalars(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _components(grid):
    """Color-blind nonzero 4-connected components, in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    groups: list[set[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in _DIRS4:
                    nxt = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            groups.append(cells)
    return groups


def _bbox_area(cells: Iterable[tuple[int, int]]) -> int:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _component_colors(grid, cells):
    return {grid[row][col] for row, col in cells}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return reasons when a grid is outside the supported task domain."""
    if type(grid) is not list or not grid:
        return ["expected a nonempty list of rows"]
    if type(grid[0]) is not list or not grid[0]:
        return ["expected nonempty list rows"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular list rows"]
    height = len(grid)
    if not (9 <= height <= 14 and 9 <= width <= 16):
        return [f"grid dimensions {height}x{width} outside 9..14 x 9..16"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid colors must be integer values 0..9 (not bool)"]

    groups = _components(grid)
    if len(groups) != 3:
        return [f"expected exactly 3 non-background components, found {len(groups)}"]
    mixed = [index for index, cells in enumerate(groups) if len(_component_colors(grid, cells)) != 1]
    if mixed:
        return [f"components must be monochromatic; mixed component indices {mixed}"]
    sizes = tuple(sorted((len(cells) for cells in groups), reverse=True))
    if len(set(sizes)) != 3:
        return [f"component sizes must be strictly distinct, got {sizes}"]
    if sizes not in _CANONICAL_SIZE_PROFILES:
        return [
            f"unsupported component size profile {sizes}; expected one of "
            f"{_CANONICAL_SIZE_PROFILES}"
        ]
    return []


def strict_canonical_like(grid) -> list[str]:
    """Canonical-scale/palette support, allowing topology needed to teach size."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 10 or len(grid[0]) != 10:
        return ["strict profile requires the canonical 10x10 canvas"]
    foreground = {value for row in grid for value in row if value != 0}
    if foreground != {5}:
        return ["strict profile requires canonical foreground color 5"]
    return []


def _normalized_shape(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_variants(shape):
    """All distinct dihedral transforms of a finite cell shape."""
    variants = set()
    for reflected in (False, True):
        for rotations in range(4):
            transformed = []
            for row, col in shape:
                if reflected:
                    col = -col
                for _ in range(rotations):
                    row, col = col, -row
                transformed.append((row, col))
            variants.add(_normalized_shape(transformed))
    return tuple(sorted(variants))


def _candidate_placements(shape, height, width):
    placements = []
    for variant in _shape_variants(shape):
        shape_h = max(row for row, _ in variant) + 1
        shape_w = max(col for _, col in variant) + 1
        for top in range(height - shape_h + 1):
            for left in range(width - shape_w + 1):
                placements.append(
                    frozenset((top + row, left + col) for row, col in variant)
                )
    return placements


def _separated(candidate, used) -> bool:
    return not any(
        (row + dr, col + dc) in used
        for row, col in candidate
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_shapes(rng, height, width, shapes, colors):
    candidate_sets = []
    for shape in shapes:
        candidates = _candidate_placements(shape, height, width)
        rng.shuffle(candidates)
        candidate_sets.append(candidates)

    chosen = []

    def search(index, used):
        if index == len(candidate_sets):
            return True
        for cells in candidate_sets[index]:
            if _separated(cells, used):
                chosen.append(cells)
                if search(index + 1, used | set(cells)):
                    return True
                chosen.pop()
        return False

    if not search(0, set()):
        raise ValueError(f"could not place the three components on {height}x{width}")
    grid = full_grid(height, width, 0)
    for cells, color in zip(chosen, colors):
        for row, col in cells:
            grid[row][col] = color
    return grid


def _draw_dimension(ctx, name, sample_index, difficulty):
    limits = {"grid_h": (9, 14), "grid_w": (9, 16)}
    lo, hi = limits[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    # Five of every twenty production slots are exact 10x10 canonical-profile
    # supports. Other slots exercise the declared dimensions and make the
    # difficulty control observable without changing task semantics.
    if sample_index % 4 == 0:
        return ctx.draw_int(name, 10, 10)
    bands = {
        "grid_h": {
            "easy": (9, 10), "medium": (10, 12), "hard": (12, 14), None: (9, 14),
        },
        "grid_w": {
            "easy": (9, 11), "medium": (10, 13), "hard": (14, 16), None: (9, 16),
        },
    }
    draw_lo, draw_hi = bands[name][difficulty]
    return ctx.draw_int(name, draw_lo, draw_hi)


def _draw_choice_axis(ctx, name, domain, default):
    options = domain if ctx.overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


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
    height = _draw_dimension(ctx, "grid_h", sample_index, difficulty)
    width = _draw_dimension(ctx, "grid_w", sample_index, difficulty)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    texture = _draw_choice_axis(ctx, "texture", TEXTURES, scheduled)
    palette_mode = _draw_choice_axis(ctx, "palette_mode", PALETTE_MODES, "canonical")

    if texture == "bars":
        shapes = (
            tuple((0, col) for col in range(6)),
            tuple((0, col) for col in range(5)),
            tuple((0, col) for col in range(3)),
        )
    else:
        # Sizes 6, 5, 3; bbox areas 6, 8, 4.  Thus bbox area ranks the
        # five-cell elbow ahead of the six-cell line, unlike cell count.
        shapes = (
            tuple((0, col) for col in range(6)),
            ((0, 0), (1, 0), (1, 1), (1, 2), (1, 3)),
            ((0, 0), (1, 0), (1, 1)),
        )

    if palette_mode == "canonical":
        colors = (5, 5, 5)
    else:
        palette_rng = ctx.draw_rng("palette")
        colors = tuple(palette_rng.sample((3, 5, 6, 7, 8, 9), 3))

    grid = _place_shapes(ctx.draw_rng("layout"), height, width, shapes, colors)
    errors = self_check(grid)
    if errors:
        raise ValueError(f"internal generation violated self_check: {errors}")
    return grid


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe invalid grid: {errors}")
    groups = _components(grid)
    is_line = [
        len({row for row, _ in cells}) == 1 or len({col for _, col in cells}) == 1
        for cells in groups
    ]
    foreground = {value for row in grid for value in row if value}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_mode": "canonical" if foreground == {5} else "varied",
        "texture": "bars" if all(is_line) else "bbox_witness",
    }


def _recolor_by_order(grid, groups):
    result = [row[:] for row in grid]
    for color, cells in zip(_OUTPUT_COLORS, groups):
        for row, col in cells:
            result[row][col] = color
    return result


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"outside rule_mirror domain: {errors}")
    groups = sorted(_components(grid), key=lambda cells: (-len(cells), min(cells)))
    return _recolor_by_order(grid, groups)


def _bbox_area_rival(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"outside bbox rival domain: {errors}")
    groups = sorted(_components(grid), key=lambda cells: (-_bbox_area(cells), min(cells)))
    return _recolor_by_order(grid, groups)


def _cell_count_not_bbox_area(grid):
    return rule_mirror(grid) != _bbox_area_rival(grid)


SEMANTIC_WITNESSES = {"cell_count_not_bbox_area": _cell_count_not_bbox_area}
SEMANTIC_RIVALS = {"bbox_area_rank": _bbox_area_rival}
WITNESS_RIVALS = {"cell_count_not_bbox_area": ["bbox_area_rank"]}
CANONICAL_SHORTCUTS = {"bbox_area_rank": _bbox_area_rival}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a universal induction claim."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
