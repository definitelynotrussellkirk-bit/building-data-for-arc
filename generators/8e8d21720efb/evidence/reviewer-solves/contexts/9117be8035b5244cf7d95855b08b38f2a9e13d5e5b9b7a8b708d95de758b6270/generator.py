"""Teaching generator for ARC task 8e8d21720efb — remove isolated cells.

The unchanged Racket authority keeps a nonzero cell exactly when at least one
cardinal neighbour has the same colour.  Version 2 replaces the old fixed four-
object scatter with a source-bound two-profile curriculum:

* ``canonical`` profiles preserve the five linked public dimension/component-
  size patterns while varying colours, placements, shapes, and orientations;
* ``witness`` profiles simultaneously distinguish local same-colour cardinal
  adjacency from global colour frequency, 8-neighbour adjacency, arbitrary
  nonzero adjacency, identity, and one-axis-only shortcuts.

The default schedule alternates these profiles.  Three demonstrations plus one
query therefore contain two witness profiles, so every single-query rotation
retains a witness after one pair is held out.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8e8d21720efb"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "76b667ae03a8"

SUMMARY = (
    "Keep each nonzero cell iff it has a same-colour cardinal neighbour. "
    "Alternating canonical-linked and counterexample-rich profiles teach that "
    "the condition is local, same-colour, and 4-connected rather than a global "
    "colour-frequency, 8-neighbour, arbitrary-contact, or one-axis rule."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 10
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0; all cells are integer ARC colours 0..9",
    "canonical profiles contain 1..3 size-2/3 blobs and 1..2 isolated singletons in distinct colours",
    "witness profiles contain horizontal and vertical blobs plus five same-colour-singleton components",
    "every witness has a blob-colour singleton, a same-colour diagonal pair, and a different-colour cardinal pair",
    "three consecutive default demonstrations contain at least one witness; every four-pair rotation window contains two",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "ten-slot linked schedule spanning 7..12",
        "valid": "7..12",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "ten-slot linked schedule spanning 8..13",
        "valid": "8..13",
        "doc": "Returned grid width.",
    },
    "lesson_profile": {
        "type": "str",
        "default": "alternating canonical|witness",
        "valid": "canonical|witness",
        "doc": "Observable structural curriculum profile.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),             (0, 1),
    (1, -1),  (1, 0),    (1, 1),
)
_AXIS_BOUNDS = {"grid_h": (7, 12), "grid_w": (8, 13)}
_PROFILE_NAMES = ("canonical", "witness")

# Linked public profiles: (height, width, sorted same-colour component sizes).
# These are empirical shape/count envelopes, not copied canonical grids.
_CANONICAL_CASES = (
    (8, 9, (1, 1, 2, 3)),
    (7, 10, (1, 1, 2, 2)),
    (9, 9, (1, 2, 3)),
    (8, 8, (1, 1, 3)),
    (9, 10, (1, 2, 2, 3)),
)
_CANONICAL_SIGNATURES = {
    (h, w): sizes for h, w, sizes in _CANONICAL_CASES
}

# Odd slots use broader dimensions while even slots preserve exact public
# dimension profiles.  The profile alternation itself is band-independent.
_WITNESS_DIMS = {
    "easy": ((7, 8), (8, 9), (7, 10), (8, 8), (9, 9)),
    "medium": ((8, 10), (9, 11), (10, 10), (9, 12), (10, 13)),
    "hard": ((10, 12), (11, 13), (12, 12), (12, 13), (11, 12)),
}

_MONO = ((0, 0),)
_DOMINO = ((0, 0), (0, 1))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_L3 = ((0, 0), (1, 0), (1, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic structural profile for audit replay."""
    del seed
    _band(difficulty)
    return "canonical" if int(sample_index) % 2 == 0 else "witness"


