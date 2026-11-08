"""Generator for ARC task c64f1187 / content hash db80068a483e.

The top legend maps each key color to a non-empty 2x2 binary mask.  The lower
array is a lattice of 2x2 color-5 tiles separated by one blank row/column; a
tile's bottom-right cell either names a key color or remains 5.  The output is
the lower lattice's bounding box with each keyed tile replaced by its colored
mask and every unkeyed tile left blank.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "db80068a483e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "7e9649df4812"
SUMMARY = (
    "Use the top color-to-2x2-mask legend to paint matching cells of the "
    "lower separated 2x2 tile lattice."
)

INVARIANTS = [
    "background is color 0; legend masks use color 1; lower tile frames use color 5",
    "three or four distinct key markers share row 0 or 1 and each owns a non-empty 2x2 mask immediately down-right",
    "the lower region is a 3x4, 3x5, or 4x4 lattice of 2x2 tiles separated by one blank row and column",
    "every tile bottom-right cell is either 5 (blank output tile) or one of the key colors",
    "every key color occurs in at least one lower tile and at least one lower tile is unkeyed",
]

PROFILES = {
    "17x18_3x5_3k": (17, 18, 3, 5, 3),
    "18x20_3x4_4k": (18, 20, 3, 4, 4),
    "20x18_4x4_4k": (20, 18, 4, 4, 4),
}
PROFILE_BY_FACTS = {
    (h, w, tile_rows, tile_cols, n_keys): name
    for name, (h, w, tile_rows, tile_cols, n_keys) in PROFILES.items()
}

AXES = {
    "profile": {
        "type": "str",
        "default": "rng canonical profile",
        "valid": "17x18_3x5_3k|18x20_3x4_4k|20x18_4x4_4k",
    },
    "key_row": {"type": "int", "default": "rng", "valid": "0..1"},
    "key_stride": {"type": "int", "default": "rng", "valid": "4..5"},
    "probe_mask_size": {"type": "int", "default": "rng", "valid": "3..4"},
    "blank_count": {"type": "int", "default": "rng", "valid": "5..6"},
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

ALL_MASKS = tuple(
    tuple((dr, dc) for bit, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))) if bits & (1 << bit))
    for bits in range(1, 16)
)
FULL_MASK = ((0, 0), (0, 1), (1, 0), (1, 1))


def _rectangular(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return 0, 0, ["empty or non-list grid"]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        errors.append("ragged grid")
        return h, w, errors
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row):
        errors.append("grid cells must be integer ARC colors 0..9")
    return h, w, errors


def _analyze(grid: list[list[int]]) -> tuple[dict[str, Any], list[str]]:
    """Recover the complete task grammar from pixels and reject impostors."""
    h, w, errors = _rectangular(grid)
    facts: dict[str, Any] = {"grid_h": h, "grid_w": w}
    if errors:
        return facts, errors

    five_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    if not five_cells:
        return facts, ["missing color-5 lower tile lattice"]
    r0 = min(r for r, _ in five_cells)
    c0 = min(c for _, c in five_cells)
    r1 = max(r for r, _ in five_cells)
    c1 = max(c for _, c in five_cells)
    if r0 < 5:
        errors.append("lower tile lattice begins too close to the legend")

    key_markers = [
        (grid[r][c], r, c)
        for r in range(r0)
        for c in range(w)
        if grid[r][c] not in (0, 1, 5)
    ]
    if not 3 <= len(key_markers) <= 4:
        errors.append(f"expected 3 or 4 key markers, got {len(key_markers)}")
    marker_colors = [color for color, _r, _c in key_markers]
    if len(set(marker_colors)) != len(marker_colors):
        errors.append("key marker colors must be distinct")
    marker_rows = {r for _color, r, _c in key_markers}
    if len(marker_rows) != 1 or (marker_rows and next(iter(marker_rows)) not in (0, 1)):
        errors.append("all key markers must share row 0 or 1")
    marker_cols = sorted(c for _color, _r, c in key_markers)
    strides = {b - a for a, b in zip(marker_cols, marker_cols[1:])}
    if marker_cols and (len(strides) != 1 or next(iter(strides), 0) not in (4, 5)):
        errors.append("key markers must use a uniform stride of 4 or 5 columns")

    masks: dict[int, tuple[tuple[int, int], ...]] = {}
    allowed_legend_cells: set[tuple[int, int]] = set()
    for color, kr, kc in key_markers:
        allowed_legend_cells.add((kr, kc))
        if kr + 2 >= r0 or kc + 2 >= w:
            errors.append(f"key color {color} lacks room for its 2x2 mask")
            continue
        mask = tuple(
            (dr, dc)
            for dr in (0, 1)
            for dc in (0, 1)
            if grid[kr + 1 + dr][kc + 1 + dc] == 1
        )
        if not mask:
            errors.append(f"key color {color} has an empty 2x2 mask")
        masks[color] = mask
        allowed_legend_cells.update((kr + 1 + dr, kc + 1 + dc) for dr, dc in mask)
    for r in range(r0):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in allowed_legend_cells:
                errors.append(f"unexpected legend-region cell {grid[r][c]} at {(r, c)}")
                break
        if errors and errors[-1].startswith("unexpected legend-region"):
            break

    def row_has_5(row: int) -> bool:
        return any(grid[row][c] == 5 for c in range(c0, c1 + 1))

    def col_has_5(col: int) -> bool:
        return any(grid[r][col] == 5 for r in range(r0, r1 + 1))

    tile_rows = [r for r in range(r0, r1 + 1) if row_has_5(r) and (r == r0 or not row_has_5(r - 1))]
    tile_cols = [c for c in range(c0, c1 + 1) if col_has_5(c) and (c == c0 or not col_has_5(c - 1))]
    if not 3 <= len(tile_rows) <= 4:
        errors.append(f"expected 3 or 4 tile rows, got {len(tile_rows)}")
    if not 4 <= len(tile_cols) <= 5:
        errors.append(f"expected 4 or 5 tile columns, got {len(tile_cols)}")
    if any(b - a != 3 for a, b in zip(tile_rows, tile_rows[1:])):
        errors.append("tile-row starts must be separated by exactly 3")
    if any(b - a != 3 for a, b in zip(tile_cols, tile_cols[1:])):
        errors.append("tile-column starts must be separated by exactly 3")

    expected_nonzero: set[tuple[int, int]] = set()
    expected_fives: set[tuple[int, int]] = set()
    centers: list[tuple[int, int, int]] = []
    key_colors = set(marker_colors)
    for tr in tile_rows:
        for tc in tile_cols:
            if tr + 1 >= h or tc + 1 >= w:
                errors.append(f"tile at {(tr, tc)} runs off the grid")
                continue
            frame = ((tr, tc), (tr, tc + 1), (tr + 1, tc))
            if any(grid[r][c] != 5 for r, c in frame):
                errors.append(f"tile at {(tr, tc)} must have three fixed color-5 frame cells")
            expected_fives.update(frame)
            expected_nonzero.update(frame)
            center = grid[tr + 1][tc + 1]
            if center not in key_colors | {5}:
                errors.append(f"tile at {(tr, tc)} has unkeyed bottom-right color {center}")
            if center != 0:
                expected_nonzero.add((tr + 1, tc + 1))
            if center == 5:
                expected_fives.add((tr + 1, tc + 1))
            centers.append((tr, tc, center))

    actual_nonzero_in_bbox = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if grid[r][c] != 0
    }
    if actual_nonzero_in_bbox != expected_nonzero:
        errors.append("lower bbox contains cells outside the separated 2x2 tile grammar")
    if five_cells != expected_fives:
        errors.append("color-5 cells do not exactly form the lower tile frames")

    used_colors = {center for _tr, _tc, center in centers if center != 5}
    missing = key_colors - used_colors
    if missing:
        errors.append(f"key color(s) never used by a lower tile: {sorted(missing)}")
    blank_positions = [(i, j) for i, tr in enumerate(tile_rows) for j, tc in enumerate(tile_cols) if grid[tr + 1][tc + 1] == 5]
    if not blank_positions:
        errors.append("at least one unkeyed tile is required to expose the blank-output branch")
    if masks and len(set(masks.values())) != len(masks):
        errors.append("key masks must be pairwise distinct")
    if masks and not any(len(mask) < 4 for mask in masks.values()):
        errors.append("at least one non-full key mask is required")
    if masks and not any(len(mask) == 4 for mask in masks.values()):
        errors.append("at least one full key mask is required")

    profile = PROFILE_BY_FACTS.get((h, w, len(tile_rows), len(tile_cols), len(key_markers)))
    if profile is None:
        errors.append(
            "grid dimensions, tile shape, and key count do not match any canonical profile"
        )

    ordered_markers = sorted(key_markers, key=lambda item: item[2])
    ordered_colors = [color for color, _r, _c in ordered_markers]
    counts = {color: sum(center == color for _tr, _tc, center in centers) for color in ordered_colors}
    probe_color = ordered_colors[0] if ordered_colors else None
    facts.update(
        {
            "bbox": (r0, c0, r1, c1),
            "tile_rows": tuple(tile_rows),
            "tile_cols": tuple(tile_cols),
            "key_markers": tuple(ordered_markers),
            "key_colors": tuple(ordered_colors),
            "masks": masks,
            "centers": tuple(centers),
            "blank_positions": tuple(blank_positions),
            "profile": profile,
            "key_row": ordered_markers[0][1] if ordered_markers and len(marker_rows) == 1 else None,
            "key_stride": next(iter(strides)) if len(strides) == 1 else None,
            "probe_mask_size": len(masks.get(probe_color, ())) if probe_color is not None else None,
            "blank_count": len(blank_positions),
            "probe_repeats": counts.get(probe_color, 0),
        }
    )
    return facts, errors


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if requested:
        observed = observe_overrides(grid)
        for name, expected in requested.items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(
                    f"override {name} requested {expected!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the exact structural feature ranges shared by all canonical pairs."""
    errors = self_check(grid)
    if errors:
        return errors
    facts, _ = _analyze(grid)
    if facts["blank_count"] not in (5, 6):
        errors.append("canonical-like scenes require exactly 5 or 6 blank lower tiles")
    expected_masks = [3, 3, 4] if len(facts["key_colors"]) == 3 else [3, 3, 3, 4]
    if sorted(len(mask) for mask in facts["masks"].values()) != expected_masks:
        errors.append(f"canonical-like mask sizes must be {expected_masks}")
    return errors


