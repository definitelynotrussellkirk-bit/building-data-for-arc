"""Generator for canonical family 696d4842 / task 76b818438a96.

Each input contains two one-cell-wide, non-branching orthogonal paths and two
singleton markers.  Exactly one endpoint of each path points through a clear
zero corridor to one marker.  The selected Racket authority extends that path
up to (but not over) the marker, then recolors the same number of original path
cells starting at the opposite endpoint with the marker color.

Canonical paths are *not* restricted to L shapes: the supplied examples contain
one, two, and three turns.  This sampler deliberately covers that topology and
also includes a short-marker branch that refutes a canonical-fitting
"far markers only" shortcut.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76b818438a96"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "000a1e2b0988"
SUMMARY = (
    "Two colored non-branching orthogonal paths (1..3 turns) and two aligned "
    "singleton markers. Extend each path toward its marker and recolor the "
    "same number of cells from the opposite endpoint in the marker color."
)

INVARIANTS = [
    "background is 0 and the four foreground objects use four distinct colors",
    "exactly two connected paths; each is one cell wide, non-branching, has two endpoints, and bends at least once",
    "exactly two singleton markers; each is uniquely aligned beyond one path endpoint through a clear corridor",
    "one marker distance is 2..3 and the other is 4..7, so every generated lesson contains the near-marker witness",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
# Legacy palette names are retained, but each now maps to a distinct exact set
# so observe_overrides can recover the requested value from returned pixels.
_PALETTES = {
    "warm": (3, 4, 6, 8),       # canonical train/test support
    "cool": (1, 2, 4, 6),       # canonical train support
    "primary": (2, 3, 4, 6),    # canonical test support
    "broad": (1, 5, 7, 9),      # held-out color support
}
_PALETTE_BY_SET = {frozenset(colors): name for name, colors in _PALETTES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 20/30 schedule plus band-weighted 14..30 support",
        "valid": "14..30",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 20/30 schedule plus band-weighted 14..30 support",
        "valid": "14..30",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed canonical-biased exact palette",
        "valid": "|".join(PALETTE_KINDS),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[Any] = []

_CANONICAL_DIMS = (20, 30)
_CANONICAL_PATH_SIZES = (7, 8, 12, 13, 16)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTIES or (
        difficulty is not None and type(difficulty) is not str
    ):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not 14 <= value <= 30:
            raise ValueError(f"{name}={value} outside [14, 30]")
    palette = overrides.get("palette_kind")
    if palette is not None:
        if type(palette) is not str:
            raise TypeError(
                f"palette_kind must be a string, not {type(palette).__name__}"
            )
        if palette not in PALETTE_KINDS:
            raise ValueError(
                f"unknown palette_kind {palette!r}; valid: {PALETTE_KINDS}"
            )


def _components(grid):
    """Same-color cardinal components, matching ARC object semantics."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                point = stack.pop()
                cells.add(point)
                for dr, dc in _DIRS4:
                    nxt = point[0] + dr, point[1] + dc
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append({"color": color, "cells": cells})
    return result


def _path_signature(cells):
    """Return ordered simple-path geometry, or None.

    A valid object is a cardinal graph path: every vertex has degree 1 or 2,
    exactly two endpoints exist, all cells lie on the endpoint walk, and at
    least one direction change occurs.  This accepts the canonical multi-turn
    paths while rejecting branches, loops, solid blocks, and straight bars.
    """
    if len(cells) < 3:
        return None
    degrees = {
        point: sum((point[0] + dr, point[1] + dc) in cells for dr, dc in _DIRS4)
        for point in cells
    }
    if any(degree not in (1, 2) for degree in degrees.values()):
        return None
    endpoints = tuple(sorted(point for point, degree in degrees.items() if degree == 1))
    if len(endpoints) != 2:
        return None
    order = []
    previous = None
    current = endpoints[0]
    while current is not None:
        order.append(current)
        choices = [
            (current[0] + dr, current[1] + dc)
            for dr, dc in _DIRS4
            if (current[0] + dr, current[1] + dc) in cells
            and (current[0] + dr, current[1] + dc) != previous
        ]
        if len(choices) > 1:
            return None
        nxt = choices[0] if choices else None
        previous, current = current, nxt
    if len(order) != len(cells) or order[-1] != endpoints[1]:
        return None
    directions = [
        (right[0] - left[0], right[1] - left[1])
        for left, right in zip(order, order[1:])
    ]
    turn_count = sum(left != right for left, right in zip(directions, directions[1:]))
    if turn_count < 1:
        return None
    segment_lengths = []
    run = 1
    for left, right in zip(directions, directions[1:]):
        if left == right:
            run += 1
        else:
            segment_lengths.append(run)
            run = 1
    segment_lengths.append(run)
    return {
        "cells": cells,
        "endpoints": endpoints,
        "order": tuple(order),
        "turn_count": turn_count,
        "segment_lengths": tuple(segment_lengths),
    }


def _outward(path, endpoint):
    order = path["order"]
    if endpoint == order[0]:
        neighbor = order[1]
    elif endpoint == order[-1]:
        neighbor = order[-2]
    else:
        raise ValueError("point is not a path endpoint")
    return endpoint[0] - neighbor[0], endpoint[1] - neighbor[1]


def _scene_info(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("cells must be integer colors in 0..9")
    height = len(grid)
    if not (14 <= height <= 30 and 14 <= width <= 30):
        raise ValueError(
            f"dims {height}x{width} outside the declared 14..30 envelope"
        )

    components = _components(grid)
    paths = []
    markers = []
    for component in components:
        if len(component["cells"]) == 1:
            markers.append(
                {
                    "color": component["color"],
                    "point": next(iter(component["cells"])),
                }
            )
            continue
        signature = _path_signature(component["cells"])
        if signature is None:
            raise ValueError(
                f"component of {len(component['cells'])} cells is not a bent simple path"
            )
        paths.append({"color": component["color"], **signature})
    if len(paths) != 2 or len(markers) != 2:
        raise ValueError(
            f"expected exactly two paths and two singleton markers, found "
            f"{len(paths)} and {len(markers)}"
        )
    if len({component["color"] for component in components}) != 4:
        raise ValueError("the four foreground objects must use four distinct colors")

    links = []
    used_markers: set[tuple[int, int]] = set()
    for path in paths:
        candidates = []
        for endpoint in path["endpoints"]:
            dr, dc = _outward(path, endpoint)
            for marker in markers:
                mr, mc = marker["point"]
                delta_r, delta_c = mr - endpoint[0], mc - endpoint[1]
                if dr and (delta_c != 0 or delta_r * dr <= 0):
                    continue
                if dc and (delta_r != 0 or delta_c * dc <= 0):
                    continue
                distance = abs(delta_r) + abs(delta_c)
                corridor = [
                    (endpoint[0] + dr * step, endpoint[1] + dc * step)
                    for step in range(1, distance)
                ]
                if all(grid[r][c] == 0 for r, c in corridor):
                    candidates.append((endpoint, (dr, dc), marker, distance))
        if len(candidates) != 1:
            raise ValueError(
                f"path color {path['color']} has {len(candidates)} clear aligned markers"
            )
        endpoint, direction, marker, distance = candidates[0]
        if distance < 2:
            raise ValueError(
                f"path color {path['color']} has an adjacent marker and no nonempty extension"
            )
        if marker["point"] in used_markers:
            raise ValueError("one marker is aligned to both paths")
        used_markers.add(marker["point"])
        other_endpoint = next(
            point for point in path["endpoints"] if point != endpoint
        )
        links.append(
            {
                "path": path,
                "marker": marker,
                "aligned_endpoint": endpoint,
                "other_endpoint": other_endpoint,
                "direction": direction,
                "distance": distance,
                "extension_count": distance - 1,
            }
        )
    if len(used_markers) != 2:
        raise ValueError("not every marker is used exactly once")
    return {
        "height": height,
        "width": width,
        "paths": paths,
        "markers": markers,
        "links": links,
        "colors": frozenset(component["color"] for component in components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        _scene_info(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    """Recover declared controls and exact realized topology from pixels."""
    scene = _scene_info(grid)
    try:
        palette_kind = _PALETTE_BY_SET[scene["colors"]]
    except KeyError as exc:
        raise ValueError(f"unrecognized four-color palette {sorted(scene['colors'])}") from exc
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "palette_kind": palette_kind,
        "n_paths": len(scene["paths"]),
        "n_markers": len(scene["markers"]),
        "path_sizes": tuple(sorted(len(path["cells"]) for path in scene["paths"])),
        "turn_counts": tuple(sorted(path["turn_count"] for path in scene["paths"])),
        "marker_distances": tuple(sorted(link["distance"] for link in scene["links"])),
        "extension_counts": tuple(
            sorted(link["extension_count"] for link in scene["links"])
        ),
    }


def _draw_dimension(ctx, name, *, sample_index, difficulty):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 14, 30)
    # Four deterministic slots per 20-index window guarantee canonical profile
    # support in every standard battery band; the fourth is 30x30.
    if sample_index % 5 == 0:
        target = 30 if (sample_index // 5) % 4 == 3 else 20
        return ctx.draw_choice(name, (target,))
    domain = list(range(14, 31))
    if difficulty == "easy":
        favored = list(range(16, 23)) + [20] * 8
    elif difficulty == "hard":
        favored = list(range(23, 31)) + [30] * 5 + [20] * 2
    else:
        favored = list(range(19, 28)) + [20] * 6 + [30] * 2
    return ctx.draw_choice(name, domain + favored * 3)


def _composition(total, parts, rng):
    if total < parts:
        return None
    if parts == 1:
        return (total,)
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    points = (0, *cuts, total)
    return tuple(points[index + 1] - points[index] for index in range(parts))


def _random_polyline(rng, size, turns):
    """Return a valid relative simple path or None after one random proposal."""
    lengths = _composition(size - 1, turns + 1, rng)
    if lengths is None:
        return None
    initial = rng.choice(_DIRS4)
    directions = [initial]
    for _ in range(turns):
        dr, dc = directions[-1]
        directions.append(rng.choice(((-dc, dr), (dc, -dr))))
    cells = [(0, 0)]
    current = (0, 0)
    for direction, length in zip(directions, lengths):
        for _ in range(length):
            current = current[0] + direction[0], current[1] + direction[1]
            cells.append(current)
    if len(set(cells)) != len(cells):
        return None
    signature = _path_signature(set(cells))
    if signature is None or signature["turn_count"] != turns:
        return None
    return signature


def _placement_origins(relative_cells, height, width, rng):
    min_r = min(r for r, _ in relative_cells)
    max_r = max(r for r, _ in relative_cells)
    min_c = min(c for _, c in relative_cells)
    max_c = max(c for _, c in relative_cells)
    r_lo, r_hi = -min_r, height - max_r - 1
    c_lo, c_hi = -min_c, width - max_c - 1
    if r_lo > r_hi or c_lo > c_hi:
        return []
    origins = [(r, c) for r in range(r_lo, r_hi + 1) for c in range(c_lo, c_hi + 1)]
    rng.shuffle(origins)
    return origins


def _clear_with_halo(grid, occupied, corridor):
    height, width = len(grid), len(grid[0])
    for r, c in corridor:
        if grid[r][c] != 0:
            return False
    for r, c in occupied:
        if grid[r][c] != 0:
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0:
                    return False
    return True


def _place_pair(grid, rng, path_color, marker_color, marker_distance, difficulty):
    height, width = len(grid), len(grid[0])
    if difficulty == "easy":
        size_choices = (7, 8, 8, 12)
        turn_choices = (1, 1, 2)
    elif difficulty == "hard":
        size_choices = (12, 13, 16, 16, 8)
        turn_choices = (2, 3, 3, 1)
    else:
        size_choices = _CANONICAL_PATH_SIZES
        turn_choices = (1, 2, 3)
    # Large paths remain available on canonical-size canvases, while 14x14
    # boundary overrides avoid wasting proposals that cannot include a far ray.
    if min(height, width) < 18:
        size_choices = tuple(size for size in size_choices if size <= 13) or (7, 8)

    for _ in range(240):
        size = rng.choice(size_choices)
        possible_turns = [turn for turn in turn_choices if turn + 2 <= size]
        turns = rng.choice(possible_turns)
        path = _random_polyline(rng, size, turns)
        if path is None:
            continue
        endpoint = rng.choice(path["endpoints"])
        dr, dc = _outward(path, endpoint)
        marker = (
            endpoint[0] + dr * marker_distance,
            endpoint[1] + dc * marker_distance,
        )
        corridor = [
            (endpoint[0] + dr * step, endpoint[1] + dc * step)
            for step in range(1, marker_distance)
        ]
        relative_all = [*path["cells"], *corridor, marker]
        origins = _placement_origins(relative_all, height, width, rng)
        for r0, c0 in origins[:80]:
            path_cells = [(r0 + r, c0 + c) for r, c in sorted(path["cells"])]
            marker_cell = (r0 + marker[0], c0 + marker[1])
            corridor_cells = [(r0 + r, c0 + c) for r, c in corridor]
            occupied = [*path_cells, marker_cell]
            if not _clear_with_halo(grid, occupied, corridor_cells):
                continue
            for r, c in path_cells:
                grid[r][c] = path_color
            grid[marker_cell[0]][marker_cell[1]] = marker_color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_dimension(
        ctx, "grid_h", sample_index=sample_index, difficulty=difficulty
    )
    width = _draw_dimension(
        ctx, "grid_w", sample_index=sample_index, difficulty=difficulty
    )
    palette_kind = ctx.draw_choice(
        "palette_kind",
        ("warm", "cool", "primary", "warm", "cool", "primary", "broad"),
    )
    colors = list(_PALETTES[palette_kind])
    rng = ctx.draw_rng("layout")
    rng.shuffle(colors)

    for _ in range(120):
        grid = full_grid(height, width, 0)
        near_distance = rng.choice((2, 3))
        far_distance = rng.choice((4, 5, 6, 7))
        distances = [near_distance, far_distance]
        rng.shuffle(distances)
        if not _place_pair(
            grid, rng, colors[0], colors[1], distances[0], difficulty
        ):
            continue
        if not _place_pair(
            grid, rng, colors[2], colors[3], distances[1], difficulty
        ):
            continue
        if not self_check(grid):
            return grid
    raise ValueError(
        f"cannot place two simple paths and aligned markers on {height}x{width}"
    )


def _walk_from(path, endpoint):
    order = list(path["order"])
    if endpoint == order[0]:
        return order
    if endpoint == order[-1]:
        return list(reversed(order))
    raise ValueError("path traversal must start at an endpoint")


def _apply_reference_rule(grid, *, minimum_marker_distance=1, recolor_origin="opposite"):
    """Deterministic semantic rival/reference helper, not label authority."""
    if recolor_origin not in {"opposite", "aligned"}:
        raise ValueError("recolor_origin must be 'opposite' or 'aligned'")
    scene = _scene_info(grid)
    output = deepcopy(grid)
    for link in scene["links"]:
        if link["distance"] < minimum_marker_distance:
            continue
        dr, dc = link["direction"]
        er, ec = link["aligned_endpoint"]
        for step in range(1, link["distance"]):
            output[er + dr * step][ec + dc * step] = link["path"]["color"]
        endpoint = (
            link["other_endpoint"]
            if recolor_origin == "opposite"
            else link["aligned_endpoint"]
        )
        for r, c in _walk_from(link["path"], endpoint)[: link["extension_count"]]:
            output[r][c] = link["marker"]["color"]
    return output


def _far_markers_only(grid):
    """Canonical-fitting shortcut: incorrectly ignores markers <4 cells away."""
    return _apply_reference_rule(grid, minimum_marker_distance=4)


def _has_near_marker(grid):
    return min(link["distance"] for link in _scene_info(grid)["links"]) <= 3


def lesson_identifiable(demos, query):
    """Check the declared canonical-fitting shortcut against one labeled lesson."""
    reasons = []
    if not demos:
        return ["no demonstrations"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            differs = (
                query.get("output") is not None
                and rival(query["input"]) != query["output"]
            )
        except Exception as exc:  # deterministic, actionable hook diagnostic
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and differs:
            reasons.append(
                f"{name} fits every demonstration but predicts a different query"
            )
    return reasons


SEMANTIC_WITNESSES = {"near_marker": _has_near_marker}
SEMANTIC_RIVALS = {"far_markers_only": _far_markers_only}
WITNESS_RIVALS = {"near_marker": ["far_markers_only"]}
CANONICAL_SHORTCUTS = {"far_markers_only": _far_markers_only}
LESSON_COMPETITORS = {"far_markers_only": _far_markers_only}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def mutation_fixtures():
    empty = full_grid(14, 14, 0)
    singleton = full_grid(14, 14, 0)
    singleton[5][8] = 4
    straight = full_grid(14, 14, 0)
    for c in range(3, 9):
        straight[7][c] = 3
    branch = full_grid(14, 14, 0)
    for c in range(3, 9):
        branch[7][c] = 3
    branch[6][6] = 3
    return [
        ("all_background", empty),
        ("singleton_only", singleton),
        ("straight_bar", straight),
        ("branched_path", branch),
    ]
