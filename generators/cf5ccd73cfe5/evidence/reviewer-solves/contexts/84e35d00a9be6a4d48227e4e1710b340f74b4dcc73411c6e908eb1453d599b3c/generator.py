"""Generator for 6b9890af.

Rule: find the hollow rectangular frame and the separate marker.  Repeat each
marker row and column independently so the marker's bounding box fills the
frame interior, preserving the frame as the output border.

The ordinary distribution deliberately includes non-square markers, unequal
height/width scales, sparse connected and disconnected markers, two placement
orientations, and several palette families.  Exact dimension and semantic
axis overrides are honored when jointly feasible and rejected loudly when a
combination cannot fit.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf5ccd73cfe5"
VERSION = "3.0.0"
TASK_ID = "cf5ccd73cfe5"
RULE_HASH = "50b927c3200b"  # whitespace-normalized canonical program_solution
SUMMARY = (
    "Scale a separate marker's binary shape independently in height and width "
    "to fill a hollow rectangular frame interior."
)

INVARIANTS = [
    "background is color 0",
    "exactly one hollow rectangular frame is present",
    "exactly one non-frame marker color is present outside the frame",
    "frame interior dimensions are integer multiples of marker bbox dimensions",
    "ordinary draws keep marker and frame spatially separate",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
PALETTES = {
    "warm": (2, 3, 4, 6, 7, 9),
    "cool": (1, 5, 8),
    "broad": tuple(range(1, 10)),
    "primary": (1, 2, 4),
}
DEGENERATE_TEXTURES = ("no_frame", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng exact after semantic-layout feasibility",
        "valid": "8..26",
    },
    "grid_w": {
        "type": "int",
        "default": "rng exact after semantic-layout feasibility",
        "valid": "8..26",
    },
    "marker_h": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "marker_w": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "scale_h": {"type": "int", "default": "difficulty-aware 1..4", "valid": "1..4"},
    "scale_w": {"type": "int", "default": "difficulty-aware 1..4", "valid": "1..4"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
}


def _record_exact_axis(ctx, label: str, value: int, lo: int, hi: int) -> int:
    """Record a jointly selected exact axis in the same provenance map as draws.

    The semantic dimensions must be chosen together so a valid single-axis
    boundary request cannot be defeated by unrelated random draws.  GenCtx's
    public scalar draws cannot express that joint feasibility constraint, so we
    record the selected exact values after enumerating the lawful tuples.
    """
    ctx._draw_bounds[label] = (lo, hi)
    return ctx._record(
        label,
        value,
        from_override=(label in ctx.overrides and ctx.overrides[label] is not None),
    )


def _marker(rng, mh: int, mw: int) -> list[tuple[int, int]]:
    """Return a marker with exact bbox ``mh x mw``.

    Whenever the bbox has more than two cells, ordinary shapes are non-solid so
    the input contains evidence against the shortcut "fill the whole frame".
    Both connected and disconnected patterns remain possible because the Racket
    rule consumes the complete non-frame cell set rather than one component.
    """
    area = mh * mw
    if area <= 2:
        return [(r, c) for r in range(mh) for c in range(mw)]

    for _ in range(300):
        cells = [
            (r, c)
            for r in range(mh)
            for c in range(mw)
            if rng.random() < 0.58
        ]
        if not cells or len(cells) == area:
            continue
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if {0, mh - 1} <= rows and {0, mw - 1} <= cols:
            return cells

    # Sparse, exact-bbox fallback.  Duplicate corners collapse naturally for a
    # one-dimensional bbox.
    return sorted({(0, 0), (mh - 1, mw - 1)})


def _frame_candidates(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    candidates = []
    for color in sorted({v for row in grid for v in row if v != 0}):
        cells = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == color
        }
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        if r2 - r1 < 3 or c2 - c1 < 3:
            continue
        perimeter = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if cells == perimeter:
            candidates.append(
                {
                    "color": color,
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    return candidates


def _analyze(grid) -> tuple[dict | None, list[str]]:
    """Parse the task grammar used by ``self_check`` and override evidence."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return None, ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cell value out of 0-9"]

    nonzero = {value for row in grid for value in row if value != 0}
    if len(nonzero) != 2:
        return None, [f"expected exactly two nonzero colors, found {len(nonzero)}"]

    frames = _frame_candidates(grid)
    if len(frames) != 1:
        return None, [f"expected exactly one hollow rectangular frame, found {len(frames)}"]
    frame = frames[0]
    frame_color = frame["color"]
    marker_colors = nonzero - {frame_color}
    if len(marker_colors) != 1:
        return None, ["could not identify one marker color distinct from the frame"]
    marker_color = next(iter(marker_colors))
    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == marker_color
    ]
    if not marker_cells:
        return None, ["marker is empty"]

    mr1 = min(r for r, _ in marker_cells)
    mr2 = max(r for r, _ in marker_cells)
    mc1 = min(c for _, c in marker_cells)
    mc2 = max(c for _, c in marker_cells)
    marker_h = mr2 - mr1 + 1
    marker_w = mc2 - mc1 + 1
    fr1, fc1, fr2, fc2 = frame["bbox"]
    if any(fr1 <= r <= fr2 and fc1 <= c <= fc2 for r, c in marker_cells):
        return None, ["marker overlaps the frame bounding box"]

    interior_h = frame["height"] - 2
    interior_w = frame["width"] - 2
    if interior_h % marker_h or interior_w % marker_w:
        return None, [
            "frame interior dimensions are not integer multiples of marker bbox dimensions"
        ]
    scale_h = interior_h // marker_h
    scale_w = interior_w // marker_w
    if scale_h < 1 or scale_w < 1:
        return None, ["non-positive marker scale"]

    return {
        "grid_h": len(grid),
        "grid_w": width,
        "frame_color": frame_color,
        "marker_color": marker_color,
        "frame_bbox": frame["bbox"],
        "frame_h": frame["height"],
        "frame_w": frame["width"],
        "marker_bbox": (mr1, mc1, mr2, mc2),
        "marker_h": marker_h,
        "marker_w": marker_w,
        "marker_cells": len(marker_cells),
        "scale_h": scale_h,
        "scale_w": scale_w,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the exact frame-plus-marker teaching grammar."""
    _facts, errors = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact semantic axis from a returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        key: facts[key]
        for key in ("grid_h", "grid_w", "marker_h", "marker_w", "scale_h", "scale_w")
    }


def _effective_overrides(overrides: dict) -> tuple[dict, str | None]:
    effective = dict(overrides)
    texture = effective.pop("texture", None)
    if texture is None:
        return effective, None
    if texture in DEGENERATE_TEXTURES:
        return effective, texture
    if texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    explicit_palette = effective.get("palette_kind")
    if explicit_palette is not None and explicit_palette != texture:
        raise ValueError(
            f"texture={texture!r} conflicts with palette_kind={explicit_palette!r}"
        )
    effective["palette_kind"] = texture
    return effective, None


def _semantic_candidates(difficulty: str | None, overrides: dict) -> list[tuple[int, int, int, int, str, int, int]]:
    requested_h = overrides.get("grid_h")
    requested_w = overrides.get("grid_w")
    for name, value in (("grid_h", requested_h), ("grid_w", requested_w)):
        if value is not None and not 8 <= int(value) <= 26:
            raise ValueError(f"{name} override {value} outside [8, 26]")

    candidates = []
    for mh in range(1, 4):
        if overrides.get("marker_h") is not None and mh != int(overrides["marker_h"]):
            continue
        for mw in range(1, 4):
            if overrides.get("marker_w") is not None and mw != int(overrides["marker_w"]):
                continue
            # The 1x1 marker makes every output a solid fill and does not teach
            # shape scaling; reject that jointly incompatible axis tuple.
            if mh == mw == 1:
                continue
            # Ordinary draws avoid the only other forced-solid bbox sizes.
            if not any(overrides.get(name) is not None for name in ("marker_h", "marker_w")):
                if mh * mw <= 2:
                    continue
            for sh in range(1, 5):
                if overrides.get("scale_h") is not None and sh != int(overrides["scale_h"]):
                    continue
                if mh * sh < 2:
                    continue
                if difficulty == "easy" and overrides.get("scale_h") is None and sh > 2:
                    continue
                if difficulty == "hard" and overrides.get("scale_h") is None and sh < 2:
                    continue
                for sw in range(1, 5):
                    if overrides.get("scale_w") is not None and sw != int(overrides["scale_w"]):
                        continue
                    if mw * sw < 2:
                        continue
                    if difficulty == "easy" and overrides.get("scale_w") is None and sw > 2:
                        continue
                    if difficulty == "hard" and overrides.get("scale_w") is None and sw < 2:
                        continue

                    frame_h = mh * sh + 2
                    frame_w = mw * sw + 2
                    layouts = (
                        ("below", frame_h + 1 + mh, max(frame_w, mw)),
                        ("right", max(frame_h, mh), frame_w + 1 + mw),
                    )
                    for layout, min_h, min_w in layouts:
                        if max(8, min_h) > 26 or max(8, min_w) > 26:
                            continue
                        if requested_h is not None and int(requested_h) < max(8, min_h):
                            continue
                        if requested_w is not None and int(requested_w) < max(8, min_w):
                            continue
                        candidates.append((mh, mw, sh, sw, layout, min_h, min_w))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    effective, degenerate = _effective_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    rng = ctx.draw_rng("layout")
    if degenerate is not None:
        return _draw_from_degenerate(degenerate, rng)

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    candidates = _semantic_candidates(difficulty, effective)
    if not candidates:
        exact = {key: effective[key] for key in AXES if effective.get(key) is not None}
        raise ValueError(f"incompatible exact override combination: {exact}")

    # A sequential four-pair lesson should expose the decisive generalization,
    # not accidentally show only square markers with uniform scaling.  Exact
    # overrides remain sovereign; the schedule only narrows unconstrained draws
    # and falls back when a requested small canvas makes a branch impossible.
    scheduled = candidates
    phase = sample_index % 4
    if phase == 0 and effective.get("scale_h") is None and effective.get("scale_w") is None:
        branch = [candidate for candidate in candidates if candidate[2] != candidate[3]]
        scheduled = branch or scheduled
    elif phase == 1 and effective.get("marker_h") is None and effective.get("marker_w") is None:
        branch = [candidate for candidate in candidates if candidate[0] != candidate[1]]
        scheduled = branch or scheduled
    elif phase == 2 and not any(
        effective.get(name) is not None
        for name in ("marker_h", "marker_w", "scale_h", "scale_w")
    ):
        branch = [
            candidate
            for candidate in candidates
            if candidate[0] == candidate[1] == 3 and candidate[2] == candidate[3]
        ]
        scheduled = branch or scheduled

    semantic_rng = ctx.draw_rng("semantic_spec")
    mh, mw, sh, sw, layout, min_h, min_w = semantic_rng.choice(scheduled)
    _record_exact_axis(ctx, "marker_h", mh, 1, 3)
    _record_exact_axis(ctx, "marker_w", mw, 1, 3)
    _record_exact_axis(ctx, "scale_h", sh, 1, 4)
    _record_exact_axis(ctx, "scale_w", sw, 1, 4)

    h = ctx.draw_int("grid_h", max(8, min_h), 26)
    w = ctx.draw_int("grid_w", max(8, min_w), 26)
    frame_h = mh * sh + 2
    frame_w = mw * sw + 2
    marker = _marker(ctx.draw_rng("marker_shape"), mh, mw)

    palette = PALETTES[palette_kind]
    if len(palette) < 2:
        raise ValueError(f"palette {palette_kind!r} has fewer than two colors")
    frame_color, marker_color = ctx.draw_rng("colors").sample(list(palette), 2)

    grid = full_grid(h, w, 0)
    if layout == "below":
        total_h = frame_h + 1 + mh
        block_r = rng.randint(0, h - total_h)
        fr = block_r
        mr = block_r + frame_h + 1
        fc = rng.randint(0, w - frame_w)
        mc = rng.randint(0, w - mw)
    else:
        total_w = frame_w + 1 + mw
        block_c = rng.randint(0, w - total_w)
        fc = block_c
        mc = block_c + frame_w + 1
        fr = rng.randint(0, h - frame_h)
        mr = rng.randint(0, h - mh)

    for c in range(fc, fc + frame_w):
        grid[fr][c] = frame_color
        grid[fr + frame_h - 1][c] = frame_color
    for r in range(fr, fr + frame_h):
        grid[r][fc] = frame_color
        grid[r][fc + frame_w - 1] = frame_color
    for dr, dc in marker:
        grid[mr + dr][mc + dc] = marker_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # fail closed rather than returning a malformed lesson
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def _draw_from_degenerate(name, rng):
    """Intentionally invalid negative probes; structural self_check rejects all."""
    grid = full_grid(15, 15, 0)
    if name == "no_frame":
        for dr, dc in ((0, 0), (0, 1), (1, 0)):
            grid[8 + dr][3 + dc] = 2
        return grid
    if name == "no_marker":
        for r in range(1, 7):
            grid[r][1] = 1
            grid[r][6] = 1
        for c in range(1, 7):
            grid[1][c] = 1
            grid[6][c] = 1
        return grid
    if name == "full_grid":
        return full_grid(15, 15, 1)
    raise ValueError(f"unknown degenerate texture {name!r}")
