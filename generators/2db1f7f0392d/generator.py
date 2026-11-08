"""Generator for arc_additional_puzzles_21_set12_bundle:E83.

The color-9 cells are walls.  Every other nonzero cell is a seed.  A seed
paints its own color horizontally and vertically through every non-wall cell
until a color-9 wall or the grid edge stops that ray.  Walls are unchanged.

Normal draws deliberately contain:
* two differently colored seeds in different wall-bounded components;
* an anchor seed with visible cells in all four cardinal directions;
* a blocker seed with an immediately blocked direction;
* an unseeded component and off-ray background cells.

Those features make the generated lesson distinguish cardinal rays from the
main plausible shortcuts: full compartment fill, horizontal-only or
vertical-only painting, first-seed-only painting, and rays that ignore walls.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2db1f7f0392d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # honest exact axes + structural/semantic teaching contract
RULE_HASH = "d90c04209e45"  # sha256[:12] of whitespace-normalized authority

SUMMARY = (
    "A 0-background grid is enclosed by color-9 walls and partitioned by "
    "additional color-9 dividers. Exactly two single-cell seeds, in distinct "
    "non-{0,9} colors and different wall-bounded components, each emit four "
    "cardinal rays in their own color. A ray paints every non-wall cell until "
    "the grid edge or a color-9 wall stops it; walls remain 9. Generated scenes "
    "also contain off-ray zeros and an empty compartment so full-region and "
    "wall-ignoring shortcuts disagree visibly."
)

INVARIANTS = [
    "the complete outer border is color 9 and at least one interior wall remains",
    "exactly two distinct singleton seed colors occur, one seed per non-wall component",
    "every seed has at least one paintable cardinal cell, so the output is non-identity",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

DIVIDER_LAYOUTS = ("vertical_split", "horizontal_split", "cross")
PALETTE_KINDS = ("low", "high", "mixed")

# All declared axes are finite, exact, consumed through GenCtx, and recoverable
# by observe_overrides().  Negative fixtures are tests, never ordinary axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware 10..15",
        "valid": "10..15",
    },
    "divider_layout": {
        "type": "str",
        "default": "rng exact",
        "valid": "|".join(DIVIDER_LAYOUTS),
    },
    "palette_kind": {
        "type": "str",
        "default": "canonical anchor or rng exact",
        "valid": "|".join(PALETTE_KINDS),
    },
}

# Five of eight sample-index residues preserve the exact canonical (h, w,
# palette) profiles.  The remaining residues expand scale while every layout,
# seed position, and wall placement still varies by the keyed RNG.
_CANONICAL_PROFILES = (
    (9, 11, (2, 3)),
    (8, 10, (2, 4)),
    (9, 12, (3, 5)),
    (10, 10, (4, 6)),
    (9, 11, (5, 7)),
)
SCHEDULE_PROFILES = tuple(range(8))


def schedule_profile(seed, sample_index, difficulty=None):
    """Stable curriculum residue; independent of seed and difficulty."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _scheduled_profile(sample_index: int):
    residue = int(sample_index) % len(SCHEDULE_PROFILES)
    return _CANONICAL_PROFILES[residue] if residue < len(_CANONICAL_PROFILES) else None


def _axis_int(ctx, overrides, name: str, default_lo: int, default_hi: int, valid_lo: int, valid_hi: int) -> int:
    # Explicit overrides must remain valid across every difficulty band.  The
    # ordinary path may use a narrower or singleton scheduled range while still
    # recording the exact requested axis through GenCtx.
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _dimensions(ctx, overrides, difficulty, profile) -> tuple[int, int]:
    if profile is not None:
        default_h = (profile[0], profile[0])
        default_w = (profile[1], profile[1])
    elif difficulty == "easy":
        default_h, default_w = (8, 9), (10, 12)
    elif difficulty == "hard":
        default_h, default_w = (10, 12), (12, 15)
    else:
        default_h, default_w = (9, 11), (11, 14)
    h = _axis_int(ctx, overrides, "grid_h", *default_h, 8, 12)
    w = _axis_int(ctx, overrides, "grid_w", *default_w, 10, 15)
    return h, w


def _palette_kind(ctx, overrides, profile) -> str:
    if overrides.get("palette_kind") is not None:
        return ctx.draw_choice("palette_kind", PALETTE_KINDS)
    if profile is not None:
        lo, hi = profile[2]
        scheduled = "low" if hi <= 4 else "high" if lo >= 5 else "mixed"
        return ctx.draw_choice("palette_kind", (scheduled,))
    return ctx.draw_choice("palette_kind", PALETTE_KINDS)


