"""Generator for ARC task 47be86674731 / source task 9a4bb226.

Rule: the input contains four isolated, completely filled 3x3 blocks.  Three
blocks use exactly two colors; exactly one block uses three colors.  Return the
three-color block unchanged.

The canonical examples deliberately move the answer through every reading-order
position, so generated lessons do the same.  This makes "pick the first/last
object" shortcuts visibly wrong instead of teaching them by accident.
"""
from __future__ import annotations

import copy
from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "47be86674731"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "fd84c5bef46d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "Find the only filled 3x3 block containing exactly three distinct colors; "
    "the other three filled 3x3 blocks contain exactly two colors. Return the "
    "three-color block unchanged."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly four 4-connected non-zero objects",
    "every non-zero object is a completely filled 3x3 block",
    "exactly one block uses three colors and the other three use two colors",
    "the non-zero palette contains eight or nine colors, matching canonical support",
]

_GRID_LO, _GRID_HI = 12, 18
_TARGET_RANKS = (0, 1, 2, 3)
_PALETTE_MODES = ("nine_nonzero", "eight_nonzero")
_TARGET_DISTRIBUTIONS = ("balanced", "mixed", "skewed")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 15 or rng 12..18",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 15 or rng 12..18",
        "valid": "12..18",
    },
    "target_rank": {
        "type": "int",
        "default": "scheduled 0,2,1,3 reading-order rank",
        "valid": "0..3",
    },
    "palette_mode": {
        "type": "str",
        "default": "scheduled nine_nonzero|eight_nonzero",
        "valid": "nine_nonzero|eight_nonzero",
    },
    "target_distribution": {
        "type": "str",
        "default": "scheduled balanced|mixed|skewed",
        "valid": "balanced|mixed|skewed",
    },
}

# Every declared axis combination is valid; future rejections must therefore be
# treated as checker-visible regressions rather than legacy compatibility noise.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Consecutive four samples mirror the canonical answer-position census:
# train ranks 0,2,1 and test rank 3.  Two profiles stay exactly at the canonical
# 15x15 shape while the others broaden size support without losing the anchor.
_PROFILE_TABLE = (
    (15, 15, 0, "nine_nonzero", "skewed"),
    (15, 15, 2, "eight_nonzero", "balanced"),
    (None, None, 1, "nine_nonzero", "mixed"),
    (None, None, 3, "eight_nonzero", "skewed"),
)
SCHEDULE_PROFILES = tuple(f"profile_{index}" for index in range(len(_PROFILE_TABLE)))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the four-way curriculum schedule to the semantic gate."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, label: str, scheduled: int | None, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if scheduled is None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _draw_scheduled_rank(ctx, scheduled: int) -> int:
    if "target_rank" in ctx.overrides and ctx.overrides["target_rank"] is not None:
        return ctx.draw_int("target_rank", 0, 3)
    return ctx.draw_int("target_rank", scheduled, scheduled)


