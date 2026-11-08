"""Generator for ``Barbell Rectangle Fill`` (task 3e2b303f4cf7).

Two same-color solid 2x2 blocks aligned in one row or column define a bar.
The oracle fills the complete 2-cell-wide rectangle between every aligned
pair.  Different bars may cross; because the canonical program scans blocks
in row-major order, horizontal bars overwrite vertical bars at crossings.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e2b303f4cf7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "0f4a8a97ac1b"
SUMMARY = (
    "Aligned same-color solid 2x2 block pairs become filled 2-wide bars; "
    "off-axis or unpaired 2x2 blocks remain unchanged, and horizontal bars "
    "overwrite vertical bars where completed rectangles cross."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every nonzero input cell belongs to exactly one solid 2x2 block",
    "each active color occurs in exactly two blocks aligned in the same rows or columns",
    "every ordinary scene contains at least two active bars and a non-identity completion",
    "at most one unique-color decoy is present: none, one block, or two off-axis blocks",
    "every three consecutive ordinary samples include both orientations, a crossing, and an off-axis rival killer",
]

LAYOUTS = ("horizontal", "vertical", "mixed_separate", "mixed_crossing")
DECOY_KINDS = ("none", "single_block", "off_axis_pair")
SCHEDULE_PROFILES = (
    "crossing_off_axis",
    "canonical_horizontal",
    "vertical_single",
    "crossing_off_axis_alt",
)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware; canonical anchor is 10", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware; canonical anchor is 10", "valid": "10..18"},
    "bar_count": {"type": "int", "default": "scheduled 2 or 3", "valid": "2..3"},
    "layout": {"type": "str", "default": "four-profile lesson schedule", "valid": "|".join(LAYOUTS)},
    "decoy_kind": {"type": "str", "default": "four-profile lesson schedule", "valid": "|".join(DECOY_KINDS)},
}

# Every declared combination is supported, including all boundary values.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_COLORS = tuple(range(1, 10))
_CELL4 = ((0, 0), (0, 1), (1, 0), (1, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the curriculum profile; every length-three window is decisive."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (("grid_h", 9, 14), ("grid_w", 10, 18), ("bar_count", 2, 3)):
        if overrides.get(name) is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    for name, options in (("layout", LAYOUTS), ("decoy_kind", DECOY_KINDS)):
        if overrides.get(name) is not None and overrides[name] not in options:
            raise ValueError(f"{name} must be one of {options}")


def _draw_int_default(ctx, name: str, lo: int, hi: int, default: int, overrides: dict[str, Any]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_choice_default(ctx, name: str, options: tuple[str, ...], default: str, overrides: dict[str, Any]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _profile_defaults(profile: str, seed: int, sample_index: int) -> dict[str, Any]:
    parity = (seed + sample_index) & 1
    if profile == "crossing_off_axis":
        return {"bar_count": 2 + parity, "layout": "mixed_crossing", "decoy_kind": "off_axis_pair"}
    if profile == "canonical_horizontal":
        return {"grid_h": 10, "grid_w": 10, "bar_count": 2, "layout": "horizontal", "decoy_kind": "none"}
    if profile == "vertical_single":
        return {"bar_count": 2 + parity, "layout": "vertical", "decoy_kind": "single_block"}
    return {"bar_count": 3 - parity, "layout": "mixed_crossing", "decoy_kind": "off_axis_pair"}


def _block_cells(top: tuple[int, int]) -> set[tuple[int, int]]:
    r, c = top
    return {(r + dr, c + dc) for dr, dc in _CELL4}


def _reflect_top(top: tuple[int, int], h: int, w: int, *, ud: bool, lr: bool) -> tuple[int, int]:
    r, c = top
    if ud:
        r = h - 2 - r
    if lr:
        c = w - 2 - c
    return r, c


def _active_block_pairs(
    h: int,
    w: int,
    bar_count: int,
    layout: str,
    *,
    ud: bool,
    lr: bool,
) -> list[tuple[str, tuple[int, int], tuple[int, int]]]:
    """Return orientation plus two endpoint top-lefts for a guaranteed layout."""
    if layout == "horizontal":
        rows = (0, max(3, (h - 2) // 2), h - 2)
        left = 1 if w >= 12 else 0
        right = w - 3 if w >= 12 else w - 2
        pairs = [("h", (rows[i], left), (rows[i], right)) for i in range(bar_count)]
    elif layout == "vertical":
        cols = (0, max(3, (w - 2) // 2), w - 2)
        top = 1 if h >= 11 else 0
        bottom = h - 3 if h >= 11 else h - 2
        pairs = [("v", (top, cols[i]), (bottom, cols[i])) for i in range(bar_count)]
    elif layout == "mixed_separate":
        # A horizontal bar occupies the top; one or two vertical bars start
        # below it, so the completed rectangles remain disjoint.
        horizontal = ("h", (0, 0), (0, w - 2))
        vertical_cols = (1, w - 3)
        verticals = [("v", (3, c), (h - 2, c)) for c in vertical_cols]
        pairs = [horizontal, *verticals[: bar_count - 1]]
    else:
        # A full-height vertical corridor and one/two interior horizontal
        # corridors force the canonical horizontal-over-vertical collision.
        vc = max(2, min(w - 4, (w - 2) // 2))
        vertical = ("v", (0, vc), (h - 2, vc))
        rows = (max(2, h // 2 - 1), min(h - 4, h // 2 + 1))
        horizontals = [("h", (r, 0), (r, w - 2)) for r in rows]
        pairs = [vertical, *horizontals[: bar_count - 1]]

    reflected: list[tuple[str, tuple[int, int], tuple[int, int]]] = []
    for orientation, a, b in pairs:
        aa = _reflect_top(a, h, w, ud=ud, lr=lr)
        bb = _reflect_top(b, h, w, ud=ud, lr=lr)
        reflected.append((orientation, min(aa, bb), max(aa, bb)))
    return reflected


def _free_block_tops(h: int, w: int, occupied: set[tuple[int, int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if not (_block_cells((r, c)) & occupied)
    ]


def _place_decoy(
    grid: list[list[int]],
    occupied: set[tuple[int, int]],
    color: int,
    kind: str,
    rng,
) -> None:
    if kind == "none":
        return
    h, w = len(grid), len(grid[0])
    candidates = _free_block_tops(h, w, occupied)
    rng.shuffle(candidates)
    if kind == "single_block":
        if not candidates:
            raise RuntimeError("no free 2x2 slot for single-block decoy")
        chosen = [candidates[0]]
    else:
        chosen = []
        for first in candidates:
            first_cells = _block_cells(first)
            for second in candidates:
                if first[0] == second[0] or first[1] == second[1]:
                    continue
                if first_cells & _block_cells(second):
                    continue
                chosen = [first, second]
                break
            if chosen:
                break
        if not chosen:
            raise RuntimeError("no free off-axis pair of 2x2 decoy slots")
    for top in chosen:
        cells = _block_cells(top)
        for r, c in cells:
            grid[r][c] = color
        occupied.update(cells)


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(profile, seed, sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if "grid_h" in defaults and overrides.get("grid_h") is None:
        h = _draw_int_default(ctx, "grid_h", 9, 14, defaults["grid_h"], overrides)
    else:
        h = ctx.draw_int_diff("grid_h", 9, 14)
    if "grid_w" in defaults and overrides.get("grid_w") is None:
        w = _draw_int_default(ctx, "grid_w", 10, 18, defaults["grid_w"], overrides)
    else:
        w = ctx.draw_int_diff("grid_w", 10, 18)
    bar_count = _draw_int_default(ctx, "bar_count", 2, 3, defaults["bar_count"], overrides)
    layout = _draw_choice_default(ctx, "layout", LAYOUTS, defaults["layout"], overrides)
    decoy_kind = _draw_choice_default(ctx, "decoy_kind", DECOY_KINDS, defaults["decoy_kind"], overrides)

    layout_rng = ctx.draw_rng("layout_geometry")
    ud = bool(layout_rng.randrange(2))
    lr = bool(layout_rng.randrange(2))
    pairs = _active_block_pairs(h, w, bar_count, layout, ud=ud, lr=lr)

    color_count = bar_count + (decoy_kind != "none")
    colors = list(ctx.draw_distinct_colors("colors", n=color_count, exclude={0}))
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()
    for color, (_, first, second) in zip(colors, pairs):
        for top in (first, second):
            cells = _block_cells(top)
            if cells & occupied:
                raise RuntimeError(f"internal layout overlap at {top}")
            for r, c in cells:
                grid[r][c] = color
            occupied.update(cells)

    if decoy_kind != "none":
        _place_decoy(grid, occupied, colors[-1], decoy_kind, ctx.draw_rng("decoy_geometry"))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "bar_count": bar_count,
        "layout": layout,
        "decoy_kind": decoy_kind,
    }
    if observed != expected:
        raise RuntimeError(f"internal observable mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and exact oracle mirror
# ---------------------------------------------------------------------------


def _rectangular_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list"
    if not all(isinstance(row, list) and row for row in grid):
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(isinstance(value, bool) or not isinstance(value, int) for row in grid for value in row):
        return "grid cells must be integers"
    if any(value < 0 or value > 9 for row in grid for value in row):
        return "grid colors must be in 0..9"
    return None


def _solid_blocks(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    h, w = len(grid), len(grid[0])
    blocks: list[tuple[int, int, int]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            value = grid[r][c]
            if value != 0 and all(grid[r + dr][c + dc] == value for dr, dc in _CELL4):
                blocks.append((value, r, c))
    return blocks


def _bar_rect(orientation: str, first: tuple[int, int], second: tuple[int, int]) -> tuple[int, int, int, int]:
    r1, c1 = first
    r2, c2 = second
    if orientation == "h":
        return r1, r1 + 1, min(c1, c2), max(c1, c2) + 1
    return min(r1, r2), max(r1, r2) + 1, c1, c1 + 1


def _rects_intersect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar1, ar2, ac1, ac2 = a
    br1, br2, bc1, bc2 = b
    return max(ar1, br1) <= min(ar2, br2) and max(ac1, bc1) <= min(ac2, bc2)


def _analysis(grid: list[list[int]]) -> dict[str, Any]:
    blocks = _solid_blocks(grid)
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    coverage: dict[tuple[int, int], int] = defaultdict(int)
    for color, r, c in blocks:
        by_color[color].append((r, c))
        for cell in _block_cells((r, c)):
            coverage[cell] += 1

    active: list[dict[str, Any]] = []
    single_colors: list[int] = []
    off_axis_colors: list[int] = []
    invalid_colors: list[int] = []
    for color, tops in sorted(by_color.items()):
        tops = sorted(tops)
        if len(tops) == 1:
            single_colors.append(color)
        elif len(tops) == 2 and tops[0][0] == tops[1][0] and abs(tops[0][1] - tops[1][1]) >= 3:
            active.append({"color": color, "orientation": "h", "tops": tuple(tops)})
        elif len(tops) == 2 and tops[0][1] == tops[1][1] and abs(tops[0][0] - tops[1][0]) >= 3:
            active.append({"color": color, "orientation": "v", "tops": tuple(tops)})
        elif len(tops) == 2 and tops[0][0] != tops[1][0] and tops[0][1] != tops[1][1]:
            off_axis_colors.append(color)
        else:
            invalid_colors.append(color)

    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0}
    block_union = set(coverage)
    crossing_pairs = 0
    for index, first in enumerate(active):
        if first["orientation"] != "h":
            continue
        rect_first = _bar_rect("h", *first["tops"])
        for second in active[index + 1 :]:
            if second["orientation"] != "v":
                continue
            if _rects_intersect(rect_first, _bar_rect("v", *second["tops"])):
                crossing_pairs += 1
    for index, first in enumerate(active):
        if first["orientation"] != "v":
            continue
        rect_first = _bar_rect("v", *first["tops"])
        for second in active[index + 1 :]:
            if second["orientation"] != "h":
                continue
            if _rects_intersect(rect_first, _bar_rect("h", *second["tops"])):
                crossing_pairs += 1

    return {
        "blocks": blocks,
        "by_color": dict(by_color),
        "coverage": dict(coverage),
        "nonzero": nonzero,
        "block_union": block_union,
        "active": active,
        "single_colors": single_colors,
        "off_axis_colors": off_axis_colors,
        "invalid_colors": invalid_colors,
        "crossing_pairs": crossing_pairs,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/rule-hiding scenes while accepting every canonical input."""
    del difficulty, meta
    error = _rectangular_error(grid)
    if error:
        return [error]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    analysis = _analysis(grid)
    if not analysis["nonzero"]:
        errors.append("all-background grid has no barbell lesson")
    if analysis["nonzero"] != analysis["block_union"]:
        errors.append("every nonzero cell must belong to a solid 2x2 block")
    if any(count != 1 for count in analysis["coverage"].values()):
        errors.append("2x2 blocks may not overlap or merge into larger solid rectangles")
    if analysis["invalid_colors"]:
        errors.append(f"invalid block multiplicity/alignment for colors {analysis['invalid_colors']}")
    if len(analysis["active"]) < 2:
        errors.append("need at least two aligned block pairs")
    if len(analysis["single_colors"]) + len(analysis["off_axis_colors"]) > 1:
        errors.append("at most one unique-color decoy is allowed")
    if len(analysis["single_colors"]) > 1 or len(analysis["off_axis_colors"]) > 1:
        errors.append("decoy grammar allows one single block or one off-axis pair")
    if analysis["single_colors"] and analysis["off_axis_colors"]:
        errors.append("single-block and off-axis decoys may not be combined")
    if analysis["active"] and rule_mirror(grid) == grid:
        errors.append("aligned pairs must produce a non-identity completion")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 22 and 10 <= w <= 24):
        return [f"grid dimensions {h}x{w} are outside the supported task envelope"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from the returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    analysis = _analysis(grid)
    orientations = [bar["orientation"] for bar in analysis["active"]]
    if all(value == "h" for value in orientations):
        layout = "horizontal"
    elif all(value == "v" for value in orientations):
        layout = "vertical"
    elif analysis["crossing_pairs"]:
        layout = "mixed_crossing"
    else:
        layout = "mixed_separate"
    if analysis["single_colors"]:
        decoy_kind = "single_block"
    elif analysis["off_axis_colors"]:
        decoy_kind = "off_axis_pair"
    else:
        decoy_kind = "none"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "bar_count": len(analysis["active"]),
        "layout": layout,
        "decoy_kind": decoy_kind,
    }


