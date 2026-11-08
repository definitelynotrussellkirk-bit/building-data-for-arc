"""Generator for ARC task b5f36515995c — route colored pairs around a wall.

The input contains a nearly full-height cyan (8) wall with two or three gaps.
Every other color appears exactly twice, once on each side of the wall.  The
canonical rule processes colors in ascending order, paints the deterministic
right/down/left/up BFS shortest path between matching endpoints, and treats the
wall, foreign terminals, and already-painted earlier paths as obstacles.

The three-slot lesson schedule is deliberately adversarial:

* ``separate``: color order agrees on both sides and routes do not interact;
* ``blocked_detour``: an earlier path blocks a later pair's independent shortest
  route, forcing the later color through a different gap;
* ``crossed``: endpoint rank differs across the wall, refuting row-rank pairing.

Every consecutive three-demo window therefore exposes wall avoidance, matching
by color, and sequential path blocking rather than merely repeating a fixed
canonical layout.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b5f36515995c"
TASK_ID = GENERATOR_ID
RULE_HASH = "3eba0ba7c07d"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "3.0.0"  # exact axes + structural checker + adversarial lesson schedule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Connect each same-colored endpoint pair through background cells. Cyan 8 "
    "is an impassable wall. Process colors in ascending order and paint the "
    "right/down/left/up BFS shortest path while treating foreign terminals and "
    "already-painted earlier paths as blocked."
)

INVARIANTS = [
    "the rectangular 10..12 by 11..12 input uses background 0 and wall color 8",
    "the middle column is color 8 except for exactly 2 or 3 separated gaps",
    "there are exactly 2 or 3 non-{0,8} colors, each appearing exactly twice",
    "each color has one endpoint strictly left and one strictly right of the wall",
    "every endpoint row is blocked at the wall, so every route must detour via a gap",
    "ascending-color BFS routes are contiguous, preserve the wall, and add path cells",
]

ROUTING_PROFILES = ("separate", "blocked_detour", "crossed")
SCHEDULE_PROFILES = ROUTING_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample/seed schedule over canonical 10..12 heights",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "sample/seed schedule over canonical 11..12 widths",
        "valid": "11..12",
    },
    "n_pairs": {
        "type": "int",
        "default": "2,2,3 repeating with the lesson schedule",
        "valid": "2..3",
    },
    "n_gaps": {
        "type": "int",
        "default": "2,3,3 repeating with the lesson schedule",
        "valid": "2..3",
    },
    "routing_profile": {
        "type": "str",
        "default": "sample_index mod 3 schedule",
        "valid": "separate|blocked_detour|crossed",
    },
}

# Three routes cannot cross a two-gap full-height wall because each painted
# path permanently occupies its wall-gap cell.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_pairs": 3, "n_gaps": 2},
]

_DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))
_PAIR_COLORS = (2, 3, 4, 5, 6, 7, 9)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_DEFAULT_PAIR_GAPS = ((2, 2), (2, 3), (3, 3))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the exact three-slot teaching cadence to the semantic gate."""
    del seed, difficulty
    return ROUTING_PROFILES[int(sample_index) % len(ROUTING_PROFILES)]


def _copy_grid(grid):
    return [list(row) for row in grid]


def _rectangular_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return 0, 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [f"cell ({r},{c})={value!r} is not an integer color 0..9"]
    return len(grid), width, []


def _bfs_path(h, w, blocked, start, goal):
    """Mirror the canonical Racket BFS, including its no-path fallback."""
    previous = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return list(reversed(path))
        for dr, dc in _DIRS:
            nxt = (current[0] + dr, current[1] + dc)
            if (
                0 <= nxt[0] < h
                and 0 <= nxt[1] < w
                and nxt not in blocked
                and nxt not in previous
            ):
                previous[nxt] = current
                queue.append(nxt)
    return [start, goal]


def _color_endpoints(grid, colors):
    return {
        color: tuple(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        )
        for color in colors
    }


