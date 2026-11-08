"""Generator for arc_puzzle_bank_seventeenth21:M116.

Rule: one 4-connected nonzero prototype contains a single color-8 anchor.
Every other nonzero component is an isolated 8 target.  Copy the prototype
onto each target by aligning the prototype anchor with that target; translated
cells outside the grid are simply clipped, exactly as in the canonical rule.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "05538555b6ce"
TASK_ID = "05538555b6ce"
VERSION = "4.0.0"
RULE_HASH = "68dc5bf6498f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A compact connected prototype contains exactly one color-8 anchor. "
    "One or two isolated 8 markers are destinations.  Copy every occupied "
    "prototype cell to each destination using anchor-relative offsets; cells "
    "whose translated coordinates fall outside the grid are clipped.  The "
    "three-example schedule always includes clipping, a non-top-left anchor, "
    "multiple targets, and a multicolor prototype across each sliding window."
)

INVARIANTS = [
    "exactly one multi-cell nonzero component is the prototype and contains one 8 anchor",
    "every other nonzero component is a singleton 8 target",
    "translated in-bounds prototype cells do not overlap the source prototype, another target, or another stamp",
    "edge targets may clip translated prototype cells, matching the canonical Racket rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng 5|6",
        "valid": "5|6",
        "doc": "Canonical-height support; both values are exact observable overrides.",
    },
    "grid_w": {
        "type": "int",
        "default": "rng 9|10|12",
        "valid": "9|10|12",
        "doc": "Canonical-width support; every value is an exact observable override.",
    },
}

_PROTO_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components_4_nonzero(grid):
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or grid[r][c] == 0:
                continue
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] != 0
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            out.append(sorted(cells))
    return out


def _analysis(grid):
    """Return the structural roles used by checks, rivals, and observables."""
    comps = _components_4_nonzero(grid)
    proto_candidates = []
    targets = []
    foreign = []
    for cells in comps:
        vals = [grid[r][c] for r, c in cells]
        if len(cells) > 1 and 8 in vals:
            proto_candidates.append(cells)
        elif len(cells) == 1 and vals[0] == 8:
            targets.append(cells[0])
        else:
            foreign.append(cells)

    info = {
        "components": comps,
        "proto_candidates": proto_candidates,
        "targets": sorted(targets),
        "foreign": foreign,
        "proto": None,
        "anchor": None,
        "anchor_offset": None,
        "rel": [],
        "target_records": [],
        "proto_colors": set(),
    }
    if len(proto_candidates) != 1:
        return info

    proto = proto_candidates[0]
    anchors = [(r, c) for r, c in proto if grid[r][c] == 8]
    info["proto"] = proto
    info["anchors"] = anchors
    if len(anchors) != 1:
        return info

    anchor = anchors[0]
    pr0 = min(r for r, _ in proto)
    pc0 = min(c for _, c in proto)
    rel = [
        (r - anchor[0], c - anchor[1], grid[r][c])
        for r, c in proto
    ]
    info["anchor"] = anchor
    info["anchor_offset"] = (anchor[0] - pr0, anchor[1] - pc0)
    info["rel"] = rel
    info["proto_colors"] = {grid[r][c] for r, c in proto if grid[r][c] != 8}

    h, w = len(grid), len(grid[0])
    for target in info["targets"]:
        translated = []
        clipped = False
        visible_non_anchor = 0
        for dr, dc, value in rel:
            nr, nc = target[0] + dr, target[1] + dc
            in_bounds = 0 <= nr < h and 0 <= nc < w
            clipped |= not in_bounds
            if in_bounds and (dr, dc) != (0, 0):
                visible_non_anchor += 1
            translated.append((nr, nc, value, in_bounds))
        info["target_records"].append(
            {
                "target": target,
                "translated": translated,
                "clipped": clipped,
                "visible_non_anchor": visible_non_anchor,
            }
        )
    return info


def oracle_output(grid):
    """Python mirror for diagnostics/tests only; canonical Racket stays authority."""
    info = _analysis(grid)
    if info["proto"] is None or info["anchor"] is None:
        raise ValueError("input does not contain one unambiguous anchored prototype")
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for tr, tc in info["targets"]:
        for dr, dc, value in info["rel"]:
            nr, nc = tr + dr, tc + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = value
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_bbox_top_left(grid):
    """Wrong rule: place the prototype bbox top-left at each target."""
    info = _analysis(grid)
    if info["proto"] is None:
        return [list(row) for row in grid]
    pr0 = min(r for r, _ in info["proto"])
    pc0 = min(c for _, c in info["proto"])
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for tr, tc in info["targets"]:
        for r, c in info["proto"]:
            nr, nc = tr + (r - pr0), tc + (c - pc0)
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = grid[r][c]
    return out


def _rival_skip_clipped(grid):
    """Wrong rule: stamp only when every occupied prototype cell fits."""
    info = _analysis(grid)
    if info["proto"] is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for record in info["target_records"]:
        if record["clipped"]:
            continue
        tr, tc = record["target"]
        for dr, dc, value in info["rel"]:
            nr, nc = tr + dr, tc + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = value
    return out


def _rival_first_target_only(grid):
    """Wrong rule: copy to only the first isolated 8 marker."""
    info = _analysis(grid)
    if info["proto"] is None:
        return [list(row) for row in grid]
    out = [list(row) for row in grid]
    if not info["targets"]:
        return out
    tr, tc = info["targets"][0]
    h, w = len(out), len(out[0])
    for dr, dc, value in info["rel"]:
        nr, nc = tr + dr, tc + dc
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = value
    return out


def _rival_monochrome_stamp(grid):
    """Wrong rule: copy shape/anchor but collapse all prototype colors to one."""
    info = _analysis(grid)
    if info["proto"] is None:
        return [list(row) for row in grid]
    colors = [
        grid[r][c]
        for r, c in info["proto"]
        if grid[r][c] != 8
    ]
    if not colors:
        return [list(row) for row in grid]
    mono = colors[0]
    out = [list(row) for row in grid]
    h, w = len(out), len(out[0])
    for tr, tc in info["targets"]:
        for dr, dc, value in info["rel"]:
            nr, nc = tr + dr, tc + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = 8 if value == 8 else mono
    return out


SEMANTIC_RIVALS = {
    "identity_marker_only": _rival_identity,
    "bbox_top_left_alignment": _rival_bbox_top_left,
    "skip_clipped_targets": _rival_skip_clipped,
    "first_target_only": _rival_first_target_only,
    "monochrome_stamp": _rival_monochrome_stamp,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All canonical exemplars use only one non-anchor prototype color, so the
# public examples alone cannot disprove a color-collapsing stamp rule.
CANONICAL_SHORTCUTS = {
    "monochrome_stamp": _rival_monochrome_stamp,
}


def _witness_full_stamp(grid) -> bool:
    info = _analysis(grid)
    return any(not record["clipped"] for record in info["target_records"])


def _witness_clipped_stamp(grid) -> bool:
    info = _analysis(grid)
    return (
        any(record["clipped"] for record in info["target_records"])
        and oracle_output(grid) != _rival_skip_clipped(grid)
    )


def _witness_anchor_offset(grid) -> bool:
    info = _analysis(grid)
    return (
        info["anchor_offset"] not in (None, (0, 0))
        and oracle_output(grid) != _rival_bbox_top_left(grid)
    )


def _witness_multiple_targets(grid) -> bool:
    info = _analysis(grid)
    return (
        len(info["targets"]) >= 2
        and oracle_output(grid) != _rival_first_target_only(grid)
    )


def _witness_multicolor(grid) -> bool:
    info = _analysis(grid)
    return (
        len(info["proto_colors"]) >= 2
        and oracle_output(grid) != _rival_monochrome_stamp(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "full_stamp_visible": _witness_full_stamp,
    "clipped_stamp_visible": _witness_clipped_stamp,
    "anchor_not_bbox_top_left": _witness_anchor_offset,
    "multiple_targets": _witness_multiple_targets,
    "multicolor_prototype": _witness_multicolor,
}

WITNESS_RIVALS = {
    "full_stamp_visible": ["identity_marker_only"],
    "clipped_stamp_visible": ["skip_clipped_targets", "identity_marker_only"],
    "anchor_not_bbox_top_left": ["bbox_top_left_alignment"],
    "multiple_targets": ["first_target_only"],
    "multicolor_prototype": ["monochrome_stamp"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives all demos."""
    official_query = oracle_output(query["input"])
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != official_query:
                errors.append(f"demos do not rule out rival operation {name}")
    return errors


