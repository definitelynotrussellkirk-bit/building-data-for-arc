"""Generator for arc_puzzle_bank_21_set14_bundle:hard_n07.

Rule: color-8 hollow frames and loose monochrome objects share one canvas.
Each frame has a distinct interior area, and each loose object has a distinct
cell count matching exactly one frame area.  The oracle redraws the frames on
blank background, clears the loose objects, and pastes each object's bounding
box at the centered position of its area-matched frame.  Cells outside the
frame interior are clipped; this clipping is answer-bearing in the canonical
examples, not an error to remove.

The official task has four linked input profiles.  They couple canvas size,
all frame interior dimensions, and all loose-object morphologies.  Default
sampling is a deterministic sample_index schedule: ``sample_index % 4 == 3``
draws reproduce a complete canonical profile (25% overall, the same rate as
the earlier 50%-of-odd random prior), ``sample_index % 4 == 1`` draws are
generalized CLIP draws, and even draws are generalized fit draws.  Every
generalized clip draw is discriminative by construction: its clipped pair is
simultaneously non-rectangular (bbox area != cell count) and pasted at a
nonzero centered offset, so a single such scene refutes bbox-area matching,
top-left pasting, and clipping-skip.  A fit pair can never do that — an
object whose cell count equals its frame's interior area and whose bbox fits
the interior necessarily FILLS the interior exactly (offset 0, rectangular) —
and canonical profiles 0/1 carry no nonzero offset either, which is why the
discriminative scenes are pinned to their own schedule slot inside every
EXAMPLES_NEEDED=3 demo window.  Every ordinary draw contains a nearest-frame
counterexample so spatial proximity cannot replace area matching.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c4ad042d2888"
TASK_ID = "c4ad042d2888"
RULE_HASH = "b25ab4b366b7"
VERSION = "2.1.0"  # deterministic schedule: discriminative clip slot at %4==1
EXAMPLES_NEEDED = 3  # indices 0,1,2 = fit, discriminative clip, fit demos

SUMMARY = (
    "2-3 distinct-area hollow color-8 frames and equally many distinct-color "
    "objects whose cell counts match those areas; center each matched object's "
    "bounding box in its frame and clip cells outside the interior."
)

INVARIANTS = [
    "background is 0 and every color-8 component is an exact hollow rectangle",
    "there are 2-3 frames with pairwise-distinct interior areas",
    "there are equally many monochrome non-{0,8} objects in distinct colors",
    "the multiset of object cell counts exactly equals the frame-area multiset",
    "no loose object starts inside a frame bounding box",
    "at least one object is closer to a wrong-area frame than to its match",
    "generalized clip draws (sample_index % 4 == 1) pair a non-rectangular "
    "clipped object with a nonzero centered paste offset, refuting bbox-area "
    "matching and top-left pasting within the scene",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 12..13 easy, 12..15 medium, 14..18 hard; "
        "canonical-prior draws pin 12..13",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 16..17 easy, 16..19 medium, 18..22 hard; "
        "canonical-prior draws pin 16..17",
        "valid": "16..22",
    },
    "n_pairs": {
        "type": "int",
        "default": "2 easy, rng 2..3 medium, 3 hard; canonical-prior draws 3",
        "valid": "2..3",
    },
    "clip_mode": {
        "type": "bool",
        "default": "alternates by sample_index; canonical-prior draws true",
        "valid": "true|false",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful; canonical-prior draws warm",
        "valid": "default|warm|cool|varied",
    },
    "texture": {
        "type": "str",
        "default": "alias for palette_kind",
        "valid": "default|warm|cool|varied",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

H_DOMINO = ((0, 0), (0, 1))
V_DOMINO = ((0, 0), (1, 0))
H_LINE_3 = ((0, 0), (0, 1), (0, 2))
V_LINE_3 = ((0, 0), (1, 0), (2, 0))
L_TRIOMINO = ((0, 0), (1, 0), (1, 1))
L_TRIOMINO_MIRROR = ((0, 1), (1, 0), (1, 1))
SQUARE_2X2 = ((0, 0), (0, 1), (1, 0), (1, 1))
T_TETROMINO = ((0, 0), (0, 1), (0, 2), (1, 1))
T_TETROMINO_DOWN = ((0, 1), (1, 0), (1, 1), (1, 2))
H_LINE_4 = ((0, 0), (0, 1), (0, 2), (0, 3))
V_LINE_4 = ((0, 0), (1, 0), (2, 0), (3, 0))
PLUS_5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
H_LINE_5 = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
V_LINE_5 = ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0))

# (height, width, ((frame_inner_h, frame_inner_w, normalized_object), ...))
# These are executable transcriptions of every canonical train/test input.
_CANONICAL_PROFILES = (
    (12, 16, ((1, 2, H_DOMINO), (1, 3, L_TRIOMINO),
              (2, 2, SQUARE_2X2))),
    (13, 17, ((1, 2, V_DOMINO), (1, 3, L_TRIOMINO),
              (2, 2, T_TETROMINO))),
    (12, 17, ((1, 2, H_DOMINO), (1, 3, L_TRIOMINO),
              (1, 5, PLUS_5))),
    (13, 17, ((1, 2, V_DOMINO), (2, 2, SQUARE_2X2),
              (1, 5, PLUS_5))),
)
# Discriminative clip combos: every entry is BOTH non-rectangular (bbox area
# != cell count, so bbox-area matching leaves the frame empty or mis-fills
# it) AND pasted at a nonzero centered offset (so top-left pasting lands on
# different cells). One such pair per generalized clip draw guarantees the
# scene refutes both shortcuts plus clipping-skip.
_DISCRIMINATIVE_CLIP_COMBOS = (
    (4, (4, 1), (T_TETROMINO, T_TETROMINO_DOWN)),
    (5, (1, 5), (PLUS_5,)),
    (5, (5, 1), (PLUS_5,)),
)

_PALETTES = {
    "default": (1, 2, 3),
    "warm": (2, 4, 6),
    "cool": (1, 3, 5),
    "varied": (4, 7, 9),
}

_FRAME_DIMS = {
    2: ((1, 2), (2, 1)),
    3: ((1, 3), (3, 1)),
    4: ((2, 2), (1, 4), (4, 1)),
    5: ((1, 5), (5, 1)),
}

_SHAPES = {
    2: (H_DOMINO, V_DOMINO),
    3: (H_LINE_3, V_LINE_3, L_TRIOMINO, L_TRIOMINO_MIRROR),
    4: (SQUARE_2X2, T_TETROMINO, T_TETROMINO_DOWN,
        H_LINE_4, V_LINE_4),
    5: (PLUS_5, H_LINE_5, V_LINE_5),
}


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(cells):
    cells = _normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _frame_cells(inner_h, inner_w):
    outer_h, outer_w = inner_h + 2, inner_w + 2
    return tuple(
        (r, c)
        for r in range(outer_h)
        for c in range(outer_w)
        if r in (0, outer_h - 1) or c in (0, outer_w - 1)
    )


def _components(grid, *, include_colors=None):
    """Monochrome 4-connected non-background components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            if include_colors is not None and color not in include_colors:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells)})
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid):
    frames, solids, malformed_eights = [], [], []
    for obj in _components(grid):
        cells = obj["cells"]
        r1, c1, r2, c2 = _bbox(cells)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        entry = {
            **obj,
            "bbox": (r1, c1, r2, c2),
            "height": height,
            "width": width,
            "size": len(cells),
            "normalized": _normalize(cells),
        }
        if obj["color"] != 8:
            solids.append(entry)
            continue
        expected = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if height >= 3 and width >= 3 and set(cells) == expected:
            entry["inner_h"] = height - 2
            entry["inner_w"] = width - 2
            entry["area"] = (height - 2) * (width - 2)
            frames.append(entry)
        else:
            malformed_eights.append(entry)
    return frames, solids, malformed_eights


