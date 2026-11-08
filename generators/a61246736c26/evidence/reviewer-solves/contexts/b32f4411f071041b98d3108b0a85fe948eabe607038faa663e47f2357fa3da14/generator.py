"""Semantic generator for ARC task a61246736c26.

Full color-8 separator rows and columns define a three-row tile lattice.  Each
column contains two identical 1/2/8 pattern tiles and one solid swatch tile.
The solid tile's row selects a frame color from the leading swatch strip; its
interior selects a fill color.  Emit one recolored pattern tile per column,
separated by color 8.
"""
from __future__ import annotations

from itertools import permutations, product

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "a61246736c26"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("same_row_counterfactual", "mixed_row_counterfactual", "varied")
RULE_HASH = "08238424436c"
SUMMARY = "Use each column's solid swatch row and fill to recolor its duplicated 1/2/8 pattern tile."
INVARIANTS = [
    "literal color-8 rows and columns delimit the lattice",
    "the lattice has three equal-height row bands and three or four tile columns",
    "each column has two identical pattern copies and one solid swatch",
    "row swatches are a permutation of 5, 9, 0 and solid fills are distinct colors from 3, 4, 6, 7",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "row_cycle_012",
    "row_cycle_120",
    "row_cycle_201",
    "top_repeat",
    "middle_repeat",
    "bottom_repeat",
    "zero_frame_all",
    "four_columns",
    "four_columns_reverse",
    "permuted_frames",
    "shared_pattern",
    "same_row_top",
    "recombined_rows",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and swatch-row/pattern curricula",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": "8888888888888888888/5111118111118111118/5182818166618177718/5122218166618177718/5182818166618177718/5111118111118111118/8888888888888888888/9111118111118111118/9133318128818122218/9133318122818182818/9133318182218188818/9111118111118111118/8888888888888888888/0111118111118111118/0182818128818122218/0122218122818182818/0182818182218188818/0111118111118111118/8888888888888888888",
    "public_2": "88888888888888888888888888888/51111118111111811111181111118/51288818188281812228181222818/51222818122221818828181282218/51882818182821818222181288218/51822218182221818828181288218/51111118111111811111181111118/88888888888888888888888888888/91111118111111811111181111118/91288818133331817777181222818/91222818133331817777181282218/91882818133331817777181288218/91822218133331817777181288218/91111118111111811111181111118/88888888888888888888888888888/01111118111111811111181111118/01444418188281812228181666618/01444418122221818828181666618/01444418182821818222181666618/01444418182221818828181666618/01111118111111811111181111118/88888888888888888888888888888",
    "public_3": "8888888888888888888888888/5111111181111111811111118/5188288181828881813333318/5182228181222281813333318/5188288181888281813333318/5122222181822221813333318/5188288181888281813333318/5111111181111111811111118/8888888888888888888888888/9111111181111111811111118/9166666181828881818882218/9166666181222281818882218/9166666181888281818228818/9166666181822221812228818/9166666181888281818288818/9111111181111111811111118/8888888888888888888888888/0111111181111111811111118/0188288181444441818882218/0182228181444441818882218/0188288181444441818228818/0122222181444441812228818/0188288181444441818288818/0111111181111111811111118/8888888888888888888888888",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_STANDARD_FRAMES = (5, 9, 0)
_FRAME_PERMUTATIONS = tuple(permutations(_STANDARD_FRAMES))
_PROFILE_SOLID_ROWS = {
    "row_cycle_012": (0, 1, 2),
    "row_cycle_120": (1, 2, 0),
    "row_cycle_201": (2, 0, 1),
    "top_repeat": (0, 0, 1),
    "middle_repeat": (1, 1, 2),
    "bottom_repeat": (2, 2, 0),
    "zero_frame_all": (2, 2, 2),
    "four_columns": (0, 1, 2, 0),
    "four_columns_reverse": (2, 1, 0, 2),
    "permuted_frames": (0, 1, 2),
    "shared_pattern": (0, 1, 2),
    "same_row_top": (0, 0, 0),
}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        return ["ARC grid dimensions must be at most 30 by 30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _bands(separators, end):
    bands = []
    previous = 0
    for separator in separators:
        if separator > previous:
            bands.append((previous, separator - 1))
        previous = separator + 1
    if previous < end:
        bands.append((previous, end - 1))
    return bands


def _source_parse(grid):
    errors = _valid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    separator_rows = [row for row, values in enumerate(grid) if all(value == 8 for value in values)]
    separator_cols = [col for col in range(width) if all(grid[row][col] == 8 for row in range(height))]
    row_bands = _bands(separator_rows, height)
    col_bands = _bands(separator_cols, width)
    if not row_bands or not col_bands:
        raise ValueError("separator lattice has no bands")
    size = row_bands[0][1] - row_bands[0][0] + 1
    row_colors = tuple(grid[first][col_bands[0][0]] for first, _last in row_bands)
    cores = []
    for first_row, last_row in row_bands:
        core_row = []
        for col_index, (first_col, last_col) in enumerate(col_bands):
            start_col = first_col + 1 if col_index == 0 else first_col
            core_row.append([list(row[start_col:last_col + 1]) for row in grid[first_row:last_row + 1]])
        cores.append(core_row)
    return {
        "height": height,
        "width": width,
        "separator_rows": separator_rows,
        "separator_cols": separator_cols,
        "row_bands": row_bands,
        "col_bands": col_bands,
        "size": size,
        "row_colors": row_colors,
        "cores": cores,
    }


def _solid_color(tile, size):
    values = [
        tile[row][col]
        for row in range(1, size - 1)
        for col in range(1, size - 1)
        if tile[row][col] != 1
    ]
    unique = set(values)
    return next(iter(unique)) if values and len(unique) == 1 else None


def _is_pattern(tile):
    values = {value for row in tile for value in row}
    return 2 in values and 8 in values


def rule_mirror(grid):
    parsed = _source_parse(grid)
    size = parsed["size"]
    output_tiles = []
    for col_index in range(len(parsed["col_bands"])):
        infos = []
        for row_index in range(len(parsed["row_bands"])):
            tile = parsed["cores"][row_index][col_index]
            infos.append((row_index, _solid_color(tile, size), tile))
        solid = next(
            (info for info in infos if info[1] is not None and info[1] not in (2, 8)),
            None,
        )
        pattern = next((info for info in infos if _is_pattern(info[2])), None)
        if solid is None or pattern is None:
            raise ValueError(f"column {col_index} lacks a selectable solid or pattern tile")
        if len(pattern[2]) != size or any(len(row) != size for row in pattern[2]):
            raise ValueError(f"column {col_index} pattern tile does not match inferred size {size}")
        frame = parsed["row_colors"][solid[0]]
        fill = solid[1]
        output_tiles.append(
            [[frame if value == 1 else fill if value == 2 else value for value in row] for row in pattern[2]]
        )
    output = []
    for row in range(size):
        values = []
        for col_index, tile in enumerate(output_tiles):
            if col_index:
                values.append(8)
            values.extend(tile[row])
        output.append(values)
    return output


def _border_is_one(tile):
    if not tile or not tile[0]:
        return False
    height, width = len(tile), len(tile[0])
    return all(
        tile[row][col] == 1
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    )


def _pattern_key(tile):
    return tuple(map(tuple, tile))


def _classify(row_colors, solid_rows, pattern_keys):
    if tuple(row_colors) != _STANDARD_FRAMES:
        return "permuted_frames"
    signature = tuple(solid_rows)
    if len(signature) == 4:
        if signature == _PROFILE_SOLID_ROWS["four_columns"]:
            return "four_columns"
        if signature == _PROFILE_SOLID_ROWS["four_columns_reverse"]:
            return "four_columns_reverse"
        return "recombined_rows"
    if signature == (0, 1, 2) and len(set(pattern_keys)) == 1:
        return "shared_pattern"
    for profile in (
        "row_cycle_012",
        "row_cycle_120",
        "row_cycle_201",
        "top_repeat",
        "middle_repeat",
        "bottom_repeat",
        "zero_frame_all",
        "same_row_top",
        ):
        if signature == _PROFILE_SOLID_ROWS[profile]:
            return profile
    return "recombined_rows"


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    try:
        parsed = _source_parse(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return result
    size = parsed["size"]
    if not 4 <= size <= 8:
        errors.append(f"tile size must be 4..8, found {size}")
    if len(parsed["row_bands"]) != 3:
        errors.append(f"expected three row bands, found {len(parsed['row_bands'])}")
    if len(parsed["col_bands"]) not in (3, 4):
        errors.append(f"expected three or four column bands, found {len(parsed['col_bands'])}")
    if any(last - first + 1 != size for first, last in parsed["row_bands"]):
        errors.append("row bands must have equal height")
    expected_widths = [size + 1] + [size] * (len(parsed["col_bands"]) - 1)
    actual_widths = [last - first + 1 for first, last in parsed["col_bands"]]
    if actual_widths != expected_widths:
        errors.append(f"column band widths {actual_widths} do not match {expected_widths}")
    expected_rows = [index * (size + 1) for index in range(4)]
    expected_cols = [size + 1 + index * (size + 1) for index in range(len(parsed["col_bands"]))]
    if parsed["separator_rows"] != expected_rows:
        errors.append("separator rows do not match the calibrated lattice")
    if parsed["separator_cols"] != expected_cols:
        errors.append("separator columns do not match the calibrated lattice")
    row_colors = []
    if len(parsed["row_bands"]) == 3:
        for first, last in parsed["row_bands"]:
            values = {grid[row][parsed["col_bands"][0][0]] for row in range(first, last + 1)}
            if len(values) != 1:
                errors.append("row swatch strip must be uniform within each band")
                row_colors.append(None)
            else:
                row_colors.append(next(iter(values)))
    if set(row_colors) != set(_STANDARD_FRAMES):
        errors.append(f"row swatches must be a permutation of {_STANDARD_FRAMES}")
    solid_rows, fill_colors, pattern_keys = [], [], []
    if len(parsed["row_bands"]) == 3 and len(parsed["col_bands"]) in (3, 4):
        for col_index in range(len(parsed["col_bands"])):
            solids = []
            patterns = []
            for row_index in range(3):
                tile = parsed["cores"][row_index][col_index]
                if len(tile) != size or any(len(row) != size for row in tile):
                    errors.append(f"tile ({row_index},{col_index}) is not {size}x{size}")
                    continue
                if not _border_is_one(tile):
                    errors.append(f"tile ({row_index},{col_index}) lacks a color-1 frame")
                solid = _solid_color(tile, size)
                if solid is not None and solid not in (2, 8):
                    if any(tile[row][col] != solid for row in range(1, size - 1) for col in range(1, size - 1)):
                        errors.append(f"solid tile ({row_index},{col_index}) has a nonuniform interior")
                    solids.append((row_index, solid))
                if _is_pattern(tile):
                    interior = {tile[row][col] for row in range(1, size - 1) for col in range(1, size - 1)}
                    if not interior <= {2, 8} or interior != {2, 8}:
                        errors.append(f"pattern tile ({row_index},{col_index}) must use both 2 and 8 inside")
                    patterns.append((row_index, _pattern_key(tile)))
            if len(solids) != 1:
                errors.append(f"column {col_index} must contain exactly one solid swatch")
            else:
                solid_rows.append(solids[0][0])
                fill_colors.append(solids[0][1])
            if len(patterns) != 2 or len({key for _row, key in patterns}) != 1:
                errors.append(f"column {col_index} must contain two identical pattern copies")
            elif patterns:
                pattern_keys.append(patterns[0][1])
    if len(fill_colors) == len(parsed["col_bands"]):
        if len(set(fill_colors)) != len(fill_colors):
            errors.append("solid fill colors must be distinct by column")
        if not set(fill_colors) <= {3, 4, 6, 7}:
            errors.append("solid fill colors must come from 3, 4, 6, 7")
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    profile = public or _classify(row_colors, solid_rows, pattern_keys)
    if profile not in SCENE_PROFILES:
        errors.append("lattice does not match a declared scene profile")
    # Structural validation must finish before the mirror indexes inferred tiles.
    # A missing separator can merge bands; executing the mirror then raises an
    # IndexError instead of returning the already collected rejection reasons.
    output = None
    if not errors:
        try:
            output = rule_mirror(grid)
        except ValueError as exc:
            errors.append(str(exc))
    result.update(
        {
            "tile_size": size,
            "column_count": len(parsed["col_bands"]),
            "row_colors": tuple(row_colors),
            "solid_rows": tuple(solid_rows),
            "fill_colors": tuple(fill_colors),
            "distinct_pattern_count": len(set(pattern_keys)),
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _pattern_tile(size, rng):
    tile = [[1 if row in (0, size - 1) or col in (0, size - 1) else 8 for col in range(size)] for row in range(size)]
    interior = [(row, col) for row in range(1, size - 1) for col in range(1, size - 1)]
    rng.shuffle(interior)
    twos = rng.randint(max(1, len(interior) // 4), max(2, 3 * len(interior) // 5))
    twos = min(twos, len(interior) - 1)
    for row, col in interior[:twos]:
        tile[row][col] = 2
    return tile


def _solid_tile(size, color):
    return [[1 if row in (0, size - 1) or col in (0, size - 1) else color for col in range(size)] for row in range(size)]


def _put_tile(grid, start_row, start_col, tile):
    for row, values in enumerate(tile):
        for col, value in enumerate(values):
            grid[start_row + row][start_col + col] = value


def _general(rng, profile, band, *, teaching=None):
    column_count = rng.choice((3, 4)) if profile in ("permuted_frames", "recombined_rows") else len(_PROFILE_SOLID_ROWS[profile])
    row_colors = list(_STANDARD_FRAMES)
    if profile == "permuted_frames":
        if teaching == "same_row":
            # Cross same-row solids with nonzero, nonfixed row swatches.
            # This distinguishes both the zero-frame and fixed-swatch rivals.
            choices = [(frames, row) for frames in _FRAME_PERMUTATIONS
                       for row in range(3)
                       if frames[row] != 0 and frames[row] != _STANDARD_FRAMES[row]]
            frames, selected_row = rng.choice(choices)
            row_colors = list(frames)
            solid_rows = (selected_row,) * column_count
        else:
            row_colors = list(rng.choice([frames for frames in _FRAME_PERMUTATIONS if frames != _STANDARD_FRAMES]))
            if teaching == "mixed_row":
                # A same-row-only witness leaves a conditional fixed-swatch
                # shortcut alive on mixed-row queries. Cross these axes too.
                choices = [rows for rows in product(range(3), repeat=column_count)
                           if len(set(rows)) > 1 and any(
                               row_colors[row] != _STANDARD_FRAMES[row] for row in rows)]
                solid_rows = rng.choice(choices)
            else:
                solid_rows = tuple(rng.randrange(3) for _ in range(column_count))
    elif profile == "recombined_rows":
        named = set(_PROFILE_SOLID_ROWS.values())
        choices = [rows for rows in product(range(3), repeat=column_count) if rows not in named]
        solid_rows = rng.choice(choices)
    else:
        solid_rows = _PROFILE_SOLID_ROWS[profile]
    if column_count == 4:
        # Four size-7 tiles would exceed the 30-cell ARC width bound.
        size = rng.choice((5, 6))
    else:
        low, high = {"easy": (4, 5), "medium": (5, 6), "hard": (7, 8)}[band]
        size = rng.randint(low, high)
    fills = rng.sample([3, 4, 6, 7], column_count)
    patterns = []
    if profile == "shared_pattern":
        pattern = _pattern_tile(size, rng)
        patterns = [[row[:] for row in pattern] for _ in range(column_count)]
    else:
        seen = set()
        for _ in range(column_count):
            for _attempt in range(100):
                pattern = _pattern_tile(size, rng)
                key = _pattern_key(pattern)
                if key not in seen:
                    seen.add(key)
                    patterns.append(pattern)
                    break
            else:
                raise RuntimeError("could not create distinct pattern tiles")
    height = 1 + 3 * (size + 1)
    width = (size + 1) + 1 + (column_count - 1) * (size + 1)
    grid = [[8] * width for _ in range(height)]
    row_starts = [1 + index * (size + 1) for index in range(3)]
    col_starts = [0] + [size + 2 + (index - 1) * (size + 1) for index in range(1, column_count)]
    for row_index, start_row in enumerate(row_starts):
        for row in range(start_row, start_row + size):
            grid[row][0] = row_colors[row_index]
        for col_index, band_start in enumerate(col_starts):
            start_col = band_start + 1 if col_index == 0 else band_start
            tile = _solid_tile(size, fills[col_index]) if solid_rows[col_index] == row_index else patterns[col_index]
            _put_tile(grid, start_row, start_col, tile)
    return grid


def _validate_indices(seed, sample_index):
    if type(seed) is not int:
        raise ValueError("seed must be a Python integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative Python integer (not bool)")


def schedule_profile(seed, sample_index, difficulty=None):
    """Coarse default teaching schedule; explicit scene overrides bypass it."""
    _validate_indices(seed, sample_index)
    _band(difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_indices(seed, sample_index)
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=band, overrides=overrides)
    if requested is None:
        phase = sample_index % LESSON_SCHEDULE_PERIOD
        if phase in (0, 1):
            # Six consecutive accepted draws ordinarily give two of each
            # witness. Production census checks actual rejection/assembly.
            teaching = "same_row" if phase == 0 else "mixed_row"
            profile = ctx.draw_choice("scene_profile", ("permuted_frames",))
            return _general(ctx.draw_rng("layout"), profile, band, teaching=teaching)
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)])
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """The supported lawful lattice domain, including row/swatch recombinations."""
    return self_check(grid)


def _same_row_nonzero(grid):
    info = _analysis(grid)
    return (not info["errors"] and len(set(info["solid_rows"])) == 1
            and info["row_colors"][info["solid_rows"][0]] != 0)


def _swatch_lookup_matters(grid):
    info = _analysis(grid)
    return (not info["errors"]
            and any(info["row_colors"][row] != _STANDARD_FRAMES[row] for row in info["solid_rows"]))


def _mixed_row_swatch_lookup_matters(grid):
    info = _analysis(grid)
    return (not info["errors"] and len(set(info["solid_rows"])) > 1
            and any(info["row_colors"][row] != _STANDARD_FRAMES[row] for row in info["solid_rows"]))


def _rival_same_row_force_zero(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if len(set(info["solid_rows"])) != 1:
        return info["output"]
    frame = info["row_colors"][info["solid_rows"][0]]
    return [[0 if value == frame else value for value in row] for row in info["output"]]


def _rival_fixed_row_swatches(grid):
    parsed = _source_parse(grid)
    altered = [list(row) for row in grid]
    for row_index, (first, last) in enumerate(parsed["row_bands"]):
        for row in range(first, last + 1):
            altered[row][parsed["col_bands"][0][0]] = _STANDARD_FRAMES[row_index]
    return rule_mirror(altered)


def _rival_mixed_rows_fixed_swatches(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if len(set(info["solid_rows"])) == 1:
        return info["output"]
    return _rival_fixed_row_swatches(grid)


SEMANTIC_WITNESSES = {
    "same_row_nonzero": _same_row_nonzero,
    "swatch_lookup_matters": _swatch_lookup_matters,
    "mixed_row_swatch_lookup_matters": _mixed_row_swatch_lookup_matters,
}
SEMANTIC_RIVALS = {
    "same_row_force_zero": _rival_same_row_force_zero,
    "fixed_row_swatches": _rival_fixed_row_swatches,
    "mixed_rows_fixed_swatches": _rival_mixed_rows_fixed_swatches,
}
WITNESS_RIVALS = {
    "same_row_nonzero": ["same_row_force_zero"],
    "swatch_lookup_matters": ["fixed_row_swatches"],
    "mixed_row_swatch_lookup_matters": ["mixed_rows_fixed_swatches"],
}
# All three shortcuts fit every labeled canonical pair; generated witnesses teach
# the missing distinctions. Finite checks cover only these declared rivals.
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
