"""Generator for S11_H2 — rotation-coded boundary stamps.

A single red (2) polyomino is the template.  Its 4-neighbour boundary is
normalized, rotated according to each code cell (1 -> 0 degrees, 3 -> 90,
4 -> 180, 6 -> 270), and stamped in cyan (8) with the code cell as the
normalized top-left anchor.  Stamp cells outside the canvas are clipped.

Ordinary draws deliberately contain an asymmetric template with at least one
strict interior cell, at least one fully visible stamp, and at least one
clipped stamp.  That makes boundary extraction, rotation, anchoring, and
clipping independently observable instead of admitting a whole-object-copy
shortcut.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f67822970902"
TASK_ID = "f67822970902"
VERSION = "3.0.0"
RULE_HASH = "8c510cf0a8f4"
# Every draw is a lawful boundary-stamp scene, so strict_canonical_like
# measures 150/150 (100%). The PRE-repair source scored 44% — which is HIGHER
# than seven of the twelve verified-good generators, so no global floor could
# ever have caught it (docs/SEMANTIC_GATE_CONTRACT.md section 2b). A task-linked
# floor is the only mechanism that makes this regression visible.
MIN_STRICT_FRAC = 0.9

SUMMARY = (
    "Extract the normalized 4-neighbour boundary of the unique red (2) "
    "template.  Every isolated code cell stamps that boundary in cyan (8): "
    "1 keeps the orientation, 3 rotates 90 degrees clockwise, 4 rotates 180 "
    "degrees, and 6 rotates 270 degrees.  The code cell is the normalized "
    "top-left anchor and cells beyond the bottom or right edge are clipped."
)

INVARIANTS = [
    "the palette is a subset of {0,1,2,3,4,6}",
    "there is exactly one 4-connected red (2) template of 5..16 cells",
    "the template boundary has four distinct rotations",
    "there are 1..8 code cells and every code produces a non-empty stamp",
    "code cells lie outside the template's one-cell halo",
    "every code contributes at least one output cell not supplied by another code",
    "ordinary draws with multiple codes include both a full and a clipped stamp",
    "ordinary templates have at least one strict interior cell",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6/7 canonical anchors in easy; 10..16 medium; 15..24 hard",
        "valid": "6..24",
    },
    "grid_w": {
        "type": "int",
        "default": "11/12 canonical anchors in easy; 12..20 medium; 16..26 hard",
        "valid": "8..26",
    },
    "tpl_k": {
        "type": "int",
        "default": "6..7 easy; 9..12 medium; 12..16 hard",
        "valid": "5..16",
    },
    "n_codes": {
        "type": "int",
        "default": "3 easy; 4..5 medium; 6..8 hard",
        "valid": "1..8",
    },
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CODES = (1, 3, 4, 6)
_CODE_ROT = {1: 0, 3: 1, 4: 2, 6: 3}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    min_r = min(row for row, _col in points)
    min_c = min(col for _row, col in points)
    return tuple(sorted((row - min_r, col - min_c) for row, col in points))


def _rotate_once(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    max_r = max(row for row, _col in points)
    return _normalize((col, max_r - row) for row, col in points)


def _rotate(cells: Iterable[tuple[int, int]], turns: int) -> tuple[tuple[int, int], ...]:
    result = _normalize(cells)
    for _ in range(turns % 4):
        result = _rotate_once(result)
    return result


def _boundary(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = set(cells)
    return tuple(
        sorted(
            point
            for point in points
            if any((point[0] + dr, point[1] + dc) not in points for dr, dc in _CARD)
        )
    )


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = [start]
        component: list[tuple[int, int]] = []
        for row, col in queue:
            component.append((row, col))
            for dr, dc in _CARD:
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)
        components.append(sorted(component))
    return components


def _rotated_boundaries(template: Iterable[tuple[int, int]]) -> dict[int, tuple[tuple[int, int], ...]]:
    normalized_boundary = _normalize(_boundary(template))
    return {code: _rotate(normalized_boundary, turns) for code, turns in _CODE_ROT.items()}


def _stamp_cells(
    anchor: tuple[int, int],
    offsets: Iterable[tuple[int, int]],
    height: int,
    width: int,
) -> set[tuple[int, int]]:
    row, col = anchor
    return {
        (row + dr, col + dc)
        for dr, dc in offsets
        if 0 <= row + dr < height and 0 <= col + dc < width
    }


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        if label in overrides and overrides[label] is not None and type(overrides[label]) is not int:
            raise ValueError(f"{label} must be an integer")


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    """Record a scheduled default while honoring the full declared override range."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _default_axes(ctx, difficulty: Any, sample_index: int) -> tuple[int, int, int, int]:
    band = "medium" if difficulty is None else difficulty
    if band == "easy":
        profile = ((6, 11), (7, 12))[sample_index % 2]
        default_h, default_w = profile
        default_k = (6, 7)[sample_index % 2]
        default_codes = 3
    elif band == "hard":
        default_h = ctx.draw_rng("grid_h_default").randint(15, 24)
        default_w = ctx.draw_rng("grid_w_default").randint(16, 26)
        default_k = ctx.draw_rng("tpl_k_default").randint(12, 16)
        default_codes = ctx.draw_rng("n_codes_default").randint(6, 8)
    else:
        default_h = ctx.draw_rng("grid_h_default").randint(10, 16)
        default_w = ctx.draw_rng("grid_w_default").randint(12, 20)
        default_k = ctx.draw_rng("tpl_k_default").randint(9, 12)
        default_codes = ctx.draw_rng("n_codes_default").randint(4, 5)

    height = _draw_scheduled_int(ctx, "grid_h", 6, 24, default_h)
    width = _draw_scheduled_int(ctx, "grid_w", 8, 26, default_w)

    # A lone dimension override remains a valid call.  Keep the other free
    # defaults informative but scale them to the realized canvas instead of
    # accidentally combining a canonical-height canvas with a hard-band
    # 16-cell template and eight independently visible stamps.
    if ctx.overrides.get("tpl_k") is None:
        if height <= 7:
            default_k = min(default_k, 7)
        if width <= 9:
            default_k = min(default_k, 8)
    if ctx.overrides.get("n_codes") is None:
        if height <= 7 or width <= 9:
            default_codes = min(default_codes, 4)

    template_size = _draw_scheduled_int(ctx, "tpl_k", 5, 16, default_k)
    code_count = _draw_scheduled_int(ctx, "n_codes", 1, 8, default_codes)
    return height, width, template_size, code_count


def _shape_ok(cells: set[tuple[int, int]], *, require_interior: bool) -> bool:
    normalized = _normalize(cells)
    boundary = _boundary(normalized)
    if require_interior and len(boundary) == len(normalized):
        return False
    rotations = {_rotate(boundary, turns) for turns in range(4)}
    return len(rotations) == 4


def _build_template(rng, size: int, max_h: int, max_w: int) -> tuple[tuple[int, int], ...]:
    """Build a connected asymmetric polyomino; ordinary sizes have an interior."""
    require_interior = size >= 6
    for _attempt in range(2000):
        if require_interior:
            # The centre has all four cardinal neighbours and therefore remains
            # a strict interior cell.  The sixth and later cells break symmetry.
            cells = {(1, 1), (0, 1), (2, 1), (1, 0), (1, 2)}
        else:
            cells = {(0, 0)}

        while len(cells) < size:
            frontier = {
                (row + dr, col + dc)
                for row, col in cells
                for dr, dc in _CARD
                if (row + dr, col + dc) not in cells
            }
            choices = []
            for point in frontier:
                trial = _normalize((*cells, point))
                trial_h = max(row for row, _col in trial) + 1
                trial_w = max(col for _row, col in trial) + 1
                if trial_h <= max_h and trial_w <= max_w:
                    choices.append(point)
            if not choices:
                break
            cells.add(rng.choice(sorted(choices)))

        if len(cells) != size:
            continue
        normalized = set(_normalize(cells))
        if _shape_ok(normalized, require_interior=require_interior):
            return _normalize(normalized)
    raise ValueError(
        f"could not construct an asymmetric {size}-cell template within {max_h}x{max_w}"
    )


def _candidate_anchors(
    height: int,
    width: int,
    forbidden: set[tuple[int, int]],
    offsets: tuple[tuple[int, int], ...],
    want_full: bool,
) -> list[tuple[tuple[int, int], set[tuple[int, int]]]]:
    candidates: list[tuple[tuple[int, int], set[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            if (row, col) in forbidden:
                continue
            stamped = _stamp_cells((row, col), offsets, height, width)
            if not stamped:
                continue
            full = len(stamped) == len(offsets)
            if full == want_full:
                candidates.append(((row, col), stamped))
    return candidates


def _place_codes(
    rng,
    height: int,
    width: int,
    template_cells: set[tuple[int, int]],
    code_values: list[int],
    rotated: dict[int, tuple[tuple[int, int], ...]],
    sample_index: int,
) -> list[tuple[int, int, int]] | None:
    halo = {
        (row + dr, col + dc)
        for row, col in template_cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < height and 0 <= col + dc < width
    }

    options_by_code: dict[int, list[tuple[tuple[int, int], set[tuple[int, int]], bool]]] = {}
    for code in set(code_values):
        options: list[tuple[tuple[int, int], set[tuple[int, int]], bool]] = []
        for want_full in (True, False):
            for anchor, stamped in _candidate_anchors(
                height, width, halo, rotated[code], want_full
            ):
                # A clipped anchor is useful only when the code still matters.
                # Reject anchors where clipping collapses this rotation to the
                # exact same visible set as any other code value.
                if any(
                    stamped == _stamp_cells(anchor, rotated[other], height, width)
                    for other in _CODES
                    if other != code
                ):
                    continue
                options.append((anchor, stamped, want_full))
        if not options:
            return None
        options_by_code[code] = options

    preferred_modes: dict[int, bool] = {}
    if len(code_values) == 1:
        preferred_modes[0] = sample_index % 2 == 0
    else:
        partial_indices = [
            index
            for index, code in enumerate(code_values)
            if any(not option[2] for option in options_by_code[code])
        ]
        full_indices = [
            index
            for index, code in enumerate(code_values)
            if any(option[2] for option in options_by_code[code])
        ]
        if not partial_indices or not full_indices:
            return None
        clipped_index = partial_indices[sample_index % len(partial_indices)]
        full_index = next((index for index in full_indices if index != clipped_index), full_indices[0])
        preferred_modes[clipped_index] = False
        preferred_modes[full_index] = True

    # Randomized deterministic retries give the small canonical canvases a
    # genuine joint placement search instead of committing greedily to an
    # anchor that makes a later code redundant.
    for _attempt in range(600):
        used: set[tuple[int, int]] = set()
        output_union: set[tuple[int, int]] = set()
        chosen: list[tuple[int, int, int, set[tuple[int, int]], bool]] = []
        failed = False
        for index, code in enumerate(code_values):
            preferred_full = preferred_modes.get(index, index % 2 == 0)
            available = [
                option
                for option in options_by_code[code]
                if option[0] not in used and option[1] - output_union
            ]
            preferred = [option for option in available if option[2] == preferred_full]
            pool = preferred or available
            if not pool:
                failed = True
                break
            # Favor anchors adding more currently new cells while retaining
            # layout variety among ties.
            best_gain = max(len(stamped - output_union) for _anchor, stamped, _full in pool)
            shortlist = [
                option
                for option in pool
                if len(option[1] - output_union) >= max(1, best_gain - 1)
            ]
            anchor, stamped, is_full = rng.choice(shortlist)
            used.add(anchor)
            output_union.update(stamped)
            chosen.append((anchor[0], anchor[1], code, stamped, is_full))
        if failed:
            continue
        if len(chosen) >= 2:
            full_flags = [item[4] for item in chosen]
            if all(full_flags) or not any(full_flags):
                continue
        if any(
            not stamped
            - set().union(*(other[3] for j, other in enumerate(chosen) if j != index))
            for index, (_row, _col, _code, stamped, _full) in enumerate(chosen)
        ):
            continue
        return [(row, col, code) for row, col, code, _stamped, _full in chosen]
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty rectangle"]}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"]}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular with non-empty rows"]}
    height = len(grid)
    if not 6 <= height <= 24 or not 8 <= width <= 26:
        errors.append("grid dimensions must be within height 6..24 and width 8..26")

    bad = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or value not in (0, 1, 2, 3, 4, 6)
    ]
    if bad:
        errors.append("input palette must be a subset of {0,1,2,3,4,6}")
        return {"errors": errors, "grid_h": height, "grid_w": width, "bad_cells": bad[:8]}

    templates = _components([list(row) for row in grid], 2)
    if len(templates) != 1:
        errors.append(f"expected exactly one red template component, found {len(templates)}")
        return {"errors": errors, "grid_h": height, "grid_w": width}
    template = set(templates[0])
    template_size = len(template)
    if not 5 <= template_size <= 16:
        errors.append(f"template size must be 5..16 cells, found {template_size}")

    boundary = _boundary(template)
    interior = template - set(boundary)
    rotated = _rotated_boundaries(template)
    rotation_signatures = set(rotated.values())
    if len(rotation_signatures) != 4:
        errors.append("template boundary must have four distinct rotations")

    codes = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _CODES
    ]
    if not 1 <= len(codes) <= 8:
        errors.append(f"expected 1..8 code cells, found {len(codes)}")

    template_halo = {
        (row + dr, col + dc)
        for row, col in template
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }
    if any((row, col) in template_halo for row, col, _value in codes):
        errors.append("code cells must lie outside the template's one-cell halo")

    stamp_sets: list[set[tuple[int, int]]] = []
    full_count = 0
    for row, col, code in codes:
        stamped = _stamp_cells((row, col), rotated[code], height, width)
        if not stamped:
            errors.append(f"code at {(row, col)} produces an empty clipped stamp")
        if any(
            stamped == _stamp_cells((row, col), rotated[other], height, width)
            for other in _CODES
            if other != code
        ):
            errors.append(f"code at {(row, col)} is rotation-insensitive after clipping")
        stamp_sets.append(stamped)
        if len(stamped) == len(rotated[code]):
            full_count += 1
    clipped_count = len(codes) - full_count
    if len(codes) >= 2 and (full_count == 0 or clipped_count == 0):
        errors.append("multi-code scenes must include at least one full and one clipped stamp")

    for index, stamped in enumerate(stamp_sets):
        others = set().union(*(other for j, other in enumerate(stamp_sets) if j != index))
        if not stamped - others:
            errors.append(f"code #{index} contributes no unique output cell")

    boundary_union = set().union(*stamp_sets) if stamp_sets else set()
    normalized_template = _normalize(template)
    body_union: set[tuple[int, int]] = set()
    for row, col, code in codes:
        body_union.update(
            _stamp_cells(
                (row, col),
                _rotate(normalized_template, _CODE_ROT[code]),
                height,
                width,
            )
        )
    body_copy_extra = body_union - boundary_union

    return {
        "errors": sorted(set(errors)),
        "grid_h": height,
        "grid_w": width,
        "tpl_k": template_size,
        "n_codes": len(codes),
        "template": sorted(template),
        "boundary": list(boundary),
        "interior_count": len(interior),
        "codes": codes,
        "code_histogram": dict(sorted(Counter(value for _r, _c, value in codes).items())),
        "full_stamps": full_count,
        "clipped_stamps": clipped_count,
        "stamp_sets": stamp_sets,
        "rotation_support": sorted({value for _r, _c, value in codes}),
        "body_copy_extra_count": len(body_copy_extra),
        "body_copy_extra_cells": sorted(body_copy_extra),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, no-op, or rule-hiding input scenes."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "tpl_k": analysis["tpl_k"],
        "n_codes": analysis["n_codes"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for parity tests; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    rotated = _rotated_boundaries(analysis["template"])
    for row, col, code in analysis["codes"]:
        for out_row, out_col in _stamp_cells(
            (row, col), rotated[code], analysis["grid_h"], analysis["grid_w"]
        ):
            output[out_row][out_col] = 8
    return output


# ---------------------------------------------------------------------------
# Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md)
# ---------------------------------------------------------------------------

def strict_canonical_like(grid) -> list[str]:
    """[] when `grid` is a lawful canonical-like scene for THIS task.

    Enforces the full task grammar: palette subset {0,1,2,3,4,6}, exactly one
    red template with four distinct boundary rotations, 1..8 halo-respecting
    code cells, non-empty rotation-sensitive stamps, full+clipped mix in
    multi-code scenes, and a unique output contribution per code.

    Deliberately does NOT demand a strict-interior template: all three
    canonical templates are interior-free, so requiring one would reject the
    very inputs this predicate characterises.  The interior / body-vs-boundary
    requirement is enforced per band via SEMANTIC_WITNESSES instead.  Pure.
    """
    return list(_analyze(grid)["errors"])


def _lawful_analysis(grid) -> dict[str, Any] | None:
    """Analysis dict for a lawful scene, else None.  Pure."""
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness_field(grid, extract) -> bool:
    analysis = _lawful_analysis(grid)
    return False if analysis is None else bool(extract(analysis))


SEMANTIC_WITNESSES = {
    # every rotation code must actually be demonstrated
    "code_0deg": lambda grid: _witness_field(grid, lambda a: 1 in a["rotation_support"]),
    "code_90deg": lambda grid: _witness_field(grid, lambda a: 3 in a["rotation_support"]),
    "code_180deg": lambda grid: _witness_field(grid, lambda a: 4 in a["rotation_support"]),
    "code_270deg": lambda grid: _witness_field(grid, lambda a: 6 in a["rotation_support"]),
    # clipping must be observable in both directions
    "full_stamp": lambda grid: _witness_field(grid, lambda a: a["full_stamps"] >= 1),
    "clipped_stamp": lambda grid: _witness_field(grid, lambda a: a["clipped_stamps"] >= 1),
    # the headline competitor-killer: canonical templates have NO interior,
    # so whole-body copying is only falsified by generated interior templates
    "strict_interior_template": lambda grid: _witness_field(
        grid, lambda a: a["interior_count"] >= 1
    ),
    "boundary_beats_whole_body": lambda grid: _witness_field(
        grid, lambda a: a["body_copy_extra_count"] >= 1
    ),
}


def _competitor_outputs(grid) -> dict[str, list[list[int]]] | None:
    """Outputs of the plausible competing rules on a lawful scene, else None.

    Competitors implemented:
      whole_body_copy — stamp the rotated WHOLE red body, not its boundary
      rotation_blind  — stamp the 0-degree boundary regardless of code value
      centre_anchor   — anchor the code cell at the stamp's bbox centre
      clip_averse     — drop any stamp that would need clipping
    Pure.
    """
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    height, width = analysis["grid_h"], analysis["grid_w"]
    normalized_template = _normalize(analysis["template"])
    boundary = _normalize(_boundary(normalized_template))

    def paint(cells: set[tuple[int, int]]) -> list[list[int]]:
        out = full_grid(height, width, 0)
        for row, col in cells:
            out[row][col] = 8
        return out

    body_cells: set[tuple[int, int]] = set()
    blind_cells: set[tuple[int, int]] = set()
    centre_cells: set[tuple[int, int]] = set()
    averse_cells: set[tuple[int, int]] = set()
    for row, col, code in analysis["codes"]:
        turns = _CODE_ROT[code]
        rotated_boundary = _rotate(boundary, turns)
        body_cells |= _stamp_cells(
            (row, col), _rotate(normalized_template, turns), height, width
        )
        blind_cells |= _stamp_cells((row, col), boundary, height, width)
        stamp_h = max(r for r, _c in rotated_boundary) + 1
        stamp_w = max(c for _r, c in rotated_boundary) + 1
        centre_cells |= {
            (row + dr - stamp_h // 2, col + dc - stamp_w // 2)
            for dr, dc in rotated_boundary
            if 0 <= row + dr - stamp_h // 2 < height
            and 0 <= col + dc - stamp_w // 2 < width
        }
        stamped = _stamp_cells((row, col), rotated_boundary, height, width)
        if len(stamped) == len(rotated_boundary):
            averse_cells |= stamped
    return {
        "whole_body_copy": paint(body_cells),
        "rotation_blind": paint(blind_cells),
        "centre_anchor": paint(centre_cells),
        "clip_averse": paint(averse_cells),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """[] when the demos force the boundary-stamp rule on the query.

    A competitor that reproduces EVERY demo output yet answers the query
    differently means the lesson underdetermines the rule.  The critical case
    is whole_body_copy: canonical-style interior-free templates never falsify
    it, so lessons must include interior-bearing demos.  Pure.
    """
    reasons: list[str] = []
    query_competitors = _competitor_outputs(query.get("input"))
    if query_competitors is None:
        return ["query input is not a lawful scene for this task"]
    query_truth = rule_mirror(query.get("input"))

    demo_rows: list[tuple[dict, dict[str, list[list[int]]]]] = []
    for index, demo in enumerate(demos):
        competitors = _competitor_outputs(demo.get("input"))
        if competitors is None:
            reasons.append(f"demo {index} input is not a lawful scene for this task")
            continue
        if demo.get("output") != rule_mirror(demo.get("input")):
            reasons.append(
                f"demo {index} output disagrees with the boundary-stamp rule mirror"
            )
            continue
        demo_rows.append((demo, competitors))
    if reasons:
        return sorted(set(reasons))

    for name in sorted(query_competitors):
        survives = all(
            competitors[name] == demo["output"] for demo, competitors in demo_rows
        )
        if survives and query_competitors[name] != query_truth:
            reasons.append(
                f"competing rule '{name}' matches every demo yet answers the "
                "query differently"
            )
    return sorted(set(reasons))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, structurally informative input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, template_size, code_count = _default_axes(ctx, difficulty, sample_index)

    max_template_h = min(6, height - 1)
    max_template_w = min(7, width - 2)
    if max_template_h < 3 or max_template_w < 3:
        raise ValueError("grid is too small to hold an informative template and code anchors")

    shape_rng = ctx.draw_rng("template_shape")
    layout_rng = ctx.draw_rng("layout")
    template = _build_template(shape_rng, template_size, max_template_h, max_template_w)
    template_h = max(row for row, _col in template) + 1
    template_w = max(col for _row, col in template) + 1
    rotated = _rotated_boundaries(template)

    start = sample_index % len(_CODES)
    code_values = [_CODES[(start + index) % len(_CODES)] for index in range(code_count)]

    positions = [
        (row, col)
        for row in range(height - template_h + 1)
        for col in range(width - template_w + 1)
    ]
    layout_rng.shuffle(positions)
    # Canonical-scale easy scenes preferentially put the template near the
    # upper-left, while the remaining bands retain broad position support.
    if difficulty == "easy":
        positions.sort(key=lambda point: point[0] + point[1])

    for template_row, template_col in positions:
        absolute_template = {
            (template_row + row, template_col + col) for row, col in template
        }
        placed_codes = _place_codes(
            layout_rng,
            height,
            width,
            absolute_template,
            code_values,
            rotated,
            sample_index,
        )
        if placed_codes is None:
            continue
        grid = full_grid(height, width, 0)
        for row, col in absolute_template:
            grid[row][col] = 2
        for row, col, code in placed_codes:
            grid[row][col] = code
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        if template_size >= 6 and (
            analysis["interior_count"] < 1
            or analysis["body_copy_extra_count"] < 1
        ):
            continue
        return grid

    raise ValueError(
        "could not place the requested template/codes while preserving full, "
        "clipped, and uniquely effective stamp witnesses"
    )
