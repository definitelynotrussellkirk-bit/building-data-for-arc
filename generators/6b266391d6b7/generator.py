"""Generate lessons for stamping a top-left 2x2 motif at 9-markers.

The top-left 2x2 block is the source motif.  Every color-9 cell outside that
block is an anchor: erase the marker and copy each non-background motif cell
with the marker as the copied block's top-left corner.

Default draws cycle through the five joint canonical profiles (dimensions,
marker count, motif mask, and broad palette relation) while varying exact
colors and marker positions.  Exact overrides may broaden each observable axis
without changing the rule.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b266391d6b7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6775ecfad4a4"

SUMMARY = (
    "Use the top-left 2x2 as a sparse motif, erase every 9-marker, and stamp "
    "the motif's nonzero cells at each marker anchor. Default draws preserve "
    "the five demonstrated joint profiles while varying colors and positions."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "the returned input is a rectangular 7..10 by 8..12 ARC grid",
    "the top-left 2x2 motif has one demonstrated sparse mask and at least two colors",
    "all nonzero cells outside the motif are 1..5 non-overlapping color-9 anchors",
    "every anchor has an otherwise blank in-bounds 2x2 destination footprint",
    "the five default schedule slots reproduce every canonical joint profile",
]

MOTIF_SHAPES = ("lower_l", "main_diag", "upper_l")
PALETTE_KINDS = ("low", "high", "mixed")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile schedule",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile schedule",
        "valid": "8..12",
    },
    "n_markers": {
        "type": "int",
        "default": "canonical 2/3-marker schedule",
        "valid": "1..5",
    },
    "motif_shape": {
        "type": "str",
        "default": "five-profile schedule",
        "valid": "|".join(MOTIF_SHAPES),
    },
    "palette_kind": {
        "type": "str",
        "default": "five-profile schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_MASKS = {
    "lower_l": ((0, 0), (1, 0), (1, 1)),
    "main_diag": ((0, 0), (1, 1)),
    "upper_l": ((0, 0), (0, 1), (1, 0)),
}
_MASK_TO_SHAPE = {frozenset(mask): name for name, mask in _MASKS.items()}

# Exact joint profiles extracted from all four train inputs plus the held-out
# test input.  The repeated test profile is represented once.
_CANONICAL_PROFILES = (
    {
        "name": "train_0",
        "grid_h": 7,
        "grid_w": 8,
        "n_markers": 2,
        "motif_shape": "lower_l",
        "palette_kind": "low",
        "color_relation": "all_distinct",
    },
    {
        "name": "train_1",
        "grid_h": 8,
        "grid_w": 9,
        "n_markers": 3,
        "motif_shape": "main_diag",
        "palette_kind": "high",
        "color_relation": "all_distinct",
    },
    {
        "name": "train_2",
        "grid_h": 7,
        "grid_w": 10,
        "n_markers": 2,
        "motif_shape": "upper_l",
        "palette_kind": "mixed",
        "color_relation": "repeat",
    },
    {
        "name": "train_3",
        "grid_h": 9,
        "grid_w": 9,
        "n_markers": 3,
        "motif_shape": "lower_l",
        "palette_kind": "mixed",
        "color_relation": "repeat",
    },
    {
        "name": "test_0",
        "grid_h": 8,
        "grid_w": 10,
        "n_markers": 3,
        "motif_shape": "upper_l",
        "palette_kind": "low",
        "color_relation": "repeat",
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _CANONICAL_PROFILES)


def _unknown_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _recorded_default_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Consume a boundary-checked exact override or record a linked default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = int(ctx.overrides[label])
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        return int(ctx._record(label, value, from_override=True))
    return int(ctx._record(label, int(default), from_override=False))


def _recorded_default_choice(
    ctx,
    label: str,
    options: tuple[str, ...],
    default: str,
) -> str:
    """Consume an exact enum override or record a linked schedule value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = str(ctx.overrides[label])
        if value not in options:
            raise ValueError(f"{label} override {value!r} not in {options!r}")
        return str(ctx._record(label, value, from_override=True))
    return str(ctx._record(label, default, from_override=False))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic five-slot canonical profile schedule."""
    del seed
    offset = {"easy": 0, "medium": 1, "hard": 2, None: 1}.get(difficulty, 1)
    return str(_CANONICAL_PROFILES[(int(sample_index) + offset) % 5]["name"])


def _profile(seed: int, sample_index: int, difficulty) -> dict[str, object]:
    name = schedule_profile(seed, sample_index, difficulty)
    return next(profile for profile in _CANONICAL_PROFILES if profile["name"] == name)


def _palette_kind(colors: list[int]) -> str | None:
    if not colors or any(color not in range(1, 9) for color in colors):
        return None
    if all(color <= 4 for color in colors):
        return "low"
    if all(color >= 5 for color in colors):
        return "high"
    return "mixed"


def _motif_relation(colors: list[int]) -> str:
    return "repeat" if len(set(colors)) < len(colors) else "all_distinct"


def _draw_motif_colors(
    *,
    count: int,
    palette_kind: str,
    relation: str,
    rng,
) -> list[int]:
    low = [1, 2, 3, 4]
    high = [5, 6, 7, 8]
    if palette_kind == "low":
        pool = low
        if relation == "repeat" and count >= 3:
            first, second = rng.sample(pool, 2)
            colors = [first, second, first]
        elif relation == "repeat" and count == 2:
            color = rng.choice(pool)
            colors = [color, color]
        else:
            colors = rng.sample(pool, count)
    elif palette_kind == "high":
        pool = high
        if relation == "repeat" and count >= 3:
            first, second = rng.sample(pool, 2)
            colors = [first, second, first]
        elif relation == "repeat" and count == 2:
            color = rng.choice(pool)
            colors = [color, color]
        else:
            colors = rng.sample(pool, count)
    else:
        # A two-cell mixed motif must be distinct; with three cells the third
        # may repeat either band while the scene remains observably mixed.
        first = rng.choice(low)
        second = rng.choice(high)
        colors = [first, second]
        if count >= 3:
            colors.append(rng.choice(colors) if relation == "repeat" else rng.choice(
                [value for value in low + high if value not in colors]
            ))
    rng.shuffle(colors)
    return colors


def _candidate_markers(h: int, w: int, rng) -> list[tuple[int, int]]:
    candidates = [(r, c) for r in range(2, h - 1) for c in range(0, w - 1)]
    rng.shuffle(candidates)
    chosen: list[tuple[int, int]] = []
    for r, c in candidates:
        if all(abs(r - pr) >= 2 or abs(c - pc) >= 2 for pr, pc in chosen):
            chosen.append((r, c))
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _unknown_overrides(overrides)
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _profile(seed, sample_index, difficulty)
    h = _recorded_default_int(ctx, "grid_h", 7, 10, int(profile["grid_h"]))
    w = _recorded_default_int(ctx, "grid_w", 8, 12, int(profile["grid_w"]))
    n_markers = _recorded_default_int(
        ctx, "n_markers", 1, 5, int(profile["n_markers"])
    )
    motif_shape = _recorded_default_choice(
        ctx, "motif_shape", MOTIF_SHAPES, str(profile["motif_shape"])
    )
    palette_kind = _recorded_default_choice(
        ctx, "palette_kind", PALETTE_KINDS, str(profile["palette_kind"])
    )

    mask = _MASKS[motif_shape]
    relation = str(profile["color_relation"])
    if len(mask) == 2:
        relation = "all_distinct"
    colors = _draw_motif_colors(
        count=len(mask),
        palette_kind=palette_kind,
        relation=relation,
        rng=ctx.draw_rng("motif_colors"),
    )

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(mask, colors):
        grid[r][c] = color

    candidates = _candidate_markers(h, w, ctx.draw_rng("marker_layout"))
    if len(candidates) < n_markers:
        raise AssertionError(
            f"only {len(candidates)} non-overlapping marker sites for {n_markers}"
        )
    for r, c in candidates[:n_markers]:
        grid[r][c] = 9

    issues = self_check(grid, difficulty=band)
    if issues:
        raise AssertionError("generated invalid stamp lesson: " + "; ".join(issues))
    observed = observe_overrides(grid)
    for label, requested in ctx.recorded_draws().items():
        if label in AXES and observed.get(label) != requested:
            raise AssertionError(
                f"axis {label!r}: requested/drawn {requested!r}, "
                f"observed {observed.get(label)!r}"
            )
    return grid


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty"]
    width = len(grid[0])
    out: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        out.append(converted)
    return (None, errors) if errors else (out, [])


def _analyze(grid) -> dict[str, Any]:
    original, errors = _coerce_grid(grid)
    if errors or original is None:
        return {"errors": errors}
    h = len(original)
    w = len(original[0])
    if not 7 <= h <= 10:
        errors.append(f"grid height {h} outside 7..10")
    if not 8 <= w <= 12:
        errors.append(f"grid width {w} outside 8..12")

    motif_cells = [
        (r, c, original[r][c])
        for r in range(2)
        for c in range(2)
        if original[r][c] != 0
    ]
    motif_mask = frozenset((r, c) for r, c, _color in motif_cells)
    motif_shape = _MASK_TO_SHAPE.get(motif_mask)
    if motif_shape is None:
        errors.append(
            "top-left motif mask must be one of lower_l, main_diag, or upper_l"
        )
    motif_colors = [color for _r, _c, color in motif_cells]
    if any(color == 9 for color in motif_colors):
        errors.append("the source motif may not contain marker color 9")
    if len(set(motif_colors)) < 2:
        errors.append("the source motif must expose at least two distinct colors")
    palette_kind = _palette_kind(motif_colors)
    if palette_kind is None:
        errors.append("motif colors must lie in 1..8")

    markers: list[tuple[int, int]] = []
    foreign: list[tuple[int, int, int]] = []
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if r < 2 and c < 2:
                continue
            if value == 9:
                markers.append((r, c))
            elif value != 0:
                foreign.append((r, c, value))
    if foreign:
        errors.append(f"outside the motif only 9-markers are allowed; found {foreign[:3]}")
    if not 1 <= len(markers) <= 5:
        errors.append(f"expected 1..5 marker anchors, got {len(markers)}")

    for r, c in markers:
        if r + 1 >= h or c + 1 >= w:
            errors.append(f"marker {(r, c)} has no in-bounds 2x2 destination")
            continue
        for dr in range(2):
            for dc in range(2):
                rr, cc = r + dr, c + dc
                if (rr, cc) != (r, c) and original[rr][cc] != 0:
                    errors.append(
                        f"marker {(r, c)} destination footprint is not blank at {(rr, cc)}"
                    )
    for index, (r, c) in enumerate(markers):
        for pr, pc in markers[:index]:
            if abs(r - pr) < 2 and abs(c - pc) < 2:
                errors.append(f"marker footprints overlap: {(pr, pc)} and {(r, c)}")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n_markers": len(markers),
        "markers": markers,
        "motif_shape": motif_shape,
        "motif_colors": motif_colors,
        "palette_kind": palette_kind,
        "color_relation": _motif_relation(motif_colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {name: analysis[name] for name in AXES}


def strict_canonical_like(grid) -> list[str]:
    """Require one complete demonstrated joint profile, not loose marginals."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    signature = {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_markers": analysis["n_markers"],
        "motif_shape": analysis["motif_shape"],
        "palette_kind": analysis["palette_kind"],
        "color_relation": analysis["color_relation"],
    }
    for profile in _CANONICAL_PROFILES:
        expected = {key: profile[key] for key in signature}
        if signature == expected:
            return []
    return [f"joint signature is outside the five canonical profiles: {signature}"]


