"""Canonical-anchored generator for ARC task 985ae207 / hash 9fd3271f703a.

Selected rule
-------------
Every 3x3 motif is a uniform ring with a different centre colour.  For each
motif, find connected objects of that centre colour outside the motif that
share either its three-row band or its three-column band.  Choose the nearest
candidate (ties by top row, then left column).  Paint a three-cell-wide corridor
from the motif toward the selected object through the object's near edge, using
the ring colour, then restore the centre colour every third cell along the
corridor centreline.  Horizontal alignment wins if a candidate overlaps both
bands.  All motifs are processed in row-major order against the original input.

The public ARC examples are not single-motif black-background scenes: they use
2--5 motifs, all four directions, large partner objects, shared partners, modal
background colour 8, and 4/5/6-colour 20x20 or 25x25 canvases.  This generator
keeps every normal draw on those linked size/palette profiles while using
palette permutations and positional jitter for lawful augmentation.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9fd3271f703a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"  # canonical-anchored multi-motif curriculum + exact override contract
RULE_HASH = "0e06c889bcd4"

SUMMARY = (
    "On a modal-background square canvas, find every 3x3 uniform ring with a "
    "distinct centre.  Connect each motif toward the nearest separate object "
    "of its centre colour that overlaps the motif's row-band or column-band; "
    "paint a ring-colour 3-wide corridor and repeat the centre marker every "
    "third cell along its middle line.  Multiple motifs, all four directions, "
    "shared partners, and same-colour candidate distractors are represented."
)

INVARIANTS = [
    "grid profile is one of the canonical 20x20/4-colour, 20x20/5-colour, or 25x25/6-colour profiles",
    "all motifs use one common ring colour distinct from the modal background and every centre colour",
    "every motif has at least one separated same-centre-colour candidate overlapping its row-band or column-band",
    "ordinary four-example windows contain horizontal, vertical, nearest-candidate, and shared-partner controls",
    "palette profile, scale profile, and scene profile are exactly recoverable from the returned grid",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCALE_PROFILES = ("compact4", "canonical5", "expanded6")
SCENE_PROFILES = ("horizontal_both", "vertical_both", "nearest_control", "shared_partner")
PALETTE_PROFILES = ("bg8", "bg0", "bg5")
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scale_profile": {
        "type": "str",
        "default": "compact4/easy, canonical5/medium, expanded6/hard",
        "valid": "|".join(SCALE_PROFILES),
    },
    "scene_profile": {
        "type": "str",
        "default": "cyclic horizontal/vertical/nearest/shared by sample_index",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_profile": {
        "type": "str",
        "default": "scheduled bg8/bg0/bg5 palette permutations",
        "valid": "|".join(PALETTE_PROFILES),
    },
}

_SCALE = {
    "compact4": (20, 2),   # background + ring + 2 centre colours = 4
    "canonical5": (20, 3), # background + ring + 3 centre colours = 5
    "expanded6": (25, 4),  # background + ring + 4 centre colours = 6
}
_BG = {"bg8": 8, "bg0": 0, "bg5": 5}
_BG_PROFILE = {v: k for k, v in _BG.items()}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Four consecutive sample indices cover every decisive scene profile."""
    _band(difficulty)
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _scheduled_scale(band: str) -> str:
    return {"easy": "compact4", "medium": "canonical5", "hard": "expanded6"}[band]


def _scheduled_palette(seed: int, sample_index: int) -> str:
    # Every short run contains canonical background 8 while still proving that
    # the selected rule is colour-relational rather than colour-literal.
    return PALETTE_PROFILES[(int(seed) + sample_index) % len(PALETTE_PROFILES)]


def _draw_axis(ctx, overrides: dict[str, Any], name: str, scheduled: str, values: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, list(values))
    return ctx.draw_choice(name, [scheduled])


def _rect_cells(r1: int, c1: int, r2: int, c2: int):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            yield r, c


def _paint_rect(grid: list[list[int]], box: tuple[int, int, int, int], color: int) -> None:
    h, w = len(grid), len(grid[0])
    r1, c1, r2, c2 = box
    if not (0 <= r1 <= r2 < h and 0 <= c1 <= c2 < w):
        raise ValueError(f"rectangle outside grid: {box}")
    for r, c in _rect_cells(*box):
        if grid[r][c] != _modal_background(grid):
            raise ValueError(f"rectangle collision at {(r, c)}")
    for r, c in _rect_cells(*box):
        grid[r][c] = color


