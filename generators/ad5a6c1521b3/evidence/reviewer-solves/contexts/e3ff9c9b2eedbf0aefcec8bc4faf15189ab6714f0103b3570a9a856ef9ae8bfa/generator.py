"""Constructive input sampler for ARC task ad5a6c1521b3 (alias fe45cba4).

For every non-background color that forms two or more 4-connected components,
select the largest component; equal sizes are broken by the lower/right
component's top-left corner (largest ``r0 + c0``).  Erase all cells of that
color, then paint the selected component's entire bounding rectangle plus one
column immediately to its left.  Colors with only one component are unchanged.

The generator deliberately covers branches hidden by the three canonical
inputs: two simultaneously split colors, three components, an upper/left
unique winner, and irregular winners whose holes make rectangle filling
observable.  Outputs are never generated here; the unchanged Racket program is
label authority.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad5a6c1521b3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8e796791a1a2"

SUMMARY = (
    "Use the unique modal background. For each other color independently, "
    "leave a single connected component unchanged; when the color is split, "
    "keep its largest component (equal sizes choose the lower/right top-left "
    "corner), erase its other components, and fill the winner's bounding "
    "rectangle together with one column on the left."
)

INVARIANTS = [
    "all cells are ARC colors and the background is a unique mode",
    "exactly three colors are present in generated scenes",
    "at least one foreground color has two or more 4-connected components",
    "each selected winner starts right of column zero and has a visible bbox hole",
    "expanded winner rectangles contain no foreign foreground color",
    "8x8 and 16x16 canonical shape/palette profiles are both scheduled",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4

SCENE_PROFILES = (
    "tie_both_8",
    "single_unique_8",
    "tie_both_16_three",
    "single_unique_16",
)
SCHEDULE_PROFILES = SCENE_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile curriculum",
        "valid": "tie_both_8|single_unique_8|tie_both_16_three|single_unique_16",
        "doc": (
            "Recoverable canvas/component profile. Every value is legal in "
            "every difficulty band."
        ),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Each profile stores (height, width, role-A cells, role-B cells).  Cells for a
# role may form several separated components.  Component-size signatures are
# unique, so scene_profile is exactly recoverable from pixels without metadata.
_PROFILE_CELLS: dict[
    str,
    tuple[int, int, tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]],
] = {
    # A has a 4-vs-4 tie won by the lower/right component.  B is split 5-vs-2.
    "tie_both_8": (
        8,
        8,
        (
            (1, 1), (1, 2), (2, 1), (3, 1),
            (4, 5), (4, 6), (5, 6), (6, 6),
        ),
        (
            (1, 5), (2, 5),
            (4, 1), (4, 2), (5, 1), (6, 1), (6, 2),
        ),
    ),
    # A's 6-cell upper/left component beats a lower/right 3-cell component.
    # B is a passive one-component distractor and must survive unchanged.
    "single_unique_8": (
        8,
        8,
        (
            (1, 1), (1, 2), (1, 3), (2, 1), (2, 3), (3, 1),
            (5, 5), (5, 6), (6, 6),
        ),
        (
            (1, 6), (1, 7), (2, 7),
        ),
    ),
    # A has three components (6-vs-6-vs-3); its lower/right 6-cell component
    # wins the tie.  B is independently split 7-vs-3.
    "tie_both_16_three": (
        16,
        16,
        (
            (2, 2), (2, 3), (2, 4), (3, 2), (4, 2), (4, 3),
            (7, 2), (8, 2), (8, 3),
            (10, 11), (10, 12), (10, 13), (11, 13), (12, 12), (12, 13),
        ),
        (
            (2, 10), (2, 11), (2, 12), (2, 13), (3, 13), (4, 13), (5, 13),
            (11, 3), (12, 3), (12, 4),
        ),
    ),
    # A is split 10-vs-4; B is a passive irregular seven-cell component.
    "single_unique_16": (
        16,
        16,
        (
            (2, 12), (2, 13), (3, 13), (4, 13),
            (8, 3), (8, 4), (8, 5), (8, 6),
            (9, 3), (9, 6),
            (10, 3), (10, 4), (10, 6),
            (11, 3),
        ),
        (
            (2, 3), (2, 4), (2, 5), (3, 3), (4, 3), (4, 4), (5, 4),
        ),
    ),
}

_PROFILE_SIGNATURES = {
    "tie_both_8": (8, 8, ((2, 5), (4, 4))),
    "single_unique_8": (8, 8, ((3,), (3, 6))),
    "tie_both_16_three": (16, 16, ((3, 6, 6), (3, 7))),
    "single_unique_16": (16, 16, ((4, 10), (7,))),
}
_PROFILE_BY_SIGNATURE = {
    signature: profile for profile, signature in _PROFILE_SIGNATURES.items()
}

# Seven palettes are coprime with the four-profile schedule, yielding all 28
# profile/palette combinations over a short deterministic run.  Canonical
# background 7 appears in two palettes; role colors may swap by keyed RNG.
_PALETTES = (
    (7, 2, 9),
    (0, 3, 8),
    (1, 4, 6),
    (5, 2, 8),
    (7, 8, 9),
    (0, 1, 5),
    (3, 6, 9),
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic curriculum; every three-demo window contains a tie/both scene."""
    del seed
    offset = {"easy": 0, "medium": 1, "hard": 2}[_band(difficulty)]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % LESSON_SCHEDULE_PERIOD]