def _build_proto(rng, *, k: int, anchor_top_left: bool, multicolor: bool):
    """Build a compact connected 4..6-cell shape and choose its 8 anchor."""
    for _ in range(200):
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = cells[rng.randrange(len(cells))]
            dr, dc = _CARDINAL[rng.randrange(len(_CARDINAL))]
            nxt = (r + dr, c + dc)
            if nxt in seen:
                continue
            cells.append(nxt)
            seen.add(nxt)
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        ph = max(r for r, _ in norm) + 1
        pw = max(c for _, c in norm) + 1
        if ph > 3 or pw > 4:
            continue

        if anchor_top_left:
            candidates = [index for index, cell in enumerate(norm) if cell == (0, 0)]
        else:
            candidates = [index for index, cell in enumerate(norm) if cell != (0, 0)]
        if not candidates:
            continue
        anchor_i = candidates[rng.randrange(len(candidates))]
        color_count = 2 if multicolor else 1
        colors = rng.sample(_PROTO_COLORS, color_count)
        proto = []
        for index, (r, c) in enumerate(norm):
            value = 8 if index == anchor_i else colors[index % color_count]
            proto.append((r, c, value))
        return proto, norm[anchor_i]
    raise ValueError("could not build compact prototype for scheduled anchor branch")


def _candidate_targets(grid, rel, *, occupied_input, occupied_stamps, want_clipped):
    h, w = len(grid), len(grid[0])
    candidates = []
    for tr in range(h):
        for tc in range(w):
            if (tr, tc) in occupied_input:
                continue
            # Generated targets are kept visibly isolated even though the
            # authority only requires 4-connectivity separation.
            if any(
                (tr + dr, tc + dc) in occupied_input
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if dr or dc
            ):
                continue

            translated = []
            clipped = False
            visible_non_anchor = 0
            for dr, dc, _value in rel:
                nr, nc = tr + dr, tc + dc
                if 0 <= nr < h and 0 <= nc < w:
                    translated.append((nr, nc))
                    if (dr, dc) != (0, 0):
                        visible_non_anchor += 1
                else:
                    clipped = True
            if clipped != want_clipped or visible_non_anchor < 2:
                continue
            translated_set = set(translated)
            if translated_set & occupied_input:
                continue
            if translated_set & occupied_stamps:
                continue
            candidates.append((tr, tc, translated_set))
    return candidates


