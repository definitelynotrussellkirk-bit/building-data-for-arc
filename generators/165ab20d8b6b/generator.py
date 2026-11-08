"""Input generator for the orthogonal-contact-shell ARC task.

The selected Racket rule erases each non-zero 4-connected blob and paints every
zero cell touching that blob in a cardinal direction with the blob's color.
Outputs remain authoritative in Racket; ``rule_mirror`` is an independently
readable Python oracle used only by review tests and semantic probes.

The sampler deliberately includes enclosed background holes.  They distinguish
the intended rule from the strongest canonical shortcut: paint only shell cells
connected to the exterior background.  All four canonical examples happen to
contain only exterior background, so that rival fits every supplied label.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "165ab20d8b6b"
TASK_ID = GENERATOR_ID
RULE_HASH = "63879e6d755e"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains 1..4 isolated, distinctly colored, interior "
    "4-connected blobs.  Erase each blob and paint all zero cells immediately "
    "adjacent to it in the four cardinal directions with that blob's color.  "
    "Generated lessons include ordinary canonical-scale blobs, smaller broad-"
    "support blobs, and 3x3 ring blobs whose enclosed center is also painted."
)

INVARIANTS = [
    "background is color 0 and every blob color is in 1..9",
    "1..4 distinctly colored 4-connected blobs lie strictly inside the border",
    "each blob has 2..8 cells and a non-empty zero orthogonal shell",
    "blob shells are pairwise disjoint, so every output cell has one owner",
    "the selected Racket rule, not this module, remains label authority",
]

SCENE_PROFILES = ("canonical", "broad", "hole_witness")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled across 8..14; canonical dimensions recur",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled across 9..16; canonical dimensions recur",
        "valid": "9..16",
    },
    "n_blobs": {
        "type": "int",
        "default": "scheduled across 1..4; two-color scenes recur",
        "valid": "1..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "canonical|broad|hole_witness; two hole witnesses per 4 samples",
        "valid": "canonical|broad|hole_witness",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))

# Ordinary, simply connected shapes.  The fallback uses the first triomino,
# which is small enough that four copies fit at the minimum 8x9 dimensions.
_L3 = frozenset({(0, 0), (1, 0), (1, 1)})
_I3 = frozenset({(0, 0), (0, 1), (0, 2)})
_O4 = frozenset({(0, 0), (0, 1), (1, 0), (1, 1)})
_T4 = frozenset({(0, 0), (0, 1), (0, 2), (1, 1)})
_L4 = frozenset({(0, 0), (1, 0), (2, 0), (2, 1)})
_Z4 = frozenset({(0, 1), (0, 2), (1, 0), (1, 1)})
_P5 = frozenset({(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)})
_V5 = frozenset({(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})
_T5 = frozenset({(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)})
_CANONICAL_SHAPES = (_L3, _I3, _O4, _T4, _L4, _Z4, _P5, _V5, _T5)
_DOMINO = frozenset({(0, 0), (0, 1)})
_RING = frozenset(
    (row, col)
    for row in range(3)
    for col in range(3)
    if (row, col) != (1, 1)
)

# Default dimensions cycle through the four canonical profiles and four broader
# profiles.  Overrides still accept every documented integer in every band.
_DIMENSION_CYCLE = (
    (8, 9),
    (9, 10),
    (10, 10),
    (9, 11),
    (11, 12),
    (12, 13),
    (13, 15),
    (14, 16),
)
_BLOB_COUNT_CYCLE = (2, 2, 2, 3, 2, 4, 2, 1)
_PROFILE_CYCLE = (
    "hole_witness",
    "canonical",
    "hole_witness",
    "broad",
)
SCHEDULE_PROFILES = SCENE_PROFILES
EXAMPLES_NEEDED = 3


def _scheduled_choice(ctx, label: str, domain: Sequence, desired):
    """Record a full-domain keyed draw while selecting a pinned schedule value.

    ``GenCtx.draw_choice`` chooses one index from a fresh label-keyed RNG.  We
    predict that index with another fresh RNG and place ``desired`` there.  The
    complete legal domain is still presented to ``draw_choice`` (so every exact
    override is accepted and provenance is truthful), while default lessons get
    a stable coverage schedule rather than probabilistic branch starvation.
    """
    values = list(domain)
    if desired not in values:
        raise ValueError(f"scheduled value {desired!r} is not legal for {label}")
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, tuple(values))
    chosen_index = ctx.draw_rng(label).randrange(len(values))
    desired_index = values.index(desired)
    values[chosen_index], values[desired_index] = (
        values[desired_index],
        values[chosen_index],
    )
    return ctx.draw_choice(label, tuple(values))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the default semantic branch for schedule-coverage diagnostics."""
    del seed, difficulty
    return _PROFILE_CYCLE[sample_index % len(_PROFILE_CYCLE)]


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_blobs"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    profile = overrides.get("scene_profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("scene_profile must be a string")


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = tuple(cells)
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return frozenset((row - top, col - left) for row, col in points)


