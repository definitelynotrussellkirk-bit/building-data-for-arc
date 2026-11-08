"""Generator for S23_M1 — rotate only the marked lattice tiles.

Full color-9 rows/columns partition the input into equal square tiles.  In
all tiles, color 2 is the motif and color 3 is only a control marker.  The
Racket authority recolors every motif to 8, rotates a tile 90 degrees
clockwise iff that tile contains a marker, removes markers, and preserves the
color-9 lattice.

Ordinary draws include both marker branches and multiple motif sizes. Seven
scene roles supply six demonstrations and one query: an unrestricted canonical
phase, two single-marker off-center phases, two double-marker phases, and two
triple-marker phases. Every role witness survives a single query holdout.
Single-marker phases preserve canonical scale and symmetric motifs; the other
phases teach direction, multiple markers, and nonalternating tile decisions.
"""
from __future__ import annotations

from collections import deque
from functools import partial
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1ee7274bdbb0"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "a23915e769b9"
EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 0.30
LESSON_SCHEDULE_PERIOD = 7
SCHEDULE_PROFILES = (
    "canonical_open", "single_offcenter_a", "single_offcenter_b",
    "double_marker_a", "double_marker_b", "triple_marker_a", "triple_marker_b",
)
_MARKER_SCHEDULE = (1, 1, 1, 2, 2, 3, 3)

SUMMARY = (
    "Full color-9 rows/columns split the input into equal square tiles. "
    "Color-2 cells are the motif. A tile containing any color-3 marker rotates "
    "its motif 90 degrees clockwise; an unmarked tile keeps it in place. "
    "The output recolors motifs to 8, removes markers, and preserves dividers."
)

INVARIANTS = [
    "the input uses only colors {0,2,3,9}",
    "single full color-9 rows/columns form a uniform lattice of square tiles",
    "every tile contains 1..6 color-2 motif cells and every motif changes under clockwise rotation",
    "marked tiles use one common marker count in 1..3; unmarked tiles contain no color 3",
    "every ordinary/canonical scene contains at least one marked and one unmarked tile",
    "at least two motif sizes occur, with no fixed location for the differing size",
]

# These are negative fixtures for defect-lint mutation checks, not lawful AXES.
DEGENERATE_TEXTURES = ("no_dividers", "no_twos", "all_rotated")

