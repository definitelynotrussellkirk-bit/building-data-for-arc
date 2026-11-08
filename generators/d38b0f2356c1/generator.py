"""Generator for ARC task 09629e4f / d38b0f2356c1.

The input is an 11x11 lattice of nine 3x3 blocks separated by gray (5)
rows and columns. Exactly one block contains no cyan (8); that clean block is
the template. The selected Racket rule treats that 3x3 template as a macro-grid:
each template cell is expanded to the corresponding 3x3 output block while the
gray lattice is preserved.

The canonical examples accidentally support a strong shortcut: the clean block
always has four occupied cells while every cyan block has five. This sampler
therefore schedules source-bound counterexamples in every three consecutive
examples: one reverses the density ordering and one gives every block the same
occupied-cell count.  This refutes both "copy the sparsest block" and "copy the
unique count outlier" while the intended no-cyan rule remains stable.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d38b0f2356c1"
TASK_ID = GENERATOR_ID
RULE_HASH = "20d59edf7f3a"
VERSION = "2.1.0"
SUMMARY = "11x11 lattice; replicate the unique 3x3 block without cyan(8)."

INVARIANTS = [
    "11x11 grid with rows and columns 3 and 7 entirely gray(5)",
    "exactly one 3x3 block contains no cyan(8); it is the nonempty template",
    "the other eight blocks each contain the same 1..3 cyan markers",
    "all distractors contain the same 0..6 non-cyan occupied cells",
    "no block interior contains gray(5)",
]

AXES = {
    "clean_block": {
        "type": "int",
        "default": "uniform 0..8",
        "valid": "0..8",
    },
    "template_cells": {
        "type": "int",
        "default": "difficulty/profile weighted over full domain",
        "valid": "1..9",
    },
    "distractor_noise": {
        "type": "int",
        "default": "difficulty/profile weighted over full domain",
        "valid": "0..6",
    },
    "cyan_count": {
        "type": "int",
        "default": "difficulty/profile weighted over full domain",
        "valid": "1..3",
    },
}
# Every Cartesian product of the four exact domains is constructively valid:
# cyan_count + distractor_noise is at most 9.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (
    "canonical_density",
    "sparser_cyan_distractor",
    "equal_occupancy",
)

_BLOCK_STARTS = (0, 4, 8)
_BLOCK_CELLS = tuple((r, c) for r in range(3) for c in range(3))
_AXIS_BOUNDS = {
    "clean_block": (0, 8),
    "template_cells": (1, 9),
    "distractor_noise": (0, 6),
    "cyan_count": (1, 3),
}
_PALETTES = {
    "canonical": (2, 3, 4, 6),
    "minimal": (2, 3),
    "cool": (1, 3, 7, 9),
    "warm": (2, 4, 6, 9),
    "broad": (1, 2, 3, 4, 6, 7, 9),
}
_DIFFICULTY_PHASE = {None: 3, "easy": 0, "medium": 1, "hard": 2}


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive examples cover canonical, rival-killing, and broad cases."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTY_PHASE:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _profiled_int(ctx, name, lo, hi, favored: Iterable[int], overrides):
    """Choose an exact scheduled default while preserving the full override domain."""
    preferred = tuple(int(value) for value in favored)
    if not preferred or any(not lo <= value <= hi for value in preferred):
        raise RuntimeError(f"internal favored value outside {name} domain")
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    rng = ctx.draw_rng(f"scheduled_{name}")
    scheduled = preferred[rng.randrange(len(preferred))]
    return ctx.draw_int(name, scheduled, scheduled)


def _profile_defaults(profile, difficulty):
    if profile == "canonical_density":
        return {
            "template_cells": (4,),
            "distractor_noise": (4,),
            "cyan_count": (1,),
        }
    if profile == "sparser_cyan_distractor":
        template = {
            None: (5, 6, 7),
            "easy": (3, 4, 5),
            "medium": (5, 6, 7),
            "hard": (7, 8, 9),
        }[difficulty]
        return {
            "template_cells": template,
            "distractor_noise": (0,),
            "cyan_count": (1,),
        }
    # Equal occupied-cell counts remove both canonical count shortcuts:
    # neither the sparsest block nor the unique count outlier identifies the
    # clean template.  The clean block is scheduled away from index zero.
    template, noise, cyan = {
        None: (5, 3, 2),
        "easy": (3, 2, 1),
        "medium": (5, 3, 2),
        "hard": (8, 5, 3),
    }[difficulty]
    return {
        "template_cells": (template,),
        "distractor_noise": (noise,),
        "cyan_count": (cyan,),
    }


def _palette_name(ctx, profile, difficulty):
    if profile == "canonical_density":
        return ctx.draw_choice("palette_profile", ("canonical",))
    options = {
        None: ("minimal", "cool", "warm", "broad"),
        "easy": ("minimal", "canonical", "warm"),
        "medium": ("canonical", "cool", "warm", "broad"),
        "hard": ("cool", "warm", "broad", "broad", "broad"),
    }[difficulty]
    return ctx.draw_choice("palette_profile", options)


def _pattern_order(kind, rng, phase):
    """Return a permutation of all nine local cells for exact-count slicing."""
    if kind == "diagonal":
        order = [(0, 0), (1, 1), (2, 2), (0, 2), (2, 0),
                 (0, 1), (1, 2), (2, 1), (1, 0)]
    elif kind == "cross":
        order = [(1, 1), (0, 1), (1, 2), (2, 1), (1, 0),
                 (0, 0), (0, 2), (2, 2), (2, 0)]
    elif kind == "border":
        order = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 1),
                 (1, 2), (2, 1), (1, 0), (1, 1)]
    else:
        order = list(_BLOCK_CELLS)
        rng.shuffle(order)
    # A deterministic band phase keeps the difficulty knob live even in the
    # canonical-density schedule, where all advertised counts intentionally match.
    shift = phase % len(order)
    return order[shift:] + order[:shift]


def _block_origin(index):
    return _BLOCK_STARTS[index // 3], _BLOCK_STARTS[index % 3]


def _write_block(grid, index, block):
    br, bc = _block_origin(index)
    for r in range(3):
        for c in range(3):
            grid[br + r][bc + c] = block[r][c]


def _paint_values(positions, palette, rng):
    colors = [palette[i % len(palette)] for i in range(len(positions))]
    rng.shuffle(colors)
    return dict(zip(positions, colors))


def _build_template(ctx, count, palette, profile, phase):
    pattern_options = {
        "canonical_density": ("random",),
        "sparser_cyan_distractor": ("diagonal", "cross", "border", "random"),
        "equal_occupancy": ("diagonal", "cross", "border", "random", "random"),
    }[profile]
    kind = ctx.draw_choice("template_pattern", pattern_options)
    rng = ctx.draw_rng(f"template_cells_phase_{phase}")
    chosen = _pattern_order(kind, rng, phase)[:count]
    values = _paint_values(chosen, palette, ctx.draw_rng("template_colors"))
    block = [[0] * 3 for _ in range(3)]
    for (r, c), color in values.items():
        block[r][c] = color
    return block


def _build_distractor(ctx, index, cyan_count, noise_count, palette, phase):
    rng = ctx.draw_rng(f"distractor_{index}_phase_{phase}")
    positions = list(_BLOCK_CELLS)
    rng.shuffle(positions)
    cyan_positions = positions[:cyan_count]
    noise_positions = positions[cyan_count:cyan_count + noise_count]
    block = [[0] * 3 for _ in range(3)]
    for r, c in cyan_positions:
        block[r][c] = 8
    values = _paint_values(
        noise_positions, palette, ctx.draw_rng(f"distractor_colors_{index}")
    )
    for (r, c), color in values.items():
        block[r][c] = color
    return block


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(profile, difficulty)
    clean_defaults = range(1, 9) if profile == "equal_occupancy" else range(9)
    clean = _profiled_int(ctx, "clean_block", 0, 8, clean_defaults, overrides)
    template_cells = _profiled_int(
        ctx, "template_cells", 1, 9, defaults["template_cells"], overrides
    )
    distractor_noise = _profiled_int(
        ctx, "distractor_noise", 0, 6, defaults["distractor_noise"], overrides
    )
    cyan_count = _profiled_int(
        ctx, "cyan_count", 1, 3, defaults["cyan_count"], overrides
    )

    phase = _DIFFICULTY_PHASE[difficulty]
    palette = _PALETTES[_palette_name(ctx, profile, difficulty)]
    template = _build_template(ctx, template_cells, palette, profile, phase)

    grid = full_grid(11, 11, 0)
    for separator in (3, 7):
        for k in range(11):
            grid[separator][k] = 5
            grid[k][separator] = 5
    for index in range(9):
        block = template if index == clean else _build_distractor(
            ctx, index, cyan_count, distractor_noise, palette, phase
        )
        _write_block(grid, index, block)
    return grid


def _shape_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) != 11 or width != 11:
        return [f"expected 11x11 grid; found {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _block(grid, index):
    br, bc = _block_origin(index)
    return [[grid[br + r][bc + c] for c in range(3)] for r in range(3)]


def _block_counts(block):
    flat = [value for row in block for value in row]
    return {
        "cyan": flat.count(8),
        "noise": sum(value not in (0, 8) for value in flat),
        "occupied": sum(value != 0 for value in flat),
        "has_gray": 5 in flat,
    }


def _analysis(grid):
    counts = [_block_counts(_block(grid, index)) for index in range(9)]
    clean = [index for index, row in enumerate(counts) if row["cyan"] == 0]
    return counts, clean


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    for index in (3, 7):
        if any(grid[index][c] != 5 for c in range(11)):
            errors.append(f"separator row {index} must be entirely gray(5)")
        if any(grid[r][index] != 5 for r in range(11)):
            errors.append(f"separator column {index} must be entirely gray(5)")
    if errors:
        return errors

    counts, clean = _analysis(grid)
    if any(row["has_gray"] for row in counts):
        errors.append("block interiors must not contain separator gray(5)")
    if len(clean) != 1:
        errors.append(f"expected exactly one clean no-cyan block; found {len(clean)}")
        return errors

    template = counts[clean[0]]
    if not 1 <= template["occupied"] <= 9:
        errors.append("template must contain 1..9 non-background cells")
    distractors = [row for index, row in enumerate(counts) if index != clean[0]]
    cyan_counts = {row["cyan"] for row in distractors}
    noise_counts = {row["noise"] for row in distractors}
    if len(cyan_counts) != 1 or not cyan_counts <= {1, 2, 3}:
        errors.append(
            "all distractors must share one cyan count in the range 1..3"
        )
    if len(noise_counts) != 1 or not noise_counts <= set(range(7)):
        errors.append(
            "all distractors must share one non-cyan noise count in the range 0..6"
        )
    return errors


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    counts, clean = _analysis(grid)
    clean_index = clean[0]
    distractors = [row for index, row in enumerate(counts) if index != clean_index]
    return {
        "clean_block": clean_index,
        "template_cells": counts[clean_index]["occupied"],
        "distractor_noise": distractors[0]["noise"],
        "cyan_count": distractors[0]["cyan"],
    }


def strict_canonical_like(grid):
    """All ordinary draws are on the selected rule's strict task manifold."""
    return self_check(grid)


