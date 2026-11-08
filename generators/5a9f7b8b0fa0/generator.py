"""Generator for H139 / task 5a9f7b8b0fa0 — panel-area relation matrix.

Full-height color-8 columns split the input into vertical panels.  The score of
one panel is the number of cells whose color is neither 0 nor 8.  The output is
the ordered square comparison matrix: 1 when two panel scores are equal, 2
when the row panel is larger, and 3 when it is smaller.

Ordinary lessons are scheduled in four residues.  Every four consecutive
examples contain strict ranks, mixed ties, two canonical-scale cases,
and a multicolor case, so panel width, color count, and diagonal-only equality
are all falsified as shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a9f7b8b0fa0"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"  # exact overrides, canonical anchoring, linked semantic schedule
RULE_HASH = "9c7ed54a3ebf"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A 0-background grid is split into 3-4 vertical panels by single full-height "
    "color-8 columns. Count every non-{0,8} cell in each panel, then emit the "
    "ordered N×N comparison matrix: 1 for equal area, 2 when the row panel is "
    "larger, and 3 when it is smaller. Panel colors, shapes, and placements are "
    "distractors; ordinary four-example windows show strict inequalities, an "
    "off-diagonal tie, canonical scale, and a multicolor panel case."
)

INVARIANTS = [
    "single full-height color-8 columns separate 3-4 nonempty vertical panels",
    "color 8 appears only in separator columns",
    "each panel contains at least one non-{0,8} cell",
    "the output is the ordered panel-area comparison matrix using 1/2/3",
    "ordinary four-example windows expose both inequality directions and off-diagonal equalities",
]

RELATION_PATTERNS = ("strict", "mixed_ties", "all_equal")
COLOR_MODES = ("monochrome", "multicolor")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-residue schedule with canonical 5/6-row anchors",
        "valid": "5..8",
    },
    "panel_count": {
        "type": "int",
        "default": "3 canonical; 4 on generalized residue",
        "valid": "3..4",
    },
    "panel_width": {
        "type": "int",
        "default": "uniform 5/6 canonical anchors, 4..6 generalized",
        "valid": "4..6",
    },
    "relation_pattern": {
        "type": "enum",
        "default": "residue-keyed strict|mixed_ties|all_equal",
        "valid": RELATION_PATTERNS,
    },
    "color_mode": {
        "type": "enum",
        "default": "residue-keyed monochrome|multicolor",
        "valid": COLOR_MODES,
    },
}

_CONTENT_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Exact canonical (height, width, palette-size) profiles used by the shared
# canonical-profile gate.  The normal schedule deliberately hits the first and
# fourth profiles in every difficulty band.
_CANONICAL_PROFILES = {
    (5, 17, 4),
    (6, 18, 5),
    (6, 19, 5),
    (6, 20, 5),
}

# Connected masks.  D4 transforms and translations provide surface variety;
# the rule reads only area, so equal-area examples intentionally use different
# masks.
_SHAPES_BY_AREA: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    current = _normalize(cells)
    if code >= 4:
        width = max(c for _, c in current) + 1
        current = _normalize((r, width - 1 - c) for r, c in current)
    for _ in range(code % 4):
        height = max(r for r, _ in current) + 1
        current = _normalize((c, height - 1 - r) for r, c in current)
    return current


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _grow_shape(area: int, max_h: int, max_w: int, rng) -> tuple[tuple[int, int], ...]:
    """Connected fallback shape, preserving insertion order for multicolor split."""
    for _ in range(128):
        cells = [(0, 0)]
        used = {(0, 0)}
        while len(cells) < area:
            frontier = []
            for r, c in cells:
                for dr, dc in _CARDINAL:
                    nxt = (r + dr, c + dc)
                    if nxt not in used:
                        frontier.append(nxt)
            if not frontier:
                break
            nxt = rng.choice(frontier)
            used.add(nxt)
            cells.append(nxt)
        norm = _normalize(cells)
        h, w = _shape_dims(norm)
        if len(norm) == area and h <= max_h and w <= max_w:
            return norm
    raise ValueError(f"cannot build connected area-{area} mask in {max_h}x{max_w}")


def _choose_shape(
    area: int,
    max_h: int,
    max_w: int,
    rng,
    *,
    avoid: set[tuple[tuple[int, int], ...]] | None = None,
) -> tuple[tuple[int, int], ...]:
    avoid = avoid or set()
    candidates = []
    for base in _SHAPES_BY_AREA.get(area, ()):  # exact small masks first
        for code in range(8):
            shape = _transform(base, code)
            h, w = _shape_dims(shape)
            if h <= max_h and w <= max_w and shape not in avoid:
                candidates.append(shape)
    if candidates:
        return rng.choice(candidates)
    shape = _grow_shape(area, max_h, max_w, rng)
    if shape in avoid:
        # Translation is irrelevant to normalized shape, but a second keyed
        # attempt usually produces a different growth path.
        for _ in range(32):
            candidate = _grow_shape(area, max_h, max_w, rng)
            if candidate not in avoid:
                return candidate
    return shape


def _draw_int_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _draw_choice_axis(ctx, overrides, name: str, default: str, options) -> str:
    if name in overrides and overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-residue curriculum schedule; seed/difficulty do not change coverage."""
    del seed, difficulty
    return int(sample_index) % 4


