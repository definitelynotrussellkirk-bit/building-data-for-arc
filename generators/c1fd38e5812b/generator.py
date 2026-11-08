"""Generate nonuniform run grids that compress to one cell per run block."""

from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "c1fd38e5812b"
TASK_ID = "c1fd38e5812b"
VERSION = "3.0.0"
RULE_HASH = "dc8aa1222f34"
SUMMARY = (
    "The input expands a small color grid by independently repeating each "
    "logical row and column; the output samples the first cell of every "
    "run detected along the input's first column and first row."
)

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
EXTRAPOLATION_PROFILES = (
    "nonuniform_runs",
    "interior_merges",
    "uniform_runs",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted complete-public and extrapolation profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INVARIANTS = [
    "the input is an exact Cartesian expansion of a 2..6 by 2..6 grid",
    "each logical row and column has an independently chosen run of 2..12",
    "adjacent logical cells on the first column and first row differ",
    "interior logical neighbors may match without erasing a detected boundary",
    "the sampled logical grid uses at least four colors, as every public grid does",
    "the output is the logical grid sampled at the detected run starts",
]

_TRANSFORMS = (
    "identity",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "horizontal_flip",
    "vertical_flip",
    "main_diagonal",
    "anti_diagonal",
)

_WEIGHTED_PROFILES = {
    band: (
        *PUBLIC_PROFILES,
        *(("nonuniform_runs",) * 8),
        *(("interior_merges",) * 5),
        *(("uniform_runs",) * 2),
    )
    for band in ("easy", "medium", "hard")
}

_LOGICAL_BOUNDS = {
    "easy": (2, 3),
    "medium": (2, 5),
    "hard": (3, 6),
}

_TOTAL_BOUNDS = {
    "easy": (8, 16),
    "medium": (10, 20),
    "hard": (12, 24),
}

_SPAN_MAX = {
    "easy": 8,
    "medium": 10,
    "hard": 12,
}

_PUBLIC_SPECS = {
    "public_train_1": {
        "logical": (
            (1, 2, 8),
            (5, 6, 3),
        ),
        "row_spans": (5, 10),
        "col_spans": (3, 5, 6),
    },
    "public_train_2": {
        "logical": (
            (4, 5, 2),
            (1, 3, 2),
        ),
        "row_spans": (4, 8),
        "col_spans": (5, 3, 6),
    },
    "public_train_3": {
        "logical": (
            (8, 7, 9, 8),
            (3, 1, 6, 4),
            (2, 4, 1, 5),
        ),
        "row_spans": (4, 5, 6),
        "col_spans": (3, 5, 4, 3),
    },
    "public_train_4": {
        "logical": (
            (2, 8),
            (3, 5),
        ),
        "row_spans": (9, 4),
        "col_spans": (4, 11),
    },
    "public_test_1": {
        "logical": (
            (8, 7, 4, 8),
            (3, 1, 2, 8),
            (4, 5, 3, 9),
            (2, 6, 1, 7),
            (1, 5, 2, 8),
        ),
        "row_spans": (2, 3, 5, 2, 3),
        "col_spans": (4, 4, 5, 2),
    },
}


def _expand(logical, row_spans, col_spans):
    grid = []
    for logical_row, row_span in zip(logical, row_spans):
        expanded_row = [
            value
            for value, col_span in zip(logical_row, col_spans)
            for _ in range(col_span)
        ]
        grid.extend([expanded_row[:] for _ in range(row_span)])
    return grid


_PUBLIC_INPUTS = {
    profile: _expand(
        spec["logical"],
        spec["row_spans"],
        spec["col_spans"],
    )
    for profile, spec in _PUBLIC_SPECS.items()
}

_PUBLIC_LITERALS = {
    tuple(tuple(row) for row in grid)
    for grid in _PUBLIC_INPUTS.values()
}


def _transform(grid, name):
    if name == "identity":
        return [row[:] for row in grid]
    if name == "rotate_90":
        return [list(row) for row in zip(*reversed(grid))]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_270":
        return [list(row) for row in reversed(list(zip(*grid)))]
    if name == "horizontal_flip":
        return [list(reversed(row)) for row in grid]
    if name == "vertical_flip":
        return [row[:] for row in reversed(grid)]
    if name == "main_diagonal":
        return [list(row) for row in zip(*grid)]
    if name == "anti_diagonal":
        return [
            list(reversed(row))
            for row in reversed(list(zip(*grid)))
        ]
    raise KeyError(name)


def _role_signature(grid):
    roles = {}
    next_role = 0
    signature = []
    for row in grid:
        role_row = []
        for value in row:
            if value not in roles:
                roles[value] = next_role
                next_role += 1
            role_row.append(roles[value])
        signature.append(tuple(role_row))
    return tuple(signature)


_PUBLIC_LOOKUP = {}
for _profile, _grid in _PUBLIC_INPUTS.items():
    for _transform_name in _TRANSFORMS:
        _signature = _role_signature(_transform(_grid, _transform_name))
        _previous = _PUBLIC_LOOKUP.setdefault(_signature, _profile)
        if _previous != _profile:
            raise RuntimeError(
                "public role profiles collide: "
                f"{_previous!r} and {_profile!r}"
            )


def _canonical_answer_profile(grid):
    return _PUBLIC_LOOKUP.get(_role_signature(grid))


def _grid_shape_error(grid):
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return "empty_or_non_grid"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "ragged"
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "invalid_arc_value"
    return None


def _spans(starts, total):
    return [
        end - start
        for start, end in zip(starts, starts[1:] + [total])
    ]


def _compression_info(grid):
    height = len(grid)
    width = len(grid[0])
    row_starts = [0] + [
        row
        for row in range(1, height)
        if grid[row][0] != grid[row - 1][0]
    ]
    col_starts = [0] + [
        col
        for col in range(1, width)
        if grid[0][col] != grid[0][col - 1]
    ]
    output = [
        [grid[row][col] for col in col_starts]
        for row in row_starts
    ]
    row_spans = _spans(row_starts, height)
    col_spans = _spans(col_starts, width)
    exact_blocks = True
    for block_row, row1 in enumerate(row_starts):
        row2 = (
            row_starts[block_row + 1]
            if block_row + 1 < len(row_starts)
            else height
        )
        for block_col, col1 in enumerate(col_starts):
            col2 = (
                col_starts[block_col + 1]
                if block_col + 1 < len(col_starts)
                else width
            )
            value = output[block_row][block_col]
            if any(
                grid[row][col] != value
                for row in range(row1, row2)
                for col in range(col1, col2)
            ):
                exact_blocks = False
    return {
        "row_starts": row_starts,
        "col_starts": col_starts,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "output": output,
        "exact_blocks": exact_blocks,
    }


def _interior_merge(output):
    rows = len(output)
    cols = len(output[0])
    horizontal = any(
        output[row][col] == output[row][col + 1]
        for row in range(1, rows)
        for col in range(cols - 1)
    )
    vertical = any(
        output[row][col] == output[row + 1][col]
        for row in range(rows - 1)
        for col in range(1, cols)
    )
    return horizontal or vertical


def solve_python(grid):
    """Input-pure mirror of the authoritative first-row/column run sampler."""
    error = _grid_shape_error(grid)
    if error is not None:
        raise ValueError(error)
    return _compression_info(grid)["output"]


def _analyze(grid):
    error = _grid_shape_error(grid)
    if error is not None:
        return {"strict": False, "reasons": [error]}

    height = len(grid)
    width = len(grid[0])
    info = _compression_info(grid)
    output = info["output"]
    logical_rows = len(output)
    logical_cols = len(output[0])
    row_spans = info["row_spans"]
    col_spans = info["col_spans"]
    reasons = []

    if not 8 <= height <= 24 or not 8 <= width <= 24:
        reasons.append("dimension_range")
    if not 2 <= logical_rows <= 6 or not 2 <= logical_cols <= 6:
        reasons.append("logical_dimensions")
    if any(not 2 <= span <= 12 for span in row_spans + col_spans):
        reasons.append("run_span_range")
    if not info["exact_blocks"]:
        reasons.append("non_solid_logical_block")
    if len({value for row in output for value in row}) < 4:
        reasons.append("output_palette")
    if output == grid:
        reasons.append("identity")

    canonical_profile = _canonical_answer_profile(grid)
    interior_merge = _interior_merge(output)
    uniform_runs = (
        len(set(row_spans)) == 1 and len(set(col_spans)) == 1
    )
    if canonical_profile is not None:
        scene_profile = canonical_profile
    elif interior_merge:
        scene_profile = "interior_merges"
    elif uniform_runs:
        scene_profile = "uniform_runs"
    else:
        scene_profile = "nonuniform_runs"

    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "logical_rows": logical_rows,
        "logical_cols": logical_cols,
        "row_starts": info["row_starts"],
        "col_starts": info["col_starts"],
        "row_spans": row_spans,
        "col_spans": col_spans,
        "output": output,
        "uniform_runs": uniform_runs,
        "interior_merge": interior_merge,
        "canonical_answer_profile": canonical_profile,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete run-compression lesson from returned pixels."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    """Recover the declared semantic control from the returned grid."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    return {"scene_profile": analysis["scene_profile"]}


_PUBLIC_SAFE_TRANSFORMS = {
    profile: tuple(
        name
        for name in _TRANSFORMS
        if (
            _compression_info(_transform(grid, name))["exact_blocks"]
            and len(_compression_info(_transform(grid, name))["output"]) >= 2
            and len(_compression_info(_transform(grid, name))["output"][0])
            >= 2
        )
    )
    for profile, grid in _PUBLIC_INPUTS.items()
}


def _public_grid(profile, palette_rng, transform_rng):
    template = _PUBLIC_INPUTS[profile]
    role_colors = list(
        dict.fromkeys(value for row in template for value in row)
    )
    replacement_colors = palette_rng.sample(
        list(range(10)),
        len(role_colors),
    )
    mapping = dict(zip(role_colors, replacement_colors))
    recolored = [
        [mapping[value] for value in row]
        for row in template
    ]
    transform = transform_rng.choice(_PUBLIC_SAFE_TRANSFORMS[profile])
    grid = _transform(recolored, transform)
    if tuple(tuple(row) for row in grid) in _PUBLIC_LITERALS:
        rotated = replacement_colors[1:] + replacement_colors[:1]
        mapping = dict(zip(role_colors, rotated))
        recolored = [
            [mapping[value] for value in row]
            for row in template
        ]
        grid = _transform(recolored, transform)
    return grid


def _nonuniform_spans(count, band, rng):
    total_lo, total_hi = _TOTAL_BOUNDS[band]
    span_hi = _SPAN_MAX[band]
    for _ in range(512):
        target = rng.randint(
            max(total_lo, 2 * count),
            min(total_hi, span_hi * count),
        )
        remaining = target
        spans = []
        for index in range(count):
            runs_left = count - index - 1
            value_lo = max(2, remaining - span_hi * runs_left)
            value_hi = min(span_hi, remaining - 2 * runs_left)
            value = rng.randint(value_lo, value_hi)
            spans.append(value)
            remaining -= value
        rng.shuffle(spans)
        if len(set(spans)) > 1:
            return spans
    raise RuntimeError(
        f"failed to draw {count} nonuniform {band!r} spans"
    )


def _uniform_spans(count, band, rng):
    total_lo, total_hi = _TOTAL_BOUNDS[band]
    span_lo = max(2, (total_lo + count - 1) // count)
    span_hi = min(12, _SPAN_MAX[band], total_hi // count)
    if span_hi < span_lo:
        raise RuntimeError(
            f"no uniform {band!r} span for {count} logical runs"
        )
    span = rng.randint(span_lo, span_hi)
    return [span] * count


def _logical_grid(rows, cols, profile, rng):
    palette_size = min(10, max(4, (rows * cols + 1) // 2))
    palette = rng.sample(list(range(10)), palette_size)
    logical = []
    for row in range(rows):
        values = []
        for col in range(cols):
            excluded = set()
            if col:
                excluded.add(values[col - 1])
            if row:
                excluded.add(logical[row - 1][col])
            choices = [color for color in palette if color not in excluded]
            values.append(rng.choice(choices))
        logical.append(values)

    if profile == "interior_merges":
        candidates = [
            ("horizontal", row, col)
            for row in range(1, rows)
            for col in range(cols - 1)
        ] + [
            ("vertical", row, col)
            for row in range(rows - 1)
            for col in range(1, cols)
        ]
        direction, row, col = rng.choice(candidates)
        if direction == "horizontal":
            logical[row][col + 1] = logical[row][col]
        else:
            logical[row + 1][col] = logical[row][col]
    return logical


def _synthetic_grid(profile, band, rng):
    logical_lo, logical_hi = _LOGICAL_BOUNDS[band]
    for _ in range(256):
        rows = rng.randint(logical_lo, logical_hi)
        cols = rng.randint(logical_lo, logical_hi)
        if profile == "uniform_runs":
            row_spans = _uniform_spans(rows, band, rng)
            col_spans = _uniform_spans(cols, band, rng)
        else:
            row_spans = _nonuniform_spans(rows, band, rng)
            col_spans = _nonuniform_spans(cols, band, rng)
        logical = _logical_grid(rows, cols, profile, rng)
        grid = _expand(logical, row_spans, col_spans)
        analysis = _analyze(grid)
        if analysis["strict"] and analysis["scene_profile"] == profile:
            return grid
    raise RuntimeError(f"failed to construct profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    profile = ctx.draw_choice(
        "scene_profile",
        _WEIGHTED_PROFILES[band],
    )
    if profile in PUBLIC_PROFILES:
        grid = _public_grid(
            profile,
            ctx.draw_rng("public_palette"),
            ctx.draw_rng("public_transform"),
        )
    elif profile in EXTRAPOLATION_PROFILES:
        grid = _synthetic_grid(
            profile,
            band,
            ctx.draw_rng("synthetic_scene"),
        )
    else:
        raise RuntimeError(f"unhandled scene profile {profile!r}")

    analysis = _analyze(grid)
    if not analysis["strict"] or analysis["scene_profile"] != profile:
        raise RuntimeError(
            "internal generation contract failed for "
            f"{profile!r}: {analysis['reasons']}"
        )
    if tuple(tuple(row) for row in grid) in _PUBLIC_LITERALS:
        raise RuntimeError("public input literal replayed")
    return grid
