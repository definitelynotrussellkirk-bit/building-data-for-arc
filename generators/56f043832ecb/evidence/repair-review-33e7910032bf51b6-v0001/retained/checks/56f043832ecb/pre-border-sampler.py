"""Constructive inputs for the enclosed-hole area selector prototype.

The input grammar is independent of the episode's private selection setting.
Every seed produces six demonstration candidates followed by four query inputs.
The first three demonstrations are a compact teaching set: a source-like anchor,
an extrema-tie/rank-inversion scene, and a total-area versus single-cavity scene.
Query order has its own seed stream, so canvas size does not identify query turn.

Shapes are solid same-color walls around explicit cavities, with separate
leaking and solid distractors.  Component bounding boxes occupy disjoint slots
with a zero moat; no foreign object is nested inside another component's bbox.
The canonical reference's component-local hole semantics therefore preserve all
existing colored cells on this grammar, including repeated-color components.
This module generates inputs only; it supplies no reference labels.
"""
from __future__ import annotations

import hashlib
import random


DEMO_COUNT = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
DEMO_PROFILES = (
    "canonical_anchor",
    "extrema_ties",
    "total_cavity_contrast",
    "one_target",
    "compact_distractors",
    "many_components",
)
QUERY_PROFILES = ("small_query", "medium_query", "wide_query", "full_canvas_query")

# Positive cavity-cell totals in the three compulsory teaching scenes.  Their
# masks, colors, component order, orientations and placement vary independently.
TEACHING_AREAS = {
    "canonical_anchor": (2, 6),
    "extrema_ties": (1, 1, 4, 6, 6),
    "total_cavity_contrast": (3, 4, 9, 12, 12),
}

Cell = tuple[int, int]
Shape = frozenset[Cell]
Grid = list[list[int]]


def _check_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed must be an exact integer in 0..{MAX_SEED}")


