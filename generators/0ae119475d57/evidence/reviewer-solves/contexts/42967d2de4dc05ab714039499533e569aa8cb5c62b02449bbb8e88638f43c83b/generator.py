"""Semantic generator for ARC task ``0ae119475d57``.

The input contains two aligned 5-row panels separated by one full nonzero row.
The output is the upper panel with every nonzero lower-panel cell painted over
it.  Normal generated scenes include preserved upper cells, lower-only cells,
true overlaps, and untouched background, so bottom precedence is observable.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ae119475d57"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "c286c869b037"
# This generator is STRUCTURALLY canonical-like: every draw is a lawful 5+1+5
# aligned panel scene, so strict_canonical_like measures 450/450 (100%).
# Holding it to its own promise is what makes a regression visible — the
# PRE-repair source scored 12% here, and with only the gate's global 0.05
# near-zero floor it would still have passed. See docs/SEMANTIC_GATE_CONTRACT.md
# section 2b: no global bar separates good from defective on this corpus.
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 2

SUMMARY = (
    "An 11-row zero-background grid contains a 5-row upper panel, a full "
    "uniform nonzero separator at row 5, and an aligned 5-row lower panel. "
    "Each panel uses one nonzero color, with the two panel colors and separator "
    "color distinct. The 5-row output keeps each upper cell unless the aligned "
    "lower cell is nonzero, in which case the lower value overrides it. Every "
    "normal generated scene contains upper-only, lower-only, overlapping, and "
    "blank aligned positions. No panel row is full, leaving one unique separator."
)

INVARIANTS = [
    "the input is exactly 11 rows: five upper, one separator, five lower",
    "row 5 is the only full uniform nonzero row",
    "upper, lower, and separator colors are pairwise distinct",
    "both panels are nonempty and include upper-only and lower-only positions",
    "normal generated scenes also contain a true overlap and untouched blank",
    "every panel row contains a zero, so no panel row mimics a separator",
]

COUNTER_HYPOTHESES = [
    "discard the lower panel and copy the upper panel",
    "discard the upper panel and copy the lower panel",
    "take a color-blind occupancy union",
    "let the upper panel win at overlaps",
    "use the separator color as the answer or as a fixed split-at-gray cue",
    "copy a fixed row, width, texture, or modal color",
]

AXES = {
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed choices within 8..16",
        "valid": "4..16",
    },
    "top_color": {
        "type": "color",
        "default": "rng, nonzero and distinct from lower/separator",
        "valid": "1..9",
    },
    "bot_color": {
        "type": "color",
        "default": "rng, nonzero and distinct from upper/separator",
        "valid": "1..9",
    },
    "sep_color": {
        "type": "color",
        "default": "rng, nonzero and distinct from both panel colors",
        "valid": "1..9",
    },
}

# Exact value-pairs, not blanket axis-pair exemptions: all 504 distinct role
# palettes remain legal, while the 27 equal-color pairs are intentional errors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {left: color, right: color}
    for left, right in (
        ("top_color", "bot_color"),
        ("top_color", "sep_color"),
        ("bot_color", "sep_color"),
    )
    for color in range(1, 10)
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_SCENE_PROFILES = (
    "canonical_sparse",
    "balanced",
    "top_heavy",
    "bottom_heavy",
)
_ALLOWED_OVERRIDES = frozenset(AXES)
_WIDTHS_BY_BAND = {
    "easy": (8, 9, 10, 11, 11),
    "medium": (10, 11, 11, 12, 13),
    "hard": (11, 11, 12, 13, 14, 15, 16),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    if h != 11:
        errors.append(f"height must be exactly 11, found {h}")
    if not 4 <= w <= 16:
        errors.append(f"width must be within 4..16, found {w}")
    if errors:
        return result

    separator = set(grid[5])
    if len(separator) != 1 or 0 in separator:
        errors.append("row 5 must be a full uniform nonzero separator")
        sep_color = None
    else:
        sep_color = next(iter(separator))

    top_colors = {
        grid[r][c]
        for r in range(5)
        for c in range(w)
        if grid[r][c] != 0
    }
    bot_colors = {
        grid[r + 6][c]
        for r in range(5)
        for c in range(w)
        if grid[r + 6][c] != 0
    }
    if len(top_colors) != 1:
        errors.append(
            "upper panel must use exactly one nonzero color, found "
            f"{sorted(top_colors)}"
        )
    if len(bot_colors) != 1:
        errors.append(
            "lower panel must use exactly one nonzero color, found "
            f"{sorted(bot_colors)}"
        )
    top_color = next(iter(top_colors)) if len(top_colors) == 1 else None
    bot_color = next(iter(bot_colors)) if len(bot_colors) == 1 else None
    role_colors = [top_color, bot_color, sep_color]
    if all(color is not None for color in role_colors) and len(set(role_colors)) != 3:
        errors.append("upper, lower, and separator colors must be pairwise distinct")

    branch_counts = {
        "blank": 0,
        "top_only": 0,
        "bottom_only": 0,
        "overlap": 0,
    }
    for r in range(5):
        for c in range(w):
            top_present = grid[r][c] != 0
            bot_present = grid[r + 6][c] != 0
            if top_present and bot_present:
                branch_counts["overlap"] += 1
            elif top_present:
                branch_counts["top_only"] += 1
            elif bot_present:
                branch_counts["bottom_only"] += 1
            else:
                branch_counts["blank"] += 1

    if branch_counts["top_only"] == 0:
        errors.append("no upper-only position; upper preservation is hidden")
    if branch_counts["bottom_only"] == 0:
        errors.append("no lower-only position; lower insertion is hidden")
    if branch_counts["blank"] == 0:
        errors.append("no aligned blank position remains as background")

    result.update(
        {
            "height": h,
            "width": w,
            "top_color": top_color,
            "bot_color": bot_color,
            "sep_color": sep_color,
            "branch_counts": branch_counts,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete canonical-compatible input grammar."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict manifold check (SEMANTIC_GATE_CONTRACT hook 1).

    Everything ``self_check`` demands, plus a reviewer-level constraint the
    grammar alone does not state: no panel row may be entirely nonzero,
    because a full panel row would visually mimic a second separator and no
    canonical pair contains one.  Canonical pairs contain ZERO true overlaps,
    so overlap presence is deliberately NOT required here (it is required of
    generated draws via SEMANTIC_WITNESSES instead); all four canonical
    inputs must pass this predicate.
    """
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    w = analysis["width"]
    for r in range(5):
        if all(grid[r][c] != 0 for c in range(w)):
            reasons.append(f"upper-panel row {r} is entirely nonzero (mimics a separator)")
        if all(grid[r + 6][c] != 0 for c in range(w)):
            reasons.append(f"lower-panel row {r + 6} is entirely nonzero (mimics a separator)")
    return reasons


