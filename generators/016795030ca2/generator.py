"""Generator for ARC task ``016795030ca2`` (source slug ``22233c11``).

Canonical rule
--------------
Each 8-connected color-3 component consists of two equal ``N x N`` blocks in
opposite quadrants of a ``2N x 2N`` bounding box.  Paint two color-8 blocks in
the *other diagonal*: one just beyond each empty bbox corner.  Equivalently,
the added blocks lie on the diagonal perpendicular to the two source blocks.
Cells outside the board are clipped, while every source block remains intact.

The canonical examples require all of the following: block sizes 1, 2, and 3;
both diagonal orientations; two components on one board (including mixed
orientations); and a clipped size-3 query.  The scheduled teaching sequence
puts those branches into every materialized three-demo lesson so that common
shortcuts cannot survive to the query.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "016795030ca2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "9a16e24d93be"

SUMMARY = (
    "Find every 8-connected motif made of two equal NxN color-3 blocks in "
    "opposite quadrants. Paint equal NxN color-8 blocks just outside the two "
    "empty corners, on the perpendicular diagonal; clip only cells that fall "
    "outside the board. All motifs are processed."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "the input palette is exactly background 0 plus motif color 3",
    "there are one or two separated 8-connected motifs",
    "every motif is exactly two equal 1x1, 2x2, or 3x3 blocks in opposite quadrants",
    "all motifs on a generated board use the same block size",
    "each projected endpoint has at least one visible cell",
    "projected cells neither overwrite a source motif nor overlap another projection",
    "plain scenes have no clipping; clip_edge scenes have visible partial clipping",
]

# Negative fixtures remain callable for mutation/diagnostic probes, but are not
# lawful override-axis values because they intentionally fail self_check.
DEGENERATE_TEXTURES = ("single_block", "no_blocks", "full_grid")
HELPFUL_TEXTURES = ("plain", "clip_edge")

# Keep only independently controllable, exactly observable axes. Orientation is
# covered by the deterministic semantic schedule and witnesses; a single bool
# would be dishonest on canonical-style mixed-orientation two-motif boards.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 9..16 with canonical 10x10 anchors",
        "valid": "9..16",
        "doc": "Grid height; every boundary is valid in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 9..16 with canonical 10x10 anchors",
        "valid": "9..16",
        "doc": "Grid width; every boundary is valid in every difficulty band.",
    },
    "block_size": {
        "type": "int",
        "default": "scheduled canonical sizes 1, 2, and 3",
        "valid": "1..3",
        "doc": "N for every NxN source block on the board.",
    },
    "n_motifs": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of separated two-block components.",
    },
    "texture": {
        "type": "str",
        "default": "scheduled plain or clip_edge",
        "valid": "plain|clip_edge",
        "doc": "plain keeps both projected blocks in bounds; clip_edge clips part of one or both.",
    },
}

# The first four entries are load-bearing: runner.run_one materializes
# sample_index 0,1,2 as demos and 3 as the query. Those demos jointly expose a
# size-1 main motif, a clipped size-2 anti motif, and two mixed size-1 motifs;
# the query asks for a size-3 main motif.
_SCHEDULE = (
    dict(grid_h=10, grid_w=10, block_size=1, n_motifs=1, texture="plain", orientation="main"),
    dict(grid_h=10, grid_w=10, block_size=2, n_motifs=1, texture="clip_edge", orientation="anti"),
    dict(grid_h=10, grid_w=10, block_size=1, n_motifs=2, texture="plain", orientation="mixed"),
    dict(grid_h=12, grid_w=12, block_size=3, n_motifs=1, texture="plain", orientation="main"),
    dict(grid_h=9, grid_w=11, block_size=2, n_motifs=1, texture="clip_edge", orientation="main"),
    dict(grid_h=16, grid_w=16, block_size=2, n_motifs=2, texture="clip_edge", orientation="mixed"),
    dict(grid_h=12, grid_w=14, block_size=2, n_motifs=1, texture="plain", orientation="anti"),
    dict(grid_h=13, grid_w=15, block_size=3, n_motifs=1, texture="clip_edge", orientation="anti"),
)

_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _cells_in_box(r1: int, c1: int, size: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r1, r1 + size)
        for c in range(c1, c1 + size)
    }


def _input_cells(r1: int, c1: int, size: int, is_anti: bool) -> set[tuple[int, int]]:
    if is_anti:
        return _cells_in_box(r1, c1 + size, size) | _cells_in_box(
            r1 + size, c1, size
        )
    return _cells_in_box(r1, c1, size) | _cells_in_box(
        r1 + size, c1 + size, size
    )


def _projection_full_groups(
    r1: int, c1: int, size: int, is_anti: bool
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Return the two full (possibly out-of-bounds) output blocks.

    Main-diagonal sources (TL+BR) project to NE+SW. Anti-diagonal sources
    (TR+BL) project to NW+SE.
    """
    if is_anti:
        return (
            _cells_in_box(r1 - size, c1 - size, size),
            _cells_in_box(r1 + 2 * size, c1 + 2 * size, size),
        )
    return (
        _cells_in_box(r1 - size, c1 + 2 * size, size),
        _cells_in_box(r1 + 2 * size, c1 - size, size),
    )


