"""Generator for 0083f06314c3 — selector chooses a template to search.

The input has exactly four panels separated by single full-height color-9
columns:

* panel 0: template A;
* panel 1: template B;
* panel 2: a one-cell selector (color 2 chooses A; every other color chooses B);
* panel 3: a search board.

The selected template is cropped to its nonzero bounding box.  Its nonzero
cells must match the board exactly, including color, while zero cells in the
crop are wildcards.  Only the original orientation is searched.  The output is
a board-sized grid that recolors the union of every selected-template match to
8.  Copies of the unselected template are deliberate distractors.

Default draws alternate a four-slot lesson schedule:

0. canonical panel-0 anchor;
1. adversarial panel-0 example;
2. canonical panel-1 anchor;
3. adversarial panel-1 example.

Every three consecutive demonstrations therefore show both selector branches,
one exact canonical anchor, and one adversarial example.  Adversarial examples
include wildcard fillers, a same-color rotated decoy, and a differently colored
same-shape decoy, so literal-background, D4, and color-blind rivals all fail.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0083f06314c3"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6a4eb398052b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35

SUMMARY = (
    "Four color-9-separated panels contain template A, template B, a selector, "
    "and a search board. Selector color 2 chooses A; any other selector color "
    "chooses B. Crop the chosen template, match its nonzero cells in the board "
    "in the original orientation and exact colors (crop zeros are wildcards), "
    "then recolor the union of all matching template cells to 8."
)

INVARIANTS = [
    "exactly four panels separated by three single full-height color-9 columns",
    "the two template panels have equal width and each contains one connected monochrome motif",
    "the selector panel is one column wide and contains exactly one nonzero cell",
    "selector color 2 chooses panel 0; every other selector color chooses panel 1",
    "ordinary draws contain every requested selected-template occurrence plus unselected-template distractors",
    "matching uses exact color and original orientation; zero cells inside the cropped template are wildcards",
]

# Every axis is exact and independently recoverable from the returned grid via
# observe_overrides().  Selector branch, colors, placements, and adversarial
# profile are intentional nuisance/schedule variables rather than fake axes.
AXES = {
    "grid_h": {
        "type": "int", "default": "difficulty-aware 6..8", "valid": "6..8",
        "doc": "Common height of all four panels.",
    },
    "template_w": {
        "type": "int", "default": "difficulty-aware 3..4", "valid": "3..4",
        "doc": "Equal width of template panels 0 and 1.",
    },
    "board_w": {
        "type": "int", "default": "difficulty-aware 8..12", "valid": "8..12",
        "doc": "Width of search-board panel 3.",
    },
    "template_cells": {
        "type": "int", "default": "difficulty-aware 3..5", "valid": "3..5",
        "doc": "Nonzero cell count of the selector-chosen template.",
    },
    "selected_copies": {
        "type": "int", "default": "difficulty-aware 1..2", "valid": "1..2",
        "doc": "Exact original-orientation/color occurrences of the selected template in the board.",
    },
    "distractor_copies": {
        "type": "int", "default": "difficulty-aware 1..2", "valid": "1..2",
        "doc": "Exact occurrences of the unselected template in the board.",
    },
}

SCHEDULE_PROFILES = (
    "canonical_panel0",
    "adversarial_panel0",
    "canonical_panel1",
    "adversarial_panel1",
)

# Official template silhouettes, including their canonical colors.
_CANONICAL_A = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
_CANONICAL_B = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_CANONICAL_LINKED_PROFILES = {
    (6, 8, 0, 1),
    (7, 8, 1, 1),
    (7, 9, 1, 2),
}

# Every generalized shape is connected, asymmetric under 90-degree rotation,
# and has at least one zero in its tight bounding box.  Those properties make
# wildcard and orientation rivals executable rather than merely named.
_SHAPES_BY_SIZE = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 1)),
    ),
    4: (
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
    ),
    5: (
        _CANONICAL_A,
        _CANONICAL_B,
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ),
}
_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)


def _norm(cells):
    cells = list(cells)
    if not cells:
        return tuple()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dims(cells):
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rotate_cw(cells):
    return _norm((c, -r) for r, c in cells)


def _d4_variants(cells):
    variants = []
    current = _norm(cells)
    for _ in range(4):
        for candidate in (current, _norm((r, -c) for r, c in current)):
            if candidate not in variants:
                variants.append(candidate)
        current = _rotate_cw(current)
    return variants


def _connected(cells):
    cells = set(cells)
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


def _template_grid(cells, color):
    h, w = _dims(cells)
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r][c] = color
    return grid


def _panel_ranges(grid):
    """Return panel column ranges, rejecting malformed/adjacent dividers."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return [], ["grid must be a non-empty rectangular list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return [], ["grid must be rectangular"]
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if any(b == a + 1 for a, b in zip(dividers, dividers[1:])):
        return [], ["divider columns must be single, not adjacent"]
    ranges = []
    start = 0
    for c in dividers:
        if start >= c:
            return [], ["empty panel adjacent to divider"]
        ranges.append((start, c - 1))
        start = c + 1
    if start >= w:
        return [], ["trailing divider leaves an empty panel"]
    ranges.append((start, w - 1))
    return ranges, []