def _branch_counts_or_none(grid):
    """Branch tally for witness predicates; None when the grid is off-grammar."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return analysis["branch_counts"]


def _witness_blank(grid) -> bool:
    counts = _branch_counts_or_none(grid)
    return counts is not None and counts["blank"] > 0


def _witness_upper_only(grid) -> bool:
    counts = _branch_counts_or_none(grid)
    return counts is not None and counts["top_only"] > 0


def _witness_lower_only(grid) -> bool:
    counts = _branch_counts_or_none(grid)
    return counts is not None and counts["bottom_only"] > 0


def _witness_true_overlap(grid) -> bool:
    """A cell where BOTH panels are nonzero with distinct colors, so the
    output visibly shows the lower value replacing the upper one.  No
    canonical pair demonstrates this — 'lower wins' is authority-derived —
    which is exactly why generated draws must witness it."""
    counts = _branch_counts_or_none(grid)
    return counts is not None and counts["overlap"] > 0


SEMANTIC_WITNESSES = {
    "aligned_blank": _witness_blank,
    "upper_only_preserved": _witness_upper_only,
    "lower_only_inserted": _witness_lower_only,
    "true_overlap_lower_wins": _witness_true_overlap,
}


def _competitor_copy_upper(grid):
    return [[grid[r][c] for c in range(len(grid[0]))] for r in range(5)]


def _competitor_copy_lower(grid):
    return [[grid[r + 6][c] for c in range(len(grid[0]))] for r in range(5)]


def _competitor_upper_wins(grid):
    w = len(grid[0])
    return [
        [grid[r][c] if grid[r][c] != 0 else grid[r + 6][c] for c in range(w)]
        for r in range(5)
    ]


_COMPETING_RULES = {
    "copy_upper_panel": _competitor_copy_upper,
    "copy_lower_panel": _competitor_copy_lower,
    "upper_wins_overlap": _competitor_upper_wins,
}



def _competitor_fill_blanks(grid):
    """Deliberate rival: overlay, but fill aligned blanks with the separator."""
    output = rule_mirror(grid)
    return [[value if value else grid[5][0] for value in row] for row in output]


# A feature-presence assertion is not yet evidence against an alternate rule.
# Bind each witness to a specific falsifiable rival; the shared semantic gate
# independently evaluates these functions against the real Racket authority.
SEMANTIC_RIVALS = {
    **_COMPETING_RULES,
    "fill_blank_with_separator": _competitor_fill_blanks,
}
WITNESS_RIVALS = {
    "aligned_blank": ["fill_blank_with_separator"],
    "upper_only_preserved": ["copy_lower_panel"],
    "lower_only_inserted": ["copy_upper_panel"],
    "true_overlap_lower_wins": ["upper_wins_overlap"],
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"upper_wins_overlap": _competitor_upper_wins}


def lesson_identifiable(demos, query) -> list[str]:
    """Demos must uniquely pin the rule against the documented shortcuts
    (SEMANTIC_GATE_CONTRACT hook 3).  A competitor that reproduces every
    demo output yet answers the query differently makes the lesson
    unidentifiable."""
    reasons: list[str] = []
    episodes = list(demos) + [query]
    for i, ep in enumerate(episodes):
        label = f"demo {i}" if i < len(demos) else "query"
        grid = ep.get("input")
        errors = _validate_grid(grid)
        if not errors and len(grid) != 11:
            errors = [f"height must be exactly 11, found {len(grid)}"]
        if errors:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
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
    for name, competitor in SEMANTIC_RIVALS.items():
        if all(competitor(d["input"]) == d["output"] for d in demos) and (
            competitor(query["input"]) != truth
        ):
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a "
                "different query answer"
            )
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact public semantic axes from a structurally valid scene."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "top_color": analysis["top_color"],
        "bot_color": analysis["bot_color"],
        "sep_color": analysis["sep_color"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket rule is authoritative."""
    if _validate_grid(grid):
        raise ValueError("rule_mirror expects a rectangular ARC-color grid")
    if len(grid) < 11:
        raise ValueError("rule_mirror requires at least 11 rows")
    w = len(grid[0])
    return [
        [grid[r + 6][c] if grid[r + 6][c] != 0 else grid[r][c] for c in range(w)]
        for r in range(5)
    ]


