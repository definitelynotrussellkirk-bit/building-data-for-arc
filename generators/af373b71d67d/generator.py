"""Generator for af373b71d67d — rotate a green motif into a frame.

The selected authority finds the color-3 object, finds the largest exact
rectangular outline of another color, erases the source object, rotates its
normalized offsets 90 degrees clockwise, and stamps them at the frame's
(top + 1, left + 1) coordinate.  Stamping is authoritative even when a target
cell replaces part of the frame border; the canonical test demonstrates that
case.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "af373b71d67d"
TASK_ID = GENERATOR_ID
RULE_HASH = "7364b3464a5f"
VERSION = "2.1.0"
SUMMARY = (
    "A connected green (3) motif and one hollow rectangular frame of another "
    "color appear on a 0 background. Erase the motif, rotate it 90 degrees "
    "clockwise, and stamp the normalized result at the frame's top-left "
    "interior coordinate. The stamp wins on contact with the frame border."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; the only foreground colors are motif color 3 and one frame color",
    "exactly one connected color-3 motif of 2..5 cells, changed by a 90-degree rotation",
    "exactly one hollow rectangular frame of a nonzero color other than 3",
    "the frame is at least 4x4 and its input interior is empty",
    "the source motif is outside and visually separated from the frame",
    "the clockwise stamp starts at frame top+1,left+1 and remains in the grid",
    "some scheduled examples overwrite a frame edge; others expose top-left rather than centered placement",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 8..16 with canonical-profile anchors",
        "valid": "8..16",
        "doc": "Grid height. Every value is constructively supported in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 10..18 with canonical-profile anchors",
        "valid": "10..18",
        "doc": "Grid width. Every value is constructively supported in every difficulty band.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_ALLOWED_OVERRIDES = frozenset(AXES)
_CANONICAL_DIMS = ((8, 10), (9, 12), (10, 12))
_FRAME_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)

# All motifs are 4-connected and have four distinct quarter-turn orientations.
# Keeping the library explicit makes the teaching guarantee reviewable.
_MOTIFS = {
    "L3": ((0, 0), (1, 0), (1, 1)),
    "L4": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "T4": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "P5": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    "F5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    "U5": ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    "V5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "Q5": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
}
_OVERWRITE_MOTIFS = ("L4", "T4", "P5", "F5", "U5", "V5", "Q5")
_ROOMY_MOTIFS = tuple(_MOTIFS)

SCHEDULE_PROFILES = ("frame_overwrite", "roomy_anchor")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive indices contain two examples of each lesson branch."""
    del seed, difficulty
    return "frame_overwrite" if sample_index % 4 in (0, 1) else "roomy_anchor"


def _normalize(cells):
    cells = list(cells)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(cells):
    cells = _normalize(cells)
    max_r = max(r for r, _ in cells)
    return _normalize((c, max_r - r) for r, c in cells)


def _rotate_ccw(cells):
    result = _normalize(cells)
    for _ in range(3):
        result = _rotate_cw(result)
    return result


def _shape_size(cells):
    cells = _normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_r in range(h):
        for start_c in range(w):
            if grid[start_r][start_c] != color or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen:
                        if grid[nr][nc] == color:
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _border_cells(r0, c0, r1, c1):
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _basic_grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9"
    return None


