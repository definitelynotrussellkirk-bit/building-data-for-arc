"""Generator for S19_H4: choose the candidate whose occupancy XORs with source to target.

The grid contains five or six 4-column panels separated by full-height maroon
(9) columns. Panel 0 is the source set, panel 1 is the target set, and the
remaining panels are candidates. Exactly one candidate C satisfies
``source XOR C == target``. The Racket authority outputs that candidate's
occupied cells in cyan (8).

The four-sample schedule deliberately covers mixed XOR, removal-only,
addition-only, and disjoint/union cases. This prevents the canonical-only
shortcut ``source - target`` from masquerading as XOR.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5bf6e2e7ed82"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "74937943805c"

SUMMARY = (
    "Split the input at full-height color-9 columns. Treat nonzero, non-9 "
    "cells as sets. The first panel is SOURCE and the second is TARGET. "
    "Choose the unique later panel C for which SOURCE symmetric-difference C "
    "equals TARGET, then return C's occupied cells recolored cyan (8)."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

INVARIANTS = [
    "background is 0 and separators are single full-height color-9 columns",
    "five or six equal 4-column panels; panel 0 is source and panel 1 is target",
    "every panel motif is nonempty and monochrome",
    "candidate colors are distinct from source/target colors and from one another",
    "exactly one candidate satisfies source XOR candidate == target",
    "the four-sample schedule covers mixed, removal-only, addition-only, and disjoint XOR relations",
]

# All declared boundary combinations are supported; an empty declaration opts
# the override checker into strict incompatibility classification.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

AXES = {
    "panel_h": {"type": "int", "default": "scheduled 4|5", "valid": "4..5"},
    "n_panels": {"type": "int", "default": "scheduled 5|6", "valid": "5..6"},
    "source_size": {"type": "int", "default": "scheduled 3..5", "valid": "2..7"},
    "target_size": {"type": "int", "default": "scheduled 2..6", "valid": "1..7"},
    "match_position": {
        "type": "str",
        "default": "scheduled first|middle|last",
        "valid": "first|middle|last",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled canonical|varied",
        "valid": "canonical|varied",
    },
}

# Consecutive windows of EXAMPLES_NEEDED=4 visit every profile exactly once.
# profile 1 is a canonical-scale anchor; the others falsify canonical shortcuts.
_SCHEDULE = (
    # relation, panel_h, n_panels, source_size, target_size, match_position, palette_kind, match_color_rank
    ("mixed", 5, 6, 5, 4, "first", "varied", "lowest"),
    ("target_subset", 4, 5, 4, 2, "middle", "canonical", "highest"),
    ("source_subset", 5, 6, 3, 6, "last", "varied", "middle"),
    ("disjoint", 4, 5, 4, 4, "middle", "canonical", "highest"),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % len(_SCHEDULE)


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, options, scheduled):
    if label in ctx.overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _split_panels(grid: list[list[int]]) -> tuple[list[int], list[list[list[int]]]]:
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    panels: list[list[list[int]]] = []
    start = 0
    for c in dividers + [w]:
        panels.append([row[start:c] for row in grid])
        start = c + 1
    return dividers, panels


def _panel_cells(panel: list[list[int]]) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    )


def _panel_colors(panel: list[list[int]]) -> frozenset[int]:
    return frozenset(value for row in panel for value in row if value not in (0, 9))


def _match_position(index: int, candidate_count: int) -> str:
    if index == 0:
        return "first"
    if index == candidate_count - 1:
        return "last"
    return "middle"


def _match_index(position: str, candidate_count: int) -> int:
    if position == "first":
        return 0
    if position == "last":
        return candidate_count - 1
    return (candidate_count - 1) // 2


def _relation_kind(source: frozenset, target: frozenset) -> str:
    if source.isdisjoint(target):
        return "disjoint"
    if target < source:
        return "target_subset"
    if source < target:
        return "source_subset"
    return "mixed"


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a nonempty list of nonempty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")

    h = len(grid)
    if h not in (4, 5):
        errors.append(f"panel height must be 4 or 5, got {h}")

    dividers, panels = _split_panels(grid)
    if any(b - a == 1 for a, b in zip(dividers, dividers[1:])):
        errors.append("divider runs must be exactly one column wide")
    if len(panels) not in (5, 6):
        errors.append(f"expected 5 or 6 panels, found {len(panels)}")
    widths = [len(panel[0]) if panel and panel[0] else 0 for panel in panels]
    if any(panel_width != 4 for panel_width in widths):
        errors.append(f"all panel widths must be 4, got {widths}")
    if any(9 in row for panel in panels for row in panel):
        errors.append("color 9 may appear only in full-height divider columns")

    cells = [_panel_cells(panel) for panel in panels]
    colors = [_panel_colors(panel) for panel in panels]
    for index, (panel_cells, panel_colors) in enumerate(zip(cells, colors)):
        if not panel_cells:
            errors.append(f"panel {index} is empty")
        if len(panel_colors) != 1:
            errors.append(f"panel {index} must be monochrome, got colors {sorted(panel_colors)}")

    if len(panels) >= 4 and all(cells[:2]):
        source, target = cells[0], cells[1]
        if source == target:
            errors.append("source and target occupancies must differ")
        candidates = cells[2:]
        if len(set(candidates)) != len(candidates):
            errors.append("candidate occupancies must be distinct")
        matches = [i for i, candidate in enumerate(candidates) if source ^ candidate == target]
        if len(matches) != 1:
            errors.append(f"expected exactly one XOR-matching candidate, found {matches}")
    else:
        source = target = frozenset()
        candidates = []
        matches = []

    if len(colors) >= 4 and all(len(panel_colors) == 1 for panel_colors in colors):
        scalar_colors = [next(iter(panel_colors)) for panel_colors in colors]
        candidate_colors = scalar_colors[2:]
        if len(set(candidate_colors)) != len(candidate_colors):
            errors.append("candidate panel colors must be distinct")
        if set(candidate_colors) & set(scalar_colors[:2]):
            errors.append("candidate colors must differ from source and target colors")
    else:
        scalar_colors = []

    return {
        "errors": errors,
        "grid": grid,
        "height": h,
        "width": width,
        "dividers": dividers,
        "panels": panels,
        "cells": cells,
        "colors": scalar_colors,
        "source": source,
        "target": target,
        "candidates": candidates,
        "match_indices": matches,
        "match_index": matches[0] if len(matches) == 1 else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete panel grammar and unique XOR semantics."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact declared axis from a valid materialized grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(facts["errors"]))
    colors = facts["colors"]
    palette_kind = "canonical" if colors[0] == colors[1] else "varied"
    return {
        "panel_h": facts["height"],
        "n_panels": len(facts["panels"]),
        "source_size": len(facts["source"]),
        "target_size": len(facts["target"]),
        "match_position": _match_position(facts["match_index"], len(facts["candidates"])),
        "palette_kind": palette_kind,
    }


def _make_relation_sets(
    positions: list[tuple[int, int]],
    source_size: int,
    target_size: int,
    relation: str,
    rng,
) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    if relation == "disjoint":
        chosen = rng.sample(positions, source_size + target_size)
        return frozenset(chosen[:source_size]), frozenset(chosen[source_size:])

    if relation == "target_subset" and target_size < source_size:
        source = frozenset(rng.sample(positions, source_size))
        target = frozenset(rng.sample(sorted(source), target_size))
        return source, target

    if relation == "source_subset" and source_size < target_size:
        target = frozenset(rng.sample(positions, target_size))
        source = frozenset(rng.sample(sorted(target), source_size))
        return source, target

    if relation == "mixed" and source_size >= 2 and target_size >= 2:
        overlap_size = rng.randint(1, min(source_size, target_size) - 1)
        overlap = set(rng.sample(positions, overlap_size))
        remaining = [cell for cell in positions if cell not in overlap]
        source_only = set(rng.sample(remaining, source_size - overlap_size))
        remaining = [cell for cell in remaining if cell not in source_only]
        target_only = set(rng.sample(remaining, target_size - overlap_size))
        return frozenset(overlap | source_only), frozenset(overlap | target_only)

    # Override combinations may make the scheduled relation impossible. The
    # axis values are still honored exactly; choose any non-degenerate pair.
    for _ in range(200):
        source = frozenset(rng.sample(positions, source_size))
        target = frozenset(rng.sample(positions, target_size))
        if source != target and source ^ target:
            return source, target
    raise ValueError("could not construct distinct nonempty source/target sets")


def _near_miss(
    true_candidate: frozenset[tuple[int, int]],
    positions: list[tuple[int, int]],
    forbidden: set[frozenset[tuple[int, int]]],
    rng,
) -> frozenset[tuple[int, int]]:
    order = list(positions)
    rng.shuffle(order)
    for cell in order:
        candidate = frozenset(set(true_candidate) ^ {cell})
        if candidate and candidate not in forbidden:
            return candidate
    raise ValueError("could not construct one-cell near-miss distractor")


def _same_count_decoy(
    size: int,
    positions: list[tuple[int, int]],
    forbidden: set[frozenset[tuple[int, int]]],
    rng,
) -> frozenset[tuple[int, int]]:
    for _ in range(200):
        candidate = frozenset(rng.sample(positions, size))
        if candidate and candidate not in forbidden:
            return candidate
    raise ValueError("could not construct same-count distractor")


def _distractor_pool(
    source: frozenset[tuple[int, int]],
    target: frozenset[tuple[int, int]],
    true_candidate: frozenset[tuple[int, int]],
    positions: list[tuple[int, int]],
    profile: int,
    rng,
) -> list[frozenset[tuple[int, int]]]:
    named = {
        "target": target,
        "source": source,
        "difference": source - target,
        "union": source | target,
    }
    priorities = (
        ("union", "difference", "same_count", "target", "source", "near"),
        ("target", "source", "near", "same_count", "union", "difference"),
        ("target", "source", "near", "same_count", "difference", "union"),
        ("source", "target", "same_count", "near", "difference", "union"),
    )[profile]

    forbidden = {true_candidate}
    out: list[frozenset[tuple[int, int]]] = []
    for name in priorities:
        if name == "same_count":
            candidate = _same_count_decoy(len(true_candidate), positions, forbidden, rng)
        elif name == "near":
            candidate = _near_miss(true_candidate, positions, forbidden, rng)
        else:
            candidate = frozenset(named[name])
        if candidate and candidate not in forbidden:
            out.append(candidate)
            forbidden.add(candidate)
    return out


def _transform_for_band(
    cells: frozenset[tuple[int, int]], panel_h: int, difficulty
) -> frozenset[tuple[int, int]]:
    """Apply a band-specific bijection so difficulty is not a dead control."""
    if difficulty == "medium":
        return frozenset((r, 3 - c) for r, c in cells)
    if difficulty == "hard":
        return frozenset((panel_h - 1 - r, c) for r, c in cells)
    return cells


def _assign_panel_colors(
    palette_kind: str,
    candidate_count: int,
    match_index: int,
    match_rank: str,
    rng,
) -> tuple[int, int, list[int]]:
    needed = candidate_count + (1 if palette_kind == "canonical" else 2)
    chosen = rng.sample(list(range(1, 8)), needed)
    if palette_kind == "canonical":
        source_color = target_color = chosen[0]
        candidate_palette = chosen[1:]
    else:
        source_color, target_color = chosen[:2]
        candidate_palette = chosen[2:]

    ordered = sorted(candidate_palette)
    if match_rank == "lowest":
        match_color = ordered[0]
    elif match_rank == "highest":
        match_color = ordered[-1]
    else:
        match_color = ordered[len(ordered) // 2]
    remaining = [color for color in candidate_palette if color != match_color]
    rng.shuffle(remaining)
    candidate_colors: list[int] = []
    for index in range(candidate_count):
        candidate_colors.append(match_color if index == match_index else remaining.pop())
    return source_color, target_color, candidate_colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    profile = schedule_profile(seed, sample_index, difficulty)
    relation, scheduled_h, scheduled_n, scheduled_source, scheduled_target, scheduled_position, scheduled_palette, match_rank = _SCHEDULE[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    panel_h = _draw_scheduled_int(ctx, "panel_h", 4, 5, scheduled_h)
    n_panels = _draw_scheduled_int(ctx, "n_panels", 5, 6, scheduled_n)
    source_size = _draw_scheduled_int(ctx, "source_size", 2, 7, scheduled_source)
    target_size = _draw_scheduled_int(ctx, "target_size", 1, 7, scheduled_target)
    match_position = _draw_scheduled_choice(
        ctx, "match_position", ("first", "middle", "last"), scheduled_position
    )
    palette_kind = _draw_scheduled_choice(
        ctx, "palette_kind", ("canonical", "varied"), scheduled_palette
    )

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    positions = [(r, c) for r in range(panel_h) for c in range(4)]
    source, target = _make_relation_sets(
        positions, source_size, target_size, relation, layout_rng
    )
    true_candidate = source ^ target
    candidate_count = n_panels - 2
    match_index = _match_index(match_position, candidate_count)
    distractors = _distractor_pool(
        source, target, true_candidate, positions, profile, layout_rng
    )
    if len(distractors) < candidate_count - 1:
        raise ValueError("insufficient distinct distractors")
    distractors = distractors[: candidate_count - 1]

    candidates: list[frozenset[tuple[int, int]]] = []
    distractor_iter = iter(distractors)
    for index in range(candidate_count):
        candidates.append(true_candidate if index == match_index else next(distractor_iter))

    source = _transform_for_band(source, panel_h, difficulty)
    target = _transform_for_band(target, panel_h, difficulty)
    candidates = [
        _transform_for_band(candidate, panel_h, difficulty)
        for candidate in candidates
    ]

    source_color, target_color, candidate_colors = _assign_panel_colors(
        palette_kind, candidate_count, match_index, match_rank, palette_rng
    )
    width = n_panels * 4 + (n_panels - 1)
    grid = full_grid(panel_h, width, 0)
    for separator in range(1, n_panels):
        column = separator * 5 - 1
        for row in range(panel_h):
            grid[row][column] = 9

    def paint(panel_index: int, cells: frozenset[tuple[int, int]], color: int) -> None:
        c0 = panel_index * 5
        for r, c in cells:
            grid[r][c0 + c] = color

    paint(0, source, source_color)
    paint(1, target, target_color)
    for index, (candidate, color) in enumerate(zip(candidates, candidate_colors), start=2):
        paint(index, candidate, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid XOR lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "panel_h": panel_h,
        "n_panels": n_panels,
        "source_size": source_size,
        "target_size": target_size,
        "match_position": match_position,
        "palette_kind": palette_kind,
    }
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    return grid


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _render_candidate(facts: dict[str, Any], candidate_index: int) -> list[list[int]]:
    out = full_grid(facts["height"], 4, 0)
    for r, c in facts["candidates"][candidate_index]:
        out[r][c] = 8
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror only; the Racket rule remains output authority."""
    facts = _valid_facts(grid)
    if facts is None:
        raise ValueError("grid is outside the generator grammar")
    return _render_candidate(facts, facts["match_index"])