def _draw_width(ctx, band: str, overrides: dict[str, Any]) -> int:
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        return ctx.draw_int("grid_w", 4, 16)
    return ctx.draw_choice("grid_w", _WIDTHS_BY_BAND[band])


def _draw_role_colors(ctx, overrides: dict[str, Any]) -> tuple[int, int, int]:
    pinned = {
        name: int(overrides[name])
        for name in ("top_color", "bot_color", "sep_color")
        if name in overrides and overrides[name] is not None
    }
    if any(not 1 <= color <= 9 for color in pinned.values()):
        raise ValueError("role colors must be integers within 1..9")
    if len(set(pinned.values())) != len(pinned):
        raise ValueError("explicit role colors must be pairwise distinct")

    top_reserved = {value for name, value in pinned.items() if name != "top_color"}
    top = ctx.draw_color("top_color", exclude={0, *top_reserved})
    bot_reserved = {value for name, value in pinned.items() if name != "bot_color"}
    bot = ctx.draw_color("bot_color", exclude={0, top, *bot_reserved})
    sep = ctx.draw_color("sep_color", exclude={0, top, bot})
    return top, bot, sep


def _scaled_count(n: int, ratio: float, band: str) -> int:
    factor = {"easy": 0.80, "medium": 1.0, "hard": 1.20}[band]
    return max(1, round(n * ratio * factor))