def _center(bbox):
    r1, c1, r2, c2 = bbox
    return (r1 + r2) / 2.0, (c1 + c2) / 2.0


def _has_nearest_frame_rebuttal(frames, solids):
    frame_by_area = {frame["area"]: frame for frame in frames}
    if len(frame_by_area) != len(frames):
        return False
    for solid in solids:
        matched = frame_by_area.get(solid["size"])
        if matched is None:
            continue
        sr, sc = _center(solid["bbox"])
        mr, mc = _center(matched["bbox"])
        matched_distance = abs(sr - mr) + abs(sc - mc)
        wrong_distances = []
        for frame in frames:
            if frame is matched:
                continue
            fr, fc = _center(frame["bbox"])
            wrong_distances.append(abs(sr - fr) + abs(sc - fc))
        if wrong_distances and min(wrong_distances) < matched_distance:
            return True
    return False


def canonical_profile_signature(grid):
    """Strict linked empirical profile, ignoring only placement/color roles."""
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return None
    frames, solids, malformed = _analyze(grid)
    if malformed or len(frames) != 3 or len(solids) != 3:
        return None
    palette = tuple(sorted({value for row in grid for value in row}))
    if palette != (0, 2, 4, 6, 8):
        return None
    if len({frame["area"] for frame in frames}) != 3:
        return None
    if len({solid["size"] for solid in solids}) != 3:
        return None
    solid_by_size = {solid["size"]: solid for solid in solids}
    linked = []
    for frame in sorted(frames, key=lambda item: item["area"]):
        solid = solid_by_size.get(frame["area"])
        if solid is None:
            return None
        linked.append((frame["inner_h"], frame["inner_w"],
                       solid["normalized"]))
    return h, w, tuple(linked)


