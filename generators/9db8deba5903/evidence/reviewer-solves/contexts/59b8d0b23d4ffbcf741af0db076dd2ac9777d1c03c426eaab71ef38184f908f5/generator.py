"""Semantic curriculum for ARC task ``9db8deba5903``.

The input is a non-trivial square pattern.  The rule produces a 2x2 tiling of
that pattern: identity, 90 degrees counter-clockwise, 180 degrees, and 90
degrees clockwise.  The curriculum deliberately includes both full four-state
rotation orbits and lawful half-turn-symmetric inputs, because one canonical
training example has the latter geometry.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "9db8deba5903"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "847ceb038813"

SUMMARY = (
    "Generate a 3x3..7x7 square pattern with 2..4 colors and a visible "
    "quarter-turn change.  The output tiles identity, 90-degree CCW, "
    "180-degree, and 90-degree CW copies into the four quadrants.  A "
    "deterministic four-profile curriculum per difficulty band includes a "
    "canonical 3x3 binary profile, multicolor cases, full rotation orbits, "
    "and lawful half-turn-symmetric cases."
)

INVARIANTS = [
    "input is a literal square ARC grid with side length 3..7",
    "input uses 2..4 colors and every color occupies at least two cells",
    "input is not invariant under a 90-degree rotation",
    "the curriculum includes both two-state and four-state rotation orbits",
]

# name, nominal band, side, sorted color counts, layout family, half-turn case
_PROFILE_ROWS = (
    ("easy_canonical_sparse", "easy", 3, (2, 7), "half_turn", True),
    ("easy_clustered_binary", "easy", 4, (5, 11), "cluster", False),
    ("easy_scattered_tricolor", "easy", 4, (3, 5, 8), "scatter", False),
    ("easy_edge_binary", "easy", 5, (8, 17), "edge", False),
    ("medium_canonical_balanced", "medium", 3, (4, 5), "half_turn", True),
    ("medium_clustered_tricolor", "medium", 5, (4, 7, 14), "cluster", False),
    ("medium_scattered_fourcolor", "medium", 5, (3, 4, 7, 11), "scatter", False),
    ("medium_edge_binary", "medium", 6, (13, 23), "edge", False),
    ("hard_canonical_diagonal", "hard", 3, (3, 6), "half_turn", True),
    ("hard_clustered_tricolor", "hard", 6, (6, 11, 19), "cluster", False),
    ("hard_scattered_fourcolor", "hard", 7, (5, 9, 14, 21), "scatter", False),
    ("hard_edge_binary", "hard", 7, (18, 31), "edge", False),
)

SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {
    name: {
        "band": band,
        "n": n,
        "counts": tuple(counts),
        "family": family,
        "half_turn": half_turn,
    }
    for name, band, n, counts, family, half_turn in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (n, tuple(sorted(counts))): name
    for name, _band_name, n, counts, _family, _half_turn in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile curriculum for the selected difficulty band",
        "valid": (
            "easy_canonical_sparse|easy_clustered_binary|easy_scattered_tricolor|"
            "easy_edge_binary|medium_canonical_balanced|medium_clustered_tricolor|"
            "medium_scattered_fourcolor|medium_edge_binary|hard_canonical_diagonal|"
            "hard_clustered_tricolor|hard_scattered_fourcolor|hard_edge_binary"
        ),
    }
}

# Legacy metadata names remain explicit and honest: there are no separate
# texture or degenerate domains in this profile-driven generator.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile for a band."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rot_cw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*reversed(grid))]


def _rot_ccw(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(list(zip(*grid)))]


def _rot_180(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotation_orbit_size(grid: Sequence[Sequence[int]]) -> int:
    r0 = [list(row) for row in grid]
    r1 = _rot_cw(r0)
    r2 = _rot_cw(r1)
    r3 = _rot_cw(r2)
    return len({repr(r0), repr(r1), repr(r2), repr(r3)})


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if height != width:
        errors.append(f"grid must be square, found {height}x{width}")
    if not 3 <= height <= 7 or not 3 <= width <= 7:
        errors.append(f"grid dimensions must be in 3..7, found {height}x{width}")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors
    return errors


def _is_solid_2x2(cells: list[tuple[int, int]]) -> bool:
    if len(cells) != 4:
        return False
    rows = sorted({r for r, _c in cells})
    cols = sorted({c for _r, c in cells})
    return (
        len(rows) == 2
        and len(cols) == 2
        and rows[1] == rows[0] + 1
        and cols[1] == cols[0] + 1
        and set(cells) == {(r, c) for r in rows for c in cols}
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    n = len(grid)
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            positions.setdefault(value, []).append((r, c))
    counts = Counter({color: len(cells) for color, cells in positions.items()})
    if not 2 <= len(counts) <= 4:
        errors.append(f"expected 2..4 distinct colors, found {len(counts)}")
    for color, cells in sorted(positions.items()):
        count = len(cells)
        if count < 2:
            errors.append(f"color {color} occupies only {count} cell(s)")
        # A tiny one-dimensional mark does not expose a meaningful 2-D
        # rotation.  Canonical minority shapes all span both axes.
        if count <= n:
            rows = {r for r, _c in cells}
            cols = {c for _r, c in cells}
            if len(rows) == 1 or len(cols) == 1:
                errors.append(f"color {color} forms a one-dimensional short line")
        if _is_solid_2x2(cells):
            errors.append(f"color {color} is only a solid 2x2 block")
    if _rot_cw(grid) == [list(row) for row in grid]:
        errors.append("grid is invariant under a 90-degree rotation")
    signature = (n, tuple(sorted(counts.values())))
    return {
        "errors": errors,
        "n": n,
        "counts": counts,
        "positions": positions,
        "scene_profile": _PROFILE_BY_SIGNATURE.get(signature),
        "orbit_size": _rotation_orbit_size(grid),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the declared profile exactly from shape and color multiplicities."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept lawful rule-revealing inputs and reject minimal impostors."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic predicate used by the generator semantic gate."""
    return self_check(grid)


