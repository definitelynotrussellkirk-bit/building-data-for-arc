"""Native parametric family for 70913cf98cee.

The canonical setting performs the exact header-directed recolor.  The
alternative first performs that same recolor, then finds exact two-cell
4-connected components in the *recolored* destination colors and cycles each
qualifying component to the next destination color in legend order.

Inputs are sampled independently of the hidden setting.  The sampler includes
components whose post-recolor topology is created or destroyed by adjacency to
pre-existing destination cells, so the second stage cannot be replaced by an
original-grid size test.
"""
from __future__ import annotations

from collections import deque
import copy
import hashlib
import random
from typing import Iterable

TASK_ID = "70913cf98cee"
SETTINGS = ("direct", "cycle_dominoes")

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (let* ((nonzero (filter (lambda (v) (not (= v 0))) (row g 0))) (pairs (let loop ((xs nonzero)) (if (empty? xs) (list) (cons (list (first xs) (second xs)) (loop (rest (rest xs)))))))) (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= r 0) (at g r c) (let ((hit (find-first (lambda (pair) (= (first pair) (at g r c))) pairs))) (if (eq? hit #f) (at g r c) (second hit)))))))))"

CYCLE_DOMINOES_PROGRAM = r"""(rule!
  (lambda (g)
    (let* ((nonzero (filter (lambda (v) (not (= v 0))) (row g 0)))
           (pairs
            (let loop ((xs nonzero))
              (if (empty? xs)
                  (list)
                  (cons (list (first xs) (second xs))
                        (loop (rest (rest xs)))))))
           (mapped
            (grid-from-fn (rows g) (cols g)
              (lambda (r c)
                (if (= r 0)
                    (at g r c)
                    (let ((hit (find-first
                                (lambda (pair) (= (first pair) (at g r c)))
                                pairs)))
                      (if (eq? hit #f) (at g r c) (second hit)))))))
           (next-destination
            (lambda (color)
              (let loop ((remaining pairs))
                (if (empty? remaining)
                    color
                    (if (= (second (first remaining)) color)
                        (if (empty? (rest remaining))
                            (second (first pairs))
                            (second (second remaining)))
                        (loop (rest remaining))))))))
      (for/fold ((out mapped)) ((obj (in-list (objects mapped 0))))
        (let ((destination-pair
               (find-first
                (lambda (pair) (= (second pair) (obj-color obj)))
                pairs)))
          (if (and (not (eq? destination-pair #f))
                   (= (obj-size obj) 2)
                   (all? (lambda (cell) (>= (first cell) 2))
                         (obj-cells obj)))
              (for/fold ((acc out)) ((cell (in-list (obj-cells obj))))
                (set-cell acc
                          (first cell)
                          (second cell)
                          (next-destination (obj-color obj))))
              out))))))"""

# Full banks are always materialized before count slicing, giving count-independent
# prefixes.  Query roles are seed-shuffled so no fixed query index encodes size.
_DEMO_PROFILES = (
    (12, 14, 2, 6),
    (14, 17, 3, 12),
    (16, 20, 4, 14),
    (9, 12, 2, 4),
    (18, 13, 3, 10),
    (13, 20, 4, 12),
)
_QUERY_PROFILES = (
    (11, 15, 2, 6),
    (17, 12, 3, 10),
    (18, 23, 4, 18),
    (30, 30, 4, 40),
)


def _strict_setting(settings: dict) -> str:
    if type(settings) is not dict or set(settings) != {"postprocess"}:
        raise ValueError("settings must contain exactly postprocess")
    value = settings["postprocess"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"postprocess must be one of {SETTINGS}")
    return value


def program(settings: dict) -> str:
    mode = _strict_setting(settings)
    return CANONICAL_PROGRAM if mode == "direct" else CYCLE_DOMINOES_PROGRAM


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _derive(seed: int, label: str, index: int = 0) -> int:
    raw = f"{TASK_ID}|{seed}|{label}|{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _pairs(grid: list[list[int]]) -> list[tuple[int, int]]:
    nonzero = [value for value in grid[0] if value != 0]
    if len(nonzero) < 4 or len(nonzero) % 2:
        raise ValueError("input header must contain an even sequence of at least two pairs")
    return list(zip(nonzero[::2], nonzero[1::2]))


def _components4(grid: list[list[int]], color: int, *, row0: int = 2) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r in range(row0, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def apply_python(grid: list[list[int]], mode: str) -> list[list[int]]:
    """Independent deterministic label claim; protected Racket verifies it."""
    if mode not in SETTINGS:
        raise ValueError("unknown mode")
    pairs = _pairs(grid)
    mapping = dict(pairs)
    mapped = [
        list(row) if r == 0 else [mapping.get(value, value) for value in row]
        for r, row in enumerate(grid)
    ]
    if mode == "direct":
        return mapped

    destinations = [dst for _src, dst in pairs]
    successor = {
        destination: destinations[(index + 1) % len(destinations)]
        for index, destination in enumerate(destinations)
    }
    out = [list(row) for row in mapped]
    for destination in destinations:
        for component in _components4(mapped, destination):
            if len(component) == 2:
                for r, c in component:
                    out[r][c] = successor[destination]
    return out


def _axis_slots(start: int, stop: int) -> list[int]:
    """Origins for separated 3x3 slots, retaining the far boundary."""
    if stop - start < 3:
        raise ValueError("axis cannot fit a 3-cell module")
    positions = list(range(start, stop - 2, 4))
    edge = stop - 3
    if positions and edge != positions[-1] and edge - positions[-1] < 4:
        positions[-1] = edge
    elif edge not in positions:
        positions.append(edge)
    if len(positions) != len(set(positions)):
        raise AssertionError("duplicate slot origins")
    return positions


def _transform(cells: list[tuple[int, int, int]], rng: random.Random) -> list[tuple[int, int, int]]:
    """Apply a random dihedral transform inside a fixed 3x3 slot."""
    turns = rng.randrange(4)
    mirror = bool(rng.randrange(2))
    out = []
    for r, c, color in cells:
        if mirror:
            c = 2 - c
        for _ in range(turns):
            r, c = c, 2 - r
        out.append((r, c, color))
    return out


def _axis_preserving_transform(
    cells: list[tuple[int, int, int]], rng: random.Random
) -> list[tuple[int, int, int]]:
    """Random flips/half-turns that keep horizontal and vertical distinct."""
    flip_rows = bool(rng.randrange(2))
    flip_cols = bool(rng.randrange(2))
    return [
        (2 - r if flip_rows else r, 2 - c if flip_cols else c, color)
        for r, c, color in cells
    ]


def _module(kind: str, src: int, dst: int, neutral: int) -> list[tuple[int, int, int]]:
    modules = {
        # A creates an exact domino from unlike colors.
        "created_h": [(0, 0, src), (0, 1, dst)],
        "created_v": [(0, 0, src), (1, 0, dst)],
        # An original source domino becomes a nonqualifying triomino after A.
        "destroy_h": [(0, 0, src), (0, 1, src), (0, 2, dst)],
        "destroy_v": [(0, 0, src), (1, 0, src), (2, 0, dst)],
        # Qualifiers that do not require a pre-existing destination seed.
        "source_h": [(0, 0, src), (0, 1, src)],
        "source_v": [(0, 0, src), (1, 0, src)],
        # Qualifiers present before A; B applies to all destination components.
        "dest_h": [(0, 0, dst), (0, 1, dst)],
        "dest_v": [(0, 0, dst), (1, 0, dst)],
        # Nonqualifying controls.
        "source_tri_l": [(0, 0, src), (1, 0, src), (1, 1, src)],
        "dest_tri_h": [(0, 0, dst), (0, 1, dst), (0, 2, dst)],
        # Four-neighbor versus eight-neighbor traps.
        "diag_two": [(0, 0, src), (1, 1, src)],
        "diag_domino_plus": [(0, 0, dst), (0, 1, dst), (1, 2, dst)],
        # Unmapped distractors remain unchanged through both stages.
        "neutral_h": [(0, 0, neutral), (0, 1, neutral)],
        "neutral_l": [(0, 0, neutral), (1, 0, neutral), (1, 1, neutral)],
    }
    try:
        return list(modules[kind])
    except KeyError as exc:
        raise ValueError(f"unknown module kind {kind}") from exc


def _module_plan(n_pairs: int, count: int) -> list[tuple[int, str]]:
    # The smallest scenes still expose both directions of the sequential
    # dependency: A can create an exact domino and can destroy an apparent
    # source domino by merging it into a triomino.  For every profile with
    # three or more legend pairs, the core then gives *every* destination an
    # exact qualifier and includes both orientations.  This prevents a
    # two-demo lesson from accidentally teaching only the last pair, only one
    # orientation, or an ambiguous two-color cycle direction.
    plan: list[tuple[int, str]] = [
        (0, "created_h"),
        (1 % n_pairs, "destroy_v"),
        (1 % n_pairs, "created_v"),
        (0, "destroy_h"),
    ]
    for pair_index in range(n_pairs):
        plan.append((pair_index, "source_h" if pair_index % 2 == 0 else "source_v"))
    for pair_index in range(n_pairs):
        plan.append((pair_index, "dest_v" if pair_index % 2 == 0 else "dest_h"))
    # Two diagonally touching mapped cells are separate 4-connected singletons.
    # This pins both the exact-size predicate and the intended connectivity.
    plan.append((0, "diag_two"))
    # A visible unmapped component supports fixed-intermediate nuisance controls.
    plan.append((0, "neutral_h"))

    extension = (
        "source_tri_l", "dest_tri_h", "diag_domino_plus",
        "neutral_l", "created_h", "created_v",
        "destroy_h", "destroy_v", "source_h", "source_v",
        "dest_h", "dest_v",
    )
    index = 0
    while len(plan) < count:
        plan.append((index % n_pairs, extension[index % len(extension)]))
        index += 1
    return plan[:count]


def _validate_scene(grid: list[list[int]], n_pairs: int) -> None:
    if not (1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30):
        raise ValueError("scene dimensions outside 1..30")
    if any(type(row) is not list or len(row) != len(grid[0]) for row in grid):
        raise ValueError("ragged scene")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("scene has non-ARC cell")
    if any(grid[1]):
        raise ValueError("separator row must be blank")
    pairs = _pairs(grid)
    if len(pairs) != n_pairs or len({value for pair in pairs for value in pair}) != 2 * n_pairs:
        raise ValueError("header pair declaration mismatch")
    direct = apply_python(grid, "direct")
    alternate = apply_python(grid, "cycle_dominoes")
    if direct == alternate:
        raise ValueError("scene does not distinguish the two settings")


def _scene(seed: int, profile: tuple[int, int, int, int], role: str, index: int) -> list[list[int]]:
    h, w, n_pairs, module_count = profile
    if not (7 <= h <= 30 and 9 <= w <= 30 and 2 <= n_pairs <= 4):
        raise ValueError("invalid internal profile")
    rng = random.Random(_derive(seed, role, index))
    colors = rng.sample(range(1, 10), 2 * n_pairs + 1)
    pairs = [(colors[2 * i], colors[2 * i + 1]) for i in range(n_pairs)]
    neutral = colors[-1]
    offset = rng.randrange(min(2, w - 3 * n_pairs) + 1)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for pair_index, (src, dst) in enumerate(pairs):
        start = offset + 3 * pair_index
        grid[0][start] = src
        grid[0][start + 2] = dst

    row_slots = _axis_slots(2, h)
    col_slots = _axis_slots(0, w)
    slots = [(r, c) for r in row_slots for c in col_slots]
    if module_count > len(slots):
        raise ValueError(f"profile requests {module_count} modules but only {len(slots)} fit")

    # Reserve a right-edge created qualifier and a bottom-edge destroyed
    # qualifier.  The rest are shuffled, so nuisance positions vary
    # independently of the hidden rule setting.
    right_top = (row_slots[0], col_slots[-1])
    bottom_left = (row_slots[-1], col_slots[0])
    reserved = [right_top, bottom_left]
    available = [slot for slot in slots if slot not in set(reserved)]
    rng.shuffle(available)
    chosen_slots = reserved + available[: module_count - len(reserved)]

    plan = _module_plan(n_pairs, module_count)
    for module_index, ((pair_index, kind), (top, left)) in enumerate(zip(plan, chosen_slots)):
        src, dst = pairs[pair_index]
        cells = _module(kind, src, dst, neutral)
        if module_index == 0:
            # Shift the horizontal created domino to the far edge of its 3x3 slot.
            cells = [(dr, dc + 1, color) for dr, dc, color in cells]
        elif module_index < min(module_count, 6 + 2 * n_pairs):
            # Preserve the planned orientation coverage in the minimum lesson;
            # flips and half-turns still vary the exact local geometry.
            cells = _axis_preserving_transform(cells, rng)
        else:
            cells = _transform(cells, rng)
        for dr, dc, color in cells:
            r, c = top + dr, left + dc
            if not (2 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                raise ValueError("internal module overlap or bounds failure")
            grid[r][c] = color

    _validate_scene(grid, n_pairs)
    return grid


def _bank(seed: int, profiles: Iterable[tuple[int, int, int, int]], role: str) -> list[list[list[int]]]:
    profiles = list(profiles)
    order_rng = random.Random(_derive(seed, role + ":order"))
    if role == "demo":
        # The minimum lesson always begins with the 3-pair and 4-pair teaching
        # profiles.  Their order, geometry, palette, and placements still vary
        # by seed; only the semantic coverage is fixed.
        anchors = [1, 2]
        order_rng.shuffle(anchors)
        tail = [index for index in range(len(profiles)) if index not in anchors]
        order_rng.shuffle(tail)
        order = anchors + tail
    else:
        order = list(range(len(profiles)))
        order_rng.shuffle(order)
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    for public_index, profile_index in enumerate(order):
        # A collision is extraordinarily unlikely, but fail-safe deterministic
        # resampling makes the distinct-input contract total.
        for salt in range(16):
            grid = _scene(seed + salt, profiles[profile_index], role, public_index)
            key = repr(grid)
            if key not in seen:
                seen.add(key)
                result.append(grid)
                break
        else:
            raise ValueError("unable to produce distinct episode inputs")
    return result


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    mode = _strict_setting(settings)

    demo_inputs = _bank(seed, _DEMO_PROFILES, "demo")
    query_inputs = _bank(seed, _QUERY_PROFILES, "query")
    train = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
        for grid in demo_inputs[:demos]
    ]
    test = [
        {"input": copy.deepcopy(grid), "output": apply_python(grid, mode)}
        for grid in query_inputs[:queries]
    ]
    return {"train": train, "test": test, "program_solution": program(settings)}