def _separated(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """True when two 3x3 boxes have at least one blank row/column between."""
    ar, ac = a
    br, bc = b
    return ar + 3 < br or br + 3 < ar or ac + 3 < bc or bc + 3 < ac


def _sample_positions(h: int, w: int, rng) -> list[tuple[int, int]]:
    """Choose four varied 3x3 anchors while preserving four isolated objects."""
    candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    for _attempt in range(200):
        rng.shuffle(candidates)
        chosen: list[tuple[int, int]] = []
        for candidate in candidates:
            if all(_separated(candidate, prior) for prior in chosen):
                chosen.append(candidate)
                if len(chosen) == 4:
                    return sorted(chosen)
    raise RuntimeError(f"could not place four separated 3x3 blocks in {h}x{w}")


def _pattern(palette: tuple[int, ...] | list[int], counts: tuple[int, ...], rng):
    values: list[int] = []
    for color, count in zip(palette, counts):
        values.extend([int(color)] * int(count))
    if len(values) != 9 or len(set(values)) != len(palette):
        raise ValueError("pattern counts must fill 9 cells and use every palette color")
    rng.shuffle(values)
    return [(index // 3, index % 3, value) for index, value in enumerate(values)]


def _target_counts(distribution: str) -> tuple[int, int, int]:
    if distribution == "balanced":
        return (3, 3, 3)
    if distribution == "mixed":
        return (4, 3, 2)
    if distribution == "skewed":
        return (5, 2, 2)
    raise ValueError(f"unknown target_distribution: {distribution!r}")


def _palette_plan(mode: str, rng) -> tuple[list[int], list[tuple[int, int]]]:
    """Return target colors and three two-color distractor palettes."""
    colors = list(range(1, 10))
    rng.shuffle(colors)
    if mode == "nine_nonzero":
        target = colors[:3]
        distractors = [tuple(colors[3:5]), tuple(colors[5:7]), tuple(colors[7:9])]
        return target, distractors
    if mode == "eight_nonzero":
        used = colors[:8]
        target = used[:3]
        distractors = [tuple(used[3:5]), tuple(used[5:7])]
        shared = rng.choice(target)
        distractors.append((used[7], shared))
        rng.shuffle(distractors)
        return target, distractors
    raise ValueError(f"unknown palette_mode: {mode!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _PROFILE_TABLE[int(sample_index) % len(_PROFILE_TABLE)]
    scheduled_h, scheduled_w, scheduled_rank, scheduled_palette, scheduled_dist = profile
    h = _draw_scheduled_int(ctx, "grid_h", scheduled_h, _GRID_LO, _GRID_HI)
    w = _draw_scheduled_int(ctx, "grid_w", scheduled_w, _GRID_LO, _GRID_HI)
    target_rank = _draw_scheduled_rank(ctx, scheduled_rank)
    palette_mode = _draw_scheduled_choice(ctx, "palette_mode", scheduled_palette, _PALETTE_MODES)
    target_distribution = _draw_scheduled_choice(
        ctx, "target_distribution", scheduled_dist, _TARGET_DISTRIBUTIONS
    )

    rng = ctx.draw_rng(f"construction:{difficulty or 'unspecified'}")
    positions = _sample_positions(h, w, rng)
    target_colors, distractor_palettes = _palette_plan(palette_mode, rng)
    target_cells = _pattern(tuple(target_colors), _target_counts(target_distribution), rng)

    grid = full_grid(h, w, 0)
    distractor_index = 0
    for rank, (r0, c0) in enumerate(positions):
        if rank == target_rank:
            cells = target_cells
        else:
            palette = distractor_palettes[distractor_index]
            distractor_index += 1
            # Canonical distractors vary their majority strength.  Keeping both
            # colors present is the only semantic obligation.
            majority = rng.choice((4, 5, 6, 7))
            cells = _pattern(palette, (majority, 9 - majority), rng)
        paint_at(grid, r0, c0, cells)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator emitted invalid grid: " + "; ".join(errors))
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _nonzero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    if not (_GRID_LO <= h <= _GRID_HI):
        errors.append(f"height {h} outside {_GRID_LO}..{_GRID_HI}")
    if not (_GRID_LO <= w <= _GRID_HI):
        errors.append(f"width {w} outside {_GRID_LO}..{_GRID_HI}")

    components = _nonzero_components(grid)
    if len(components) != 4:
        errors.append(f"expected exactly four non-zero objects, got {len(components)}")

    blocks: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        r0, c0, r1, c1 = _bbox(cells)
        if len(cells) != 9 or (r1 - r0 + 1, c1 - c0 + 1) != (3, 3):
            errors.append(
                f"object {index} must be a filled 3x3 block; "
                f"cells={len(cells)} bbox={(r1 - r0 + 1, c1 - c0 + 1)}"
            )
            continue
        if any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
            errors.append(f"object {index} has a hole inside its 3x3 bounding box")
            continue
        values = [grid[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        blocks.append(
            {
                "bbox": (r0, c0, r1, c1),
                "colors": sorted(set(values)),
                "counts": Counter(values),
                "grid": [list(grid[r][c0 : c1 + 1]) for r in range(r0, r1 + 1)],
            }
        )

    blocks.sort(key=lambda block: (block["bbox"][0], block["bbox"][1]))
    target_indices = [index for index, block in enumerate(blocks) if len(block["colors"]) == 3]
    distractor_indices = [index for index, block in enumerate(blocks) if len(block["colors"]) == 2]
    bad_color_counts = [
        (index, len(block["colors"]))
        for index, block in enumerate(blocks)
        if len(block["colors"]) not in (2, 3)
    ]
    if bad_color_counts:
        errors.append(f"blocks must use exactly two or three colors: {bad_color_counts}")
    if len(target_indices) != 1:
        errors.append(f"expected exactly one three-color block, got {len(target_indices)}")
    if len(distractor_indices) != 3:
        errors.append(f"expected exactly three two-color distractor blocks, got {len(distractor_indices)}")

    nonzero_palette = sorted({value for row in grid for value in row if value != 0})
    if len(nonzero_palette) not in (8, 9):
        errors.append(
            f"expected eight or nine non-zero colors as in canonical inputs, got {len(nonzero_palette)}"
        )

    target_rank = target_indices[0] if len(target_indices) == 1 else None
    target_distribution = None
    if target_rank is not None:
        target_counts = sorted(blocks[target_rank]["counts"].values(), reverse=True)
        if target_counts == [3, 3, 3]:
            target_distribution = "balanced"
        elif target_counts == [4, 3, 2]:
            target_distribution = "mixed"
        elif target_counts == [5, 2, 2]:
            target_distribution = "skewed"
        else:
            # Canonical targets include all of these named families, but the
            # authority rule permits any 3-color arrangement.  self_check must
            # therefore accept other canonical-valid count splits too.
            target_distribution = "other"

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "blocks": blocks,
        "target_rank": target_rank,
        "target_distribution": target_distribution,
        "nonzero_palette": nonzero_palette,
        "palette_mode": (
            "nine_nonzero" if len(nonzero_palette) == 9 else
            "eight_nonzero" if len(nonzero_palette) == 8 else None
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority grammar, including all canonical inputs."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Require the exact canonical 15x15 profile on top of the rule grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) != (15, 15):
        errors.append(f"shape {(len(grid), len(grid[0]))} is generalized, not canonical 15x15")
    return errors


def semantic_observables(grid) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "block_count": len(facts["blocks"]),
        "target_rank": facts["target_rank"],
        "palette_mode": facts["palette_mode"],
        "target_distribution": facts["target_distribution"],
        "block_color_counts": tuple(len(block["colors"]) for block in facts["blocks"]),
        "nonzero_palette_size": len(facts["nonzero_palette"]),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    return {axis: facts[axis] for axis in AXES}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only Python mirror; canonical Racket remains output authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    target_rank = facts["target_rank"]
    assert target_rank is not None
    return copy.deepcopy(facts["blocks"][target_rank]["grid"])


def _fixed_rank_solver(rank: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def solve(grid: list[list[int]]) -> list[list[int]]:
        facts = _analysis(grid)
        if facts["errors"] or len(facts["blocks"]) <= rank:
            return copy.deepcopy(grid)
        return copy.deepcopy(facts["blocks"][rank]["grid"])
    return solve


SEMANTIC_RIVALS = {
    "always_first_block": _fixed_rank_solver(0),
    "always_second_block": _fixed_rank_solver(1),
    "always_third_block": _fixed_rank_solver(2),
    "always_fourth_block": _fixed_rank_solver(3),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _target_rank_witness(rank: int) -> Callable[[list[list[int]]], bool]:
    return lambda grid: not self_check(grid) and semantic_observables(grid)["target_rank"] == rank


SEMANTIC_WITNESSES = {
    "target_first": _target_rank_witness(0),
    "target_second": _target_rank_witness(1),
    "target_third": _target_rank_witness(2),
    "target_fourth": _target_rank_witness(3),
}
WITNESS_RIVALS = {
    "target_first": ["always_second_block", "always_fourth_block"],
    "target_second": ["always_first_block", "always_third_block"],
    "target_third": ["always_first_block", "always_fourth_block"],
    "target_fourth": ["always_first_block", "always_second_block"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a fixed-position selector can survive the demos."""
    reasons: list[str] = []
    ranks: set[int] = set()
    palette_modes: set[str] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is malformed")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output does not match the three-color selector")
        facts = semantic_observables(demo["input"])
        ranks.add(int(facts["target_rank"]))
        palette_modes.add(str(facts["palette_mode"]))
    if len(ranks) < 3:
        reasons.append(f"demos expose only {len(ranks)} target positions; need at least three")
    if palette_modes != set(_PALETTE_MODES):
        reasons.append("demos do not cover both canonical palette-size modes")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    official_query = rule_mirror(query["input"])
    if official_query != query["output"]:
        reasons.append("query output does not match the three-color selector")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(demo, dict)
            and "input" in demo
            and competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != official_query:
            reasons.append(f"competing rule '{name}' fits every demo but changes the query")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named near-misses that a structural self_check must reject."""
    valid = generate(99173, 0, difficulty="medium")
    facts = _analysis(valid)
    target_rank = facts["target_rank"]
    assert target_rank is not None
    target_bbox = facts["blocks"][target_rank]["bbox"]
    r0, c0, _, _ = target_bbox

    fixtures: list[tuple[str, list[list[int]]]] = []

    missing_target_cell = copy.deepcopy(valid)
    missing_target_cell[r0 + 1][c0 + 1] = 0
    fixtures.append(("target_not_filled_3x3", missing_target_cell))

    target_two_colors = copy.deepcopy(valid)
    target_colors = facts["blocks"][target_rank]["colors"]
    replaced, replacement = target_colors[-1], target_colors[0]
    for r in range(r0, r0 + 3):
        for c in range(c0, c0 + 3):
            if target_two_colors[r][c] == replaced:
                target_two_colors[r][c] = replacement
    fixtures.append(("no_three_color_target", target_two_colors))

    extra_three_color = copy.deepcopy(valid)
    distractor = next(block for i, block in enumerate(facts["blocks"]) if i != target_rank)
    dr0, dc0, _, _ = distractor["bbox"]
    absent = next(color for color in range(1, 10) if color not in distractor["colors"])
    extra_three_color[dr0][dc0] = absent
    fixtures.append(("two_three_color_targets", extra_three_color))

    isolated_noise = copy.deepcopy(valid)
    for r in range(len(isolated_noise)):
        for c in range(len(isolated_noise[0])):
            if isolated_noise[r][c] != 0:
                continue
            if all(
                not (0 <= r + dr < len(isolated_noise) and 0 <= c + dc < len(isolated_noise[0]))
                or isolated_noise[r + dr][c + dc] == 0
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                isolated_noise[r][c] = 1
                fixtures.append(("isolated_nonzero_noise", isolated_noise))
                return fixtures
    raise AssertionError("could not construct isolated-noise mutation fixture")
