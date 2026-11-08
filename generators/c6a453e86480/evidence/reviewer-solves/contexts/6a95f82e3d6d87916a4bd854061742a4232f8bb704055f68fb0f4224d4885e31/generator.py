"""Legend recoloring by the minimum column of each color-1 component.

Inputs only: the unchanged canonical Racket program supplies all production
labels. Python recolorings below are explicitly named diagnostic rivals.
Ordinary shapes alternate with layouts that distinguish component rank from
canonical-compatible shortcuts; see notes.md for the finite lesson guarantee.
"""
from __future__ import annotations

from functools import partial
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c6a453e86480"
TASK_ID = GENERATOR_ID
RULE_HASH = "1971dd8a407b"
VERSION = "2.0.0"
SUMMARY = "Read 3 or 4 top-row legend colors; recolor equally many 1-components by minimum-column rank."
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0; the top row contains 3 or 4 distinct colors from 2..9",
    "row 1 is the single required blank separator; body colors are only 0 and 1",
    "the number of 4-connected color-1 components equals the legend length",
    "components have distinct minimum columns; legend columns need not align with component columns",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors plus 5..10", "valid": "5..10"},
    "grid_w": {"type": "int", "default": "canonical anchors plus 10..16", "valid": "10..16"},
    "n_blobs": {"type": "int", "default": "canonical anchors plus 3..4", "valid": "3..4"},
    "palette_kind": {"type": "str", "default": "rng", "valid": "|".join(PALETTE_KINDS)},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(PALETTE_KINDS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_kind": left, "texture": right}
    for left in PALETTE_KINDS for right in PALETTE_KINDS if left != right
]
_WARM = frozenset((2, 4, 6, 9))
_COOL = frozenset((3, 5, 7, 8))
_PROFILES = ((5, 13, 3), (5, 14, 4), (6, 13, 3))


def _palette_kind(colors):
    colors = set(colors)
    if colors <= _WARM:
        return "warm"
    if colors <= _COOL:
        return "cool"
    if {2, 3} <= colors:
        return "default"
    return "varied"


_PALETTES = {
    (count, kind): tuple(p for p in combinations(range(2, 10), count)
                         if _palette_kind(p) == kind)
    for count in (3, 4) for kind in PALETTE_KINDS
}


def _integer(ctx, name, low, high, default):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    # Record the actual scheduled default; never draw and then clip a count.
    return ctx.draw_choice(name, [default])


