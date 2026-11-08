"""Semantic curriculum generator for ARC task cae2f5a8b903.

Each nonzero color owns one small 8-connected motif and appears as several
spatially separated copies of that motif.  Object counts are distinct.  The
answer is the 3x3 motif of the color with the greatest number of 8-connected
components, recolored with that winning color.

The four-slot schedule is deliberate rather than decorative: every four
consecutive examples include (1) a case where cell mass and object count pick
different colors, (2) the canonical two-versus-one boundary, (3) two losing
colors that share a motif and together outnumber the winning motif, and (4) a
difficulty-scaled generalization.  Thus a normal lesson cannot be solved by
counting cells, taking the first object, using 4-connectivity, memorizing a
color rank, or counting shape repetitions while ignoring color.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "cae2f5a8b903"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0eadf5b9f415"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "Count 8-connected monochrome components separately for each nonzero color. "
    "Choose the unique color with the most components, take its first object in "
    "reading order, and copy that color's cells from the object's top-left "
    "3x3 window into a 3x3 output; every other output cell is zero."
)

INVARIANTS = [
    "background is color 0",
    "two or three nonzero colors occur",
    "each color repeats one exact 3x3-bounding 8-connected motif",
    "object counts are positive, distinct, and have a unique maximum",
    "every motif has four through six cells and every object is spatially separate",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_GRID_SIZES = (12, 14, 16)
_WINNER_RANKS = ("lowest", "highest")
_AREA_RELATIONS = ("winner_most_cells", "loser_more_cells")
_WINNER_POSITIONS = ("first", "later")
_LOSER_MOTIF_RELATIONS = ("distinct", "shared")
_WINNER_LINKAGES = ("orthogonal", "diagonal")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot schedule; 12/14/16",
        "valid": "12|14|16",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot schedule; 12/14/16",
        "valid": "12|14|16",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical schedule uses 2 or 3",
        "valid": "2..3",
    },
    "winner_count": {
        "type": "int",
        "default": "canonical schedule uses 2, 3, or 4",
        "valid": "2..4",
    },
    "winner_color_rank": {
        "type": "str",
        "default": "schedule alternates lowest and highest",
        "valid": "lowest|highest",
    },
    "area_relation": {
        "type": "str",
        "default": "schedule includes both object-count/cell-count agreement and conflict",
        "valid": "winner_most_cells|loser_more_cells",
    },
    "winner_position": {
        "type": "str",
        "default": "schedule includes winner-first and winner-later scenes",
        "valid": "first|later",
    },
    "loser_motif_relation": {
        "type": "str",
        "default": "schedule includes distinct motifs and a shared-loser control",
        "valid": "distinct|shared",
    },
    "winner_linkage": {
        "type": "str",
        "default": "schedule includes 4-connected and diagonal-only 8-connected winners",
        "valid": "orthogonal|diagonal",
    },
}

# These are the only finite-domain requests that cannot be represented while
# preserving the task grammar.  Raised exceptions also carry the axes, so the
# override checker can distinguish intentional incompatibility from a bug.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_colors": 3, "winner_count": 2},
    {"n_colors": 2, "loser_motif_relation": "shared"},
    {"winner_count": 2, "loser_motif_relation": "shared"},
    {"winner_count": 2, "area_relation": "loser_more_cells"},
    {"winner_count": 3, "area_relation": "loser_more_cells"},
    {"area_relation": "loser_more_cells", "winner_linkage": "orthogonal"},
]

SCHEDULE_PROFILES = (
    "canonical_count_conflict",
    "two_vs_one_boundary",
    "shared_loser_motif",
    "difficulty_generalization",
)

_PROFILE_DEFAULTS = {
    "canonical_count_conflict": {
        "grid_h": 14,
        "grid_w": 14,
        "n_colors": 3,
        "winner_count": 4,
        "winner_color_rank": "lowest",
        "area_relation": "loser_more_cells",
        "winner_position": "later",
        "loser_motif_relation": "distinct",
        "winner_linkage": "diagonal",
    },
    "two_vs_one_boundary": {
        "grid_h": 14,
        "grid_w": 14,
        "n_colors": 2,
        "winner_count": 2,
        "winner_color_rank": "highest",
        "area_relation": "winner_most_cells",
        "winner_position": "first",
        "loser_motif_relation": "distinct",
        "winner_linkage": "orthogonal",
    },
    "shared_loser_motif": {
        "grid_h": 14,
        "grid_w": 14,
        "n_colors": 3,
        "winner_count": 4,
        "winner_color_rank": "highest",
        "area_relation": "winner_most_cells",
        "winner_position": "later",
        "loser_motif_relation": "shared",
        "winner_linkage": "orthogonal",
    },
    "difficulty_generalization": {
        "grid_h": 14,
        "grid_w": 14,
        "n_colors": 3,
        "winner_count": 3,
        "winner_color_rank": "lowest",
        "area_relation": "winner_most_cells",
        "winner_position": "first",
        "loser_motif_relation": "distinct",
        "winner_linkage": "diagonal",
    },
}

_ADJ4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_ADJ8 = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),               (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def schedule_profile(
    seed: int, sample_index: int, difficulty: str | None = None
) -> str:
    """Expose the deterministic four-example lesson schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _incompatible(message: str, *axes: str) -> None:
    exc = ValueError(message)
    exc.incompatible_axes = tuple(axes)
    raise exc


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(
            f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}"
        )

    for name, allowed in (
        ("grid_h", _GRID_SIZES),
        ("grid_w", _GRID_SIZES),
        ("n_colors", (2, 3)),
        ("winner_count", (2, 3, 4)),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}")

    for name, allowed in (
        ("winner_color_rank", _WINNER_RANKS),
        ("area_relation", _AREA_RELATIONS),
        ("winner_position", _WINNER_POSITIONS),
        ("loser_motif_relation", _LOSER_MOTIF_RELATIONS),
        ("winner_linkage", _WINNER_LINKAGES),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}")
    return band


