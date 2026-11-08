"""Generator for custom task 33997447 / fa3e0c305476.

Each cyan object is recolored from the number of connected non-cyan regions in
its own bounding box: 1 -> blue, 2 -> red, 3 -> green, 4 -> orange, otherwise
keep the object's original color.

Version 3.1 uses a linked four-pair lesson schedule rather than requiring every
individual grid to contain every branch.  The first three demonstrations jointly
show counts 0 through 6, including all mapped and unchanged cases; the fourth
pair is a query composed only from already-demonstrated branches.  This keeps
each scene close to the canonical two/three-object scale while making every
materialized lesson identify the intended rule.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "fa3e0c305476"
TASK_ID = "fa3e0c305476"
VERSION = "3.2.0"
RULE_HASH = "c89e9c00a1d3"

SUMMARY = (
    "Find every cyan object. Within that object's bounding box, count the "
    "connected regions whose cells are not cyan. Recolor the whole object by "
    "that count: 1->blue(1), 2->red(2), 3->green(3), 4->orange(7); any other "
    "count leaves the object cyan. Sequential sample indices form a linked "
    "lesson: demonstrations cover 0,1,2 then 3,4 then 1,5,6; the next query "
    "uses only the already-demonstrated 2,3,4 branches."
)

INVARIANTS = [
    "the palette is exactly a zero background plus cyan-8 objects",
    "cyan objects are separated by at least one background row or column",
    "every object's bounding-box perimeter is cyan, so counted regions are enclosed",
    "sample indices 0..2 jointly witness every mapped count 1..4 and fallback counts 0,5,6",
    "sample index 3 queries only branch outcomes already identified by the demonstrations",
]

# The runner consumes sequential sample indices.  Keeping these four profiles in
# this exact order makes every normal 3-demo/1-query materialization teach the
# complete map without inflating each individual scene beyond canonical scale.
PROFILES = {
    "lesson_zero_12": (0, 1, 2),
    "lesson_34": (3, 4),
    "lesson_156": (1, 5, 6),
    "query_234": (2, 3, 4),
}
PROFILE_ORDER = tuple(PROFILES)
GEOMETRY_STYLES = ("compact", "mixed_scale")

# Preferred default envelopes.  `_profile_fits` below is the exact compatibility
# predicate and permits alternate wide/short layouts where lawful.
_PROFILE_DRAW_MIN_DIMS = {
    "lesson_zero_12": (6, 12),
    "lesson_34": (6, 13),
    "lesson_156": (9, 11),
    "query_234": (9, 13),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed, profile-compatible",
        "valid": "6..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed, profile-compatible",
        "valid": "6..30",
    },
    "profile": {
        "type": "str",
        "default": "four-step linked lesson schedule",
        "valid": "lesson_zero_12|lesson_34|lesson_156|query_234",
    },
    "geometry_style": {
        "type": "str",
        "default": "alternating compact and mixed-scale enclosed regions",
        "valid": "compact|mixed_scale",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
_CARD = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("profile")
    if profile is not None and profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    geometry = overrides.get("geometry_style")
    if geometry is not None and geometry not in GEOMETRY_STYLES:
        raise ValueError(f"unknown geometry_style {geometry!r}")


def _scheduled_profile(sample_index: int) -> str:
    return PROFILE_ORDER[sample_index % len(PROFILE_ORDER)]


def _scheduled_geometry(seed: int, sample_index: int) -> str:
    # Seed parity prevents geometry from becoming a fixed proxy for profile.
    return GEOMETRY_STYLES[(int(seed) + sample_index) % len(GEOMETRY_STYLES)]


def _profile_fits(profile: str, height: int, width: int) -> bool:
    """Exact conservative envelopes for at least one legal compact packing."""
    if profile == "lesson_zero_12":
        return (height >= 6 and width >= 12) or (height >= 7 and width >= 6)
    if profile == "lesson_34":
        return (height >= 6 and width >= 13) or (height >= 9 and width >= 7)
    if profile == "lesson_156":
        return (height >= 9 and width >= 11) or (height >= 6 and width >= 29)
    if profile == "query_234":
        return (height >= 9 and width >= 13) or (height >= 6 and width >= 19)
    return False


def _lattice_frame(
    hole_count: int,
    hole_rows: int,
    hole_cols: int,
    hole_h: int,
    hole_w: int,
) -> tuple[frozenset[tuple[int, int]], int, int]:
    """Return a connected cyan lattice with exactly ``hole_count`` regions."""
    if hole_rows * hole_cols != hole_count:
        raise ValueError("lattice factorization does not match hole count")
    height = hole_rows * hole_h + hole_rows + 1
    width = hole_cols * hole_w + hole_cols + 1
    holes = {
        (1 + hr * (hole_h + 1) + dr, 1 + hc * (hole_w + 1) + dc)
        for hr in range(hole_rows)
        for hc in range(hole_cols)
        for dr in range(hole_h)
        for dc in range(hole_w)
    }
    cells = frozenset(
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in holes
    )
    return cells, height, width


def _frame_candidates(
    hole_count: int,
    *,
    scaled: bool,
    rng,
) -> list[tuple[frozenset[tuple[int, int]], int, int]]:
    if hole_count == 0:
        candidates = []
        for height, width in ((2, 2), (2, 3), (3, 2), (3, 3)):
            cells = frozenset(
                (row, col)
                for row in range(height)
                for col in range(width)
            )
            candidates.append((cells, height, width))
        rng.shuffle(candidates)
        return candidates

    hole_shapes = ((1, 2), (2, 1)) if scaled else ((1, 1),)
    candidates = []
    for hole_rows in range(1, hole_count + 1):
        if hole_count % hole_rows:
            continue
        hole_cols = hole_count // hole_rows
        for hole_h, hole_w in hole_shapes:
            candidates.append(
                _lattice_frame(
                    hole_count,
                    hole_rows,
                    hole_cols,
                    hole_h,
                    hole_w,
                )
            )
    # A candidate can arise twice for symmetric factorizations/shapes.
    deduped = list({(cells, height, width) for cells, height, width in candidates})
    rng.shuffle(deduped)
    return deduped


def _separated(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return (
        lr1 + 1 < rr0
        or rr1 + 1 < lr0
        or lc1 + 1 < rc0
        or rc1 + 1 < lc0
    )


def _candidate_positions(
    height: int,
    width: int,
    frame_h: int,
    frame_w: int,
    placed: Iterable[tuple[int, int, int, int]],
    rng,
) -> list[tuple[int, int]]:
    """All legal top-lefts, with edge/adjacent anchors tried first.

    The old anchor-only search silently made valid tight canonical-scale
    canvases appear unpackable.  The canvas is at most 18x30 and profiles have
    at most three objects, so exhaustive positions are cheap and complete.
    """
    anchors = {(0, 0), (0, width - frame_w),
               (height - frame_h, 0),
               (height - frame_h, width - frame_w)}
    for r0, c0, r1, c1 in placed:
        for row in (r1 + 2, r0 - frame_h - 1, r0, r1 - frame_h + 1):
            for col in (c1 + 2, c0 - frame_w - 1, c0, c1 - frame_w + 1):
                anchors.add((row, col))
    anchors = {
        (row, col)
        for row, col in anchors
        if 0 <= row <= height - frame_h and 0 <= col <= width - frame_w
    }
    remainder = [
        (row, col)
        for row in range(height - frame_h + 1)
        for col in range(width - frame_w + 1)
        if (row, col) not in anchors
    ]
    anchor_list = list(anchors)
    rng.shuffle(anchor_list)
    rng.shuffle(remainder)
    return anchor_list + remainder


def _pack_frames(
    height: int,
    width: int,
    hole_counts: tuple[int, ...],
    geometry_style: str,
    rng,
):
    positive_counts = tuple(count for count in hole_counts if count > 0)
    scaled_choices = [None]
    if geometry_style == "mixed_scale":
        scaled_choices = list(positive_counts)
        rng.shuffle(scaled_choices)

    for scaled_count in scaled_choices:
        option_map = {
            count: _frame_candidates(
                count, scaled=(count == scaled_count), rng=rng
            )
            for count in hole_counts
        }
        # Place the most restrictive/largest counts first; preserve count as a
        # stable tie-breaker so replay never depends on set/dict iteration order.
        order = sorted(
            hole_counts,
            key=lambda count: (
                -min(frame_h * frame_w for _, frame_h, frame_w in option_map[count]),
                -count,
            ),
        )
        placements: dict[
            int, tuple[frozenset[tuple[int, int]], int, int, int, int]
        ] = {}
        rectangles: list[tuple[int, int, int, int]] = []

        def search(index: int) -> bool:
            if index == len(order):
                return True
            count = order[index]
            for cells, frame_h, frame_w in option_map[count]:
                if frame_h > height or frame_w > width:
                    continue
                for row, col in _candidate_positions(
                    height, width, frame_h, frame_w, rectangles, rng
                ):
                    rect = (row, col, row + frame_h - 1, col + frame_w - 1)
                    if not all(_separated(rect, prior) for prior in rectangles):
                        continue
                    placements[count] = (cells, frame_h, frame_w, row, col)
                    rectangles.append(rect)
                    if search(index + 1):
                        return True
                    rectangles.pop()
                    placements.pop(count, None)
            return False

        if search(0):
            return [placements[count] for count in hole_counts]

    raise ValueError(
        f"profile objects do not fit requested {height}x{width} canvas"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    explicit_profile = overrides.get("profile")
    explicit_h = "grid_h" in overrides
    explicit_w = "grid_w" in overrides
    explicit_dimension = explicit_h or explicit_w
    planned_profile = explicit_profile
    if planned_profile is None and not explicit_dimension:
        planned_profile = _scheduled_profile(sample_index)

    if planned_profile is not None:
        min_h, min_w = _PROFILE_DRAW_MIN_DIMS[planned_profile]
    else:
        # Keep a one-axis override generatable without silently changing it.
        min_h = 7 if explicit_w and int(overrides["grid_w"]) < 12 else 6
        min_w = 12 if explicit_h and int(overrides["grid_h"]) < 7 else 6
    height = ctx.draw_int_diff("grid_h", min_h, 18)
    width = ctx.draw_int_diff("grid_w", min_w, 30)

    if explicit_profile is not None:
        profile = ctx.draw_choice("profile", PROFILE_ORDER)
    elif explicit_dimension:
        fitting = tuple(
            profile_name
            for profile_name in PROFILE_ORDER
            if _profile_fits(profile_name, height, width)
        )
        if not fitting:
            raise ValueError(
                f"no lawful linked profile fits requested {height}x{width} canvas"
            )
        profile = ctx.draw_choice(
            "profile", (fitting[sample_index % len(fitting)],)
        )
    else:
        profile = ctx.draw_choice("profile", (planned_profile,))

    if not _profile_fits(profile, height, width):
        raise ValueError(
            f"profile {profile!r} is incompatible with requested "
            f"{height}x{width} canvas"
        )

    if "geometry_style" in overrides:
        geometry_style = ctx.draw_choice("geometry_style", GEOMETRY_STYLES)
    elif explicit_dimension:
        # A lone dimension override must remain generatable at its boundary;
        # mixed-scale geometry is a separate explicit axis and may be combined
        # only when the requested canvas can hold it.
        geometry_style = ctx.draw_choice("geometry_style", ("compact",))
    else:
        geometry_style = ctx.draw_choice(
            "geometry_style", (_scheduled_geometry(seed, sample_index),)
        )

    rng = ctx.draw_rng("layout")
    placements = _pack_frames(
        height,
        width,
        PROFILES[profile],
        geometry_style,
        rng,
    )
    grid = full_grid(height, width, 0)
    for cells, _, _, row0, col0 in placements:
        for row, col in cells:
            grid[row0 + row][col0 + col] = 8
    return grid


def _components_of(grid, color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if grid[start_row][start_col] != color or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _CARD:
                    nxt = (row + dr, col + dc)
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


def _regions(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    regions = []
    for start in sorted(cells):
        if start in seen:
            continue
        region = set()
        stack = [start]
        seen.add(start)
        while stack:
            cell = stack.pop()
            region.add(cell)
            for dr, dc in _CARD:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        regions.append(region)
    return regions


def _analyze(grid) -> dict:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["empty or non-grid input"], "facts": {}}
    height, width = len(grid), len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["ragged or zero-width grid"], "facts": {}}

    palette = {value for row in grid for value in row}
    invalid_values = sorted(
        value
        for value in palette
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    )
    if invalid_values:
        errors.append(f"colors outside integer 0..9: {invalid_values}")
    if not palette <= {0, 8}:
        errors.append(f"expected only background 0 and cyan 8; got {sorted(palette)}")

    components = _components_of(grid, 8)
    if len(components) < 2:
        errors.append(f"expected at least two cyan objects; got {len(components)}")

    object_facts = []
    for index, component in enumerate(components):
        rows = [row for row, _ in component]
        cols = [col for _, col in component]
        row0, row1 = min(rows), max(rows)
        col0, col1 = min(cols), max(cols)
        frame_h, frame_w = row1 - row0 + 1, col1 - col0 + 1
        if frame_h < 2 or frame_w < 2:
            errors.append(
                f"cyan object {index} has undersized bbox {frame_h}x{frame_w}"
            )
            continue

        perimeter = {
            (row0, col)
            for col in range(col0, col1 + 1)
        } | {
            (row1, col)
            for col in range(col0, col1 + 1)
        } | {
            (row, col0)
            for row in range(row0, row1 + 1)
        } | {
            (row, col1)
            for row in range(row0, row1 + 1)
        }
        missing_perimeter = [
            cell for cell in sorted(perimeter) if grid[cell[0]][cell[1]] != 8
        ]
        if missing_perimeter:
            errors.append(
                f"cyan object {index} has an open bbox perimeter at {missing_perimeter[0]}"
            )

        non_cyan = {
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if grid[row][col] != 8
        }
        regions = _regions(non_cyan)
        hole_count = len(regions)
        if not 0 <= hole_count <= 6:
            errors.append(
                f"cyan object {index} has unsupported region count {hole_count}"
            )
        object_facts.append(
            {
                "bbox": (row0, col0, row1, col1),
                "hole_count": hole_count,
                "hole_sizes": tuple(sorted(len(region) for region in regions)),
            }
        )

    counts = tuple(sorted(fact["hole_count"] for fact in object_facts))
    profile = next(
        (name for name, expected in PROFILES.items() if counts == tuple(expected)),
        None,
    )
    hole_sizes = [
        size for fact in object_facts for size in fact["hole_sizes"]
    ]
    if hole_sizes and all(size == 1 for size in hole_sizes):
        geometry_style = "compact"
    elif hole_sizes and any(size > 1 for size in hole_sizes) and any(
        size == 1 for size in hole_sizes
    ):
        geometry_style = "mixed_scale"
    else:
        geometry_style = None

    return {
        "errors": errors,
        "facts": {
            "grid_h": height,
            "grid_w": width,
            "objects": object_facts,
            "hole_counts": counts,
            "profile": profile,
            "geometry_style": geometry_style,
        },
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons while accepting every canonical input."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover each declared axis from a valid generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    observed: dict[str, int | str] = {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
    }
    if facts["profile"] is not None:
        observed["profile"] = facts["profile"]
    if facts["geometry_style"] is not None:
        observed["geometry_style"] = facts["geometry_style"]
    return observed


def semantic_signature(grid) -> dict:
    """Task-linked observables used by focused tests and review census."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    facts = analysis["facts"]
    count_histogram = Counter(facts["hole_counts"])
    return {
        "errors": [],
        "profile": facts["profile"],
        "geometry_style": facts["geometry_style"],
        "hole_counts": list(facts["hole_counts"]),
        "count_histogram": dict(sorted(count_histogram.items())),
        "object_count": len(facts["objects"]),
        "all_core_branches": all(count in count_histogram for count in (1, 2, 3, 4)),
        "fallback_branch": any(count not in (1, 2, 3, 4) for count in count_histogram),
    }