def _draw_profile(ctx, overrides: dict[str, Any], scheduled: str) -> str:
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        value = overrides["scene_profile"]
        if type(value) is not str:
            raise TypeError("scene_profile override must be a string")
        return str(ctx.draw_choice("scene_profile", SCENE_PROFILES))
    return str(ctx.draw_choice("scene_profile", (scheduled,)))


def _layout_variant(
    profile: str,
    h: int,
    w: int,
    role_a: tuple[tuple[int, int], ...],
    role_b: tuple[tuple[int, int], ...],
    rng,
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    """Apply only branch-preserving whole-scene transforms.

    Translation changes absolute placement without altering connectivity, sizes,
    tie scores relative to one another, or cross-color separation.  The 8x8 tie
    profile also permits a vertical reflection; both tied components exchange
    vertical order, so the lower/right tie rule remains observable.
    """
    cells = role_a + role_b
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)

    reflect_vertical = profile == "tie_both_8" and bool(rng.randrange(2))
    if reflect_vertical:
        role_a = tuple((h - 1 - r, c) for r, c in role_a)
        role_b = tuple((h - 1 - r, c) for r, c in role_b)
        cells = role_a + role_b
        min_r = min(r for r, _ in cells)
        max_r = max(r for r, _ in cells)

    # Keep at least one column available to the left of every possible winner.
    dr = rng.randint(-min_r, h - 1 - max_r)
    if h == 8:
        dc = 0
    else:
        lower_dc = max(-min_c, -2)
        upper_dc = min(w - 1 - max_c, 2)
        dc = rng.randint(lower_dc, upper_dc)

    def move(source):
        return tuple((r + dr, c + dc) for r, c in source)

    return move(role_a), move(role_b)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _draw_profile(
        ctx,
        overrides,
        schedule_profile(seed, sample_index, difficulty),
    )
    h, w, role_a, role_b = _PROFILE_CELLS[profile]
    role_a, role_b = _layout_variant(
        profile, h, w, role_a, role_b, ctx.draw_rng("layout_variant")
    )
    bg, first, second = ctx.draw_rng("palette").choice(_PALETTES)
    if ctx.draw_rng("role_swap").randrange(2):
        first, second = second, first
    grid = full_grid(h, w, bg)
    for r, c in role_a:
        grid[r][c] = first
    for r, c in role_b:
        if grid[r][c] != bg:
            raise RuntimeError(f"profile {profile!r} overlaps at {(r, c)}")
        grid[r][c] = second
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return ["grid must be rectangular"]
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _modal_background(grid: Any) -> tuple[int | None, list[str]]:
    counts = Counter(value for row in grid for value in row)
    highest = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == highest)
    if len(winners) != 1:
        return None, [f"background mode must be unique; tied colors are {winners}"]
    return winners[0], []