def _apply_pairs(
    grid: list[list[int]],
    *,
    allow_horizontal: bool = True,
    allow_vertical: bool = True,
    allow_off_axis_bbox: bool = False,
    orientation_order: tuple[str, ...] | None = None,
) -> list[list[int]]:
    blocks = _solid_blocks(grid)
    pairs: list[tuple[int, str, tuple[int, int], tuple[int, int]]] = []
    for i, (color1, r1, c1) in enumerate(blocks):
        for color2, r2, c2 in blocks[i + 1 :]:
            if color1 != color2:
                continue
            orientation = "h" if r1 == r2 else ("v" if c1 == c2 else "off")
            pairs.append((color1, orientation, (r1, c1), (r2, c2)))
    if orientation_order is not None:
        rank = {orientation: index for index, orientation in enumerate(orientation_order)}
        pairs.sort(key=lambda item: rank.get(item[1], len(rank)))

    out = deepcopy(grid)
    for color, orientation, first, second in pairs:
        r1, c1 = first
        r2, c2 = second
        if orientation == "h" and allow_horizontal:
            for r in (r1, r1 + 1):
                for c in range(min(c1, c2), max(c1, c2) + 2):
                    out[r][c] = color
        elif orientation == "v" and allow_vertical:
            for c in (c1, c1 + 1):
                for r in range(min(r1, r2), max(r1, r2) + 2):
                    out[r][c] = color
        elif orientation == "off" and allow_off_axis_bbox:
            for r in range(min(r1, r2), max(r1, r2) + 2):
                for c in range(min(c1, c2), max(c1, c2) + 2):
                    out[r][c] = color
    return out


