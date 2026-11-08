"""Generator for ARC task c3202e5a / canonical id 4d5bb3c0250b.

A square grid is partitioned into equal square blocks by full, one-cell-wide
separator rows and columns.  Exactly one block is *pure*: all of its nonzero
cells have one color.  Every other block contains at least two nonzero colors.
The Racket oracle extracts the whole unique pure block, preserving its zeros.

The default distribution keeps a 78% prior on one of the three complete
canonical structural profiles while varying colors, target position, target
morphology, occupancy, and distractor palettes.  The remaining draws use two
lawful generalized profiles.  Distractors deliberately reuse the target color
so neither a unique-color nor a fixed-location shortcut solves the task.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4d5bb3c0250b"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "0bc50653fe24"

SUMMARY = (
    "Equal square blocks separated by full same-color rows/columns; crop the "
    "unique block whose nonzero cells all share one color."
)

INVARIANTS = [
    "square ARC grid no larger than 30x30 with colors 0..9",
    "one or more full nonzero separator rows and columns, all one color",
    "separator lines form equal square blocks",
    "exactly one nonempty block has one nonzero color",
    "every distractor block has the declared 2..7 distinct nonzero colors",
]

# name -> (block size, number of blocks per dimension).  The first three are
# the complete linked profiles observed across every canonical train/test
# input.  The final two broaden size/count support without changing the rule.
_PROFILES = {
    "canonical_23_5x4": (5, 4),
    "canonical_29_5x5": (5, 5),
    "canonical_23_3x6": (3, 6),
    "generalized_19_3x5": (3, 5),
    "generalized_29_4x6": (4, 6),
}
_CANONICAL_PROFILES = tuple(name for name in _PROFILES if name.startswith("canonical_"))
_GENERALIZED_PROFILES = tuple(name for name in _PROFILES if name.startswith("generalized_"))
_PROFILE_BY_SIGNATURE = {
    (size * count + count - 1, size, count): name
    for name, (size, count) in _PROFILES.items()
}
_CANONICAL_PRIOR_P = 0.78
# (profile, target-cell count, target bbox h/w, target touches outer block ring)
_CANONICAL_SIGNATURES = frozenset({
    ("canonical_23_5x4", 6, 5, 4, True),
    ("canonical_23_5x4", 8, 5, 4, False),
    ("canonical_23_3x6", 4, 3, 3, True),
    ("canonical_29_5x5", 6, 5, 5, False),
})

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "profile": {
        "type": "str",
        "default": "78% complete canonical linked profile, else generalized",
        "valid": (
            "canonical_23_5x4|canonical_29_5x5|canonical_23_3x6|"
            "generalized_19_3x5|generalized_29_4x6"
        ),
    },
    "separator_color": {
        "type": "color",
        "default": "keyed nonzero color",
        "valid": "1..9",
    },
    "target_color": {
        "type": "color",
        "default": "keyed nonzero color distinct from separator",
        "valid": "1..9",
    },
    "target_at_border": {
        "type": "bool",
        "default": "keyed true|false",
        "valid": "true|false",
    },
    "target_cells": {
        "type": "int",
        "default": "difficulty-keyed choice of 4|6|8",
        "valid": "4|6|8",
    },
    "distractor_colors": {
        "type": "int",
        "default": "difficulty-keyed 2..7",
        "valid": "2..7",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
# The override checker treats an explicit empty declaration as strict mode:
# every rejected combination must carry structured incompatible-axis metadata.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_controls(seed, sample_index, difficulty, overrides) -> None:
    """Reject scalar coercions and undeclared controls before any keyed draw."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name == "profile":
            if type(value) is not str or value not in _PROFILES:
                raise ValueError(f"profile must be one of {tuple(_PROFILES)!r}")
        elif name in {"separator_color", "target_color"}:
            if type(value) is not int or not 1 <= value <= 9:
                raise ValueError(f"{name} must be a literal integer color in 1..9")
        elif name == "target_at_border":
            if type(value) is not bool:
                raise TypeError("target_at_border must be a literal bool")
        elif name == "target_cells":
            if type(value) is not int or value not in {4, 6, 8}:
                raise ValueError("target_cells must be one of 4, 6, or 8")
        elif name == "distractor_colors":
            if type(value) is not int or not 2 <= value <= 7:
                raise ValueError("distractor_colors must be a literal integer in 2..7")

    separator = overrides.get("separator_color")
    target = overrides.get("target_color")
    if separator is not None and target is not None and separator == target:
        exc = ValueError("separator_color and target_color must be distinct")
        exc.incompatible_axes = ("separator_color", "target_color")
        raise exc


