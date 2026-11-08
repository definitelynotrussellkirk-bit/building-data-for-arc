"""Generator for ARC task b6592c220670 — scripted transform gallery.

The top row is a left-to-right script.  Codes 1, 2, 3, and 4 mean identity,
rotate 90 degrees clockwise, flip left/right, and rotate 180 degrees.  The
motif below the blank separator row is cropped to its bounding box. The script is
applied *cumulatively*, and every intermediate state is packed into a horizontal
one-column-spaced gallery.

The canonical examples deliberately contain multicolour motifs and sometimes
reuse script colours inside the motif.  Ordinary draws preserve both cases so a
learner cannot replace the row-role rule with a colour-disjoint shortcut.
Every four consecutive ordinary draws also contain a repeated instruction: each
occurrence executes and emits a panel, even if that symbol appeared before.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b6592c220670"
TASK_ID = "b6592c220670"
VERSION = "3.0.0"
RULE_HASH = "042a7b2c96f6"  # sha256[:12] of normalized canonical program_solution
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Read the nonzero codes in row 0 from left to right.  Crop the motif below "
    "the all-zero separator row to its bounding box, then apply every code to the "
    "previous state (1=identity, 2=rotate-CW, 3=flip-LR, 4=rotate-180).  "
    "Pack all intermediate states left-to-right with one zero column between "
    "them.  Motif colours are preserved; they may overlap the script colours."
)

INVARIANTS = [
    "background is 0 and row 1 is an all-zero separator",
    "row 0 contains 1..6 script cells, each valued 1..4",
    "rows 2 onward contain a finite motif spanning at least two rows and columns",
    "ordinary lessons include monochrome and multicolour motifs, with both script-colour overlap and disjoint palettes",
    "the output is the cumulative, not independent, transform gallery",
    "every four consecutive ordinary draws include a repeated script symbol; no deduplication is allowed",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors or difficulty-aware", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "canonical anchors or difficulty-aware", "valid": "9..20"},
    "n_codes": {"type": "int", "default": "3 on anchors; otherwise 2..4", "valid": "1..6"},
    "motif_cells": {"type": "int", "default": "4 or 5 on anchors; otherwise 4..8", "valid": "4..8"},
    "motif_colors": {"type": "int", "default": "schedule: three multicolour then one monochrome", "valid": "1..3"},
    "palette_relation": {"type": "str", "default": "alternates by sample_index", "valid": "overlap|disjoint"},
    "first_code": {"type": "int", "default": "four-slot schedule covers 1,2,3,4", "valid": "1..4"},
}

SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 0.20

# Exact canonical (h, w, input-palette-size) profiles.
_CANONICAL_PROFILES = {(8, 10, 4), (8, 9, 5), (7, 11, 6), (8, 10, 5)}

# Canonical-profile anchors.  Their code and motif palettes intentionally mirror
# the canonical role relations without copying the canonical geometry.
_ANCHORS = (
    # Repeat a nonadjacent instruction while preserving the exact (8, 10, 4)
    # input profile: replacing code 1 with 2 is balanced by motif color 7.
    {"h": 8, "w": 10, "codes": (2, 3, 2), "cells": 4, "palette": (2, 7)},
    {"h": 8, "w": 9, "codes": (1, 4, 2), "cells": 5, "palette": (4, 5)},
    {"h": 7, "w": 11, "codes": (3, 2, 4), "cells": 4, "palette": (6, 7)},
    {"h": 8, "w": 10, "codes": (4, 3, 2), "cells": 4, "palette": (8,)},
)

# Connected asymmetric masks, nested by size.  Dihedral randomization below
# supplies orientation variation while preserving exact cell count.
_MASKS = {
    4: ((0, 0), (1, 0), (2, 0), (2, 1)),
    5: ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    6: ((0, 0), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    7: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive samples visit every decisive script/palette slot."""
    del seed, difficulty
    return sample_index % 4


def _draw_int_axis(ctx, label: str, lo: int, hi: int, *, fixed=None, default=None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if fixed is not None:
        return ctx.draw_int(label, int(fixed), int(fixed))
    dlo, dhi = default if default is not None else (lo, hi)
    return ctx.draw_int_diff(label, dlo, dhi)


def _draw_choice_axis(ctx, label: str, options, *, fixed):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (fixed,))


