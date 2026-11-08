"""Count isolated colored cells and match them to hollow-frame checkerboards.

Labels are always supplied by the unchanged canonical Racket authority.  Normal
lessons alternate fully matched scenes and counterexamples to rank/fit matching.
Four consecutive inputs retain both kinds after any one query holdout.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "18bd3cd2985e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "70c5793d0c5a"
SUMMARY = (
    "Hollow rectangular frames and four-connected singleton components on zero. "
    "Erase the singletons; fill local even-parity interior cells only when their "
    "count equals that color's singleton count. Scenes include all, partial and "
    "absent count matches, varied colors, sizes, positions and diagonal singles."
)
INVARIANTS = [
    "Every multi-cell component is an empty hollow rectangular frame.",
    "Frame checkerboard capacities are distinct and positive.",
    "Singleton groups have distinct counts, avoiding color overwrite ties.",
    "Unmatched groups are erased and unmatched frames remain empty.",
    "Same-color diagonal neighbors are separate four-connected singletons.",
]
AXES = {
    "grid_h": {"type": "int", "default": "varies", "valid": "12..30"},
    "grid_w": {"type": "int", "default": "varies", "valid": "12..30"},
    "n_frames": {"type": "int", "default": "varies", "valid": "1..3"},
    "match_mode": {"type": "str", "default": "varies", "valid": "all|partial|none"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [{"n_frames": 1, "match_mode": "partial"}]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 6
SCHEDULE_PROFILES = ("all", "partial", "none")
MIN_STRICT_FRAC = 0.25
_MODES = ("all", "partial", "all", "partial", "all", "none")
_PROFILES = ((20, 20, 2), (18, 23, 2), (12, 20, 2), (22, 26, 3))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    parts = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                y, x = todo.pop()
                cells.append((y, x))
                for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (0 <= yy < h and 0 <= xx < w and (yy, xx) not in seen
                            and grid[yy][xx] == color):
                        seen.add((yy, xx))
                        todo.append((yy, xx))
            parts.append((color, cells))
    return parts


def _scene(grid):
    frames, singles = [], Counter()
    for color, cells in _components(grid):
        if len(cells) == 1:
            singles[color] += 1
            continue
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        bottom = max(r for r, c in cells)
        right = max(c for r, c in cells)
        capacity = ((bottom - top - 1) * (right - left - 1) + 1) // 2
        frames.append((color, top, left, bottom, right, capacity, cells))
    return frames, singles


def self_check(grid, *, difficulty=None, meta=None):
    """Check the actual component geometry, without relying on caller metadata."""
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty list of grid rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["expected nonempty row lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integers in 0..9, excluding booleans"]
    frames, singles = _scene(grid)
    errors = []
    if not frames:
        errors.append("expected at least one hollow rectangular frame")
    capacities = []
    for color, top, left, bottom, right, capacity, cells in frames:
        if bottom - top < 2 or right - left < 2:
            errors.append("multi-cell component has no rectangular interior")
            continue
        boundary = {(r, c) for r in range(top, bottom + 1)
                    for c in range(left, right + 1)
                    if r in (top, bottom) or c in (left, right)}
        if set(cells) != boundary:
            errors.append("multi-cell component is not a complete hollow frame")
        if any(grid[r][c] != 0 for r in range(top + 1, bottom)
               for c in range(left + 1, right)):
            errors.append("frame interior must be empty")
        capacities.append(capacity)
    if len(capacities) != len(set(capacities)):
        errors.append("duplicate frame capacity would invoke first-frame tie behavior")
    if len(singles) != len(set(singles.values())):
        errors.append("duplicate singleton counts permit competing fill colors")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    frames, singles = _scene(grid)
    if not 2 <= len(frames) <= 3:
        return ["canonical scenes contain two or three frames"]
    if sorted(f[5] for f in frames) != sorted(singles.values()):
        return ["canonical scenes match every frame and singleton group exactly"]
    return []


def observe_overrides(grid):
    frames, singles = _scene(grid)
    matched = sum(f[5] in singles.values() for f in frames)
    mode = "all" if matched == len(frames) else "partial" if matched else "none"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_frames": len(frames), "match_mode": mode}


def schedule_profile(seed, sample_index, difficulty=None):
    return _MODES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_integer(ctx, label, default, lower, upper):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lower, upper)
    return ctx.draw_int_strict(label, default, default)


def _separated(box, placed):
    top, left, fh, fw = box
    return all(top + fh < y or y + hh < top or left + fw < x or x + ww < left
               for y, x, hh, ww in placed)


def _draw_scene(rng, h, w, k, mode, max_side, max_capacity):
    area_limit = max(20, h * w // (2 * k))
    candidates = [(fh, fw, ((fh - 2) * (fw - 2) + 1) // 2)
                  for fh in range(3, min(max_side, h) + 1)
                  for fw in range(3, min(max_side, w) + 1)
                  if fh * fw <= area_limit
                  and ((fh - 2) * (fw - 2) + 1) // 2 <= max_capacity]
    for attempt in range(80):
        rng.shuffle(candidates)
        chosen, capacities = [], set()
        for shape in candidates:
            if shape[2] not in capacities:
                chosen.append(shape)
                capacities.add(shape[2])
                if len(chosen) == k:
                    break
        if len(chosen) != k:
            raise RuntimeError("shape domain cannot realize the requested distinct frames")
        gaps = [n for n in range(1, max(capacities)) if n not in capacities]
        if mode != "all" and not gaps:
            # Every nonall scene must distinguish equality from merely fitting.
            continue
        boxes = [None] * k
        placed = []
        for i in sorted(range(k), key=lambda j: -chosen[j][0] * chosen[j][1]):
            fh, fw, capacity = chosen[i]
            for _ in range(100):
                top, left = rng.randrange(h - fh + 1), rng.randrange(w - fw + 1)
                # A fully matched scene itself refutes both fixed global phases.
                if mode == "all" and k >= 2 and i < 2 and (top + left) % 2 != i:
                    continue
                if _separated((top, left, fh, fw), placed):
                    boxes[i] = (top, left, fh, fw)
                    placed.append(boxes[i])
                    break
            if boxes[i] is None:
                break
        if any(box is None for box in boxes):
            continue
        counts = [shape[2] for shape in chosen]
        if mode == "partial":
            replaceable = [i for i, count in enumerate(counts) if count < max(capacities)]
            counts[rng.choice(replaceable)] = rng.choice(gaps)
        elif mode == "none":
            counts = [rng.choice(gaps)]
            if k >= 2:
                counts.append(max(capacities) + rng.randint(1, k))
            extras = [n for n in range(1, max(capacities) + k + 1)
                      if n not in capacities and n not in counts]
            counts.extend(rng.sample(extras, k - len(counts)))
            rng.shuffle(counts)
        colors = rng.sample(list(range(1, 10)), 2 * k)
        grid = full_grid(h, w, 0)
        occupied = set()
        for i, (top, left, fh, fw) in enumerate(boxes):
            draw_frame(grid, top, left, top + fh - 1, left + fw - 1, colors[i])
            occupied.update((r, c) for r in range(top, top + fh)
                            for c in range(left, left + fw))
        available = [(r, c) for r in range(h) for c in range(w)
                     if (r, c) not in occupied]
        complete = True
        for i in sorted(range(k), key=lambda j: -counts[j]):
            color, remaining = colors[k + i], counts[i]
            rng.shuffle(available)
            for r, c in available:
                if grid[r][c] != 0:
                    continue
                if any(0 <= y < h and 0 <= x < w and grid[y][x] == color
                       for y, x in ((r-1,c), (r+1,c), (r,c-1), (r,c+1))):
                    continue
                grid[r][c] = color
                remaining -= 1
                if remaining == 0:
                    break
            if remaining:
                complete = False
                break
        if complete and not self_check(grid):
            return grid
    raise RuntimeError("bounded scene construction exhausted; no partial scene returned")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError("unknown or retired override(s): " + ", ".join(sorted(unknown)))
    if type(seed) is not int or type(sample_index) is not int or seed < 0 or sample_index < 0:
        raise ValueError("seed and sample_index must be nonnegative integers, not bools")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    for name in ("grid_h", "grid_w", "n_frames"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(name + " must be an integer, not a coerced scalar")
    if overrides.get("match_mode") is not None and overrides["match_mode"] not in SCHEDULE_PROFILES:
        raise ValueError("match_mode must be all, partial, or none")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("scene")
    dh, dw, dk = rng.choice(_PROFILES)
    if ctx.draw_rng("profile-support").randrange(4) == 0:
        dh, dw, dk = rng.randint(12, 30), rng.randint(12, 30), rng.randint(2, 3)
    h = _draw_integer(ctx, "grid_h", dh, 12, 30)
    w = _draw_integer(ctx, "grid_w", dw, 12, 30)
    k = _draw_integer(ctx, "n_frames", dk, 1, 3)
    default_mode = schedule_profile(seed, sample_index, difficulty)
    if k == 1 and default_mode == "partial":
        default_mode = "all"
    mode = ctx.draw_choice("match_mode", SCHEDULE_PROFILES if overrides.get("match_mode") is not None
                           else (default_mode,))
    if k == 1 and mode == "partial":
        error = ValueError("n_frames=1 and match_mode=partial are incompatible")
        error.incompatible_axes = ("n_frames", "match_mode")
        raise error
    max_side, max_capacity = {"easy": (6, 6), "medium": (9, 16), "hard": (11, 27)}.get(
        difficulty, (9, 16))
    return _draw_scene(rng, h, w, k, mode, max_side, max_capacity)


def _rival_output(grid, kind):
    """Declared alternatives only; these never label generated training pairs."""
    frames, singles = _scene(grid)
    out = [row[:] for row in grid]
    for color, cells in _components(grid):
        if len(cells) == 1:
            r, c = cells[0]
            out[r][c] = 0
    if kind == "erase_only":
        return out
    if kind == "rank_pairing":
        assignments = [(f, color) for f, (color, count) in zip(
            sorted(frames, key=lambda f: f[5]), sorted(singles.items(), key=lambda x: x[1]))]
    elif kind == "smallest_fitting_frame":
        pending = sorted(singles.items(), key=lambda item: item[1])
        assignments = []
        for frame in sorted(frames, key=lambda f: f[5]):
            if pending and pending[0][1] <= frame[5]:
                color, count = pending.pop(0)
                assignments.append((frame, color))
    elif kind == "smallest_sufficient_group":
        pending = sorted(singles.items(), key=lambda item: item[1])
        assignments = []
        for frame in sorted(frames, key=lambda f: f[5]):
            while pending and pending[0][1] < frame[5]:
                pending.pop(0)
            if pending:
                color, count = pending.pop(0)
                assignments.append((frame, color))
    else:
        assignments = [(f, color) for f in frames for color, count in singles.items()
                       if count == f[5]]
    for frame, color in assignments:
        _, top, left, bottom, right, capacity, cells = frame
        for r in range(top + 1, bottom):
            for c in range(left + 1, right):
                keep = ((r - top - 1 + c - left - 1) % 2 == 0)
                if kind == "solid_fill":
                    keep = True
                elif kind == "global_even":
                    keep = (r + c) % 2 == 0
                elif kind == "global_odd":
                    keep = (r + c) % 2 == 1
                if keep:
                    out[r][c] = color
    return out


def rank_pairing(grid):
    return _rival_output(grid, "rank_pairing")


def smallest_fitting_frame(grid):
    return _rival_output(grid, "smallest_fitting_frame")


def smallest_sufficient_group(grid):
    return _rival_output(grid, "smallest_sufficient_group")


def erase_only(grid):
    return _rival_output(grid, "erase_only")


def solid_fill(grid):
    return _rival_output(grid, "solid_fill")


def global_even(grid):
    return _rival_output(grid, "global_even")


def global_odd(grid):
    return _rival_output(grid, "global_odd")


SEMANTIC_RIVALS = {"rank_pairing": rank_pairing,
                   "smallest_fitting_frame": smallest_fitting_frame, "erase_only": erase_only,
                   "smallest_sufficient_group": smallest_sufficient_group,
                   "solid_fill": solid_fill, "global_even": global_even,
                   "global_odd": global_odd}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"rank_pairing": rank_pairing,
                       "smallest_fitting_frame": smallest_fitting_frame,
                       "smallest_sufficient_group": smallest_sufficient_group}


def _undersized_unmatched(grid):
    frames, singles = _scene(grid)
    capacities = {f[5] for f in frames}
    return bool(capacities) and any(n not in capacities and n < max(capacities)
                                    for n in singles.values())


SEMANTIC_WITNESSES = {
    "rank_counterexample": lambda g: observe_overrides(g)["match_mode"] != "all",
    "fit_counterexample": _undersized_unmatched,
    "sufficient_counterexample": lambda g: observe_overrides(g)["match_mode"] != "all",
    "all_matched": lambda g: observe_overrides(g)["match_mode"] == "all",
    "partly_matched": lambda g: observe_overrides(g)["match_mode"] == "partial",
    "no_match": lambda g: observe_overrides(g)["match_mode"] == "none",
}
WITNESS_RIVALS = {"rank_counterexample": ["rank_pairing"],
                  "fit_counterexample": ["smallest_fitting_frame"],
                  "sufficient_counterexample": ["smallest_sufficient_group"]}
BRANCH_WITNESSES = ("all_matched", "partly_matched", "no_match")


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(name + " fits all demonstrations but changes the query")
    return reasons