def _components(grid: Any, color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(r for r, _ in points),
        min(c for _, c in points),
        max(r for r, _ in points),
        max(c for _, c in points),
    )


def _winner(components: list[set[tuple[int, int]]], *, top_left_tie: bool = False):
    if top_left_tie:
        return max(components, key=lambda cells: (len(cells), -sum(_bbox(cells)[:2])))
    return max(components, key=lambda cells: (len(cells), sum(_bbox(cells)[:2])))


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    bg, bg_errors = _modal_background(grid)
    if bg_errors:
        return {"errors": bg_errors}
    assert bg is not None
    colors = sorted({value for row in grid for value in row if value != bg})
    per_color = []
    for color in colors:
        components = _components(grid, color)
        rows = [
            {"cells": cells, "size": len(cells), "bbox": _bbox(cells)}
            for cells in components
        ]
        rows.sort(key=lambda row: (row["bbox"][0], row["bbox"][1]))
        per_color.append({"color": color, "components": rows})
    signature = tuple(
        sorted(
            tuple(sorted(row["size"] for row in item["components"]))
            for item in per_color
        )
    )
    return {
        "errors": [],
        "height": len(grid),
        "width": len(grid[0]),
        "background": bg,
        "colors": colors,
        "palette_size": len(colors) + 1,
        "per_color": per_color,
        "active": [item for item in per_color if len(item["components"]) >= 2],
        "passive": [item for item in per_color if len(item["components"]) == 1],
        "signature": signature,
    }