def _neighbors(cell: tuple[int, int], n: int) -> list[tuple[int, int]]:
    r, c = cell
    return [
        (rr, cc)
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < n and 0 <= cc < n
    ]


def _connected(cells: set[tuple[int, int]], n: int) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        for neighbor in _neighbors(queue.popleft(), n):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _connected_seed(n: int, count: int, rng) -> set[tuple[int, int]]:
    cells = {(rng.randrange(n), rng.randrange(n))}
    while len(cells) < count:
        frontier = sorted(
            {
                neighbor
                for cell in cells
                for neighbor in _neighbors(cell, n)
                if neighbor not in cells
            }
        )
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return cells


def _scattered_seed(n: int, count: int, rng) -> set[tuple[int, int]]:
    all_cells = [(r, c) for r in range(n) for c in range(n)]
    rng.shuffle(all_cells)
    chosen: set[tuple[int, int]] = set()
    for cell in all_cells:
        if all(cell not in _neighbors(old, n) for old in chosen):
            chosen.add(cell)
            if len(chosen) == count:
                return chosen
    for cell in all_cells:
        chosen.add(cell)
        if len(chosen) == count:
            break
    return chosen


def _edge_seed(n: int, count: int, rng) -> set[tuple[int, int]]:
    edges = [
        [(0, c) for c in range(n)],
        [(n - 1, c) for c in range(n)],
        [(r, 0) for r in range(n)],
        [(r, n - 1) for r in range(n)],
    ]
    first, second = rng.sample(range(4), 2)
    chosen = {rng.choice(edges[first]), rng.choice(edges[second])}
    remaining = [(r, c) for r in range(n) for c in range(n) if (r, c) not in chosen]
    rng.shuffle(remaining)
    chosen.update(remaining[: count - len(chosen)])
    return chosen


def _family_seed(n: int, count: int, family: str, rng) -> set[tuple[int, int]]:
    if family == "cluster":
        return _connected_seed(n, count, rng)
    if family == "scatter":
        return _scattered_seed(n, count, rng)
    if family == "edge":
        return _edge_seed(n, count, rng)
    cells = [(r, c) for r in range(n) for c in range(n)]
    return set(rng.sample(cells, count))


def _family_holds(grid: Sequence[Sequence[int]], family: str) -> bool:
    n = len(grid)
    counts = Counter(value for row in grid for value in row)
    rare = min(counts, key=lambda color: (counts[color], color))
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == rare}
    if family == "cluster":
        return _connected(cells, n)
    if family == "scatter":
        return not _connected(cells, n)
    if family == "edge":
        touched = set()
        if any(r == 0 for r, _c in cells):
            touched.add("top")
        if any(r == n - 1 for r, _c in cells):
            touched.add("bottom")
        if any(c == 0 for _r, c in cells):
            touched.add("left")
        if any(c == n - 1 for _r, c in cells):
            touched.add("right")
        return len(touched) >= 2
    return True


