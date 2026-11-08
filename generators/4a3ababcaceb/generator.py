"""Copy the strongest red motif into a marked tile, replacing that tile.

Three consecutive default draws contain a canonical-scale anchor, an explicit
shortcut counterexample, and a broad-layout example. Only four independently
observable controls are advertised. Racket remains the output authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "4a3ababcaceb"
VERSION = "3.1.0"
TASK_ID = "4a3ababcaceb"
RULE_HASH = "3617779ffc60"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "A regular lattice of 3x3 tiles separated by 9. Select the unique tile "
    "with the most red (2) cells, then REPLACE the distinct tile containing "
    "one green (3) marker with the source's red mask in cyan (8), zero elsewhere. "
    "Other tiles stay unchanged. Includes denser non-source tiles, weaker red "
    "candidates, non-red source clutter, target clutter and off-center markers."
)
INVARIANTS = [
    "rectangular integer ARC grid, with complete color-9 dividers every fourth cell",
    "all tiles are 3x3; no interior cell is color 9",
    "one distinct source has a unique positive maximum number of color-2 cells",
    "exactly one color-3 marker; its target tile contains no red cells",
    "default three-demo windows refute every named shortcut",
]
AXES = {
    "tile_rows": {"type": "int", "default": "scheduled 1..5", "valid": "1..5"},
    "tile_cols": {"type": "int", "default": "scheduled 3..6", "valid": "3..6"},
    "src_size": {"type": "int", "default": "scheduled 2..9", "valid": "2..9"},
    "marker_offset": {"type": "int", "default": "scheduled 0..8", "valid": "0..8",
                      "doc": "Row-major offset of the single green target marker."},
}
SCHEDULE_PROFILES = (0, 1, 2)
_NUISANCE = (1, 4, 5, 6, 7, 8)


def schedule_profile(seed, sample_index, difficulty=None):
    """Rotate lesson starts with seed; do not assume sample_index starts at zero."""
    return (seed + sample_index) % 3


def _draw_axis(ctx, name, lo, hi, default_lo, default_hi):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default_lo, default_hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed must be an integer and sample_index a nonnegative integer")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    row_max, col_max = {"easy": (3, 4), "hard": (5, 6)}.get(difficulty, (4, 5))
    rows = _draw_axis(ctx, "tile_rows", 1, 5, 1, 1 if profile == 0 else row_max)
    cols = _draw_axis(ctx, "tile_cols", 3, 6, 3, 3 if profile == 0 else col_max)
    src_lo, src_hi = ((3, 4), (2, 7), (2, 8))[profile]
    if profile == 0 and ctx.draw_rng("full_source_boundary").randrange(7) == 0:
        src_lo = src_hi = 9
    size = _draw_axis(ctx, "src_size", 2, 9, src_lo, src_hi)
    if overrides.get("marker_offset") is not None:
        marker = ctx.draw_int("marker_offset", 0, 8)
    elif profile == 0:
        marker = ctx.draw_int("marker_offset", 4, 4)
    elif profile == 1:
        marker = ctx.draw_choice("marker_offset", (0, 1, 2, 3, 5, 6, 7, 8))
    else:
        marker = ctx.draw_int("marker_offset", 0, 8)

    layout_rng = ctx.draw_rng("layout")
    src, target, competitor = layout_rng.sample(range(rows * cols), 3)
    if (profile == 1 and src < competitor) or (profile == 2 and src > competitor):
        src, competitor = competitor, src
    tiles = [blank_tile() for _ in range(rows * cols)]
    shape_rng = ctx.draw_rng("source_shape")
    red_offsets = shape_rng.sample(range(9), size)
    for offset in red_offsets:
        tiles[src][offset // 3][offset % 3] = 2
    palette_rng = ctx.draw_rng("nuisance_palette")
    palette = (1,) if profile in (0, 1) else _NUISANCE
    for index, tile in enumerate(tiles):
        if index in (src, target):
            continue
        rng = ctx.draw_rng(f"decoy_{index}")
        if profile == 0:
            for offset in rng.sample(range(9), 3):
                tile[offset // 3][offset % 3] = 1
        elif index == competitor:
            # Only the designated candidate is dense. Unrelated tiles should
            # not multiply multicolor objects merely to create palette variety.
            reds = set(rng.sample(range(9), size - 1))
            nuisance = palette_rng.choice(palette)
            for offset in range(9):
                tile[offset // 3][offset % 3] = (
                    2 if offset in reds else (nuisance if profile == 1 else 0)
                )
        elif rng.randrange(3) == 0:
            offset = rng.randrange(9)
            tile[offset // 3][offset % 3] = palette_rng.choice(palette)
    if profile != 0:
        # One non-red source cell makes "copy all nonzero source cells" wrong.
        empty = [offset for offset in range(9) if offset not in red_offsets]
        if empty:
            offset = ctx.draw_rng("source_noise").choice(empty)
            tiles[src][offset // 3][offset % 3] = palette_rng.choice(palette)
        # Replacement, not overlay: non-red target clutter must be erased.
        nuisance = palette_rng.choice(palette)
        tiles[target] = [[nuisance for _ in range(3)] for _ in range(3)]
    tiles[target][marker // 3][marker % 3] = 3
    return assemble_tiles([tiles[row * cols:(row + 1) * cols] for row in range(rows)])


def _structure(grid):
    """Validate before indexing; never mutate caller-owned grids."""
    if not isinstance(grid, list) or not grid or not all(isinstance(r, list) for r in grid):
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if not width or any(len(r) != width for r in grid):
        raise ValueError("grid must be rectangular and nonempty")
    if len(grid) > 30 or width > 30:
        raise ValueError("grid exceeds 30x30 ARC bounds")
    if (len(grid) + 1) % 4 or (width + 1) % 4:
        raise ValueError("lattice must consist of 3x3 tiles and one-cell dividers")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid values must be integer colors in 0..9")
            divider = r % 4 == 3 or c % 4 == 3
            if (value == 9) != divider:
                raise ValueError("incomplete divider or interior color-9 cell")
    rows, cols = (len(grid) + 1) // 4, (width + 1) // 4
    if rows * cols < 2:
        raise ValueError("source and target need distinct tiles and a divider")
    tiles = [[grid[r + i][c + j] for i in range(3) for j in range(3)]
             for r in range(0, len(grid), 4) for c in range(0, width, 4)]
    if sum(tile.count(3) for tile in tiles) != 1:
        raise ValueError("expected exactly one green target marker")
    counts = [tile.count(2) for tile in tiles]
    maximum = max(counts)
    if not maximum or counts.count(maximum) != 1:
        raise ValueError("expected a unique positive maximum red source")
    source = counts.index(maximum)
    target = next(i for i, tile in enumerate(tiles) if 3 in tile)
    if source == target or counts[target]:
        raise ValueError("target must be distinct and contain no red cells")
    return rows, cols, tiles, source, target


def self_check(grid, *, difficulty=None, meta=None):
    try:
        _structure(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """The documented equal-tile, unambiguous-source task grammar, not a palette test."""
    return self_check(grid)


def observe_overrides(grid):
    rows, cols, tiles, source, target = _structure(grid)
    return {"tile_rows": rows, "tile_cols": cols, "src_size": tiles[source].count(2),
            "marker_offset": tiles[target].index(3)}


def _render(grid, source=None, *, all_nonzero=False, overlay=False, target=None):
    _, cols, tiles, actual_source, actual_target = _structure(grid)
    source = actual_source if source is None else source
    target = actual_target if target is None else target
    out = [row[:] for row in grid]
    for offset, value in enumerate(tiles[source]):
        r, c = 4 * (target // cols) + offset // 3, 4 * (target % cols) + offset % 3
        mark = value != 0 if all_nonzero else value == 2
        if mark:
            out[r][c] = 8
        elif not overlay:
            out[r][c] = 0
    return out


def rule_mirror(grid):
    """Test-only oracle; production labels must still execute canonical Racket."""
    return _render(grid)


def _largest_tile(grid):
    _, _, tiles, _, target = _structure(grid)
    source = max((i for i in range(len(tiles)) if i != target),
                 key=lambda i: sum(v != 0 for v in tiles[i]))
    return _render(grid, source, all_nonzero=True)


def _first_red(grid):
    _, _, tiles, _, _ = _structure(grid)
    source = next(i for i, tile in enumerate(tiles) if 2 in tile)
    return _render(grid, source)


def _center_marker(grid):
    _, _, tiles, _, _ = _structure(grid)
    target = next((i for i, tile in enumerate(tiles) if tile[4] == 3), None)
    return [row[:] for row in grid] if target is None else _render(grid, target=target)


def _least_occupied_red(grid):
    _, _, tiles, _, _ = _structure(grid)
    source = min((i for i,tile in enumerate(tiles) if 2 in tile),
                 key=lambda i: sum(v != 0 for v in tiles[i]))
    return _render(grid, source)


def _purest_red(grid):
    _, _, tiles, _, _ = _structure(grid)
    source = max((i for i,tile in enumerate(tiles) if 2 in tile),
                 key=lambda i: tiles[i].count(2) / sum(v != 0 for v in tiles[i]))
    return _render(grid, source)


def _last_red(grid):
    _, _, tiles, _, _ = _structure(grid)
    return _render(grid, max(i for i,tile in enumerate(tiles) if 2 in tile))


SEMANTIC_RIVALS = {
    "largest_nonzero_tile": _largest_tile,
    "first_red_tile": _first_red,
    "copy_all_source_nonzero": lambda grid: _render(grid, all_nonzero=True),
    "overlay_target": lambda grid: _render(grid, overlay=True),
    "center_marker_only": _center_marker,
    "least_occupied_red_tile": _least_occupied_red,
    "purest_red_tile": _purest_red,
    "last_red_tile": _last_red,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "largest_nonzero_tile", "first_red_tile", "copy_all_source_nonzero", "center_marker_only",
    "least_occupied_red_tile", "purest_red_tile", "last_red_tile")}


def _refutes(grid, rival):
    return not self_check(grid) and SEMANTIC_RIVALS[rival](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "denser_decoy": lambda grid: _refutes(grid, "largest_nonzero_tile"),
    "weaker_red_before_source": lambda grid: _refutes(grid, "first_red_tile"),
    "source_nonred_clutter": lambda grid: _refutes(grid, "copy_all_source_nonzero"),
    "target_requires_erasure": lambda grid: _refutes(grid, "overlay_target"),
    "offcenter_marker": lambda grid: _refutes(grid, "center_marker_only"),
    "sparser_red_is_weaker": lambda grid: _refutes(grid, "least_occupied_red_tile"),
    "purer_red_is_weaker": lambda grid: _refutes(grid, "purest_red_tile"),
    "weaker_red_after_source": lambda grid: _refutes(grid, "last_red_tile"),
}
WITNESS_RIVALS = {
    "denser_decoy": ["largest_nonzero_tile"],
    "weaker_red_before_source": ["first_red_tile"],
    "source_nonred_clutter": ["copy_all_source_nonzero"],
    "target_requires_erasure": ["overlay_target"],
    "offcenter_marker": ["center_marker_only"],
    "sparser_red_is_weaker": ["least_occupied_red_tile"],
    "purer_red_is_weaker": ["purest_red_tile"],
    "weaker_red_after_source": ["last_red_tile"],
}


def lesson_identifiable(demos, query):
    """Finite-rival check, not a claim of uniqueness among all possible rules."""
    for pair in list(demos) + [query]:
        if self_check(pair.get("input")):
            return ["lesson includes an input outside the task grammar"]
        if pair.get("output") is not None and pair["output"] != rule_mirror(pair["input"]):
            return ["lesson includes an output inconsistent with the task mirror"]
    answer = rule_mirror(query["input"])
    return [f"rival {name} fits every demo but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(d["input"]) == d.get("output") for d in demos)
            and rival(query["input"]) != answer]


def mutation_fixtures():
    good = generate(0, 0)
    missing_divider = [r[:] for r in good]
    missing_divider[0][3] = 0
    no_source = [[0 if v == 2 else v for v in r] for r in good]
    no_target = [[0 if v == 3 else v for v in r] for r in good]
    two_targets = [r[:] for r in good]
    for r, row in enumerate(two_targets):
        for c, value in enumerate(row):
            if value == 0:
                two_targets[r][c] = 3
                return [("missing_divider", missing_divider), ("no_source", no_source),
                        ("no_target", no_target), ("two_targets", two_targets),
                        ("ragged", good[:-1] + [good[-1][:-1]])]
    raise AssertionError("canonical anchor unexpectedly has no background")
