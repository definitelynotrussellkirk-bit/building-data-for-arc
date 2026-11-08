"""Generator for ``Seeded Frames Fill`` (task a2eace95c1cf).

Each input contains two or three hollow, axis-aligned rectangular frames.  A
frame may contain exactly one differently colored seed cell or no seed.  The
Racket oracle fills every seeded frame's whole interior with that *local* seed
color and leaves seedless frames unchanged.

The default schedule deliberately includes canonical-profile anchors plus
broader counterexamples: adjacent and gapped frames, two and three frames,
seedless frames, multiple independent seed colors, and a color reused in a
different geometric role.  Those examples rebut global-color, fill-all-frames,
leftmost-only, fixed-position, and palette-role shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid
from puzzle_generators.helpers.selfcheck import (
    components,
    interior_cells,
    is_full_frame_component,
)

GENERATOR_ID = "a2eace95c1cf"
VERSION = "3.0.0"
TASK_ID = "a2eace95c1cf"
RULE_HASH = "90ce0abbec54"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "A 0-background grid contains two or three hollow rectangular frames. "
    "Each frame has its own border color and contains either no seed or "
    "exactly one differently colored interior seed; at least one frame is "
    "seeded. Fill every seeded frame's complete interior with that frame's "
    "local seed color, preserving all borders and leaving seedless frames "
    "unchanged. Frames may be separated or directly adjacent."
)

INVARIANTS = [
    "two or three exact hollow rectangular frame components",
    "one to n_frames seeded frames; every seeded frame has exactly one seed",
    "each seed differs from its own frame border and has a blank cell to fill",
    "frame boxes never overlap; adjacent and background-gapped layouts are legal",
    "all non-background cells belong to a frame border or to its single seed",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-skewed 9..14",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-skewed 12..18",
        "valid": "12..18",
    },
    "n_frames": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "2..3",
    },
    "n_seeded_frames": {
        "type": "int",
        "default": "scheduled 1..3, linked <= n_frames",
        "valid": "1..3",
    },
    "frame_spacing": {
        "type": "enum",
        "default": "scheduled gapped|adjacent",
        "valid": ["gapped", "adjacent"],
    },
}

# Executably audited from all four canonical demonstrations and the held-out
# query.  Exact coordinates are retained only for the canonical-prior branch;
# strict_canonical_like deliberately quotients translation and seed position,
# which are nuisance variables for this rule.
_CANONICAL_PROFILES = (
    {
        "grid_h": 10,
        "grid_w": 13,
        "boxes": ((1, 1, 4, 4), (1, 7, 5, 11)),
        "seeded": (True, False),
    },
    {
        "grid_h": 11,
        "grid_w": 12,
        "boxes": ((1, 1, 5, 5), (6, 2, 9, 8)),
        "seeded": (True, True),
    },
    {
        "grid_h": 9,
        "grid_w": 14,
        "boxes": ((1, 1, 4, 6), (2, 9, 7, 12)),
        "seeded": (False, True),
    },
    {
        "grid_h": 10,
        "grid_w": 14,
        "boxes": ((1, 1, 4, 5), (2, 8, 4, 11), (5, 8, 8, 12)),
        "seeded": (True, False, True),
    },
    {
        "grid_h": 11,
        "grid_w": 14,
        "boxes": ((1, 1, 5, 5), (1, 8, 4, 12), (6, 3, 9, 10)),
        "seeded": (True, False, True),
    },
)


def _as_int_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                out.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            try:
                out.append([int(value) for value in row])
            except (TypeError, ValueError):
                return []
        else:
            return []
    return out


def _boxes_overlap(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    return not (lr1 < rr0 or rr1 < lr0 or lc1 < rc0 or rc1 < lc0)


def _boxes_adjacent(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> bool:
    """Whether two disjoint boxes have no background-cell moat between them."""
    if _boxes_overlap(left, right):
        return False
    lr0, lc0, lr1, lc1 = left
    rr0, rc0, rr1, rc1 = right
    row_gap = max(0, rr0 - lr1 - 1, lr0 - rr1 - 1)
    col_gap = max(0, rc0 - lc1 - 1, lc0 - rc1 - 1)
    return row_gap == 0 and col_gap == 0


def _analysis(grid: Any) -> dict[str, Any]:
    g = _as_int_grid(grid)
    errors: list[str] = []
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        return {
            "errors": ["grid must be nonempty and rectangular"],
            "grid": g,
            "frames": [],
        }
    if any(value < 0 or value > 9 for row in g for value in row):
        errors.append("grid colors must be integers in 0..9")

    h, w = len(g), len(g[0])
    if not 9 <= h <= 14:
        errors.append(f"grid height {h} is outside 9..14")
    if not 12 <= w <= 18:
        errors.append(f"grid width {w} is outside 12..18")

    comps = components(g, same_color=True)
    frames = [
        comp
        for comp in comps
        if comp["color"] != 0
        and is_full_frame_component(comp, color=comp["color"], min_size=3)
    ]
    frames.sort(key=lambda frame: frame["bbox"])
    if not 2 <= len(frames) <= 3:
        errors.append(f"expected two or three rectangular frames, got {len(frames)}")

    frame_rows: list[dict[str, Any]] = []
    accounted: set[tuple[int, int]] = set()
    for index, frame in enumerate(frames):
        box = frame["bbox"]
        r0, c0, r1, c1 = box
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if fw < 4:
            errors.append(f"frame {index} width {fw} is smaller than 4")
        if fh > 8 or fw > 8:
            errors.append(f"frame {index} exceeds the supported 8-cell span")
        accounted.update(frame["cells"])
        interior = interior_cells(box)
        nonzero = [(r, c, g[r][c]) for r, c in interior if g[r][c] != 0]
        seeds = [cell for cell in nonzero if cell[2] != frame["color"]]
        same_as_border = [cell for cell in nonzero if cell[2] == frame["color"]]
        if same_as_border:
            errors.append(f"frame {index} contains interior cells in its border color")
        if len(seeds) > 1:
            errors.append(f"frame {index} has {len(seeds)} interior seeds")
        if seeds:
            accounted.add((seeds[0][0], seeds[0][1]))
            if len(interior) < 2:
                errors.append(f"frame {index} seed has no blank interior cell to fill")
            elif not any(g[r][c] == 0 for r, c in interior):
                errors.append(f"frame {index} seed leaves no blank interior cell")
        frame_rows.append(
            {
                "color": frame["color"],
                "bbox": box,
                "height": fh,
                "width": fw,
                "interior": interior,
                "seed": seeds[0] if len(seeds) == 1 else None,
            }
        )

    adjacency_edges: list[tuple[int, int]] = []
    for left_index, left in enumerate(frame_rows):
        for right_index in range(left_index + 1, len(frame_rows)):
            right = frame_rows[right_index]
            if _boxes_overlap(left["bbox"], right["bbox"]):
                errors.append(f"frame boxes {left_index} and {right_index} overlap")
            elif _boxes_adjacent(left["bbox"], right["bbox"]):
                adjacency_edges.append((left_index, right_index))

    nonzero_cells = {
        (r, c)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if value != 0
    }
    extras = sorted(nonzero_cells - accounted)
    if extras:
        errors.append(f"found {len(extras)} non-frame/non-seed colored cells")

    seeded_frames = [frame for frame in frame_rows if frame["seed"] is not None]
    if not seeded_frames:
        errors.append("at least one frame must contain a seed")

    return {
        "errors": errors,
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "frames": frame_rows,
        "n_frames": len(frame_rows),
        "n_seeded_frames": len(seeded_frames),
        "frame_spacing": "adjacent" if adjacency_edges else "gapped",
        "adjacency_edges": tuple(adjacency_edges),
        "palette_size": len({value for row in g for value in row}),
        "border_colors": tuple(frame["color"] for frame in frame_rows),
        "seed_colors": tuple(frame["seed"][2] for frame in seeded_frames),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding frame-fill lessons."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared semantic axis from the returned grid."""
    analysis = _analysis(grid)
    return {
        "grid_h": analysis.get("grid_h"),
        "grid_w": analysis.get("grid_w"),
        "n_frames": analysis.get("n_frames"),
        "n_seeded_frames": analysis.get("n_seeded_frames"),
        "frame_spacing": analysis.get("frame_spacing"),
    }


def canonical_profile_signature(grid) -> tuple[Any, ...] | None:
    """Linked task profile, ignoring only translation, colors, and seed offset."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    morphology = tuple(
        sorted(
            (
                frame["height"],
                frame["width"],
                frame["seed"] is not None,
            )
            for frame in analysis["frames"]
        )
    )
    return (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["palette_size"],
        morphology,
        len(analysis["adjacency_edges"]),
    )


def _profile_signature(profile: dict[str, Any]) -> tuple[Any, ...]:
    morphology = tuple(
        sorted(
            (
                box[2] - box[0] + 1,
                box[3] - box[1] + 1,
                seeded,
            )
            for box, seeded in zip(profile["boxes"], profile["seeded"])
        )
    )
    edges = sum(
        _boxes_adjacent(left, right)
        for index, left in enumerate(profile["boxes"])
        for right in profile["boxes"][index + 1 :]
    )
    return (
        profile["grid_h"],
        profile["grid_w"],
        1 + len(profile["boxes"]) + sum(profile["seeded"]),
        morphology,
        edges,
    )


_CANONICAL_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _CANONICAL_PROFILES
)


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"linked frame profile is outside the five canonical signatures: {signature}"]
    return []


def _candidate_boxes(h: int, w: int) -> list[tuple[int, int, int, int]]:
    boxes: list[tuple[int, int, int, int]] = []
    for fh in range(3, min(6, h) + 1):
        for fw in range(4, min(8, w) + 1):
            for r0 in range(0, h - fh + 1):
                for c0 in range(0, w - fw + 1):
                    boxes.append((r0, c0, r0 + fh - 1, c0 + fw - 1))
    return boxes


def _general_boxes(
    h: int,
    w: int,
    n_frames: int,
    spacing: str,
    rng,
) -> tuple[tuple[int, int, int, int], ...]:
    candidates = _candidate_boxes(h, w)
    for _ in range(1200):
        first = rng.choice(candidates)
        chosen = [first]
        for index in range(1, n_frames):
            legal = []
            for candidate in candidates:
                if any(_boxes_overlap(candidate, old) for old in chosen):
                    continue
                if spacing == "gapped":
                    if any(_boxes_adjacent(candidate, old) for old in chosen):
                        continue
                elif index == 1 and not _boxes_adjacent(candidate, chosen[0]):
                    continue
                legal.append(candidate)
            if not legal:
                break
            chosen.append(rng.choice(legal))
        if len(chosen) == n_frames:
            chosen.sort()
            observed = "adjacent" if any(
                _boxes_adjacent(left, right)
                for index, left in enumerate(chosen)
                for right in chosen[index + 1 :]
            ) else "gapped"
            if observed == spacing:
                return tuple(chosen)

    # Deterministic minimum-size templates cover the hardest override corner:
    # 9x12, three frames, exact gapped/adjacent spacing.
    if n_frames == 2:
        gap = 1 if spacing == "gapped" else 0
        return ((1, 1, 4, 4), (1, 5 + gap, 4, 8 + gap))
    row = 5 if spacing == "gapped" else 4
    return ((1, 1, 3, 4), (1, 6, 3, 9), (row, 1, row + 2, 4))


def _scheduled_shape(slot: int) -> tuple[int, int, str]:
    return {
        0: (2, 1, "gapped"),
        1: (2, 2, "adjacent"),
        2: (3, 2, "adjacent"),
        3: (3, 2, "adjacent"),
        4: (2, 1, "gapped"),
        5: (3, 3, "gapped"),
        6: (3, 2, "adjacent"),
        7: (3, 2, "adjacent"),
    }[slot]


def _canonical_profile_for(slot: int, rng) -> dict[str, Any] | None:
    if slot in (0, 4):
        return _CANONICAL_PROFILES[rng.choice((0, 2))]
    if slot == 1:
        return _CANONICAL_PROFILES[1]
    if slot in (2, 6):
        return _CANONICAL_PROFILES[rng.choice((3, 4))]
    return None


def _linked_counts(ctx, overrides: dict[str, Any], scheduled: tuple[int, int]) -> tuple[int, int]:
    requested_frames = overrides.get("n_frames")
    requested_seeded = overrides.get("n_seeded_frames")
    if requested_frames is not None and requested_seeded is not None:
        n_frames = int(requested_frames)
        n_seeded = int(requested_seeded)
        if n_seeded > n_frames:
            raise ValueError("n_seeded_frames cannot exceed n_frames")
        return (
            ctx.draw_int("n_frames", n_frames, n_frames),
            ctx.draw_int("n_seeded_frames", n_seeded, n_seeded),
        )
    if requested_frames is not None:
        n_frames = ctx.draw_int("n_frames", 2, 3)
        n_seeded = ctx.draw_int("n_seeded_frames", 1, n_frames)
        return n_frames, n_seeded
    if requested_seeded is not None:
        n_seeded = ctx.draw_int("n_seeded_frames", 1, 3)
        n_frames = ctx.draw_int("n_frames", max(2, n_seeded), 3)
        return n_frames, n_seeded
    return (
        ctx.draw_int("n_frames", scheduled[0], scheduled[0]),
        ctx.draw_int("n_seeded_frames", scheduled[1], scheduled[1]),
    )


def _seed_positions(
    boxes: tuple[tuple[int, int, int, int], ...],
    seeded_indices: tuple[int, ...],
    sample_index: int,
    rng,
) -> dict[int, tuple[int, int]]:
    positions: dict[int, tuple[int, int]] = {}
    for order, frame_index in enumerate(seeded_indices):
        r0, c0, r1, c1 = boxes[frame_index]
        cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        mode = (sample_index + order) % 3
        if mode == 0:
            position = cells[0]
        elif mode == 1:
            position = cells[-1]
        else:
            position = rng.choice(cells)
        positions[frame_index] = position
    return positions


def _colors(
    n_frames: int,
    seeded_indices: tuple[int, ...],
    rng,
    *,
    reuse_role: bool,
) -> tuple[list[int], dict[int, int]]:
    border_colors = rng.sample(list(range(1, 10)), n_frames)
    seed_colors: dict[int, int] = {}
    available = [color for color in range(1, 10) if color not in border_colors]
    if reuse_role and seeded_indices:
        unseeded = [index for index in range(n_frames) if index not in seeded_indices]
        source_index = unseeded[0] if unseeded else (seeded_indices[0] + 1) % n_frames
        first = seeded_indices[0]
        reused = border_colors[source_index]
        if reused == border_colors[first]:
            raise AssertionError("role-reuse color unexpectedly equals its own border")
        seed_colors[first] = reused
        for frame_index in seeded_indices[1:]:
            choices = [
                color
                for color in available
                if color != border_colors[frame_index]
                and color not in seed_colors.values()
            ]
            seed_colors[frame_index] = rng.choice(choices)
    else:
        chosen = rng.sample(available, len(seeded_indices))
        seed_colors.update(zip(seeded_indices, chosen))
    return border_colors, seed_colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    slot = int(sample_index) % 8
    scheduled_frames, scheduled_seeded, scheduled_spacing = _scheduled_shape(slot)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")

    explicit = any(value is not None for value in overrides.values())
    profile = None if explicit else _canonical_profile_for(slot, layout_rng)
    if profile is not None:
        h = ctx.draw_int("grid_h", profile["grid_h"], profile["grid_h"])
        w = ctx.draw_int("grid_w", profile["grid_w"], profile["grid_w"])
        boxes = tuple(profile["boxes"])
        seeded_indices = tuple(
            index for index, seeded in enumerate(profile["seeded"]) if seeded
        )
        n_frames = ctx.draw_int("n_frames", len(boxes), len(boxes))
        n_seeded = ctx.draw_int(
            "n_seeded_frames", len(seeded_indices), len(seeded_indices)
        )
        observed_spacing = "adjacent" if any(
            _boxes_adjacent(left, right)
            for index, left in enumerate(boxes)
            for right in boxes[index + 1 :]
        ) else "gapped"
        spacing = ctx.draw_choice("frame_spacing", (observed_spacing,))
        reuse_role = False
    else:
        h = ctx.draw_int_diff("grid_h", 9, 14)
        w = ctx.draw_int_diff("grid_w", 12, 18)
        n_frames, n_seeded = _linked_counts(
            ctx, overrides, (scheduled_frames, scheduled_seeded)
        )
        spacing_options = (
            ("gapped", "adjacent")
            if overrides.get("frame_spacing") is not None
            else (scheduled_spacing,)
        )
        spacing = ctx.draw_choice("frame_spacing", spacing_options)
        boxes = _general_boxes(h, w, n_frames, spacing, layout_rng)
        if not explicit and slot in (3, 7) and n_seeded == 2 and n_frames == 3:
            seeded_indices = (0, 2)
        else:
            seeded_indices = tuple(sorted(layout_rng.sample(range(n_frames), n_seeded)))
        reuse_role = not explicit and slot == 7

    if len(boxes) != n_frames or len(seeded_indices) != n_seeded:
        raise AssertionError("linked frame counts drifted before rendering")

    border_colors, seed_colors = _colors(
        n_frames,
        seeded_indices,
        layout_rng,
        reuse_role=reuse_role,
    )
    seed_positions = _seed_positions(boxes, seeded_indices, sample_index, layout_rng)

    grid = full_grid(h, w, 0)
    for frame_index, box in enumerate(boxes):
        r0, c0, r1, c1 = box
        draw_rect_outline(
            grid,
            r0,
            c0,
            r1 - r0 + 1,
            c1 - c0 + 1,
            border_colors[frame_index],
        )
        if frame_index in seed_positions:
            r, c = seed_positions[frame_index]
            grid[r][c] = seed_colors[frame_index]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid seeded-frame lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_frames": n_frames,
        "n_seeded_frames": n_seeded,
        "frame_spacing": spacing,
    }
    if any(observed[key] != value for key, value in expected.items()):
        raise AssertionError(f"rendered axes drifted: expected {expected}, observed {observed}")
    return grid


def _fill_local(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("input is outside the seeded-frame teaching grammar")
    out = [row[:] for row in analysis["grid"]]
    for frame in analysis["frames"]:
        if frame["seed"] is None:
            continue
        color = frame["seed"][2]
        for r, c in frame["interior"]:
            out[r][c] = color
    return out


def _rival_output(grid: Any, rival: str) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("rival received malformed input")
    out = [row[:] for row in analysis["grid"]]
    seeded = [frame for frame in analysis["frames"] if frame["seed"] is not None]
    first_color = seeded[0]["seed"][2]
    if rival == "identity":
        return out
    if rival == "global_first_seed":
        for frame in seeded:
            for r, c in frame["interior"]:
                out[r][c] = first_color
        return out
    if rival == "fill_all_frames":
        for frame in analysis["frames"]:
            for r, c in frame["interior"]:
                out[r][c] = first_color
        return out
    if rival == "leftmost_seeded_only":
        frame = seeded[0]
        for r, c in frame["interior"]:
            out[r][c] = frame["seed"][2]
        return out
    raise ValueError(f"unknown rival {rival!r}")


_RIVALS = (
    "identity",
    "global_first_seed",
    "fill_all_frames",
    "leftmost_seeded_only",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to falsify named shortcut rules on a decisive query."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        try:
            expected = _fill_local(pair.get("input"))
        except ValueError:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output is not the local seeded-frame fill")

    for rival in _RIVALS:
        falsified = any(
            pair.get("output") != _rival_output(pair.get("input"), rival)
            for pair in demos
            if not self_check(pair.get("input"))
        )
        if not falsified:
            reasons.append(f"demonstrations do not falsify rival rule {rival}")

    try:
        query_expected = _fill_local(query.get("input"))
    except ValueError:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    if query.get("output") != query_expected:
        reasons.append("query output is not the local seeded-frame fill")
    query_analysis = _analysis(query.get("input"))
    if query_analysis["n_seeded_frames"] < 2:
        reasons.append("query lacks two independently seeded frames")
    if query_analysis["n_seeded_frames"] >= query_analysis["n_frames"]:
        reasons.append("query lacks a seedless frame")
    if len(set(query_analysis["seed_colors"])) < 2:
        reasons.append("query seed colors do not distinguish local from global fill")
    for rival in _RIVALS:
        if query_expected == _rival_output(query.get("input"), rival):
            reasons.append(f"query answer is equivalent under rival rule {rival}")
    return reasons


def _witness(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def wrapped(grid: Any) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return wrapped


SEMANTIC_WITNESSES = {
    "seedless_frame": _witness(
        lambda analysis: analysis["n_seeded_frames"] < analysis["n_frames"]
    ),
    "multiple_local_seed_colors": _witness(
        lambda analysis: analysis["n_seeded_frames"] >= 2
        and len(set(analysis["seed_colors"])) >= 2
    ),
    "adjacent_frames": _witness(
        lambda analysis: analysis["frame_spacing"] == "adjacent"
    ),
    "gapped_frames": _witness(
        lambda analysis: analysis["frame_spacing"] == "gapped"
    ),
    "three_frames": _witness(lambda analysis: analysis["n_frames"] == 3),
    "three_row_frame": _witness(
        lambda analysis: any(frame["height"] == 3 for frame in analysis["frames"])
    ),
    "seven_plus_wide_frame": _witness(
        lambda analysis: any(frame["width"] >= 7 for frame in analysis["frames"])
    ),
    "color_reused_across_roles": _witness(
        lambda analysis: any(
            seed in analysis["border_colors"] for seed in analysis["seed_colors"]
        )
    ),
}
