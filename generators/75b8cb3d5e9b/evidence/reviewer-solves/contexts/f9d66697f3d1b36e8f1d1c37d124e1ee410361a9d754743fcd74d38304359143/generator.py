"""Lawful inputs for ``Learn the Transform and Apply It`` (75b8cb3d5e9b).

Two full color-9 columns split the input into source, transformed source, and
query panels.  The selected Racket authority crops each motif, chooses the
first matching D4 transform in its fixed precedence, and applies that same
transform to the cropped query.

Generated source and query motifs span a 3x3 local frame and have trivial D4
stabilizers.  Consequently every generated demonstration has one matching
transform and every wrong fixed transform changes the query answer.  The
canonical rows are still accepted even where one individual row is ambiguous;
the unchanged authority's precedence remains the label definition there.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "75b8cb3d5e9b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "9c9988768752"

SUMMARY = (
    "Three panels are separated by full color-9 columns. Panel 2 is a uniquely "
    "inferable non-identity D4 transform of panel 1 on generated draws; emit "
    "panel 3 after that same transform."
)

INVARIANTS = [
    "the input has three equal-width panels separated by exactly two full color-9 columns",
    "each cropped motif spans a 3x3 local frame and contains 4..7 non-background cells",
    "panel 2 is a color-preserving D4 transform of panel 1",
    "generated source motifs identify exactly one non-identity transform",
    "generated query motifs have eight distinct D4 orientations",
    "the canonical Racket rule remains the sole output authority",
]

# Canonical transform-code precedence:
#   0 identity; 1/2/3 rotations; 4 flip-LR; 5/6/7 are flip-LR then rotation.
# Names for 5..7 are anti-transpose, flip-UD, and transpose respectively.
TRANSFORMS = ("r1", "r2", "r3", "fh", "atr", "fv", "tr")
TRANSFORM_PRECEDENCE = ("id",) + TRANSFORMS
_NAME_TO_CODE = {name: code for code, name in enumerate(TRANSFORM_PRECEDENCE)}
_CODE_TO_NAME = {code: name for name, code in _NAME_TO_CODE.items()}

AXES = {
    "panel_h": {
        "type": "int",
        "default": "linked balanced 112-slot schedule",
        "valid": "3..5",
        "doc": "Height of every panel; the local motif remains 3x3.",
    },
    "panel_w": {
        "type": "int",
        "default": "linked balanced 112-slot schedule",
        "valid": "3..5",
        "doc": "Width of every panel; the local motif remains 3x3.",
    },
    "transform": {
        "type": "enum",
        "default": "linked balanced 112-slot schedule",
        "valid": ["r1", "r2", "r3", "fh", "atr", "fv", "tr"],
        "doc": "The unique non-identity source-to-target D4 transform.",
    },
    "source_cells": {
        "type": "int",
        "default": "linked balanced 112-slot schedule",
        "valid": "4..7",
        "doc": "Number of occupied cells in the source motif.",
    },
    "query_cells": {
        "type": "int",
        "default": "linked balanced 112-slot schedule",
        "valid": "4..7",
        "doc": "Number of occupied cells in the query motif.",
    },
    "source_palette_size": {
        "type": "int",
        "default": "linked balanced 112-slot schedule",
        "valid": "1..2",
        "doc": "Number of preserved colors used by source and target motifs.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

# A 112-slot balanced schedule breaks nuisance-to-label shortcuts.  Each of
# eight morphology profiles appears in two seven-draw cycles.  Those two
# occurrences have opposite cycle parity, so every exact tuple
# (height, width, source cells, query cells, palette size) occurs once with
# every transform.  Palette size alternates on every draw.  Six profiles use
# canonical 3x3 panels and the two wider profiles are never adjacent, so every
# circular 14-draw window contains at least seven canonical-size examples.
_NUISANCE_PROFILES = (
    (3, 3, 4, 4),
    (3, 3, 5, 7),
    (3, 3, 6, 5),
    (3, 3, 7, 4),
    (3, 3, 4, 6),
    (3, 3, 7, 7),
    (3, 4, 5, 6),
    (5, 5, 6, 4),
)
# Profile IDs 6 and 7 are the non-canonical-size cycles.  Each profile ID
# occurs at one even and one odd cycle index; no two wide cycles are adjacent.
_CYCLE_PROFILE_IDS = (0, 0, 6, 1, 1, 6, 2, 2, 7, 3, 3, 7, 4, 4, 5, 5)
SCHEDULE_PERIOD = len(_CYCLE_PROFILE_IDS) * len(TRANSFORMS)
SCHEDULE_PROFILES = tuple(range(SCHEDULE_PERIOD))
_COLOR_POOL = (1, 2, 3, 4, 5, 6, 7, 8)


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _transform_grid(grid: Sequence[Sequence[int]], transform: int | str) -> list[list[int]]:
    """Apply the authority's exact transform-code convention."""
    if isinstance(transform, str):
        try:
            code = _NAME_TO_CODE[transform]
        except KeyError as exc:
            raise ValueError(f"unknown transform {transform!r}") from exc
    else:
        code = transform
    src = [list(row) for row in grid]
    if code == 0:
        return [row[:] for row in src]
    if code == 1:
        return [list(row) for row in zip(*src[::-1])]
    if code == 2:
        return [row[::-1] for row in src[::-1]]
    if code == 3:
        return [list(row) for row in zip(*src)][::-1]
    if code == 4:
        return [row[::-1] for row in src]
    if code == 5:
        return _transform_grid(_transform_grid(src, 4), 1)
    if code == 6:
        return _transform_grid(_transform_grid(src, 4), 2)
    if code == 7:
        return _transform_grid(_transform_grid(src, 4), 3)
    raise ValueError(f"transform code must be in 0..7, got {code!r}")