def _variants(shape: frozenset[tuple[int, int]]) -> tuple[frozenset, ...]:
    variants: set[frozenset[tuple[int, int]]] = set()
    for reflected in (False, True):
        points = [(-row if reflected else row, col) for row, col in shape]
        for _ in range(4):
            variants.add(_normalize(points))
            points = [(col, -row) for row, col in points]
    return tuple(sorted(variants, key=lambda item: sorted(item)))


def _shell(
    cells: frozenset[tuple[int, int]], height: int, width: int
) -> frozenset[tuple[int, int]]:
    return frozenset(
        (row + dr, col + dc)
        for row, col in cells
        for dr, dc in CARDINAL
        if 0 <= row + dr < height
        and 0 <= col + dc < width
        and (row + dr, col + dc) not in cells
    )


def _placement_candidates(shape, height: int, width: int):
    seen: set[frozenset[tuple[int, int]]] = set()
    candidates = []
    for variant in _variants(shape):
        shape_h = max(row for row, _ in variant) + 1
        shape_w = max(col for _, col in variant) + 1
        # Strictly interior: the shape's bounding box starts at >=1 and ends
        # at <=height-2 / width-2, leaving room for its entire shell.
        for top in range(1, height - shape_h):
            for left in range(1, width - shape_w):
                cells = frozenset(
                    (top + row, left + col) for row, col in variant
                )
                if cells in seen:
                    continue
                seen.add(cells)
                candidates.append((cells, _shell(cells, height, width)))
    return candidates


def _pack_shapes(shapes, height: int, width: int, rng):
    candidate_sets = []
    for shape in shapes:
        candidates = _placement_candidates(shape, height, width)
        rng.shuffle(candidates)
        candidate_sets.append(candidates)
    if any(not candidates for candidates in candidate_sets):
        return None

    # Place the most constrained shape first, but restore caller order before
    # coloring so palette assignment is stable and profile-leading shapes stay
    # easy to inspect.
    order = sorted(range(len(shapes)), key=lambda index: len(candidate_sets[index]))
    selected: list[tuple[frozenset, frozenset] | None] = [None] * len(shapes)

    def search(position: int, occupied: frozenset, used_shell: frozenset) -> bool:
        if position == len(order):
            return True
        shape_index = order[position]
        for cells, shell in candidate_sets[shape_index]:
            if (
                cells & occupied
                or cells & used_shell
                or shell & occupied
                or shell & used_shell
            ):
                continue
            selected[shape_index] = (cells, shell)
            if search(position + 1, occupied | cells, used_shell | shell):
                return True
            selected[shape_index] = None
        return False

    if not search(0, frozenset(), frozenset()):
        return None
    return [item[0] for item in selected if item is not None]


def _shape_plan(profile: str, n_blobs: int, difficulty, rng):
    if profile == "hole_witness":
        # Ring + dominoes is constructively feasible even at 8x9 with four
        # blobs, and the ring's center supplies the semantic counterexample.
        return [_RING] + [_DOMINO] * (n_blobs - 1), [
            _RING
        ] + [_DOMINO] * (n_blobs - 1)
    if profile == "broad":
        extras = [rng.choice(_CANONICAL_SHAPES) for _ in range(n_blobs - 1)]
        return [_DOMINO] + extras, [_DOMINO] + [_L3] * (n_blobs - 1)

    # Hard scenes favor the larger half of the ordinary library; easy scenes
    # favor triomino/tetromino shapes.  This is an undeclared texture choice,
    # not an exact control, and has a guaranteed all-L fallback.
    if difficulty == "easy":
        pool = _CANONICAL_SHAPES[:6]
    elif difficulty == "hard":
        pool = _CANONICAL_SHAPES[2:]
    else:
        pool = _CANONICAL_SHAPES
    return [rng.choice(pool) for _ in range(n_blobs)], [_L3] * n_blobs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _DIMENSION_CYCLE[
        sample_index % len(_DIMENSION_CYCLE)
    ]
    height = _scheduled_choice(ctx, "grid_h", tuple(range(8, 15)), scheduled_h)
    width = _scheduled_choice(ctx, "grid_w", tuple(range(9, 17)), scheduled_w)
    n_blobs = _scheduled_choice(
        ctx,
        "n_blobs",
        (1, 2, 3, 4),
        _BLOB_COUNT_CYCLE[sample_index % len(_BLOB_COUNT_CYCLE)],
    )
    profile = _scheduled_choice(
        ctx,
        "scene_profile",
        SCENE_PROFILES,
        _PROFILE_CYCLE[sample_index % len(_PROFILE_CYCLE)],
    )

    shape_rng = ctx.draw_rng("shape_texture")
    primary, fallback = _shape_plan(profile, n_blobs, difficulty, shape_rng)
    placement_rng = ctx.draw_rng("placement")
    placements = _pack_shapes(primary, height, width, placement_rng)
    if placements is None and primary != fallback:
        placements = _pack_shapes(
            fallback, height, width, ctx.draw_rng("fallback_placement")
        )
    if placements is None:
        raise ValueError(
            f"could not construct {profile} with {n_blobs} blobs in "
            f"{height}x{width}"
        )

    colors = ctx.draw_rng("palette").sample(range(1, 10), n_blobs)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in zip(colors, placements):
        for row, col in cells:
            grid[row][col] = color
    findings = self_check(grid)
    if findings:
        raise RuntimeError(
            "constructive generator violated its own contract: " + "; ".join(findings)
        )
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                r, c = stack.pop()
                for dr, dc in CARDINAL:
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        cells.add(point)
                        stack.append(point)
            result.append((color, frozenset(cells)))
    return result


