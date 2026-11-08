"""Generator for ARC task fa3550d200a0 / 414297c0.

The modal non-zero color identifies a rectangular canvas.  Colored marker
cells embedded in that canvas match the unique non-{0, 2, canvas} marker of
outside color-2 pieces.  Each matched piece is translated so its marker lands
on the same-colored canvas marker and is stamped into the cropped canvas.
Outside pieces with an unmatched marker are distractors and are not stamped.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "fa3550d200a0"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "af9e935761ad"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

SUMMARY = (
    "A variable 0-background grid contains one solid rectangular canvas in "
    "the modal non-zero color. Two through five distinct marker colors occur "
    "once inside the canvas. Isolated outside pieces contain one matching "
    "marker cell plus a small color-2 shape; translating each piece so its "
    "marker lands on the same-colored canvas marker stamps that shape into "
    "the canvas crop. Some lessons also include one unmatched-marker outside "
    "piece, which is a distractor and must be ignored."
    " Endpoint and diagonal pieces teach full eight-connected object extraction."
)

INVARIANTS = [
    "zero is the background and the unique modal non-zero color is the canvas",
    "the canvas color occupies one filled rectangular bounding box apart from marker substitutions",
    "each canvas marker color occurs exactly once and has exactly one matched outside piece",
    "every outside piece is 8-isolated from the canvas and every other outside piece",
    "an outside piece has exactly one non-{0,2,canvas} marker and all remaining cells are color 2",
    "matched stamps fit inside the canvas and each contributes at least one color-2 payload cell",
    "an optional unmatched-marker piece exercises the rule's ignore branch",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

# The first color is the canvas color.  Distinct canvas colors make the palette
# axis observable from the returned grid, while every palette still has enough
# remaining colors for five matched markers plus one unmatched distractor.
_PALETTES = {
    "warm": (1, 3, 4, 5, 6, 7, 8, 9),
    "cool": (8, 9, 6, 4, 3, 1, 5, 7),
    "broad": (5, 1, 7, 3, 9, 4, 8, 6),
    "primary": (3, 1, 5, 7, 9, 4, 6, 8),
}
_CANVAS_TO_PALETTE = {colors[0]: name for name, colors in _PALETTES.items()}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile mixture with difficulty-weighted 16..30",
        "valid": "16..30",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile mixture with difficulty-weighted 18..30",
        "valid": "18..30",
    },
    "piece_count": {
        "type": "int",
        "default": "sample schedule cycles 2,3,4,5",
        "valid": "2..5",
    },
    "decoy_count": {
        "type": "int",
        "default": "sample schedule guarantees both 0 and 1 per lesson",
        "valid": "0..1",
    },
    "rect_h": {
        "type": "int",
        "default": "difficulty-weighted 6..12",
        "valid": "6..12",
    },
    "rect_w": {
        "type": "int",
        "default": "difficulty-weighted 6..min(12, grid_w-10)",
        "valid": "6..12",
        "constraint": "rect_w <= grid_w - 10",
    },
    "canvas_side": {
        "type": "str",
        "default": "rng left or right",
        "valid": "left|right",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng palette family",
        "valid": "warm|cool|broad|primary",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    "rect_w > grid_w - 10: the canvas and two isolated 3-column piece lanes do not fit",
]

# Connected shapes around the unique marker at relative coordinate (0, 0).
# Every shape has 2-4 payload cells, so even six outside pieces cannot make
# color 2 more frequent than the smallest 6x6 canvas color.
_BASE_SHAPES = (
    ((0, 0), (-1, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (-1, 0), (0, -1), (0, 1)),
    ((0, 0), (-1, 0), (-1, 1), (0, -1)),
    ((0, 0), (-1, 0), (0, 1), (1, 1)),
    ((0, 0), (0, -1), (1, -1), (1, 0), (1, 1)),
    ((0, 0), (-1, -1), (-1, 0), (0, 1), (1, 1)),
    ((0, 0), (-1, 0), (0, -1), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (-1, -1), (1, 1)),
)
_ENDPOINT_SHAPE = ((0, 0), (0, 1), (0, 2))
_DIAGONAL_SHAPE = ((0, 0), (-1, -1), (1, 1))

_NEIGHBORS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not a coerced scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    integer_ranges = {
        "grid_h": (16, 30),
        "grid_w": (18, 30),
        "piece_count": (2, 5),
        "decoy_count": (0, 1),
        "rect_h": (6, 12),
        "rect_w": (6, 12),
    }
    for name, (lo, hi) in integer_ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    if "canvas_side" in overrides and overrides["canvas_side"] not in (None, "left", "right"):
        raise ValueError("canvas_side must be 'left' or 'right'")
    if "palette_kind" in overrides and overrides["palette_kind"] not in (None, *_PALETTES):
        raise ValueError("palette_kind must be warm, cool, broad, or primary")
    if overrides.get("grid_w") is not None and overrides.get("rect_w") is not None:
        if overrides["rect_w"] > overrides["grid_w"] - 10:
            raise ValueError("rect_w must be <= grid_w - 10 for two isolated piece lanes")


def _weighted_values(lo: int, hi: int, difficulty) -> tuple[int, ...]:
    values = list(range(lo, hi + 1))
    span = max(1, (hi - lo + 1) // 3)
    if difficulty == "easy":
        values.extend(list(range(lo, min(hi + 1, lo + span))) * 2)
    elif difficulty == "hard":
        values.extend(list(range(max(lo, hi - span + 1), hi + 1)) * 2)
    else:
        mid = (lo + hi) // 2
        values.extend(range(max(lo, mid - 1), min(hi, mid + 1) + 1))
    return tuple(values)


def _transform_shape(shape: Iterable[tuple[int, int]], turn: int, reflect: bool):
    cells = list(shape)
    for _ in range(turn % 4):
        cells = [(dc, -dr) for dr, dc in cells]
    if reflect:
        cells = [(dr, -dc) for dr, dc in cells]
    return tuple(sorted(set(cells)))


def _components8(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col, grid[current_row][current_col]))
                for dr, dc in _NEIGHBORS8:
                    next_row, next_col = current_row + dr, current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if grid[next_row][next_col] == 0 or (next_row, next_col) in seen:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(cells)
    return components


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be non-empty lists or tuples"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    height = len(grid)
    if height > 30 or width > 30:
        errors.append("grid exceeds the ARC 30x30 limit")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, errors + ["cells must be integer ARC colors 0..9"]

    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return None, errors + ["grid has no non-zero cells"]
    highest = max(counts.values())
    modal_colors = [color for color, count in counts.items() if count == highest]
    if len(modal_colors) != 1:
        return None, errors + [f"modal non-zero canvas color is not unique: {sorted(modal_colors)}"]
    canvas = modal_colors[0]
    if canvas == 2:
        errors.append("color 2 must be payload, not the modal canvas color")

    canvas_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == canvas
    ]
    top = min(row for row, _col in canvas_cells)
    bottom = max(row for row, _col in canvas_cells)
    left = min(col for _row, col in canvas_cells)
    right = max(col for _row, col in canvas_cells)
    if any(
        grid[row][col] == canvas
        for row in range(height)
        for col in range(width)
        if not (top <= row <= bottom and left <= col <= right)
    ):
        errors.append("canvas color appears outside its bounding box")
    if any(
        grid[row][col] == 0
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    ):
        errors.append("canvas bounding box contains a zero hole")
    if any(
        grid[row][col] == 2
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    ):
        errors.append("input canvas contains payload color 2 before stamping")

    marker_positions = {}
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            value = grid[row][col]
            if value not in (canvas, 0, 2):
                marker_positions.setdefault(value, []).append((row, col))
    if len(marker_positions) < 2:
        errors.append(f"expected at least two canvas marker colors, found {len(marker_positions)}")
    duplicate_markers = sorted(color for color, positions in marker_positions.items() if len(positions) != 1)
    if duplicate_markers:
        errors.append(f"canvas marker colors must occur exactly once: {duplicate_markers}")

    outside_components = []
    for component in _components8(grid):
        inside_flags = [top <= row <= bottom and left <= col <= right for row, col, _value in component]
        if all(inside_flags):
            continue
        if any(inside_flags):
            errors.append("an outside object touches or crosses the canvas component")
            continue
        outside_components.append(component)
    if not outside_components:
        errors.append("expected at least two outside pieces")

    matched_by_color = Counter()
    matched = 0
    decoys = 0
    piece_records = []
    for component_index, component in enumerate(outside_components):
        specials = [
            (row, col, value)
            for row, col, value in component
            if value not in (0, 2, canvas)
        ]
        if len(specials) != 1:
            errors.append(
                f"outside piece {component_index} must have exactly one special marker, found {len(specials)}"
            )
            continue
        special_row, special_col, marker = specials[0]
        if any(value not in (2, marker) for _row, _col, value in component):
            errors.append(f"outside piece {component_index} contains a non-payload extra color")
        payload_count = sum(value == 2 for _row, _col, value in component)
        if payload_count < 1:
            errors.append(f"outside piece {component_index} has no color-2 payload")
        if marker in marker_positions and len(marker_positions[marker]) == 1:
            matched += 1
            matched_by_color[marker] += 1
            anchor_row, anchor_col = marker_positions[marker][0]
            targets = [
                (
                    anchor_row + row - special_row,
                    anchor_col + col - special_col,
                    value,
                )
                for row, col, value in component
            ]
            if any(
                not (top <= row <= bottom and left <= col <= right)
                for row, col, _value in targets
            ):
                errors.append(f"matched piece {component_index} would be clipped by the canvas boundary")
            if not any(value == 2 for _row, _col, value in targets):
                errors.append(f"matched piece {component_index} has no stamping payload")
            piece_records.append(("matched", marker, component, targets))
        else:
            decoys += 1
            piece_records.append(("decoy", marker, component, ()))

    if matched < 2:
        errors.append(f"expected at least two matched outside pieces, found {matched}")
    missing = sorted(
        color
        for color, positions in marker_positions.items()
        if len(positions) == 1 and matched_by_color[color] != 1
    )
    duplicates = sorted(color for color, count in matched_by_color.items() if count != 1)
    if missing:
        errors.append(f"canvas markers without exactly one matched outside piece: {missing}")
    if duplicates:
        errors.append(f"outside marker colors used by multiple matched pieces: {duplicates}")

    features = {
        "grid_h": height,
        "grid_w": width,
        "canvas_color": canvas,
        "canvas_bbox": (top, left, bottom, right),
        "canvas_h": bottom - top + 1,
        "canvas_w": right - left + 1,
        "marker_positions": marker_positions,
        "piece_count": matched,
        "decoy_count": decoys,
        "outside_components": outside_components,
        "piece_records": piece_records,
    }
    return features, sorted(set(errors))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _features, errors = _analyze(grid)
    return errors


def observe_overrides(grid):
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    top, left, bottom, right = features["canvas_bbox"]
    observed = {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "piece_count": features["piece_count"],
        "decoy_count": features["decoy_count"],
        "rect_h": features["canvas_h"],
        "rect_w": features["canvas_w"],
    }
    if left == 1:
        observed["canvas_side"] = "left"
    elif right == features["grid_w"] - 2:
        observed["canvas_side"] = "right"
    palette_kind = _CANVAS_TO_PALETTE.get(features["canvas_color"])
    if palette_kind is not None:
        observed["palette_kind"] = palette_kind
    return observed


def _choose_canvas_anchors(shapes, canvas_h, canvas_w, rng, *, teaching=False):
    candidates = [
        (row, col)
        for row in range(1, canvas_h - 1)
        for col in range(1, canvas_w - 1)
    ]
    rng.shuffle(candidates)
    anchors = []
    footprints = []
    payload_union = set()
    protected = set()
    for shape_index, shape in enumerate(shapes):
        selected = None
        for anchor in candidates:
            if anchor in anchors:
                continue
            footprint = {(anchor[0] + dr, anchor[1] + dc) for dr, dc in shape}
            if any(not (0 <= row < canvas_h and 0 <= col < canvas_w) for row, col in footprint):
                continue
            if any(existing_anchor in footprint for existing_anchor in anchors):
                continue
            if any(anchor in existing_footprint for existing_footprint in footprints):
                continue
            payload = footprint - {anchor}
            if not payload - payload_union:
                continue
            # Scheduled teaching pieces retain their own visible payloads;
            # a later stamp cannot accidentally hide the separating evidence.
            if footprint & protected:
                continue
            selected = (anchor, footprint, payload)
            break
        if selected is None:
            return None
        anchor, footprint, payload = selected
        anchors.append(anchor)
        footprints.append(footprint)
        payload_union.update(payload)
        if teaching and shape_index < 2:
            protected.update(footprint)
    return anchors


def _piece_slots(height, canvas_side, canvas_left, canvas_width):
    # Bounding-box origins, not marker positions. Endpoint markers may lie two
    # cells from a payload while the complete object still fits a 3x3 box.
    row_anchors = (1, 6, 11)
    if canvas_side == "left":
        first_col = canvas_left + canvas_width + 1
        col_anchors = (first_col, first_col + 4)
    else:
        col_anchors = (1, 5)
    slots = [(row, col) for row in row_anchors for col in col_anchors]
    if any(not (1 <= row < height - 1) for row, _col in slots):
        raise AssertionError("piece slot schedule exceeds grid height")
    return slots


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    if overrides.get("piece_count") is not None:
        piece_count = ctx.draw_choice("piece_count", (2, 3, 4, 5))
    else:
        piece_count = ctx.draw_choice("piece_count", ((2, 3, 4, 5)[sample_index % 4],))
    if overrides.get("decoy_count") is not None:
        decoy_count = ctx.draw_choice("decoy_count", (0, 1))
    else:
        # Sequential samples 0..3 always contain a distractor witness and a
        # matched-only contrast in the demonstrations of a standard episode.
        scheduled = 1 if sample_index % 4 in (0, 2) else 0
        decoy_count = ctx.draw_choice("decoy_count", (scheduled,))

    # Preserve canonical-scale profiles in every difficulty band, alongside a
    # broad size component. Exact overrides still go through the keyed draws.
    core = ctx.draw_choice("profile_component", ("canonical", "canonical", "broad")) == "canonical"
    color_count = 3 + piece_count + decoy_count
    anchor_h, anchor_w = ((18, 22) if color_count == 7 else
                          (26, 24) if color_count == 8 else
                          ctx.draw_choice("small_profile", ((16, 18), (16, 20))))
    h_choices = _weighted_values(16, 30, difficulty) + ((anchor_h,) * 100 if core else ())
    # A caller can fix rect_w without fixing grid_w: draw from compatible
    # widths instead of silently shrinking the requested rectangle.
    min_width = max(18, (overrides.get("rect_w") or 6) + 10)
    w_choices = _weighted_values(min_width, 30, difficulty)
    if core and anchor_w >= min_width:
        w_choices += (anchor_w,) * 100
    grid_h = ctx.draw_choice("grid_h", h_choices)
    grid_w = ctx.draw_choice("grid_w", w_choices)
    canvas_h = ctx.draw_choice("rect_h", _weighted_values(6, 12, difficulty))
    canvas_w = ctx.draw_choice("rect_w", _weighted_values(6, min(12, grid_w - 10), difficulty))
    canvas_side = ctx.draw_choice("canvas_side", ("left", "right"))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    palette = _PALETTES[palette_kind]
    canvas_color = palette[0]
    marker_pool = list(palette[1:])
    rng.shuffle(marker_pool)
    matched_colors = marker_pool[:piece_count]
    decoy_colors = marker_pool[piece_count:piece_count + decoy_count]

    teaching = sample_index % 2 == 0
    anchors = None
    # Re-draw only shape choices, never semantic axes, until marker footprints
    # are feasible.  This preserves keyed-axis provenance exactly.
    for _attempt in range(120):
        matched_shapes = [
            _transform_shape(
                (_ENDPOINT_SHAPE if i == 0 else _DIAGONAL_SHAPE) if teaching and i < 2
                else rng.choice(_BASE_SHAPES), rng.randrange(4), bool(rng.randrange(2)))
            for i in range(piece_count)
        ]
        anchors = _choose_canvas_anchors(matched_shapes, canvas_h, canvas_w, rng, teaching=teaching)
        if anchors is not None:
            break
    if anchors is None:
        raise RuntimeError("could not place non-conflicting matched stamp anchors")
    transformed_shapes = matched_shapes + [
        _transform_shape(rng.choice(_BASE_SHAPES), rng.randrange(4), bool(rng.randrange(2)))
        for _ in range(decoy_count)
    ]

    canvas_top = rng.randint(1, grid_h - canvas_h - 1)
    canvas_left = 1 if canvas_side == "left" else grid_w - canvas_w - 1
    grid = full_grid(grid_h, grid_w, 0)
    draw_rect(grid, canvas_top, canvas_left, canvas_h, canvas_w, canvas_color)
    for (anchor_row, anchor_col), marker_color in zip(anchors, matched_colors):
        grid[canvas_top + anchor_row][canvas_left + anchor_col] = marker_color

    slots = _piece_slots(grid_h, canvas_side, canvas_left, canvas_w)
    rng.shuffle(slots)
    outside_colors = matched_colors + decoy_colors
    for shape, marker_color, (piece_row, piece_col) in zip(
        transformed_shapes,
        outside_colors,
        slots,
    ):
        min_r = min(dr for dr, _dc in shape)
        min_c = min(dc for _dr, dc in shape)
        for dr, dc in shape:
            grid[piece_row + dr - min_r][piece_col + dc - min_c] = marker_color if (dr, dc) == (0, 0) else 2

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def strict_canonical_like(grid):
    """The validated object domain, including all supplied canonical inputs."""
    return self_check(grid)


def diagnostic_stamp(grid, *, mode="eight_connected"):
    """Diagnostic Python prediction; all saved labels come from Racket.

    The two intentionally wrong modes retain a local marker window or only the
    marker's four-connected component. They are executable teaching rivals.
    """
    features, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    top, left, bottom, right = features["canvas_bbox"]
    out = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    if mode == "crop_only":
        return out
    for kind, marker, cells, _targets in features["piece_records"]:
        if kind != "matched":
            continue
        sr, sc, _ = next(cell for cell in cells if cell[2] == marker)
        ar, ac = features["marker_positions"][marker][0]
        selected = cells
        if mode == "local_window_3x3":
            selected = [(r, c, grid[r][c])
                        for r in range(max(0, sr - 1), min(len(grid), sr + 2))
                        for c in range(max(0, sc - 1), min(len(grid[0]), sc + 2))
                        if grid[r][c] != 0]
        elif mode == "four_connected":
            available = {(r, c) for r, c, _value in cells}
            reached, pending = {(sr, sc)}, [(sr, sc)]
            while pending:
                r, c = pending.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = r + dr, c + dc
                    if p in available and p not in reached:
                        reached.add(p)
                        pending.append(p)
            selected = [(r, c, value) for r, c, value in cells if (r, c) in reached]
        for r, c, value in selected:
            nr, nc = ar + r - sr - top, ac + c - sc - left
            if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
                out[nr][nc] = value
    return out


def _local_window(grid):
    return diagnostic_stamp(grid, mode="local_window_3x3")


def _four_connected(grid):
    return diagnostic_stamp(grid, mode="four_connected")


def _crop_only(grid):
    return diagnostic_stamp(grid, mode="crop_only")


def _window_witness(grid):
    return diagnostic_stamp(grid) != _local_window(grid)


def _connectivity_witness(grid):
    return diagnostic_stamp(grid) != _four_connected(grid)


SEMANTIC_RIVALS = {
    "local_window_3x3": _local_window,
    "four_connected": _four_connected,
    "crop_only": _crop_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"local_window_3x3": _local_window}
SEMANTIC_WITNESSES = {
    "endpoint_payload": _window_witness,
    "diagonal_connection": _connectivity_witness,
}
WITNESS_RIVALS = {
    "endpoint_payload": ["local_window_3x3"],
    "diagonal_connection": ["four_connected"],
}
