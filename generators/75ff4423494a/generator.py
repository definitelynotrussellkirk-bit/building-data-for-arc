"""Generator for ARC task 75ff4423494a — anchored template copies with overlap.

The largest nonzero 4-connected component containing cyan (8) is the
prototype.  Its first cyan cell in row-major order is the origin.  Copy the
prototype's bounding-box template to the original origin and to every other
cyan cell.  Equal writes agree; different nonzero writes become maroon (9).

The canonical demonstrations leave two plausible shortcuts unresolved:
considering only isolated cyan destinations, and hard-coding the canonical
payload colors 2 and 3.  Every default profile directly teaches the disputed
branches: adjacent destination markers with a conflict-to-9, a non-top-left
origin, a noncanonical payload pair, and an ignored payload singleton.  The
six-profile schedule still preserves canonical dimensions and palette size.
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "75ff4423494a"
TASK_ID = "75ff4423494a"
VERSION = "2.0.0"
RULE_HASH = "0124781298a5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A two-color prototype containing one cyan origin plus 1-3 cyan targets; "
    "copy the prototype at every target and paint conflicting overlaps maroon."
)

INVARIANTS = [
    "background is 0 and input foreground is exactly cyan plus two payload colors",
    "the authority-selected prototype is a canonical 5- or 6-cell morphology",
    "the prototype contains exactly one cyan origin and is strictly the largest component",
    "1-3 other cyan cells are copy destinations; they may touch one another",
    "zero or one isolated payload-colored distractor is ignored by the rule",
    "translated copies are clipped naturally at canvas boundaries",
    "every default example contains the full declared rival-witness set",
    "all declared exact controls are recoverable from the returned grid",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

TEMPLATE_KINDS = ("hook6", "cross6", "step5")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "9..12",
        "doc": "Exact grid height; overrides use the full range in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "10..14",
        "doc": "Exact grid width; overrides use the full range in every band.",
    },
    "n_anchors": {
        "type": "int",
        "default": "scheduled 2..3",
        "valid": "1..3",
        "doc": "Exact number of cyan destination cells outside the prototype.",
    },
    "template_kind": {
        "type": "str",
        "default": "scheduled canonical morphology",
        "valid": "|".join(TEMPLATE_KINDS),
        "doc": "Exact prototype support relative to its cyan origin.",
    },
}

# Each cell is (dr, dc, role) relative to the cyan origin.  Role 8 is the
# marker, 0 is the frequent payload color, and 1 is the rare payload color.
# These are the three distinct prototype morphologies in the canonical task.
_TEMPLATE_ROLES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "hook6": (
        (0, 0, 8),
        (0, 1, 0),
        (1, 0, 0),
        (1, 1, 0),
        (2, 1, 0),
        (2, 2, 1),
    ),
    "cross6": (
        (0, 0, 8),
        (0, 1, 0),
        (1, -1, 0),
        (1, 0, 0),
        (1, 1, 0),
        (2, 0, 1),
    ),
    "step5": (
        (0, -1, 0),
        (0, 0, 8),
        (1, -1, 0),
        (2, -1, 0),
        (2, 0, 1),
    ),
}
_SUPPORT_TO_KIND = {
    frozenset((dr, dc) for dr, dc, _role in cells): kind
    for kind, cells in _TEMPLATE_ROLES.items()
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PAYLOAD_PAIRS = (
    (1, 4),
    (2, 5),
    (3, 6),
    (4, 7),
    (5, 1),
    (6, 2),
    (7, 3),
)

# (height, width, anchors, template, layout, add_distractor).  Default
# profiles all carry the complete teaching contract so every rotation of a
# four-pair lesson remains identifiable from its three demonstrations.
SCHEDULE_PROFILES = (0, 1, 2, 3, 4, 5)
_PROFILE_SPECS = (
    (9, 10, 2, "cross6", "adjacent_conflict", True),
    (10, 11, 2, "step5", "adjacent_conflict", True),
    (9, 12, 3, "cross6", "adjacent_conflict", True),
    (10, 10, 2, "step5", "adjacent_conflict", True),
    (9, 10, 3, "cross6", "adjacent_conflict", True),
    (10, 11, 2, "step5", "adjacent_conflict", True),
)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Six-profile cycle; difficulty rotates support instead of narrowing it."""
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return (int(seed) + int(sample_index) + _BAND_OFFSET[difficulty]) % len(
        SCHEDULE_PROFILES
    )


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid values must be integer ARC colors in 0..9"
    return None


