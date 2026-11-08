"""Generator for S15_H6: stamp one template at every 3/4 marker.

The color-2 component is interpreted relative to its bounding-box top-left.
Each color-3 and color-4 cell is an anchor for an identical cyan copy.  Copy
cells outside the canvas or on color-9 walls are discarded; overlapping copies
simply share the same cyan output cell.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26e0ef7cf48b"
TASK_ID = "26e0ef7cf48b"
VERSION = "3.0.0"
RULE_HASH = "4073f9cf50ec"

SUMMARY = (
    "A black grid contains one connected red (2) template, green (3) and "
    "yellow (4) one-cell anchors, and optional maroon (9) walls. Normalize "
    "the template to its bounding-box top-left and stamp that same shape in "
    "cyan (8) at every 3/4 anchor. Discard stamped cells that are outside the "
    "grid or lie on a 9. Overlapping copies merge. Sequential lessons cycle "
    "through wall blocking, boundary clipping, overlap, and an uncluttered "
    "base case so the query rule is demonstrated rather than hidden."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the only non-background input colors are 2, 3, 4, 9",
    "all color-2 cells form exactly one 4-connected template of 3-7 cells",
    "there is at least one color-3 anchor and at least one color-4 anchor",
    "every anchor has at least one surviving stamped cell",
    "each marker color contributes at least one surviving cell not supplied by the other color",
    "normal sample_index 0..2 demonstrations expose blocking, clipping, and overlap",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..24",
        "valid": "8..24",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 8..24",
        "valid": "8..24",
    },
    "template_size": {
        "type": "int",
        "default": "difficulty-aware 3..7",
        "valid": "3..7",
    },
    "n_markers_3": {
        "type": "int",
        "default": "difficulty-aware 1..5",
        "valid": "1..5",
    },
    "n_markers_4": {
        "type": "int",
        "default": "difficulty-aware 1..5",
        "valid": "1..5",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
# With the runner's usual 3 demonstrations + 1 query, all three decisive
# branches occur in demonstrations and the query is an ordinary base case.
_SAMPLE_SCHEDULE = ("blocked", "clipped", "overlap", "plain")


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            seen.add((row, col))
            queue = deque([(row, col)])
            cells: list[tuple[int, int]] = []
            while queue:
                cur_row, cur_col = queue.popleft()
                cells.append((cur_row, cur_col))
                for drow, dcol in _DIR4:
                    nxt = cur_row + drow, cur_col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            components.append(sorted(cells))
    return components


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _stamp_facts(grid, offsets):
    height, width = len(grid), len(grid[0])
    walls = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    }
    anchors = {
        color: [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
        for color in (3, 4)
    }
    per_anchor = []
    by_color = {3: set(), 4: set()}
    clipped_cells = 0
    blocked_cells = 0
    for color in (3, 4):
        for anchor in anchors[color]:
            raw = {
                (anchor[0] + drow, anchor[1] + dcol)
                for drow, dcol in offsets
            }
            in_bounds = {
                cell
                for cell in raw
                if 0 <= cell[0] < height and 0 <= cell[1] < width
            }
            surviving = in_bounds - walls
            clipped = len(raw - in_bounds)
            blocked = len(in_bounds & walls)
            clipped_cells += clipped
            blocked_cells += blocked
            by_color[color].update(surviving)
            per_anchor.append(
                {
                    "color": color,
                    "anchor": anchor,
                    "raw": raw,
                    "surviving": surviving,
                    "clipped": clipped,
                    "blocked": blocked,
                }
            )
    overlap_cells: set[tuple[int, int]] = set()
    for index, stamp in enumerate(per_anchor):
        for previous in per_anchor[:index]:
            overlap_cells.update(stamp["surviving"] & previous["surviving"])
    return {
        "anchors": anchors,
        "walls": walls,
        "per_anchor": per_anchor,
        "by_color": by_color,
        "clipped_cells": clipped_cells,
        "blocked_cells": blocked_cells,
        "overlap_cells": overlap_cells,
        "output_cells": by_color[3] | by_color[4],
    }


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"]}
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
    illegal = sorted({value for row in grid for value in row} - {0, 2, 3, 4, 9})
    if illegal:
        errors.append(f"illegal input colors: {illegal}")

    template_components = _components(grid, 2)
    if len(template_components) != 1:
        errors.append(
            f"expected exactly one 4-connected color-2 template, got {len(template_components)}"
        )
        return {"errors": errors}
    template = template_components[0]
    if not 3 <= len(template) <= 7:
        errors.append(f"template must contain 3-7 cells, got {len(template)}")
    offsets = _normalize(template)
    template_height = max(row for row, _ in offsets) + 1
    template_width = max(col for _, col in offsets) + 1

    facts = _stamp_facts(grid, offsets)
    counts = {color: len(facts["anchors"][color]) for color in (3, 4)}
    for color in (3, 4):
        if not 1 <= counts[color] <= 5:
            errors.append(f"expected 1-5 color-{color} anchors, got {counts[color]}")
    empty_anchors = [
        stamp["anchor"]
        for stamp in facts["per_anchor"]
        if not stamp["surviving"]
    ]
    if empty_anchors:
        errors.append(f"anchors with no surviving stamp cells: {empty_anchors}")
    if not facts["output_cells"]:
        errors.append("stamping would produce an empty output")
    for color, other in ((3, 4), (4, 3)):
        if facts["by_color"][color] and not (
            facts["by_color"][color] - facts["by_color"][other]
        ):
            errors.append(
                f"color-{color} anchors have no surviving contribution unique from color-{other}"
            )

    return {
        "errors": errors,
        "template": template,
        "offsets": offsets,
        "template_height": template_height,
        "template_width": template_width,
        **facts,
    }


def _meta_overrides(meta):
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, including override drift."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in observed and int(requested) != observed[name]:
            errors.append(
                f"override {name}={requested!r} realized as {observed[name]!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis directly from the rendered input."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(analysis["template"]),
        "n_markers_3": len(analysis["anchors"][3]),
        "n_markers_4": len(analysis["anchors"][4]),
    }


def rule_mirror(grid):
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid stamp scene: " + "; ".join(analysis["errors"]))
    output = full_grid(len(grid), len(grid[0]), 0)
    for row, col in analysis["output_cells"]:
        output[row][col] = 8
    return output


def semantic_signature(grid) -> dict[str, object]:
    """Linked branch observables used by the strict task-specific census."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"valid": False, "errors": tuple(analysis["errors"])}
    template_rows = [row for row, _ in analysis["template"]]
    template_cols = [col for _, col in analysis["template"]]
    row0, row1 = min(template_rows), max(template_rows)
    col0, col1 = min(template_cols), max(template_cols)
    height, width = len(grid), len(grid[0])
    center_row = (row0 + row1) / 2
    center_col = (col0 + col1) / 2
    return {
        "valid": True,
        "template_size": len(analysis["template"]),
        "template_height": analysis["template_height"],
        "template_width": analysis["template_width"],
        "origin_in_template": (0, 0) in analysis["offsets"],
        "n_markers_3": len(analysis["anchors"][3]),
        "n_markers_4": len(analysis["anchors"][4]),
        "wall_count": len(analysis["walls"]),
        "blocked": analysis["blocked_cells"] > 0,
        "clipped": analysis["clipped_cells"] > 0,
        "overlap": bool(analysis["overlap_cells"]),
        "output_cells": len(analysis["output_cells"]),
        "unique_3": len(analysis["by_color"][3] - analysis["by_color"][4]),
        "unique_4": len(analysis["by_color"][4] - analysis["by_color"][3]),
        "template_zone": (
            "top" if center_row < height / 3 else "bottom" if center_row >= 2 * height / 3 else "middle",
            "left" if center_col < width / 3 else "right" if center_col >= 2 * width / 3 else "center",
        ),
    }


