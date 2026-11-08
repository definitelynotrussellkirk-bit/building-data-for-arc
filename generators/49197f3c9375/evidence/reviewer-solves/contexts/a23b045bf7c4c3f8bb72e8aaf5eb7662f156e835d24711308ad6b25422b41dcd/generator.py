"""Generator for S11_H4 — find the shape class that occurs only once.

The canonical rule groups monochrome 4-connected components by a shape
signature invariant to rotations and reflections.  Two shape classes occur
exactly twice and one occurs once.  The output is the singleton component's
boundary, normalized to its tight crop and painted in its original color.

Normal draws deliberately defeat common shortcuts.  A finite six-role teaching
schedule alternates boundary-only and interior-bearing singletons while cycling
the singleton through first/middle/last scan positions.  Thus every consecutive
four-pair lesson, under any one-pair query rotation, contains a demonstration
that distinguishes both ``whole singleton`` and ``last motif`` rivals.  The
first six roles of every 24-draw block are additionally pinned to the canonical
8x15/six-color profile; other draws retain the broader curriculum.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49197f3c9375"
VERSION = "3.0.0"
TASK_ID = "49197f3c9375"
RULE_HASH = "4303be5db475"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Five separated motifs: two dihedral-equivalent pairs and one unmatched "
    "shape; the rule returns the unmatched shape's cropped boundary."
)

INVARIANTS = [
    "background is 0 and exactly five monochrome 4-connected motifs are generated with background separation",
    "dihedral shape-signature multiplicities are exactly 2, 2, and 1",
    "generated draws contain one rotation-only pair and one reflection-only pair",
    "the unmatched motif appears first, middle, or last in scan order",
    "the unmatched motif shares both its cell count and bbox dimensions with another motif",
    "every consecutive four scheduled draws teach both boundary extraction and singleton selection",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8 on canonical anchors; otherwise difficulty-aware over 9..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware draw over 15..20",
        "valid": "15..20",
    },
    "target_topology": {
        "type": "str",
        "default": "alternating six-role lesson schedule",
        "valid": "boundary_only|interior_bearing",
    },
    "target_slot": {
        "type": "str",
        "default": "first/middle/last six-role lesson schedule",
        "valid": "first|middle|last",
    },
    "color_scheme": {
        "type": "str",
        "default": "rng",
        "valid": "distinct|reused|monochrome",
    },
}

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TARGET_INDEX = {"first": 0, "middle": 2, "last": 4}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_SLOT_SCHEDULE = ("first", "middle", "last", "first", "middle", "last")
_TOPOLOGY_SCHEDULE = (
    "interior_bearing",
    "boundary_only",
    "interior_bearing",
    "boundary_only",
    "interior_bearing",
    "boundary_only",
)
LESSON_SCHEDULE_PERIOD = 24
SCHEDULE_PROFILES = tuple(
    (slot, topology, canonical_anchor)
    for slot, topology in zip(_SLOT_SCHEDULE, _TOPOLOGY_SCHEDULE)
    for canonical_anchor in (False, True)
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise TypeError(f"{label} must be an integer, not {type(value).__name__}")
    for label in ("target_topology", "target_slot", "color_scheme"):
        value = overrides.get(label)
        if value is not None and type(value) is not str:
            raise TypeError(f"{label} must be a string, not {type(value).__name__}")


def _scheduled_choice(ctx, label: str, options, scheduled):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    """Return the finite default curriculum role for evidence enumeration."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    index = int(sample_index)
    role = index % len(_SLOT_SCHEDULE)
    return (
        _SLOT_SCHEDULE[role],
        _TOPOLOGY_SCHEDULE[role],
        index % LESSON_SCHEDULE_PERIOD < len(_SLOT_SCHEDULE),
    )


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate90(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(turns % 4):
        result = _rotate90(result)
    return result


def _reflect_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((r, -c) for r, c in cells)


def _rotations(cells: Iterable[tuple[int, int]]) -> set[tuple[tuple[int, int], ...]]:
    current = _normalize(cells)
    result = set()
    for _ in range(4):
        result.add(current)
        current = _rotate90(current)
    return result


def _signature(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _normalize(cells)
    return min(_rotations(cells) | _rotations(_reflect_lr(cells)))


def _is_chiral(cells: Iterable[tuple[int, int]]) -> bool:
    cells = _normalize(cells)
    return _rotations(cells).isdisjoint(_rotations(_reflect_lr(cells)))


def _bbox_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = _normalize(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _interior_count(cells: Iterable[tuple[int, int]]) -> int:
    cell_set = set(_normalize(cells))
    return sum(
        all((r + dr, c + dc) in cell_set for dr, dc in _NEIGHBORS)
        for r, c in cell_set
    )


def _random_polyomino(
    rng,
    size: int,
    *,
    forbidden: set[tuple[tuple[int, int], ...]],
    require_chiral: bool = False,
    require_nontrivial_rotation: bool = False,
    require_interior: bool | None = None,
    bbox: tuple[int, int] | None = None,
) -> tuple[tuple[int, int], ...]:
    """Draw a small connected polyomino satisfying structural constraints."""
    for _ in range(6000):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(_NEIGHBORS)
            cells.add((r + dr, c + dc))
        shape = _normalize(cells)
        h, w = _bbox_dims(shape)
        if h > 4 or w > 4:
            continue
        if bbox is not None and (h, w) != bbox:
            continue
        if require_chiral and not _is_chiral(shape):
            continue
        if require_nontrivial_rotation and len(_rotations(shape)) < 2:
            continue
        has_interior = _interior_count(shape) > 0
        if require_interior is not None and has_interior != require_interior:
            continue
        if _signature(shape) in forbidden:
            continue
        return shape
    raise ValueError(
        f"could not draw size={size} polyomino with bbox={bbox}, "
        f"chiral={require_chiral}, nontrivial_rotation={require_nontrivial_rotation}, "
        f"interior={require_interior}"
    )


def _nonidentity_rotation(shape, rng):
    choices = [_rotate(shape, turns) for turns in (1, 2, 3)]
    choices = [candidate for candidate in choices if candidate != _normalize(shape)]
    if not choices:
        raise ValueError("rotation pair base has no non-identity orientation")
    return rng.choice(choices)


def _reflected_orientation(shape, rng):
    reflected = _reflect_lr(shape)
    choices = [_rotate(reflected, turns) for turns in range(4)]
    choices = [candidate for candidate in choices if candidate != _normalize(shape)]
    if not choices:
        raise ValueError("reflection pair base has no distinct reflected orientation")
    return rng.choice(choices)


def _size_plan(difficulty: str | None, topology: str, rng) -> tuple[int, int, int]:
    """Return pair-A, pair-B, target sizes; target size is never a unique cue."""
    if topology == "interior_bearing":
        pair_b = {"easy": 5, "medium": 6, "hard": 7}.get(difficulty, rng.choice([5, 6, 7]))
        return 9, pair_b, 9
    target = {
        "easy": rng.choice([4, 5]),
        "medium": rng.choice([5, 6]),
        "hard": rng.choice([7, 8]),
    }.get(difficulty, rng.choice([4, 5, 6, 7, 8]))
    pair_b = {4: 5, 5: 7, 6: 8, 7: 9, 8: 6}[target]
    return target, pair_b, target


def _build_shapes(rng, difficulty, topology):
    pair_a_size, pair_b_size, target_size = _size_plan(difficulty, topology, rng)
    forbidden: set[tuple[tuple[int, int], ...]] = set()

    pair_a = _random_polyomino(
        rng,
        pair_a_size,
        forbidden=forbidden,
        require_chiral=True,
        require_nontrivial_rotation=True,
    )
    forbidden.add(_signature(pair_a))

    if topology == "interior_bearing":
        target = tuple((r, c) for r in range(3) for c in range(3))
        target = _normalize(target)
        target_bbox = (3, 3)
        pair_b = _random_polyomino(
            rng,
            pair_b_size,
            forbidden=forbidden | {_signature(target)},
            require_chiral=True,
            require_interior=False,
            bbox=target_bbox,
        )
    else:
        target_bbox = _bbox_dims(pair_a)
        target = _random_polyomino(
            rng,
            target_size,
            forbidden=forbidden,
            require_interior=False,
            bbox=target_bbox,
        )
        pair_b = _random_polyomino(
            rng,
            pair_b_size,
            forbidden=forbidden | {_signature(target)},
            require_chiral=True,
            require_interior=False,
        )

    if _signature(target) in forbidden:
        raise ValueError("target signature collided with a paired class")
    forbidden.add(_signature(target))
    if _signature(pair_b) in forbidden:
        raise ValueError("second pair signature collided with existing class")

    return [
        pair_a,
        _nonidentity_rotation(pair_a, rng),
        pair_b,
        _reflected_orientation(pair_b, rng),
    ], target


def _row_positions(width: int, shapes, rng) -> list[int]:
    widths = [_bbox_dims(shape)[1] for shape in shapes]
    required = sum(widths) + len(widths) - 1
    if required > width:
        raise ValueError(f"row needs width {required}, grid has {width}")
    buckets = [0] * (len(widths) + 1)
    for _ in range(width - required):
        buckets[rng.randrange(len(buckets))] += 1
    positions = []
    cursor = buckets[0]
    for index, shape_width in enumerate(widths):
        positions.append(cursor)
        cursor += shape_width
        if index < len(widths) - 1:
            cursor += 1 + buckets[index + 1]
    return positions


def _place_ordered(grid, ordered_shapes, colors, rng):
    h, w = len(grid), len(grid[0])
    top, bottom = ordered_shapes[:3], ordered_shapes[3:]
    top_h = max(_bbox_dims(shape)[0] for shape in top)
    bottom_h = max(_bbox_dims(shape)[0] for shape in bottom)
    required_h = top_h + 1 + bottom_h
    if required_h > h:
        raise ValueError(f"layout needs height {required_h}, grid has {h}")
    top_margin = rng.randint(0, h - required_h)
    row_starts = [top_margin, top_margin + top_h + 1]
    color_rows = [colors[:3], colors[3:]]
    for row_index, shapes in enumerate((top, bottom)):
        cols = _row_positions(w, shapes, rng)
        for shape, color, left in zip(shapes, color_rows[row_index], cols):
            for dr, dc in shape:
                grid[row_starts[row_index] + dr][left + dc] = color


def _colors_for_scheme(scheme: str, rng) -> list[int]:
    if scheme == "distinct":
        return rng.sample(list(range(1, 10)), 5)
    if scheme == "reused":
        first, second = rng.sample(list(range(1, 10)), 2)
        return [first, second, first, second, first]
    color = rng.choice(list(range(1, 10)))
    return [color] * 5


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            min_r = min(rr for rr, _ in cells)
            min_c = min(cc for _, cc in cells)
            max_r = max(rr for rr, _ in cells)
            max_c = max(cc for _, cc in cells)
            local = _normalize(cells)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "local": local,
                    "signature": _signature(local),
                    "bbox": (min_r, min_c, max_r, max_c),
                    "height": max_r - min_r + 1,
                    "width": max_c - min_c + 1,
                    "size": len(cells),
                    "interior": _interior_count(local),
                }
            )
    result.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    return result


def _relation_kind(first, second) -> str:
    first = _normalize(first)
    second = _normalize(second)
    is_rotation = second in _rotations(first)
    is_reflection = second in _rotations(_reflect_lr(first))
    if is_rotation and not is_reflection:
        return "rotation_only"
    if is_reflection and not is_rotation:
        return "reflection_only"
    if is_rotation and is_reflection:
        return "rotation_or_reflection"
    return "not_equivalent"


def _semantic_facts(grid):
    motifs = _components(grid)
    groups = defaultdict(list)
    for obj in motifs:
        groups[obj["signature"]].append(obj)
    singletons = [group[0] for group in groups.values() if len(group) == 1]
    target = singletons[0] if len(singletons) == 1 else None
    relations = sorted(
        _relation_kind(group[0]["local"], group[1]["local"])
        for group in groups.values()
        if len(group) == 2
    )
    color_counts = Counter(obj["color"] for obj in motifs)
    return motifs, groups, target, relations, color_counts


def observe_overrides(grid) -> dict[str, str]:
    """Recover exact semantic axes from a returned grid for contract checks."""
    motifs, _groups, target, _relations, color_counts = _semantic_facts(grid)
    observed = {"grid_h": len(grid), "grid_w": len(grid[0])}
    if target is not None:
        observed["target_topology"] = (
            "interior_bearing" if target["interior"] else "boundary_only"
        )
        rank = motifs.index(target)
        observed["target_slot"] = {0: "first", 2: "middle", 4: "last"}.get(rank, "other")
    counts = sorted(color_counts.values())
    if counts == [1, 1, 1, 1, 1]:
        observed["color_scheme"] = "distinct"
    elif counts == [2, 3]:
        observed["color_scheme"] = "reused"
    elif counts == [5]:
        observed["color_scheme"] = "monochrome"
    else:
        observed["color_scheme"] = "other"
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    if any(
        not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
        for row in grid
    ):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 12 and 15 <= w <= 20):
        errors.append(f"expected dimensions within 8..12 x 15..20, got {h}x{w}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
        return errors

    motifs, groups, target, relations, color_counts = _semantic_facts(grid)
    if len(motifs) != 5:
        errors.append(f"expected exactly five motifs, found {len(motifs)}")
    multiplicities = sorted(len(group) for group in groups.values())
    if multiplicities != [1, 2, 2]:
        errors.append(f"expected dihedral signature multiplicities [1, 2, 2], found {multiplicities}")
    # The task groups under the full dihedral action.  Canonical pairs may be
    # symmetry-ambiguous (``rotation_or_reflection``), so requiring a specific
    # witness orientation here would reject lawful canonical inputs.  The
    # stronger generated-distribution property is checked before return below.
    if target is None:
        errors.append("expected exactly one unmatched shape signature")
        return errors

    rank = motifs.index(target)
    if rank not in {0, 2, 4}:
        errors.append(f"unmatched motif must occupy first/middle/last slot, found rank {rank}")
    if sum(obj["size"] == target["size"] for obj in motifs) < 2:
        errors.append("unmatched motif's cell count must be shared by another motif")
    target_dims = {(target["height"], target["width"]), (target["width"], target["height"])}
    if sum((obj["height"], obj["width"]) in target_dims for obj in motifs) < 2:
        errors.append("unmatched motif's bbox dimensions must be shared by another motif")

    counts = sorted(color_counts.values())
    if counts not in ([1, 1, 1, 1, 1], [2, 3], [5]):
        errors.append(f"unexpected component-color multiplicities {counts}")
    if counts != [1, 1, 1, 1, 1] and color_counts[target["color"]] < 2:
        errors.append("in reused/monochrome modes, target color must occur on another motif")
    return errors


def _has_different_color_touch(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] != 0
        and grid[nr][nc] not in (0, grid[r][c])
        for r in range(h)
        for c in range(w)
        for dr, dc in ((1, 0), (0, 1))
        for nr, nc in ((r + dr, c + dc),)
        if nr < h and nc < w
    )


