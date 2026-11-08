"""Generator for the four-quadrant priority-overlay task.

A centered yellow cross splits a rectangular grid into four equal-shaped
quadrants.  The output overlays corresponding cells with the strict priority
BR > TL > TR > BL.  Ordinary draws use one distinct role color per quadrant
and contain collision witnesses that identify every comparison in that order.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import permutations
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1672855ac30c"
TASK_ID = "1672855ac30c"
VERSION = "3.0.0"
RULE_HASH = "5ebd21db613e"  # normalized canonical program_solution sha256[:12]
# Four demos per lesson, matching the repair report's validated 50/50
# four-demo lesson schedule.  Color-precedence competitors are additionally
# refuted structurally by the even/odd palette-block reversal in generate()
# (three demos alone had left the competitor alive in ~8% of lessons).
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A centered yellow(4) cross divides an odd rectangular grid into TL, TR, "
    "BL, and BR quadrants of the same shape.  Each quadrant has one distinct "
    "role color plus background 0.  For every local cell, output the first "
    "nonzero value in priority order BR, TL, TR, BL."
)

INVARIANTS = [
    "exactly one full yellow(4) row and one full yellow(4) column form a centered cross",
    "the four quadrants have equal shape and each uses exactly one distinct nonzero role color",
    "every ordinary draw contains decisive witnesses for BR>TL, TL>TR, and TR>BL plus a BL fallback",
    "background is 0 and yellow appears only on the cross",
]

POSITION_BIASES = ("scattered", "diagonal", "corners", "edges", "centered")
PALETTE_KINDS = ("canonical", "warm", "cool", "mixed")
DEGENERATE_TEXTURES = ("empty_quadrants", "full_quadrants", "monochrome")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "quadrant_h": {
        "type": "int",
        "default": "difficulty-aware rng with recurring canonical anchor 5",
        "valid": "3..9",
    },
    "quadrant_w": {
        "type": "int",
        "default": "difficulty-aware rng with recurring canonical anchor 4",
        "valid": "3..9",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng canonical|warm|cool|mixed",
        "valid": "|".join(PALETTE_KINDS),
    },
    "quadrant_density": {
        "type": "float",
        "default": "difficulty-aware rng 0.16..0.58",
        "valid": "0.08..0.70",
    },
    "position_bias": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(POSITION_BIASES),
    },
}


def _draw_dimension(ctx, label: str, options: tuple[int, ...]) -> int:
    """Honor the full declared override domain while keeping a curriculum."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, 3, 9)
    return int(ctx.draw_choice(label, options))


def _draw_density(ctx) -> float:
    if "quadrant_density" in ctx.overrides and ctx.overrides["quadrant_density"] is not None:
        value = float(ctx.overrides["quadrant_density"])
        if not 0.08 <= value <= 0.70:
            raise ValueError("quadrant_density override must be within 0.08..0.70")
        return value
    rng = ctx.draw_rng("quadrant_density")
    if ctx.difficulty == "easy":
        return rng.uniform(0.16, 0.28)
    if ctx.difficulty == "hard":
        return rng.uniform(0.40, 0.58)
    return rng.uniform(0.24, 0.44)


def _role_palette(kind: str, rng) -> tuple[int, int, int, int]:
    """Return distinct (TL, TR, BL, BR) role colors, excluding 0 and 4."""
    pools = {
        "canonical": [7, 9, 2, 8],
        "warm": [2, 3, 6, 9],
        "cool": [1, 5, 7, 8],
        "mixed": [1, 2, 3, 5, 6, 7, 8, 9],
    }
    pool = list(pools[kind])
    if kind == "mixed":
        rng.shuffle(pool)
        pool = pool[:4]
    else:
        # Preserve the canonical role mapping for the anchor palette, but vary
        # the other palettes so color identity cannot become a role shortcut.
        if kind != "canonical":
            rng.shuffle(pool)
    return tuple(pool)  # type: ignore[return-value]


def _quadrant_cells(qh: int, qw: int):
    return [(r, c) for r in range(qh) for c in range(qw)]


