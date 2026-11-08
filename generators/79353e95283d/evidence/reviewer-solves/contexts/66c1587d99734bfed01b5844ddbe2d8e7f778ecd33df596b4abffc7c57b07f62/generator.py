"""Input sampler for 0520fde7: aligned binary panels, AND emitted as color 2.

The selected Racket rule remains the label authority. Ordinary samples contain
all four paired-cell states, and a four-profile schedule crosses height and
separator color. Density/pattern controls describe proposals before witness
repair; they are not promises about exact final occupancy or topology.
"""
from __future__ import annotations

from functools import partial
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79353e95283d"
TASK_ID = GENERATOR_ID
RULE_HASH = "06a8d3595fe6"
VERSION = "3.0.0"
SUMMARY = (
    "Two aligned binary 3-column panels separated by a uniform color 2..9. "
    "Racket emits 2 exactly at paired 1/1 positions and 0 elsewhere. Ordinary "
    "samples teach all four Boolean inputs; crossed size/separator profiles "
    "retain canonical 3x7 gray-separator support in every difficulty band."
)
INVARIANTS = [
    "1..18 rows, width 7, binary 0/1 panels and one uniform separator in 2..9",
    "ordinary default draws contain 00, 01, 10 and 11 at aligned panel positions",
    "explicit lawful edge textures are separate from the ordinary curriculum",
]
PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
HELPFUL_TEXTURES = PANEL_PATTERNS
DEGENERATE_TEXTURES = ("no_aligned", "all_aligned", "same_panels")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
EXPECTED_OUTPUT_CODOMAIN = (0, 2)
SOLID_OUTPUT_JUSTIFICATION = (
    "The fixed Racket AND rule lawfully emits all zero for disjoint panels and "
    "all two for full overlapping panels; these are explicit edge textures, "
    "not ordinary teaching draws."
)
AXES = {
    "grid_h": {"type": "int", "default": "crossed profile: 3 or band-specific 4..18", "valid": "1..18"},
    "sep_color": {"type": "color", "default": "crossed profile: 5 or another color 2..9", "valid": "2..9"},
    "left_density": {"type": "float", "default": "rng 0.4..0.7", "valid": "0..1", "exact": False,
                     "semantics": "proposal occupancy tendency before minimum-overlap and witness repair"},
    "right_density": {"type": "float", "default": "rng 0.4..0.7", "valid": "0..1", "exact": False,
                      "semantics": "proposal occupancy tendency before minimum-overlap and witness repair"},
    "panel_pattern": {"type": "str", "default": "rng proposal style", "valid": "|".join(PANEL_PATTERNS),
                      "exact": False, "semantics": "stochastic texture proposal, not exact final topology"},
    "texture": {"type": "str", "default": "alias for panel_pattern", "exact": False,
                "valid": "|".join(PANEL_PATTERNS + DEGENERATE_TEXTURES),
                "semantics": "proposal alias or explicit lawful edge mode"},
    "aligned_pairs_target": {"type": "int", "default": "rng 1..h", "valid": "1..h*3", "exact": False,
                             "semantics": "minimum overlap; height-dependent boundary tested in task tests"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("texture", "panel_pattern"),
    ("grid_h", "aligned_pairs_target"),
    {"texture": DEGENERATE_TEXTURES, "left_density": None},
    {"texture": DEGENERATE_TEXTURES, "right_density": None},
    {"texture": "no_aligned", "aligned_pairs_target": None},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "height_and_separator", "separator_only", "height_only")
MIN_STRICT_FRAC = 0.20


def schedule_profile(seed, sample_index, difficulty=None):
    """Cross both axes once per four consecutive requested sample indices."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validated_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    values = {key: value for key, value in overrides.items() if value is not None}
    for key in ("grid_h", "sep_color", "aligned_pairs_target"):
        if key in values and type(values[key]) is not int:
            raise ValueError(f"{key} must be an integer, not a boolean or coerced value")
    for key in ("left_density", "right_density"):
        if key in values:
            value = values[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{key} must be a finite number in 0..1")
    if "panel_pattern" in values and values["panel_pattern"] not in PANEL_PATTERNS:
        raise ValueError("panel_pattern must name a supported proposal style")
    if "texture" in values and values["texture"] not in PANEL_PATTERNS + DEGENERATE_TEXTURES:
        raise ValueError("texture must name a supported proposal style or lawful edge mode")
    texture = values.get("texture")
    if texture and "panel_pattern" in values and values["panel_pattern"] != texture:
        raise ValueError("texture and panel_pattern conflict")
    if texture in DEGENERATE_TEXTURES:
        for key in ("left_density", "right_density"):
            if key in values:
                raise ValueError(f"texture={texture} and {key} are incompatible: the edge mode defines occupancy")
        if texture == "no_aligned" and "aligned_pairs_target" in values:
            raise ValueError("texture=no_aligned and aligned_pairs_target are incompatible")
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validated_overrides(overrides)
    # Normalize a helpful texture alias before creating one provenance context.
    if overrides.get("texture") in PANEL_PATTERNS:
        overrides["panel_pattern"] = overrides["texture"]
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    if "grid_h" in overrides:
        h = ctx.draw_int_strict("grid_h", 1, 18)
    elif profile in ("canonical", "separator_only"):
        h = ctx.draw_int_strict("grid_h", 3, 3)
    else:
        lo, hi = {"easy": (4, 6), "hard": (9, 18)}.get(difficulty, (4, 12))
        h = ctx.draw_int_strict("grid_h", lo, hi)
    if "sep_color" in overrides:
        sep = ctx.draw_color("sep_color", exclude={0, 1})
    else:
        choices = (5,) if profile in ("canonical", "height_only") else (2, 3, 4, 6, 7, 8, 9)
        sep = ctx.draw_choice("sep_color", choices)
    if "aligned_pairs_target" in overrides:
        target = overrides["aligned_pairs_target"]
        if not 1 <= target <= h * 3:
            raise ValueError(f"grid_h={h} and aligned_pairs_target={target} require 1..{h*3} overlap cells")
        target = ctx.draw_int_strict("aligned_pairs_target", 1, h * 3)
    else:
        target = ctx.draw_int_strict("aligned_pairs_target", 1, h)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_edge(texture, h, sep, target, ctx.draw_rng("edge_panels"))
    pattern = ctx.draw_choice("panel_pattern", PANEL_PATTERNS)
    ld = overrides.get("left_density")
    if ld is None:
        ld = ctx.draw_rng("left_density").uniform(0.4, 0.7)
    rd = overrides.get("right_density")
    if rd is None:
        rd = ctx.draw_rng("right_density").uniform(0.4, 0.7)
    grid = full_grid(h, 7, 0)
    for row in grid:
        row[3] = sep
    _fill_panel(grid, 0, pattern, ld, ctx.draw_rng("left_panel"))
    _fill_panel(grid, 4, pattern, rd, ctx.draw_rng("right_panel"))
    _ensure_teaching_states(grid, target, ctx.draw_rng("teaching_states"))
    return grid


def _fill_panel(grid, offset, pattern, density, rng):
    """Independent stochastic proposals: every style responds to density."""
    h = len(grid)
    phase_r, phase_c = rng.randrange(h), rng.randrange(3)
    bh = max(1, round(h * density))
    bw = max(1, round(3 * density))
    for r in range(h):
        for c in range(3):
            rr, cc = (r + phase_r) % h, (c + phase_c) % 3
            if pattern == "random":
                probability = density
            else:
                mask = {
                    "blob": rr < bh and cc < bw,
                    "stripes": rr % 2 == 0,
                    "checker": (rr + cc) % 2 == 0,
                    "border": rr in (0, h - 1) or cc in (0, 2),
                    "diagonal": cc == rr % 3,
                }[pattern]
                bias = 0.8 * density * (1 - density)
                probability = density + (bias if mask else -bias)
            grid[r][offset + c] = int(rng.random() < probability)


def _ensure_teaching_states(grid, target, rng):
    """Reserve movable negative witnesses, then enforce the requested minimum."""
    cells = [(r, c) for r in range(len(grid)) for c in range(3)]
    rng.shuffle(cells)
    # An explicit near-full minimum can leave fewer than three negatives.
    # In that case the requested bound takes priority; defaults always leave
    # three slots at h>=2. This is documented as outside rich default lessons.
    reserve = cells[:3] if len(cells) - target >= 3 else []
    for (r, c), (left, right) in zip(reserve, ((0, 0), (0, 1), (1, 0))):
        grid[r][c], grid[r][c + 4] = left, right
    have = _aligned_count(grid)
    for r, c in cells[len(reserve):]:
        if have >= target:
            break
        if grid[r][c] != 1 or grid[r][c + 4] != 1:
            grid[r][c] = grid[r][c + 4] = 1
            have += 1


def _draw_edge(name, h, sep, target, rng):
    grid = full_grid(h, 7, 0)
    for row in grid:
        row[3] = sep
    cells = [(r, c) for r in range(h) for c in range(3)]
    if name == "no_aligned":
        for r, c in cells:
            left, right = rng.choice(((0, 0), (0, 1), (1, 0)))
            grid[r][c], grid[r][c + 4] = left, right
    elif name == "all_aligned":
        for r, c in cells:
            grid[r][c] = grid[r][c + 4] = 1
    else:
        rng.shuffle(cells)
        count = rng.randint(target, len(cells))
        for r, c in cells[:count]:
            grid[r][c] = grid[r][c + 4] = 1
    return grid


def _aligned_count(grid):
    return sum(row[c] == row[c + 4] == 1 for row in grid for c in range(3))


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 18:
        return ["input must contain 1..18 rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 7 for row in grid):
        return ["input must be rectangular with width 7"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9; booleans are not colors"]
    separators = {row[3] for row in grid}
    if len(separators) != 1 or not 2 <= grid[0][3] <= 9:
        return ["separator must be one uniform color in 2..9"]
    if any(row[c] not in (0, 1) for row in grid for c in (0, 1, 2, 4, 5, 6)):
        return ["left and right panels must use only 0 and 1"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 3 or grid[0][3] != 5:
        return ["canonical examples have height 3 and separator color 5"]
    return []


def observe_overrides(grid):
    """Recover exact shape/color controls; overlap is a diagnostic count."""
    return {"grid_h": len(grid), "sep_color": grid[0][3], "actual_aligned_pairs": _aligned_count(grid)}


def _boolean_rival(grid, *, mask):
    """A candidate truth table for diagnostics, never a generation label source."""
    return [[2 * ((mask >> (2*row[c] + row[c+4])) & 1) for c in range(3)] for row in grid]


def _fixed_three_rows(grid):
    return _boolean_rival(grid, mask=8)[:3]


def _gray_separator_only(grid):
    if grid[0][3] != 5:
        return [[0, 0, 0] for _ in grid]
    return _boolean_rival(grid, mask=8)


def _has_state(grid, *, state):
    return any((row[c], row[c+4]) == state for row in grid for c in range(3))


# Exhaust the 15 wrong coordinatewise Boolean tables, rather than hand-picking
# only copy/OR/XOR. The intended AND table is mask 8 (only state 11 is positive).
SEMANTIC_RIVALS = {f"boolean_{mask:04b}": partial(_boolean_rival, mask=mask)
                   for mask in range(16) if mask != 8}
SEMANTIC_RIVALS.update({"fixed_three_rows": _fixed_three_rows, "gray_separator_only": _gray_separator_only})
SEMANTIC_WITNESSES = {
    "has_00": partial(_has_state, state=(0, 0)),
    "has_01": partial(_has_state, state=(0, 1)),
    "has_10": partial(_has_state, state=(1, 0)),
    "has_11": partial(_has_state, state=(1, 1)),
    "fixed_three_rows": lambda grid: len(grid) > 3,
    "gray_separator_only": lambda grid: grid[0][3] != 5 and _aligned_count(grid) > 0,
}
WITNESS_RIVALS = {
    "has_00": ["boolean_1001"], "has_01": ["boolean_1010"],
    "has_10": ["boolean_1100"], "has_11": ["boolean_0110"],
    "fixed_three_rows": ["fixed_three_rows"], "gray_separator_only": ["gray_separator_only"],
}
CANONICAL_SHORTCUTS = {"fixed_three_rows": _fixed_three_rows, "gray_separator_only": _gray_separator_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite rival check on actual labeled lessons, including query rotations."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