def _scheduled_requirements(sample_index: int) -> dict[str, object]:
    """Profiles with bounded gaps so every 3 consecutive demos teach the rule."""
    return {
        "clipped": sample_index % 3 == 0,
        "n_targets": 1 if sample_index % 3 == 0 else 2,
        "multicolor": sample_index % 2 == 1,
        "anchor_top_left": sample_index % 5 == 0,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", (5, 6))
    w = ctx.draw_choice("grid_w", (9, 10, 12))
    layout_rng = ctx.draw_rng("layout")
    proto_rng = ctx.draw_rng("prototype")
    req = _scheduled_requirements(sample_index)
    k = {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 4 + (sample_index % 3))

    for _attempt in range(240):
        grid = full_grid(h, w, 0)
        proto, (ar, ac) = _build_proto(
            proto_rng,
            k=k,
            anchor_top_left=bool(req["anchor_top_left"]),
            multicolor=bool(req["multicolor"]),
        )
        ph = max(r for r, _, _ in proto) + 1
        pw = max(c for _, c, _ in proto) + 1
        if ph > h or pw > w:
            continue

        p0r = layout_rng.randint(0, h - ph)
        p0c = layout_rng.randint(0, w - pw)
        for r, c, value in proto:
            grid[p0r + r][p0c + c] = value

        rel = [(r - ar, c - ac, value) for r, c, value in proto]
        occupied_input = {
            (p0r + r, p0c + c)
            for r, c, _value in proto
        }
        occupied_stamps = set()
        target_modes = [bool(req["clipped"])] + [False] * (int(req["n_targets"]) - 1)
        targets = []
        realized = True
        for want_clipped in target_modes:
            candidates = _candidate_targets(
                grid,
                rel,
                occupied_input=occupied_input,
                occupied_stamps=occupied_stamps,
                want_clipped=want_clipped,
            )
            if not candidates:
                realized = False
                break
            tr, tc, stamp_cells = candidates[layout_rng.randrange(len(candidates))]
            grid[tr][tc] = 8
            targets.append((tr, tc))
            occupied_input.add((tr, tc))
            occupied_stamps.update(stamp_cells)
        if not realized:
            continue

        strict_errors = strict_canonical_like(grid)
        if strict_errors:
            continue
        # These checks make the declared three-demo schedule a real semantic
        # guarantee rather than a correlation in metadata.
        if bool(req["clipped"]) and not _witness_clipped_stamp(grid):
            continue
        if not bool(req["anchor_top_left"]) and not _witness_anchor_offset(grid):
            continue
        if int(req["n_targets"]) > 1 and not _witness_multiple_targets(grid):
            continue
        if bool(req["multicolor"]) and not _witness_multicolor(grid):
            continue
        return grid
    raise ValueError("could not realize scheduled anchor-stamp board")


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from a generated grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("cannot observe axes from an empty or ragged grid")
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None):
    """Authority-valid structural grammar; clipping is explicitly lawful."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"]

    errors = []
    info = _analysis(grid)
    if len(info["proto_candidates"]) != 1:
        return [
            "expected exactly one multi-cell nonzero component containing an 8 anchor, "
            f"found {len(info['proto_candidates'])}"
        ]
    if info["foreign"]:
        errors.append(
            f"every non-prototype component must be a singleton 8 target; found {len(info['foreign'])} foreign component(s)"
        )
    proto = info["proto"]
    if proto is None:
        return errors or ["anchored prototype analysis failed"]
    if len(proto) < 2:
        errors.append("prototype must contain more than one occupied cell")
    anchors = info.get("anchors", [])
    if len(anchors) != 1:
        errors.append(f"prototype must contain exactly one 8 anchor, found {len(anchors)}")
        return errors

    input_nonzero = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    stamp_sets = []
    for record in info["target_records"]:
        target = record["target"]
        translated = {
            (r, c)
            for r, c, _value, in_bounds in record["translated"]
            if in_bounds
        }
        illegal = (translated & input_nonzero) - {target}
        if illegal:
            errors.append(
                f"stamp at target {target} overlaps existing input cell {sorted(illegal)[0]}"
            )
        for prior in stamp_sets:
            overlap = translated & prior
            if overlap:
                errors.append(
                    f"stamp at target {target} overlaps another stamp at {sorted(overlap)[0]}"
                )
                break
        stamp_sets.append(translated)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked teaching predicate, stricter than the authority grammar."""
    errors = list(self_check(grid))
    if errors:
        return errors
    info = _analysis(grid)
    if not 4 <= len(info["proto"]) <= 6:
        errors.append(f"prototype should contain 4..6 cells, got {len(info['proto'])}")
    if not info["targets"]:
        errors.append("teaching scenes require at least one isolated 8 target")
    for record in info["target_records"]:
        if record["visible_non_anchor"] < 2:
            errors.append(
                f"target {record['target']} exposes fewer than two copied non-anchor cells"
            )
    if len(info["proto_colors"]) not in (1, 2):
        errors.append("prototype should use one or two non-anchor colors")
    return errors
