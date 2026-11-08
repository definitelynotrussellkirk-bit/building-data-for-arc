"""Proposed raw or opposite-pair-cancelled T-tetromino tallies.

This opt-in family extends the exact-T scene grammar through 30x30 while
retaining the exact canonical Racket default. Every label returned here is a
deterministic Python claim, independently replayed by the native worker.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random


TASK_ID = "e971e0773705"
SETTINGS = ("raw", "cancel_opposites")
DEFAULT = {"count_mode": "raw"}
DEMO_LIMITS = (4, 6)
QUERY_LIMITS = (1, 4)
MAX_ATTEMPTS = 128
TOP_T = ((0, 0), (0, 1), (0, 2), (1, 1))
BOTTOM_T = ((0, 1), (1, 0), (1, 1), (1, 2))
GREEN = ((0, 0), (2, 0), (0, 2), (2, 2))
BLUE = ((0, 3), (2, 3), (0, 5), (2, 5))
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"count_mode"}:
        raise ValueError("settings must contain exactly count_mode")
    value = settings["count_mode"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"count_mode must be one of {SETTINGS}")
    return value


def _components(grid, connectivity=4):
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if connectivity == 8:
        directions += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        group, stack = [start], [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in pending:
                    pending.remove(point)
                    group.append(point)
                    stack.append(point)
        result.append(tuple(sorted(group)))
    return result


def _normalized(component):
    row, col = min(r for r, _ in component), min(c for _, c in component)
    return tuple(sorted((r - row, c - col) for r, c in component))


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty list matrix within 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or value not in (0, 2) for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with literal integer colors 0 and 2")
    groups = _components(grid)
    if not 1 <= len(groups) <= 70:
        raise ValueError("the proposed grammar contains 1..70 isolated T components")
    if any(_normalized(group) not in (TOP_T, BOTTOM_T) for group in groups):
        raise ValueError("every four-connected red component must be an exact vertical T tetromino")
    return True


def _kind(component):
    top = min(r for r, _ in component)
    return 0 if sum(r == top for r, _ in component) >= 3 else 1


def counts(grid, connectivity=4):
    """Return (top-bar count, bottom-bar count), with literal canonical classification."""
    validate_grid(grid)
    groups = _components(grid, connectivity)
    top = sum(_kind(group) == 0 for group in groups)
    return top, len(groups) - top


def residual_counts(top, bottom, count_mode):
    validate_settings({"count_mode": count_mode})
    if any(type(value) is not int or value < 0 for value in (top, bottom)):
        raise ValueError("orientation counts must be nonnegative literal integers")
    matched = min(top, bottom) if count_mode == "cancel_opposites" else 0
    return top - matched, bottom - matched


def emblem(top, bottom, cap=4):
    if any(type(value) is not int or value < 0 for value in (top, bottom)):
        raise ValueError("orientation counts must be nonnegative literal integers")
    if type(cap) is not int or not 0 <= cap <= 4:
        raise ValueError("the four-position emblem supports integer caps 0..4")
    output = [[0] * 6 for _ in range(3)]
    for r, c in GREEN[:min(bottom, cap)]:
        output[r][c] = 3
    for r, c in BLUE[:min(top, cap)]:
        output[r][c] = 1
    return output


def solve(grid, *, count_mode="raw"):
    return emblem(*residual_counts(*counts(grid), count_mode))


def rule_program(count_mode="cancel_opposites", *, cap=4, cap_before_cancel=False, connectivity=4):
    """Render complete named counterfactuals; program() owns the exact default."""
    validate_settings({"count_mode": count_mode})
    if type(cap) is not int or not 0 <= cap <= 4 or type(cap_before_cancel) is not bool:
        raise ValueError("cap must be an integer 0..4 and cap_before_cancel a boolean")
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    object_fn = "objects" if connectivity == 4 else "objects-8"
    before_top = f"(min a {cap})" if cap_before_cancel else "a"
    before_bottom = f"(min b {cap})" if cap_before_cancel else "b"
    matched = "(min pre-a pre-b)" if count_mode == "cancel_opposites" else "0"
    return f"""(rule! (lambda (g)
  (let* ((os (filter (lambda (o) (= (obj-color o) 2)) ({object_fn} g 0)))
         (a (count-if (lambda (o)
              (>= (count-if (lambda (p) (= (first p) (obj-r1 o))) (obj-cells o)) 3)) os))
         (b (- (length os) a))
         (pre-a {before_top}) (pre-b {before_bottom})
         (matched {matched})
         (left-a (- pre-a matched)) (left-b (- pre-b matched))
         (green (take (list (list 0 0) (list 2 0) (list 0 2) (list 2 2)) (min left-b {cap})))
         (blue (take (list (list 0 3) (list 2 3) (list 0 5) (list 2 5)) (min left-a {cap}))))
    (grid-from-fn 3 6 (lambda (r c)
      (cond ((member (list r c) green) 3)
            ((member (list r c) blue) 1)
            (else 0)))))))"""


def program(settings):
    mode = validate_settings(settings)
    return CANONICAL_PROGRAM if mode == "raw" else rule_program(mode)


def _rng(seed, purpose, index=0, attempt=0):
    material = f"{TASK_ID}/cancel-v1/{seed}/{purpose}/{index}/{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(material.encode()).digest(), "big"))


def _can_place(grid, shape, top, left):
    height, width = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in shape}
    for r, c in cells:
        if not 0 <= r < height or not 0 <= c < width or grid[r][c]:
            return False
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if (rr, cc) not in cells and 0 <= rr < height and 0 <= cc < width and grid[rr][cc]:
                return False
    return True


def _paint(grid, shape, top, left):
    for r, c in shape:
        grid[top + r][left + c] = 2


def make_scene(top, bottom, height, width, rng, *, diagonal=False):
    """Bounded random exact-T placement, with an optional diagonal-contact pair."""
    if diagonal and bottom < 2:
        raise ValueError("the teaching diagonal pair needs two bottom-bar Ts")
    for restart in range(MAX_ATTEMPTS):
        grid = [[0] * width for _ in range(height)]
        remaining_bottom = bottom
        if diagonal:
            r = rng.choice((0, height - 4))
            c = rng.choice((0, width - 5))
            _paint(grid, BOTTOM_T, r, c)
            _paint(grid, BOTTOM_T, r + 2, c + 2)
            remaining_bottom -= 2
        shapes = [TOP_T] * top + [BOTTOM_T] * remaining_bottom
        rng.shuffle(shapes)
        complete = True
        for shape in shapes:
            positions = [(r, c) for r in range(height - 1) for c in range(width - 2)]
            rng.shuffle(positions)
            selected = next(((r, c) for r, c in positions if _can_place(grid, shape, r, c)), None)
            if selected is None:
                complete = False
                break
            _paint(grid, shape, *selected)
        if complete:
            validate_grid(grid)
            if counts(grid) != (top, bottom):
                raise AssertionError("scene placement changed orientation counts")
            return grid, restart + 1
    raise RuntimeError("bounded exact-T placement exhausted")


def _spaced_starts(extent, count, object_width, rng):
    """Positive internal gaps, with the first and last object touching edges."""
    if count == 1:
        return [0]
    spare = extent - count * object_width - (count - 1)
    if spare < 0:
        raise ValueError("objects do not fit this packed axis")
    gaps = [1] * (count - 1)
    for _ in range(spare):
        gaps[rng.randrange(len(gaps))] += 1
    starts = [0]
    for gap in gaps:
        starts.append(starts[-1] + object_width + gap)
    return starts


def dense_scene(top, bottom, rng):
    """Construct 54 four-isolated Ts on shuffled slots spanning a 30x30 canvas."""
    if top + bottom != 54:
        raise ValueError("the dense stress profile requires 54 objects")
    rs, cs = _spaced_starts(30, 10, 2, rng), _spaced_starts(30, 7, 3, rng)
    corners = {(rs[0], cs[0]), (rs[0], cs[-1]), (rs[-1], cs[0]), (rs[-1], cs[-1])}
    pool = [(r, c) for r in rs for c in cs if (r, c) not in corners]
    positions = sorted(corners) + rng.sample(pool, 50)
    rng.shuffle(positions)
    shapes = [TOP_T] * top + [BOTTOM_T] * bottom
    rng.shuffle(shapes)
    grid = [[0] * 30 for _ in range(30)]
    for shape, (r, c) in zip(shapes, positions):
        _paint(grid, shape, r, c)
    validate_grid(grid)
    if counts(grid) != (top, bottom):
        raise AssertionError("dense construction changed orientation counts")
    return grid


def _geometry_counts(grid, choice):
    groups = _components(grid)
    height, width = len(grid), len(grid[0])
    if choice == "border":
        groups = [g for g in groups if not any(r in (0, height - 1) or c in (0, width - 1) for r, c in g)]
    elif choice == "upper":
        groups = [g for g in groups if 2 * min(r for r, _ in g) < height]
    elif choice == "left":
        groups = [g for g in groups if 2 * min(c for _, c in g) < width]
    elif choice == "rows":
        keys = {(min(r for r, _ in g), _kind(g)) for g in groups}
        return sum(kind == 0 for _, kind in keys), sum(kind == 1 for _, kind in keys)
    top = sum(_kind(g) == 0 for g in groups)
    return top, len(groups) - top


def _teaching_ok(grids):
    """Finite constructive teaching screen; protected independent audit is separate."""
    for mode in SETTINGS:
        targets = [solve(grid, count_mode=mode) for grid in grids]
        variants = [[counts(grid, connectivity=8) for grid in grids]]
        variants += [[_geometry_counts(grid, kind) for grid in grids] for kind in ("border", "upper", "left", "rows")]
        for readings in variants:
            wrong = [emblem(*residual_counts(*value, mode)) for value in readings]
            if wrong == targets:
                return False
    return True


def input_bank(seed):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    profile_rng = _rng(seed, "profiles")
    saturated = ((7, 2), (8, 3), (9, 3), (9, 4), (10, 2))
    first = profile_rng.choice(saturated)
    second = profile_rng.choice(saturated)[::-1]
    third = profile_rng.choice(((2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (3, 6)))
    if profile_rng.randrange(2):
        third = third[::-1]
    if profile_rng.randrange(2):
        first, second = first[::-1], second[::-1]
    tied = profile_rng.choice((2, 3, 4))
    profiles = [first, second, third, (tied, tied)]
    shapes = [(14 + profile_rng.randrange(3), 18 + profile_rng.randrange(3)),
              (14 + profile_rng.randrange(3), 18 + profile_rng.randrange(3)),
              (12 + profile_rng.randrange(3), 17 + profile_rng.randrange(3)),
              (10 + profile_rng.randrange(3), 13 + profile_rng.randrange(3))]
    for teaching_attempt in range(MAX_ATTEMPTS):
        demos, costs = [], []
        for index, ((top, bottom), (height, width)) in enumerate(zip(profiles, shapes)):
            grid, cost = make_scene(top, bottom, height, width, _rng(seed, "teaching", index, teaching_attempt), diagonal=True)
            demos.append(grid)
            costs.append(cost)
        if _teaching_ok(demos):
            break
    else:
        raise RuntimeError("bounded four-demo teaching selection exhausted")
    seen = {json.dumps(grid, separators=(",", ":")) for grid in demos}
    extra_profiles = ((4, 0), (0, 4), (1, 1), (7, 1), (1, 7), (4, 2), (2, 4), (1, 2), (2, 1), (1, 0), (0, 1))
    for index in range(4, 6):
        top, bottom = profile_rng.choice(extra_profiles)
        for attempt in range(MAX_ATTEMPTS):
            grid, cost = make_scene(top, bottom, 9 + index, 13 + index, _rng(seed, "extra-demo", index, attempt))
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                seen.add(key)
                demos.append(grid)
                costs.append(cost)
                break
        else:
            raise RuntimeError("bounded novel-demo selection exhausted")
    small = profile_rng.choice(((1, 0), (0, 1), (2, 0), (0, 2), (1, 1), (2, 1), (1, 2)))
    if seed == 0:
        small = (1, 0)
    query_counts = [small,
                    profile_rng.choice(((0, 5), (5, 0), (1, 4), (4, 1), (2, 3), (3, 2), (0, 4), (4, 0))),
                    profile_rng.choice(((9, 9), (10, 8), (8, 10), (15, 3), (3, 15), (18, 0), (0, 18))),
                    profile_rng.choice(((28, 26), (26, 28), (29, 25), (25, 29), (27, 27), (30, 24), (24, 30)))]
    queries = []
    for index, (top, bottom) in enumerate(query_counts):
        if index == 0 and seed == 0:
            grid = [[0] * 3 for _ in range(2)]
            _paint(grid, TOP_T if top else BOTTOM_T, 0, 0)
            cost = 1
        elif index == 0:
            small_rng = _rng(seed, "small-query")
            height, width = 6 + small_rng.randrange(4), 8 + small_rng.randrange(4)
            grid, cost = make_scene(top, bottom, height, width, small_rng)
        elif index == 3:
            grid, cost = dense_scene(top, bottom, _rng(seed, "dense-query")), 1
        else:
            height, width = ((12, 16) if index == 1 else (20, 24))
            grid, cost = make_scene(top, bottom, height, width, _rng(seed, "query", index))
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise AssertionError("query is not novel relative to the complete input bank")
        seen.add(key)
        queries.append(grid)
        costs.append(cost)
    return demos, queries, {
        "maximum_attempts": MAX_ATTEMPTS,
        "teaching_attempts": teaching_attempt + 1,
        "placement_attempts": costs,
        "demo_counts": [list(counts(grid)) for grid in demos],
        "query_counts": [list(value) for value in query_counts],
    }


def generate(seed, settings, demos=4, queries=4):
    mode = validate_settings(settings)
    if type(demos) is not int or not 4 <= demos <= 6 or type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("supported counts: 4..6 demonstrations and 1..4 queries")
    train_inputs, test_inputs, costs = input_bank(seed)
    return {
        "train": [{"input": deepcopy(grid), "output": solve(grid, count_mode=mode)} for grid in train_inputs[:demos]],
        "test": [{"input": deepcopy(grid), "output": solve(grid, count_mode=mode)} for grid in test_inputs[:queries]],
        "program_solution": program(settings), "settings": deepcopy(settings), "sampler": costs,
    }
