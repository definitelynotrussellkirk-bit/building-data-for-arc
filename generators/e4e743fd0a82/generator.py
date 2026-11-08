"""Generator for arc_puzzle_bank_21_set10_s:S10_E2 — fill row intervals.

Rule: in each row, a color appearing exactly twice with only background cells
between its two occurrences is extended into a solid horizontal bar from the
left endpoint through the right endpoint. Other rows remain unchanged.

The distribution uses complete linked layouts rather than independently drawn
height/width/count marginals. Three layouts reproduce the official train/test
morphology (including span multisets and edge-contact patterns), and three
larger layouts provide controlled generalization. Lawful distractor rows
separately test the exact-two, same-color, and all-zero-gap preconditions.

Combinatorial axes (3): layout, texture, color_reuse.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4e743fd0a82"
VERSION = "3.0.0"  # linked profiles + observable axes + structural self_check
TASK_ID = "e4e743fd0a82"
RULE_HASH = "39e714bb1edd"
SUMMARY = (
    "A zero-background grid contains several rows with exactly two equal "
    "nonzero endpoints separated by at least two zero cells. Fill each such "
    "interval inclusively with its endpoint color; blank and explicitly "
    "non-qualifying distractor rows stay unchanged."
)

INVARIANTS = [
    "the grid is one of six declared linked (height, width, qualifying-row) layouts",
    "every qualifying row has exactly two equal colors with endpoint distance >= 3",
    "the cells strictly between qualifying endpoints are all background 0",
    "at most one lawful distractor row tests a single failed precondition",
    "all nonzero colors are drawn from 2..9",
]

# edge_counts = (left-only spans, right-only spans, interior spans)
LAYOUT_SPECS = {
    # Executably extracted official profiles. Row positions and color names are
    # nuisance variation; dimensions, active-row count, edge contacts, and span
    # multiset are the linked task-relevant morphology.
    "canonical_a": {
        "h": 6, "w": 9, "n_rows": 2,
        "edge_counts": (0, 1, 1), "canonical_spans": (5, 6),
    },
    "canonical_b": {
        "h": 7, "w": 10, "n_rows": 3,
        "edge_counts": (1, 1, 1), "canonical_spans": (4, 6, 6),
    },
    "canonical_c": {
        "h": 8, "w": 11, "n_rows": 3,
        "edge_counts": (1, 1, 1), "canonical_spans": (4, 6, 8),
    },
    # Disjoint generalized tuples keep layout recoverable from the returned
    # grid while adding larger canvases and edge-heavy cases.
    "wide_right": {
        "h": 6, "w": 12, "n_rows": 3,
        "edge_counts": (0, 1, 2), "canonical_spans": None,
    },
    "tall_mixed": {
        "h": 9, "w": 13, "n_rows": 4,
        "edge_counts": (1, 1, 2), "canonical_spans": None,
    },
    "edge_heavy": {
        "h": 10, "w": 14, "n_rows": 6,
        "edge_counts": (3, 3, 0), "canonical_spans": None,
    },
}
LAYOUTS = tuple(LAYOUT_SPECS)

TEXTURES = (
    "pairs_only",
    "singleton_distractor",
    "mismatched_distractor",
    "blocked_gap_distractor",
)
PALETTE_KINDS: tuple = ()
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES = TEXTURES

# Keep this literal: lint_generator validates exact metadata from the AST.
AXES = {
    "layout": {
        "type": "str",
        "default": "difficulty-weighted linked profile",
        "valid": "canonical_a|canonical_b|canonical_c|wide_right|tall_mixed|edge_heavy",
    },
    "texture": {
        "type": "str",
        "default": "difficulty-weighted lawful row grammar",
        "valid": "pairs_only|singleton_distractor|mismatched_distractor|blocked_gap_distractor",
    },
    "color_reuse": {
        "type": "bool",
        "default": "difficulty-weighted false/true",
        "valid": "true|false",
    },
}

# Every band contains every exact option so boundary overrides remain legal.
# Repetitions change only the default prior.
_LAYOUT_OPTIONS = {
    "easy": (
        "canonical_a", "canonical_a", "canonical_b", "canonical_b",
        "canonical_c", "canonical_c", "wide_right", "tall_mixed",
        "edge_heavy",
    ),
    "medium": (
        "canonical_a", "canonical_b", "canonical_c", "wide_right",
        "wide_right", "tall_mixed", "tall_mixed", "edge_heavy",
    ),
    "hard": (
        "canonical_a", "canonical_b", "canonical_c", "wide_right",
        "tall_mixed", "tall_mixed", "edge_heavy", "edge_heavy",
        "edge_heavy",
    ),
}
_TEXTURE_OPTIONS = {
    "easy": (
        "pairs_only", "pairs_only", "pairs_only", "pairs_only",
        "singleton_distractor", "mismatched_distractor",
        "blocked_gap_distractor",
    ),
    "medium": (
        "pairs_only", "pairs_only", "singleton_distractor",
        "mismatched_distractor", "blocked_gap_distractor",
    ),
    "hard": (
        "pairs_only", "pairs_only", "singleton_distractor",
        "mismatched_distractor", "blocked_gap_distractor",
        "blocked_gap_distractor",
    ),
}
_REUSE_OPTIONS = {
    "easy": (False, False, False, True),
    "medium": (False, False, True),
    "hard": (False, False, True, True),
}


def _row_info(kind, color=None, left=None, right=None, span=None):
    return {
        "kind": kind,
        "color": color,
        "left": left,
        "right": right,
        "span": span,
    }


def _band(difficulty) -> str:
    return difficulty if difficulty in ("easy", "medium", "hard") else "medium"


def _layout_from_grid(h: int, w: int, n_rows: int):
    for name, spec in LAYOUT_SPECS.items():
        if (h, w, n_rows) == (spec["h"], spec["w"], spec["n_rows"]):
            return name
    return None


def _classify_row(row: list[int]) -> dict:
    nz = [(c, value) for c, value in enumerate(row) if value != 0]
    if not nz:
        return _row_info("blank")
    if len(nz) == 1:
        return _row_info("singleton_distractor")
    if len(nz) == 2:
        (c1, v1), (c2, v2) = nz
        if c2 - c1 >= 3 and v1 == v2:
            return _row_info("pair", v1, c1, c2, c2 - c1)
        if c2 - c1 >= 3 and v1 != v2:
            return _row_info("mismatched_distractor")
        return _row_info("invalid")
    if len(nz) == 3:
        (c1, v1), (cm, vm), (c2, v2) = nz
        if c2 - c1 >= 3 and v1 == v2 and vm != v1 and c1 < cm < c2:
            return _row_info("blocked_gap_distractor")
    return _row_info("invalid")


def _analyze(grid) -> dict:
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"errors": ["empty or non-list grid"]}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged or non-list grid"]}
    if any(
        not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid contains non-integer or out-of-range color"]}

    rows = [_classify_row(row) for row in grid]
    pairs = [info for info in rows if info["kind"] == "pair"]
    distractors = [
        info["kind"] for info in rows if info["kind"].endswith("_distractor")
    ]
    invalid_rows = [
        index for index, info in enumerate(rows) if info["kind"] == "invalid"
    ]
    h = len(grid)
    layout = _layout_from_grid(h, w, len(pairs))
    if not distractors:
        texture = "pairs_only"
    elif len(distractors) == 1:
        texture = distractors[0]
    else:
        texture = None

    left_count = sum(
        info["left"] == 0 and info["right"] != w - 1 for info in pairs
    )
    right_count = sum(
        info["right"] == w - 1 and info["left"] != 0 for info in pairs
    )
    interior_count = sum(
        info["left"] != 0 and info["right"] != w - 1 for info in pairs
    )
    both_edge_count = sum(
        info["left"] == 0 and info["right"] == w - 1 for info in pairs
    )
    colors = tuple(int(info["color"]) for info in pairs)
    spans = tuple(sorted(int(info["span"]) for info in pairs))

    return {
        "errors": [],
        "h": h,
        "w": w,
        "rows": rows,
        "pairs": pairs,
        "layout": layout,
        "texture": texture,
        "distractors": distractors,
        "invalid_rows": invalid_rows,
        "edge_counts": (left_count, right_count, interior_count),
        "both_edge_count": both_edge_count,
        "pair_colors": colors,
        "color_reuse": len(set(colors)) < len(colors),
        "spans": spans,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact teaching grammar, not merely palette and dimensions."""
    info = _analyze(grid)
    if info["errors"]:
        return list(info["errors"])

    errors: list[str] = []
    if info["layout"] is None:
        errors.append(
            f"unrecognized linked layout {(info['h'], info['w'], len(info['pairs']))}"
        )
        return errors
    spec = LAYOUT_SPECS[info["layout"]]

    bad_colors = sorted(
        {value for row in grid for value in row if value != 0 and value not in range(2, 10)}
    )
    if bad_colors:
        errors.append(f"nonzero colors outside 2..9: {bad_colors}")
    if info["invalid_rows"]:
        errors.append(f"invalid nonblank row grammar at rows {info['invalid_rows']}")
    if info["texture"] not in TEXTURES:
        errors.append("expected zero or one lawful distractor row")
    if info["both_edge_count"]:
        errors.append("a qualifying span may touch at most one horizontal edge")
    if info["edge_counts"] != spec["edge_counts"]:
        errors.append(
            f"edge-contact counts {info['edge_counts']} != layout {spec['edge_counts']}"
        )
    if (
        spec["canonical_spans"] is not None
        and info["spans"] != spec["canonical_spans"]
    ):
        errors.append(
            f"span multiset {info['spans']} != canonical layout "
            f"{spec['canonical_spans']}"
        )
    if len(info["pairs"]) != spec["n_rows"]:
        errors.append(f"qualifying rows {len(info['pairs'])} != {spec['n_rows']}")
    return errors


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid itself."""
    info = _analyze(grid)
    if (
        info["errors"]
        or info["layout"] is None
        or info["texture"] not in TEXTURES
    ):
        return {}
    return {
        "layout": info["layout"],
        "texture": info["texture"],
        "color_reuse": info["color_reuse"],
    }


def canonical_profile_signature(grid):
    """Joint morphology used for canonical-retention and recombination tests."""
    info = _analyze(grid)
    if info["errors"] or info["layout"] is None or info["texture"] is None:
        return None
    return (
        info["h"],
        info["w"],
        len(info["pairs"]),
        info["edge_counts"],
        info["spans"],
        info["texture"],
        info["color_reuse"],
    )


_CANONICAL_SIGNATURES = {
    (6, 9, 2, (0, 1, 1), (5, 6), "pairs_only", False),
    (7, 10, 3, (1, 1, 1), (4, 6, 6), "pairs_only", False),
    (8, 11, 3, (1, 1, 1), (4, 6, 8), "pairs_only", False),
}


def _random_pair_columns(kind: str, w: int, rng, span=None) -> tuple[int, int]:
    if kind == "left":
        realized = span if span is not None else rng.randint(3, w - 2)
        return 0, realized
    if kind == "right":
        realized = span if span is not None else rng.randint(3, w - 2)
        return w - 1 - realized, w - 1
    if kind == "interior":
        realized = span if span is not None else rng.randint(3, w - 3)
        left = rng.randint(1, w - 2 - realized)
        return left, left + realized
    raise ValueError(f"unknown pair kind {kind!r}")


def _pair_plan(layout: str, rng) -> list[tuple[str, object]]:
    if layout == "canonical_a":
        plan = [("interior", 5), ("right", 6)]
    elif layout == "canonical_b":
        plan = [("left", 4), ("right", 6), ("interior", 6)]
    elif layout == "canonical_c":
        plan = [("left", 6), ("right", 8), ("interior", 4)]
    else:
        spec = LAYOUT_SPECS[layout]
        left, right, interior = spec["edge_counts"]
        plan = (
            [("left", None)] * left
            + [("right", None)] * right
            + [("interior", None)] * interior
        )
    rng.shuffle(plan)
    return plan


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = _band(difficulty)
    layout = ctx.draw_choice("layout", _LAYOUT_OPTIONS[band])
    texture = ctx.draw_choice("texture", _TEXTURE_OPTIONS[band])
    color_reuse = ctx.draw_choice("color_reuse", _REUSE_OPTIONS[band])

    spec = LAYOUT_SPECS[layout]
    grid = full_grid(spec["h"], spec["w"], 0)
    rng = ctx.draw_rng("scene")
    total_nonblank_rows = spec["n_rows"] + (texture != "pairs_only")
    row_ids = rng.sample(range(spec["h"]), total_nonblank_rows)
    pair_rows = row_ids[:spec["n_rows"]]

    if color_reuse:
        unique_count = max(1, spec["n_rows"] - 1)
        palette = rng.sample(range(2, 10), unique_count)
        pair_colors = (palette + [palette[0]])[:spec["n_rows"]]
        rng.shuffle(pair_colors)
    else:
        pair_colors = rng.sample(range(2, 10), spec["n_rows"])

    for row, color, (kind, span) in zip(
        pair_rows,
        pair_colors,
        _pair_plan(layout, rng),
    ):
        left, right = _random_pair_columns(kind, spec["w"], rng, span)
        grid[row][left] = color
        grid[row][right] = color

    if texture != "pairs_only":
        row = row_ids[-1]
        if texture == "singleton_distractor":
            grid[row][rng.randrange(spec["w"])] = rng.randrange(2, 10)
        elif texture == "mismatched_distractor":
            left = rng.randint(0, spec["w"] - 4)
            right = rng.randint(left + 3, spec["w"] - 1)
            c1, c2 = rng.sample(range(2, 10), 2)
            grid[row][left], grid[row][right] = c1, c2
        elif texture == "blocked_gap_distractor":
            left = rng.randint(0, spec["w"] - 5)
            right = rng.randint(left + 4, spec["w"] - 1)
            middle = rng.randint(left + 1, right - 1)
            endpoint, blocker = rng.sample(range(2, 10), 2)
            grid[row][left] = endpoint
            grid[row][middle] = blocker
            grid[row][right] = endpoint
        else:  # draw_choice validates, but keep the branch total and loud.
            raise ValueError(f"unsupported texture {texture!r}")

    return grid