def _rng(seed: int, stream: str) -> random.Random:
    digest = hashlib.sha256(f"56f043832ecb:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _normalize(cells) -> Shape:
    points = frozenset(cells)
    if not points:
        raise ValueError("a component must contain colored cells")
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def _dimensions(cells: Shape) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _frame(
    hole_h: int,
    hole_w: int,
    *,
    thickness: int = 1,
    open_gap: bool = False,
    spur: bool = False,
) -> Shape:
    """A rectangle with a cavity, optional wall gap, and optional outward spur."""
    if min(hole_h, hole_w, thickness) < 1 or (open_gap and thickness != 1):
        raise ValueError("invalid frame construction")
    h, w = hole_h + 2 * thickness, hole_w + 2 * thickness
    cells = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if not (thickness <= r < h - thickness and thickness <= c < w - thickness)
    }
    if open_gap:
        cells.remove((0, 1 + hole_w // 2))
    if spur:
        cells.add((h // 2, w))
    return _normalize(cells)


def _compartments(hole_h: int, widths: tuple[int, ...]) -> Shape:
    """One connected wall component enclosing separate rectangular cavities."""
    if hole_h < 1 or len(widths) < 2 or min(widths) < 1:
        raise ValueError("invalid compartment construction")
    h = hole_h + 2
    w = 2 + sum(widths) + len(widths) - 1
    holes: set[Cell] = set()
    left = 1
    for width in widths:
        holes.update((r, c) for r in range(1, h - 1) for c in range(left, left + width))
        left += width + 1
    return frozenset((r, c) for r in range(h) for c in range(w) if (r, c) not in holes)


def _l_frame(hole_h: int, hole_w: int, arm: int = 1) -> Shape:
    """A concave outer wall around an L cavity, with exterior zeros in its bbox."""
    if min(hole_h, hole_w) <= arm or arm < 1:
        raise ValueError("invalid L-shaped cavity")
    holes = {
        (r, c)
        for r in range(1, hole_h + 1)
        for c in range(1, hole_w + 1)
        if r <= arm or c <= arm
    }
    dilation = {
        (r + dr, c + dc)
        for r, c in holes
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }
    return _normalize(dilation - holes)


def _solid(h: int, w: int) -> Shape:
    return frozenset((r, c) for r in range(h) for c in range(w))


def _orientations(cells: Shape) -> list[Shape]:
    h, w = _dimensions(cells)
    variants = set()
    for flip_r in (False, True):
        for flip_c in (False, True):
            base = frozenset(
                (h - 1 - r if flip_r else r, w - 1 - c if flip_c else c)
                for r, c in cells
            )
            variants.add(base)
            variants.add(frozenset((c, r) for r, c in base))
    return sorted(variants, key=lambda shape: tuple(sorted(shape)))


def _bands(length: int, count: int) -> list[tuple[int, int]]:
    usable = length - count + 1
    base, extra = divmod(usable, count)
    if base < 1:
        raise ValueError("canvas cannot support requested separated slots")
    result = []
    start = 0
    for index in range(count):
        size = base + (index < extra)
        result.append((start, start + size - 1))
        start += size + 1
    return result


def _scene(
    h: int,
    w: int,
    layout: tuple[int, int],
    shapes: list[Shape],
    rng: random.Random,
    *,
    repeat_colors: tuple[tuple[int, int], ...] = (),
    canonical_palette: bool = False,
    boundary: bool = True,
) -> Grid:
    """Place independent components into a moat-separated slot partition."""
    slots = [
        (r0, c0, r1, c1)
        for r0, r1 in _bands(h, layout[0])
        for c0, c1 in _bands(w, layout[1])
    ]
    if len(shapes) > len(slots):
        raise ValueError("more components than layout slots")
    if len(shapes) < len(slots):
        slots = rng.sample(slots, len(shapes))
    palette = (2, 3, 4, 6, 7) if canonical_palette else tuple(range(1, 10))
    colors = rng.sample(palette, len(shapes))
    for target, source in repeat_colors:
        colors[target] = colors[source]
    components = list(zip(shapes, colors))
    rng.shuffle(components)
    grid = [[0] * w for _ in range(h)]
    for (shape, color), (r0, c0, r1, c1) in zip(components, slots):
        room_h, room_w = r1 - r0 + 1, c1 - c0 + 1
        allowed = [
            candidate
            for candidate in _orientations(shape)
            if _dimensions(candidate)[0] <= room_h and _dimensions(candidate)[1] <= room_w
        ]
        if not allowed:
            raise ValueError(f"component {_dimensions(shape)} does not fit slot {room_h}x{room_w}")
        selected = rng.choice(allowed)
        sh, sw = _dimensions(selected)
        row_room, col_room = room_h - sh, room_w - sw
        dr, dc = rng.randrange(row_room + 1), rng.randrange(col_room + 1)
        if boundary:
            row_edges = ([0] if r0 == 0 else []) + ([row_room] if r1 == h - 1 else [])
            col_edges = ([0] if c0 == 0 else []) + ([col_room] if c1 == w - 1 else [])
            if row_edges:
                dr = rng.choice(row_edges)
            if col_edges:
                dc = rng.choice(col_edges)
        for r, c in selected:
            grid[r0 + dr + r][c0 + dc + c] = color

    # Whole-scene symmetries retain the teaching relations but remove fixed
    # reading-order, direction and orientation associations.
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [list(reversed(row)) for row in grid]
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    return grid


def _profile(name: str, rng: random.Random) -> Grid:
    if name == "canonical_anchor":
        return _scene(8, 11, (1, 2), [_frame(1, 2), _frame(2, 3)], rng, canonical_palette=True)
    if name == "extrema_ties":
        return _scene(
            19, 29, (2, 3),
            [_frame(1, 1, thickness=3), _frame(1, 1, spur=True), _frame(2, 3, spur=True),
             _compartments(2, (1, 2)), _frame(2, 2, spur=True), _frame(7, 7, open_gap=True)],
            rng, repeat_colors=((2, 0),),
        )
    if name == "total_cavity_contrast":
        return _scene(
            21, 27, (2, 3),
            [_compartments(2, (3, 3)), _frame(3, 3), _compartments(2, (1, 1)),
             _l_frame(2, 2), _l_frame(4, 4, 2), _frame(4, 4, open_gap=True, spur=True)],
            rng,
        )
    if name == "one_target":
        return _scene(12, 17, (1, 1), [_l_frame(rng.randint(5, 8), rng.randint(8, 12), 2)], rng)
    if name == "compact_distractors":
        return _scene(
            14, 21, (2, 3),
            [_frame(1, 1, thickness=2), _frame(2, 2), _compartments(1, (1, 1)),
             _l_frame(3, 3), _frame(3, 3, open_gap=True), _solid(2, rng.randint(2, 4))],
            rng, repeat_colors=((3, 0),), boundary=False,
        )
    if name == "many_components":
        return _scene(
            23, 29, (3, 3),
            [_frame(1, 3), _frame(3, 3), _frame(1, 1, thickness=2), _l_frame(3, 4),
             _compartments(2, (2, 2)), _frame(3, 3, open_gap=True), _frame(4, 4),
             _compartments(1, (1, 1, 1)), _solid(2, rng.randint(2, 5))],
            rng,
        )
    if name == "small_query":
        return _scene(
            9, 13, (2, 2),
            [_frame(1, 1), _frame(1, 2, spur=True), _frame(1, 1, open_gap=True)], rng,
        )
    if name == "medium_query":
        return _scene(
            16, 20, (2, 3),
            [_frame(2, 2), _frame(1, 1, thickness=2), _compartments(2, (1, 1)),
             _l_frame(4, 3), _frame(4, 3, open_gap=True), _frame(3, 2)],
            rng, repeat_colors=((5, 1),),
        )
    if name == "wide_query":
        return _scene(
            24, 27, (2, 3),
            [_l_frame(6, 6, 2), _frame(1, 2, thickness=3), _compartments(3, (2, 3)),
             _frame(4, 4, spur=True), _frame(7, 6, open_gap=True), _frame(1, rng.randint(6, 8))],
            rng,
        )
    if name == "full_canvas_query":
        return _scene(
            30, 30, (3, 3),
            [_frame(6, 7), _frame(1, 1, thickness=3), _compartments(3, (2, 2)),
             _frame(7, 7, open_gap=True), _l_frame(6, 6, 2), _frame(4, 5, spur=True),
             _frame(3, 4, thickness=2), _compartments(2, (1, 2, 1)), _frame(1, 1)],
            rng, repeat_colors=((1, 0),),
        )
    raise ValueError(f"unknown input profile: {name}")


def profile_names(seed: int) -> list[str]:
    """Private names aligned to the deterministic six-demo/four-query bank."""
    _check_seed(seed)
    queries = list(QUERY_PROFILES)
    _rng(seed, "query-order").shuffle(queries)
    return list(DEMO_PROFILES) + queries


def sample_inputs(seed: int) -> list[Grid]:
    """Return ten fresh, distinct lawful inputs, independent of private rules.

    Counts are applied by the adapter: take the first requested demos from
    ``bank[:6]`` and the first requested queries from ``bank[6:]``.  Consequently
    one-query and four-query requests share the exact first query.  Profile
    dimensions are distinct even after transpose, so uniqueness is guaranteed
    constructively rather than repaired by duplicating or dropping examples.
    """
    return [_profile(name, _rng(seed, name)) for name in profile_names(seed)]
