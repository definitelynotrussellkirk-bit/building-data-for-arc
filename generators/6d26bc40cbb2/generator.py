"""Canonical-linked generator for ARC task 6d26bc40cbb2.

Two maroon (9) marker cells encode a translation vector in row-major order.
The output removes the markers, keeps the foreground payload, and overlays a
copy of that payload translated by the marker vector.  If the translated copy
leaves the grid, the canonical Racket rule clips it at the grid boundary.

The generator deliberately teaches both fully-visible and clipped copies.  It
also anchors ordinary draws to the three demonstrated (height, width, palette)
profiles while retaining broader lawful variation.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6d26bc40cbb2"
TASK_ID = "6d26bc40cbb2"
VERSION = "3.1.0"
# Re-pinned atomically with the selected commented Racket source by this repair.
RULE_HASH = "c0f6a7976dde"

BACKGROUND = 0
MARKER = 9
PAYLOAD_COLORS = tuple(range(1, 9))
COPY_EXTENTS = ("fully_visible", "clipped")
EXAMPLES_NEEDED = 3
_CANONICAL_PROFILES = ((6, 7), (8, 8), (8, 9))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

SUMMARY = (
    "A connected nonzero/non-9 payload and exactly two maroon (9) markers are "
    "placed on a 0 background. Reading the markers in row-major order gives a "
    "translation vector. Remove both markers, keep the original payload, and "
    "overlay a copy shifted by that vector; the shifted copy wins on overlap "
    "and is clipped at the grid boundary. Ordinary draws cover both fully "
    "visible and clipped copies and periodically match canonical scale."
)

INVARIANTS = [
    "background is 0; exactly two marker cells have color 9",
    "all other nonzero cells form one 4-connected payload",
    "marker2 - marker1 in row-major order is the payload-copy translation",
    "the output removes markers, preserves the original payload, and overlays the translated copy",
    "translated payload cells outside the grid are clipped rather than invalidating the scene",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-keyed 6..12 with periodic canonical-profile anchors",
        "valid": "6..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-keyed 7..14 with periodic canonical-profile anchors",
        "valid": "7..14",
    },
    "payload_size": {
        "type": "int",
        "default": "difficulty-keyed exact foreground-cell count",
        "valid": "3..7",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-keyed exact number of payload colors",
        "valid": "1..3",
    },
    "copy_extent": {
        "type": "str",
        "default": "keyed choice between fully-visible and clipped translated copies",
        "valid": "fully_visible|clipped",
    },
}


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    global_bounds: tuple[int, int],
    band_bounds: tuple[int, int],
) -> int:
    """Honor the full declared override range even in a narrower difficulty band."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, *global_bounds)
    return ctx.draw_int(name, *band_bounds)