def _paint_motif(grid: list[list[int]], r: int, c: int, ring: int, centre: int) -> None:
    h, w = len(grid), len(grid[0])
    if not (0 <= r <= h - 3 and 0 <= c <= w - 3):
        raise ValueError(f"motif outside grid: {(r, c)}")
    bg = _modal_background(grid)
    for rr in range(r, r + 3):
        for cc in range(c, c + 3):
            if grid[rr][cc] != bg:
                raise ValueError(f"motif collision at {(rr, cc)}")
    for rr in range(r, r + 3):
        for cc in range(c, c + 3):
            grid[rr][cc] = ring
    grid[r + 1][c + 1] = centre


def _horizontal_layout(size: int, centres: list[int], ring: int, bg: int, rng) -> list[list[int]]:
    g = full_grid(size, size, bg)
    n = len(centres)
    rows = ([4, 12] if n == 2 else [3, 9, 15] if n == 3 else [3, 8, 13, 18])
    for i, (base_r, centre) in enumerate(zip(rows, centres)):
        r = max(1, min(size - 4, base_r + rng.choice((-1, 0, 1))))
        if i % 2 == 0:  # left partner
            c = 6 + rng.choice((0, 1))
            span = (max(0, r - 2), 0, min(size - 1, r + 5), 2)
        else:  # right partner
            c = size - 9 + rng.choice((0, 1))
            span = (max(0, r - 2), size - 3, min(size - 1, r + 5), size - 1)
        _paint_rect(g, span, centre)
        _paint_motif(g, r, c, ring, centre)
    return g


def _vertical_layout(size: int, centres: list[int], ring: int, bg: int, rng) -> list[list[int]]:
    g = full_grid(size, size, bg)
    n = len(centres)
    cols = ([4, 12] if n == 2 else [3, 9, 15] if n == 3 else [3, 8, 13, 18])
    for i, (base_c, centre) in enumerate(zip(cols, centres)):
        c = max(1, min(size - 4, base_c + rng.choice((-1, 0, 1))))
        if i % 2 == 0:  # top partner
            r = 6 + rng.choice((0, 1))
            span = (0, max(0, c - 2), 2, min(size - 1, c + 5))
        else:  # bottom partner
            r = size - 9 + rng.choice((0, 1))
            span = (size - 3, max(0, c - 2), size - 1, min(size - 1, c + 5))
        _paint_rect(g, span, centre)
        _paint_motif(g, r, c, ring, centre)
    return g


def _nearest_layout(size: int, centres: list[int], ring: int, bg: int, rng) -> list[list[int]]:
    g = full_grid(size, size, bg)
    if size == 20:
        mr = 8 + rng.choice((-1, 0, 1)); mc = 8 + rng.choice((-1, 0, 1))
        near_gap = rng.choice((2, 3))
        near_c1 = mc + 3 + near_gap
        _paint_rect(g, (mr - 1, near_c1, mr + 3, min(size - 1, near_c1 + 2)), centres[0])
        _paint_rect(g, (mr - 2, 0, mr + 4, 2), centres[0])
        _paint_motif(g, mr, mc, ring, centres[0])
        # Keep the extra motifs on vertical lanes.  The old right-edge extras
        # could collide with the deliberately jittered near candidate, which
        # made some legal override combinations seed-dependent.
        extras = [
            (3 + rng.choice((0, 1)), 4 + rng.choice((0, 1)), "up"),
            (13 + rng.choice((0, 1)), 4 + rng.choice((0, 1)), "down"),
        ]
    else:
        mr = 10 + rng.choice((-1, 0, 1)); mc = 10 + rng.choice((-1, 0, 1))
        near_gap = rng.choice((2, 3))
        near_c1 = mc + 3 + near_gap
        _paint_rect(g, (mr - 1, near_c1, mr + 3, near_c1 + 2), centres[0])
        _paint_rect(g, (mr - 2, 0, mr + 4, 2), centres[0])
        _paint_motif(g, mr, mc, ring, centres[0])
        extras = [
            (3 + rng.choice((0, 1)), 4 + rng.choice((0, 1)), "up"),
            (18 + rng.choice((0, 1)), 4 + rng.choice((0, 1)), "down"),
            (18 + rng.choice((0, 1)), 17 + rng.choice((0, 1)), "down"),
        ]
    for centre, (r, c, direction) in zip(centres[1:], extras):
        if direction == "left":
            box = (max(0, r - 1), 0, min(size - 1, r + 4), 1)
        elif direction == "right":
            box = (max(0, r - 1), size - 3, min(size - 1, r + 4), size - 1)
        elif direction == "up":
            box = (0, max(0, c - 1), 1, min(size - 1, c + 3))
        elif direction == "down":
            box = (size - 2, max(0, c - 1), size - 1, min(size - 1, c + 3))
        else:  # pragma: no cover - layout templates are fixed above
            raise AssertionError(direction)
        _paint_rect(g, box, centre)
        _paint_motif(g, r, c, ring, centre)
    return g