def canonical_profile_signature(grid):
    facts, errors = _analyze(grid)
    if errors:
        return None
    return (
        facts["profile"],
        facts["key_row"],
        facts["key_stride"],
        facts["blank_count"],
        tuple(sorted(len(mask) for mask in facts["masks"].values())),
    )


def _choose_probe_mask(size: int, rng) -> tuple[tuple[int, int], ...]:
    return rng.choice([mask for mask in ALL_MASKS if len(mask) == size])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", tuple(PROFILES))
    key_row = ctx.draw_int("key_row", 0, 1)
    key_stride = ctx.draw_int("key_stride", 4, 5)
    probe_mask_size = ctx.draw_int("probe_mask_size", 3, 4)
    blank_count = ctx.draw_int("blank_count", 5, 6)

    h, w, n_tile_rows, n_tile_cols, n_keys = PROFILES[profile]
    rng = ctx.draw_rng(f"layout_{band}")
    key_colors = list(ctx.draw_distinct_colors(f"key_colors_{band}", n=n_keys, exclude={0, 1, 5}))

    max_key_left = w - ((n_keys - 1) * key_stride + 3)
    if max_key_left < 0:
        raise ValueError("selected key layout does not fit the canonical profile")
    key_left = rng.randint(0, max_key_left)

    three_masks = [mask for mask in ALL_MASKS if len(mask) == 3]
    probe_mask = _choose_probe_mask(probe_mask_size, rng)
    masks: list[tuple[tuple[int, int], ...]] = [probe_mask]
    if probe_mask != FULL_MASK:
        masks.append(FULL_MASK)
    while len(masks) < n_keys:
        candidates = [mask for mask in three_masks if mask not in masks]
        masks.append(rng.choice(candidates))
    if not any(len(mask) < 4 for mask in masks):
        raise AssertionError("internal mask construction lost the sparse branch")

    bbox_h = 3 * n_tile_rows - 1
    bbox_w = 3 * n_tile_cols - 1
    min_tile_top = key_row + 6
    max_tile_top = h - bbox_h - 1
    if min_tile_top > max_tile_top:
        raise ValueError("legend and lower lattice cannot fit with required separation")
    tile_top = rng.randint(min_tile_top, max_tile_top)
    tile_left = rng.randint(0, w - bbox_w)
    tile_rows = [tile_top + 3 * i for i in range(n_tile_rows)]
    tile_cols = [tile_left + 3 * j for j in range(n_tile_cols)]

    positions = [(i, j) for i in range(n_tile_rows) for j in range(n_tile_cols)]
    rng.shuffle(positions)
    blank_positions = set(positions[:blank_count])
    available = positions[blank_count:]
    if len(available) < n_keys + 1:
        raise ValueError("blank_count leaves too few keyed tiles for every key and one repeat")

    center_by_pos: dict[tuple[int, int], int] = {pos: 5 for pos in blank_positions}
    rng.shuffle(available)
    cursor = 0
    # Every key appears and the first key repeats, matching the canonical count range.
    for color in key_colors:
        center_by_pos[available[cursor]] = color
        cursor += 1
    center_by_pos[available[cursor]] = key_colors[0]
    cursor += 1
    while cursor < len(available):
        center_by_pos[available[cursor]] = rng.choice(key_colors)
        cursor += 1

    grid = full_grid(h, w, 0)
    for index, color in enumerate(key_colors):
        kc = key_left + index * key_stride
        grid[key_row][kc] = color
        for dr, dc in masks[index]:
            grid[key_row + 1 + dr][kc + 1 + dc] = 1

    for i, tr in enumerate(tile_rows):
        for j, tc in enumerate(tile_cols):
            grid[tr][tc] = 5
            grid[tr][tc + 1] = 5
            grid[tr + 1][tc] = 5
            grid[tr + 1][tc + 1] = center_by_pos[(i, j)]

    generated_errors = self_check(grid, difficulty=band, meta={"overrides": {
        "profile": profile,
        "key_row": key_row,
        "key_stride": key_stride,
        "probe_mask_size": probe_mask_size,
        "blank_count": blank_count,
    }})
    if generated_errors:
        raise AssertionError("generated invalid key-mask lesson: " + "; ".join(generated_errors))
    return grid


