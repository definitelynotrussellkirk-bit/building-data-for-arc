"""Input sampler for local rays inside connected rectangular gray frames.

The canonical Racket program treats a color-5 connected component as a chamber
only when that *whole component* is exactly one rectangular border.  Therefore
two visually recognizable rectangles whose borders touch form one malformed
component and are intentionally inactive.  This sampler alternates ordinary
isolated chambers with that canonical counterexample.  It returns inputs only;
Racket remains the label authority.  Python rule mirrors below exist solely for
regression tests and declared-rival audits.
"""
from __future__ import annotations

from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "501c7f0770eb"
TASK_ID = GENERATOR_ID
RULE_HASH = "a850cef9c1ff"
VERSION = "3.1.0"

SUMMARY = (
    "A zero-background grid contains either two isolated rectangular gray(5) "
    "chambers or three visible rectangles where two touch and merge into one "
    "non-rectangular component. Only connected color-5 components that are "
    "exact rectangle borders are active. In each active chamber, blue(1) emits "
    "a vertical orange(7) ray and red(2) a horizontal ray; gray walls and "
    "yellow(4) blockers stop the ray. Seeds and blockers inside the malformed "
    "touching pair stay unchanged."
)

INVARIANTS = [
    "10..15 by 16..22 rectangular grid using only colors 0,1,2,4,5",
    "two or three isolated frames, or three visible frames with exactly one isolated active component",
    "every visible frame has exactly one seed and one or two blockers in its interior",
    "both seed colors occur in every input",
    "at least one active seed has an axis blocker with open space behind it",
]

LAYOUT_KINDS = ("isolated", "mixed_touching")
BLOCKER_STYLES = ("axis_only", "mixed")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-weighted 10..15", "valid": "10..15"},
    "grid_w": {"type": "int", "default": "difficulty-weighted 16..22", "valid": "16..22"},
    "layout_kind": {
        "type": "str",
        "default": "two-profile isolated/touching schedule",
        "valid": "isolated|mixed_touching",
    },
    "blocker_style": {
        "type": "str",
        "default": "two-profile mixed/axis schedule",
        "valid": "axis_only|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# Every four-pair lesson (three demonstrations plus one query) contains two of
# each topology.  Holding out any one pair therefore leaves a touching-frame
# counterexample in the demonstrations.
SCHEDULE_PROFILES = (
    "isolated:mixed",
    "mixed_touching:axis_only",
)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# A frame is (top row, left column, height, width).
Frame = tuple[int, int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Public semantic schedule keyed only by sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _scheduled_axes(seed: int, sample_index: int) -> tuple[str, str]:
    del seed
    profile = SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]
    layout, blocker = profile.split(":", 1)
    return layout, blocker


def _border_cells(frame: Frame) -> set[tuple[int, int]]:
    r0, c0, fh, fw = frame
    r1, c1 = r0 + fh - 1, c0 + fw - 1
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _interior_cells(*frame: int) -> list[tuple[int, int]]:
    r0, c0, fh, fw = frame
    return [
        (r, c)
        for r in range(r0 + 1, r0 + fh - 1)
        for c in range(c0 + 1, c0 + fw - 1)
    ]


def _draw_frame(grid: list[list[int]], frame: Frame) -> None:
    for r, c in _border_cells(frame):
        grid[r][c] = 5


def _rectangle_frames(grid: list[list[int]]) -> list[Frame]:
    """Find every canonical-size visible rectangle, including touching ones.

    A summed-area table makes each candidate check constant-time.  Repeated
    brute-force border-set construction dominated the override-contract matrix.
    """
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    prefix = [[0] * (w + 1) for _ in range(h + 1)]
    for r, row in enumerate(grid):
        running = 0
        for c, value in enumerate(row):
            running += value == 5
            prefix[r + 1][c + 1] = prefix[r][c + 1] + running

    def gray_count(r0: int, c0: int, r1: int, c1: int) -> int:
        return (
            prefix[r1][c1]
            - prefix[r0][c1]
            - prefix[r1][c0]
            + prefix[r0][c0]
        )

    found: list[Frame] = []
    for fh in range(4, 7):
        border_count = 2 * fh - 2
        for fw in range(6, 9):
            expected = border_count + 2 * fw - 2
            for r0 in range(h - fh + 1):
                r1 = r0 + fh
                for c0 in range(w - fw + 1):
                    c1 = c0 + fw
                    if gray_count(r0 + 1, c0 + 1, r1 - 1, c1 - 1):
                        continue
                    if gray_count(r0, c0, r1, c1) == expected:
                        found.append((r0, c0, fh, fw))
    return found


def _color_components(grid: list[list[int]], color: int = 5) -> list[frozenset[tuple[int, int]]]:
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    components: list[frozenset[tuple[int, int]]] = []
    while cells:
        start = min(cells)
        seen = {start}
        stack = [start]
        cells.remove(start)
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in cells:
                    cells.remove(nxt)
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(frozenset(seen))
    return components


def _frame_analysis(
    grid: list[list[int]],
) -> tuple[list[Frame], list[Frame], list[frozenset[tuple[int, int]]]]:
    frames = _rectangle_frames(grid)
    components = _color_components(grid, 5)
    component_set = set(components)
    active = [
        frame
        for frame in frames
        if frozenset(_border_cells(frame)) in component_set
    ]
    return frames, active, components


def _active_frames(grid: list[list[int]]) -> list[Frame]:
    return _frame_analysis(grid)[1]


def _component_id(frame: Frame, components: list[frozenset[tuple[int, int]]]) -> int | None:
    border = _border_cells(frame)
    hits = [index for index, component in enumerate(components) if border <= component]
    return hits[0] if len(hits) == 1 else None


def _infer_layout(
    grid: list[list[int]],
    analysis: tuple[
        list[Frame],
        list[Frame],
        list[frozenset[tuple[int, int]]],
    ] | None = None,
) -> str:
    frames, active_list, components = analysis or _frame_analysis(grid)
    active = set(active_list)
    if len(frames) in (2, 3) and len(active) == len(frames):
        return "isolated"
    if len(frames) == 3 and len(active) == 1:
        inactive = [frame for frame in frames if frame not in active]
        ids = [_component_id(frame, components) for frame in inactive]
        active_id = _component_id(next(iter(active)), components)
        if ids[0] is not None and ids[0] == ids[1] and ids[0] != active_id:
            return "mixed_touching"
    raise ValueError(
        f"expected two or three isolated active frames or one active plus a touching pair; "
        f"found {len(frames)} rectangles and {len(active)} active"
    )


def _frame_contents(grid: list[list[int]], frame: Frame):
    inside = _interior_cells(*frame)
    seeds = [(r, c, grid[r][c]) for r, c in inside if grid[r][c] in (1, 2)]
    blockers = [(r, c) for r, c in inside if grid[r][c] == 4]
    return seeds, blockers


def _is_axis(seed: tuple[int, int, int], cell: tuple[int, int]) -> bool:
    sr, sc, color = seed
    r, c = cell
    return c == sc if color == 1 else r == sr


def _infer_blocker_style(
    grid: list[list[int]], frames: Iterable[Frame] | None = None
) -> str:
    for frame in frames if frames is not None else _rectangle_frames(grid):
        seeds, blockers = _frame_contents(grid, frame)
        if len(seeds) != 1:
            raise ValueError("cannot infer blocker style without exactly one seed per frame")
        if any(not _is_axis(seeds[0], blocker) for blocker in blockers):
            return "mixed"
    return "axis_only"


def observe_overrides(grid: list[list[int]]) -> dict[str, object]:
    """Recover every declared axis from returned pixels."""
    analysis = _frame_analysis(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout_kind": _infer_layout(grid, analysis),
        "blocker_style": _infer_blocker_style(grid, analysis[0]),
    }


def _weighted_dimension(
    ctx, name: str, lo: int, hi: int, difficulty, *, canonical_anchor: int | None = None
) -> int:
    values = list(range(lo, hi + 1))
    if ctx.overrides.get(name) is not None:
        # Exact overrides must remain legal even on an anchored default draw.
        return ctx.draw_choice(name, values)
    if canonical_anchor is not None:
        return ctx.draw_choice(name, (canonical_anchor,))
    if difficulty == "easy":
        values += list(range(lo, min(hi, lo + 2) + 1)) * 3
    elif difficulty == "hard":
        values += list(range(max(lo, hi - 2), hi + 1)) * 3
    else:
        middle = (lo + hi) // 2
        values += [middle] * 3
    return ctx.draw_choice(name, values)


def _isolated_two_frames(h: int, w: int, rng) -> list[Frame]:
    placements = []
    for fw1 in range(6, 9):
        for fw2 in range(6, 9):
            for c1 in (0, 1):
                for right_margin in (0, 1):
                    c2 = w - right_margin - fw2
                    if c2 >= c1 + fw1 + 1:  # at least one zero column between components
                        placements.append((fw1, fw2, c1, c2))
    if not placements:
        raise ValueError(f"{h}x{w} cannot fit two isolated chambers")
    fw1, fw2, c1, c2 = rng.choice(placements)
    fh1 = rng.choice(tuple(range(5, min(6, h) + 1)))
    fh2 = rng.choice(tuple(range(5, min(6, h) + 1)))
    r1 = rng.randint(0, h - fh1)
    r2 = rng.randint(0, h - fh2)
    return [(r1, c1, fh1, fw1), (r2, c2, fh2, fw2)]


def _isolated_three_frames(h: int, w: int, rng) -> list[Frame]:
    """Two upper chambers plus one lower chamber, all 4-disconnected."""
    placements = []
    top_h = 5
    for fw1 in range(6, 9):
        for fw2 in range(6, 9):
            for c1 in (0, 1):
                for right_margin in (0, 1):
                    c2 = w - right_margin - fw2
                    if c2 < c1 + fw1 + 1:
                        continue
                    for lower_h in (4, 5):
                        for lower_r in range(top_h + 1, h - lower_h + 1):
                            for lower_w in range(6, 9):
                                if lower_w <= w:
                                    placements.append(
                                        (fw1, fw2, c1, c2, lower_h, lower_r, lower_w)
                                    )
    if not placements:
        raise ValueError(f"{h}x{w} cannot fit three isolated chambers")
    fw1, fw2, c1, c2, lower_h, lower_r, lower_w = rng.choice(placements)
    lower_c = rng.randint(0, w - lower_w)
    return [
        (0, c1, top_h, fw1),
        (0, c2, top_h, fw2),
        (lower_r, lower_c, lower_h, lower_w),
    ]


def _isolated_frames(h: int, w: int, rng) -> list[Frame]:
    return (
        _isolated_three_frames(h, w, rng)
        if rng.randrange(2)
        else _isolated_two_frames(h, w, rng)
    )


def _mixed_vertical_frames(h: int, w: int, rng) -> list[Frame]:
    placements = []
    for fh1 in (4, 5):
        for fh2 in (4, 5):
            if fh1 + fh2 > h:
                continue
            for pair_w in (6, 7):
                for iso_h in (5, 6):
                    if iso_h > h:
                        continue
                    for iso_w in (6, 7, 8):
                        for pair_c in (0, 1):
                            for right_margin in (0, 1):
                                iso_c = w - right_margin - iso_w
                                if iso_c >= pair_c + pair_w + 1:
                                    placements.append((fh1, fh2, pair_w, iso_h, iso_w, pair_c, iso_c))
    if not placements:
        raise ValueError(f"{h}x{w} cannot fit the vertical touching profile")
    fh1, fh2, pair_w, iso_h, iso_w, pair_c, iso_c = rng.choice(placements)
    pair_r = rng.randint(0, h - fh1 - fh2)
    iso_r = rng.randint(0, h - iso_h)
    return [
        (pair_r, pair_c, fh1, pair_w),
        (pair_r + fh1, pair_c, fh2, pair_w),
        (iso_r, iso_c, iso_h, iso_w),
    ]


def _mixed_horizontal_frames(h: int, w: int, rng) -> list[Frame]:
    placements = []
    for fw1 in (6, 7):
        for fw2 in (6, 7):
            if fw1 + fw2 > w:
                continue
            for pair_r in (0, 1):
                pair_h = 4
                pair_bottom = pair_r + pair_h - 1
                for iso_h in (4, 5, 6):
                    for iso_r in range(pair_bottom + 2, h - iso_h + 1):
                        for iso_w in (6, 7, 8):
                            if iso_w <= w:
                                placements.append((fw1, fw2, pair_r, iso_h, iso_r, iso_w))
    if not placements:
        raise ValueError(f"{h}x{w} cannot fit the horizontal touching profile")
    fw1, fw2, pair_r, iso_h, iso_r, iso_w = rng.choice(placements)
    pair_c = rng.randint(0, w - fw1 - fw2)
    iso_c = rng.randint(0, w - iso_w)
    return [
        (pair_r, pair_c, 4, fw1),
        (pair_r, pair_c + fw1, 4, fw2),
        (iso_r, iso_c, iso_h, iso_w),
    ]


def _mixed_frames(h: int, w: int, rng) -> list[Frame]:
    builders = [_mixed_vertical_frames, _mixed_horizontal_frames]
    rng.shuffle(builders)
    errors = []
    for builder in builders:
        try:
            return builder(h, w, rng)
        except ValueError as exc:
            errors.append(str(exc))
    raise ValueError("; ".join(errors))


def _random_seed_site(frame: Frame, seed_color: int, rng) -> tuple[int, int]:
    del seed_color
    return rng.choice(_interior_cells(*frame))


def _clip_seed_and_blocker(
    frame: Frame, seed_color: int, rng
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Choose seed, blocker, and an open cell beyond the blocker."""
    r0, c0, fh, fw = frame
    reverse = bool(rng.randrange(2))
    if seed_color == 1:
        rows = list(range(r0 + 1, r0 + fh - 1))
        if len(rows) < 3:
            raise ValueError("vertical clipping witness requires frame height at least 5")
        c = rng.randint(c0 + 1, c0 + fw - 2)
        seed_i, blocker_i, beyond_i = (0, len(rows) - 2, len(rows) - 1)
        if reverse:
            seed_i, blocker_i, beyond_i = len(rows) - 1, 1, 0
        return (rows[seed_i], c), (rows[blocker_i], c), (rows[beyond_i], c)
    cols = list(range(c0 + 1, c0 + fw - 1))
    if len(cols) < 3:
        raise ValueError("horizontal clipping witness requires frame width at least 5")
    r = rng.randint(r0 + 1, r0 + fh - 2)
    seed_i, blocker_i, beyond_i = (0, len(cols) - 2, len(cols) - 1)
    if reverse:
        seed_i, blocker_i, beyond_i = len(cols) - 1, 1, 0
    return (r, cols[seed_i]), (r, cols[blocker_i]), (r, cols[beyond_i])


def _axis_candidates(frame: Frame, seed: tuple[int, int, int]) -> list[tuple[int, int]]:
    return [cell for cell in _interior_cells(*frame) if cell != seed[:2] and _is_axis(seed, cell)]


def _off_axis_candidates(frame: Frame, seed: tuple[int, int, int]) -> list[tuple[int, int]]:
    return [cell for cell in _interior_cells(*frame) if cell != seed[:2] and not _is_axis(seed, cell)]


def _place_contents(
    grid: list[list[int]],
    frames: list[Frame],
    seed_colors: list[int],
    active_indices: set[int],
    blocker_style: str,
    rng,
) -> None:
    clip_index = min(active_indices)
    off_axis_index = None
    if blocker_style == "mixed":
        off_axis_index = next(index for index in range(len(frames)) if index != clip_index)

    for index, (frame, seed_color) in enumerate(zip(frames, seed_colors)):
        reserved: set[tuple[int, int]] = set()
        if index == clip_index:
            seed_cell, blocker, beyond = _clip_seed_and_blocker(frame, seed_color, rng)
            blockers = [blocker]
            reserved.add(beyond)
        else:
            seed_cell = _random_seed_site(frame, seed_color, rng)
            seed = (*seed_cell, seed_color)
            pool = (
                _off_axis_candidates(frame, seed)
                if index == off_axis_index
                else _axis_candidates(frame, seed)
            )
            blockers = [rng.choice(pool)]

        seed = (*seed_cell, seed_color)
        extra_pool = (
            _off_axis_candidates(frame, seed)
            if index == off_axis_index
            else _axis_candidates(frame, seed)
        )
        extra_pool = [cell for cell in extra_pool if cell not in blockers and cell not in reserved]
        if extra_pool and rng.randrange(2):
            blockers.append(rng.choice(extra_pool))

        grid[seed_cell[0]][seed_cell[1]] = seed_color
        for r, c in blockers:
            grid[r][c] = 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer; sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name in ("grid_h", "grid_w"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, not {type(overrides[name]).__name__}")
    for name, allowed in (("layout_kind", LAYOUT_KINDS), ("blocker_style", BLOCKER_STYLES)):
        value = overrides.get(name)
        if value is not None and (type(value) is not str or value not in allowed):
            raise ValueError(f"{name} must be one of {allowed}, not {value!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    canonical_profile = (12, 18) if seed % 2 == 0 else (None, None)
    h = _weighted_dimension(
        ctx, "grid_h", 10, 15, difficulty, canonical_anchor=canonical_profile[0]
    )
    w = _weighted_dimension(
        ctx, "grid_w", 16, 22, difficulty, canonical_anchor=canonical_profile[1]
    )
    scheduled_layout, scheduled_blocker = _scheduled_axes(seed, sample_index)
    layout_options = LAYOUT_KINDS if overrides.get("layout_kind") is not None else (scheduled_layout,)
    blocker_options = BLOCKER_STYLES if overrides.get("blocker_style") is not None else (scheduled_blocker,)
    layout_kind = ctx.draw_choice("layout_kind", layout_options)
    blocker_style = ctx.draw_choice("blocker_style", blocker_options)
    rng = ctx.draw_rng("layout")

    frames = _isolated_frames(h, w, rng) if layout_kind == "isolated" else _mixed_frames(h, w, rng)
    grid = full_grid(h, w, 0)
    for frame in frames:
        _draw_frame(grid, frame)

    if layout_kind == "isolated":
        seed_colors = [1, 2]
        while len(seed_colors) < len(frames):
            seed_colors.append(rng.choice((1, 2)))
        rng.shuffle(seed_colors)
        active_indices = set(range(len(frames)))
    else:
        # The first two frames are the touching pair; the third is isolated.
        pair_colors = [1, 2]
        rng.shuffle(pair_colors)
        active_color = 2 if frames[2][2] == 4 else rng.choice((1, 2))
        seed_colors = pair_colors + [active_color]
        active_indices = {2}

    _place_contents(grid, frames, seed_colors, active_indices, blocker_style, rng)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator violated its contract: {errors}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 4, 5) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,4,5"]
    h = len(grid)
    errors: list[str] = []
    if not 10 <= h <= 15:
        errors.append(f"grid height {h} outside 10..15")
    if not 16 <= w <= 22:
        errors.append(f"grid width {w} outside 16..22")

    analysis = _frame_analysis(grid)
    frames, active, _components = analysis
    try:
        layout = _infer_layout(grid, analysis)
    except ValueError as exc:
        errors.append(str(exc))
        layout = None

    seed_colors: set[int] = set()
    all_interiors = {cell for frame in frames for cell in _interior_cells(*frame)}
    all_borders = {cell for frame in frames for cell in _border_cells(frame)}
    for frame in frames:
        seeds, blockers = _frame_contents(grid, frame)
        if len(seeds) != 1:
            errors.append(f"frame {frame} has {len(seeds)} seeds; expected exactly one")
            continue
        seed_colors.add(seeds[0][2])
        if not 1 <= len(blockers) <= 3:
            errors.append(f"frame {frame} has {len(blockers)} blockers; expected one to three")
    if seed_colors != {1, 2}:
        errors.append(f"expected both seed colors across frames, found {sorted(seed_colors)}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 5 and (r, c) not in all_borders:
                errors.append(f"extraneous color-5 cell at {(r, c)}")
            elif value in (1, 2, 4) and (r, c) not in all_interiors:
                errors.append(f"color-{value} cell outside a frame interior at {(r, c)}")
    if layout == "isolated" and len(active) not in (2, 3):
        errors.append("isolated layout must have two or three active frame components")
    if layout == "mixed_touching" and len(active) != 1:
        errors.append("mixed touching layout must have exactly one active frame component")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _ray_model(
    grid: list[list[int]], frames: Iterable[Frame], *, ignore_blockers: bool = False
) -> list[list[int]]:
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    for r0, c0, fh, fw in frames:
        rmin, rmax = r0 + 1, r0 + fh - 2
        cmin, cmax = c0 + 1, c0 + fw - 2
        seeds, _ = _frame_contents(source, (r0, c0, fh, fw))
        for sr, sc, color in seeds:
            directions = ((-1, 0), (1, 0)) if color == 1 else ((0, -1), (0, 1))
            out[sr][sc] = 7
            for dr, dc in directions:
                r, c = sr + dr, sc + dc
                while rmin <= r <= rmax and cmin <= c <= cmax:
                    value = source[r][c]
                    if value == 4:
                        if not ignore_blockers:
                            break
                    else:
                        out[r][c] = 7
                    r += dr
                    c += dc
    return out


def _component_rule_model(grid: list[list[int]]) -> list[list[int]]:
    """Independent audit mirror; never used to label generated examples."""
    return _ray_model(grid, _active_frames(grid))


def _all_rectangles_fire(grid: list[list[int]]) -> list[list[int]]:
    """Rival: incorrectly treats every visually complete rectangle as active."""
    return _ray_model(grid, _rectangle_frames(grid))


def _ignore_blockers(grid: list[list[int]]) -> list[list[int]]:
    """Rival: leaves yellow cells intact but lets rays continue through them."""
    return _ray_model(grid, _active_frames(grid), ignore_blockers=True)


def _has_inactive_touching_pair(grid: list[list[int]]) -> bool:
    try:
        return _infer_layout(grid) == "mixed_touching" and _all_rectangles_fire(grid) != _component_rule_model(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _has_observable_axis_blocker(grid: list[list[int]]) -> bool:
    try:
        return _ignore_blockers(grid) != _component_rule_model(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "touching_frames_inactive": _has_inactive_touching_pair,
    "axis_blocker_clips": _has_observable_axis_blocker,
}
SEMANTIC_RIVALS = {
    "all_rectangles_fire": _all_rectangles_fire,
    "ignore_blockers": _ignore_blockers,
}
WITNESS_RIVALS = {
    "touching_frames_inactive": ["all_rectangles_fire"],
    "axis_blocker_clips": ["ignore_blockers"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