def strict_canonical_like(grid):
    """Structural task manifold shared by canonical and generated inputs."""
    return self_check(grid)


def _render_object(obj, *, boundary_only: bool) -> list[list[int]]:
    cells = set(obj["local"])
    if boundary_only:
        cells = {
            (r, c)
            for r, c in cells
            if any((r + dr, c + dc) not in cells for dr, dc in _NEIGHBORS)
        }
    out = full_grid(obj["height"], obj["width"], 0)
    for r, c in cells:
        out[r][c] = obj["color"]
    return out


def _singleton_object(grid):
    _motifs, _groups, target, _relations, _color_counts = _semantic_facts(grid)
    if target is None:
        raise ValueError("input does not contain exactly one singleton shape class")
    return target


def rule_mirror(grid):
    """Python evidence mirror; selected Racket remains label authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid singleton-shape input: " + "; ".join(errors))
    return _render_object(_singleton_object(grid), boundary_only=True)


def _whole_singleton(grid):
    """Plausible canonical-fit rival: crop the singleton without hollowing it."""
    return _render_object(_singleton_object(grid), boundary_only=False)


def _last_motif_boundary(grid):
    """Plausible canonical-fit rival: select the last motif in scan order."""
    motifs = _components(grid)
    if not motifs:
        raise ValueError("input contains no foreground motif")
    return _render_object(motifs[-1], boundary_only=True)


def _interior_boundary_witness(grid) -> bool:
    try:
        return _whole_singleton(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _singleton_not_last_witness(grid) -> bool:
    try:
        return _last_motif_boundary(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "interior_boundary": _interior_boundary_witness,
    "singleton_not_last": _singleton_not_last_witness,
}
SEMANTIC_RIVALS: dict[
    str, Callable[[list[list[int]]], list[list[int]]]
] = {
    "whole_singleton": _whole_singleton,
    "last_motif_boundary": _last_motif_boundary,
}
WITNESS_RIVALS = {
    "interior_boundary": ["whole_singleton"],
    "singleton_not_last": ["last_motif_boundary"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a declared canonical-fit rival survives it."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if not all(rival(pair["input"]) == pair["output"] for pair in demos):
            continue
        if rival(query["input"]) != query["output"]:
            reasons.append(f"{name} fits every demo but changes the query answer")
        else:
            reasons.append(f"{name} survives every demo and the query")
    return reasons


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
    exact_overrides = {
        label for label in AXES if overrides.get(label) is not None
    }
    profile_anchor = (
        not exact_overrides
        and int(sample_index) % LESSON_SCHEDULE_PERIOD < len(_SLOT_SCHEDULE)
    )
    role = int(sample_index) % len(_SLOT_SCHEDULE)

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int_diff("grid_h", 8, 12)
    elif profile_anchor:
        h = ctx.draw_int("grid_h", 8, 8)
    else:
        h = ctx.draw_int_diff("grid_h", 9, 12)

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int_diff("grid_w", 15, 20)
    elif profile_anchor:
        w = ctx.draw_int("grid_w", 15, 15)
    else:
        w = ctx.draw_int_diff("grid_w", 15, 20)

    topology = _scheduled_choice(
        ctx,
        "target_topology",
        ("boundary_only", "interior_bearing"),
        _TOPOLOGY_SCHEDULE[role],
    )
    target_slot = _scheduled_choice(
        ctx,
        "target_slot",
        ("first", "middle", "last"),
        _SLOT_SCHEDULE[role],
    )
    if profile_anchor and overrides.get("color_scheme") is None:
        color_scheme = ctx.draw_choice("color_scheme", ("distinct",))
    else:
        color_scheme = ctx.draw_choice(
            "color_scheme",
            ("distinct",) * 8 + ("reused",) * 2 + ("monochrome",),
        )
    rng = ctx.draw_rng("layout")

    for _ in range(40):
        try:
            paired, target = _build_shapes(rng, difficulty, topology)
            rng.shuffle(paired)
            ordered = list(paired)
            ordered.insert(_TARGET_INDEX[target_slot], target)
            colors = _colors_for_scheme(color_scheme, rng)
            grid = full_grid(h, w, 0)
            _place_ordered(grid, ordered, colors, rng)
        except ValueError:
            continue
        errors = self_check(grid, difficulty=difficulty, meta={"generated": True})
        _motifs, _groups, _target, relations, _color_counts = _semantic_facts(grid)
        if (
            not errors
            and not _has_different_color_touch(grid)
            and relations == ["reflection_only", "rotation_only"]
        ):
            return grid
    raise ValueError("could not realize a valid paired-shape layout")
