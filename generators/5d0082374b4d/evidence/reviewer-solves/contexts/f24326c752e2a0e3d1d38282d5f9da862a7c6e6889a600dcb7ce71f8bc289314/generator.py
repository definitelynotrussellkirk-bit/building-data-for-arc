"""Generator for Corner-Marker Stripe Fill (canonical task 5d0082374b4d).

Each input contains two or three disjoint color-1 rectangular frames.  The two
cells just inside the top-left and top-right corners of each frame are distinct
marker colors ``a`` and ``b``.  The Racket oracle preserves the frame borders,
erases everything else, and fills each interior with vertical columns
``a, b, a, b, ...`` starting at the left interior edge.

Normal draws deliberately include multiple frames, repeated stripe columns,
both odd and even interior widths, varied frame sizes/placements, and distinct
marker colors across frames.  Those choices rebut identity, single-frame,
solid-fill, horizontal-stripe, fixed-size, fixed-position, and modal-color
shortcuts while staying inside the canonical grammar.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "5d0082374b4d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "80261197592b"
SUMMARY = (
    "Two or three separated color-1 rectangle frames contain distinct marker "
    "colors at their top interior corners; every interior is filled with "
    "alternating vertical marker-color stripes starting from the left."
)

INVARIANTS = [
    "background is 0 and every nonzero cell belongs to a frame or one of its two markers",
    "normal draws contain exactly 2 or 3 disjoint full-perimeter color-1 frames",
    "canonical frames are at least 4x4; normal generated frames are at least 4x5",
    "each frame has distinct non-{0,1} markers at (r1+1,c1+1) and (r1+1,c2-1)",
    "all other input-interior cells are 0 and all marker colors are distinct across frames",
    "every normal draw has an interior width of at least 3, so the alternating repeat is visible",
]

HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_markers", "single_marker")
LAWFUL_DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "9..14",
        "doc": "canvas height; every boundary is valid in every difficulty band",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "12..20",
        "doc": "canvas width; every boundary is valid in every difficulty band",
    },
    "n_frames": {
        "type": "int",
        "default": "difficulty-skewed rng",
        "valid": "2..3",
        "doc": "exact number of independently striped frames",
    },
    "texture": {
        "type": "str",
        "default": "rng helpful palette ordering",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": "marker-palette ordering; degenerate probe names are intentionally off-distribution",
    },
}

# Every palette contains the same lawful colors, but in a different ordering.
# Applying the same keyed shuffle to different orderings makes each helpful
# texture behaviorally live without assigning semantic meaning to ARC colors.
_TEXTURE_PALETTES = {
    "default": (2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7, 3, 5, 8, 9),
    "cool": (8, 9, 3, 6, 2, 4, 5, 7),
    "varied": (2, 8, 4, 9, 3, 7, 5, 6),
}


def _inclusive_cells(r1: int, c1: int, r2: int, c2: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
    }


def _perimeter(r1: int, c1: int, r2: int, c2: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _connected_components(grid, color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _grid_validation_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC 30x30 limit: {h}x{w}")
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != w:
            errors.append("grid must be rectangular")
            return errors
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in row
        ):
            errors.append("grid colors must be integers in 0..9")
            return errors
    return errors


def _analyze(grid) -> dict:
    errors = _grid_validation_errors(grid)
    if errors:
        return {"errors": errors, "frames": [], "facts": {}}

    h, w = len(grid), len(grid[0])
    frames = []
    frame_cells: set[tuple[int, int]] = set()
    for component in _connected_components(grid, 1):
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        expected = _perimeter(r1, c1, r2, c2)
        if component != expected:
            errors.append(
                "color-1 component is not one complete rectangle perimeter: "
                f"bbox={(r1, c1, r2, c2)}, cells={len(component)}, expected={len(expected)}"
            )
            continue
        outer_h, outer_w = r2 - r1 + 1, c2 - c1 + 1
        if outer_h < 4 or outer_w < 4:
            errors.append(
                f"frame {(r1, c1, r2, c2)} is too small: {outer_h}x{outer_w}"
            )
            continue
        frame_cells.update(component)
        frames.append(
            {
                "r1": r1,
                "c1": c1,
                "r2": r2,
                "c2": c2,
                "outer_h": outer_h,
                "outer_w": outer_w,
                "inner_h": outer_h - 2,
                "inner_w": outer_w - 2,
            }
        )

    frames.sort(key=lambda frame: (frame["r1"], frame["c1"]))
    if not 1 <= len(frames) <= 3:
        errors.append(f"expected 1-3 complete frames, found {len(frames)}")

    # Frame rectangles may not overlap. Edge-adjacent color-1 borders would
    # already have merged into a malformed component above; diagonal contact is
    # harmless, though normal generated layouts leave a full blank separator.
    for index, left in enumerate(frames):
        for right in frames[index + 1 :]:
            separated = (
                left["r2"] < right["r1"]
                or right["r2"] < left["r1"]
                or left["c2"] < right["c1"]
                or right["c2"] < left["c1"]
            )
            if not separated:
                errors.append(
                    "frame bounding boxes overlap: "
                    f"{(left['r1'], left['c1'], left['r2'], left['c2'])} and "
                    f"{(right['r1'], right['c1'], right['r2'], right['c2'])}"
                )

    allowed_nonzero = set(frame_cells)
    marker_colors: list[int] = []
    for frame in frames:
        r1, c1, r2, c2 = (
            frame["r1"],
            frame["c1"],
            frame["r2"],
            frame["c2"],
        )
        left_marker = (r1 + 1, c1 + 1)
        right_marker = (r1 + 1, c2 - 1)
        a = grid[left_marker[0]][left_marker[1]]
        b = grid[right_marker[0]][right_marker[1]]
        frame["a"] = a
        frame["b"] = b
        frame["right_marker_overwritten"] = frame["inner_w"] % 2 == 1
        if a in (0, 1) or b in (0, 1):
            errors.append(
                f"frame {(r1, c1, r2, c2)} markers must both be non-{{0,1}}, got {(a, b)}"
            )
        if a == b:
            errors.append(
                f"frame {(r1, c1, r2, c2)} markers must be distinct, got {a}"
            )
        marker_colors.extend((a, b))
        allowed_nonzero.update((left_marker, right_marker))

        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if (r, c) in (left_marker, right_marker):
                    continue
                if grid[r][c] != 0:
                    errors.append(
                        f"unexpected nonzero interior cell at {(r, c)}: {grid[r][c]}"
                    )

    if marker_colors and len(set(marker_colors)) != len(marker_colors):
        errors.append(
            "marker colors must be distinct across frames in the teaching grammar: "
            f"{marker_colors}"
        )

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in allowed_nonzero:
                errors.append(
                    f"unexpected nonzero cell outside frame grammar at {(r, c)}: {grid[r][c]}"
                )

    if frames and max(frame["inner_w"] for frame in frames) < 3:
        errors.append("no frame visibly repeats the alternating stripe pattern")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "n_frames": len(frames),
        "outer_heights": [frame["outer_h"] for frame in frames],
        "outer_widths": [frame["outer_w"] for frame in frames],
        "inner_widths": [frame["inner_w"] for frame in frames],
        "odd_inner_width_count": sum(frame["inner_w"] % 2 == 1 for frame in frames),
        "even_inner_width_count": sum(frame["inner_w"] % 2 == 0 for frame in frames),
        "right_marker_overwrite_count": sum(
            frame["right_marker_overwritten"] for frame in frames
        ),
        "marker_pairs": [[frame.get("a"), frame.get("b")] for frame in frames],
        "marker_color_count": len(set(marker_colors)),
        "left_marker_less_count": sum(
            frame.get("a", 0) < frame.get("b", 0) for frame in frames
        ),
        "left_marker_greater_count": sum(
            frame.get("a", 0) > frame.get("b", 0) for frame in frames
        ),
    }
    return {"errors": errors, "frames": frames, "facts": facts}


def semantic_features(grid) -> dict:
    """Return task-linked observables used by focused tests and review census."""
    analysis = _analyze(grid)
    return {
        "errors": list(analysis["errors"]),
        **analysis["facts"],
    }


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    facts = analysis["facts"]
    return {"n_frames": facts.get("n_frames", 0)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", {})
        if isinstance(candidate, dict):
            overrides = candidate
    unknown = set(overrides) - set(AXES)
    if unknown:
        errors.append(f"unknown override(s): {sorted(unknown)}")
    if overrides and not errors:
        observed = observe_overrides(grid)
        if "n_frames" in overrides and observed["n_frames"] != int(overrides["n_frames"]):
            errors.append(
                f"override n_frames requested {overrides['n_frames']!r}, "
                f"observed {observed['n_frames']!r}"
            )
    return errors


def expected_output(grid) -> list[list[int]]:
    """Python mirror for testing only; the Racket rule remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid stripe-frame input: " + "; ".join(analysis["errors"]))
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for frame in analysis["frames"]:
        r1, c1, r2, c2 = (
            frame["r1"],
            frame["c1"],
            frame["r2"],
            frame["c2"],
        )
        draw_frame(out, r1, c1, r2, c2, 1)
        a, b = frame["a"], frame["b"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                out[r][c] = a if (c - (c1 + 1)) % 2 == 0 else b
    return out


def _split_two(total: int, minimum: int, maximum: int, rng) -> tuple[int, int, int, int]:
    """Choose two separated segment starts/sizes within one dimension."""
    candidates = []
    for first_size in range(minimum, min(maximum, total) + 1):
        for second_size in range(minimum, min(maximum, total) + 1):
            for gap in range(1, 4):
                used = first_size + gap + second_size
                if used > total:
                    continue
                for before in range(total - used + 1):
                    candidates.append(
                        (before, first_size, before + first_size + gap, second_size)
                    )
    if not candidates:
        raise ValueError(
            f"cannot split dimension {total} into two {minimum}..{maximum} segments"
        )
    return rng.choice(candidates)


def _split_three(total: int, minimum: int, maximum: int, rng) -> list[tuple[int, int]]:
    candidates = []
    for a in range(minimum, min(maximum, total) + 1):
        for b in range(minimum, min(maximum, total) + 1):
            for c in range(minimum, min(maximum, total) + 1):
                for gap1 in range(1, 3):
                    for gap2 in range(1, 3):
                        used = a + gap1 + b + gap2 + c
                        if used > total:
                            continue
                        for before in range(total - used + 1):
                            candidates.append(
                                [
                                    (before, a),
                                    (before + a + gap1, b),
                                    (before + a + gap1 + b + gap2, c),
                                ]
                            )
    if not candidates:
        raise ValueError(
            f"cannot split dimension {total} into three {minimum}..{maximum} segments"
        )
    return rng.choice(candidates)


def _random_frame_in_slot(
    row_start: int,
    row_size: int,
    col_start: int,
    col_size: int,
    rng,
) -> tuple[int, int, int, int]:
    frame_h = rng.randint(4, min(7, row_size))
    frame_w = rng.randint(5, min(8, col_size))
    r1 = rng.randint(row_start, row_start + row_size - frame_h)
    c1 = rng.randint(col_start, col_start + col_size - frame_w)
    return r1, c1, r1 + frame_h - 1, c1 + frame_w - 1


def _layout_frames(h: int, w: int, n_frames: int, rng) -> list[tuple[int, int, int, int]]:
    if n_frames == 2:
        styles = ["horizontal", "vertical"]
        style = rng.choice(styles)
        if style == "horizontal":
            c1, width1, c2, width2 = _split_two(w, 5, 8, rng)
            row1 = rng.randint(0, h - 4)
            height1 = rng.randint(4, min(7, h - row1))
            row2 = rng.randint(0, h - 4)
            height2 = rng.randint(4, min(7, h - row2))
            return [
                (row1, c1, row1 + height1 - 1, c1 + width1 - 1),
                (row2, c2, row2 + height2 - 1, c2 + width2 - 1),
            ]
        r1, height1, r2, height2 = _split_two(h, 4, 7, rng)
        width1 = rng.randint(5, min(8, w))
        width2 = rng.randint(5, min(8, w))
        col1 = rng.randint(0, w - width1)
        col2 = rng.randint(0, w - width2)
        return [
            (r1, col1, r1 + height1 - 1, col1 + width1 - 1),
            (r2, col2, r2 + height2 - 1, col2 + width2 - 1),
        ]

    if n_frames != 3:
        raise ValueError(f"n_frames must be 2 or 3, got {n_frames}")

    styles = ["mixed"]
    if w >= 17:
        styles.append("horizontal")
    if h >= 14:
        styles.append("vertical")
    style = rng.choice(styles)
    if style == "horizontal":
        columns = _split_three(w, 5, 6, rng)
        frames = []
        for col, width in columns:
            height = rng.randint(4, min(7, h))
            row = rng.randint(0, h - height)
            frames.append((row, col, row + height - 1, col + width - 1))
        return frames
    if style == "vertical":
        rows = _split_three(h, 4, 5, rng)
        frames = []
        for row, height in rows:
            width = rng.randint(5, min(8, w))
            col = rng.randint(0, w - width)
            frames.append((row, col, row + height - 1, col + width - 1))
        return frames

    top, top_h, bottom, bottom_h = _split_two(h, 4, 7, rng)
    left, left_w, right, right_w = _split_two(w, 5, 8, rng)
    slots = [
        (top, top_h, left, left_w),
        (top, top_h, right, right_w),
        (bottom, bottom_h, left, left_w),
        (bottom, bottom_h, right, right_w),
    ]
    omitted = rng.randrange(4)
    return [
        _random_frame_in_slot(*slot, rng)
        for index, slot in enumerate(slots)
        if index != omitted
    ]


def _marker_colors(texture: str, n_frames: int, rng) -> list[tuple[int, int]]:
    palette = list(_TEXTURE_PALETTES[texture])
    rng.shuffle(palette)
    needed = 2 * n_frames
    if needed > len(palette):
        raise ValueError(f"not enough distinct marker colors for {n_frames} frames")
    return [tuple(palette[index : index + 2]) for index in range(0, needed, 2)]


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(10, 14, 0)
    if name == "no_frames":
        grid[2][2] = 4
        grid[2][8] = 6
    elif name == "no_markers":
        draw_frame(grid, 1, 1, 6, 8, 1)
    elif name == "single_marker":
        draw_frame(grid, 1, 1, 6, 8, 1)
        grid[2][2] = 4
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        if set(overrides) != {"texture"}:
            raise ValueError(
                f"degenerate texture {requested_texture!r} is incompatible with other overrides"
            )
        return _draw_from_degenerate(requested_texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 9, 14)
    w = ctx.draw_int_diff("grid_w", 12, 20)
    n_frames = ctx.draw_int_diff("n_frames", 2, 3)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    frames = _layout_frames(h, w, n_frames, ctx.draw_rng("layout"))
    marker_pairs = _marker_colors(texture, n_frames, ctx.draw_rng("markers"))
    grid = full_grid(h, w, 0)
    for (r1, c1, r2, c2), (a, b) in zip(frames, marker_pairs):
        draw_frame(grid, r1, c1, r2, c2, 1)
        grid[r1 + 1][c1 + 1] = a
        grid[r1 + 1][c2 - 1] = b

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-specific must-reject structural near-misses."""
    base = generate(
        9173,
        11,
        difficulty="hard",
        grid_h=12,
        grid_w=16,
        n_frames=2,
        texture="varied",
    )
    frames = _analyze(base)["frames"]
    first = frames[0]
    r1, c1, r2, c2 = first["r1"], first["c1"], first["r2"], first["c2"]

    broken_border = [row[:] for row in base]
    broken_border[r1][c1 + 1] = 0

    misplaced_marker = [row[:] for row in base]
    marker_color = misplaced_marker[r1 + 1][c1 + 1]
    misplaced_marker[r1 + 1][c1 + 1] = 0
    misplaced_marker[r1 + 2][c1 + 1] = marker_color

    duplicate_markers = [row[:] for row in base]
    duplicate_markers[r1 + 1][c2 - 1] = duplicate_markers[r1 + 1][c1 + 1]

    outside_distractor = [row[:] for row in base]
    occupied = set().union(
        *(
            _inclusive_cells(f["r1"], f["c1"], f["r2"], f["c2"])
            for f in frames
        )
    )
    outside = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if (r, c) not in occupied
    )
    outside_distractor[outside[0]][outside[1]] = 9

    third_marker = [row[:] for row in base]
    third_marker[r1 + 2][c1 + 2] = 9

    return [
        ("broken_frame_border", broken_border),
        ("marker_moved_off_corner", misplaced_marker),
        ("duplicate_marker_colors", duplicate_markers),
        ("outside_colored_distractor", outside_distractor),
        ("extra_interior_marker", third_marker),
    ]
