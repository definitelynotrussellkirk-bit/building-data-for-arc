"""Generator for ARC task 1ea2cf5a712b: rotated colored-template matches.

A three-column template panel is separated from a board by one full-height
color-9 column.  The cropped 3x3 template uses two colors.  The canonical rule
searches the board for the template in all four rotations, treating template
zeros as wildcards, and marks every matched window's center with color 8 on a
zero board-sized output.

Ordinary generated scenes contain two or three true rotated matches, one
shortcut-rebutting decoy (wrong color mapping or a reflected copy), and an
extra foreground cell in a template-zero position of one true match.  The
extra cell makes the wildcard semantics observable rather than silently
teaching exact 3x3 window equality.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "1ea2cf5a712b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d20eedb326dc"

SUMMARY = (
    "Crop the two-color template left of the color-9 divider, search the board "
    "for that template in all four rotations with template zeros acting as "
    "wildcards, and mark color 8 at the center of every matching window on an "
    "otherwise zero board-sized output."
)

INVARIANTS = [
    "the input has a three-column template panel, one color-9 divider column, and a board",
    "the cropped template is a connected asymmetric 3x3 pattern using exactly two nonzero colors",
    "the board uses only background plus the two template colors and contains two or three true rotated matches",
    "one true match contains an extra foreground cell where the template has zero, making zero-as-wildcard observable",
    "one same-palette decoy rebuts either color-blind matching or reflection matching",
    "the output is board-sized, contains only 0 and 8, and marks unique match centers",
]

COUNTER_HYPOTHESES = [
    "match only the template's shown orientation",
    "ignore the template's color assignment and match only its occupied shape",
    "require template-zero cells to be zero instead of treating them as wildcards",
    "accept reflections as well as rotations",
    "mark only the first match or a fixed number of positions",
    "echo a fixed marker color, position, size, or board texture",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "uniform 7..9 in every difficulty band",
        "valid": "7..9",
    },
    "board_w": {
        "type": "int",
        "default": "uniform 8..9 in every difficulty band",
        "valid": "8..9",
    },
    "match_count": {
        "type": "int",
        "default": "uniform 2..3 in every difficulty band",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[object, ...] = ()

MIN_STRICT_FRAC = 0.05
EXAMPLES_NEEDED = 4

SCHEDULE_PROFILES = (
    "canonical_color_swap",
    "generalized_reflection",
    "canonical_reflection",
    "generalized_color_swap",
)

# Role 1 is the majority color and role 2 is the asymmetric marker color.
# Every template has four distinct rotations and a reflection outside that set.
_ROLE_TEMPLATES: tuple[tuple[tuple[int, ...], ...], ...] = (
    (
        (1, 2, 0),
        (1, 1, 1),
        (1, 0, 1),
    ),
    (
        (1, 1, 0),
        (0, 1, 2),
        (1, 1, 1),
    ),
    (
        (1, 0, 0),
        (1, 2, 1),
        (1, 1, 0),
    ),
    (
        (0, 1, 1),
        (1, 2, 0),
        (1, 1, 1),
    ),
)

_CANONICAL_ROLE_TEMPLATE = _ROLE_TEMPLATES[0]
_CANONICAL_TEMPLATE = (
    (2, 7, 0),
    (2, 2, 2),
    (2, 0, 2),
)
_GENERAL_COLOR_PAIRS = ((1, 4), (3, 6), (5, 2), (7, 3))
_DIVIDER_COLOR = 9
_MARK_COLOR = 8
_TEMPLATE_PANEL_W = 3


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Four-cycle whose every length-four window contains both decoy classes."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _rotate_grid(grid: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    height = len(grid)
    width = len(grid[0])
    return tuple(tuple(grid[height - 1 - r][c] for r in range(height)) for c in range(width))


def _rotate_n(grid: tuple[tuple[int, ...], ...], count: int) -> tuple[tuple[int, ...], ...]:
    out = grid
    for _ in range(count % 4):
        out = _rotate_grid(out)
    return out


def _flip_lr(grid: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in grid)


def _rotation_variants(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    variants = []
    current = template
    for _ in range(4):
        if current not in variants:
            variants.append(current)
        current = _rotate_grid(current)
    return tuple(variants)


def _d4_variants(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    variants = list(_rotation_variants(template))
    current = _flip_lr(template)
    for _ in range(4):
        if current not in variants:
            variants.append(current)
        current = _rotate_grid(current)
    return tuple(variants)


def _connected_nonzero(template: tuple[tuple[int, ...], ...]) -> bool:
    cells = {(r, c) for r, row in enumerate(template) for c, value in enumerate(row) if value != 0}
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _crop_nonzero(panel: list[list[int]]) -> tuple[tuple[int, ...], ...] | None:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, _DIVIDER_COLOR)
    ]
    if not cells:
        return None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return tuple(tuple(panel[r][c] for c in range(c0, c1 + 1)) for r in range(r0, r1 + 1))


def _split_input(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]]]:
    height = len(grid)
    divider_columns = [
        c for c in range(len(grid[0])) if all(grid[r][c] == _DIVIDER_COLOR for r in range(height))
    ]
    if divider_columns != [_TEMPLATE_PANEL_W]:
        raise ValueError(
            f"expected exactly one full-height color-9 divider at column {_TEMPLATE_PANEL_W}, "
            f"found {divider_columns}"
        )
    if any(
        grid[r][c] == _DIVIDER_COLOR
        for r in range(height)
        for c in range(len(grid[0]))
        if c != _TEMPLATE_PANEL_W
    ):
        raise ValueError("color 9 may appear only in the divider column")
    left = [row[:_TEMPLATE_PANEL_W] for row in grid]
    board = [row[_TEMPLATE_PANEL_W + 1 :] for row in grid]
    if not board or not board[0]:
        raise ValueError("board panel is empty")
    return left, board


def _match_at(
    board: list[list[int]],
    template: tuple[tuple[int, ...], ...],
    row0: int,
    col0: int,
    *,
    exact_zeros: bool = False,
    color_blind: bool = False,
) -> bool:
    for dr, row in enumerate(template):
        for dc, template_value in enumerate(row):
            board_value = board[row0 + dr][col0 + dc]
            if template_value == 0:
                if exact_zeros and board_value != 0:
                    return False
            elif color_blind:
                if board_value == 0:
                    return False
            elif board_value != template_value:
                return False
    return True


def _match_records(
    board: list[list[int]],
    template: tuple[tuple[int, ...], ...],
    *,
    include_reflections: bool = False,
    exact_zeros: bool = False,
    color_blind: bool = False,
) -> tuple[tuple[int, int, int, int, int], ...]:
    variants = _d4_variants(template) if include_reflections else _rotation_variants(template)
    records: list[tuple[int, int, int, int, int]] = []
    for variant_index, variant in enumerate(variants):
        th, tw = len(variant), len(variant[0])
        if th > len(board) or tw > len(board[0]):
            continue
        for r in range(len(board) - th + 1):
            for c in range(len(board[0]) - tw + 1):
                if _match_at(
                    board,
                    variant,
                    r,
                    c,
                    exact_zeros=exact_zeros,
                    color_blind=color_blind,
                ):
                    records.append((r, c, th, tw, variant_index))
    return tuple(records)


def _record_centers(records: Iterable[tuple[int, int, int, int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted(
            {
                (r + height // 2, c + width // 2)
                for r, c, height, width, _ in records
            }
        )
    )


def _render_centers(height: int, width: int, centers: Iterable[tuple[int, int]]) -> list[list[int]]:
    output = full_grid(height, width, 0)
    for r, c in centers:
        if 0 <= r < height and 0 <= c < width:
            output[r][c] = _MARK_COLOR
    return output


def _analyse(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    normalized = [list(row) for row in grid]
    try:
        panel, board = _split_input(normalized)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    template = _crop_nonzero(panel)
    if template is None:
        return {"errors": ["template panel has no nonzero template"]}

    colors = sorted({value for row in template for value in row if value != 0})
    template_cells = sum(value != 0 for row in template for value in row)
    records = _match_records(board, template)
    centers = _record_centers(records)

    return {
        "errors": [],
        "grid": normalized,
        "height": len(normalized),
        "total_width": len(normalized[0]),
        "board_width": len(board[0]),
        "panel": panel,
        "board": board,
        "template": template,
        "template_colors": colors,
        "template_cells": template_cells,
        "records": records,
        "centers": centers,
        "match_count": len(centers),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting all canonical inputs."""
    del difficulty, meta
    analysis = _analyse(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    template = analysis["template"]
    board = analysis["board"]
    colors = analysis["template_colors"]

    if (len(template), len(template[0])) != (3, 3):
        errors.append(f"cropped template must be 3x3, found {len(template)}x{len(template[0])}")
    if len(colors) != 2:
        errors.append(f"template must use exactly two nonzero colors, found {colors}")
    if any(color in (_DIVIDER_COLOR, _MARK_COLOR) for color in colors):
        errors.append("template colors may not use divider color 9 or output color 8")
    if not 5 <= analysis["template_cells"] <= 7:
        errors.append(f"template must contain 5..7 foreground cells, found {analysis['template_cells']}")
    if not _connected_nonzero(template):
        errors.append("template foreground must be orthogonally connected")
    if len(_rotation_variants(template)) != 4:
        errors.append("template must have four distinct rotations so orientation is observable")

    allowed_board_values = {0, *colors}
    board_values = {value for row in board for value in row}
    if not board_values <= allowed_board_values:
        errors.append(
            f"board may use only background and the two template colors {sorted(allowed_board_values)}, "
            f"found {sorted(board_values)}"
        )
    if analysis["match_count"] < 1:
        errors.append("board contains no rotated template match")
    if len(analysis["records"]) != analysis["match_count"]:
        errors.append("a board window matches multiple rotations, making the center/orientation ambiguous")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return [] on the public-size, public-template canonical manifold."""
    errors = list(self_check(grid))
    if errors:
        return errors
    analysis = _analyse(grid)
    if analysis["height"] not in (7, 8):
        errors.append("canonical inputs have height 7 or 8")
    if analysis["board_width"] != 8:
        errors.append("canonical inputs have board width 8")
    if analysis["template"] != _CANONICAL_TEMPLATE:
        errors.append("canonical inputs use the red/cyan-marker template pattern")
    return errors


def canonical_profile_signature(grid):
    """Strict linked profile used by task-local evidence."""
    if self_check(grid):
        return None
    analysis = _analyse(grid)
    palette_size = len({value for row in analysis["grid"] for value in row})
    signature = (analysis["height"], analysis["total_width"], palette_size)
    return signature if signature in {(7, 12, 4), (8, 12, 4)} else None


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyse(grid)
    return {
        "grid_h": analysis["height"],
        "board_w": analysis["board_width"],
        "match_count": analysis["match_count"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python test mirror; the canonical Racket rule remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyse(grid)
    return _render_centers(
        analysis["height"],
        analysis["board_width"],
        analysis["centers"],
    )


def _role_template_to_colors(
    role_template: tuple[tuple[int, ...], ...], primary: int, marker: int
) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(0 if value == 0 else primary if value == 1 else marker for value in row)
        for row in role_template
    )


def _swap_colors(template: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    colors = sorted({value for row in template for value in row if value != 0})
    if len(colors) != 2:
        raise ValueError("color swap requires exactly two template colors")
    left, right = colors
    return tuple(
        tuple(right if value == left else left if value == right else 0 for value in row)
        for row in template
    )


def _paint_window(
    board: list[list[int]],
    anchor: tuple[int, int],
    pattern: tuple[tuple[int, ...], ...],
) -> None:
    r0, c0 = anchor
    for dr, row in enumerate(pattern):
        for dc, value in enumerate(row):
            if value != 0:
                board[r0 + dr][c0 + dc] = value


def _corner_anchors(height: int, width: int) -> list[tuple[int, int]]:
    anchors = {(0, 0), (0, width - 3), (height - 3, 0), (height - 3, width - 3)}
    return sorted(anchors)


def _build_candidate(
    rng,
    *,
    height: int,
    board_width: int,
    match_count: int,
    role_template: tuple[tuple[int, ...], ...],
    colors: tuple[int, int],
    decoy_kind: str,
    connect_components: bool,
) -> list[list[int]]:
    template = _role_template_to_colors(role_template, *colors)
    board = full_grid(height, board_width, 0)
    anchors = _corner_anchors(height, board_width)
    rng.shuffle(anchors)
    target_anchors = anchors[:match_count]
    decoy_anchor = anchors[match_count]

    rotation_start = rng.randrange(4)
    orientations = tuple((rotation_start + index) % 4 for index in range(match_count))
    target_cell_sets: list[set[tuple[int, int]]] = []
    for anchor, orientation in zip(target_anchors, orientations):
        variant = _rotate_n(template, orientation)
        _paint_window(board, anchor, variant)
        target_cell_sets.append(
            {
                (anchor[0] + r, anchor[1] + c)
                for r, row in enumerate(variant)
                for c, value in enumerate(row)
                if value != 0
            }
        )

    if connect_components and len(target_cell_sets) >= 2:
        start, end = min(
            (
                (left, right)
                for left in target_cell_sets[0]
                for right in target_cell_sets[1]
            ),
            key=lambda pair: abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]),
        )
        r, c = start
        while r != end[0]:
            r += 1 if end[0] > r else -1
            if board[r][c] == 0:
                board[r][c] = colors[0]
        while c != end[1]:
            c += 1 if end[1] > c else -1
            if board[r][c] == 0:
                board[r][c] = colors[0]

    # Make zero-as-wildcard observable on one true match.
    wildcard_anchor = target_anchors[0]
    wildcard_variant = _rotate_n(template, orientations[0])
    zero_cells = [
        (r, c)
        for r, row in enumerate(wildcard_variant)
        for c, value in enumerate(row)
        if value == 0
    ]
    wr, wc = rng.choice(zero_cells)
    board[wildcard_anchor[0] + wr][wildcard_anchor[1] + wc] = rng.choice(colors)

    decoy_rotation = rng.randrange(4)
    if decoy_kind == "color_swap":
        decoy = _rotate_n(_swap_colors(template), decoy_rotation)
    elif decoy_kind == "reflection":
        decoy = _rotate_n(_flip_lr(template), decoy_rotation)
    else:
        raise ValueError(f"unknown decoy kind: {decoy_kind!r}")
    _paint_window(board, decoy_anchor, decoy)

    panel = full_grid(height, _TEMPLATE_PANEL_W, 0)
    top = rng.randint(0, height - 3)
    for dr, row in enumerate(template):
        for dc, value in enumerate(row):
            panel[top + dr][dc] = value

    output = full_grid(height, _TEMPLATE_PANEL_W + 1 + board_width, 0)
    for r in range(height):
        output[r][:_TEMPLATE_PANEL_W] = panel[r]
        output[r][_TEMPLATE_PANEL_W] = _DIVIDER_COLOR
        output[r][_TEMPLATE_PANEL_W + 1 :] = board[r]
    return output


def _rival_identity_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    # Search exactly the shown orientation, not the full rotation set.
    template = analysis["template"]
    records = []
    th, tw = len(template), len(template[0])
    for r in range(len(analysis["board"]) - th + 1):
        for c in range(len(analysis["board"][0]) - tw + 1):
            if _match_at(analysis["board"], template, r, c):
                records.append((r, c, th, tw, 0))
    centers = _record_centers(records)
    return _render_centers(analysis["height"], analysis["board_width"], centers)


def _rival_color_blind(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    records = _match_records(analysis["board"], analysis["template"], color_blind=True)
    return _render_centers(analysis["height"], analysis["board_width"], _record_centers(records))


def _rival_exact_zeros(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    records = _match_records(analysis["board"], analysis["template"], exact_zeros=True)
    return _render_centers(analysis["height"], analysis["board_width"], _record_centers(records))


def _rival_reflections_allowed(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    records = _match_records(
        analysis["board"], analysis["template"], include_reflections=True
    )
    return _render_centers(analysis["height"], analysis["board_width"], _record_centers(records))


def _rival_first_match_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyse(grid)
    centers = analysis["centers"][:1]
    return _render_centers(analysis["height"], analysis["board_width"], centers)


def _lawful(grid) -> bool:
    return not self_check(grid)


def _witness_canonical_anchor(grid) -> bool:
    return _lawful(grid) and not strict_canonical_like(grid)


def _witness_rotation_needed(grid) -> bool:
    return _lawful(grid) and _rival_identity_only(grid) != rule_mirror(grid)


def _witness_color_mapping(grid) -> bool:
    return _lawful(grid) and _rival_color_blind(grid) != rule_mirror(grid)


def _witness_zero_wildcard(grid) -> bool:
    return _lawful(grid) and _rival_exact_zeros(grid) != rule_mirror(grid)


def _witness_no_reflection(grid) -> bool:
    return _lawful(grid) and _rival_reflections_allowed(grid) != rule_mirror(grid)


def _witness_all_matches(grid) -> bool:
    return _lawful(grid) and _rival_first_match_only(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "canonical_anchor": _witness_canonical_anchor,
    "rotation_branch_changes_answer": _witness_rotation_needed,
    "two_color_mapping_rebuts_shape_only": _witness_color_mapping,
    "template_zero_is_wildcard": _witness_zero_wildcard,
    "reflection_is_not_a_rotation": _witness_no_reflection,
    "all_matches_are_marked": _witness_all_matches,
}

SEMANTIC_RIVALS = {
    "shown_orientation_only": _rival_identity_only,
    "color_blind_shape_match": _rival_color_blind,
    "require_zero_cells_clear": _rival_exact_zeros,
    "rotations_and_reflections": _rival_reflections_allowed,
    "first_match_only": _rival_first_match_only,
}

WITNESS_RIVALS = {
    "canonical_anchor": ["shown_orientation_only"],
    "rotation_branch_changes_answer": ["shown_orientation_only"],
    "two_color_mapping_rebuts_shape_only": ["color_blind_shape_match"],
    "template_zero_is_wildcard": ["require_zero_cells_clear"],
    "reflection_is_not_a_rotation": ["rotations_and_reflections"],
    "all_matches_are_marked": ["first_match_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "require_template_zeros_clear": _rival_exact_zeros,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives all demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"competitor {name!r} could not be evaluated: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes that the structural checker must reject."""
    base = generate(901, 0, difficulty="medium", grid_h=8, board_w=8, match_count=2)
    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_divider = [row[:] for row in base]
    for row in missing_divider:
        row[_TEMPLATE_PANEL_W] = 0
    fixtures.append(("missing_divider", missing_divider))

    second_divider = [row[:] for row in base]
    for row in second_divider:
        row[-1] = _DIVIDER_COLOR
    fixtures.append(("second_divider", second_divider))

    monochrome_template = [row[:] for row in base]
    template_colors = sorted(
        {value for row in monochrome_template for value in row[:_TEMPLATE_PANEL_W] if value != 0}
    )
    for r, row in enumerate(monochrome_template):
        for c in range(_TEMPLATE_PANEL_W):
            if row[c] == template_colors[1]:
                monochrome_template[r][c] = template_colors[0]
    fixtures.append(("monochrome_template", monochrome_template))

    no_board_match = [row[:] for row in base]
    for row in no_board_match:
        for c in range(_TEMPLATE_PANEL_W + 1, len(row)):
            row[c] = 0
    fixtures.append(("no_board_match", no_board_match))

    output_color_leak = [row[:] for row in base]
    output_color_leak[0][-1] = _MARK_COLOR
    fixtures.append(("output_color_in_input", output_color_leak))

    foreign_board_color = [row[:] for row in base]
    colors = set(value for row in foreign_board_color for value in row)
    foreign = next(value for value in range(1, 8) if value not in colors)
    foreign_board_color[0][-1] = foreign
    fixtures.append(("foreign_board_color", foreign_board_color))
    return fixtures


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int("grid_h", 7, 9)
    board_width = ctx.draw_int("board_w", 8, 9)
    match_count = ctx.draw_int("match_count", 2, 3)
    rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")

    profile = schedule_profile(seed, sample_index, difficulty)
    if profile.startswith("canonical"):
        role_template = _CANONICAL_ROLE_TEMPLATE
        colors = (2, 7)
    else:
        role_template = rng.choice(_ROLE_TEMPLATES[1:])
        colors = rng.choice(_GENERAL_COLOR_PAIRS)
    decoy_kind = "reflection" if profile.endswith("reflection") else "color_swap"

    for _ in range(128):
        grid = _build_candidate(
            rng,
            height=height,
            board_width=board_width,
            match_count=match_count,
            role_template=role_template,
            colors=colors,
            decoy_kind=decoy_kind,
            connect_components=difficulty == "hard",
        )
        if self_check(grid):
            continue
        if observe_overrides(grid)["match_count"] != match_count:
            continue
        official = rule_mirror(grid)
        if _rival_exact_zeros(grid) == official:
            continue
        if _rival_identity_only(grid) == official:
            continue
        if decoy_kind == "color_swap" and _rival_color_blind(grid) == official:
            continue
        if decoy_kind == "reflection" and _rival_reflections_allowed(grid) == official:
            continue
        return grid
    raise RuntimeError(
        f"could not construct a valid {profile} scene for "
        f"height={height}, board_width={board_width}, match_count={match_count}"
    )
