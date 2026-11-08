"""Lawful instances for H141: infer a dihedral transform and recolor A→B.

Each input is three 3×3 panels separated by full cyan (8) columns.  Panel B
is a non-identity D4 transform of panel A followed by a consistent, visible
recolor.  Panel C uses exactly A's source palette.  The canonical Racket rule
infers the first matching transform/mapping under a declared D4 precedence and
applies both to C.  Transpose precedes anti-transpose when symmetric panels tie.

Generated scenes deliberately make A and C D4-asymmetric, so the intended
transform is unique and every wrong transform changes the query answer.  The
one evidence-ambiguous canonical test is resolved by the selected precedence;
generated data never reproduces that ambiguity.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "6c88f7697696"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "09a64aa644b8"

SUMMARY = (
    "Three 3×3 panels are separated by full cyan (8) columns. Panel B is a "
    "uniquely inferable non-identity rotation/reflection of panel A followed "
    "by a consistent non-identity recolor. Panel C uses the same source "
    "palette; output is C after that same transform and recolor."
)

INVARIANTS = [
    "the input is exactly 3×11 with full color-8 divider columns 3 and 7",
    "the three 3×3 panels contain no divider color and use background 0",
    "panel B has the support of exactly one non-identity D4 transform of panel A on generated draws",
    "A→B defines an injective source-to-target mapping and every source color changes",
    "panel C uses exactly the source palette established by panel A",
    "generated A and C supports have trivial D4 stabilizers, so wrong transforms change the query answer",
    "ambiguous canonical panels use the declared D4 precedence, with transpose before anti-transpose",
    "the canonical Racket rule remains the sole output authority",
]

TRANSFORMS = ("r1", "r2", "r3", "fh", "fv", "tr", "atr")
TRANSFORM_PRECEDENCE = ("id",) + TRANSFORMS
_TRANSFORM_ORDER = TRANSFORM_PRECEDENCE
_COLOR_POOL = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "transform": {
        "type": "enum",
        "default": "linked 14-profile schedule",
        "valid": ["r1", "r2", "r3", "fh", "fv", "tr", "atr"],
        "doc": "The uniquely inferable A→B dihedral transform.",
    },
    "source_color_count": {
        "type": "int",
        "default": "linked 14-profile schedule",
        "valid": "1..3",
        "doc": "Number of source colors present in both A and C.",
    },
    "a_cells": {
        "type": "int",
        "default": "linked 14-profile schedule",
        "valid": "3..7",
        "doc": "Number of non-background cells in panel A.",
    },
    "c_cells": {
        "type": "int",
        "default": "linked 14-profile schedule",
        "valid": "3..7",
        "doc": "Number of non-background cells in panel C.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95

# Every consecutive pair contains different transforms and at least one
# multi-color mapping.  The second seven profiles repeat every transform with
# different color/count morphology.  Difficulty only changes the phase.
_PROFILES = (
    ("r1", 1, 5, 6, "disjoint"),
    ("r2", 2, 6, 5, "permuted"),
    ("r3", 3, 5, 4, "disjoint"),
    ("fh", 2, 4, 6, "disjoint"),
    ("fv", 1, 6, 5, "disjoint"),
    ("tr", 3, 5, 4, "permuted"),
    ("atr", 2, 4, 5, "disjoint"),
    ("r1", 3, 6, 3, "permuted"),
    ("r2", 2, 4, 6, "disjoint"),
    ("r3", 1, 5, 4, "disjoint"),
    ("fh", 3, 6, 5, "disjoint"),
    ("fv", 2, 5, 6, "permuted"),
    ("tr", 1, 4, 4, "disjoint"),
    ("atr", 2, 6, 5, "disjoint"),
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))

# Exact canonical inputs.  The third one admits both transpose and
# anti-transpose from A→B while those transforms disagree on C.  The selected
# rule resolves that tie by its declared precedence; generation still avoids
# ambiguity so every synthetic lesson identifies the transform from evidence.
_CANONICAL_INPUTS = {
    (
        (1, 0, 2, 8, 4, 0, 3, 8, 1, 1, 0),
        (1, 2, 2, 8, 4, 4, 3, 8, 0, 2, 0),
        (0, 2, 0, 8, 0, 4, 0, 8, 0, 2, 2),
    ),
    (
        (5, 0, 0, 8, 0, 2, 2, 8, 0, 5, 0),
        (5, 6, 6, 8, 0, 7, 0, 8, 5, 5, 6),
        (0, 0, 6, 8, 7, 7, 0, 8, 0, 0, 6),
    ),
    (
        (4, 4, 0, 8, 6, 0, 0, 8, 4, 0, 0),
        (0, 4, 0, 8, 6, 6, 6, 8, 4, 4, 0),
        (0, 4, 4, 8, 0, 0, 6, 8, 0, 4, 0),
    ),
}


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _transform_grid(grid: Sequence[Sequence[int]], code: str) -> list[list[int]]:
    """Apply the same D4 naming convention as the canonical Racket rule."""
    src = [list(row) for row in grid]
    if code == "id":
        return [row[:] for row in src]
    if code == "r1":  # rotate clockwise
        return [list(row) for row in zip(*src[::-1])]
    if code == "r2":
        return [row[::-1] for row in src[::-1]]
    if code == "r3":  # rotate counter-clockwise
        return [list(row) for row in zip(*src)][::-1]
    if code == "fh":  # horizontal-axis name in authority = left/right flip
        return [row[::-1] for row in src]
    if code == "fv":
        return [row[:] for row in src[::-1]]
    if code == "tr":
        return [list(row) for row in zip(*src)]
    if code == "atr":
        transposed = [list(row) for row in zip(*src)]
        return [row[::-1] for row in transposed[::-1]]
    raise ValueError(f"unknown transform {code!r}")


def _recolor(grid: Sequence[Sequence[int]], mapping: dict[int, int]) -> list[list[int]]:
    return [[mapping.get(value, value) for value in row] for row in grid]


def _support(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    )


def _support_grid(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    out = full_grid(3, 3, 0)
    for r, c in cells:
        out[r][c] = 1
    return out


def _orbit_signatures(grid: Sequence[Sequence[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(sorted({_support(_transform_grid(grid, code)) for code in _TRANSFORM_ORDER}))


def _orbit_key(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return min(_orbit_signatures(grid))


def _build_mask_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    positions = tuple((r, c) for r in range(3) for c in range(3))
    bank: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for count in range(3, 8):
        masks = []
        for cells in combinations(positions, count):
            if len(_orbit_signatures(_support_grid(cells))) == 8:
                masks.append(tuple(cells))
        bank[count] = tuple(masks)
    return bank


_MASKS_BY_COUNT = _build_mask_bank()


def _split_panels(grid: Sequence[Sequence[int]]) -> tuple[list[list[int]], ...]:
    return tuple(
        [[row[c] for c in range(left, left + 3)] for row in grid]
        for left in (0, 4, 8)
    )


def _candidate_transforms(
    a: Sequence[Sequence[int]], b: Sequence[Sequence[int]]
) -> list[tuple[str, dict[int, int]]]:
    candidates: list[tuple[str, dict[int, int]]] = []
    for code in _TRANSFORM_ORDER:
        transformed = _transform_grid(a, code)
        mapping: dict[int, int] = {}
        valid = True
        for r in range(3):
            for c in range(3):
                source = transformed[r][c]
                target = b[r][c]
                if (source == 0) != (target == 0):
                    valid = False
                    break
                if source != 0:
                    prior = mapping.get(source)
                    if prior is not None and prior != target:
                        valid = False
                        break
                    mapping[source] = target
            if not valid:
                break
        if valid:
            candidates.append((code, mapping))
    return candidates


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analyze(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    if (h, w) != (3, 11):
        return {"errors": [f"expected a 3x11 input, got {h}x{w}"]}

    errors = []
    canonical_input = _freeze(grid) in _CANONICAL_INPUTS
    for col in (3, 7):
        if any(grid[row][col] != 8 for row in range(3)):
            errors.append(f"column {col} must be a full color-8 divider")
    extra_eights = [
        (r, c)
        for r in range(3)
        for c in range(11)
        if c not in (3, 7) and grid[r][c] == 8
    ]
    if extra_eights:
        errors.append("color 8 may appear only in the two divider columns")
    if errors:
        return {"errors": errors, "canonical_input": canonical_input}

    a, b, c = _split_panels(grid)
    a_palette = {value for row in a for value in row if value}
    b_palette = {value for row in b for value in row if value}
    c_palette = {value for row in c for value in row if value}
    a_cells = len(_support(a))
    c_cells = len(_support(c))

    if not 1 <= len(a_palette) <= 3:
        errors.append(f"panel A must use 1..3 source colors, found {len(a_palette)}")
    if c_palette != a_palette:
        errors.append(
            f"panel C palette {sorted(c_palette)} must equal panel A palette {sorted(a_palette)}"
        )
    if not 3 <= a_cells <= 7:
        errors.append(f"panel A must contain 3..7 non-background cells, found {a_cells}")
    if not 3 <= c_cells <= 7:
        errors.append(f"panel C must contain 3..7 non-background cells, found {c_cells}")

    candidates = _candidate_transforms(a, b)
    if not candidates:
        errors.append("no D4 transform plus consistent recolor maps panel A to panel B")
        selected_code, mapping = None, {}
    else:
        selected_code, mapping = candidates[0]
        if len(candidates) != 1 and not canonical_input:
            errors.append(
                "A→B admits multiple transform/recolor explanations: "
                + ", ".join(code for code, _ in candidates)
            )
        if selected_code == "id":
            errors.append("identity A→B transform hides the intended operation")
        if set(mapping) != a_palette:
            errors.append("A→B mapping does not define every source color")
        if len(set(mapping.values())) != len(mapping):
            errors.append("A→B recolor must be injective")
        fixed = sorted(source for source, target in mapping.items() if source == target)
        if fixed:
            errors.append(f"source colors map to themselves: {fixed}")
        if set(mapping.values()) != b_palette:
            errors.append("panel B palette must be exactly the mapping targets")

    a_orbit_size = len(_orbit_signatures(a))
    c_orbit_size = len(_orbit_signatures(c))
    same_orbit = _orbit_key(a) == _orbit_key(c)
    if not canonical_input:
        if a_orbit_size != 8:
            errors.append(f"panel A support has only {a_orbit_size}/8 distinct D4 variants")
        if c_orbit_size != 8:
            errors.append(f"panel C support has only {c_orbit_size}/8 distinct D4 variants")
        if same_orbit:
            errors.append("panels A and C must come from different D4 support orbits")

    truth = transform_only = recolor_only = None
    if selected_code is not None and mapping:
        transform_only = _transform_grid(c, selected_code)
        recolor_only = _recolor(c, mapping)
        truth = _recolor(transform_only, mapping)
        if truth == [list(row) for row in c]:
            errors.append("query answer equals panel C unchanged")
        if truth == transform_only:
            errors.append("recolor is not visible in the query answer")
        if truth == recolor_only:
            errors.append("transform is not visible in the query answer")

    relation = None
    if a_palette and b_palette:
        relation = "permuted" if a_palette == b_palette else "disjoint" if a_palette.isdisjoint(b_palette) else "overlap"

    return {
        "errors": errors,
        "canonical_input": canonical_input,
        "canonical_ambiguity_exception": canonical_input and len(candidates) > 1,
        "panels": (a, b, c),
        "candidates": candidates,
        "transform": selected_code,
        "mapping": mapping,
        "source_color_count": len(a_palette),
        "a_cells": a_cells,
        "c_cells": c_cells,
        "palette_relation": relation,
        "a_orbit_size": a_orbit_size,
        "c_orbit_size": c_orbit_size,
        "same_orbit": same_orbit,
        "truth": truth,
        "transform_only": transform_only,
        "recolor_only": recolor_only,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, identity, and rule-hiding scenes."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "transform": analysis["transform"],
        "source_color_count": analysis["source_color_count"],
        "a_cells": analysis["a_cells"],
        "c_cells": analysis["c_cells"],
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "palette_relation": analysis["palette_relation"],
        "transform_candidate_count": len(analysis["candidates"]),
        "a_orbit_size": analysis["a_orbit_size"],
        "c_orbit_size": analysis["c_orbit_size"],
        "canonical_ambiguity_exception": analysis["canonical_ambiguity_exception"],
        "transform_visible": analysis["truth"] != analysis["recolor_only"],
        "recolor_visible": analysis["truth"] != analysis["transform_only"],
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _witness(grid, **expected) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and all(observed.get(key) == value for key, value in expected.items())


SEMANTIC_WITNESSES = {
    **{
        f"transform_{code}": (lambda grid, code=code: _witness(grid, transform=code))
        for code in TRANSFORMS
    },
    "one_source_color": lambda grid: _witness(grid, source_color_count=1),
    "two_source_colors": lambda grid: _witness(grid, source_color_count=2),
    "three_source_colors": lambda grid: _witness(grid, source_color_count=3),
    "disjoint_source_target_palettes": lambda grid: _witness(grid, palette_relation="disjoint"),
    "permuted_source_target_palette": lambda grid: _witness(grid, palette_relation="permuted"),
    "unique_transform_explanation": lambda grid: _witness(grid, transform_candidate_count=1),
    "both_query_effects_visible": lambda grid: _witness(grid, transform_visible=True, recolor_visible=True),
}


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror for focused tests; Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["truth"]]


def _query_panel(grid) -> list[list[int]]:
    return [row[:] for row in _split_panels(grid)[2]]


def _rival_copy_query(grid) -> list[list[int]]:
    return _query_panel(grid)


def _rival_transform_only(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["transform_only"]]


def _rival_recolor_only(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["recolor_only"]]


SEMANTIC_RIVALS = {
    "copy query panel unchanged": _rival_copy_query,
    "apply transform but keep source colors": _rival_transform_only,
    "apply recolor but skip transform": _rival_recolor_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
WITNESS_RIVALS = {
    **{f"transform_{code}": ["copy query panel unchanged"] for code in TRANSFORMS},
    "one_source_color": ["apply transform but keep source colors"],
    "two_source_colors": ["apply transform but keep source colors"],
    "three_source_colors": ["apply transform but keep source colors"],
    "disjoint_source_target_palettes": ["apply transform but keep source colors"],
    "permuted_source_target_palette": ["apply transform but keep source colors"],
    "unique_transform_explanation": ["copy query panel unchanged"],
    "both_query_effects_visible": list(SEMANTIC_RIVALS),
}


def _profile_index(sample_index: int, difficulty=None) -> int:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    offset = {None: 0, "easy": 0, "medium": 5, "hard": 9}[difficulty]
    return (sample_index + offset) % len(_PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    return _profile_index(sample_index, difficulty)


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _paint_mask(mask, colors: Sequence[int], rng) -> list[list[int]]:
    cells = list(mask)
    rng.shuffle(cells)
    assignments = list(colors)
    while len(assignments) < len(cells):
        assignments.append(rng.choice(colors))
    rng.shuffle(assignments)
    out = full_grid(3, 3, 0)
    for (r, c), color in zip(cells, assignments, strict=True):
        out[r][c] = color
    return out


def _choose_distinct_orbit_mask(rng, count: int, other_grid=None):
    candidates = list(_MASKS_BY_COUNT[count])
    if other_grid is not None:
        other_key = _orbit_key(other_grid)
        candidates = [mask for mask in candidates if _orbit_key(_support_grid(mask)) != other_key]
    if not candidates:
        raise ValueError(f"no D4-asymmetric {count}-cell mask in a distinct orbit")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; the Racket rule owns the output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    profile = _PROFILES[_profile_index(sample_index, difficulty)]
    default_transform, default_colors, default_a_cells, default_c_cells, palette_relation = profile
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    transform = _draw_choice_axis(ctx, overrides, "transform", default_transform, TRANSFORMS)
    source_color_count = _draw_int_axis(ctx, overrides, "source_color_count", default_colors, 1, 3)
    a_cells = _draw_int_axis(ctx, overrides, "a_cells", default_a_cells, 3, 7)
    c_cells = _draw_int_axis(ctx, overrides, "c_cells", default_c_cells, 3, 7)

    rng = ctx.draw_rng("scene")
    source_colors = rng.sample(list(_COLOR_POOL), source_color_count)
    if palette_relation == "permuted" and source_color_count >= 2:
        target_colors = source_colors[1:] + source_colors[:1]
    else:
        target_colors = rng.sample(
            [color for color in _COLOR_POOL if color not in source_colors],
            source_color_count,
        )
    mapping = dict(zip(source_colors, target_colors, strict=True))

    a_mask = _choose_distinct_orbit_mask(rng, a_cells)
    a = _paint_mask(a_mask, source_colors, rng)
    c_mask = _choose_distinct_orbit_mask(rng, c_cells, other_grid=a)
    c = _paint_mask(c_mask, source_colors, rng)
    b = _recolor(_transform_grid(a, transform), mapping)

    grid = full_grid(3, 11, 0)
    for divider in (3, 7):
        for row in range(3):
            grid[row][divider] = 8
    for panel_index, panel in enumerate((a, b, c)):
        left = panel_index * 4
        for row in range(3):
            for col in range(3):
                grid[row][left + col] = panel[row][col]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to falsify named shortcuts that alter the query answer."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    transforms = set()
    source_counts = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the transform+recolor rule")
        observed = semantic_observables(demo["input"])
        if observed["transform_candidate_count"] != 1:
            reasons.append(f"demo {index} does not uniquely identify its transform")
        transforms.add(observed["transform"])
        source_counts.append(observed["source_color_count"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    if reasons:
        return reasons
    if len(transforms) < 2:
        reasons.append("demonstrations expose only one transform, leaving a fixed-transform shortcut")
    if max(source_counts, default=0) < 2:
        reasons.append("demonstrations never expose a multi-color mapping")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