def _grow_polyomino(rng, size: int) -> tuple[tuple[int, int], ...]:
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(tuple(cells))
            drow, dcol = rng.choice(_DIR4)
            cells.add((row + drow, col + dcol))
        offsets = _normalize(cells)
        # Avoid a single occupied row/column most of the time, but retain line
        # examples as lawful variation and a shortcut rebuttal.
        if size <= 3 or rng.random() < 0.20 or (
            max(row for row, _ in offsets) > 0
            and max(col for _, col in offsets) > 0
        ):
            return offsets
    return offsets


def _raw_footprint(anchor, offsets):
    return {(anchor[0] + row, anchor[1] + col) for row, col in offsets}


def _in_bounds(cell, height, width):
    return 0 <= cell[0] < height and 0 <= cell[1] < width


def _safe_positions(height, width, shape_height, shape_width):
    return [
        (row, col)
        for row in range(height - shape_height + 1)
        for col in range(width - shape_width + 1)
    ]


def _overlap_pair(rng, safe_positions, offsets):
    safe = set(safe_positions)
    differences = [
        (first[0] - second[0], first[1] - second[1])
        for first in offsets
        for second in offsets
        if first != second
    ]
    rng.shuffle(differences)
    bases = list(safe_positions)
    rng.shuffle(bases)
    for base in bases:
        for drow, dcol in differences:
            other = base[0] + drow, base[1] + dcol
            if other in safe and other != base:
                return base, other
    return None


def _clipped_position(rng, height, width, offsets):
    candidates = []
    for row in range(height):
        for col in range(width):
            raw = _raw_footprint((row, col), offsets)
            in_bounds = {cell for cell in raw if _in_bounds(cell, height, width)}
            if in_bounds and len(in_bounds) < len(raw):
                candidates.append((row, col))
    return rng.choice(candidates) if candidates else None