def _shared_layout(size: int, centres: list[int], ring: int, bg: int, rng) -> list[list[int]]:
    g = full_grid(size, size, bg)
    if size == 20:
        # One large right-side object is the selected partner for two non-aligned
        # motifs of centre colour 0.  Its 36 cells also anchors the canonical
        # large-object distribution missing from the old generator.
        _paint_rect(g, (3, 17, 14, 19), centres[0])
        a = (4 + rng.choice((0, 1)), 7 + rng.choice((0, 1)))
        b = (11 + rng.choice((0, 1)), 11 + rng.choice((0, 1)))
        _paint_motif(g, *a, ring, centres[0])
        _paint_motif(g, *b, ring, centres[0])
        extra_specs = [
            (1, 2, (6, 1, 8, 5), "down"),
            (15, 3, (10, 2, 12, 6), "up"),
        ]
    else:
        # 3 x 16 = 48 cells: deliberately spans the canonical max-object median.
        _paint_rect(g, (3, 22, 18, 24), centres[0])
        a = (5 + rng.choice((0, 1)), 9 + rng.choice((0, 1)))
        b = (14 + rng.choice((0, 1)), 14 + rng.choice((0, 1)))
        _paint_motif(g, *a, ring, centres[0])
        _paint_motif(g, *b, ring, centres[0])
        extra_specs = [
            (2, 4, (1, 0, 6, 1), "left"),
            (10, 4, (9, 0, 14, 1), "left"),
            (20, 7, (19, 1, 24, 3), "left"),
        ]
    for centre, (base_r, base_c, box, _direction) in zip(centres[1:], extra_specs):
        r = base_r + rng.choice((0, 1))
        c = base_c + rng.choice((0, 1))
        _paint_rect(g, box, centre)
        _paint_motif(g, r, c, ring, centre)
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scale_profile = _draw_axis(ctx, overrides, "scale_profile", _scheduled_scale(band), SCALE_PROFILES)
    scene_profile = _draw_axis(ctx, overrides, "scene_profile", schedule_profile(seed, sample_index, band), SCENE_PROFILES)
    palette_profile = _draw_axis(ctx, overrides, "palette_profile", _scheduled_palette(seed, sample_index), PALETTE_PROFILES)

    size, n_centres = _SCALE[scale_profile]
    bg = _BG[palette_profile]
    color_rng = ctx.draw_rng("colors")
    chosen = color_rng.sample([c for c in range(10) if c != bg], n_centres + 1)
    ring, centres = chosen[0], chosen[1:]
    layout_rng = ctx.draw_rng("layout")

    if scene_profile == "horizontal_both":
        grid = _horizontal_layout(size, centres, ring, bg, layout_rng)
    elif scene_profile == "vertical_both":
        grid = _vertical_layout(size, centres, ring, bg, layout_rng)
    elif scene_profile == "nearest_control":
        grid = _nearest_layout(size, centres, ring, bg, layout_rng)
    elif scene_profile == "shared_partner":
        grid = _shared_layout(size, centres, ring, bg, layout_rng)
    else:  # defensive; draw_choice already validates the domain
        raise ValueError(f"unknown scene profile: {scene_profile!r}")

    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError("generator produced invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "scale_profile": scale_profile,
        "scene_profile": scene_profile,
        "palette_profile": palette_profile,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization drift: expected={expected}, observed={observed}")
    return grid


# ---------------------------------------------------------------------------
# Structural analysis: mirrors the selected Racket authority closely enough to
# power self-checks, semantic witnesses, executable competitors, and tests.
# ---------------------------------------------------------------------------

def _validate_grid(grid: Any) -> tuple[list[list[int]], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid is empty or not a row sequence"]
    rows = [list(row) if isinstance(row, (list, tuple)) else [] for row in grid]
    if any(not row for row in rows):
        return rows, ["grid contains an empty/non-sequence row"]
    w = len(rows[0])
    if any(len(row) != w for row in rows):
        errors.append("grid is ragged")
    bad = [(r, c, v) for r, row in enumerate(rows) for c, v in enumerate(row)
           if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9]
    if bad:
        errors.append(f"grid contains non-ARC cell {bad[0]}")
    return rows, errors


def _modal_background(grid: list[list[int]]) -> int:
    counts = Counter(v for row in grid for v in row)
    return counts.most_common(1)[0][0]


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)]); seen.add((r, c)); cells: list[tuple[int, int]] = []
            while q:
                rr, cc = q.popleft(); cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _overlap(a1: int, a2: int, b1: int, b2: int) -> bool:
    return max(a1, b1) <= min(a2, b2)