def _expand_block(grid, source_index):
    """Expand a selected 3x3 block into the nine 3x3 output regions."""
    source = _block(grid, source_index)
    out = full_grid(11, 11, 0)
    for separator in (3, 7):
        for k in range(11):
            out[separator][k] = 5
            out[k][separator] = 5
    for source_r in range(3):
        for source_c in range(3):
            value = source[source_r][source_c]
            target_index = 3 * source_r + source_c
            _write_block(out, target_index, [[value] * 3 for _ in range(3)])
    return out


def _intended_output(grid):
    """Independent Python oracle matching the selected no-cyan Racket rule."""
    counts, clean = _analysis(grid)
    del counts
    if len(clean) != 1:
        raise ValueError(f"expected one no-cyan block, found {len(clean)}")
    return _expand_block(grid, clean[0])


def _sparsest_block_rival(grid):
    """Plausible WRONG rule: copy the first least-occupied 3x3 block."""
    counts, _ = _analysis(grid)
    minimum = min(row["occupied"] for row in counts)
    source = next(index for index, row in enumerate(counts) if row["occupied"] == minimum)
    return _expand_block(grid, source)


def _unique_occupancy_outlier_rival(grid):
    """Plausible WRONG rule: select a block with a unique occupied-cell count."""
    counts, _ = _analysis(grid)
    frequencies = Counter(row["occupied"] for row in counts)
    unique = [
        index for index, row in enumerate(counts)
        if frequencies[row["occupied"]] == 1
    ]
    source = unique[0] if unique else 0
    return _expand_block(grid, source)