def _paint_probability(bias: str, r: int, c: int, qh: int, qw: int, density: float) -> float:
    if bias == "diagonal":
        on_diag = abs(r / max(1, qh - 1) - c / max(1, qw - 1)) < 0.22
        return min(0.92, density + (0.34 if on_diag else -0.10))
    if bias == "corners":
        near_corner = r in (0, qh - 1) and c in (0, qw - 1)
        return min(0.92, density + (0.42 if near_corner else -0.08))
    if bias == "edges":
        on_edge = r in (0, qh - 1) or c in (0, qw - 1)
        return min(0.92, density + (0.25 if on_edge else -0.12))
    if bias == "centered":
        nr = abs(r - (qh - 1) / 2) / max(1.0, qh / 2)
        nc = abs(c - (qw - 1) / 2) / max(1.0, qw / 2)
        return min(0.92, max(0.04, density + 0.28 * (1.0 - (nr + nc) / 2)))
    return density


def _set_local(g, cr: int, cc: int, r: int, c: int, values: tuple[int, int, int, int]) -> None:
    tl, tr, bl, br = values
    g[r][c] = tl
    g[r][cc + 1 + c] = tr
    g[cr + 1 + r][c] = bl
    g[cr + 1 + r][cc + 1 + c] = br


def _get_local(g, cr: int, cc: int, r: int, c: int) -> tuple[int, int, int, int]:
    return (
        g[r][c],
        g[r][cc + 1 + c],
        g[cr + 1 + r][c],
        g[cr + 1 + r][cc + 1 + c],
    )


def _force_priority_witnesses(
    g, qh: int, qw: int, colors: tuple[int, int, int, int], rng
) -> None:
    """Install a minimal chain that uniquely identifies BR > TL > TR > BL."""
    cells = _quadrant_cells(qh, qw)
    rng.shuffle(cells)
    p_br, p_tl, p_tr, p_bl, p_bg = cells[:5]
    tl, tr, bl, br = colors
    _set_local(g, qh, qw, *p_br, (tl, tr, bl, br))  # BR beats all lower roles
    _set_local(g, qh, qw, *p_tl, (tl, tr, bl, 0))   # TL beats TR and BL
    _set_local(g, qh, qw, *p_tr, (0, tr, bl, 0))    # TR beats BL
    _set_local(g, qh, qw, *p_bl, (0, 0, bl, 0))     # BL fallback
    _set_local(g, qh, qw, *p_bg, (0, 0, 0, 0))      # explicit background stack


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # One third of ordinary sample indexes anchor the exact canonical 11x9
    # profile.  Remaining samples retain broad rectangular size variation.
    canonical_anchor = sample_index % 3 == 0
    if canonical_anchor:
        qh_options, qw_options = (5,), (4,)
    elif difficulty == "easy":
        qh_options, qw_options = (3, 4, 5), (3, 4, 5)
    elif difficulty == "hard":
        qh_options, qw_options = (6, 7, 8, 9), (5, 6, 7, 8, 9)
    else:
        qh_options, qw_options = (4, 5, 6, 7), (3, 4, 5, 6)

    qh = _draw_dimension(ctx, "quadrant_h", qh_options)
    qw = _draw_dimension(ctx, "quadrant_w", qw_options)
    rng = ctx.draw_rng("layout")

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(str(texture), qh, qw, rng)
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture override: {texture!r}")
    if texture is not None and "position_bias" in overrides:
        if overrides["position_bias"] != texture:
            raise ValueError("texture and position_bias disagree")

    # Color-precedence refutation schedule: consecutive even/odd sample
    # indices share ONE 4-color pool (block-keyed rng) and the odd index
    # reverses the role assignment.  Each scene's forced witnesses pin the
    # chain br>tl>tr>bl over its colors, so the even scene forces p3>p0 while
    # its odd partner forces p0>p3 — a color CYCLE that refutes every fixed
    # color-precedence order.  Within a single scene that refutation is
    # impossible (positional priority always yields a consistent color
    # chain), and without it a demo window can leave a color pair unordered
    # (semantic-gate lesson seed 210111206046418 left 8-vs-7 free).
    block, phase_parity = divmod(int(sample_index), 2)
    block_rng = stable_rng(seed, f"{TASK_ID}|palette-block|{block}", VERSION)
    if overrides.get("palette_kind") is not None:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    else:
        palette_kind = ctx.draw_choice(
            "palette_kind", (block_rng.choice(PALETTE_KINDS),)
        )
    position_bias = (
        str(texture)
        if texture is not None
        else str(ctx.draw_choice("position_bias", POSITION_BIASES))
    )
    density = _draw_density(ctx)
    colors = _role_palette(str(palette_kind), block_rng)
    if phase_parity == 1:
        colors = tuple(reversed(colors))

    h, w = 2 * qh + 1, 2 * qw + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[qh][c] = 4
    for r in range(h):
        g[r][qw] = 4

    for q_index, color in enumerate(colors):
        q_rng = ctx.draw_rng(f"quadrant_{q_index}")
        for r, c in _quadrant_cells(qh, qw):
            probability = _paint_probability(position_bias, r, c, qh, qw, density)
            if q_rng.random() < max(0.02, min(0.96, probability)):
                if q_index == 0:
                    g[r][c] = color
                elif q_index == 1:
                    g[r][qw + 1 + c] = color
                elif q_index == 2:
                    g[qh + 1 + r][c] = color
                else:
                    g[qh + 1 + r][qw + 1 + c] = color

    _force_priority_witnesses(g, qh, qw, colors, ctx.draw_rng("witnesses"))
    return g


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    facts: dict[str, Any] = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"], "facts": facts}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": facts}
    if h > 30 or w > 30:
        errors.append(f"grid exceeds ARC limit: {h}x{w}")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid colors must be integers in 0..9")
        return {"errors": errors, "facts": facts}

    full_rows = [r for r, row in enumerate(grid) if all(value == 4 for value in row)]
    full_cols = [c for c in range(w) if all(grid[r][c] == 4 for r in range(h))]
    if len(full_rows) != 1 or len(full_cols) != 1:
        errors.append("expected exactly one full yellow row and one full yellow column")
        return {"errors": errors, "facts": facts}
    cr, cc = full_rows[0], full_cols[0]
    facts.update({"quadrant_h": cr, "quadrant_w": cc, "cross_row": cr, "cross_col": cc})
    if cr < 3 or cc < 3:
        errors.append("quadrants must be at least 3x3")
    if h != 2 * cr + 1 or w != 2 * cc + 1:
        errors.append("yellow cross must be centered so all four quadrants have equal shape")
    if any(
        grid[r][c] == 4 and r != cr and c != cc
        for r in range(h)
        for c in range(w)
    ):
        errors.append("yellow may appear only on the full cross")
    if errors:
        return {"errors": errors, "facts": facts}

    role_sets = [set() for _ in range(4)]
    branch_counts = {
        "br_priority": 0,
        "tl_priority": 0,
        "tr_priority": 0,
        "bl_fallback": 0,
        "background": 0,
    }
    for r in range(cr):
        for c in range(cc):
            values = _get_local(grid, cr, cc, r, c)
            for q_index, value in enumerate(values):
                if value not in (0, 4):
                    role_sets[q_index].add(value)
            tl, tr, bl, br = values
            if br != 0 and any((tl, tr, bl)):
                branch_counts["br_priority"] += 1
            if br == 0 and tl != 0 and any((tr, bl)):
                branch_counts["tl_priority"] += 1
            if br == 0 and tl == 0 and tr != 0 and bl != 0:
                branch_counts["tr_priority"] += 1
            if br == 0 and tl == 0 and tr == 0 and bl != 0:
                branch_counts["bl_fallback"] += 1
            if not any(values):
                branch_counts["background"] += 1

    for name, colors in zip(("TL", "TR", "BL", "BR"), role_sets):
        if len(colors) != 1:
            errors.append(f"{name} quadrant must use exactly one nonzero role color; got {sorted(colors)}")
    role_colors = [next(iter(colors)) for colors in role_sets if len(colors) == 1]
    if len(role_colors) == 4 and len(set(role_colors)) != 4:
        errors.append("the four quadrant role colors must be distinct")
    for branch in ("br_priority", "tl_priority", "tr_priority", "bl_fallback"):
        if branch_counts[branch] == 0:
            errors.append(f"missing decisive {branch} witness")

    facts.update({"role_colors": role_colors, "branch_counts": branch_counts})
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "quadrant_h": int(analysis["facts"]["quadrant_h"]),
        "quadrant_w": int(analysis["facts"]["quadrant_w"]),
    }