def _seed_colors(ctx, kind: str, profile) -> tuple[int, int]:
    if profile is not None and ctx.overrides.get("palette_kind") is None:
        return tuple(profile[2])
    rng = ctx.draw_rng("seed_colors")
    if kind == "low":
        return tuple(rng.sample((1, 2, 3, 4), 2))
    if kind == "high":
        return tuple(rng.sample((5, 6, 7, 8), 2))
    return (rng.choice((1, 2, 3, 4)), rng.choice((5, 6, 7, 8)))


def _paint_border(grid: list[list[int]]) -> None:
    h, w = len(grid), len(grid[0])
    for row in range(h):
        grid[row][0] = 9
        grid[row][w - 1] = 9
    for col in range(w):
        grid[0][col] = 9
        grid[h - 1][col] = 9


def _paint_walls(grid: list[list[int]], layout: str, rng) -> None:
    """Build three or four wall-bounded components at canonical scale."""
    h, w = len(grid), len(grid[0])
    _paint_border(grid)

    if layout == "vertical_split":
        split_left = bool(rng.randrange(2))
        if split_left:
            divider_col = rng.choice(list(range(3, w - 4 + 1)))
        else:
            divider_col = rng.choice(list(range(4, w - 3)))
        cut_row = rng.choice(list(range(3, h - 3)))
        for row in range(h):
            grid[row][divider_col] = 9
        cols = range(0, divider_col + 1) if split_left else range(divider_col, w)
        for col in cols:
            grid[cut_row][col] = 9
        return

    if layout == "horizontal_split":
        split_top = bool(rng.randrange(2))
        if split_top:
            divider_row = rng.choice(list(range(3, h - 3 + 1)))
        else:
            divider_row = rng.choice(list(range(4, h - 2)))
        cut_col = rng.choice(list(range(3, w - 3)))
        for col in range(w):
            grid[divider_row][col] = 9
        rows = range(0, divider_row + 1) if split_top else range(divider_row, h)
        for row in rows:
            grid[row][cut_col] = 9
        return

    if layout != "cross":
        raise ValueError(f"unsupported divider_layout: {layout!r}")
    divider_row = rng.choice(list(range(3, h - 3)))
    divider_col = rng.choice(list(range(4, w - 4 + 1)))
    for col in range(w):
        grid[divider_row][col] = 9
    for row in range(h):
        grid[row][divider_col] = 9


def _nonwall_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 9 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 9
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _seed_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]


def _has_four_open_neighbours(grid: list[list[int]], row: int, col: int) -> bool:
    return all(grid[row + dr][col + dc] == 0 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))


def _has_open_neighbour(grid: list[list[int]], row: int, col: int) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        0 <= row + dr < h and 0 <= col + dc < w and grid[row + dr][col + dc] == 0
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def _interior_wall_with_space_beyond(grid: list[list[int]], row: int, col: int) -> bool:
    """A cardinal ray from (row,col) reaches an interior wall with open space beyond."""
    h, w = len(grid), len(grid[0])
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        while 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 9:
            rr += dr
            cc += dc
        if not (0 <= rr < h and 0 <= cc < w):
            continue
        if rr in (0, h - 1) or cc in (0, w - 1):
            continue
        br, bc = rr + dr, cc + dc
        if 0 <= br < h and 0 <= bc < w and grid[br][bc] != 9:
            return True
    return False