def _gap(box: tuple[int, int, int, int], mr: int, mc: int) -> int:
    r1, c1, r2, c2 = box
    return max(0, c1 - (mc + 2), mc - c2) + max(0, r1 - (mr + 2), mr - r2)


def _motif_rows(grid: list[list[int]], bg: int):
    h, w = len(grid), len(grid[0])
    motifs = []
    for r in range(h - 2):
        for c in range(w - 2):
            ring = [grid[r + dr][c + dc] for dr in range(3) for dc in range(3) if (dr, dc) != (1, 1)]
            outer = ring[0]; centre = grid[r + 1][c + 1]
            if outer != bg and centre != bg and outer != centre and all(v == outer for v in ring):
                motifs.append({"r": r, "c": c, "ring": outer, "centre": centre})
    return motifs


def _candidate_rows(grid: list[list[int]], motif: dict[str, Any]):
    mr, mc, centre = motif["r"], motif["c"], motif["centre"]
    rows = []
    for cells in _components(grid, centre):
        box = _bbox(cells); r1, c1, r2, c2 = box
        inside = all(mr <= r <= mr + 2 and mc <= c <= mc + 2 for r, c in cells)
        if inside:
            continue
        row_overlap = _overlap(r1, r2, mr, mr + 2)
        col_overlap = _overlap(c1, c2, mc, mc + 2)
        if not (row_overlap or col_overlap):
            continue
        direction = (
            "left" if row_overlap and c2 < mc else
            "right" if row_overlap and c1 > mc + 2 else
            "up" if (not row_overlap) and r2 < mr else
            "down" if (not row_overlap) and r1 > mr + 2 else
            "overlap"
        )
        rows.append({
            "box": box,
            "cells": cells,
            "size": len(cells),
            "gap": _gap(box, mr, mc),
            "row_overlap": row_overlap,
            "col_overlap": col_overlap,
            "direction": direction,
        })
    rows.sort(key=lambda row: (row["gap"], row["box"][0], row["box"][1]))
    return rows


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    rows, errors = _validate_grid(grid)
    if errors:
        return {"grid": rows}, errors
    h, w = len(rows), len(rows[0]); bg = _modal_background(rows)
    counts = Counter(v for row in rows for v in row)
    if list(counts.values()).count(counts[bg]) > 1:
        errors.append("background mode is tied")
    motifs = _motif_rows(rows, bg)
    if not motifs:
        errors.append("no 3x3 uniform-ring/distinct-centre motif")
    ring_colors = {m["ring"] for m in motifs}
    if len(ring_colors) != 1:
        errors.append(f"motifs do not share one ring colour: {sorted(ring_colors)}")
    if not (2 <= len(motifs) <= 5):
        errors.append(f"motif count {len(motifs)} outside canonical 2..5")

    selected_keys: list[tuple[int, tuple[int, int, int, int]]] = []
    for motif in motifs:
        candidates = _candidate_rows(rows, motif)
        motif["candidates"] = candidates
        motif["selected"] = candidates[0] if candidates else None
        if not candidates:
            errors.append(f"motif at {(motif['r'], motif['c'])} has no aligned same-centre partner")
            continue
        selected = candidates[0]
        if selected["gap"] < 2:
            errors.append(f"motif at {(motif['r'], motif['c'])} is not visibly separated from its partner")
        if selected["direction"] not in {"left", "right", "up", "down"}:
            errors.append(f"motif at {(motif['r'], motif['c'])} has ambiguous partner geometry")
        if selected["size"] < 8:
            errors.append(f"partner for motif {(motif['r'], motif['c'])} is too small ({selected['size']} cells)")
        selected_keys.append((motif["centre"], selected["box"]))

    colors = set(counts)
    centre_colors = {m["centre"] for m in motifs}
    expected_colors = {bg} | ring_colors | centre_colors
    if colors != expected_colors:
        errors.append(f"palette contains non-role colours: actual={sorted(colors)} roles={sorted(expected_colors)}")

    info = {
        "grid": rows, "h": h, "w": w, "bg": bg, "palette": tuple(sorted(colors)),
        "motifs": motifs, "ring_colors": ring_colors, "centre_colors": centre_colors,
        "selected_keys": selected_keys,
    }
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile_key = (info["h"], info["w"], len(info["palette"]))
    scale_lookup = {(20, 20, 4): "compact4", (20, 20, 5): "canonical5", (25, 25, 6): "expanded6"}
    if profile_key not in scale_lookup:
        raise ValueError(f"unrecognized scale profile {profile_key}")
    palette_profile = _BG_PROFILE.get(info["bg"])
    if palette_profile is None:
        raise ValueError(f"unrecognized palette profile background {info['bg']}")

    motifs = info["motifs"]
    if any(len(m["candidates"]) >= 2 for m in motifs):
        scene = "nearest_control"
    elif len(set(info["selected_keys"])) < len(info["selected_keys"]):
        scene = "shared_partner"
    else:
        directions = {m["selected"]["direction"] for m in motifs if m["selected"]}
        if directions <= {"left", "right"} and {"left", "right"} <= directions:
            scene = "horizontal_both"
        elif directions <= {"up", "down"} and {"up", "down"} <= directions:
            scene = "vertical_both"
        else:
            raise ValueError(f"scene profile is not exactly observable from directions {sorted(directions)}")
    return {"scale_profile": scale_lookup[profile_key], "scene_profile": scene, "palette_profile": palette_profile}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    _band(difficulty)
    info, errors = _analyse(grid)
    if errors:
        return list(dict.fromkeys(errors))
    # Canonical-linked envelope. Palette permutations are lawful, but linked
    # size/palette counts remain exact.
    if (info["h"], info["w"], len(info["palette"])) not in {(20, 20, 4), (20, 20, 5), (25, 25, 6)}:
        errors.append("grid does not match a canonical linked size/palette profile")
    return list(dict.fromkeys(errors))


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


