"""Generator for 3f2ed19e5882 — permute equal-width column blocks by headers.

The input grammar is the canonical one.  Row 0 partitions the full width into
K equal-width, distinctly colored source blocks.  Row 1 contains the same
colored runs in a non-identity destination order.  Rows 2 onward are the body.
The Racket oracle removes the two header rows and concatenates the source body
blocks in row-1 order.

Version 3.0.0 replaces a weak rewrite whose row-1 colors occupied one cell each,
whose ordinary draws could be identity/no-op examples, whose declared texture
modes were inert, and whose self_check did not verify the permutation grammar.
This version uses full canonical-style runs, pairwise-distinct connected body
blocks, exact observable axes, and a structural mutation-sensitive checker.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f2ed19e5882"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e1eea8f4abb8"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Rows 0 and 1 are equal-width colored block headers. Row 0 names the source "
    "body blocks; row 1 gives a non-identity permutation of those same blocks. "
    "Drop the headers and concatenate the source body blocks in row-1 order."
)

INVARIANTS = [
    "row 0 fully partitions the width into 2..6 equal-width runs of distinct nonzero colors",
    "row 1 fully partitions the width into the same runs and colors in a non-identity order",
    "every body block is nonempty, connected to its header, and pairwise distinct from every other body block",
    "reordering by row 1 changes the body, so ordinary lessons never hide the operation as an identity",
]

AXES = {
    "n_blocks": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "2..6",
        "doc": "Number of equal-width source/destination blocks.",
    },
    "body_rows": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "3..9",
        "doc": "Number of rows below the two header rows.",
    },
    "block_w": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "2..5",
        "doc": "Exact common width of every source and destination header run.",
    },
}

# There are no texture escape hatches: ordinary and override draws share the
# same lawful semantic grammar.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLORS = tuple(range(1, 10))
_BANDS = {
    "easy": {
        "n_blocks": (2, 3),
        "body_rows": (3, 4),
        "block_w": (2, 3),
        "body_palette": (4, 6),
        "density": (0.34, 0.48),
    },
    "medium": {
        "n_blocks": (3, 4),
        "body_rows": (4, 6),
        "block_w": (2, 4),
        "body_palette": (6, 8),
        "density": (0.40, 0.54),
    },
    "hard": {
        "n_blocks": (4, 6),
        "body_rows": (5, 9),
        "block_w": (2, 5),
        "body_palette": (8, 9),
        "density": (0.46, 0.60),
    },
}
_VALID_BOUNDS = {
    "n_blocks": (2, 6),
    "body_rows": (3, 9),
    "block_w": (2, 5),
}


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid must have at least one column"]
    width = len(grid[0])
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    return (None, errors) if errors else (converted, [])


def _runs(row: Iterable[int]) -> list[tuple[int, int, int]]:
    values = list(row)
    out: list[tuple[int, int, int]] = []
    start = 0
    while start < len(values):
        color = values[start]
        end = start + 1
        while end < len(values) and values[end] == color:
            end += 1
        out.append((color, start, end))
        start = end
    return out


def _block_matrix(
    grid: list[list[int]], start: int, width: int
) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row[start : start + width]) for row in grid[2:])


def _reordered_body(
    grid: list[list[int]],
    source_runs: list[tuple[int, int, int]],
    destination_runs: list[tuple[int, int, int]],
) -> list[list[int]]:
    source_by_color = {
        color: (start, end) for color, start, end in source_runs
    }
    output: list[list[int]] = []
    for row in grid[2:]:
        out_row: list[int] = []
        for color, _start, _end in destination_runs:
            src_start, src_end = source_by_color[color]
            out_row.extend(row[src_start:src_end])
        output.append(out_row)
    return output


def _nonzero_components(grid: list[list[int]]) -> int:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = 0
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            components += 1
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            while queue:
                row, col = queue.popleft()
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + drow, col + dcol
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] != 0
                        and (next_row, next_col) not in seen
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {
        "n_blocks": None,
        "body_rows": None,
        "block_w": None,
        "source_colors": (),
        "destination_colors": (),
        "permutation": (),
        "moved_positions": 0,
        "distinct_body_blocks": 0,
        "output_changes": False,
        "palette_size": 0,
        "nonzero_components": 0,
    }
    if converted is None:
        return {"errors": errors, "facts": facts}

    height, width = len(converted), len(converted[0])
    if not 5 <= height <= 11:
        errors.append("grid height must be 5..11 (two headers plus 3..9 body rows)")
    if not 4 <= width <= 30:
        errors.append("grid width must be 4..30")
    if height < 3:
        return {"errors": errors, "facts": facts}

    source_runs = _runs(converted[0])
    destination_runs = _runs(converted[1])
    source_colors = tuple(color for color, _start, _end in source_runs)
    destination_colors = tuple(color for color, _start, _end in destination_runs)
    source_widths = tuple(end - start for _color, start, end in source_runs)
    destination_widths = tuple(end - start for _color, start, end in destination_runs)

    facts["n_blocks"] = len(source_runs)
    facts["body_rows"] = height - 2
    facts["source_colors"] = source_colors
    facts["destination_colors"] = destination_colors
    facts["palette_size"] = len({value for row in converted for value in row})
    facts["nonzero_components"] = _nonzero_components(converted)

    if not 2 <= len(source_runs) <= 6:
        errors.append(f"row 0 must contain 2..6 runs; got {len(source_runs)}")
    if any(color == 0 for color in source_colors):
        errors.append("row 0 must be fully covered by nonzero source runs")
    if len(set(source_colors)) != len(source_colors):
        errors.append("row 0 source-run colors must be distinct")
    if not source_widths or len(set(source_widths)) != 1:
        errors.append("all row-0 source runs must have one common width")
    else:
        facts["block_w"] = source_widths[0]
        if not 2 <= source_widths[0] <= 5:
            errors.append("common block width must be 2..5")

    if len(destination_runs) != len(source_runs):
        errors.append("row 1 must contain exactly one run for every source block")
    if any(color == 0 for color in destination_colors):
        errors.append("row 1 must be fully covered by nonzero destination runs")
    if len(set(destination_colors)) != len(destination_colors):
        errors.append("row 1 destination-run colors must be distinct")
    if set(destination_colors) != set(source_colors):
        errors.append("row 1 must use exactly the row-0 source colors")
    if destination_widths != source_widths:
        errors.append("row-1 runs must preserve the common source block width")
    if destination_colors == source_colors and source_colors:
        errors.append("destination order must be non-identity")

    if not errors:
        source_index = {color: index for index, color in enumerate(source_colors)}
        permutation = tuple(source_index[color] for color in destination_colors)
        facts["permutation"] = permutation
        facts["moved_positions"] = sum(
            index != source for index, source in enumerate(permutation)
        )

        block_width = source_widths[0]
        body_blocks = [
            _block_matrix(converted, index * block_width, block_width)
            for index in range(len(source_runs))
        ]
        facts["distinct_body_blocks"] = len(set(body_blocks))
        for index, block in enumerate(body_blocks):
            if not any(value != 0 for row in block for value in row):
                errors.append(f"body block {index} must contain nonzero content")
        if len(set(body_blocks)) != len(body_blocks):
            errors.append("body blocks must be pairwise distinct")

        body_palette = {value for row in converted[2:] for value in row}
        if 0 not in body_palette:
            errors.append("body must contain background zeros")
        if len(body_palette - {0}) < 2:
            errors.append("body must contain at least two nonzero colors")

        body = [row[:] for row in converted[2:]]
        reordered = _reordered_body(converted, source_runs, destination_runs)
        facts["output_changes"] = reordered != body
        if reordered == body:
            errors.append("the destination order must visibly change the body")

    return {"errors": errors, "facts": facts}


def self_check(
    grid: Any, *, difficulty: Any = None, meta: Any = None
) -> list[str]:
    """Validate the complete canonical input grammar and visible rule firing."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover exact axes plus task-linked permutation observables from a grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "n_blocks": facts["n_blocks"],
        "body_rows": facts["body_rows"],
        "block_w": facts["block_w"],
        "permutation": facts["permutation"],
        "moved_positions": facts["moved_positions"],
        "distinct_body_blocks": facts["distinct_body_blocks"],
        "output_changes": facts["output_changes"],
        "palette_size": facts["palette_size"],
        "nonzero_components": facts["nonzero_components"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror of the canonical rule; Racket is authoritative.

    Drop both header rows and concatenate the source body blocks (keyed by the
    row-0 runs) in the row-1 destination order.
    """
    converted, errors = _coerce_grid(grid)
    if converted is None:
        raise ValueError("; ".join(errors))
    source_runs = [run for run in _runs(converted[0]) if run[0] != 0]
    destination_runs = [run for run in _runs(converted[1]) if run[0] != 0]
    return _reordered_body(converted, source_runs, destination_runs)


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked strict manifold check (SEMANTIC_GATE_CONTRACT hook 1).

    The full teaching grammar (equal-width nonzero header runs, matching color
    sets, non-identity order, distinct nonempty body blocks, visible change)
    plus one reviewer-level constraint: no body block may be a solid uniform
    rectangle, because a solid block reduces block identity to a histogram
    shortcut.  All three canonical inputs satisfy this.
    """
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    facts = analysis["facts"]
    block_width = facts["block_w"]
    converted, _ = _coerce_grid(grid)
    for index in range(facts["n_blocks"]):
        block = _block_matrix(converted, index * block_width, block_width)
        if len({value for row in block for value in row}) < 2:
            reasons.append(
                f"body block {index} is a solid uniform rectangle "
                "(block identity degenerates to a histogram)"
            )
    return reasons


def _header_runs_ok(grid: Any) -> tuple[list, list] | None:
    converted, errors = _coerce_grid(grid)
    if converted is None or len(converted) < 3:
        return None
    source_runs = _runs(converted[0])
    destination_runs = _runs(converted[1])
    return source_runs, destination_runs


def _witness_equal_width_full_runs(grid: Any) -> bool:
    """Both header rows fully partition the width into nonzero runs of one
    common width — the canonical run grammar (the pre-repair generator used
    one-cell row-1 markers instead)."""
    parsed = _header_runs_ok(grid)
    if parsed is None:
        return False
    source_runs, destination_runs = parsed
    widths = {end - start for _color, start, end in source_runs}
    widths |= {end - start for _color, start, end in destination_runs}
    colors = [color for color, _s, _e in source_runs] + [
        color for color, _s, _e in destination_runs
    ]
    return len(widths) == 1 and all(color != 0 for color in colors)


def _facts_or_none(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis["facts"]


def _witness_non_identity_order(grid: Any) -> bool:
    facts = _facts_or_none(grid)
    return facts is not None and facts["moved_positions"] >= 2


def _witness_output_changes(grid: Any) -> bool:
    facts = _facts_or_none(grid)
    return facts is not None and bool(facts["output_changes"])


def _witness_reversed_order(grid: Any) -> bool:
    """The destination order is the exact reversal of the source order — one
    of the scheduled permutation classes, witnessing order variety beyond a
    single rotation."""
    facts = _facts_or_none(grid)
    if facts is None:
        return False
    permutation = facts["permutation"]
    return permutation == tuple(reversed(range(len(permutation))))


SEMANTIC_WITNESSES = {
    "equal_width_full_header_runs": _witness_equal_width_full_runs,
    "non_identity_destination_order": _witness_non_identity_order,
    "output_visibly_changes": _witness_output_changes,
    "reversed_destination_order": _witness_reversed_order,
}


def _order_competitor(order_fn):
    """Build a competitor that ignores row 1 and uses its own block order."""

    def _apply(grid: list[list[int]]) -> list[list[int]]:
        converted, errors = _coerce_grid(grid)
        if converted is None:
            raise ValueError("; ".join(errors))
        source_runs = [run for run in _runs(converted[0]) if run[0] != 0]
        fake_destination = order_fn(source_runs)
        return _reordered_body(converted, source_runs, fake_destination)

    return _apply


_COMPETING_RULES = {
    "copy_body_unchanged": _order_competitor(lambda runs: list(runs)),
    "always_reverse_blocks": _order_competitor(lambda runs: list(reversed(runs))),
    "always_rotate_left": _order_competitor(lambda runs: runs[1:] + runs[:1]),
    "always_rotate_right": _order_competitor(lambda runs: runs[-1:] + runs[:-1]),
    "sort_blocks_by_color": _order_competitor(
        lambda runs: sorted(runs, key=lambda run: run[0])
    ),
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Demos must pin the row-1-driven order against order shortcuts
    (SEMANTIC_GATE_CONTRACT hook 3).  Also catches the degenerate identity
    lesson directly: a demo whose destination order equals its source order
    teaches nothing."""
    reasons: list[str] = []
    episodes = list(demos) + [query]
    labels = [f"demo {i}" for i in range(len(demos))] + ["query"]
    parsed: list[list[list[int]]] = []
    for label, episode in zip(labels, episodes):
        converted, errors = _coerce_grid(episode.get("input"))
        if converted is None or len(converted) < 3:
            reasons.append(f"{label}: malformed input: {'; '.join(errors) or 'too few rows'}")
            continue
        source_colors = [color for color, _s, _e in _runs(converted[0]) if color != 0]
        destination_colors = [
            color for color, _s, _e in _runs(converted[1]) if color != 0
        ]
        if source_colors == destination_colors:
            reasons.append(
                f"{label}: identity destination order — a degenerate lesson"
            )
        parsed.append(converted)
    if reasons:
        return reasons
    for i, demo in enumerate(demos):
        if demo.get("output") != rule_mirror(demo["input"]):
            reasons.append(f"demo {i}: output does not match the task rule")
    if reasons:
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query: provided output does not match the task rule")
    for name, competitor in _COMPETING_RULES.items():
        if all(
            competitor(demo["input"]) == demo["output"] for demo in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a "
                "different query answer"
            )
    return reasons


def _draw_axis(ctx: Any, name: str, default_bounds: tuple[int, int]) -> int:
    valid_bounds = _VALID_BOUNDS[name]
    bounds = (
        valid_bounds
        if name in ctx.overrides and ctx.overrides[name] is not None
        else default_bounds
    )
    return ctx.draw_int(name, bounds[0], bounds[1])


def _destination_order(colors: list[int], sample_index: int, rng: Any) -> list[int]:
    """Use a short semantic schedule, then a random non-identity permutation."""
    count = len(colors)
    mode = sample_index % 4
    if mode == 0:
        return colors[1:] + colors[:1]
    if mode == 1:
        return colors[-1:] + colors[:-1]
    if mode == 2:
        return list(reversed(colors))
    order = colors[:]
    rng.shuffle(order)
    if order == colors:
        shift = 1 + rng.randrange(count - 1)
        order = colors[shift:] + colors[:shift]
    return order


def _connected_cells(
    rows: int,
    cols: int,
    target: int,
    start_col: int,
    rng: Any,
) -> list[tuple[int, int]]:
    cells = {(0, start_col)}
    while len(cells) < target:
        boundary: list[tuple[int, int]] = []
        for row, col in cells:
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                next_cell = row + drow, col + dcol
                if (
                    0 <= next_cell[0] < rows
                    and 0 <= next_cell[1] < cols
                    and next_cell not in cells
                ):
                    boundary.append(next_cell)
        if not boundary:
            break
        cells.add(rng.choice(boundary))
    return sorted(cells)


def _body_blocks(
    ctx: Any,
    *,
    n_blocks: int,
    body_rows: int,
    block_w: int,
    band: str,
) -> list[list[list[int]]]:
    profile = _BANDS[band]
    palette_rng = ctx.draw_rng("body_palette")
    palette_lo, palette_hi = profile["body_palette"]
    palette_min = max(n_blocks + 1, palette_lo)
    palette_max = min(9, max(palette_min, palette_hi))
    palette_count = palette_rng.randint(palette_min, palette_max)
    body_palette = palette_rng.sample(list(_COLORS), palette_count)
    anchors = body_palette[:n_blocks]
    fillers = body_palette[n_blocks:]

    density_rng = ctx.draw_rng("body_density")
    density_lo, density_hi = profile["density"]
    density = density_rng.uniform(density_lo, density_hi)
    area = body_rows * block_w
    target = max(2, min(area - 1, round(area * density)))

    blocks: list[list[list[int]]] = []
    filler_cursor = 0
    for block_index in range(n_blocks):
        rng = ctx.draw_rng(f"body_block:{block_index}")
        start_col = block_index % block_w
        occupied = _connected_cells(
            body_rows, block_w, target, start_col, rng
        )
        block = full_grid(body_rows, block_w, 0)
        anchor_cell = (0, start_col)
        block[anchor_cell[0]][anchor_cell[1]] = anchors[block_index]
        for row, col in occupied:
            if (row, col) == anchor_cell:
                continue
            block[row][col] = fillers[filler_cursor % len(fillers)]
            filler_cursor += 1
        blocks.append(block)
    return blocks


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = "medium" if difficulty is None else difficulty
    if band not in _BANDS:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = _BANDS[band]
    n_blocks = _draw_axis(ctx, "n_blocks", profile["n_blocks"])
    body_rows = _draw_axis(ctx, "body_rows", profile["body_rows"])
    block_w = _draw_axis(ctx, "block_w", profile["block_w"])

    legend_rng = ctx.draw_rng("legend_colors")
    source_colors = legend_rng.sample(list(_COLORS), n_blocks)
    destination_colors = _destination_order(
        source_colors,
        sample_index,
        ctx.draw_rng("destination_order"),
    )
    blocks = _body_blocks(
        ctx,
        n_blocks=n_blocks,
        body_rows=body_rows,
        block_w=block_w,
        band=band,
    )

    width = n_blocks * block_w
    grid = full_grid(2 + body_rows, width, 0)
    for block_index, color in enumerate(source_colors):
        start = block_index * block_w
        for col in range(start, start + block_w):
            grid[0][col] = color
    for block_index, color in enumerate(destination_colors):
        start = block_index * block_w
        for col in range(start, start + block_w):
            grid[1][col] = color
    for block_index, block in enumerate(blocks):
        start = block_index * block_w
        for row in range(body_rows):
            grid[row + 2][start : start + block_w] = block[row][:]

    findings = self_check(grid)
    if findings:  # construction invariant: fail loudly, never return a weak lesson
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    return grid
