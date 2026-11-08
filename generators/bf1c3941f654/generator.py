"""Generator for ``bf1c3941f654`` — recolor red cells enclosed by blue frames.

The canonical rule recognizes each closed rectangular color-1 frame and changes
only color-2 cells strictly inside that frame to color 4.  Color-2 distractors
outside every frame remain unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "bf1c3941f654"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c2152e6fcfee"

SUMMARY = (
    "Find every closed rectangular color-1 frame. Recolor each color-2 cell "
    "strictly inside any such frame to color 4, while preserving color-2 "
    "distractors outside all frames and leaving every other cell unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the input palette is exactly {0, 1, 2}",
    "there are exactly two disjoint closed rectangular color-1 frames",
    "each frame contains at least one red cell and at least one zero interior cell",
    "the total number of red cells inside frames is 2..4",
    "there are 1..3 red distractors outside every frame",
]

COUNTER_HYPOTHESES = [
    "recolor every red cell, including outside distractors",
    "recolor exactly one marker per frame",
    "fill an entire frame interior with yellow",
    "use a fixed frame position or fixed frame size",
    "treat an open or irregular color-1 boundary as a valid enclosure",
    "copy the modal color or use marker count alone as the answer",
]

# Only caller-visible, exact instance properties are declared.  Frame sizes,
# positions, per-frame red allocation, and layout orientation remain deterministic
# nuisance variation rather than pseudo-axes that an override cannot recover.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-shaped with canonical-profile prior",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-shaped with canonical-profile prior",
        "valid": "12..16",
    },
    "n_frames": {
        "type": "int",
        "default": "2",
        "valid": "2",
    },
    "inside_twos": {
        "type": "int",
        "default": "difficulty-shaped 2..4",
        "valid": "2..4",
    },
    "outside_twos": {
        "type": "int",
        "default": "difficulty-shaped 1..3",
        "valid": "1..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


@dataclass(frozen=True)
class Frame:
    r1: int
    c1: int
    r2: int
    c2: int
    cells: frozenset[tuple[int, int]]

    @property
    def h(self) -> int:
        return self.r2 - self.r1 + 1

    @property
    def w(self) -> int:
        return self.c2 - self.c1 + 1

    @property
    def perimeter_size(self) -> int:
        return 2 * (self.h + self.w) - 4

    def interior(self) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(self.r1 + 1, self.r2)
            for c in range(self.c1 + 1, self.c2)
        ]

    def contains_strictly(self, r: int, c: int) -> bool:
        return self.r1 < r < self.r2 and self.c1 < c < self.c2


# The three joint canonical input profiles, derived from every train and held-out
# test pair: (height, width, ((frame_h, frame_w, inside_reds), ...), outside_reds).
_CANONICAL_PROFILES = (
    (10, 12, ((4, 5, 1), (4, 5, 1)), 2),
    (11, 13, ((4, 4, 1), (5, 6, 2)), 2),
    (12, 14, ((5, 5, 2), (5, 5, 2)), 2),
)

_ALLOWED_OVERRIDES = frozenset(AXES)


def _valid_grid_shape(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _color_components(
    grid: list[list[int]], color: int
) -> list[frozenset[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    components: list[frozenset[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    component.add((rr, cc))
                    stack.append((rr, cc))
        components.append(frozenset(component))
    return components


def _perimeter_cells(r1: int, c1: int, r2: int, c2: int) -> frozenset[tuple[int, int]]:
    cells = {(r1, c) for c in range(c1, c2 + 1)}
    cells.update((r2, c) for c in range(c1, c2 + 1))
    cells.update((r, c1) for r in range(r1 + 1, r2))
    cells.update((r, c2) for r in range(r1 + 1, r2))
    return frozenset(cells)


def _frame_from_component(component: frozenset[tuple[int, int]]) -> Frame | None:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    expected = _perimeter_cells(r1, c1, r2, c2)
    if component != expected:
        return None
    return Frame(r1, c1, r2, c2, component)


def find_frames(grid: list[list[int]]) -> tuple[list[Frame], int]:
    """Return valid color-1 frames and the number of invalid color-1 components."""
    frames: list[Frame] = []
    invalid = 0
    for component in _color_components(grid, 1):
        frame = _frame_from_component(component)
        if frame is None:
            invalid += 1
        else:
            frames.append(frame)
    frames.sort(key=lambda frame: (frame.r1, frame.c1, frame.r2, frame.c2))
    return frames, invalid


def _inside_frame_indices(frames: Iterable[Frame], r: int, c: int) -> list[int]:
    return [index for index, frame in enumerate(frames) if frame.contains_strictly(r, c)]


def semantic_profile(grid: list[list[int]]) -> dict[str, object]:
    """Task-linked, returned-grid-only features used by tests and censuses."""
    frames, invalid_components = find_frames(grid)
    inside_counts = []
    zero_counts = []
    for frame in frames:
        interior = frame.interior()
        inside_counts.append(sum(grid[r][c] == 2 for r, c in interior))
        zero_counts.append(sum(grid[r][c] == 0 for r, c in interior))
    outside_twos = 0
    multiply_enclosed_twos = 0
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 2:
                continue
            memberships = _inside_frame_indices(frames, r, c)
            if not memberships:
                outside_twos += 1
            elif len(memberships) > 1:
                multiply_enclosed_twos += 1
    signatures = tuple(
        sorted(
            (frame.h, frame.w, count)
            for frame, count in zip(frames, inside_counts)
        )
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette": tuple(sorted({value for row in grid for value in row})),
        "n_frames": len(frames),
        "invalid_color1_components": invalid_components,
        "frame_signatures": signatures,
        "inside_counts": tuple(inside_counts),
        "inside_twos": sum(inside_counts),
        "outside_twos": outside_twos,
        "interior_zero_counts": tuple(zero_counts),
        "multiply_enclosed_twos": multiply_enclosed_twos,
    }


def observe_overrides(grid) -> dict[str, int]:
    profile = semantic_profile(grid)
    return {
        "grid_h": int(profile["grid_h"]),
        "grid_w": int(profile["grid_w"]),
        "n_frames": int(profile["n_frames"]),
        "inside_twos": int(profile["inside_twos"]),
        "outside_twos": int(profile["outside_twos"]),
    }


def canonical_like(grid: list[list[int]]) -> bool:
    """Strict empirical-manifold predicate from all official input pairs."""
    profile = semantic_profile(grid)
    key = (
        profile["grid_h"],
        profile["grid_w"],
        profile["frame_signatures"],
        profile["outside_twos"],
    )
    canonical_keys = {
        (h, w, tuple(sorted(signatures)), outside)
        for h, w, signatures, outside in _CANONICAL_PROFILES
    }
    return (
        profile["palette"] == (0, 1, 2)
        and profile["invalid_color1_components"] == 0
        and profile["multiply_enclosed_twos"] == 0
        and all(count >= 1 for count in profile["interior_zero_counts"])
        and key in canonical_keys
    )


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only mirror of the canonical rule; Racket remains authoritative."""
    if not _valid_grid_shape(grid):
        raise ValueError("rule_mirror expects a rectangular non-empty grid")
    frames, _ = find_frames(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2 and any(frame.contains_strictly(r, c) for frame in frames):
                out[r][c] = 4
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and shortcut-teaching scenes."""
    if not _valid_grid_shape(grid):
        return ["grid must be a non-empty rectangular list of rows"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (10 <= h <= 14 and 12 <= w <= 16):
        errors.append(f"grid dimensions {h}x{w} outside 10..14 by 12..16")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    profile = semantic_profile(grid)
    if profile["palette"] != (0, 1, 2):
        errors.append(f"input palette must be exactly (0, 1, 2), got {profile['palette']}")
    if profile["invalid_color1_components"]:
        errors.append("every color-1 component must be one complete rectangular frame")
    if profile["n_frames"] != 2:
        errors.append(f"expected exactly 2 frames, got {profile['n_frames']}")
    if profile["multiply_enclosed_twos"]:
        errors.append("a red cell lies inside more than one frame")

    inside_counts = tuple(profile["inside_counts"])
    zero_counts = tuple(profile["interior_zero_counts"])
    if len(inside_counts) == 2:
        if any(count < 1 for count in inside_counts):
            errors.append("each frame must contain at least one red cell")
        if any(count < 1 for count in zero_counts):
            errors.append("each frame must retain at least one zero interior cell")
    inside_total = int(profile["inside_twos"])
    outside_total = int(profile["outside_twos"])
    if not 2 <= inside_total <= 4:
        errors.append(f"inside red count must be 2..4, got {inside_total}")
    if not 1 <= outside_total <= 3:
        errors.append(f"outside red count must be 1..3, got {outside_total}")
    return errors


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi) -> int:
    """Explicit overrides use the full declared range in every difficulty band."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _positive_allocations(total: int, capacities: tuple[int, int]) -> list[tuple[int, int]]:
    return [
        (left, total - left)
        for left in range(1, total)
        if left <= capacities[0] and total - left <= capacities[1]
    ]


def _choose_boxes(
    h: int,
    w: int,
    sizes: tuple[tuple[int, int], tuple[int, int]],
    rng,
) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    """Construct two separated frame boxes without rejection-heavy search."""
    (fh1, fw1), (fh2, fw2) = sizes
    modes = []
    if fw1 + fw2 + 1 <= w:
        modes.append("side_by_side")
    if fh1 + fh2 + 1 <= h:
        modes.append("stacked")
    if not modes:
        raise ValueError(f"frame sizes {sizes!r} do not fit lawfully in {h}x{w}")

    mode = rng.choice(modes)
    if mode == "side_by_side":
        max_gap = w - fw1 - fw2
        gap = rng.randint(1, max_gap)
        slack = w - fw1 - fw2 - gap
        left = rng.randint(0, slack)
        c1 = left
        c2 = c1 + fw1 + gap
        r1 = rng.randint(0, h - fh1)
        r2 = rng.randint(0, h - fh2)
        return (r1, c1, r1 + fh1 - 1, c1 + fw1 - 1), (
            r2, c2, r2 + fh2 - 1, c2 + fw2 - 1
        )

    max_gap = h - fh1 - fh2
    gap = rng.randint(1, max_gap)
    slack = h - fh1 - fh2 - gap
    top = rng.randint(0, slack)
    r1 = top
    r2 = r1 + fh1 + gap
    c1 = rng.randint(0, w - fw1)
    c2 = rng.randint(0, w - fw2)
    return (r1, c1, r1 + fh1 - 1, c1 + fw1 - 1), (
        r2, c2, r2 + fh2 - 1, c2 + fw2 - 1
    )


def _choose_general_sizes(
    h: int,
    w: int,
    inside_total: int,
    rng,
) -> tuple[tuple[tuple[int, int], tuple[int, int]], tuple[int, int]]:
    size_options = [
        (fh, fw)
        for fh in range(4, min(6, h) + 1)
        for fw in range(4, min(7, w) + 1)
    ]
    candidates = []
    for first in size_options:
        for second in size_options:
            if not (
                first[1] + second[1] + 1 <= w
                or first[0] + second[0] + 1 <= h
            ):
                continue
            capacities = (
                (first[0] - 2) * (first[1] - 2) - 1,
                (second[0] - 2) * (second[1] - 2) - 1,
            )
            allocations = _positive_allocations(inside_total, capacities)
            if allocations:
                candidates.append(((first, second), allocations))
    if not candidates:
        raise ValueError(
            f"no lawful two-frame layout for {h}x{w} with {inside_total} inside reds"
        )
    sizes, allocations = rng.choice(candidates)
    return sizes, rng.choice(allocations)


def _draw_scene(
    h: int,
    w: int,
    sizes: tuple[tuple[int, int], tuple[int, int]],
    allocation: tuple[int, int],
    outside_twos: int,
    rng,
) -> list[list[int]]:
    boxes = _choose_boxes(h, w, sizes, rng)
    grid = full_grid(h, w, 0)
    for box in boxes:
        draw_frame(grid, *box, 1)

    for box, count in zip(boxes, allocation):
        r1, c1, r2, c2 = box
        interior = [
            (r, c)
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
        ]
        if len(interior) <= count:
            raise ValueError("frame interior needs at least one zero after red placement")
        for r, c in rng.sample(interior, count):
            grid[r][c] = 2

    outside_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if all(not (r1 <= r <= r2 and c1 <= c <= c2) for r1, c1, r2, c2 in boxes)
    ]
    if len(outside_candidates) < outside_twos:
        raise ValueError("not enough cells outside frames for distractors")
    for r, c in rng.sample(outside_candidates, outside_twos):
        grid[r][c] = 2
    return grid

