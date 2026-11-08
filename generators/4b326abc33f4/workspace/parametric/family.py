"""Pure sampler, mirrors, and adversarial helpers for 4b326abc33f4.

The native adapter keeps its input distribution independent of the private
setting.  Step A orders valid frames by the canonical bbox order and extracts
their side-seed colors.  Step B either uses that sequence locally or rotates it
one position so every frame receives the next frame's color.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_bytes().decode("utf-8")
CYCLIC_NEXT_PROGRAM = (HERE / "cyclic-next.rkt").read_bytes().decode("utf-8")
MODES = ("local", "cyclic_next")
PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)

# (height, width, bboxes as r0,c0,r1,c1, distractor count)
PROFILES = {
    # The tall first frame starts before but is centered below the short second
    # frame; its much larger area also breaks center-row and area-order rivals.
    "demo0": (14, 18, ((0, 1, 10, 4), (3, 11, 6, 15), (9, 7, 13, 16)), 4),
    "demo1": (18, 16, ((0, 9, 4, 13), (4, 1, 9, 5), (8, 10, 13, 15), (12, 2, 17, 7)), 5),
    "demo2": (16, 20, ((1, 12, 5, 17), (5, 2, 10, 6), (10, 11, 15, 16)), 5),
    "demo3": (20, 22, ((0, 2, 6, 7), (2, 15, 8, 21), (11, 1, 17, 6), (12, 14, 19, 20)), 7),
    "demo4": (22, 18, ((1, 10, 7, 16), (7, 1, 13, 6), (14, 9, 21, 15)), 6),
    "demo5": (26, 26, ((0, 1, 7, 8), (3, 17, 10, 24), (15, 0, 23, 7), (17, 17, 25, 25)), 10),
    "query0": (12, 20, ((0, 0, 4, 4), (1, 13, 6, 19), (7, 6, 11, 11)), 4),
    "query1": (20, 16, ((1, 9, 5, 13), (5, 1, 10, 5), (10, 10, 15, 15), (14, 2, 19, 7)), 6),
    "query2": (24, 24, ((0, 4, 7, 10), (5, 16, 12, 23), (15, 1, 23, 8)), 8),
    "query3": (30, 30, ((0, 1, 8, 9), (2, 20, 10, 29), (18, 0, 27, 8), (20, 19, 29, 28)), 12),
}
DEMO_PROFILES = tuple(f"demo{i}" for i in range(6))
QUERY_PROFILES = tuple(f"query{i}" for i in range(4))


def _rng(seed: int, label: str) -> random.Random:
    digest = sha256(f"4b326abc33f4|{seed}|{label}|v1".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _validate_grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    w = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= w <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers in 0..9")
    return len(grid), w


def analyze_frames(grid):
    h, w = _validate_grid(grid)
    fives = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    seen = set()
    components = []
    for start in sorted(fives):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = set()
        while stack:
            r, c = stack.pop()
            component.add((r, c))
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in fives and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(component)
    records = []
    for component in components:
        rs = [r for r, _ in component]
        cs = [c for _, c in component]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        if component != border or r1 - r0 < 3 or c1 - c0 < 3:
            raise ValueError("color-5 component is not a rectangular hollow frame")
        mid = (r0 + r1) // 2
        candidates = []
        if c0 > 0 and grid[mid][c0 - 1] not in (0, 5):
            candidates.append(("left", grid[mid][c0 - 1], (mid, c0 - 1)))
        if c1 + 1 < w and grid[mid][c1 + 1] not in (0, 5):
            candidates.append(("right", grid[mid][c1 + 1], (mid, c1 + 1)))
        if len(candidates) != 1:
            raise ValueError(f"frame {(r0, r1, c0, c1)} needs exactly one side seed")
        side, color, position = candidates[0]
        records.append({
            "bbox": (r0, r1, c0, c1),
            "seed_side": side,
            "seed_color": color,
            "seed_position": position,
            "boundary_contacts": tuple(name for name, hit in (
                ("top", r0 == 0), ("bottom", r1 == h - 1),
                ("left", c0 == 0), ("right", c1 == w - 1)) if hit),
        })
    return sorted(records, key=lambda row: row["bbox"])


def seed_sequence(grid):
    return tuple(frame["seed_color"] for frame in analyze_frames(grid))


def rotated_seed_sequence(sequence):
    sequence = tuple(sequence)
    return sequence[1:] + sequence[:1] if sequence else sequence


def _paint(grid, frames, colors):
    out = deepcopy(grid)
    for frame, color in zip(frames, colors):
        r0, r1, c0, c1 = frame["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = color
    return out


def apply_mode(grid, mode: str):
    if mode not in MODES:
        raise ValueError(f"unknown assignment mode: {mode!r}")
    frames = analyze_frames(grid)
    colors = tuple(frame["seed_color"] for frame in frames)
    if mode == "cyclic_next":
        colors = rotated_seed_sequence(colors)
    return _paint(grid, frames, colors)


def _apply_assignment(grid, assignment):
    frames = analyze_frames(grid)
    return _paint(grid, frames, assignment(frames))


def _previous(frames):
    colors = tuple(frame["seed_color"] for frame in frames)
    return colors[-1:] + colors[:-1]


def _first_everywhere(frames):
    return (frames[0]["seed_color"],) * len(frames)


def _last_everywhere(frames):
    return (frames[-1]["seed_color"],) * len(frames)


def _sorted_colors(frames):
    return tuple(sorted(frame["seed_color"] for frame in frames))


def _left_to_right_next_output(grid):
    frames = analyze_frames(grid)
    lr = sorted(frames, key=lambda row: (row["bbox"][2], row["bbox"][0], row["bbox"]))
    shifted = rotated_seed_sequence(tuple(frame["seed_color"] for frame in lr))
    by_bbox = {frame["bbox"]: color for frame, color in zip(lr, shifted)}
    return _paint(grid, frames, tuple(by_bbox[frame["bbox"]] for frame in frames))


def _largest_only_output(grid):
    frames = analyze_frames(grid)
    largest = max(frames, key=lambda frame: ((frame["bbox"][1] - frame["bbox"][0] - 1) *
                                             (frame["bbox"][3] - frame["bbox"][2] - 1), frame["bbox"]))
    out = deepcopy(grid)
    r0, r1, c0, c1 = largest["bbox"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            out[r][c] = largest["seed_color"]
    return out


def _ordered_next_output(grid, key):
    frames = analyze_frames(grid)
    ordered = sorted(frames, key=key)
    shifted = rotated_seed_sequence(tuple(frame["seed_color"] for frame in ordered))
    by_bbox = {frame["bbox"]: color for frame, color in zip(ordered, shifted)}
    return _paint(grid, frames, tuple(by_bbox[frame["bbox"]] for frame in frames))


def _center_row_order_next_output(grid):
    return _ordered_next_output(
        grid,
        lambda frame: (
            frame["bbox"][0] + frame["bbox"][1],
            frame["bbox"][2] + frame["bbox"][3],
            frame["bbox"],
        ),
    )


def _area_order_next_output(grid):
    return _ordered_next_output(
        grid,
        lambda frame: (
            (frame["bbox"][1] - frame["bbox"][0] - 1)
            * (frame["bbox"][3] - frame["bbox"][2] - 1),
            frame["bbox"],
        ),
    )


def _color_rank_order_next_output(grid):
    return _ordered_next_output(grid, lambda frame: (frame["seed_color"], frame["bbox"]))


def _side_hybrid_output(grid, *, next_side):
    frames = analyze_frames(grid)
    local = tuple(frame["seed_color"] for frame in frames)
    shifted = rotated_seed_sequence(local)
    colors = tuple(
        shifted[index] if frame["seed_side"] == next_side else local[index]
        for index, frame in enumerate(frames)
    )
    return _paint(grid, frames, colors)


def _rotate_prefix_or_suffix_output(grid, *, prefix):
    frames = analyze_frames(grid)
    colors = [frame["seed_color"] for frame in frames]
    if len(colors) >= 3:
        if prefix:
            colors[:3] = rotated_seed_sequence(colors[:3])
        else:
            colors[-3:] = rotated_seed_sequence(colors[-3:])
    return _paint(grid, frames, colors)


RIVALS = {
    "cyclic_previous": lambda grid: _apply_assignment(grid, _previous),
    "first_seed_everywhere": lambda grid: _apply_assignment(grid, _first_everywhere),
    "last_seed_everywhere": lambda grid: _apply_assignment(grid, _last_everywhere),
    "sort_seed_colors": lambda grid: _apply_assignment(grid, _sorted_colors),
    "global_left_to_right_next": _left_to_right_next_output,
    "center_row_order_next": _center_row_order_next_output,
    "area_order_next": _area_order_next_output,
    "color_rank_order_next": _color_rank_order_next_output,
    "left_side_next_right_local": lambda grid: _side_hybrid_output(grid, next_side="left"),
    "right_side_next_left_local": lambda grid: _side_hybrid_output(grid, next_side="right"),
    "rotate_first_three_only": lambda grid: _rotate_prefix_or_suffix_output(grid, prefix=True),
    "rotate_last_three_only": lambda grid: _rotate_prefix_or_suffix_output(grid, prefix=False),
    "fill_largest_frame_only": _largest_only_output,
}


def setting_survivors(demos):
    return [mode for mode in MODES if all(apply_mode(pair["input"], mode) == pair["output"] for pair in demos)]


def rival_survivors(demos, mode):
    del mode
    return [name for name, rival in RIVALS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]


def _transform_bbox(bbox, h, w, transform):
    r0, c0, r1, c1 = bbox
    if transform == "identity":
        return bbox
    if transform == "hflip":
        return (r0, w - 1 - c1, r1, w - 1 - c0)
    if transform == "vflip":
        return (h - 1 - r1, c0, h - 1 - r0, c1)
    if transform == "rot180":
        return (h - 1 - r1, w - 1 - c1, h - 1 - r0, w - 1 - c0)
    raise ValueError(transform)


def _safe_distractor_cells(h, w, bboxes, seed_positions):
    forbidden = set(seed_positions)
    for r0, c0, r1, c1 in bboxes:
        for r in range(max(0, r0 - 1), min(h, r1 + 2)):
            for c in range(max(0, c0 - 1), min(w, c1 + 2)):
                forbidden.add((r, c))
    return [(r, c) for r in range(h) for c in range(w) if (r, c) not in forbidden]


def _color_rank_next_assignment(sequence):
    sequence = tuple(sequence)
    order = sorted(range(len(sequence)), key=lambda index: sequence[index])
    ranked_colors = tuple(sequence[index] for index in order)
    shifted = rotated_seed_sequence(ranked_colors)
    result = list(sequence)
    for index, color in zip(order, shifted):
        result[index] = color
    return tuple(result)


def _teaching_colors(rng, count):
    """Draw a sequence that cannot collapse into numeric-rank shortcuts."""
    for _ in range(256):
        values = list(PALETTE)
        rng.shuffle(values)
        seq = tuple(values[:count])
        ranked = {tuple(sorted(seq)), tuple(sorted(seq, reverse=True))}
        rank_next = _color_rank_next_assignment(seq)
        if (seq not in ranked and rotated_seed_sequence(seq) not in ranked
                and rank_next not in {seq, rotated_seed_sequence(seq)}):
            return seq
    raise AssertionError("could not draw a rank-resistant teaching color sequence")


def build_scene(profile: str, seed: int, *, seed_colors=None, transform=None, distractor_colors=None):
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}")
    h, w, raw_bboxes, distractor_count = PROFILES[profile]
    rng = _rng(seed, profile)
    if transform is None:
        transforms = ("identity", "hflip") if profile in {"demo0", "demo1"} else (
            "identity", "hflip", "vflip", "rot180"
        )
        transform = transforms[rng.randrange(len(transforms))]
    bboxes = [_transform_bbox(bbox, h, w, transform) for bbox in raw_bboxes]
    bboxes = sorted(bboxes, key=lambda bbox: (bbox[0], bbox[2], bbox[1], bbox[3]))
    if seed_colors is None:
        seed_colors = _teaching_colors(rng, len(bboxes))
    if type(seed_colors) not in (list, tuple) or len(seed_colors) != len(bboxes):
        raise ValueError("seed_colors must match the frame count")
    if any(type(color) is not int or color not in PALETTE for color in seed_colors):
        raise ValueError("seed colors must be nonzero non-5 ARC colors")

    grid = [[0 for _ in range(w)] for _ in range(h)]
    seed_positions = []
    side_flip = rng.randrange(2)
    for index, (bbox, color) in enumerate(zip(bboxes, seed_colors)):
        r0, c0, r1, c1 = bbox
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    if grid[r][c] != 0:
                        raise ValueError("profile frames overlap")
                    grid[r][c] = 5
        mid = (r0 + r1) // 2
        if c0 == 0:
            side = "right"
        elif c1 == w - 1:
            side = "left"
        else:
            side = "left" if (side_flip + index) % 2 == 0 else "right"
        position = (mid, c0 - 1) if side == "left" else (mid, c1 + 1)
        if grid[position[0]][position[1]] != 0:
            raise ValueError("profile seed collides")
        grid[position[0]][position[1]] = int(color)
        seed_positions.append(position)

    candidates = _safe_distractor_cells(h, w, bboxes, seed_positions)
    rng.shuffle(candidates)
    if distractor_colors is None:
        distractor_colors = [PALETTE[(seed + i * 3) % len(PALETTE)] for i in range(distractor_count)]
    for (r, c), color in zip(candidates[:distractor_count], distractor_colors):
        grid[r][c] = int(color)

    frames = analyze_frames(grid)
    if len(frames) != len(bboxes):
        raise AssertionError("scene construction lost a frame")
    return grid


def geometry_signature(grid):
    h, w = _validate_grid(grid)
    frames = analyze_frames(grid)
    return (h, w, tuple((frame["bbox"], frame["seed_side"]) for frame in frames))


def has_reading_order_confound(grid):
    frames = analyze_frames(grid)
    canonical = [frame["bbox"] for frame in frames]
    left_to_right = [frame["bbox"] for frame in sorted(frames, key=lambda row: (row["bbox"][2], row["bbox"][0], row["bbox"]))]
    return canonical != left_to_right


def crossed_controls(seed: int):
    a = build_scene("demo0", seed, seed_colors=(1, 7, 3), transform="identity")
    b = build_scene("demo0", seed, seed_colors=(8, 2, 6), transform="identity")
    c = build_scene("demo0", seed + 1, seed_colors=(1, 7, 3), transform="identity")
    d = build_scene("query0", seed + 2, seed_colors=(1, 7, 3), transform="identity")
    return {
        "same_geometry_different_intermediate": (a, b),
        "same_intermediate_different_geometry": (c, d),
    }
