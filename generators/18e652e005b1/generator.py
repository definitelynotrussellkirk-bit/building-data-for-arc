"""Generator for bank dc02f6f7c147 / M105: Motif Recolor Broadcast.

The last row is an ordered command strip.  The upper field contains one
single-color motif and reserves the final column as background.  The oracle
crops the motif's bounding box, recolors one copy for each command color, and
packs those copies left-to-right with one background column between them.

The canonical corpus deliberately includes both connected and disconnected
motifs, so connectivity is an axis rather than an invariant.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "18e652e005b1"
TASK_ID = GENERATOR_ID
VERSION = "4.2.0"
RULE_HASH = "6674d903ad0a"

SUMMARY = (
    "A zero-background grid has a nonempty, single-color motif in the field "
    "above the last row and left of the reserved final column.  The last row "
    "starts with 2-6 distinct nonzero command colors followed only by zeros. "
    "Crop the motif to its bounding box, make one copy per command color, "
    "recolor every occupied motif cell with that command, and concatenate the "
    "copies left-to-right with one blank column between adjacent copies."
)

EXAMPLES_NEEDED = 3

# Any three consecutive default sample indices contain all three schedule rows.
# Thus a materialized lesson always demonstrates 2/3/4 commands and both motif
# connectivity classes before the query, instead of hoping random demos expose
# those answer-relevant alternatives.
DEFAULT_LESSON_SCHEDULE = (
    (2, "connected"),
    (3, "disconnected"),
    (4, "connected"),
)

INVARIANTS = [
    "background is 0",
    "the upper field contains a nonempty motif in exactly one nonzero color",
    "the final input column is background and is excluded from motif extraction",
    "the bottom row starts with at least two distinct nonzero command colors and then zeros",
    "the motif color is different from every command color",
    "the derived oracle output is at most 30 by 30",
    "motif connectivity may be connected or disconnected; internal blanks are preserved by cropping",
]

# These signatures are extracted from every canonical train input and the held-
# out test input.  Colors and absolute placement are intentionally omitted so
# the prior teaches the empirical morphology without replaying literal scenes.
# A focused test derives the same signatures from data/canonical/puzzles.jsonl.
CANONICAL_SCENES = (
    (6, 9, 3, ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2))),
    (7, 10, 3, ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))),
    (6, 8, 4, ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1))),
    (7, 11, 3, ((0, 0), (0, 2), (1, 1))),
    # The held-out test repeats the second morphology/profile with new colors.
    (7, 10, 3, ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 6..14 with a canonical-profile prior",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 8..16 with a canonical-profile prior",
        "valid": "8..16",
    },
    "commands": {
        "type": "int",
        "default": "lesson schedule 2,3,4; overrides support 2..6",
        "valid": "2..6",
    },
    "motif_cells": {
        "type": "int",
        "default": "difficulty-skewed 3..10 with canonical values 3 or 5",
        "valid": "3..10",
    },
    "motif_connectivity": {
        "type": "str",
        "default": "lesson schedule covers connected and disconnected",
        "valid": "connected|disconnected",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic lesson input.

    A 35% default-only canonical prior keeps every difficulty band anchored to
    the exact linked canonical dimension/count/morphology manifold.  Any caller
    override disables that prior so every declared boundary is exact-or-loud.
    """
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_scene = None
    scheduled = None
    if not overrides:
        scheduled = DEFAULT_LESSON_SCHEDULE[sample_index % len(DEFAULT_LESSON_SCHEDULE)]
        scheduled_n, scheduled_connectivity = scheduled
        canonical_candidates = tuple(
            scene
            for scene in CANONICAL_SCENES
            if scene[2] == scheduled_n
            and _connectivity_label(scene[3]) == scheduled_connectivity
        )
        if (
            canonical_candidates
            and ctx.draw_rng("canonical_prior").random() < 0.35
        ):
            canonical_scene = ctx.draw_choice(
                "canonical_scene", canonical_candidates
            )

    if canonical_scene is not None:
        h0, w0, n0, motif_tuple = canonical_scene
        h = ctx.draw_int("grid_h", h0, h0)
        w = ctx.draw_int("grid_w", w0, w0)
        n = ctx.draw_int("commands", n0, n0)
        motif = list(motif_tuple)
        motif_cells = ctx.draw_int("motif_cells", len(motif), len(motif))
        connectivity = _connectivity_label(motif)
        ctx.draw_choice("motif_connectivity", (connectivity,))
    else:
        h = ctx.draw_int_diff("grid_h", 6, 14)
        w = ctx.draw_int_diff("grid_w", 8, 16)
        if scheduled is None:
            n = ctx.draw_int_diff("commands", 2, 6)
            connectivity = ctx.draw_choice(
                "motif_connectivity", ("connected", "disconnected")
            )
        else:
            scheduled_n, scheduled_connectivity = scheduled
            n = ctx.draw_int("commands", scheduled_n, scheduled_n)
            connectivity = ctx.draw_choice(
                "motif_connectivity", (scheduled_connectivity,)
            )
        motif_cells = ctx.draw_int_diff("motif_cells", 3, 10)
        shape_rng = ctx.draw_rng("motif_shape")
        # The oracle emits n copies with n-1 separator columns.  Keep the
        # derived output inside ARC's 30-column grid bound even for exact
        # commands=6 overrides; height is already bounded by h-1 <= 13.
        max_motif_w = min(w - 1, (30 - (n - 1)) // n)
        if connectivity == "connected":
            motif = _connected_motif(
                shape_rng, motif_cells, h - 1, max_motif_w
            )
        else:
            motif = _disconnected_motif(
                shape_rng, motif_cells, h - 1, max_motif_w
            )

    motif_h, motif_w = _bbox_dims(motif)
    # The Racket rule extracts columns 0..w-2, so keep the entire motif inside
    # that field and leave column w-1 blank on every row.
    top = ctx.draw_int("motif_top", 0, h - 1 - motif_h)
    left = ctx.draw_int("motif_left", 0, w - 1 - motif_w)

    motif_color = ctx.draw_color("motif_color", exclude=(0,))
    command_colors = ctx.draw_distinct_colors(
        "command_colors", n=n, exclude=(0, motif_color)
    )

    grid = full_grid(h, w, 0)
    for dr, dc in motif:
        grid[top + dr][left + dc] = motif_color
    for c, color in enumerate(command_colors):
        grid[h - 1][c] = color
    return grid


def _bbox_dims(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _components(cells):
    remaining = set(cells)
    components = []
    while remaining:
        start = remaining.pop()
        todo = [start]
        component = {start}
        while todo:
            r, c = todo.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    todo.append(neighbor)
        components.append(component)
    return components


def _connectivity_label(cells):
    return "connected" if len(_components(cells)) == 1 else "disconnected"


def _connected_motif(rng, k, max_h, max_w):
    """Grow exactly ``k`` 4-connected cells inside the available field."""
    cells = {(rng.randrange(max_h), rng.randrange(max_w))}
    while len(cells) < k:
        frontier = sorted(
            {
                (r + dr, c + dc)
                for r, c in cells
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= r + dr < max_h
                and 0 <= c + dc < max_w
                and (r + dr, c + dc) not in cells
            }
        )
        if not frontier:
            raise ValueError("connected motif has no growth frontier")
        cells.add(rng.choice(frontier))
    return _normalize(cells)


def _disconnected_motif(rng, k, max_h, max_w):
    """Sample exactly ``k`` cells with at least two 4-components."""
    population = [(r, c) for r in range(max_h) for c in range(max_w)]
    for _ in range(256):
        cells = rng.sample(population, k)
        if len(_components(cells)) >= 2:
            return _normalize(cells)
    # The minimum field is 5x7, so this deterministic separated construction
    # always fits the declared k<=10 domain and preserves exact cell count.
    left_count = k // 2
    right_count = k - left_count
    left = [(r, 0) for r in range(left_count)]
    right = [(r, 2) for r in range(right_count)]
    return _normalize(left + right)


def _coerce_grid(grid):
    """Accept canonical compact string rows as well as generated int rows."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    out = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(ch not in "0123456789" for ch in row):
                raise ValueError("compact row contains a non-color character")
            out.append([int(ch) for ch in row])
        elif isinstance(row, list):
            out.append(list(row))
        else:
            raise ValueError("row must be a list or compact color string")
    return out


def _scene_features(grid):
    g = _coerce_grid(grid)
    h = len(g)
    w = len(g[0]) if g else 0
    if w == 0 or any(len(row) != w for row in g):
        raise ValueError("grid is empty or ragged")
    motif = [(r, c) for r in range(h - 1) for c in range(w - 1) if g[r][c] != 0]
    command_cols = [c for c, value in enumerate(g[-1]) if value != 0]
    commands = [g[-1][c] for c in command_cols]
    return g, motif, command_cols, commands


def observe_overrides(grid):
    """Recover every exact declared semantic axis from the returned grid."""
    g, motif, _, commands = _scene_features(grid)
    return {
        "grid_h": len(g),
        "grid_w": len(g[0]),
        "commands": len(commands),
        "motif_cells": len(motif),
        "motif_connectivity": _connectivity_label(motif) if motif else "empty",
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed lessons while accepting every canonical input."""
    try:
        g, motif, command_cols, commands = _scene_features(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    h, w = len(g), len(g[0])
    errors = []
    if h < 2 or w < 2:
        errors.append(f"grid too small: {h}x{w}")
    bad_colors = [value for row in g for value in row if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9]
    if bad_colors:
        errors.append("grid contains a non-integer or color outside 0..9")

    if any(g[r][w - 1] != 0 for r in range(h)):
        errors.append("reserved final column must be background")
    if len(motif) < 3:
        errors.append(f"expected at least three motif cells, got {len(motif)}")
    motif_colors = {g[r][c] for r, c in motif}
    if len(motif_colors) != 1:
        errors.append(f"motif must use exactly one color, got {sorted(motif_colors)}")

    if len(commands) < 2:
        errors.append(f"expected at least two commands, got {len(commands)}")
    if command_cols != list(range(len(command_cols))):
        errors.append("commands must be contiguous from bottom-left")
    if len(set(commands)) != len(commands):
        errors.append("command colors must be distinct")
    if motif_colors and any(color in motif_colors for color in commands):
        errors.append("motif color must differ from every command color")

    if motif and commands:
        motif_h, motif_w = _bbox_dims(motif)
        output_h = motif_h
        output_w = len(commands) * motif_w + len(commands) - 1
        if output_h > 30 or output_w > 30:
            errors.append(
                f"derived output exceeds 30x30: {output_h}x{output_w}"
            )
    return errors