def _draw_half_turn(n: int, counts: tuple[int, ...], palette: tuple[int, ...], rng):
    if n % 2 != 1:
        raise ValueError("half-turn profiles require an odd side length")
    center = (n // 2, n // 2)
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    seen = {center}
    for r in range(n):
        for c in range(n):
            if (r, c) in seen:
                continue
            mate = (n - 1 - r, n - 1 - c)
            pairs.append(((r, c), mate))
            seen.add((r, c))
            seen.add(mate)

    odd = [index for index, count in enumerate(counts) if count % 2]
    if len(odd) != 1:
        raise ValueError("half-turn profile must have exactly one odd color count")
    for _attempt in range(256):
        shuffled_pairs = list(pairs)
        rng.shuffle(shuffled_pairs)
        grid = [[palette[odd[0]] for _c in range(n)] for _r in range(n)]
        grid[center[0]][center[1]] = palette[odd[0]]
        cursor = 0
        for index, (color, count) in enumerate(zip(palette, counts)):
            pair_count = (count - (1 if index == odd[0] else 0)) // 2
            for pair in shuffled_pairs[cursor : cursor + pair_count]:
                for r, c in pair:
                    grid[r][c] = color
            cursor += pair_count
        if self_check(grid) == [] and _rot_180(grid) == grid:
            return grid
    raise RuntimeError("could not realize a lawful half-turn profile")


def _draw_general(
    n: int,
    counts: tuple[int, ...],
    palette: tuple[int, ...],
    family: str,
    rng,
):
    all_cells = [(r, c) for r in range(n) for c in range(n)]
    for _attempt in range(512):
        rare_cells = _family_seed(n, counts[0], family, rng)
        remaining = [cell for cell in all_cells if cell not in rare_cells]
        remaining_values = [
            color
            for color, count in zip(palette[1:], counts[1:])
            for _ in range(count)
        ]
        rng.shuffle(remaining_values)
        grid = [[palette[0] for _c in range(n)] for _r in range(n)]
        for (r, c), value in zip(remaining, remaining_values):
            grid[r][c] = value
        if (
            self_check(grid) == []
            and _rot_180(grid) != grid
            and _family_holds(grid, family)
        ):
            return grid
    raise RuntimeError(f"could not realize scene family {family!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", [scheduled])
    profile = _PROFILE_BY_NAME[profile_name]
    n = profile["n"]
    counts = profile["counts"]
    palette = ctx.draw_distinct_colors("palette", n=len(counts))
    rng = ctx.draw_rng("layout")
    if profile["half_turn"]:
        return _draw_half_turn(n, counts, palette, rng)
    return _draw_general(n, counts, palette, profile["family"], rng)


def _tile_quadrants(
    top_left: Sequence[Sequence[int]],
    top_right: Sequence[Sequence[int]],
    bottom_left: Sequence[Sequence[int]],
    bottom_right: Sequence[Sequence[int]],
) -> list[list[int]]:
    n = len(top_left)
    return [
        list(top_left[r]) + list(top_right[r])
        for r in range(n)
    ] + [
        list(bottom_left[r]) + list(bottom_right[r])
        for r in range(n)
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for regression tests and semantic rivals."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    original = [list(row) for row in grid]
    return _tile_quadrants(
        original,
        _rot_ccw(original),
        _rot_180(original),
        _rot_cw(original),
    )


def _repeat_identity(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    original = [list(row) for row in grid]
    return _tile_quadrants(original, original, original, original)


def _swap_quarter_turns(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    original = [list(row) for row in grid]
    return _tile_quadrants(
        original,
        _rot_cw(original),
        _rot_180(original),
        _rot_ccw(original),
    )


def _rotation_changes_grid(grid) -> bool:
    return _rot_cw(grid) != [list(row) for row in grid]


def _quarter_turn_direction_visible(grid) -> bool:
    return _rot_cw(grid) != _rot_ccw(grid)


def _half_turn_symmetric_case(grid) -> bool:
    original = [list(row) for row in grid]
    return _rot_180(grid) == original and _rot_cw(grid) != original


def _full_rotation_orbit(grid) -> bool:
    return _rotation_orbit_size(grid) == 4


def _multicolor_case(grid) -> bool:
    return len({value for row in grid for value in row}) >= 3


def _canonical_3x3_binary(grid) -> bool:
    return (
        len(grid) == 3
        and all(len(row) == 3 for row in grid)
        and len({value for row in grid for value in row}) == 2
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "rotation_changes_grid": _rotation_changes_grid,
    "quarter_turn_direction_visible": _quarter_turn_direction_visible,
    "half_turn_symmetric_case": _half_turn_symmetric_case,
    "full_rotation_orbit": _full_rotation_orbit,
    "multicolor_case": _multicolor_case,
    "canonical_3x3_binary": _canonical_3x3_binary,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "repeat_identity": _repeat_identity,
    "swap_quarter_turns": _swap_quarter_turns,
}
WITNESS_RIVALS = {
    "rotation_changes_grid": ["repeat_identity"],
    "quarter_turn_direction_visible": ["swap_quarter_turns"],
}
BRANCH_WITNESSES = {
    "half_turn_symmetric_case",
    "full_rotation_orbit",
    "multicolor_case",
    "canonical_3x3_binary",
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo lesson to falsify both named shortcut rules."""
    errors: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        errors.append(f"expected at least {EXAMPLES_NEEDED} demonstrations")
        return errors
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demonstration {index} is malformed")
            return errors
        if self_check(demo["input"]):
            errors.append(f"demonstration {index} has an invalid input")
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is malformed")
    elif self_check(query["input"]):
        errors.append("query has an invalid input")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            errors.append(f"competitor {name!r} survives every demonstration")
    return errors