def _one_components_below_legend(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(1, height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            cells = []
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                    if (1 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in seen and grid[rr][cc] == 1):
                        seen.add((rr, cc))
                        pending.append((rr, cc))
            result.append(cells)
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["expected nonempty grid rows"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["ragged grid"]
    if len(grid) < 3 or len(grid) > 30 or width > 30:
        return ["expected height 3..30 and width 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9; booleans are not colors"]
    messages = []
    legend = [value for value in grid[0] if value]
    if len(legend) not in (3, 4):
        messages.append("expected 3 or 4 legend cells")
    if len(set(legend)) != len(legend) or 1 in legend:
        messages.append("legend colors must be distinct members of 2..9")
    if any(grid[1]):
        messages.append("row 1 must be the blank separator")
    if any(value not in (0, 1) for row in grid[1:] for value in row):
        messages.append("body may contain only background 0 and blob color 1")
    blobs = _one_components_below_legend(grid)
    if len(blobs) != len(legend):
        messages.append("component count must equal legend length")
    minima = [min(c for r, c in cells) for cells in blobs]
    if len(set(minima)) != len(minima):
        messages.append("component minimum columns must be distinct")
    return messages


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    kind = _palette_kind(value for value in grid[0] if value)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_blobs": len(_one_components_below_legend(grid)),
            "palette_kind": kind, "texture": kind}


def _recolor_with_key(grid, *, mode="minimum_column"):
    """Diagnostic predictions only; not a production label authority."""
    legend = [value for value in grid[0] if value]
    cells = _one_components_below_legend(grid)
    keys = {
        "minimum_column": lambda blob: min(c for r, c in blob),
        "row_major": min,
        "centroid": lambda blob: sum(c for r, c in blob) / len(blob),
        "rightmost": lambda blob: max(c for r, c in blob),
        "bbox_center": lambda blob: min(c for r, c in blob) + max(c for r, c in blob),
        "largest_first": lambda blob: -len(blob),
        "largest_bbox": lambda blob: -(max(r for r, c in blob)-min(r for r, c in blob)+1)
                                           * (max(c for r, c in blob)-min(c for r, c in blob)+1),
        "widest_first": lambda blob: min(c for r, c in blob)-max(c for r, c in blob),
        "first_pixel_column": lambda blob: min(blob)[1],
        "bottom_row_column": lambda blob: min(c for r, c in blob
                                                if r == max(rr for rr, cc in blob)),
        "numeric_legend": lambda blob: min(c for r, c in blob),
    }
    if mode == "numeric_legend":
        legend = sorted(legend)
    out = [list(row) for row in grid]
    for color, blob in zip(legend, sorted(cells, key=keys[mode])):
        for r, c in blob:
            out[r][c] = color
    return out


def _vertical_bands(grid):
    """Rival: recolor each 1-cell by its equal-width column band, no objects."""
    legend = [value for value in grid[0] if value]
    out = [list(row) for row in grid]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if value == 1:
                out[r][c] = legend[min(len(legend)-1, c*len(legend)//len(grid[0]))]
    return out


CANONICAL_SHORTCUTS = {
    name: partial(_recolor_with_key, mode=name)
    for name in ("row_major", "centroid", "rightmost", "bbox_center", "largest_first",
                 "largest_bbox", "widest_first", "first_pixel_column", "bottom_row_column")
}
CANONICAL_SHORTCUTS["vertical_bands"] = _vertical_bands
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS,
                   "numeric_legend": partial(_recolor_with_key, mode="numeric_legend")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rank_trap(grid, *, include_bottom=True):
    intended = _recolor_with_key(grid)
    return all(rival(grid) != intended for name, rival in SEMANTIC_RIVALS.items()
               if include_bottom or name != "bottom_row_column")


SEMANTIC_WITNESSES = {"rank_trap": _rank_trap}
WITNESS_RIVALS = {"rank_trap": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query):
    """Only named-rival ambiguity is assessed; universal induction is unknown."""
    return [f"{name} fits every demonstration and changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def _teaching_blobs(rng, height, width, count):
    # A lower left shape overlaps B's columns, but its top and bottom tips,
    # centroid, right edge and bbox center lie to B's right. Its leftmost
    # cells are in a middle row. C is larger than B. Height-5 overrides keep
    # the original two-row hook; they are lawful individual inputs but do
    # not carry the full production-lesson guarantee for bottom-row rank.
    length = rng.randint(5, min(7, width-4))
    left = rng.randint(0, width-length-4)
    gap = 3 if height >= 6 else 2
    top = rng.randint(2, height-gap-1)
    bottom = rng.randint(top+gap, height-1)
    if height >= 6:
        first = ({(bottom-1, c) for c in range(left, left+length)}
                 | {(bottom-2, left+length-1), (bottom, left+length-1)})
    else:
        first = ({(bottom, c) for c in range(left, left+length)}
                 | {(bottom-1, left+length-1)})
    blobs = [
        first,
        {(top, left+1), (top, left+2)},
        {(top, c) for c in range(left+length, left+length+rng.randint(3, 4))},
    ]
    if count == 4:
        start = rng.randint(left+length+2, width-2)
        blobs.append({(bottom, start), (bottom, start+1)})
    return blobs


def _ordinary_blobs(rng, height, width, count):
    for attempt in range(30):
        # grow_blob excludes neighbours of used cells. Row 0 alone reserves
        # row 1; reserving row 1 as occupied would incorrectly exclude row 2.
        used = {(0, c) for c in range(width)}
        blobs = []
        for index in range(count):
            cells = grow_blob(rng, height, width, used, rng.randint(2, 6), max_attempts=40)
            if cells is None:
                break
            blobs.append(cells)
            used |= cells
        minima = [min(c for r, c in cells) for cells in blobs]
        if len(blobs) == count and len(set(minima)) == count:
            return blobs
    # A bounded constructive fallback preserves every requested dimension and
    # count, and can only add teaching support rather than remove it.
    return _teaching_blobs(rng, height, width, count)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("palette_kind") is not None and overrides.get("texture") is not None:
        if overrides["palette_kind"] != overrides["texture"]:
            raise ValueError("palette_kind and texture are aliases and must agree")
    texture = overrides.get("texture")
    kind = ctx.draw_choice("palette_kind", [texture] if texture is not None else PALETTE_KINDS)
    if kind not in PALETTE_KINDS:
        raise ValueError("unknown palette_kind/texture")
    ctx.draw_choice("texture", [kind])
    rng = ctx.draw_rng("layout")
    if sample_index % 4 != 3:
        profile = _PROFILES[(sample_index//4 + sample_index%4) % len(_PROFILES)]
    else:
        cap = {"easy": 7, "medium": 9, "hard": 10, None: 9}[difficulty]
        profile = (rng.randint(5, cap), rng.randint(10, 16), rng.randint(3, 4))
    focused = sample_index % 2 == 0
    if focused:
        profile = (max(6, profile[0]), profile[1], profile[2])
    height = _integer(ctx, "grid_h", 5, 10, profile[0])
    width = _integer(ctx, "grid_w", 10, 16, profile[1])
    count = _integer(ctx, "n_blobs", 3, 4, profile[2])
    colors = list(rng.choice(_PALETTES[count, kind]))
    rng.shuffle(colors)
    if focused and colors == sorted(colors):
        colors[0], colors[1] = colors[1], colors[0]
    grid = full_grid(height, width, 0)
    for col, color in zip(sorted(rng.sample(range(width), count)), colors):
        grid[0][col] = color
    blobs = (_teaching_blobs(rng, height, width, count) if focused else
             _ordinary_blobs(rng, height, width, count))
    for blob in blobs:
        for r, c in blob:
            grid[r][c] = 1
    problems = self_check(grid)
    if problems:
        raise ValueError("constructed invalid rank puzzle: " + "; ".join(problems))
    if focused and not _rank_trap(grid, include_bottom=height >= 6):
        raise ValueError("constructed teaching layout failed its rival refutations")
    return grid
