"""Generator for f29955be8ba2 — permute three row blocks by a side header.

The first column's top three cells contain a permutation of 1, 2, 3.  After
removing that column, the remaining grid is three equal-height horizontal
blocks.  The selected Racket authority stacks those blocks in header order.

Version 3 replaces a weak sampler whose declared overrides were partly inert,
whose negative textures leaked into the ordinary axis domain, and which had no
task-specific structural or semantic contract.  This sampler keeps the Racket
rule unchanged while making every public axis observable and scheduling
counterexamples to the strongest canonical shortcut: reading header numbers as
ranks of the blocks' foreground colors instead of their top-to-bottom positions.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f29955be8ba2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "7f09fab6403a"

SUMMARY = (
    "Column 0 rows 0..2 encode a permutation of three equal-height row blocks. "
    "Drop the header column and stack the blocks in that order. Block geometry, "
    "width, sparse contents, and foreground colors vary; scheduled palettes "
    "break the canonical color-rank shortcut."
)

INVARIANTS = [
    "the grid has three equal-height horizontal blocks and a one-cell side header",
    "column 0 rows 0..2 are a permutation of 1,2,3 and all later header cells are zero",
    "each block is a nonempty, non-solid sparse mask painted in one distinct foreground color",
    "the three masks are pairwise distinct; ordinary draws use a non-identity permutation",
    "output drops column 0 and stacks whole blocks in the exact order named by the header",
]

AXES = {
    "block_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware draws",
        "valid": "2..5",
        "doc": "Exact height of each of the three row blocks.",
    },
    "block_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-aware draws",
        "valid": "3..18",
        "doc": "Exact body width after dropping the side header.",
    },
    "permutation": {
        "type": "str",
        "default": "five-way non-identity teaching schedule",
        "valid": "123|132|213|231|312|321",
        "doc": "Top-to-bottom block indexes written in column 0 rows 0..2.",
    },
    "palette_profile": {
        "type": "str",
        "default": "canonical_low|varied|canonical_high schedule",
        "valid": "canonical_low|canonical_high|varied",
        "doc": "Exact ordered foreground-color profile; varied is forced non-monotone.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_PERMS = ("123", "132", "213", "231", "312", "321")
_TEACHING_PERMS = ("132", "231", "213", "312", "321")
_PALETTE_PROFILES = ("canonical_low", "canonical_high", "varied")
_PALETTE_SCHEDULE = ("canonical_low", "varied", "canonical_high")
_BANDS = {
    "easy": {"block_h": (2, 3), "block_w": (4, 8)},
    "medium": {"block_h": (3, 4), "block_w": (6, 12)},
    "hard": {"block_h": (3, 5), "block_w": (8, 18)},
}
_LIMITS = {"block_h": (2, 5), "block_w": (3, 18)}

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = _PALETTE_SCHEDULE
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the palette branch used by the three-example teaching schedule."""
    del seed, difficulty
    return _PALETTE_SCHEDULE[sample_index % len(_PALETTE_SCHEDULE)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name in ("block_h", "block_w"):
        value = overrides.get(name)
        if value is None:
            continue
        lo, hi = _LIMITS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")
    value = overrides.get("permutation")
    if value is not None and (type(value) is not str or value not in _PERMS):
        raise ValueError(f"permutation must be one of {_PERMS}")
    value = overrides.get("palette_profile")
    if value is not None and (
        type(value) is not str or value not in _PALETTE_PROFILES
    ):
        raise ValueError(f"palette_profile must be one of {_PALETTE_PROFILES}")


def _shape_anchor(sample_index: int) -> tuple[int, int] | None:
    """Two sparse anchors per 12 draws cover both canonical profile cells."""
    residue = sample_index % 12
    if residue == 0:
        return 3, 7  # 9x8 with palette size 5 under canonical_low
    if residue == 5:
        return 3, 8  # 9x9 with palette size 7 under canonical_high
    return None


def _draw_axis(ctx: Any, name: str, default_bounds: tuple[int, int], anchor: int | None) -> int:
    if ctx.overrides.get(name) is not None:
        lo, hi = _LIMITS[name]
        return ctx.draw_int(name, lo, hi)
    if anchor is not None:
        return ctx.draw_int(name, anchor, anchor)
    return ctx.draw_int(name, *default_bounds)


def _draw_permutation(ctx: Any, sample_index: int) -> str:
    if ctx.overrides.get("permutation") is not None:
        return ctx.draw_choice("permutation", _PERMS)
    scheduled = _TEACHING_PERMS[sample_index % len(_TEACHING_PERMS)]
    return ctx.draw_choice("permutation", (scheduled,))


def _draw_palette_profile(ctx: Any, sample_index: int) -> str:
    if ctx.overrides.get("palette_profile") is not None:
        return ctx.draw_choice("palette_profile", _PALETTE_PROFILES)
    scheduled = schedule_profile(ctx.seed, sample_index, ctx.difficulty)
    return ctx.draw_choice("palette_profile", (scheduled,))


def _foreground_colors(ctx: Any, profile: str) -> tuple[int, int, int]:
    if profile == "canonical_low":
        return 2, 3, 4
    if profile == "canonical_high":
        return 5, 6, 7
    colors = tuple(ctx.draw_rng("varied_palette").sample(range(2, 10), 3))
    # A varied profile is deliberately not sorted by source-block position.
    # Therefore "header values mean ascending color ranks" must disagree.
    if colors == tuple(sorted(colors)):
        colors = colors[1:] + colors[:1]
    return colors


def _fallback_mask(block_h: int, block_w: int, count: int, index: int) -> frozenset[tuple[int, int]]:
    cells = [(r, c) for r in range(block_h) for c in range(block_w)]
    start = (index * max(1, block_w // 2 + 1)) % len(cells)
    return frozenset(cells[(start + step) % len(cells)] for step in range(count))


def _draw_masks(ctx: Any, block_h: int, block_w: int) -> tuple[frozenset[tuple[int, int]], ...]:
    area = block_h * block_w
    lo = max(2, area // 4)
    hi = max(lo, min(area - 1, (2 * area) // 3))
    anchors = ((0, 0), (block_h - 1, block_w - 1), (0, block_w - 1))
    positions = [(r, c) for r in range(block_h) for c in range(block_w)]
    masks: list[frozenset[tuple[int, int]]] = []
    for index, anchor in enumerate(anchors):
        rng = ctx.draw_rng(f"block_pattern:{index}")
        count = rng.randint(lo, hi)
        candidates = [cell for cell in positions if cell != anchor]
        chosen: frozenset[tuple[int, int]] | None = None
        for _attempt in range(64):
            mask = frozenset((anchor, *rng.sample(candidates, count - 1)))
            if mask not in masks:
                chosen = mask
                break
        if chosen is None:
            for shift in range(area):
                mask = _fallback_mask(block_h, block_w, count, index + shift)
                if mask not in masks:
                    chosen = mask
                    break
        if chosen is None:  # constructive bounds above make this unreachable
            raise RuntimeError("could not construct three distinct block masks")
        masks.append(chosen)
    return tuple(masks)


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_overrides(overrides)
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
    anchor = _shape_anchor(sample_index)
    block_h = _draw_axis(
        ctx, "block_h", _BANDS[band]["block_h"], None if anchor is None else anchor[0]
    )
    block_w = _draw_axis(
        ctx, "block_w", _BANDS[band]["block_w"], None if anchor is None else anchor[1]
    )
    permutation = _draw_permutation(ctx, sample_index)
    palette_profile = _draw_palette_profile(ctx, sample_index)
    colors = _foreground_colors(ctx, palette_profile)
    masks = _draw_masks(ctx, block_h, block_w)

    grid = full_grid(3 * block_h, block_w + 1, 0)
    for row, value in enumerate(int(char) for char in permutation):
        grid[row][0] = value
    for block_index, (color, mask) in enumerate(zip(colors, masks)):
        row0 = block_index * block_h
        for row, col in mask:
            grid[row0 + row][col + 1] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid grid: " + "; ".join(findings))
    return grid


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty row sequence"]
    first = grid[0]
    if not isinstance(first, (list, tuple)) or not first:
        return None, ["grid must have at least one column"]
    width = len(first)
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        out_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                out_row.append(0)
            else:
                out_row.append(value)
        converted.append(out_row)
    return (None, errors) if errors else (converted, [])


def _analyze(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    facts: dict[str, Any] = {
        "block_h": None,
        "block_w": None,
        "permutation": None,
        "colors": (),
        "masks": (),
        "counts": (),
        "palette_profile": None,
        "output_changes": False,
    }
    if converted is None:
        return {"grid": None, "errors": errors, "facts": facts}

    height, width = len(converted), len(converted[0])
    if height % 3:
        errors.append("grid height must be divisible by three")
    block_h = height // 3 if height % 3 == 0 else None
    block_w = width - 1
    facts["block_h"] = block_h
    facts["block_w"] = block_w
    if block_h is None or not 2 <= block_h <= 5:
        errors.append("block height must be 2..5")
    if not 3 <= block_w <= 18:
        errors.append("body width must be 3..18")

    if height >= 3:
        header = tuple(converted[row][0] for row in range(3))
        if sorted(header) != [1, 2, 3]:
            errors.append("column 0 rows 0..2 must be a permutation of 1,2,3")
        else:
            facts["permutation"] = "".join(str(value) for value in header)
    else:
        errors.append("grid must contain three header rows")
    if any(converted[row][0] != 0 for row in range(3, height)):
        errors.append("column 0 below the three-cell header must be zero")

    colors: list[int] = []
    masks: list[frozenset[tuple[int, int]]] = []
    counts: list[int] = []
    if block_h is not None and 2 <= block_h <= 5 and 3 <= block_w <= 18:
        area = block_h * block_w
        for block_index in range(3):
            color_set: set[int] = set()
            cells: set[tuple[int, int]] = set()
            for row in range(block_h):
                for col in range(block_w):
                    value = converted[block_index * block_h + row][col + 1]
                    if value:
                        color_set.add(value)
                        cells.add((row, col))
            if not cells:
                errors.append(f"block {block_index} must be nonempty")
                colors.append(-1)
            elif len(color_set) != 1:
                errors.append(f"block {block_index} must use exactly one foreground color")
                colors.append(-1)
            else:
                colors.append(next(iter(color_set)))
            if len(cells) == area:
                errors.append(f"block {block_index} must retain at least one background cell")
            masks.append(frozenset(cells))
            counts.append(len(cells))
        valid_colors = [color for color in colors if color >= 0]
        if len(valid_colors) == 3 and len(set(valid_colors)) != 3:
            errors.append("the three blocks must use distinct foreground colors")
        if len(set(masks)) != 3:
            errors.append("the three block masks must be pairwise distinct")

    facts["colors"] = tuple(colors)
    facts["masks"] = tuple(masks)
    facts["counts"] = tuple(counts)
    if tuple(colors) == (2, 3, 4):
        facts["palette_profile"] = "canonical_low"
    elif tuple(colors) == (5, 6, 7):
        facts["palette_profile"] = "canonical_high"
    elif len(colors) == 3 and all(color >= 0 for color in colors):
        facts["palette_profile"] = "varied"

    if not errors and facts["permutation"] is not None:
        facts["output_changes"] = facts["permutation"] != "123"
    return {"grid": converted, "errors": errors, "facts": facts}


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate this generator's full structural input contract."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    """Accept lawful, non-degenerate teaching instances of the selected rule."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if analysis["facts"]["permutation"] == "123":
        reasons.append("identity permutation does not visibly teach reordering")
    return reasons


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every exact public axis from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "block_h": facts["block_h"],
        "block_w": facts["block_w"],
        "permutation": facts["permutation"],
        "palette_profile": facts["palette_profile"],
        "foreground_colors": facts["colors"],
        "occupied_counts": facts["counts"],
        "output_changes": facts["output_changes"],
    }


def _blocks_from_analysis(analysis: dict[str, Any]) -> list[list[list[int]]]:
    grid = analysis["grid"]
    facts = analysis["facts"]
    block_h = facts["block_h"]
    return [
        [row[1:] for row in grid[index * block_h : (index + 1) * block_h]]
        for index in range(3)
    ]


def _stack(blocks: list[list[list[int]]], order: Iterable[int]) -> list[list[int]]:
    return [row[:] for index in order for row in blocks[index]]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror used by tests/contracts; the pinned Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    blocks = _blocks_from_analysis(analysis)
    order = [int(char) - 1 for char in analysis["facts"]["permutation"]]
    return _stack(blocks, order)


def _rival_header_values_as_color_ranks(grid: Any) -> list[list[int]]:
    """Wrong rule: 1/2/3 index ascending foreground colors, not source rows."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    blocks = _blocks_from_analysis(analysis)
    colors = analysis["facts"]["colors"]
    rank_to_source = sorted(range(3), key=lambda index: colors[index])
    order = [rank_to_source[int(char) - 1] for char in analysis["facts"]["permutation"]]
    return _stack(blocks, order)


def _rival_cyclic_from_first_header(grid: Any) -> list[list[int]]:
    """Wrong rule: use only the first header value and preserve cyclic order."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    blocks = _blocks_from_analysis(analysis)
    first = int(analysis["facts"]["permutation"][0]) - 1
    return _stack(blocks, (first, (first + 1) % 3, (first + 2) % 3))


def _facts_or_none(grid: Any) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis["facts"]


def _witness_palette_order_decoupled(grid: Any) -> bool:
    facts = _facts_or_none(grid)
    return facts is not None and facts["colors"] != tuple(sorted(facts["colors"]))


def _witness_noncyclic_header(grid: Any) -> bool:
    facts = _facts_or_none(grid)
    return facts is not None and facts["permutation"] not in ("123", "231", "312")


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "palette_order_decoupled": _witness_palette_order_decoupled,
    "noncyclic_header": _witness_noncyclic_header,
}
SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "header_values_as_color_ranks": _rival_header_values_as_color_ranks,
    "cyclic_from_first_header": _rival_cyclic_from_first_header,
}
WITNESS_RIVALS = {
    "palette_order_decoupled": ["header_values_as_color_ranks"],
    "noncyclic_header": ["cyclic_from_first_header"],
}
# This rival fits all three usable canonical pairs because the canonical source
# blocks' foreground colors increase with their top-to-bottom positions.
CANONICAL_SHORTCUTS = {
    "header_values_as_color_ranks": _rival_header_values_as_color_ranks,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Report a named wrong rule that survives every demo but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not isinstance(query, dict):
        return ["demos must be a sequence and query must be a mapping"]
    for label, episode in [
        *((f"demo {index}", item) for index, item in enumerate(demos)),
        ("query", query),
    ]:
        if not isinstance(episode, dict) or "input" not in episode:
            reasons.append(f"{label}: missing input")
            continue
        findings = self_check(episode["input"])
        if findings:
            reasons.append(f"{label}: invalid input: {'; '.join(findings)}")
    if reasons:
        return reasons

    for index, demo in enumerate(demos):
        truth = rule_mirror(demo["input"])
        if demo.get("output") != truth:
            reasons.append(f"demo {index}: output does not match the selected rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query: provided output does not match the selected rule")
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(demo["input"]) == demo["output"] for demo in demos
            )
            changes_query = competitor(query["input"]) != query_truth
        except Exception as exc:  # loud contract failure, never silent
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a different query answer"
            )
    return reasons