def _crop_panel(grid, c0, c1):
    cells = [
        (r, c - c0, grid[r][c])
        for r in range(len(grid))
        for c in range(c0, c1 + 1)
        if grid[r][c] not in (0, 9)
    ]
    if not cells:
        return []
    min_r = min(r for r, _, _ in cells)
    min_c = min(c for _, c, _ in cells)
    max_r = max(r for r, _, _ in cells)
    max_c = max(c for _, c, _ in cells)
    out = full_grid(max_r - min_r + 1, max_c - min_c + 1, 0)
    for r, c, value in cells:
        out[r - min_r][c - min_c] = value
    return out


def _selector_color(grid, panel):
    c0, c1 = panel
    for r in range(len(grid)):
        for c in range(c0, c1 + 1):
            value = grid[r][c]
            if value not in (0, 9):
                return value
    return None


def _board_from_panel(grid, panel):
    c0, c1 = panel
    return [row[c0:c1 + 1] for row in grid]


def _nonzero_cells(template):
    return [
        (r, c, value)
        for r, row in enumerate(template)
        for c, value in enumerate(row)
        if value != 0
    ]


def _match_positions(board, template, *, ignore_color=False, solid_bbox=False):
    """Canonical mode-0 placements; template zero is wildcard unless solid."""
    if not board or not template:
        return []
    bh, bw = len(board), len(board[0])
    th, tw = len(template), len(template[0])
    if th > bh or tw > bw:
        return []
    positions = []
    for r0 in range(bh - th + 1):
        for c0 in range(bw - tw + 1):
            ok = True
            for r in range(th):
                for c in range(tw):
                    tv = template[r][c]
                    bv = board[r0 + r][c0 + c]
                    if tv == 0:
                        if solid_bbox and bv != 0:
                            ok = False
                            break
                    elif ignore_color:
                        if bv == 0:
                            ok = False
                            break
                    elif bv != tv:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                positions.append((r0, c0))
    return positions


def _union_output(board, template, positions):
    out = full_grid(len(board), len(board[0]), 0)
    nz = _nonzero_cells(template)
    for r0, c0 in positions:
        for r, c, _ in nz:
            out[r0 + r][c0 + c] = 8
    return out


