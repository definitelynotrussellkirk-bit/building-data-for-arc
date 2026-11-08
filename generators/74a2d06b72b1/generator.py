"""Generator for arc_additional_puzzle_bank_volume17:H116.

Rule: the color-1 rectangular frames, sorted by bbox area descending, are
selected by index = (count of color-2 cells) - 1. Fill the selected
frame's interior with 8, except the region covered by the next-smaller
frame -- i.e. the ring between frame[idx] and frame[idx+1].

This generator draws K nested concentric color-1 frames plus N color-2
markers (N = idx+1), placed outside the frames.

Combinatorial axes: grid size, the nested frames, and the marker count
(which ring fills).
Degenerates: no_frames, no_markers, full_grid.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "74a2d06b72b1"
VERSION = "2.0.0"  # diversity: K nested frames + marker-count ring select (was fixed ~26)
TASK_ID = "74a2d06b72b1"
RULE_HASH = "c7287233192c"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "0-bg grid (size varies) with K (2-4) nested concentric color-1 frames "
    "and N color-2 markers. Rule: sort frames by area; (N-1) selects one; "
    "fill the ring between it and the next-inner frame with 8 (or the whole "
    "interior if it is the innermost). The grid size, frames and marker "
    "count vary freely (was a fixed setup, ~26 distinct)."
)

INVARIANTS = [
    "K nested concentric color-1 frames with distinct areas",
    "N color-2 markers select frame index N-1 (1 <= N <= K)",
    "the output fills the ring between the selected and next-inner frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_markers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "varies"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "varies"},
    "n_frames":       {"type": "int", "default": "varies", "valid": "2..4"},
    "select_idx":     {"type": "int", "default": "coverage cycle 0,K-1,1,K-2",
                       "valid": "0..K-1"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "nested_plus_markers",
                       "valid": "nested_plus_markers"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_frames|no_markers|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        kr, cr = (2, 2), (3, 4)
    elif difficulty == "hard":
        kr, cr = (3, 4), (3, 6)
    else:
        kr, cr = (2, 3), (3, 5)

    for _attempt in range(40):
        K = rng.randint(*kr)
        ih = rng.randint(*cr); iw = rng.randint(*cr)
        boxes = [(0, 0, ih - 1, iw - 1)]
        for _ in range(K - 1):
            r1, c1, r2, c2 = boxes[-1]
            mt = rng.randint(2, 3); ml = rng.randint(2, 3)
            mb = rng.randint(2, 3); mr = rng.randint(2, 3)
            boxes.append((r1 - mt, c1 - ml, r2 + mb, c2 + mr))
        or1, oc1 = boxes[-1][0], boxes[-1][1]
        boxes = [(r1 - or1, c1 - oc1, r2 - or1, c2 - oc1) for (r1, c1, r2, c2) in boxes]
        oh = boxes[-1][2] + 1; ow = boxes[-1][3] + 1

        h = rng.randint(oh + 3, oh + 7); w = rng.randint(ow + 3, ow + 7)
        if h > 30 or w > 30:
            continue
        top = rng.randint(1, h - oh - 1); left = rng.randint(1, w - ow - 1)

        g = full_grid(h, w, 0)
        for (r1, c1, r2, c2) in boxes:
            draw_frame(g, top + r1, left + c1, top + r2, left + c2, 1)

        # Markers select a ring.  Schedule the first few sample indices so a
        # normal three-example lesson cannot collapse to the retained
        # "always outermost" shortcut; later indices continue cycling through
        # all lawful selectors.  An explicit select_idx override remains exact.
        if "select_idx" in overrides:
            idx = overrides["select_idx"]
            if type(idx) is not int or not 0 <= idx < K:
                raise ValueError(f"select_idx must be an integer in 0..{K - 1}")
        else:
            teaching_order = (0, K - 1, min(1, K - 1), max(0, K - 2))
            idx = teaching_order[sample_index % len(teaching_order)]
        n2 = idx + 1
        outer = (top + boxes[-1][0], left + boxes[-1][1], top + boxes[-1][2], left + boxes[-1][3])
        free = [(r, c) for r in range(h) for c in range(w)
                if not (outer[0] - 1 <= r <= outer[2] + 1 and outer[1] - 1 <= c <= outer[3] + 1)]
        rng.shuffle(free)
        if len(free) < n2:
            continue
        for (r, c) in free[:n2]:
            g[r][c] = 2
        return g

    raise ValueError("could not realize nested-frame input")


def _frame_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    frames = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen \
                            and grid[nr][nc] == 1:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells); r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells); c1 = max(cc for _, cc in cells)
            if r1 - r0 < 2 or c1 - c0 < 2:
                continue
            border = {(rr, cc) for rr in range(r0, r1 + 1)
                      for cc in range(c0, c1 + 1)
                      if rr in (r0, r1) or cc in (c0, c1)}
            if set(cells) == border:
                frames.append((r0, c0, r1, c1))
    return frames


def _ordered_frames(grid):
    return sorted(
        _frame_components(grid),
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )


def _selection_state(grid):
    problems = self_check(grid)
    if problems:
        raise ValueError("invalid nested-frame input: " + "; ".join(problems))
    frames = _ordered_frames(grid)
    marker_count = sum(value == 2 for row in grid for value in row)
    return {
        "frames": frames,
        "marker_count": marker_count,
        "selected_index": marker_count - 1,
    }


def _paint_index(grid, index, *, exclude_next_inner=True):
    frames = _ordered_frames(grid)
    if not 0 <= index < len(frames):
        raise ValueError(f"frame index {index} is outside 0..{len(frames) - 1}")
    selected = frames[index]
    inner = frames[index + 1] if exclude_next_inner and index + 1 < len(frames) else None
    output = deepcopy(grid)
    for r in range(selected[0] + 1, selected[2]):
        for c in range(selected[1] + 1, selected[3]):
            blocked = (
                inner is not None
                and inner[0] <= r <= inner[2]
                and inner[1] <= c <= inner[3]
            )
            if output[r][c] == 0 and not blocked:
                output[r][c] = 8
    return output


def rule_mirror(grid):
    """Independent Python mirror; the selected canonical Racket is authority."""
    state = _selection_state(grid)
    return _paint_index(grid, state["selected_index"])


def strict_canonical_like(grid):
    """The lawful generated nested-frame grammar is the strict manifold."""
    return self_check(grid)


def _rival_always_outermost(grid):
    _selection_state(grid)
    return _paint_index(grid, 0)


def _rival_always_innermost(grid):
    state = _selection_state(grid)
    return _paint_index(grid, len(state["frames"]) - 1)


def _rival_fill_selected_interior(grid):
    state = _selection_state(grid)
    return _paint_index(
        grid,
        state["selected_index"],
        exclude_next_inner=False,
    )


SEMANTIC_RIVALS = {
    "always_outermost": _rival_always_outermost,
    "always_innermost": _rival_always_innermost,
    "fill_selected_interior": _rival_fill_selected_interior,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _lawful_state(grid):
    try:
        return _selection_state(grid)
    except (TypeError, ValueError, IndexError):
        return None


def _witness_outermost_selected(grid):
    state = _lawful_state(grid)
    return bool(state and state["selected_index"] == 0)


def _witness_non_outer_selected(grid):
    state = _lawful_state(grid)
    return bool(state and state["selected_index"] > 0)


def _witness_non_innermost_selected(grid):
    state = _lawful_state(grid)
    return bool(
        state and state["selected_index"] < len(state["frames"]) - 1
    )


def _witness_innermost_selected(grid):
    state = _lawful_state(grid)
    return bool(
        state and state["selected_index"] == len(state["frames"]) - 1
    )


SEMANTIC_WITNESSES = {
    "outermost_selected": _witness_outermost_selected,
    "non_outer_selected": _witness_non_outer_selected,
    "non_innermost_selected": _witness_non_innermost_selected,
    "innermost_selected": _witness_innermost_selected,
    "inner_exclusion_required": _witness_non_innermost_selected,
}
WITNESS_RIVALS = {
    "outermost_selected": ["always_innermost"],
    "non_outer_selected": ["always_outermost"],
    "non_innermost_selected": ["always_innermost"],
    "innermost_selected": ["always_outermost"],
    "inner_exclusion_required": ["fill_selected_interior"],
}


def lesson_identifiable(demos, query):
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        problems = self_check(demo["input"])
        if problems:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match marker-selected ring fill")
        valid_demos.append(demo)

    query_problems = self_check(query["input"])
    if query_problems:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match marker-selected ring fill")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = len(valid_demos) == len(demos) and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons


def self_check(grid, *, difficulty=None):
    problems = []
    frames = _frame_components(grid)
    if len(frames) < 2:
        problems.append(f"expected at least two nested color-1 frames, found {len(frames)}")
        return problems
    frames = sorted(frames, key=lambda b: (b[2]-b[0]+1)*(b[3]-b[1]+1), reverse=True)
    areas = [(b[2]-b[0]+1)*(b[3]-b[1]+1) for b in frames]
    if len(set(areas)) != len(areas):
        problems.append("nested frames do not have distinct areas")
    for outer, inner in zip(frames, frames[1:]):
        if not (outer[0] < inner[0] and outer[1] < inner[1] and
                outer[2] > inner[2] and outer[3] > inner[3]):
            problems.append(f"frames are not strictly nested: {outer} vs {inner}")
            break
    marker_count = sum(v == 2 for row in grid for v in row)
    if not (1 <= marker_count <= len(frames)):
        problems.append(f"marker count {marker_count} does not select one of {len(frames)} frames")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    draw_frame(g, 1, 1, 9, 9, 1)
    draw_frame(g, 3, 3, 7, 7, 1)
    g[11][1] = 2
    if name == "no_frames":
        return full_grid(13, 13, 0)
    if name == "no_markers":
        g[11][1] = 0
        return g
    if name == "full_grid":
        return full_grid(13, 13, 1)
    return g