def _choose_by_set_score(grid, ideal_fn: Callable[[dict[str, Any]], frozenset]):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    ideal = ideal_fn(facts)
    index = min(
        range(len(facts["candidates"])),
        key=lambda i: (len(facts["candidates"][i] ^ ideal), i),
    )
    return _render_candidate(facts, index)


def _rival_first_candidate(grid):
    facts = _valid_facts(grid)
    return None if facts is None else _render_candidate(facts, 0)


def _rival_middle_candidate(grid):
    facts = _valid_facts(grid)
    return None if facts is None else _render_candidate(facts, (len(facts["candidates"]) - 1) // 2)


def _rival_last_candidate(grid):
    facts = _valid_facts(grid)
    return None if facts is None else _render_candidate(facts, len(facts["candidates"]) - 1)


def _rival_target_copy(grid):
    return _choose_by_set_score(grid, lambda facts: facts["target"])


def _rival_source_copy(grid):
    return _choose_by_set_score(grid, lambda facts: facts["source"])


def _rival_set_difference(grid):
    return _choose_by_set_score(grid, lambda facts: facts["source"] - facts["target"])


def _rival_union(grid):
    return _choose_by_set_score(grid, lambda facts: facts["source"] | facts["target"])


def _rival_lowest_color(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    index = min(range(len(facts["candidates"])), key=lambda i: (facts["colors"][i + 2], i))
    return _render_candidate(facts, index)


def _rival_highest_color(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    index = min(range(len(facts["candidates"])), key=lambda i: (-facts["colors"][i + 2], i))
    return _render_candidate(facts, index)


def _rival_smallest_candidate(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    index = min(range(len(facts["candidates"])), key=lambda i: (len(facts["candidates"][i]), i))
    return _render_candidate(facts, index)


def _rival_largest_candidate(grid):
    facts = _valid_facts(grid)
    if facts is None:
        return None
    index = min(range(len(facts["candidates"])), key=lambda i: (-len(facts["candidates"][i]), i))
    return _render_candidate(facts, index)


def _disagrees(grid, rival: Callable) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _relation_is(name: str):
    return lambda grid: bool(
        (facts := _valid_facts(grid))
        and _relation_kind(facts["source"], facts["target"]) == name
    )


def _palette_is(name: str):
    return lambda grid: bool(
        (facts := _valid_facts(grid))
        and ("canonical" if facts["colors"][0] == facts["colors"][1] else "varied") == name
    )


def _match_is(name: str):
    return lambda grid: bool(
        (facts := _valid_facts(grid))
        and _match_position(facts["match_index"], len(facts["candidates"])) == name
    )


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 4x24, six-color, removal-only manifold."""
    facts = _analyze(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if facts["height"] != 4 or len(facts["panels"]) != 5:
        reasons.append("canonical scale is five 4x4 panels")
    if len({value for row in grid for value in row}) != 6:
        reasons.append("canonical inputs use six total colors")
    if facts["colors"][0] != facts["colors"][1]:
        reasons.append("canonical source and target share a color")
    if _relation_kind(facts["source"], facts["target"]) != "target_subset":
        reasons.append("canonical target is a proper subset of source")
    return reasons


SEMANTIC_RIVALS = {
    "first_candidate": _rival_first_candidate,
    "middle_candidate": _rival_middle_candidate,
    "last_candidate": _rival_last_candidate,
    "target_copy": _rival_target_copy,
    "source_copy": _rival_source_copy,
    "set_difference_only": _rival_set_difference,
    "union_only": _rival_union,
    "lowest_color": _rival_lowest_color,
    "highest_color": _rival_highest_color,
    "smallest_candidate": _rival_smallest_candidate,
    "largest_candidate": _rival_largest_candidate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All three canonical pairs have target ⊂ source, so this rival reproduces
    # them exactly. Mixed/addition/disjoint generated profiles must kill it.
    "set_difference_only": _rival_set_difference,
}

SEMANTIC_WITNESSES = {
    "canonical_profile_anchor": lambda grid: strict_canonical_like(grid) == [],
    "mixed_add_and_remove": _relation_is("mixed"),
    "removal_only": _relation_is("target_subset"),
    "addition_only": _relation_is("source_subset"),
    "disjoint_union_case": _relation_is("disjoint"),
    "matching_candidate_first": _match_is("first"),
    "matching_candidate_middle": _match_is("middle"),
    "matching_candidate_last": _match_is("last"),
    "canonical_palette": _palette_is("canonical"),
    "varied_palette": _palette_is("varied"),
    "first_position_rebutted": lambda grid: _disagrees(grid, _rival_first_candidate),
    "last_position_rebutted": lambda grid: _disagrees(grid, _rival_last_candidate),
    "lowest_color_rebutted": lambda grid: _disagrees(grid, _rival_lowest_color),
    "highest_color_rebutted": lambda grid: _disagrees(grid, _rival_highest_color),
    "smallest_size_rebutted": lambda grid: _disagrees(grid, _rival_smallest_candidate),
    "largest_size_rebutted": lambda grid: _disagrees(grid, _rival_largest_candidate),
    "difference_shortcut_rebutted": lambda grid: _disagrees(grid, _rival_set_difference),
    "union_shortcut_rebutted": lambda grid: _disagrees(grid, _rival_union),
    "target_copy_rebutted": lambda grid: _disagrees(grid, _rival_target_copy),
    "source_copy_rebutted": lambda grid: _disagrees(grid, _rival_source_copy),
}

WITNESS_RIVALS = {
    "canonical_profile_anchor": ["lowest_color"],
    "mixed_add_and_remove": ["set_difference_only", "union_only"],
    "removal_only": ["union_only"],
    "addition_only": ["union_only"],
    "disjoint_union_case": ["set_difference_only"],
    "matching_candidate_first": ["last_candidate"],
    "matching_candidate_middle": ["first_candidate", "last_candidate"],
    "matching_candidate_last": ["first_candidate"],
    "canonical_palette": ["lowest_color"],
    "varied_palette": ["target_copy"],
    "first_position_rebutted": ["first_candidate"],
    "last_position_rebutted": ["last_candidate"],
    "lowest_color_rebutted": ["lowest_color"],
    "highest_color_rebutted": ["highest_color"],
    "smallest_size_rebutted": ["smallest_candidate"],
    "largest_size_rebutted": ["largest_candidate"],
    "difference_shortcut_rebutted": ["set_difference_only"],
    "union_shortcut_rebutted": ["union_only"],
    "target_copy_rebutted": ["target_copy"],
    "source_copy_rebutted": ["source_copy"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives all demos."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with XOR rule")
    try:
        query_expected = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons
    if query.get("output") != query_expected:
        reasons.append("query output disagrees with XOR rule")
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair.get("output") for pair in demos)
            if survives and rival(query["input"]) != query_expected:
                reasons.append(
                    f"competing rule {name!r} fits every demo but answers the query differently"
                )
        except Exception as exc:  # fail loud in the hook contract
            reasons.append(f"competing rule {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