def _inspect_scene(grid):
    """Return (facts, findings); never raises for malformed user input."""
    first = _basic_grid_error(grid)
    if first:
        return None, [first]
    h, w = len(grid), len(grid[0])
    findings = []
    foreground = sorted({value for row in grid for value in row if value != 0})
    frame_colors = [color for color in foreground if color != 3]
    if 3 not in foreground:
        findings.append("missing color-3 motif")
    if len(frame_colors) != 1:
        findings.append(
            f"expected exactly one nonzero frame color other than 3, got {frame_colors}"
        )

    motif_components = _color_components(grid, 3)
    motif = motif_components[0] if len(motif_components) == 1 else None
    if len(motif_components) != 1:
        findings.append(f"expected exactly one color-3 motif, got {len(motif_components)}")
    elif not 2 <= len(motif) <= 5:
        findings.append(f"color-3 motif size {len(motif)} outside 2..5")
    elif _normalize(motif) == _rotate_cw(motif):
        findings.append("color-3 motif is unchanged by a 90-degree rotation")

    frame_color = frame_colors[0] if len(frame_colors) == 1 else None
    frame = None
    frame_bbox = None
    if frame_color is not None:
        frame_components = _color_components(grid, frame_color)
        if len(frame_components) != 1:
            findings.append(
                f"expected exactly one frame component in color {frame_color}, got {len(frame_components)}"
            )
        else:
            frame = frame_components[0]
            rows = [r for r, _ in frame]
            cols = [c for _, c in frame]
            frame_bbox = min(rows), min(cols), max(rows), max(cols)
            r0, c0, r1, c1 = frame_bbox
            if r1 - r0 + 1 < 4 or c1 - c0 + 1 < 4:
                findings.append("frame bbox is smaller than 4x4")
            expected = _border_cells(*frame_bbox)
            if set(frame) != expected:
                findings.append("frame cells are not exactly one hollow rectangular outline")
            if any(grid[r][c] != 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
                findings.append("frame interior is not empty in the input")

    if motif is not None and frame is not None and frame_bbox is not None:
        frame_set = set(frame)
        if any(
            max(abs(r - fr), abs(c - fc)) <= 1
            for r, c in motif
            for fr, fc in frame_set
        ):
            findings.append("motif must be visually separated from the frame")
        rotated = _rotate_cw(motif)
        r0, c0, _, _ = frame_bbox
        target = [(r0 + 1 + r, c0 + 1 + c) for r, c in rotated]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in target):
            findings.append("clockwise stamp would leave the grid")

    facts = None
    if not findings and motif is not None and frame is not None and frame_bbox is not None:
        facts = {
            "motif": tuple(motif),
            "frame": tuple(frame),
            "frame_color": frame_color,
            "frame_bbox": frame_bbox,
        }
    return facts, findings


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, findings = _inspect_scene(grid)
    return findings


def strict_canonical_like(grid):
    return self_check(grid)


def _require_scene(grid):
    facts, findings = _inspect_scene(grid)
    if findings:
        raise ValueError("invalid task grid: " + "; ".join(findings[:3]))
    return facts


def _apply_offsets(grid, offsets, *, erase=True, centered=False, preserve_frame=False):
    facts = _require_scene(grid)
    out = [list(row) for row in grid]
    if erase:
        for r, c in facts["motif"]:
            out[r][c] = 0
    offsets = _normalize(offsets)
    out_h, out_w = _shape_size(offsets)
    r0, c0, r1, c1 = facts["frame_bbox"]
    shift_r = shift_c = 0
    if centered:
        interior_h = r1 - r0 - 1
        interior_w = c1 - c0 - 1
        shift_r = max(0, (interior_h - out_h) // 2)
        shift_c = max(0, (interior_w - out_w) // 2)
    frame_set = set(facts["frame"])
    for r, c in offsets:
        target = r0 + 1 + shift_r + r, c0 + 1 + shift_c + c
        if not (0 <= target[0] < len(out) and 0 <= target[1] < len(out[0])):
            raise ValueError(f"rival target {target} leaves the grid")
        if preserve_frame and target in frame_set:
            continue
        out[target[0]][target[1]] = 3
    return out


def _intended_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _rotate_cw(facts["motif"]))


def _unrotated_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _normalize(facts["motif"]))


def _counterclockwise_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _rotate_ccw(facts["motif"]))


def _keep_source_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _rotate_cw(facts["motif"]), erase=False)


def _centered_when_fits_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _rotate_cw(facts["motif"]), centered=True)


def _preserve_frame_output(grid):
    facts = _require_scene(grid)
    return _apply_offsets(grid, _rotate_cw(facts["motif"]), preserve_frame=True)


def _clockwise_direction_witness(grid):
    intended = _intended_output(grid)
    return intended != _unrotated_output(grid) and intended != _counterclockwise_output(grid)


def _erase_source_witness(grid):
    return _intended_output(grid) != _keep_source_output(grid)


def _top_left_anchor_witness(grid):
    return _intended_output(grid) != _centered_when_fits_output(grid)


def _frame_overwrite_witness(grid):
    return _intended_output(grid) != _preserve_frame_output(grid)


SEMANTIC_WITNESSES = {
    "clockwise_direction": _clockwise_direction_witness,
    "erase_source": _erase_source_witness,
    "top_left_anchor": _top_left_anchor_witness,
    "frame_overwrite": _frame_overwrite_witness,
}
SEMANTIC_RIVALS = {
    "unrotated": _unrotated_output,
    "counterclockwise": _counterclockwise_output,
    "keep_source": _keep_source_output,
    "centered_when_fits": _centered_when_fits_output,
    "preserve_frame": _preserve_frame_output,
}
WITNESS_RIVALS = {
    "clockwise_direction": ["unrotated", "counterclockwise"],
    "erase_source": ["keep_source"],
    "top_left_anchor": ["centered_when_fits"],
    "frame_overwrite": ["preserve_frame"],
}
CANONICAL_SHORTCUTS = {"centered_when_fits": _centered_when_fits_output}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _default_dimensions(ctx, sample_index, difficulty):
    rng = ctx.draw_rng("default_dimensions")
    if sample_index % 5 == 0:
        return rng.choice(_CANONICAL_DIMS)
    all_h = list(range(8, 17))
    all_w = list(range(10, 19))
    if difficulty == "easy":
        h_choices = all_h + [8, 9, 10, 11] * 4
        w_choices = all_w + [10, 11, 12, 13] * 4
    elif difficulty == "hard":
        h_choices = all_h + [12, 13, 14, 15, 16] * 4
        w_choices = all_w + [14, 15, 16, 17, 18] * 4
    else:
        h_choices = all_h + [9, 10, 11, 12, 13, 14] * 3
        w_choices = all_w + [11, 12, 13, 14, 15, 16] * 3
    return rng.choice(h_choices), rng.choice(w_choices)