def _grid_validation(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a non-empty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a non-empty rectangular grid"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors in 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _grid_validation(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14:
        errors.append(f"grid height {height} outside 8..14")
    if not 9 <= width <= 16:
        errors.append(f"grid width {width} outside 9..16")

    components = _components(grid)
    if not 1 <= len(components) <= 4:
        errors.append(f"expected 1..4 blobs, found {len(components)}")
    colors = [color for color, _ in components]
    if len(set(colors)) != len(colors):
        errors.append("each color must form exactly one connected blob")

    shells = []
    for color, cells in components:
        if not 2 <= len(cells) <= 8:
            errors.append(
                f"blob color {color} has size {len(cells)}, expected 2..8"
            )
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        ):
            errors.append(f"blob color {color} touches the border")
        for row, col in cells:
            for dr, dc in CARDINAL:
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] not in (0, color)
                ):
                    errors.append(
                        f"blob color {color} touches another blob orthogonally"
                    )
                    break
            else:
                continue
            break
        shell = frozenset(
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in CARDINAL
            if 0 <= row + dr < height
            and 0 <= col + dc < width
            and (row + dr, col + dc) not in cells
            and grid[row + dr][col + dc] == 0
        )
        if not shell:
            errors.append(f"blob color {color} has no zero orthogonal shell")
        shells.append((color, shell))

    for index, (color, shell) in enumerate(shells):
        for other_color, other_shell in shells[:index]:
            overlap = shell & other_shell
            if overlap:
                errors.append(
                    f"shells for colors {other_color} and {color} overlap at "
                    f"{sorted(overlap)[:3]}"
                )
    return errors


def strict_canonical_like(grid):
    """Accept canonical inputs and every lawful point on this sampler's manifold."""
    return self_check(grid)


def rule_mirror(grid):
    """Pure Python mirror of the selected rule; never used as label authority."""
    errors = _grid_validation(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in _components(grid):
        for row, col in _shell(cells, height, width):
            if grid[row][col] == 0:
                output[row][col] = color
    return output


def _exterior_background(grid):
    height, width = len(grid), len(grid[0])
    todo = deque(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
        and (row in (0, height - 1) or col in (0, width - 1))
    )
    seen = set(todo)
    while todo:
        row, col = todo.popleft()
        for dr, dc in CARDINAL:
            point = (row + dr, col + dc)
            if (
                0 <= point[0] < height
                and 0 <= point[1] < width
                and point not in seen
                and grid[point[0]][point[1]] == 0
            ):
                seen.add(point)
                todo.append(point)
    return frozenset(seen)


def _enclosed_background(grid):
    zeros = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0
    }
    return frozenset(zeros - _exterior_background(grid))


def _has_enclosed_hole(grid):
    if _grid_validation(grid):
        return False
    return bool(_enclosed_background(grid))


def _external_shell_only(grid):
    """Plausible wrong rule: ignore shell cells in enclosed background holes."""
    errors = _grid_validation(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    exterior = _exterior_background(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in _components(grid):
        for row, col in _shell(cells, height, width) & exterior:
            if grid[row][col] == 0:
                output[row][col] = color
    return output


def observe_overrides(grid):
    """Recover every exact advertised axis from pixels alone."""
    findings = self_check(grid)
    if findings:
        raise ValueError("; ".join(findings))
    components = _components(grid)
    if _has_enclosed_hole(grid):
        profile = "hole_witness"
    elif any(not 3 <= len(cells) <= 5 for _, cells in components):
        profile = "broad"
    else:
        profile = "canonical"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(components),
        "scene_profile": profile,
    }


def lesson_identifiable(demos, query):
    """Require the demonstrations to refute every declared lesson competitor."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"{name} fits every demonstration")
    return reasons


SEMANTIC_WITNESSES = {"enclosed_hole": _has_enclosed_hole}
SEMANTIC_RIVALS = {"external_shell_only": _external_shell_only}
WITNESS_RIVALS = {"enclosed_hole": ["external_shell_only"]}
CANONICAL_SHORTCUTS = {"external_shell_only": _external_shell_only}
LESSON_COMPETITORS = {"external_shell_only": _external_shell_only}
