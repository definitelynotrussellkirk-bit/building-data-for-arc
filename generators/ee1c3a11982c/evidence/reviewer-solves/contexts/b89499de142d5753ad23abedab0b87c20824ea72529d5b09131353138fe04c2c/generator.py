"""ARC 99fa7670: rightward rays, then downward on the right border.

The canonical Racket program remains the label authority. Ordinary draws cycle
through canonical-like, same-row-priority, and repeated-color lessons. Explicit
controls override that curriculum, never get silently clamped, and retain the
zero bottom/right input border. See notes.md for the teaching-domain boundary.
"""
from __future__ import annotations

from math import isqrt

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee1c3a11982c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2fa78bb0910e"
SUMMARY = (
    "Sparse nonzero sources on a zero background. Each source extends right; "
    "the right border carries the latest source color downward. Row-major "
    "last-covering-source precedence permits multiple sources per row and "
    "repeated colors. Three-example default windows contain both counterexamples."
)
INVARIANTS = [
    "rectangular integer grid with ARC colors 0..9 and dimensions 3..16",
    "at least one nonzero source; zero background",
    "last input row and column are zero so both legs are visible",
    "repeated colors and multiple sources per row are valid extensions",
]
SEED_LAYOUTS = ("scattered", "diagonal", "anti_diag", "row", "col", "corners", "blob")
PALETTE_KINDS = ("warm", "cool", "broad", "small")
HELPFUL_TEXTURES = SEED_LAYOUTS + ("single_seed",)
# Invalid stress inputs are deliberately separate from the training override API.
DEGENERATE_TEXTURES = ()
LAWFUL_DEGENERATE_TEXTURES = ("single_seed",)
PALETTES = {
    "warm": (3, 4, 6, 9), "cool": (1, 5, 7, 8),
    "broad": tuple(range(1, 10)), "small": (1, 2, 3),
}
AXES = {
    "grid_h": {"type": "int", "default": "profile-dependent 3..16", "valid": "3..16"},
    "grid_w": {"type": "int", "default": "profile-dependent 3..16", "valid": "3..16"},
    "n_seeds": {"type": "int", "default": "1..8, bounded by available separated cells", "valid": "1..8"},
    "palette_size": {"type": "int", "default": "1..n_seeds, profile-dependent", "valid": "1..8"},
    "seed_layout": {"type": "str", "default": "keyed preference", "valid": "|".join(SEED_LAYOUTS)},
    "position_bias": {"type": "str", "default": "keyed preference", "valid": "spread|center|edge"},
    "palette_kind": {"type": "str", "default": "broad", "valid": "|".join(PALETTE_KINDS)},
    "min_seed_separation": {"type": "int", "default": "1", "valid": "1..3"},
    "texture": {"type": "str", "default": "legacy layout alias", "valid": "|".join(HELPFUL_TEXTURES)},
}
# Presence selects strict structured-rejection accounting in the shared checker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical_like", "same_row", "repeated_color")
# Demonstration-scale shape/count scaffolds, not stored example grids.
CANONICAL_SCAFFOLDS = ((3, 3, 1), (6, 6, 2), (7, 5, 3))
MIN_STRICT_FRAC = 0.20  # One third by schedule; a finite pinned census may vary.


def schedule_profile(seed, sample_index, difficulty=None):
    """Every contiguous three default examples cover all profiles, for any seed."""
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID)
    phase = ctx.draw_rng("curriculum_phase").randrange(3)
    return SCHEDULE_PROFILES[(phase + sample_index) % 3]