def _difficulty_bounds(difficulty: Any) -> dict[str, tuple[int, int]]:
    if difficulty == "easy":
        return {
            "grid_h": (6, 9),
            "grid_w": (7, 10),
            "payload_size": (3, 4),
            "palette_size": (1, 2),
        }
    if difficulty == "hard":
        return {
            "grid_h": (9, 12),
            "grid_w": (10, 14),
            "payload_size": (5, 7),
            "palette_size": (2, 3),
        }
    return {
        "grid_h": (7, 11),
        "grid_w": (8, 12),
        "payload_size": (4, 6),
        "palette_size": (1, 3),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a fresh deterministic input that obeys every declared exact axis."""
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

    # Every second un-overridden sample is pinned to one demonstrated scale.
    # The profile-floor census therefore has exact support in every band, while
    # the remaining 50% of draws retain broader size/count variation.
    canonical_anchor = not any(value is not None for value in overrides.values()) and sample_index % 2 == 0
    if canonical_anchor:
        profile_rng = ctx.draw_rng("canonical_profile")
        height, width = profile_rng.choice(_CANONICAL_PROFILES)
        height = ctx.draw_int("grid_h", height, height)
        width = ctx.draw_int("grid_w", width, width)
        payload_size = ctx.draw_int("payload_size", 3, 3)
        palette_size = ctx.draw_int("palette_size", 1, 1)
    else:
        bounds = _difficulty_bounds(difficulty)
        height = _draw_int_axis(ctx, overrides, "grid_h", (6, 12), bounds["grid_h"])
        width = _draw_int_axis(ctx, overrides, "grid_w", (7, 14), bounds["grid_w"])
        payload_size = _draw_int_axis(
            ctx, overrides, "payload_size", (3, 7), bounds["payload_size"]
        )
        if "palette_size" in overrides and overrides["palette_size"] is not None:
            palette_size = ctx.draw_int("palette_size", 1, 3)
        elif sample_index % 2 == 1:
            # Every three-consecutive-pair lesson window contains an odd sample,
            # so the canonical-fitting "modal color only" shortcut is always
            # refuted by at least one multicolor demonstration. Alternate 2/3
            # colors across odd residues to retain palette variation.
            scheduled_palette = 2 if sample_index % 4 == 1 else 3
            palette_size = ctx.draw_int("palette_size", scheduled_palette, scheduled_palette)
        else:
            palette_size = _draw_int_axis(
                ctx, overrides, "palette_size", (1, 3), bounds["palette_size"]
            )

    copy_extent = ctx.draw_choice("copy_extent", COPY_EXTENTS)
    if palette_size > payload_size:  # defensive; current declared ranges forbid this.
        raise ValueError("palette_size cannot exceed payload_size")

    shape_rng = ctx.draw_rng("payload_shape")
    layout_rng = ctx.draw_rng("layout")
    for _ in range(48):
        shape = _polyomino(shape_rng, payload_size)
        sh = max(row for row, _ in shape) + 1
        sw = max(col for _, col in shape) + 1
        if sh > height or sw > width:
            continue
        layout = _find_layout(height, width, shape, copy_extent, layout_rng)
        if layout is None:
            continue
        cells, marker1, marker2 = layout
        break
    else:
        raise RuntimeError(
            "could not construct a lawful scene for exact axes "
            f"h={height}, w={width}, payload_size={payload_size}, "
            f"palette_size={palette_size}, copy_extent={copy_extent!r}"
        )

    palette_rng = ctx.draw_rng("payload_palette")
    palette = palette_rng.sample(list(PAYLOAD_COLORS), palette_size)
    ordered_cells = list(cells)
    palette_rng.shuffle(ordered_cells)

    # Preserve the old color-count distribution: seed every requested color
    # exactly once, then draw all remaining colors freely from that palette.
    colors = list(palette)
    colors.extend(
        palette_rng.choice(palette)
        for _ in range(payload_size - palette_size)
    )

    assignments: list[tuple[tuple[int, int], int]] = []
    if palette_size > 1:
        # A realistic canonical-fitting shortcut keeps the complete original
        # object but copies only its modal color.  Put a non-modal color on a
        # source cell whose translated destination is newly visible, so every
        # multicolor scene gives direct evidence against that shortcut without
        # restricting shape, vector, clipping, palette, or count distributions.
        counts = Counter(colors)
        modal = min(counts, key=lambda color: (-counts[color], color))
        dr = marker2[0] - marker1[0]
        dc = marker2[1] - marker1[1]
        occupied = set(cells)
        revealing_sources = [
            cell
            for cell in ordered_cells
            if (
                0 <= cell[0] + dr < height
                and 0 <= cell[1] + dc < width
                and (cell[0] + dr, cell[1] + dc) not in occupied
            )
        ]
        if not revealing_sources:  # _find_layout guarantees this branch is unreachable.
            raise RuntimeError("multicolor scene has no newly visible copied cell")
        teaching_cell = palette_rng.choice(revealing_sources)
        teaching_colors = [color for color in colors if color != modal]
        teaching_color = palette_rng.choice(teaching_colors)
        colors.remove(teaching_color)
        remaining_cells = [cell for cell in ordered_cells if cell != teaching_cell]
        palette_rng.shuffle(colors)
        assignments.append((teaching_cell, teaching_color))
        assignments.extend(zip(remaining_cells, colors))
    else:
        palette_rng.shuffle(colors)
        assignments.extend(zip(ordered_cells, colors))

    grid = full_grid(height, width, BACKGROUND)
    for (row, col), color in assignments:
        grid[row][col] = color
    grid[marker1[0]][marker1[1]] = MARKER
    grid[marker2[0]][marker2[1]] = MARKER

    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError("constructed invalid teaching scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "payload_size": payload_size,
        "palette_size": palette_size,
        "copy_extent": copy_extent,
    }
    if observed != expected:
        raise RuntimeError(f"exact-axis construction mismatch: expected={expected}, observed={observed}")
    return [list(row) for row in grid]


def _polyomino(rng, size: int) -> list[tuple[int, int]]:
    """Draw a compact exact-size 4-connected polyomino and normalize it."""
    cells = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((row + dr, col + dc))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return sorted((row - min_row, col - min_col) for row, col in cells)


def _find_layout(
    height: int,
    width: int,
    shape: list[tuple[int, int]],
    copy_extent: str,
    rng,
) -> tuple[list[tuple[int, int]], tuple[int, int], tuple[int, int]] | None:
    """Find payload placement, translation, and free marker pair for the branch."""
    sh = max(row for row, _ in shape) + 1
    sw = max(col for _, col in shape) + 1
    placements = [
        (top, left)
        for top in range(height - sh + 1)
        for left in range(width - sw + 1)
    ]
    rng.shuffle(placements)

    # Row-major marker order means dr is positive, or dr==0 with positive dc.
    deltas = [
        (dr, dc)
        for dr in range(height)
        for dc in range(-(width - 1), width)
        if (dr > 0 or (dr == 0 and dc > 0))
    ]
    rng.shuffle(deltas)

    for top, left in placements:
        cells = [(top + row, left + col) for row, col in shape]
        occupied = set(cells)
        for dr, dc in deltas:
            shifted = [(row + dr, col + dc) for row, col in cells]
            visible = {
                (row, col)
                for row, col in shifted
                if 0 <= row < height and 0 <= col < width
            }
            clipped_count = len(shifted) - len(visible)
            if copy_extent == "fully_visible" and clipped_count:
                continue
            if copy_extent == "clipped" and (clipped_count == 0 or not visible):
                continue
            # Every generated lesson must visibly add at least one translated
            # payload cell; otherwise remove-markers-only is an undetectable rival.
            if not (visible - occupied):
                continue

            blocked = occupied | visible
            marker_pairs = []
            for row in range(height):
                for col in range(width):
                    other = (row + dr, col + dc)
                    if not (0 <= other[0] < height and 0 <= other[1] < width):
                        continue
                    first = (row, col)
                    if first in blocked or other in blocked:
                        continue
                    marker_pairs.append((first, other))
            if marker_pairs:
                marker1, marker2 = rng.choice(marker_pairs)
                return cells, marker1, marker2
    return None


def _payload_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (BACKGROUND, MARKER)
    ]


def _is_connected(cells: list[tuple[int, int]]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            nxt = (row + dr, col + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == remaining


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Recover task semantics and exact generated axes from an input grid."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid is empty or not a list of rows"], "facts": {}}
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid rows are empty or non-rectangular"], "facts": {}}
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color value")

    markers = sorted(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == MARKER
    )
    payload = _payload_cells(grid)
    if len(markers) != 2:
        errors.append(f"expected exactly two 9-markers, found {len(markers)}")
    if not payload:
        errors.append("no payload cells")
    elif not _is_connected(payload):
        errors.append("payload cells are not one 4-connected object")

    facts: dict[str, Any] = {
        "height": height,
        "width": width,
        "markers": tuple(markers),
        "payload": tuple(payload),
        "payload_size": len(payload),
        "palette": tuple(sorted({grid[row][col] for row, col in payload})),
    }
    facts["palette_size"] = len(facts["palette"])

    if len(markers) == 2 and payload:
        (r1, c1), (r2, c2) = markers
        dr, dc = r2 - r1, c2 - c1
        shifted = [(row + dr, col + dc) for row, col in payload]
        visible = tuple(
            (row, col)
            for row, col in shifted
            if 0 <= row < height and 0 <= col < width
        )
        visible_set = set(visible)
        payload_set = set(payload)
        clipped = len(shifted) - len(visible)
        copy_extent = (
            "invisible"
            if not visible
            else "clipped"
            if clipped
            else "fully_visible"
        )
        facts.update(
            {
                "delta": (dr, dc),
                "shifted": tuple(shifted),
                "visible_shifted": visible,
                "clipped_count": clipped,
                "copy_extent": copy_extent,
                "visible_new_count": len(visible_set - payload_set),
                "marker_copy_overlap": len(visible_set & set(markers)),
                "shift_horizontal": "left" if dc < 0 else "right" if dc > 0 else "vertical",
            }
        )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid structural grammar; canonical inputs must all pass."""
    del difficulty, meta
    return list(analyze_scene(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Teaching-distribution predicate layered on top of authority validity."""
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    facts = analysis["facts"]
    if facts.get("copy_extent") not in COPY_EXTENTS:
        errors.append("translation must leave at least one copied payload cell visible")
    if facts.get("visible_new_count", 0) < 1:
        errors.append("translation does not visibly add a new payload cell")
    if facts.get("marker_copy_overlap", 0):
        errors.append("a marker lies inside the visible translated payload footprint")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a returned generated grid."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "payload_size": facts["payload_size"],
        "palette_size": facts["palette_size"],
        "copy_extent": facts.get("copy_extent"),
    }


def semantic_signature(grid) -> tuple[Any, ...] | None:
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts.get("copy_extent"),
        facts.get("shift_horizontal"),
        facts["payload_size"],
        facts["palette_size"],
        facts.get("delta"),
    )


def solve_python(grid: list[list[int]]) -> list[list[int]]:
    """Test-only mirror of the canonical Racket rule; never an oracle fallback."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    height = len(grid)
    width = len(grid[0])
    (r1, c1), (r2, c2) = analysis["facts"]["markers"]
    dr, dc = r2 - r1, c2 - c1
    out = full_grid(height, width, BACKGROUND)
    for row in range(height):
        for col in range(width):
            src_row, src_col = row - dr, col - dc
            src_value = (
                grid[src_row][src_col]
                if 0 <= src_row < height and 0 <= src_col < width
                else BACKGROUND
            )
            value = grid[row][col]
            if src_value not in (BACKGROUND, MARKER):
                out[row][col] = src_value
            elif value not in (BACKGROUND, MARKER):
                out[row][col] = value
    return out


def _payload_only(grid: list[list[int]]) -> list[list[int]]:
    return [
        [value if value not in (BACKGROUND, MARKER) else BACKGROUND for value in row]
        for row in grid
    ]


def rival_remove_markers_only(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: delete the markers but never make the translated copy."""
    return _payload_only(grid)


def rival_move_instead_of_copy(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: translate the payload but incorrectly delete its original."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    height, width = len(grid), len(grid[0])
    dr, dc = analysis["facts"]["delta"]
    out = full_grid(height, width, BACKGROUND)
    for row, col in analysis["facts"]["payload"]:
        dst = (row + dr, col + dc)
        if 0 <= dst[0] < height and 0 <= dst[1] < width:
            out[dst[0]][dst[1]] = grid[row][col]
    return out


def rival_reverse_vector_copy(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: keep the payload but copy it using marker1-marker2."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    height, width = len(grid), len(grid[0])
    dr, dc = analysis["facts"]["delta"]
    out = _payload_only(grid)
    for row, col in analysis["facts"]["payload"]:
        dst = (row - dr, col - dc)
        if 0 <= dst[0] < height and 0 <= dst[1] < width:
            out[dst[0]][dst[1]] = grid[row][col]
    return out


def rival_modal_color_only(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut: keep the payload but copy only its modal color."""
    analysis = analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    facts = analysis["facts"]
    counts = Counter(grid[row][col] for row, col in facts["payload"])
    modal = min(counts, key=lambda color: (-counts[color], color))
    height, width = len(grid), len(grid[0])
    dr, dc = facts["delta"]
    out = _payload_only(grid)
    for row, col in facts["payload"]:
        if grid[row][col] != modal:
            continue
        dst = (row + dr, col + dc)
        if 0 <= dst[0] < height and 0 <= dst[1] < width:
            out[dst[0]][dst[1]] = modal
    return out


def _rival_disagrees(grid: list[list[int]], rival: Callable) -> bool:
    try:
        return solve_python(grid) != rival(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "fully_visible_copy": lambda grid: analyze_scene(grid)["facts"].get("copy_extent") == "fully_visible",
    "clipped_copy": lambda grid: analyze_scene(grid)["facts"].get("copy_extent") == "clipped",
    "shift_left": lambda grid: analyze_scene(grid)["facts"].get("shift_horizontal") == "left",
    "shift_right_or_vertical": lambda grid: analyze_scene(grid)["facts"].get("shift_horizontal") in {"right", "vertical"},
    "multicolor_payload": lambda grid: (
        analyze_scene(grid)["facts"].get("palette_size", 0) > 1
        and _rival_disagrees(grid, rival_modal_color_only)
    ),
    "visible_copy_refutes_identity": lambda grid: _rival_disagrees(grid, rival_remove_markers_only),
    "original_retained": lambda grid: _rival_disagrees(grid, rival_move_instead_of_copy),
}

SEMANTIC_RIVALS = {
    "remove_markers_only": rival_remove_markers_only,
    "move_instead_of_copy": rival_move_instead_of_copy,
    "reverse_vector_copy": rival_reverse_vector_copy,
    "modal_color_only": rival_modal_color_only,
}

WITNESS_RIVALS = {
    "fully_visible_copy": ["remove_markers_only"],
    "clipped_copy": ["remove_markers_only"],
    "shift_left": ["reverse_vector_copy"],
    "shift_right_or_vertical": ["reverse_vector_copy"],
    "multicolor_payload": ["modal_color_only"],
    "visible_copy_refutes_identity": ["remove_markers_only"],
    "original_retained": ["move_instead_of_copy"],
}

# The first three are refuted by every generated teaching scene.  The modal
# shortcut fits every single-color canonical example; each multicolor scene now
# refutes it directly, and the three-example schedule guarantees such a demo.
LESSON_COMPETITORS = {
    "remove_markers_only": rival_remove_markers_only,
    "move_instead_of_copy": rival_move_instead_of_copy,
    "reverse_vector_copy": rival_reverse_vector_copy,
    "modal_color_only": rival_modal_color_only,
}

CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require selected-rule outputs and reject each plausible per-lesson rival."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    findings: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        structural = strict_canonical_like(pair["input"])
        if structural:
            findings.append(f"pair {index} is outside teaching grammar: {structural}")
            continue
        expected = solve_python(pair["input"])
        if expected != pair["output"]:
            findings.append(f"pair {index} output disagrees with selected rule")
    if findings:
        return findings

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            relation = "different" if rival(query["input"]) != query["output"] else "same"
            findings.append(
                f"demos do not refute competitor {name}; its query answer is {relation}"
            )
    return findings