def rule_mirror(grid):
    """Exact pure Python mirror of the selected canonical Racket program."""
    return _apply_pairs(grid)


def _rival_horizontal_only(grid):
    return _apply_pairs(grid, allow_vertical=False)


def _rival_vertical_only(grid):
    return _apply_pairs(grid, allow_horizontal=False)


def _rival_fill_any_same_color_bbox(grid):
    return _apply_pairs(grid, allow_off_axis_bbox=True)


def _rival_vertical_over_horizontal(grid):
    # The canonical loop fills row-major pairs, which makes crossing horizontal
    # corridors last.  This rival applies all horizontal pairs first instead.
    return _apply_pairs(grid, orientation_order=("h", "v", "off"))


def _has_horizontal(grid) -> bool:
    return any(bar["orientation"] == "h" for bar in _analysis(grid)["active"])


def _has_vertical(grid) -> bool:
    return any(bar["orientation"] == "v" for bar in _analysis(grid)["active"])


def _has_crossing(grid) -> bool:
    return _analysis(grid)["crossing_pairs"] > 0


def _has_off_axis_decoy(grid) -> bool:
    return bool(_analysis(grid)["off_axis_colors"])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "horizontal_pairs_only": _rival_horizontal_only,
    "vertical_pairs_only": _rival_vertical_only,
    "fill_any_same_color_bbox": _rival_fill_any_same_color_bbox,
    "vertical_over_horizontal_at_crossings": _rival_vertical_over_horizontal,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"fill_any_same_color_bbox": _rival_fill_any_same_color_bbox}
