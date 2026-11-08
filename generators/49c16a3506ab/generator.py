"""Generator for f28a3cbb / task 49c16a3506ab.

Each non-background color owns a solid 3x3 block in a grid corner. Scattered
cells of that color slide toward their own block: horizontally when they share
the block's row band, vertically when they share its column band, and
diagonally otherwise. A cell stops immediately before the next step would
enter the block (or leave the grid).

Normal draws contain every motion branch, collision-free destinations,
independently varied per-color scatter counts, and an explicit witness that
refutes the tempting "move to the nearest block" shortcut. Default sample
indices alternate the two opposite-corner layouts so every four-pair lesson
teaches transfer beyond the canonical main diagonal. The Racket rule remains
the output authority; ``rule_mirror`` is only an independent parity aid.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49c16a3506ab"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "b81d150b289c"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Background 6. Each non-6 color has one solid 3x3 corner block. "
    "Scattered same-color cells slide toward their own block: row-band cells "
    "horizontally, column-band cells vertically, and all others diagonally, "
    "stopping adjacent to the block."
)

INVARIANTS = [
    "exactly 2 distinct non-background colors, each anchored by exactly one solid "
    "3x3 corner block",
    "every normal draw contains row, column, and diagonal scattered-cell "
    "witnesses",
    "per-color scatter counts vary independently through an exactly observable "
    "equal/first-sparse/second-sparse relation",
    "at least one scattered source is strictly nearer to the other color's block, "
    "so color ownership rather than geometric proximity is required",
    "all scattered sources and slide destinations are pairwise disjoint and "
    "destinations are background in the input",
    "the transformation is non-identity and preserves every corner block",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted keyed draw, 9 favored",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted keyed draw, 9 favored",
        "valid": "9..15",
    },
    "corner_pair": {
        "type": "str",
        "default": "sample-index schedule alternating main and anti",
        "valid": "main|anti",
    },
    "scatter_count": {
        "type": "int",
        "default": "difficulty-keyed dense-color maximum 4..6",
        "valid": "4..6",
    },
    "scatter_relation": {
        "type": "str",
        "default": "keyed draw",
        "valid": "equal|first_sparse|second_sparse",
    },
    "branch_bias": {
        "type": "str",
        "default": "keyed draw",
        "valid": "row|column|diagonal",
    },
}

BACKGROUND = 6
CORNERS = ("tl", "tr", "bl", "br")
BRANCHES = ("row", "column", "diagonal")
_SCATTER_RELATIONS = ("equal", "first_sparse", "second_sparse")
_PAIR_OPTIONS = ("main", "anti")
_SIZE_OPTIONS = (9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 11, 12, 13, 14, 15)
_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)


def _validate_call(difficulty, overrides: dict) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "scatter_count"):
        value = overrides.get(name)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{name} must be an integer")
    for name in ("corner_pair", "scatter_relation", "branch_bias"):
        value = overrides.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")


def _corner_origin(corner: str, h: int, w: int) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, w - 3),
        "bl": (h - 3, 0),
        "br": (h - 3, w - 3),
    }[corner]


def _pair_corners(pair: str) -> tuple[str, str]:
    if pair == "main":
        return ("tl", "br")
    if pair == "anti":
        return ("tr", "bl")
    raise ValueError(f"corner_pair must be one of {AXES['corner_pair']['valid']}")


def _branch_counts(total: int, bias: str) -> dict[str, int]:
    """Keep every branch positive; dense colors make ``bias`` observable."""
    if not 3 <= total <= 6:
        raise ValueError("per-color scatter count must be in 3..6")
    if bias not in BRANCHES:
        raise ValueError(f"branch_bias must be one of {'|'.join(BRANCHES)}")
    templates = {
        3: (1, 1, 1),
        4: (2, 1, 1),
        5: (3, 1, 1),
        6: (3, 2, 1),
    }
    high, mid, low = templates[total]
    other = [branch for branch in BRANCHES if branch != bias]
    return {bias: high, other[0]: mid, other[1]: low}


def _scatter_counts(dense_count: int, relation: str) -> tuple[int, int]:
    """Return counts in ``_pair_corners`` order for an observable relation."""
    sparse_count = max(3, dense_count - 2)
    if relation == "equal":
        return dense_count, dense_count
    if relation == "first_sparse":
        return sparse_count, dense_count
    if relation == "second_sparse":
        return dense_count, sparse_count
    raise ValueError(f"scatter_relation must be one of {'|'.join(_SCATTER_RELATIONS)}")


def _in_block(r: int, c: int, origin: tuple[int, int]) -> bool:
    r0, c0 = origin
    return r0 <= r <= r0 + 2 and c0 <= c <= c0 + 2


def _classify(r: int, c: int, origin: tuple[int, int]) -> str:
    r0, c0 = origin
    if r0 <= r <= r0 + 2:
        return "row"
    if c0 <= c <= c0 + 2:
        return "column"
    return "diagonal"


def _slide_dest(
    r: int, c: int, origin: tuple[int, int], h: int, w: int
) -> tuple[int, int]:
    r0, c0 = origin
    row_band = r0 <= r <= r0 + 2
    col_band = c0 <= c <= c0 + 2
    hdir = -1 if c0 == 0 else 1
    vdir = -1 if r0 == 0 else 1
    dr = vdir if not row_band else 0
    dc = hdir if not col_band else 0
    rr, cc = r, c
    while True:
        nr, nc = rr + dr, cc + dc
        if (
            nr < 0
            or nr >= h
            or nc < 0
            or nc >= w
            or _in_block(nr, nc, origin)
        ):
            return rr, cc
        rr, cc = nr, nc


def _distance_to_block(
    r: int, c: int, origin: tuple[int, int]
) -> int:
    """Chebyshev distance from a cell to the nearest cell of a 3x3 block."""
    r0, c0 = origin
    dr = 0 if r0 <= r <= r0 + 2 else min(abs(r - r0), abs(r - (r0 + 2)))
    dc = 0 if c0 <= c <= c0 + 2 else min(abs(c - c0), abs(c - (c0 + 2)))
    return max(dr, dc)


def _candidate_cells(
    grid: list[list[int]], corner: str, branch: str
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    origin = _corner_origin(corner, h, w)
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != BACKGROUND or _in_block(r, c, origin):
                continue
            if _classify(r, c, origin) != branch:
                continue
            dest = _slide_dest(r, c, origin, h, w)
            if dest == (r, c) or grid[dest[0]][dest[1]] != BACKGROUND:
                continue
            out.append(((r, c), dest))
    return out


def _place_scattered(
    grid: list[list[int]],
    specs: list[tuple[int, str, str, int]],
    ctx,
) -> None:
    """Place a collision-free set with a required color-binding witness.

    The old exhaustive fixed-order search could become exponential after a
    witness was pinned.  This solver uses deterministic bounded restarts and
    dynamic minimum-remaining-values selection. Candidate sets are generous,
    so the first attempt normally succeeds, while the bound keeps every valid
    override responsive.
    """
    requirements: list[tuple[int, str, str]] = []
    candidate_map: dict[
        tuple[int, str, str],
        list[tuple[tuple[int, int], tuple[int, int]]],
    ] = {}
    origins = {
        color: _corner_origin(corner, len(grid), len(grid[0]))
        for color, corner, _, _ in specs
    }

    def is_binding_witness(color: int, source: tuple[int, int]) -> bool:
        own_distance = _distance_to_block(*source, origins[color])
        return any(
            other_color != color
            and _distance_to_block(*source, other_origin) < own_distance
            for other_color, other_origin in origins.items()
        )

    witness_options: list[
        tuple[
            tuple[int, str, str],
            tuple[tuple[int, int], tuple[int, int]],
        ]
    ] = []
    for color, corner, bias, total in specs:
        counts = _branch_counts(total, bias)
        for branch in BRANCHES:
            key = (color, corner, branch)
            candidates = _candidate_cells(grid, corner, branch)
            ctx.draw_rng(f"candidates:{color}:{corner}:{branch}").shuffle(candidates)
            candidate_map[key] = candidates
            requirements.extend([key] * counts[branch])
            witness_options.extend(
                (key, candidate)
                for candidate in candidates
                if is_binding_witness(color, candidate[0])
            )

    if not witness_options:
        raise ValueError("no candidate can demonstrate own-color block binding")

    def legal(
        candidate: tuple[tuple[int, int], tuple[int, int]],
        sources: set[tuple[int, int]],
        destinations: set[tuple[int, int]],
    ) -> bool:
        source, dest = candidate
        return (
            source not in sources
            and dest not in destinations
            and source not in destinations
            and dest not in sources
        )

    for attempt in range(128):
        rng = ctx.draw_rng(f"placement-attempt:{attempt}")
        shuffled_witnesses = witness_options[:]
        rng.shuffle(shuffled_witnesses)
        witness_key, witness_candidate = shuffled_witnesses[0]
        source, dest = witness_candidate
        chosen = [(witness_key[0], source, dest)]
        sources = {source}
        destinations = {dest}
        remaining = requirements[:]
        remaining.remove(witness_key)

        failed = False
        while remaining:
            unique_keys = set(remaining)
            options_by_key = {
                key: [
                    candidate
                    for candidate in candidate_map[key]
                    if legal(candidate, sources, destinations)
                ]
                for key in unique_keys
            }
            if any(not options for options in options_by_key.values()):
                failed = True
                break
            minimum = min(len(options) for options in options_by_key.values())
            tight_keys = sorted(
                key for key, options in options_by_key.items() if len(options) == minimum
            )
            key = tight_keys[rng.randrange(len(tight_keys))]
            options = options_by_key[key]
            candidate = options[rng.randrange(len(options))]
            source, dest = candidate
            chosen.append((key[0], source, dest))
            sources.add(source)
            destinations.add(dest)
            remaining.remove(key)

        if failed:
            continue

        for color, (r, c), _ in chosen:
            grid[r][c] = color
        if _nearest_anchor(grid) != rule_mirror(grid):
            return
        for _, (r, c), _ in chosen:
            grid[r][c] = BACKGROUND

    raise ValueError(
        "grid_h, grid_w, corner_pair, scatter_count, scatter_relation, and "
        "branch_bias combination cannot place collision-free color-binding "
        "witnesses within the deterministic retry budget"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", _SIZE_OPTIONS)
    w = ctx.draw_choice("grid_w", _SIZE_OPTIONS)
    if overrides.get("corner_pair") is None:
        scheduled_pair = _PAIR_OPTIONS[sample_index % len(_PAIR_OPTIONS)]
        corner_pair = ctx.draw_choice("corner_pair", (scheduled_pair,))
    else:
        corner_pair = ctx.draw_choice("corner_pair", _PAIR_OPTIONS)
    scatter_count = ctx.draw_int_diff("scatter_count", 4, 6)
    scatter_relation = ctx.draw_choice("scatter_relation", _SCATTER_RELATIONS)
    branch_bias = ctx.draw_choice("branch_bias", BRANCHES)

    rng = ctx.draw_rng("layout")
    corners = _pair_corners(corner_pair)
    counts = _scatter_counts(scatter_count, scatter_relation)
    colors = list(_COLORS)
    rng.shuffle(colors)
    colors = colors[: len(corners)]
    grid = full_grid(h, w, BACKGROUND)
    specs = []
    for color, corner, count in zip(colors, corners, counts):
        r0, c0 = _corner_origin(corner, h, w)
        for dr in range(3):
            for dc in range(3):
                grid[r0 + dr][c0 + dc] = color
        specs.append((color, corner, branch_bias, count))

    _place_scattered(grid, specs, ctx)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def _find_blocks(grid: list[list[int]]) -> dict[int, tuple[str, tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    found: dict[int, tuple[str, tuple[int, int]]] = {}
    for corner in CORNERS:
        origin = _corner_origin(corner, h, w)
        r0, c0 = origin
        color = grid[r0][c0]
        if color == BACKGROUND:
            continue
        if all(grid[r0 + dr][c0 + dc] == color for dr in range(3) for dc in range(3)):
            if color in found:
                found[color] = ("duplicate", origin)
            else:
                found[color] = (corner, origin)
    return found


def _scatter_by_color(
    grid: list[list[int]], blocks: dict[int, tuple[str, tuple[int, int]]]
) -> dict[int, list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    out = {color: [] for color in blocks}
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == BACKGROUND or color not in blocks:
                continue
            _, origin = blocks[color]
            if not _in_block(r, c, origin):
                out[color].append((r, c))
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python spelling of the selected canonical Racket rule."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("rule requires a nonempty rectangular grid")
    h, w = len(grid), len(grid[0])
    blocks = _find_blocks(grid)
    colors = sorted({value for row in grid for value in row if value != BACKGROUND})
    out = [row[:] for row in grid]
    for color in colors:
        if color not in blocks or blocks[color][0] == "duplicate":
            raise ValueError(f"color {color} has no unique solid corner block")
        _, origin = blocks[color]
        scattered = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == color and not _in_block(r, c, origin)
        ]
        for r, c in scattered:
            dr, dc = _slide_dest(r, c, origin, h, w)
            out[r][c] = BACKGROUND
            out[dr][dc] = color
    return out


def _pair_name(corners: Iterable[str]) -> str:
    corners = set(corners)
    if corners == {"tl", "br"}:
        return "main"
    if corners == {"tr", "bl"}:
        return "anti"
    return "invalid"


def observe_overrides(grid) -> dict:
    """Recover every exact axis from the returned grid itself."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {}
    h, w = len(grid), len(grid[0])
    blocks = _find_blocks(grid)
    valid_blocks = {
        color: value for color, value in blocks.items() if value[0] != "duplicate"
    }
    scatter = _scatter_by_color(grid, valid_blocks)
    pair = _pair_name(value[0] for value in valid_blocks.values())
    ordered_counts: tuple[int, ...] = ()
    if pair != "invalid":
        colors_by_corner = {
            corner: color for color, (corner, _) in valid_blocks.items()
        }
        if all(corner in colors_by_corner for corner in _pair_corners(pair)):
            ordered_counts = tuple(
                len(scatter[colors_by_corner[corner]])
                for corner in _pair_corners(pair)
            )
    scatter_relation = "invalid"
    scatter_count = -1
    if len(ordered_counts) == 2:
        first, second = ordered_counts
        scatter_count = max(first, second)
        if first == second:
            scatter_relation = "equal"
        elif first < second:
            scatter_relation = "first_sparse"
        else:
            scatter_relation = "second_sparse"

    branch_totals = Counter()
    for color, cells in scatter.items():
        origin = valid_blocks[color][1]
        branch_totals.update(_classify(r, c, origin) for r, c in cells)
    branch_bias = "invalid"
    if branch_totals:
        ordered = branch_totals.most_common()
        if len(ordered) == 1 or ordered[0][1] > ordered[1][1]:
            branch_bias = ordered[0][0]
    return {
        "grid_h": h,
        "grid_w": w,
        "corner_pair": pair,
        "scatter_count": scatter_count,
        "scatter_relation": scatter_relation,
        "branch_bias": branch_bias,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or rule-hiding scenes, while accepting canonical rows."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if not (9 <= h <= 15 and 9 <= w <= 15):
        errors.append(f"dimensions {h}x{w} outside 9..15")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer colors 0..9")
        return errors
    colors = sorted({value for row in grid for value in row if value != BACKGROUND})
    if len(colors) != 2:
        errors.append(f"expected exactly 2 non-background colors, found {len(colors)}")
    blocks = _find_blocks(grid)
    for color in colors:
        if color not in blocks:
            errors.append(f"color {color} lacks a solid 3x3 corner block")
        elif blocks[color][0] == "duplicate":
            errors.append(f"color {color} has multiple solid corner blocks")
    if set(blocks) - set(colors):
        errors.append("corner-block color accounting mismatch")
    if any(color not in blocks or blocks[color][0] == "duplicate" for color in colors):
        return errors
    if _pair_name(value[0] for value in blocks.values()) == "invalid":
        errors.append("the two 3x3 blocks must occupy opposite corners")
        return errors

    scattered = _scatter_by_color(grid, blocks)
    all_sources = set()
    all_destinations = set()
    global_branches = Counter()
    for color in colors:
        cells = scattered[color]
        if not 3 <= len(cells) <= 6:
            errors.append(f"color {color} has {len(cells)} scattered cells; expected 3..6")
        origin = blocks[color][1]
        local_branches = Counter(_classify(r, c, origin) for r, c in cells)
        global_branches.update(local_branches)
        if len(local_branches) < 2:
            errors.append(f"color {color} exposes fewer than two motion branches")
        for source in cells:
            dest = _slide_dest(source[0], source[1], origin, h, w)
            if dest == source:
                errors.append(f"color {color} contains a non-moving scatter at {source}")
            if grid[dest[0]][dest[1]] != BACKGROUND:
                errors.append(f"slide destination {dest} is not background in the input")
            if source in all_sources:
                errors.append(f"duplicate scattered source {source}")
            if dest in all_destinations:
                errors.append(f"multiple scattered cells share destination {dest}")
            if source in all_destinations or dest in all_sources:
                errors.append(f"source/destination interaction at {source}->{dest}")
            all_sources.add(source)
            all_destinations.add(dest)
    if len(global_branches) < 2:
        errors.append("scene exposes fewer than two motion branches")
    if not errors:
        try:
            output = rule_mirror(grid)
        except Exception as exc:  # pragma: no cover - defensive contract
            errors.append(f"rule mirror rejected scene: {type(exc).__name__}: {exc}")
        else:
            if output == grid:
                errors.append("transformation is identity")
            if _nearest_anchor(grid) == output:
                errors.append(
                    "scene does not distinguish own-color blocks from the "
                    "nearest-anchor shortcut"
                )
    return errors


def strict_canonical_like(grid):
    """Strict linked profile used by the semantic census."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if observed["grid_h"] != 9 or observed["grid_w"] != 9:
        reasons.append("canonical grids are 9x9")
    if observed["corner_pair"] != "main":
        reasons.append("canonical colors occupy top-left and bottom-right")
    return reasons


def _has_branch(grid, branch: str) -> bool:
    blocks = _find_blocks(grid)
    if not blocks:
        return False
    for color, cells in _scatter_by_color(grid, blocks).items():
        origin = blocks[color][1]
        if any(_classify(r, c, origin) == branch for r, c in cells):
            return True
    return False


def _blocks_only(grid):
    out = [row[:] for row in grid]
    blocks = _find_blocks(grid)
    for color, cells in _scatter_by_color(grid, blocks).items():
        for r, c in cells:
            out[r][c] = BACKGROUND
    return out


def _cardinal_only(grid):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    blocks = _find_blocks(grid)
    for color, cells in _scatter_by_color(grid, blocks).items():
        origin = blocks[color][1]
        for r, c in cells:
            if _classify(r, c, origin) == "diagonal":
                continue
            dr, dc = _slide_dest(r, c, origin, h, w)
            out[r][c] = BACKGROUND
            out[dr][dc] = color
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _nearest_anchor(grid):
    """Plausible wrong rule: slide every scatter toward the nearest block."""
    out = [row[:] for row in grid]
    if not grid or not grid[0]:
        return out
    h, w = len(grid), len(grid[0])
    blocks = {
        color: value
        for color, value in _find_blocks(grid).items()
        if value[0] != "duplicate"
    }
    if len(blocks) < 2:
        return out
    anchors = sorted(
        blocks.items(),
        key=lambda item: CORNERS.index(item[1][0]),
    )
    moves = []
    for color, cells in _scatter_by_color(grid, blocks).items():
        for r, c in cells:
            _, (_, target_origin) = min(
                anchors,
                key=lambda item: (
                    _distance_to_block(r, c, item[1][1]),
                    CORNERS.index(item[1][0]),
                ),
            )
            moves.append((color, (r, c), _slide_dest(r, c, target_origin, h, w)))
    for _, (r, c), _ in moves:
        out[r][c] = BACKGROUND
    for color, _, (r, c) in moves:
        out[r][c] = color
    return out


def _canonical_main_only(grid):
    """Plausible wrong rule learned from canonical main-diagonal examples."""
    blocks = _find_blocks(grid)
    if _pair_name(value[0] for value in blocks.values()) == "main":
        return rule_mirror(grid)
    return _identity(grid)


SEMANTIC_WITNESSES = {
    "row_slide": lambda grid: _has_branch(grid, "row"),
    "column_slide": lambda grid: _has_branch(grid, "column"),
    "diagonal_slide": lambda grid: _has_branch(grid, "diagonal"),
    "anti_diagonal_pair": lambda grid: observe_overrides(grid).get("corner_pair") == "anti",
    "color_binding": lambda grid: _nearest_anchor(grid) != rule_mirror(grid),
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "blocks_only": _blocks_only,
    "cardinal_only": _cardinal_only,
    "nearest_anchor": _nearest_anchor,
    "canonical_main_only": _canonical_main_only,
}
WITNESS_RIVALS = {
    "row_slide": ["identity", "blocks_only"],
    "column_slide": ["identity", "blocks_only"],
    "diagonal_slide": ["cardinal_only"],
    "anti_diagonal_pair": ["canonical_main_only"],
    "color_binding": ["nearest_anchor"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is sufficient when demos jointly refute the named rivals."""
    reasons = []
    if not demos:
        return ["lesson has no demonstrations"]
    for index, pair in enumerate(demos):
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is structurally invalid: {errors[0]}")
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the rule")
    for branch in BRANCHES:
        if not any(_has_branch(pair["input"], branch) for pair in demos):
            reasons.append(f"demonstrations omit the {branch} branch")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"rival {name!r} survives every demonstration")
    if self_check(query["input"]):
        reasons.append("query is structurally invalid")
    return reasons