def canonical_profile_index(grid) -> int | None:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    signature = {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_markers": analysis["n_markers"],
        "motif_shape": analysis["motif_shape"],
        "palette_kind": analysis["palette_kind"],
        "color_relation": analysis["color_relation"],
    }
    for index, profile in enumerate(_CANONICAL_PROFILES):
        if signature == {key: profile[key] for key in signature}:
            return index
    return None


def _truth(grid) -> list[list[int]]:
    """Python mirror used only for tests and named rival discrimination."""
    out = deepcopy(grid)
    motif = [[grid[r][c] for c in range(2)] for r in range(2)]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9 and not (r < 2 and c < 2)
    ]
    for r, c in markers:
        out[r][c] = 0
    for r, c in markers:
        for dr in range(2):
            for dc in range(2):
                value = motif[dr][dc]
                if value != 0 and r + dr < len(out) and c + dc < len(out[0]):
                    out[r + dr][c + dc] = value
    return out


def _rival_erase_only(grid):
    out = deepcopy(grid)
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 9 and not (r < 2 and c < 2):
                out[r][c] = 0
    return out


def _rival_first_marker_only(grid):
    out = _rival_erase_only(grid)
    motif = [[grid[r][c] for c in range(2)] for r in range(2)]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9 and not (r < 2 and c < 2)
    ]
    if markers:
        r, c = markers[0]
        for dr in range(2):
            for dc in range(2):
                if motif[dr][dc] != 0:
                    out[r + dr][c + dc] = motif[dr][dc]
    return out