def _incompatible(message, overrides):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key, value in overrides.items():
        if AXES[key]["type"] == "int":
            if type(value) is not int:
                raise ValueError(f"{key} must be an integer, not {value!r}")
            lo, hi = map(int, AXES[key]["valid"].split(".."))
            if not lo <= value <= hi:
                raise ValueError(f"{key}={value} outside {lo}..{hi}")
        elif value not in AXES[key]["valid"].split("|"):
            raise ValueError(f"unsupported {key}={value!r}; see AXES or diagnostic_inputs()")
    if "texture" in overrides and "seed_layout" in overrides:
        if overrides["texture"] != overrides["seed_layout"]:
            _incompatible("texture and seed_layout disagree", overrides)
    if overrides.get("texture") == "single_seed":
        if overrides.get("n_seeds", 1) != 1 or overrides.get("palette_size", 1) != 1:
            _incompatible("single_seed requires n_seeds=1 and palette_size=1", overrides)
    if overrides.get("palette_size", 1) > overrides.get("n_seeds", 8):
        _incompatible("palette_size cannot exceed n_seeds", overrides)
    if overrides.get("min_seed_separation", 1) > 1 and (
            overrides.get("n_seeds") == 1 or overrides.get("texture") == "single_seed"):
        _incompatible("nontrivial min_seed_separation requires at least two sources", overrides)
    kind = overrides.get("palette_kind", "broad")
    if overrides.get("palette_size", 1) > len(PALETTES[kind]):
        _incompatible("palette_size exceeds palette_kind color pool", overrides)


def _layout_cells(layout, h_max, w_max, bias, rng):
    """Rank all legal cells; motifs/biases are preferences, not rigid shapes.

    Shuffle before stable sorting to remove fixed top-left/tie-order artifacts.
    Layout priority precedes the bias; after a motif fills, other cells are legal.
    """
    cells = [(r, c) for r in range(h_max) for c in range(w_max)]
    rng.shuffle(cells)
    if bias == "center":
        cells.sort(key=lambda rc: abs(2*rc[0]-(h_max-1)) + abs(2*rc[1]-(w_max-1)))
    elif bias == "edge":
        cells.sort(key=lambda rc: min(rc[0], h_max-1-rc[0], rc[1], w_max-1-rc[1]))
    if layout == "row":
        row = rng.randrange(h_max)
        cells.sort(key=lambda rc: rc[0] != row)
    elif layout == "col":
        col = rng.randrange(w_max)
        cells.sort(key=lambda rc: rc[1] != col)
    elif layout == "diagonal":
        cells.sort(key=lambda rc: rc[0] != rc[1])
    elif layout == "anti_diag":
        cells.sort(key=lambda rc: rc[1] != w_max-1-rc[0])
    elif layout == "corners":
        corners = {(0, 0), (0, w_max-1), (h_max-1, 0), (h_max-1, w_max-1)}
        cells.sort(key=lambda rc: rc not in corners)
    elif layout == "blob":
        row, col = rng.randrange(h_max), rng.randrange(w_max)
        cells.sort(key=lambda rc: abs(rc[0]-row) + abs(rc[1]-col))
    return cells


def _pack(cells, target, sep, anchors=(), unique_rows=False):
    placed = list(anchors)
    for r, c in cells:
        if len(placed) >= target:
            break
        if (r, c) in placed or (unique_rows and any(pr == r for pr, _ in placed)):
            continue
        if all(abs(pr-r) + abs(pc-c) >= sep for pr, pc in placed):
            placed.append((r, c))
    return placed


def _plan_cells(cells, target, sep, rng, anchors=(), unique_rows=False):
    """Bounded placement, with deterministic separated-lattice fallback.

    A custom combination that still cannot be placed is rejected, not truncated.
    This is not a claim to solve every maximum-packing instance optimally.
    """
    best = _pack(cells, target, sep, anchors, unique_rows)
    if len(best) >= target or sep == 1 or unique_rows:
        return best
    for _ in range(24):
        shuffled = list(cells)
        rng.shuffle(shuffled)
        candidate = _pack(shuffled, target, sep, anchors, unique_rows)
        if len(candidate) > len(best):
            best = candidate
        if len(best) >= target:
            return best
    for r_phase in range(sep):
        for c_phase in range(sep):
            ranked = sorted(cells, key=lambda rc: not (rc[0] % sep == r_phase and rc[1] % sep == c_phase))
            candidate = _pack(ranked, target, sep, anchors, unique_rows)
            if len(candidate) > len(best):
                best = candidate
            if len(best) >= target:
                return best
    return best


def generate(seed, sample_index, *, difficulty=None, **overrides):
    # Legacy spelling remains callable, but metadata correctly declares a lower
    # bound rather than an exact realized minimum pair distance.
    if "seed_separation" in overrides:
        legacy = overrides.pop("seed_separation")
        if "min_seed_separation" in overrides and overrides["min_seed_separation"] != legacy:
            raise ValueError("seed_separation and min_seed_separation disagree")
        overrides["min_seed_separation"] = legacy
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    # Build the scheduling context first: shared audits capture the final GenCtx.
    profile = schedule_profile(seed, sample_index, difficulty) if not overrides else "custom"
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    scaffold = None
    if profile == "canonical_like" and ctx.draw_rng("canonical_scaffold_mix").randrange(2) == 0:
        scaffold = ctx.draw_rng("canonical_scaffold").choice(CANONICAL_SCAFFOLDS)
    sep = ctx.draw_int("min_seed_separation", 1, 3) if "min_seed_separation" in overrides else 1
    required = max(overrides.get("n_seeds", 1), overrides.get("palette_size", 1))
    # Fit explicit cardinalities in otherwise unpinned dimensions using a safe
    # square lattice. When dimensions are pinned, the planner decides feasibility.
    side = isqrt(required-1) + 1
    minimum = max(3, (side-1)*sep + 2)
    upper = 8 if profile == "canonical_like" else 16
    h = ctx.draw_int("grid_h", scaffold[0], scaffold[0]) if scaffold else ctx.draw_int(
        "grid_h", 3 if "grid_h" in overrides else minimum, 16 if "grid_h" in overrides else upper)
    w = ctx.draw_int("grid_w", scaffold[1], scaffold[1]) if scaffold else ctx.draw_int(
        "grid_w", 3 if "grid_w" in overrides else minimum, 16 if "grid_w" in overrides else upper)
    layout = ctx.draw_choice("seed_layout", SEED_LAYOUTS)
    if "texture" in overrides:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
        if texture != "single_seed":
            layout = texture
    else:
        texture = layout
    bias = ctx.draw_choice("position_bias", ("spread", "center", "edge"))
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS) if "palette_kind" in overrides else "broad"
    pool = list(PALETTES[kind])
    rng.shuffle(pool)
    limit = {None: 5, "easy": 3, "medium": 5, "hard": 8}[difficulty]
    if "n_seeds" in overrides:
        limit = overrides["n_seeds"]
    limit = max(limit, overrides.get("palette_size", 1))
    if texture == "single_seed":
        limit = 1
    cells = _layout_cells(layout, h-1, w-1, bias, rng)
    anchors = []
    if profile == "same_row":
        row = rng.randrange(h-1)
        cols = rng.sample(range(w-1), 2)
        anchors = [(row, cols[0]), (row, cols[1])]
    elif profile == "repeated_color":
        rows = rng.sample(range(h-1), 2)
        anchors = [(rows[0], rng.randrange(w-1)), (rows[1], rng.randrange(w-1))]
    if profile == "canonical_like":
        limit = min(limit, 3, h-1)
    placed = _plan_cells(cells, limit, sep, rng, anchors, profile == "canonical_like")
    minimum_count = max(1, len(anchors), overrides.get("palette_size", 1))
    if len(placed) < max(minimum_count, overrides.get("n_seeds", 1)):
        _incompatible("grid_h/grid_w, n_seeds and seed_separation cannot be realized by bounded placement", overrides)
    count = ctx.draw_int("n_seeds", scaffold[2], scaffold[2]) if scaffold else ctx.draw_int(
        "n_seeds", minimum_count, len(placed))
    placed = placed[:count]
    if "palette_size" in overrides:
        color_count = ctx.draw_int("palette_size", 1, min(count, len(pool)))
    elif profile == "repeated_color":
        color_count = ctx.draw_int("palette_size", min(count-1, len(pool)), min(count-1, len(pool)))
    elif profile in ("same_row", "canonical_like"):
        color_count = ctx.draw_int("palette_size", min(count, len(pool)), min(count, len(pool)))
    else:
        color_count = ctx.draw_int("palette_size", 1, min(count, len(pool)))
    palette = pool[:color_count]
    colors = palette + [rng.choice(palette) for _ in range(count-color_count)]
    rng.shuffle(colors)
    if profile == "repeated_color":
        # The first two anchors are in different rows. Use each remaining color
        # once, so exact palette cardinality survives assignment and overlap.
        colors = [palette[0], palette[0]] + palette[1:]
        colors += [rng.choice(palette) for _ in range(count-len(colors))]
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(placed, colors):
        grid[r][c] = color
    assert observe_overrides(grid)["n_seeds"] == count
    assert observe_overrides(grid)["palette_size"] == color_count
    return grid


def _sources(grid):
    return [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def observe_overrides(grid):
    sources = _sources(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_seeds": len(sources),
            "palette_size": len({v for _, _, v in sources})}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Teaching-input validation, not an output validator or proof of a rule."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["each row must be a sequence"]
    h, w = len(grid), len(grid[0])
    if not 3 <= h <= 16 or not 3 <= w <= 16:
        return ["teaching dimensions must be 3..16"]
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integer ARC values 0..9 (not bool)"]
    if not _sources(grid):
        return ["no nonzero source cells"]
    if any(grid[-1]) or any(row[-1] for row in grid):
        return ["last row and column must be zero in the teaching input"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    sources = _sources(grid)
    if len(grid) > 8 or len(grid[0]) > 8:
        errors.append("outside compact canonical-scale support")
    if len(sources) > 3:
        errors.append("more than three sources")
    if len({r for r, _, _ in sources}) != len(sources):
        errors.append("multiple sources share a row")
    if len({v for _, _, v in sources}) != len(sources):
        errors.append("source colors repeat")
    return errors


def diagnostic_inputs():
    """Explicit non-training negatives; callers should expect self_check errors."""
    return [("no_sources", full_grid(5, 5, 0)), ("nonzero_border", full_grid(5, 5, 2)),
            ("ragged", [[1, 0, 0], [0], [0, 0, 0]]),
            ("invalid_color", [[10, 0, 0], [0, 0, 0], [0, 0, 0]])]


def _scan_rule(grid):
    """Independent linear-time check oracle only; labels still come from Racket."""
    out = []
    border_color = 0
    for row in grid:
        color = 0
        result = []
        for value in row:
            if value:
                color = value
            result.append(color)
        if color:
            border_color = color
        result[-1] = border_color
        out.append(result)
    return out


def _leftmost_row_rival(grid):
    """Use only the first/leftmost source in each row, then extend its L."""
    pruned = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                pruned[r][c] = color
                break
    return _scan_rule(pruned)


def _one_per_color_rival(grid):
    """Treat each color as one source, retaining its first row-major occurrence."""
    pruned = full_grid(len(grid), len(grid[0]), 0)
    seen = set()
    for r, c, color in _sources(grid):
        if color not in seen:
            pruned[r][c] = color
            seen.add(color)
    return _scan_rule(pruned)


def _right_only_rival(grid):
    return [[next((row[k] for k in range(c, -1, -1) if row[k]), 0)
             for c in range(len(row))] for row in grid]


def _same_row_witness(grid):
    return any(len({v for v in row if v}) > 1 for row in grid)


def _repeat_witness(grid):
    sources = _sources(grid)
    return any(len({r for r, _, v in sources if v == color}) > 1
               for color in {v for _, _, v in sources})


SEMANTIC_RIVALS = {
    "leftmost_source_per_row": _leftmost_row_rival,
    "one_source_per_color": _one_per_color_rival,
    "right_only": _right_only_rival,
}
SEMANTIC_WITNESSES = {
    "same_row_priority": _same_row_witness,
    "repeated_color_sources": _repeat_witness,
    "downward_leg": lambda grid: bool(_sources(grid)) and not any(grid[-1]),
}
WITNESS_RIVALS = {
    "same_row_priority": ["leftmost_source_per_row"],
    "repeated_color_sources": ["one_source_per_color"],
    "downward_leg": ["right_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in ("leftmost_source_per_row", "one_source_per_color")}


def lesson_identifiable(demos, query):
    """Relative to named competitors only; not a proof of unique induction.

    Uses visible demonstration labels, never a private query label or oracle.
    Remaining rivals are reported even if they happen to agree on this query.
    """
    if not isinstance(demos, list) or not demos:
        return ["at least one visible demonstration is required"]
    if any(not isinstance(d, dict) or "input" not in d or "output" not in d for d in demos):
        return ["each demonstration requires input and output"]
    return [f"visible demonstrations do not refute {name}" for name, rule in LESSON_COMPETITORS.items()
            if all(rule(d["input"]) == d["output"] for d in demos)]
