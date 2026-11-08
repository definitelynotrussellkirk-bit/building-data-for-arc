"""Generator for e9399a9f5b3b — find rotated template matches in panels.

The first panel is a colored template. Full color-9 columns separate it from
candidate panels. The official rule crops the template and marks every
candidate containing that exact color pattern under one of the four rotations;
template zeros are wildcards. Reflections are not matches.

The teaching distribution deliberately makes weak shortcuts fail: every
candidate contains the template color and the same number of template-colored
cells, nonmatches are one-cell near-misses or reflection-only traps, marker
colors occur independently of the answer, and scheduled lessons cover
identity, quarter-turn, multiple-match, and reflection-discrimination cases.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9399a9f5b3b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7ed9ec1730fc"
# The ordinary four-profile schedule realizes exactly 11 distinct selection strips.
EXPECTED_OUTPUT_CODOMAIN = 11

SUMMARY = (
    "Split at full color-9 columns. Crop the one-color template in the first "
    "panel, search each candidate for the template in any of its four rotations "
    "with template zeros acting as wildcards, and output a 1xN strip with "
    "cyan 8 under exactly the matching candidates. Reflections do not count."
)

INVARIANTS = [
    "the first panel contains one connected 4- or 5-cell single-color template",
    "3 or 4 equal-width candidate panels follow single full color-9 separators",
    "every candidate contains the template color, so color presence is not the answer",
    "ordinary generated candidates have equal template-color counts",
    "at least one candidate matches under rotation and at least one does not",
    "nonmatches include same-count near-misses and scheduled reflection-only traps",
    "marker colors are sparse distractors and do not encode the match pattern",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

AXES = {
    "panel_h": {
        "type": "int",
        "default": "difficulty-weighted; canonical schedule slot uses 5",
        "valid": "5..7",
    },
    "template_w": {
        "type": "int",
        "default": "difficulty-weighted; canonical schedule slot uses 3",
        "valid": "3..4",
    },
    "candidate_w": {
        "type": "int",
        "default": "difficulty-weighted; canonical schedule slot uses 5",
        "valid": "4..5",
    },
    "n_cands": {
        "type": "int",
        "default": "scheduled 4,3,4,4",
        "valid": "3..4",
    },
    "template_size": {
        "type": "int",
        "default": "scheduled 5,4,5,4",
        "valid": "4..5",
    },
    "template_color": {
        "type": "color",
        "default": "rng 1..8; canonical schedule slot uses 6",
        "valid": "1..8",
    },
    "extra_colors": {
        "type": "int",
        "default": "rng 2..4; canonical schedule slot uses 4",
        "valid": "2..4",
    },
    "match_count": {
        "type": "int",
        "default": "scheduled 1,1,2,1",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PROFILE_NAMES = (
    "canonical_single",
    "quarter_turn_single",
    "multiple_matches",
    "reflection_trap",
)
SCHEDULE_PROFILES = _PROFILE_NAMES

# Both shapes are chiral under rotations, which makes a reflected copy a real
# negative example rather than an answer-equivalent rotation.
_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 1), (0, 2), (1, 0), (1, 1)),  # S tetromino
    5: ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),  # canonical-like pentomino
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _norm_cells(cells: Any) -> tuple[tuple[int, int], ...]:
    cells = tuple((int(r), int(c)) for r, c in cells)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _rot_cells(cells: Any, turns: int) -> tuple[tuple[int, int], ...]:
    out = _norm_cells(cells)
    for _ in range(turns % 4):
        out = _norm_cells((c, -r) for r, c in out)
    return out


def _flip_lr_cells(cells: Any) -> tuple[tuple[int, int], ...]:
    cells = _norm_cells(cells)
    width = max(c for _, c in cells) + 1
    return _norm_cells((r, width - 1 - c) for r, c in cells)


def _dims(cells: Any) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _cells_to_grid(cells: Any, color: int) -> list[list[int]]:
    cells = _norm_cells(cells)
    h, w = _dims(cells)
    out = full_grid(h, w, 0)
    for r, c in cells:
        out[r][c] = color
    return out


def _rotate_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _grid_variants(template: list[list[int]], *, reflections: bool) -> list[list[list[int]]]:
    variants: list[list[list[int]]] = []
    current = [list(row) for row in template]
    for _ in range(4):
        if current not in variants:
            variants.append(current)
        current = _rotate_grid(current)
    if reflections:
        current = _flip_lr_grid(template)
        for _ in range(4):
            if current not in variants:
                variants.append(current)
            current = _rotate_grid(current)
    return variants


def _match_at(board: list[list[int]], template: list[list[int]], r0: int, c0: int) -> bool:
    for r, row in enumerate(template):
        for c, value in enumerate(row):
            if value != 0 and board[r0 + r][c0 + c] != value:
                return False
    return True


def _find_matches(
    board: list[list[int]],
    template: list[list[int]],
    *,
    reflections: bool = False,
    identity_only: bool = False,
) -> list[tuple[int, int, int]]:
    variants = [template] if identity_only else _grid_variants(template, reflections=reflections)
    found: list[tuple[int, int, int]] = []
    for variant_index, variant in enumerate(variants):
        vh, vw = len(variant), len(variant[0])
        if vh > len(board) or vw > len(board[0]):
            continue
        for r0 in range(len(board) - vh + 1):
            for c0 in range(len(board[0]) - vw + 1):
                if _match_at(board, variant, r0, c0):
                    found.append((r0, c0, variant_index))
    return found


def _full_separator_columns(grid: list[list[int]]) -> list[int]:
    return [
        c for c in range(len(grid[0]))
        if all(grid[r][c] == 9 for r in range(len(grid)))
    ]


def _split_panels(grid: list[list[int]]) -> tuple[list[list[list[int]]], list[int]]:
    separators = _full_separator_columns(grid)
    panels: list[list[list[int]]] = []
    start = 0
    for separator in separators + [len(grid[0])]:
        if start < separator:
            panels.append([list(row[start:separator]) for row in grid])
        start = separator + 1
    return panels, separators


def _crop_template(panel: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c) for r, row in enumerate(panel) for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in panel[r0:r1 + 1]]


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    seen = set(stack)
    while stack:
        r, c = stack.pop()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in remaining:
                remaining.remove(nxt)
                seen.add(nxt)
                stack.append(nxt)
    return not remaining


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    info: dict[str, Any] = {"errors": errors}
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty sequence of rows")
        return info
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("grid rows must be non-empty")
        return info
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return info
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return info
    if not 5 <= h <= 7:
        errors.append(f"panel height must be 5..7, got {h}")

    normalized = [list(row) for row in grid]
    panels, separators = _split_panels(normalized)
    if len(separators) not in (3, 4):
        errors.append(f"expected 3 or 4 full color-9 separators, got {len(separators)}")
    if any(b == a + 1 for a, b in zip(separators, separators[1:])):
        errors.append("separator columns must be single, not adjacent runs")
    if len(panels) != len(separators) + 1:
        errors.append("separator layout did not produce one template plus candidates")
        return info
    if len(panels) < 4:
        errors.append("at least one template and three candidates are required")
        return info

    template_panel, candidates = panels[0], panels[1:]
    template_w = len(template_panel[0])
    candidate_widths = [len(panel[0]) for panel in candidates]
    if not 3 <= template_w <= 4:
        errors.append(f"template panel width must be 3..4, got {template_w}")
    if len(set(candidate_widths)) != 1:
        errors.append(f"candidate panels must have equal width, got {candidate_widths}")
        candidate_w = candidate_widths[0]
    else:
        candidate_w = candidate_widths[0]
    if not 4 <= candidate_w <= 6:
        errors.append(f"candidate width must be 4..6, got {candidate_w}")

    template_values = [value for row in template_panel for value in row if value != 0]
    template_colors = sorted(set(template_values) - {9})
    if 9 in template_values:
        errors.append("template panel may not contain separator color 9")
    if len(template_colors) != 1:
        errors.append(f"template must use exactly one nonzero color, got {template_colors}")
        template_color = template_colors[0] if template_colors else None
    else:
        template_color = template_colors[0]
    template_cells = {
        (r, c) for r, row in enumerate(template_panel) for c, value in enumerate(row)
        if template_color is not None and value == template_color
    }
    template_size = len(template_cells)
    if template_size not in (4, 5):
        errors.append(f"template must contain 4 or 5 colored cells, got {template_size}")
    if template_cells and not _connected(template_cells):
        errors.append("template colored cells must be 4-connected")

    template = _crop_template(template_panel)
    match_indices: list[int] = []
    identity_match_indices: list[int] = []
    dihedral_match_indices: list[int] = []
    candidate_color_counts: list[int] = []
    candidate_marker_colors: list[set[int]] = []
    if template_color is not None:
        for index, panel in enumerate(candidates):
            color_count = sum(value == template_color for row in panel for value in row)
            candidate_color_counts.append(color_count)
            if color_count == 0:
                errors.append(f"candidate {index} lacks the template color")
            marker_colors = {
                value for row in panel for value in row
                if value not in (0, 9, template_color)
            }
            candidate_marker_colors.append(marker_colors)
            marker_cells = sum(
                value not in (0, 9, template_color) for row in panel for value in row
            )
            if marker_cells > 2:
                errors.append(f"candidate {index} has more than two sparse marker cells")
            if len(marker_colors) > 2:
                errors.append(f"candidate {index} uses more than two marker colors")
            if _find_matches(panel, template):
                match_indices.append(index)
            if _find_matches(panel, template, identity_only=True):
                identity_match_indices.append(index)
            if _find_matches(panel, template, reflections=True):
                dihedral_match_indices.append(index)

    if not match_indices:
        errors.append("at least one candidate must contain a rotated template match")
    if len(match_indices) == len(candidates):
        errors.append("at least one candidate must be a nonmatch")

    extra_palette = sorted(
        set(value for row in normalized for value in row) - {0, 9}
        - ({template_color} if template_color is not None else set())
    )
    if not 2 <= len(extra_palette) <= 4:
        errors.append(f"expected 2..4 extra distractor colors, got {extra_palette}")

    info.update({
        "grid": normalized,
        "panel_h": h,
        "width": w,
        "panels": panels,
        "separators": separators,
        "template_panel": template_panel,
        "candidates": candidates,
        "template": template,
        "template_w": template_w,
        "candidate_w": candidate_w,
        "n_cands": len(candidates),
        "template_color": template_color,
        "template_size": template_size,
        "extra_colors": len(extra_palette),
        "extra_palette": extra_palette,
        "match_indices": match_indices,
        "match_count": len(match_indices),
        "identity_match_indices": identity_match_indices,
        "dihedral_match_indices": dihedral_match_indices,
        "candidate_color_counts": candidate_color_counts,
        "candidate_marker_colors": candidate_marker_colors,
    })
    return info


def observe_overrides(grid: Any) -> dict[str, int]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {axis: int(info[axis]) for axis in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analysis(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed[axis] != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analysis(grid)
    if info["errors"]:
        return list(info["errors"])
    reasons: list[str] = []
    if info["panel_h"] not in (5, 6):
        reasons.append("canonical panels have height 5 or 6")
    if info["template_w"] != 3:
        reasons.append("canonical template panel width is 3")
    if info["candidate_w"] not in (5, 6):
        reasons.append("canonical candidate width is 5 or 6")
    if info["n_cands"] != 4:
        reasons.append("canonical task has exactly four candidates")
    if info["template_color"] != 6:
        reasons.append("canonical template color is 6")
    if info["template_size"] != 5:
        reasons.append("canonical template contains five colored cells")
    if info["match_count"] != 1:
        reasons.append("canonical examples contain exactly one matching candidate")
    palette_size = len(set(value for row in info["grid"] for value in row))
    if palette_size not in (6, 7):
        reasons.append("canonical palette size is 6 or 7")
    return reasons


def canonical_profile_signature(grid: Any) -> str | None:
    reasons = strict_canonical_like(grid)
    if reasons:
        return None
    info = _analysis(grid)
    return f"h{info['panel_h']}_cw{info['candidate_w']}_palette{len(set(sum(info['grid'], [])))}"


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror only; the canonical Racket program is authoritative."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [[8 if index in info["match_indices"] else 0 for index in range(info["n_cands"])]]


def _rival_strip(grid: Any, selector: Callable[[dict[str, Any], int], bool]) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [[8 if selector(info, i) else 0 for i in range(info["n_cands"])]]


def _rival_color_presence(grid: Any) -> list[list[int]]:
    return _rival_strip(grid, lambda info, i: info["candidate_color_counts"][i] > 0)


def _rival_equal_color_count(grid: Any) -> list[list[int]]:
    return _rival_strip(
        grid, lambda info, i: info["candidate_color_counts"][i] == info["template_size"]
    )


def _rival_identity_only(grid: Any) -> list[list[int]]:
    return _rival_strip(grid, lambda info, i: i in info["identity_match_indices"])


def _rival_allow_reflections(grid: Any) -> list[list[int]]:
    return _rival_strip(grid, lambda info, i: i in info["dihedral_match_indices"])


def _rival_first_candidate(grid: Any) -> list[list[int]]:
    return _rival_strip(grid, lambda info, i: i == 0)


def _rival_last_candidate(grid: Any) -> list[list[int]]:
    return _rival_strip(grid, lambda info, i: i == info["n_cands"] - 1)


SEMANTIC_RIVALS = {
    "template_color_presence": _rival_color_presence,
    "equal_template_color_count": _rival_equal_color_count,
    "identity_orientation_only": _rival_identity_only,
    "allow_reflections": _rival_allow_reflections,
    "always_first_candidate": _rival_first_candidate,
    "always_last_candidate": _rival_last_candidate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _lawful_info(grid: Any) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(grid: Any, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


SEMANTIC_WITNESSES = {
    "canonical_single_match": lambda grid: _witness(
        grid,
        lambda a: (
            a["panel_h"] in (5, 6)
            and a["template_w"] == 3
            and a["candidate_w"] in (5, 6)
            and a["n_cands"] == 4
            and a["template_color"] == 6
            and a["template_size"] == 5
            and a["match_count"] == 1
            and len(set(sum(a["grid"], []))) in (6, 7)
        ),
    ),
    "quarter_turn_only_match": lambda grid: _witness(
        grid,
        lambda a: any(
            i in a["match_indices"] and i not in a["identity_match_indices"]
            for i in range(a["n_cands"])
        ),
    ),
    "multiple_matches": lambda grid: _witness(grid, lambda a: a["match_count"] == 2),
    "reflection_only_nonmatch": lambda grid: _witness(
        grid,
        lambda a: any(
            i in a["dihedral_match_indices"] and i not in a["match_indices"]
            for i in range(a["n_cands"])
        ),
    ),
    "same_count_nonmatch": lambda grid: _witness(
        grid,
        lambda a: any(
            i not in a["match_indices"]
            and a["candidate_color_counts"][i] == a["template_size"]
            for i in range(a["n_cands"])
        ),
    ),
    "answer_not_first_only": lambda grid: _witness(
        grid, lambda a: a["match_indices"] != [0]
    ),
    "answer_not_last_only": lambda grid: _witness(
        grid, lambda a: a["match_indices"] != [a["n_cands"] - 1]
    ),
    "three_candidates": lambda grid: _witness(grid, lambda a: a["n_cands"] == 3),
    "four_candidates": lambda grid: _witness(grid, lambda a: a["n_cands"] == 4),
}

WITNESS_RIVALS = {
    "canonical_single_match": [
        "template_color_presence",
        "equal_template_color_count",
    ],
    "quarter_turn_only_match": ["identity_orientation_only"],
    "multiple_matches": ["always_first_candidate", "always_last_candidate"],
    "reflection_only_nonmatch": ["allow_reflections"],
    "same_count_nonmatch": [
        "template_color_presence",
        "equal_template_color_count",
    ],
    "answer_not_first_only": ["always_first_candidate"],
    "answer_not_last_only": ["always_last_candidate"],
    "three_candidates": ["always_first_candidate", "always_last_candidate"],
    "four_candidates": ["always_first_candidate", "always_last_candidate"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    checked: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the rotation-only rule")
            continue
        checked.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is malformed: {query_errors[0]}")
        return reasons
    query_truth = rule_mirror(query["input"])

    for name, competitor in LESSON_COMPETITORS.items():
        if checked and all(competitor(pair["input"]) == pair["output"] for pair in checked):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competitor {name!r} fits every demo but changes the query answer"
                )
    return sorted(set(reasons))


def _weighted_options(band: str, axis: str) -> list[int]:
    tables = {
        "panel_h": {
            "easy": [5, 5, 5, 6, 7],
            "medium": [5, 5, 6, 6, 7],
            "hard": [5, 6, 6, 7, 7],
        },
        "template_w": {
            "easy": [3, 3, 3, 4],
            "medium": [3, 3, 4, 4],
            "hard": [3, 4, 4, 4],
        },
        "candidate_w": {
            "easy": [4, 4, 5, 5],
            "medium": [4, 5, 5, 5],
            "hard": [4, 5, 5, 5],
        },
        "extra_colors": {
            "easy": [2, 2, 3, 4],
            "medium": [2, 3, 3, 4],
            "hard": [2, 3, 4, 4],
        },
    }
    return tables[axis][band]


def _placement_options(h: int, w: int, cells: Any) -> list[tuple[int, int]]:
    sh, sw = _dims(cells)
    return [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]


def _paint_cells(panel: list[list[int]], cells: Any, r0: int, c0: int, color: int) -> None:
    for r, c in cells:
        panel[r0 + r][c0 + c] = color


def _matching_panel(
    rng, h: int, w: int, shape: Any, color: int, *, force_quarter_turn: bool
) -> list[list[int]]:
    turns = rng.choice((1, 3)) if force_quarter_turn else rng.choice((0, 1, 2, 3))
    cells = _rot_cells(shape, turns)
    placements = _placement_options(h, w, cells)
    rng.shuffle(placements)
    template = _cells_to_grid(shape, color)
    for r0, c0 in placements:
        panel = full_grid(h, w, 0)
        _paint_cells(panel, cells, r0, c0, color)
        if not _find_matches(panel, template):
            continue
        if force_quarter_turn and _find_matches(panel, template, identity_only=True):
            continue
        return panel
    raise RuntimeError("could not construct requested matching candidate")


def _reflection_panel(rng, h: int, w: int, shape: Any, color: int) -> list[list[int]]:
    cells = _flip_lr_cells(shape)
    placements = _placement_options(h, w, cells)
    rng.shuffle(placements)
    template = _cells_to_grid(shape, color)
    for r0, c0 in placements:
        panel = full_grid(h, w, 0)
        _paint_cells(panel, cells, r0, c0, color)
        if _find_matches(panel, template):
            continue
        if not _find_matches(panel, template, reflections=True):
            continue
        return panel
    raise RuntimeError("could not construct reflection-only candidate")


def _near_miss_panel(
    rng, h: int, w: int, shape: Any, color: int
) -> tuple[list[list[int]], tuple[int, int]]:
    template = _cells_to_grid(shape, color)
    orientations = [_rot_cells(shape, turns) for turns in range(4)]
    rng.shuffle(orientations)
    for cells in orientations:
        placements = _placement_options(h, w, cells)
        rng.shuffle(placements)
        for r0, c0 in placements:
            ordered = list(cells)
            rng.shuffle(ordered)
            for missing in ordered:
                x_cells = [(r0 + r, c0 + c) for r, c in cells if (r, c) != missing]
                occupied = set(x_cells) | {(r0 + missing[0], c0 + missing[1])}
                decoys = [
                    (r, c) for r in range(h) for c in range(w)
                    if (r, c) not in occupied
                ]
                rng.shuffle(decoys)
                for decoy in decoys:
                    panel = full_grid(h, w, 0)
                    for r, c in x_cells:
                        panel[r][c] = color
                    panel[decoy[0]][decoy[1]] = color
                    if not _find_matches(panel, template):
                        return panel, (r0 + missing[0], c0 + missing[1])
    raise RuntimeError("could not construct same-count near-miss candidate")


def _assign_markers(
    rng,
    candidates: list[list[list[int]]],
    forced: dict[int, list[tuple[int, int]]],
    palette: list[int],
) -> None:
    slots: list[tuple[int, int, int]] = []
    for candidate_index, panel in enumerate(candidates):
        required = list(forced.get(candidate_index, ()))
        if required:
            slots.extend((candidate_index, r, c) for r, c in required)
        else:
            empty = [
                (r, c) for r in range(len(panel)) for c in range(len(panel[0]))
                if panel[r][c] == 0
            ]
            rng.shuffle(empty)
            r, c = empty[0]
            slots.append((candidate_index, r, c))

    needed = max(0, len(palette) - len(slots))
    for _ in range(needed):
        options: list[tuple[int, int, int]] = []
        per_candidate_counts = {
            i: sum(slot[0] == i for slot in slots) for i in range(len(candidates))
        }
        for candidate_index, panel in enumerate(candidates):
            if per_candidate_counts[candidate_index] >= 2:
                continue
            for r in range(len(panel)):
                for c in range(len(panel[0])):
                    if panel[r][c] == 0 and (candidate_index, r, c) not in slots:
                        options.append((candidate_index, r, c))
        if not options:
            raise RuntimeError("not enough empty cells to realize extra marker colors")
        slots.append(rng.choice(options))

    rng.shuffle(slots)
    for index, (candidate_index, r, c) in enumerate(slots):
        candidates[candidate_index][r][c] = palette[index % len(palette)]


def _scheduled_match_indices(
    seed: int, slot: int, n_cands: int, match_count: int
) -> list[int]:
    """Choose varied answer positions without weakening the four-slot lesson.

    The seed-relative offset expands the finite 1xN output support.  The slot
    offsets guarantee that a complete scheduled lesson cannot be solved by an
    always-first or always-last shortcut, regardless of the seed.
    """
    base = abs(int(seed)) % n_cands
    offsets = (0, 1, 0, 2)
    start = (base + offsets[slot]) % n_cands
    if match_count == 1:
        return [start]
    return sorted({start, (start + 1) % n_cands})


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    slot = int(sample_index) % len(_PROFILE_NAMES)

    effective = dict(overrides)
    scheduled = {
        0: {
            "panel_h": 5,
            "template_w": 3,
            "candidate_w": 5,
            "n_cands": 4,
            "template_size": 5,
            "template_color": 6,
            "extra_colors": 4,
            "match_count": 1,
        },
        1: {"n_cands": 3, "template_size": 4, "match_count": 1},
        2: {"n_cands": 4, "template_size": 5, "match_count": 2},
        3: {"n_cands": 4, "template_size": 4, "match_count": 1},
    }[slot]
    for key, value in scheduled.items():
        effective.setdefault(key, value)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective,
    )
    panel_h = ctx.draw_choice("panel_h", _weighted_options(band, "panel_h"))
    template_w = ctx.draw_choice("template_w", _weighted_options(band, "template_w"))
    candidate_w = ctx.draw_choice("candidate_w", _weighted_options(band, "candidate_w"))
    n_cands = ctx.draw_choice("n_cands", [3, 4])
    template_size = ctx.draw_choice("template_size", [4, 5])
    template_color = ctx.draw_choice("template_color", list(range(1, 9)))
    extra_colors = ctx.draw_choice("extra_colors", _weighted_options(band, "extra_colors"))
    match_count = ctx.draw_choice("match_count", [1, 2])

    layout_rng = ctx.draw_rng("layout")
    shape = _SHAPES[template_size]
    shape_h, shape_w = _dims(shape)
    if shape_h > panel_h or shape_w > template_w:
        raise ValueError("template shape does not fit requested template panel")

    template_panel = full_grid(panel_h, template_w, 0)
    tr = layout_rng.randint(0, panel_h - shape_h)
    tc = layout_rng.randint(0, template_w - shape_w)
    _paint_cells(template_panel, shape, tr, tc, template_color)

    match_indices = _scheduled_match_indices(seed, slot, n_cands, match_count)
    candidates: list[list[list[int]]] = []
    forced_markers: dict[int, list[tuple[int, int]]] = {}
    reflection_index = next(
        (i for i in range(n_cands) if i not in match_indices), None
    ) if slot == 3 else None
    quarter_turn_index = match_indices[0] if slot == 1 else None

    for candidate_index in range(n_cands):
        if candidate_index in match_indices:
            panel = _matching_panel(
                layout_rng,
                panel_h,
                candidate_w,
                shape,
                template_color,
                force_quarter_turn=(candidate_index == quarter_turn_index),
            )
        elif candidate_index == reflection_index:
            panel = _reflection_panel(
                layout_rng, panel_h, candidate_w, shape, template_color
            )
        else:
            panel, missing = _near_miss_panel(
                layout_rng, panel_h, candidate_w, shape, template_color
            )
            forced_markers.setdefault(candidate_index, []).append(missing)
        candidates.append(panel)

    color_rng = ctx.draw_rng("colors")
    marker_palette = color_rng.sample(
        [color for color in range(1, 9) if color != template_color],
        extra_colors,
    )
    _assign_markers(layout_rng, candidates, forced_markers, marker_palette)

    width = template_w + n_cands + n_cands * candidate_w
    grid = full_grid(panel_h, width, 0)
    cursor = 0
    for r in range(panel_h):
        grid[r][cursor:cursor + template_w] = template_panel[r]
    cursor += template_w
    for panel in candidates:
        for r in range(panel_h):
            grid[r][cursor] = 9
            grid[r][cursor + 1:cursor + 1 + candidate_w] = panel[r]
        cursor += candidate_w + 1

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "panel_h": panel_h,
        "template_w": template_w,
        "candidate_w": candidate_w,
        "n_cands": n_cands,
        "template_size": template_size,
        "template_color": template_color,
        "extra_colors": extra_colors,
        "match_count": match_count,
    }
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, got {observed}")
    return grid


def mutation_fixtures():
    """Task-specific malformed inputs that a structural checker must reject."""
    base = generate(9301, 0, difficulty="medium")
    info = _analysis(base)
    fixtures: list[tuple[str, list[list[int]]]] = []

    broken_separator = deepcopy(base)
    broken_separator[0][info["separators"][0]] = 0
    fixtures.append(("broken_separator", broken_separator))

    empty_template = deepcopy(base)
    for r in range(info["panel_h"]):
        for c in range(info["template_w"]):
            empty_template[r][c] = 0
    fixtures.append(("empty_template", empty_template))

    missing_template_color = deepcopy(base)
    first_candidate_start = info["template_w"] + 1
    for r in range(info["panel_h"]):
        for c in range(info["candidate_w"]):
            if missing_template_color[r][first_candidate_start + c] == info["template_color"]:
                missing_template_color[r][first_candidate_start + c] = info["extra_palette"][0]
    fixtures.append(("candidate_without_template_color", missing_template_color))

    fake_separator = deepcopy(base)
    fake_col = first_candidate_start
    for r in range(info["panel_h"]):
        fake_separator[r][fake_col] = 9
    fixtures.append(("extra_full_separator", fake_separator))

    disconnected_template = deepcopy(base)
    template_cells = sorted(
        (r, c) for r in range(info["panel_h"]) for c in range(info["template_w"])
        if disconnected_template[r][c] == info["template_color"]
    )
    r, c = template_cells[-1]
    disconnected_template[r][c] = 0
    disconnected_template[info["panel_h"] - 1][0] = info["template_color"]
    fixtures.append(("disconnected_template", disconnected_template))
    return fixtures
