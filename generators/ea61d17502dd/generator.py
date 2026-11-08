"""Crossed-strand inputs for the woven-rectangle ARC rule.

A horizontal and vertical nonzero segment cross on a zero background.  Each
segment has a majority base color and exactly two minority markers of a second
color.  The crossing contains one base color, selecting the primary strand.
The selected Racket authority weaves the marker-bounded rectangle; this module
only samples lawful inputs and supplies independently testable semantic hooks.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ea61d17502dd"
TASK_ID = GENERATOR_ID
RULE_HASH = "b956a6f1bc99"
VERSION = "3.1.0"
SUMMARY = (
    "Two contiguous crossing strands carry four distinct colors: a majority "
    "base and two equal minority markers on each strand. The crossing base "
    "selects horizontal or vertical priority. The authority fills the rectangle "
    "bounded horizontally by the two horizontal markers and vertically by the "
    "crossing plus both vertical markers with a parity-dependent woven plaid."
)

INVARIANTS = [
    "all nonzero cells lie on one uniquely dominant row or one uniquely dominant column",
    "both strands are contiguous and are either both full-span or both strict subsegments",
    "excluding the crossing, each strand has one majority base and exactly two markers of one minority color",
    "the four base/marker colors are distinct and the crossing equals exactly one strand base",
    "vertical markers may lie on one side of the crossing or straddle it",
]

PRIMARIES = ("horizontal", "vertical")
VERTICAL_RELATIONS = ("outside", "straddle")
STRAND_EXTENTS = ("full", "partial")
DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h": {"type": "int", "default": "canonical schedule plus weighted 10..25", "valid": "10..25"},
    "grid_w": {"type": "int", "default": "canonical schedule plus weighted 10..15", "valid": "10..15"},
    "primary": {"type": "str", "default": "3-profile teaching schedule", "valid": "horizontal|vertical"},
    "vertical_relation": {"type": "str", "default": "3-profile teaching schedule", "valid": "outside|straddle"},
    "strand_extent": {"type": "str", "default": "3-profile teaching schedule", "valid": "full|partial"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3

# Every consecutive three samples contains both crossing priorities, a partial
# geometry, one outside case, and two straddled-marker counterexamples.  The
# duplicate witness keeps every three-demo subset of a four-pair episode from
# losing all evidence against the crossing-to-farthest shortcut under rotation.
_TEACHING_SCHEDULE = (
    ("horizontal", "outside", "full"),
    ("vertical", "straddle", "partial"),
    ("horizontal", "straddle", "partial"),
)
# The first four residues guarantee every 20-draw profile-floor run sees all
# unique public dimensions in every difficulty band.  Residue four is broad.
_SIZE_SCHEDULE = ((10, 10), (12, 12), (15, 15), (25, 15), None)


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"difficulty must be one of easy|medium|hard|None, got {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        if name in overrides:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if "grid_h" in overrides and not 10 <= overrides["grid_h"] <= 25:
        raise ValueError("grid_h must be in 10..25")
    if "grid_w" in overrides and not 10 <= overrides["grid_w"] <= 15:
        raise ValueError("grid_w must be in 10..15")
    domains = {
        "primary": PRIMARIES,
        "vertical_relation": VERTICAL_RELATIONS,
        "strand_extent": STRAND_EXTENTS,
    }
    for name, domain in domains.items():
        if name in overrides:
            value = overrides[name]
            if type(value) is not str:
                raise TypeError(f"{name} must be a string, not {type(value).__name__}")
            if value not in domain:
                raise ValueError(f"{name} must be one of {domain}, got {value!r}")


def _weighted_dimension(ctx, name, lo, hi, difficulty):
    values = list(range(lo, hi + 1))
    if name == "grid_h":
        favored = {
            None: range(10, 26),
            "easy": range(10, 16),
            "medium": range(12, 21),
            "hard": range(16, 26),
        }[difficulty]
    else:
        favored = {
            None: range(10, 16),
            "easy": range(10, 13),
            "medium": range(11, 15),
            "hard": range(13, 16),
        }[difficulty]
    choices = values + [value for value in favored for _ in range(4)]
    return ctx.draw_rng(f"{name}_broad").choice(choices)


def _effective_axes(seed, sample_index, difficulty, overrides):
    """Resolve scheduled defaults, then feed every exact axis through GenCtx.

    The override checker audits the final context's keyed provenance.  A small
    planning context is used only for the broad size residue; the final context
    receives all resolved values as effective overrides and records each one
    through its typed draw method.
    """
    effective = dict(overrides)
    scheduled_size = _SIZE_SCHEDULE[sample_index % len(_SIZE_SCHEDULE)]
    if scheduled_size is not None:
        effective.setdefault("grid_h", scheduled_size[0])
        effective.setdefault("grid_w", scheduled_size[1])
    elif "grid_h" not in effective or "grid_w" not in effective:
        planner = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides={},
        )
        if "grid_h" not in effective:
            effective["grid_h"] = _weighted_dimension(
                planner, "planned_grid_h", 10, 25, difficulty
            )
        if "grid_w" not in effective:
            effective["grid_w"] = _weighted_dimension(
                planner, "planned_grid_w", 10, 15, difficulty
            )

    scheduled_profile = _TEACHING_SCHEDULE[
        sample_index % len(_TEACHING_SCHEDULE)
    ]
    effective.setdefault("primary", scheduled_profile[0])
    effective.setdefault("vertical_relation", scheduled_profile[1])
    effective.setdefault("strand_extent", scheduled_profile[2])
    return effective


def _segment(dimension, extent, rng):
    if extent == "full":
        return 0, dimension - 1
    length = rng.randint(6, dimension - 1)
    start = rng.randint(0, dimension - length)
    return start, start + length - 1


def _choose_crossing(v_start, v_end, h_start, h_end, relation, rng):
    if relation == "straddle":
        row_candidates = list(range(v_start + 1, v_end))
    else:
        row_candidates = [
            row for row in range(v_start, v_end + 1)
            if row - v_start >= 2 or v_end - row >= 2
        ]
    col_candidates = list(range(h_start, h_end + 1))
    row = rng.choice(row_candidates)
    col = rng.choice(col_candidates)
    return row, col


def _vertical_markers(v_start, v_end, row, relation, rng):
    above = list(range(v_start, row))
    below = list(range(row + 1, v_end + 1))
    if relation == "outside":
        sides = [side for side in (above, below) if len(side) >= 2]
        return sorted(rng.sample(rng.choice(sides), 2))
    pairs = [
        (upper, lower)
        for upper in above
        for lower in below
        if row - upper != lower - row
    ]
    if not pairs:
        pairs = [(upper, lower) for upper in above for lower in below]
    return list(rng.choice(pairs))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    effective = _effective_axes(
        seed, sample_index, difficulty, overrides
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 10, 25)
    w = ctx.draw_int("grid_w", 10, 15)
    primary = ctx.draw_choice("primary", PRIMARIES)
    relation = ctx.draw_choice("vertical_relation", VERTICAL_RELATIONS)
    extent = ctx.draw_choice("strand_extent", STRAND_EXTENTS)
    rng = ctx.draw_rng("crossed_strands")
    h_start, h_end = _segment(w, extent, rng)
    v_start, v_end = _segment(h, extent, rng)
    row, col = _choose_crossing(v_start, v_end, h_start, h_end, relation, rng)

    hbase, hspec, vbase, vspec = ctx.draw_distinct_colors(
        "strand_colors", n=4, exclude={0}
    )
    grid = full_grid(h, w, 0)
    for c in range(h_start, h_end + 1):
        grid[row][c] = hbase
    for r in range(v_start, v_end + 1):
        grid[r][col] = vbase

    h_candidates = [c for c in range(h_start, h_end + 1) if c != col]
    h_markers = rng.sample(h_candidates, 2)
    v_markers = _vertical_markers(v_start, v_end, row, relation, rng)
    for c in h_markers:
        grid[row][c] = hspec
    for r in v_markers:
        grid[r][col] = vspec
    grid[row][col] = hbase if primary == "horizontal" else vbase
    return grid


def _recover(grid):
    h, w = len(grid), len(grid[0])
    row_counts = [sum(value != 0 for value in values) for values in grid]
    col_counts = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    row = row_counts.index(max(row_counts))
    col = col_counts.index(max(col_counts))
    hvals = [grid[row][c] for c in range(w) if c != col and grid[row][c] != 0]
    vvals = [grid[r][col] for r in range(h) if r != row and grid[r][col] != 0]
    hcounts, vcounts = Counter(hvals), Counter(vvals)
    hbase = max(hcounts, key=hcounts.get)
    vbase = max(vcounts, key=vcounts.get)
    hspec = next(color for color in hcounts if color != hbase)
    vspec = next(color for color in vcounts if color != vbase)
    hcols = [c for c in range(w) if c != col and grid[row][c] == hspec]
    vrows = [r for r in range(h) if r != row and grid[r][col] == vspec]
    hsegment = [c for c in range(w) if grid[row][c] != 0]
    vsegment = [r for r in range(h) if grid[r][col] != 0]
    return {
        "h": h,
        "w": w,
        "row": row,
        "col": col,
        "hbase": hbase,
        "hspec": hspec,
        "vbase": vbase,
        "vspec": vspec,
        "hcols": hcols,
        "vrows": vrows,
        "hsegment": hsegment,
        "vsegment": vsegment,
        "primary": "horizontal" if grid[row][col] == hbase else "vertical",
    }


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    info = _recover(grid)
    full = (
        info["hsegment"] == list(range(info["w"]))
        and info["vsegment"] == list(range(info["h"]))
    )
    partial = (
        info["hsegment"] != list(range(info["w"]))
        and info["vsegment"] != list(range(info["h"]))
    )
    lo, hi = min(info["vrows"]), max(info["vrows"])
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "primary": info["primary"],
        "vertical_relation": "straddle" if lo < info["row"] < hi else "outside",
        "strand_extent": "full" if full else "partial" if partial else "mixed",
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    h = len(grid)
    errors = []
    if not 10 <= h <= 25:
        errors.append(f"grid height {h} outside 10..25")
    if not 10 <= w <= 15:
        errors.append(f"grid width {w} outside 10..15")
    colors = {value for row in grid for value in row}
    if 0 not in colors:
        errors.append("expected background color 0")
    nonzero = colors - {0}
    if len(nonzero) != 4:
        errors.append(f"expected exactly four nonzero colors, found {len(nonzero)}")

    row_counts = [sum(value != 0 for value in row) for row in grid]
    col_counts = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
    max_row, max_col = max(row_counts), max(col_counts)
    rows = [r for r, count in enumerate(row_counts) if count == max_row]
    cols = [c for c, count in enumerate(col_counts) if count == max_col]
    if len(rows) != 1 or max_row < 6:
        errors.append(f"expected one dominant row with at least 6 cells, got {rows} count={max_row}")
    if len(cols) != 1 or max_col < 6:
        errors.append(f"expected one dominant column with at least 6 cells, got {cols} count={max_col}")
    if len(rows) != 1 or len(cols) != 1:
        return errors
    row, col = rows[0], cols[0]

    off_axis = [
        (r, c) for r in range(h) for c in range(w)
        if grid[r][c] != 0 and r != row and c != col
    ]
    if off_axis:
        errors.append(f"nonzero cells must lie on the dominant row/column, found {off_axis[:3]}")
    if grid[row][col] == 0:
        errors.append("crossing cell must be nonzero")

    hsegment = [c for c in range(w) if grid[row][c] != 0]
    vsegment = [r for r in range(h) if grid[r][col] != 0]
    if hsegment and hsegment != list(range(min(hsegment), max(hsegment) + 1)):
        errors.append("horizontal strand must be contiguous")
    if vsegment and vsegment != list(range(min(vsegment), max(vsegment) + 1)):
        errors.append("vertical strand must be contiguous")
    hfull = hsegment == list(range(w))
    vfull = vsegment == list(range(h))
    if hfull != vfull:
        errors.append("strands must be both full-span or both partial")

    hvals = [grid[row][c] for c in hsegment if c != col]
    vvals = [grid[r][col] for r in vsegment if r != row]
    hcounts, vcounts = Counter(hvals), Counter(vvals)
    if len(hcounts) != 2:
        errors.append(f"horizontal strand excluding crossing needs two colors, found {dict(hcounts)}")
    if len(vcounts) != 2:
        errors.append(f"vertical strand excluding crossing needs two colors, found {dict(vcounts)}")
    if len(hcounts) != 2 or len(vcounts) != 2:
        return errors

    hbase, hbase_n = hcounts.most_common(1)[0]
    vbase, vbase_n = vcounts.most_common(1)[0]
    hspec = next(color for color in hcounts if color != hbase)
    vspec = next(color for color in vcounts if color != vbase)
    if hcounts[hspec] != 2 or hbase_n <= hcounts[hspec]:
        errors.append(f"horizontal markers/base counts must be 2 and >2, got {dict(hcounts)}")
    if vcounts[vspec] != 2 or vbase_n <= vcounts[vspec]:
        errors.append(f"vertical markers/base counts must be 2 and >2, got {dict(vcounts)}")
    if len({hbase, hspec, vbase, vspec}) != 4:
        errors.append("horizontal/vertical base and marker colors must all be distinct")
    if grid[row][col] not in (hbase, vbase):
        errors.append("crossing must contain the horizontal or vertical base color")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _weave(grid, *, crossing_to_farthest=False):
    info = _recover(grid)
    h, w = info["h"], info["w"]
    row = info["row"]
    near = min(info["vrows"], key=lambda r: abs(r - row))
    far = max(info["vrows"], key=lambda r: abs(r - row))
    if crossing_to_farthest:
        min_row, max_row = sorted((row, far))
    else:
        min_row = min([row, *info["vrows"]])
        max_row = max([row, *info["vrows"]])
    min_col, max_col = min(info["hcols"]), max(info["hcols"])
    horizontal_primary = info["primary"] == "horizontal"
    out = [[0] * w for _ in range(h)]
    for r in range(min_row, max_row + 1):
        warp_row = (r - min_row) % 2 == 0
        in_band = min(near, far) <= r <= max(near, far)
        for c in range(min_col, max_col + 1):
            warp_col = (c - min_col) % 2 == 0
            if warp_row:
                if in_band:
                    if warp_col:
                        value = info["vspec"]
                    elif r == near and horizontal_primary:
                        value = info["hbase"]
                    else:
                        value = info["vbase"]
                else:
                    value = info["hspec"] if warp_col else info["vbase"]
            elif horizontal_primary:
                value = info["hbase"]
            else:
                value = info["hbase"] if warp_col else info["vbase"]
            out[r][c] = value
    return out


def rule_mirror(grid):
    """Python mirror used for diagnostics; the selected Racket source is authority."""
    return _weave(deepcopy(grid), crossing_to_farthest=False)


def _crossing_to_farthest(grid):
    """Wrong canonical-fitting rival: ignore the nearer straddled marker for bounds."""
    return _weave(deepcopy(grid), crossing_to_farthest=True)


def _vertical_straddle(grid):
    try:
        return observe_overrides(grid)["vertical_relation"] == "straddle"
    except Exception:
        return False


SEMANTIC_WITNESSES = {"vertical_straddle": _vertical_straddle}
SEMANTIC_RIVALS = {"crossing_to_farthest": _crossing_to_farthest}
WITNESS_RIVALS = {"vertical_straddle": ["crossing_to_farthest"]}
CANONICAL_SHORTCUTS = {"crossing_to_farthest": _crossing_to_farthest}
LESSON_COMPETITORS = {"crossing_to_farthest": _crossing_to_farthest}


def lesson_identifiable(demos, query):
    """Return named surviving wrong rules; [] means demos refute all declared rivals."""
    problems = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
        except Exception as exc:
            problems.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            problems.append(f"{name} fits every demonstration")
    return problems