def _solve_with_template(grid, template_index, *, mode="exact"):
    ranges, errors = _panel_ranges(grid)
    if errors or len(ranges) < 4:
        return None
    template = _crop_panel(grid, *ranges[template_index])
    board = _board_from_panel(grid, ranges[3])
    if not template:
        return None
    if mode == "solid_bbox":
        return _union_output(
            board, template,
            _match_positions(board, template, solid_bbox=True),
        )
    if mode == "shape_only":
        return _union_output(
            board, template,
            _match_positions(board, template, ignore_color=True),
        )
    if mode == "d4":
        output = full_grid(len(board), len(board[0]), 0)
        colored = [(r, c, v) for r, c, v in _nonzero_cells(template)]
        base_cells = [(r, c) for r, c, _ in colored]
        color_by_cell = {(r, c): v for r, c, v in colored}
        for variant_cells in _d4_variants(base_cells):
            # All generated/canonical templates are monochrome.  Preserve the
            # canonical color when forming the transformed rival template.
            color = next(iter(color_by_cell.values()))
            variant = _template_grid(variant_cells, color)
            for r0, c0 in _match_positions(board, variant):
                for r, c, _ in _nonzero_cells(variant):
                    output[r0 + r][c0 + c] = 8
        return output
    positions = _match_positions(board, template)
    return _union_output(board, template, positions)


def rule_mirror(grid):
    ranges, errors = _panel_ranges(grid)
    if errors or len(ranges) < 4:
        raise ValueError("; ".join(errors or ["need at least four panels"]))
    selector = _selector_color(grid, ranges[2])
    if selector is None:
        raise ValueError("selector panel is empty")
    return _solve_with_template(grid, 0 if selector == 2 else 1)


