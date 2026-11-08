"""Generator for "Decode the Transform Sequence and Stamp the Row".

A 5x5 one-color prototype is followed by four transform opcodes and a target
color.  Apply the opcodes cumulatively, recolor each intermediate prototype to
the target color, and concatenate the four 5x5 panels with one blank separator.

The sampler exposes one exact, pixel-observable control: prototype cell count.
A three-profile schedule guarantees that every three consecutive examples cover
all six opcodes and that each example refutes three task-specific rival rules.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2c784862f42b"
TASK_ID = GENERATOR_ID
RULE_HASH = "e8e6e0187218"
VERSION = "2.1.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read a 5x5 prototype, then apply four codes cumulatively: 0 identity, "
    "1 clockwise, 2 half-turn, 3 counter-clockwise, 4 left-right reflection, "
    "and 5 up-down reflection. Recolor each intermediate panel to the final "
    "row color and stamp the four panels left-to-right with blank separators."
)

INVARIANTS = [
    "the input is 6x5; rows 0..4 contain one 4-connected, one-color prototype",
    "the prototype contains 4..8 cells and is embedded in the full 5x5 frame",
    "row 5 columns 0..3 contain at least three distinct opcodes from 0..5",
    "row 5 column 4 is a nonzero target color different from the prototype color",
    "each opcode transforms the running panel, not the original prototype",
]

AXES = {
    "prototype_cells": {
        "type": "int",
        "default": "uniform 4..8",
        "valid": "4..8",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("codes_0124", "codes_0345", "codes_1235")
_SEQUENCE_BANKS = {
    # Each profile uses four distinct opcodes.  The missing pairs are disjoint,
    # so ANY TWO profile types cover all six codes.  Consequently every
    # leave-one-out rotation of four consecutive pairs still teaches the full
    # opcode alphabet.  Each sequence also contains a quarter turn and a
    # reflection, allowing one asymmetric prototype to refute all rivals.
    "codes_0124": (
        (0, 1, 2, 4),
        (1, 4, 0, 2),
        (2, 0, 4, 1),
        (4, 2, 1, 0),
    ),
    "codes_0345": (
        (0, 3, 4, 5),
        (3, 5, 0, 4),
        (4, 0, 5, 3),
        (5, 4, 3, 0),
    ),
    "codes_1235": (
        (1, 2, 3, 5),
        (2, 5, 1, 3),
        (3, 1, 5, 2),
        (5, 3, 2, 1),
    ),
}

# Deterministic escape hatches for the vanishingly unlikely event that random
# connected growth repeatedly produces a symmetry that preserves a rival.
_FALLBACK_SHAPES = {
    4: ((0, 1), (1, 0), (1, 1), (1, 2)),
    5: ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    6: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (3, 1)),
    7: ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2)),
    8: ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (2, 3), (2, 4)),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum residue used for this draw."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _copy(grid):
    return [list(row) for row in grid]


def _transform(panel, code):
    panel = _copy(panel)
    if code == 0:
        return panel
    if code == 1:
        return [list(row) for row in zip(*panel[::-1])]
    if code == 2:
        return [row[::-1] for row in panel[::-1]]
    if code == 3:
        return [list(row) for row in zip(*panel)][::-1]
    if code == 4:
        return [row[::-1] for row in panel]
    if code == 5:
        return [row[:] for row in panel[::-1]]
    raise ValueError(f"unknown transform code {code!r}")


def _recolor(panel, color):
    return [[color if value else 0 for value in row] for row in panel]


def _gallery(panels):
    out = []
    for r in range(5):
        row = []
        for index, panel in enumerate(panels):
            if index:
                row.append(0)
            row.extend(panel[r])
        out.append(row)
    return out


def _validated_parts(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _copy(grid[:5]), tuple(grid[5][:4]), grid[5][4]


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    current, codes, target = _validated_parts(grid)
    panels = []
    for code in codes:
        current = _transform(current, code)
        panels.append(_recolor(current, target))
    return _gallery(panels)


def _independent_steps(grid):
    """Rival: apply every code to the original prototype, not cumulatively."""
    prototype, codes, target = _validated_parts(grid)
    return _gallery([_recolor(_transform(prototype, code), target) for code in codes])


def _remapped_codes(grid, mapping):
    prototype, codes, target = _validated_parts(grid)
    current = prototype
    panels = []
    for code in codes:
        current = _transform(current, mapping.get(code, code))
        panels.append(_recolor(current, target))
    return _gallery(panels)


def _swap_quarter_turns(grid):
    """Rival: decode opcode 1 as CCW and 3 as CW."""
    return _remapped_codes(grid, {1: 3, 3: 1})


def _swap_reflections(grid):
    """Rival: decode opcode 4 as up-down and 5 as left-right."""
    return _remapped_codes(grid, {4: 5, 5: 4})


def _prototype_cells(grid):
    return {(r, c) for r in range(5) for c in range(5) if grid[r][c] != 0}


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the authority-compatible teaching grammar used by this sampler."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or len(grid) != 6:
        return ["expected a 6x5 prototype-plus-command grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 5 for row in grid):
        return ["expected a rectangular 6x5 prototype-plus-command grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (booleans are not colors)"]

    errors = []
    cells = _prototype_cells(grid)
    if not 4 <= len(cells) <= 8:
        errors.append(f"prototype should contain 4..8 non-background cells, found {len(cells)}")
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        errors.append(f"prototype should use exactly one source color, found {sorted(colors)}")
    if cells and not _connected(cells):
        errors.append("prototype cells must form one 4-connected component")

    codes = tuple(grid[5][:4])
    if any(not 0 <= code <= 5 for code in codes):
        errors.append(f"transform codes must lie in 0..5, found {list(codes)}")
    if len(set(codes)) < 3:
        errors.append(f"sequence must expose at least three distinct transform codes, found {list(codes)}")

    target = grid[5][4]
    if not 1 <= target <= 9:
        errors.append(f"target color must lie in 1..9, found {target}")
    if len(colors) == 1 and target in colors:
        errors.append("target color must differ from the prototype color")
    return errors


def strict_canonical_like(grid):
    """All normal draws are within the declared task-specific manifold."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    if self_check(grid):
        return {}
    return {"prototype_cells": len(_prototype_cells(grid))}


