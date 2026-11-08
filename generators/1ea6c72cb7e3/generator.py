"""Generator for task 1ea6c72cb7e3: wall-blocked line-of-sight voting.

Every non-{0, 5} singleton is a differently colored watcher.  A background
cell sees watchers sharing its row or column unless a color-5 wall lies
between them.  The canonical Racket rule preserves walls/watchers and paints
background cells with 0, the sole visible watcher color, or 8 for a conflict.

The generator builds the long bar/cross wall topology seen in the canonical
pairs, then rejects layouts that fail to exercise all three visibility
branches or in which the walls do not actually occlude a watcher.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ea6c72cb7e3"
TASK_ID = "1ea6c72cb7e3"
VERSION = "3.1.0"
RULE_HASH = "e74d7b3af3b2"

SUMMARY = (
    "Interleave canonical-scale anchors, line-of-sight counterexamples, and "
    "broad wall/watcher layouts; each three-draw lesson refutes named rivals."
)

INVARIANTS = [
    "background is modal color 0; color 5 is the only wall color",
    "there are exactly 3 or 4 isolated singleton watchers in distinct colors, "
    "never using 0, 5, or conflict marker 8",
    "walls form a cross, ladder, split cross, or split ladder made from long "
    "axis-aligned runs rather than isolated pixels",
    "some background cells see zero, exactly one, and at least two distinct "
    "watcher colors",
    "every watcher owns at least one sole-visible background cell",
    "at least one color-5 wall changes a watcher's line of sight",
]

SCENE_PROFILES = ("cross", "ladder", "split_cross", "split_ladder")
_VALID_H = (9, 13)
_VALID_W = (9, 14)
_VALID_WATCHERS = (3, 4)
_WATCHER_COLORS = (1, 2, 3, 4, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale anchors; otherwise difficulty-skewed rng 9..13",
        "valid": "9..13",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale anchors; otherwise difficulty-skewed rng 9..14",
        "valid": "9..14",
        "doc": "Grid width.",
    },
    "n_watchers": {
        "type": "int",
        "default": "3 for canonical anchors; otherwise difficulty-skewed rng 3..4",
        "valid": "3..4",
        "doc": "Exact number of distinct singleton watcher cells.",
    },
    "scene_profile": {
        "type": "enum",
        "default": "difficulty-weighted rng",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Observable wall topology: connected or split bar/cross forms.",
    },
}


def _paint_h(grid: list[list[int]], row: int, c0: int, c1: int) -> None:
    for col in range(c0, c1 + 1):
        grid[row][col] = 5


def _paint_v(grid: list[list[int]], col: int, r0: int, r1: int) -> None:
    for row in range(r0, r1 + 1):
        grid[row][col] = 5


def _wall_runs(grid: list[list[int]]) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    """Maximal horizontal/vertical color-5 runs of length at least two."""
    h, w = len(grid), len(grid[0])
    horizontal: list[tuple[int, int, int]] = []
    vertical: list[tuple[int, int, int]] = []
    for row in range(h):
        col = 0
        while col < w:
            if grid[row][col] != 5:
                col += 1
                continue
            start = col
            while col < w and grid[row][col] == 5:
                col += 1
            if col - start >= 2:
                horizontal.append((row, start, col - 1))
    for col in range(w):
        row = 0
        while row < h:
            if grid[row][col] != 5:
                row += 1
                continue
            start = row
            while row < h and grid[row][col] == 5:
                row += 1
            if row - start >= 2:
                vertical.append((col, start, row - 1))
    return horizontal, vertical


def _wall_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 5
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def _classify_profile(grid: list[list[int]]) -> str | None:
    horizontal, vertical = _wall_runs(grid)
    components = _wall_components(grid)
    h_count, v_count, c_count = len(horizontal), len(vertical), len(components)
    if c_count == 1 and (h_count, v_count) == (1, 1):
        return "cross"
    if c_count == 1 and (h_count, v_count) in {(2, 1), (1, 2)}:
        return "ladder"
    if c_count == 2 and (h_count, v_count) in {(2, 1), (1, 2)}:
        return "split_cross"
    if c_count == 2 and (h_count, v_count) in {(3, 1), (1, 3)}:
        return "split_ladder"
    return None


def _build_cross(rng, h: int, w: int) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    row = rng.randint(2, h - 3)
    col = rng.randint(2, w - 3)
    left = rng.randint(2, min(col, 5))
    right = rng.randint(2, min(w - 1 - col, 5))
    up = rng.randint(2, min(row, 5))
    down = rng.randint(2, min(h - 1 - row, 5))
    _paint_h(grid, row, col - left, col + right)
    _paint_v(grid, col, row - up, row + down)
    return grid


def _build_ladder(rng, h: int, w: int) -> tuple[list[list[int]], str]:
    """Build one connected two-rail ladder; return its rail orientation."""
    grid = full_grid(h, w, 0)
    if rng.choice((False, True)):
        first = rng.randint(1, h - 5)
        second = rng.randint(first + 3, min(h - 2, first + 6))
        span = rng.randint(4, min(w - 1, 8))
        start = rng.randint(0, w - span)
        end = start + span - 1
        connector = rng.randint(start + 1, end - 1)
        _paint_h(grid, first, start, end)
        _paint_h(grid, second, start, end)
        _paint_v(grid, connector, first, second)
        return grid, "h"

    first = rng.randint(1, w - 5)
    second = rng.randint(first + 3, min(w - 2, first + 6))
    span = rng.randint(4, min(h - 1, 8))
    start = rng.randint(0, h - span)
    end = start + span - 1
    connector = rng.randint(start + 1, end - 1)
    _paint_v(grid, first, start, end)
    _paint_v(grid, second, start, end)
    _paint_h(grid, connector, first, second)
    return grid, "v"


def _detached_bar_candidates(
    grid: list[list[int]], orientation: str, length: int
) -> list[tuple[int, int]]:
    """Starts for bars separated from every existing wall by one 4-neighbor step."""
    h, w = len(grid), len(grid[0])
    candidates: list[tuple[int, int]] = []
    if orientation == "h":
        starts = ((row, col) for row in range(h) for col in range(w - length + 1))
    else:
        starts = ((row, col) for row in range(h - length + 1) for col in range(w))
    for row, col in starts:
        cells = [
            (row, col + offset) if orientation == "h" else (row + offset, col)
            for offset in range(length)
        ]
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        neighborhood = set(cells)
        for r, c in cells:
            neighborhood.update(
                (r + dr, c + dc)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < h and 0 <= c + dc < w
            )
        if any(grid[r][c] == 5 for r, c in neighborhood):
            continue
        candidates.append((row, col))
    return candidates


def _add_detached_bar(grid: list[list[int]], rng, orientation: str) -> bool:
    max_len = min(5, len(grid[0]) if orientation == "h" else len(grid))
    lengths = list(range(2, max_len + 1))
    rng.shuffle(lengths)
    for length in lengths:
        candidates = _detached_bar_candidates(grid, orientation, length)
        if not candidates:
            continue
        row, col = rng.choice(candidates)
        if orientation == "h":
            _paint_h(grid, row, col, col + length - 1)
        else:
            _paint_v(grid, col, row, row + length - 1)
        return True
    return False


def _build_walls(rng, h: int, w: int, profile: str) -> list[list[int]]:
    for _ in range(240):
        if profile == "cross":
            grid = _build_cross(rng, h, w)
        elif profile == "ladder":
            grid, _ = _build_ladder(rng, h, w)
        elif profile == "split_cross":
            grid = _build_cross(rng, h, w)
            if not _add_detached_bar(grid, rng, rng.choice(("h", "v"))):
                continue
        elif profile == "split_ladder":
            grid, orientation = _build_ladder(rng, h, w)
            if not _add_detached_bar(grid, rng, orientation):
                continue
        else:  # generate validates the public override before entering here.
            raise ValueError(f"unknown scene_profile {profile!r}")
        if _classify_profile(grid) == profile:
            return grid
    raise ValueError(f"could not realize wall profile {profile!r} on {h}x{w}")


def _watchers(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, grid[row][col])
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] not in {0, 5}
    ]


def _between_values(
    grid: list[list[int]], row: int, col: int, other_row: int, other_col: int
) -> Iterable[int]:
    if row == other_row:
        for c in range(min(col, other_col) + 1, max(col, other_col)):
            yield grid[row][c]
    elif col == other_col:
        for r in range(min(row, other_row) + 1, max(row, other_row)):
            yield grid[r][col]


def _visibility_facts(grid: list[list[int]]) -> dict:
    watchers = _watchers(grid)
    branch_counts = Counter({"zero": 0, "one": 0, "multi": 0})
    sole_by_color = Counter()
    blocked_watchers: set[int] = set()
    wall_effect_cells = 0
    suppressed_conflicts = 0
    max_visible = 0

    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 0:
                continue
            visible: set[int] = set()
            without_walls: set[int] = set()
            for wr, wc, color in watchers:
                if wr != row and wc != col:
                    continue
                without_walls.add(color)
                if 5 in _between_values(grid, row, col, wr, wc):
                    blocked_watchers.add(color)
                else:
                    visible.add(color)
            max_visible = max(max_visible, len(visible))
            if not visible:
                branch_counts["zero"] += 1
            elif len(visible) == 1:
                branch_counts["one"] += 1
                sole_by_color[next(iter(visible))] += 1
            else:
                branch_counts["multi"] += 1
            if visible != without_walls:
                wall_effect_cells += 1
            if len(without_walls) >= 2 and len(visible) < 2:
                suppressed_conflicts += 1

    components = _wall_components(grid)
    return {
        "watchers": watchers,
        "profile": _classify_profile(grid),
        "branches": dict(branch_counts),
        "sole_by_color": dict(sole_by_color),
        "blocked_watchers": sorted(blocked_watchers),
        "wall_effect_cells": wall_effect_cells,
        "suppressed_conflicts": suppressed_conflicts,
        "max_visible": max_visible,
        "wall_component_sizes": sorted((len(component) for component in components), reverse=True),
    }


def observe_overrides(grid) -> dict:
    """Recover the exact semantic axes represented by the returned grid."""
    facts = _visibility_facts(grid)
    return {
        "n_watchers": len(facts["watchers"]),
        "scene_profile": facts["profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding instances, not merely bad palettes."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid value"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]

    errors: list[str] = []
    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for value in values
    ):
        return ["grid contains a non-integer or color outside 0..9"]
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(
            f"dims {h}x{w} outside declared envelope "
            f"{_VALID_H[0]}..{_VALID_H[1]} x {_VALID_W[0]}..{_VALID_W[1]}"
        )
    if values.count(0) * 2 <= h * w:
        errors.append("background 0 is not a strict majority")
    illegal = sorted(set(values) - ({0, 5} | set(_WATCHER_COLORS)))
    if illegal:
        errors.append(f"illegal input colors (including reserved conflict 8): {illegal}")

    watchers = _watchers(grid)
    if not (_VALID_WATCHERS[0] <= len(watchers) <= _VALID_WATCHERS[1]):
        errors.append(f"expected 3 or 4 watcher cells, got {len(watchers)}")
    watcher_colors = [color for _, _, color in watchers]
    if len(set(watcher_colors)) != len(watcher_colors):
        errors.append("watcher colors are not pairwise distinct singleton labels")
    for index, (row, col, _) in enumerate(watchers):
        if any(
            abs(row - other_row) + abs(col - other_col) < 2
            for other_row, other_col, _ in watchers[index + 1 :]
        ):
            errors.append("watchers are not 4-neighbor isolated")
            break

    wall_cells = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 5
    }
    if not wall_cells:
        errors.append("no color-5 wall cells")
    horizontal, vertical = _wall_runs(grid)
    supported = set()
    for row, c0, c1 in horizontal:
        supported.update((row, col) for col in range(c0, c1 + 1))
    for col, r0, r1 in vertical:
        supported.update((row, col) for row in range(r0, r1 + 1))
    if wall_cells - supported:
        errors.append("wall topology contains isolated pixels outside length-2+ runs")

    facts = _visibility_facts(grid)
    if facts["profile"] not in SCENE_PROFILES:
        errors.append(
            "wall topology is not an observable cross/ladder/split profile "
            f"(classified {facts['profile']!r})"
        )
    component_sizes = facts["wall_component_sizes"]
    if not component_sizes or component_sizes[0] < 7:
        errors.append("largest connected wall component is shorter than 7 cells")

    branches = facts["branches"]
    for branch in ("zero", "one", "multi"):
        if branches.get(branch, 0) < 1:
            errors.append(f"visibility branch {branch!r} is not exercised")
    missing_sole = sorted(
        color for color in watcher_colors if facts["sole_by_color"].get(color, 0) < 1
    )
    if missing_sole:
        errors.append(f"watchers without a sole-visible cell: {missing_sole}")
    if facts["wall_effect_cells"] < 1:
        errors.append("walls do not alter any watcher line of sight")

    requested = {}
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if not isinstance(requested, dict):
            requested = {}
    if requested.get("n_watchers") is not None and len(watchers) != int(requested["n_watchers"]):
        errors.append(
            f"n_watchers override requested {requested['n_watchers']}, realized {len(watchers)}"
        )
    if requested.get("scene_profile") is not None and facts["profile"] != requested["scene_profile"]:
        errors.append(
            f"scene_profile override requested {requested['scene_profile']!r}, "
            f"realized {facts['profile']!r}"
        )
    return errors


def _profile_options(difficulty: str | None) -> tuple[str, ...]:
    # Every band contains every valid option, so explicit overrides retain the
    # full declared domain.  Repetition only adjusts the default prior.
    if difficulty == "easy":
        return (
            "cross", "cross", "cross", "ladder", "split_cross", "split_ladder"
        )
    if difficulty == "hard":
        return (
            "cross", "ladder", "split_cross", "split_cross",
            "split_ladder", "split_ladder", "split_ladder",
        )
    return (
        "cross", "cross", "ladder", "split_cross", "split_cross", "split_ladder"
    )


def _watcher_palette(ctx, n_watchers: int, curriculum: str) -> tuple[int, ...]:
    rng = ctx.draw_rng("watcher_palette")
    if curriculum == "contrast":
        novel = rng.choice((1, 6, 7, 9))
        colors = [novel] + rng.sample([c for c in _WATCHER_COLORS if c != novel], n_watchers - 1)
        rng.shuffle(colors)
        return tuple(colors)
    if curriculum == "anchor" and n_watchers == 3:
        colors = [2, 3, 4]
        rng.shuffle(colors)
        return tuple(colors)
    # Keep the canonical 2/3/4 trio common without making palette a declared
    # semantic axis.  Other legal colors prevent a fixed-palette shortcut.
    if n_watchers == 3 and rng.random() < 0.55:
        colors = [2, 3, 4]
        rng.shuffle(colors)
        return tuple(colors)
    if n_watchers == 4 and rng.random() < 0.45:
        extra = rng.choice([color for color in _WATCHER_COLORS if color not in {2, 3, 4}])
        colors = [2, 3, 4, extra]
        rng.shuffle(colors)
        return tuple(colors)
    return tuple(rng.sample(list(_WATCHER_COLORS), n_watchers))


_ANCHOR_SHAPES = ((9, 9), (10, 10), (11, 11), (10, 11))
SCHEDULE_PROFILES = ("anchor", "contrast", "broad")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-rotated 3-cycle; any three consecutive draws include every role.

    The claim concerns the default three-demo runner, not arbitrary shuffled
    pools or one/two-demo exports. Exact overrides take priority over anchors.
    """
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % 3]


