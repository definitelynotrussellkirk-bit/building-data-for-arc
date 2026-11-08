"""Fill exact hollow orange rectangles and preserve contrastive decoys.

The canonical rule is color- and shape-specific: only exact one-cell-thick
orange (7) rectangular outlines receive cyan (8) interiors.  Every default
sample also contains a broken orange near-frame and an exact non-orange frame,
so canonical-fitting shortcuts cannot survive the generated lessons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "af6e765bcc41"
TASK_ID = "af6e765bcc41"
VERSION = "3.0.0"
RULE_HASH = "c8f338ea5e1e"
SUMMARY = (
    "On a zero background, fill the zero interior of every exact hollow "
    "orange (7) rectangular frame with cyan (8). Preserve the orange outline, "
    "broken orange near-frames, non-orange frames, and all unrelated cells."
)
INVARIANTS = [
    "inputs are rectangular ARC-color grids with no cyan",
    "at least one exact hollow orange frame has an empty interior",
    "default draws include one broken orange near-frame",
    "default draws include one exact hollow frame in a non-orange color",
    "accepted numeric overrides are recoverable exactly from the pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical profile by band", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical profile by band", "valid": "10..16"},
    "n_frames": {"type": "int", "default": "1 easy; 1..2 medium; 2 hard", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

_CANONICAL_PROFILES = ((8, 11), (9, 10), (10, 10), (10, 12), (11, 11))
_DISTRACTOR_COLORS = (1, 2, 3, 4, 5, 6, 9)


def _components_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
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
            comps.append(comp)
    return comps


def _bbox(comp):
    return (
        min(r for r, _ in comp),
        min(c for _, c in comp),
        max(r for r, _ in comp),
        max(c for _, c in comp),
    )


def _border(comp):
    r0, c0, r1, c1 = _bbox(comp)
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _empty_interior(grid, comp):
    r0, c0, r1, c1 = _bbox(comp)
    return all(
        grid[r][c] == 0
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    )


def _is_exact_frame(grid, comp):
    r0, c0, r1, c1 = _bbox(comp)
    return (
        r1 - r0 + 1 >= 3
        and c1 - c0 + 1 >= 3
        and set(comp) == _border(comp)
        and _empty_interior(grid, comp)
    )


def _is_broken_frame(grid, comp):
    r0, c0, r1, c1 = _bbox(comp)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3 or not _empty_interior(grid, comp):
        return False
    border = _border(comp)
    missing = border - set(comp)
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    return len(missing) == 1 and not (missing & corners) and set(comp) == border - missing


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and the generated exact-frame/near-frame grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid values must be integer ARC colors 0..9"]
    errs: list[str] = []
    if any(v == 8 for row in grid for v in row):
        errs.append("input must not already contain output color 8")

    exact = 0
    broken = 0
    for index, comp in enumerate(_components_color(grid, 7)):
        if _is_exact_frame(grid, comp):
            exact += 1
        elif _is_broken_frame(grid, comp):
            broken += 1
        else:
            errs.append(f"orange component {index} is neither an exact frame nor a one-gap near-frame")
    if exact < 1:
        errs.append("expected at least one exact hollow orange frame")
    if broken > 1:
        errs.append(f"expected at most one broken orange near-frame, found {broken}")
    return errs


def _integer_axis(ctx, name, lo, hi, defaults):
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, *defaults)


def _profile_choices(difficulty):
    if difficulty == "easy":
        return _CANONICAL_PROFILES[:2]
    if difficulty == "medium":
        return _CANONICAL_PROFILES[1:4]
    if difficulty == "hard":
        return _CANONICAL_PROFILES[3:]
    return _CANONICAL_PROFILES


def _motif_slots(h, w, rng):
    """Four disjoint corner regions separated by one blank row and column."""
    rmid, cmid = h // 2, w // 2
    row_regions = ((0, rmid - 1), (rmid + 1, h - 1))
    col_regions = ((0, cmid - 1), (cmid + 1, w - 1))
    slots = []
    for rlo, rhi in row_regions:
        for clo, chi in col_regions:
            region_h, region_w = rhi - rlo + 1, chi - clo + 1
            rh = rng.randint(3, min(5, region_h))
            rw = rng.randint(3, min(5, region_w))
            r = rng.randint(rlo, rhi - rh + 1)
            c = rng.randint(clo, chi - rw + 1)
            slots.append((r, c, rh, rw))
    rng.shuffle(slots)
    return slots


def _draw_broken_outline(grid, box, rng):
    r, c, rh, rw = box
    draw_rect_outline(grid, r, c, rh, rw, 7)
    removable = (
        [(r, cc) for cc in range(c + 1, c + rw - 1)]
        + [(r + rh - 1, cc) for cc in range(c + 1, c + rw - 1)]
        + [(rr, c) for rr in range(r + 1, r + rh - 1)]
        + [(rr, c + rw - 1) for rr in range(r + 1, r + rh - 1)]
    )
    rr, cc = rng.choice(removable)
    grid[rr][cc] = 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(
            f"unknown or removed override axes: {sorted(unknown)}; supported: {sorted(AXES)}"
        )
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    bounds = {"grid_h": (8, 16), "grid_w": (10, 16), "n_frames": (1, 2)}
    for name, value in overrides.items():
        lo, hi = bounds[name]
        if type(value) is not int or not lo <= value <= hi:
            exc = ValueError(f"{name} must be an integer in {lo}..{hi}")
            exc.incompatible_axes = (name,)
            raise exc

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("canonical_profile", _profile_choices(difficulty))
    h = _integer_axis(ctx, "grid_h", 8, 16, (profile[0], profile[0]))
    w = _integer_axis(ctx, "grid_w", 10, 16, (profile[1], profile[1]))
    if difficulty == "easy":
        n_default = (1, 1)
    elif difficulty == "hard":
        n_default = (2, 2)
    else:
        n_default = (1, 2)
    n_frames = _integer_axis(ctx, "n_frames", 1, 2, n_default)

    rng = ctx.draw_rng("layout")
    slots = _motif_slots(h, w, rng)
    grid = full_grid(h, w, 0)
    for box in slots[:n_frames]:
        draw_rect_outline(grid, *box, 7)
    _draw_broken_outline(grid, slots[n_frames], rng)
    distractor_color = rng.choice(_DISTRACTOR_COLORS)
    draw_rect_outline(grid, *slots[n_frames + 1], distractor_color)
    return grid


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": sum(
            _is_exact_frame(grid, comp) for comp in _components_color(grid, 7)
        ),
    }


def _fill_bbox_interior(out, grid, comp):
    r0, c0, r1, c1 = _bbox(comp)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if grid[r][c] == 0:
                out[r][c] = 8


def _oracle_output(grid):
    """Python mirror used only for focused semantic tests, never label authority."""
    out = [row[:] for row in grid]
    for comp in _components_color(grid, 7):
        if _is_exact_frame(grid, comp):
            _fill_bbox_interior(out, grid, comp)
    return out


def _orange_bboxes_rival(grid):
    """Shortcut: fill every orange component's bounding-box interior."""
    out = [row[:] for row in grid]
    for comp in _components_color(grid, 7):
        _fill_bbox_interior(out, grid, comp)
    return out