SCHEDULE_PROFILES = (0, 1, 2, 3)


def _scheduled_defaults(sample_index: int, difficulty: str | None) -> dict[str, Any]:
    residue = int(sample_index) % 4
    if residue == 0:
        return {
            "grid_h": 5,
            "panel_count": 3,
            "panel_width": 5,
            "relation_pattern": "mixed_ties",
            "color_mode": "monochrome",
            "canonical_profile": "test_like",
        }
    if residue == 1:
        return {
            "grid_h": 6,
            "panel_count": 3,
            "panel_width": 6,
            "relation_pattern": "strict",
            "color_mode": "monochrome",
            "canonical_profile": "train_like",
        }
    if residue == 2:
        return {
            "grid_h": 6,
            "panel_count": 4,
            "panel_width": 5,
            "relation_pattern": "mixed_ties",
            "color_mode": "multicolor",
            "canonical_profile": None,
        }
    # Generalized residue broadens panel count and scale while preserving the
    # canonical shrink relation (N < input height and N < input width).
    return {
        "grid_h": {"easy": 6, "medium": 7, "hard": 8}.get(difficulty, 7),
        "panel_count": 4,
        "panel_width": {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5),
        "relation_pattern": "strict",
        "color_mode": "monochrome",
        "canonical_profile": None,
    }


def _rank_patterns(n: int, *, tied: bool) -> tuple[tuple[int, ...], ...]:
    """All ordered rank patterns in canonical label order.

    Rank labels are contiguous from zero.  For n=4 this gives 24 strict
    permutations and 50 mixed-tie patterns, enough for a genuinely varied
    finite output alphabet without inventing rule-irrelevant output noise.
    """
    from itertools import product

    patterns = []
    for values in product(range(n), repeat=n):
        labels = sorted(set(values))
        if labels != list(range(len(labels))):
            continue
        is_strict = len(labels) == n
        is_all_equal = len(labels) == 1
        if tied:
            if is_strict or is_all_equal:
                continue
        elif not is_strict:
            continue
        patterns.append(values)
    return tuple(patterns)


def _areas_for(pattern: str, n: int, rng, *, selector: int) -> list[int]:
    del rng  # selector gives stable, audit-friendly codomain coverage
    if pattern == "strict":
        ranks = _rank_patterns(n, tied=False)
        chosen = ranks[selector % len(ranks)]
        return [3 + rank for rank in chosen]
    if pattern == "mixed_ties":
        ranks = _rank_patterns(n, tied=True)
        chosen = ranks[selector % len(ranks)]
        return [3 + rank for rank in chosen]
    if pattern == "all_equal":
        return [4] * n
    raise ValueError(f"unknown relation pattern {pattern!r}")


def _panel_colors(
    n: int,
    color_mode: str,
    rng,
    *,
    canonical_profile: str | None,
) -> list[tuple[int, int | None]]:
    if canonical_profile == "test_like":
        primaries = [2, 3, 2]
    elif canonical_profile == "train_like":
        primaries = [2, 4, 5]
    else:
        primaries = list(_CONTENT_COLORS)
        rng.shuffle(primaries)
        primaries = [primaries[i % len(primaries)] for i in range(n)]
        # Reuse one color across unequal panels on some draws so color identity
        # cannot act as an area label.
        if n >= 3 and rng.randrange(2) == 0:
            primaries[-1] = primaries[0]
    if color_mode == "monochrome":
        return [(color, None) for color in primaries]
    secondaries = [c for c in _CONTENT_COLORS if c not in primaries]
    if not secondaries:
        secondaries = list(_CONTENT_COLORS)
    rng.shuffle(secondaries)
    return [
        (primary, secondaries[index % len(secondaries)])
        for index, primary in enumerate(primaries)
    ]