def expected_output(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("malformed lesson: " + "; ".join(analysis["errors"]))
    qh = int(analysis["facts"]["quadrant_h"])
    qw = int(analysis["facts"]["quadrant_w"])
    out = full_grid(qh, qw, 0)
    for r in range(qh):
        for c in range(qw):
            tl, tr, bl, br = _get_local(grid, qh, qw, r, c)
            out[r][c] = br or tl or tr or bl or 0
    return out


def matching_priority_orders(grid, official_output=None) -> list[tuple[str, ...]]:
    """Return priority permutations answer-equivalent on this demonstration."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return []
    qh = int(analysis["facts"]["quadrant_h"])
    qw = int(analysis["facts"]["quadrant_w"])
    official = official_output if official_output is not None else expected_output(grid)
    names = ("TL", "TR", "BL", "BR")
    matches: list[tuple[str, ...]] = []
    for order in permutations(names):
        candidate = full_grid(qh, qw, 0)
        for r in range(qh):
            for c in range(qw):
                values = dict(zip(names, _get_local(grid, qh, qw, r, c)))
                candidate[r][c] = next((values[name] for name in order if values[name] != 0), 0)
        if candidate == official:
            matches.append(tuple(order))
    return matches


# --- Task-linked semantic gate hooks (docs/SEMANTIC_GATE_CONTRACT.md) ---

_PRIORITY_ORDER = ("BR", "TL", "TR", "BL")
_CANONICAL_QUADRANT = (5, 4)  # every canonical input is 11x9
_CANONICAL_ROLES = [7, 9, 2, 8]  # TL, TR, BL, BR in every canonical pair


def strict_canonical_like(grid):
    """[] iff grid matches the strict canonical manifold: lawful grammar,
    11x9 scale (5x4 quadrants), the exact canonical role palette, and an
    answer that identifies the BR>TL>TR>BL order uniquely (all 14 canonical
    pairs satisfy every one of these)."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze(grid)["facts"]
    reasons = []
    scale = (facts["quadrant_h"], facts["quadrant_w"])
    if scale != _CANONICAL_QUADRANT:
        reasons.append(
            f"quadrants {scale} differ from the canonical {_CANONICAL_QUADRANT}"
        )
    if facts["role_colors"] != _CANONICAL_ROLES:
        reasons.append(
            f"role colors {facts['role_colors']} differ from the canonical "
            f"{_CANONICAL_ROLES} (TL, TR, BL, BR)"
        )
    if len(matching_priority_orders(grid)) != 1:
        reasons.append(
            "grid does not uniquely identify the BR>TL>TR>BL priority order"
        )
    return reasons


def _branch_count(grid, branch):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return 0
    return analysis["facts"]["branch_counts"][branch]


def _w_br_wins_collision(grid):
    return _branch_count(grid, "br_priority") > 0


def _w_tl_wins_without_br(grid):
    return _branch_count(grid, "tl_priority") > 0


def _w_tr_wins_without_br_tl(grid):
    return _branch_count(grid, "tr_priority") > 0


def _w_bl_fallback(grid):
    return _branch_count(grid, "bl_fallback") > 0


def _w_background_stack(grid):
    return _branch_count(grid, "background") > 0


def _w_priority_order_uniquely_identified(grid):
    return (
        not self_check(grid)
        and len(matching_priority_orders(grid)) == 1
    )


def _w_non_canonical_scale(grid):
    if self_check(grid):
        return False
    facts = _analyze(grid)["facts"]
    return (facts["quadrant_h"], facts["quadrant_w"]) != _CANONICAL_QUADRANT


def _w_non_canonical_role_palette(grid):
    if self_check(grid):
        return False
    return _analyze(grid)["facts"]["role_colors"] != _CANONICAL_ROLES


SEMANTIC_WITNESSES = {
    "br_wins_collision": _w_br_wins_collision,
    "tl_wins_without_br": _w_tl_wins_without_br,
    "tr_wins_without_br_tl": _w_tr_wins_without_br_tl,
    "bl_fallback": _w_bl_fallback,
    "background_stack": _w_background_stack,
    "priority_order_uniquely_identified": _w_priority_order_uniquely_identified,
    "non_canonical_scale": _w_non_canonical_scale,
    "non_canonical_role_palette": _w_non_canonical_role_palette,
}


def _color_precedence_audit(checked, q_grid, q_answer):
    """Reason string when a color-precedence competitor (some fixed linear
    order over COLORS, not quadrant roles) survives every demo yet is not
    forced to reproduce the query answer; None otherwise."""
    beats: set[tuple[int, int]] = set()
    for grid, output in checked:
        facts = _analyze(grid)["facts"]
        qh, qw = facts["quadrant_h"], facts["quadrant_w"]
        for r in range(qh):
            for c in range(qw):
                winner = output[r][c]
                losers = {
                    value
                    for value in _get_local(grid, qh, qw, r, c)
                    if value not in (0, winner)
                }
                beats.update((winner, loser) for loser in losers)
    # Transitive closure; a cycle means NO color order explains the demos,
    # i.e. the competitor family is already refuted.
    closure = set(beats)
    changed = True
    while changed:
        changed = False
        for a, b in list(closure):
            for c, d in list(closure):
                if b == c and (a, d) not in closure:
                    closure.add((a, d))
                    changed = True
    if any((b, a) in closure for a, b in closure):
        return None
    facts = _analyze(q_grid)["facts"]
    qh, qw = facts["quadrant_h"], facts["quadrant_w"]
    for r in range(qh):
        for c in range(qw):
            winner = q_answer[r][c]
            losers = {
                value
                for value in _get_local(q_grid, qh, qw, r, c)
                if value not in (0, winner)
            }
            for loser in losers:
                if (winner, loser) not in closure:
                    return (
                        "a color-precedence competitor consistent with every "
                        f"demo may rank color {loser} above {winner} and "
                        f"answer query cell ({r},{c}) differently"
                    )
    return None


def lesson_identifiable(demos, query):
    """[] iff the demos leave no competing rule that answers the query
    differently: every quadrant-priority permutation consistent with all
    demos must reproduce the true query answer (the pre-repair defect was a
    draw compatible with ALL 24 permutations), and no fixed color-precedence
    order survives the demos while remaining free on the query."""
    checked = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        errors = self_check(demo["input"])
        if errors:
            return [f"demo {index} input off-grammar: {errors[0]}"]
        if demo["output"] != expected_output(demo["input"]):
            return [f"demo {index} output does not match the canonical rule"]
        checked.append((demo["input"], demo["output"]))
    if not isinstance(query, dict) or "input" not in query:
        return ["query is not an input pair"]
    q_errors = self_check(query["input"])
    if q_errors:
        return [f"query input off-grammar: {q_errors[0]}"]
    q_grid = query["input"]
    q_answer = expected_output(q_grid)

    reasons = []
    consistent = None
    for grid, output in checked:
        orders = set(matching_priority_orders(grid, output))
        consistent = orders if consistent is None else consistent & orders
    q_true_orders = set(matching_priority_orders(q_grid, q_answer))
    divergent = sorted((consistent or set()) - q_true_orders)
    if divergent:
        reasons.append(
            f"{len(divergent)} quadrant-priority permutation(s) consistent "
            "with every demo answer the query differently, e.g. "
            f"{'>'.join(divergent[0])}"
        )
    color_reason = _color_precedence_audit(checked, q_grid, q_answer)
    if color_reason:
        reasons.append(color_reason)
    return reasons


def mutation_fixtures():
    """Task-linked malformed scenes that self_check must reject."""
    base = generate(9137, 41, difficulty="medium")
    qh = (len(base) - 1) // 2
    qw = (len(base[0]) - 1) // 2

    broken_cross = deepcopy(base)
    broken_cross[qh][0] = 0

    extra_cross = deepcopy(base)
    extra_cross[0] = [4] * len(extra_cross[0])

    palette_leak = deepcopy(base)
    used = {value for row in palette_leak for value in row}
    foreign = next(color for color in range(1, 10) if color not in used and color != 4)
    palette_leak[0][0] = foreign

    missing_tr_witness = deepcopy(base)
    for r in range(qh):
        for c in range(qw):
            tl, tr, bl, br = _get_local(missing_tr_witness, qh, qw, r, c)
            if br == 0 and tl == 0 and tr != 0 and bl != 0:
                missing_tr_witness[qh + 1 + r][c] = 0

    empty_bl = deepcopy(base)
    for r in range(qh + 1, len(empty_bl)):
        for c in range(qw):
            empty_bl[r][c] = 0

    return [
        ("broken_cross", broken_cross),
        ("extra_cross", extra_cross),
        ("quadrant_palette_leak", palette_leak),
        ("missing_tr_priority_witness", missing_tr_witness),
        ("empty_bl_quadrant", empty_bl),
    ]


def _draw_from_degenerate(name: str, qh: int, qw: int, rng):
    h, w = 2 * qh + 1, 2 * qw + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[qh][c] = 4
    for r in range(h):
        g[r][qw] = 4
    if name == "empty_quadrants":
        return g
    if name == "full_quadrants":
        for r in range(h):
            for c in range(w):
                if r != qh and c != qw:
                    g[r][c] = 3
        return g
    if name == "monochrome":
        for q_index in range(4):
            for r, c in _quadrant_cells(qh, qw):
                if (r + c + q_index) % 3 == 0:
                    if q_index == 0:
                        g[r][c] = 3
                    elif q_index == 1:
                        g[r][qw + 1 + c] = 3
                    elif q_index == 2:
                        g[qh + 1 + r][c] = 3
                    else:
                        g[qh + 1 + r][qw + 1 + c] = 3
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