def _render_policy(grid: list[list[int]], policy: str) -> list[list[int]]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, r1, c1 = facts["bbox"]
    out = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    first_color = facts["key_colors"][0]
    first_mask = facts["masks"][first_color]
    for tr, tc, color in facts["centers"]:
        if color == 5:
            if policy != "paint_blank_tiles":
                continue
            mask = first_mask
            paint_color = 5
        else:
            paint_color = color
            if policy == "solid_fill":
                mask = FULL_MASK
            elif policy == "first_mask_for_all":
                mask = first_mask
            else:
                mask = facts["masks"][color]
        for dr, dc in mask:
            out[tr - r0 + dr][tc - c0 + dc] = paint_color
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _render_policy(grid, "canonical")


def _solid_fill(grid):
    return _render_policy(grid, "solid_fill")


def _first_mask_for_all(grid):
    return _render_policy(grid, "first_mask_for_all")


def _paint_blank_tiles(grid):
    return _render_policy(grid, "paint_blank_tiles")


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "solid_fill": _solid_fill,
    "first_mask_for_all": _first_mask_for_all,
    "paint_blank_tiles": _paint_blank_tiles,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _facts_predicate(predicate: Callable[[dict[str, Any]], bool]):
    def wrapped(grid) -> bool:
        facts, errors = _analyze(grid)
        return not errors and bool(predicate(facts))
    return wrapped


