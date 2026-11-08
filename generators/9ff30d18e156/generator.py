"""Endpoint Segment Fill: diverse inputs for the unchanged Racket authority.

Each repeated nonzero color owns its row-local min/max interval. Generation
constructs inputs only; labels must still come from Racket. Distinct repeated
colors have disjoint intervals, avoiding an unillustrated overwrite-order rule.
The four-profile cycle gives every three consecutive default demonstrations
counterexamples to both whole-row filling and exactly-two-occurrence filling.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9ff30d18e156"
TASK_ID = "9ff30d18e156"
VERSION = "2.0.0"
RULE_HASH = "efbc8aee85e7"
EXAMPLES_NEEDED = 3
SUMMARY = "Fill each repeated color's row-local span; sample endpoints, multi-hit and disjoint-color rows."
INVARIANTS = [
    "Rectangular integer grid with colors 0..9 and background 0.",
    "At least one repeated nonzero color has an unfilled cell inside its row-local span.",
    "Intervals of different repeated colors in a row do not overlap; singleton colors are allowed.",
    "n_pairs is the exact number of productive rows, not the number of colors or endpoint cells.",
]
HELPFUL_TEXTURES = ("endpoints", "mixed", "multihit", "multicolor")
# Diagnostic identity fixtures are not public generation modes.
DEGENERATE_TEXTURES = ()
SCHEDULE_PROFILES = HELPFUL_TEXTURES
AXES = {
    "grid_h": {"type": "int", "default": "difficulty: easy 7..8, medium 7..9, hard 8..9", "valid": "3..10"},
    "grid_w": {"type": "int", "default": "difficulty: easy 10..11, medium 10..13, hard 12..13", "valid": "8..14"},
    "n_pairs": {"type": "int", "default": "3", "valid": "1..5",
                "doc": "Exact number of productive rows. Must not exceed grid_h."},
    "texture": {"type": "str", "default": "four-profile cycle by sample_index",
                "valid": "endpoints|mixed|multihit|multicolor",
                "doc": "mixed combines two separated colors with >=3 hits of one color."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("grid_h", "n_pairs")]


class IncompatibleOverrides(ValueError):
    def __init__(self, message):
        super().__init__(message)
        self.incompatible_axes = ("grid_h", "n_pairs")


def _groups(row):
    counts = Counter(row)
    return {v: [c for c, x in enumerate(row) if x == v]
            for v, n in counts.items() if v != 0 and n >= 2}


def _productive(row):
    return any(any(row[c] != v for c in range(cs[0], cs[-1] + 1))
               for v, cs in _groups(row).items())


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broader non-overlapping, nonidentity task domain safely.

    This is not an exact-membership test for a finite generator profile. Small
    hand-built/canonical witnesses are valid even outside the draw-size bounds.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected nonempty rectangular grid"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["rows must be nonempty lists or tuples"]
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be in 1..30"]
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cell values must be integers in 0..9 (not bool)"]
    errors = []
    for r, row in enumerate(grid):
        spans = sorted((cs[0], cs[-1]) for cs in _groups(row).values())
        if any(left[1] >= right[0] for left, right in zip(spans, spans[1:])):
            errors.append(f"row {r}: overlapping repeated-color spans are outside the draw domain")
    if not any(_productive(row) for row in grid):
        errors.append("no productive repeated-color span")
    return errors


def schedule_profile(seed, sample_index, difficulty=None):
    return HELPFUL_TEXTURES[sample_index % len(HELPFUL_TEXTURES)]


def _paint_hits(row, start, length, color, multihit, rng):
    """Place endpoints and optional interior hits, always reserving a hole."""
    row[start] = row[start + length - 1] = color
    if multihit:
        interior = list(range(start + 1, start + length - 1))
        hole = rng.choice(interior)
        candidates = [c for c in interior if c != hole]
        for c in rng.sample(candidates, rng.randint(1, len(candidates))):
            row[c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}; supported: {', '.join(AXES)}")
    for name, lo, hi in (("grid_h", 3, 10), ("grid_w", 8, 14), ("n_pairs", 1, 5)):
        if name in overrides and (type(overrides[name]) is not int or not lo <= overrides[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if "texture" in overrides and overrides["texture"] not in HELPFUL_TEXTURES:
        raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}")
    # Difficulty changes default geometry only, never legal override bounds.
    # The rule-disambiguating profile cycle stays present in every band.
    effective = {"n_pairs": 3, "texture": schedule_profile(seed, sample_index, difficulty), **overrides}
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    n = ctx.draw_int("n_pairs", 1, 5)
    if "grid_h" in overrides and overrides["grid_h"] < n:
        raise IncompatibleOverrides("n_pairs cannot exceed grid_h")
    shape_rng = ctx.draw_rng("shape")
    h_band, w_band = {"easy": ((7, 8), (10, 11)),
                      "hard": ((8, 9), (12, 13))}.get(difficulty, ((7, 9), (10, 13)))
    ctx.overrides.setdefault("grid_h", shape_rng.randint(*h_band))
    ctx.overrides.setdefault("grid_w", shape_rng.randint(*w_band))
    h = ctx.draw_int("grid_h", max(3, n), 10)
    w = ctx.draw_int("grid_w", 8, 14)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Clean anchors preserve blank-row separation without a retry cap. Explicit
    # small-height overrides still work in the broader non-overlapping domain.
    if texture == "endpoints" and h >= 2 * n - 1:
        compressed = sorted(rng.sample(range(h - n + 1), n))
        active = [value + offset for offset, value in enumerate(compressed)]
    else:
        active = rng.sample(range(h), n)  # the requested count is exact
    primary_colors = rng.sample(range(1, 10), n)
    for r, first_color in zip(active, primary_colors):
        row = g[r]
        two = texture in ("multicolor", "mixed")
        multiple_hits = texture in ("multihit", "mixed")
        if two:
            # Five allocation buckets: left padding, first span extension,
            # separator extension, second span extension, right padding.
            first_min = 4 if multiple_hits else 3
            extras = [0] * 5
            for _ in range(w - (first_min + 1 + 3)):
                extras[rng.randrange(5)] += 1
            a = extras[0]
            la = first_min + extras[1]
            b = a + la + 1 + extras[2]
            lb = 3 + extras[3]
            second_color = rng.choice([v for v in range(1, 10) if v != first_color])
            _paint_hits(row, a, la, first_color, multiple_hits, rng)
            _paint_hits(row, b, lb, second_color, False, rng)
            spans = [(a, a + la - 1), (b, b + lb - 1)]
        else:
            length = rng.randint(4 if multiple_hits else 3, w)
            start = rng.randint(0, w - length)
            _paint_hits(row, start, length, first_color, multiple_hits, rng)
            spans = [(start, start + length - 1)]
        # Keep endpoint profiles clean canonical anchors. In the others, a
        # singleton beyond a span must survive without extending that span.
        outside = [c for c in range(w) if all(not lo <= c <= hi for lo, hi in spans)]
        if texture != "endpoints" and outside and rng.random() < 0.5:
            row[rng.choice(outside)] = rng.choice([v for v in range(1, 10) if v not in row])
        if rng.random() < 0.5:
            row.reverse()
    if texture != "endpoints":
        for r in sorted(set(range(h)) - set(active)):
            if rng.random() < 0.4:
                for c, value in zip(rng.sample(range(w), 2), rng.sample(range(1, 10), 2)):
                    g[r][c] = value
    return g


def observe_overrides(grid):
    rows = [row for row in grid if _productive(row)]
    profiles = set()
    for row in rows:
        gs = _groups(row)
        two, multi = len(gs) >= 2, any(len(cs) >= 3 for cs in gs.values())
        profiles.add("mixed" if two and multi else "multicolor" if two else "multihit" if multi else "endpoints")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_pairs": len(rows),
            "texture": next(iter(profiles)) if len(profiles) == 1 else "heterogeneous"}


def strict_canonical_like(grid):
    """Structural canonical family, not an exact size/palette membership test."""
    errors = self_check(grid)
    if errors:
        return errors
    for row in grid:
        nonzero = [v for v in row if v]
        if nonzero and (len(nonzero) != 2 or len(set(nonzero)) != 1 or not _productive(row)):
            return ["not a clean single-pair-per-active-row canonical anchor"]
    return []


# The following are explicit rival rules, not production label generators.
def rival_whole_row(grid):
    out = [list(row) for row in grid]
    for row in out:
        positions = [c for c, v in enumerate(row) if v]
        if len(positions) >= 2:
            color = row[positions[0]]
            row[positions[0]:positions[-1]+1] = [color] * (positions[-1]-positions[0]+1)
    return out


def rival_exactly_two(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for v, cs in _groups(row).items():
            if len(cs) == 2:
                out[r][cs[0]:cs[-1]+1] = [v] * (cs[-1]-cs[0]+1)
    return out


def _has_multihit(grid):
    return any(len(cs) >= 3 and any(row[c] != v for c in range(cs[0], cs[-1]+1))
               for row in grid for v, cs in _groups(row).items())


def _has_multicolor(grid):
    return any(len(_groups(row)) >= 2 for row in grid)


SEMANTIC_RIVALS = {"whole_row": rival_whole_row, "exactly_two": rival_exactly_two}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"multiple_hits": _has_multihit, "separate_color_spans": _has_multicolor}
WITNESS_RIVALS = {"multiple_hits": ["exactly_two"], "separate_color_spans": ["whole_row"]}


def lesson_identifiable(demos, query):
    """Finite-rival check only; this does not assert universal identifiability."""
    return [f"demonstrations do not refute rival {name}"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]


def mutation_fixtures():
    return [
        ("no_pairs", [[0,2,0,0,0], [0,0,0,3,0]]),
        ("mismatched_endpoints", [[2,0,0,3,0], [0,4,0,0,5]]),
        ("span_already_filled", [[0,2,2,2,0], [0,0,3,3,3]]),
        ("overlapping_spans", [[2,3,0,2,3], [0,0,0,0,0]]),
    ]