def _analyze(grid):
    errors = self_check(grid)
    if errors:
        return None
    ranges, _ = _panel_ranges(grid)
    selector = _selector_color(grid, ranges[2])
    selected_index = 0 if selector == 2 else 1
    selected = _crop_panel(grid, *ranges[selected_index])
    unselected = _crop_panel(grid, *ranges[1 - selected_index])
    board = _board_from_panel(grid, ranges[3])
    return {
        "ranges": ranges,
        "height": len(grid),
        "template_w": ranges[0][1] - ranges[0][0] + 1,
        "board_w": ranges[3][1] - ranges[3][0] + 1,
        "selector": selector,
        "selected_index": selected_index,
        "selected": selected,
        "unselected": unselected,
        "board": board,
        "selected_matches": _match_positions(board, selected),
        "distractor_matches": _match_positions(board, unselected),
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis is None:
        raise ValueError("cannot observe axes from an invalid grid")
    return {
        "grid_h": analysis["height"],
        "template_w": analysis["template_w"],
        "board_w": analysis["board_w"],
        "template_cells": len(_nonzero_cells(analysis["selected"])),
        "selected_copies": len(analysis["selected_matches"]),
        "distractor_copies": len(analysis["distractor_matches"]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    messages = []
    ranges, errors = _panel_ranges(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 8):
        messages.append(f"grid height must be 6..8, got {h}")
    if any(value not in range(10) for row in grid for value in row):
        messages.append("grid values must be ARC colors 0..9")
    if len(ranges) != 4:
        messages.append(f"need exactly four panels, got {len(ranges)}")
        return messages
    widths = [c1 - c0 + 1 for c0, c1 in ranges]
    if widths[0] != widths[1] or widths[0] not in (3, 4):
        messages.append(f"template panels must have equal width 3 or 4, got {widths[:2]}")
    if widths[2] != 1:
        messages.append(f"selector panel must be one column wide, got {widths[2]}")
    if not (8 <= widths[3] <= 12):
        messages.append(f"board width must be 8..12, got {widths[3]}")

    templates = []
    for index in (0, 1):
        crop = _crop_panel(grid, *ranges[index])
        if not crop:
            messages.append(f"template panel {index} is empty")
            templates.append([])
            continue
        cells = [(r, c) for r, row in enumerate(crop) for c, v in enumerate(row) if v]
        colors = {v for row in crop for v in row if v}
        if len(colors) != 1:
            messages.append(f"template panel {index} must be monochrome")
        if not _connected(cells):
            messages.append(f"template panel {index} must be four-connected")
        if not (3 <= len(cells) <= 5):
            messages.append(f"template panel {index} must contain 3..5 cells, got {len(cells)}")
        templates.append(crop)

    selector_cells = [
        grid[r][c]
        for r in range(h)
        for c in range(ranges[2][0], ranges[2][1] + 1)
        if grid[r][c] not in (0, 9)
    ]
    if len(selector_cells) != 1:
        messages.append(f"selector panel must contain exactly one nonzero cell, got {len(selector_cells)}")
        return messages
    selected_index = 0 if selector_cells[0] == 2 else 1
    if not templates[selected_index] or not templates[1 - selected_index]:
        return messages
    board = _board_from_panel(grid, ranges[3])
    selected_count = len(_match_positions(board, templates[selected_index]))
    distractor_count = len(_match_positions(board, templates[1 - selected_index]))
    if not (1 <= selected_count <= 2):
        messages.append(f"selected template must occur 1..2 times, got {selected_count}")
    if not (1 <= distractor_count <= 2):
        messages.append(f"unselected template must occur 1..2 times, got {distractor_count}")
    return messages


def strict_canonical_like(grid) -> list[str]:
    """Exact linked empirical manifold shared by all three official inputs."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analyze(grid)
    assert analysis is not None
    ranges = analysis["ranges"]
    widths = tuple(c1 - c0 + 1 for c0, c1 in ranges)
    if widths not in ((3, 3, 1, 8), (3, 3, 1, 9)):
        reasons.append(f"canonical panel widths are (3,3,1,8|9), got {widths}")

    a = _crop_panel(grid, *ranges[0])
    b = _crop_panel(grid, *ranges[1])
    if a != _template_grid(_CANONICAL_A, 2):
        reasons.append("panel 0 is not the canonical color-2 L template")
    if b != _template_grid(_CANONICAL_B, 3):
        reasons.append("panel 1 is not the canonical color-3 T template")

    selector_positions = [
        (r, c - ranges[2][0], grid[r][c])
        for r in range(len(grid))
        for c in range(ranges[2][0], ranges[2][1] + 1)
        if grid[r][c] not in (0, 9)
    ]
    if len(selector_positions) != 1 or selector_positions[0][0] != 0 \
            or selector_positions[0][2] not in (2, 3):
        reasons.append("canonical selector is one top-row cell of color 2 or 3")

    linked = (
        analysis["height"], analysis["board_w"], analysis["selected_index"],
        len(analysis["distractor_matches"]),
    )
    if linked not in _CANONICAL_LINKED_PROFILES:
        reasons.append(f"linked canonical profile absent: {linked}")
    if len(analysis["selected_matches"]) != 2:
        reasons.append("canonical board contains exactly two selected-template matches")
    board_nonzero = [v for row in analysis["board"] for v in row if v]
    expected = 5 * (2 + len(analysis["distractor_matches"]))
    if len(board_nonzero) != expected or set(board_nonzero) - {2, 3}:
        reasons.append("canonical board contains only selected/unselected template cells")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _axis(ctx, label, lo, hi, *, canonical=None):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if canonical is not None:
        return ctx.draw_int(label, canonical, canonical)
    return ctx.draw_int_diff(label, lo, hi)


def _place_panel_motif(panel, cells, color, rng, *, force_top=False):
    sh, sw = _dims(cells)
    top = 0 if force_top else rng.randint(0, len(panel) - sh)
    left = rng.randint(0, len(panel[0]) - sw)
    for r, c in cells:
        panel[top + r][left + c] = color


def _assemble(panels):
    h = len(panels[0])
    width = sum(len(panel[0]) for panel in panels) + len(panels) - 1
    grid = full_grid(h, width, 0)
    c0 = 0
    for index, panel in enumerate(panels):
        for r in range(h):
            grid[r][c0:c0 + len(panel[0])] = panel[r][:]
        c0 += len(panel[0])
        if index < len(panels) - 1:
            for r in range(h):
                grid[r][c0] = 9
            c0 += 1
    return grid


def _candidate_anchors(cells, h, w):
    sh, sw = _dims(cells)
    return [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]


def _build_board(
    rng, h, w, selected_cells, selected_color, selected_copies,
    unselected_cells, unselected_color, distractor_copies, *, adversarial,
):
    """Pack exact copies and adversarial decoys, then verify exact semantics."""
    selected_template = _template_grid(selected_cells, selected_color)
    unselected_template = _template_grid(unselected_cells, unselected_color)
    rotated = _rotate_cw(selected_cells)
    if adversarial and rotated == _norm(selected_cells):
        raise ValueError("adversarial selected shape must change under 90-degree rotation")
    extra_colors = [c for c in _COLORS if c not in {selected_color, unselected_color}]
    decoy_color = rng.choice(extra_colors)

    # Selected copies reserve their whole bbox so every template-zero can be
    # filled without another object occupying it. Other objects reserve only
    # their nonzero footprint, which keeps the small canonical canvases viable.
    object_specs = []
    for i in range(selected_copies):
        object_specs.append((selected_cells, selected_color, f"selected_{i}", True))
    for i in range(distractor_copies):
        object_specs.append((unselected_cells, unselected_color, f"unselected_{i}", False))
    if adversarial:
        object_specs.extend((
            (rotated, selected_color, "rotated_same_color", False),
            (selected_cells, decoy_color, "same_shape_other_color", False),
        ))

    for _attempt in range(160):
        board = full_grid(h, w, 0)
        occupied = set()
        reserved = set()
        placements = {}

        def backtrack(index):
            if index == len(object_specs):
                return True
            cells, color, tag, reserve_bbox = object_specs[index]
            anchors = _candidate_anchors(cells, h, w)
            rng.shuffle(anchors)
            sh, sw = _dims(cells)
            for r0, c0 in anchors:
                footprint = {(r0 + r, c0 + c) for r, c in cells}
                bbox = {
                    (r0 + r, c0 + c)
                    for r in range(sh) for c in range(sw)
                }
                if footprint & (occupied | reserved):
                    continue
                if reserve_bbox and bbox & (occupied | reserved):
                    continue
                for r, c in footprint:
                    board[r][c] = color
                occupied.update(footprint)
                if reserve_bbox:
                    reserved.update(bbox)
                placements[tag] = (r0, c0)
                if backtrack(index + 1):
                    return True
                placements.pop(tag, None)
                if reserve_bbox:
                    reserved.difference_update(bbox)
                occupied.difference_update(footprint)
                for r, c in footprint:
                    board[r][c] = 0
            return False

        if not backtrack(0):
            continue

        if adversarial:
            sh, sw = _dims(selected_cells)
            zeros = [
                (r, c) for r in range(sh) for c in range(sw)
                if (r, c) not in set(selected_cells)
            ]
            if not zeros:
                continue
            # Put a non-template color under a wildcard zero in EVERY selected
            # copy. A literal-background rival therefore misses every true hit.
            for i in range(selected_copies):
                r0, c0 = placements[f"selected_{i}"]
                choices = [(r, c) for r, c in zeros if board[r0 + r][c0 + c] == 0]
                if not choices:
                    break
                r, c = rng.choice(choices)
                board[r0 + r][c0 + c] = decoy_color
            else:
                selected_hits = _match_positions(board, selected_template)
                unselected_hits = _match_positions(board, unselected_template)
                if len(selected_hits) != selected_copies \
                        or len(unselected_hits) != distractor_copies:
                    continue
                true_out = _union_output(board, selected_template, selected_hits)
                solid_out = _union_output(
                    board, selected_template,
                    _match_positions(board, selected_template, solid_bbox=True),
                )
                colorblind_out = _union_output(
                    board, selected_template,
                    _match_positions(board, selected_template, ignore_color=True),
                )
                d4_out = full_grid(h, w, 0)
                for variant_cells in _d4_variants(selected_cells):
                    variant = _template_grid(variant_cells, selected_color)
                    for rr, cc in _match_positions(board, variant):
                        for r, c, _ in _nonzero_cells(variant):
                            d4_out[rr + r][cc + c] = 8
                if true_out == solid_out or true_out == colorblind_out or true_out == d4_out:
                    continue
                return board
            continue

        selected_hits = _match_positions(board, selected_template)
        unselected_hits = _match_positions(board, unselected_template)
        if len(selected_hits) == selected_copies and len(unselected_hits) == distractor_copies:
            return board
    raise ValueError("could not pack a semantically exact template-search board")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_index = sample_index % 4
    canonical_anchor = profile_index in (0, 2) and not overrides
    selected_index = 0 if profile_index in (0, 1) else 1
    rng = ctx.draw_rng("layout")

    if canonical_anchor:
        if selected_index == 0:
            linked = (6, 8, 0, 1)
        else:
            linked = (7, 8, 1, 1) if seed % 2 == 0 else (7, 9, 1, 2)
        grid_h = _axis(ctx, "grid_h", 6, 8, canonical=linked[0])
        template_w = _axis(ctx, "template_w", 3, 4, canonical=3)
        board_w = _axis(ctx, "board_w", 8, 12, canonical=linked[1])
        template_cells = _axis(ctx, "template_cells", 3, 5, canonical=5)
        selected_copies = _axis(ctx, "selected_copies", 1, 2, canonical=2)
        distractor_copies = _axis(ctx, "distractor_copies", 1, 2, canonical=linked[3])
        shape_a, shape_b = _CANONICAL_A, _CANONICAL_B
        color_a, color_b = 2, 3
        selector_color = 2 if selected_index == 0 else 3
    else:
        grid_h = _axis(ctx, "grid_h", 6, 8)
        template_w = _axis(ctx, "template_w", 3, 4)
        board_w = _axis(ctx, "board_w", 8, 12)
        template_cells = _axis(ctx, "template_cells", 3, 5)
        selected_copies = _axis(ctx, "selected_copies", 1, 2)
        distractor_copies = _axis(ctx, "distractor_copies", 1, 2)

        selected_shape = rng.choice(_SHAPES_BY_SIZE[template_cells])
        all_shapes = [shape for shapes in _SHAPES_BY_SIZE.values() for shape in shapes]
        unselected_options = [shape for shape in all_shapes if _norm(shape) != _norm(selected_shape)]
        unselected_shape = rng.choice(unselected_options)
        if selected_index == 0:
            shape_a, shape_b = selected_shape, unselected_shape
            selector_color = 2
        else:
            shape_a, shape_b = unselected_shape, selected_shape
            selector_color = rng.choice((3, 4, 5, 6, 7, 8))
        palette = [c for c in _COLORS if c != selector_color]
        color_a, color_b = rng.sample(palette, 2)

    panel_a = full_grid(grid_h, template_w, 0)
    panel_b = full_grid(grid_h, template_w, 0)
    selector_panel = full_grid(grid_h, 1, 0)
    _place_panel_motif(panel_a, shape_a, color_a, rng)
    _place_panel_motif(panel_b, shape_b, color_b, rng)
    selector_panel[0 if canonical_anchor else rng.randrange(grid_h)][0] = selector_color

    selected_cells = shape_a if selected_index == 0 else shape_b
    selected_color = color_a if selected_index == 0 else color_b
    unselected_cells = shape_b if selected_index == 0 else shape_a
    unselected_color = color_b if selected_index == 0 else color_a
    board = _build_board(
        rng, grid_h, board_w,
        selected_cells, selected_color, selected_copies,
        unselected_cells, unselected_color, distractor_copies,
        adversarial=not canonical_anchor,
    )
    grid = _assemble([panel_a, panel_b, selector_panel, board])
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": grid_h,
        "template_w": template_w,
        "board_w": board_w,
        "template_cells": template_cells,
        "selected_copies": selected_copies,
        "distractor_copies": distractor_copies,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: requested={expected} observed={observed}")
    return grid


# ---------------------------------------------------------------------------
# Semantic rivals, witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------

def _selected_index(grid):
    ranges, errors = _panel_ranges(grid)
    if errors or len(ranges) < 3:
        return None
    selector = _selector_color(grid, ranges[2])
    return None if selector is None else (0 if selector == 2 else 1)


def _rival_always_panel0(grid):
    return _solve_with_template(grid, 0)


def _rival_always_panel1(grid):
    return _solve_with_template(grid, 1)


def _rival_solid_bbox(grid):
    index = _selected_index(grid)
    return None if index is None else _solve_with_template(grid, index, mode="solid_bbox")


def _rival_d4_rotation(grid):
    index = _selected_index(grid)
    return None if index is None else _solve_with_template(grid, index, mode="d4")


def _rival_shape_only(grid):
    index = _selected_index(grid)
    return None if index is None else _solve_with_template(grid, index, mode="shape_only")


def _rival_mark_all_nonzero(grid):
    ranges, errors = _panel_ranges(grid)
    if errors or len(ranges) < 4:
        return None
    board = _board_from_panel(grid, ranges[3])
    return [[8 if value else 0 for value in row] for row in board]


def _rival_first_match_only(grid):
    ranges, errors = _panel_ranges(grid)
    if errors or len(ranges) < 4:
        return None
    index = _selected_index(grid)
    if index is None:
        return None
    template = _crop_panel(grid, *ranges[index])
    board = _board_from_panel(grid, ranges[3])
    matches = _match_positions(board, template)
    return _union_output(board, template, matches[:1])


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "always_panel0": _rival_always_panel0,
    "always_panel1": _rival_always_panel1,
    "solid_bbox": _rival_solid_bbox,
    "d4_rotation": _rival_d4_rotation,
    "shape_only_ignore_color": _rival_shape_only,
    "mark_all_nonzero": _rival_mark_all_nonzero,
    "first_match_only": _rival_first_match_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "solid_bbox": _rival_solid_bbox,
    "d4_rotation": _rival_d4_rotation,
    "shape_only_ignore_color": _rival_shape_only,
    "first_match_only": _rival_first_match_only,
}


def _valid_analysis(grid):
    return _analyze(grid)


def _witness_canonical(grid):
    return strict_canonical_like(grid) == []


def _witness_panel(index):
    return lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["selected_index"] == index
    )


def _witness_rival(name):
    return lambda grid: (
        (true := rule_mirror(grid)) is not None
        and SEMANTIC_RIVALS[name](grid) != true
    )


def _witness_multiple(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["selected_matches"]) > 1


SEMANTIC_WITNESSES = {
    "canonical_linked_profile": _witness_canonical,
    "selector_chooses_panel0": _witness_panel(0),
    "selector_chooses_panel1": _witness_panel(1),
    "wildcard_zero_is_not_literal": _witness_rival("solid_bbox"),
    "rotation_is_not_allowed": _witness_rival("d4_rotation"),
    "color_is_part_of_match": _witness_rival("shape_only_ignore_color"),
    "unselected_template_is_not_output": _witness_rival("mark_all_nonzero"),
    "all_occurrences_are_unioned": _witness_multiple,
}
WITNESS_RIVALS = {
    "canonical_linked_profile": ["mark_all_nonzero"],
    "selector_chooses_panel0": ["always_panel1"],
    "selector_chooses_panel1": ["always_panel0"],
    "wildcard_zero_is_not_literal": ["solid_bbox"],
    "rotation_is_not_allowed": ["d4_rotation"],
    "color_is_part_of_match": ["shape_only_ignore_color"],
    "unselected_template_is_not_output": ["mark_all_nonzero"],
    "all_occurrences_are_unioned": ["first_match_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with selector/template rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, rival in sorted(LESSON_COMPETITORS.items()):
        survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if survives:
            relation = "same" if rival(query["input"]) == query_answer else "different"
            reasons.append(
                f"competing rule {name!r} fits every demo and gives a {relation} query answer"
            )
    return reasons