def _profile_signature(profile):
    h, w, linked = profile
    return h, w, tuple(
        (inner_h, inner_w, _normalize(shape))
        for inner_h, inner_w, shape in linked
    )


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _CANONICAL_PROFILES
)


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md, v1)
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    """[] when grid carries one of the four strict LINKED canonical profiles.

    This is the semantic replacement for the coarse (h, w, palette) tuple: the
    pre-repair generator scored 0/180 strict task-linked matches while the
    coarse profile stayed green. Membership means the full coupling of canvas
    size, every frame's interior dimensions, and every area-matched object's
    normalized morphology equals a canonical train/test input.
    """
    signature = canonical_profile_signature(grid)
    if signature is None:
        return [
            "not a strict linked profile: needs exactly 3 hollow color-8 "
            "frames with distinct areas, 3 area-matched distinct-size loose "
            "objects, and palette {0,2,4,6,8}"
        ]
    if signature not in _CANONICAL_SIGNATURES:
        h, w, linked = signature
        return [
            f"linked profile {h}x{w} with interiors "
            f"{[(ih, iw) for ih, iw, _ in linked]} is not one of the 4 "
            "canonical train/test profiles"
        ]
    return []


def _matched_pairs(grid):
    """(frame, solid) pairs matched by interior area == cell count, or None."""
    frames, solids, malformed = _analyze(grid)
    if malformed:
        return None
    frame_by_area = {frame["area"]: frame for frame in frames}
    if len(frame_by_area) != len(frames):
        return None
    pairs = []
    for solid in solids:
        frame = frame_by_area.get(solid["size"])
        if frame is not None:
            pairs.append((frame, solid))
    return pairs


def _witness_matched_object_fits(grid) -> bool:
    """Fit branch: a matched object's bbox fits fully in its frame interior."""
    pairs = _matched_pairs(grid) or []
    return any(
        solid["height"] <= frame["inner_h"] and solid["width"] <= frame["inner_w"]
        for frame, solid in pairs
    )


def _witness_matched_object_clipped(grid) -> bool:
    """Clip branch: a matched object's bbox exceeds its frame interior, so
    the answer-bearing clipping beyond the interior must be exercised."""
    pairs = _matched_pairs(grid) or []
    return any(
        solid["height"] > frame["inner_h"] or solid["width"] > frame["inner_w"]
        for frame, solid in pairs
    )


def _witness_nearest_frame_rebuttal(grid) -> bool:
    """Shortcut killer: an object closer to a wrong-area frame than to its
    area match, so spatial proximity cannot replace area matching."""
    frames, solids, malformed = _analyze(grid)
    if malformed:
        return False
    return _has_nearest_frame_rebuttal(frames, solids)


SEMANTIC_WITNESSES = {
    "matched_object_fits": _witness_matched_object_fits,
    "matched_object_clipped": _witness_matched_object_clipped,
    "nearest_frame_rebuttal": _witness_nearest_frame_rebuttal,
}


