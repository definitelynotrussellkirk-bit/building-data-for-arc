"""Generator for dd231d152e42 — border emitters cast blocked inward rays.

Every nonzero, non-gray border cell is an emitter. Top/bottom emitters cast
vertically inward and left/right emitters cast horizontally inward. Gray (5)
cells are preserved blockers. Interior nonzero non-gray cells are distractors:
they neither emit nor block and disappear unless a ray repaints their cell.
At ray crossings, the numerically larger emitter color wins.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dd231d152e42"
TASK_ID = "dd231d152e42"
VERSION = "2.0.0"
RULE_HASH = "7c29c678f8b1"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "Nonzero non-gray cells on the four borders cast straight rays inward. "
    "Gray (5) cells stop and preserve rays, interior colored distractors do "
    "not emit or block, and crossing rays keep the larger color number."
)

INVARIANTS = [
    "background is 0 and corners are empty",
    "2-6 distinct-colored emitters occupy non-corner border cells on both a vertical and horizontal side",
    "1-3 interior gray(5) blockers are preserved, with at least one stopping a ray while another ray reaches the far border",
    "0-2 interior colored distractors do not block or emit; scheduled witnesses place them on rays",
    "at least one unequal-color vertical/horizontal crossing exposes larger-number precedence",
]

EMITTER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
SIDES = ("top", "bottom", "left", "right")
VERTICAL_SIDES = {"top", "bottom"}
HORIZONTAL_SIDES = {"left", "right"}

AXES = {
    "grid_h": {"type": "int", "default": "canonical schedule plus varied scale", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "canonical schedule plus varied scale", "valid": "5..10"},
    "n_emitters": {"type": "int", "default": "sample schedule 3..6, canonical anchors use 4", "valid": "2..6"},
    "n_blockers": {"type": "int", "default": "sample schedule", "valid": "1..3"},
    "n_distractors": {"type": "int", "default": "sample schedule", "valid": "0..2"},
}

DEGENERATE_TEXTURES = (
    "no_emitters",
    "corner_emitter",
    "blocker_on_border",
    "all_rays_blocked",
    "interior_emitters_only",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()


def _profiled_int(ctx, name: str, lo: int, hi: int, desired: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, desired, desired)


def _side(cell: tuple[int, int], h: int, w: int) -> str | None:
    r, c = cell
    if r == 0 and 0 < c < w - 1:
        return "top"
    if r == h - 1 and 0 < c < w - 1:
        return "bottom"
    if c == 0 and 0 < r < h - 1:
        return "left"
    if c == w - 1 and 0 < r < h - 1:
        return "right"
    return None


def _direction(side: str) -> tuple[int, int]:
    return {
        "top": (1, 0),
        "bottom": (-1, 0),
        "left": (0, 1),
        "right": (0, -1),
    }[side]


def _slots(side: str, h: int, w: int) -> list[tuple[int, int]]:
    if side == "top":
        return [(0, c) for c in range(1, w - 1)]
    if side == "bottom":
        return [(h - 1, c) for c in range(1, w - 1)]
    if side == "left":
        return [(r, 0) for r in range(1, h - 1)]
    return [(r, w - 1) for r in range(1, h - 1)]


def _full_path(emitter: tuple[int, int, int, str], h: int, w: int) -> list[tuple[int, int]]:
    r, c, _, side = emitter
    dr, dc = _direction(side)
    path: list[tuple[int, int]] = []
    r += dr
    c += dc
    while 0 <= r < h and 0 <= c < w:
        path.append((r, c))
        r += dr
        c += dc
    return path


def _trace(
    emitters: list[tuple[int, int, int, str]],
    blockers: set[tuple[int, int]],
    h: int,
    w: int,
    *,
    stop_at_blockers: bool = True,
) -> tuple[
    dict[tuple[int, int], list[tuple[str, int]]],
    list[dict[str, Any]],
    set[tuple[int, int]],
]:
    proposals: dict[tuple[int, int], list[tuple[str, int]]] = defaultdict(list)
    rays: list[dict[str, Any]] = []
    reached_blockers: set[tuple[int, int]] = set()
    for r, c, color, side in emitters:
        dr, dc = _direction(side)
        rr, cc = r + dr, c + dc
        path: list[tuple[int, int]] = []
        blocker = None
        while 0 <= rr < h and 0 <= cc < w:
            if stop_at_blockers and (rr, cc) in blockers:
                blocker = (rr, cc)
                reached_blockers.add(blocker)
                break
            path.append((rr, cc))
            proposals[(rr, cc)].append((side, color))
            rr += dr
            cc += dc
        rays.append({"emitter": (r, c, color, side), "path": path, "blocker": blocker})
    return proposals, rays, reached_blockers


def _analyze(grid: list[list[int]]) -> tuple[dict[str, Any], list[str]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {}, ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (5 <= h <= 10 and 5 <= w <= 10):
        errors.append(f"grid dimensions outside 5..10 contract: {h}x{w}")
    values = {value for row in grid for value in row}
    invalid = sorted(values - set(range(10)))
    if invalid:
        errors.append(f"ARC colors must be 0..9, found {invalid}")
    if 0 not in values:
        errors.append("background color 0 is absent")

    corners = ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1))
    if any(grid[r][c] != 0 for r, c in corners):
        errors.append("all four corners must remain background")

    emitters: list[tuple[int, int, int, str]] = []
    blockers: set[tuple[int, int]] = set()
    distractors: list[tuple[int, int, int]] = []
    border_gray = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            side = _side((r, c), h, w)
            if value == 5:
                blockers.add((r, c))
                if side is not None or (r, c) in corners:
                    border_gray += 1
            elif side is not None:
                emitters.append((r, c, value, side))
            elif (r, c) not in corners:
                distractors.append((r, c, value))
    if border_gray:
        errors.append("gray blockers must be interior, never on the border")

    n_emitters = len(emitters)
    n_blockers = len(blockers)
    n_distractors = len(distractors)
    if not (2 <= n_emitters <= 6):
        errors.append(f"expected 2..6 border emitters, got {n_emitters}")
    if not (1 <= n_blockers <= 3):
        errors.append(f"expected 1..3 gray blockers, got {n_blockers}")
    if not (0 <= n_distractors <= 2):
        errors.append(f"expected 0..2 interior distractors, got {n_distractors}")

    emitter_colors = [color for _, _, color, _ in emitters]
    distractor_colors = [color for _, _, color in distractors]
    if len(set(emitter_colors)) != len(emitter_colors):
        errors.append("emitter colors must be distinct")
    if len(set(distractor_colors)) != len(distractor_colors):
        errors.append("distractor colors must be distinct")
    if set(emitter_colors) & set(distractor_colors):
        errors.append("distractor colors must be disjoint from emitter colors")

    side_counts = Counter(side for *_, side in emitters)
    if emitters and not (set(side_counts) & VERTICAL_SIDES):
        errors.append("at least one top/bottom emitter is required")
    if emitters and not (set(side_counts) & HORIZONTAL_SIDES):
        errors.append("at least one left/right emitter is required")

    proposals, rays, reached_blockers = _trace(emitters, blockers, h, w)
    if blockers and not reached_blockers:
        errors.append("at least one gray blocker must stop a ray")
    blocked_rays = sum(ray["blocker"] is not None for ray in rays)
    full_rays = sum(ray["blocker"] is None for ray in rays)
    if rays and blocked_rays == 0:
        errors.append("at least one ray must be stopped by a blocker")
    if rays and full_rays == 0:
        errors.append("at least one ray must reach the opposite border")
    if any(len(ray["path"]) == 0 for ray in rays):
        errors.append("every emitter must paint at least one cell before stopping")

    crossings = {
        cell: hits
        for cell, hits in proposals.items()
        if any(side in VERTICAL_SIDES for side, _ in hits)
        and any(side in HORIZONTAL_SIDES for side, _ in hits)
    }
    if not crossings:
        errors.append("at least one unblocked vertical/horizontal ray crossing is required")

    higher_vertical = False
    higher_horizontal = False
    for hits in crossings.values():
        winner_side, _ = max(hits, key=lambda item: item[1])
        if winner_side in VERTICAL_SIDES:
            higher_vertical = True
        else:
            higher_horizontal = True

    reached_cells = set(proposals)
    traversed_distractors = [
        (r, c, color) for r, c, color in distractors if (r, c) in reached_cells
    ]

    analysis = {
        "grid_h": h,
        "grid_w": w,
        "n_emitters": n_emitters,
        "n_blockers": n_blockers,
        "n_distractors": n_distractors,
        "emitters": emitters,
        "blockers": blockers,
        "distractors": distractors,
        "side_counts": dict(side_counts),
        "proposals": proposals,
        "rays": rays,
        "reached_blockers": reached_blockers,
        "blocked_rays": blocked_rays,
        "full_rays": full_rays,
        "crossings": crossings,
        "higher_vertical": higher_vertical,
        "higher_horizontal": higher_horizontal,
        "traversed_distractors": traversed_distractors,
        "palette_size": len(values),
    }
    return analysis, errors


def observe_overrides(grid):
    analysis, errors = _analyze(grid)
    if errors:
        return {}
    return {name: analysis[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis, errors = _analyze(grid)
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be easy, medium, hard, or None")
    if not errors and isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        for name in AXES:
            if requested.get(name) is not None and requested[name] != analysis[name]:
                errors.append(
                    f"{name} requested {requested[name]!r}, observed {analysis[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    analysis, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (analysis["grid_h"], analysis["grid_w"]) not in {(5, 5), (6, 6), (6, 7)}:
        reasons.append("dimensions are outside the observed canonical profiles")
    if analysis["n_emitters"] != 4:
        reasons.append("canonical inputs have exactly four emitters")
    if analysis["side_counts"] != {"top": 1, "bottom": 1, "left": 1, "right": 1}:
        reasons.append("canonical inputs have exactly one emitter on each side")
    if analysis["n_blockers"] not in (1, 2):
        reasons.append("canonical inputs have one or two blockers")
    if analysis["n_distractors"] not in (0, 1):
        reasons.append("canonical inputs have zero or one interior distractor")
    expected_palette = 6 + analysis["n_distractors"]
    if analysis["palette_size"] != expected_palette:
        reasons.append("canonical palette linkage is 0 + four emitters + gray + distractors")
    return reasons


def _side_plan(n_emitters: int, profile: int) -> list[str]:
    pairs = (("top", "left"), ("bottom", "right"), ("top", "right"), ("bottom", "left"))
    plan = list(pairs[profile % len(pairs)])
    for side in SIDES:
        if len(plan) >= n_emitters:
            break
        if side not in plan:
            plan.append(side)
    cycle = SIDES[profile % 4 :] + SIDES[: profile % 4]
    while len(plan) < n_emitters:
        plan.append(cycle[(len(plan) - 4) % 4])
    return plan


def _choose_emitters(
    h: int,
    w: int,
    n_emitters: int,
    profile: int,
    rng,
) -> list[tuple[int, int, int, str]]:
    plan = _side_plan(n_emitters, profile)
    chosen_cells: list[tuple[int, int, str]] = []
    by_side = Counter(plan)
    for side in SIDES:
        count = by_side[side]
        if not count:
            continue
        candidates = _slots(side, h, w)
        if count > len(candidates):
            raise ValueError(f"{count} emitters do not fit on {side} side")
        rng.shuffle(candidates)
        for r, c in candidates[:count]:
            chosen_cells.append((r, c, side))

    palette = list(EMITTER_COLORS)
    rng.shuffle(palette)
    colors = palette[:n_emitters]
    desired_orientation = "vertical" if profile % 2 == 0 else "horizontal"
    target_index = next(
        i
        for i, (_, _, side) in enumerate(chosen_cells)
        if (side in VERTICAL_SIDES) == (desired_orientation == "vertical")
    )
    max_color = max(colors)
    max_index = colors.index(max_color)
    colors[target_index], colors[max_index] = colors[max_index], colors[target_index]
    return [
        (r, c, color, side)
        for (r, c, side), color in zip(chosen_cells, colors)
    ]


def _before_or_at(
    path: list[tuple[int, int]], target: tuple[int, int]
) -> set[tuple[int, int]]:
    if target not in path:
        return set()
    return set(path[: path.index(target) + 1])


def _construct_grid(
    *,
    h: int,
    w: int,
    n_emitters: int,
    n_blockers: int,
    n_distractors: int,
    profile: int,
    rng,
) -> list[list[int]]:
    if n_emitters + n_distractors > len(EMITTER_COLORS):
        raise ValueError("emitters and distractors require distinct non-gray colors")

    for _ in range(240):
        emitters = _choose_emitters(h, w, n_emitters, profile, rng)
        vertical = [emitter for emitter in emitters if emitter[3] in VERTICAL_SIDES]
        horizontal = [emitter for emitter in emitters if emitter[3] in HORIZONTAL_SIDES]
        if not vertical or not horizontal:
            continue

        desired_vertical = profile % 2 == 0
        primary_pool = vertical if desired_vertical else horizontal
        secondary_pool = horizontal if desired_vertical else vertical
        primary = max(primary_pool, key=lambda e: e[2])
        secondary = min(secondary_pool, key=lambda e: e[2])
        crossing = (secondary[0], primary[1]) if primary[3] in VERTICAL_SIDES else (primary[0], secondary[1])

        protected: set[tuple[int, int]] = set()
        protected |= _before_or_at(_full_path(primary, h, w), crossing)
        protected |= _before_or_at(_full_path(secondary, h, w), crossing)

        interior = [
            (r, c)
            for r in range(1, h - 1)
            for c in range(1, w - 1)
            if (r, c) != crossing
        ]
        blocker_sets = list(combinations(interior, n_blockers))
        rng.shuffle(blocker_sets)
        chosen = None
        chosen_trace = None
        for candidate in blocker_sets:
            blockers = set(candidate)
            proposals, rays, reached = _trace(emitters, blockers, h, w)
            if not reached or not any(ray["blocker"] is None for ray in rays):
                continue
            crossing_hits = proposals.get(crossing, [])
            if not (
                any(side in VERTICAL_SIDES for side, _ in crossing_hits)
                and any(side in HORIZONTAL_SIDES for side, _ in crossing_hits)
            ):
                continue
            chosen = blockers
            chosen_trace = (proposals, rays, reached)
            break
        if chosen is None or chosen_trace is None:
            continue
        blockers = chosen
        proposals, rays, reached = chosen_trace

        used_colors = {color for _, _, color, _ in emitters}
        distractor_palette = [color for color in EMITTER_COLORS if color not in used_colors]
        candidate_cells = [
            cell
            for cell in proposals
            if 0 < cell[0] < h - 1
            and 0 < cell[1] < w - 1
            and cell not in blockers
            and cell != crossing
        ]
        rng.shuffle(candidate_cells)
        if len(candidate_cells) < n_distractors or len(distractor_palette) < n_distractors:
            continue

        grid = full_grid(h, w, 0)
        for r, c, color, _ in emitters:
            grid[r][c] = color
        for r, c in blockers:
            grid[r][c] = 5
        rng.shuffle(distractor_palette)
        for (r, c), color in zip(candidate_cells[:n_distractors], distractor_palette):
            grid[r][c] = color

        if not self_check(grid):
            return grid
    raise ValueError("could not construct a valid emitter/blocker scene after 240 attempts")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            return _draw_from_degenerate(texture)
        raise ValueError(f"unsupported texture override: {texture!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = sample_index % 5
    canonical_dims = ((6, 6), (5, 5), (6, 7))
    if profile < 3:
        desired_h, desired_w = canonical_dims[profile]
    elif difficulty == "easy":
        desired_h, desired_w = ((7, 7), (7, 8))[profile - 3]
    elif difficulty == "hard":
        desired_h, desired_w = ((10, 10), (10, 9))[profile - 3]
    else:
        desired_h, desired_w = ((8, 9), (9, 8))[profile - 3]

    desired_counts = (
        (4, 1, 0),
        (4, 1, 1),
        (4, 2, 0),
        (5, 3, 2),
        (3, 2, 1),
    )[profile]
    h = _profiled_int(ctx, "grid_h", 5, 10, desired_h)
    w = _profiled_int(ctx, "grid_w", 5, 10, desired_w)
    n_emitters = _profiled_int(ctx, "n_emitters", 2, 6, desired_counts[0])
    n_blockers = _profiled_int(ctx, "n_blockers", 1, 3, desired_counts[1])
    n_distractors = _profiled_int(ctx, "n_distractors", 0, 2, desired_counts[2])
    rng = ctx.draw_rng("layout")
    return _construct_grid(
        h=h,
        w=w,
        n_emitters=n_emitters,
        n_blockers=n_blockers,
        n_distractors=n_distractors,
        profile=profile,
        rng=rng,
    )


def _predict(
    grid: list[list[int]],
    *,
    blockers_stop: bool = True,
    precedence: str = "max",
    preserve_distractors: bool = False,
    border_only: bool = False,
) -> list[list[int]]:
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot predict malformed scene: " + "; ".join(errors))
    h, w = analysis["grid_h"], analysis["grid_w"]
    out = full_grid(h, w, 0)
    for r, c in analysis["blockers"]:
        out[r][c] = 5
    for r, c, color, _ in analysis["emitters"]:
        out[r][c] = color
    if border_only:
        return out
    proposals, _, _ = _trace(
        analysis["emitters"],
        analysis["blockers"],
        h,
        w,
        stop_at_blockers=blockers_stop,
    )
    for (r, c), hits in proposals.items():
        if out[r][c] != 0:
            continue
        if precedence == "min":
            color = min(color for _, color in hits)
        elif precedence == "vertical":
            vertical = [color for side, color in hits if side in VERTICAL_SIDES]
            color = max(vertical) if vertical else max(color for _, color in hits)
        elif precedence == "horizontal":
            horizontal = [color for side, color in hits if side in HORIZONTAL_SIDES]
            color = max(horizontal) if horizontal else max(color for _, color in hits)
        else:
            color = max(color for _, color in hits)
        out[r][c] = color
    if preserve_distractors:
        for r, c, color in analysis["distractors"]:
            out[r][c] = color
    return out


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} is malformed: {errors[0]}")
        elif _predict(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} disagrees with the declared max-precedence rule")
    if reasons:
        return reasons

    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "rays ignore gray blockers": lambda grid: _predict(grid, blockers_stop=False),
        "crossings keep the smaller color": lambda grid: _predict(grid, precedence="min"),
        "vertical rays always win crossings": lambda grid: _predict(grid, precedence="vertical"),
        "horizontal rays always win crossings": lambda grid: _predict(grid, precedence="horizontal"),
        "interior colored cells are preserved": lambda grid: _predict(grid, preserve_distractors=True),
        "only border emitters and blockers are copied": lambda grid: _predict(grid, border_only=True),
    }
    for name, rival in rivals.items():
        consistent = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if consistent and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not refute rival rule: {name}")
    return reasons


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid):
        analysis, errors = _analyze(grid)
        if errors:
            return False
        if name == "all_four_sides":
            return set(analysis["side_counts"]) == set(SIDES)
        if name == "blocked_ray":
            return analysis["blocked_rays"] > 0
        if name == "full_length_ray":
            return analysis["full_rays"] > 0
        if name == "unequal_color_crossing":
            return bool(analysis["crossings"])
        if name == "higher_vertical":
            return analysis["higher_vertical"]
        if name == "higher_horizontal":
            return analysis["higher_horizontal"]
        if name == "traversed_distractor":
            return bool(analysis["traversed_distractors"])
        if name == "multiple_blockers":
            return analysis["n_blockers"] >= 2
        raise KeyError(name)

    return predicate


SEMANTIC_WITNESSES = {
    name: _witness(name)
    for name in (
        "all_four_sides",
        "blocked_ray",
        "full_length_ray",
        "unequal_color_crossing",
        "higher_vertical",
        "higher_horizontal",
        "traversed_distractor",
        "multiple_blockers",
    )
}


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(6, 6, 0)
    if name == "no_emitters":
        grid[2][2] = 5
    elif name == "corner_emitter":
        grid[0][0] = 4
        grid[2][2] = 5
        grid[2][5] = 7
    elif name == "blocker_on_border":
        grid[0][2] = 5
        grid[2][0] = 3
        grid[5][3] = 8
    elif name == "all_rays_blocked":
        grid[0][2] = 3
        grid[2][0] = 7
        grid[1][2] = 5
        grid[2][1] = 5
    elif name == "interior_emitters_only":
        grid[2][2] = 3
        grid[3][3] = 7
        grid[1][1] = 5
    else:
        raise ValueError(f"unknown degenerate texture: {name!r}")
    return grid