def _rule_mirror(
    grid: Any,
    *,
    first_split_only: bool = False,
    top_left_tie: bool = False,
    preserve_winner_holes: bool = False,
    omit_left_column: bool = False,
    lower_right_only: bool = False,
) -> list[list[int]]:
    """Python mirror for semantic checks; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    bg = analysis["background"]
    out = deepcopy(grid)
    processed = 0
    for color in range(10):
        if color == bg:
            continue
        components = _components(grid, color)
        if len(components) < 2:
            continue
        if first_split_only and processed:
            continue
        processed += 1
        winner = (
            max(components, key=lambda cells: (sum(_bbox(cells)[:2]), len(cells)))
            if lower_right_only
            else _winner(components, top_left_tie=top_left_tie)
        )
        r0, c0, r1, c1 = _bbox(winner)
        for r, row in enumerate(out):
            for c, value in enumerate(row):
                if value == color:
                    out[r][c] = bg
        if preserve_winner_holes:
            for r, c in winner:
                out[r][c] = color
            if not omit_left_column:
                for r in range(r0, r1 + 1):
                    out[r][max(0, c0 - 1)] = color
        else:
            left = c0 if omit_left_column else max(0, c0 - 1)
            for r in range(r0, r1 + 1):
                for c in range(left, c1 + 1):
                    out[r][c] = color
    return [list(row) for row in out]


def observe_overrides(grid: Any) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return {}
    signature = (
        analysis["height"],
        analysis["width"],
        analysis["signature"],
    )
    profile = _PROFILE_BY_SIGNATURE.get(signature)
    return {"scene_profile": profile} if profile is not None else {}


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad task grammar, including lawful equal-size ties."""
    del difficulty
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    errors: list[str] = []
    if not analysis["active"]:
        errors.append("at least one non-background color must be split into components")
        return errors

    bg = analysis["background"]
    for item in analysis["active"]:
        components = [row["cells"] for row in item["components"]]
        winner = _winner(components)
        r0, c0, r1, c1 = _bbox(winner)
        if c0 == 0:
            errors.append(f"color {item['color']} winner has no visible left expansion column")
        largest = max(len(component) for component in components)
        tied = [component for component in components if len(component) == largest]
        tie_scores = [sum(_bbox(component)[:2]) for component in tied]
        if len(tie_scores) != len(set(tie_scores)):
            errors.append(
                f"color {item['color']} has an unresolved equal-size/equal-position tie"
            )
        foreign = {
            grid[r][c]
            for r in range(r0, r1 + 1)
            for c in range(max(0, c0 - 1), c1 + 1)
            if grid[r][c] not in (bg, item["color"])
        }
        if foreign:
            errors.append(
                f"color {item['color']} expansion overlaps foreign colors {sorted(foreign)}"
            )
    if not errors and _rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("scene hides the rule because the canonical output is unchanged")

    requested = None
    if isinstance(meta, dict):
        raw_overrides = meta.get("overrides")
        if isinstance(raw_overrides, dict):
            requested = raw_overrides.get("scene_profile")
    if requested is not None:
        observed = observe_overrides(grid).get("scene_profile")
        if observed != requested:
            errors.append(
                f"scene_profile override requested {requested!r}, observed {observed!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Canonical support manifold: palette three on an 8x8 or 16x16 canvas."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if (analysis["height"], analysis["width"]) not in {(8, 8), (16, 16)}:
        return ["canonical canvas must be 8x8 or 16x16"]
    if analysis["palette_size"] != 3:
        return ["canonical palette size is exactly three"]
    return []


def _rival_first_split_only(grid: Any) -> list[list[int]]:
    return _rule_mirror(grid, first_split_only=True)


def _rival_top_left_tie(grid: Any) -> list[list[int]]:
    return _rule_mirror(grid, top_left_tie=True)


def _rival_preserve_winner_holes(grid: Any) -> list[list[int]]:
    return _rule_mirror(grid, preserve_winner_holes=True)


def _rival_omit_left_column(grid: Any) -> list[list[int]]:
    return _rule_mirror(grid, omit_left_column=True)


def _rival_lower_right_component(grid: Any) -> list[list[int]]:
    """Plausible shortcut: choose location first and ignore component size."""
    return _rule_mirror(grid, lower_right_only=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "first_split_only": _rival_first_split_only,
    "top_left_tie": _rival_top_left_tie,
    "preserve_winner_holes": _rival_preserve_winner_holes,
    "omit_left_column": _rival_omit_left_column,
    "lower_right_component": _rival_lower_right_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The canonical pairs expose only one split color, and their largest component
# is also the lower/right one (or tied), so both shortcuts fit all official pairs.
CANONICAL_SHORTCUTS = {
    "first_split_only": _rival_first_split_only,
    "lower_right_component": _rival_lower_right_component,
}


def _valid_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis.get("errors") else analysis


def _has_tie(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    for item in analysis["active"]:
        sizes = [row["size"] for row in item["components"]]
        if sizes.count(max(sizes)) >= 2:
            return True
    return False


def _winner_has_hole(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    for item in analysis["active"]:
        winner = _winner([row["cells"] for row in item["components"]])
        r0, c0, r1, c1 = _bbox(winner)
        if len(winner) < (r1 - r0 + 1) * (c1 - c0 + 1):
            return True
    return False


def _winner_not_lower_right(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    for item in analysis["active"]:
        rows = item["components"]
        winner = max(rows, key=lambda row: row["size"])
        if all(winner["size"] != row["size"] for row in rows if row is not winner):
            if any(sum(winner["bbox"][:2]) < sum(row["bbox"][:2]) for row in rows):
                return True
    return False


SEMANTIC_WITNESSES = {
    "multiple_split_colors": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and len(analysis["active"]) >= 2
    ),
    "equal_size_lower_right_tie": _has_tie,
    "three_components": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and any(len(item["components"]) >= 3 for item in analysis["active"])
    ),
    "irregular_winner_bbox_fill": _winner_has_hole,
    "unique_winner_can_be_upper_left": _winner_not_lower_right,
    "visible_left_column": lambda grid: (
        not self_check(grid) and _rule_mirror(grid) != _rival_omit_left_column(grid)
    ),
}
WITNESS_RIVALS = {
    "multiple_split_colors": ["first_split_only"],
    "equal_size_lower_right_tie": ["top_left_tie"],
    "three_components": ["first_split_only"],
    "irregular_winner_bbox_fill": ["preserve_winner_holes"],
    "unique_winner_can_be_upper_left": ["lower_right_component"],
    "visible_left_column": ["omit_left_column"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject materialized lessons where a declared shortcut survives demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        try:
            expected = _rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"{label} is not a lawful input: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"{label} disagrees with the split-component rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