def _support(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    )


def _support_grid(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    grid = full_grid(3, 3, 0)
    for r, c in cells:
        grid[r][c] = 1
    return grid


def _orbit_signatures(grid: Sequence[Sequence[int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(sorted({_support(_transform_grid(grid, code)) for code in range(8)}))


def _orbit_key(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return min(_orbit_signatures(grid))


def _build_mask_bank() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    positions = tuple((r, c) for r in range(3) for c in range(3))
    bank: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for count in range(4, 8):
        masks = []
        for cells in combinations(positions, count):
            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            if rows != {0, 1, 2} or cols != {0, 1, 2}:
                continue
            support = _support_grid(cells)
            if len(_orbit_signatures(support)) == 8:
                masks.append(tuple(cells))
        if not masks:
            raise RuntimeError(f"no full-span D4-asymmetric masks for {count} cells")
        bank[count] = tuple(masks)
    return bank


_MASKS_BY_COUNT = _build_mask_bank()


def _profile_index(sample_index: int, difficulty=None) -> int:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    offset = {None: 0, "easy": 0, "medium": 35, "hard": 70}[difficulty]
    return (sample_index + offset) % SCHEDULE_PERIOD


def _profile_values(profile_index: int) -> tuple[str, int, int, int, int, int]:
    cycle, transform_index = divmod(profile_index, len(TRANSFORMS))
    nuisance_index = _CYCLE_PROFILE_IDS[cycle]
    panel_h, panel_w, source_cells, query_cells = _NUISANCE_PROFILES[nuisance_index]
    palette_size = 2 if (cycle + transform_index) % 2 == 0 else 1
    return (
        TRANSFORMS[transform_index],
        panel_h,
        panel_w,
        source_cells,
        query_cells,
        palette_size,
    )


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    return _profile_index(sample_index, difficulty)


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_transform_axis(ctx, overrides, default: str) -> str:
    if "transform" in overrides and overrides["transform"] is not None:
        return ctx.draw_choice("transform", TRANSFORMS)
    return ctx.draw_choice("transform", (default,))


def _choose_mask(rng, count: int, *, different_orbit_from=None):
    candidates = list(_MASKS_BY_COUNT[count])
    if different_orbit_from is not None:
        other_key = _orbit_key(_support_grid(different_orbit_from))
        filtered = [
            mask
            for mask in candidates
            if _orbit_key(_support_grid(mask)) != other_key
        ]
        if filtered:
            candidates = filtered
    return rng.choice(candidates)


def _paint_source(mask, colors: Sequence[int], rng) -> list[list[int]]:
    grid = full_grid(3, 3, 0)
    if len(colors) == 1:
        for r, c in mask:
            grid[r][c] = colors[0]
        return grid

    first, second = colors if rng.randrange(2) == 0 else tuple(reversed(colors))
    for r, c in mask:
        grid[r][c] = first if (r + c) % 2 == 0 else second
    used = {grid[r][c] for r, c in mask}
    if len(used) == 1:
        r, c = mask[-1]
        grid[r][c] = second if grid[r][c] == first else first
    return grid


def _paint_query(mask, color: int) -> list[list[int]]:
    grid = full_grid(3, 3, 0)
    for r, c in mask:
        grid[r][c] = color
    return grid


def _place(panel: list[list[int]], motif: Sequence[Sequence[int]], rng) -> None:
    top = rng.randint(0, len(panel) - len(motif))
    left = rng.randint(0, len(panel[0]) - len(motif[0]))
    for r, row in enumerate(motif):
        for c, value in enumerate(row):
            if value:
                panel[top + r][left + c] = value


def _split_panels(grid, divider_columns):
    starts = (0, divider_columns[0] + 1, divider_columns[1] + 1)
    stops = (divider_columns[0], divider_columns[1], len(grid[0]))
    return tuple(
        [[grid[r][c] for c in range(starts[i], stops[i])] for r in range(len(grid))]
        for i in range(3)
    )


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return None
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in panel[r0 : r1 + 1]]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC bounds: {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analyze(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, width = len(grid), len(grid[0])
    dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 2:
        return {"errors": [f"expected exactly two full color-9 divider columns, found {dividers}"]}
    panels = _split_panels(grid, dividers)
    panel_widths = tuple(len(panel[0]) for panel in panels)
    errors = []
    if len(set(panel_widths)) != 1:
        errors.append(f"panels must have equal widths, found {panel_widths}")
    if not 3 <= h <= 5:
        errors.append(f"panel height {h} outside 3..5")
    if any(not 3 <= panel_width <= 5 for panel_width in panel_widths):
        errors.append(f"panel widths {panel_widths} outside 3..5")
    divider_set = set(dividers)
    if any(grid[r][c] == 9 for r in range(h) for c in range(width) if c not in divider_set):
        errors.append("color 9 may appear only in the two divider columns")

    crops = tuple(_crop(panel) for panel in panels)
    for index, crop in enumerate(crops, start=1):
        if crop is None:
            errors.append(f"panel {index} has no motif")
        elif (len(crop), len(crop[0])) != (3, 3):
            errors.append(f"panel {index} crop must span 3x3, got {len(crop)}x{len(crop[0])}")
    if errors:
        return {"errors": errors, "panels": panels, "crops": crops}

    source, target, query = crops
    source_cells = sum(value != 0 for row in source for value in row)
    target_cells = sum(value != 0 for row in target for value in row)
    query_cells = sum(value != 0 for row in query for value in row)
    source_palette = {value for row in source for value in row if value}
    target_palette = {value for row in target for value in row if value}
    query_palette = {value for row in query for value in row if value}
    if not 4 <= source_cells <= 7:
        errors.append(f"source motif has {source_cells} cells, expected 4..7")
    if target_cells != source_cells:
        errors.append("source and target must have the same occupied-cell count")
    if not 4 <= query_cells <= 7:
        errors.append(f"query motif has {query_cells} cells, expected 4..7")
    if not 1 <= len(source_palette) <= 2:
        errors.append(f"source palette size {len(source_palette)} outside 1..2")
    if target_palette != source_palette:
        errors.append("target must preserve the source palette")
    if len(query_palette) != 1:
        errors.append(f"query must use exactly one motif color, found {sorted(query_palette)}")

    candidates = [
        code for code in range(8) if _transform_grid(source, code) == target
    ]
    if not candidates:
        errors.append("target is not a D4 transform of source")
    if errors:
        return {
            "errors": errors,
            "panels": panels,
            "crops": crops,
            "candidates": candidates,
        }

    selected_code = candidates[0]
    query_orbit = {_freeze(_transform_grid(query, code)) for code in range(8)}
    truth = _transform_grid(query, selected_code)
    return {
        "errors": [],
        "panels": panels,
        "crops": crops,
        "panel_h": h,
        "panel_w": panel_widths[0],
        "source_cells": source_cells,
        "query_cells": query_cells,
        "source_palette_size": len(source_palette),
        "candidates": candidates,
        "selected_code": selected_code,
        "selected_transform": _CODE_TO_NAME[selected_code],
        "query_orbit_size": len(query_orbit),
        "truth": truth,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic lawful input; Racket owns all labels."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "transform":
            if not isinstance(value, str):
                raise TypeError(f"transform must be a string, not {type(value).__name__}")
        elif type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    profile = _profile_values(_profile_index(sample_index, difficulty))
    default_transform, default_h, default_w, default_source_cells, default_query_cells, default_palette = profile
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    transform = _draw_transform_axis(ctx, overrides, default_transform)
    panel_h = _draw_int_axis(ctx, overrides, "panel_h", default_h, 3, 5)
    panel_w = _draw_int_axis(ctx, overrides, "panel_w", default_w, 3, 5)
    source_cells = _draw_int_axis(ctx, overrides, "source_cells", default_source_cells, 4, 7)
    query_cells = _draw_int_axis(ctx, overrides, "query_cells", default_query_cells, 4, 7)
    palette_size = _draw_int_axis(ctx, overrides, "source_palette_size", default_palette, 1, 2)

    source_rng = ctx.draw_rng("source_motif")
    query_rng = ctx.draw_rng("query_motif")
    color_rng = ctx.draw_rng("colors")
    placement_rng = ctx.draw_rng("placements")

    source_mask = _choose_mask(source_rng, source_cells)
    query_mask = _choose_mask(query_rng, query_cells, different_orbit_from=source_mask)
    source_colors = color_rng.sample(list(_COLOR_POOL), palette_size)
    query_color = color_rng.choice([color for color in _COLOR_POOL if color not in source_colors])
    source = _paint_source(source_mask, source_colors, color_rng)
    target = _transform_grid(source, transform)
    query = _paint_query(query_mask, query_color)

    panels = [full_grid(panel_h, panel_w, 0) for _ in range(3)]
    for panel, motif in zip(panels, (source, target, query), strict=True):
        _place(panel, motif, placement_rng)

    grid = full_grid(panel_h, panel_w * 3 + 2, 0)
    for divider in (panel_w, panel_w * 2 + 1):
        for row in range(panel_h):
            grid[row][divider] = 9
    for panel_index, panel in enumerate(panels):
        left = panel_index * (panel_w + 1)
        for row in range(panel_h):
            for col in range(panel_w):
                grid[row][left + col] = panel[row][col]

    analysis = _analyze(grid)
    if analysis["errors"]:
        raise RuntimeError(f"constructed invalid instance: {analysis['errors']}")
    if len(analysis["candidates"]) != 1:
        raise RuntimeError(f"constructed ambiguous transform: {analysis['candidates']}")
    if analysis["query_orbit_size"] != 8:
        raise RuntimeError(f"constructed query orbit size {analysis['query_orbit_size']}, expected 8")
    return [row[:] for row in grid]


def observe_overrides(grid) -> dict[str, object]:
    """Recover every advertised axis from pixels, not RNG bookkeeping."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "panel_h": analysis["panel_h"],
        "panel_w": analysis["panel_w"],
        "transform": analysis["selected_transform"],
        "source_cells": analysis["source_cells"],
        "query_cells": analysis["query_cells"],
        "source_palette_size": analysis["source_palette_size"],
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    query = analysis["crops"][2]
    return {
        **observe_overrides(grid),
        "transform_candidate_count": len(analysis["candidates"]),
        "candidate_transforms": tuple(_CODE_TO_NAME[code] for code in analysis["candidates"]),
        "query_orbit_size": analysis["query_orbit_size"],
        "query_changes": analysis["truth"] != query,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror for tests; selected Racket remains label authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["truth"]]


def _fixed_transform(name: str):
    def rival(grid):
        analysis = _analyze(grid)
        if analysis["errors"]:
            raise ValueError("; ".join(analysis["errors"]))
        return _transform_grid(analysis["crops"][2], name)

    return rival


SEMANTIC_RIVALS = {
    f"always_{name}": _fixed_transform(name) for name in TRANSFORM_PRECEDENCE
}
CANONICAL_SHORTCUTS = {"always_r1": SEMANTIC_RIVALS["always_r1"]}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _transform_witness(name: str):
    def witness(grid):
        analysis = _analyze(grid)
        return (
            not analysis["errors"]
            and analysis["selected_transform"] == name
            and len(analysis["candidates"]) == 1
            and analysis["query_orbit_size"] == 8
        )

    return witness


SEMANTIC_WITNESSES = {
    f"transform_{name}": _transform_witness(name) for name in TRANSFORMS
}
WITNESS_RIVALS = {
    f"transform_{name}": [
        rival_name
        for rival_name in SEMANTIC_RIVALS
        if rival_name != f"always_{name}"
    ]
    for name in TRANSFORMS
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require two distinct demonstrated transforms and refute fixed-rule rivals."""
    if not isinstance(demos, (list, tuple)):
        return ["demonstrations must be a sequence"]
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    transforms: set[str] = set()
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is unlawful: {analysis['errors'][0]}")
            continue
        if len(analysis["candidates"]) != 1:
            reasons.append(f"demo {index} does not uniquely identify one transform")
        if analysis["query_orbit_size"] != 8:
            reasons.append(f"demo {index} query does not distinguish all D4 transforms")
        expected = [list(row) for row in analysis["truth"]]
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the transform rule")
        transforms.add(analysis["selected_transform"])
        valid_demos.append(demo)

    query_analysis = _analyze(query["input"])
    if query_analysis["errors"]:
        reasons.append(f"query input is unlawful: {query_analysis['errors'][0]}")
    elif "output" in query and query["output"] != query_analysis["truth"]:
        reasons.append("query output disagrees with the transform rule")
    if reasons:
        return reasons
    if len(transforms) < 2:
        reasons.append("demonstrations expose only one transform, leaving a fixed-transform shortcut")

    query_truth = [list(row) for row in query_analysis["truth"]]
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