def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_rng = ctx.draw_rng("profile")
    layout_rng = ctx.draw_rng("layout")
    band = difficulty or "medium"

    # A deliberately strong empirical-manifold prior keeps official joint
    # dimensions and frame morphology common without copying literal positions.
    # Any explicit override bypasses the prior so the full declared domain stays
    # exact and band-independent.
    prior_rate = {"easy": 0.60, "medium": 0.50, "hard": 0.40}[band]
    force_multi_witness = (
        not overrides and band in ("easy", "medium") and sample_index % 3 == 1
    )
    use_canonical_profile = (
        not overrides
        and not force_multi_witness
        and profile_rng.random() < prior_rate
    )

    if use_canonical_profile:
        choices = {
            "easy": (_CANONICAL_PROFILES[0],),
            "medium": _CANONICAL_PROFILES,
            "hard": (_CANONICAL_PROFILES[2],),
        }[band]
        h0, w0, signatures, outside0 = profile_rng.choice(choices)
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n_frames = ctx.draw_int("n_frames", 2, 2)
        inside_total = ctx.draw_int(
            "inside_twos", sum(signature[2] for signature in signatures),
            sum(signature[2] for signature in signatures)
        )
        outside_total = ctx.draw_int("outside_twos", outside0, outside0)
        sizes = tuple((fh, fw) for fh, fw, _ in signatures)
        allocation = tuple(count for _, _, count in signatures)
    else:
        bands = {
            "easy": ((10, 11), (12, 13), (2, 3), (1, 2)),
            "medium": ((10, 13), (12, 15), (2, 4), (1, 3)),
            "hard": ((12, 14), (14, 16), (3, 4), (2, 3)),
        }
        h_band, w_band, inside_band, outside_band = bands[band]
        if force_multi_witness:
            inside_band = (3, 3)
        h = _banded_int(ctx, overrides, "grid_h", *h_band, 10, 14)
        w = _banded_int(ctx, overrides, "grid_w", *w_band, 12, 16)
        n_frames = _banded_int(ctx, overrides, "n_frames", 2, 2, 2, 2)
        inside_total = _banded_int(
            ctx, overrides, "inside_twos", *inside_band, 2, 4
        )
        outside_total = _banded_int(
            ctx, overrides, "outside_twos", *outside_band, 1, 3
        )
        sizes, allocation = _choose_general_sizes(
            h, w, inside_total, layout_rng
        )

    if n_frames != 2:
        raise ValueError("this task's teaching distribution requires exactly two frames")
    grid = _draw_scene(
        h,
        w,
        sizes,
        allocation,
        outside_total,
        layout_rng,
    )
    errors = self_check(grid, difficulty=difficulty, meta=overrides)
    if errors:
        raise AssertionError(f"internal generator contract violation: {errors}")
    return grid