def _clip_cells(
    cells: set[tuple[int, int]], height: int, width: int
) -> set[tuple[int, int]]:
    return {(r, c) for r, c in cells if 0 <= r < height and 0 <= c < width}


def _candidate(
    r1: int, c1: int, size: int, is_anti: bool, height: int, width: int
) -> dict[str, Any]:
    source = _input_cells(r1, c1, size, is_anti)
    full_groups = _projection_full_groups(r1, c1, size, is_anti)
    visible_groups = tuple(_clip_cells(group, height, width) for group in full_groups)
    visible = visible_groups[0] | visible_groups[1]
    clipped = sum(len(group) - len(visible_group) for group, visible_group in zip(full_groups, visible_groups))
    return {
        "r1": r1,
        "c1": c1,
        "size": size,
        "is_anti": is_anti,
        "source": source,
        "full_groups": full_groups,
        "visible_groups": visible_groups,
        "visible": visible,
        "clipped": clipped,
    }


def _source_components_separate(a: set[tuple[int, int]], b: set[tuple[int, int]]) -> bool:
    return not any(
        (r + dr, c + dc) in b
        for r, c in a
        for dr, dc in ((0, 0),) + _NEIGHBORS_8
    )


def _compatible(candidate: dict[str, Any], chosen: list[dict[str, Any]]) -> bool:
    for other in chosen:
        if not _source_components_separate(candidate["source"], other["source"]):
            return False
        if candidate["visible"] & other["source"]:
            return False
        if other["visible"] & candidate["source"]:
            return False
        if candidate["visible"] & other["visible"]:
            return False
    return True