def _case_index(sample_index: int) -> int:
    return (int(sample_index) // 2) % len(_CANONICAL_CASES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")
    profile = overrides.get("lesson_profile")
    if profile is not None:
        if type(profile) is not str:
            raise ValueError(
                f"lesson_profile must be a string, not {type(profile).__name__}"
            )
        if profile not in _PROFILE_NAMES:
            raise ValueError(
                f"lesson_profile={profile!r} not in {_PROFILE_NAMES!r}"
            )


def _draw_scheduled_int(ctx, overrides, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_BOUNDS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, (scheduled,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _d4_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    points = tuple(cells)
    variants = set()
    for reflected in (False, True):
        for turns in range(4):
            out = []
            for r, c in points:
                x, y = r, -c if reflected else c
                for _ in range(turns):
                    x, y = y, -x
                out.append((x, y))
            variants.add(_normalize(out))
    return tuple(sorted(variants))


_DOMINO_VARIANTS = _d4_variants(_DOMINO)
_TRIOMINO_VARIANTS = tuple(sorted(set(_d4_variants(_LINE3)) | set(_d4_variants(_L3))))


def _shape_for_size(ctx, size: int, label: str) -> tuple[tuple[int, int], ...]:
    if size == 1:
        return _MONO
    if size == 2:
        return ctx.draw_rng(label).choice(_DOMINO_VARIANTS)
    if size == 3:
        return ctx.draw_rng(label).choice(_TRIOMINO_VARIANTS)
    raise ValueError(f"unsupported component size: {size}")


def _shape_dims(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _halo(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for r, c in cells
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _place_sparse_components(
    ctx,
    h: int,
    w: int,
    components: Sequence[tuple[int, tuple[tuple[int, int], ...]]],
) -> list[list[int]]:
    """Place complete components with a one-cell external halo by backtracking."""
    ordered = sorted(
        enumerate(components),
        key=lambda item: (-len(item[1][1]), item[0]),
    )
    options = []
    for original_index, (color, shape) in ordered:
        sh, sw = _shape_dims(shape)
        candidates = [
            tuple((r0 + r, c0 + c) for r, c in shape)
            for r0 in range(h - sh + 1)
            for c0 in range(w - sw + 1)
        ]
        ctx.draw_rng(f"component_position_{original_index}").shuffle(candidates)
        options.append((original_index, color, candidates))

    def search(index: int, forbidden: set[tuple[int, int]], chosen: dict[int, tuple[int, tuple[tuple[int, int], ...]]]):
        if index == len(options):
            return chosen
        original_index, color, candidates = options[index]
        for cells in candidates:
            if any(cell in forbidden for cell in cells):
                continue
            result = search(
                index + 1,
                forbidden | _halo(cells, h, w),
                {**chosen, original_index: (color, cells)},
            )
            if result is not None:
                return result
        return None

    placed = search(0, set(), {})
    if placed is None:
        raise RuntimeError(
            f"cannot place {len(components)} sparse components in {h}x{w}"
        )
    grid = full_grid(h, w, 0)
    for index in range(len(components)):
        color, cells = placed[index]
        for r, c in cells:
            grid[r][c] = color
    return grid


def _canonical_grid(ctx, h: int, w: int, case: int) -> list[list[int]]:
    sizes = _CANONICAL_CASES[case][2]
    colors = ctx.draw_distinct_colors("canonical_palette", n=len(sizes), exclude=(0,))
    # Vary which colour receives which size without changing the linked multiset.
    assignment = list(zip(colors, sizes))
    ctx.draw_rng("canonical_component_order").shuffle(assignment)
    components = [
        (color, _shape_for_size(ctx, size, f"canonical_shape_{index}"))
        for index, (color, size) in enumerate(assignment)
    ]
    return _place_sparse_components(ctx, h, w, components)


def _transform_point(r: int, c: int, h: int, w: int, transform: str) -> tuple[int, int]:
    if "v" in transform:
        r = h - 1 - r
    if "h" in transform:
        c = w - 1 - c
    return r, c


def _witness_grid(ctx, h: int, w: int) -> list[list[int]]:
    """Build one grid that refutes every declared shortcut simultaneously."""
    a, b, c, d, e = ctx.draw_distinct_colors("witness_palette", n=5, exclude=(0,))
    transform = ctx.draw_choice("witness_transform", ("none", "h", "v", "hv"))

    # A: horizontal blob plus remote singleton of the same colour.  The remote
    # singleton defeats global-frequency filtering while the blob survives.
    colored_cells = [
        (1, 1, a),
        (1, 2, a),
        (h - 2, w - 2, a),
        # B: a same-colour diagonal pair.  Both cells are cardinally isolated.
        (1, w - 3, b),
        (2, w - 2, b),
        # C/D: cardinal contact of different colours.  Same-colour adjacency is
        # still absent, so both are erased by the authority.
        (h - 2, 1, c),
        (h - 2, 2, d),
        # E: vertical blob, jointly refuting horizontal-only/vertical-only rules.
        (h // 2 - 1, w // 2, e),
        (h // 2, w // 2, e),
    ]
    grid = full_grid(h, w, 0)
    for r, col, color in colored_cells:
        rr, cc = _transform_point(r, col, h, w, transform)
        if grid[rr][cc] != 0:
            raise RuntimeError("witness template collision")
        grid[rr][cc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    scheduled_profile = schedule_profile(seed, sample_index, difficulty=band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("lesson_profile") is not None:
        profile = ctx.draw_choice("lesson_profile", _PROFILE_NAMES)
    else:
        profile = ctx.draw_choice("lesson_profile", (scheduled_profile,))

    case = _case_index(sample_index)
    if profile == "canonical":
        scheduled_h, scheduled_w, _ = _CANONICAL_CASES[case]
    else:
        scheduled_h, scheduled_w = _WITNESS_DIMS[band][case]
    h = _draw_scheduled_int(ctx, overrides, "grid_h", scheduled_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", scheduled_w)

    grid = (
        _canonical_grid(ctx, h, w, case)
        if profile == "canonical"
        else _witness_grid(ctx, h, w)
    )
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed an invalid {profile} grid: {errors}")
    if classify_profile(grid) != profile:
        raise RuntimeError("constructed profile is not observable from returned pixels")
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must contain at least one column"]
    width = len(grid[0])
    for index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return [f"row {index} is not rectangular width {width}"]
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["grid values must be integer ARC colours 0..9"]
    return []


def _neighbors(
    point: tuple[int, int],
    h: int,
    w: int,
    deltas: Iterable[tuple[int, int]] = _CARDINALS,
) -> list[tuple[int, int]]:
    r, c = point
    return [
        (r + dr, c + dc)
        for dr, dc in deltas
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]


def _same_color_components(grid) -> list[tuple[int, frozenset[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells = {start}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for neighbor in _neighbors(point, h, w):
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        components.append((color, frozenset(cells)))
    return components


def _analysis(grid) -> dict[str, Any]:
    components = _same_color_components(grid)
    cell_size = {
        point: len(cells)
        for _, cells in components
        for point in cells
    }
    by_color: dict[int, list[frozenset[tuple[int, int]]]] = defaultdict(list)
    for color, cells in components:
        by_color[color].append(cells)
    singletons = [(color, next(iter(cells))) for color, cells in components if len(cells) == 1]
    blobs = [(color, cells) for color, cells in components if len(cells) >= 2]
    h, w = len(grid), len(grid[0])

    local_frequency_witness = any(
        any(len(cells) == 1 for cells in groups)
        and any(len(cells) >= 2 for cells in groups)
        for groups in by_color.values()
    )
    diagonal_pair = any(
        color_a == color_b
        and abs(point_a[0] - point_b[0]) == 1
        and abs(point_a[1] - point_b[1]) == 1
        for index, (color_a, point_a) in enumerate(singletons)
        for color_b, point_b in singletons[index + 1 :]
    )
    different_color_touch = False
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or cell_size[(r, c)] != 1:
                continue
            for nr, nc in _neighbors((r, c), h, w, ((1, 0), (0, 1))):
                if (
                    grid[nr][nc] != 0
                    and grid[nr][nc] != grid[r][c]
                    and cell_size[(nr, nc)] == 1
                ):
                    different_color_touch = True

    horizontal_blob = any(
        (r, c + 1) in cells
        for _, cells in blobs
        for r, c in cells
    )
    vertical_blob = any(
        (r + 1, c) in cells
        for _, cells in blobs
        for r, c in cells
    )
    return {
        "components": components,
        "by_color": by_color,
        "singletons": singletons,
        "blobs": blobs,
        "local_frequency_witness": local_frequency_witness,
        "diagonal_pair": diagonal_pair,
        "different_color_touch": different_color_touch,
        "horizontal_blob": horizontal_blob,
        "vertical_blob": vertical_blob,
    }


def _profile_from_analysis(info: dict[str, Any]) -> str | None:
    components = info["components"]
    singletons = info["singletons"]
    blobs = info["blobs"]
    witness = (
        len(components) == 7
        and len(singletons) == 5
        and sorted(len(cells) for _, cells in blobs) == [2, 2]
        and len(info["by_color"]) == 5
        and info["local_frequency_witness"]
        and info["diagonal_pair"]
        and info["different_color_touch"]
        and info["horizontal_blob"]
        and info["vertical_blob"]
    )
    if witness:
        return "witness"

    canonical = (
        1 <= len(blobs) <= 3
        and 1 <= len(singletons) <= 2
        and all(1 <= len(cells) <= 3 for _, cells in components)
        and len(components) == len(info["by_color"])
        and not info["different_color_touch"]
    )
    if canonical:
        return "canonical"
    return None


def classify_profile(grid) -> str:
    """Recover the exact lesson profile from returned pixels."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    profile = _profile_from_analysis(_analysis(grid))
    if profile is None:
        raise ValueError("grid does not match canonical or witness grammar")
    return profile


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrow two-profile teaching grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 12 and 8 <= w <= 13):
        errors.append(f"grid shape {h}x{w} outside accepted 7..12 by 8..13 range")
        return errors

    info = _analysis(grid)
    if not info["components"]:
        errors.append("grid must contain nonzero components")
    if any(len(cells) > 3 for _, cells in info["components"]):
        errors.append("same-colour components may contain at most three cells")
    if sum(value != 0 for row in grid for value in row) >= h * w / 2:
        errors.append("background 0 must be the strict majority")
    if _profile_from_analysis(info) is None:
        errors.append("grid does not match canonical or witness teaching grammar")
    return list(dict.fromkeys(errors))


def observe_overrides(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors[0]}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "lesson_profile": classify_profile(grid),
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked public dimension/component-size profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    if classify_profile(grid) != "canonical":
        errors.append("strict public profile is canonical, not witness")
        return errors
    h, w = len(grid), len(grid[0])
    expected = _CANONICAL_SIGNATURES.get((h, w))
    if expected is None:
        errors.append(f"shape {(h, w)} is outside the five linked public profiles")
        return errors
    actual = tuple(sorted(len(cells) for _, cells in _same_color_components(grid)))
    if actual != expected:
        errors.append(f"component-size signature {actual} != linked public {expected}")
    return errors


def _keep_by(grid, predicate: Callable[[int, int, int], bool]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0 and predicate(r, c, color):
                out[r][c] = color
    return out


def rule_mirror(grid):
    """Independent Python mirror of the unchanged selected Racket authority."""
    if _grid_errors(grid):
        raise ValueError("rule_mirror requires a rectangular ARC-colour grid")
    h, w = len(grid), len(grid[0])
    return _keep_by(
        grid,
        lambda r, c, color: any(
            grid[nr][nc] == color for nr, nc in _neighbors((r, c), h, w)
        ),
    )


def _rival_identity(grid):
    return deepcopy(grid)


def _rival_global_color_frequency(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    return _keep_by(grid, lambda r, c, color: counts[color] >= 2)


def _rival_same_color_eight_neighbor(grid):
    h, w = len(grid), len(grid[0])
    return _keep_by(
        grid,
        lambda r, c, color: any(
            grid[nr][nc] == color
            for nr, nc in _neighbors((r, c), h, w, _EIGHT)
        ),
    )


def _rival_any_nonzero_cardinal_neighbor(grid):
    h, w = len(grid), len(grid[0])
    return _keep_by(
        grid,
        lambda r, c, color: any(
            grid[nr][nc] != 0 for nr, nc in _neighbors((r, c), h, w)
        ),
    )


def _rival_horizontal_only(grid):
    h, w = len(grid), len(grid[0])
    return _keep_by(
        grid,
        lambda r, c, color: any(
            grid[nr][nc] == color
            for nr, nc in _neighbors((r, c), h, w, ((0, -1), (0, 1)))
        ),
    )


def _rival_vertical_only(grid):
    h, w = len(grid), len(grid[0])
    return _keep_by(
        grid,
        lambda r, c, color: any(
            grid[nr][nc] == color
            for nr, nc in _neighbors((r, c), h, w, ((-1, 0), (1, 0)))
        ),
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _rival_identity,
    "global_color_frequency": _rival_global_color_frequency,
    "same_color_eight_neighbor": _rival_same_color_eight_neighbor,
    "any_nonzero_cardinal_neighbor": _rival_any_nonzero_cardinal_neighbor,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "global_color_frequency",
        "same_color_eight_neighbor",
        "any_nonzero_cardinal_neighbor",
    )
}


def _valid_rival_difference(grid, rival_name: str) -> bool:
    return not self_check(grid) and rule_mirror(grid) != SEMANTIC_RIVALS[rival_name](grid)


def _witness_identity(grid) -> bool:
    return _valid_rival_difference(grid, "identity")


def _witness_global_frequency(grid) -> bool:
    return _analysis(grid)["local_frequency_witness"] and _valid_rival_difference(
        grid, "global_color_frequency"
    )


def _witness_eight_neighbor(grid) -> bool:
    return _analysis(grid)["diagonal_pair"] and _valid_rival_difference(
        grid, "same_color_eight_neighbor"
    )


def _witness_any_contact(grid) -> bool:
    return _analysis(grid)["different_color_touch"] and _valid_rival_difference(
        grid, "any_nonzero_cardinal_neighbor"
    )


def _witness_horizontal_only(grid) -> bool:
    return _analysis(grid)["vertical_blob"] and _valid_rival_difference(
        grid, "horizontal_only"
    )


def _witness_vertical_only(grid) -> bool:
    return _analysis(grid)["horizontal_blob"] and _valid_rival_difference(
        grid, "vertical_only"
    )


SEMANTIC_WITNESSES = {
    "isolated_cells_are_erased": _witness_identity,
    "adjacency_is_local_not_global_frequency": _witness_global_frequency,
    "connectivity_is_cardinal_not_eight_neighbor": _witness_eight_neighbor,
    "neighbor_must_have_the_same_colour": _witness_any_contact,
    "vertical_adjacency_also_survives": _witness_horizontal_only,
    "horizontal_adjacency_also_survives": _witness_vertical_only,
}
WITNESS_RIVALS = {
    "isolated_cells_are_erased": ["identity"],
    "adjacency_is_local_not_global_frequency": ["global_color_frequency"],
    "connectivity_is_cardinal_not_eight_neighbor": ["same_color_eight_neighbor"],
    "neighbor_must_have_the_same_colour": ["any_nonzero_cardinal_neighbor"],
    "vertical_adjacency_also_survives": ["horizontal_only"],
    "horizontal_adjacency_also_survives": ["vertical_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstration pairs"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        grammar_errors = self_check(pair["input"])
        if grammar_errors:
            reasons.append(f"{role} input is outside teaching grammar: {grammar_errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with selected rule")

    valid_demos = [
        pair
        for pair in demos
        if isinstance(pair, dict) and "input" in pair and "output" in pair
    ]
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            if valid_demos and all(
                competitor(pair["input"]) == pair["output"]
                for pair in valid_demos
            ):
                reasons.append(f"competitor {name!r} survives every demonstration")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons


def mutation_fixtures():
    """Minimal impostors that the structural validator must reject."""
    blank = full_grid(7, 8, 0)

    solid = full_grid(7, 8, 1)

    short_line = full_grid(7, 8, 0)
    short_line[3][2:5] = [2, 2, 2]

    square = full_grid(7, 8, 0)
    for r in (2, 3):
        for c in (2, 3):
            square[r][c] = 3

    repeated_remote = full_grid(7, 8, 0)
    repeated_remote[1][1] = 4
    repeated_remote[5][6] = 4

    different_touch_only = full_grid(7, 8, 0)
    different_touch_only[3][3] = 5
    different_touch_only[3][4] = 6

    return [
        ("blank", blank),
        ("solid_component", solid),
        ("short_line_only", short_line),
        ("solid_two_by_two", square),
        ("two_remote_same_colour_singletons", repeated_remote),
        ("different_colour_touch_only", different_touch_only),
    ]