def _nonzero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 0
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        component: list[tuple[int, int]] = []
        while stack:
            cell = stack.pop()
            component.append(cell)
            for dr, dc in _CARDINAL:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def _component_key(cells: list[tuple[int, int]]) -> tuple[int, int, int]:
    return (-len(cells), min(r for r, _ in cells), min(c for _, c in cells))


def _analysis(grid: Any) -> dict[str, Any]:
    shape_error = _shape_error(grid)
    if shape_error:
        return {"errors": [shape_error]}

    height, width = len(grid), len(grid[0])
    components = _nonzero_components(grid)
    candidates = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[r][c] == 8 for r, c in cells)
    ]
    errors: list[str] = []
    if not candidates:
        return {
            "errors": ["no multi-cell nonzero component contains a cyan origin"],
            "height": height,
            "width": width,
            "components": components,
            "proto": None,
        }

    proto = sorted(candidates, key=_component_key)[0]
    proto_set = set(proto)
    proto_eights = sorted((r, c) for r, c in proto if grid[r][c] == 8)
    if not proto_eights:
        return {
            "errors": ["selected prototype contains no cyan origin"],
            "height": height,
            "width": width,
            "components": components,
            "proto": proto_set,
        }
    origin = proto_eights[0]
    top = min(r for r, _ in proto)
    left = min(c for _, c in proto)
    bottom = max(r for r, _ in proto)
    right = max(c for _, c in proto)
    rel = sorted(
        (r - origin[0], c - origin[1], grid[r][c]) for r, c in proto
    )
    support = frozenset((dr, dc) for dr, dc, _value in rel)
    template_kind = _SUPPORT_TO_KIND.get(support)
    payload_colors = {value for _dr, _dc, value in rel if value != 8}
    targets = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 8 and (r, c) not in proto_set
    ]
    outside_components = [
        cells for cells in components if set(cells) != proto_set
    ]
    component_of: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for cells in components:
        for cell in cells:
            component_of[cell] = cells
    foreign = [
        (r, c)
        for cells in outside_components
        for r, c in cells
        if grid[r][c] != 8
    ]
    target_records = []
    for target in targets:
        translated = [
            (target[0] + dr, target[1] + dc, value)
            for dr, dc, value in rel
        ]
        target_records.append(
            {
                "target": target,
                "component_size": len(component_of[target]),
                "translated": translated,
                "fully_visible": all(
                    0 <= r < height and 0 <= c < width
                    for r, c, _value in translated
                ),
            }
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "candidates": candidates,
        "proto": proto_set,
        "proto_eights": proto_eights,
        "origin": origin,
        "bbox": (top, left, bottom, right),
        "anchor_offset": (origin[0] - top, origin[1] - left),
        "rel": rel,
        "support": support,
        "template_kind": template_kind,
        "payload_colors": payload_colors,
        "targets": targets,
        "target_records": target_records,
        "outside_components": outside_components,
        "foreign": foreign,
    }


def _overlay(
    grid: list[list[int]],
    *,
    targets: list[tuple[int, int]] | None = None,
    include_value: Callable[[int], bool] | None = None,
    conflict_mode: str = "nine",
    align_bbox_top_left: bool = False,
) -> list[list[int]]:
    info = _analysis(grid)
    if info.get("proto") is None:
        return copy.deepcopy(grid)
    height, width = len(grid), len(grid[0])
    selected_targets = info["targets"] if targets is None else targets
    anchors = [info["origin"], *selected_targets]
    output = full_grid(height, width, 0)
    if align_bbox_top_left:
        top, left, _bottom, _right = info["bbox"]
        bbox_rel = [
            (r - top, c - left, grid[r][c]) for r, c in info["proto"]
        ]
        writes = bbox_rel
    else:
        writes = info["rel"]

    for anchor in anchors:
        for dr, dc, value in writes:
            if include_value is not None and not include_value(value):
                continue
            rr, cc = anchor[0] + dr, anchor[1] + dc
            if not (0 <= rr < height and 0 <= cc < width):
                continue
            old = output[rr][cc]
            if old == 0 or old == value:
                output[rr][cc] = value
            elif conflict_mode == "last":
                output[rr][cc] = value
            else:
                output[rr][cc] = 9
    return output