def _canonical_window(height: int, width: int) -> tuple[int, int, int, int]:
    """Interior used by canonical-scale residues, matching official margins."""
    if height == 5:
        return 1, 3, 1, min(width - 2, 3)
    return 1, 3, 1, min(width - 2, 4)


def _place_shape(
    grid: list[list[int]],
    panel_left: int,
    panel_width: int,
    shape: tuple[tuple[int, int], ...],
    colors: tuple[int, int | None],
    rng,
    *,
    canonical_profile: str | None,
) -> None:
    height = len(grid)
    shape_h, shape_w = _shape_dims(shape)
    if canonical_profile:
        r_lo, r_hi, c_lo, c_hi = _canonical_window(height, panel_width)
        room_h = r_hi - r_lo + 1
        room_w = c_hi - c_lo + 1
        if shape_h > room_h or shape_w > room_w:
            raise ValueError("canonical-profile mask does not fit canonical interior")
        row0 = rng.randint(r_lo, r_hi - shape_h + 1)
        col0 = panel_left + rng.randint(c_lo, c_hi - shape_w + 1)
    else:
        row0 = rng.randint(0, height - shape_h)
        col0 = panel_left + rng.randint(0, panel_width - shape_w)

    primary, secondary = colors
    # The mask is connected.  For multicolor scenes, recolor one terminal cell;
    # the primary prefix remains connected and both colors are observable.
    accent = shape[-1] if secondary is not None else None
    for rr, cc in shape:
        grid[row0 + rr][col0 + cc] = secondary if (rr, cc) == accent else primary


def _split_panels(grid: list[list[int]]) -> tuple[list[tuple[int, int]], list[str]]:
    height, width = len(grid), len(grid[0])
    separators = [
        col for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    errors: list[str] = []
    if separators and (separators[0] == 0 or separators[-1] == width - 1):
        errors.append("separator columns may not lie on the outer grid edge")
    if any(right == left + 1 for left, right in zip(separators, separators[1:])):
        errors.append("adjacent separator columns create an empty panel")
    separator_set = set(separators)
    stray = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8 and col not in separator_set
    ]
    if stray:
        errors.append(f"color 8 appears outside full-height separators at {stray[:3]}")
    cuts = [-1] + separators + [width]
    panels = [(left + 1, right) for left, right in zip(cuts, cuts[1:]) if right > left + 1]
    if len(panels) != len(separators) + 1:
        errors.append("separator grammar does not form nonempty panels")
    return panels, errors