AXES = {
    "tile_size": {
        "type": "int",
        "default": "single-marker phase=3; otherwise easy=3, medium=3..4, hard=4..5",
        "valid": "3..5",
    },
    "n_tile_rows": {
        "type": "int",
        "default": "single-marker phase=1; otherwise easy=1, medium=1..2, hard=2..3",
        "valid": "1..3",
    },
    "n_tile_cols": {
        "type": "int",
        "default": "single-marker phase=3; otherwise easy/medium=3, hard=3..4",
        "valid": "2..4",
    },
    "shape_size": {
        "type": "int",
        "default": "anchor: single-marker/easy=2..5; medium=2..6; hard=3..6",
        "valid": "1..6",
    },
    "rotate_flag": {
        "type": "bool",
        "default": "keyed boolean for the top-left anchor tile",
        "valid": "false|true",
    },
    "n_flag_cells": {
        "type": "int",
        "default": "sample_index cycles through 1,1,1,2,2,3,3 in every band; exact override wins",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _rotate_cw(cells: set[tuple[int, int]], size: int) -> set[tuple[int, int]]:
    return {(c, size - 1 - r) for r, c in cells}


def _rotate_ccw(cells: set[tuple[int, int]], size: int) -> set[tuple[int, int]]:
    return {(size - 1 - c, r) for r, c in cells}


def _rotate_180(cells: set[tuple[int, int]], size: int) -> set[tuple[int, int]]:
    return {(size - 1 - r, size - 1 - c) for r, c in cells}


def _flip_h(cells: set[tuple[int, int]], size: int) -> set[tuple[int, int]]:
    return {(r, size - 1 - c) for r, c in cells}


def _flip_v(cells: set[tuple[int, int]], size: int) -> set[tuple[int, int]]:
    return {(size - 1 - r, c) for r, c in cells}


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(cells)


def _transform_distinguishing(cells: set[tuple[int, int]], size: int) -> bool:
    """True when clockwise rotation differs from the common rival transforms."""
    clockwise = _rotate_cw(cells, size)
    rivals = (
        cells,
        _rotate_ccw(cells, size),
        _rotate_180(cells, size),
        _flip_h(cells, size),
        _flip_v(cells, size),
    )
    return all(clockwise != rival for rival in rivals)


def _sample_mask(
    rng,
    size: int,
    count: int,
    *,
    connected: bool | None,
    distinguishing: bool = True,
    accept: Callable[[set[tuple[int, int]]], bool] | None = None,
) -> set[tuple[int, int]]:
    """Sample exact-size motifs, with finite recovery from rejected proposals.

    Growing a connected motif avoids the rare-subset failure of rejection-only
    sampling for sparse 5x5 tiles. The exhaustive fallback guarantees a result
    whenever the requested finite class is nonempty, even for an unlucky RNG.
    """
    if not 1 <= count <= min(6, size * size - 1):
        raise ValueError(f"shape_size={count} is invalid for tile_size={size}")
    if connected is False and count == 1:
        raise ValueError("a one-cell motif cannot be disconnected")
    all_cells = [(r, c) for r in range(size) for c in range(size)]

    def admissible(cells):
        if connected is not None and _connected(cells) != connected:
            return False
        valid_transform = (
            _transform_distinguishing(cells, size)
            if distinguishing else _rotate_cw(cells, size) != cells
        )
        return valid_transform and (accept is None or accept(cells))

    for _ in range(1024):
        if connected is True:
            cells = {rng.choice(all_cells)}
            while len(cells) < count:
                frontier = sorted(
                    {
                        (r + dr, c + dc)
                        for r, c in cells
                        for dr, dc in _CARDINAL
                        if 0 <= r + dr < size and 0 <= c + dc < size
                    }
                    - cells
                )
                cells.add(rng.choice(frontier))
        else:
            cells = set(rng.sample(all_cells, count))
        if admissible(cells):
            return cells

    # At the declared maximum this visits only C(25, 6) = 177100 subsets.
    # Reservoir sampling selects from all feasible masks without storing them.
    from itertools import combinations

    selected = None
    accepted = 0
    for candidate in combinations(all_cells, count):
        cells = set(candidate)
        if admissible(cells):
            accepted += 1
            if rng.randrange(accepted) == 0:
                selected = cells
    if selected is not None:
        return selected
    raise ValueError(
        f"no feasible motif: tile={size}, count={count}, "
        f"connected={connected}, distinguishing={distinguishing}"
    )


def _segments(length: int, dividers: list[int]) -> list[tuple[int, int]]:
    bounds: list[tuple[int, int]] = []
    previous = -1
    for divider in [*dividers, length]:
        if divider - previous <= 1:
            return []
        bounds.append((previous + 1, divider))
        previous = divider
    return bounds


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"], "tiles": [], "facts": {}}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty first row"], "tiles": [], "facts": {}}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"], "tiles": [], "facts": {}}
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")

    palette = {value for row in grid for value in row}
    bad_colors = sorted(palette - {0, 2, 3, 9})
    if bad_colors:
        errors.append(f"colors outside {{0,2,3,9}}: {bad_colors}")

    divider_rows = [
        r for r in range(height) if all(grid[r][c] == 9 for c in range(width))
    ]
    divider_cols = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]
    if not divider_cols:
        errors.append("no full-height color-9 divider column")

    row_bounds = _segments(height, divider_rows)
    col_bounds = _segments(width, divider_cols)
    if not row_bounds:
        errors.append("divider rows are consecutive or leave an empty tile row")
    if not col_bounds:
        errors.append("divider columns are consecutive or leave an empty tile column")
    if errors:
        return {
            "errors": errors,
            "tiles": [],
            "facts": {},
            "divider_rows": divider_rows,
            "divider_cols": divider_cols,
        }

    row_sizes = {end - start for start, end in row_bounds}
    col_sizes = {end - start for start, end in col_bounds}
    if len(row_sizes) != 1 or len(col_sizes) != 1 or row_sizes != col_sizes:
        errors.append(
            f"divider lattice does not form equal square tiles: "
            f"row sizes={sorted(row_sizes)}, col sizes={sorted(col_sizes)}"
        )
    tile_size = next(iter(row_sizes)) if len(row_sizes) == 1 else 0
    if not 3 <= tile_size <= 5:
        errors.append(f"tile_size {tile_size} outside declared 3..5")
    tile_rows, tile_cols = len(row_bounds), len(col_bounds)
    if not 1 <= tile_rows <= 3:
        errors.append(f"n_tile_rows {tile_rows} outside declared 1..3")
    if not 2 <= tile_cols <= 4:
        errors.append(f"n_tile_cols {tile_cols} outside declared 2..4")

    divider_row_set, divider_col_set = set(divider_rows), set(divider_cols)
    stray_nines = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 9 and r not in divider_row_set and c not in divider_col_set
    ]
    if stray_nines:
        errors.append(f"color 9 appears inside a tile at {stray_nines[0]}")

    tiles: list[dict[str, Any]] = []
    for tile_r, (r0, r1) in enumerate(row_bounds):
        for tile_c, (c0, c1) in enumerate(col_bounds):
            twos = {
                (r - r0, c - c0)
                for r in range(r0, r1)
                for c in range(c0, c1)
                if grid[r][c] == 2
            }
            threes = {
                (r - r0, c - c0)
                for r in range(r0, r1)
                for c in range(c0, c1)
                if grid[r][c] == 3
            }
            if not 1 <= len(twos) <= 6:
                errors.append(
                    f"tile ({tile_r},{tile_c}) has {len(twos)} motif cells; expected 1..6"
                )
            elif _rotate_cw(twos, tile_size) == twos:
                errors.append(
                    f"tile ({tile_r},{tile_c}) motif is clockwise-rotation invariant"
                )
            if len(threes) > 3:
                errors.append(
                    f"tile ({tile_r},{tile_c}) has {len(threes)} markers; expected 0..3"
                )
            tiles.append(
                {
                    "tile_row": tile_r,
                    "tile_col": tile_c,
                    "r0": r0,
                    "c0": c0,
                    "twos": twos,
                    "threes": threes,
                }
            )

    marked = [tile for tile in tiles if tile["threes"]]
    unmarked = [tile for tile in tiles if not tile["threes"]]
    if not marked:
        errors.append("no marked tile; the clockwise branch is absent")
    if not unmarked:
        errors.append("no unmarked tile; the copy branch is absent")
    marker_counts = {len(tile["threes"]) for tile in marked}
    if len(marker_counts) > 1:
        errors.append(f"marked tiles use inconsistent marker counts: {sorted(marker_counts)}")
    motif_sizes = {len(tile["twos"]) for tile in tiles}
    if len(motif_sizes) < 2:
        errors.append("all tiles have the same motif size (count-only shortcut)")

    facts = {
        "tile_size": tile_size,
        "n_tile_rows": tile_rows,
        "n_tile_cols": tile_cols,
        "shape_size": len(tiles[0]["twos"]) if tiles else None,
        "rotate_flag": bool(tiles and tiles[0]["threes"]),
        "n_flag_cells": next(iter(marker_counts)) if len(marker_counts) == 1 else None,
        "marked_tiles": len(marked),
        "unmarked_tiles": len(unmarked),
        "motif_sizes": sorted(motif_sizes),
    }
    return {
        "errors": errors,
        "tiles": tiles,
        "facts": facts,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_bounds": row_bounds,
        "col_bounds": col_bounds,
        "height": height,
        "width": width,
    }


def observe_overrides(grid) -> dict[str, int | bool]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "tile_size": facts["tile_size"],
        "n_tile_rows": facts["n_tile_rows"],
        "n_tile_cols": facts["n_tile_cols"],
        "shape_size": facts["shape_size"],
        "rotate_flag": facts["rotate_flag"],
        "n_flag_cells": facts["n_flag_cells"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = {}
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if not isinstance(requested, dict):
            requested = {}
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in observed and observed[axis] != value:
            errors.append(f"{axis} requested {value!r}, realized {observed[axis]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    facts = analysis["facts"]
    if (facts["tile_size"], facts["n_tile_rows"], facts["n_tile_cols"]) != (3, 1, 3):
        reasons.append("canonical lattice is exactly three 3x3 tiles in one row")
    if facts["n_flag_cells"] != 1:
        reasons.append("canonical marked tiles contain exactly one color-3 marker")
    if any(not 2 <= len(tile["twos"]) <= 5 for tile in analysis["tiles"]):
        reasons.append("canonical motif sizes lie in 2..5")
    return reasons


def _marked_rotation_visible(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        tile["threes"] and _rotate_cw(tile["twos"], analysis["facts"]["tile_size"]) != tile["twos"]
        for tile in analysis["tiles"]
    )


def _unmarked_copy_control(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        not tile["threes"] and _rotate_cw(tile["twos"], analysis["facts"]["tile_size"]) != tile["twos"]
        for tile in analysis["tiles"]
    )


def _mixed_marker_control(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["facts"]["marked_tiles"] > 0
        and analysis["facts"]["unmarked_tiles"] > 0
    )


def _motif_size_distractor(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and len(analysis["facts"]["motif_sizes"]) >= 2


def _marker_not_answer(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    size = analysis["facts"]["tile_size"]
    for tile in analysis["tiles"]:
        if not tile["threes"]:
            continue
        rotated = _rotate_cw(tile["twos"], size)
        if tile["threes"] - rotated and rotated - tile["threes"]:
            return True
    return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "marked_rotation_visible": _marked_rotation_visible,
    "unmarked_copy_control": _unmarked_copy_control,
    "mixed_marker_control": _mixed_marker_control,
    "motif_size_distractor": _motif_size_distractor,
    "marker_not_answer": _marker_not_answer,
}


def _banded_int(ctx, label: str, band_lo: int, band_hi: int, global_lo: int, global_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, global_lo, global_hi)
    return ctx.draw_int(label, band_lo, band_hi)


def _draw_sizes(rng, n_tiles: int, anchor_size: int, *, low: int, high: int) -> list[int]:
    sizes = [anchor_size] + [rng.randint(low, high) for _ in range(1, n_tiles)]
    if len(set(sizes)) == 1:
        alternatives = [value for value in range(low, high + 1) if value != anchor_size]
        if not alternatives:
            alternatives = [value for value in range(1, 7) if value != anchor_size]
        sizes[rng.randrange(1, n_tiles)] = rng.choice(alternatives)
    return sizes


def _place_markers(
    rng,
    motif: set[tuple[int, int]],
    size: int,
    count: int,
    *,
    forbidden=frozenset(),
) -> set[tuple[int, int]]:
    empty = {(r, c) for r in range(size) for c in range(size)} - motif - set(forbidden)
    if len(empty) < count:
        raise ValueError(
            f"shape_size={len(motif)} leaves only {len(empty)} allowed cells "
            f"for n_flag_cells={count}"
        )
    rotated = _rotate_cw(motif, size)
    marker_only = sorted(empty - rotated)
    if not marker_only:
        raise ValueError("marked motif leaves no marker cell outside its rotated answer")

    # A motif/forbidden cell in the answer is already protected. Otherwise keep
    # one answer cell unavailable to markers, including for singleton motifs.
    if not rotated - empty:
        if len(empty) <= count:
            raise ValueError(
                f"n_flag_cells={count} leaves no uncovered rotated-answer cell"
            )
        empty.remove(rng.choice(sorted(rotated)))
    rng.shuffle(marker_only)
    first = marker_only[0]
    remaining = sorted(empty - {first})
    rng.shuffle(remaining)
    return {first, *remaining[:count - 1]}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"Unknown override key(s): {', '.join(sorted(unknown))}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        return _draw_from_degenerate(texture, ctx.draw_rng("degenerate"))

    band = difficulty or "medium"
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    core = phase < 3
    teaching = phase != 0
    scheduled_markers = _MARKER_SCHEDULE[phase]
    if core or band == "easy":
        ts = _banded_int(ctx, "tile_size", 3, 3, 3, 5)
        tile_rows = _banded_int(ctx, "n_tile_rows", 1, 1, 1, 3)
        tile_cols = _banded_int(ctx, "n_tile_cols", 3, 3, 2, 4)
        anchor_size = _banded_int(ctx, "shape_size", 2, 5, 1, 6)
        other_low, other_high = 2, 5
    elif band == "hard":
        ts = _banded_int(ctx, "tile_size", 4, 5, 3, 5)
        tile_rows = _banded_int(ctx, "n_tile_rows", 2, 3, 1, 3)
        tile_cols = _banded_int(ctx, "n_tile_cols", 3, 4, 2, 4)
        anchor_size = _banded_int(ctx, "shape_size", 3, 6, 1, 6)
        other_low, other_high = 2, 6
    else:
        ts = _banded_int(ctx, "tile_size", 3, 4, 3, 5)
        tile_rows = _banded_int(ctx, "n_tile_rows", 1, 2, 1, 3)
        tile_cols = _banded_int(ctx, "n_tile_cols", 3, 3, 2, 4)
        anchor_size = _banded_int(ctx, "shape_size", 2, 6, 1, 6)
        other_low, other_high = 2, 6
    marker_count = _banded_int(ctx, "n_flag_cells", scheduled_markers, scheduled_markers, 1, 3)
    anchor_marked = ctx.draw_choice("rotate_flag", (False, True))

    n_tiles = tile_rows * tile_cols
    flag_rng = ctx.draw_rng("tile_flags")
    flags = [anchor_marked] + [flag_rng.random() < 0.5 for _ in range(1, n_tiles)]
    if len(set(flags)) == 1:
        flags[flag_rng.randrange(1, n_tiles)] = not anchor_marked
    alternating = [anchor_marked if i % 2 == 0 else not anchor_marked for i in range(n_tiles)]
    if teaching and n_tiles >= 3 and flags == alternating:
        choices = [i for i in range(1, n_tiles)
                   if len(set(flags[:i] + [not flags[i]] + flags[i + 1:])) == 2]
        chosen = flag_rng.choice(choices)
        flags[chosen] = not flags[chosen]
    center_witness_tile = ctx.draw_rng("offcenter_control").choice(
        [i for i, marked in enumerate(flags) if marked]
    ) if teaching else None

    size_rng = ctx.draw_rng("motif_sizes")
    motif_sizes = _draw_sizes(
        size_rng,
        n_tiles,
        anchor_size,
        low=other_low,
        high=other_high,
    )

    height = tile_rows * ts + tile_rows - 1
    width = tile_cols * ts + tile_cols - 1
    grid = full_grid(height, width, 0)
    for divider_index in range(1, tile_rows):
        row = divider_index * (ts + 1) - 1
        for col in range(width):
            grid[row][col] = 9
    for divider_index in range(1, tile_cols):
        col = divider_index * (ts + 1) - 1
        for row in range(height):
            grid[row][col] = 9

    for index in range(n_tiles):
        tile_r, tile_c = divmod(index, tile_cols)
        r0, c0 = tile_r * (ts + 1), tile_c * (ts + 1)
        topology = (
            None if core else
            (True if motif_sizes[index] == 1 else ctx.draw_rng(f"topology_{index}").choice((False, True)))
        )
        forbidden = {(ts // 2, ts // 2)} if index == center_witness_tile else set()
        mask_rng = ctx.draw_rng(f"motif_{index}")

        def marker_layout_fits(cells):
            try:
                _place_markers(ctx.draw_rng(f"markers_{index}"), cells, ts, marker_count,
                               forbidden=forbidden)
            except ValueError:
                return False
            return True

        motif = _sample_mask(
            mask_rng, ts, motif_sizes[index], connected=topology,
            distinguishing=not core, accept=marker_layout_fits if flags[index] else None,
        )
        for r, c in motif:
            grid[r0 + r][c0 + c] = 2
        if flags[index]:
            markers = _place_markers(
                ctx.draw_rng(f"markers_{index}"), motif, ts, marker_count, forbidden=forbidden
            )
            for r, c in markers:
                grid[r0 + r][c0 + c] = 3
    return grid


def _draw_from_degenerate(name: str, rng):
    if name == "no_dividers":
        grid = full_grid(3, 3, 0)
        for r, c in ((0, 0), (0, 1), (1, 0)):
            grid[r][c] = 2
        grid[2][2] = 3
        return grid
    if name == "no_twos":
        grid = full_grid(3, 7, 0)
        for r in range(3):
            grid[r][3] = 9
        grid[0][0] = 3
        return grid
    if name == "all_rotated":
        grid = full_grid(3, 7, 0)
        for r in range(3):
            grid[r][3] = 9
        left = _sample_mask(rng, 3, 3, connected=True)
        right = _sample_mask(rng, 3, 4, connected=False)
        for base, motif in ((0, left), (4, right)):
            for r, c in motif:
                grid[r][base + c] = 2
            marker = next(iter({(r, c) for r in range(3) for c in range(3)} - motif))
            grid[marker[0]][base + marker[1]] = 3
        return grid
    raise ValueError(name)


def _render_candidate(grid, transform: str) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    size = analysis["facts"]["tile_size"]
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row in analysis["divider_rows"]:
        for col in range(analysis["width"]):
            output[row][col] = 9
    for col in analysis["divider_cols"]:
        for row in range(analysis["height"]):
            output[row][col] = 9
    transforms = {
        "copy": lambda cells: set(cells),
        "cw": lambda cells: _rotate_cw(cells, size),
        "ccw": lambda cells: _rotate_ccw(cells, size),
        "180": lambda cells: _rotate_180(cells, size),
        "flip_h": lambda cells: _flip_h(cells, size),
        "flip_v": lambda cells: _flip_v(cells, size),
    }
    for index, tile in enumerate(analysis["tiles"]):
        marked = bool(tile["threes"])
        if transform == "conditional_cw":
            operation = "cw" if marked else "copy"
        elif transform == "copy_all":
            operation = "copy"
        elif transform == "rotate_all_cw":
            operation = "cw"
        elif transform == "rotate_unmarked_cw":
            operation = "copy" if marked else "cw"
        elif transform.startswith("marked_"):
            operation = transform.removeprefix("marked_") if marked else "copy"
        elif transform == "center_only":
            operation = "cw" if (size // 2, size // 2) in tile["threes"] else "copy"
        elif transform == "exactly_one_marker":
            operation = "cw" if len(tile["threes"]) == 1 else "copy"
        elif transform == "single_marker_center_only":
            active = marked and (len(tile["threes"]) != 1 or (size // 2, size // 2) in tile["threes"])
            operation = "cw" if active else "copy"
        elif transform == "skip_two_markers":
            operation = "cw" if marked and len(tile["threes"]) != 2 else "copy"
        elif transform == "skip_three_markers":
            operation = "cw" if marked and len(tile["threes"]) != 3 else "copy"
        elif transform == "alternating_tiles":
            anchor_flag = bool(analysis["tiles"][0]["threes"])
            operation = "cw" if (anchor_flag if index % 2 == 0 else not anchor_flag) else "copy"
        elif transform in ("marker_pivot", "marker_cells", "one_cell_per_tile"):
            operation = "cw" if marked else "copy"
        else:
            raise ValueError(transform)
        cells = transforms[operation](tile["twos"])
        if transform == "marker_pivot" and marked:
            pr, pc = min(tile["threes"])
            cells = {(pr + c - pc, pc - r + pr) for r, c in tile["twos"]}
        elif transform == "marker_cells" and marked:
            cells = tile["threes"]
        elif transform == "one_cell_per_tile":
            cells = {min(cells)}
        for r, c in cells:
            if 0 <= r < size and 0 <= c < size:
                output[tile["r0"] + r][tile["c0"] + c] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror used only by tests and semantic auditing."""
    return _render_candidate(grid, "conditional_cw")


_CANDIDATE_RULES = (
    "conditional_cw",
    "copy_all",
    "rotate_all_cw",
    "rotate_unmarked_cw",
    "marked_ccw",
    "marked_180",
    "marked_flip_h",
    "marked_flip_v",
    "center_only",
    "exactly_one_marker",
    "single_marker_center_only",
    "skip_two_markers",
    "skip_three_markers",
    "alternating_tiles",
    "marker_pivot",
    "marker_cells",
    "one_cell_per_tile",
)

SEMANTIC_RIVALS = {name: partial(_render_candidate, transform=name)
                   for name in _CANDIDATE_RULES if name != "conditional_cw"}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "center_only", "exactly_one_marker", "single_marker_center_only", "skip_two_markers", "skip_three_markers",
    "alternating_tiles", "marker_pivot",
)}


def _refutes(grid, rival):
    analysis = _analyze(grid)
    return not analysis["errors"] and rule_mirror(grid) != SEMANTIC_RIVALS[rival](grid)


SEMANTIC_WITNESSES.update({
    "offcenter_marker_control": partial(_refutes, rival="center_only"),
    "single_offcenter_control": partial(_refutes, rival="single_marker_center_only"),
    "two_markers_control": partial(_refutes, rival="skip_two_markers"),
    "three_markers_control": partial(_refutes, rival="skip_three_markers"),
    "nonalternating_control": partial(_refutes, rival="alternating_tiles"),
    "marker_is_not_rotation_pivot": partial(_refutes, rival="marker_pivot"),
})
WITNESS_RIVALS = {
    "marked_rotation_visible": ["copy_all"],
    "unmarked_copy_control": ["rotate_all_cw"],
    "mixed_marker_control": ["rotate_unmarked_cw"],
    "motif_size_distractor": ["one_cell_per_tile"],
    "marker_not_answer": ["marker_cells"],
    "offcenter_marker_control": ["center_only"],
    "single_offcenter_control": ["single_marker_center_only"],
    "two_markers_control": ["skip_two_markers", "exactly_one_marker"],
    "three_markers_control": ["skip_three_markers", "exactly_one_marker"],
    "nonalternating_control": ["alternating_tiles"],
    "marker_is_not_rotation_pivot": ["marker_pivot"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    surviving = []
    for candidate in _CANDIDATE_RULES:
        try:
            consistent = all(
                _render_candidate(pair["input"], candidate) == pair["output"]
                for pair in demos
            )
        except Exception as exc:
            return [f"could not parse demonstration: {type(exc).__name__}: {exc}"]
        if consistent:
            surviving.append(candidate)
    if "conditional_cw" not in surviving:
        return ["demonstrations disagree with the pinned conditional-clockwise rule"]
    try:
        official_query = _render_candidate(query["input"], "conditional_cw")
    except Exception as exc:
        return [f"could not parse query: {type(exc).__name__}: {exc}"]
    if official_query != query["output"]:
        reasons.append("query output disagrees with the pinned conditional-clockwise rule")
    for candidate in surviving:
        if candidate == "conditional_cw":
            continue
        if _render_candidate(query["input"], candidate) != official_query:
            reasons.append(
                f"competing rule {candidate!r} fits every demonstration but changes the query answer"
            )
    return reasons
