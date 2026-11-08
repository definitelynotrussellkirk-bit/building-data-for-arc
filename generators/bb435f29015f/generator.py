"""Generator for ARC task bb435f29015f — Keep the Largest.

Treat every same-colour 4-connected nonzero component as one object.  Preserve
only the unique object with the greatest cell count, in its original colour and
position, and replace every cell of every smaller object with background 0.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bb435f29015f"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "7ced211440aa"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "Find the same-colour 4-connected nonzero components, keep the unique "
    "component with the most cells unchanged, and erase every smaller "
    "component to background 0."
)

INVARIANTS = [
    "background is 0 and every ordinary draw contains background cells",
    "ordinary draws contain two or three separated same-colour 4-connected components",
    "every component has at least three cells and exactly one is strictly largest",
    "different components have a one-cell background moat, including diagonals",
    "the output keeps the largest component in place and erases all distractors",
]

# Every public axis is exact and recoverable from the returned grid.  Defaults
# follow a four-slot lesson schedule, while an explicit override keeps the full
# declared domain in every difficulty band.
AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical profile", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "scheduled canonical profile", "valid": "7..14"},
    "n_objs": {"type": "int", "default": "scheduled 2 or 3", "valid": "2..3"},
    "color_family": {"type": "str", "default": "keyed low|mid|high", "valid": "low|mid|high"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Degenerates are mutation fixtures, not accepted texture values and not part
# of the ordinary AXES domain.
DEGENERATE_TEXTURES = (
    "all_background",
    "single_object",
    "tied_largest",
    "touching_objects",
    "one_cell_noise",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

_COLOR_FAMILIES = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}
_FAMILY_NAMES = tuple(_COLOR_FAMILIES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MOAT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

Shape = tuple[tuple[int, int], ...]

_LINE3: Shape = ((0, 0), (0, 1), (0, 2))
_L3: Shape = ((0, 0), (0, 1), (1, 0))
_SQUARE4: Shape = ((0, 0), (0, 1), (1, 0), (1, 1))
_L4: Shape = ((0, 0), (1, 0), (2, 0), (2, 1))
_T5: Shape = ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1))
_Z5: Shape = ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2))
_SOLID6: Shape = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2))
_TRIANGLE6: Shape = ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1), (2, 2))
_COMPACT7: Shape = (
    (0, 0), (0, 1), (0, 2),
    (1, 0), (1, 1), (1, 2),
    (2, 1),
)
_RING8: Shape = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)
_SOLID9: Shape = tuple((r, c) for r in range(3) for c in range(3))
_RING12: Shape = (
    (0, 0), (0, 1), (0, 2), (0, 3),
    (1, 0),                         (1, 3),
    (2, 0),                         (2, 3),
    (3, 0), (3, 1), (3, 2), (3, 3),
)
_PATH6_3X4: Shape = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3))
_PATH8_4X5: Shape = (
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 4), (2, 4), (3, 4),
)

# Exact canonical morphology families, winner first.  D4 transforms and new
# placements retain the linked component signatures without copying examples.
_CANONICAL_ARCHETYPES: tuple[dict[str, Any], ...] = (
    {"dims": (8, 10), "shapes": (_RING8, _SQUARE4, _LINE3)},
    {"dims": (9, 9), "shapes": (_SOLID9, _T5)},
    {"dims": (7, 12), "shapes": (_TRIANGLE6, _Z5, _LINE3)},
    {"dims": (8, 11), "shapes": (_RING12, _Z5)},
    {"dims": (9, 12), "shapes": (_RING12, _L4, _SQUARE4)},
)
_CANONICAL_LINKED_PROFILES = {
    (8, 10, 3, 4),
    (9, 9, 2, 3),
    (7, 12, 3, 4),
    (8, 11, 2, 3),
    (9, 12, 3, 4),
}

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "bbox_and_position_decoy",
    "modal_colour_decoy",
    "close_gap_decoy",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive examples visit every pedagogical profile exactly once."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(shape: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(shape)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(shape: Shape, code: int) -> Shape:
    cells = list(shape)
    if code & 4:
        cells = [(r, -c) for r, c in cells]
    for _ in range(code & 3):
        cells = [(c, -r) for r, c in cells]
    return _normalize(cells)


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _axis_choice(ctx, overrides, label: str, default: Any, full: Iterable[Any]):
    overridden = label in overrides and overrides[label] is not None
    options = tuple(full) if overridden else (default,)
    return ctx.draw_choice(label, options)


def _difficulty_name(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    return str(difficulty)


def _canonical_variant(ctx, difficulty: str) -> int:
    options = {
        "easy": (0, 1),
        "medium": (0, 2, 3),
        "hard": (2, 3, 4),
    }[difficulty]
    return int(ctx.draw_rng("canonical_variant").choice(options))


def _default_geometry(ctx, profile: str, difficulty: str) -> tuple[int, int, int, int | None]:
    if profile == "canonical_anchor":
        variant = _canonical_variant(ctx, difficulty)
        h, w = _CANONICAL_ARCHETYPES[variant]["dims"]
        return h, w, len(_CANONICAL_ARCHETYPES[variant]["shapes"]), variant
    if profile == "bbox_and_position_decoy":
        return 9, 12, 3, None
    if profile == "modal_colour_decoy":
        return 8, 10, 3, None
    return 7, 12, 3, None


def _special_shapes(profile: str, difficulty: str, canonical_variant: int | None) -> tuple[Shape, ...]:
    if profile == "canonical_anchor":
        if canonical_variant is None:
            raise ValueError("canonical anchor is missing its archetype")
        return tuple(_CANONICAL_ARCHETYPES[canonical_variant]["shapes"])
    if profile == "bbox_and_position_decoy":
        if difficulty == "easy":
            return (_RING12, _PATH8_4X5, _LINE3)
        if difficulty == "hard":
            return (_COMPACT7, _PATH6_3X4, _LINE3)
        return (_SOLID9, _PATH8_4X5, _LINE3)
    if profile == "modal_colour_decoy":
        if difficulty == "easy":
            return (_RING8, _T5, _SQUARE4)
        if difficulty == "hard":
            return (_SOLID6, _SQUARE4, _LINE3)
        return (_COMPACT7, _SQUARE4, _L4)
    # The smaller object has a larger bounding box, and the size gap is one.
    return (_SOLID6, _T5, _LINE3)


def _compact_shapes(n_objs: int) -> tuple[Shape, ...]:
    return (_T5, _SQUARE4, _LINE3)[:n_objs]


def _transform_shapes(ctx, shapes: tuple[Shape, ...]) -> tuple[Shape, ...]:
    rng = ctx.draw_rng("shape_transforms")
    return tuple(_transform(shape, rng.randrange(8)) for shape in shapes)


def _placements_to_grid(
    h: int,
    w: int,
    shapes: tuple[Shape, ...],
    colors: tuple[int, ...],
    placements: list[tuple[tuple[int, int], ...]],
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for cells, color in zip(placements, colors):
        for r, c in cells:
            grid[r][c] = color
    return grid


def _place_shapes(
    h: int,
    w: int,
    shapes: tuple[Shape, ...],
    colors: tuple[int, ...],
    rng,
    *,
    winner_not_first: bool,
) -> list[list[int]]:
    candidates: dict[int, list[tuple[tuple[int, int], ...]]] = {}
    for index, shape in enumerate(shapes):
        sh, sw = _shape_dims(shape)
        anchors = [
            tuple((top + r, left + c) for r, c in shape)
            for top in range(h - sh + 1)
            for left in range(w - sw + 1)
        ]
        rng.shuffle(anchors)
        if winner_not_first and index == 0:
            anchors.sort(key=lambda cells: -(min(cells)[0] + min(cells)[1]))
        elif winner_not_first and index == 1:
            anchors.sort(key=lambda cells: min(cells)[0] + min(cells)[1])
        candidates[index] = anchors

    order = sorted(range(len(shapes)), key=lambda i: (-len(shapes[i]), i))
    occupied: set[tuple[int, int]] = set()
    placed: list[tuple[tuple[int, int], ...] | None] = [None] * len(shapes)
    nodes = 0

    def free(cells: tuple[tuple[int, int], ...]) -> bool:
        for r, c in cells:
            if (r, c) in occupied:
                return False
            if any((r + dr, c + dc) in occupied for dr, dc in _MOAT):
                return False
        return True

    def accepted() -> bool:
        if not winner_not_first:
            return True
        starts = [min(cells or ()) for cells in placed]
        return starts[0] != min(starts)

    def search(depth: int) -> bool:
        nonlocal nodes
        if depth == len(order):
            return accepted()
        index = order[depth]
        for cells in candidates[index]:
            nodes += 1
            if nodes > 120_000:
                return False
            if not free(cells):
                continue
            placed[index] = cells
            occupied.update(cells)
            if search(depth + 1):
                return True
            occupied.difference_update(cells)
            placed[index] = None
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(shapes)} separated objects on a {h}x{w} grid"
        )
    final = [cells for cells in placed if cells is not None]
    return _placements_to_grid(h, w, shapes, colors, final)


def _component_records(grid: Any) -> tuple[list[dict[str, Any]], list[str], int, int]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return [], ["grid must be a nonempty list of rows"], 0, 0
    if not all(isinstance(row, list) for row in grid):
        return [], ["every row must be a list"], 0, 0
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"], len(grid), width
    height = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c})={value!r} is not an ARC colour 0..9")
                if len(errors) >= 8:
                    return [], errors, height, width
    if errors:
        return [], errors, height, width

    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells_tuple = tuple(sorted(cells))
            r1 = min(r for r, _ in cells_tuple)
            r2 = max(r for r, _ in cells_tuple)
            c1 = min(c for _, c in cells_tuple)
            c2 = max(c for _, c in cells_tuple)
            normalized = {(r - r1, c - c1) for r, c in cells_tuple}
            bh, bw = r2 - r1 + 1, c2 - c1 + 1
            outside: set[tuple[int, int]] = set()
            queue: deque[tuple[int, int]] = deque()
            for rr in range(bh):
                for cc in range(bw):
                    if rr not in (0, bh - 1) and cc not in (0, bw - 1):
                        continue
                    if (rr, cc) not in normalized and (rr, cc) not in outside:
                        outside.add((rr, cc))
                        queue.append((rr, cc))
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < bh
                        and 0 <= nc < bw
                        and (nr, nc) not in normalized
                        and (nr, nc) not in outside
                    ):
                        outside.add((nr, nc))
                        queue.append((nr, nc))
            hole_cells = {
                (rr, cc)
                for rr in range(bh)
                for cc in range(bw)
                if (rr, cc) not in normalized and (rr, cc) not in outside
            }
            hole_count = 0
            remaining = set(hole_cells)
            while remaining:
                hole_count += 1
                seed = remaining.pop()
                todo = [seed]
                while todo:
                    rr, cc = todo.pop()
                    for dr, dc in _CARDINAL:
                        nxt = (rr + dr, cc + dc)
                        if nxt in remaining:
                            remaining.remove(nxt)
                            todo.append(nxt)
            records.append(
                {
                    "color": color,
                    "cells": cells_tuple,
                    "size": len(cells_tuple),
                    "start": cells_tuple[0],
                    "bbox": (r1, c1, r2, c2),
                    "bbox_h": bh,
                    "bbox_w": bw,
                    "bbox_area": bh * bw,
                    "holes": hole_count,
                }
            )
    records.sort(key=lambda record: record["start"])
    return records, errors, height, width


def _winner(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise ValueError("there are no nonzero components")
    return min(records, key=lambda record: (-record["size"], record["start"]))


def _colors_for_scene(ctx, family: str, n_objs: int, profile: str) -> tuple[int, ...]:
    palette = list(_COLOR_FAMILIES[family])
    rng = ctx.draw_rng("object_colors")
    rng.shuffle(palette)
    if profile == "modal_colour_decoy" and n_objs == 3:
        return palette[0], palette[1], palette[1]
    return tuple(palette[:n_objs])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket rule owns output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    difficulty_name = _difficulty_name(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_n, canonical_variant = _default_geometry(
        ctx, profile, difficulty_name
    )
    default_family = ctx.draw_rng("default_color_family").choice(_FAMILY_NAMES)

    h = int(_axis_choice(ctx, overrides, "grid_h", default_h, range(7, 15)))
    w = int(_axis_choice(ctx, overrides, "grid_w", default_w, range(7, 15)))
    n_objs = int(_axis_choice(ctx, overrides, "n_objs", default_n, (2, 3)))
    family = str(
        _axis_choice(ctx, overrides, "color_family", default_family, _FAMILY_NAMES)
    )

    geometry_overridden = any(
        name in overrides and overrides[name] is not None
        for name in ("grid_h", "grid_w", "n_objs")
    )
    if geometry_overridden:
        shapes = _compact_shapes(n_objs)
        winner_not_first = profile in (
            "bbox_and_position_decoy",
            "close_gap_decoy",
        )
    else:
        shapes = _special_shapes(profile, difficulty_name, canonical_variant)
        winner_not_first = profile in (
            "bbox_and_position_decoy",
            "close_gap_decoy",
        )
    shapes = _transform_shapes(ctx, tuple(shapes[:n_objs]))
    colors = _colors_for_scene(ctx, family, n_objs, profile)
    grid = _place_shapes(
        h,
        w,
        shapes,
        colors,
        ctx.draw_rng("layout"),
        winner_not_first=winner_not_first,
    )
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact public axis from a returned lawful scene."""
    records, errors, h, w = _component_records(grid)
    if errors:
        raise ValueError("cannot observe malformed scene: " + "; ".join(errors))
    colors = {record["color"] for record in records}
    families = [
        name for name, palette in _COLOR_FAMILIES.items() if colors and colors <= set(palette)
    ]
    if len(families) != 1:
        raise ValueError(f"nonzero colours do not identify one family: {sorted(colors)}")
    return {
        "grid_h": h,
        "grid_w": w,
        "n_objs": len(records),
        "color_family": families[0],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the teachable input grammar while accepting every canonical pair."""
    del difficulty
    records, errors, h, w = _component_records(grid)
    if errors:
        return errors
    if not (7 <= h <= 14 and 7 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} are outside 7..14")
    if not any(value == 0 for row in grid for value in row):
        errors.append("grid must contain background cells")
    if not (2 <= len(records) <= 3):
        errors.append(f"expected two or three nonzero components, found {len(records)}")
    sizes = [record["size"] for record in records]
    if any(size < 3 for size in sizes):
        errors.append(f"every component must have at least three cells; sizes={sizes}")
    if sizes and sizes.count(max(sizes)) != 1:
        errors.append(f"largest component must be unique; sizes={sizes}")

    owner: dict[tuple[int, int], int] = {}
    for index, record in enumerate(records):
        for cell in record["cells"]:
            owner[cell] = index
    for (r, c), index in owner.items():
        for dr, dc in _MOAT:
            other = owner.get((r + dr, c + dc))
            if other is not None and other != index:
                errors.append("different components must have a one-cell background moat")
                break
        if errors and errors[-1].startswith("different components"):
            break

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict) and requested:
            try:
                observed = observe_overrides(grid)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                for axis, value in requested.items():
                    if axis in AXES and value is not None and observed.get(axis) != value:
                        errors.append(
                            f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Linked canonical predicate: scale, palette roles, counts, and size ordering."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    records, _, h, w = _component_records(grid)
    colors = {record["color"] for record in records}
    linked = (h, w, len(records), len(colors) + 1)
    if linked not in _CANONICAL_LINKED_PROFILES:
        reasons.append(
            "linked (height,width,object-count,palette-size) profile is not canonical: "
            f"{linked}"
        )
    if len(colors) != len(records):
        reasons.append("canonical-linked scenes use a distinct colour per component")
    sizes = sorted((record["size"] for record in records), reverse=True)
    if sizes and not 6 <= sizes[0] <= 12:
        reasons.append(f"largest size {sizes[0]} is outside canonical 6..12")
    if len(sizes) >= 2 and not 3 <= sizes[1] <= 5:
        reasons.append(f"runner-up size {sizes[1]} is outside canonical 3..5")
    return reasons


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; the selected Racket source is authoritative."""
    records, errors, h, w = _component_records(grid)
    if errors:
        raise ValueError("cannot apply rule mirror: " + "; ".join(errors))
    best = _winner(records)
    output = full_grid(h, w, 0)
    for r, c in best["cells"]:
        output[r][c] = best["color"]
    return output


def _select_record(grid, key: Callable[[dict[str, Any]], Any]) -> list[list[int]]:
    records, errors, h, w = _component_records(grid)
    if errors or not records:
        raise ValueError("cannot apply rival to malformed scene")
    chosen = min(records, key=key)
    output = full_grid(h, w, 0)
    for r, c in chosen["cells"]:
        output[r][c] = chosen["color"]
    return output


def _keep_first_component(grid):
    return _select_record(grid, lambda record: record["start"])


def _keep_largest_bbox(grid):
    return _select_record(
        grid,
        lambda record: (-record["bbox_area"], record["start"]),
    )


def _keep_smallest_component(grid):
    return _select_record(grid, lambda record: (record["size"], record["start"]))


def _keep_modal_colour(grid):
    records, errors, h, w = _component_records(grid)
    if errors or not records:
        raise ValueError("cannot apply modal-colour rival to malformed scene")
    counts = Counter(value for row in grid for value in row if value != 0)
    colour = min(counts, key=lambda value: (-counts[value], value))
    output = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == colour:
                output[r][c] = value
    return output


def _copy_input(grid):
    return [list(row) for row in grid]


SEMANTIC_RIVALS = {
    "keep_first_component": _keep_first_component,
    "keep_largest_bbox": _keep_largest_bbox,
    "keep_modal_colour": _keep_modal_colour,
    "keep_smallest_component": _keep_smallest_component,
    "copy_input": _copy_input,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Every canonical example uses one colour per component, so global colour
# frequency is answer-equivalent there; the modal-colour curriculum slot is the
# required generated counterexample.
CANONICAL_SHORTCUTS = {"keep_modal_colour": _keep_modal_colour}


def _lawful_records(grid) -> list[dict[str, Any]] | None:
    if self_check(grid):
        return None
    records, _, _, _ = _component_records(grid)
    return records


def _rival_differs(grid, rival: Callable[[Any], Any]) -> bool:
    try:
        return not self_check(grid) and rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


def _close_gap(grid) -> bool:
    records = _lawful_records(grid)
    if records is None:
        return False
    sizes = sorted((record["size"] for record in records), reverse=True)
    return len(sizes) >= 2 and sizes[0] - sizes[1] == 1


def _hollow_winner(grid) -> bool:
    records = _lawful_records(grid)
    return False if records is None else _winner(records)["holes"] >= 1


SEMANTIC_WITNESSES = {
    "distractors_erased": lambda grid: _rival_differs(grid, _copy_input),
    "first_scan_decoy": lambda grid: _rival_differs(grid, _keep_first_component),
    "larger_bbox_decoy": lambda grid: _rival_differs(grid, _keep_largest_bbox),
    "modal_colour_decoy": lambda grid: _rival_differs(grid, _keep_modal_colour),
    "close_size_gap": _close_gap,
    "hollow_largest": _hollow_winner,
    "canonical_linked_profile": lambda grid: strict_canonical_like(grid) == [],
}
WITNESS_RIVALS = {
    "distractors_erased": ["copy_input", "keep_smallest_component"],
    "first_scan_decoy": ["keep_first_component"],
    "larger_bbox_decoy": ["keep_largest_bbox"],
    "modal_colour_decoy": ["keep_modal_colour"],
}
BRANCH_WITNESSES = {
    "close_size_gap",
    "hollow_largest",
    "canonical_linked_profile",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid exact pairs and demonstration-level refutation of each rival."""
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict):
            reasons.append(f"{role} is not an input/output pair dict")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        findings = self_check(grid)
        if findings:
            reasons.append(f"{role} is not lawful: {findings[:2]}")
            continue
        if rule_mirror(grid) != output:
            reasons.append(f"{role} output does not keep exactly the largest component")
    if reasons:
        return reasons

    required_witnesses = (
        "first_scan_decoy",
        "larger_bbox_decoy",
        "modal_colour_decoy",
    )
    for name in required_witnesses:
        predicate = SEMANTIC_WITNESSES[name]
        if not any(predicate(pair["input"]) for pair in demos):
            reasons.append(f"demonstrations do not contain required witness {name!r}")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
