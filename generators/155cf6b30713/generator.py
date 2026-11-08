"""Generator for ARC task 155cf6b30713.

Each input contains three equal square panels separated by full color-5 columns.
The first two panels demonstrate a non-identity D4 transform and a color map.
The same transform and map are applied to the third panel; query colors absent
from the demonstrated map pass through unchanged.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "155cf6b30713"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "c4019681eb48"
SUMMARY = (
    "Infer an exact-position dihedral transform and color mapping from panels "
    "1→2, then apply both to panel 3 while preserving unmapped query colors."
)
EXAMPLES_NEEDED = 2

INVARIANTS = [
    "the input is three equal 4..6 square panels separated by full color-5 columns",
    "panel 2 has exactly the transformed support of panel 1 and a consistent nonzero color map",
    "the learned transform is a unique non-identity D4 transform in exact panel coordinates",
    "the query output applies the learned geometry and recolors only mapped source colors",
    "generated lessons are sparse canonical-profile anchors and contain mapped plus unmapped query colors",
]

_CODES = ("r1", "r2", "r3", "fh", "fv", "tr", "atr")
_ALL_CODES = ("id", *_CODES)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "transform": {
        "type": "enum",
        "default": "rng",
        "valid": "r1|r2|r3|fh|fv|tr|atr",
    },
    "panel_size": {
        "type": "int",
        "default": "rng 4..6",
        "valid": "4..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


def _validate_generate_args(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    if "panel_size" in overrides:
        value = overrides["panel_size"]
        if type(value) is not int:
            raise TypeError("panel_size override must be an integer (not bool)")
        if not 4 <= value <= 6:
            raise ValueError("panel_size override must be in 4..6")
    if "transform" in overrides:
        value = overrides["transform"]
        if type(value) is not str:
            raise TypeError("transform override must be a string")
        if value not in _CODES:
            raise ValueError(f"transform override must be one of {_CODES}")


def _xform_grid(grid, code):
    """Apply one exact D4 transform to a rectangular grid without mutation."""
    h = len(grid)
    w = len(grid[0])
    if code == "id":
        return [list(row) for row in grid]
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [
            [grid[h - 1 - r][w - 1 - c] for c in range(w)]
            for r in range(h)
        ]
    if code == "r3":
        return [[grid[r][w - 1 - c] for r in range(h)] for c in range(w)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    if code == "fv":
        return list(reversed([list(row) for row in grid]))
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    if code == "atr":
        return [
            [grid[h - 1 - c][w - 1 - r] for c in range(h)]
            for r in range(w)
        ]
    raise ValueError(f"unknown D4 transform {code!r}")


def _support(grid):
    """Exact-position binary support; unlike the old validator, never translate."""
    return tuple(tuple(value != 0 for value in row) for row in grid)


def _d4_unique(grid):
    return len({_support(_xform_grid(grid, code)) for code in _ALL_CODES}) == 8


def _split_panels(grid):
    p = len(grid)
    return [
        [list(row[start : start + p]) for row in grid]
        for start in (0, p + 1, 2 * p + 2)
    ]


def _matching_transforms(ex_in, ex_out):
    wanted = _support(ex_out)
    return [
        code for code in _CODES if _support(_xform_grid(ex_in, code)) == wanted
    ]


def _mapping_for(ex_in, ex_out, code):
    transformed = _xform_grid(ex_in, code)
    mapping = {}
    for source_row, target_row in zip(transformed, ex_out):
        for source, target in zip(source_row, target_row):
            if source == 0:
                if target != 0:
                    raise ValueError("panel 2 adds foreground outside transformed support")
                continue
            if target == 0:
                raise ValueError("panel 2 deletes transformed foreground")
            previous = mapping.setdefault(source, target)
            if previous != target:
                raise ValueError(
                    f"source color {source} maps inconsistently to {previous} and {target}"
                )
    return mapping


def infer_relation(grid):
    """Return the first authority-order transform and its demonstrated map."""
    ex_in, ex_out, _query = _split_panels(grid)
    matches = _matching_transforms(ex_in, ex_out)
    if not matches:
        raise ValueError("example panels do not demonstrate a non-identity D4 transform")
    code = matches[0]
    return code, _mapping_for(ex_in, ex_out, code)


def _apply_mapping(grid, mapping, *, drop_unmapped=False):
    out = []
    for row in grid:
        out_row = []
        for value in row:
            if value == 0:
                out_row.append(0)
            elif value in mapping:
                out_row.append(mapping[value])
            elif drop_unmapped:
                out_row.append(0)
            else:
                out_row.append(value)
        out.append(out_row)
    return out


def rule_mirror(grid):
    """Supplemental Python mirror of the selected Racket authority."""
    code, mapping = infer_relation(grid)
    query = _split_panels(grid)[2]
    return _apply_mapping(_xform_grid(query, code), mapping)


def _component_sizes(n_colors, n_cells):
    if (n_colors, n_cells) == (2, 4):
        return [2, 2]
    if (n_colors, n_cells) == (2, 5):
        return [2, 3]
    if (n_colors, n_cells) == (3, 5):
        return [2, 2, 1]
    raise ValueError(f"unsupported sparse component profile {(n_colors, n_cells)}")


def _random_panel(rng, p, colors, n_cells):
    """Draw one connected support whose per-color pieces are connected.

    A short self-avoiding path mirrors the canonical 2+2 / 2+3 colored
    components instead of scattering singleton markers across the panel.
    """
    sizes = _component_sizes(len(colors), n_cells)
    for _attempt in range(64):
        path = [(rng.randrange(p), rng.randrange(p))]
        while len(path) < n_cells:
            r, c = path[-1]
            candidates = [
                (nr, nc)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                if 0 <= nr < p and 0 <= nc < p and (nr, nc) not in path
            ]
            if not candidates:
                break
            rng.shuffle(candidates)
            path.append(candidates[0])
        if len(path) != n_cells:
            continue

        color_order = list(colors)
        rng.shuffle(color_order)
        size_order = list(sizes)
        rng.shuffle(size_order)
        grid = full_grid(p, p, 0)
        cursor = 0
        for color, size in zip(color_order, size_order):
            for r, c in path[cursor : cursor + size]:
                grid[r][c] = color
            cursor += size
        return grid
    raise ValueError("could not draw a short connected sparse panel")


def _five_touches_right_separator(panel):
    return any(row[-1] == 5 for row in panel)


def _palette_profile(rng, sample_index, difficulty):
    """Return source, target, query colors and canonical foreground cell count.

    Profiles alternate deterministically so every band has both canonical input
    color counts.  The band offset changes the curriculum order without changing
    the lawful override domain.
    """
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    eight_color = (sample_index + offset) % 2 == 1
    legal = [1, 2, 3, 4, 6, 7, 8, 9]
    if eight_color:
        a, b, c, d, e, f = rng.sample(legal, 6)
        # Three demonstrated source/target colors plus a two-color mixed-role
        # query preserve the canonical training palette signature: the output
        # has exactly two input colors while five other input colors disappear.
        return (a, b, c), (d, e, f), (a, e), 5

    a, b, c = rng.sample(legal, 3)
    # Including separator color 5 inside panel 1 reproduces the canonical
    # five-color profile.  Target/query colors avoid 5, so no new divider is
    # introduced after transformation.
    return (5, a), (b, c), (a, b), 4


def _paste_panel(out, panel_index, panel):
    p = len(panel)
    left = panel_index * (p + 1)
    for r, row in enumerate(panel):
        out[r][left : left + p] = row


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_args(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    code = ctx.draw_choice("transform", _CODES)
    p = ctx.draw_int_strict("panel_size", 4, 6)
    band = difficulty or "default"
    palette_rng = ctx.draw_rng(f"palette:{band}")
    layout_rng = ctx.draw_rng(f"layout:{band}")
    source_colors, target_colors, query_colors, n_cells = _palette_profile(
        palette_rng, sample_index, difficulty
    )
    mapping = dict(zip(source_colors, target_colors))

    for _attempt in range(512):
        ex_in = _random_panel(layout_rng, p, source_colors, n_cells)
        query = _random_panel(layout_rng, p, query_colors, n_cells)
        if _five_touches_right_separator(ex_in):
            continue
        if not (_d4_unique(ex_in) and _d4_unique(query)):
            continue
        if _support(_xform_grid(query, code)) == _support(query):
            continue
        ex_out = _apply_mapping(_xform_grid(ex_in, code), mapping)
        break
    else:
        raise ValueError("could not realize sparse exact-D4-unique analogy panels")

    grid = full_grid(p, 3 * p + 2, 0)
    for separator in (p, 2 * p + 1):
        for r in range(p):
            grid[r][separator] = 5
    _paste_panel(grid, 0, ex_in)
    _paste_panel(grid, 1, ex_out)
    _paste_panel(grid, 2, query)
    return grid


def _grid_structure_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"grid cell ({r},{c}) must be an integer color 0..9 (not bool)"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_structure_errors(grid)
    if errors:
        return errors

    p = len(grid)
    width = len(grid[0])
    if not 4 <= p <= 6 or width != 3 * p + 2:
        return [
            f"expected p rows and 3p+2 columns for p in 4..6; got {p}x{width}"
        ]

    separators = [
        c for c in range(width) if all(grid[r][c] == 5 for r in range(p))
    ]
    expected_separators = [p, 2 * p + 1]
    if separators != expected_separators:
        return [
            f"expected exactly two full color-5 separators at {expected_separators}; "
            f"found {separators}"
        ]

    ex_in, ex_out, query = _split_panels(grid)
    panels = (ex_in, ex_out, query)
    nonzero_counts = [sum(value != 0 for row in panel for value in row) for panel in panels]
    if len(set(nonzero_counts)) != 1 or nonzero_counts[0] not in (4, 5):
        errors.append(
            f"panels must share canonical sparse foreground count 4 or 5; got {nonzero_counts}"
        )
    if any(not any(value != 0 for row in panel for value in row) for panel in panels):
        errors.append("all three panels need non-empty foreground")
    distinct_count = len({value for row in grid for value in row})
    if distinct_count not in (5, 8):
        errors.append(f"canonical input color profile must contain 5 or 8 colors; got {distinct_count}")
    example_input_colors = {value for row in ex_in for value in row if value}
    example_output_colors = {value for row in ex_out for value in row if value}
    if len(example_input_colors) not in (2, 3):
        errors.append("example input panel must use two or three nonzero colors")
    if len(example_output_colors) != len(example_input_colors):
        errors.append("example output panel must preserve the demonstrated color-role count")

    if not _d4_unique(ex_in):
        errors.append("example input support is not unique across all exact D4 transforms")
    matches = _matching_transforms(ex_in, ex_out)
    if len(matches) != 1:
        errors.append(
            f"example panels must imply exactly one non-identity exact-position transform; got {matches}"
        )
        return errors

    code = matches[0]
    try:
        mapping = _mapping_for(ex_in, ex_out, code)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    source_colors = {value for row in ex_in for value in row if value}
    if set(mapping) != source_colors:
        errors.append("every demonstrated source color must have one mapped target color")
    if len(set(mapping.values())) != len(mapping):
        errors.append("demonstrated target colors must be distinct")
    if any(source == target for source, target in mapping.items()):
        errors.append("the demonstrated recolor must change every source color")
    if _support(_xform_grid(query, code)) == _support(query):
        errors.append("query support is unchanged by the learned transform")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    if self_check(grid):
        return {}
    code, _mapping = infer_relation(grid)
    return {"panel_size": len(grid), "transform": code}


def _identity_query(grid):
    return deepcopy(_split_panels(grid)[2])


def _transform_only(grid):
    code, _mapping = infer_relation(grid)
    return _xform_grid(_split_panels(grid)[2], code)


def _recolor_only(grid):
    _code, mapping = infer_relation(grid)
    return _apply_mapping(_split_panels(grid)[2], mapping)


def _drop_unmapped(grid):
    code, mapping = infer_relation(grid)
    query = _xform_grid(_split_panels(grid)[2], code)
    return _apply_mapping(query, mapping, drop_unmapped=True)


def _unmixed_query_only(grid):
    """Canonical-fitting shortcut: assume mapped/pass-through roles never mix."""
    _code, mapping = infer_relation(grid)
    query_colors = {
        value for row in _split_panels(grid)[2] for value in row if value != 0
    }
    mapped = query_colors & set(mapping)
    unmapped = query_colors - set(mapping)
    if not mapped or not unmapped:
        return rule_mirror(grid)
    return _identity_query(grid)


def _transform_effect_witness(grid):
    expected = rule_mirror(grid)
    return expected != _identity_query(grid) and expected != _recolor_only(grid)


def _mapped_query_witness(grid):
    return rule_mirror(grid) != _transform_only(grid)


def _unmapped_query_witness(grid):
    return rule_mirror(grid) != _drop_unmapped(grid)


def _mixed_query_roles_witness(grid):
    return rule_mirror(grid) != _unmixed_query_only(grid)


SEMANTIC_WITNESSES = {
    "transform_changes_query": _transform_effect_witness,
    "mapped_query_color": _mapped_query_witness,
    "unmapped_query_color": _unmapped_query_witness,
    "mixed_mapped_and_unmapped_query_colors": _mixed_query_roles_witness,
}
SEMANTIC_RIVALS = {
    "identity_query": _identity_query,
    "transform_only": _transform_only,
    "recolor_only": _recolor_only,
    "drop_unmapped": _drop_unmapped,
    "unmixed_query_only": _unmixed_query_only,
}
WITNESS_RIVALS = {
    "transform_changes_query": ["identity_query", "recolor_only"],
    "mapped_query_color": ["transform_only"],
    "unmapped_query_color": ["drop_unmapped"],
    "mixed_mapped_and_unmapped_query_colors": ["unmixed_query_only"],
}
CANONICAL_SHORTCUTS = {"unmixed_query_only": _unmixed_query_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"{name} survives every demonstration and changes the query answer"
                )
    return reasons