# ---------------------------------------------------------------------------
# Python mirror + rivals. These are evidence helpers only; the Racket rule
# remains the output authority used by the runner and materializer.
# ---------------------------------------------------------------------------

def _paint_selected(out, motif, selected):
    h, w = len(out), len(out[0]); mr, mc = motif["r"], motif["c"]
    ring, centre = motif["ring"], motif["centre"]
    r1, c1, r2, c2 = selected["box"]
    if selected["row_overlap"]:
        start = max(0, c2 - 1) if c2 < mc else mc
        end = min(w - 1, c1 + 1) if c1 > mc + 2 else mc + 2
        for r in range(mr, mr + 3):
            for c in range(start, end + 1):
                out[r][c] = ring
        for c in range(start, end + 1):
            if (c - (mc + 1)) % 3 == 0:
                out[mr + 1][c] = centre
    else:
        start = max(0, r2 - 1) if r2 < mr else mr
        end = min(h - 1, r1 + 1) if r1 > mr + 2 else mr + 2
        for r in range(start, end + 1):
            for c in range(mc, mc + 3):
                out[r][c] = ring
        for r in range(start, end + 1):
            if (r - (mr + 1)) % 3 == 0:
                out[r][mc + 1] = centre


def _render_with_selector(grid: Any, selector: Callable[[dict[str, Any]], dict[str, Any] | None], *, first_only=False, right_down_only=False):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(info["grid"])
    motifs = info["motifs"][:1] if first_only else info["motifs"]
    for motif in motifs:
        selected = selector(motif)
        if selected is None:
            continue
        if right_down_only and selected["direction"] in {"left", "up"}:
            continue
        _paint_selected(out, motif, selected)
    return out


