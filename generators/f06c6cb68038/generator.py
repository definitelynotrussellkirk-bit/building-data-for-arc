"""Generator for ARC task 88207623 / canonical id f06c6cb68038.

Each setup has a vertical color-2 guide, a color-4 pattern on one side, and one
colored marker on the opposite side.  The marker is already one reflected cell
of that pattern.  Complete the reflection across the guide, painting every
reflected color-4 cell with that setup's marker color.

Canonical scenes can contain several independent setups whose guide row spans
touch or overlap.  Marker-to-guide ownership is therefore determined by the
same nearest-guide score used by the selected Racket rule; row separation is a
curriculum choice, not part of the authority-valid input grammar.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f06c6cb68038"
TASK_ID = GENERATOR_ID
VERSION = "4.2.0"
RULE_HASH = "e962fd415d0a"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "A 0-background grid contains multiple vertical color-2 guides.  Each guide "
    "has a color-4 pattern on one side and a differently colored marker on the "
    "opposite side; the marker occupies one location obtained by reflecting a "
    "pattern cell across that guide.  Reflect every far-side 4-cell across its "
    "matched guide and paint the reflected cells with that marker's color."
)

INVARIANTS = [
    "background is 0 and guides are contiguous vertical color-2 components",
    "each guide has exactly one marker matched by the selected rule's nearest-guide score",
    "each marker is opposite its guide from the relevant color-4 pattern",
    "each marker already occupies the reflection of one far-side color-4 cell",
    "every color-4 cell participates in at least one matched guide reflection",
    "in-bounds reflected destinations are blank except for the marker seed; clipped cross-setup cells are allowed",
]

_MARKER_COLORS = (1, 3, 5, 6, 7, 8, 9)

# Only expose a control that the returned grid can recover exactly.  Grid size,
# marker palette, and orientation still vary, but they are latent curriculum
# choices rather than override promises.
AXES = {
    "n_setups": {"type": "int", "default": "difficulty schedule 2..4", "valid": "1..4"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _components_of_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps: list[list[tuple[int, int]]] = []
    for r0 in range(h):
        for c0 in range(w):
            if seen[r0][c0] or grid[r0][c0] != color:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _run_score(line: dict[str, int], mr: int, mc: int) -> int:
    row_gap = 0 if line["r1"] <= mr <= line["r2"] else min(
        abs(mr - line["r1"]), abs(mr - line["r2"])
    )
    return abs(mc - line["col"]) + 10 * row_gap


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of rows"], "setups": []}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"], "setups": []}
    h = len(grid)
    bad_values = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 2, 4, *_MARKER_COLORS}
        },
        key=repr,
    )
    if bad_values:
        errors.append(f"unexpected colors/values {bad_values}")

    raw_lines = _components_of_color(grid, 2)
    lines: list[dict[str, int]] = []
    if not raw_lines:
        errors.append("no color-2 guide line")
    for cells in raw_lines:
        cols = {c for _, c in cells}
        rows = sorted(r for r, _ in cells)
        if len(cols) != 1:
            errors.append("a color-2 guide component is not vertical")
            continue
        if rows != list(range(rows[0], rows[-1] + 1)):
            errors.append("a color-2 guide line is not contiguous")
            continue
        if len(rows) < 2:
            errors.append("a color-2 guide line is shorter than 2 cells")
            continue
        lines.append({"col": next(iter(cols)), "r1": rows[0], "r2": rows[-1]})

    markers = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 2, 4)
    ]
    if len(markers) != len(lines):
        errors.append(f"expected one marker per guide line; markers={len(markers)} lines={len(lines)}")
    if not lines or not markers:
        return {"errors": errors, "setups": [], "lines": lines, "markers": markers}

    assigned: dict[int, list[tuple[int, int, int]]] = {i: [] for i in range(len(lines))}
    marker_best: list[tuple[int, int, int, int]] = []
    for mr, mc, color in markers:
        scores = [_run_score(line, mr, mc) for line in lines]
        best = min(scores)
        winners = [i for i, score in enumerate(scores) if score == best]
        if len(winners) != 1:
            errors.append(f"marker at ({mr},{mc}) has tied nearest guides")
            continue
        idx = winners[0]
        assigned[idx].append((mr, mc, color))
        marker_best.append((mr, mc, color, idx))

    for idx, line_markers in assigned.items():
        if len(line_markers) != 1:
            line = lines[idx]
            errors.append(
                f"guide at col {line['col']} rows {line['r1']}..{line['r2']} "
                f"has {len(line_markers)} nearest markers"
            )

    setups: list[dict[str, Any]] = []
    covered_4: set[tuple[int, int]] = set()
    for idx, line in enumerate(lines):
        if len(assigned[idx]) != 1:
            continue
        mr, mc, color = assigned[idx][0]
        linec = line["col"]
        if mc == linec:
            errors.append("marker lies on guide line")
            continue
        if not line["r1"] <= mr <= line["r2"]:
            errors.append(f"marker at ({mr},{mc}) lies outside its guide row span")
            continue
        marker_left = mc < linec
        anchor_c = 2 * linec - mc
        if not (0 <= anchor_c < w) or grid[mr][anchor_c] != 4:
            errors.append(
                f"marker at ({mr},{mc}) is not the reflection of a far-side color-4 cell"
            )

        pattern: list[tuple[int, int]] = []
        for r in range(line["r1"], line["r2"] + 1):
            for c in range(w):
                if grid[r][c] != 4:
                    continue
                on_far_side = c > linec if marker_left else c < linec
                if not on_far_side:
                    continue
                mirror_c = 2 * linec - c
                # The selected rule clips out-of-bounds reflections.  Canonical
                # overlapping row spans expose unrelated 4-cells to another
                # guide; those cross-setup candidates can legitimately clip.
                if not (0 <= mirror_c < w):
                    continue
                target = grid[r][mirror_c]
                if target != 0 and not (r == mr and mirror_c == mc and target == color):
                    errors.append(
                        f"reflection of color-4 cell ({r},{c}) lands on occupied cell ({r},{mirror_c})"
                    )
                    continue
                pattern.append((r, c))
                covered_4.add((r, c))
        if not pattern:
            errors.append(f"guide at col {linec} has no far-side color-4 pattern")
        setups.append(
            {
                "line": line,
                "marker": (mr, mc, color),
                "marker_left": marker_left,
                "pattern": tuple(pattern),
            }
        )

    all_4 = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4}
    orphaned = all_4 - covered_4
    if orphaned:
        errors.append(f"{len(orphaned)} color-4 cell(s) do not participate in any matched reflection")

    return {
        "errors": errors,
        "setups": setups,
        "lines": lines,
        "markers": markers,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Authority-valid structural grammar; accepts every canonical input."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"n_setups": len(analysis["setups"])}


def _apply_rule(
    grid: list[list[int]],
    *,
    assume_marker_side: str | None = None,
    reuse_first_marker_color: bool = False,
) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = [row[:] for row in grid]
    first_color = analysis["setups"][0]["marker"][2]
    w = len(grid[0])
    for setup in analysis["setups"]:
        line = setup["line"]
        _, mc, marker_color = setup["marker"]
        linec = line["col"]
        if assume_marker_side == "left":
            marker_left = True
        elif assume_marker_side == "right":
            marker_left = False
        else:
            marker_left = mc < linec
        color = first_color if reuse_first_marker_color else marker_color
        for r in range(line["r1"], line["r2"] + 1):
            for c in range(w):
                if grid[r][c] != 4:
                    continue
                if (marker_left and c > linec) or ((not marker_left) and c < linec):
                    mirror_c = 2 * linec - c
                    if 0 <= mirror_c < w:
                        out[r][mirror_c] = color
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected Racket rule for diagnostics/tests."""
    return _apply_rule(grid)