def _draw_dimension(ctx, overrides, label, lo, hi, default):
    if overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    # A singleton choice records the actual scheduled dimension in public draw
    # provenance while explicit callers retain the entire documented domain.
    return ctx.draw_choice(label, (default,))


def _shape_options(mode, difficulty):
    names = list(_OVERWRITE_MOTIFS if mode == "frame_overwrite" else _ROOMY_MOTIFS)
    if difficulty == "easy":
        names += [name for name in names if len(_MOTIFS[name]) <= 4] * 3
    elif difficulty == "hard":
        names += [name for name in names if len(_MOTIFS[name]) == 5] * 3
    return names


def _frame_dimensions(mode, rotated, rng):
    rot_h, rot_w = _shape_size(rotated)
    if mode == "roomy_anchor":
        # Two spare interior rows make a centered placement visibly different.
        # Width remains compact so the 8x10 boundary can hold the source beside it.
        return rot_h + 4, max(4, rot_w + 2 + rng.randint(0, 1))
    # Make the stamp hit exactly one frame edge while leaving no centering slack
    # in the other dimension. This isolates the overwrite lesson.
    if rot_w >= 3 and (rot_h < 3 or rng.randrange(2) == 0):
        return max(4, rot_h + 2), rot_w + 1
    return rot_h + 1, max(4, rot_w + 2)


def _rectangles_have_gap(sr, sc, sh, sw, fr, fc, fh, fw):
    sr1, sc1 = sr + sh - 1, sc + sw - 1
    fr1, fc1 = fr + fh - 1, fc + fw - 1
    return (
        sr1 < fr - 1
        or fr1 < sr - 1
        or sc1 < fc - 1
        or fc1 < sc - 1
    )


@lru_cache(maxsize=2048)
def _placements(h, w, sh, sw, fh, fw):
    """All source/frame bbox placements with one empty row or column between."""
    rows = []
    for fr in range(h - fh + 1):
        for fc in range(w - fw + 1):
            for sr in range(h - sh + 1):
                for sc in range(w - sw + 1):
                    if _rectangles_have_gap(sr, sc, sh, sw, fr, fc, fh, fw):
                        rows.append((sr, sc, fr, fc))
    return tuple(rows)


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_dimensions(ctx, sample_index, difficulty)
    h = _draw_dimension(ctx, overrides, "grid_h", 8, 16, default_h)
    w = _draw_dimension(ctx, overrides, "grid_w", 10, 18, default_w)

    mode = schedule_profile(seed, sample_index, difficulty)
    shape_name = ctx.draw_choice("motif_shape", _shape_options(mode, difficulty))
    motif = _MOTIFS[shape_name]
    rotated = _rotate_cw(motif)
    shape_h, shape_w = _shape_size(motif)
    frame_rng = ctx.draw_rng("frame_geometry")
    frame_h, frame_w = _frame_dimensions(mode, rotated, frame_rng)

    placements = _placements(h, w, shape_h, shape_w, frame_h, frame_w)
    if not placements:
        raise ValueError(
            f"no constructive layout for grid_h={h}, grid_w={w}, mode={mode}, "
            f"motif={shape_name}, frame={frame_h}x{frame_w}"
        )
    layout_rng = ctx.draw_rng("layout")
    source_r, source_c, frame_r, frame_c = layout_rng.choice(placements)
    frame_color = ctx.draw_choice(
        "frame_color", (_FRAME_COLORS[sample_index % len(_FRAME_COLORS)],)
    )

    grid = full_grid(h, w, 0)
    draw_frame(
        grid,
        frame_r,
        frame_c,
        frame_r + frame_h - 1,
        frame_c + frame_w - 1,
        frame_color,
    )
    for r, c in motif:
        grid[source_r + r][source_c + c] = 3

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    return grid