def rule_mirror(grid: Any):
    return _render_with_selector(grid, lambda m: m["candidates"][0] if m["candidates"] else None)


def _rival_first_aligned_same_color(grid: Any):
    def selector(m):
        return min(m["candidates"], key=lambda x: (x["box"][0], x["box"][1])) if m["candidates"] else None
    return _render_with_selector(grid, selector)


def _rival_farthest_same_color(grid: Any):
    def selector(m):
        return max(m["candidates"], key=lambda x: (x["gap"], -x["box"][0], -x["box"][1])) if m["candidates"] else None
    return _render_with_selector(grid, selector)


def _rival_first_motif_only(grid: Any):
    return _render_with_selector(grid, lambda m: m["candidates"][0], first_only=True)


def _rival_right_down_only(grid: Any):
    return _render_with_selector(grid, lambda m: m["candidates"][0], right_down_only=True)


def _directions(grid: Any) -> set[str]:
    info, errors = _analyse(grid)
    return set() if errors else {m["selected"]["direction"] for m in info["motifs"] if m["selected"]}


def _witness_direction(name: str):
    return lambda grid: name in _directions(grid)


def _witness_multiple(grid: Any) -> bool:
    info, errors = _analyse(grid); return not errors and len(info["motifs"]) >= 2


def _witness_nearest(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(len(m["candidates"]) >= 2 and m["candidates"][0]["gap"] < m["candidates"][-1]["gap"] for m in info["motifs"])


def _witness_shared(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and len(set(info["selected_keys"])) < len(info["selected_keys"])


def _witness_position_variation(grid: Any) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(m["r"] not in {3, 7, 12, 15} or m["c"] not in {3, 7, 12, 15} for m in info["motifs"])


SEMANTIC_WITNESSES = {
    "connects_left": _witness_direction("left"),
    "connects_right": _witness_direction("right"),
    "connects_up": _witness_direction("up"),
    "connects_down": _witness_direction("down"),
    "multiple_motifs_processed": _witness_multiple,
    "nearest_same_color_candidate_selected": _witness_nearest,
    "multiple_motifs_can_share_one_partner": _witness_shared,
    "positions_are_not_fixed_to_canonical_slots": _witness_position_variation,
}

SEMANTIC_RIVALS = {
    "first_aligned_same_color": _rival_first_aligned_same_color,
    "farthest_same_color": _rival_farthest_same_color,
    "first_motif_only": _rival_first_motif_only,
    "right_and_down_only": _rival_right_down_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every public motif has only one same-colour aligned candidate, so both
    # shortcuts fit canonical. nearest_control is the generated discriminator.
    "first_aligned_same_color": _rival_first_aligned_same_color,
    "farthest_same_color": _rival_farthest_same_color,
}
WITNESS_RIVALS = {
    "connects_left": ["right_and_down_only"],
    "connects_right": ["first_motif_only"],
    "connects_up": ["right_and_down_only"],
    "connects_down": ["first_motif_only"],
    "multiple_motifs_processed": ["first_motif_only"],
    "nearest_same_color_candidate_selected": ["first_aligned_same_color", "farthest_same_color"],
    "multiple_motifs_can_share_one_partner": ["first_motif_only"],
    "positions_are_not_fixed_to_canonical_slots": ["first_motif_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    profiles: set[str] = set()
    for i, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {i} is not an input/output pair"); continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {i} malformed: {errors[0]}"); continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {i} output disagrees with the selected authority mirror")
        profiles.add(observe_overrides(pair["input"])["scene_profile"])
    missing = set(SCENE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations miss scene profiles: {sorted(missing)}")

    # A lesson is only called identifiable when each named plausible rival is
    # explicitly refuted by at least one demonstration.
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos if isinstance(pair, dict) and "input" in pair and "output" in pair):
            reasons.append(f"competitor survives all demos: {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qerr = strict_canonical_like(query["input"])
        if qerr:
            reasons.append(f"query malformed: {qerr[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the selected authority mirror")
    return reasons