def _components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color {value!r} at ({row_index},{col_index})")
    if errors:
        return {"errors": errors, "grid_h": len(grid), "grid_w": width}

    panels, panel_errors = _split_panels(grid)
    errors.extend(panel_errors)
    panel_facts = []
    for index, (left, right) in enumerate(panels):
        cells = {
            (row, col - left)
            for row in range(len(grid))
            for col in range(left, right)
            if grid[row][col] not in (0, 8)
        }
        colors = {
            grid[row][col]
            for row in range(len(grid))
            for col in range(left, right)
            if grid[row][col] not in (0, 8)
        }
        if not cells:
            errors.append(f"panel {index} has no non-{{0,8}} content")
        panel_facts.append(
            {
                "index": index,
                "left": left,
                "right": right,
                "width": right - left,
                "area": len(cells),
                "colors": tuple(sorted(colors)),
                "component_count": _components(cells) if cells else 0,
                "normalized_cells": _normalize(cells) if cells else (),
            }
        )
    areas = [panel["area"] for panel in panel_facts]
    relation_pattern = None
    if areas:
        counts = Counter(areas)
        if len(counts) == 1:
            relation_pattern = "all_equal"
        elif len(counts) == len(areas):
            relation_pattern = "strict"
        else:
            relation_pattern = "mixed_ties"
    color_mode = None
    if panel_facts:
        color_mode = (
            "monochrome"
            if all(len(panel["colors"]) == 1 for panel in panel_facts)
            else "multicolor"
        )
    widths = {panel["width"] for panel in panel_facts}
    return {
        "errors": errors,
        "grid_h": len(grid),
        "grid_w": width,
        "palette": tuple(sorted({value for row in grid for value in row})),
        "panels": panel_facts,
        "areas": areas,
        "panel_count": len(panel_facts),
        "panel_width": next(iter(widths)) if len(widths) == 1 else None,
        "relation_pattern": relation_pattern,
        "color_mode": color_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the panel grammar without rejecting lawful all-equal cases."""
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    height, width = analysis["grid_h"], analysis["grid_w"]
    if not (5 <= height <= 8):
        errors.append(f"grid height must be 5..8, got {height}")
    if not (11 <= width <= 30):
        errors.append(f"grid width must be 11..30, got {width}")
    if not (3 <= analysis["panel_count"] <= 4):
        errors.append(f"expected 3..4 panels, found {analysis['panel_count']}")
    if any(not (3 <= panel["width"] <= 8) for panel in analysis["panels"]):
        errors.append("panel widths must lie in 3..8")
    if analysis["relation_pattern"] not in RELATION_PATTERNS:
        errors.append(
            "panel areas must form strict, mixed-tie, or all-equal relation classes"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "panel_count": analysis["panel_count"],
        "panel_width": analysis["panel_width"],
        "relation_pattern": analysis["relation_pattern"],
        "color_mode": analysis["color_mode"],
    }


def _relation_from_scores(scores: list[int]) -> list[list[int]]:
    return [
        [1 if left == right else 2 if left > right else 3 for right in scores]
        for left in scores
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests; the canonical Racket remains authority."""
    source = deepcopy(grid)
    analysis = _analyze(source)
    if analysis.get("errors"):
        raise ValueError("invalid task input: " + "; ".join(analysis["errors"]))
    return _relation_from_scores(analysis["areas"])


def _rival_panel_width(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task input")
    return _relation_from_scores([panel["width"] for panel in analysis["panels"]])


def _rival_distinct_color_count(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task input")
    return _relation_from_scores([len(panel["colors"]) for panel in analysis["panels"]])


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": analysis["errors"]}
    output = _relation_from_scores(analysis["areas"])
    off_diagonal = [
        output[row][col]
        for row in range(len(output))
        for col in range(len(output))
        if row != col
    ]
    return {
        "areas": tuple(analysis["areas"]),
        "relation_pattern": analysis["relation_pattern"],
        "color_mode": analysis["color_mode"],
        "off_diagonal_symbols": tuple(sorted(set(off_diagonal))),
        "strict_canonical_like": strict_canonical_like(grid) == [],
        "panel_width_rival_disagrees": output != _rival_panel_width(grid),
        "color_count_rival_disagrees": output != _rival_distinct_color_count(grid),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis.get("errors", []))
    if reasons:
        return reasons
    profile = (
        analysis["grid_h"],
        analysis["grid_w"],
        len(analysis["palette"]),
    )
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical H/W/palette support")
    if analysis["panel_count"] != 3:
        reasons.append("canonical manifold has exactly three panels")
    if not all(len(panel["colors"]) == 1 for panel in analysis["panels"]):
        reasons.append("canonical panels are monochrome")
    # Every official input has blank outer rows outside the full-height dividers.
    separator_cols = {
        col for col in range(analysis["grid_w"])
        if all(grid[row][col] == 8 for row in range(analysis["grid_h"]))
    }
    for row in (0, analysis["grid_h"] - 1):
        if any(grid[row][col] != (8 if col in separator_cols else 0)
               for col in range(analysis["grid_w"])):
            reasons.append("canonical outer rows are blank except for separators")
            break
    return reasons


def _has_unequal_area_branch(grid) -> bool:
    output = rule_mirror(grid)
    flat = {value for row in output for value in row}
    return 2 in flat and 3 in flat


def _has_off_diagonal_equality(grid) -> bool:
    output = rule_mirror(grid)
    return any(
        row != col and output[row][col] == 1
        for row in range(len(output))
        for col in range(len(output))
    )


def _refutes_panel_width(grid) -> bool:
    return rule_mirror(grid) != _rival_panel_width(grid)


def _refutes_color_count(grid) -> bool:
    return rule_mirror(grid) != _rival_distinct_color_count(grid)


def _equal_area_different_shape(grid) -> bool:
    analysis = _analyze(grid)
    panels = analysis.get("panels", [])
    for left in range(len(panels)):
        for right in range(left + 1, len(panels)):
            if (
                panels[left]["area"] == panels[right]["area"]
                and panels[left]["normalized_cells"] != panels[right]["normalized_cells"]
            ):
                return True
    return False


SEMANTIC_WITNESSES = {
    # Gate-facing witnesses are deliberately rival-linked.  Presence-only
    # curriculum properties stay enforced by lesson_identifiable instead of
    # masquerading as counterexamples to an unnamed hypothesis.
    "refutes_equal_width_shortcut": _refutes_panel_width,
    "refutes_distinct_color_count_shortcut": _refutes_color_count,
}

SEMANTIC_RIVALS = {
    "panel_width": _rival_panel_width,
    "distinct_color_count": _rival_distinct_color_count,
}
WITNESS_RIVALS = {
    "refutes_equal_width_shortcut": ["panel_width"],
    "refutes_distinct_color_count_shortcut": ["distinct_color_count"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require each four-demo window to kill the two plausible count rivals."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return reasons
    outputs = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} invalid: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output disagrees with area rule")
            continue
        valid_demos.append(pair["input"])
        outputs.append(expected)
    if len(valid_demos) != len(demos):
        return reasons

    symbols = {value for output in outputs for row in output for value in row}
    if not {1, 2, 3} <= symbols:
        reasons.append("demonstrations do not expose equal, greater, and less symbols")
    if not any(_has_off_diagonal_equality(grid) for grid in valid_demos):
        reasons.append("demonstrations lack an off-diagonal equality witness")
    if not any(_refutes_panel_width(grid) for grid in valid_demos):
        reasons.append("equal-width panel rival survives every demonstration")
    if not any(_refutes_color_count(grid) for grid in valid_demos):
        reasons.append("distinct-color-count rival survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not a pair with an input")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query invalid: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with area rule")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    defaults = _scheduled_defaults(int(sample_index), difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 5, 8)
    panel_count = _draw_int_axis(
        ctx, overrides, "panel_count", defaults["panel_count"], 3, 4
    )
    panel_width = _draw_int_axis(
        ctx, overrides, "panel_width", defaults["panel_width"], 4, 6
    )
    relation_pattern = _draw_choice_axis(
        ctx,
        overrides,
        "relation_pattern",
        defaults["relation_pattern"],
        RELATION_PATTERNS,
    )
    color_mode = _draw_choice_axis(
        ctx, overrides, "color_mode", defaults["color_mode"], COLOR_MODES
    )

    width = panel_count * panel_width + panel_count - 1
    if width > 30:  # impossible for declared domains; defensive contract check
        raise ValueError(f"requested axes produce width {width} > 30")

    canonical_profile = defaults["canonical_profile"] if not overrides else None
    area_rng = ctx.draw_rng("areas")
    layout_rng = ctx.draw_rng("layout")
    areas = _areas_for(
        relation_pattern,
        panel_count,
        area_rng,
        selector=int(seed) + int(sample_index),
    )
    if max(areas) > height * panel_width:
        raise ValueError("requested axes cannot fit the scheduled panel areas")
    colors = _panel_colors(
        panel_count,
        color_mode,
        layout_rng,
        canonical_profile=canonical_profile,
    )

    grid = full_grid(height, width, 0)
    panel_left = 0
    shapes_by_area: dict[int, set[tuple[tuple[int, int], ...]]] = {}
    for index, (area, panel_colors) in enumerate(zip(areas, colors)):
        if index:
            for row in range(height):
                grid[row][panel_left] = 8
            panel_left += 1
        # Canonical residues preserve the official blank outer rows; other
        # residues use the full panel and broaden placement support.
        if canonical_profile:
            r_lo, r_hi, c_lo, c_hi = _canonical_window(height, panel_width)
            max_h, max_w = r_hi - r_lo + 1, c_hi - c_lo + 1
        else:
            max_h, max_w = height, panel_width
        avoid = shapes_by_area.setdefault(area, set())
        shape = _choose_shape(area, max_h, max_w, layout_rng, avoid=avoid)
        avoid.add(shape)
        _place_shape(
            grid,
            panel_left,
            panel_width,
            shape,
            panel_colors,
            layout_rng,
            canonical_profile=canonical_profile,
        )
        panel_left += panel_width

    errors = self_check(grid)
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "panel_count": panel_count,
        "panel_width": panel_width,
        "relation_pattern": relation_pattern,
        "color_mode": color_mode,
    }
    if observed != expected:
        raise ValueError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid
