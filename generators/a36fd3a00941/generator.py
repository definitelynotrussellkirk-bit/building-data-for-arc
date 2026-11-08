"""Semantic generator for ``a36fd3a00941`` — perimeter gallery.

The pinned rule extracts every non-zero 4-connected monochrome component,
crops it to its bounding box, sorts by ``(bbox_perimeter, left, top)``, and
packs the crops left-to-right, top-aligned, with one zero column between them.

Every generated scene is canonical-scale and contains a deliberate teaching
counterexample: the two larger crops have the same occupied-cell count, while the
larger-perimeter crop has the smaller bounding-box area and occurs farther
left in the input. Thus sorting by area or pixel count reverses the last two
crops instead of imitating the perimeter rule.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a36fd3a00941"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d0dcd1dd1256"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains three separated monochrome pieces. "
    "Crop each object to its bounding box, sort the crops by bounding-box "
    "perimeter ascending (ties: original left column, then top row), and "
    "pack them left-to-right, top-aligned, with one zero column between crops."
)

INVARIANTS = [
    "background is 0",
    "exactly three separated 4-connected monochrome components",
    "component colors and bbox perimeters are pairwise distinct",
    "bbox crops are preserved exactly",
    "output crops are top-aligned with exactly one zero-column separator",
]

COUNTER_HYPOTHESES = [
    "sort by bounding-box area instead of perimeter",
    "sort by occupied-cell count instead of perimeter",
    "preserve input scan order",
    "sort by color",
    "sort perimeter descending",
    "replace sparse crops by solid rectangles",
    "bottom-align crops",
    "omit separator columns",
]

PROFILE_DIMS: dict[str, tuple[int, int]] = {
    "canonical_8x12": (8, 12),
    "canonical_9x11": (9, 11),
    "canonical_8x13": (8, 13),
    "canonical_9x12": (9, 12),
}
PROFILE_NAMES = tuple(PROFILE_DIMS)
_PROFILE_BY_DIMS = {dims: name for name, dims in PROFILE_DIMS.items()}
_CANONICAL_DIMS = frozenset(_PROFILE_BY_DIMS)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic canonical schedule",
        "valid": "canonical_8x12|canonical_9x11|canonical_8x13|canonical_9x12",
    },
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
SCHEDULE_PROFILES = PROFILE_NAMES


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in PROFILE_NAMES:
        raise ValueError(
            f"override 'scene_profile'={profile!r} not in {PROFILE_NAMES}"
        )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive sample indexes visit all canonical dimensions."""
    del seed, difficulty
    return PROFILE_NAMES[int(sample_index) % len(PROFILE_NAMES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    top = min(r for r, _ in values)
    left = min(c for _, c in values)
    return tuple(sorted((r - top, c - left) for r, c in values))


def _reflect(
    shape: tuple[tuple[int, int], ...], *, flip_r: bool, flip_c: bool
) -> tuple[tuple[int, int], ...]:
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    return _normalize(
        (
            (
                height - 1 - r if flip_r else r,
                width - 1 - c if flip_c else c,
            )
            for r, c in shape
        )
    )


def _middle_shape(rng) -> tuple[tuple[int, int], ...]:
    """Connected five-cell shape spanning a 3x2 bounding box."""
    cells = {(0, 0), (0, 1), (1, 0), (1, 1), (2, rng.randrange(2))}
    return _reflect(
        _normalize(cells),
        flip_r=bool(rng.randrange(2)),
        flip_c=bool(rng.randrange(2)),
    )


def _large_shape() -> tuple[tuple[int, int], ...]:
    """Five-cell horizontal line spanning a 1x5 bounding box."""
    return tuple((0, c) for c in range(5))

def _place(
    grid: list[list[int]],
    shape: Iterable[tuple[int, int]],
    origin: tuple[int, int],
    color: int,
) -> None:
    r0, c0 = origin
    for dr, dc in shape:
        r, c = r0 + dr, c0 + dc
        if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
            raise AssertionError("shape escaped its canonical profile")
        if grid[r][c] != 0:
            raise AssertionError("shape placement overlap")
        grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_overrides(overrides)
    scheduled = schedule_profile(int(seed), int(sample_index), band)
    effective = dict(overrides)
    if effective.get("scene_profile") is None:
        effective["scene_profile"] = scheduled

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", PROFILE_NAMES)
    h, w = PROFILE_DIMS[profile]
    rng = ctx.draw_rng("layout")

    # Output identities are small, middle, large.  Colors deliberately avoid
    # agreeing with that order, while positions put the large object first in
    # row-major input order and left of the middle object for area/count ties.
    lo, mid, hi = sorted(rng.sample(range(1, 10), 3))
    small_color, middle_color, large_color = hi, lo, mid

    small = ((0, 0), (0, 1), (1, 0), (1, 1))       # 2x2, p=8, 4 cells
    middle = _middle_shape(ctx.draw_rng(f"middle_shape_{band}"))  # 3x2, p=10, 5 cells
    large = _large_shape()                                      # 1x5, p=12, 5 cells

    # Difficulty changes nuisance layout only; the semantic counterexample is
    # equally explicit in every band.  These three layouts are guaranteed to
    # differ for the same seed/index instead of relying on probabilistic draws.
    top, large_left, small_left = {
        "easy": (0, 0, 0),
        "medium": (1, 0, 1),
        "hard": (0, 1, 1),
    }[band]
    middle_left = w - 2

    grid = full_grid(h, w, 0)
    _place(grid, large, (top, large_left), large_color)
    _place(grid, small, (h - 2, small_left), small_color)
    _place(grid, middle, (h - 3, middle_left), middle_color)

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["scene_profile"] != profile:
        raise ValueError(
            f"internal axis mismatch: requested {profile!r}, "
            f"observed {observed['scene_profile']!r}"
        )
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and Python rule mirror (Racket remains authority)
# ---------------------------------------------------------------------------


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for r, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError:
                return None, [f"row {r} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {r} is not a sequence"]
        if not values:
            return None, ["grid rows must be nonempty"]
        if width is None:
            width = len(values)
        elif len(values) != width:
            return None, ["ragged grid"]
        for c, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [f"invalid ARC color at ({r},{c}): {value!r}"]
        rows.append(values)
    return rows, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            top = min(r for r, _ in cells)
            bottom = max(r for r, _ in cells)
            left = min(c for _, c in cells)
            right = max(c for _, c in cells)
            crop = [values[left : right + 1] for values in grid[top : bottom + 1]]
            box_h = bottom - top + 1
            box_w = right - left + 1
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (top, left, bottom, right),
                    "height": box_h,
                    "width": box_w,
                    "bbox_area": box_h * box_w,
                    "bbox_perimeter": 2 * (box_h + box_w),
                    "size": len(cells),
                    "crop": crop,
                }
            )
    result.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    return result


def _authority_order(pieces: list[dict[str, Any]]) -> list[int]:
    return sorted(
        range(len(pieces)),
        key=lambda i: (
            pieces[i]["bbox_perimeter"],
            pieces[i]["bbox"][1],
            pieces[i]["bbox"][0],
        ),
    )


def _pack_pieces(
    pieces: list[dict[str, Any]],
    order: list[int],
    *,
    gap: int = 1,
    alignment: str = "top",
    solid_bbox: bool = False,
) -> list[list[int]]:
    selected = [pieces[i] for i in order]
    if not selected:
        return [[0]]
    out_h = max(obj["height"] for obj in selected)
    out_w = sum(obj["width"] for obj in selected) + gap * (len(selected) - 1)
    output = full_grid(out_h, out_w, 0)
    left = 0
    for obj in selected:
        if alignment == "top":
            top = 0
        elif alignment == "bottom":
            top = out_h - obj["height"]
        else:
            raise ValueError(f"unknown alignment: {alignment}")
        if solid_bbox:
            for r in range(obj["height"]):
                for c in range(obj["width"]):
                    output[top + r][left + c] = obj["color"]
        else:
            for r, row in enumerate(obj["crop"]):
                for c, value in enumerate(row):
                    output[top + r][left + c] = value
        left += obj["width"] + gap
    return output


def _valid_pieces(grid: Any) -> list[dict[str, Any]]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    pieces = _components(values)
    if not pieces:
        raise ValueError("grid contains no non-zero components")
    return pieces


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for tests and rival scoring; canonical Racket is authority."""
    pieces = _valid_pieces(grid)
    return _pack_pieces(pieces, _authority_order(pieces))


def semantic_observables(grid: Any) -> dict[str, Any]:
    values, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if errors or values is None:
        return result
    pieces = _components(values)
    result.update(
        {
            "grid": values,
            "height": len(values),
            "width": len(values[0]),
            "palette": tuple(sorted({value for row in values for value in row})),
            "pieces": pieces,
            "n_pieces": len(pieces),
            "scene_profile": _PROFILE_BY_DIMS.get((len(values), len(values[0]))),
            "perimeters": tuple(sorted(obj["bbox_perimeter"] for obj in pieces)),
            "sizes": tuple(sorted(obj["size"] for obj in pieces)),
            "areas": tuple(sorted(obj["bbox_area"] for obj in pieces)),
        }
    )
    return result


def _clearance_error(pieces: list[dict[str, Any]]) -> str | None:
    owner = {
        cell: index
        for index, obj in enumerate(pieces)
        for cell in obj["cells"]
    }
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    return "different components touch, including diagonally"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and the canonical-scale teaching grammar."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors

    height, width = facts["height"], facts["width"]
    if not (8 <= height <= 9 and 11 <= width <= 13):
        errors.append(
            f"supported teaching envelope is h=8..9, w=11..13; found {height}x{width}"
        )
    if 0 not in facts["palette"]:
        errors.append("background color 0 must be visible")

    pieces = facts["pieces"]
    if len(pieces) != 3:
        errors.append(f"expected exactly three components, found {len(pieces)}")
        return errors
    colors = [obj["color"] for obj in pieces]
    if len(set(colors)) != 3:
        errors.append("component colors must be pairwise distinct")
    perimeters = [obj["bbox_perimeter"] for obj in pieces]
    if len(set(perimeters)) != 3:
        errors.append("component bbox perimeters must be pairwise distinct")
    for obj in pieces:
        if obj["height"] > 3 or obj["width"] > 5:
            errors.append(
                "component crop exceeds supported 3x5 teaching morphology: "
                f"{obj['height']}x{obj['width']}"
            )
        if obj["size"] > 5:
            errors.append(f"component has {obj['size']} cells; expected at most 5")
    clearance = _clearance_error(pieces)
    if clearance:
        errors.append(clearance)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked profile check used by the empirical-manifold gate."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if (facts["height"], facts["width"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions are outside the four canonical profiles")
    if len(facts["palette"]) != 4:
        reasons.append("canonical inputs use background plus three object colors")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    reasons = self_check(grid)
    if reasons:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(reasons))
    facts = semantic_observables(grid)
    profile = facts.get("scene_profile")
    if profile is None:
        raise ValueError(
            f"unrecognized scene dimensions: {facts['height']}x{facts['width']}"
        )
    return {"scene_profile": profile}


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["height"],
        facts["width"],
        facts["scene_profile"],
        tuple(
            (
                obj["bbox_perimeter"],
                obj["bbox_area"],
                obj["size"],
                obj["height"],
                obj["width"],
            )
            for obj in facts["pieces"]
        ),
    )


# ---------------------------------------------------------------------------
# Named rivals, witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------


def _rival_bbox_area(grid):
    pieces = _valid_pieces(grid)
    order = sorted(
        range(len(pieces)),
        key=lambda i: (
            pieces[i]["bbox_area"],
            pieces[i]["bbox"][1],
            pieces[i]["bbox"][0],
        ),
    )
    return _pack_pieces(pieces, order)


def _rival_pixel_count(grid):
    pieces = _valid_pieces(grid)
    order = sorted(
        range(len(pieces)),
        key=lambda i: (
            pieces[i]["size"],
            pieces[i]["bbox_area"],
            pieces[i]["bbox"][1],
            pieces[i]["bbox"][0],
        ),
    )
    return _pack_pieces(pieces, order)


def _rival_input_scan_order(grid):
    pieces = _valid_pieces(grid)
    return _pack_pieces(pieces, list(range(len(pieces))))


def _rival_color_order(grid):
    pieces = _valid_pieces(grid)
    order = sorted(
        range(len(pieces)),
        key=lambda i: (
            pieces[i]["color"],
            pieces[i]["bbox"][1],
            pieces[i]["bbox"][0],
        ),
    )
    return _pack_pieces(pieces, order)


def _rival_descending_perimeter(grid):
    pieces = _valid_pieces(grid)
    order = sorted(
        range(len(pieces)),
        key=lambda i: (
            -pieces[i]["bbox_perimeter"],
            pieces[i]["bbox"][1],
            pieces[i]["bbox"][0],
        ),
    )
    return _pack_pieces(pieces, order)


def _rival_solid_bbox(grid):
    pieces = _valid_pieces(grid)
    return _pack_pieces(pieces, _authority_order(pieces), solid_bbox=True)


def _rival_bottom_align(grid):
    pieces = _valid_pieces(grid)
    return _pack_pieces(pieces, _authority_order(pieces), alignment="bottom")


def _rival_no_gap(grid):
    pieces = _valid_pieces(grid)
    return _pack_pieces(pieces, _authority_order(pieces), gap=0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "bbox_area_ascending": _rival_bbox_area,
    "occupied_count_ascending": _rival_pixel_count,
    "input_scan_order": _rival_input_scan_order,
    "color_ascending": _rival_color_order,
    "perimeter_descending": _rival_descending_perimeter,
    "solid_bbox_crops": _rival_solid_bbox,
    "bottom_align": _rival_bottom_align,
    "omit_gap_columns": _rival_no_gap,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "bbox_area_ascending": _rival_bbox_area,
    "occupied_count_ascending": _rival_pixel_count,
}


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _rival_disagrees(name: str, grid: Any) -> bool:
    return not _grids_equal(rule_mirror(grid), SEMANTIC_RIVALS[name](grid))


def _profile_is(name: str, grid: Any) -> bool:
    return semantic_observables(grid).get("scene_profile") == name


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    **{
        f"profile_{name}": (lambda grid, expected=name: _profile_is(expected, grid))
        for name in PROFILE_NAMES
    },
    "perimeter_not_bbox_area": lambda g: _rival_disagrees("bbox_area_ascending", g),
    "perimeter_not_occupied_count": lambda g: _rival_disagrees("occupied_count_ascending", g),
    "input_scan_not_output_order": lambda g: _rival_disagrees("input_scan_order", g),
    "color_not_output_order": lambda g: _rival_disagrees("color_ascending", g),
    "ascending_perimeter_visible": lambda g: _rival_disagrees("perimeter_descending", g),
    "crop_texture_preserved": lambda g: _rival_disagrees("solid_bbox_crops", g),
    "top_alignment_visible": lambda g: _rival_disagrees("bottom_align", g),
    "one_column_gaps_visible": lambda g: _rival_disagrees("omit_gap_columns", g),
}
BRANCH_WITNESSES = {f"profile_{name}" for name in PROFILE_NAMES}
WITNESS_RIVALS = {
    "perimeter_not_bbox_area": ["bbox_area_ascending"],
    "perimeter_not_occupied_count": ["occupied_count_ascending"],
    "input_scan_not_output_order": ["input_scan_order"],
    "color_not_output_order": ["color_ascending"],
    "ascending_perimeter_visible": ["perimeter_descending"],
    "crop_texture_preserved": ["solid_bbox_crops"],
    "top_alignment_visible": ["bottom_align"],
    "one_column_gaps_visible": ["omit_gap_columns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a declared plausible wrong rule survives its demos."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} outside rule grammar: {exc}")
            continue
        if not _grids_equal(expected, pair.get("output")):
            reasons.append(f"demo {index} output disagrees with pinned rule")

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query outside rule grammar: {exc}")
        return reasons

    if "output" in query and not _grids_equal(query_answer, query["output"]):
        reasons.append("query output disagrees with pinned rule")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                _grids_equal(competitor(pair["input"]), pair.get("output"))
                for pair in demos
            )
            if survives and not _grids_equal(competitor(query["input"]), query_answer):
                reasons.append(
                    f"competitor '{name}' fits every demo but changes the query answer"
                )
        except (KeyError, ValueError) as exc:
            reasons.append(f"competitor '{name}' raised: {exc}")
    return reasons