def _normalize_cells(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform_cells(cells, variant: int):
    pts = list(cells)
    if variant >= 4:
        pts = [(r, -c) for r, c in pts]
    for _ in range(variant % 4):
        pts = [(c, -r) for r, c in pts]
    return _normalize_cells(pts)


def _make_script(first_code: int, n_codes: int, rng, *, require_repeat=False, require_order=False) -> list[int]:
    """Sample an ordered word, not a permutation of instruction symbols.

    Outside teaching slots, all symbols remain available at every position.
    The repetition slot copies an earlier symbol to a later position. The order
    slot starts with identity and ends with a quarter turn: all current masks
    differ from their quarter turns, so reversing that word changes panel one.
    Single-instruction overrides cannot promise either witness.
    """
    script = [first_code] + [rng.choice((1, 2, 3, 4)) for _ in range(n_codes - 1)]
    if require_order and n_codes >= 2:
        script[-1] = 2
    if require_repeat and n_codes >= 2:
        later = rng.randrange(1, n_codes)
        script[later] = script[rng.randrange(later)]
    return script


def _make_palette(script: list[int], n_colors: int, relation: str, rng) -> tuple[int, ...]:
    script_set = set(script)
    if relation == "overlap":
        first = rng.choice(sorted(script_set))
        pool = [c for c in range(1, 10) if c != first]
        rng.shuffle(pool)
        return tuple([first, *pool[: n_colors - 1]])
    if relation == "disjoint":
        pool = [c for c in range(1, 10) if c not in script_set]
        if len(pool) < n_colors:
            raise ValueError("not enough motif colors disjoint from script")
        rng.shuffle(pool)
        return tuple(pool[:n_colors])
    raise ValueError(f"unknown palette_relation: {relation!r}")


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
    slot = sample_index % 4
    # Half of ordinary draws are exact-profile anchors. Any explicit override
    # selects the general path so every declared boundary remains composable.
    anchor = not overrides and sample_index % 8 < 4
    spec = _ANCHORS[slot] if anchor else None

    h = _draw_int_axis(ctx, "grid_h", 7, 16, fixed=spec and spec["h"])
    w = _draw_int_axis(ctx, "grid_w", 9, 20, fixed=spec and spec["w"])
    n_codes = _draw_int_axis(
        ctx, "n_codes", 1, 6, fixed=spec and len(spec["codes"]), default=(2, 4)
    )
    motif_cells = _draw_int_axis(
        ctx, "motif_cells", 4, 8, fixed=spec and spec["cells"]
    )
    scheduled_motif_colors = 1 if slot == 3 else 2
    motif_colors = _draw_int_axis(
        ctx,
        "motif_colors",
        1,
        3,
        fixed=(len(spec["palette"]) if spec else scheduled_motif_colors),
    )
    scheduled_relation = "overlap" if slot in (0, 1) else "disjoint"
    palette_relation = _draw_choice_axis(
        ctx,
        "palette_relation",
        ("overlap", "disjoint"),
        fixed=scheduled_relation,
    )
    first_code = _draw_int_axis(ctx, "first_code", 1, 4, fixed=_ANCHORS[slot]["codes"][0])

    layout_rng = ctx.draw_rng("layout")
    script_rng = ctx.draw_rng("script")
    palette_rng = ctx.draw_rng("motif_palette")
    color_rng = ctx.draw_rng("motif_coloring")

    if spec is not None:
        script = list(spec["codes"])
        palette = tuple(spec["palette"])
    else:
        script = _make_script(
            first_code, n_codes, script_rng, require_repeat=(slot == 0),
            require_order=(slot == 1 and first_code == 1),
        )
        palette = _make_palette(script, motif_colors, palette_relation, palette_rng)

    # The fixed anchor script already has the scheduled first code; the general
    # path is built from it. Keep this assertion close to the source of truth.
    if len(script) != n_codes or script[0] != first_code:
        raise AssertionError("script axis realization drifted")
    realized_relation = "overlap" if set(script) & set(palette) else "disjoint"
    if len(set(palette)) != motif_colors or realized_relation != palette_relation:
        raise AssertionError("motif palette axis realization drifted")

    g = full_grid(h, w, 0)
    code_cols = sorted(layout_rng.sample(range(w), n_codes))
    for col, code in zip(code_cols, script):
        g[0][col] = code

    shape = _transform_cells(_MASKS[motif_cells], layout_rng.randrange(8))
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    r0 = layout_rng.randint(2, h - sh)
    c0 = layout_rng.randint(0, w - sw)
    shuffled_cells = list(shape)
    color_rng.shuffle(shuffled_cells)
    cell_colors = {}
    for index, cell in enumerate(shuffled_cells):
        cell_colors[cell] = palette[index] if index < len(palette) else color_rng.choice(palette)
    for r, c in shape:
        g[r0 + r][c0 + c] = cell_colors[(r, c)]

    realized_meta = {
        "overrides": {
            "grid_h": h,
            "grid_w": w,
            "n_codes": n_codes,
            "motif_cells": motif_cells,
            "motif_colors": motif_colors,
            "palette_relation": palette_relation,
            "first_code": first_code,
        }
    }
    errors = self_check(g, difficulty=difficulty, meta=realized_meta)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return g


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a nonempty sequence"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (3 <= len(grid) <= 30 and 3 <= w <= 30):
        return [f"grid dimensions must lie in 3..30, got {len(grid)}x{w}"]
    bad = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
           if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9]
    return [] if not bad else [f"grid contains invalid ARC cells: {bad[:4]}"]


def _positions(grid, predicate):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if predicate(value)]



def _script(grid) -> list[int]:
    return [value for value in grid[0] if value in (1, 2, 3, 4)]


def _motif_cells(grid):
    return [(r, c) for r in range(2, len(grid)) for c, value in enumerate(grid[r]) if value != 0]


def _crop_motif(grid) -> list[list[int]]:
    cells = _motif_cells(grid)
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _step(grid, code):
    if code == 2:
        return _rotate_cw(grid)
    if code == 3:
        return _flip_lr(grid)
    if code == 4:
        return _rotate_180(grid)
    return [list(row) for row in grid]


def _gallery(states):
    if not states:
        return [[0]]
    height = max(len(state) for state in states)
    width = sum(len(state[0]) for state in states) + len(states) - 1
    out = full_grid(height, width, 0)
    left = 0
    for state in states:
        for r, row in enumerate(state):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(state[0]) + 1
    return out


def rule_mirror(grid):
    cur = _crop_motif(grid)
    states = []
    for code in _script(grid):
        cur = _step(cur, code)
        states.append(cur)
    return _gallery(states)


def _rival_skip_code(code_to_skip):
    """Dropping an instruction loses its emitted panel, even for identity."""
    def rival(grid):
        cur = _crop_motif(grid)
        states = []
        for code in _script(grid):
            if code == code_to_skip:
                continue
            cur = _step(cur, code)
            states.append(cur)
        return _gallery(states)
    return rival


def _rival_palette_filter(grid, *, keep_shared):
    """Mis-segment the motif by script color instead of by row role."""
    script_colors = set(_script(grid))
    wrong = [list(row) for row in grid]
    for r, c in _motif_cells(grid):
        if (grid[r][c] in script_colors) != keep_shared:
            wrong[r][c] = 0
    return rule_mirror(wrong)


def _rival_discard_script_colored_motif(grid):
    return _rival_palette_filter(grid, keep_shared=False)


def _rival_keep_only_script_colored_motif(grid):
    return _rival_palette_filter(grid, keep_shared=True)


def _rival_deduplicate_script(grid):
    """Wrong but canonical-compatible: execute only the first occurrence of a code."""
    cur = _crop_motif(grid)
    states = []
    for code in dict.fromkeys(_script(grid)):
        cur = _step(cur, code)
        states.append(cur)
    return _gallery(states)


def _rival_independent(grid):
    base = _crop_motif(grid)
    return _gallery([_step(base, code) for code in _script(grid)])


def _rival_reverse_script(grid):
    cur = _crop_motif(grid)
    states = []
    for code in reversed(_script(grid)):
        cur = _step(cur, code)
        states.append(cur)
    return _gallery(states)


def _rival_first_code_only(grid):
    script = _script(grid)
    return _gallery([_step(_crop_motif(grid), script[0])]) if script else [[0]]


def _rival_final_state_only(grid):
    cur = _crop_motif(grid)
    for code in _script(grid):
        cur = _step(cur, code)
    return _gallery([cur])


def _rival_monochrome(grid):
    out = rule_mirror(grid)
    motif = _crop_motif(grid)
    colors = [v for row in motif for v in row if v]
    if not colors:
        return out
    replacement = colors[0]
    return [[replacement if value else 0 for value in row] for row in out]


def observe_overrides(grid) -> dict[str, Any]:
    if _grid_errors(grid):
        return {}
    codes = _script(grid)
    motif = _motif_cells(grid)
    if not codes or not motif:
        return {}
    motif_values = {grid[r][c] for r, c in motif}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_codes": len(codes),
        "motif_cells": len(motif),
        "motif_colors": len(motif_values),
        "palette_relation": "overlap" if set(codes) & motif_values else "disjoint",
        "first_code": codes[0],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if any(grid[1][c] != 0 for c in range(w)):
        errors.append("row 1 must be an all-zero separator")
    bad_script = [(c, value) for c, value in enumerate(grid[0]) if value not in (0, 1, 2, 3, 4)]
    if bad_script:
        errors.append(f"row 0 contains non-script values: {bad_script[:4]}")
    codes = _script(grid)
    if not 1 <= len(codes) <= 6:
        errors.append(f"expected 1..6 row-0 codes, found {len(codes)}")

    motif = _motif_cells(grid)
    if not 3 <= len(motif) <= 12:
        errors.append(f"expected 3..12 motif cells below separator, found {len(motif)}")
    else:
        mh = max(r for r, _ in motif) - min(r for r, _ in motif) + 1
        mw = max(c for _, c in motif) - min(c for _, c in motif) + 1
        if mh < 2 or mw < 2:
            errors.append("motif must span at least two rows and two columns")

    if not errors and len(rule_mirror(grid)) > 30:
        errors.append("gallery output exceeds ARC height limit 30")
    if not errors and len(rule_mirror(grid)[0]) > 30:
        errors.append("gallery output exceeds ARC width limit 30")

    requested = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    if requested:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(f"override {name}={expected!r} realized as {observed.get(name)!r}")
    return errors


def mutation_fixtures():
    """Named malformed scenes used to prove the checker rejects impostors."""
    fixtures = []

    fixtures.append(("all_background", full_grid(8, 10, 0)))

    no_codes = full_grid(8, 10, 0)
    for r, c in ((3, 3), (4, 3), (4, 4), (5, 4)):
        no_codes[r][c] = 8
    fixtures.append(("no_codes", no_codes))

    no_motif = full_grid(8, 10, 0)
    no_motif[0][1], no_motif[0][4], no_motif[0][8] = 2, 3, 4
    fixtures.append(("no_motif", no_motif))

    separator_leak = generate(7701, 4, difficulty="medium")
    separator_leak[1][0] = 6
    fixtures.append(("separator_leak", separator_leak))

    invalid_script = generate(7702, 5, difficulty="medium")
    code_col = next(c for c, value in enumerate(invalid_script[0]) if value)
    invalid_script[0][code_col] = 7
    fixtures.append(("invalid_script_value", invalid_script))

    line_motif = full_grid(8, 10, 0)
    line_motif[0][1], line_motif[0][4] = 2, 3
    for c in range(3, 7):
        line_motif[4][c] = 8
    fixtures.append(("one_dimensional_motif", line_motif))
    return fixtures


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside canonical profiles {sorted(_CANONICAL_PROFILES)}")
    if len(_script(grid)) != 3:
        errors.append("canonical examples use exactly three script cells")
    if len(_motif_cells(grid)) not in (4, 5):
        errors.append("canonical examples use four or five motif cells")
    return errors


def _valid(grid) -> bool:
    try:
        return not self_check(grid)
    except Exception:
        return False