def _choose_anchors(
    rng,
    *,
    mode,
    height,
    width,
    offsets,
    shape_height,
    shape_width,
    n3,
    n4,
    forbidden,
):
    safe = [pos for pos in _safe_positions(height, width, shape_height, shape_width) if pos not in forbidden]
    all_positions = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in forbidden
    ]
    total = n3 + n4
    if len(safe) < total:
        return None

    anchors3: list[tuple[int, int]] = []
    anchors4: list[tuple[int, int]] = []
    used: set[tuple[int, int]] = set()

    if mode == "overlap":
        pair = _overlap_pair(rng, safe, offsets)
        if pair is None:
            return None
        anchors3.append(pair[0])
        anchors4.append(pair[1])
        used.update(pair)
    elif mode == "clipped":
        clipped = _clipped_position(rng, height, width, offsets)
        if clipped is None or clipped in forbidden:
            return None
        anchors3.append(clipped)
        used.add(clipped)
        candidate4 = [pos for pos in safe if pos not in used]
        if not candidate4:
            return None
        anchors4.append(rng.choice(candidate4))
        used.add(anchors4[-1])
    else:
        first3 = rng.choice(safe)
        anchors3.append(first3)
        used.add(first3)
        candidate4 = [pos for pos in safe if pos not in used]
        if not candidate4:
            return None
        first4 = rng.choice(candidate4)
        anchors4.append(first4)
        used.add(first4)

    remaining = [pos for pos in safe if pos not in used]
    rng.shuffle(remaining)
    while len(anchors3) < n3 and remaining:
        anchors3.append(remaining.pop())
    while len(anchors4) < n4 and remaining:
        anchors4.append(remaining.pop())
    if len(anchors3) != n3 or len(anchors4) != n4:
        return None
    return anchors3, anchors4


def _build_scene(ctx, mode, height, width, template_size, n3, n4):
    rng = ctx.draw_rng("layout")
    for _attempt in range(600):
        offsets = _grow_polyomino(rng, template_size)
        shape_height = max(row for row, _ in offsets) + 1
        shape_width = max(col for _, col in offsets) + 1
        if shape_height > height or shape_width > width:
            continue

        template_positions = _safe_positions(height, width, shape_height, shape_width)
        rng.shuffle(template_positions)
        for template_top in template_positions[:80]:
            template_cells = {
                (template_top[0] + row, template_top[1] + col)
                for row, col in offsets
            }
            anchors = _choose_anchors(
                rng,
                mode=mode,
                height=height,
                width=width,
                offsets=offsets,
                shape_height=shape_height,
                shape_width=shape_width,
                n3=n3,
                n4=n4,
                forbidden=template_cells,
            )
            if anchors is None:
                continue
            anchors3, anchors4 = anchors
            marker_cells = set(anchors3) | set(anchors4)
            grid = full_grid(height, width, 0)
            for row, col in template_cells:
                grid[row][col] = 2
            for row, col in anchors3:
                grid[row][col] = 3
            for row, col in anchors4:
                grid[row][col] = 4

            if mode == "blocked":
                candidates = []
                for anchor in anchors3 + anchors4:
                    for cell in _raw_footprint(anchor, offsets):
                        if (
                            _in_bounds(cell, height, width)
                            and cell not in template_cells
                            and cell not in marker_cells
                        ):
                            candidates.append(cell)
                rng.shuffle(candidates)
                if not candidates:
                    continue
                grid[candidates[0][0]][candidates[0][1]] = 9
                # Sometimes add an inert wall, matching the canonical examples
                # and preventing "delete every 9-adjacent cell" shortcuts.
                if rng.random() < 0.5:
                    inert = [
                        (row, col)
                        for row in range(height)
                        for col in range(width)
                        if grid[row][col] == 0
                        and (row, col) not in set(candidates)
                    ]
                    if inert:
                        row, col = rng.choice(inert)
                        grid[row][col] = 9

            analysis = _analyze(grid)
            if analysis["errors"]:
                continue
            signature = semantic_signature(grid)
            if mode == "blocked" and not signature["blocked"]:
                continue
            if mode == "clipped" and not signature["clipped"]:
                continue
            if mode == "overlap" and not signature["overlap"]:
                continue
            return grid
    raise ValueError(
        "could not realize a lawful stamp scene for "
        f"mode={mode}, grid={height}x{width}, template_size={template_size}, "
        f"markers=({n3},{n4})"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 8, 24)
    width = ctx.draw_int_diff("grid_w", 8, 24)
    template_size = ctx.draw_int_diff("template_size", 3, 7)
    n3 = ctx.draw_int_diff("n_markers_3", 1, 5)
    n4 = ctx.draw_int_diff("n_markers_4", 1, 5)
    mode = _SAMPLE_SCHEDULE[sample_index % len(_SAMPLE_SCHEDULE)]
    return _build_scene(ctx, mode, height, width, template_size, n3, n4)
