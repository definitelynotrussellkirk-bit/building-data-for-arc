"""Inputs for bbb1b8b6: merge only when the two panels are zero-complements.

The unchanged canonical Racket rule checks ALL aligned cells. If exactly one
cell in every pair is nonzero, overlay the panels while preserving colors.
Otherwise return the entire left panel unchanged, including its zeros.

A seed-permuted four-profile curriculum exposes both Boolean failure modes and
an equal-population trap. Generation constructs inputs only. Audit mirrors and
wrong solvers below are for semantic checks, never for producing dataset labels.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "27080597d778"
VERSION = "2.0.0"
RULE_HASH = "7362bea2dda7"
SUMMARY = (
    "A height-3..10, width-9 grid has two width-4 monochrome/zero panels and a "
    "gray separator in column 4. Overlay the panels, preserving their colors, "
    "only if every aligned cell pair contains exactly one nonzero cell. If "
    "any pair overlaps or is empty on both sides, output the complete left "
    "panel unchanged. Generate complement, overlap-only, gap-only and balanced "
    "overlap-plus-gap cases, including canonical-height/color anchors."
)
INVARIANTS = [
    "height in 3..10, width exactly 9, rectangular integer grids with colors 0..9",
    "column 4 is all 5; neither data panel uses 5",
    "each data panel uses at most one nonzero color; the two colors may coincide",
    "both globally complementary and noncomplementary panels are legal",
    "ordinary draws retain a clean row with a right-only cell to expose global fallback",
]
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15
BRANCHES = ("complement", "overlap", "gap", "balanced")
SCHEDULE_PROFILES = BRANCHES
FILL_LAYOUTS = ("scattered", "alternating", "left_heavy", "right_heavy", "diag", "checker")
PALETTE_KINDS = ("distinct", "same")
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
CANONICAL_RIGHT_COLORS = (2, 3, 6, 7)
HELPFUL_TEXTURES = FILL_LAYOUTS
# These are legal rule-domain edge cases, not malformed negative examples.
# They are available only through an explicit diagnostic texture override.
DEGENERATE_TEXTURES = ("empty_halves", "full_left", "full_right")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware with 40% height-4 anchors", "valid": "3..10"},
    "color_left": {"type": "color", "default": "canonical 1 or keyed non-gray color", "valid": "1|2|3|4|6|7|8|9"},
    "color_right": {"type": "color", "default": "keyed color respecting palette_kind", "valid": "1|2|3|4|6|7|8|9"},
    "branch": {"type": "enum", "default": "seed-permuted four-slot schedule", "valid": "|".join(BRANCHES)},
    "palette_kind": {"type": "enum", "default": "distinct; equal explicit color pins imply same", "valid": "distinct|same"},
    "fill_layout": {"type": "enum", "default": "two-thirds scattered; otherwise structured", "valid": "|".join(FILL_LAYOUTS)},
    "balance": {"type": "enum", "default": "scattered-only density hint; a lone pin selects scattered", "valid": "even|left|right"},
    "max_defects": {"type": "int", "default": "1 except hard band 3; upper bound, not exact count", "valid": "1..3"},
}
# Reject only genuinely contradictory palettes/aliases. Single pins always work.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_kind": "distinct", "color_left": color, "color_right": color}
    for color in COLORS
] + [
    {"palette_kind": "same", "color_left": left, "color_right": right}
    for left in COLORS for right in COLORS if left != right
] + [
    {"fill_layout": layout, "balance": balance}
    for layout in FILL_LAYOUTS if layout != "scattered"
    for balance in ("even", "left", "right")
] + [
    {"branch": "complement", "max_defects": value} for value in (1, 2, 3)
] + [("texture", "fill_layout"), ("texture", "branch"), ("texture", "balance")]
Grid = list[list[int]]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}; inert v1 anchor/asymmetry knobs were retired")
    for name, lo, hi in (("grid_h", 3, 10), ("max_defects", 1, 3)):
        if name in overrides and (type(overrides[name]) is not int or not lo <= overrides[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    for name in ("color_left", "color_right"):
        if name in overrides and (type(overrides[name]) is not int or overrides[name] not in COLORS):
            raise ValueError(f"{name} must be one of {COLORS}")
    domains = {"branch": BRANCHES, "palette_kind": PALETTE_KINDS,
               "fill_layout": FILL_LAYOUTS, "balance": ("even", "left", "right"),
               "texture": FILL_LAYOUTS + DEGENERATE_TEXTURES}
    for name, domain in domains.items():
        if name in overrides and (not isinstance(overrides[name], str) or overrides[name] not in domain):
            raise ValueError(f"{name} must be one of {domain}")
    texture = overrides.get("texture")
    explicit_layout = overrides.get("fill_layout", texture)
    if "balance" in overrides and explicit_layout is not None and explicit_layout != "scattered":
        raise ValueError("balance is only defined for scattered layouts, not fixed-density or diagnostic textures")
    if "max_defects" in overrides and overrides.get("branch") == "complement":
        raise ValueError("max_defects is inapplicable to an explicitly fault-free complement branch")
    if texture and "fill_layout" in overrides and texture != overrides["fill_layout"]:
        raise ValueError("texture and fill_layout specify conflicting layouts")
    if texture in DEGENERATE_TEXTURES and "branch" in overrides:
        raise ValueError("diagnostic texture and branch cannot be combined")
    if "color_left" in overrides and "color_right" in overrides:
        same = overrides["color_left"] == overrides["color_right"]
        kind = overrides.get("palette_kind")
        if (kind == "same" and not same) or (kind == "distinct" and same):
            raise ValueError("palette_kind conflicts with color_left/color_right")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive indices cover all profiles; seed permutes order.

    Exporters should independently shuffle demonstrations (the workspace tool
    does) rather than expose a fixed cyclic query/demonstration-position relation.
    """
    del difficulty
    order = list(BRANCHES)
    stable_rng(seed, f"{TASK_ID}:branch-order", VERSION).shuffle(order)
    return order[sample_index % len(order)]


def _draw_palette(ctx, overrides, anchored: bool) -> tuple[int, int]:
    implied_same = ("color_left" in overrides and "color_right" in overrides
                    and overrides["color_left"] == overrides["color_right"])
    default = "same" if implied_same else "distinct"
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS if "palette_kind" in overrides else (default,))
    if kind == "same" and "color_right" in overrides and "color_left" not in overrides:
        left_options = (overrides["color_right"],)
    else:
        left_options = COLORS if "color_left" in overrides or not anchored else (1,)
        if kind == "distinct" and "color_right" in overrides:
            left_options = tuple(c for c in left_options if c != overrides["color_right"])
            if not left_options:  # right=1 overrides a canonical palette anchor
                left_options = tuple(c for c in COLORS if c != overrides["color_right"])
    left = ctx.draw_choice("color_left", left_options)
    if kind == "same":
        right_options = (left,)
    else:
        pool = COLORS if "color_right" in overrides or not anchored else CANONICAL_RIGHT_COLORS
        right_options = tuple(c for c in pool if c != left)
    right = ctx.draw_choice("color_right", right_options)
    return left, right


def _make_mask(height: int, layout: str, balance: str, rng) -> list[list[bool]]:
    center = {"even": 0.5, "left": 0.72, "right": 0.28}[balance]
    density = rng.uniform(center - 0.12, center + 0.12)
    phase = rng.randrange(2)
    offset = rng.randrange(4)
    mask = []
    for r in range(height):
        row = []
        for c in range(4):
            if layout == "alternating":
                left = (r + phase) % 2 == 0
            elif layout == "checker":
                left = (r + c + phase) % 2 == 0
            elif layout == "diag":
                left = c <= (r + offset) % 4
            else:
                p = 0.82 if layout == "left_heavy" else 0.18 if layout == "right_heavy" else density
                left = rng.random() < p
            row.append(left)
        mask.append(row)
    # Geometry-only repairs, not output-based rejection sampling. Both roles
    # remain visible, and right-only cells occupy at least two different rows.
    cells = [(r, c) for r in range(height) for c in range(4)]
    rng.shuffle(cells)
    for value in (True, False):
        missing = max(0, 2 - sum(mask[r][c] == value for r, c in cells))
        for r, c in [cell for cell in cells if mask[cell[0]][cell[1]] != value][:missing]:
            mask[r][c] = value
    right_rows = {r for r, c in cells if not mask[r][c]}
    if len(right_rows) == 1:
        r, c = next(cell for cell in cells if cell[0] not in right_rows)
        mask[r][c] = False
    return mask


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError("seed and nonnegative sample_index must be integers")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    anchored = ctx.draw_rng("canonical-anchor").random() < 0.40
    lo, hi = {"easy": (3, 5), "hard": (7, 10)}.get(difficulty, (4, 8))
    if "grid_h" in overrides:
        lo, hi = 3, 10
    elif anchored:
        lo = hi = 4
    height = ctx.draw_int("grid_h", lo, hi)
    left, right = _draw_palette(ctx, overrides, anchored)
    branch = ctx.draw_choice("branch", BRANCHES if "branch" in overrides
                             else (schedule_profile(seed, sample_index),))
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        grid = full_grid(height, 9, 0)
        for row in grid:
            row[4] = 5
            if texture == "full_left":
                row[:4] = [left] * 4
            elif texture == "full_right":
                row[5:] = [right] * 4
        return grid
    layout_options = ((texture,) if texture else FILL_LAYOUTS if "fill_layout" in overrides
                      else ("scattered",) if "balance" in overrides
                      else ("scattered",) * 10 + FILL_LAYOUTS[1:])
    layout = ctx.draw_choice("fill_layout", layout_options)
    balance = ctx.draw_choice("balance", ("even", "left", "right"))
    max_defects = ctx.draw_int("max_defects", 1, 3) if "max_defects" in overrides else ctx.draw_choice("max_defects", (3 if difficulty == "hard" else 1,))
    mask = _make_mask(height, layout, balance, ctx.draw_rng("mask"))
    grid = full_grid(height, 9, 0)
    for r, row in enumerate(mask):
        grid[r][4] = 5
        for c, use_left in enumerate(row):
            grid[r][c if use_left else c + 5] = left if use_left else right
    # Preserve a right-only cell on a completely unmodified row. The candidate
    # sets exist by _make_mask's two-role / two-right-row construction.
    clean_rows = [r for r in range(height) if not all(mask[r])
                  and any(mask[rr][c] for rr in range(height) if rr != r for c in range(4))
                  and any(not mask[rr][c] for rr in range(height) if rr != r for c in range(4))]
    rng = ctx.draw_rng("faults")
    clean_row = rng.choice(clean_rows)
    overlaps = [(r, c) for r in range(height) if r != clean_row for c in range(4) if mask[r][c]]
    gaps = [(r, c) for r in range(height) if r != clean_row for c in range(4) if not mask[r][c]]
    rng.shuffle(overlaps)
    rng.shuffle(gaps)
    limit = min(max_defects, len(overlaps), len(gaps))
    count = rng.randint(1, limit)
    if branch in ("overlap", "balanced"):
        for r, c in overlaps[:count]:
            grid[r][c + 5] = right
    if branch in ("gap", "balanced"):
        for r, c in gaps[:count]:
            grid[r][c + 5] = 0
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful input grammar, not just the rule's true branch."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    errors = []
    if not 3 <= len(grid) <= 10:
        errors.append(f"height {len(grid)} outside expected 3..10")
    if any(not isinstance(row, list) or len(row) != 9 for row in grid):
        return errors + ["every row must have width 9"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return errors + ["cells must be integer colors 0..9 (not booleans)"]
    if any(row[4] != 5 for row in grid):
        errors.append("separator column 4 is not all color 5")
    for name, start in (("left", 0), ("right", 5)):
        colors = {row[c] for row in grid for c in range(start, start + 4) if row[c]}
        if len(colors) > 1:
            errors.append(f"{name} panel uses multiple nonzero colors")
        if 5 in colors:
            errors.append(f"{name} panel uses separator color 5")
    return errors


def _occupancy(grid: Grid) -> Counter:
    return Counter((bool(row[c]), bool(row[c + 5])) for row in grid for c in range(4))


def observe_overrides(grid: Grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = _occupancy(grid)
    overlap, gap = counts[True, True], counts[False, False]
    if overlap and gap:
        branch = "balanced" if overlap == gap else "mixed"
    else:
        branch = "overlap" if overlap else "gap" if gap else "complement"
    result: dict[str, Any] = {"grid_h": len(grid), "branch": branch}
    left = {v for row in grid for v in row[:4] if v}
    right = {v for row in grid for v in row[5:] if v}
    if left:
        result["color_left"] = next(iter(left))
    if right:
        result["color_right"] = next(iter(right))
    if left and right:
        result["palette_kind"] = "same" if left == right else "distinct"
    # Layout and balance are construction distributions, not uniquely recoverable
    # semantic roles. max_defects is an upper bound, so do not invent observations.
    return result


def strict_canonical_like(grid: Grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    seen = observe_overrides(grid)
    if len(grid) != 4:
        errors.append("canonical-height anchor requires four rows")
    if seen.get("color_left") != 1:
        errors.append("canonical palette has left color 1")
    if seen.get("color_right") not in CANONICAL_RIGHT_COLORS:
        errors.append("canonical right color is 2, 3, 6, or 7")
    return errors


# Audit-only solvers. Runtime/exports still derive every label with Racket.
def _left(grid: Grid) -> Grid:
    return [row[:4] for row in grid]


def _overlay(grid: Grid) -> Grid:
    return [[row[c] or row[c + 5] for c in range(4)] for row in grid]


def audit_output(grid: Grid) -> Grid:
    counts = _occupancy(grid)
    return _left(grid) if counts[True, True] or counts[False, False] else _overlay(grid)


def _no_overlaps(grid: Grid) -> Grid:
    return _left(grid) if _occupancy(grid)[True, True] else _overlay(grid)


def _no_gaps(grid: Grid) -> Grid:
    return _left(grid) if _occupancy(grid)[False, False] else _overlay(grid)


def _population_count(grid: Grid) -> Grid:
    count = sum(v != 0 for row in grid for v in row[:4] + row[5:])
    return _overlay(grid) if count == 4 * len(grid) else _left(grid)


def _row_local(grid: Grid) -> Grid:
    return [audit_output([row])[0] for row in grid]


def _pixel_xor(grid: Grid) -> Grid:
    return [[(row[c] or row[c + 5]) if bool(row[c]) != bool(row[c + 5]) else 0
             for c in range(4)] for row in grid]


def _recolor_merge(grid: Grid) -> Grid:
    color = next((v for row in grid for v in row[:4] if v), 1)
    return [[color if v else 0 for v in row] for row in audit_output(grid)]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "always_left": _left,
    "always_overlay": _overlay,
    "no_overlaps_suffice": _no_overlaps,
    "no_gaps_suffice": _no_gaps,
    "population_count": _population_count,
    "row_local": _row_local,
    "pixel_xor": _pixel_xor,
    "recolor_merge": _recolor_merge,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in ("no_overlaps_suffice", "no_gaps_suffice")}


def _witness(grid: Grid, profile: str) -> bool:
    if self_check(grid) or observe_overrides(grid)["branch"] != profile:
        return False
    return audit_output(grid) != (_left(grid) if profile == "complement" else _overlay(grid))


SEMANTIC_WITNESSES = {
    "merge_preserves_both_colors": lambda g: _witness(g, "complement") and observe_overrides(g).get("palette_kind") == "distinct",
    "overlap_without_gaps": lambda g: _witness(g, "overlap"),
    "gap_without_overlaps": lambda g: _witness(g, "gap"),
    "balanced_faults": lambda g: _witness(g, "balanced"),
    "global_not_row_local": lambda g: not self_check(g) and audit_output(g) != _row_local(g),
}
WITNESS_RIVALS = {
    "merge_preserves_both_colors": ["always_left", "recolor_merge"],
    "overlap_without_gaps": ["no_gaps_suffice", "always_overlay"],
    "gap_without_overlaps": ["no_overlaps_suffice", "always_overlay"],
    "balanced_faults": ["population_count"],
    "global_not_row_local": ["row_local"],
}


def _pair_errors(item, name: str) -> list[str]:
    if not isinstance(item, dict):
        return [f"{name} must be an input/output pair"]
    errors = self_check(item.get("input"))
    if errors:
        return [f"{name}: {e}" for e in errors]
    output = item.get("output")
    if (not isinstance(output, list) or len(output) != len(item["input"])
            or any(not isinstance(row, list) or len(row) != 4 for row in output)
            or any(type(v) is not int or not 0 <= v <= 9 for row in output for v in row)):
        return [f"{name}: output must be a height-matched width-4 integer grid"]
    if output != audit_output(item["input"]):
        return [f"{name}: output disagrees with audit mirror; verify with canonical Racket"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Query-specific falsification of named rivals, not a uniqueness proof."""
    if not isinstance(demos, list) or not demos:
        return ["lesson needs nonempty demonstrations"]
    errors = [error for i, demo in enumerate(demos) for error in _pair_errors(demo, f"demo {i}")]
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors
    return [f"competitor {name!r} fits every demo but gives a different query answer"
            for name, solver in SEMANTIC_RIVALS.items()
            if all(solver(demo["input"]) == demo["output"] for demo in demos)
            and solver(query["input"]) != query["output"]]


def mutation_fixtures():
    grid = generate(17, 0, branch="complement")
    separator = [row[:] for row in grid]
    separator[0][4] = 0
    foreign = [row[:] for row in grid]
    color = observe_overrides(grid)["color_left"]
    foreign[0][0] = next(c for c in COLORS if c != color)
    # Use another existing left pixel so replacing one cannot remove the old color.
    gray_panel = [row[:] for row in grid]
    gray_panel[0][0] = 5
    return [("broken_separator", separator), ("foreign_panel_color", foreign),
            ("gray_data_panel", gray_panel), ("ragged", grid[:-1] + [[0]])]
