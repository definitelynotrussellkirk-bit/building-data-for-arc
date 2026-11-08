"""Generator for ARC rule family 45922a9666b2 (source task 712bf12e).

The answer-bearing unit is a complete three-walker scene: canvas dimensions,
the ordered path roles, each role's turn count, and its top, boxed, or
right-edge terminal row.  This generator preserves one of the four linked
published role profiles while procedurally varying start columns, turn rows,
and off-path gray cells.  Total gray mass is preserved per profile.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "45922a9666b2"
TASK_ID = "45922a9666b2"
VERSION = "3.0.0"
RULE_HASH = "26a6c2419e6e"

SUMMARY = (
    "Every red cell on the bottom row starts an independent walker. A walker "
    "moves upward while the cell above is not gray. When gray blocks the cell "
    "above, it moves one cell right if that cell is in bounds and not gray, "
    "then again prefers upward. It stops at the top or when both options are "
    "blocked, and every visited cell becomes red."
)

INVARIANTS = [
    "exactly three red starts occur on the bottom row",
    "one complete linked published tuple of path roles is preserved",
    "each role preserves its turn count, stop type, and terminal row",
    "the three routes are disjoint and no blocker conflicts with a route cell",
    "the published total gray count and fixed palette {0,2,5} are preserved",
]

SCENE_PROFILES = (
    "profile_13x14_mixed",
    "profile_12x13_light",
    "profile_13x15_dense",
    "profile_13x13_edge",
)
ROUTE_LAYOUTS = ("canonical", "procedural")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked path-role profile",
        "valid": (
            "profile_13x14_mixed|profile_12x13_light|"
            "profile_13x15_dense|profile_13x13_edge"
        ),
    },
    "route_layout": {
        "type": "str",
        "default": "15% canonical and 85% procedural path geometry",
        "valid": "canonical|procedural",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# The four unique published inputs across the linked training and augmented
# rows. Outputs are never embedded; rule_mirror derives them from each input.
_PROFILE_ROWS = {
    "profile_13x14_mixed": (
        "00000050005000",
        "00000000500050",
        "00000000000500",
        "00550005500000",
        "00550000000000",
        "00000050005000",
        "05500000050000",
        "50500500000005",
        "50005050000000",
        "50000000005000",
        "00500050005500",
        "00000005055000",
        "50200205502000",
    ),
    "profile_12x13_light": (
        "0500000005000",
        "0500055000000",
        "5000000500050",
        "0000050000000",
        "0000500000005",
        "0000500000000",
        "5000000000055",
        "0050000000000",
        "0050050050000",
        "0500500500000",
        "0000005500500",
        "0020020002000",
    ),
    "profile_13x15_dense": (
        "050000050000055",
        "050000000050050",
        "500000000000000",
        "000050000005000",
        "000000005050000",
        "055550000050050",
        "550000050550005",
        "050000000050000",
        "000550000500000",
        "050000050050500",
        "055000500050000",
        "005000000550500",
        "055200020200550",
    ),
    "profile_13x13_edge": (
        "0005050000055",
        "0000050505550",
        "0000005000000",
        "5050005500005",
        "0055050000005",
        "0000000050500",
        "0055050500000",
        "5000055050000",
        "0500000005500",
        "0505000505050",
        "0500000005500",
        "5050505000000",
        "0002000202550",
    ),
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
}

# Deterministic, noncanonical valid layouts used only if 512 seeded proposals
# all conflict. The fallback remains a complete requested procedural layout;
# it never drops a path or silently changes the requested axis.
_PROCEDURAL_FALLBACKS = {
    "profile_13x14_mixed": (
        (0, 1, 2),
        ((1, 1), (), (9, 1, 1)),
    ),
    "profile_12x13_light": (
        (0, 1, 3),
        ((1,), (3,), (3,)),
    ),
    "profile_13x15_dense": (
        (0, 1, 2),
        ((1, 1), (3, 3), (5, 5, 1)),
    ),
    "profile_13x13_edge": (
        (0, 1, 9),
        ((1,), (8,), (5, 5, 5)),
    ),
}


def _profile_grid(profile):
    return [
        [int(value) for value in row]
        for row in _PROFILE_ROWS[profile]
    ]


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _trace_path(grid, start_col):
    height = len(grid)
    width = len(grid[0])
    row = height - 1
    col = start_col
    cells = [(row, col)]
    stop = None
    for _ in range(height * width):
        if row > 0 and grid[row - 1][col] != 5:
            row -= 1
            cells.append((row, col))
        elif (
            row > 0
            and col + 1 < width
            and grid[row][col + 1] != 5
            and grid[row - 1][col] == 5
        ):
            col += 1
            cells.append((row, col))
        else:
            if row == 0:
                stop = "top"
            elif col + 1 >= width:
                stop = "right_edge"
            else:
                stop = "boxed"
            break
    return tuple(cells), stop


def _turn_count(cells):
    return sum(
        next_row == row and next_col == col + 1
        for (row, col), (next_row, next_col) in zip(cells, cells[1:])
    )


def _path_signature(grid):
    height = len(grid)
    width = len(grid[0])
    red_positions = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    )
    starts = tuple(
        col for col, value in enumerate(grid[-1]) if value == 2
    )
    paths = tuple(_trace_path(grid, col) for col in starts)
    gray_count = sum(value == 5 for row in grid for value in row)
    return (
        height,
        width,
        red_positions,
        starts,
        paths,
        gray_count,
    )


def _role_signature(height, width, paths, gray_count):
    return (
        height,
        width,
        tuple(
            (_turn_count(cells), stop, cells[-1][0])
            for cells, stop in paths
        ),
        gray_count,
    )


@lru_cache(maxsize=None)
def _profile_signature(profile):
    return _path_signature(_profile_grid(profile))


@lru_cache(maxsize=None)
def _profile_role_signature(profile):
    height, width, _reds, _starts, paths, gray_count = (
        _profile_signature(profile)
    )
    return _role_signature(height, width, paths, gray_count)


def _constraints_for_paths(paths):
    open_cells = set()
    critical_gray = set()
    for cells, stop in paths:
        cells_set = set(cells)
        if open_cells & cells_set:
            return None
        open_cells.update(cells_set)
        for (row, col), (next_row, next_col) in zip(cells, cells[1:]):
            if next_row == row and next_col == col + 1:
                critical_gray.add((row - 1, col))
        row, col = cells[-1]
        if stop in ("boxed", "right_edge"):
            critical_gray.add((row - 1, col))
        if stop == "boxed":
            critical_gray.add((row, col + 1))
    if open_cells & critical_gray:
        return None
    return frozenset(open_cells), frozenset(critical_gray)


@lru_cache(maxsize=None)
def _profile_constraints(profile):
    constraints = _constraints_for_paths(_profile_signature(profile)[4])
    if constraints is None:
        raise AssertionError("published profile has conflicting routes")
    open_cells, critical_gray = constraints
    grid = _profile_grid(profile)
    height = len(grid)
    width = len(grid[0])
    candidates = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in open_cells
        and (row, col) not in critical_gray
    )
    canonical_nuisance = frozenset(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
        and (row, col) not in critical_gray
    )
    return open_cells, critical_gray, candidates, canonical_nuisance


def _build_path(height, start_col, role, turn_rows):
    turn_count, stop, terminal_row = role
    if len(turn_rows) != turn_count:
        raise ValueError("turn-row count does not match role")
    row = height - 1
    col = start_col
    cells = [(row, col)]
    turns_by_row = {}
    for turn_row in turn_rows:
        turns_by_row[turn_row] = turns_by_row.get(turn_row, 0) + 1
    while row > terminal_row:
        for _turn in range(turns_by_row.get(row, 0)):
            col += 1
            cells.append((row, col))
        row -= 1
        cells.append((row, col))
    if terminal_row > 0:
        for _turn in range(turns_by_row.get(terminal_row, 0)):
            col += 1
            cells.append((row, col))
    return tuple(cells), stop


def _starts_fit(starts, roles, width):
    for start_col, (turn_count, stop, _terminal_row) in zip(
        starts, roles
    ):
        final_col = start_col + turn_count
        if final_col >= width:
            return False
        if stop == "boxed" and final_col + 1 >= width:
            return False
        if stop == "right_edge" and final_col != width - 1:
            return False
    return True


def _procedural_paths(profile, rng):
    height, width, roles, _gray_count = _profile_role_signature(profile)
    canonical_paths = _profile_signature(profile)[4]
    for _attempt in range(512):
        starts = tuple(sorted(rng.sample(range(width), 3)))
        if not _starts_fit(starts, roles, width):
            continue
        paths = []
        for start_col, role in zip(starts, roles):
            turn_count, _stop, terminal_row = role
            allowed_rows = tuple(range(max(1, terminal_row), height))
            turn_rows = tuple(
                sorted(
                    (
                        rng.choice(allowed_rows)
                        for _turn in range(turn_count)
                    ),
                    reverse=True,
                )
            )
            paths.append(
                _build_path(height, start_col, role, turn_rows)
            )
        paths = tuple(paths)
        if paths == canonical_paths:
            continue
        if _constraints_for_paths(paths) is not None:
            return paths

    starts, row_groups = _PROCEDURAL_FALLBACKS[profile]
    paths = tuple(
        _build_path(height, start_col, role, turn_rows)
        for start_col, role, turn_rows in zip(starts, roles, row_groups)
    )
    if (
        paths == canonical_paths
        or _constraints_for_paths(paths) is None
    ):
        raise AssertionError("invalid procedural fallback")
    return paths


def _render_scene(profile, paths, rng):
    height, width, _roles, target_gray_count = (
        _profile_role_signature(profile)
    )
    constraints = _constraints_for_paths(paths)
    if constraints is None:
        raise ValueError("path constraints conflict")
    open_cells, critical_gray = constraints
    candidates = tuple(
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in open_cells
        and (row, col) not in critical_gray
    )
    nuisance_count = target_gray_count - len(critical_gray)
    if nuisance_count < 0 or nuisance_count > len(candidates):
        raise ValueError("profile gray mass is infeasible")
    selected = rng.sample(candidates, nuisance_count)
    grid = [[0 for _col in range(width)] for _row in range(height)]
    for row, col in critical_gray:
        grid[row][col] = 5
    for row, col in selected:
        grid[row][col] = 5
    for cells, _stop in paths:
        row, col = cells[0]
        grid[row][col] = 2
    traced = tuple(
        _trace_path(grid, cells[0][1])
        for cells, _stop in paths
    )
    if traced != paths:
        raise AssertionError("constructed path trace diverged")
    return grid


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    if set(value for row in coerced for value in row) != {0, 2, 5}:
        return None
    height, width, red_positions, starts, paths, gray_count = (
        _path_signature(coerced)
    )
    if (
        len(starts) != 3
        or len(red_positions) != 3
        or any(row != height - 1 for row, _col in red_positions)
    ):
        return None
    constraints = _constraints_for_paths(paths)
    if constraints is None:
        return None
    observed_role = _role_signature(
        height,
        width,
        paths,
        gray_count,
    )
    matches = [
        profile
        for profile in SCENE_PROFILES
        if observed_role == _profile_role_signature(profile)
    ]
    if len(matches) != 1:
        return None
    profile = matches[0]
    route_layout = (
        "canonical"
        if paths == _profile_signature(profile)[4]
        else "procedural"
    )
    return {
        "scene_profile": profile,
        "route_layout": route_layout,
    }


def canonical_profile_index(grid):
    """Return the complete linked public path-role profile index."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a returned valid grid."""
    signature = _semantic_signature(grid)
    if signature is None:
        return {}
    return dict(signature)


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            ("profile_13x14_mixed",) * 30
            + ("profile_12x13_light",) * 40
            + ("profile_13x15_dense",) * 15
            + ("profile_13x13_edge",) * 15
        )
    if difficulty == "hard":
        return (
            ("profile_13x14_mixed",) * 15
            + ("profile_12x13_light",) * 15
            + ("profile_13x15_dense",) * 35
            + ("profile_13x13_edge",) * 35
        )
    return (
        ("profile_13x14_mixed",) * 25
        + ("profile_12x13_light",) * 25
        + ("profile_13x15_dense",) * 25
        + ("profile_13x13_edge",) * 25
    )


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")
    if (
        "route_layout" in overrides
        and overrides["route_layout"] not in ROUTE_LAYOUTS
    ):
        raise ValueError("unknown route_layout")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    route_layout = ctx.draw_choice(
        "route_layout",
        ("canonical",) * 15 + ("procedural",) * 85,
    )
    if route_layout == "canonical":
        paths = _profile_signature(profile)[4]
    else:
        paths = _procedural_paths(
            profile,
            ctx.draw_rng("route_geometry"),
        )
    grid = _render_scene(
        profile,
        paths,
        ctx.draw_rng("nuisance_cells"),
    )
    observed = _semantic_signature(grid)
    if observed != {
        "scene_profile": profile,
        "route_layout": route_layout,
    }:
        raise AssertionError("constructed scene lost an exact axis")
    return grid


def rule_mirror(grid):
    """Independent Python mirror of the canonical Racket walker rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in coerced]
    starts = tuple(
        col for col, value in enumerate(coerced[-1]) if value == 2
    )
    for start_col in starts:
        cells, _stop = _trace_path(coerced, start_col)
        for row, col in cells:
            output[row][col] = 2
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept only complete linked public path-role profiles."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must preserve one complete published path-role profile: "
            "exact canvas, three disjoint routes, ordered turn/stop/terminal "
            "tuple, gray mass, and palette {0,2,5}"
        ]
    if rule_mirror(coerced) == coerced:
        return ["walker rule must change at least one cell"]
    return []