def _has_sparser_cyan_distractor(grid):
    counts, clean = _analysis(grid)
    if len(clean) != 1:
        return False
    template_cells = counts[clean[0]]["occupied"]
    return any(
        row["cyan"] > 0 and row["occupied"] < template_cells
        for index, row in enumerate(counts)
        if index != clean[0]
    )


def _has_equal_occupancy_nonfirst_clean(grid):
    counts, clean = _analysis(grid)
    return (
        len(clean) == 1
        and clean[0] != 0
        and len({row["occupied"] for row in counts}) == 1
    )


def lesson_identifiable(demos, query):
    """Require the demos to reject every declared canonical-fitting rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(pair["input"])
        if errors:
            return [f"demo {index} is outside the strict manifold: {errors[0]}"]
        if pair["output"] != _intended_output(pair["input"]):
            return [f"demo {index} output disagrees with the intended rule"]
    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in demos):
            return [f"{name} shortcut survives every demonstration"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query is outside the strict manifold: {query_errors[0]}"]
    return []


SEMANTIC_WITNESSES = {
    "sparser_cyan_distractor": _has_sparser_cyan_distractor,
    "equal_occupancy_nonfirst_clean": _has_equal_occupancy_nonfirst_clean,
}
SEMANTIC_RIVALS = {
    "sparsest_block": _sparsest_block_rival,
    "unique_occupancy_outlier": _unique_occupancy_outlier_rival,
}
WITNESS_RIVALS = {
    "sparser_cyan_distractor": ["sparsest_block"],
    "equal_occupancy_nonfirst_clean": [
        "sparsest_block",
        "unique_occupancy_outlier",
    ],
}
CANONICAL_SHORTCUTS = {
    "sparsest_block": _sparsest_block_rival,
    "unique_occupancy_outlier": _unique_occupancy_outlier_rival,
}
LESSON_COMPETITORS = {
    "sparsest_block": _sparsest_block_rival,
    "unique_occupancy_outlier": _unique_occupancy_outlier_rival,
}