SEMANTIC_WITNESSES = {
    "horizontal_completion": _has_horizontal,
    "vertical_completion": _has_vertical,
    "crossing_horizontal_priority": _has_crossing,
    "off_axis_pair_unchanged": _has_off_axis_decoy,
}
WITNESS_RIVALS = {
    "horizontal_completion": ["vertical_pairs_only"],
    "vertical_completion": ["horizontal_pairs_only"],
    "crossing_horizontal_priority": ["vertical_over_horizontal_at_crossings"],
    "off_axis_pair_unchanged": ["fill_any_same_color_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo window to eliminate all named competitors."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is unlawful: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the pinned rule mirror")
        else:
            valid_demos.append(pair)
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is unlawful: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the pinned rule mirror")

    required: dict[str, Callable[[list[list[int]]], bool]] = {
        "horizontal completion": _has_horizontal,
        "vertical completion": _has_vertical,
        "crossing priority": _has_crossing,
        "off-axis non-completion": _has_off_axis_decoy,
    }
    for label, predicate in required.items():
        if not any(predicate(pair["input"]) for pair in valid_demos):
            reasons.append(f"demonstrations lack {label}")
    for name, rival in LESSON_COMPETITORS.items():
        if not any(rival(pair["input"]) != pair["output"] for pair in valid_demos):
            reasons.append(f"named rival remains viable on demonstrations: {name}")
    return reasons