SEMANTIC_WITNESSES = {
    "profile_17x18": _facts_predicate(lambda f: f["profile"] == "17x18_3x5_3k"),
    "profile_18x20": _facts_predicate(lambda f: f["profile"] == "18x20_3x4_4k"),
    "profile_20x18": _facts_predicate(lambda f: f["profile"] == "20x18_4x4_4k"),
    "key_row_zero": _facts_predicate(lambda f: f["key_row"] == 0),
    "key_row_one": _facts_predicate(lambda f: f["key_row"] == 1),
    "stride_four": _facts_predicate(lambda f: f["key_stride"] == 4),
    "stride_five": _facts_predicate(lambda f: f["key_stride"] == 5),
    "probe_mask_three": _facts_predicate(lambda f: f["probe_mask_size"] == 3),
    "probe_mask_four": _facts_predicate(lambda f: f["probe_mask_size"] == 4),
    "three_cell_mask": _facts_predicate(lambda f: any(len(mask) == 3 for mask in f["masks"].values())),
    "full_mask": _facts_predicate(lambda f: any(len(mask) == 4 for mask in f["masks"].values())),
    "five_blank_tiles": _facts_predicate(lambda f: f["blank_count"] == 5),
    "six_blank_tiles": _facts_predicate(lambda f: f["blank_count"] == 6),
    "sparse_mask_refutes_solid_fill": _facts_predicate(lambda f: any(len(mask) < 4 for mask in f["masks"].values())),
    "distinct_used_key_masks": _facts_predicate(lambda f: len({f["masks"][color] for color in f["key_colors"]}) > 1),
    "blank_tile_branch": _facts_predicate(lambda f: bool(f["blank_positions"])),
    "repeated_probe_color": _facts_predicate(lambda f: f["probe_repeats"] >= 2),
}