def _has_code(code: int) -> Callable[[Any], bool]:
    return lambda grid: _valid(grid) and code in _script(grid)


def _multicolor(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["motif_colors"] >= 2


def _palette_relation(name: str) -> Callable[[Any], bool]:
    return lambda grid: _valid(grid) and observe_overrides(grid)["palette_relation"] == name


def _rival_differs(rival) -> Callable[[Any], bool]:
    return lambda grid: _valid(grid) and rule_mirror(grid) != rival(grid)


SEMANTIC_RIVALS = {
    "skip_identity_instruction": _rival_skip_code(1),
    "skip_rotate_cw_instruction": _rival_skip_code(2),
    "skip_flip_lr_instruction": _rival_skip_code(3),
    "skip_rotate_180_instruction": _rival_skip_code(4),
    "discard_script_colored_motif": _rival_discard_script_colored_motif,
    "keep_only_script_colored_motif": _rival_keep_only_script_colored_motif,
    "deduplicate_script": _rival_deduplicate_script,
    "independent_transforms": _rival_independent,
    "reverse_script": _rival_reverse_script,
    "first_code_only": _rival_first_code_only,
    "final_state_only": _rival_final_state_only,
    "collapse_motif_to_one_color": _rival_monochrome,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Other semantic rivals are already falsified by the canonical examples. Only
# advertise a canonical shortcut after checking every usable canonical pair.
CANONICAL_SHORTCUTS = {"deduplicate_script": _rival_deduplicate_script}

SEMANTIC_WITNESSES = {
    "repeated_instruction_is_executed": _rival_differs(_rival_deduplicate_script),
    "identity_code_present": _has_code(1),
    "rotate_cw_code_present": _has_code(2),
    "flip_lr_code_present": _has_code(3),
    "rotate_180_code_present": _has_code(4),
    "multicolor_motif_preserved": _multicolor,
    "script_color_reused_inside_motif": _palette_relation("overlap"),
    "motif_palette_disjoint_from_script": _palette_relation("disjoint"),
    "cumulative_composition_changes_answer": _rival_differs(_rival_independent),
    "left_to_right_order_changes_answer": _rival_differs(_rival_reverse_script),
    "all_intermediate_states_are_emitted": _rival_differs(_rival_final_state_only),
}

WITNESS_RIVALS = {
    "identity_code_present": ["skip_identity_instruction"],
    "rotate_cw_code_present": ["skip_rotate_cw_instruction"],
    "flip_lr_code_present": ["skip_flip_lr_instruction"],
    "rotate_180_code_present": ["skip_rotate_180_instruction"],
    "script_color_reused_inside_motif": ["discard_script_colored_motif"],
    "motif_palette_disjoint_from_script": ["keep_only_script_colored_motif"],
    "repeated_instruction_is_executed": ["deduplicate_script"],
    "multicolor_motif_preserved": ["collapse_motif_to_one_color"],
    "cumulative_composition_changes_answer": ["independent_transforms"],
    "left_to_right_order_changes_answer": ["reverse_script"],
    "all_intermediate_states_are_emitted": ["first_code_only", "final_state_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        if self_check(pair["input"]):
            reasons.append(f"pair {index} input is outside the task grammar")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the pinned rule")
    if reasons:
        return reasons

    demo_codes = {code for pair in demos for code in _script(pair["input"])}
    if demo_codes != {1, 2, 3, 4}:
        reasons.append(f"demos cover script codes {sorted(demo_codes)}, need all 1..4")
    relations = {observe_overrides(pair["input"])["palette_relation"] for pair in demos}
    if relations != {"overlap", "disjoint"}:
        reasons.append(f"demos cover palette relations {sorted(relations)}, need both")
    if not any(_multicolor(pair["input"]) for pair in demos):
        reasons.append("demos contain no multicolour motif")
    if not any(rule_mirror(pair["input"]) != _rival_independent(pair["input"]) for pair in demos):
        reasons.append("demos do not distinguish cumulative from independent transforms")

    query_input, query_output = query["input"], query["output"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query_input) != query_output:
            reasons.append(f"rival {name!r} fits every demo but changes the query answer")
    return reasons