def _contrast_positions(base, candidates, n_watchers, rng):
    """Propose two collinear watchers plus a perpendicular third around a zero.

    Construction makes triple visibility affordable; validation still decides
    whether all rival predictions differ. Nothing about the output is encoded
    as an input marker or exported as a label.
    """
    row, col = rng.choice(candidates)
    horizontal = [(r, c) for r, c in candidates if r == row and c != col
                  and 5 not in _between_values(base, row, col, r, c)]
    vertical = [(r, c) for r, c in candidates if c == col and r != row
                and 5 not in _between_values(base, row, col, r, c)]
    primary, secondary = (horizontal, vertical) if rng.choice((False, True)) else (vertical, horizontal)
    if len(primary) < 2 or not secondary:
        return None
    positions = rng.sample(primary, 2) + [rng.choice(secondary)]
    if n_watchers == 4:
        spare = [p for p in candidates if p not in positions and p != (row, col)]
        positions.append(rng.choice(spare))
    return positions


def _diagnostic_prediction(grid, *, canonical_colors=False, exactly_two=False,
                           opaque_watchers=False, ignore_walls=False):
    """Diagnostic Python model / rivals ONLY. Racket remains label authority.

    Separate from the ray-accumulation test model. Canonical and generated
    Racket comparisons must verify these hypotheses before accepting evidence.
    """
    watchers = _watchers(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            seen = set()
            for wr, wc, color in watchers:
                if canonical_colors and color not in (2, 3, 4):
                    continue
                if wr != r and wc != c:
                    continue
                between = list(_between_values(grid, r, c, wr, wc))
                if not ignore_walls and 5 in between:
                    continue
                if opaque_watchers and any(v not in (0, 5) for v in between):
                    continue
                seen.add(color)
            n = len(seen)
            out[r][c] = (0 if n == 0 else next(iter(seen)) if n == 1
                         else 0 if exactly_two and n > 2 else 8)
    return out


def _canonical_colors_only(grid):
    return _diagnostic_prediction(grid, canonical_colors=True)


def _exactly_two_conflicts(grid):
    return _diagnostic_prediction(grid, exactly_two=True)


def _opaque_watchers(grid):
    return _diagnostic_prediction(grid, opaque_watchers=True)


def _ignore_walls(grid):
    return _diagnostic_prediction(grid, ignore_walls=True)


def strict_canonical_like(grid):
    """Lawful task-domain scenes, not equality with a canonical size/palette."""
    return self_check(grid)


def _palette_witness(grid):
    return any(color not in (2, 3, 4) for _, _, color in _watchers(grid))


def _triple_witness(grid):
    return _visibility_facts(grid)["max_visible"] >= 3


def _transparency_witness(grid):
    return _opaque_watchers(grid) != _diagnostic_prediction(grid)


def _occlusion_witness(grid):
    return _ignore_walls(grid) != _diagnostic_prediction(grid)


SEMANTIC_RIVALS = {
    "canonical_colors_only": _canonical_colors_only,
    "exactly_two_conflicts": _exactly_two_conflicts,
    "opaque_watchers": _opaque_watchers,
    "ignore_walls": _ignore_walls,
}
CANONICAL_SHORTCUTS = {
    "canonical_colors_only": _canonical_colors_only,
    "exactly_two_conflicts": _exactly_two_conflicts,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "palette_generalization": _palette_witness,
    "three_or_more_visible": _triple_witness,
    "transparent_watchers": _transparency_witness,
    "material_occlusion": _occlusion_witness,
}
WITNESS_RIVALS = {
    "palette_generalization": ["canonical_colors_only"],
    "three_or_more_visible": ["exactly_two_conflicts"],
    "transparent_watchers": ["opaque_watchers"],
    "material_occlusion": ["ignore_walls"],
}


def _contrast_complete(grid):
    expected = _diagnostic_prediction(grid)
    return all(rival(grid) != expected for rival in LESSON_COMPETITORS.values())


def lesson_identifiable(demos, query):
    """Refutation against named rivals, not universal induction or query access.

    Deliberately use demonstrations alone. A rival surviving all demos is a
    teaching deficiency even when its answer happens to agree on this query.
    """
    return [f"rival survives every demonstration: {name}"
            for name, rival in {**CANONICAL_SHORTCUTS, **LESSON_COMPETITORS}.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    curriculum = schedule_profile(seed, sample_index, difficulty)
    if curriculum == "anchor":
        ah, aw = ctx.draw_choice("anchor_shape", _ANCHOR_SHAPES)
        # Choose the feasible default domain BEFORE each keyed draw. Explicit
        # controls still use their complete published domain, never a clamp.
        h = ctx.draw_int("grid_h", *(_VALID_H if overrides.get("grid_h") is not None else (ah, ah)))
        w = ctx.draw_int("grid_w", *(_VALID_W if overrides.get("grid_w") is not None else (aw, aw)))
        n_watchers = ctx.draw_int("n_watchers", *(_VALID_WATCHERS if overrides.get("n_watchers") is not None else (3, 3)))
    else:
        h = ctx.draw_int_diff("grid_h", *_VALID_H)
        w = ctx.draw_int_diff("grid_w", *_VALID_W)
        n_watchers = ctx.draw_int_diff("n_watchers", *_VALID_WATCHERS)
    profile = ctx.draw_choice("scene_profile", _profile_options(difficulty))
    colors = _watcher_palette(ctx, n_watchers, curriculum)
    rng = ctx.draw_rng("layout")

    for _ in range(120):
        base = _build_walls(rng, h, w, profile)
        candidates = [
            (row, col)
            for row in range(h)
            for col in range(w)
            if base[row][col] == 0
        ]
        for _ in range(180):
            positions = (
                _contrast_positions(base, candidates, n_watchers, rng)
                if curriculum == "contrast" else rng.sample(candidates, n_watchers)
            )
            if positions is None:
                continue
            if any(
                abs(r0 - r1) + abs(c0 - c1) < 2
                for index, (r0, c0) in enumerate(positions)
                for r1, c1 in positions[index + 1 :]
            ):
                continue
            grid = [row[:] for row in base]
            for (row, col), color in zip(positions, colors):
                grid[row][col] = color
            if not self_check(
                grid,
                difficulty=difficulty,
                meta={"overrides": {"n_watchers": n_watchers, "scene_profile": profile}},
            ):
                if curriculum != "contrast" or _contrast_complete(grid):
                    return grid
    raise ValueError(
        f"could not realize a branch-complete {profile} scene on {h}x{w} "
        f"with {n_watchers} watchers"
    )