def _profile_defaults(sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index)
    defaults = dict(_PROFILE_DEFAULTS[profile])
    if profile == "difficulty_generalization":
        size = {"easy": 12, "medium": 14, "hard": 16}[band]
        defaults["grid_h"] = size
        defaults["grid_w"] = size
    return defaults


def _resolve_default_dependencies(
    defaults: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    """Adapt only unspecified axes so every accepted single override is exact."""
    values = dict(defaults)
    values.update({k: v for k, v in overrides.items() if v is not None})

    explicit = {k for k, v in overrides.items() if v is not None}

    # winner_count=2 leaves room for exactly one positive lower count.
    if values["winner_count"] == 2 and values["n_colors"] == 3:
        if {"winner_count", "n_colors"} <= explicit:
            _incompatible(
                "winner_count=2 cannot realize three positive distinct object counts",
                "winner_count", "n_colors",
            )
        if "winner_count" in explicit:
            values["n_colors"] = 2
        else:
            values["winner_count"] = 3

    # A shared relation specifically means the two losing colors share one
    # motif; with only one loser the relation is undefined and thus rejected.
    if values["loser_motif_relation"] == "shared" and values["n_colors"] == 2:
        if {"loser_motif_relation", "n_colors"} <= explicit:
            _incompatible(
                "loser_motif_relation='shared' requires three colors",
                "loser_motif_relation", "n_colors",
            )
        if "loser_motif_relation" in explicit:
            if values["winner_count"] == 2 and "winner_count" in explicit:
                _incompatible(
                    "loser_motif_relation='shared' requires winner_count>=3",
                    "loser_motif_relation", "winner_count",
                )
            values["n_colors"] = 3
            if values["winner_count"] == 2:
                values["winner_count"] = 3
        else:
            values["loser_motif_relation"] = "distinct"

    # With 4..6 cells per motif, only counts 4 versus 3 can make a losing
    # color have more cells while the winner still has more components.
    if (
        values["area_relation"] == "loser_more_cells"
        and values["winner_count"] < 4
    ):
        if {"area_relation", "winner_count"} <= explicit:
            _incompatible(
                "loser_more_cells requires winner_count=4 under the 4..6-cell motif grammar",
                "area_relation", "winner_count",
            )
        if "area_relation" in explicit:
            values["winner_count"] = 4
        else:
            values["area_relation"] = "winner_most_cells"

    # A 3x3-bounding 4-connected motif needs at least five cells.  The
    # cell-mass conflict needs a four-cell winner, so that profile necessarily
    # uses diagonal-only 8-connectivity.
    if (
        values["area_relation"] == "loser_more_cells"
        and values["winner_linkage"] == "orthogonal"
    ):
        if {"area_relation", "winner_linkage"} <= explicit:
            _incompatible(
                "loser_more_cells requires the four-cell diagonal winner motif",
                "area_relation", "winner_linkage",
            )
        if "area_relation" in explicit:
            values["winner_linkage"] = "diagonal"
        else:
            values["area_relation"] = "winner_most_cells"

    # Re-check the dependency that may have changed after the adaptations.
    if values["n_colors"] == 3 and values["winner_count"] == 2:
        _incompatible(
            "three colors require winner_count at least 3",
            "n_colors", "winner_count",
        )
    if values["n_colors"] == 2 and values["loser_motif_relation"] == "shared":
        _incompatible(
            "shared losing motifs require two losing colors",
            "n_colors", "loser_motif_relation",
        )
    return values


def _record_axis(ctx, name: str, value: Any, overrides: dict[str, Any]) -> Any:
    """Record every realized axis through GenCtx, including scheduled defaults."""
    if name in ("grid_h", "grid_w"):
        domain: Iterable[Any] = _GRID_SIZES
    elif name == "n_colors":
        domain = (2, 3)
    elif name == "winner_count":
        domain = (2, 3, 4)
    elif name == "winner_color_rank":
        domain = _WINNER_RANKS
    elif name == "area_relation":
        domain = _AREA_RELATIONS
    elif name == "winner_position":
        domain = _WINNER_POSITIONS
    elif name == "loser_motif_relation":
        domain = _LOSER_MOTIF_RELATIONS
    elif name == "winner_linkage":
        domain = _WINNER_LINKAGES
    else:  # pragma: no cover - internal programming error
        raise KeyError(name)

    if name in overrides and overrides[name] is not None:
        return ctx.draw_choice(name, tuple(domain))
    # A singleton keyed draw records the schedule/adaptation without allowing a
    # second random decision to drift away from the declared profile.
    return ctx.draw_choice(name, (value,))


def _connected(cells: Iterable[tuple[int, int]], adjacency) -> bool:
    cells = tuple(cells)
    if not cells:
        return False
    remaining = set(cells)
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        row, col = stack.pop()
        for dr, dc in adjacency:
            nxt = (row + dr, col + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return len(seen) == len(remaining)


def _shape_bank() -> tuple[dict[int, tuple[tuple[tuple[int, int], ...], ...]], dict[int, tuple[tuple[tuple[int, int], ...], ...]]]:
    all_cells = tuple((r, c) for r in range(3) for c in range(3))
    orthogonal: dict[int, list[tuple[tuple[int, int], ...]]] = defaultdict(list)
    diagonal: dict[int, list[tuple[tuple[int, int], ...]]] = defaultdict(list)
    for size in range(4, 7):
        for shape in combinations(all_cells, size):
            rows = {r for r, _ in shape}
            cols = {c for _, c in shape}
            if rows != {0, 1, 2} or cols != {0, 1, 2}:
                continue
            if not _connected(shape, _ADJ8):
                continue
            target = orthogonal if _connected(shape, _ADJ4) else diagonal
            target[size].append(tuple(shape))
    return (
        {size: tuple(shapes) for size, shapes in orthogonal.items()},
        {size: tuple(shapes) for size, shapes in diagonal.items()},
    )


_ORTHOGONAL_SHAPES, _DIAGONAL_SHAPES = _shape_bank()


def _pick_shape(pool, rng, *, exclude=()):
    excluded = set(exclude)
    choices = [shape for shape in pool if shape not in excluded]
    if not choices:  # pragma: no cover - banks are exhaustively built above
        raise RuntimeError("shape bank exhausted")
    return rng.choice(choices)


def _choose_motifs(
    n_colors: int,
    area_relation: str,
    loser_motif_relation: str,
    winner_linkage: str,
    rng,
) -> tuple[tuple[tuple[int, int], ...], list[tuple[tuple[int, int], ...]]]:
    linkage_bank = (
        _ORTHOGONAL_SHAPES if winner_linkage == "orthogonal" else _DIAGONAL_SHAPES
    )
    winner_size = 4 if area_relation == "loser_more_cells" else 6
    winner = _pick_shape(linkage_bank[winner_size], rng)

    if area_relation == "loser_more_cells":
        loser_sizes = [6, 5]
    else:
        loser_sizes = [5, 5]

    first_loser = _pick_shape(
        _ORTHOGONAL_SHAPES[loser_sizes[0]] + _DIAGONAL_SHAPES[loser_sizes[0]],
        rng,
        exclude=(winner,),
    )
    losers = [first_loser]
    if n_colors == 3:
        if loser_motif_relation == "shared":
            losers.append(first_loser)
        else:
            second_loser = _pick_shape(
                _ORTHOGONAL_SHAPES[loser_sizes[1]] + _DIAGONAL_SHAPES[loser_sizes[1]],
                rng,
                exclude=(winner, first_loser),
            )
            losers.append(second_loser)
    return winner, losers


def _object_counts(
    profile: str, n_colors: int, winner_count: int
) -> list[int]:
    if n_colors == 2:
        return [winner_count, winner_count - 1]
    if profile == "canonical_count_conflict" and winner_count == 4:
        return [4, 3, 1]
    return [winner_count, winner_count - 1, winner_count - 2]


def _lattice_slots(height: int, width: int, rng) -> list[tuple[int, int]]:
    row_bases = list(range(0, height - 2, 4))
    col_bases = list(range(0, width - 2, 4))
    row_margin = height - (row_bases[-1] + 3)
    col_margin = width - (col_bases[-1] + 3)
    row_offset = rng.randint(0, row_margin)
    col_offset = rng.randint(0, col_margin)
    return [
        (row + row_offset, col + col_offset)
        for row in row_bases
        for col in col_bases
    ]


def _render(
    height: int,
    width: int,
    colors: list[int],
    counts: list[int],
    motifs: list[tuple[tuple[int, int], ...]],
    winner_position: str,
    rng,
) -> list[list[int]]:
    total = sum(counts)
    slots = _lattice_slots(height, width, rng)
    if total > len(slots):  # defensive; all declared combinations fit 12x12
        _incompatible(
            "requested object counts do not fit the selected grid",
            "grid_h", "grid_w", "n_colors", "winner_count",
        )

    # The earliest occupied lattice slot is always included, making the
    # winner_position axis exactly recoverable from the grid.
    selected = [slots[0]]
    selected.extend(rng.sample(slots[1:], total - 1))
    selected.sort()

    roles: list[int] = []
    for role, count in enumerate(counts):
        roles.extend([role] * count)
    first_role = 0 if winner_position == "first" else 1
    roles.remove(first_role)
    rng.shuffle(roles)
    roles.insert(0, first_role)

    grid = full_grid(height, width, 0)
    for (row0, col0), role in zip(selected, roles):
        color = colors[role]
        for dr, dc in motifs[role]:
            grid[row0 + dr][col0 + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, band)
    defaults = _profile_defaults(sample_index, band)
    resolved = _resolve_default_dependencies(defaults, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    values = {
        name: _record_axis(ctx, name, resolved[name], overrides)
        for name in AXES
    }

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(tuple(range(1, 10)), values["n_colors"])
    palette.sort()
    winner = palette[0] if values["winner_color_rank"] == "lowest" else palette[-1]
    losers = [color for color in palette if color != winner]
    palette_rng.shuffle(losers)
    colors = [winner, *losers]

    motifs_rng = ctx.draw_rng("motifs")
    winner_motif, losing_motifs = _choose_motifs(
        values["n_colors"],
        values["area_relation"],
        values["loser_motif_relation"],
        values["winner_linkage"],
        motifs_rng,
    )
    motifs = [winner_motif, *losing_motifs]
    counts = _object_counts(profile, values["n_colors"], values["winner_count"])
    return _render(
        values["grid_h"], values["grid_w"], colors, counts, motifs,
        values["winner_position"], ctx.draw_rng("layout"),
    )


def _grid_shape_and_values(grid: Any) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty sequences"]
    height = len(grid)
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return height, width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append(f"cell ({r},{c}) must be an ARC integer 0..9")
                return height, width, errors
    return height, width, errors


def _components(grid: Any, adjacency=_ADJ8) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for dr, dc in adjacency:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            r1 = min(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            r2 = max(r for r, _ in cells)
            c2 = max(c for _, c in cells)
            motif = tuple(sorted((r - r1, c - c1) for r, c in cells))
            components.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (r1, c1, r2, c2),
                    "motif": motif,
                    "size": len(cells),
                }
            )
    return components


def _analysis(grid: Any) -> tuple[dict[str, Any], list[str]]:
    height, width, errors = _grid_shape_and_values(grid)
    if errors:
        return {}, errors
    if not 10 <= height <= 20:
        errors.append(f"height must be in 10..20, found {height}")
    if not 10 <= width <= 20:
        errors.append(f"width must be in 10..20, found {width}")

    colors = sorted({value for row in grid for value in row if value != 0})
    if not 2 <= len(colors) <= 3:
        errors.append(f"input must contain two or three nonzero colors, found {len(colors)}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("input must retain background color 0")

    components = _components(grid)
    by_color: dict[int, list[dict[str, Any]]] = {
        color: [obj for obj in components if obj["color"] == color]
        for color in colors
    }
    for color, color_objects in by_color.items():
        if not color_objects:
            errors.append(f"color {color} has no 8-connected object")
            continue
        motifs = {obj["motif"] for obj in color_objects}
        if len(motifs) != 1:
            errors.append(f"color {color} must repeat one exact motif, found {len(motifs)}")
        for obj in color_objects:
            r1, c1, r2, c2 = obj["bbox"]
            if (r2 - r1 + 1, c2 - c1 + 1) != (3, 3):
                errors.append(
                    f"color {color} object at {(r1, c1)} must have an exact 3x3 bbox"
                )
                break
            if not 4 <= obj["size"] <= 6:
                errors.append(
                    f"color {color} object at {(r1, c1)} must have 4..6 cells"
                )
                break

    counts = {color: len(by_color.get(color, ())) for color in colors}
    if counts and (0 in counts.values() or len(set(counts.values())) != len(counts)):
        errors.append(f"object counts must be positive and distinct, found {counts}")

    winner = None
    if counts:
        maximum = max(counts.values())
        winners = [color for color, count in counts.items() if count == maximum]
        if len(winners) != 1:
            errors.append(f"object-count winner must be unique, found {winners}")
        else:
            winner = winners[0]

    info = {
        "grid_h": height,
        "grid_w": width,
        "colors": colors,
        "components": components,
        "by_color": by_color,
        "counts": counts,
        "winner": winner,
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete repeated-motif/object-count input grammar."""
    del difficulty, meta
    return _analysis(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    """Recognize the public 14x14 morphology and its four count profiles."""
    info, errors = _analysis(grid)
    if errors:
        return errors
    if (info["grid_h"], info["grid_w"]) != (14, 14):
        return ["strict canonical profile requires a 14x14 input"]
    profile = tuple(sorted(info["counts"].values(), reverse=True))
    if profile not in {(4, 3, 1), (4, 3, 2), (3, 2, 1), (3, 2), (2, 1)}:
        return [f"strict canonical object-count profile not recognized: {profile}"]
    return []


def _winner_object(info: dict[str, Any]) -> dict[str, Any]:
    winner = info["winner"]
    return next(obj for obj in info["components"] if obj["color"] == winner)


def _window_for_color(
    grid: list[list[int]], color: int, obj: dict[str, Any], *, component_only=False
) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    r1, c1, _r2, _c2 = obj["bbox"]
    component_cells = set(obj["cells"])
    output = [[0] * 3 for _ in range(3)]
    for dr in range(3):
        for dc in range(3):
            row, col = r1 + dr, c1 + dc
            if not (0 <= row < height and 0 <= col < width):
                continue
            if component_only:
                if (row, col) in component_cells:
                    output[dr][dc] = color
            elif grid[row][col] == color:
                output[dr][dc] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected Racket rule, including its 3x3 window."""
    height, width, errors = _grid_shape_and_values(grid)
    if errors or height == 0 or width == 0:
        return []
    components = _components(grid)
    if not components:
        return [[0] * 3 for _ in range(3)]
    counts = Counter(obj["color"] for obj in components)
    # Canonical inputs have a unique maximum.  Stable first-seen tie handling
    # mirrors the selected rule's source-order color list for malformed probes.
    order = []
    for row in grid:
        for value in row:
            if value and value not in order:
                order.append(value)
    winner = max(order, key=lambda color: counts[color])
    obj = next(item for item in components if item["color"] == winner)
    return _window_for_color(grid, winner, obj)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from a returned lawful grid."""
    info, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + errors[0])
    winner = info["winner"]
    losers = [color for color in info["colors"] if color != winner]
    totals = {
        color: sum(obj["size"] for obj in info["by_color"][color])
        for color in info["colors"]
    }
    first_color = info["components"][0]["color"]
    winner_motif = info["by_color"][winner][0]["motif"]
    loser_motifs = [info["by_color"][color][0]["motif"] for color in losers]
    loser_relation = (
        "shared"
        if len(loser_motifs) == 2 and loser_motifs[0] == loser_motifs[1]
        else "distinct"
    )
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "n_colors": len(info["colors"]),
        "winner_count": info["counts"][winner],
        "winner_color_rank": "lowest" if winner == min(info["colors"]) else "highest",
        "area_relation": (
            "winner_most_cells"
            if totals[winner] > max(totals[color] for color in losers)
            else "loser_more_cells"
        ),
        "winner_position": "first" if first_color == winner else "later",
        "loser_motif_relation": loser_relation,
        "winner_linkage": (
            "orthogonal" if _connected(winner_motif, _ADJ4) else "diagonal"
        ),
    }


def semantic_observables(grid) -> dict[str, Any]:
    info, errors = _analysis(grid)
    if errors:
        return {"valid": False, "errors": errors}
    observed = observe_overrides(grid)
    winner = info["winner"]
    return {
        "valid": True,
        **observed,
        "count_profile": tuple(sorted(info["counts"].values(), reverse=True)),
        "winner_color": winner,
        "winner_motif": info["by_color"][winner][0]["motif"],
    }


def _output_from_color_choice(grid, color: int) -> list[list[int]]:
    components = _components(grid)
    obj = next(item for item in components if item["color"] == color)
    return _window_for_color(grid, color, obj)


def _rival_most_cells_color(grid):
    components = _components(grid)
    colors = []
    for row in grid:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    totals = Counter(value for row in grid for value in row if value)
    return _output_from_color_choice(grid, max(colors, key=lambda color: totals[color]))


def _rival_largest_single_object(grid):
    components = _components(grid)
    obj = max(components, key=lambda item: item["size"])
    return _window_for_color(grid, obj["color"], obj)


def _rival_first_object(grid):
    obj = _components(grid)[0]
    return _window_for_color(grid, obj["color"], obj)


def _rival_lowest_color(grid):
    colors = sorted({value for row in grid for value in row if value})
    return _output_from_color_choice(grid, colors[0])


def _rival_highest_color(grid):
    colors = sorted({value for row in grid for value in row if value})
    return _output_from_color_choice(grid, colors[-1])


def _rival_four_connected_components(grid):
    components = _components(grid, _ADJ4)
    order = []
    for row in grid:
        for value in row:
            if value and value not in order:
                order.append(value)
    counts = Counter(obj["color"] for obj in components)
    winner = max(order, key=lambda color: counts[color])
    obj = next(item for item in components if item["color"] == winner)
    return _window_for_color(grid, winner, obj, component_only=True)


def _rival_most_repeated_motif_ignoring_color(grid):
    components = _components(grid)
    counts = Counter(obj["motif"] for obj in components)
    motif = max((obj["motif"] for obj in components), key=lambda shape: counts[shape])
    obj = next(item for item in components if item["motif"] == motif)
    return _window_for_color(grid, obj["color"], obj)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "most_cells_color": _rival_most_cells_color,
    "largest_single_object": _rival_largest_single_object,
    "first_object": _rival_first_object,
    "lowest_color": _rival_lowest_color,
    "highest_color": _rival_highest_color,
    "four_connected_components": _rival_four_connected_components,
    "most_repeated_motif_ignoring_color": _rival_most_repeated_motif_ignoring_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# This wrong rule fits all four public pairs because every public color owns a
# unique motif.  The shared-loser schedule profile supplies the missing
# generated counterexample.
CANONICAL_SHORTCUTS = {
    "most_repeated_motif_ignoring_color": _rival_most_repeated_motif_ignoring_color,
}


def _witness_relation(grid, axis: str, value: Any, rivals: Iterable[str]) -> bool:
    try:
        observed = observe_overrides(grid)
        canonical = rule_mirror(grid)
        return observed[axis] == value and all(
            SEMANTIC_RIVALS[name](grid) != canonical for name in rivals
        )
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "object_count_beats_cell_mass": lambda grid: _witness_relation(
        grid, "area_relation", "loser_more_cells",
        ("most_cells_color", "largest_single_object"),
    ),
    "winner_occurs_after_a_loser": lambda grid: _witness_relation(
        grid, "winner_position", "later", ("first_object",),
    ),
    "lowest_rank_wins": lambda grid: _witness_relation(
        grid, "winner_color_rank", "lowest", ("highest_color",),
    ),
    "highest_rank_wins": lambda grid: _witness_relation(
        grid, "winner_color_rank", "highest", ("lowest_color",),
    ),
    "diagonal_eight_connectivity_matters": lambda grid: _witness_relation(
        grid, "winner_linkage", "diagonal", ("four_connected_components",),
    ),
    "losing_colors_share_the_modal_motif": lambda grid: _witness_relation(
        grid, "loser_motif_relation", "shared",
        ("most_repeated_motif_ignoring_color",),
    ),
}

WITNESS_RIVALS = {
    "object_count_beats_cell_mass": ["most_cells_color", "largest_single_object"],
    "winner_occurs_after_a_loser": ["first_object"],
    "lowest_rank_wins": ["highest_color"],
    "highest_rank_wins": ["lowest_color"],
    "diagonal_eight_connectivity_matters": ["four_connected_components"],
    "losing_colors_share_the_modal_motif": ["most_repeated_motif_ignoring_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson in which a named plausible shortcut survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    ranks: set[str] = set()
    positions: set[str] = set()
    count_profiles: set[tuple[int, ...]] = set()
    saw_cell_conflict = False
    saw_shared_losers = False
    saw_diagonal = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the object-count rule")
        observed = observe_overrides(pair["input"])
        info, _ = _analysis(pair["input"])
        ranks.add(observed["winner_color_rank"])
        positions.add(observed["winner_position"])
        count_profiles.add(tuple(sorted(info["counts"].values(), reverse=True)))
        saw_cell_conflict |= observed["area_relation"] == "loser_more_cells"
        saw_shared_losers |= observed["loser_motif_relation"] == "shared"
        saw_diagonal |= observed["winner_linkage"] == "diagonal"
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] |= rival(pair["input"]) != expected

    if ranks != {"lowest", "highest"}:
        reasons.append("demonstrations must show both the lowest and highest color winning")
    if positions != {"first", "later"}:
        reasons.append("demonstrations must show winner-first and winner-later scenes")
    if len(count_profiles) < 3:
        reasons.append("demonstrations must vary the object-count profile")
    if not saw_cell_conflict:
        reasons.append("demonstrations need an object-count versus cell-mass conflict")
    if not saw_shared_losers:
        reasons.append("demonstrations need two losing colors that share a motif")
    if not saw_diagonal:
        reasons.append("demonstrations need an 8-connected but not 4-connected winner")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query input invalid: {errors[0]}")
    return reasons


def mutation_fixtures():
    """Task-local must-reject near-misses used by the defect lint."""
    base = generate(911, 0, difficulty="medium")
    fixtures = []

    tied = [row[:] for row in base]
    info, _ = _analysis(tied)
    winner = info["winner"]
    loser = max(
        (color for color in info["colors"] if color != winner),
        key=lambda color: info["counts"][color],
    )
    obj = info["by_color"][winner][-1]
    for row, col in obj["cells"]:
        tied[row][col] = 0
    fixtures.append(("tied_object_counts", tied))

    varied = [row[:] for row in base]
    info, _ = _analysis(varied)
    obj = info["by_color"][winner][-1]
    row, col = obj["cells"][0]
    varied[row][col] = 0
    fixtures.append(("same_color_nonidentical_motif", varied))

    tiny = [row[:] for row in base]
    info, _ = _analysis(tiny)
    obj = info["by_color"][loser][0]
    for row, col in obj["cells"][3:]:
        tiny[row][col] = 0
    fixtures.append(("undersized_object", tiny))

    extra_color = [row[:] for row in base]
    absent = next(color for color in range(1, 10) if color not in info["colors"])
    extra_color[0][0] = absent
    fixtures.append(("unrepeated_extra_color", extra_color))
    return fixtures