def _rival_solid_bbox(grid):
    out = _rival_erase_only(grid)
    color = grid[0][0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9 and not (r < 2 and c < 2):
                for dr in range(2):
                    for dc in range(2):
                        out[r + dr][c + dc] = color
    return out


def _rival_first_color_only(grid):
    out = _rival_erase_only(grid)
    color = grid[0][0]
    mask = [(r, c) for r in range(2) for c in range(2) if grid[r][c] != 0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9 and not (r < 2 and c < 2):
                for dr, dc in mask:
                    out[r + dr][c + dc] = color
    return out


def _rival_fixed_lower_l(grid):
    out = _rival_erase_only(grid)
    source = [grid[r][c] for r in range(2) for c in range(2) if grid[r][c] != 0]
    colors = [source[min(index, len(source) - 1)] for index in range(3)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 9 and not (r < 2 and c < 2):
                for (dr, dc), color in zip(_MASKS["lower_l"], colors):
                    out[r + dr][c + dc] = color
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "erase_markers_only": _rival_erase_only,
    "stamp_first_marker_only": _rival_first_marker_only,
    "solid_2x2_stamp": _rival_solid_bbox,
    "monochrome_stamp": _rival_first_color_only,
    "fixed_lower_l_mask": _rival_fixed_lower_l,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness(name: str):
    return lambda grid: _analyze(grid).get("motif_shape") == name


SEMANTIC_WITNESSES = {
    "lower_l_mask": _witness("lower_l"),
    "main_diagonal_mask": _witness("main_diag"),
    "upper_l_mask": _witness("upper_l"),
    "multiple_markers": lambda grid: _analyze(grid).get("n_markers", 0) >= 2,
    "sparse_motif_hole": lambda grid: any(
        grid[r][c] == 0 for r in range(2) for c in range(2)
    ),
    "multicolor_motif": lambda grid: len(set(_analyze(grid).get("motif_colors", []))) >= 2,
    "mixed_palette": lambda grid: _analyze(grid).get("palette_kind") == "mixed",
}
WITNESS_RIVALS = {
    "main_diagonal_mask": ["fixed_lower_l_mask"],
    "upper_l_mask": ["fixed_lower_l_mask"],
    "multiple_markers": ["stamp_first_marker_only"],
    "sparse_motif_hole": ["solid_2x2_stamp"],
    "multicolor_motif": ["monochrome_stamp"],
    "mixed_palette": ["monochrome_stamp"],
    "lower_l_mask": ["erase_markers_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever any named shortcut survives every demo."""
    del query
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = True
        for pair in demos:
            if competitor(pair["input"]) != pair["output"]:
                survives = False
                break
        if survives:
            reasons.append(f"named shortcut survives all demonstrations: {name}")
    return reasons