def _place_seeds(grid: list[list[int]], colors: tuple[int, int], rng) -> bool:
    components = _nonwall_components(grid)
    if len(components) < 3:
        return False

    anchor_options: list[tuple[int, list[tuple[int, int]]]] = []
    blocker_options: list[tuple[int, list[tuple[int, int]]]] = []
    for index, component in enumerate(components):
        anchors = [(r, c) for r, c in component if _has_four_open_neighbours(grid, r, c)]
        blockers = [
            (r, c)
            for r, c in component
            if _has_open_neighbour(grid, r, c)
            and _interior_wall_with_space_beyond(grid, r, c)
            and any(grid[r + dr][c + dc] == 9 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        ]
        if anchors:
            anchor_options.append((index, anchors))
        if blockers:
            blocker_options.append((index, blockers))

    rng.shuffle(anchor_options)
    anchor_options.sort(key=lambda item: len(components[item[0]]), reverse=True)
    for anchor_index, anchors in anchor_options:
        candidates = [(idx, cells) for idx, cells in blocker_options if idx != anchor_index]
        if not candidates:
            continue
        blocker_index, blockers = rng.choice(candidates)
        ar, ac = rng.choice(anchors)
        br, bc = rng.choice(blockers)
        grid[ar][ac] = colors[0]
        grid[br][bc] = colors[1]
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, shortcut-rebutting input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _scheduled_profile(sample_index)
    height, width = _dimensions(ctx, overrides, difficulty, profile)
    layout = ctx.draw_choice("divider_layout", DIVIDER_LAYOUTS)
    palette_kind = _palette_kind(ctx, overrides, profile)
    colors = _seed_colors(ctx, palette_kind, profile)
    layout_rng = ctx.draw_rng("layout")

    # Geometry is retried only within this deterministic keyed stream.  Every
    # successful ordinary draw satisfies the same semantic witness contract.
    for _attempt in range(80):
        grid = full_grid(height, width, 0)
        _paint_walls(grid, layout, layout_rng)
        if not _place_seeds(grid, colors, layout_rng):
            continue
        if not _generated_semantic_errors(grid):
            return grid
    raise RuntimeError(
        f"could not build a semantic {layout} scene at {height}x{width} "
        f"for seed={seed}, sample_index={sample_index}"
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not (8 <= height <= 12 and 10 <= width <= 15):
        errors.append(f"dimensions {height}x{width} outside supported 8..12 x 10..15")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color")
        return {"errors": errors}

    if any(grid[0][col] != 9 or grid[height - 1][col] != 9 for col in range(width)):
        errors.append("top and bottom borders must be entirely color 9")
    if any(grid[row][0] != 9 or grid[row][width - 1] != 9 for row in range(height)):
        errors.append("left and right borders must be entirely color 9")
    interior_walls = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 9
    ]
    if not interior_walls:
        errors.append("at least one interior color-9 divider is required")

    seeds = _seed_cells(grid)
    if len(seeds) != 2:
        errors.append(f"expected exactly two singleton seeds, found {len(seeds)}")
    seed_colors = [value for _row, _col, value in seeds]
    if len(set(seed_colors)) != len(seed_colors):
        errors.append("the two seeds must have distinct colors")
    for color in set(seed_colors):
        count = sum(value == color for row in grid for value in row)
        if count != 1:
            errors.append(f"seed color {color} appears {count} times in the input; expected one singleton")

    components = _nonwall_components(grid)
    if len(components) < 2:
        errors.append("walls do not separate the grid into at least two non-wall components")
    component_of = {cell: index for index, component in enumerate(components) for cell in component}
    seeded_components = [component_of.get((row, col)) for row, col, _value in seeds]
    if len(seeded_components) == 2 and seeded_components[0] == seeded_components[1]:
        errors.append("both seeds lie in the same wall-bounded component")
    for index, component in enumerate(components):
        count = sum(grid[row][col] not in (0, 9) for row, col in component)
        if count > 1:
            errors.append(f"component {index} contains {count} seeds; expected at most one")
    for row, col, value in seeds:
        if not _has_open_neighbour(grid, row, col):
            errors.append(f"seed {(row, col, value)} has no paintable cardinal neighbour")

    return {
        "errors": sorted(set(errors)),
        "height": height,
        "width": width,
        "seeds": seeds,
        "components": components,
        "seeded_components": seeded_components,
        "interior_walls": interior_walls,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid structural grammar; accepts every canonical input."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold stays inside the same structural task grammar."""
    return self_check(grid)


def _full_interior_rows(grid: list[list[int]]) -> list[int]:
    return [row for row in range(1, len(grid) - 1) if all(value == 9 for value in grid[row])]


def _full_interior_cols(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    return [col for col in range(1, w - 1) if all(grid[row][col] == 9 for row in range(h))]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    full_rows = _full_interior_rows(grid)
    full_cols = _full_interior_cols(grid)
    if full_rows and full_cols:
        layout = "cross"
    elif full_cols:
        layout = "vertical_split"
    elif full_rows:
        layout = "horizontal_split"
    else:
        raise ValueError("could not recover divider_layout from wall geometry")
    colors = sorted(value for _row, _col, value in analysis["seeds"])
    palette_kind = "low" if colors[-1] <= 4 else "high" if colors[0] >= 5 else "mixed"
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "divider_layout": layout,
        "palette_kind": palette_kind,
    }


def _paint_rays(grid: list[list[int]], directions) -> list[list[int]]:
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row, col, color in _seed_cells(grid):
        for dr, dc in directions:
            rr, cc = row + dr, col + dc
            while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 9:
                output[rr][cc] = color
                rr += dr
                cc += dc
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent test mirror; canonical Racket remains the output authority."""
    return _paint_rays(grid, ((-1, 0), (1, 0), (0, -1), (0, 1)))


def _rival_horizontal_only(grid):
    return _paint_rays(grid, ((0, -1), (0, 1)))


def _rival_vertical_only(grid):
    return _paint_rays(grid, ((-1, 0), (1, 0)))


def _rival_first_seed_only(grid):
    output = [row[:] for row in grid]
    seeds = _seed_cells(grid)
    if not seeds:
        return output
    row, col, color = seeds[0]
    height, width = len(grid), len(grid[0])
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = row + dr, col + dc
        while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 9:
            output[rr][cc] = color
            rr += dr
            cc += dc
    return output


def _rival_fill_seeded_compartments(grid):
    output = [row[:] for row in grid]
    for component in _nonwall_components(grid):
        colors = [grid[row][col] for row, col in component if grid[row][col] not in (0, 9)]
        if len(colors) == 1:
            for row, col in component:
                output[row][col] = colors[0]
    return output


def _rival_ignore_walls(grid):
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for row, col, color in _seed_cells(grid):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, col + dc
            while 0 <= rr < height and 0 <= cc < width:
                if grid[rr][cc] == 0:
                    output[rr][cc] = color
                rr += dr
                cc += dc
    return output


def _rival_global_first_color_fill(grid):
    output = [row[:] for row in grid]
    seeds = _seed_cells(grid)
    if not seeds:
        return output
    color = seeds[0][2]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "first_seed_only": _rival_first_seed_only,
    "fill_seeded_compartments": _rival_fill_seeded_compartments,
    "ignore_walls": _rival_ignore_walls,
    "global_first_color_fill": _rival_global_first_color_fill,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_four_directions(grid) -> bool:
    return any(_has_four_open_neighbours(grid, row, col) for row, col, _value in _seed_cells(grid))


def _witness_all_seeds_active(grid) -> bool:
    truth = rule_mirror(grid)
    for row, col, color in _seed_cells(grid):
        if not any(
            0 <= row + dr < len(grid)
            and 0 <= col + dc < len(grid[0])
            and truth[row + dr][col + dc] == color
            and grid[row + dr][col + dc] == 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        ):
            return False
    return True


def _witness_off_ray_background(grid) -> bool:
    components = _nonwall_components(grid)
    for component in components:
        seeds = [(row, col) for row, col in component if grid[row][col] not in (0, 9)]
        if len(seeds) != 1:
            continue
        sr, sc = seeds[0]
        if any(grid[row][col] == 0 and row != sr and col != sc for row, col in component):
            return True
    return False


def _witness_empty_component(grid) -> bool:
    return any(all(grid[row][col] == 0 for row, col in component) for component in _nonwall_components(grid))


def _witness_interior_wall_stop(grid) -> bool:
    return any(_interior_wall_with_space_beyond(grid, row, col) for row, col, _value in _seed_cells(grid))


def _witness_zero_length_direction(grid) -> bool:
    return any(
        any(grid[row + dr][col + dc] == 9 for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        for row, col, _value in _seed_cells(grid)
    )


SEMANTIC_WITNESSES = {
    "four_cardinal_directions": _witness_four_directions,
    "every_seed_is_active": _witness_all_seeds_active,
    "off_ray_background_remains": _witness_off_ray_background,
    "empty_component_remains_empty": _witness_empty_component,
    "interior_wall_stops_ray": _witness_interior_wall_stop,
    "immediately_blocked_direction": _witness_zero_length_direction,
}

WITNESS_RIVALS = {
    "four_cardinal_directions": ["horizontal_only", "vertical_only"],
    "every_seed_is_active": ["first_seed_only"],
    "off_ray_background_remains": ["fill_seeded_compartments"],
    "empty_component_remains_empty": ["global_first_color_fill"],
    "interior_wall_stops_ray": ["ignore_walls"],
    "immediately_blocked_direction": ["ignore_walls"],
}


def _generated_semantic_errors(grid) -> list[str]:
    reasons = strict_canonical_like(grid)
    if reasons:
        return reasons
    for name, witness in SEMANTIC_WITNESSES.items():
        if not witness(grid):
            reasons.append(f"missing semantic witness: {name}")
    truth = rule_mirror(grid)
    if truth == grid:
        reasons.append("canonical transformation is identity")
    for name, rival in SEMANTIC_RIVALS.items():
        if rival(grid) == truth:
            reasons.append(f"rival '{name}' is not falsified by this draw")
    return sorted(set(reasons))


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when any named plausible rival survives all demos."""
    reasons: list[str] = []
    prepared: list[tuple[list[list[int]], dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = strict_canonical_like(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the task grammar: {'; '.join(errors)}")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the cardinal-ray rule")
            continue
        prepared.append((demo["output"], {name: rival(demo["input"]) for name, rival in SEMANTIC_RIVALS.items()}))

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is malformed")
        return sorted(set(reasons))
    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is outside the task grammar: {'; '.join(query_errors)}")
        return sorted(set(reasons))
    query_truth = rule_mirror(query["input"])

    for name, rival in SEMANTIC_RIVALS.items():
        survives = all(outputs[name] == expected for expected, outputs in prepared)
        if survives and rival(query["input"]) != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demonstration but answers the query differently"
            )
    return sorted(set(reasons))