def _grow_connected_shape(rng, count):
    start = (rng.randrange(5), rng.randrange(5))
    cells = {start}
    while len(cells) < count:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= r + dr < 5 and 0 <= c + dc < 5 and (r + dr, c + dc) not in cells
            }
        )
        cells.add(rng.choice(frontier))
    return cells


def _centered_shape(shape):
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    row0 = (5 - height) // 2
    col0 = (5 - width) // 2
    return {(row0 + r, col0 + c) for r, c in shape}


def _assemble(cells, source, codes, target):
    grid = full_grid(6, 5, 0)
    for r, c in cells:
        grid[r][c] = source
    for c, code in enumerate(codes):
        grid[5][c] = code
    grid[5][4] = target
    return grid


def _rivals_refuted(grid):
    intended = rule_mirror(grid)
    return all(rival(grid) != intended for rival in SEMANTIC_RIVALS.values())


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    if "prototype_cells" in overrides and overrides["prototype_cells"] is not None:
        value = overrides["prototype_cells"]
        if type(value) is not int:
            raise ValueError(f"prototype_cells must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    count_options = {
        "easy": (4, 4, 4, 5, 5, 6, 7, 8),
        "medium": (4, 5, 5, 6, 6, 7, 7, 8),
        "hard": (4, 5, 6, 7, 7, 8, 8, 8),
        None: (4, 5, 6, 7, 8),
    }[difficulty]
    # Every band retains the full exact override domain; only the default prior
    # changes.  This avoids both dead difficulty bands and band-clipped controls.
    count = ctx.draw_choice("prototype_cells", count_options)
    profile = schedule_profile(seed, sample_index, difficulty=difficulty)
    codes = tuple(ctx.draw_rng("sequence_variant").choice(_SEQUENCE_BANKS[profile]))
    source_options = sorted(set(codes) - {0})
    source = ctx.draw_rng("source_color").choice(source_options)
    target_options = [color for color in range(1, 10) if color not in set(codes)]
    target = ctx.draw_rng("target_color").choice(target_options)

    rng = ctx.draw_rng("prototype_shape")
    for _ in range(256):
        cells = _grow_connected_shape(rng, count)
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(rows) < 2 or len(cols) < 2:
            continue
        grid = _assemble(cells, source, codes, target)
        if not self_check(grid) and _rivals_refuted(grid):
            return grid

    fallback = _assemble(_centered_shape(_FALLBACK_SHAPES[count]), source, codes, target)
    if self_check(fallback) or not _rivals_refuted(fallback):
        raise RuntimeError("failed to construct a lawful rival-separating prototype")
    return fallback


def _witness_cumulative(grid):
    try:
        return _independent_steps(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _witness_quarter_direction(grid):
    try:
        return _swap_quarter_turns(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _witness_reflection_axis(grid):
    try:
        return _swap_reflections(grid) != rule_mirror(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES = {
    "cumulative_composition": _witness_cumulative,
    "quarter_turn_direction": _witness_quarter_direction,
    "reflection_axis": _witness_reflection_axis,
}
SEMANTIC_RIVALS = {
    "independent_steps": _independent_steps,
    "swap_quarter_turns": _swap_quarter_turns,
    "swap_reflections": _swap_reflections,
}
WITNESS_RIVALS = {
    "cumulative_composition": ["independent_steps"],
    "quarter_turn_direction": ["swap_quarter_turns"],
    "reflection_axis": ["swap_reflections"],
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# None of these rivals fits every public pair, so there is no honest canonical
# shortcut declaration.  They remain useful lesson-level competitors.
CANONICAL_SHORTCUTS: dict[str, object] = {}


def lesson_identifiable(demos, query):
    """Check labels, opcode coverage, and declared-rival separation."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    covered_codes = set()
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"demo {index} is missing an input")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is outside the teaching grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match cumulative transforms")
            continue
        covered_codes.update(pair["input"][5][:4])
        valid_demos.append(pair)

    missing = sorted(set(range(6)) - covered_codes)
    if missing:
        reasons.append(f"demonstrations do not cover opcodes {missing}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input")
        return reasons
    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match cumulative transforms")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            if competitor(query["input"]) != query_answer:
                reasons.append(f"demonstrations remain consistent with rival: {name}")
    return reasons