def _apply_rule_variant(grid, *, match, placement, clip):
    """Python transcription of the canonical rule with pluggable defects.

    match: "cells" (canonical: interior area == cell count) or "bbox_area"
    (competitor: interior area == bounding-box area).
    placement: "centered" (canonical) or "top_left" (competitor).
    clip: True (canonical: drop cells beyond the frame interior) or False
    (competitor: paint the full bbox, only grid bounds apply).

    Returns the output grid, or None when the variant is inapplicable
    (malformed frames / duplicate frame areas), which counts as falsified.
    """
    h, w = len(grid), len(grid[0])
    frames, solids, malformed = _analyze(grid)
    if malformed:
        return None
    if len({frame["area"] for frame in frames}) != len(frames):
        return None
    frames = sorted(frames, key=lambda item: (item["area"], item["bbox"]))
    avail = sorted(solids, key=lambda item: (item["size"], item["bbox"]))

    out = full_grid(h, w, 0)
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = 8

    def measure(solid):
        if match == "cells":
            return solid["size"]
        return solid["height"] * solid["width"]

    for frame in frames:
        cand = next(
            (solid for solid in avail if measure(solid) == frame["area"]), None
        )
        if cand is None:
            continue
        avail = [solid for solid in avail if solid is not cand]
        sr1, sc1, sr2, sc2 = cand["bbox"]
        sub_h, sub_w = sr2 - sr1 + 1, sc2 - sc1 + 1
        fr1, fc1, fr2, fc2 = frame["bbox"]
        if placement == "centered":
            top = fr1 + 1 + max(0, (frame["inner_h"] - sub_h) // 2)
            left = fc1 + 1 + max(0, (frame["inner_w"] - sub_w) // 2)
        else:
            top = fr1 + 1
            left = fc1 + 1
        cand_cells = set(cand["cells"])
        for r in range(sub_h):
            for c in range(sub_w):
                if (sr1 + r, sc1 + c) not in cand_cells:
                    continue
                tr, tc = top + r, left + c
                if clip and not (tr < fr2 and tc < fc2):
                    continue
                if 0 <= tr < h and 0 <= tc < w:
                    out[tr][tc] = cand["color"]
    return out


def _rule_mirror(grid):
    """Canonical behaviour (tests/hooks only; Racket stays authoritative)."""
    return _apply_rule_variant(grid, match="cells", placement="centered", clip=True)


def _competitor_bbox_area_match(grid):
    """Competing rule: match objects to frames by BOUNDING-BOX area instead of
    cell count. Falsified by non-rectangular objects (L/T/plus)."""
    return _apply_rule_variant(
        grid, match="bbox_area", placement="centered", clip=True)


def _competitor_top_left_paste(grid):
    """Competing rule: paste at the frame interior's top-left corner instead
    of the centered offset."""
    return _apply_rule_variant(
        grid, match="cells", placement="top_left", clip=True)


def _competitor_no_clipping(grid):
    """Competing rule: paint the full object bbox without clipping cells that
    fall beyond the frame interior."""
    return _apply_rule_variant(
        grid, match="cells", placement="centered", clip=False)


_LESSON_COMPETITORS = {
    "match frames by bounding-box area instead of interior-area==cell-count":
        _competitor_bbox_area_match,
    "paste at frame interior top-left instead of centred":
        _competitor_top_left_paste,
    "skip clipping beyond the frame interior":
        _competitor_no_clipping,
}


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos uniquely determine the query answer.

    A competing rule consistent with EVERY demo that answers the query
    differently makes the lesson ambiguous. Pure: no mutation, no RNG."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        mirrored = _rule_mirror(demo["input"])
        if mirrored != demo["output"]:
            reasons.append(
                f"demo {index} output does not match the canonical "
                "area-match/centre/clip rule"
            )
    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' is consistent with every demo but "
                "answers the query differently"
            )
    return reasons


def observe_overrides(grid):
    """Exact semantic values recoverable from the returned input grid."""
    frames, solids, malformed = _analyze(grid)
    if malformed:
        return {"n_pairs": len(frames), "clip_mode": False}
    solid_by_size = {solid["size"]: solid for solid in solids}
    clipped = False
    for frame in frames:
        solid = solid_by_size.get(frame["area"])
        if solid is None:
            continue
        if (solid["height"] > frame["inner_h"]
                or solid["width"] > frame["inner_w"]):
            clipped = True
            break
    return {"n_pairs": len(frames), "clip_mode": clipped}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural teaching-distribution checker, including shortcut witnesses."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if not (12 <= h <= 18 and 16 <= w <= 22):
        errors.append(f"dims {h}x{w} outside valid 12..18 x 16..22")
    bad_values = {
        value
        for row in grid
        for value in row
        if (not isinstance(value, int) or isinstance(value, bool)
            or not 0 <= value <= 9)
    }
    if bad_values:
        errors.append("grid contains non-integer or color outside 0..9")
        return errors

    frames, solids, malformed = _analyze(grid)
    if malformed:
        errors.append(
            f"every color-8 component must be an exact hollow rectangle; "
            f"found {len(malformed)} malformed component(s)"
        )
    if not (2 <= len(frames) <= 3):
        errors.append(f"expected 2..3 hollow frames, found {len(frames)}")
    if len(solids) != len(frames):
        errors.append(
            f"expected one loose object per frame, found {len(solids)} "
            f"objects and {len(frames)} frames"
        )

    frame_areas = [frame["area"] for frame in frames]
    solid_sizes = [solid["size"] for solid in solids]
    if len(set(frame_areas)) != len(frame_areas):
        errors.append(f"frame interior areas must be distinct, found {frame_areas}")
    if len(set(solid_sizes)) != len(solid_sizes):
        errors.append(f"loose-object sizes must be distinct, found {solid_sizes}")
    if sorted(frame_areas) != sorted(solid_sizes):
        errors.append(
            f"object sizes {sorted(solid_sizes)} do not match frame areas "
            f"{sorted(frame_areas)}"
        )

    solid_colors = [solid["color"] for solid in solids]
    if len(set(solid_colors)) != len(solid_colors):
        errors.append(f"loose objects must use distinct colors, found {solid_colors}")

    for solid in solids:
        sr1, sc1, sr2, sc2 = solid["bbox"]
        for frame in frames:
            fr1, fc1, fr2, fc2 = frame["bbox"]
            if not (sr2 < fr1 or fr2 < sr1 or sc2 < fc1 or fc2 < sc1):
                errors.append(
                    f"loose color-{solid['color']} object overlaps frame bbox"
                )
                break

    if (len(frames) >= 2 and len(solids) == len(frames)
            and sorted(frame_areas) == sorted(solid_sizes)
            and not _has_nearest_frame_rebuttal(frames, solids)):
        errors.append(
            "no nearest-frame counterexample; proximity would solve this lesson"
        )
    return errors


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _choose_palette(ctx, overrides, *, canonical=False):
    texture = overrides.get("texture")
    palette_kind = overrides.get("palette_kind")
    if texture is not None and palette_kind is not None:
        raise ValueError(
            "texture and palette_kind are conflicting aliases; pass only one"
        )
    if texture is not None:
        kind = ctx.draw_choice("texture", PALETTE_KINDS)
    elif canonical:
        kind = ctx.draw_choice("palette_kind", ["warm"])
    else:
        kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    return kind, _PALETTES[kind]


def _fit_shape(inner_h, inner_w):
    return tuple(
        (r, c)
        for r in range(inner_h)
        for c in range(inner_w)
    )


def _generalized_profile(n_pairs, clip_mode, rng):
    """Linked (inner_h, inner_w, shape) profile for a generalized draw.

    Fit draws use full-interior rectangles (an area-matched fitting object
    necessarily fills its interior). Clip draws are ALWAYS discriminative:
    the clipped pair comes from _DISCRIMINATIVE_CLIP_COMBOS, so the scene
    refutes bbox-area matching and top-left pasting by itself.
    """
    if not clip_mode:
        areas = sorted(rng.sample((2, 3, 4, 5), n_pairs))
        linked = []
        for area in areas:
            inner_h, inner_w = rng.choice(_FRAME_DIMS[area])
            linked.append((inner_h, inner_w, _normalize(_fit_shape(inner_h, inner_w))))
        return tuple(linked)

    clip_area, clip_dims, clip_shapes = rng.choice(_DISCRIMINATIVE_CLIP_COMBOS)
    other_areas = rng.sample(
        [area for area in (2, 3, 4, 5) if area != clip_area], n_pairs - 1
    )
    linked = []
    for area in sorted([clip_area, *other_areas]):
        if area == clip_area:
            inner_h, inner_w = clip_dims
            shape = rng.choice(clip_shapes)
        else:
            inner_h, inner_w = rng.choice(_FRAME_DIMS[area])
            shape = _fit_shape(inner_h, inner_w)
        linked.append((inner_h, inner_w, _normalize(shape)))
    return tuple(linked)


def _absolute_cells(cells, top, left):
    return {(top + r, left + c) for r, c in cells}


def _bbox_overlap(a, b):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (ar2 < br1 or br2 < ar1 or ac2 < bc1 or bc2 < ac1)


def _painted_too_close(cells, existing):
    for r, c in cells:
        for er, ec in existing:
            if max(abs(r - er), abs(c - ec)) <= 1:
                return True
    return False


def _pack_items(h, w, items, rng):
    """Backtracking rectangle pack with a one-cell visual gap."""
    ordered = sorted(
        items,
        key=lambda item: item["height"] * item["width"],
        reverse=True,
    )
    for _ in range(24):
        candidates = {}
        for index, item in enumerate(ordered):
            positions = [
                (r, c)
                for r in range(h - item["height"] + 1)
                for c in range(w - item["width"] + 1)
            ]
            rng.shuffle(positions)
            candidates[index] = positions

        placed = []
        painted = set()
        node_budget = [50000]

        def search(index):
            if index == len(ordered):
                return True
            item = ordered[index]
            for top, left in candidates[index]:
                node_budget[0] -= 1
                if node_budget[0] < 0:
                    return False
                bbox = (
                    top,
                    left,
                    top + item["height"] - 1,
                    left + item["width"] - 1,
                )
                if any(_bbox_overlap(bbox, other["bbox"]) for other in placed):
                    continue
                cells = _absolute_cells(item["cells"], top, left)
                if _painted_too_close(cells, painted):
                    continue
                entry = {**item, "top": top, "left": left,
                         "bbox": bbox, "absolute": cells}
                placed.append(entry)
                painted.update(cells)
                if search(index + 1):
                    return True
                placed.pop()
                painted.difference_update(cells)
            return False

        if search(0):
            return placed
    return None


def _render_scene(h, w, linked, colors, rng):
    items = []
    for pair_index, ((inner_h, inner_w, shape), color) in enumerate(
            zip(linked, colors)):
        frame = _frame_cells(inner_h, inner_w)
        frame_h, frame_w = inner_h + 2, inner_w + 2
        items.append({
            "kind": "frame",
            "pair_index": pair_index,
            "color": 8,
            "cells": frame,
            "height": frame_h,
            "width": frame_w,
        })
        shape = _normalize(shape)
        shape_h, shape_w = _shape_dims(shape)
        items.append({
            "kind": "solid",
            "pair_index": pair_index,
            "color": color,
            "cells": shape,
            "height": shape_h,
            "width": shape_w,
        })

    for _ in range(80):
        placed = _pack_items(h, w, items, rng)
        if placed is None:
            continue
        grid = full_grid(h, w, 0)
        for item in placed:
            for r, c in item["absolute"]:
                grid[r][c] = item["color"]
        frames, solids, malformed = _analyze(grid)
        if (not malformed and _has_nearest_frame_rebuttal(frames, solids)
                and not self_check(grid)):
            return grid
    raise ValueError(
        f"could not pack {len(linked)} matched frame/object pairs in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi, pair_lo, pair_hi = 12, 13, 16, 17, 2, 2
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi, pair_lo, pair_hi = 14, 18, 18, 22, 3, 3
    else:
        h_lo, h_hi, w_lo, w_hi, pair_lo, pair_hi = 12, 15, 16, 19, 2, 3

    explicit_clip = overrides.get("clip_mode") is not None
    default_clip = bool(sample_index % 2)
    no_overrides = not any(value is not None for value in overrides.values())
    # Deterministic schedule: canonical profiles at sample_index % 4 == 3
    # (25% of default draws — same overall rate as the old 50%-of-odd random
    # prior), so the OTHER odd residue (% 4 == 1) is always a generalized
    # discriminative clip draw. Every EXAMPLES_NEEDED=3 demo window built
    # from consecutive sample indices therefore contains a scene refuting
    # bbox-area matching, top-left pasting, and clipping-skip.
    canonical_draw = no_overrides and sample_index % 4 == 3

    if canonical_draw:
        profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
        h, w, linked = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("n_pairs", 3, 3)
        ctx.draw_choice("clip_mode", [True])
        _, palette = _choose_palette(ctx, overrides, canonical=True)
        colors = list(palette)
        ctx.draw_rng("colors").shuffle(colors)
        return _render_scene(h, w, linked, colors, ctx.draw_rng("layout"))

    h = _banded_int(ctx, overrides, "grid_h", h_lo, h_hi, 12, 18)
    w = _banded_int(ctx, overrides, "grid_w", w_lo, w_hi, 16, 22)
    n_pairs = _banded_int(
        ctx, overrides, "n_pairs", pair_lo, pair_hi, 2, 3
    )
    if explicit_clip:
        clip_mode = ctx.draw_choice("clip_mode", [False, True])
    else:
        clip_mode = ctx.draw_choice("clip_mode", [default_clip])
    _, palette = _choose_palette(ctx, overrides)
    colors = list(palette[:n_pairs])
    ctx.draw_rng("colors").shuffle(colors)
    linked = _generalized_profile(
        n_pairs,
        clip_mode,
        ctx.draw_rng("profile"),
    )
    return _render_scene(h, w, linked, colors, ctx.draw_rng("layout"))
