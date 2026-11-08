"""Generator for ARC task 868de0fa / content task c09f9e692978.

Each same-colour hollow rectangular frame is filled independently.  The border
is preserved; a frame whose *interior width* is odd receives colour 7, while a
frame whose interior width is even receives colour 2.

The public examples use square blue frames, so height parity is an exact rival
on the canonical set.  Ordinary generated scenes therefore include rectangular
frames with opposite width/height parity in both directions.  Every third
sample is instead anchored to a public (dimensions, palette, frame-count)
profile so the curriculum remains tied to the canonical manifold.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "c09f9e692978"
TASK_ID = "c09f9e692978"
VERSION = "3.0.0"
RULE_HASH = "d74485baf037"

SUMMARY = (
    "On a zero-background grid, find every complete same-colour hollow "
    "rectangular frame. Preserve its border. Fill every zero cell strictly "
    "inside that frame with colour 7 when the number of interior columns is "
    "odd, and with colour 2 when the number of interior columns is even. "
    "Frames are handled independently; border colour, position, height, and "
    "the number of other frames do not determine the fill colour."
)

INVARIANTS = [
    "background is colour 0",
    "there are 2..5 complete hollow rectangular same-colour frames",
    "every frame has a non-empty zero interior and dimensions 3..10",
    "frame borders avoid output colours 2 and 7",
    "the default lesson distribution contains both odd and even interior widths",
    "ordinary non-canonical samples contain width/height parity disagreements",
]

EXAMPLES_NEEDED = 3

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 10..22 with periodic canonical anchors",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 10..22 with periodic canonical anchors",
        "valid": "10..22",
    },
    "n_frames": {
        "type": "int",
        "default": "difficulty-aware 2..5 with periodic canonical anchors",
        "valid": "2..5",
    },
    "parity_profile": {
        "type": "str",
        "default": "mixed",
        "valid": "mixed|odd_only|even_only",
    },
}

_PARITY_PROFILES = ("mixed", "odd_only", "even_only")
_BORDER_PALETTE = (1, 3, 4, 5, 6, 8, 9)
_CANONICAL_DIMS_COUNTS = {
    (10, 10, 2),
    (10, 10, 3),
    (11, 11, 3),
    (15, 15, 2),
    (20, 20, 4),
    (20, 20, 5),
}

# Exact public-profile layouts, stored as (row, col, frame_h, frame_w).
# They are not copied as training outputs; they are lawful input geometries that
# keep the generated distribution anchored to the observed public manifold.
_CANONICAL_LAYOUTS: tuple[tuple[int, int, tuple[tuple[int, int, int, int], ...]], ...] = (
    (10, 10, ((0, 0, 3, 3), (0, 4, 6, 6))),
    (10, 10, ((0, 0, 4, 4), (2, 6, 3, 3), (5, 0, 5, 5))),
    (11, 11, ((1, 1, 3, 3), (2, 5, 4, 4), (6, 0, 5, 5))),
    (15, 15, ((1, 1, 7, 7), (9, 6, 6, 6))),
    (
        20,
        20,
        (
            (0, 12, 5, 5),
            (2, 1, 8, 8),
            (7, 10, 10, 10),
            (11, 1, 7, 7),
        ),
    ),
    (
        20,
        20,
        (
            (0, 0, 5, 5),
            (1, 6, 4, 4),
            (3, 12, 6, 6),
            (9, 2, 7, 7),
            (12, 12, 8, 8),
        ),
    ),
)


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_int_axis(ctx, overrides, name, default_lo, default_hi):
    if name in overrides:
        return ctx.draw_int(name, int(AXES[name]["valid"].split("..")[0]),
                            int(AXES[name]["valid"].split("..")[1]))
    return ctx.draw_int(name, default_lo, default_hi)


def _draw_choice_axis(ctx, overrides, name, default_options, all_options):
    if name in overrides:
        return ctx.draw_choice(name, all_options)
    return ctx.draw_choice(name, default_options)


def _canonical_candidates(difficulty: Any):
    if difficulty == "easy":
        return _CANONICAL_LAYOUTS[:3]
    if difficulty == "medium":
        return (_CANONICAL_LAYOUTS[2], _CANONICAL_LAYOUTS[3])
    if difficulty == "hard":
        return _CANONICAL_LAYOUTS[4:]
    return _CANONICAL_LAYOUTS


def _canonical_anchor(ctx, difficulty):
    choices = _canonical_candidates(difficulty)
    rng = ctx.draw_rng("canonical_profile")
    return choices[rng.randrange(len(choices))]


def _pack_specs(specs, h, w, rng):
    """Shelf-pack rectangles with deterministic random slack distribution."""
    rows = []
    current = []
    used_w = 0
    row_h = 0
    for fh, fw in specs:
        if current and used_w + fw > w:
            rows.append((current, used_w, row_h))
            current = []
            used_w = 0
            row_h = 0
        if fw > w:
            return None
        current.append((fh, fw))
        used_w += fw
        row_h = max(row_h, fh)
    if current:
        rows.append((current, used_w, row_h))
    total_h = sum(row_h for _, _, row_h in rows)
    if total_h > h:
        return None

    def distribute(total, slots):
        cuts = sorted(rng.randint(0, total) for _ in range(max(0, slots - 1)))
        points = [0, *cuts, total]
        return [points[i + 1] - points[i] for i in range(slots)]

    vertical = distribute(h - total_h, len(rows) + 1)
    placements = []
    y = vertical[0]
    for row_index, (row_specs, row_width, this_h) in enumerate(rows):
        horizontal = distribute(w - row_width, len(row_specs) + 1)
        x = horizontal[0]
        for index, (fh, fw) in enumerate(row_specs):
            placements.append((y, x, fh, fw))
            x += fw + horizontal[index + 1]
        y += this_h + vertical[row_index + 1]
    return placements


def _frame_specs(n_frames, parity_profile, h, w, rng):
    odd_shapes = ((8, 9), (6, 7), (4, 5), (4, 3))
    even_shapes = ((9, 10), (7, 8), (5, 6), (3, 4))
    if parity_profile == "odd_only":
        parities = ["odd"] * n_frames
    elif parity_profile == "even_only":
        parities = ["even"] * n_frames
    else:
        start = rng.randrange(2)
        parities = ["odd" if (i + start) % 2 == 0 else "even"
                    for i in range(n_frames)]
        if "odd" not in parities:
            parities[0] = "odd"
        if "even" not in parities:
            parities[-1] = "even"

    for scale in range(len(odd_shapes)):
        specs = [odd_shapes[scale] if parity == "odd" else even_shapes[scale]
                 for parity in parities]
        orders = [
            specs,
            list(reversed(specs)),
            sorted(specs, key=lambda shape: shape[1]),
            sorted(specs, key=lambda shape: shape[1], reverse=True),
        ]
        for ordered in orders:
            placements = _pack_specs(ordered, h, w, rng)
            if placements is not None:
                return placements
    raise ValueError(
        f"could not pack {n_frames} frames in {h}x{w} for {parity_profile}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_mode = not overrides and sample_index % 3 == 0
    if canonical_mode:
        h0, w0, layout = _canonical_anchor(ctx, difficulty)
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n_frames = ctx.draw_int("n_frames", len(layout), len(layout))
        parity_profile = ctx.draw_choice("parity_profile", ["mixed"])
        del n_frames, parity_profile
        grid = full_grid(h, w, 0)
        for r, c, fh, fw in layout:
            draw_rect_outline(grid, r, c, fh, fw, 1)
        return grid

    if difficulty == "easy":
        h_lo, h_hi = 10, 14
        w_lo, w_hi = 10, 14
        n_lo, n_hi = 2, 3
    elif difficulty == "medium":
        h_lo, h_hi = 12, 18
        w_lo, w_hi = 12, 18
        n_lo, n_hi = 2, 4
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        w_lo, w_hi = 18, 22
        n_lo, n_hi = 3, 5
    else:
        h_lo, h_hi = 10, 22
        w_lo, w_hi = 10, 22
        n_lo, n_hi = 2, 5

    h = _draw_int_axis(ctx, overrides, "grid_h", h_lo, h_hi)
    w = _draw_int_axis(ctx, overrides, "grid_w", w_lo, w_hi)
    n_frames = _draw_int_axis(ctx, overrides, "n_frames", n_lo, n_hi)
    parity_profile = _draw_choice_axis(
        ctx, overrides, "parity_profile", ["mixed"], list(_PARITY_PROFILES)
    )

    placement_rng = ctx.draw_rng("frame_geometry")
    placements = _frame_specs(n_frames, parity_profile, h, w, placement_rng)
    colors = list(_BORDER_PALETTE)
    ctx.draw_rng("frame_palette").shuffle(colors)

    grid = full_grid(h, w, 0)
    for color, (r, c, fh, fw) in zip(colors, placements):
        draw_rect_outline(grid, r, c, fh, fw, color)
    return grid


def _same_color_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _frame_record(grid, color, cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    fh, fw = r2 - r1 + 1, c2 - c1 + 1
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    interior = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
    ]
    return {
        "color": color,
        "cells": set(cells),
        "border": border,
        "interior": interior,
        "bbox": (r1, c1, r2, c2),
        "frame_h": fh,
        "frame_w": fw,
        "interior_h": fh - 2,
        "interior_w": fw - 2,
        "is_exact_border": set(cells) == border,
        "interior_is_zero": all(grid[r][c] == 0 for r, c in interior),
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors = []
    facts: dict[str, Any] = {}
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"errors": ["grid must be a non-empty list of non-empty rows"], "facts": facts}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": facts}
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid contains a non-ARC colour value"], "facts": facts}

    height = len(grid)
    if not (10 <= height <= 22 and 10 <= width <= 22):
        errors.append(f"grid dimensions {height}x{width} outside 10..22")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background colour 0 is absent")

    frames = [
        _frame_record(grid, color, cells)
        for color, cells in _same_color_components(grid)
    ]
    if not 2 <= len(frames) <= 5:
        errors.append(f"expected 2..5 hollow frames, found {len(frames)}")
    for index, frame in enumerate(frames):
        if frame["color"] in (0, 2, 7):
            errors.append(
                f"frame {index} uses reserved background/output colour {frame['color']}"
            )
        if not frame["is_exact_border"]:
            errors.append(f"component {index} is not an exact rectangular border")
        if not frame["interior"]:
            errors.append(f"frame {index} has no interior")
        if not frame["interior_is_zero"]:
            errors.append(f"frame {index} interior is not empty in the input")
        if not 3 <= frame["frame_h"] <= 10 or not 3 <= frame["frame_w"] <= 10:
            errors.append(
                f"frame {index} dimensions {frame['frame_h']}x{frame['frame_w']} outside 3..10"
            )

    odd = sum(frame["interior_w"] % 2 == 1 for frame in frames)
    even = sum(frame["interior_w"] % 2 == 0 for frame in frames)
    if odd and even:
        parity_profile = "mixed"
    elif odd:
        parity_profile = "odd_only"
    elif even:
        parity_profile = "even_only"
    else:
        parity_profile = "none"
    changed_cells = sum(
        frame["interior_h"] * frame["interior_w"] for frame in frames
    )
    facts.update(
        grid_h=height,
        grid_w=width,
        frames=frames,
        n_frames=len(frames),
        parity_profile=parity_profile,
        odd_width_frames=odd,
        even_width_frames=even,
        odd_width_even_height=sum(
            frame["interior_w"] % 2 == 1 and frame["interior_h"] % 2 == 0
            for frame in frames
        ),
        even_width_odd_height=sum(
            frame["interior_w"] % 2 == 0 and frame["interior_h"] % 2 == 1
            for frame in frames
        ),
        border_colors=sorted({frame["color"] for frame in frames}),
        changed_cells=changed_cells,
        changed_fraction=changed_cells / (height * width),
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_frames": facts["n_frames"],
        "parity_profile": facts["parity_profile"],
    }


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    result = [row[:] for row in grid]
    for frame in analysis["facts"]["frames"]:
        fill = 7 if frame["interior_w"] % 2 else 2
        for r, c in frame["interior"]:
            result[r][c] = fill
    return result


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    facts = analysis["facts"]
    profile = (facts["grid_h"], facts["grid_w"], facts["n_frames"])
    if profile not in _CANONICAL_DIMS_COUNTS:
        reasons.append(f"profile {profile} is outside the canonical profile set")
    if facts["border_colors"] != [1]:
        reasons.append(f"canonical borders are blue (1), found {facts['border_colors']}")
    if facts["parity_profile"] != "mixed":
        reasons.append("canonical examples contain both odd and even interior widths")
    if any(frame["frame_h"] != frame["frame_w"] for frame in facts["frames"]):
        reasons.append("canonical frames are square")
    return reasons


def _witness(predicate: Callable[[dict[str, Any]], bool]):
    def check(grid):
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(predicate(analysis["facts"]))

    return check


SEMANTIC_WITNESSES = {
    "odd_interior_width_to_7": _witness(lambda facts: facts["odd_width_frames"] > 0),
    "even_interior_width_to_2": _witness(lambda facts: facts["even_width_frames"] > 0),
    "odd_width_even_height_discriminator": _witness(
        lambda facts: facts["odd_width_even_height"] > 0
    ),
    "even_width_odd_height_discriminator": _witness(
        lambda facts: facts["even_width_odd_height"] > 0
    ),
    "multiple_independent_frames": _witness(lambda facts: facts["n_frames"] >= 2),
    "border_colour_is_not_answer": _witness(
        lambda facts: any(color != 1 for color in facts["border_colors"])
    ),
}


def _rival_output(grid, rival):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    result = [row[:] for row in grid]
    for frame in analysis["facts"]["frames"]:
        if rival == "height_parity":
            fill = 7 if frame["interior_h"] % 2 else 2
        elif rival == "interior_area_parity":
            fill = 7 if (frame["interior_h"] * frame["interior_w"]) % 2 else 2
        elif rival == "always_7":
            fill = 7
        elif rival == "always_2":
            fill = 2
        elif rival == "border_colour_parity":
            fill = 7 if frame["color"] % 2 else 2
        else:
            raise ValueError(f"unknown rival {rival!r}")
        for r, c in frame["interior"]:
            result[r][c] = fill
    return result


LESSON_COMPETITORS = {
    name: (lambda grid, name=name: _rival_output(grid, name))
    for name in (
        "height_parity",
        "interior_area_parity",
        "always_7",
        "always_2",
        "border_colour_parity",
    )
}

# Canonical examples cannot distinguish width parity from height parity because
# every public frame is square.  This declared rival is paired with explicit
# generated witnesses below so the semantic gate can verify the rebuttal.
SEMANTIC_RIVALS = {"height_parity": LESSON_COMPETITORS["height_parity"]}
WITNESS_RIVALS = {
    "odd_width_even_height_discriminator": ["height_parity"],
    "even_width_odd_height_discriminator": ["height_parity"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for index, demo in enumerate(demos):
        analysis = _analyze(demo.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} is malformed: {'; '.join(analysis['errors'])}")
            continue
        if rule_mirror(demo["input"]) != demo.get("output"):
            reasons.append(f"demo {index} output does not match the selected width-parity rule")
    query_analysis = _analyze(query.get("input"))
    if query_analysis["errors"]:
        reasons.append(f"query is malformed: {'; '.join(query_analysis['errors'])}")
    if reasons:
        return reasons

    query_official = rule_mirror(query["input"])
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if survives and rival(query["input"]) != query_official:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_frames": facts["n_frames"],
        "parity_profile": facts["parity_profile"],
        "odd_width_frames": facts["odd_width_frames"],
        "even_width_frames": facts["even_width_frames"],
        "odd_width_even_height": facts["odd_width_even_height"],
        "even_width_odd_height": facts["even_width_odd_height"],
        "border_colors": facts["border_colors"],
        "changed_cells": facts["changed_cells"],
        "changed_fraction": round(facts["changed_fraction"], 6),
        "strict_canonical_like": not strict_canonical_like(grid),
    }
