"""Generator for the cyan-frame crosshair task (canonical family 41e4d17e).

Input grids contain one or two separated odd-sized rectangular outlines in
color 1 on cyan (8).  The rule draws a full-grid horizontal and vertical ray in
color 6 through every frame center, replacing cyan cells only and preserving
all frame pixels.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "2acfd448f58b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d929eea715e7"
SUMMARY = (
    "One or two odd rectangular 1-frames on cyan(8); color 6 fills every "
    "cyan cell on each frame-center row and column."
)
EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 0.25

POSITION_BIASES = (
    "spread",
    "corners",
    "diagonal",
    "row_aligned",
    "col_aligned",
)
ODD_SIZES = (3, 5, 7, 9)
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 9..22",
        "valid": "9..22",
        "doc": "Exact input height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 9..22",
        "valid": "9..22",
        "doc": "Exact input width.",
    },
    "n_frames": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of separated rectangular outlines.",
    },
    "frame_h_min": {
        "type": "int",
        "default": "3",
        "valid": "3|5|7|9",
        "doc": "Inclusive minimum odd frame height.",
    },
    "frame_h_max": {
        "type": "int",
        "default": "difficulty-weighted odd cap",
        "valid": "3|5|7|9",
        "doc": "Inclusive maximum odd frame height.",
    },
    "frame_w_min": {
        "type": "int",
        "default": "3",
        "valid": "3|5|7|9",
        "doc": "Inclusive minimum odd frame width.",
    },
    "frame_w_max": {
        "type": "int",
        "default": "difficulty-weighted odd cap",
        "valid": "3|5|7|9",
        "doc": "Inclusive maximum odd frame width.",
    },
    "position_bias": {
        "type": "str",
        "default": "six-example teaching schedule",
        "valid": "spread|corners|diagonal|row_aligned|col_aligned",
        "doc": "Observable relationship among the frame centers.",
    },
}
INVARIANTS = [
    "background is cyan (8), and all non-background input cells are color 1",
    "there are exactly one or two 4-connected rectangular-outline frames",
    "every frame has odd height and odd width in 3..9, so its center is unique",
    "frames have a one-cell exterior margin and at least one cyan cell between them",
    "the output changes only cyan cells on frame-center rows or columns to color 6",
]


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _scheduled_profile(sample_index: int) -> str:
    return (
        "canonical_single",
        "canonical_pair",
        "row_aligned_pair",
        "col_aligned_pair",
        "varied_single",
        "varied_pair",
    )[sample_index % EXAMPLES_NEEDED]


def _default_cap(band: str) -> int:
    return {"easy": 5, "medium": 7, "hard": 9}[band]


def _draw_odd_interval(
    ctx, prefix: str, band: str, *, canonical_defaults: bool
) -> tuple[int, int]:
    min_label = f"frame_{prefix}_min"
    max_label = f"frame_{prefix}_max"
    min_overridden = min_label in ctx.overrides
    max_overridden = max_label in ctx.overrides

    if max_overridden and not min_overridden:
        maximum = ctx.draw_choice(max_label, ODD_SIZES)
        minimum = ctx.draw_choice(min_label, (3,))
        return minimum, maximum

    if min_overridden:
        minimum = ctx.draw_choice(min_label, ODD_SIZES)
    elif canonical_defaults:
        minimum = ctx.draw_choice(min_label, (5,))
    else:
        minimum = ctx.draw_choice(min_label, (3,))

    legal_maxima = tuple(size for size in ODD_SIZES if size >= minimum)
    if max_overridden:
        maximum = ctx.draw_choice(max_label, legal_maxima)
    elif canonical_defaults:
        maximum = ctx.draw_choice(max_label, (5,))
    else:
        requested_cap = max(minimum, _default_cap(band))
        maximum = ctx.draw_choice(max_label, (requested_cap,))
    return minimum, maximum


def _box_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return ar1 + 1 < br0 or br1 + 1 < ar0 or ac1 + 1 < bc0 or bc1 + 1 < ac0


def _positions(height: int, width: int, fh: int, fw: int):
    for row in range(1, height - fh):
        for col in range(1, width - fw):
            yield row, col, row + fh - 1, col + fw - 1


def _center(box: tuple[int, int, int, int]) -> tuple[int, int]:
    r0, c0, r1, c1 = box
    return (r0 + r1) // 2, (c0 + c1) // 2


def _single_score(
    box: tuple[int, int, int, int],
    *,
    bias: str,
    height: int,
    width: int,
) -> tuple[int, ...]:
    row, col = _center(box)
    if bias == "corners":
        return (row + col, row, col)
    if bias == "diagonal":
        return (abs(row - col), row + col, row, col)
    if bias == "row_aligned":
        return (abs(2 * row - (height - 1)), col, row)
    if bias == "col_aligned":
        return (abs(2 * col - (width - 1)), row, col)
    return (
        abs(2 * row - (height - 1)) + abs(2 * col - (width - 1)),
        row,
        col,
    )


def _pair_score(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    *,
    bias: str,
    height: int,
    width: int,
) -> tuple[int, ...] | None:
    r1, c1 = _center(first)
    r2, c2 = _center(second)
    dr, dc = abs(r1 - r2), abs(c1 - c2)
    if bias == "row_aligned" and r1 != r2:
        return None
    if bias == "col_aligned" and c1 != c2:
        return None
    if bias in {"spread", "corners", "diagonal"} and (r1 == r2 or c1 == c2):
        return None

    if bias == "row_aligned":
        primary = -dc
    elif bias == "col_aligned":
        primary = -dr
    elif bias == "diagonal":
        primary = abs(dr - dc)
    else:
        primary = -(dr + dc)
    edge_spread = min(r1 + c1, r2 + c2) + min(
        (height - 1 - r1) + (width - 1 - c1),
        (height - 1 - r2) + (width - 1 - c2),
    )
    return (primary, edge_spread, min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))


def _choose_boxes(
    *,
    height: int,
    width: int,
    sizes: list[tuple[int, int]],
    bias: str,
    rng,
) -> list[tuple[int, int, int, int]]:
    candidates = [
        list(_positions(height, width, fh, fw))
        for fh, fw in sizes
    ]
    if any(not rows for rows in candidates):
        raise ValueError(
            f"frame sizes {sizes} do not fit {height}x{width} with exterior margin"
        )
    if len(sizes) == 1:
        if bias == "spread":
            return [rng.choice(candidates[0])]
        ranked = sorted(
            candidates[0],
            key=lambda box: _single_score(
                box, bias=bias, height=height, width=width
            ),
        )
        window = max(1, min(len(ranked), max(4, len(ranked) // 4)))
        return [rng.choice(ranked[:window])]

    first_rows, second_rows = candidates

    def legal(first, second, *, aligned: str | None = None) -> bool:
        if not _separated(first, second):
            return False
        r1, c1 = _center(first)
        r2, c2 = _center(second)
        if aligned == "row":
            return r1 == r2
        if aligned == "col":
            return c1 == c2
        return r1 != r2 and c1 != c2

    if bias in {"row_aligned", "col_aligned"}:
        axis = 0 if bias == "row_aligned" else 1
        first_by_center: dict[int, list[tuple[int, int, int, int]]] = {}
        second_by_center: dict[int, list[tuple[int, int, int, int]]] = {}
        for box in first_rows:
            first_by_center.setdefault(_center(box)[axis], []).append(box)
        for box in second_rows:
            second_by_center.setdefault(_center(box)[axis], []).append(box)
        common = sorted(set(first_by_center) & set(second_by_center))
        rng.shuffle(common)
        for center_value in common:
            left = list(first_by_center[center_value])
            right = list(second_by_center[center_value])
            rng.shuffle(left)
            rng.shuffle(right)
            for first in left:
                for second in right:
                    if legal(
                        first,
                        second,
                        aligned="row" if axis == 0 else "col",
                    ):
                        return [first, second]
        raise ValueError(
            f"cannot align two separated frame centers for {bias!r} in "
            f"{height}x{width}"
        )

    def distance(box, target: tuple[int, int]) -> int:
        row, col = _center(box)
        return abs(row - target[0]) + abs(col - target[1])

    if bias == "corners":
        orientations = [
            ((1, 1), (height - 2, width - 2)),
            ((1, width - 2), (height - 2, 1)),
        ]
        rng.shuffle(orientations)
        target_pairs = orientations
    elif bias == "diagonal":
        target_pairs = [
            (
                (max(1, height // 3), max(1, width // 3)),
                (min(height - 2, 2 * height // 3), min(width - 2, 2 * width // 3)),
            ),
            (
                (max(1, height // 3), min(width - 2, 2 * width // 3)),
                (min(height - 2, 2 * height // 3), max(1, width // 3)),
            ),
        ]
        rng.shuffle(target_pairs)
    else:
        target_pairs = []

    for first_target, second_target in target_pairs:
        first_ranked = sorted(first_rows, key=lambda box: distance(box, first_target))
        second_ranked = sorted(second_rows, key=lambda box: distance(box, second_target))
        first_window = first_ranked[: max(4, min(24, len(first_ranked)))]
        second_window = second_ranked[: max(4, min(24, len(second_ranked)))]
        rng.shuffle(first_window)
        rng.shuffle(second_window)
        for first in first_window:
            for second in second_window:
                if legal(first, second):
                    return [first, second]
        for first in first_ranked:
            for second in second_ranked:
                if legal(first, second):
                    return [first, second]

    first_order = list(first_rows)
    second_order = list(second_rows)
    rng.shuffle(first_order)
    rng.shuffle(second_order)
    for first in first_order:
        for second in second_order:
            if legal(first, second):
                return [first, second]
    raise ValueError(
        f"cannot place two separated frames {sizes} in {height}x{width} "
        f"with position_bias={bias!r}"
    )


def _size_options(minimum: int, maximum: int, grid_dim: int) -> tuple[int, ...]:
    return tuple(
        size
        for size in ODD_SIZES
        if minimum <= size <= maximum and size <= grid_dim - 2
    )


def _candidate_size_sets(
    *,
    profile: str,
    n_frames: int,
    h_options: tuple[int, ...],
    w_options: tuple[int, ...],
    rng,
) -> list[list[tuple[int, int]]]:
    all_sizes = list(product(h_options, w_options))
    if not all_sizes:
        raise ValueError("frame bounds leave no odd size that fits the grid")

    if profile in {"canonical_single", "canonical_pair"}:
        if (5, 5) not in all_sizes:
            raise ValueError(
                f"profile {profile!r} requires 5x5 within the requested frame bounds"
            )
        return [[(5, 5)] * n_frames]

    if n_frames == 1:
        preferred = [size for size in all_sizes if size[0] != size[1]]
        fallback = [size for size in all_sizes if size[0] == size[1]]
        rng.shuffle(preferred)
        rng.shuffle(fallback)
        return [[size] for size in preferred + fallback]

    preferred = [
        [first, second]
        for first in all_sizes
        for second in all_sizes
        if first != second
    ]
    fallback = [
        [first, second]
        for first in all_sizes
        for second in all_sizes
        if first == second
    ]
    rng.shuffle(preferred)
    rng.shuffle(fallback)
    return preferred + fallback


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    profile = _scheduled_profile(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    canonical_defaults = profile in {"canonical_single", "canonical_pair"}
    h_min, h_max = _draw_odd_interval(
        ctx,
        "h",
        band,
        canonical_defaults=canonical_defaults
        and not {"frame_h_min", "frame_h_max"}.intersection(overrides),
    )
    w_min, w_max = _draw_odd_interval(
        ctx,
        "w",
        band,
        canonical_defaults=canonical_defaults
        and not {"frame_w_min", "frame_w_max"}.intersection(overrides),
    )

    scheduled_frames = 1 if profile in {"canonical_single", "varied_single"} else 2
    n_frames = ctx.draw_choice(
        "n_frames", (1, 2) if "n_frames" in overrides else (scheduled_frames,)
    )
    scheduled_bias = {
        "canonical_single": "spread",
        "canonical_pair": "diagonal",
        "row_aligned_pair": "row_aligned",
        "col_aligned_pair": "col_aligned",
        "varied_single": "corners",
        "varied_pair": "spread",
    }[profile]
    position_bias = ctx.draw_choice(
        "position_bias", POSITION_BIASES if "position_bias" in overrides else (scheduled_bias,)
    )

    frame_override_names = {
        "frame_h_min", "frame_h_max", "frame_w_min", "frame_w_max"
    }
    canonical_profile = profile in {"canonical_single", "canonical_pair"} and not {
        "grid_h",
        "grid_w",
        *frame_override_names,
    }.intersection(overrides)
    if canonical_profile:
        height = ctx.draw_choice("grid_h", (15,))
        width = ctx.draw_choice("grid_w", (15,))
    else:
        min_height = h_min + 2
        min_width = w_min + 2
        if n_frames == 2:
            if position_bias == "row_aligned":
                min_width = 2 * w_min + 3
            elif position_bias == "col_aligned":
                min_height = 2 * h_min + 3
            elif position_bias in {"corners", "diagonal"}:
                min_height = 2 * h_min + 3
                min_width = 2 * w_min + 3
            elif position_bias == "spread":
                min_height = h_min + 3
                min_width = 2 * w_min + 3
        height = (
            ctx.draw_int("grid_h", 9, 22)
            if "grid_h" in overrides
            else ctx.draw_int_diff("grid_h", max(9, min_height), 22)
        )
        width = (
            ctx.draw_int("grid_w", 9, 22)
            if "grid_w" in overrides
            else ctx.draw_int_diff("grid_w", max(9, min_width), 22)
        )

    h_options = _size_options(h_min, h_max, height)
    w_options = _size_options(w_min, w_max, width)
    if not h_options or not w_options:
        raise ValueError(
            f"requested frame interval {h_min}..{h_max} x {w_min}..{w_max} "
            f"does not fit {height}x{width} with an exterior margin"
        )

    rng = ctx.draw_rng("layout")
    size_profile = (
        ("varied_single" if n_frames == 1 else "varied_pair")
        if profile in {"canonical_single", "canonical_pair"}
        and frame_override_names.intersection(overrides)
        else profile
    )
    size_sets = _candidate_size_sets(
        profile=size_profile,
        n_frames=n_frames,
        h_options=h_options,
        w_options=w_options,
        rng=rng,
    )
    boxes = None
    last_error = None
    for sizes in size_sets:
        try:
            boxes = _choose_boxes(
                height=height,
                width=width,
                sizes=sizes,
                bias=position_bias,
                rng=rng,
            )
            break
        except ValueError as exc:
            last_error = exc
    if boxes is None:
        raise ValueError(
            f"no requested frame sizes can realize position_bias={position_bias!r} "
            f"in {height}x{width}: {last_error}"
        )

    grid = full_grid(height, width, 8)
    for r0, c0, r1, c1 in boxes:
        draw_rect_outline(grid, r0, c0, r1 - r0 + 1, c1 - c0 + 1, 1)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator emitted an unlawful grid: " + "; ".join(errors))
    return grid


def _component_cells(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = r + dr, c + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"errors": errors, "frames": []}
    if not isinstance(grid, list) or not grid:
        errors.append("grid must be a nonempty list of rows")
        return result
    if not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid rows must be nonempty lists")
        return result
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value not in (1, 8)
        for row in grid
        for value in row
    ):
        errors.append("input cells must use only frame color 1 and cyan background 8")
        return result

    height = len(grid)
    if not 9 <= height <= 22:
        errors.append(f"grid height {height} outside 9..22")
    if not 9 <= width <= 22:
        errors.append(f"grid width {width} outside 9..22")

    components = _component_cells(grid, 1)
    if not 1 <= len(components) <= 2:
        errors.append(f"expected one or two color-1 frames, found {len(components)}")

    frames: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        cell_set = set(cells)
        r0 = min(row for row, _ in cells)
        r1 = max(row for row, _ in cells)
        c0 = min(col for _, col in cells)
        c1 = max(col for _, col in cells)
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        expected = _box_cells((r0, c0, r1, c1))
        if cell_set != expected:
            errors.append(f"color-1 component {index} is not a complete rectangle outline")
        if fh not in ODD_SIZES or fw not in ODD_SIZES:
            errors.append(
                f"frame {index} is {fh}x{fw}; dimensions must be odd members of {ODD_SIZES}"
            )
        if r0 < 1 or c0 < 1 or r1 >= height - 1 or c1 >= width - 1:
            errors.append(f"frame {index} lacks the required one-cell exterior margin")
        frames.append(
            {
                "box": (r0, c0, r1, c1),
                "height": fh,
                "width": fw,
                "center": ((r0 + r1) // 2, (c0 + c1) // 2),
            }
        )

    if len(frames) == 2 and not _separated(frames[0]["box"], frames[1]["box"]):
        errors.append("the two frames touch or lack a cyan separation cell")
    if not any(value == 8 for row in grid for value in row):
        errors.append("no cyan background cell remains")

    result.update(
        {
            "height": height,
            "width": width,
            "frames": sorted(frames, key=lambda item: item["box"]),
            "n_frames": len(frames),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the task's exact frame grammar."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Return exact axis values that are directly recoverable from a grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_frames": analysis["n_frames"],
    }


def _paint_crosshairs(
    grid: list[list[int]],
    frames: list[dict[str, Any]],
    *,
    horizontal: bool = True,
    vertical: bool = True,
    local_only: bool = False,
    preserve_frames: bool = True,
) -> list[list[int]]:
    output = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for frame in frames:
        row, col = frame["center"]
        r0, c0, r1, c1 = frame["box"]
        col_range = range(c0, c1 + 1) if local_only else range(width)
        row_range = range(r0, r1 + 1) if local_only else range(height)
        if horizontal:
            for c in col_range:
                if grid[row][c] == 8 or not preserve_frames:
                    output[row][c] = 6
        if vertical:
            for r in row_range:
                if grid[r][col] == 8 or not preserve_frames:
                    output[r][col] = 6
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python oracle for tests and semantic hooks."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _paint_crosshairs(grid, analysis["frames"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 15x15, 5x5-frame teaching manifold."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if (analysis["height"], analysis["width"]) != (15, 15):
        reasons.append("canonical grids are 15x15")
    if any((frame["height"], frame["width"]) != (5, 5) for frame in analysis["frames"]):
        reasons.append("canonical frames are 5x5")
    return reasons


def _lawful_frames(grid) -> list[dict[str, Any]]:
    analysis = _analyze(grid)
    return [] if analysis["errors"] else analysis["frames"]


def _has_frame_shape(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    frames = _lawful_frames(grid)
    return bool(frames) and any(predicate(frame) for frame in frames)


def _centers(grid) -> list[tuple[int, int]]:
    return [frame["center"] for frame in _lawful_frames(grid)]


SEMANTIC_WITNESSES = {
    "canonical_profile": lambda grid: not strict_canonical_like(grid),
    "single_frame": lambda grid: len(_lawful_frames(grid)) == 1,
    "two_frames": lambda grid: len(_lawful_frames(grid)) == 2,
    "row_aligned_centers": lambda grid: (
        len(_centers(grid)) == 2 and _centers(grid)[0][0] == _centers(grid)[1][0]
    ),
    "col_aligned_centers": lambda grid: (
        len(_centers(grid)) == 2 and _centers(grid)[0][1] == _centers(grid)[1][1]
    ),
    "non_square_frame": lambda grid: _has_frame_shape(
        grid, lambda frame: frame["height"] != frame["width"]
    ),
    "mixed_frame_sizes": lambda grid: (
        len(_lawful_frames(grid)) == 2
        and (
            _lawful_frames(grid)[0]["height"],
            _lawful_frames(grid)[0]["width"],
        )
        != (
            _lawful_frames(grid)[1]["height"],
            _lawful_frames(grid)[1]["width"],
        )
    ),
    "distinct_center_rows_and_cols": lambda grid: (
        len(_centers(grid)) == 2
        and _centers(grid)[0][0] != _centers(grid)[1][0]
        and _centers(grid)[0][1] != _centers(grid)[1][1]
    ),
}


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    frames = analysis["frames"]
    first = frames[:1]
    largest = [max(frames, key=lambda f: f["height"] * f["width"])]
    output = [row[:] for row in grid]
    center_row, center_col = (len(grid) - 1) // 2, (len(grid[0]) - 1) // 2
    for col in range(len(grid[0])):
        if grid[center_row][col] == 8:
            output[center_row][col] = 6
    for row in range(len(grid)):
        if grid[row][center_col] == 8:
            output[row][center_col] = 6
    center_dot = [row[:] for row in grid]
    for frame in frames:
        row, col = frame["center"]
        if grid[row][col] == 8:
            center_dot[row][col] = 6
    return {
        "center_dot_only": center_dot,
        "horizontal_only": _paint_crosshairs(grid, frames, vertical=False),
        "vertical_only": _paint_crosshairs(grid, frames, horizontal=False),
        "local_bbox_crosshair": _paint_crosshairs(grid, frames, local_only=True),
        "first_frame_only": _paint_crosshairs(grid, first),
        "largest_frame_only": _paint_crosshairs(grid, largest),
        "grid_center_crosshair": output,
        "overwrite_frame_cells": _paint_crosshairs(
            grid, frames, preserve_frames=False
        ),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible wrong rule survives all demonstrations."""
    query_input = query.get("input") if isinstance(query, dict) else None
    query_competitors = _competitor_outputs(query_input)
    if query_competitors is None:
        return ["query input is not a lawful frame scene"]
    query_truth = rule_mirror(query_input)

    demo_rows: list[tuple[dict[str, Any], dict[str, list[list[int]]]]] = []
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict):
            reasons.append(f"demo {index} is not a mapping")
            continue
        grid = demo.get("input")
        competitors = _competitor_outputs(grid)
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful frame scene")
            continue
        try:
            truth = rule_mirror(grid)
        except ValueError as exc:
            reasons.append(f"demo {index} mirror failed: {exc}")
            continue
        if demo.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with the crosshair rule")
            continue
        demo_rows.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        if all(competitors[name] == demo["output"] for demo, competitors in demo_rows):
            if query_competitors[name] != query_truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but changes the query answer"
                )
    return sorted(set(reasons))