def _candidate_positions(
    height: int,
    width: int,
    size: int,
    is_anti: bool,
    texture: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for r1 in range(height - 2 * size + 1):
        for c1 in range(width - 2 * size + 1):
            item = _candidate(r1, c1, size, is_anti, height, width)
            if any(not group for group in item["visible_groups"]):
                continue
            if item["visible"] & item["source"]:
                continue
            if texture == "plain" and item["clipped"] != 0:
                continue
            if texture == "clip_edge" and item["clipped"] == 0:
                continue
            candidates.append(item)
    return candidates


def _place_motifs(
    height: int,
    width: int,
    size: int,
    orientations: list[bool],
    texture: str,
    rng,
) -> list[dict[str, Any]]:
    pools = [
        _candidate_positions(height, width, size, is_anti, texture)
        for is_anti in orientations
    ]
    for pool in pools:
        rng.shuffle(pool)

    def search(index: int, chosen: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        if index == len(pools):
            return list(chosen)
        for item in pools[index]:
            if not _compatible(item, chosen):
                continue
            chosen.append(item)
            result = search(index + 1, chosen)
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0, [])
    if result is None:
        raise ValueError(
            "incompatible exact axes: cannot place "
            f"n_motifs={len(orientations)}, block_size={size}, texture={texture!r} "
            f"on {height}x{width} without merging motifs or overlapping projections"
        )
    return result


def _explicit_compat_defaults(overrides: dict[str, Any]) -> dict[str, Any]:
    """Choose safe defaults around explicit axes; caller values win later.

    The override checker exercises each axis independently in every difficulty
    band. An independent boundary must therefore remain constructible rather
    than inheriting an unrelated scheduled size/texture combination.
    """
    requested_size = int(overrides.get("block_size", 1))
    requested_motifs = int(overrides.get("n_motifs", 1))
    requested_texture = str(overrides.get("texture", "plain"))
    if requested_texture == "clip_edge" and "block_size" not in overrides:
        requested_size = 2

    if requested_motifs == 2 and "block_size" not in overrides:
        requested_size = 1
    if requested_texture == "plain" and "block_size" not in overrides:
        requested_size = 1

    base_dim = max(10, 4 * requested_size)
    if requested_motifs == 2:
        base_dim = max(base_dim, 16 if requested_size > 1 else 10)
    base_dim = min(16, base_dim)

    height = int(overrides.get("grid_h", base_dim))
    width = int(overrides.get("grid_w", base_dim))
    if "texture" not in overrides and min(height, width) < 4 * requested_size:
        requested_texture = "clip_edge"

    return {
        "grid_h": height,
        "grid_w": width,
        "block_size": requested_size,
        "n_motifs": requested_motifs,
        "texture": requested_texture,
        "orientation": "mixed" if requested_motifs == 2 else "main",
    }


def _effective_defaults(sample_index: int, overrides: dict[str, Any]) -> dict[str, Any]:
    if overrides:
        defaults = _explicit_compat_defaults(overrides)
    else:
        defaults = dict(_SCHEDULE[sample_index % len(_SCHEDULE)])
    defaults.update(overrides)
    return defaults


def _orientation_list(profile: str, n_motifs: int, rng) -> list[bool]:
    if n_motifs == 1:
        if profile == "anti":
            return [True]
        if profile == "main":
            return [False]
        return [bool(rng.randrange(2))]
    if profile == "mixed":
        result = [False, True]
        if rng.randrange(2):
            result.reverse()
        return result
    if profile == "anti":
        return [True, True]
    if profile == "main":
        return [False, False]
    return [bool(rng.randrange(2)) for _ in range(n_motifs)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")

    texture_request = overrides.get("texture")
    if texture_request in DEGENERATE_TEXTURES:
        ctx = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides={
                "grid_h": overrides.get("grid_h", 10 + sample_index % 4),
                "grid_w": overrides.get("grid_w", 10 + (sample_index * 3) % 4),
            },
        )
        return _draw_degenerate(str(texture_request), ctx, ctx.draw_rng("degenerate"))

    defaults = _effective_defaults(sample_index, overrides)
    orientation_profile = str(defaults.pop("orientation", "random"))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=defaults,
    )
    height = ctx.draw_int("grid_h", 9, 16)
    width = ctx.draw_int("grid_w", 9, 16)
    size = ctx.draw_int("block_size", 1, 3)
    n_motifs = ctx.draw_int("n_motifs", 1, 2)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    if 2 * size > height or 2 * size > width:
        raise ValueError(
            f"incompatible exact axes: block_size={size} motif does not fit in {height}x{width}"
        )

    band_key = difficulty if difficulty in {"easy", "medium", "hard"} else "all"
    rng = ctx.draw_rng(f"layout:{band_key}")
    orientations = _orientation_list(orientation_profile, n_motifs, rng)
    placements = _place_motifs(
        height, width, size, orientations, texture, rng
    )

    grid = full_grid(height, width, 0)
    for item in placements:
        for r, c in item["source"]:
            grid[r][c] = 3

    errors = self_check(grid)
    if errors:
        raise ValueError("generated grid failed self_check: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis in AXES:
        if axis in observed and observed[axis] != ctx.axis_value(axis):
            raise ValueError(
                f"internal exact-axis mismatch for {axis}: "
                f"requested/drawn {ctx.axis_value(axis)!r}, observed {observed[axis]!r}"
            )
    return grid


def _draw_degenerate(name: str, ctx, rng):
    """Build deterministic negative fixtures that self_check must reject."""
    height = ctx.draw_int("grid_h", 9, 16)
    width = ctx.draw_int("grid_w", 9, 16)
    grid = full_grid(height, width, 0)
    if name == "no_blocks":
        return grid
    if name == "single_block":
        size = rng.choice((1, 2, 3))
        r1 = rng.randint(0, height - size)
        c1 = rng.randint(0, width - size)
        fill_box(grid, r1, c1, r1 + size - 1, c1 + size - 1, 3)
        return grid
    for r in range(height):
        for c in range(width):
            grid[r][c] = 3
    return grid


def _components_8(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 3
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS_8:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _analyze_grid(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"], "motifs": []}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"], "motifs": []}
    height = len(grid)
    if not (9 <= height <= 16 and 9 <= width <= 16):
        errors.append(f"dimensions {height}x{width} are outside 9..16")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 3):
                errors.append(f"cell ({r},{c})={value!r}; input palette must be exactly 0/3")
                if len(errors) >= 8:
                    return {"errors": errors, "motifs": []}

    components = _components_8(grid)
    if not (1 <= len(components) <= 2):
        errors.append(f"expected 1..2 color-3 components, found {len(components)}")

    motifs: list[dict[str, Any]] = []
    all_source = set().union(*components) if components else set()
    for index, cells in enumerate(components):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(cols), max(cols)
        box_h, box_w = r2 - r1 + 1, c2 - c1 + 1
        if box_h != box_w or box_h % 2:
            errors.append(
                f"component {index} bbox is {box_h}x{box_w}; expected an even square 2N x 2N"
            )
            continue
        size = box_h // 2
        if not (1 <= size <= 3):
            errors.append(f"component {index} block size {size} is outside canonical 1..3")
            continue
        main = _input_cells(r1, c1, size, False)
        anti = _input_cells(r1, c1, size, True)
        if cells == main:
            is_anti = False
        elif cells == anti:
            is_anti = True
        else:
            errors.append(
                f"component {index} is not exactly two full opposite {size}x{size} quadrants"
            )
            continue
        item = _candidate(r1, c1, size, is_anti, height, width)
        if any(not group for group in item["visible_groups"]):
            errors.append(
                f"component {index} has a fully clipped endpoint; both added blocks must remain visible"
            )
        if item["visible"] & all_source:
            errors.append(f"component {index} projection would overwrite a source motif")
        motifs.append(item)

    sizes = {item["size"] for item in motifs}
    if len(sizes) > 1:
        errors.append(f"all motifs must share one observable block_size, found {sorted(sizes)}")
    for left in range(len(motifs)):
        for right in range(left + 1, len(motifs)):
            if motifs[left]["visible"] & motifs[right]["visible"]:
                errors.append(
                    f"motif projections {left} and {right} overlap; output ownership is ambiguous"
                )
    if motifs and not any(item["visible"] for item in motifs):
        errors.append("all projections are invisible; output would equal input")

    texture = None
    if motifs:
        texture = "clip_edge" if any(item["clipped"] for item in motifs) else "plain"
    return {
        "errors": errors,
        "motifs": motifs,
        "height": height,
        "width": width,
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Mutation-sensitive structural gate for the lawful teaching grammar."""
    del difficulty, meta
    return _analyze_grid(grid)["errors"]


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from a valid returned input grid."""
    analysis = _analyze_grid(grid)
    if analysis["errors"] or not analysis["motifs"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "block_size": analysis["motifs"][0]["size"],
        "n_motifs": len(analysis["motifs"]),
        "texture": analysis["texture"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Return [] for the narrow canonical 10x10, 0/3 input manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    if len(grid) != 10 or len(grid[0]) != 10:
        reasons.append(f"canonical inputs are 10x10, found {len(grid)}x{len(grid[0])}")
    palette = {value for row in grid for value in row}
    if palette != {0, 3}:
        reasons.append(f"canonical palette must be exactly {{0,3}}, found {sorted(palette)}")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests only; Racket remains authoritative."""
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("invalid motif grid: " + "; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for motif in analysis["motifs"]:
        for r, c in motif["visible"]:
            output[r][c] = 8
    return output


# ---------------------------------------------------------------------------
# Task-linked witnesses and lesson identifiability
# ---------------------------------------------------------------------------


def _analysis_ok(grid) -> dict[str, Any] | None:
    analysis = _analyze_grid(grid)
    return None if analysis["errors"] else analysis


def _witness_canonical_anchor(grid) -> bool:
    return strict_canonical_like(grid) == []


def _witness_size(size: int):
    def predicate(grid) -> bool:
        analysis = _analysis_ok(grid)
        return bool(analysis and analysis["motifs"][0]["size"] == size)

    return predicate


def _witness_orientation(is_anti: bool):
    def predicate(grid) -> bool:
        analysis = _analysis_ok(grid)
        return bool(
            analysis
            and any(item["is_anti"] == is_anti for item in analysis["motifs"])
        )

    return predicate


def _witness_multiple_mixed(grid) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and len(analysis["motifs"]) == 2
        and {item["is_anti"] for item in analysis["motifs"]} == {False, True}
    )


def _witness_clipping(grid) -> bool:
    analysis = _analysis_ok(grid)
    return bool(analysis and analysis["texture"] == "clip_edge")


def _witness_two_visible_ends(grid) -> bool:
    analysis = _analysis_ok(grid)
    return bool(
        analysis
        and all(all(group for group in item["visible_groups"]) for item in analysis["motifs"])
    )


SEMANTIC_WITNESSES = {
    "canonical_10x10_anchor": _witness_canonical_anchor,
    "block_size_1": _witness_size(1),
    "block_size_2": _witness_size(2),
    "block_size_3": _witness_size(3),
    "main_diagonal_source": _witness_orientation(False),
    "anti_diagonal_source": _witness_orientation(True),
    "two_motifs_with_mixed_orientations": _witness_multiple_mixed,
    "partial_edge_clipping": _witness_clipping,
    "both_projected_endpoints_visible": _witness_two_visible_ends,
}


def _paint_selected(
    grid: list[list[int]],
    *,
    only_first: bool = False,
    only_end: int | None = None,
    single_cell: bool = False,
    skip_clipped: bool = False,
    orientation_filter: bool | None = None,
    occupied_diagonal: bool = False,
) -> list[list[int]]:
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("invalid competitor input")
    output = deepcopy(grid)
    motifs = analysis["motifs"][:1] if only_first else analysis["motifs"]
    for motif in motifs:
        if skip_clipped and motif["clipped"]:
            continue
        if orientation_filter is not None and motif["is_anti"] != orientation_filter:
            continue
        groups = motif["visible_groups"]
        if occupied_diagonal:
            full = _projection_full_groups(
                motif["r1"], motif["c1"], motif["size"], not motif["is_anti"]
            )
            groups = tuple(
                _clip_cells(group, analysis["height"], analysis["width"])
                for group in full
            )
        selected = groups if only_end is None else (groups[only_end],)
        for group in selected:
            cells = group
            if single_cell and group:
                cells = {sorted(group)[len(group) // 2]}
            for r, c in cells:
                output[r][c] = 8
    return output


_LESSON_COMPETITORS = {
    "mark one cell per projected block": lambda grid: _paint_selected(grid, single_cell=True),
    "paint only one projected endpoint": lambda grid: _paint_selected(grid, only_end=0),
    "continue the occupied diagonal": lambda grid: _paint_selected(grid, occupied_diagonal=True),
    "process only the first component": lambda grid: _paint_selected(grid, only_first=True),
    "discard components whose projections clip": lambda grid: _paint_selected(grid, skip_clipped=True),
    "process only main-diagonal components": lambda grid: _paint_selected(grid, orientation_filter=False),
    "process only anti-diagonal components": lambda grid: _paint_selected(grid, orientation_filter=True),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        expected = rule_mirror(demo["input"])
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output does not match the perpendicular-block rule")
    query_answer = rule_mirror(query["input"])
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the perpendicular-block rule")

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )

    serialized = {repr(demo.get("output")) for demo in demos}
    if len(serialized) == 1 and repr(query_answer) not in serialized:
        reasons.append("a fixed-output memorization shortcut fits every demo")
    return reasons