def _grid_size(block_size: int, block_count: int) -> int:
    return block_size * block_count + block_count - 1


def _separator_positions(block_size: int, block_count: int) -> list[int]:
    return [block_size + i * (block_size + 1) for i in range(block_count - 1)]


def _bands(separators: Iterable[int], limit: int) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    for separator in separators:
        if start < separator:
            spans.append((start, separator - 1))
        start = separator + 1
    if start < limit:
        spans.append((start, limit - 1))
    return spans


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = next(iter(remaining))
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen) == len(remaining)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = list(cells)
    if not points:
        return 0, 0
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _canonical_sparse(
    points: list[tuple[int, int]], expected_bbox: tuple[int, int]
) -> bool:
    """Official morphology class: exact count/bbox and disconnected globally."""
    return bool(points) and not _is_connected(points) and _bbox(points) == expected_bbox


def _sample_target_cells(
    rng,
    block_size: int,
    count: int,
    canonical_bbox: tuple[int, int] | None,
):
    cells = [(r, c) for r in range(block_size) for c in range(block_size)]
    count = min(count, len(cells) - 1)
    if canonical_bbox is not None:
        for _ in range(2048):
            picked = rng.sample(cells, count)
            if _canonical_sparse(picked, canonical_bbox):
                return picked
        raise ValueError(
            f"could not construct canonical target morphology: "
            f"block={block_size}, cells={count}, bbox={canonical_bbox}"
        )
    # Generalized examples intentionally include connected and arbitrary sparse
    # layouts, so target morphology cannot stand in for color-purity testing.
    if rng.random() < 0.45:
        start = rng.choice(cells)
        chosen = {start}
        frontier = [start]
        while len(chosen) < count:
            candidates = []
            for r, c in frontier:
                for dr, dc in _DIRS4:
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < block_size
                        and 0 <= nxt[1] < block_size
                        and nxt not in chosen
                    ):
                        candidates.append(nxt)
            if not candidates:
                candidates = [cell for cell in cells if cell not in chosen]
            nxt = rng.choice(candidates)
            chosen.add(nxt)
            frontier.append(nxt)
        return list(chosen)
    return rng.sample(cells, count)