def oracle_output(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror for diagnostics/tests; canonical Racket remains authority."""
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    info = _analysis(grid)
    if info.get("proto") is None:
        raise ValueError("input does not contain an authority-selectable prototype")
    return _overlay(grid)


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    integer_bounds = {
        "grid_h": (9, 12),
        "grid_w": (10, 14),
        "n_anchors": (1, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in integer_bounds:
            if type(value) is not int:
                raise TypeError(f"{name} override must be an integer")
            lo, hi = integer_bounds[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
        elif name == "template_kind":
            if type(value) is not str:
                raise TypeError("template_kind override must be a string")
            if value not in TEMPLATE_KINDS:
                raise ValueError(
                    f"template_kind override {value!r} not in {TEMPLATE_KINDS!r}"
                )


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_exact_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _colored_template(
    kind: str, primary: int, secondary: int
) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (dr, dc, 8 if role == 8 else primary if role == 0 else secondary)
        for dr, dc, role in _TEMPLATE_ROLES[kind]
    )


def _valid_origins(
    height: int, width: int, template: tuple[tuple[int, int, int], ...]
) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(height)
        for c in range(width)
        if all(0 <= r + dr < height and 0 <= c + dc < width for dr, dc, _ in template)
    ]


def _stamp_cells(
    origin: tuple[int, int], template: tuple[tuple[int, int, int], ...]
) -> dict[tuple[int, int], int]:
    return {
        (origin[0] + dr, origin[1] + dc): value
        for dr, dc, value in template
    }


def _has_color_conflict(
    origins: list[tuple[int, int]], template: tuple[tuple[int, int, int], ...]
) -> bool:
    written: dict[tuple[int, int], int] = {}
    for origin in origins:
        for position, value in _stamp_cells(origin, template).items():
            if position in written and written[position] != value:
                return True
            written.setdefault(position, value)
    return False


def _candidate_targets(
    origins: list[tuple[int, int]],
    proto_origin: tuple[int, int],
    template: tuple[tuple[int, int, int], ...],
) -> list[tuple[int, int]]:
    proto_support = set(_stamp_cells(proto_origin, template))
    result = []
    for target in origins:
        if target in proto_support:
            continue
        # Keep destination markers out of the prototype's 4-connected component.
        if any(
            (target[0] + dr, target[1] + dc) in proto_support
            for dr, dc in _CARDINAL
        ):
            continue
        result.append(target)
    return result


def _choose_separate_targets(
    candidates: list[tuple[int, int]],
    n_anchors: int,
    proto_origin: tuple[int, int],
    template: tuple[tuple[int, int, int], ...],
) -> list[tuple[int, int]] | None:
    proto_stamp = set(_stamp_cells(proto_origin, template))

    def search(
        start: int,
        chosen: list[tuple[int, int]],
        occupied: set[tuple[int, int]],
    ) -> list[tuple[int, int]] | None:
        if len(chosen) == n_anchors:
            return list(chosen)
        for index in range(start, len(candidates)):
            target = candidates[index]
            if any(
                abs(target[0] - other[0]) + abs(target[1] - other[1]) <= 1
                for other in chosen
            ):
                continue
            stamp = set(_stamp_cells(target, template))
            if stamp & occupied:
                continue
            result = search(index + 1, [*chosen, target], occupied | stamp)
            if result is not None:
                return result
        return None

    return search(0, [], proto_stamp)


def _choose_conflict_targets(
    candidates: list[tuple[int, int]],
    n_anchors: int,
    proto_origin: tuple[int, int],
    template: tuple[tuple[int, int, int], ...],
) -> list[tuple[int, int]] | None:
    if n_anchors < 2:
        return None
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1 :]:
            if abs(left[0] - right[0]) + abs(left[1] - right[1]) != 1:
                continue
            selected = [left, right]
            if not _has_color_conflict([proto_origin, *selected], template):
                continue
            if n_anchors == 2:
                return selected
            for extra in candidates:
                if extra not in selected:
                    return [*selected, extra]
    return None


def _construct_grid(
    *,
    height: int,
    width: int,
    n_anchors: int,
    template_kind: str,
    layout_mode: str,
    primary: int,
    secondary: int,
    layout_rng,
) -> list[list[int]]:
    template = _colored_template(template_kind, primary, secondary)
    proto_origins = _valid_origins(height, width, template)
    layout_rng.shuffle(proto_origins)
    for proto_origin in proto_origins:
        candidates = _candidate_targets(proto_origins, proto_origin, template)
        layout_rng.shuffle(candidates)
        if layout_mode == "adjacent_conflict" and n_anchors >= 2:
            targets = _choose_conflict_targets(
                candidates, n_anchors, proto_origin, template
            )
        else:
            targets = _choose_separate_targets(
                candidates, n_anchors, proto_origin, template
            )
        if targets is None:
            continue
        grid = full_grid(height, width, 0)
        for (r, c), value in _stamp_cells(proto_origin, template).items():
            grid[r][c] = value
        for r, c in targets:
            grid[r][c] = 8
        return grid
    raise ValueError(
        f"could not construct {layout_mode} layout for {height}x{width}, "
        f"{template_kind}, n_anchors={n_anchors}"
    )



def _add_isolated_distractor(
    grid: list[list[int]], color: int, rng
) -> list[list[int]]:
    """Add one ignored singleton on a cell the authority leaves blank."""
    output = oracle_output(grid)
    height, width = len(grid), len(grid[0])
    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0
        and output[r][c] == 0
        and all(
            not (0 <= r + dr < height and 0 <= c + dc < width)
            or grid[r + dr][c + dc] == 0
            for dr, dc in _CARDINAL
        )
    ]
    if not candidates:
        raise ValueError("could not place an isolated ignored distractor")
    r, c = candidates[rng.randrange(len(candidates))]
    result = copy.deepcopy(grid)
    result[r][c] = color
    return result

def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile_index = schedule_profile(seed, sample_index, difficulty)
    (
        scheduled_h,
        scheduled_w,
        scheduled_anchors,
        scheduled_kind,
        layout_mode,
        add_distractor,
    ) = _PROFILE_SPECS[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 9, 12)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 10, 14)
    n_anchors = _draw_exact_int(ctx, "n_anchors", scheduled_anchors, 1, 3)
    template_kind = _draw_exact_choice(
        ctx, "template_kind", scheduled_kind, TEMPLATE_KINDS
    )
    color_rng = ctx.draw_rng("payload_colors")
    primary, secondary = _PAYLOAD_PAIRS[color_rng.randrange(len(_PAYLOAD_PAIRS))]
    layout_rng = ctx.draw_rng("layout")
    effective_layout = layout_mode if n_anchors >= 2 else "separate"
    grid = _construct_grid(
        height=height,
        width=width,
        n_anchors=n_anchors,
        template_kind=template_kind,
        layout_mode=effective_layout,
        primary=primary,
        secondary=secondary,
        layout_rng=layout_rng,
    )
    if add_distractor:
        grid = _add_isolated_distractor(
            grid, secondary, ctx.draw_rng("ignored_distractor")
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_anchors": n_anchors,
        "template_kind": template_kind,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    if effective_layout == "adjacent_conflict":
        if not _witness_adjacent_targets(grid) or not _witness_conflict_to_nine(grid):
            raise AssertionError("scheduled adjacent conflict was not realized")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected generator domain and authority disambiguation."""
    del difficulty, meta
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors or info.get("proto") is None:
        return errors or ["prototype analysis failed"]

    height, width = info["height"], info["width"]
    if not 9 <= height <= 12:
        errors.append(f"grid height must be in 9..12, got {height}")
    if not 10 <= width <= 14:
        errors.append(f"grid width must be in 10..14, got {width}")
    if any(value == 9 for row in grid for value in row):
        errors.append("maroon 9 is an output-only conflict color")
    if len(info["proto_eights"]) != 1:
        errors.append(
            f"prototype must contain exactly one cyan origin, found {len(info['proto_eights'])}"
        )
    if info["template_kind"] is None:
        errors.append("prototype support is not one of the declared canonical morphologies")
    if len(info["payload_colors"]) != 2:
        errors.append(
            f"prototype must use exactly two payload colors, found {len(info['payload_colors'])}"
        )
    else:
        counts = Counter(value for _dr, _dc, value in info["rel"] if value != 8)
        if sorted(counts.values()) != [1, len(info["proto"]) - 2]:
            errors.append("prototype must have one rare payload cell and one frequent payload")
        elif info["template_kind"] is not None:
            rare = min(counts, key=counts.get)
            expected_rare = {
                (dr, dc)
                for dr, dc, role in _TEMPLATE_ROLES[info["template_kind"]]
                if role == 1
            }
            actual_rare = {
                (dr, dc) for dr, dc, value in info["rel"] if value == rare
            }
            if actual_rare != expected_rare:
                errors.append("rare payload color is not in the morphology's canonical role")
    foreign_components = [
        cells
        for cells in info["outside_components"]
        if any(grid[r][c] != 8 for r, c in cells)
    ]
    if len(info["foreign"]) > 1:
        errors.append(
            f"expected at most one ignored payload distractor, found {len(info['foreign'])}"
        )
    for cells in foreign_components:
        values = [grid[r][c] for r, c in cells]
        if len(cells) != 1 or 8 in values:
            errors.append(
                "ignored foreground must be a singleton payload cell, never a mixed target component"
            )
            break
        if values[0] not in info["payload_colors"]:
            errors.append("ignored distractor must reuse a prototype payload color")
            break
    if not 1 <= len(info["targets"]) <= 3:
        errors.append(
            f"expected 1..3 cyan destinations outside the prototype, found {len(info['targets'])}"
        )
    other_sizes = [
        len(cells) for cells in info["outside_components"] if cells
    ]
    if other_sizes and len(info["proto"]) <= max(other_sizes):
        errors.append("prototype must be strictly larger than every destination component")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Every accepted grid is on the task-linked four-color teaching manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _analysis(grid)
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "n_anchors": len(info["targets"]),
        "template_kind": info["template_kind"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    info = _analysis(grid)
    output = oracle_output(grid)
    return {
        **observe_overrides(grid),
        "palette_size": len({value for row in grid for value in row}),
        "payload_colors": sorted(info["payload_colors"]),
        "anchor_offset": info["anchor_offset"],
        "adjacent_target_component": any(
            record["component_size"] > 1 for record in info["target_records"]
        ),
        "output_has_conflict_9": any(9 in row for row in output),
        "ignored_payload_cells": len(info["foreign"]),
    }


# ---------------------------------------------------------------------------
# Plausible rival rules and semantic witnesses
# ---------------------------------------------------------------------------


def _rival_identity(grid):
    return copy.deepcopy(grid)


def _rival_bbox_top_left(grid):
    return _overlay(grid, align_bbox_top_left=True)


def _rival_first_target_only(grid):
    info = _analysis(grid)
    return _overlay(grid, targets=info.get("targets", [])[:1])


def _rival_isolated_targets_only(grid):
    info = _analysis(grid)
    targets = [
        record["target"]
        for record in info.get("target_records", [])
        if record["component_size"] == 1
    ]
    return _overlay(grid, targets=targets)


def _rival_fixed_colors_2_3_only(grid):
    return _overlay(grid, include_value=lambda value: value in (2, 3, 8))


def _rival_last_writer_wins(grid):
    return _overlay(grid, conflict_mode="last")


def _rival_preserve_ignored_foreground(grid):
    output = oracle_output(grid)
    info = _analysis(grid)
    for r, c in info.get("foreign", []):
        if output[r][c] == 0:
            output[r][c] = grid[r][c]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_marker_only": _rival_identity,
    "bbox_top_left_alignment": _rival_bbox_top_left,
    "first_target_only": _rival_first_target_only,
    "isolated_targets_only": _rival_isolated_targets_only,
    "fixed_colors_2_3_only": _rival_fixed_colors_2_3_only,
    "last_writer_wins_conflicts": _rival_last_writer_wins,
    "preserve_ignored_foreground": _rival_preserve_ignored_foreground,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "isolated_targets_only": _rival_isolated_targets_only,
    "fixed_colors_2_3_only": _rival_fixed_colors_2_3_only,
}


def _lawful(grid) -> bool:
    return self_check(grid) == []


def _witness_multiple_targets(grid) -> bool:
    info = _analysis(grid)
    return (
        _lawful(grid)
        and len(info["targets"]) >= 2
        and oracle_output(grid) != _rival_first_target_only(grid)
    )


def _witness_origin_offset(grid) -> bool:
    info = _analysis(grid)
    return (
        _lawful(grid)
        and info["anchor_offset"] != (0, 0)
        and oracle_output(grid) != _rival_bbox_top_left(grid)
    )


def _witness_adjacent_targets(grid) -> bool:
    info = _analysis(grid)
    return (
        _lawful(grid)
        and any(record["component_size"] > 1 for record in info["target_records"])
        and oracle_output(grid) != _rival_isolated_targets_only(grid)
    )


def _witness_noncanonical_payload(grid) -> bool:
    info = _analysis(grid)
    return (
        _lawful(grid)
        and info["payload_colors"] != {2, 3}
        and oracle_output(grid) != _rival_fixed_colors_2_3_only(grid)
    )


def _witness_conflict_to_nine(grid) -> bool:
    if not _lawful(grid):
        return False
    output = oracle_output(grid)
    return any(9 in row for row in output) and output != _rival_last_writer_wins(grid)


def _witness_discard_ignored_foreground(grid) -> bool:
    info = _analysis(grid)
    return (
        _lawful(grid)
        and bool(info["foreign"])
        and oracle_output(grid) != _rival_preserve_ignored_foreground(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "multiple_targets": _witness_multiple_targets,
    "origin_not_bbox_top_left": _witness_origin_offset,
    "adjacent_destination_component": _witness_adjacent_targets,
    "noncanonical_payload_colors": _witness_noncanonical_payload,
    "conflicting_overlap_to_9": _witness_conflict_to_nine,
    "discard_ignored_foreground": _witness_discard_ignored_foreground,
}
WITNESS_RIVALS = {
    "multiple_targets": ["identity_marker_only", "first_target_only"],
    "origin_not_bbox_top_left": ["bbox_top_left_alignment"],
    "adjacent_destination_component": ["isolated_targets_only"],
    "noncanonical_payload_colors": ["fixed_colors_2_3_only"],
    "conflicting_overlap_to_9": ["last_writer_wins_conflicts"],
    "discard_ignored_foreground": ["preserve_ignored_foreground"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives every demo."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = oracle_output(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the anchor-copy grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with anchored overlay")

    try:
        query_answer = oracle_output(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the anchor-copy grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with anchored overlay")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and rival(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons
