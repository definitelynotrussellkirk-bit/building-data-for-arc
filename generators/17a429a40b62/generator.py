"""Generator for ARC task 17a429a40b62 — two-row legend remap.

The first two rows form aligned source/destination color pairs.  Only source
colors below the legend are replaced; destination colors already present in
the body remain unchanged.  A scheduled canonical-morphology prior keeps the
official linked shape manifold visible in every difficulty band, while other
draws vary legend placement, pair count, palette role, and body morphology to
rebut fixed-position and fixed-template shortcuts.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "17a429a40b62"
VERSION = "2.0.0"
TASK_ID = "17a429a40b62"
RULE_HASH = "1127d1e98497"
SUMMARY = (
    "Rows 0 and 1 contain two or three aligned, disjoint source/destination "
    "color pairs. Every source appears at least twice below the legend and is "
    "recolored to its paired destination; any destination colors already in "
    "the body remain unchanged. Every fourth ordinary sample uses the exact "
    "canonical role-normalized body morphology (with width 8 or 9)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is color 0",
    "rows 0 and 1 contain exactly 2 or 3 aligned nonzero legend pairs",
    "source colors and destination colors are each distinct and mutually disjoint",
    "every source color occurs at least twice below row 1, so every mapping fires",
    "body cells contain only background, source colors, and up to two destination-color unchanged witnesses",
    "ordinary sample indices divisible by four reproduce a canonical color-role-normalized input signature",
]

PALETTE_PROFILES = ("no_gray", "gray_source", "gray_destination")
LEGEND_LAYOUTS = ("canonical_even", "shifted_even", "scattered")
BODY_STYLES = ("canonical_template", "striped", "scattered")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 5 or difficulty-aware rng 5..10",
        "valid": "5..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 8..9 or difficulty-aware rng 6..12",
        "valid": "6..12",
    },
    "n_pairs": {
        "type": "int",
        "default": "scheduled canonical 3 or rng 2..3",
        "valid": "2..3",
    },
    "unchanged_body_colors": {
        "type": "int",
        "default": "scheduled canonical 0 or rng 0..2",
        "valid": "0..2",
    },
    "palette_profile": {
        "type": "enum",
        "default": "rng over whether gray is absent, a source, or a destination",
        "valid": PALETTE_PROFILES,
    },
    "legend_layout": {
        "type": "enum",
        "default": "scheduled canonical-even or rng over three observable layouts",
        "valid": LEGEND_LAYOUTS,
    },
    "body_style": {
        "type": "enum",
        "default": "scheduled canonical template or rng over canonical/striped/scattered",
        "valid": BODY_STYLES,
    },
}

_CANONICAL_SOURCE_CELLS = (
    (2, 1, 0), (2, 3, 1), (2, 5, 2),
    (3, 0, 2), (3, 2, 1), (3, 4, 0),
    (4, 2, 0), (4, 3, 2), (4, 6, 1),
)


def _band_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (5, 6), (6, 8)
    if difficulty == "hard":
        return (8, 10), (9, 12)
    return (6, 8), (7, 10)


def _requested_int(overrides: dict, name: str) -> int | None:
    value = overrides.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} override must be an integer") from exc


def _draw_palette(rng, profile: str, n_pairs: int) -> tuple[list[int], list[int]]:
    needed = 2 * n_pairs
    if profile == "no_gray":
        colors = list(random_palette(rng, needed, exclude=(5,)))
        return colors[:n_pairs], colors[n_pairs:]

    other = list(random_palette(rng, needed - 1, exclude=(5,)))
    if profile == "gray_source":
        srcs = [5, *other[: n_pairs - 1]]
        dsts = other[n_pairs - 1 :]
    elif profile == "gray_destination":
        srcs = other[:n_pairs]
        dsts = [5, *other[n_pairs:]]
    else:  # guarded by GenCtx, retained as a local assertion boundary
        raise ValueError(f"unknown palette_profile {profile!r}")
    rng.shuffle(srcs)
    rng.shuffle(dsts)
    return srcs, dsts


def _legend_columns(rng, width: int, n_pairs: int, layout: str) -> list[int]:
    canonical = tuple(range(0, 2 * n_pairs, 2))
    shifted = tuple(range(1, 1 + 2 * n_pairs, 2))
    if layout == "canonical_even":
        return list(canonical)
    if layout == "shifted_even":
        return list(shifted)
    fixed_even_columns = {0, 2, 4}
    choices = [
        combo
        for combo in combinations(range(width), n_pairs)
        if combo not in (canonical, shifted)
        # A scattered lesson must refute a solver that always reads only
        # columns 0/2/4.  Exclude the remaining two-pair subsets of that
        # shortcut codomain, not merely the exact canonical tuple.
        and not set(combo).issubset(fixed_even_columns)
    ]
    if not choices:
        raise ValueError(
            f"grid_w={width} leaves no scattered legend layout for {n_pairs} pairs"
        )
    return list(rng.choice(choices))


def _free_body_cells(grid) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0
    ]


def _add_unchanged_witnesses(grid, rng, dsts: list[int], count: int, *, parity_only: bool = False) -> None:
    if count == 0:
        return
    free = _free_body_cells(grid)
    if parity_only:
        free = [(r, c) for r, c in free if (r + c) % 2 == 0]
    if len(free) < count:
        raise ValueError("not enough body cells for unchanged destination witnesses")
    rng.shuffle(free)
    for color, (r, c) in zip(dsts[:count], free):
        grid[r][c] = color


def _paint_canonical_template(grid, srcs: list[int]) -> None:
    if len(srcs) != 3 or len(grid) < 5 or len(grid[0]) < 7:
        raise ValueError("canonical_template requires n_pairs=3, grid_h>=5, grid_w>=7")
    for r, c, source_index in _CANONICAL_SOURCE_CELLS:
        if (r, c) == (4, 3) and len(grid[0]) == 8:
            source_index = 0
        grid[r][c] = srcs[source_index]


def _paint_striped(grid, rng, srcs: list[int], dsts: list[int], unchanged_count: int) -> None:
    cells = [
        (r, c)
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if (r + c) % 2 == 0
    ]
    needed = 2 * len(srcs) + unchanged_count
    if len(cells) < needed:
        raise ValueError("grid too small for striped body witnesses")
    rng.shuffle(cells)
    cursor = 0
    for color in dsts[:unchanged_count]:
        r, c = cells[cursor]
        grid[r][c] = color
        cursor += 1
    source_stream = [color for color in srcs for _ in range(2)]
    rng.shuffle(source_stream)
    for color in source_stream:
        r, c = cells[cursor]
        grid[r][c] = color
        cursor += 1
    while cursor < len(cells):
        r, c = cells[cursor]
        grid[r][c] = rng.choice(srcs)
        cursor += 1


def _paint_scattered(
    grid,
    rng,
    srcs: list[int],
    dsts: list[int],
    unchanged_count: int,
    difficulty: str | None,
) -> None:
    all_cells = [(r, c) for r in range(2, len(grid)) for c in range(len(grid[0]))]
    minimum = 2 * len(srcs) + unchanged_count
    density = {"easy": 0.25, "hard": 0.45}.get(difficulty, 0.35)
    total = min(len(all_cells) - 1, max(minimum, round(len(all_cells) * density)))
    even = [p for p in all_cells if (p[0] + p[1]) % 2 == 0]
    odd = [p for p in all_cells if (p[0] + p[1]) % 2 == 1]
    first = rng.choice(even)
    second = rng.choice(odd)
    remaining = [p for p in all_cells if p not in (first, second)]
    selected = [first, second, *rng.sample(remaining, total - 2)]
    rng.shuffle(selected)

    source_stream = [color for color in srcs for _ in range(2)]
    source_stream.extend(rng.choice(srcs) for _ in range(total - unchanged_count - len(source_stream)))
    rng.shuffle(source_stream)
    for color, (r, c) in zip(source_stream, selected):
        grid[r][c] = color

    used = len(source_stream)
    for color, (r, c) in zip(dsts[:unchanged_count], selected[used:]):
        grid[r][c] = color

    canonical_positions = {(r, c) for r, c, _ in _CANONICAL_SOURCE_CELLS}
    source_positions = {
        (r, c)
        for r in range(2, len(grid))
        for c, value in enumerate(grid[r])
        if value in srcs
    }
    if len(srcs) == 3 and source_positions == canonical_positions:
        replacement = next(p for p in all_cells if p not in selected)
        old = next(iter(source_positions))
        grid[replacement[0]][replacement[1]] = grid[old[0]][old[1]]
        grid[old[0]][old[1]] = 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket rule remains output authority."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    episode_slot = int(sample_index) % 4
    canonical_prior = not overrides and episode_slot == 0
    requested_pairs = _requested_int(overrides, "n_pairs")
    requested_width = _requested_int(overrides, "grid_w")
    requested_style = overrides.get("body_style")

    if requested_pairs is not None and not 2 <= requested_pairs <= 3:
        raise ValueError("n_pairs override outside declared range 2..3")
    if requested_style == "canonical_template" and requested_pairs not in (None, 3):
        raise ValueError("canonical_template is incompatible with n_pairs=2")
    if requested_style == "canonical_template" and requested_width is not None and requested_width < 7:
        raise ValueError("canonical_template requires grid_w>=7")

    (h_lo, h_hi), (w_lo, w_hi) = _band_ranges(difficulty)
    if overrides.get("grid_h") is not None:
        height = ctx.draw_int("grid_h", 5, 10)
    elif canonical_prior:
        height = ctx.draw_int("grid_h", 5, 5)
    else:
        height = ctx.draw_int("grid_h", h_lo, h_hi)

    if overrides.get("grid_w") is not None:
        width = ctx.draw_int("grid_w", 6, 12)
    elif canonical_prior:
        width = ctx.draw_int("grid_w", 8, 9)
    elif requested_style == "canonical_template":
        width = ctx.draw_int("grid_w", max(7, w_lo), w_hi)
    else:
        width = ctx.draw_int("grid_w", w_lo, w_hi)

    if overrides.get("n_pairs") is not None:
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    elif canonical_prior or requested_style == "canonical_template":
        n_pairs = ctx.draw_int("n_pairs", 3, 3)
    else:
        n_pairs = ctx.draw_int("n_pairs", 2, 3)

    if requested_style == "canonical_template" and (n_pairs != 3 or width < 7):
        raise ValueError("canonical_template requires n_pairs=3 and grid_w>=7")

    if overrides.get("unchanged_body_colors") is not None:
        unchanged_count = ctx.draw_int("unchanged_body_colors", 0, 2)
    elif canonical_prior:
        unchanged_count = ctx.draw_int("unchanged_body_colors", 0, 0)
    elif not overrides and episode_slot % 2 == 1:
        # Every three consecutive normal demonstrations include an unchanged
        # destination witness, refuting a bidirectional color-swap shortcut.
        unchanged_count = ctx.draw_int("unchanged_body_colors", 1, 2)
    else:
        unchanged_count = ctx.draw_int("unchanged_body_colors", 0, 2)

    if overrides.get("palette_profile") is not None:
        palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)
    elif canonical_prior:
        # The three canonical examples themselves cover gray-as-source,
        # gray-as-destination, and gray-absent roles, so retain all three.
        palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)
    else:
        palette_profile = ctx.draw_choice("palette_profile", PALETTE_PROFILES)

    if overrides.get("legend_layout") is not None:
        legend_layout = ctx.draw_choice("legend_layout", LEGEND_LAYOUTS)
    elif canonical_prior:
        legend_layout = ctx.draw_choice("legend_layout", ("canonical_even",))
    elif not overrides:
        # Slots 1..3 are always noncanonical. Therefore any three consecutive
        # demonstrations contain a direct fixed-position shortcut rebuttal.
        legend_layout = ctx.draw_choice("legend_layout", ("shifted_even", "scattered"))
    else:
        legend_layout = ctx.draw_choice("legend_layout", LEGEND_LAYOUTS)

    allowed_styles = list(BODY_STYLES)
    if n_pairs != 3 or width < 7:
        allowed_styles.remove("canonical_template")
    if overrides.get("body_style") is not None:
        body_style = ctx.draw_choice("body_style", BODY_STYLES)
        if body_style not in allowed_styles:
            raise ValueError(
                f"body_style={body_style!r} is incompatible with n_pairs={n_pairs}, grid_w={width}"
            )
    elif canonical_prior:
        body_style = ctx.draw_choice("body_style", ("canonical_template",))
    else:
        body_style = ctx.draw_choice("body_style", tuple(allowed_styles))

    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)
    srcs, dsts = _draw_palette(rng, palette_profile, n_pairs)
    columns = _legend_columns(rng, width, n_pairs, legend_layout)
    for column, source, destination in zip(columns, srcs, dsts):
        grid[0][column] = source
        grid[1][column] = destination

    if body_style == "canonical_template":
        _paint_canonical_template(grid, srcs)
        _add_unchanged_witnesses(grid, rng, dsts, unchanged_count)
    elif body_style == "striped":
        _paint_striped(grid, rng, srcs, dsts, unchanged_count)
    else:
        _paint_scattered(grid, rng, srcs, dsts, unchanged_count, difficulty)
    return grid


def _analysis(grid) -> dict:
    height = len(grid)
    width = len(grid[0])
    row0 = {c for c, value in enumerate(grid[0]) if value != 0}
    row1 = {c for c, value in enumerate(grid[1]) if value != 0}
    columns = sorted(row0 & row1)
    srcs = [grid[0][c] for c in columns]
    dsts = [grid[1][c] for c in columns]
    source_set = set(srcs)
    destination_set = set(dsts)
    source_positions = {
        (r, c)
        for r in range(2, height)
        for c, value in enumerate(grid[r])
        if value in source_set
    }
    body_nonzero_positions = {
        (r, c)
        for r in range(2, height)
        for c, value in enumerate(grid[r])
        if value != 0
    }
    canonical_positions = {(r, c) for r, c, _ in _CANONICAL_SOURCE_CELLS}
    if len(srcs) == 3 and source_positions == canonical_positions:
        body_style = "canonical_template"
    elif body_nonzero_positions and all((r + c) % 2 == 0 for r, c in body_nonzero_positions):
        body_style = "striped"
    else:
        body_style = "scattered"

    canonical_columns = list(range(0, 2 * len(columns), 2))
    shifted_columns = list(range(1, 1 + 2 * len(columns), 2))
    if columns == canonical_columns:
        legend_layout = "canonical_even"
    elif columns == shifted_columns:
        legend_layout = "shifted_even"
    else:
        legend_layout = "scattered"

    if 5 in source_set and 5 not in destination_set:
        palette_profile = "gray_source"
    elif 5 in destination_set and 5 not in source_set:
        palette_profile = "gray_destination"
    elif 5 not in source_set and 5 not in destination_set:
        palette_profile = "no_gray"
    else:
        palette_profile = "ambiguous_gray"

    body_destination_colors = {
        value
        for row in grid[2:]
        for value in row
        if value in destination_set
    }
    source_counts = {
        source: sum(value == source for row in grid[2:] for value in row)
        for source in srcs
    }
    unknown_body_colors = {
        value
        for row in grid[2:]
        for value in row
        if value not in ({0} | source_set | destination_set)
    }
    return {
        "row0_columns": row0,
        "row1_columns": row1,
        "columns": columns,
        "srcs": srcs,
        "dsts": dsts,
        "n_pairs": len(columns),
        "unchanged_body_colors": len(body_destination_colors),
        "palette_profile": palette_profile,
        "legend_layout": legend_layout,
        "body_style": body_style,
        "source_counts": source_counts,
        "unknown_body_colors": unknown_body_colors,
        "body_nonzero_positions": body_nonzero_positions,
    }


def observe_overrides(grid) -> dict[str, int | str]:
    info = _analysis(grid)
    return {
        "n_pairs": info["n_pairs"],
        "unchanged_body_colors": info["unchanged_body_colors"],
        "palette_profile": info["palette_profile"],
        "legend_layout": info["legend_layout"],
        "body_style": info["body_style"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed legend lessons and accept every canonical input."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cell values must be integer ARC colors 0..9"]
    if len(grid) < 5:
        return ["grid needs at least five rows for a two-row legend and body witnesses"]
    if width < 6:
        return ["grid needs width at least six for two or three separated legend pairs"]

    errors: list[str] = []
    info = _analysis(grid)
    if info["row0_columns"] != info["row1_columns"]:
        errors.append("legend source and destination columns must align exactly")
    if info["n_pairs"] not in (2, 3):
        errors.append(f"expected 2 or 3 legend pairs, got {info['n_pairs']}")
    if len(set(info["srcs"])) != len(info["srcs"]):
        errors.append("source legend colors must be distinct")
    if len(set(info["dsts"])) != len(info["dsts"]):
        errors.append("destination legend colors must be distinct")
    if set(info["srcs"]) & set(info["dsts"]):
        errors.append("source and destination color sets must be disjoint")
    if info["unknown_body_colors"]:
        errors.append(
            "body contains colors absent from the legend: "
            + repr(sorted(info["unknown_body_colors"]))
        )
    for source, count in info["source_counts"].items():
        if count < 2:
            errors.append(f"source color {source} appears only {count} time(s) below the legend")
    if info["unchanged_body_colors"] > 2:
        errors.append("body may contain at most two distinct destination-color witnesses")
    body_cells = [value for row in grid[2:] for value in row]
    if 0 not in body_cells:
        errors.append("body must retain at least one background cell")

    requested = dict((meta or {}).get("overrides", {}))
    requested.update({
        key: value
        for key, value in (meta or {}).items()
        if key in AXES and key not in requested
    })
    observed = observe_overrides(grid)
    for axis, expected in requested.items():
        if axis in observed and expected is not None and observed[axis] != expected:
            errors.append(
                f"requested {axis}={expected!r} but returned grid shows {observed[axis]!r}"
            )
    return errors
