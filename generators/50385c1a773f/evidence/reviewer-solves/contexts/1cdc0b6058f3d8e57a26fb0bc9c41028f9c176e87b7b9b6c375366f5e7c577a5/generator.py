"""Semantic generator for ARC task 50385c1a773f (mirror-traced beam).

A red source emits a beam to the right. Green slash mirrors and yellow
backslash mirrors turn the beam; gray cells stop it, otherwise it may leave the
canvas. Every traversed black cell becomes cyan in the output.

The public examples establish two semantically important termination branches:
four demonstrations stop at a gray wall, while the held-out example leaves the
left edge after two reflections and contains an unused gray distractor. This
generator preserves both branches and procedurally mixes exact public-profile
morphology with broader, still unambiguous ray layouts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "50385c1a773f"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "326ba9cc3a3b"

SUMMARY = (
    "A single red (2) source launches a beam to the right through black (0) "
    "cells. A green (3) slash mirror maps (dr,dc) to (-dc,-dr), while a "
    "yellow (4) backslash mirror maps it to (dc,dr). The beam stops at the "
    "first gray (5) cell or when it leaves the grid; every traversed black "
    "cell is painted cyan (8). All mirrors lie on the traced route. One or "
    "two straight gray wall components may be present, including an unused "
    "distractor wall on the boundary-exit branch demonstrated by the public "
    "test example."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "rectangular 8..16 by 9..16 input over colors {0,2,3,4,5}",
    "exactly one source (2) in the left third of the grid",
    "1..3 mirrors (3/4), every one reached by the source-launched beam",
    "every source/mirror/termination segment contains at least two black cells",
    "the beam terminates at a gray wall or the grid boundary without looping",
    "1..2 gray 4-connected components, each a straight contiguous segment",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "35% linked public profile; otherwise difficulty-aware",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "35% linked public profile; otherwise difficulty-aware",
        "valid": "9..16",
    },
    "n_deflectors": {
        "type": "int",
        "default": "linked public profile or difficulty-aware 1..3",
        "valid": "1..3",
    },
    "termination": {
        "type": "str",
        "default": "wall or boundary",
        "valid": "wall|boundary",
    },
    "n_wall_components": {
        "type": "int",
        "default": "1..2; boundary exits retain at least one distractor wall",
        "valid": "1..2",
    },
}

_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_RIGHT = (0, 1)


@dataclass(frozen=True)
class _PublicProfile:
    grid_h: int
    grid_w: int
    mirror_kinds: tuple[int, ...]
    termination: str
    wall_specs: tuple[tuple[int, str], ...]

    @property
    def n_deflectors(self) -> int:
        return len(self.mirror_kinds)

    @property
    def n_wall_components(self) -> int:
        return len(self.wall_specs)


# Linked tuples and coarse wall morphology from all four train inputs and the
# held-out input. Coordinates are never copied; every returned scene is newly
# constructed from the linked profile.
_PUBLIC_PROFILES = (
    _PublicProfile(8, 10, (3,), "wall", ((1, "primary"), (4, "h"))),
    _PublicProfile(9, 11, (4, 3), "wall", ((3, "primary"),)),
    _PublicProfile(10, 12, (3, 4), "wall", ((1, "primary"),)),
    _PublicProfile(9, 10, (4,), "wall", ((3, "primary"),)),
    _PublicProfile(10, 12, (3, 4), "boundary", ((1, "single"),)),
)

# Only hashes are retained: linked public morphology is useful, exact public
# coordinate copies are not.  A deterministic nuisance-layout retry rejects
# the five official inputs without embedding or returning their grids.
_CANONICAL_INPUT_HASHES = frozenset({
    "0abc9a226541efaff73b905329a24c8fa22758df620c09cac78590720c3f28cd",
    "3400bd8b2c55a438f339efa20634b30e10bf187a23612548f5928800b0d01907",
    "c06e9f0d881adbdddc4675e3bc656e87bb27214adaee33f86f2311df4c38429c",
    "8ec8139bac1580726cc6e22510b167616ae03f0f04d13b9e7a34c9f5a0ac479b",
    "3f8f586620e7e8151515c8773f09c4ab74e7ab9248a041fffdf1e4cdc43a322e",
})


def _grid_fingerprint(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class _Route:
    source: tuple[int, int]
    mirrors: tuple[tuple[int, int, int], ...]
    zero_path: tuple[tuple[int, int], ...]
    segments: tuple[int, ...]
    final_direction: tuple[int, int]
    wall_stop: tuple[int, int] | None
    final_capacity: int


def _bounce(direction: tuple[int, int], kind: int) -> tuple[int, int]:
    dr, dc = direction
    if kind == 3:
        return -dc, -dr
    if kind == 4:
        return dc, dr
    raise ValueError(f"unknown mirror color: {kind}")


def _mirror_kind(
    incoming: tuple[int, int], outgoing: tuple[int, int]
) -> int | None:
    for kind in (3, 4):
        if _bounce(incoming, kind) == outgoing:
            return kind
    return None


def _step_cells(
    start: tuple[int, int], end: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    """Interior cells of one horizontal/vertical segment."""
    sr, sc = start
    er, ec = end
    if sr == er:
        dc = 1 if ec > sc else -1
        return tuple((sr, c) for c in range(sc + dc, ec, dc))
    if sc == ec:
        dr = 1 if er > sr else -1
        return tuple((r, sc) for r in range(sr + dr, er, dr))
    raise ValueError("route segment must be axis-aligned")


def _distance_to_edge(
    h: int, w: int, pos: tuple[int, int], direction: tuple[int, int]
) -> int:
    r, c = pos
    dr, dc = direction
    if dr < 0:
        return r
    if dr > 0:
        return h - 1 - r
    if dc < 0:
        return c
    return w - 1 - c


def _build_route(
    *,
    h: int,
    w: int,
    source: tuple[int, int],
    mirror_positions: tuple[tuple[int, int], ...],
    final_direction: tuple[int, int],
    termination: str,
    wall_distance: int | None,
    primary_wall_length: int,
    segment_max: int | None,
) -> _Route | None:
    points = (source,) + mirror_positions
    zero_path: list[tuple[int, int]] = []
    segments: list[int] = []
    occupied = {source, *mirror_positions}

    incoming = _RIGHT
    mirrors: list[tuple[int, int, int]] = []
    for index, (left, right) in enumerate(zip(points, points[1:])):
        cells = _step_cells(left, right)
        if len(cells) < 2 or (segment_max is not None and len(cells) > segment_max):
            return None
        if any(cell in occupied or cell in zero_path for cell in cells):
            return None
        zero_path.extend(cells)
        segments.append(len(cells))
        segment_direction = (
            0 if right[0] == left[0] else (1 if right[0] > left[0] else -1),
            0 if right[1] == left[1] else (1 if right[1] > left[1] else -1),
        )
        if segment_direction != incoming:
            return None
        if index + 1 < len(mirror_positions):
            nxt = mirror_positions[index + 1]
            outgoing = (
                0 if nxt[0] == right[0] else (1 if nxt[0] > right[0] else -1),
                0 if nxt[1] == right[1] else (1 if nxt[1] > right[1] else -1),
            )
        else:
            outgoing = final_direction
        kind = _mirror_kind(incoming, outgoing)
        if kind is None:
            return None
        mirrors.append((right[0], right[1], kind))
        incoming = outgoing

    last = mirror_positions[-1]
    capacity = _distance_to_edge(h, w, last, final_direction)
    if termination == "boundary":
        if capacity < 2:
            return None
        final_cells = tuple(
            (last[0] + final_direction[0] * step,
             last[1] + final_direction[1] * step)
            for step in range(1, capacity + 1)
        )
        wall_stop = None
    else:
        if wall_distance is None or wall_distance < 3:
            return None
        if wall_distance + primary_wall_length - 1 > capacity:
            return None
        final_cells = tuple(
            (last[0] + final_direction[0] * step,
             last[1] + final_direction[1] * step)
            for step in range(1, wall_distance)
        )
        wall_stop = (
            last[0] + final_direction[0] * wall_distance,
            last[1] + final_direction[1] * wall_distance,
        )
        planned_wall = tuple(
            (
                wall_stop[0] + final_direction[0] * offset,
                wall_stop[1] + final_direction[1] * offset,
            )
            for offset in range(primary_wall_length)
        )
        if any(cell in occupied or cell in zero_path or cell in final_cells for cell in planned_wall):
            return None
    if len(final_cells) < 2 or (
        segment_max is not None and len(final_cells) > segment_max
    ):
        return None
    if any(cell in occupied or cell in zero_path for cell in final_cells):
        return None
    if wall_stop is not None and (wall_stop in occupied or wall_stop in zero_path):
        return None
    zero_path.extend(final_cells)
    segments.append(len(final_cells))
    return _Route(
        source=source,
        mirrors=tuple(mirrors),
        zero_path=tuple(zero_path),
        segments=tuple(segments),
        final_direction=final_direction,
        wall_stop=wall_stop,
        final_capacity=capacity,
    )


def _sample_route(
    rng,
    *,
    h: int,
    w: int,
    n_deflectors: int,
    termination: str,
    source_col: int | None = None,
    mirror_kinds: tuple[int, ...] | None = None,
    primary_wall_length: int = 1,
    segment_max: int | None = None,
) -> _Route:
    """Sample only nuisance geometry; semantic axes are fixed by the caller."""
    for _ in range(2048):
        c0 = source_col
        if c0 is None:
            c0 = rng.randint(0, min(3, w // 3))
        if not 0 <= c0 <= w - 4:
            continue
        r0 = rng.randrange(h)
        c1_choices = [c for c in range(c0 + 3, w)]
        if segment_max is not None:
            c1_choices = [c for c in c1_choices if c - c0 - 1 <= segment_max]
        if not c1_choices:
            continue
        c1 = rng.choice(c1_choices)
        source = (r0, c0)
        m1 = (r0, c1)

        mirror_positions: tuple[tuple[int, int], ...]
        final_options: list[tuple[int, int]]
        if n_deflectors == 1:
            mirror_positions = (m1,)
            final_options = [(-1, 0), (1, 0)]
        else:
            r1_choices = [r for r in range(h) if abs(r - r0) >= 3]
            if segment_max is not None:
                r1_choices = [r for r in r1_choices if abs(r - r0) - 1 <= segment_max]
            if not r1_choices:
                continue
            r1 = rng.choice(r1_choices)
            m2 = (r1, c1)
            if n_deflectors == 2:
                mirror_positions = (m1, m2)
                final_options = [(0, -1), (0, 1)]
            else:
                c2_choices = [c for c in range(w) if abs(c - c1) >= 3]
                if segment_max is not None:
                    c2_choices = [
                        c for c in c2_choices
                        if abs(c - c1) - 1 <= segment_max
                    ]
                if not c2_choices:
                    continue
                c2 = rng.choice(c2_choices)
                mirror_positions = (m1, m2, (r1, c2))
                final_options = [(-1, 0), (1, 0)]

        rng.shuffle(final_options)
        for final_direction in final_options:
            last = mirror_positions[-1]
            capacity = _distance_to_edge(h, w, last, final_direction)
            if termination == "boundary":
                wall_distances: Iterable[int | None] = (None,)
            else:
                max_stop = capacity - primary_wall_length + 1
                if max_stop < 3:
                    continue
                choices = list(range(3, max_stop + 1))
                rng.shuffle(choices)
                wall_distances = choices
            for wall_distance in wall_distances:
                route = _build_route(
                    h=h,
                    w=w,
                    source=source,
                    mirror_positions=mirror_positions,
                    final_direction=final_direction,
                    termination=termination,
                    wall_distance=wall_distance,
                    primary_wall_length=primary_wall_length,
                    segment_max=segment_max,
                )
                if route is None:
                    continue
                kinds = tuple(kind for _, _, kind in route.mirrors)
                if mirror_kinds is not None and kinds != mirror_kinds:
                    continue
                return route
    raise ValueError(
        "could not realize requested ray geometry: "
        f"{h=} {w=} {n_deflectors=} {termination=} "
        f"{mirror_kinds=} {primary_wall_length=}"
    )


def _wall_components(grid) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for dr, dc in _DIRECTIONS:
                    nxt = cell[0] + dr, cell[1] + dc
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == 5
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            rows = {cell[0] for cell in cells}
            cols = {cell[1] for cell in cells}
            if len(cells) == 1:
                orientation = "single"
                straight = True
            elif len(rows) == 1:
                orientation = "h"
                straight = max(cols) - min(cols) + 1 == len(cells)
            elif len(cols) == 1:
                orientation = "v"
                straight = max(rows) - min(rows) + 1 == len(cells)
            else:
                orientation = "other"
                straight = False
            components.append({
                "cells": tuple(sorted(cells)),
                "length": len(cells),
                "orientation": orientation,
                "straight": straight,
            })
    return components


def _analysis(grid) -> dict:
    errors: list[str] = []
    result = {
        "errors": errors,
        "termination": None,
        "n_deflectors": 0,
        "n_wall_components": 0,
        "segments": (),
        "path": (),
        "mirror_kinds": (),
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
    if not 8 <= h <= 16:
        errors.append(f"grid height {h} outside 8..16")
    if not 9 <= w <= 16:
        errors.append(f"grid width {w} outside 9..16")
    bad = sorted({
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int)
        or value not in {0, 2, 3, 4, 5}
    }, key=repr)
    if bad:
        errors.append(f"colors outside {{0,2,3,4,5}}: {bad}")
        return result

    sources = [
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 2
    ]
    mirrors = {
        (r, c): grid[r][c]
        for r in range(h)
        for c in range(w)
        if grid[r][c] in (3, 4)
    }
    walls = _wall_components(grid)
    result.update(
        n_deflectors=len(mirrors),
        n_wall_components=len(walls),
        wall_components=walls,
    )
    if len(sources) != 1:
        errors.append(f"expected exactly one source (2), got {len(sources)}")
        return result
    source = sources[0]
    result["source"] = source
    if source[1] > w // 3:
        errors.append(
            f"source column {source[1]} is outside the intended left third"
        )
    if not 1 <= len(mirrors) <= 3:
        errors.append(f"expected 1..3 mirrors, got {len(mirrors)}")
    if not 1 <= len(walls) <= 2:
        errors.append(f"expected 1..2 gray wall components, got {len(walls)}")
    for component in walls:
        if not component["straight"]:
            errors.append(
                "gray wall component is not a straight contiguous segment: "
                f"{component['cells']}"
            )
        if not 1 <= component["length"] <= 4:
            errors.append(
                f"gray wall length {component['length']} outside 1..4"
            )

    r, c = source[0], source[1] + 1
    direction = _RIGHT
    states: set[tuple[int, int, int, int]] = set()
    visited_cells: set[tuple[int, int]] = set()
    path: list[tuple[int, int]] = []
    hit: list[tuple[int, int, int]] = []
    segments: list[int] = []
    segment_length = 0
    termination = None
    for _ in range(h * w * 4 + 8):
        if not (0 <= r < h and 0 <= c < w):
            termination = "boundary"
            segments.append(segment_length)
            break
        state = (r, c, direction[0], direction[1])
        if state in states or (r, c) in visited_cells:
            errors.append(f"beam revisits ({r},{c}); looping/crossing lessons are excluded")
            termination = "loop"
            break
        states.add(state)
        visited_cells.add((r, c))
        value = grid[r][c]
        if value == 5:
            termination = "wall"
            segments.append(segment_length)
            break
        if value == 0:
            path.append((r, c))
            segment_length += 1
        elif value in (3, 4):
            segments.append(segment_length)
            segment_length = 0
            hit.append((r, c, value))
            direction = _bounce(direction, value)
        else:
            errors.append(f"beam encounters source color again at ({r},{c})")
            termination = "invalid"
            break
        r += direction[0]
        c += direction[1]
    else:
        errors.append("beam exceeded structural fuel bound")
        termination = "fuel"

    hit_positions = {(r, c) for r, c, _ in hit}
    missing = sorted(set(mirrors) - hit_positions)
    if missing:
        errors.append(f"{len(missing)} mirror(s) are not on the traced beam: {missing}")
    if termination not in {"wall", "boundary"}:
        errors.append(f"beam did not terminate at a wall or boundary: {termination}")
    if not path:
        errors.append("beam traverses no black cells, so the transform is a no-op")
    if segments and any(length < 2 for length in segments):
        errors.append(
            "every source/mirror/termination segment must contain at least two "
            f"black cells; got {segments}"
        )

    result.update(
        termination=termination,
        segments=tuple(segments),
        path=tuple(path),
        hit_mirrors=tuple(hit),
        mirror_kinds=tuple(kind for _, _, kind in hit),
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, route-aware input validation; accepts all five public inputs."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_deflectors": analysis["n_deflectors"],
        "termination": analysis["termination"],
        "n_wall_components": analysis["n_wall_components"],
    }


def _draw_banded_int(
    ctx,
    overrides: dict,
    label: str,
    default_lo: int,
    default_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _difficulty_ranges(difficulty: str | None) -> tuple[tuple[int, int], ...]:
    if difficulty == "easy":
        return (8, 10), (9, 12), (1, 2)
    if difficulty == "medium":
        return (9, 13), (10, 14), (1, 2)
    if difficulty == "hard":
        return (11, 16), (12, 16), (2, 3)
    return (8, 16), (9, 16), (1, 3)


def _segment_options(
    h: int,
    w: int,
    *,
    length: int,
    orientation: str,
    forbidden: set[tuple[int, int]],
    existing_walls: set[tuple[int, int]],
) -> list[tuple[tuple[int, int], ...]]:
    orientations = ("h", "v") if orientation in {"any", "single"} else (orientation,)
    if length == 1:
        orientations = ("h",)
    out: list[tuple[tuple[int, int], ...]] = []
    for orient in orientations:
        row_starts = range(h) if orient == "h" else range(h - length + 1)
        col_starts = range(w - length + 1) if orient == "h" else range(w)
        for r in row_starts:
            for c in col_starts:
                cells = tuple(
                    (r, c + i) if orient == "h" else (r + i, c)
                    for i in range(length)
                )
                if any(cell in forbidden or cell in existing_walls for cell in cells):
                    continue
                cell_set = set(cells)
                touches = False
                for rr, cc in cells:
                    for dr, dc in _DIRECTIONS:
                        neighbor = rr + dr, cc + dc
                        if neighbor in existing_walls and neighbor not in cell_set:
                            touches = True
                            break
                    if touches:
                        break
                if not touches:
                    out.append(cells)
    return out


def _add_decoy_wall(
    grid,
    rng,
    *,
    forbidden: set[tuple[int, int]],
    existing_walls: set[tuple[int, int]],
    requested: tuple[int, str] | None,
) -> None:
    h, w = len(grid), len(grid[0])
    specs: list[tuple[int, str]]
    if requested is not None:
        length, orientation = requested
        specs = [(length, "any" if orientation == "single" else orientation)]
    else:
        specs = [
            (length, orientation)
            for length in (1, 2, 3, 4)
            for orientation in ("h", "v")
        ]
        rng.shuffle(specs)
    choices: list[tuple[tuple[int, int], ...]] = []
    for length, orientation in specs:
        choices.extend(_segment_options(
            h,
            w,
            length=length,
            orientation=orientation,
            forbidden=forbidden,
            existing_walls=existing_walls,
        ))
        if choices and requested is None:
            break
    if not choices:
        raise ValueError(f"could not place disconnected decoy wall {requested!r}")
    cells = rng.choice(choices)
    for r, c in cells:
        grid[r][c] = 5
    existing_walls.update(cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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

    profile: _PublicProfile | None = None
    if not overrides and ctx.draw_rng("public_profile_prior").random() < 0.35:
        profile = ctx.draw_rng("public_profile_choice").choice(_PUBLIC_PROFILES)

    if profile is not None:
        h = ctx.draw_int("grid_h", profile.grid_h, profile.grid_h)
        w = ctx.draw_int("grid_w", profile.grid_w, profile.grid_w)
        n_deflectors = ctx.draw_int(
            "n_deflectors", profile.n_deflectors, profile.n_deflectors
        )
        termination = ctx.draw_choice("termination", (profile.termination,))
        n_wall_components = ctx.draw_int(
            "n_wall_components",
            profile.n_wall_components,
            profile.n_wall_components,
        )
        mirror_kinds = profile.mirror_kinds
        source_col = 1
        primary_wall_length = (
            profile.wall_specs[0][0] if termination == "wall" else 1
        )
        segment_max = 7
    else:
        h_range, w_range, mirror_range = _difficulty_ranges(difficulty)
        h = _draw_banded_int(ctx, overrides, "grid_h", *h_range, 8, 16)
        w = _draw_banded_int(ctx, overrides, "grid_w", *w_range, 9, 16)
        n_deflectors = _draw_banded_int(
            ctx, overrides, "n_deflectors", *mirror_range, 1, 3
        )
        termination = ctx.draw_choice("termination", ("wall", "boundary"))
        n_wall_components = ctx.draw_int("n_wall_components", 1, 2)
        mirror_kinds = None
        source_col = None
        primary_wall_length = 1
        segment_max = None

    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_deflectors": n_deflectors,
        "termination": termination,
        "n_wall_components": n_wall_components,
    }
    last_retry_reason = "no layout attempt completed"
    for layout_attempt in range(32):
        rng = ctx.draw_rng(f"layout:{layout_attempt}")
        attempt_primary_wall_length = primary_wall_length
        try:
            route = _sample_route(
                rng,
                h=h,
                w=w,
                n_deflectors=n_deflectors,
                termination=termination,
                source_col=source_col,
                mirror_kinds=mirror_kinds,
                primary_wall_length=attempt_primary_wall_length,
                segment_max=segment_max,
            )

            grid = full_grid(h, w, 0)
            grid[route.source[0]][route.source[1]] = 2
            for r, c, kind in route.mirrors:
                grid[r][c] = kind

            existing_walls: set[tuple[int, int]] = set()
            if termination == "wall":
                assert route.wall_stop is not None
                if profile is None:
                    occupied_route = {
                        route.source,
                        *route.zero_path,
                        *((r, c) for r, c, _ in route.mirrors),
                    }
                    max_length = 0
                    for offset in range(4):
                        cell = (
                            route.wall_stop[0] + route.final_direction[0] * offset,
                            route.wall_stop[1] + route.final_direction[1] * offset,
                        )
                        if not (0 <= cell[0] < h and 0 <= cell[1] < w):
                            break
                        if cell in occupied_route:
                            break
                        max_length += 1
                    attempt_primary_wall_length = rng.randint(1, max_length)
                for offset in range(attempt_primary_wall_length):
                    cell = (
                        route.wall_stop[0] + route.final_direction[0] * offset,
                        route.wall_stop[1] + route.final_direction[1] * offset,
                    )
                    grid[cell[0]][cell[1]] = 5
                    existing_walls.add(cell)

            forbidden = {
                route.source,
                *route.zero_path,
                *((r, c) for r, c, _ in route.mirrors),
            }
            extra_components = n_wall_components - (
                1 if termination == "wall" else 0
            )
            requested_decoys: list[tuple[int, str] | None] = []
            if profile is not None:
                start = 1 if termination == "wall" else 0
                requested_decoys.extend(profile.wall_specs[start:])
            requested_decoys.extend(
                [None] * (extra_components - len(requested_decoys))
            )
            for requested in requested_decoys:
                _add_decoy_wall(
                    grid,
                    rng,
                    forbidden=forbidden,
                    existing_walls=existing_walls,
                    requested=requested,
                )
        except ValueError as exc:
            last_retry_reason = f"layout {layout_attempt}: {exc}"
            continue

        analysis = _analysis(grid)
        if analysis["errors"]:
            raise AssertionError(
                "constructed invalid scene: " + "; ".join(analysis["errors"])
            )
        observed = observe_overrides(grid)
        if observed != expected:
            raise AssertionError(
                f"axis realization mismatch: {expected=} {observed=}"
            )
        if _grid_fingerprint(grid) in _CANONICAL_INPUT_HASHES:
            last_retry_reason = (
                f"layout {layout_attempt}: exact canonical input fingerprint"
            )
            continue
        return grid

    raise ValueError(
        "could not construct a non-canonical exact-copy scene after 32 "
        f"deterministic layout attempts ({last_retry_reason})"
    )


def _distance_along(start: tuple[int, int], end: tuple[int, int]) -> int:
    return abs(end[0] - start[0]) + abs(end[1] - start[1])
