"""Generator for d8ce64d73f8a — flood the seed's four-connected chamber.

Gray 5 cells are walls.  The single red 2 is a seed.  The selected rule
repaints every non-wall cell reachable from that seed by cardinal moves cyan 8
and leaves every other chamber unchanged.

Every ordinary draw is also a counterexample to the two shortcuts left
unfalsified by the five public pairs: eight-connected flooding and always
choosing the lexicographically top-left chamber.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d8ce64d73f8a"
VERSION = "2.0.0"
TASK_ID = "d8ce64d73f8a"
RULE_HASH = "2a17285ed2a7"
SUMMARY = (
    "Gray 5 walls form two to four chambers; flood only the four-connected "
    "chamber containing the single red 2 seed with cyan 8."
)

INVARIANTS = [
    "the outer border is entirely gray(5)",
    "the only input colors are 0, 2, and 5, with exactly one red(2) seed",
    "non-wall cells form two to four cardinally connected chambers",
    "the seed chamber is not the lexicographically top-left chamber",
    "a diagonal-only contact makes eight-connected flooding overreach",
]

AXES = {
    "room_count": {
        "type": "int",
        "default": "rng 2..4",
        "valid": "2..4",
    },
    "seed_role": {
        "type": "str",
        "default": "rng",
        "valid": "largest|nonlargest",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical_anchor", "general_a", "general_b")

_CANONICAL_DIMS = ((10, 12), (11, 13), (12, 12), (10, 14), (12, 10))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = _CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))
_SEED_ROLES = ("largest", "nonlargest")

Grid = list[list[int]]
Cell = tuple[int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum slot for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _dimensions(ctx, profile: str, difficulty) -> tuple[int, int]:
    if profile == "canonical_anchor":
        return ctx.draw_rng("canonical_dimensions").choice(_CANONICAL_DIMS)
    ranges = {
        None: ((10, 16), (12, 19)),
        "easy": ((10, 12), (12, 15)),
        "medium": ((11, 15), (13, 18)),
        "hard": ((13, 18), (16, 22)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[difficulty]
    rng = ctx.draw_rng("general_dimensions")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi)


def _outer_border(height: int, width: int) -> Grid:
    grid = full_grid(height, width, 0)
    for c in range(width):
        grid[0][c] = 5
        grid[-1][c] = 5
    for r in range(height):
        grid[r][0] = 5
        grid[r][-1] = 5
    return grid


def _add_diagonal_corner_room(grid: Grid, ctx) -> None:
    """Isolate a bottom-right room whose corner only touches the main room diagonally."""
    height, width = len(grid), len(grid[0])
    size_rng = ctx.draw_rng("corner_room_size")
    room_h = size_rng.randint(2, min(4, height - 6))
    room_w = size_rng.randint(2, min(4, width - 6))
    corner_r = height - room_h - 2
    corner_c = width - room_w - 2

    # The open cell (corner_r, corner_c) belongs to the main chamber.  The
    # isolated room begins at (+1,+1); its two cardinal bridge cells are walls.
    for r in range(corner_r + 1, height):
        grid[r][corner_c] = 5
    for c in range(corner_c + 1, width):
        grid[corner_r][c] = 5


def _add_border_pocket(grid: Grid, center_col: int) -> None:
    """Use the top border as one side of a one-cell closed chamber.

    The compact U-shaped wall cannot line up with the distant corner L-wall,
    and the open row beneath it keeps the surrounding main chamber connected.
    """
    grid[1][center_col - 1] = 5
    grid[1][center_col + 1] = 5
    grid[2][center_col] = 5


def _add_pockets(grid: Grid, count: int, ctx) -> None:
    del ctx
    centers = (2, 6)
    if len(grid[0]) < 10:
        raise ValueError(f"grid width {len(grid[0])} cannot host two border pockets")
    for center_col in centers[:count]:
        _add_border_pocket(grid, center_col)


def _transform(grid: Grid, corner: str) -> Grid:
    """Move the constructed bottom-right chamber to the requested corner."""
    if corner == "bottom_right":
        return deepcopy(grid)
    if corner == "top_right":
        return [list(row) for row in reversed(grid)]
    if corner == "bottom_left":
        return [list(reversed(row)) for row in grid]
    if corner == "top_left":
        return [list(reversed(row)) for row in reversed(grid)]
    raise ValueError(f"unknown corner {corner!r}")


def _regions(grid: Grid, *, diagonal: bool = False) -> list[frozenset[Cell]]:
    height, width = len(grid), len(grid[0])
    steps = _EIGHT if diagonal else _CARDINAL
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 5}
    regions: list[frozenset[Cell]] = []
    while unseen:
        start = min(unseen)
        seen = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in steps:
                nr, nc = r + dr, c + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and grid[nr][nc] != 5
                    and (nr, nc) not in seen
                ):
                    seen.add((nr, nc))
                    queue.append((nr, nc))
        part = frozenset(seen)
        regions.append(part)
        unseen.difference_update(part)
    return sorted(regions, key=lambda cells: min(cells))


def _seed_cell(grid: Grid) -> Cell | None:
    hits = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    return hits[0] if len(hits) == 1 else None


def _paint(grid: Grid, cells) -> Grid:
    out = deepcopy(grid)
    for r, c in cells:
        out[r][c] = 8
    return out


def _build_scene(height: int, width: int, room_count: int, seed_role: str, ctx) -> Grid:
    grid = _outer_border(height, width)
    _add_diagonal_corner_room(grid, ctx)
    _add_pockets(grid, room_count - 2, ctx)

    if seed_role == "largest":
        corner = "top_left"
    else:
        corner = ctx.draw_rng("nonlargest_corner").choice(
            ("top_right", "bottom_left", "bottom_right")
        )
    grid = _transform(grid, corner)

    parts = _regions(grid)
    main = max(parts, key=lambda cells: (len(cells), tuple(sorted(cells))))
    non_main = [part for part in parts if part is not main]
    corner_room = max(non_main, key=lambda cells: (len(cells), tuple(sorted(cells))))
    target = main if seed_role == "largest" else corner_room
    seed = ctx.draw_rng("seed_cell").choice(sorted(target))
    grid[seed[0]][seed[1]] = 2
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    room_count = ctx.draw_int_strict("room_count", 2, 4)
    seed_role = ctx.draw_choice("seed_role", _SEED_ROLES)
    profile = schedule_profile(seed, sample_index, difficulty)
    height, width = _dimensions(ctx, profile, difficulty)
    grid = _build_scene(height, width, room_count, seed_role, ctx)
    issues = self_check(grid)
    if issues:
        raise RuntimeError(f"internal generator defect: {issues}")
    return grid


def _seed_region(grid: Grid, *, diagonal: bool = False) -> frozenset[Cell]:
    start = _seed_cell(grid)
    if start is None:
        return frozenset()
    return next(
        (part for part in _regions(grid, diagonal=diagonal) if start in part),
        frozenset(),
    )


def rule_mirror(grid: Grid) -> Grid:
    """Python mirror of the selected Racket rule, used only for semantic checks."""
    return _paint(grid, _seed_region(grid))


def _eight_connected_flood(grid: Grid) -> Grid:
    return _paint(grid, _seed_region(grid, diagonal=True))


def _top_left_flood(grid: Grid) -> Grid:
    parts = _regions(grid)
    return _paint(grid, parts[0] if parts else ())


def _analysis(grid: Grid) -> dict:
    parts = _regions(grid)
    start = _seed_cell(grid)
    seed_part = next(part for part in parts if start in part)
    return {
        "parts": parts,
        "seed_part": seed_part,
        "room_count": len(parts),
        "seed_role": (
            "largest" if len(seed_part) == max(len(part) for part in parts) else "nonlargest"
        ),
    }


def observe_overrides(grid: Grid) -> dict[str, object]:
    stats = _analysis(grid)
    return {
        "room_count": stats["room_count"],
        "seed_role": stats["seed_role"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical topology and reject malformed training scenes."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    height, width = len(grid), len(grid[0])
    if not (3 <= height <= 30 and 3 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} outside 3..30")
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            return errors + ["grid must be rectangular"]
        for value in row:
            if type(value) is not int or value not in (0, 2, 5):
                return errors + [f"invalid cell value {value!r}; expected only 0, 2, 5"]

    palette = {value for row in grid for value in row}
    if palette != {0, 2, 5}:
        errors.append(f"expected palette {{0, 2, 5}}, found {sorted(palette)}")
    if any(value != 5 for value in grid[0] + grid[-1]):
        errors.append("top and bottom borders must be gray wall 5")
    if any(row[0] != 5 or row[-1] != 5 for row in grid):
        errors.append("left and right borders must be gray wall 5")

    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(seeds) != 1:
        errors.append(f"expected exactly one red seed, found {len(seeds)}")

    parts = _regions(grid)
    if not 2 <= len(parts) <= 4:
        errors.append(f"expected two to four non-wall chambers, found {len(parts)}")
    if len(seeds) == 1:
        seed_part = next((part for part in parts if seeds[0] in part), frozenset())
        if len(seed_part) < 2:
            errors.append("seed chamber must contain at least one blank cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _witness_diagonal_separation(grid: Grid) -> bool:
    return rule_mirror(grid) != _eight_connected_flood(grid)


def _witness_seed_not_top_left(grid: Grid) -> bool:
    return rule_mirror(grid) != _top_left_flood(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "eight_connected": _eight_connected_flood,
    "top_left": _top_left_flood,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "diagonal_separation": _witness_diagonal_separation,
    "seed_not_top_left": _witness_seed_not_top_left,
}
WITNESS_RIVALS = {
    "diagonal_separation": ["eight_connected"],
    "seed_not_top_left": ["top_left"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when a declared rival still survives all demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with selected rule")
    if query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but answers the query differently"
                )
            else:
                reasons.append(f"{name} survives every demonstration and the query")
    return reasons