def _canonical_prior_signature(ctx, overrides):
    """Choose one whole official linked signature on default-only draws."""
    if overrides:
        return None
    if ctx.draw_rng("canonical-prior").random() >= _CANONICAL_PRIOR_P:
        return None
    return ctx.draw_rng("canonical-signature").choice(
        tuple(sorted(_CANONICAL_SIGNATURES))
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")
    target_rng = ctx.draw_rng("target-layout")
    distractor_rng = ctx.draw_rng("distractor-layout")

    canonical_signature = _canonical_prior_signature(ctx, overrides)
    if canonical_signature is None:
        profile = ctx.draw_choice("profile", tuple(_PROFILES))
        canonical_bbox = None
    else:
        profile, prior_cells, bbox_h, bbox_w, prior_border = canonical_signature
        profile = ctx.draw_choice("profile", (profile,))
        canonical_bbox = (bbox_h, bbox_w)
    block_size, block_count = _PROFILES[profile]
    size = _grid_size(block_size, block_count)

    explicit_target = overrides.get("target_color")
    sep_exclude = {0}
    if explicit_target is not None:
        sep_exclude.add(explicit_target)
    separator_color = ctx.draw_color_strict("separator_color", exclude=sep_exclude)
    target_color = ctx.draw_color_strict(
        "target_color", exclude={0, separator_color}
    )
    if canonical_signature is None:
        target_at_border = ctx.draw_choice("target_at_border", (False, True))
        target_cell_options = {
            "easy": (4, 4, 4, 6, 8),
            "medium": (4, 6, 6, 6, 8),
            "hard": (4, 6, 8, 8, 8),
        }.get(str(difficulty), (4, 6, 8))
        target_cells = ctx.draw_choice("target_cells", target_cell_options)
    else:
        target_at_border = ctx.draw_choice("target_at_border", (prior_border,))
        target_cells = ctx.draw_choice("target_cells", (prior_cells,))
    distractor_colors = ctx.draw_int_diff("distractor_colors", 2, 7)

    if target_cells >= block_size * block_size:
        raise ValueError(
            "target_cells must leave at least one zero in the selected block"
        )

    separators = _separator_positions(block_size, block_count)
    grid = full_grid(size, size, 0)
    for r in separators:
        for c in range(size):
            grid[r][c] = separator_color
    for c in separators:
        for r in range(size):
            grid[r][c] = separator_color

    spans = _bands(separators, size)
    blocks = [(ri, ci, rb, cb) for ri, rb in enumerate(spans) for ci, cb in enumerate(spans)]
    if target_at_border:
        candidates = [
            block
            for block in blocks
            if block[0] in {0, block_count - 1}
            or block[1] in {0, block_count - 1}
        ]
    else:
        candidates = [
            block
            for block in blocks
            if 0 < block[0] < block_count - 1
            and 0 < block[1] < block_count - 1
        ]
    if not candidates:
        raise ValueError(
            f"profile {profile!r} has no block for target_at_border={target_at_border}"
        )
    target = layout_rng.choice(candidates)

    local_target_cells = _sample_target_cells(
        target_rng, block_size, target_cells, canonical_bbox
    )

    for ri, ci, (r0, r1), (c0, c1) in blocks:
        local_cells = [
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        ]
        if (ri, ci) == (target[0], target[1]):
            for lr, lc in local_target_cells:
                grid[r0 + lr][c0 + lc] = target_color
            continue

        # Exact number of distinct nonzero colors in every distractor.  The
        # first distractor palette slot is always the target color, defeating
        # the shortcut "crop the only block containing the output color".
        legal = [c for c in range(1, 10) if c != target_color]
        palette = [target_color] + distractor_rng.sample(
            legal, distractor_colors - 1
        )
        extra_by_band = {"easy": 1, "medium": 3, "hard": 5}.get(
            str(difficulty), 3
        )
        occupied = min(
            len(local_cells) - 1,
            distractor_colors + distractor_rng.randint(0, extra_by_band),
        )
        positions = distractor_rng.sample(local_cells, occupied)
        for color, (r, c) in zip(palette, positions):
            grid[r][c] = color
        for r, c in positions[len(palette):]:
            grid[r][c] = distractor_rng.choice(palette)

    return grid


def _analyze(grid):
    """Return rule-relevant structure recovered only from the returned grid."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid colors must be integers 0..9")

    full_rows = [
        r for r, row in enumerate(grid) if len(set(row)) == 1 and row[0] != 0
    ]
    full_cols = [
        c
        for c in range(w)
        if len({grid[r][c] for r in range(h)}) == 1 and grid[0][c] != 0
    ]
    separator_colors = {
        *[grid[r][0] for r in full_rows],
        *[grid[0][c] for c in full_cols],
    }
    row_spans = _bands(full_rows, h)
    col_spans = _bands(full_cols, w)
    blocks = []
    for ri, (r0, r1) in enumerate(row_spans):
        for ci, (c0, c1) in enumerate(col_spans):
            nonzero = [
                grid[r][c]
                for r in range(r0, r1 + 1)
                for c in range(c0, c1 + 1)
                if grid[r][c] != 0
            ]
            colors = set(nonzero)
            points = [
                (r - r0, c - c0)
                for r in range(r0, r1 + 1)
                for c in range(c0, c1 + 1)
                if grid[r][c] != 0
            ]
            blocks.append(
                {
                    "ri": ri,
                    "ci": ci,
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "colors": colors,
                    "points": points,
                }
            )
    pure = [block for block in blocks if len(block["colors"]) == 1 and block["points"]]
    return {
        "height": h,
        "width": w,
        "full_rows": full_rows,
        "full_cols": full_cols,
        "separator_colors": separator_colors,
        "row_spans": row_spans,
        "col_spans": col_spans,
        "blocks": blocks,
        "pure": pure,
    }


def observe_overrides(grid) -> dict:
    """Recover every declared exact axis from grid content, never metadata."""
    data = _analyze(grid)
    if len(data["separator_colors"]) != 1 or len(data["pure"]) != 1:
        return {}
    block_heights = {b["height"] for b in data["blocks"]}
    block_widths = {b["width"] for b in data["blocks"]}
    if len(block_heights) != 1 or block_heights != block_widths:
        return {}
    block_size = next(iter(block_heights))
    block_count = len(data["row_spans"])
    profile = _PROFILE_BY_SIGNATURE.get(
        (data["height"], block_size, block_count)
    )
    target = data["pure"][0]
    distractor_counts = {
        len(block["colors"])
        for block in data["blocks"]
        if block is not target
    }
    return {
        "profile": profile,
        "separator_color": next(iter(data["separator_colors"])),
        "target_color": next(iter(target["colors"])),
        "target_at_border": (
            target["ri"] in {0, block_count - 1}
            or target["ci"] in {0, block_count - 1}
        ),
        "target_cells": len(target["points"]),
        "distractor_colors": (
            next(iter(distractor_counts))
            if len(distractor_counts) == 1
            else tuple(sorted(distractor_counts))
        ),
    }


def canonical_profile_signature(grid):
    """Complete strict empirical-manifold signature, or ``None``.

    Nuisance factors intentionally relaxed: separator/target colors, exact
    target block position, and exact occupied coordinates.  Retained jointly:
    one of the three observed (grid, block-size, block-count) profiles,
    exactly one pure target, official target cell-count support, disconnected
    sparse morphology spanning the target block, and >=2-color distractors.
    """
    try:
        data = _analyze(grid)
    except ValueError:
        return None
    if len(data["separator_colors"]) != 1 or len(data["pure"]) != 1:
        return None
    block_sizes = {(b["height"], b["width"]) for b in data["blocks"]}
    if len(block_sizes) != 1:
        return None
    block_h, block_w = next(iter(block_sizes))
    if block_h != block_w:
        return None
    profile = _PROFILE_BY_SIGNATURE.get(
        (data["height"], block_h, len(data["row_spans"]))
    )
    if profile not in _CANONICAL_PROFILES:
        return None
    target = data["pure"][0]
    block_count = len(data["row_spans"])
    signature = (
        profile,
        len(target["points"]),
        *_bbox(target["points"]),
        (
            target["ri"] in {0, block_count - 1}
            or target["ci"] in {0, block_count - 1}
        ),
    )
    if signature not in _CANONICAL_SIGNATURES or _is_connected(target["points"]):
        return None
    if any(
        len(block["colors"]) < 2
        for block in data["blocks"]
        if block is not target
    ):
        return None
    return signature


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full input grammar required by the Racket oracle."""
    try:
        data = _analyze(grid)
    except ValueError as exc:
        return [str(exc)]

    problems: list[str] = []
    h, w = data["height"], data["width"]
    if h != w:
        problems.append(f"grid must be square, got {h}x{w}")
    if h > 30 or w > 30:
        problems.append(f"grid exceeds ARC 30x30 limit: {h}x{w}")
    if not data["full_rows"] or not data["full_cols"]:
        problems.append("need at least one full nonzero separator row and column")
    if len(data["separator_colors"]) != 1:
        problems.append("all separator rows and columns must share one color")

    row_sizes = [end - start + 1 for start, end in data["row_spans"]]
    col_sizes = [end - start + 1 for start, end in data["col_spans"]]
    if not row_sizes or len(set(row_sizes)) != 1:
        problems.append("separator rows must form equal-height bands")
    if not col_sizes or len(set(col_sizes)) != 1:
        problems.append("separator columns must form equal-width bands")
    if row_sizes and col_sizes and row_sizes[0] != col_sizes[0]:
        problems.append("separator bands must form square blocks")
    if len(data["row_spans"]) != len(data["col_spans"]):
        problems.append("row and column block counts must match")

    if len(data["pure"]) != 1:
        problems.append(
            f"expected exactly one nonempty pure-color block, got {len(data['pure'])}"
        )
    for block in data["blocks"]:
        if block in data["pure"]:
            continue
        if len(block["colors"]) < 2:
            problems.append(
                "every distractor block must contain at least two nonzero colors"
            )
            break
    return problems


def _crop_block(grid, data, block):
    r0, r1 = data["row_spans"][block["ri"]]
    c0, c1 = data["col_spans"][block["ci"]]
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def rule_mirror(grid):
    """Independent Python mirror for tests; Racket remains label authority."""
    problems = self_check(grid)
    if problems:
        raise ValueError("invalid separator-block scene: " + "; ".join(problems))
    data = _analyze(grid)
    return _crop_block(grid, data, data["pure"][0])


def strict_canonical_like(grid) -> list[str]:
    """The full lawful manifold shared by canonical and generated inputs."""
    return list(self_check(grid))


def _crop_top_left_block(grid):
    """Rival: crops the first block without checking color cardinality."""
    data = _analyze(grid)
    if not data["blocks"]:
        return None
    return _crop_block(grid, data, data["blocks"][0])


def _target_not_top_left(grid) -> bool:
    try:
        data = _analyze(grid)
    except ValueError:
        return False
    return bool(
        len(data["pure"]) == 1
        and (data["pure"][0]["ri"], data["pure"][0]["ci"]) != (0, 0)
    )


SEMANTIC_WITNESSES = {"target_not_top_left": _target_not_top_left}
SEMANTIC_RIVALS = {"crop_top_left_block": _crop_top_left_block}
WITNESS_RIVALS = {"target_not_top_left": ("crop_top_left_block",)}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave the top-left rival viable."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the unique-pure-block rule")

    try:
        query_answer = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the unique-pure-block rule")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair.get("output") for pair in demos)
        if survives and rival(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons

