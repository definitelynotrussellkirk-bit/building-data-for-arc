"""Semantic generator for ARC task ``29f732637b01`` (original ``f25fbde4``).

The authoritative rule crops the input to the tight bounding box of every
nonzero cell and then replaces each cropped cell by a 2x2 block.  Ordinary
lessons alternate between exact canonical morphology (up to translation,
color renaming, and D4 symmetry) and generalized multicolor, disconnected
content.  The alternation ensures any three consecutive demonstrations refute
canonical-fitting monochrome shortcuts while every scene still makes both the
crop and the factor-two scale visible.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "29f732637b01"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "12e3ebc2bb96"
MIN_STRICT_FRAC = 0.40
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A 7..16 by 7..16 zero-background canvas contains sparse nonzero content "
    "strictly inside the border. Its tight bounding box is 2..5 cells per "
    "side and contains at least one internal background cell. The output is "
    "the tight crop of all nonzero content, with every crop cell expanded to "
    "a 2x2 block; zero cells and every foreground color are preserved."
)

INVARIANTS = [
    "background is 0 and forms at least a one-cell margin around all content",
    "the nonzero bounding box is 2..5 cells high and wide",
    "the bounding box contains at least one zero, so the crop is not a solid rectangle",
    "ordinary generalized draws contain disconnected multicolor content",
    "the correct output has exactly twice the crop height and width",
]

COUNTER_HYPOTHESES = [
    "return the full input unchanged",
    "upscale the whole canvas without cropping",
    "crop without upscaling",
    "replace the crop by a solid bounding box",
    "crop and upscale only the largest connected component",
    "collapse all foreground colors to one color (or always to canonical color 4)",
    "memorize the canonical 9x9 size, fixed color, or one canonical bitmap",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9 on canonical-profile draws; rng 7..16 otherwise",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "9 on canonical-profile draws; rng 7..16 otherwise",
        "valid": "7..16",
    },
    "shape_h": {
        "type": "int",
        "default": "canonical profile height or rng 2..5",
        "valid": "2..5",
    },
    "shape_w": {
        "type": "int",
        "default": "canonical profile width or rng 2..5",
        "valid": "2..5",
    },
    "fg_palette_size": {
        "type": "int",
        "default": "1 on canonical-profile draws; 2 otherwise",
        "valid": "1..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
SCHEDULE_PROFILES = ("canonical_profile", "generalized_multicolor")

# Exact normalized canonical binary crops, in train-then-test order.
_CANONICAL_MASKS = (
    ((0, 1, 0), (1, 1, 0), (0, 0, 1)),
    ((0, 1, 1, 0), (1, 1, 1, 1), (0, 1, 1, 0)),
    ((0, 1, 0), (1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((0, 1, 0, 1, 0), (1, 0, 1, 0, 1), (0, 1, 0, 1, 0)),
)


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    bounds = {
        "grid_h": (7, 16),
        "grid_w": (7, 16),
        "shape_h": (2, 5),
        "shape_w": (2, 5),
        "fg_palette_size": (1, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Any three consecutive sample indexes contain a multicolor lesson."""
    del seed, difficulty
    return "canonical_profile" if sample_index % 2 else "generalized_multicolor"


def _rot90(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(mask[len(mask) - 1 - r][c] for r in range(len(mask)))
                 for c in range(len(mask[0])))


def _flip_lr(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in mask)


def _d4_variants(mask: tuple[tuple[int, ...], ...]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    out: list[tuple[tuple[int, ...], ...]] = []
    cur = mask
    for _ in range(4):
        for candidate in (cur, _flip_lr(cur)):
            if candidate not in out:
                out.append(candidate)
        cur = _rot90(cur)
    return tuple(out)


_CANONICAL_VARIANTS = frozenset(
    variant for mask in _CANONICAL_MASKS for variant in _d4_variants(mask)
)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _content_cells(grid) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    if not cells:
        return None
    return (
        min(r for r, _ in cells),
        max(r for r, _ in cells),
        min(c for _, c in cells),
        max(c for _, c in cells),
    )


def _crop(grid):
    cells = _content_cells(grid)
    box = _bbox(cells)
    if box is None:
        return []
    r0, r1, c0, c1 = box
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _upscale(grid, factor: int = 2):
    return [
        [value for value in row for _ in range(factor)]
        for row in grid
        for _ in range(factor)
    ]


def _authoritative_python(grid):
    return _upscale(_crop(grid), 2)


def _components(grid) -> list[list[tuple[int, int]]]:
    remaining = set(_content_cells(grid))
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        comp = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    comp.append(nxt)
        components.append(comp)
    return components


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    h, w = len(grid), len(grid[0])
    cells = _content_cells(grid)
    box = _bbox(cells)
    if box is None:
        result.update({"height": h, "width": w, "bbox": None})
        return result
    r0, r1, c0, c1 = box
    crop = [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]
    fg = sorted({value for row in grid for value in row if value != 0})
    mask = tuple(tuple(int(value != 0) for value in row) for row in crop)
    result.update(
        {
            "height": h,
            "width": w,
            "bbox": box,
            "shape_h": r1 - r0 + 1,
            "shape_w": c1 - c0 + 1,
            "fg_palette": fg,
            "fg_palette_size": len(fg),
            "nonzero_count": len(cells),
            "internal_zero_count": sum(value == 0 for row in crop for value in row),
            "component_count": len(_components(grid)),
            "mask": mask,
            "strict_profile": (
                h == 9
                and w == 9
                and len(fg) == 1
                and mask in _CANONICAL_VARIANTS
            ),
        }
    )
    return result


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts.get("bbox") is None:
        return ("invalid", tuple(facts.get("errors", [])))
    return (
        facts["height"],
        facts["width"],
        facts["shape_h"],
        facts["shape_w"],
        facts["fg_palette_size"],
        facts["nonzero_count"],
        facts["internal_zero_count"],
        facts["component_count"],
        facts["mask"],
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated envelope while accepting all canonicals."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    h, w = facts["height"], facts["width"]
    if not 7 <= h <= 16 or not 7 <= w <= 16:
        errors.append(f"canvas must be within 7..16, found {h}x{w}")
    if facts.get("bbox") is None:
        errors.append("grid has no nonzero content")
        return errors
    r0, r1, c0, c1 = facts["bbox"]
    if r0 < 1 or c0 < 1 or r1 > h - 2 or c1 > w - 2:
        errors.append("content must have at least one zero-background cell on every side")
    sh, sw = facts["shape_h"], facts["shape_w"]
    if not 2 <= sh <= 5 or not 2 <= sw <= 5:
        errors.append(f"content bbox must be 2..5 per side, found {sh}x{sw}")
    if facts["nonzero_count"] < 2:
        errors.append("content must contain at least two nonzero cells")
    if not 1 <= facts["fg_palette_size"] <= 3:
        errors.append(
            f"foreground palette must contain 1..3 colors, found {facts['fg_palette_size']}"
        )
    if facts["internal_zero_count"] == 0:
        errors.append("content bbox is solid; internal background needed to expose crop geometry")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact empirical canonical morphology, modulo lawful nuisance symmetries."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["height"] != 9 or facts["width"] != 9:
        reasons.append("canonical canvas is exactly 9x9")
    if facts["fg_palette_size"] != 1:
        reasons.append("canonical inputs are monochrome foreground")
    if facts["mask"] not in _CANONICAL_VARIANTS:
        reasons.append("normalized bitmap is not a canonical train/test morphology up to D4")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts.get("bbox") is None:
        raise ValueError("cannot observe override axes from an invalid/empty grid")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "shape_h": facts["shape_h"],
        "shape_w": facts["shape_w"],
        "fg_palette_size": facts["fg_palette_size"],
    }


def _random_general_mask(sh: int, sw: int, rng, *, minimum_cells: int,
                         require_disconnected: bool) -> tuple[tuple[int, ...], ...]:
    all_cells = [(r, c) for r in range(sh) for c in range(sw)]
    anchors = {(0, 0), (sh - 1, sw - 1)}
    for _ in range(256):
        cells = set(anchors)
        target = rng.randint(max(minimum_cells, 2), max(minimum_cells, sh * sw - 1))
        candidates = [cell for cell in all_cells if cell not in cells]
        rng.shuffle(candidates)
        cells.update(candidates[: max(0, target - len(cells))])
        if len(cells) >= sh * sw:
            cells.remove(rng.choice(sorted(cells - anchors)))
        mask = tuple(
            tuple(int((r, c) in cells) for c in range(sw))
            for r in range(sh)
        )
        if require_disconnected:
            dummy = [list(row) for row in mask]
            if len(_components(dummy)) < 2:
                continue
        return mask
    # Deterministic sparse fallback. It is disconnected whenever two colors are
    # requested on a 2x2 bbox; override-only 3-color 2x2 uses a lawful L-shape.
    cells = set(anchors)
    for cell in all_cells:
        if len(cells) >= minimum_cells:
            break
        cells.add(cell)
    if len(cells) == sh * sw:
        removable = [cell for cell in sorted(cells) if cell not in anchors]
        if removable:
            cells.remove(removable[-1])
    return tuple(tuple(int((r, c) in cells) for c in range(sw)) for r in range(sh))


def _palette_for_band(palette: tuple[int, ...], band: str) -> tuple[int, ...]:
    """Difficulty is a lawful color-renaming nuisance, made observably live."""
    offset = {"easy": 0, "medium": 3, "hard": 6}[band]
    return tuple(((color - 1 + offset) % 9) + 1 for color in palette)


def _paint_mask(mask, palette: tuple[int, ...], rng):
    occupied = [(r, c) for r, row in enumerate(mask) for c, bit in enumerate(row) if bit]
    if len(occupied) < len(palette):
        raise ValueError("mask has fewer occupied cells than foreground colors")
    rng.shuffle(occupied)
    colors: dict[tuple[int, int], int] = {}
    for cell, color in zip(occupied, palette):
        colors[cell] = color
    for cell in occupied[len(palette):]:
        colors[cell] = rng.choice(palette)
    return tuple(
        tuple(colors.get((r, c), 0) for c in range(len(mask[0])))
        for r in range(len(mask))
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # Explicit overrides request the full independent axis envelope. Ordinary
    # odd-index draws use a complete canonical profile; even draws are the
    # guaranteed multicolor counterexample profile.
    canonical_profile = not overrides and schedule_profile(seed, sample_index, band) == "canonical_profile"
    if canonical_profile:
        profile_rng = ctx.draw_rng("canonical_profile")
        base = profile_rng.choice(_CANONICAL_MASKS)
        mask = profile_rng.choice(_d4_variants(base))
        sh, sw = len(mask), len(mask[0])
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 9, 9)
        ctx.draw_int("shape_h", sh, sh)
        ctx.draw_int("shape_w", sw, sw)
        n_palette = ctx.draw_int("fg_palette_size", 1, 1)
    else:
        h = ctx.draw_int("grid_h", 7, 16)
        w = ctx.draw_int("grid_w", 7, 16)
        sh = ctx.draw_int("shape_h", 2, 5)
        sw = ctx.draw_int("shape_w", 2, 5)
        if overrides:
            n_palette = ctx.draw_int("fg_palette_size", 1, 3)
        else:
            n_palette = ctx.draw_int("fg_palette_size", 2, 2)
        mask_rng = ctx.draw_rng("general_mask")
        mask = _random_general_mask(
            sh,
            sw,
            mask_rng,
            minimum_cells=n_palette,
            require_disconnected=not overrides,
        )

    palette = ctx.draw_distinct_colors("palette", n=n_palette, exclude={0})
    palette = _palette_for_band(palette, band)
    paint_rng = ctx.draw_rng("paint")
    painted = _paint_mask(mask, palette, paint_rng)
    position_rng = ctx.draw_rng("position")
    rr = position_rng.randint(1, h - sh - 1)
    cc = position_rng.randint(1, w - sw - 1)
    grid = full_grid(h, w, 0)
    for dr in range(sh):
        for dc in range(sw):
            grid[rr + dr][cc + dc] = painted[dr][dc]

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected}, observed {observed[axis]}"
            )
    return grid


# ---------------------------------------------------------------------------
# Named rivals and lesson-level identifiability
# ---------------------------------------------------------------------------

def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_upscale_full_canvas(grid):
    return _upscale(grid, 2)


def _rival_crop_without_scale(grid):
    return _crop(grid)


def _rival_solid_bbox(grid):
    crop = _crop(grid)
    fg = next((value for row in crop for value in row if value != 0), 1)
    return [[fg for _ in row] for row in _upscale(crop, 2)]


def _rival_monochrome_crop_upscale(grid):
    crop = _crop(grid)
    fg = next((value for row in crop for value in row if value != 0), 1)
    mono = [[fg if value != 0 else 0 for value in row] for row in crop]
    return _upscale(mono, 2)


def _rival_fixed_color4_crop_upscale(grid):
    crop = _crop(grid)
    mono = [[4 if value != 0 else 0 for value in row] for row in crop]
    return _upscale(mono, 2)


def _rival_largest_component_only(grid):
    components = _components(grid)
    if not components:
        return []
    chosen = max(components, key=lambda comp: (len(comp), tuple(sorted(comp))))
    h, w = len(grid), len(grid[0])
    keep = set(chosen)
    reduced = [[grid[r][c] if (r, c) in keep else 0 for c in range(w)] for r in range(h)]
    return _upscale(_crop(reduced), 2)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "identity_full_canvas": _rival_identity,
    "upscale_full_canvas": _rival_upscale_full_canvas,
    "crop_without_scale": _rival_crop_without_scale,
    "solid_bbox": _rival_solid_bbox,
    "monochrome_crop_upscale": _rival_monochrome_crop_upscale,
    "fixed_color4_crop_upscale": _rival_fixed_color4_crop_upscale,
    "largest_component_only": _rival_largest_component_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "monochrome_crop_upscale": _rival_monochrome_crop_upscale,
    "fixed_color4_crop_upscale": _rival_fixed_color4_crop_upscale,
}


def _witness_cropped_canvas(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and facts.get("bbox") is not None and (
        facts["shape_h"] < facts["height"] or facts["shape_w"] < facts["width"]
    )


def _witness_internal_background(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and facts.get("internal_zero_count", 0) > 0


def _witness_disconnected(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and facts.get("component_count", 0) >= 2


def _witness_multicolor(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and facts.get("fg_palette_size", 0) >= 2


def _witness_non_square(grid) -> bool:
    facts = semantic_observables(grid)
    return not facts.get("errors") and facts.get("shape_h") != facts.get("shape_w")


SEMANTIC_WITNESSES = {
    "cropped_canvas": _witness_cropped_canvas,
    "factor_two_visible": _witness_cropped_canvas,
    "interior_background_preserved": _witness_internal_background,
    "disconnected_content_all_kept": _witness_disconnected,
    "multicolor_preserved": _witness_multicolor,
    "non_square_crop": _witness_non_square,
}
WITNESS_RIVALS = {
    "cropped_canvas": ["identity_full_canvas", "upscale_full_canvas"],
    "factor_two_visible": ["crop_without_scale"],
    "interior_background_preserved": ["solid_bbox"],
    "disconnected_content_all_kept": ["largest_component_only"],
    "multicolor_preserved": ["monochrome_crop_upscale", "fixed_color4_crop_upscale"],
}


def _grids_equal(left, right) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named wrong rule fits every demonstration.

    The query is checked only to distinguish a genuinely ambiguous query from
    an answer-equivalent competitor; ordinary three-demo schedules refute every
    declared competitor before the query is considered.
    """
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits_demos:
                continue
            if not _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} fits every demo but disagrees on query")
            else:
                reasons.append(f"competitor {name!r} survives every demo and the query")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
