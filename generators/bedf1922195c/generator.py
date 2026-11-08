"""Curriculum generator for ARC task ``bedf1922195c``.

Rule: inspect every 4-connected blue (1) object.  When that object is a
straight horizontal or vertical segment of odd length at least three, recolor
only its middle cell red (2).  All other objects and cells are unchanged.

The canonical examples establish the positive case but do not distinguish
four plausible shortcuts: applying the operation to every color, ignoring
length parity, ignoring straightness, or restricting the rule to the observed
lengths 3 and 5.  Every generated scene includes a length-7 target, while the
scheduled branch profiles pair the other counterexamples so every three-demo
lesson (including any query rotation from four consecutive samples) eliminates
all four shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bedf1922195c"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "6a1fd35b307c"

SUMMARY = (
    "For each blue (1) 4-connected component that is a straight horizontal "
    "or vertical segment of odd length at least 3, recolor only its middle "
    "cell red (2); leave even blue segments, bent blue objects, nonblue "
    "segments, and every other cell unchanged."
)

INVARIANTS = [
    "background is 0 and input color 2 is reserved for the output mark",
    "every generated scene has at least two qualifying odd straight blue segments",
    "every generated scene contains a qualifying length-7 blue segment",
    "nonzero objects are orthogonally separated so component identity is unambiguous",
    "the total input palette is exactly three or four colors, matching canonical support",
    "every scheduled scene contains the length-range witness and exactly two branch counterexamples",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# The branch cycle is deliberately AB, BC, CA (up to rotation).  Thus any three
# consecutive demonstrations cover all three branch rivals; among four
# consecutive samples, removing any one as the query still leaves those rivals
# refuted.  A length-7 target appears in every scene to refute the fourth rival.
_PROFILES_BY_BAND = {
    "easy": (
        "easy_shape_color_8x10_p4",
        "easy_color_parity_11x12_p3",
        "easy_parity_shape_12x13_p4",
    ),
    "medium": (
        "medium_color_parity_9x9_p3",
        "medium_parity_shape_13x14_p3",
        "medium_shape_color_9x11_p3",
    ),
    "hard": (
        "hard_parity_shape_9x10_p3",
        "hard_shape_color_14x16_p4",
        "hard_color_parity_10x10_p3",
    ),
}
SCHEDULE_PROFILES = tuple(
    profile
    for band in ("easy", "medium", "hard")
    for profile in _PROFILES_BY_BAND[band]
)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic three-profile schedule within the selected difficulty band",
        "valid": (
            "easy_shape_color_8x10_p4|easy_color_parity_11x12_p3|"
            "easy_parity_shape_12x13_p4|medium_color_parity_9x9_p3|"
            "medium_parity_shape_13x14_p3|medium_shape_color_9x11_p3|"
            "hard_parity_shape_9x10_p3|hard_shape_color_14x16_p4|"
            "hard_color_parity_10x10_p3"
        ),
    }
}


@dataclass(frozen=True)
class _Profile:
    height: int
    width: int
    palette_size: int
    branch: str


_PROFILE_SPECS = {
    "easy_shape_color_8x10_p4": _Profile(8, 10, 4, "shape_color"),
    "easy_color_parity_11x12_p3": _Profile(11, 12, 3, "color_parity"),
    "easy_parity_shape_12x13_p4": _Profile(12, 13, 4, "parity_shape"),
    "medium_color_parity_9x9_p3": _Profile(9, 9, 3, "color_parity"),
    "medium_parity_shape_13x14_p3": _Profile(13, 14, 3, "parity_shape"),
    "medium_shape_color_9x11_p3": _Profile(9, 11, 3, "shape_color"),
    "hard_parity_shape_9x10_p3": _Profile(9, 10, 3, "parity_shape"),
    "hard_shape_color_14x16_p4": _Profile(14, 16, 4, "shape_color"),
    "hard_color_parity_10x10_p3": _Profile(10, 10, 3, "color_parity"),
}

_BRANCH_SIGNATURES = {
    # (even blue segment, bent odd blue object, nonblue odd straight segment)
    "parity_shape": (True, True, False),
    "shape_color": (False, True, True),
    "color_parity": (True, False, True),
}
_PROFILE_BY_SIGNATURE = {
    (
        spec.height,
        spec.width,
        spec.palette_size,
        _BRANCH_SIGNATURES[spec.branch],
    ): name
    for name, spec in _PROFILE_SPECS.items()
}

Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]


@dataclass(frozen=True)
class _ObjectSpec:
    name: str
    color: int
    variants: tuple[Shape, ...]


def _band(difficulty) -> str:
    """Normalize the public difficulty hint; ``None`` uses the medium band."""
    if difficulty == "easy":
        return "easy"
    if difficulty == "hard":
        return "hard"
    return "medium"


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact cyclic curriculum profile for one ordinary draw."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _normalize(cells: Iterable[Cell]) -> Shape:
    points = tuple(cells)
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def _segment_variants(*lengths: int) -> tuple[Shape, ...]:
    variants: set[Shape] = set()
    for length in lengths:
        variants.add(tuple((0, col) for col in range(length)))
        variants.add(tuple((row, 0) for row in range(length)))
    return tuple(sorted(variants))


_TARGET_VARIANTS = _segment_variants(3, 5)
_LONG_TARGET_VARIANTS = _segment_variants(7)
_EVEN_VARIANTS = _segment_variants(2, 4)
_NONBLUE_SEGMENT_VARIANTS = _segment_variants(3, 5)
_BENT_VARIANTS = tuple(sorted({
    _normalize(((0, 0), (1, 0), (1, 1))),
    _normalize(((0, 0), (0, 1), (1, 0))),
    _normalize(((0, 0), (0, 1), (1, 1))),
    _normalize(((0, 1), (1, 0), (1, 1))),
}))
_NEUTRAL_VARIANTS = tuple(sorted({
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
}))


def _components(grid: Sequence[Sequence[int]], color: int | None = None):
    """Return monochrome 4-connected components as ``(color, cells)`` pairs."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result: list[tuple[int, tuple[Cell, ...]]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0 or (color is not None and value != color) or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (r + dr, c + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == value
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append((value, tuple(sorted(cells))))
    return result


def _is_straight(cells: Sequence[Cell]) -> bool:
    return len({row for row, _ in cells}) == 1 or len({col for _, col in cells}) == 1


def _middle(cells: Sequence[Cell]) -> Cell:
    if len({row for row, _ in cells}) == 1:
        ordered = sorted(cells, key=lambda point: point[1])
    elif len({col for _, col in cells}) == 1:
        ordered = sorted(cells, key=lambda point: point[0])
    else:
        ordered = sorted(cells)
    return ordered[len(ordered) // 2]


def _is_target(cells: Sequence[Cell]) -> bool:
    return len(cells) >= 3 and len(cells) % 2 == 1 and _is_straight(cells)


def rule_mirror(grid: Grid) -> Grid:
    """Pure Python mirror of the pinned Racket rule."""
    out = [list(row) for row in grid]
    for _, cells in _components(grid, 1):
        if _is_target(cells):
            row, col = _middle(cells)
            out[row][col] = 2
    return out


def _any_color_odd_straight(grid: Grid) -> Grid:
    """Rival: apply the midpoint rule to qualifying objects of every color."""
    out = [list(row) for row in grid]
    for color, cells in _components(grid):
        if color != 2 and _is_target(cells):
            row, col = _middle(cells)
            out[row][col] = 2
    return out


def _ignore_parity(grid: Grid) -> Grid:
    """Rival: mark a middle cell of every straight blue segment of length >=2."""
    out = [list(row) for row in grid]
    for _, cells in _components(grid, 1):
        if len(cells) >= 2 and _is_straight(cells):
            row, col = _middle(cells)
            out[row][col] = 2
    return out


def _ignore_straightness(grid: Grid) -> Grid:
    """Rival: mark the row-major middle of every odd blue object."""
    out = [list(row) for row in grid]
    for _, cells in _components(grid, 1):
        if len(cells) >= 3 and len(cells) % 2 == 1:
            row, col = sorted(cells)[len(cells) // 2]
            out[row][col] = 2
    return out


def _only_lengths_3_or_5(grid: Grid) -> Grid:
    """Rival: apply the rule only to target lengths seen in canonical examples."""
    out = [list(row) for row in grid]
    for _, cells in _components(grid, 1):
        if len(cells) in (3, 5) and _is_straight(cells):
            row, col = _middle(cells)
            out[row][col] = 2
    return out


def _has_even_blue_segment(grid: Grid) -> bool:
    return any(
        len(cells) >= 2 and len(cells) % 2 == 0 and _is_straight(cells)
        for _, cells in _components(grid, 1)
    )


def _has_bent_odd_blue(grid: Grid) -> bool:
    return any(
        len(cells) >= 3 and len(cells) % 2 == 1 and not _is_straight(cells)
        for _, cells in _components(grid, 1)
    )


def _has_nonblue_odd_segment(grid: Grid) -> bool:
    return any(
        color not in (0, 1, 2)
        and len(cells) >= 3
        and len(cells) % 2 == 1
        and _is_straight(cells)
        for color, cells in _components(grid)
    )


def _has_length_seven_blue_segment(grid: Grid) -> bool:
    return any(
        len(cells) == 7 and _is_straight(cells)
        for _, cells in _components(grid, 1)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "even_blue_segment": _has_even_blue_segment,
    "bent_odd_blue": _has_bent_odd_blue,
    "nonblue_odd_segment": _has_nonblue_odd_segment,
    "length_seven_blue_segment": _has_length_seven_blue_segment,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "any_color_odd_straight": _any_color_odd_straight,
    "ignore_parity": _ignore_parity,
    "ignore_straightness": _ignore_straightness,
    "only_lengths_3_or_5": _only_lengths_3_or_5,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    "nonblue_odd_segment": ["any_color_odd_straight"],
    "even_blue_segment": ["ignore_parity"],
    "bent_odd_blue": ["ignore_straightness"],
    "length_seven_blue_segment": ["only_lengths_3_or_5"],
}
# Convenience inverse used by the task-local regression probes.
RIVAL_WITNESSES = {
    rival: witness
    for witness, rivals in WITNESS_RIVALS.items()
    for rival in rivals
}


@lru_cache(maxsize=None)
def _candidate_options(
    variants: tuple[Shape, ...], height: int, width: int
) -> tuple[frozenset[Cell], ...]:
    """Cache immutable translations; generation randomizes only traversal order."""
    options: set[frozenset[Cell]] = set()
    for shape in variants:
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(col for _, col in shape) + 1
        for top in range(height - shape_height + 1):
            for left in range(width - shape_width + 1):
                options.add(
                    frozenset((top + row, left + col) for row, col in shape)
                )
    return tuple(sorted(options, key=lambda cells: tuple(sorted(cells))))


def _expanded(cells: frozenset[Cell], height: int, width: int) -> frozenset[Cell]:
    expanded = set(cells)
    for row, col in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + dr, col + dc)
            if 0 <= neighbor[0] < height and 0 <= neighbor[1] < width:
                expanded.add(neighbor)
    return frozenset(expanded)


def _place_objects(
    specs: Sequence[_ObjectSpec],
    height: int,
    width: int,
    ctx,
) -> dict[str, frozenset[Cell]]:
    """Exhaustively place all objects with an orthogonal gap between them.

    Translation tables are cached and traversed from keyed cyclic offsets.  This
    keeps large checker batteries fast without introducing a retry cap: every
    candidate remains reachable before the search can declare infeasibility.
    """
    ordered_specs = tuple(
        sorted(
            specs,
            key=lambda spec: (-max(len(shape) for shape in spec.variants), spec.name),
        )
    )
    options = {
        spec.name: _candidate_options(spec.variants, height, width)
        for spec in ordered_specs
    }
    traversal: dict[str, tuple[int, int]] = {}
    for spec in ordered_specs:
        count = len(options[spec.name])
        rng = ctx.draw_rng(f"placement_{spec.name}")
        traversal[spec.name] = (rng.randrange(count), rng.choice((-1, 1)))

    def search(
        index: int,
        blocked: frozenset[Cell],
        placed: dict[str, frozenset[Cell]],
    ) -> dict[str, frozenset[Cell]] | None:
        if index == len(ordered_specs):
            return dict(placed)
        spec = ordered_specs[index]
        choices = options[spec.name]
        start, direction = traversal[spec.name]
        for offset in range(len(choices)):
            cells = choices[(start + direction * offset) % len(choices)]
            if not cells.isdisjoint(blocked):
                continue
            placed[spec.name] = cells
            answer = search(
                index + 1,
                blocked | _expanded(cells, height, width),
                placed,
            )
            if answer is not None:
                return answer
            del placed[spec.name]
        return None

    answer = search(0, frozenset(), {})
    if answer is None:
        raise RuntimeError(
            f"constructive placement failed for {height}x{width} profile; "
            "declared scene grammar is infeasible"
        )
    return answer


def _object_specs(profile: _Profile, ctx) -> tuple[_ObjectSpec, ...]:
    palette_rng = ctx.draw_rng("palette")
    distractor_colors = tuple(palette_rng.sample(range(3, 10), profile.palette_size - 2))
    specs: list[_ObjectSpec] = [
        _ObjectSpec("target_a", 1, _LONG_TARGET_VARIANTS),
        _ObjectSpec("target_b", 1, _TARGET_VARIANTS),
    ]

    branch = profile.branch
    if branch in ("parity_shape", "color_parity"):
        specs.append(_ObjectSpec("even_blue", 1, _EVEN_VARIANTS))
    if branch in ("parity_shape", "shape_color"):
        specs.append(_ObjectSpec("bent_blue", 1, _BENT_VARIANTS))
    if branch in ("shape_color", "color_parity"):
        specs.append(
            _ObjectSpec("nonblue_odd", distractor_colors[0], _NONBLUE_SEGMENT_VARIANTS)
        )
        unused_colors = distractor_colors[1:]
    else:
        unused_colors = distractor_colors

    for index, color in enumerate(unused_colors):
        specs.append(_ObjectSpec(f"neutral_{index}", color, _NEUTRAL_VARIANTS))
    return tuple(specs)


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    requested = overrides.get("scene_profile")
    if requested is None:
        requested = schedule_profile(seed, sample_index, difficulty)
    if not isinstance(requested, str) or requested not in _PROFILE_SPECS:
        raise ValueError(
            "scene_profile must be one of: " + ", ".join(SCHEDULE_PROFILES)
        )

    # Feeding the exact scheduled value through GenCtx preserves public draw
    # provenance and makes explicit overrides obey the same validity gate.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={"scene_profile": requested},
    )
    profile_name = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    profile = _PROFILE_SPECS[profile_name]
    specs = _object_specs(profile, ctx)
    placements = _place_objects(specs, profile.height, profile.width, ctx)

    grid = full_grid(profile.height, profile.width, 0)
    for spec in specs:
        for row, col in placements[spec.name]:
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement collision")
            grid[row][col] = spec.color
    return grid


def _branch_signature(grid: Grid) -> tuple[bool, bool, bool]:
    return (
        _has_even_blue_segment(grid),
        _has_bent_odd_blue(grid),
        _has_nonblue_odd_segment(grid),
    )


def observe_overrides(grid: Grid) -> dict[str, str]:
    """Recover the exact scene profile from returned pixels alone."""
    signature = (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
        _branch_signature(grid),
    )
    try:
        profile = _PROFILE_BY_SIGNATURE[signature]
    except KeyError as exc:
        raise ValueError(f"grid does not match a declared scene profile: {signature}") from exc
    return {"scene_profile": profile}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical rule manifold without replaying canonical layouts."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colors 0..9 (not bool)"]

    errors: list[str] = []
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 is absent")
    if 2 in palette:
        errors.append("input color 2 is reserved for output midpoint marks")
    if len(palette) not in (3, 4):
        errors.append(f"input palette must contain exactly 3 or 4 colors, found {len(palette)}")
    if not any(value not in (0, 1, 2) for value in palette):
        errors.append("at least one nonblue distractor color is required")

    qualifying = [cells for _, cells in _components(grid, 1) if _is_target(cells)]
    if len(qualifying) < 2:
        errors.append(
            f"need at least two qualifying odd straight blue segments, found {len(qualifying)}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted grid is a truthful member of the declared rule manifold."""
    return self_check(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every named canonical-fitting rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the midpoint-rule teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact pinned transformation")
            continue
        valid_demos.append(demo)

    if len(valid_demos) < EXAMPLES_NEEDED:
        reasons.append(
            f"only {len(valid_demos)} valid demonstrations remain; need {EXAMPLES_NEEDED}"
        )
    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"named competitor {name!r} survives every demonstration")
    return reasons
