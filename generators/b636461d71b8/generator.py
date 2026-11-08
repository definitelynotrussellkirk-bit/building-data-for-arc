"""Generator for b636461d71b8 — dihedral match matrix.

A fixed 7x9 input contains four monochrome 3x3 binary panels at TL, TR, BL,
and BR.  The output is a 2x2 matrix: cell (r, c) is 8 exactly when top panel
r and bottom panel c are equal after cropping and any rotation/reflection.
Panel colors are nuisance labels and are deliberately all distinct.
"""
from __future__ import annotations

from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b636461d71b8"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "753f48cab523"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95
EXPECTED_OUTPUT_CODOMAIN = 11  # all nonempty 2x2 equality matrices reachable ordinarily

SUMMARY = (
    "A fixed 7x9 zero-background grid contains four monochrome five-cell "
    "panels in the 3x3 slots TL, TR, BL, and BR. The four panel colors are "
    "distinct nuisance labels. Crop each binary panel to its content. Output "
    "a 2x2 matrix with 8 at (r,c) exactly when top panel r and bottom panel c "
    "are equivalent under the full D4 group (rotation or reflection), else 0. "
    "The default sample-index schedule covers every output position, singleton "
    "and multi-match relations, reflection-only matches, and offset-only matches."
)

INVARIANTS = [
    "grid is exactly 7x9; row 3, columns 3..5, and all non-panel cells are zero",
    "each of the four 3x3 panels is monochrome and has exactly five nonzero cells",
    "the four panel colors are distinct and do not encode the relation",
    "ordinary draws contain at least one top-bottom D4 match",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Each palette has exactly four distinct nonzero colors.  The sets are unique,
# so observe_overrides can recover the selected mode from the returned grid.
_PALETTES = {
    "default": (1, 2, 3, 4),
    "warm": (2, 3, 4, 7),
    "cool": (1, 5, 6, 8),
    "varied": (2, 5, 7, 9),
}

# Matrix entries are in row-major order: (T0~B0, T0~B1, T1~B0, T1~B1).
_MATCH_PATTERNS = {
    "none": (0, 0, 0, 0),
    "single_tl": (1, 0, 0, 0),
    "single_tr": (0, 1, 0, 0),
    "single_bl": (0, 0, 1, 0),
    "single_br": (0, 0, 0, 1),
    "diagonal": (1, 0, 0, 1),
    "cross": (0, 1, 1, 0),
    "top_row": (1, 1, 0, 0),
    "bottom_row": (0, 0, 1, 1),
    "left_col": (1, 0, 1, 0),
    "right_col": (0, 1, 0, 1),
    "all": (1, 1, 1, 1),
}
_PATTERN_NAME = {value: name for name, value in _MATCH_PATTERNS.items()}

# Every lesson begins with the same four structurally complementary demos.
# They jointly place a positive in every output cell, contain multi-match
# examples, and exercise reflection-only and crop-offset positives at sample
# indices 1 and 3.  The two query slots vary by seed; across ordinary draws
# this exposes all eleven nonempty relation matrices without weakening the
# four-example teaching contract.
_LESSON_PREFIX = (
    "single_tl",
    "single_br",
    "cross",
    "top_row",
)
_QUERY_PATTERN_PAIRS = (
    ("diagonal", "single_tr"),
    ("single_bl", "bottom_row"),
    ("left_col", "right_col"),
    ("all", "single_tl"),
)
_ORDINARY_PATTERNS = tuple(name for name in _MATCH_PATTERNS if name != "none")

AXES = {
    "grid_h": {"type": "int", "default": "7", "valid": "7"},
    "grid_w": {"type": "int", "default": "9", "valid": "9"},
    "match_pattern": {
        "type": "enum",
        "default": "sample-index teaching schedule",
        "valid": "none|single_tl|single_tr|single_bl|single_br|diagonal|cross|top_row|bottom_row|left_col|right_col|all",
    },
    "palette_kind": {
        "type": "enum",
        "default": "difficulty-linked nuisance palette",
        "valid": "default|warm|cool|varied",
    },
}

_SLOT_ORIGINS = ((0, 0), (0, 6), (4, 0), (4, 6))
_PANEL_POSITIONS = {
    (sr + r, sc + c)
    for sr, sc in _SLOT_ORIGINS
    for r in range(3)
    for c in range(3)
}


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate(mask):
    return _normalize((c, -r) for r, c in mask)


def _reflect(mask):
    return _normalize((r, -c) for r, c in mask)


def _rotation_orbit(mask):
    variants = set()
    current = _normalize(mask)
    for _ in range(4):
        variants.add(current)
        current = _rotate(current)
    return tuple(sorted(variants))


def _d4_orbit(mask):
    rotations = _rotation_orbit(mask)
    return tuple(sorted(set(rotations) | {_reflect(v) for v in rotations}))


def _dclass(mask):
    return min(_d4_orbit(mask))


def _rotation_class(mask):
    return min(_rotation_orbit(mask))


def _bbox_size(mask):
    normalized = _normalize(mask)
    return (
        max(r for r, _ in normalized) + 1,
        max(c for _, c in normalized) + 1,
    )


# Enumerate every D4 class of a five-cell binary pattern inside a 3x3 panel.
# This includes all canonical classes and avoids a hand-picked texture leak.
_MOTIFS = tuple(
    sorted(
        {
            _dclass((divmod(index, 3) for index in chosen))
            for chosen in combinations(range(9), 5)
        }
    )
)
_NONTRIVIAL_MOTIF_IDS = tuple(
    index for index, motif in enumerate(_MOTIFS) if len(_d4_orbit(motif)) > 1
)
_CHIRAL_MOTIF_IDS = tuple(
    index
    for index, motif in enumerate(_MOTIFS)
    if len(_d4_orbit(motif)) > len(_rotation_orbit(motif))
)
_SHIFTABLE_MOTIF_IDS = tuple(
    index
    for index, motif in enumerate(_MOTIFS)
    if any(min(_bbox_size(v)) < 3 for v in _d4_orbit(motif))
    and len(_d4_orbit(motif)) > 1
)


def _canonicalize_labels(labels):
    mapping = {}
    out = []
    for label in labels:
        if label not in mapping:
            mapping[label] = len(mapping)
        out.append(mapping[label])
    return tuple(out)


def _matrix_for_labels(labels):
    t0, t1, b0, b1 = labels
    return (int(t0 == b0), int(t0 == b1), int(t1 == b0), int(t1 == b1))


_PATTERN_ASSIGNMENTS = {}
for _name, _pattern in _MATCH_PATTERNS.items():
    _assignments = {
        _canonicalize_labels(labels)
        for labels in product(range(4), repeat=4)
        if _matrix_for_labels(labels) == _pattern
    }
    _PATTERN_ASSIGNMENTS[_name] = tuple(sorted(_assignments))


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for axis in ("grid_h", "grid_w"):
        value = overrides.get(axis)
        if value is not None and type(value) is not int:
            raise ValueError(f"{axis} must be an integer")
    for axis in ("match_pattern", "palette_kind"):
        value = overrides.get(axis)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{axis} must be a string")


def _draw_pinned_choice(ctx, overrides, label, default, options):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _draw_fixed_int(ctx, label, value):
    return ctx.draw_int(label, value, value)


def _choose_motif_ids(rng, labels, mode):
    distinct_labels = sorted(set(labels))
    matched_labels = [
        label
        for label in distinct_labels
        if any(labels[index] == label for index in (0, 1))
        and any(labels[index] == label for index in (2, 3))
    ]
    special_label = matched_labels[0] if matched_labels else None
    chosen = {}
    used = set()
    for label in distinct_labels:
        if label == special_label and mode == "reflection":
            pool = _CHIRAL_MOTIF_IDS
        elif label == special_label and mode == "shifted":
            pool = _SHIFTABLE_MOTIF_IDS
        elif label in matched_labels:
            pool = _NONTRIVIAL_MOTIF_IDS
        else:
            pool = tuple(range(len(_MOTIFS)))
        available = [index for index in pool if index not in used]
        if not available:
            available = [index for index in range(len(_MOTIFS)) if index not in used]
        motif_id = rng.choice(available)
        chosen[label] = motif_id
        used.add(motif_id)
    return chosen, special_label


def _offset_options(variant):
    height, width = _bbox_size(variant)
    return tuple(
        (row, col)
        for row in range(4 - height)
        for col in range(4 - width)
    )


def _place_variant(variant, offset):
    row, col = offset
    return tuple(sorted((row + r, col + c) for r, c in variant))


def _realize_label_occurrences(rng, motif, positions, mode, is_special):
    orbit = list(_d4_orbit(motif))
    base = rng.choice(orbit)
    if is_special and mode == "reflection":
        other = _reflect(base)
        # Chiral motifs guarantee this is not reachable by rotation alone.
        if other in _rotation_orbit(base):
            alternatives = [v for v in orbit if v not in _rotation_orbit(base)]
            other = rng.choice(alternatives)
    elif is_special and mode == "shifted":
        other = base
    else:
        alternatives = [variant for variant in orbit if variant != base]
        other = rng.choice(alternatives) if alternatives else base

    top_positions = [position for position in positions if position < 2]
    bottom_positions = [position for position in positions if position >= 2]
    realized = {}
    first_offset = None
    for group, variant in ((top_positions, base), (bottom_positions, other)):
        for occurrence_index, position in enumerate(group):
            current = variant
            if occurrence_index and len(orbit) > 1:
                current = orbit[(orbit.index(variant) + occurrence_index) % len(orbit)]
            options = list(_offset_options(current))
            if is_special and mode == "shifted" and first_offset is not None:
                different = [offset for offset in options if offset != first_offset]
                if different:
                    options = different
            offset = rng.choice(options)
            if first_offset is None:
                first_offset = offset
            realized[position] = _place_variant(current, offset)
    return realized


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
    height = _draw_fixed_int(ctx, "grid_h", 7)
    width = _draw_fixed_int(ctx, "grid_w", 9)

    lesson_variant = int(seed) % len(_QUERY_PATTERN_PAIRS)
    if sample_index < len(_LESSON_PREFIX):
        default_pattern = _LESSON_PREFIX[sample_index]
    elif sample_index < len(_LESSON_PREFIX) + 2:
        default_pattern = _QUERY_PATTERN_PAIRS[lesson_variant][
            sample_index - len(_LESSON_PREFIX)
        ]
    else:
        default_pattern = _ORDINARY_PATTERNS[
            (sample_index + 2 * lesson_variant) % len(_ORDINARY_PATTERNS)
        ]
    pattern_name = _draw_pinned_choice(
        ctx, overrides, "match_pattern", default_pattern, tuple(_MATCH_PATTERNS)
    )
    default_palette = {
        None: "varied",
        "easy": "default",
        "medium": "warm",
        "hard": "cool",
    }[difficulty]
    palette_kind = _draw_pinned_choice(
        ctx, overrides, "palette_kind", default_palette, PALETTE_KINDS
    )

    layout_rng = ctx.draw_rng("layout")
    labels = layout_rng.choice(_PATTERN_ASSIGNMENTS[pattern_name])
    mode = {
        0: "rotation",
        1: "reflection",
        2: "rotation",
        3: "shifted",
    }.get(sample_index, "mixed")
    motif_ids, special_label = _choose_motif_ids(layout_rng, labels, mode)

    local_cells = [None, None, None, None]
    for label in sorted(set(labels)):
        positions = [index for index, value in enumerate(labels) if value == label]
        realized = _realize_label_occurrences(
            layout_rng,
            _MOTIFS[motif_ids[label]],
            positions,
            mode,
            label == special_label,
        )
        for position, cells in realized.items():
            local_cells[position] = cells

    colors = list(_PALETTES[palette_kind])
    layout_rng.shuffle(colors)
    grid = full_grid(height, width, 0)
    for (slot_row, slot_col), cells, color in zip(
        _SLOT_ORIGINS, local_cells, colors
    ):
        for row, col in cells:
            grid[slot_row + row][slot_col + col] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid dihedral lesson: " + "; ".join(errors))
    if pattern_name != "none" and not any(_MATCH_PATTERNS[pattern_name]):
        raise AssertionError("ordinary match pattern unexpectedly has no positive")
    return grid


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty row sequence")
    rows = []
    for row in grid:
        if isinstance(row, str):
            rows.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            rows.append(list(row))
        else:
            raise ValueError("grid contains a non-row value")
    return rows


def _analyze(grid):
    errors = []
    try:
        g = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    widths = {len(row) for row in g}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    height, width = len(g), len(g[0])
    if (height, width) != (7, 9):
        errors.append(f"grid must be 7x9, got {height}x{width}")
    invalid = [
        (row, col, value)
        for row, values in enumerate(g)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if invalid:
        errors.append(f"grid contains invalid ARC color at {invalid[0][:2]}")
        return {"errors": errors}
    if (height, width) != (7, 9):
        return {"errors": errors}

    foreign = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in _PANEL_POSITIONS and g[row][col] != 0
    ]
    if foreign:
        errors.append(f"non-panel cell {foreign[0]} must be zero")

    panels = []
    for name, (slot_row, slot_col) in zip(("TL", "TR", "BL", "BR"), _SLOT_ORIGINS):
        cells = [
            (row, col)
            for row in range(3)
            for col in range(3)
            if g[slot_row + row][slot_col + col] != 0
        ]
        colors = {
            g[slot_row + row][slot_col + col]
            for row, col in cells
        }
        if len(cells) != 5:
            errors.append(f"panel {name} has {len(cells)} cells, expected 5")
        if len(colors) != 1:
            errors.append(f"panel {name} has {len(colors)} nonzero colors, expected 1")
        panels.append({
            "name": name,
            "cells": tuple(sorted(cells)),
            "normalized": _normalize(cells),
            "color": next(iter(colors)) if len(colors) == 1 else None,
        })
    panel_colors = [panel["color"] for panel in panels if panel["color"] is not None]
    if len(panel_colors) == 4 and len(set(panel_colors)) != 4:
        errors.append("the four panel colors must be distinct nuisance labels")

    pattern = None
    if all(panel["normalized"] for panel in panels):
        pattern = tuple(
            int(_dclass(panels[top]["normalized"]) == _dclass(panels[bottom]["normalized"]))
            for top, bottom in ((0, 2), (0, 3), (1, 2), (1, 3))
        )
        if pattern not in _PATTERN_NAME:
            errors.append(f"unrealizable relation matrix {pattern!r}")

    reflection_only = False
    orientation_changed = False
    offset_only = False
    if pattern is not None:
        for matrix_index, (top, bottom) in enumerate(((0, 2), (0, 3), (1, 2), (1, 3))):
            if not pattern[matrix_index]:
                continue
            top_panel, bottom_panel = panels[top], panels[bottom]
            if _rotation_class(top_panel["normalized"]) != _rotation_class(bottom_panel["normalized"]):
                reflection_only = True
            if top_panel["normalized"] != bottom_panel["normalized"]:
                orientation_changed = True
            elif top_panel["cells"] != bottom_panel["cells"]:
                offset_only = True

    return {
        "errors": errors,
        "grid": g,
        "grid_h": height,
        "grid_w": width,
        "panels": panels,
        "panel_colors": tuple(panel_colors),
        "pattern": pattern,
        "match_pattern": _PATTERN_NAME.get(pattern),
        "match_count": sum(pattern) if pattern is not None else None,
        "reflection_only_positive": reflection_only,
        "orientation_changed_positive": orientation_changed,
        "offset_only_positive": offset_only,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    palette_set = frozenset(analysis["panel_colors"])
    palette_kind = next(
        (name for name, colors in _PALETTES.items() if frozenset(colors) == palette_set),
        None,
    )
    observed = {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "match_pattern": analysis["match_pattern"],
    }
    if palette_kind is not None:
        observed["palette_kind"] = palette_kind
    return observed


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def semantic_observables(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    pattern = analysis["pattern"]
    return {
        **observe_overrides(grid),
        "pattern": pattern,
        "match_count": analysis["match_count"],
        "singleton": analysis["match_count"] == 1,
        "multi_match": analysis["match_count"] >= 2,
        "diagonal_positive": bool(pattern[0] or pattern[3]),
        "off_diagonal_positive": bool(pattern[1] or pattern[2]),
        "reflection_only_positive": analysis["reflection_only_positive"],
        "orientation_changed_positive": analysis["orientation_changed_positive"],
        "offset_only_positive": analysis["offset_only_positive"],
        "four_distinct_panel_colors": len(set(analysis["panel_colors"])) == 4,
    }


def strict_canonical_like(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["match_count"] == 0:
        return ["canonical lessons contain at least one positive relation"]
    return []


def _witness(grid, predicate):
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(predicate(observables))


SEMANTIC_WITNESSES = {
    "canonical_diagonal_singleton": lambda grid: _witness(
        grid,
        lambda obs: obs["match_pattern"] in {"single_tl", "single_br"},
    ),
    "off_diagonal_singleton": lambda grid: _witness(
        grid,
        lambda obs: obs["match_pattern"] in {"single_tr", "single_bl"},
    ),
    "multi_match": lambda grid: _witness(grid, lambda obs: obs["multi_match"]),
    "cross_relation": lambda grid: _witness(
        grid, lambda obs: obs["match_pattern"] == "cross"
    ),
    "row_shared_class": lambda grid: _witness(
        grid, lambda obs: obs["match_pattern"] in {"top_row", "bottom_row"}
    ),
    "column_shared_class": lambda grid: _witness(
        grid, lambda obs: obs["match_pattern"] in {"left_col", "right_col"}
    ),
    "all_four_relations": lambda grid: _witness(
        grid, lambda obs: obs["match_pattern"] == "all"
    ),
    "reflection_only_positive": lambda grid: _witness(
        grid, lambda obs: obs["reflection_only_positive"]
    ),
    "offset_only_positive": lambda grid: _witness(
        grid, lambda obs: obs["offset_only_positive"]
    ),
    "four_distinct_nuisance_colors": lambda grid: _witness(
        grid, lambda obs: obs["four_distinct_panel_colors"]
    ),
}


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    pattern = analysis["pattern"]
    return [
        [8 if pattern[0] else 0, 8 if pattern[1] else 0],
        [8 if pattern[2] else 0, 8 if pattern[3] else 0],
    ]


def _relation_matrix(grid, equivalence):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    panels = analysis["panels"]
    values = []
    for top, bottom in ((0, 2), (0, 3), (1, 2), (1, 3)):
        values.append(8 if equivalence(panels[top], panels[bottom]) else 0)
    return [values[:2], values[2:]]


def _exact_orientation_rule(grid):
    return _relation_matrix(
        grid, lambda left, right: left["normalized"] == right["normalized"]
    )


def _rotation_only_rule(grid):
    return _relation_matrix(
        grid,
        lambda left, right: _rotation_class(left["normalized"])
        == _rotation_class(right["normalized"]),
    )


def _cell_count_rule(grid):
    return _relation_matrix(
        grid, lambda left, right: len(left["cells"]) == len(right["cells"])
    )


def _same_color_rule(grid):
    return _relation_matrix(grid, lambda left, right: left["color"] == right["color"])


def _transpose_rule(grid):
    truth = rule_mirror(grid)
    return [[truth[0][0], truth[1][0]], [truth[0][1], truth[1][1]]]


def _first_positive_only_rule(grid):
    truth = rule_mirror(grid)
    out = [[0, 0], [0, 0]]
    for row in range(2):
        for col in range(2):
            if truth[row][col] == 8:
                out[row][col] = 8
                return out
    return out


_COMPETITORS = {
    "exact cropped orientation only": _exact_orientation_rule,
    "rotation but not reflection": _rotation_only_rule,
    "equal cell count": _cell_count_rule,
    "equal panel color": _same_color_rule,
    "transpose the relation matrix": _transpose_rule,
    "keep only the first positive": _first_positive_only_rule,
}


def lesson_identifiable(demos, query):
    reasons = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if self_check(query_input):
        return ["query input is not a lawful four-panel relation scene"]
    query_truth = rule_mirror(query_input)
    if query.get("output") != query_truth:
        reasons.append("query output disagrees with the D4 relation rule")

    positive_support = set()
    has_multi = False
    has_reflection_only = False
    has_offset_only = False
    outputs = set()
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} is invalid: {errors[0]}")
            continue
        truth = rule_mirror(demo_input)
        if demo.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with the D4 relation rule")
            continue
        outputs.add(tuple(tuple(row) for row in truth))
        obs = semantic_observables(demo_input)
        pattern = obs["pattern"]
        positive_support.update(i for i, value in enumerate(pattern) if value)
        has_multi |= obs["multi_match"]
        has_reflection_only |= obs["reflection_only_positive"]
        has_offset_only |= obs["offset_only_positive"]

    if positive_support != {0, 1, 2, 3}:
        reasons.append(
            f"demo positives cover matrix positions {sorted(positive_support)}, expected all four"
        )
    if not has_multi:
        reasons.append("demos contain no multi-match relation matrix")
    if not has_reflection_only:
        reasons.append("demos contain no positive requiring reflection rather than rotation")
    if not has_offset_only:
        reasons.append("demos contain no positive requiring crop/offset normalization")
    if len(outputs) < 3:
        reasons.append("demos expose fewer than three distinct output matrices")
    if reasons:
        return reasons

    for name, competitor in _COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            alternative = competitor(query_input)
            if alternative != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor '{name}', which changes the query"
                )
    return reasons