WITNESS_RIVALS = {
    "sparse_mask_refutes_solid_fill": ["solid_fill"],
    "distinct_used_key_masks": ["first_mask_for_all"],
    "blank_tile_branch": ["paint_blank_tiles"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that permit solid-fill, one-mask, or paint-all shortcuts."""
    reasons: list[str] = []
    if len(demos) < 1:
        return ["at least one complete demonstration is required"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not isinstance(pair.get("input"), list):
            reasons.append(f"demo {index} is missing an input grid")
            continue
        inp, out = pair["input"], pair.get("output")
        facts, errors = _analyze(inp)
        if errors:
            reasons.append(f"demo {index} violates the key-mask teaching grammar")
            continue
        intended = rule_mirror(inp)
        if out != intended:
            reasons.append(f"demo {index} output disagrees with the key-mask rule")
        for name, rival in LESSON_COMPETITORS.items():
            if rival(inp) == intended:
                reasons.append(f"demo {index} fails to refute competitor {name}")

    if not isinstance(query, dict) or not isinstance(query.get("input"), list):
        reasons.append("query input is missing")
        return reasons
    query_grid = query["input"]
    facts, errors = _analyze(query_grid)
    if errors:
        reasons.append("query violates the key-mask teaching grammar")
        return reasons
    intended = rule_mirror(query_grid)
    for name, rival in LESSON_COMPETITORS.items():
        if rival(query_grid) == intended:
            reasons.append(f"query answer is ambiguous with competitor {name}")
    return reasons