def _rival_all_markers_left(grid):
    return _apply_rule(grid, assume_marker_side="left")


def _rival_all_markers_right(grid):
    return _apply_rule(grid, assume_marker_side="right")


def _rival_first_marker_color(grid):
    return _apply_rule(grid, reuse_first_marker_color=True)


def _witness_marker_left(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(s["marker_left"] for s in analysis["setups"])


def _witness_marker_right(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and any(not s["marker_left"] for s in analysis["setups"])


def _witness_distinct_marker_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len({s["marker"][2] for s in analysis["setups"]}) >= 2


SEMANTIC_WITNESSES = {
    "marker_left_branch": _witness_marker_left,
    "marker_right_branch": _witness_marker_right,
    "distinct_marker_colors": _witness_distinct_marker_colors,
}

SEMANTIC_RIVALS = {
    "assume_all_markers_left": _rival_all_markers_left,
    "assume_all_markers_right": _rival_all_markers_right,
    "reuse_first_marker_color": _rival_first_marker_color,
}

WITNESS_RIVALS = {
    "marker_left_branch": ["assume_all_markers_right"],
    "marker_right_branch": ["assume_all_markers_left"],
    "distinct_marker_colors": ["reuse_first_marker_color"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for i, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {i} is outside the teaching grammar: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {i} output does not match guide reflection")
    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is outside the teaching grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match guide reflection")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query_answer:
                reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def _place_setup(
    grid: list[list[int]],
    rng,
    br0: int,
    br1: int,
    width: int,
    *,
    marker_left: bool,
    marker_color: int,
) -> bool:
    """Place one canonical-shaped setup inside row band [br0, br1]."""
    band_h = br1 - br0 + 1
    if band_h < 3 or width < 7:
        return False
    kmax = max(1, (width - 3) // 2)
    k = rng.randint(1, kmax)
    if width - 1 - k < k:
        return False
    linec = rng.randint(k, width - 1 - k)
    lr0 = rng.randint(br0, br1 - 1)
    lr1 = rng.randint(lr0 + 1, br1)
    for r in range(lr0, lr1 + 1):
        grid[r][linec] = 2

    if marker_left:
        far_cols = list(range(linec + 1, linec + 1 + k))
    else:
        far_cols = list(range(linec - k, linec))
    region = [(r, c) for r in range(lr0, lr1 + 1) for c in far_cols]
    if not region:
        return False

    # The canonical marker is a seed cell of the reflected shape.  Select the
    # far-side anchor first, paint it as 4, then put the marker at its mirror.
    count = rng.randint(max(2, len(region) // 3), len(region))
    pattern = rng.sample(region, min(count, len(region)))
    anchor = rng.choice(pattern)
    for r, c in pattern:
        grid[r][c] = 4
    mr, far_c = anchor
    mc = 2 * linec - far_c
    if not (0 <= mc < width) or grid[mr][mc] != 0:
        return False
    grid[mr][mc] = marker_color
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Choose latent profile scale BEFORE drawing the observable n_setups axis.
    # GenCtx records keyed draws for provenance, so replacing n_setups after a
    # draw would make the returned grid disagree with its own generation trace.
    profile_rng = ctx.draw_rng("profile")
    canonical_anchor = "n_setups" not in overrides and profile_rng.random() < 0.5
    if "n_setups" in overrides:
        n_setups = ctx.draw_int("n_setups", 1, 4)
    elif canonical_anchor and difficulty == "hard":
        n_setups = ctx.draw_int("n_setups", 4, 4)
    elif canonical_anchor:
        n_setups = ctx.draw_int("n_setups", 2, 2)
    elif difficulty == "easy":
        n_setups = ctx.draw_int("n_setups", 2, 2)
    elif difficulty == "hard":
        n_setups = ctx.draw_int("n_setups", 3, 4)
    else:
        n_setups = ctx.draw_int("n_setups", 2, 3)

    rng = ctx.draw_rng("layout")
    base_h = {
        "easy": (10, 14),
        "medium": (14, 19),
        "hard": (18, 26),
        None: (13, 19),
    }[difficulty]
    base_w = {
        "easy": (12, 16),
        "medium": (14, 20),
        "hard": (18, 26),
        None: (14, 20),
    }[difficulty]
    # Row-separated generation is deliberately stricter than canonical, but a
    # one-row separator is enough to preserve ownership.  This also permits the
    # canonical 16x18 / four-setup profile in every difficulty curriculum.
    min_h = 4 * n_setups - 1
    h_lo = max(base_h[0], min_h)
    h_hi = max(base_h[1], h_lo)

    # Keep a substantial, deterministic canonical-scale anchor stream in every
    # difficulty band.  It prevents a difficulty-only scale shortcut and gives
    # the canonical-profile floor real per-band support, while the other half
    # of draws still explores the wider difficulty-specific size range.
    anchor_hw = None
    if canonical_anchor:
        if difficulty == "hard":
            anchor_hw = (16, 18)
        else:
            anchor_hw = (profile_rng.choice((14, 16)), 16)
        min_h = 4 * n_setups - 1
        h_lo = max(base_h[0], min_h)
        h_hi = max(base_h[1], h_lo)

    for _attempt in range(80):
        if anchor_hw is not None:
            h, w = anchor_hw
        else:
            h = rng.randint(h_lo, h_hi)
            w = rng.randint(*base_w)
        grid = full_grid(h, w, 0)
        gap = 1
        band_h = (h - (n_setups - 1) * gap) // n_setups
        if band_h < 3:
            continue

        marker_colors = rng.sample(list(_MARKER_COLORS), n_setups)
        start_left = ((int(seed) + int(sample_index)) & 1) == 0
        orientations = [start_left if i % 2 == 0 else not start_left for i in range(n_setups)]
        cur = 0
        placed = 0
        for i in range(n_setups):
            br0 = cur
            br1 = br0 + band_h - 1
            if br1 >= h:
                break
            if _place_setup(
                grid,
                rng,
                br0,
                br1,
                w,
                marker_left=orientations[i],
                marker_color=marker_colors[i],
            ):
                placed += 1
            cur = br1 + 1 + gap
        if placed != n_setups:
            continue
        errors = self_check(grid)
        if not errors:
            return grid

    raise AssertionError("failed to generate a valid guide-reflection scene after 80 attempts")