def _branch_targets(n: int, profile: str, band: str) -> dict[str, int]:
    ratios = {
        "canonical_sparse": (0.04, 0.12, 0.12),
        "balanced": (0.15, 0.20, 0.20),
        "top_heavy": (0.10, 0.34, 0.12),
        "bottom_heavy": (0.10, 0.12, 0.34),
    }
    overlap_ratio, top_ratio, bottom_ratio = ratios[profile]
    counts = {
        "overlap": _scaled_count(n, overlap_ratio, band),
        "top_only": _scaled_count(n, top_ratio, band),
        "bottom_only": _scaled_count(n, bottom_ratio, band),
    }
    while sum(counts.values()) >= n:
        key = max(counts, key=counts.get)
        if counts[key] == 1:
            break
        counts[key] -= 1
    counts["blank"] = n - sum(counts.values())
    if counts["blank"] < 5:
        raise ValueError("branch profile needs at least five blanks for separator repair")
    return counts


def _remove_false_separators(grid: list[list[int]], rng: Any) -> None:
    """Repair full panel rows with at most five count-preserving swaps.

    Every profile has at least five aligned blank cells. A full panel row
    has none, so some other row has at least two aligned blanks (pigeonhole
    over the four remaining rows). Move one occupied *pair* to such a blank.
    The source row gains a blank and the destination retains one; no new
    full panel row is created. All four branch counts and role colors stay
    exact. Already-valid scenes are untouched, without a reserved blank
    column, extra shared-blank requirement, or rejection-sampling loop.
    """
    width = len(grid[0])
    for r in range(5):
        if not (all(grid[r]) or all(grid[r + 6])):
            continue
        destinations = []
        for other in range(5):
            blanks = [
                c for c in range(width)
                if grid[other][c] == 0 and grid[other + 6][c] == 0
            ]
            if len(blanks) >= 2:
                destinations.extend((other, c) for c in blanks)
        if not destinations:
            raise RuntimeError("separator repair requires at least five aligned blanks")
        target_r, target_c = rng.choice(destinations)
        source_c = rng.randrange(width)
        for offset in (0, 6):
            grid[target_r + offset][target_c] = grid[r + offset][source_c]
            grid[r + offset][source_c] = 0


def _paint_scene(
    width: int,
    top_color: int,
    bot_color: int,
    sep_color: int,
    profile: str,
    band: str,
    rng: Any,
) -> list[list[int]]:
    grid = full_grid(11, width, 0)
    grid[5] = [sep_color] * width
    cells = [(r, c) for r in range(5) for c in range(width)]
    rng.shuffle(cells)
    counts = _branch_targets(len(cells), profile, band)
    cursor = 0
    overlap = cells[cursor : cursor + counts["overlap"]]
    cursor += counts["overlap"]
    top_only = cells[cursor : cursor + counts["top_only"]]
    cursor += counts["top_only"]
    bottom_only = cells[cursor : cursor + counts["bottom_only"]]

    for r, c in overlap:
        grid[r][c] = top_color
        grid[r + 6][c] = bot_color
    for r, c in top_only:
        grid[r][c] = top_color
    for r, c in bottom_only:
        grid[r + 6][c] = bot_color
    _remove_false_separators(grid, rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"{name} must be an integer or None, found {value!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    width = _draw_width(ctx, band, overrides)
    top_color, bot_color, sep_color = _draw_role_colors(ctx, overrides)
    profile = _SCENE_PROFILES[int(sample_index) % len(_SCENE_PROFILES)]
    grid = _paint_scene(
        width,
        top_color,
        bot_color,
        sep_color,
        profile,
        band,
        ctx.draw_rng("layout"),
    )
    errors = strict_canonical_like(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    return grid
