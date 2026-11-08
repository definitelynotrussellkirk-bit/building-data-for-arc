"""Generator for 14b:m92 — crop the component selected by a bottom-row key.

The final row contains one nonzero key cell.  Above it are three or four
isolated, monochromatic 4-connected blobs.  Exactly one blob has the key
colour; the canonical rule returns the tight bounding-box crop of that blob.

The ordinary distribution deliberately places a smaller and a larger
distractor around the selected blob.  Consequently the key is necessary:
"pick the smallest", "pick the largest/modal colour", and fixed-position
shortcuts all fail on generated lessons.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "30aababfb197"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "d7f9b4f68d45"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the single nonzero colour in the bottom row. In the rows above, "
    "find the unique 4-connected blob of that colour and return its tight "
    "bounding-box crop, preserving the blob's colour and internal zero cells."
)

INVARIANTS = [
    "background is colour 0",
    "the bottom row contains exactly one nonzero key cell",
    "the body contains three or four isolated monochromatic blobs in distinct colours",
    "exactly one body blob has the key colour and at least two blobs are distractors",
    "the selected blob is non-solid inside a bbox at least 2x2",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
# Prefixes are intentionally unique for both the 3-blob and 4-blob branches,
# so palette_kind is exactly recoverable from the returned grid.
_PALETTES = {
    "default": (1, 2, 3, 4),
    "warm": (2, 4, 7, 9),
    "cool": (1, 5, 8, 6),
    "varied": (3, 6, 8, 9),
}
_PALETTE_SIGNATURES = {
    frozenset(colors[:count]): kind
    for kind, colors in _PALETTES.items()
    for count in (3, 4)
}

AXES = {
    "grid_h": {"type": "int", "default": "banded 9..15", "valid": "9..15"},
    "grid_w": {"type": "int", "default": "banded 10..16", "valid": "10..16"},
    "palette_kind": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "|".join(PALETTE_KINDS),
    },
    "n_blobs": {"type": "int", "default": "sample_index cycle 3..4", "valid": "3..4"},
    "key_column": {"type": "int", "default": "rng 0..9", "valid": "0..9"},
    "target_size": {"type": "int", "default": "sample_index cycle 5..7", "valid": "5..7"},
}

# Every finite boundary tuple is supported by the slot construction.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_H_RANGE = (9, 15)
_W_RANGE = (10, 16)
_TARGET_RANGE = (5, 7)
_CANONICAL_PROFILES = ((9, 11), (10, 12), (10, 13), (10, 14), (11, 13))
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in values
        ):
            raise ValueError("grid colours must be literal integers in 0..9")
        rows.append(values)
    return rows


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return row-major monochromatic 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            colour = grid[r][c]
            if colour == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rs = [cell[0] for cell in cells]
            cs = [cell[1] for cell in cells]
            out.append(
                {
                    "color": colour,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rs), min(cs), max(rs), max(cs)),
                }
            )
    return out


def _crop_component(body: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    r1, c1, r2, c2 = component["bbox"]
    return [row[c1 : c2 + 1] for row in body[r1 : r2 + 1]]


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    if not (_H_RANGE[0] <= h <= _H_RANGE[1]):
        errors.append(f"grid height {h} outside {_H_RANGE[0]}..{_H_RANGE[1]}")
    if not (_W_RANGE[0] <= w <= _W_RANGE[1]):
        errors.append(f"grid width {w} outside {_W_RANGE[0]}..{_W_RANGE[1]}")

    key_cells = [(c, value) for c, value in enumerate(values[-1]) if value != 0]
    if len(key_cells) != 1:
        errors.append(f"expected exactly one bottom-row key, got {len(key_cells)}")
        return {
            "errors": errors,
            "grid": values,
            "height": h,
            "width": w,
            "key_cells": key_cells,
        }

    key_column, key_color = key_cells[0]
    body = [row[:] for row in values[:-1]]
    components = _components(body)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3..4 body blobs, got {len(components)}")

    by_color: dict[int, list[dict[str, Any]]] = {}
    for component in components:
        by_color.setdefault(component["color"], []).append(component)
        if component["size"] < 3:
            errors.append(
                f"body blob colour {component['color']} has size {component['size']}, expected at least 3"
            )
    repeated = sorted(color for color, items in by_color.items() if len(items) != 1)
    if repeated:
        errors.append(f"each body colour must form exactly one blob; repeated colours {repeated}")


    key_components = by_color.get(key_color, [])
    if len(key_components) != 1:
        errors.append(
            f"expected exactly one body blob in key colour {key_color}, got {len(key_components)}"
        )
        target = None
    else:
        target = key_components[0]

    distractors = [component for component in components if component is not target]
    if target is not None and len(distractors) < 2:
        errors.append("expected at least two distractor body blobs")

    output: list[list[int]] | None = None
    if target is not None:
        r1, c1, r2, c2 = target["bbox"]
        bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
        if bbox_h < 2 or bbox_w < 2:
            errors.append("selected blob bbox must be at least 2x2")
        if bbox_h * bbox_w <= target["size"]:
            errors.append("selected blob must leave at least one zero inside its bbox")
        bbox_colors = {
            body[r][c]
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        if not bbox_colors <= {0, key_color}:
            errors.append("a distractor intrudes into the selected blob's bbox")
        output = _crop_component(body, target)

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "body": body,
        "key_column": key_column,
        "key_color": key_color,
        "components": components,
        "target": target,
        "distractors": distractors,
        "n_blobs": len(components),
        "target_size": target["size"] if target is not None else None,
        "body_colors": frozenset(by_color),
        "output": output,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and shortcut-hiding scenes; accept all canonical inputs."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else {}
    if not requested:
        return errors
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in AXES and observed.get(axis) != value:
            errors.append(f"meta {axis} requested {value!r}, observed {observed.get(axis)!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis directly from the returned grid."""
    analysis = _analysis_or_raise(grid)
    signature = analysis["body_colors"]
    kind = _PALETTE_SIGNATURES.get(signature)
    if kind is None:
        raise ValueError(f"body palette {sorted(signature)} has no declared palette_kind")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "palette_kind": kind,
        "n_blobs": analysis["n_blobs"],
        "key_column": analysis["key_column"],
        "target_size": analysis["target_size"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is a strict extension that includes all 5 canonicals."""
    return self_check(grid)


def _draw_axis_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _slots(body_h: int, width: int) -> list[tuple[int, int, int, int]]:
    """Four separated inclusive rectangles, each at least 3x4 at min size."""
    gap_r = (body_h - 1) // 2
    gap_c = (width - 1) // 2
    slots = [
        (0, 0, gap_r - 1, gap_c - 1),
        (0, gap_c + 1, gap_r - 1, width - 1),
        (gap_r + 1, 0, body_h - 1, gap_c - 1),
        (gap_r + 1, gap_c + 1, body_h - 1, width - 1),
    ]
    if any(r2 - r1 + 1 < 3 or c2 - c1 + 1 < 4 for r1, c1, r2, c2 in slots):
        raise ValueError(f"{body_h + 1}x{width} grid cannot host four blob slots")
    return slots


def _shape_in_slot(
    rng,
    slot: tuple[int, int, int, int],
    size: int,
    *,
    require_internal_zero: bool,
) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = slot
    sh, sw = r2 - r1 + 1, c2 - c1 + 1
    for _ in range(400):
        local = grow_blob(rng, sh, sw, set(), size, max_attempts=20)
        if local is None:
            continue
        rs = [r for r, _ in local]
        cs = [c for _, c in local]
        bbox_h, bbox_w = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        if bbox_h < 2 or bbox_w < 2:
            continue
        if require_internal_zero and bbox_h * bbox_w <= size:
            continue
        return {(r1 + r, c1 + c) for r, c in local}
    raise RuntimeError(f"could not draw connected size-{size} shape in {sh}x{sw} slot")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    # A deterministic four-step teaching schedule guarantees variation inside
    # every consecutive lesson window while preserving exact caller overrides.
    scheduled = {
        "palette_kind": PALETTE_KINDS[sample_index % len(PALETTE_KINDS)],
        "n_blobs": 3 + (sample_index % 2),
        "target_size": _TARGET_RANGE[0] + (sample_index % 3),
    }
    effective_overrides = {**scheduled, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    h_defaults = {"easy": (9, 11), "medium": (9, 13), "hard": (12, 15)}[band]
    w_defaults = {"easy": (10, 12), "medium": (11, 14), "hard": (13, 16)}[band]

    # Even sample indexes are exact canonical-profile anchors.  This keeps
    # every difficulty band on the task's observed scale while odd indexes
    # retain the broader curriculum.  Explicit dimension overrides always win.
    canonical_anchor = sample_index % 2 == 0
    anchor_h, anchor_w = _CANONICAL_PROFILES[(sample_index // 2) % len(_CANONICAL_PROFILES)]
    h_range = (anchor_h, anchor_h) if canonical_anchor else h_defaults
    w_range = (anchor_w, anchor_w) if canonical_anchor else w_defaults
    h = _draw_axis_int(ctx, overrides, "grid_h", *h_range, *_H_RANGE)
    w = _draw_axis_int(ctx, overrides, "grid_w", *w_range, *_W_RANGE)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    n_blobs = ctx.draw_int("n_blobs", 3, 4)
    target_size = ctx.draw_int("target_size", *_TARGET_RANGE)
    key_column = ctx.draw_int("key_column", 0, 9)

    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    grid[-1][key_column] = 1  # overwritten after role colours are assigned

    slots = _slots(h - 1, w)[:n_blobs]
    target_slot_index = sample_index % n_blobs
    target_slot = slots[target_slot_index]

    colors = list(_PALETTES[palette_kind][:n_blobs])
    rng.shuffle(colors)
    key_color = colors[0]
    grid[-1][key_column] = key_color

    # The target is never the smallest or largest body blob.  In the 4-blob
    # branch an equal-sized distractor additionally destroys unique-size cues.
    distractor_sizes = [target_size - 2, target_size + 2]
    if n_blobs == 4:
        distractor_sizes.append(target_size)
    rng.shuffle(distractor_sizes)

    remaining_colors = iter(colors[1:])
    remaining_sizes = iter(distractor_sizes)
    for index, slot in enumerate(slots):
        if index == target_slot_index:
            color = key_color
            size = target_size
            require_internal_zero = True
        else:
            color = next(remaining_colors)
            size = next(remaining_sizes)
            require_internal_zero = False
        cells = _shape_in_slot(
            rng,
            slot,
            size,
            require_internal_zero=require_internal_zero,
        )
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.recorded_draws()},
    )
    if errors:
        raise AssertionError("generator produced invalid task grid: " + "; ".join(errors))
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic mirror; canonical Racket remains the sole output authority."""
    output = _analysis_or_raise(grid)["output"]
    return [row[:] for row in output]


def _crop_choice(grid, key: Callable[[dict[str, Any]], Any], *, reverse=False):
    analysis = _analysis_or_raise(grid)
    component = sorted(analysis["components"], key=key, reverse=reverse)[0]
    return _crop_component(analysis["body"], component)


def _rival_largest(grid):
    return _crop_choice(grid, lambda component: (component["size"], -component["bbox"][0]), reverse=True)


def _rival_smallest(grid):
    return _crop_choice(grid, lambda component: (component["size"], component["bbox"][0]))


def _rival_topmost(grid):
    return _crop_choice(grid, lambda component: (component["bbox"][0], component["bbox"][1]))


def _rival_leftmost(grid):
    return _crop_choice(grid, lambda component: (component["bbox"][1], component["bbox"][0]))


def _rival_modal_colour(grid):
    analysis = _analysis_or_raise(grid)
    counts = Counter(value for row in analysis["grid"] for value in row if value != 0)
    modal = max(counts, key=lambda color: (counts[color], -color))
    component = next(component for component in analysis["components"] if component["color"] == modal)
    return _crop_component(analysis["body"], component)


def _rival_emit_key(grid):
    return [[_analysis_or_raise(grid)["key_color"]]]


def _rival_solid_bbox(grid):
    analysis = _analysis_or_raise(grid)
    r1, c1, r2, c2 = analysis["target"]["bbox"]
    return [[analysis["key_color"]] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]


SEMANTIC_RIVALS = {
    "largest_blob": _rival_largest,
    "smallest_blob": _rival_smallest,
    "topmost_blob": _rival_topmost,
    "leftmost_blob": _rival_leftmost,
    "modal_colour_blob": _rival_modal_colour,
    "emit_key_cell": _rival_emit_key,
    "solid_selected_bbox": _rival_solid_bbox,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _target_not_extreme(grid, which: str) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    target_size = analysis["target"]["size"]
    sizes = [component["size"] for component in analysis["distractors"]]
    return target_size < max(sizes) if which == "largest" else target_size > min(sizes)


def _target_not_positional(grid, which: str) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    target = analysis["target"]
    if which == "top":
        return target["bbox"][0] > min(component["bbox"][0] for component in analysis["components"])
    return target["bbox"][1] > min(component["bbox"][1] for component in analysis["components"])


def _nonmodal_target(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    counts = Counter(value for row in analysis["grid"] for value in row if value != 0)
    return counts[analysis["key_color"]] < max(counts.values())


def _target_has_hole(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    r1, c1, r2, c2 = analysis["target"]["bbox"]
    return (r2 - r1 + 1) * (c2 - c1 + 1) > analysis["target"]["size"]


SEMANTIC_WITNESSES = {
    "key_selects_nonlargest": lambda grid: _target_not_extreme(grid, "largest"),
    "key_selects_nonsmallest": lambda grid: _target_not_extreme(grid, "smallest"),
    "key_selects_nontopmost": lambda grid: _target_not_positional(grid, "top"),
    "key_selects_nonleftmost": lambda grid: _target_not_positional(grid, "left"),
    "key_colour_is_nonmodal": _nonmodal_target,
    "selected_shape_has_internal_zero": _target_has_hole,
    "three_blob_branch": lambda grid: (_valid_analysis(grid) or {}).get("n_blobs") == 3,
    "four_blob_branch": lambda grid: (_valid_analysis(grid) or {}).get("n_blobs") == 4,
    "equal_size_distractor_branch": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and any(component["size"] == analysis["target"]["size"] for component in analysis["distractors"])
    ),
}

WITNESS_RIVALS = {
    "key_selects_nonlargest": ["largest_blob", "modal_colour_blob"],
    "key_selects_nonsmallest": ["smallest_blob"],
    "key_selects_nontopmost": ["topmost_blob"],
    "key_selects_nonleftmost": ["leftmost_blob"],
    "key_colour_is_nonmodal": ["modal_colour_blob"],
    "selected_shape_has_internal_zero": ["solid_selected_bbox"],
    "three_blob_branch": ["largest_blob"],
    "four_blob_branch": ["largest_blob"],
    "equal_size_distractor_branch": ["largest_blob"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut fits every demo but changes query."""
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"{label} input violates teaching grammar: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            reasons.append(f"{label} output disagrees with the key-selected crop rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == _coerce_grid(pair["output"]) for pair in demos)
        if survives and competitor(query["input"]) != _coerce_grid(query["output"]):
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons
