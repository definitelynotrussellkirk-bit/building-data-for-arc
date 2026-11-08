"""Generator for ARC task 6c434453 / canonical id 1279f507a3eb.

Rule: every exact 3x3 blue(1) frame with a zero center becomes a red(2)
plus: the four corners are erased, while the four side midpoints and center
become red.  Every other blue shape is preserved.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1279f507a3eb"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "8a3979ab592a"

SUMMARY = (
    "A 10-12 by 10-12 zero-background binary grid contains one or two exact "
    "3x3 blue(1) hollow frames plus two or three separated non-frame blue "
    "objects. Every exact frame is replaced by a red(2) plus (corners erased; "
    "side midpoints and center painted red), while all non-frame blue objects "
    "remain unchanged."
)

INVARIANTS = [
    "input palette is exactly background 0 and blue 1",
    "there are 1..2 isolated exact 3x3 hollow blue frames",
    "there are 2..3 separated non-frame blue distractor objects",
    "target frame centers start at 0 and no distractor occupies a target 3x3 box",
    "normal draws visibly exercise the transformation and retain unchanged blue distractors",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical-anchored profile", "valid": "10..12"},
    "grid_w": {"type": "int", "default": "scheduled canonical-anchored profile", "valid": "10..12"},
    "n_rings": {"type": "int", "default": "scheduled 1/2 alternation", "valid": "1..2"},
    "n_distractors": {"type": "int", "default": "scheduled 2/3 alternation", "valid": "2..3"},
    "edge_ring": {"type": "bool", "default": "scheduled edge/interior coverage", "valid": "false|true"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

# Adjacent profiles alternate 2-ring / 1-ring scenes.  Therefore every
# consecutive two-demo lesson contains a counterexample to the public-data
# shortcut "only transform when exactly two rings are present".  Three of six
# profiles retain the canonical 10x10 binary mechanical profile. Edge coverage
# is arranged with no two consecutive edge-free profiles while deliberately
# breaking any edge_ring <-> n_rings correlation.
_PROFILES = (
    {"grid_h": 10, "grid_w": 10, "n_rings": 2, "n_distractors": 3, "edge_ring": True},
    {"grid_h": 10, "grid_w": 10, "n_rings": 1, "n_distractors": 2, "edge_ring": False},
    {"grid_h": 11, "grid_w": 10, "n_rings": 2, "n_distractors": 2, "edge_ring": True},
    {"grid_h": 10, "grid_w": 10, "n_rings": 1, "n_distractors": 3, "edge_ring": True},
    {"grid_h": 10, "grid_w": 12, "n_rings": 2, "n_distractors": 3, "edge_ring": False},
    {"grid_h": 12, "grid_w": 10, "n_rings": 1, "n_distractors": 2, "edge_ring": True},
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))

_RING = tuple(
    (dr, dc)
    for dr in range(3)
    for dc in range(3)
    if (dr, dc) != (1, 1)
)
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Canonical inputs use 2-, 4-, and 5-cell non-target components.  Keep the same
# scale and include a 3x3-bbox plus/T-like object so "any 3x3 blue object" is a
# visibly false rival rule.
_DECOY_SHAPES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),  # plus, 5 cells, 3x3 bbox
    ((0, 0), (0, 1), (1, 0), (1, 1)),          # 2x2 block, 4 cells
    ((0, 0), (0, 1)),                           # domino, 2 cells
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic semantic-curriculum profile index."""
    del seed
    offsets = {None: 0, "easy": 0, "medium": 2, "hard": 4}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + offsets[difficulty]) % len(_PROFILES)


def _draw_profile_int(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_profile_bool(ctx, overrides, name: str, default: bool) -> bool:
    if name in overrides and overrides[name] is not None:
        return bool(ctx.draw_choice(name, (False, True)))
    return bool(ctx.draw_choice(name, (default,)))


def _shape_cells(shape, top: int, left: int) -> set[tuple[int, int]]:
    return {(top + dr, left + dc) for dr, dc in shape}


def _ring_box(top: int, left: int) -> set[tuple[int, int]]:
    return {(top + dr, left + dc) for dr in range(3) for dc in range(3)}


def _in_bounds(cells: set[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _separate_from_occupied(
    cells: set[tuple[int, int]], occupied: set[tuple[int, int]]
) -> bool:
    if cells & occupied:
        return False
    return not any(
        (r + dr, c + dc) in occupied
        for r, c in cells
        for dr, dc in _ORTHOGONALS
    )


def _ring_candidates(h: int, w: int, *, edge: bool) -> list[tuple[int, int]]:
    candidates = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            touches = r0 == 0 or c0 == 0 or r0 == h - 3 or c0 == w - 3
            if touches == edge:
                candidates.append((r0, c0))
    return candidates


def _all_ring_candidates(h: int, w: int) -> list[tuple[int, int]]:
    return [(r0, c0) for r0 in range(h - 2) for c0 in range(w - 2)]


def _decoy_candidates(shape, h: int, w: int) -> list[tuple[int, int]]:
    sh = max(dr for dr, _ in shape) + 1
    sw = max(dc for _, dc in shape) + 1
    return [(r0, c0) for r0 in range(h - sh + 1) for c0 in range(w - sw + 1)]


def _place_scene(rng, h: int, w: int, n_rings: int, n_distractors: int,
                 edge_ring: bool) -> list[list[int]]:
    """Search deterministically for an exact-axis scene; fail rather than lie."""
    for _scene_attempt in range(200):
        grid = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        reserved_ring_boxes: set[tuple[int, int]] = set()
        ring_tops: list[tuple[int, int]] = []

        # The first ring realizes the edge_ring axis. Subsequent rings may be
        # anywhere when edge_ring=True, but all must be interior when False.
        ok = True
        for ring_index in range(n_rings):
            if edge_ring and ring_index == 0:
                candidates = _ring_candidates(h, w, edge=True)
            elif edge_ring:
                candidates = _all_ring_candidates(h, w)
            else:
                candidates = _ring_candidates(h, w, edge=False)
            rng.shuffle(candidates)
            placed = False
            for r0, c0 in candidates:
                box = _ring_box(r0, c0)
                cells = _shape_cells(_RING, r0, c0)
                if box & reserved_ring_boxes:
                    continue
                if not _separate_from_occupied(cells, occupied):
                    continue
                if box & occupied:
                    continue
                for r, c in cells:
                    grid[r][c] = 1
                occupied |= cells
                reserved_ring_boxes |= box
                ring_tops.append((r0, c0))
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        # Always include the plus-shaped near-miss first; then canonical-scale
        # 2x2 and domino distractors. Randomly rotate the ordering of the latter
        # two so layouts do not leak a fixed component-size position.
        shapes = list(_DECOY_SHAPES[:n_distractors])
        if n_distractors >= 3 and rng.random() < 0.5:
            shapes[1], shapes[2] = shapes[2], shapes[1]
        for shape in shapes:
            candidates = _decoy_candidates(shape, h, w)
            rng.shuffle(candidates)
            placed = False
            for r0, c0 in candidates:
                cells = _shape_cells(shape, r0, c0)
                if not _in_bounds(cells, h, w):
                    continue
                if cells & reserved_ring_boxes:
                    continue
                if not _separate_from_occupied(cells, occupied):
                    continue
                for r, c in cells:
                    grid[r][c] = 1
                occupied |= cells
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue

        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        if analysis["n_rings"] != n_rings:
            continue
        if analysis["n_distractors"] != n_distractors:
            continue
        if analysis["edge_ring"] != edge_ring:
            continue
        return grid
    raise ValueError(
        "could not place requested scene without hiding or inventing a 3x3 frame: "
        f"{h=} {w=} {n_rings=} {n_distractors=} {edge_ring=}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    profile = _PROFILES[schedule_profile(seed, sample_index, difficulty)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", profile["grid_h"], 10, 12)
    w = _draw_profile_int(ctx, overrides, "grid_w", profile["grid_w"], 10, 12)
    n_rings = _draw_profile_int(ctx, overrides, "n_rings", profile["n_rings"], 1, 2)
    n_distractors = _draw_profile_int(
        ctx, overrides, "n_distractors", profile["n_distractors"], 2, 3
    )
    edge_ring = _draw_profile_bool(ctx, overrides, "edge_ring", profile["edge_ring"])

    grid = _place_scene(
        ctx.draw_rng("layout"), h, w, n_rings, n_distractors, edge_ring
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid frame lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _ORTHOGONALS:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        result.append(comp)
    return result


def _ring_toplefts(grid) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    out = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            if grid[r0 + 1][c0 + 1] != 0:
                continue
            if all(grid[r0 + dr][c0 + dc] == 1 for dr, dc in _RING):
                out.append((r0, c0))
    return out


def _component_is_ring(comp: set[tuple[int, int]], grid) -> bool:
    if len(comp) != 8:
        return False
    r0, r1 = min(r for r, _ in comp), max(r for r, _ in comp)
    c0, c1 = min(c for _, c in comp), max(c for _, c in comp)
    if r1 - r0 != 2 or c1 - c0 != 2:
        return False
    return grid[r0 + 1][c0 + 1] == 0 and comp == _shape_cells(_RING, r0, c0)


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be rectangular"]}
    if not 10 <= h <= 12:
        errors.append(f"grid height {h} outside 10..12")
    if not 10 <= w <= 12:
        errors.append(f"grid width {w} outside 10..12")

    blue: set[tuple[int, int]] = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1):
                errors.append(f"cell ({r},{c}) must be binary 0/1, got {value!r}")
            elif value == 1:
                blue.add((r, c))
    if any("must be binary" in error for error in errors):
        return {"errors": errors, "grid_h": h, "grid_w": w}

    components = _components(blue)
    ring_components = [comp for comp in components if _component_is_ring(comp, grid)]
    distractors = [comp for comp in components if not _component_is_ring(comp, grid)]
    local_rings = _ring_toplefts(grid)
    if len(local_rings) != len(ring_components):
        errors.append(
            "every target frame must be an isolated 8-cell component; "
            f"found {len(local_rings)} local frame(s) but {len(ring_components)} isolated frame object(s)"
        )
    if not 1 <= len(ring_components) <= 2:
        errors.append(f"expected 1..2 hollow frame objects, got {len(ring_components)}")
    if not 2 <= len(distractors) <= 3:
        errors.append(f"expected 2..3 non-frame distractor objects, got {len(distractors)}")
    for index, comp in enumerate(distractors):
        if not 2 <= len(comp) <= 5:
            errors.append(
                f"distractor {index} has {len(comp)} cells; expected canonical-scale 2..5"
            )
        bh = max(r for r, _ in comp) - min(r for r, _ in comp) + 1
        bw = max(c for _, c in comp) - min(c for _, c in comp) + 1
        if bh > 3 or bw > 3:
            errors.append(
                f"distractor {index} bbox {bh}x{bw} exceeds canonical-scale 3x3"
            )

    edge_ring = any(
        r0 == 0 or c0 == 0 or r0 == h - 3 or c0 == w - 3
        for r0, c0 in local_rings
    )
    ring_cells = set().union(*ring_components) if ring_components else set()
    distractor_cells = blue - ring_cells
    if not ring_cells:
        errors.append("rule would be an identity: no exact hollow frame target")
    if not distractor_cells:
        errors.append("lesson hides the preservation branch: no unchanged blue distractor")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n_rings": len(ring_components),
        "n_distractors": len(distractors),
        "edge_ring": edge_ring,
        "ring_toplefts": local_rings,
        "ring_components": ring_components,
        "distractors": distractors,
        "ring_cells": ring_cells,
        "distractor_cells": distractor_cells,
        "blue_cells": blue,
    }


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every exact AXES value from returned pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_rings": analysis["n_rings"],
        "n_distractors": analysis["n_distractors"],
        "edge_ring": analysis["edge_ring"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical/generated scenes; reject rule-hiding binary impostors."""
    del difficulty
    errors = list(_analyze(grid)["errors"])
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for name, value in requested.items():
        if name in AXES and observed.get(name) != value:
            errors.append(
                f"override {name}={value!r} realized as {observed.get(name)!r}"
            )
    return errors


def _apply_rule(grid):
    """Python mirror used only for audits/rivals; canonical Racket stays authority."""
    out = [list(row) for row in grid]
    for r0, c0 in _ring_toplefts(grid):
        cr, cc = r0 + 1, c0 + 1
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            out[cr + dr][cc + dc] = 0
        for dr, dc in ((-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)):
            out[cr + dr][cc + dc] = 2
    return out


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    distractor_sizes = Counter(len(comp) for comp in analysis["distractors"])
    return {
        **observe_overrides(grid),
        "interior_rings": sum(
            1
            for r0, c0 in analysis["ring_toplefts"]
            if r0 > 0 and c0 > 0
            and r0 < analysis["grid_h"] - 3
            and c0 < analysis["grid_w"] - 3
        ),
        "distractor_sizes": dict(distractor_sizes),
        "has_three_by_three_nonframe": any(
            (max(r for r, _ in comp) - min(r for r, _ in comp) + 1) == 3
            and (max(c for _, c in comp) - min(c for _, c in comp) + 1) == 3
            for comp in analysis["distractors"]
        ),
        "blue_distractor_cells": len(analysis["distractor_cells"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Strict linked predicate for the lawful canonical-anchored lesson family."""
    return list(_analyze(grid)["errors"])


def _witness(grid, pred: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(pred(obs))


SEMANTIC_WITNESSES = {
    "single_ring_counterexample": lambda grid: _witness(grid, lambda o: o["n_rings"] == 1),
    "edge_ring": lambda grid: _witness(grid, lambda o: o["edge_ring"]),
    "interior_ring": lambda grid: _witness(grid, lambda o: o["interior_rings"] > 0),
    "three_by_three_nonframe_unchanged": lambda grid: _witness(
        grid, lambda o: o["has_three_by_three_nonframe"]
    ),
    "unchanged_blue_distractors": lambda grid: _witness(
        grid, lambda o: o["blue_distractor_cells"] >= 2
    ),
}


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_center_only(grid):
    out = [list(row) for row in grid]
    for r0, c0 in _ring_toplefts(grid):
        out[r0 + 1][c0 + 1] = 2
    return out


def _rival_recolor_all_blue(grid):
    return [[2 if value == 1 else value for value in row] for row in grid]


def _rival_ignore_edge_rings(grid):
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r0, c0 in _ring_toplefts(grid):
        if r0 == 0 or c0 == 0 or r0 == h - 3 or c0 == w - 3:
            continue
        one = [[0 for _ in row] for row in grid]
        for dr, dc in _RING:
            one[r0 + dr][c0 + dc] = 1
        transformed = _apply_rule(one)
        for r in range(h):
            for c in range(w):
                if one[r][c] != transformed[r][c]:
                    out[r][c] = transformed[r][c]
    return out


def _rival_two_ring_only(grid):
    if len(_ring_toplefts(grid)) != 2:
        return [list(row) for row in grid]
    return _apply_rule(grid)


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "center_only": _rival_center_only,
    "recolor_all_blue": _rival_recolor_all_blue,
    "ignore_edge_rings": _rival_ignore_edge_rings,
    "two_ring_only": _rival_two_ring_only,
}
WITNESS_RIVALS = {
    "single_ring_counterexample": ["two_ring_only"],
    "edge_ring": ["ignore_edge_rings"],
    "three_by_three_nonframe_unchanged": ["recolor_all_blue"],
    "unchanged_blue_distractors": ["recolor_all_blue"],
    "interior_ring": ["center_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every public/canonical pair contains exactly two target rings, so this
    # wrong count-gated rule is answer-equivalent there. The scheduled 1-ring
    # profiles are the required generated discriminator.
    "two_ring_only": _rival_two_ring_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful frame lesson: " + "; ".join(query_errors)]
    query_truth = _apply_rule(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != _apply_rule(demo_input):
            reasons.append(f"demo {index} output disagrees with the frame-to-plus rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