def _all_color_frames_rival(grid):
    """Shortcut: fill every exact nonzero rectangular frame, ignoring color."""
    out = [row[:] for row in grid]
    for color in range(1, 10):
        if color == 8:
            continue
        for comp in _components_color(grid, color):
            if _is_exact_frame(grid, comp):
                _fill_bbox_interior(out, grid, comp)
    return out


def _broken_orange_witness(grid):
    return any(_is_broken_frame(grid, comp) for comp in _components_color(grid, 7))


def _nonorange_frame_witness(grid):
    return any(
        _is_exact_frame(grid, comp)
        for color in _DISTRACTOR_COLORS
        for comp in _components_color(grid, color)
    )


SEMANTIC_RIVALS = {
    "orange_bboxes": _orange_bboxes_rival,
    "all_color_frames": _all_color_frames_rival,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "broken_orange": _broken_orange_witness,
    "nonorange_frame": _nonorange_frame_witness,
}
WITNESS_RIVALS = {
    "broken_orange": ["orange_bboxes"],
    "nonorange_frame": ["all_color_frames"],
}



def strict_canonical_like(grid):
    return self_check(grid)


def lesson_identifiable(demos, query):
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < 1:
        return ["lesson needs at least one labeled demonstration"]
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is not a labeled input/output pair")
            continue
        if pair["output"] != _oracle_output(pair["input"]):
            reasons.append(f"pair {index} label disagrees with the exact orange-frame rule")
    for name, rival in SEMANTIC_RIVALS.items():
        valid_demos = [
            pair for pair in demos
            if isinstance(pair, dict) and "input" in pair and "output" in pair
        ]
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