def _route_paths(grid, *, ignore_prior_paths=False, ignore_wall=False):
    """Return (output, paths) under the selected or a named rival policy."""
    h, w = len(grid), len(grid[0])
    colors = sorted({value for row in grid for value in row if value not in (0, 8)})
    endpoints = _color_endpoints(grid, colors)
    out = _copy_grid(grid)
    paths = {}
    for color in colors:
        cells = endpoints[color]
        if len(cells) != 2:
            continue
        source = grid if ignore_prior_paths else out
        blocked = {
            (r, c)
            for r, row in enumerate(source)
            for c, value in enumerate(row)
            if (
                (value == 8 and not ignore_wall)
                or (value not in (0, 8, color))
            )
        }
        path = _bfs_path(h, w, blocked, cells[0], cells[1])
        paths[color] = path
        for r, c in path:
            out[r][c] = color
    return out, paths


def rule_mirror(grid):
    """Test-only Python mirror; canonical Racket remains output authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _route_paths(grid)[0]


def _path_is_contiguous(path):
    return bool(path) and all(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        for a, b in zip(path, path[1:])
    )


def _rank_order(endpoints, *, left, wall_col):
    def point(color):
        candidates = [
            cell for cell in endpoints[color]
            if (cell[1] < wall_col) == left
        ]
        return candidates[0]

    return tuple(sorted(endpoints, key=lambda color: (*point(color), color)))


def _analyze(grid) -> dict[str, Any]:
    h, w, errors = _rectangular_grid(grid)
    facts: dict[str, Any] = {
        "errors": errors,
        "h": h,
        "w": w,
        "wall_col": None,
        "gap_rows": (),
        "colors": (),
        "endpoints": {},
        "paths": {},
        "independent_paths": {},
        "crossings": {},
        "routing_profile": None,
    }
    if errors:
        return facts
    if not (8 <= h <= 14 and 9 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} are outside the lawful task envelope")

    wall_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    wall_columns = sorted({c for _, c in wall_cells})
    if len(wall_columns) != 1:
        errors.append(f"expected color 8 in exactly one wall column, found {wall_columns}")
        return facts
    wall_col = wall_columns[0]
    facts["wall_col"] = wall_col
    if wall_col != w // 2:
        errors.append(f"wall column {wall_col} is not the middle column {w // 2}")
    gap_rows = tuple(r for r in range(h) if grid[r][wall_col] == 0)
    facts["gap_rows"] = gap_rows
    if not 1 <= len(gap_rows) <= 3:
        errors.append(f"wall must have 1..3 gaps, found {len(gap_rows)}")
    if any(b - a < 2 for a, b in zip(gap_rows, gap_rows[1:])):
        errors.append("wall gaps must be separated by at least one wall cell")
    expected_wall = {(r, wall_col) for r in range(h) if r not in gap_rows}
    if set(wall_cells) != expected_wall:
        errors.append("color 8 must form one full-height wall except at its gaps")

    counts = Counter(value for row in grid for value in row if value not in (0, 8))
    colors = tuple(sorted(counts))
    facts["colors"] = colors
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2 or 3 endpoint colors, found {len(colors)}")
    for color, count in counts.items():
        if count != 2:
            errors.append(f"color {color} appears {count} times, expected exactly 2")

    endpoints = _color_endpoints(grid, colors)
    facts["endpoints"] = endpoints
    for color, cells in endpoints.items():
        if len(cells) != 2:
            continue
        left = [cell for cell in cells if cell[1] < wall_col]
        right = [cell for cell in cells if cell[1] > wall_col]
        if len(left) != 1 or len(right) != 1:
            errors.append(f"color {color} must have one endpoint on each side of the wall")
            continue
        if any(cell[0] in gap_rows for cell in cells):
            errors.append(f"color {color} has an endpoint on a gap row, hiding the wall detour")
        if abs(cells[0][0] - cells[1][0]) + abs(cells[0][1] - cells[1][1]) < 4:
            errors.append(f"color {color} endpoints are too close to demonstrate routing")

    if errors:
        return facts

    output, paths = _route_paths(grid)
    _, independent_paths = _route_paths(grid, ignore_prior_paths=True)
    facts["output"] = output
    facts["paths"] = paths
    facts["independent_paths"] = independent_paths
    crossings = {}
    for color in colors:
        path = paths.get(color, ())
        cells = endpoints[color]
        if len(path) <= 2 or not _path_is_contiguous(path):
            errors.append(f"color {color} has no contiguous routed path")
            continue
        if path[0] != cells[0] or path[-1] != cells[1]:
            errors.append(f"color {color} path endpoints disagree with its markers")
        crossing = tuple(r for r, c in path if c == wall_col)
        crossings[color] = crossing
        if len(crossing) != 1 or crossing[0] not in gap_rows:
            errors.append(f"color {color} must cross exactly one declared wall gap")
        if not any(grid[r][c] == 0 for r, c in path):
            errors.append(f"color {color} route paints no background cells")
    facts["crossings"] = crossings
    if errors:
        return facts

    blocked_detour = any(paths[color] != independent_paths[color] for color in colors)
    left_order = _rank_order(endpoints, left=True, wall_col=wall_col)
    right_order = _rank_order(endpoints, left=False, wall_col=wall_col)
    crossed = left_order != right_order
    facts["left_order"] = left_order
    facts["right_order"] = right_order
    facts["routing_profile"] = (
        "blocked_detour" if blocked_detour else ("crossed" if crossed else "separate")
    )
    facts["wall_rival_differs"] = _route_paths(grid, ignore_wall=True)[0] != output
    facts["independent_rival_differs"] = _route_paths(grid, ignore_prior_paths=True)[0] != output
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, degenerate, unreachable, and rule-hiding scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid):
    """The exact wall/pairs/routing grammar used by canonical and generated data."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "n_pairs": len(facts["colors"]),
        "n_gaps": len(facts["gap_rows"]),
        "routing_profile": facts["routing_profile"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    facts = _analyze(grid)
    if facts["errors"]:
        return {"errors": list(facts["errors"])}
    return {
        **observe_overrides(grid),
        "gap_rows": facts["gap_rows"],
        "crossing_rows": tuple(facts["crossings"][color][0] for color in facts["colors"]),
        "path_lengths": tuple(len(facts["paths"][color]) for color in facts["colors"]),
        "left_order": facts["left_order"],
        "right_order": facts["right_order"],
        "wall_rival_differs": facts["wall_rival_differs"],
        "independent_rival_differs": facts["independent_rival_differs"],
    }


def _default_axes(seed, sample_index):
    slot = int(sample_index) % 3
    n_pairs, n_gaps = _DEFAULT_PAIR_GAPS[slot]
    return {
        "grid_h": 10 + ((int(seed) + int(sample_index)) % 3),
        "grid_w": 11 + ((int(seed) * 3 + int(sample_index)) % 2),
        "n_pairs": n_pairs,
        "n_gaps": n_gaps,
        "routing_profile": ROUTING_PROFILES[slot],
    }


def _validate_call(difficulty, overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    if overrides.get("n_pairs") == 3 and overrides.get("n_gaps") == 2:
        raise ValueError("n_pairs=3 is incompatible with n_gaps=2")


def _classify_constructed(grid, wall_col, colors):
    """Fast candidate classifier for scenes already built by this generator."""
    output, paths = _route_paths(grid)
    _, independent_paths = _route_paths(grid, ignore_prior_paths=True)
    crossings = {}
    for color in colors:
        path = paths.get(color, ())
        if len(path) <= 2 or not _path_is_contiguous(path):
            return None
        crossing = tuple(r for r, c in path if c == wall_col)
        if len(crossing) != 1:
            return None
        crossings[color] = crossing
    if len({rows[0] for rows in crossings.values()}) < 2:
        return None
    blocked_detour = any(paths[color] != independent_paths[color] for color in colors)
    endpoints = _color_endpoints(grid, colors)
    crossed = (
        _rank_order(endpoints, left=True, wall_col=wall_col)
        != _rank_order(endpoints, left=False, wall_col=wall_col)
    )
    profile = "blocked_detour" if blocked_detour else ("crossed" if crossed else "separate")
    return profile, output


def _build_scene(h, w, n_pairs, n_gaps, profile, colors, rng):
    wall_col = w // 2
    candidate_gap_rows = tuple(range(1, h - 1))
    left_positions = tuple((r, c) for r in range(h) for c in range(1, wall_col))
    right_positions = tuple((r, c) for r in range(h) for c in range(wall_col + 1, w - 1))

    for _attempt in range(4000):
        gap_rows = tuple(sorted(rng.sample(candidate_gap_rows, n_gaps)))
        if any(b - a < 2 for a, b in zip(gap_rows, gap_rows[1:])):
            continue
        allowed_left = [cell for cell in left_positions if cell[0] not in gap_rows]
        allowed_right = [cell for cell in right_positions if cell[0] not in gap_rows]
        left = rng.sample(allowed_left, n_pairs)
        right = rng.sample(allowed_right, n_pairs)
        if any(
            abs(left[i][0] - right[i][0]) + abs(left[i][1] - right[i][1]) < 4
            for i in range(n_pairs)
        ):
            continue

        grid = full_grid(h, w, 0)
        for row in range(h):
            if row not in gap_rows:
                grid[row][wall_col] = 8
        for color, a, b in zip(colors, left, right):
            grid[a[0]][a[1]] = color
            grid[b[0]][b[1]] = color

        classified = _classify_constructed(grid, wall_col, colors)
        if classified is None or classified[0] != profile:
            continue
        output = classified[1]
        # Every ordinary draw must visibly require the wall.
        if _route_paths(grid, ignore_wall=True)[0] == output:
            continue
        facts = _analyze(grid)
        if facts["errors"]:
            raise AssertionError(f"constructed an invalid scene: {facts['errors']!r}")
        expected = {
            "grid_h": h,
            "grid_w": w,
            "n_pairs": n_pairs,
            "n_gaps": n_gaps,
            "routing_profile": profile,
        }
        observed = {
            "grid_h": facts["h"],
            "grid_w": facts["w"],
            "n_pairs": len(facts["colors"]),
            "n_gaps": len(facts["gap_rows"]),
            "routing_profile": facts["routing_profile"],
        }
        if observed != expected:
            raise AssertionError(f"constructed axes {expected!r}, observed {observed!r}")
        return grid
    raise ValueError(
        f"could not realize profile={profile!r}, n_pairs={n_pairs}, "
        f"n_gaps={n_gaps} on {h}x{w} after 4000 deterministic attempts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    explicit = set(overrides)
    effective = _default_axes(seed, sample_index)
    effective.update(overrides)

    # Single-axis boundary overrides remain realizable.  Only an explicitly
    # requested incompatible pair is rejected and declared above.
    if "n_pairs" in explicit and "n_gaps" not in explicit and effective["n_pairs"] > effective["n_gaps"]:
        effective["n_gaps"] = effective["n_pairs"]
    if "n_gaps" in explicit and "n_pairs" not in explicit and effective["n_pairs"] > effective["n_gaps"]:
        effective["n_pairs"] = effective["n_gaps"]
    if effective["n_pairs"] > effective["n_gaps"]:
        raise ValueError("n_pairs cannot exceed n_gaps for a full-height blocking wall")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 10, 12)
    w = ctx.draw_int("grid_w", 11, 12)
    n_pairs = ctx.draw_int("n_pairs", 2, 3)
    n_gaps = ctx.draw_int("n_gaps", 2, 3)
    profile = ctx.draw_choice("routing_profile", ROUTING_PROFILES)
    colors = tuple(ctx.draw_distinct_colors("pair_colors", n=n_pairs, exclude=(0, 8)))
    layout_rng = ctx.draw_rng(f"layout_{difficulty or 'default'}")
    layout_seed = layout_rng.getrandbits(128)
    del layout_seed  # consuming the draw makes the band-specific label auditable
    return _build_scene(h, w, n_pairs, n_gaps, profile, colors, layout_rng)


# ---------------------------------------------------------------------------
# Named rival rules and lesson-level identifiability contract
# ---------------------------------------------------------------------------


def _rival_identity(grid):
    return _copy_grid(grid)


def _rival_ignore_wall(grid):
    return _route_paths(grid, ignore_wall=True)[0]


def _rival_independent_paths(grid):
    return _route_paths(grid, ignore_prior_paths=True)[0]


def _rival_rank_pairing(grid):
    """Pair endpoints by vertical rank rather than by matching color."""
    facts = _analyze(grid)
    if facts["errors"]:
        return _copy_grid(grid)
    h, w, wall_col = facts["h"], facts["w"], facts["wall_col"]
    endpoints = facts["endpoints"]
    left_cells = sorted(
        (cell, color)
        for color, cells in endpoints.items()
        for cell in cells
        if cell[1] < wall_col
    )
    right_cells = sorted(
        (cell, color)
        for color, cells in endpoints.items()
        for cell in cells
        if cell[1] > wall_col
    )
    out = _copy_grid(grid)
    for (start, color), (goal, _right_color) in zip(left_cells, right_cells):
        blocked = {
            (r, c)
            for r, row in enumerate(out)
            for c, value in enumerate(row)
            if value == 8 or (value not in (0, 8, color))
        }
        for r, c in _bfs_path(h, w, blocked, start, goal):
            out[r][c] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity": _rival_identity,
    "ignore_wall": _rival_ignore_wall,
    "independent_paths": _rival_independent_paths,
    "rank_pairing": _rival_rank_pairing,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "independent_paths": _rival_independent_paths,
    "rank_pairing": _rival_rank_pairing,
}


def _witness(predicate):
    def wrapped(grid):
        facts = _analyze(grid)
        return not facts["errors"] and bool(predicate(facts))

    return wrapped


SEMANTIC_WITNESSES = {
    "wall_changes_the_route": _witness(lambda facts: facts["wall_rival_differs"]),
    "earlier_path_blocks_later_pair": _witness(
        lambda facts: facts["routing_profile"] == "blocked_detour"
        and facts["independent_rival_differs"]
    ),
    "crossed_endpoint_order_requires_color_matching": _witness(
        lambda facts: facts["routing_profile"] == "crossed"
    ),
}

WITNESS_RIVALS = {
    "wall_changes_the_route": ["ignore_wall"],
    "earlier_path_blocks_later_pair": ["independent_paths"],
    "crossed_endpoint_order_requires_color_matching": ["rank_pairing"],
}


def lesson_identifiable(demos, query):
    """Require every three-demo lesson to kill the principal shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    profiles = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the routing rule")
            continue
        profiles.add(observe_overrides(pair["input"])["routing_profile"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the routing rule")

    missing_profiles = sorted(set(ROUTING_PROFILES) - profiles)
    if missing_profiles:
        reasons.append(f"demonstrations omit routing profile(s): {missing_profiles}")

    for name, rival in LESSON_COMPETITORS.items():
        if name == "identity":
            # Every valid routed scene already paints background; retaining this
            # rival makes the lesson report explicit without demanding a special
            # schedule slot.
            pass
        survived = True
        for pair in demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    survived = False
                    break
            except Exception:
                survived = False
                break
        if survived:
            reasons.append(f"rival {name!r} still fits every demonstration")
    return reasons
