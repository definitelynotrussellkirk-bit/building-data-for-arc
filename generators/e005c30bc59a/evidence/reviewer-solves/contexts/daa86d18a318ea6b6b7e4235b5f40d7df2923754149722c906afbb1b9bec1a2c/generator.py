"""Semantic generator for ARC task e005c30bc59a (reflected laser trail).

A single non-corner border source emits inward. Slash mirrors (1) and
backslash mirrors (2) turn the beam, walls (5) stop it, and traversed black
cells are painted with the source color. Ordinary draws are route-aware: each
contains at least one reached mirror and a non-trivial trail. Unreached mirrors
and walls remain available as canonical-style distractors.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e005c30bc59a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9114178dd0f7"

SUMMARY = (
    "A single source in color 3/4/6/7/8/9 sits on a non-corner border cell and "
    "launches a beam inward. Color 1 is a slash mirror, color 2 a backslash "
    "mirror, and color 5 a wall. The beam paints traversed black cells with the "
    "source color, turns at reached mirrors, and stops at a wall or boundary. "
    "Every ordinary draw reaches at least one mirror; optional off-route mirrors "
    "and walls teach that only objects encountered by the beam matter."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "rectangular 8..14 by 8..15 input over colors 0..9",
    "exactly one source-colored cell, on a non-corner border position",
    "1..4 interior mirrors (1/2), with at least one reached by the beam",
    "0..2 interior walls (5); the beam terminates at a wall or boundary",
    "every reached segment contains at least one black cell and the beam does not repeat a directional state",
]

SOURCE_COLORS = (3, 4, 6, 7, 8, 9)
SOURCE_EDGES = ("top", "bottom", "left", "right")
MIRROR_PROFILES = {
    "one_hit": (1, 0),
    "two_hit": (2, 0),
    "three_hit": (3, 0),
    "one_hit_one_decoy": (1, 1),
    "one_hit_two_decoys": (1, 2),
    "two_hit_one_decoy": (2, 1),
    "three_hit_one_decoy": (3, 1),
}
WALL_PROFILES = {
    "boundary_none": ("boundary", 0),
    "boundary_one_decoy": ("boundary", 1),
    "boundary_two_decoys": ("boundary", 2),
    "wall_stop": ("wall", 1),
    "wall_stop_plus_decoy": ("wall", 2),
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware with canonical-scale support", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware with canonical-scale support", "valid": "8..15"},
    "source_edge": {"type": "str", "default": "four-role cyclic schedule", "valid": "top|bottom|left|right"},
    "source_color": {"type": "int", "default": "cyclic schedule includes non-7 counterexamples", "valid": "3|4|6|7|8|9"},
    "mirror_profile": {
        "type": "str",
        "default": "difficulty-aware reached/decoy profile",
        "valid": "one_hit|two_hit|three_hit|one_hit_one_decoy|one_hit_two_decoys|two_hit_one_decoy|three_hit_one_decoy",
    },
    "wall_profile": {
        "type": "str",
        "default": "cyclic boundary/wall-stop schedule",
        "valid": "boundary_none|boundary_one_decoy|boundary_two_decoys|wall_stop|wall_stop_plus_decoy",
    },
}

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_SHAPES = ((8, 8), (9, 9), (10, 10), (9, 10))


def _bounce(direction: tuple[int, int], kind: int) -> tuple[int, int]:
    dr, dc = direction
    if kind == 1:
        return -dc, -dr
    if kind == 2:
        return dc, dr
    raise ValueError(f"unknown mirror kind {kind!r}")


def _mirror_kind(
    incoming: tuple[int, int], outgoing: tuple[int, int]
) -> int | None:
    for kind in (1, 2):
        if _bounce(incoming, kind) == outgoing:
            return kind
    return None


def _turns(direction: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    dr, dc = direction
    return ((-dc, dr), (dc, -dr))


def _distance_to_edge(
    h: int, w: int, position: tuple[int, int], direction: tuple[int, int]
) -> int:
    r, c = position
    dr, dc = direction
    if dr < 0:
        return r
    if dr > 0:
        return h - 1 - r
    if dc < 0:
        return c
    return w - 1 - c


def _step(
    position: tuple[int, int], direction: tuple[int, int], distance: int
) -> tuple[int, int]:
    return (
        position[0] + direction[0] * distance,
        position[1] + direction[1] * distance,
    )


def _source_position(rng, h: int, w: int, edge: str) -> tuple[int, int]:
    if edge == "top":
        return 0, rng.randint(1, w - 2)
    if edge == "bottom":
        return h - 1, rng.randint(1, w - 2)
    if edge == "left":
        return rng.randint(1, h - 2), 0
    if edge == "right":
        return rng.randint(1, h - 2), w - 1
    raise ValueError(f"unknown source edge {edge!r}")


def _inward(edge: str) -> tuple[int, int]:
    return {
        "top": (1, 0),
        "bottom": (-1, 0),
        "left": (0, 1),
        "right": (0, -1),
    }[edge]


def _sample_route(
    rng,
    *,
    h: int,
    w: int,
    edge: str,
    n_hit_mirrors: int,
    termination: str,
    required_kinds: tuple[int, ...] | None,
) -> dict[str, Any]:
    """Construct a non-crossing ray route with black cells between events."""
    if required_kinds is not None and len(required_kinds) != n_hit_mirrors:
        raise ValueError("required mirror-kind count does not match route profile")

    for _attempt in range(4096):
        source = _source_position(rng, h, w, edge)
        current = source
        direction = _inward(edge)
        used: set[tuple[int, int]] = {source}
        zero_path: list[tuple[int, int]] = []
        mirrors: list[tuple[int, int, int]] = []
        segments: list[int] = []
        failed = False

        for mirror_index in range(n_hit_mirrors):
            capacity = _distance_to_edge(h, w, current, direction)
            candidates: list[
                tuple[int, tuple[int, int], tuple[int, int], int, tuple[tuple[int, int], ...]]
            ] = []
            for distance in range(2, capacity):
                segment = tuple(_step(current, direction, d) for d in range(1, distance))
                mirror = _step(current, direction, distance)
                if mirror in used or any(cell in used for cell in segment):
                    continue
                for outgoing in _turns(direction):
                    kind = _mirror_kind(direction, outgoing)
                    if kind is None:
                        continue
                    if required_kinds is not None and kind != required_kinds[mirror_index]:
                        continue
                    if _distance_to_edge(h, w, mirror, outgoing) < 2:
                        continue
                    first_after = _step(mirror, outgoing, 1)
                    if first_after in used or first_after in segment:
                        continue
                    candidates.append((distance, mirror, outgoing, kind, segment))
            if not candidates:
                failed = True
                break
            _, mirror, outgoing, kind, segment = rng.choice(candidates)
            zero_path.extend(segment)
            used.update(segment)
            mirrors.append((mirror[0], mirror[1], kind))
            used.add(mirror)
            segments.append(len(segment))
            current = mirror
            direction = outgoing

        if failed:
            continue

        capacity = _distance_to_edge(h, w, current, direction)
        if termination == "boundary":
            if capacity < 1:
                continue
            final_segment = tuple(
                _step(current, direction, distance)
                for distance in range(1, capacity + 1)
            )
            wall_stop = None
        elif termination == "wall":
            if capacity < 3:
                continue
            wall_distance = rng.choice(list(range(2, capacity)))
            final_segment = tuple(
                _step(current, direction, distance)
                for distance in range(1, wall_distance)
            )
            wall_stop = _step(current, direction, wall_distance)
        else:
            raise ValueError(f"unknown termination {termination!r}")

        if not final_segment:
            continue
        if any(cell in used for cell in final_segment):
            continue
        if wall_stop is not None and (wall_stop in used or wall_stop in final_segment):
            continue
        zero_path.extend(final_segment)
        segments.append(len(final_segment))
        return {
            "source": source,
            "mirrors": tuple(mirrors),
            "zero_path": tuple(zero_path),
            "segments": tuple(segments),
            "termination": termination,
            "wall_stop": wall_stop,
            "final_direction": direction,
        }

    raise ValueError(
        "could not construct a non-crossing route: "
        f"{h=} {w=} {edge=} {n_hit_mirrors=} {termination=} {required_kinds=}"
    )


def _available_interior_cells(
    h: int, w: int, forbidden: set[tuple[int, int]]
) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if (r, c) not in forbidden
    ]


def _choice_with_default(ctx, overrides: dict[str, Any], label: str, all_values, defaults):
    return ctx.draw_choice(label, all_values if label in overrides else defaults)


def _int_with_default(
    ctx,
    overrides: dict[str, Any],
    label: str,
    valid: tuple[int, int],
    default: tuple[int, int],
) -> int:
    return ctx.draw_int(label, *(valid if label in overrides else default))


def _defaults_for_role(
    role: int, difficulty: str | None
) -> tuple[tuple[str, ...], tuple[int, ...], tuple[str, ...], tuple[str, ...], tuple[int, ...]]:
    if role == 0:
        return ("top",), (3, 4, 6, 8, 9), ("one_hit_one_decoy",), ("boundary_one_decoy",), (1,)
    if role == 1:
        return ("left",), (7,), ("two_hit",), ("wall_stop",), (1, 2)
    if role == 2:
        return ("bottom",), (3, 4, 6, 8, 9), ("two_hit_one_decoy",), ("boundary_two_decoys",), (2, 1)
    if difficulty == "hard":
        return ("right",), (7, 8, 9), ("three_hit_one_decoy",), ("wall_stop_plus_decoy",), (1, 2, 1)
    return ("right",), (7, 8, 9), ("one_hit_two_decoys",), ("wall_stop_plus_decoy",), (2,)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    role = sample_index % EXAMPLES_NEEDED
    edge_defaults, color_defaults, mirror_defaults, wall_defaults, role_kinds = _defaults_for_role(
        role, difficulty
    )

    if not ({"grid_h", "grid_w"} & set(overrides)) and sample_index % 5 == 0:
        canonical_h, canonical_w = _CANONICAL_SHAPES[(sample_index // 5) % len(_CANONICAL_SHAPES)]
        h_default = (canonical_h, canonical_h)
        w_default = (canonical_w, canonical_w)
    elif difficulty == "easy":
        h_default, w_default = (8, 10), (8, 11)
    elif difficulty == "hard":
        h_default, w_default = (10, 14), (10, 15)
    else:
        h_default, w_default = (8, 12), (8, 13)

    h = _int_with_default(ctx, overrides, "grid_h", (8, 14), h_default)
    w = _int_with_default(ctx, overrides, "grid_w", (8, 15), w_default)
    source_edge = _choice_with_default(
        ctx, overrides, "source_edge", SOURCE_EDGES, edge_defaults
    )
    source_color = _choice_with_default(
        ctx, overrides, "source_color", SOURCE_COLORS, color_defaults
    )
    mirror_profile = _choice_with_default(
        ctx,
        overrides,
        "mirror_profile",
        tuple(MIRROR_PROFILES),
        mirror_defaults,
    )
    wall_profile = _choice_with_default(
        ctx,
        overrides,
        "wall_profile",
        tuple(WALL_PROFILES),
        wall_defaults,
    )

    n_hit, n_decoy_mirrors = MIRROR_PROFILES[mirror_profile]
    termination, n_walls = WALL_PROFILES[wall_profile]
    # Role-specific mirror orientation is a curriculum default, not an extra
    # hidden constraint on an explicit route-profile request.  In particular,
    # the hard role-3 wall-stop template (1, 2, 1) has no non-crossing boundary
    # realization for many seeds.  Keeping it after wall_profile is overridden
    # turns a legal exact override into a 48 x 4096 rejection search.
    required_kinds = (
        role_kinds
        if not ({"mirror_profile", "wall_profile"} & set(overrides))
        and len(role_kinds) == n_hit
        else None
    )

    last_error = "no route attempt"
    for layout_attempt in range(48):
        rng = ctx.draw_rng(f"layout:{layout_attempt}")
        try:
            route = _sample_route(
                rng,
                h=h,
                w=w,
                edge=source_edge,
                n_hit_mirrors=n_hit,
                termination=termination,
                required_kinds=required_kinds,
            )
        except ValueError as exc:
            last_error = str(exc)
            continue

        grid = full_grid(h, w, 0)
        sr, sc = route["source"]
        grid[sr][sc] = source_color
        for r, c, kind in route["mirrors"]:
            grid[r][c] = kind
        if route["wall_stop"] is not None:
            wr, wc = route["wall_stop"]
            grid[wr][wc] = 5

        forbidden = {
            route["source"],
            *route["zero_path"],
            *((r, c) for r, c, _ in route["mirrors"]),
        }
        if route["wall_stop"] is not None:
            forbidden.add(route["wall_stop"])
        available = _available_interior_cells(h, w, forbidden)
        rng.shuffle(available)
        needed_decoy_walls = n_walls - (1 if termination == "wall" else 0)
        if len(available) < n_decoy_mirrors + needed_decoy_walls:
            last_error = "not enough cells for requested decoys"
            continue

        hit_kinds = {kind for _, _, kind in route["mirrors"]}
        for index in range(n_decoy_mirrors):
            r, c = available.pop()
            if 1 not in hit_kinds:
                kind = 1
            elif 2 not in hit_kinds:
                kind = 2
            else:
                kind = rng.choice((1, 2))
            grid[r][c] = kind
            hit_kinds.add(kind)
        for _ in range(needed_decoy_walls):
            r, c = available.pop()
            grid[r][c] = 5

        analysis = _analysis(grid)
        if analysis["errors"]:
            last_error = "; ".join(analysis["errors"])
            continue
        expected = {
            "grid_h": h,
            "grid_w": w,
            "source_edge": source_edge,
            "source_color": source_color,
            "mirror_profile": mirror_profile,
            "wall_profile": wall_profile,
        }
        observed = observe_overrides(grid)
        if observed != expected:
            raise AssertionError(f"axis realization mismatch: {expected=} {observed=}")
        return grid

    raise ValueError(f"could not realize requested scene after 48 attempts: {last_error}")


def _source_edge(position: tuple[int, int], h: int, w: int) -> str | None:
    r, c = position
    if r == 0 and c not in (0, w - 1):
        return "top"
    if r == h - 1 and c not in (0, w - 1):
        return "bottom"
    if c == 0 and r not in (0, h - 1):
        return "left"
    if c == w - 1 and r not in (0, h - 1):
        return "right"
    return None


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "termination": None,
        "path": (),
        "hit_mirrors": (),
        "segments": (),
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty sequence of rows")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("grid rows must be non-empty sequences")
        return result
    h, w = len(grid), len(grid[0])
    result.update(grid_h=h, grid_w=w)
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if not 8 <= h <= 14:
        errors.append(f"grid height {h} outside 8..14")
    if not 8 <= w <= 15:
        errors.append(f"grid width {w} outside 8..15")
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool) or not isinstance(value, int) or value not in range(10)
        },
        key=repr,
    )
    if bad:
        errors.append(f"non-ARC colors: {bad}")
        return result

    sources = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] in SOURCE_COLORS
    ]
    mirrors = {
        (r, c): grid[r][c]
        for r in range(h)
        for c in range(w)
        if grid[r][c] in (1, 2)
    }
    walls = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 5
    }
    result.update(mirrors=mirrors, walls=walls)
    if len(sources) != 1:
        errors.append(f"expected exactly one source-colored cell, got {len(sources)}")
        return result
    sr, sc, source_color = sources[0]
    edge = _source_edge((sr, sc), h, w)
    result.update(source=(sr, sc), source_color=source_color, source_edge=edge)
    if edge is None:
        errors.append("source must occupy a non-corner border cell")
        return result
    if not 1 <= len(mirrors) <= 4:
        errors.append(f"expected 1..4 interior mirrors, got {len(mirrors)}")
    for r, c in mirrors:
        if r in (0, h - 1) or c in (0, w - 1):
            errors.append(f"mirror on border at {(r, c)}")
    if not 0 <= len(walls) <= 2:
        errors.append(f"expected 0..2 walls, got {len(walls)}")
    for r, c in walls:
        if r in (0, h - 1) or c in (0, w - 1):
            errors.append(f"wall on border at {(r, c)}")

    direction = _inward(edge)
    r, c = sr + direction[0], sc + direction[1]
    states: set[tuple[int, int, int, int]] = set()
    path: list[tuple[int, int]] = []
    hit: list[tuple[int, int, int]] = []
    segments: list[int] = []
    segment_length = 0
    termination = None
    for _ in range(5 * h * w + 8):
        if not (0 <= r < h and 0 <= c < w):
            termination = "boundary"
            segments.append(segment_length)
            break
        state = (r, c, direction[0], direction[1])
        if state in states:
            errors.append(f"beam repeats a directional state at {(r, c)}")
            termination = "loop"
            break
        states.add(state)
        value = grid[r][c]
        if value == 0:
            path.append((r, c))
            segment_length += 1
        elif value == 5:
            termination = "wall"
            segments.append(segment_length)
            break
        elif value in (1, 2):
            segments.append(segment_length)
            segment_length = 0
            hit.append((r, c, value))
            direction = _bounce(direction, value)
        else:
            errors.append(f"beam encounters unexpected color {value} at {(r, c)}")
            termination = "invalid"
            break
        r += direction[0]
        c += direction[1]
    else:
        errors.append("beam exceeded fuel bound")
        termination = "fuel"

    if not hit:
        errors.append("beam must reach at least one mirror")
    if segments and any(length < 1 for length in segments):
        errors.append(f"each reached segment must contain black cells; got {segments}")
    if termination not in {"wall", "boundary"}:
        errors.append(f"beam did not terminate at wall/boundary: {termination}")
    hit_positions = {(r, c) for r, c, _ in hit}
    result.update(
        termination=termination,
        path=tuple(path),
        hit_mirrors=tuple(hit),
        hit_mirror_positions=hit_positions,
        decoy_mirrors=tuple(sorted(set(mirrors) - hit_positions)),
        segments=tuple(segments),
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    palette = {value for row in grid for value in row}
    if not {1, 2, 5}.issubset(palette):
        return ["strict canonical-like scenes contain both mirror colors and at least one wall"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    n_hit = len(analysis["hit_mirrors"])
    n_decoy = len(analysis["decoy_mirrors"])
    mirror_profile = next(
        name for name, counts in MIRROR_PROFILES.items() if counts == (n_hit, n_decoy)
    )
    wall_counts = len(analysis["walls"])
    wall_profile = next(
        name
        for name, values in WALL_PROFILES.items()
        if values == (analysis["termination"], wall_counts)
    )
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "source_edge": analysis["source_edge"],
        "source_color": analysis["source_color"],
        "mirror_profile": mirror_profile,
        "wall_profile": wall_profile,
    }


def _apply_beam(
    grid,
    *,
    paint_color: int | None = None,
    mirror_mode: str = "normal",
    walls_stop: bool = True,
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid laser scene: " + "; ".join(analysis["errors"]))
    h, w = analysis["grid_h"], analysis["grid_w"]
    sr, sc = analysis["source"]
    direction = _inward(analysis["source_edge"])
    color = analysis["source_color"] if paint_color is None else paint_color
    out = deepcopy(grid)
    r, c = sr + direction[0], sc + direction[1]
    states: set[tuple[int, int, int, int]] = set()
    for _ in range(5 * h * w + 8):
        if not (0 <= r < h and 0 <= c < w):
            break
        state = (r, c, direction[0], direction[1])
        if state in states:
            break
        states.add(state)
        value = grid[r][c]
        if value == 0:
            out[r][c] = color
        elif value == 5:
            if walls_stop:
                break
        elif value in (1, 2):
            kind = value
            if mirror_mode == "all_slash":
                kind = 1
            elif mirror_mode == "all_backslash":
                kind = 2
            elif mirror_mode == "ignore":
                kind = 0
            if kind:
                direction = _bounce(direction, kind)
        else:
            break
        r += direction[0]
        c += direction[1]
    return out


def rule_mirror(grid) -> list[list[int]]:
    return _apply_beam(grid)


def _rival_constant_seven(grid):
    return _apply_beam(grid, paint_color=7)


def _rival_ignore_mirrors(grid):
    return _apply_beam(grid, mirror_mode="ignore")


def _rival_all_slash(grid):
    return _apply_beam(grid, mirror_mode="all_slash")


def _rival_all_backslash(grid):
    return _apply_beam(grid, mirror_mode="all_backslash")


def _rival_ignore_walls(grid):
    return _apply_beam(grid, walls_stop=False)


LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "constant_trail_color_7": _rival_constant_seven,
    "ignore_mirrors": _rival_ignore_mirrors,
    "treat_both_mirrors_as_slash": _rival_all_slash,
    "treat_both_mirrors_as_backslash": _rival_all_backslash,
    "ignore_walls": _rival_ignore_walls,
}
SEMANTIC_RIVALS = LESSON_COMPETITORS
CANONICAL_SHORTCUTS = {
    "constant_trail_color_7": _rival_constant_seven,
}


def _rival_differs(name: str, grid) -> bool:
    if self_check(grid):
        return False
    return LESSON_COMPETITORS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "non_7_source_refutes_constant_color": lambda grid: (
        not self_check(grid)
        and _analysis(grid)["source_color"] != 7
        and _rival_differs("constant_trail_color_7", grid)
    ),
    "reached_mirror_changes_route": lambda grid: _rival_differs("ignore_mirrors", grid),
    "slash_backslash_contrast": lambda grid: (
        not self_check(grid)
        and {kind for _, _, kind in _analysis(grid)["hit_mirrors"]} == {1, 2}
        and _rival_differs("treat_both_mirrors_as_slash", grid)
        and _rival_differs("treat_both_mirrors_as_backslash", grid)
    ),
    "wall_stop_has_visible_consequence": lambda grid: (
        not self_check(grid)
        and _analysis(grid)["termination"] == "wall"
        and _rival_differs("ignore_walls", grid)
    ),
}

WITNESS_RIVALS = {
    "non_7_source_refutes_constant_color": ["constant_trail_color_7"],
    "reached_mirror_changes_route": ["ignore_mirrors"],
    "slash_backslash_contrast": [
        "treat_both_mirrors_as_slash",
        "treat_both_mirrors_as_backslash",
    ],
    "wall_stop_has_visible_consequence": ["ignore_walls"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} must be a pair dict")
            continue
        errors = self_check(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} invalid: {'; '.join(errors)}")
        elif pair.get("output") != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with intended beam rule")
    if not isinstance(query, dict):
        return reasons + ["query must be a pair dict"]
    query_errors = self_check(query.get("input"))
    if query_errors:
        return reasons + ["query invalid: " + "; ".join(query_errors)]
    intended_query = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != intended_query:
        reasons.append("query output disagrees with intended beam rule")

    survivors = []
    divergent = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        except Exception:
            fits = False
        if not fits:
            continue
        survivors.append(name)
        if competitor(query["input"]) != intended_query:
            divergent.append(name)
    if survivors:
        detail = ", ".join(sorted(survivors))
        if divergent:
            reasons.append("demos leave query-divergent rival(s): " + detail)
        else:
            reasons.append("demos fail to refute rival(s): " + detail)
    return reasons
