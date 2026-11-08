"""Generator for cyclic shape continuation task f65b8464b007.

Each horizontal band contains three-wide colored shape sections. Colors stay
fixed by section while the shapes shift one section left in every new band.
The output is the next three-row band in that cyclic sequence.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f65b8464b007"
VERSION = "4.0.0"
TASK_ID = "f65b8464b007"
RULE_HASH = "ca4a7208d4ef"

SUMMARY = (
    "Construct one through three bands of three-wide shape sections. "
    "Section colors remain fixed, while each successive band moves every "
    "shape one section left cyclically. The output continues that sequence "
    "for one more three-row band."
)

INVARIANTS = [
    "three through five sections are three cells wide with blank separators",
    "one through three three-row bands have blank boundary/separator rows",
    "each section has one fixed color and section colors are distinct",
    "every shape is a distinct four-through-seven-cell 3x3-spanning mask",
    "each successive band shifts the preceding shapes left by one section",
    "the output shifts the final input band once more and preserves colors",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

SW = 3
STRIDE = 4
_PROFILE_PRIOR = 0.12

AXES = {
    "n_sections": {
        "type": "int",
        "default": "difficulty-aware 3..5",
        "valid": "3..5",
    },
    "n_bands": {
        "type": "int",
        "default": "difficulty-aware 1..3",
        "valid": "1..3",
    },
}

# Complete public input morphology in reading order. Colors are deliberately
# omitted: they are fixed section roles and can be relabeled bijectively.
_PROFILE_PATTERNS = (
    (
        ("111001001", "100100111", "100011100", "101101101"),
    ),
    (
        ("101010101", "100111001", "111010010"),
        ("100111001", "111010010", "101010101"),
    ),
    (
        ("100111001", "101010101", "101111010", "010111010"),
        ("101010101", "101111010", "010111010", "100111001"),
    ),
    (
        ("101101111", "010111010", "111000111"),
        ("010111010", "111000111", "101101111"),
        ("111000111", "101101111", "010111010"),
    ),
    (
        ("110010111", "110001110", "101101101", "010111010"),
        ("110001110", "101101101", "010111010", "110010111"),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label, lower, upper in (
        ("n_sections", 3, 5),
        ("n_bands", 1, 3),
    ):
        value = overrides.get(label)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(
                f"{label} must be an integer in [{lower}, {upper}]"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _mask_cells(mask):
    return tuple(
        (index // SW, index % SW)
        for index, value in enumerate(mask)
        if value == "1"
    )


def _mask_from_cells(cells):
    occupied = set(cells)
    return "".join(
        "1" if (row, col) in occupied else "0"
        for row in range(SW)
        for col in range(SW)
    )


def _transform_mask(mask, transform):
    cells = _mask_cells(mask)
    transformed = []
    for row, col in cells:
        if transform >= 4:
            col = SW - 1 - col
        for _turn in range(transform % 4):
            row, col = col, SW - 1 - row
        transformed.append((row, col))
    return _mask_from_cells(transformed)


def _patterns_have_rule_width(patterns):
    columns_establish_width = all(
        any(
            band[0][row * SW + col] == "1"
            for band in patterns
            for row in range(SW)
        )
        for col in (1, 2)
    )
    no_false_separator_row = all(
        any(mask[row * SW + col] == "1" for mask in band for col in range(SW))
        for band in patterns
        for row in range(SW)
    )
    return columns_establish_width and no_false_separator_row


def _profile_variants(patterns):
    n_sections = len(patterns[0])
    variants = []
    for transform in range(8):
        transformed = tuple(
            tuple(
                _transform_mask(mask, transform)
                for mask in band
            )
            for band in patterns
        )
        for phase in range(n_sections):
            variant = tuple(
                tuple(
                    band[(section + phase) % n_sections]
                    for section in range(n_sections)
                )
                for band in transformed
            )
            if _patterns_have_rule_width(variant):
                variants.append(variant)
    return tuple(dict.fromkeys(variants))


_PROFILE_SIGNATURE_TO_INDEX = {
    (len(patterns[0]), len(patterns), variant): index
    for index, patterns in enumerate(_PROFILE_PATTERNS)
    for variant in _profile_variants(patterns)
}


def _pattern_spans_box(mask):
    cells = _mask_cells(mask)
    if not cells:
        return False
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return (
        min(rows) == 0
        and max(rows) == SW - 1
        and min(cols) == 0
        and max(cols) == SW - 1
    )


_GENERAL_MASKS = tuple(
    format(bits, "09b")
    for bits in range(1, 1 << 9)
    if 4 <= bits.bit_count() <= 7
    and _pattern_spans_box(format(bits, "09b"))
    and any(format(bits, "09b")[index] == "1" for index in (1, 4, 7))
    and any(format(bits, "09b")[index] == "1" for index in (3, 4, 5))
)


def _build_grid(patterns, colors):
    n_bands = len(patterns)
    n_sections = len(patterns[0])
    height = STRIDE * n_bands + 1
    width = STRIDE * n_sections - 1
    grid = full_grid(height, width, 0)
    for band_index, band in enumerate(patterns):
        top = 1 + STRIDE * band_index
        for section_index, mask in enumerate(band):
            left = STRIDE * section_index
            color = colors[section_index]
            for row, col in _mask_cells(mask):
                grid[top + row][left + col] = color
    return grid


def _apply_rule(grid):
    grid = _coerce_grid(grid)
    height = len(grid)
    width = len(grid[0])
    try:
        shape_width = next(
            col
            for col in range(1, width)
            if all(grid[row][col] == 0 for row in range(height))
        )
    except StopIteration as error:
        raise ValueError("no all-zero separator column") from error
    stride = shape_width + 1
    n_sections = (width + 1) // stride
    starts = [index * stride for index in range(n_sections)]
    separator_rows = [
        row
        for row in range(height)
        if all(value == 0 for value in grid[row])
    ]
    if len(separator_rows) < 2:
        raise ValueError("at least two all-zero rows are required")
    first_start = separator_rows[0] + 1
    last_start = separator_rows[-2] + 1
    colors = []
    for start in starts:
        values = [
            grid[row][col]
            for row in range(first_start, first_start + 3)
            for col in range(start, start + shape_width)
            if grid[row][col] != 0
        ]
        if not values:
            raise ValueError("every first-band section needs a color")
        colors.append(values[0])

    output = full_grid(3, width, 0)
    for row in range(3):
        for col in range(width):
            section_index = col // stride
            local_col = col % stride
            if section_index >= n_sections or local_col >= shape_width:
                continue
            source_index = (section_index + 1) % n_sections
            source_col = starts[source_index] + local_col
            if grid[last_start + row][source_col] != 0:
                output[row][col] = colors[section_index]
    return output


def _scene_analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, None, ["grid must be a non-empty list or tuple"]
    if not all(
        isinstance(row, (list, tuple, str)) and row for row in grid
    ):
        return None, None, [
            "rows must be non-empty lists, tuples, or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]
    height = len(coerced)
    errors = []
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0 through 9")
        return coerced, None, errors

    if (
        (height - 1) % STRIDE != 0
        or not 1 <= (height - 1) // STRIDE <= 3
    ):
        errors.append("height must encode one through three 3-row bands")
    if (
        (width + 1) % STRIDE != 0
        or not 3 <= (width + 1) // STRIDE <= 5
    ):
        errors.append("width must encode three through five sections")
    if errors:
        return coerced, None, errors

    n_bands = (height - 1) // STRIDE
    n_sections = (width + 1) // STRIDE
    separator_rows = tuple(range(0, height, STRIDE))
    separator_cols = tuple(range(SW, width, STRIDE))
    if any(any(coerced[row]) for row in separator_rows):
        errors.append("boundary and inter-band rows must be all zero")
    if any(
        coerced[row][col] != 0
        for col in separator_cols
        for row in range(height)
    ):
        errors.append("inter-section columns must be all zero")
    if any(
        all(value == 0 for value in coerced[top + local_row])
        for top in range(1, height, STRIDE)
        for local_row in range(SW)
    ):
        errors.append("content rows must not imitate separator rows")
    if any(
        all(coerced[row][col] == 0 for row in range(height))
        for col in (1, 2)
    ):
        errors.append(
            "global columns 1 and 2 must establish shape width three"
        )

    colors = []
    patterns = []
    for band_index in range(n_bands):
        top = 1 + STRIDE * band_index
        band_patterns = []
        for section_index in range(n_sections):
            left = STRIDE * section_index
            cells = [
                coerced[top + row][left + col]
                for row in range(SW)
                for col in range(SW)
            ]
            nonzero = [value for value in cells if value != 0]
            unique_colors = set(nonzero)
            if len(unique_colors) != 1:
                errors.append(
                    "each band-section must use exactly one nonzero color"
                )
                band_patterns.append("".join(
                    "1" if value != 0 else "0" for value in cells
                ))
                continue
            color = nonzero[0]
            if band_index == 0:
                colors.append(color)
            elif color != colors[section_index]:
                errors.append("section colors must stay fixed across bands")
            mask = "".join(
                "1" if value != 0 else "0" for value in cells
            )
            if not 4 <= len(nonzero) <= 7:
                errors.append(
                    "every shape must contain four through seven cells"
                )
            if not _pattern_spans_box(mask):
                errors.append("every shape must span its complete 3x3 box")
            band_patterns.append(mask)
        patterns.append(tuple(band_patterns))

    if len(colors) == n_sections and len(set(colors)) != n_sections:
        errors.append("section colors must be distinct")
    if patterns and len(set(patterns[0])) != n_sections:
        errors.append("first-band shapes must be distinct")
    for band_index in range(1, len(patterns)):
        expected = tuple(
            patterns[band_index - 1][
                (section_index + 1) % n_sections
            ]
            for section_index in range(n_sections)
        )
        if patterns[band_index] != expected:
            errors.append(
                "each band must be the preceding shapes shifted left once"
            )

    if errors:
        return coerced, None, errors
    output = _apply_rule(coerced)
    return coerced, {
        "height": height,
        "width": width,
        "n_sections": n_sections,
        "n_bands": n_bands,
        "colors": tuple(colors),
        "patterns": tuple(patterns),
        "cell_counts": tuple(
            tuple(mask.count("1") for mask in band)
            for band in patterns
        ),
        "output": output,
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "n_sections": features["n_sections"],
        "n_bands": features["n_bands"],
    }


def rule_mirror(grid):
    return _apply_rule(grid)


def canonical_profile_index(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    signature = (
        features["n_sections"],
        features["n_bands"],
        features["patterns"],
    )
    return _PROFILE_SIGNATURE_TO_INDEX.get(signature)


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _draw_profile(index, rng):
    patterns = rng.choice(
        _profile_variants(_PROFILE_PATTERNS[index])
    )
    colors = rng.sample(list(range(1, 10)), len(patterns[0]))
    return _build_grid(patterns, colors)


def _draw_general(n_sections, n_bands, band, rng):
    count_ranges = {
        "easy": (4, 5),
        "medium": (4, 6),
        "hard": (5, 7),
    }
    lower, upper = count_ranges[band]
    candidates = [
        mask
        for mask in _GENERAL_MASKS
        if lower <= mask.count("1") <= upper
    ]
    base_patterns = tuple(rng.sample(candidates, n_sections))
    patterns = tuple(
        tuple(
            base_patterns[(section_index + band_index) % n_sections]
            for section_index in range(n_sections)
        )
        for band_index in range(n_bands)
    )
    colors = rng.sample(list(range(1, 10)), n_sections)
    return _build_grid(patterns, colors)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_PATTERNS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            profile_index,
            ctx.draw_rng("profile_transform"),
        )
        observed = observe_overrides(grid)
        for label in AXES:
            ctx.draw_choice(label, (observed[label],))
    else:
        section_options = {
            "easy": (3, 3, 4),
            "medium": (3, 4, 4),
            "hard": (4, 4, 5),
        }[band]
        band_options = {
            "easy": (1, 1, 2),
            "medium": (1, 2, 2, 3),
            "hard": (2, 3, 3),
        }[band]
        if overrides.get("n_sections") is not None:
            section_options = (3, 4, 5)
        if overrides.get("n_bands") is not None:
            band_options = (1, 2, 3)
        n_sections = ctx.draw_choice("n_sections", section_options)
        n_bands = ctx.draw_choice("n_bands", band_options)
        grid = _draw_general(
            n_sections,
            n_bands,
            band,
            ctx.draw_rng("patterns"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
