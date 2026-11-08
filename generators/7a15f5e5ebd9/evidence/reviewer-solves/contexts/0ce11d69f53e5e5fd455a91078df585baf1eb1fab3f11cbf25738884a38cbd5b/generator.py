"""Generator for E120 / Offset Cloud Replay (7a15f5e5ebd9).

A maroon 9 marks the reference origin of every yellow 4 in the input.  Red 2
cells are destination anchors.  The output clears the source scene, keeps every
red anchor, and replays every yellow offset at every red anchor.  Replayed cells
are clipped independently at the grid boundary; red anchors are repainted last.

The default ten-slot curriculum alternates all five linked canonical profiles
with rule-lawful counterexamples.  The counterexamples deliberately include
clipping, overlapping copies, a stamp landing on another red anchor, destinations
above/left of the source, long-range offsets, and disconnected yellow templates.
Those branches distinguish the true offset-replay rule from shortcuts that fit
all five official pairs (XOR overlap, yellow-over-red priority, local-only offsets,
and destinations restricted to the canonical lower-right quadrant).
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7a15f5e5ebd9"
TASK_ID = "7a15f5e5ebd9"
VERSION = "2.0.0"
RULE_HASH = "9a1bc43f327f"

SUMMARY = (
    "One maroon(9) reference defines the offsets of 4-6 yellow(4) template "
    "cells.  Replay all offsets at 1-5 red(2) anchors on a blank same-size "
    "canvas, clip each replayed cell independently, then repaint anchors red. "
    "The ten-slot lesson schedule covers every linked canonical profile plus "
    "overlap, clipping, anchor-collision, long-range, disconnected-template, "
    "and above/left-destination counterexamples."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

INVARIANTS = [
    "grid is 8..18 by 8..18 and uses only colors 0, 2, 4, and 9",
    "exactly one maroon 9 reference and one declared 4-6-cell yellow template",
    "one to five distinct red 2 destination anchors outside the source template",
    "each destination contributes at least one visible yellow output cell after red anchors are repainted",
    "offset cells are clipped independently at boundaries; overlap is set union; red anchors win color priority",
    "default lessons alternate every linked canonical profile with semantic counterexamples",
]

# Exact yellow offsets relative to the maroon reference.  The first five are
# the complete canonical support.  The final two are lawful generalizations
# with long-range and disconnected cells; each contains a translation vector
# that is both a template offset and a difference of two offsets, making it
# possible to witness both yellow/yellow overlap and yellow/red collision in a
# single compact teaching scene.
_TEMPLATES: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical_down_t": tuple(sorted(((0, 1), (1, 0), (1, 1), (2, 1)))),
    "canonical_side_fork": tuple(sorted(((-1, 0), (0, 1), (1, 0), (1, 1)))),
    "canonical_right_hook": tuple(sorted(((0, 1), (0, 2), (1, 0), (2, 1)))),
    "canonical_tall_fork": tuple(
        sorted(((-1, 1), (0, 1), (1, 0), (1, 1), (2, 1)))
    ),
    "canonical_right_block": tuple(
        sorted(((-1, 0), (0, 1), (1, 0), (1, 1), (1, 2)))
    ),
    "scatter_long_a": tuple(
        sorted(((-3, 0), (-1, -2), (0, 1), (1, 3), (2, -1), (3, 2)))
    ),
    "scatter_long_b": tuple(
        sorted(((-3, -1), (-1, 2), (0, -2), (1, 1), (2, 3), (3, 0)))
    ),
}
_TEMPLATE_NAMES = tuple(_TEMPLATES)

# Complete linked canonical profiles: dimensions, yellow bitmap, and red-anchor
# offsets relative to the maroon reference.  `clipped` is the number of
# canonical replay attempts outside the canvas and is preserved by default
# canonical schedule slots even when the whole linked scene is translated.
_CANONICAL_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "h": 10,
        "w": 12,
        "template": "canonical_down_t",
        "anchor_offsets": ((5, 7), (7, 3)),
        "clipped": 1,
    },
    {
        "h": 11,
        "w": 13,
        "template": "canonical_side_fork",
        "anchor_offsets": ((2, 5), (4, 7), (6, 3)),
        "clipped": 0,
    },
    {
        "h": 9,
        "w": 11,
        "template": "canonical_right_hook",
        "anchor_offsets": ((4, 5), (6, 1)),
        "clipped": 1,
    },
    {
        "h": 12,
        "w": 12,
        "template": "canonical_tall_fork",
        "anchor_offsets": ((4, 4), (5, 7), (7, 3)),
        "clipped": 0,
    },
    {
        "h": 11,
        "w": 12,
        "template": "canonical_right_block",
        "anchor_offsets": ((2, 7), (4, 6), (6, 2)),
        "clipped": 0,
    },
)
_CANONICAL_SIGNATURES = frozenset(
    (
        profile["h"],
        profile["w"],
        profile["template"],
        tuple(sorted(profile["anchor_offsets"])),
    )
    for profile in _CANONICAL_PROFILES
)

# (template, anchor count, placement kind, canonical profile index or None).
# Every cyclic window of four slots contains at least one `teaching` slot.
# Slot 9 preserves the lawful single-destination branch without creating a
# four-example window that lacks a full semantic counterexample.
_SCHEDULE: tuple[tuple[str, int, str, int | None], ...] = (
    ("canonical_down_t", 2, "canonical", 0),
    ("scatter_long_b", 3, "teaching", None),
    ("canonical_side_fork", 3, "canonical", 1),
    ("scatter_long_a", 4, "teaching", None),
    ("canonical_right_hook", 2, "canonical", 2),
    ("scatter_long_b", 3, "teaching", None),
    ("canonical_tall_fork", 3, "canonical", 3),
    ("scatter_long_a", 5, "teaching", None),
    ("canonical_right_block", 3, "canonical", 4),
    ("scatter_long_b", 1, "single", None),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked canonical height or difficulty-skewed 11..18",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "linked canonical width or difficulty-skewed 11..18",
        "valid": "8..18",
    },
    "template": {
        "type": "str",
        "default": "ten-slot schedule over five canonical and two long-range templates",
        "valid": (
            "canonical_down_t|canonical_side_fork|canonical_right_hook|"
            "canonical_tall_fork|canonical_right_block|scatter_long_a|"
            "scatter_long_b"
        ),
    },
    "n_anchors": {
        "type": "int",
        "default": "ten-slot schedule spanning 1..5",
        "valid": "1..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_ALLOWED_COLORS = {0, 2, 4, 9}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return a deterministic, non-aliased curriculum slot.

    The seed mix prevents tools that hold ``sample_index`` fixed from seeing a
    single prototype forever; for any fixed seed, consecutive sample indexes
    still traverse consecutive slots, preserving cyclic lesson guarantees.
    """
    del difficulty
    seed_mix = int(seed) ^ (int(seed) >> 3)
    return (int(sample_index) + seed_mix) % len(_SCHEDULE)


def _clone(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _in_bounds(point: tuple[int, int], h: int, w: int) -> bool:
    r, c = point
    return 0 <= r < h and 0 <= c < w


def _translated(
    origin: tuple[int, int], offsets: Iterable[tuple[int, int]]
) -> set[tuple[int, int]]:
    r, c = origin
    return {(r + dr, c + dc) for dr, dc in offsets}


def _visible_stamp(
    anchor: tuple[int, int],
    offsets: Iterable[tuple[int, int]],
    h: int,
    w: int,
) -> set[tuple[int, int]]:
    return {point for point in _translated(anchor, offsets) if _in_bounds(point, h, w)}


def _connected_components(cells: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component = {start}
        remaining.remove(start)
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIR4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def _grid_facts(grid: Any) -> dict[str, Any]:
    """Parse and validate one input without consulting canonical answers."""
    facts: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        facts["errors"].append("grid must be a nonempty list of rows")
        return facts
    h, w = len(grid), len(grid[0])
    facts.update({"h": h, "w": w})
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        facts["errors"].append("grid must be rectangular with nonempty rows")
        return facts
    if not (8 <= h <= 18 and 8 <= w <= 18):
        facts["errors"].append(f"grid dimensions {h}x{w} must both be in 8..18")

    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or value not in _ALLOWED_COLORS
    ]
    if bad_values:
        facts["errors"].append("grid may use only colors 0, 2, 4, and 9")

    nines = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    anchors = tuple(
        sorted(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 2
        )
    )
    fours = tuple(
        sorted(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 4
        )
    )
    facts.update({"anchors": anchors, "fours": fours})

    if len(nines) != 1:
        facts["errors"].append(f"expected exactly one 9 reference, found {len(nines)}")
        return facts
    ref = nines[0]
    offsets = tuple(sorted((r - ref[0], c - ref[1]) for r, c in fours))
    template = next(
        (name for name, declared in _TEMPLATES.items() if declared == offsets),
        None,
    )
    anchor_offsets = tuple(sorted((r - ref[0], c - ref[1]) for r, c in anchors))
    facts.update(
        {
            "ref": ref,
            "shape_offsets": offsets,
            "template": template,
            "n_anchors": len(anchors),
            "anchor_offsets": anchor_offsets,
        }
    )

    if template is None:
        facts["errors"].append("yellow offsets do not match a declared template")
    if not 1 <= len(anchors) <= 5:
        facts["errors"].append(f"expected 1-5 red anchors, found {len(anchors)}")

    anchor_set = set(anchors)
    stamp_counts: Counter[tuple[int, int]] = Counter()
    clipped_by_anchor: list[int] = []
    contribution_by_anchor: list[int] = []
    for anchor in anchors:
        visible = _visible_stamp(anchor, offsets, h, w)
        clipped_by_anchor.append(len(offsets) - len(visible))
        contribution_by_anchor.append(len(visible - anchor_set))
        stamp_counts.update(visible)

    if any(count == 0 for count in contribution_by_anchor):
        facts["errors"].append(
            "every red anchor must contribute a visible yellow cell after anchors are repainted"
        )

    components = _connected_components(fours) if fours else []
    facts.update(
        {
            "clipped_by_anchor": tuple(clipped_by_anchor),
            "clipped_offsets": sum(clipped_by_anchor),
            "contribution_by_anchor": tuple(contribution_by_anchor),
            "stamp_counts": stamp_counts,
            "overlap_cells": sum(count > 1 for count in stamp_counts.values()),
            "anchor_collision_cells": tuple(sorted(set(stamp_counts) & anchor_set)),
            "output_yellow_cells": len(set(stamp_counts) - anchor_set),
            "template_components_4": len(components),
        }
    )
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes, while accepting canonical per-cell clipping."""
    del difficulty, meta
    return list(_grid_facts(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact axis from an emitted grid."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "template": facts["template"],
        "n_anchors": facts["n_anchors"],
    }


def canonical_profile_signature(grid):
    """Return the full linked canonical signature, or ``None``."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        return None
    signature = (
        facts["h"],
        facts["w"],
        facts["template"],
        facts["anchor_offsets"],
    )
    return signature if signature in _CANONICAL_SIGNATURES else None


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact linked empirical support of the five official inputs."""
    facts = _grid_facts(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if canonical_profile_signature(grid) is None:
        reasons.append(
            "dimensions, template, and anchor offsets do not form a linked canonical profile"
        )
    return reasons


def semantic_observables(grid) -> dict[str, Any]:
    facts = _grid_facts(grid)
    if facts["errors"]:
        return {"errors": list(facts["errors"])}
    offsets = facts["shape_offsets"]
    min_r = min(r for r, _ in offsets)
    max_r = max(r for r, _ in offsets)
    min_c = min(c for _, c in offsets)
    max_c = max(c for _, c in offsets)
    ref_r, ref_c = facts["ref"]
    return {
        "template": facts["template"],
        "shape_cells": len(offsets),
        "shape_bbox": (max_r - min_r + 1, max_c - min_c + 1),
        "bbox_holes": (max_r - min_r + 1) * (max_c - min_c + 1) - len(offsets),
        "n_anchors": facts["n_anchors"],
        "clipped_offsets": facts["clipped_offsets"],
        "overlap_cells": facts["overlap_cells"],
        "anchor_collision_cells": len(facts["anchor_collision_cells"]),
        "template_components_4": facts["template_components_4"],
        "has_anchor_above_or_left": any(
            r < ref_r or c < ref_c for r, c in facts["anchors"]
        ),
        "has_long_range_offset": any(abs(r) > 2 or abs(c) > 2 for r, c in offsets),
        "horizontally_symmetric": tuple(sorted((r, -c) for r, c in offsets))
        == offsets,
        "canonical_signature": canonical_profile_signature(grid),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains authoritative."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["h"], facts["w"], 0)
    for r, c in facts["anchors"]:
        output[r][c] = 2
    for anchor in facts["anchors"]:
        for point in _visible_stamp(
            anchor, facts["shape_offsets"], facts["h"], facts["w"]
        ):
            output[point[0]][point[1]] = 4
    for r, c in facts["anchors"]:
        output[r][c] = 2
    return output


def _valid_ref_positions(h: int, w: int, offsets: tuple[tuple[int, int], ...]):
    min_r = min(0, *(r for r, _ in offsets))
    max_r = max(0, *(r for r, _ in offsets))
    min_c = min(0, *(c for _, c in offsets))
    max_c = max(0, *(c for _, c in offsets))
    return [
        (r, c)
        for r in range(-min_r, h - max_r)
        for c in range(-min_c, w - max_c)
    ]


def _render_grid(
    h: int,
    w: int,
    ref: tuple[int, int],
    offsets: tuple[tuple[int, int], ...],
    anchors: Iterable[tuple[int, int]],
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    rr, rc = ref
    grid[rr][rc] = 9
    for dr, dc in offsets:
        grid[rr + dr][rc + dc] = 4
    for r, c in anchors:
        grid[r][c] = 2
    return grid


def _anchor_metrics(
    anchors: Iterable[tuple[int, int]],
    offsets: tuple[tuple[int, int], ...],
    ref: tuple[int, int],
    h: int,
    w: int,
) -> dict[str, Any]:
    anchors = tuple(sorted(anchors))
    anchor_set = set(anchors)
    counts: Counter[tuple[int, int]] = Counter()
    clipped = []
    contributions = []
    for anchor in anchors:
        visible = _visible_stamp(anchor, offsets, h, w)
        clipped.append(len(offsets) - len(visible))
        contributions.append(len(visible - anchor_set))
        counts.update(visible)
    return {
        "anchors": anchors,
        "clipped": sum(clipped),
        "overlap": sum(count > 1 for count in counts.values()),
        "collisions": len(set(counts) & anchor_set),
        "above_or_left": any(r < ref[0] or c < ref[1] for r, c in anchors),
        "contributions": tuple(contributions),
        "spread": min(
            (
                abs(a[0] - b[0]) + abs(a[1] - b[1])
                for index, a in enumerate(anchors)
                for b in anchors[index + 1 :]
            ),
            default=h + w,
        ),
    }


def _canonical_grid(profile_index: int, rng) -> list[list[int]]:
    profile = _CANONICAL_PROFILES[profile_index]
    h, w = profile["h"], profile["w"]
    offsets = _TEMPLATES[profile["template"]]
    anchor_offsets = tuple(profile["anchor_offsets"])
    candidates = []
    for ref in _valid_ref_positions(h, w, offsets):
        anchors = tuple((ref[0] + dr, ref[1] + dc) for dr, dc in anchor_offsets)
        if not all(_in_bounds(anchor, h, w) for anchor in anchors):
            continue
        source = {ref, *_translated(ref, offsets)}
        if source & set(anchors):
            continue
        metrics = _anchor_metrics(anchors, offsets, ref, h, w)
        if metrics["clipped"] != profile["clipped"]:
            continue
        if any(count == 0 for count in metrics["contributions"]):
            continue
        candidates.append((ref, anchors))
    if not candidates:
        raise ValueError(f"linked canonical profile {profile_index} has no placement")
    ref, anchors = rng.choice(candidates)
    return _render_grid(h, w, ref, offsets, anchors)


def _legal_anchor_cells(
    h: int,
    w: int,
    source: set[tuple[int, int]],
    offsets: tuple[tuple[int, int], ...],
) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in source and _visible_stamp((r, c), offsets, h, w)
    ]


def _choose_general_anchors(
    candidates: list[tuple[int, int]],
    offsets: tuple[tuple[int, int], ...],
    ref: tuple[int, int],
    h: int,
    w: int,
    n_anchors: int,
    mode: str,
    rng,
) -> tuple[tuple[int, int], ...]:
    if len(candidates) < n_anchors:
        raise ValueError(f"only {len(candidates)} legal anchor cells for {n_anchors} anchors")
    best: tuple[tuple[int, int], ...] | None = None
    best_score: tuple[Any, ...] | None = None
    attempts = min(48, max(18, n_anchors * 8))
    for _ in range(attempts):
        chosen = tuple(sorted(rng.sample(candidates, n_anchors)))
        metrics = _anchor_metrics(chosen, offsets, ref, h, w)
        if any(count == 0 for count in metrics["contributions"]):
            continue
        if mode == "clustered":
            score = (
                metrics["overlap"] > 0,
                metrics["collisions"] > 0,
                metrics["clipped"] > 0,
                metrics["overlap"] + metrics["collisions"],
                metrics["clipped"],
                -metrics["spread"],
            )
        elif mode == "edge":
            score = (
                metrics["clipped"] > 0,
                metrics["above_or_left"],
                metrics["clipped"],
                metrics["spread"],
            )
        else:
            score = (
                metrics["spread"],
                -metrics["overlap"],
                -metrics["collisions"],
                -metrics["clipped"],
            )
        if best_score is None or score > best_score:
            best, best_score = chosen, score
    if best is None:
        raise ValueError("could not choose anchors with visible contributions")
    return best


def _general_grid(h, w, template, n_anchors, mode, rng):
    offsets = _TEMPLATES[template]
    refs = _valid_ref_positions(h, w, offsets)
    rng.shuffle(refs)
    for ref in refs:
        source = {ref, *_translated(ref, offsets)}
        candidates = _legal_anchor_cells(h, w, source, offsets)
        try:
            anchors = _choose_general_anchors(
                candidates, offsets, ref, h, w, n_anchors, mode, rng
            )
        except ValueError:
            continue
        grid = _render_grid(h, w, ref, offsets, anchors)
        if not self_check(grid):
            return grid
    raise ValueError(
        f"cannot place template={template!r}, n_anchors={n_anchors} in {h}x{w}"
    )


def _teaching_deltas(offsets: tuple[tuple[int, int], ...]):
    """Translations that cause both stamp overlap and a stamp-on-anchor hit."""
    differences = {
        (r1 - r2, c1 - c2)
        for r1, c1 in offsets
        for r2, c2 in offsets
        if (r1, c1) != (r2, c2)
    }
    return tuple(sorted(set(offsets) & differences))


def _teaching_grid(h, w, template, n_anchors, rng):
    """Construct an omnibus counterexample for every named canonical shortcut."""
    if n_anchors < 3:
        raise ValueError("teaching profile needs at least three anchors")
    offsets = _TEMPLATES[template]
    deltas = _teaching_deltas(offsets)
    if not deltas:
        raise ValueError(f"template {template!r} has no teaching translation")

    refs = _valid_ref_positions(h, w, offsets)
    refs.sort(key=lambda p: (abs(p[0] - h // 2) + abs(p[1] - w // 2), p))
    center_band = refs[: max(1, min(8, len(refs)))]
    rng.shuffle(center_band)
    for ref in center_band + refs[len(center_band) :]:
        source = {ref, *_translated(ref, offsets)}
        candidates = _legal_anchor_cells(h, w, source, offsets)
        candidate_set = set(candidates)

        # If second = first + delta and delta is both a template offset and a
        # difference of two offsets, then a stamp from `first` lands on the
        # red `second` anchor and the two yellow stamps overlap elsewhere.
        pairs = []
        for first in candidates:
            for dr, dc in deltas:
                second = (first[0] + dr, first[1] + dc)
                if second not in candidate_set or second == first:
                    continue
                pair = tuple(sorted((first, second)))
                metrics = _anchor_metrics(pair, offsets, ref, h, w)
                if (
                    metrics["clipped"] > 0
                    and metrics["overlap"] > 0
                    and metrics["collisions"] > 0
                    and all(count > 0 for count in metrics["contributions"])
                ):
                    pairs.append((pair, metrics))
        if not pairs:
            continue
        # Deduplicate the two directions, then prefer stronger boundary and
        # overlap evidence.  Random tie selection retains seed diversity.
        dedup = {}
        for pair, metrics in pairs:
            dedup[pair] = metrics
        ranked = sorted(
            dedup.items(),
            key=lambda item: (
                item[1]["clipped"],
                item[1]["overlap"] + item[1]["collisions"],
                -item[1]["spread"],
                item[0],
            ),
            reverse=True,
        )
        top = ranked[: max(1, min(12, len(ranked)))]
        rng.shuffle(top)
        for (first, second), _ in top:
            chosen = [first, second]
            remaining = [point for point in candidates if point not in chosen]
            above_left = [
                point
                for point in remaining
                if point[0] < ref[0] or point[1] < ref[1]
            ]
            rng.shuffle(above_left)
            for point in above_left:
                trial = tuple(sorted([*chosen, point]))
                metrics = _anchor_metrics(trial, offsets, ref, h, w)
                if all(count > 0 for count in metrics["contributions"]):
                    chosen.append(point)
                    break
            if len(chosen) < 3:
                continue
            remaining = [point for point in remaining if point not in chosen]
            while len(chosen) < n_anchors:
                # Sample a bounded candidate subset, then keep the point that
                # preserves witnesses while adding geometric spread.
                pool = list(remaining)
                rng.shuffle(pool)
                pool = pool[: min(80, len(pool))]
                best = None
                best_score = None
                for point in pool:
                    trial = tuple(sorted([*chosen, point]))
                    metrics = _anchor_metrics(trial, offsets, ref, h, w)
                    if any(count == 0 for count in metrics["contributions"]):
                        continue
                    score = (
                        metrics["overlap"] + metrics["collisions"],
                        metrics["clipped"],
                        metrics["above_or_left"],
                        metrics["spread"],
                    )
                    if best_score is None or score > best_score:
                        best, best_score = point, score
                if best is None:
                    break
                chosen.append(best)
                remaining.remove(best)
            if len(chosen) != n_anchors:
                continue
            metrics = _anchor_metrics(chosen, offsets, ref, h, w)
            if not (
                metrics["clipped"] > 0
                and metrics["overlap"] > 0
                and metrics["collisions"] > 0
                and metrics["above_or_left"]
            ):
                continue
            grid = _render_grid(h, w, ref, offsets, chosen)
            if not self_check(grid):
                return grid
    raise ValueError(f"could not construct teaching profile {template!r} in {h}x{w}")

def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    scheduled_template, scheduled_count, kind, profile_index = _SCHEDULE[slot]
    use_linked_canonical = not overrides and kind == "canonical"

    if use_linked_canonical:
        profile = _CANONICAL_PROFILES[profile_index]
        h = ctx.draw_int("grid_h", profile["h"], profile["h"])
        w = ctx.draw_int("grid_w", profile["w"], profile["w"])
        template = ctx.draw_choice("template", (scheduled_template,))
        n_anchors = ctx.draw_int("n_anchors", scheduled_count, scheduled_count)
    elif not overrides:
        h = ctx.draw_int_diff("grid_h", 11, 18)
        w = ctx.draw_int_diff("grid_w", 11, 18)
        template = ctx.draw_choice("template", (scheduled_template,))
        n_anchors = ctx.draw_int("n_anchors", scheduled_count, scheduled_count)
    else:
        h = ctx.draw_int_diff("grid_h", 8, 18)
        w = ctx.draw_int_diff("grid_w", 8, 18)
        template = ctx.draw_choice("template", _TEMPLATE_NAMES)
        n_anchors = ctx.draw_int("n_anchors", 1, 5)

    rng = ctx.draw_rng("placement")
    if use_linked_canonical:
        grid = _canonical_grid(profile_index, rng)
    elif not overrides and kind == "teaching":
        grid = _teaching_grid(h, w, template, n_anchors, rng)
    elif not overrides and kind == "single":
        grid = _general_grid(h, w, template, n_anchors, "edge", rng)
    else:
        mode = ("spread", "clustered", "edge")[int(sample_index) % 3]
        grid = _general_grid(h, w, template, n_anchors, mode, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated malformed grid: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Named rival rules and task-linked witnesses.
# ---------------------------------------------------------------------------

def _facts_or_raise(grid):
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return facts


def _blank_with_anchors(facts):
    output = full_grid(facts["h"], facts["w"], 0)
    for r, c in facts["anchors"]:
        output[r][c] = 2
    return output


def _paint_offsets(
    facts,
    anchors,
    offsets,
    *,
    repaint_anchors=True,
    drop_if_clipped=False,
):
    output = _blank_with_anchors(facts)
    for anchor in anchors:
        translated = _translated(anchor, offsets)
        if drop_if_clipped and any(
            not _in_bounds(point, facts["h"], facts["w"]) for point in translated
        ):
            continue
        for r, c in translated:
            if _in_bounds((r, c), facts["h"], facts["w"]):
                output[r][c] = 4
    if repaint_anchors:
        for r, c in facts["anchors"]:
            output[r][c] = 2
    return output


def _rival_identity(grid):
    return _clone(grid)


def _rival_first_anchor_only(grid):
    facts = _facts_or_raise(grid)
    return _paint_offsets(facts, facts["anchors"][:1], facts["shape_offsets"])


def _rival_fill_template_bbox(grid):
    facts = _facts_or_raise(grid)
    offsets = facts["shape_offsets"]
    rows = [r for r, _ in offsets]
    cols = [c for _, c in offsets]
    bbox = tuple(
        (dr, dc)
        for dr in range(min(rows), max(rows) + 1)
        for dc in range(min(cols), max(cols) + 1)
    )
    return _paint_offsets(facts, facts["anchors"], bbox)


def _rival_fixed_down_t(grid):
    facts = _facts_or_raise(grid)
    return _paint_offsets(
        facts, facts["anchors"], _TEMPLATES["canonical_down_t"]
    )


def _rival_horizontal_mirror(grid):
    facts = _facts_or_raise(grid)
    mirrored = tuple((r, -c) for r, c in facts["shape_offsets"])
    return _paint_offsets(facts, facts["anchors"], mirrored)


def _rival_local_radius_2(grid):
    facts = _facts_or_raise(grid)
    local = tuple(
        (r, c)
        for r, c in facts["shape_offsets"]
        if abs(r) <= 2 and abs(c) <= 2
    )
    return _paint_offsets(facts, facts["anchors"], local)


def _rival_xor_overlaps(grid):
    facts = _facts_or_raise(grid)
    counts: Counter[tuple[int, int]] = Counter()
    for anchor in facts["anchors"]:
        counts.update(
            point
            for point in _translated(anchor, facts["shape_offsets"])
            if _in_bounds(point, facts["h"], facts["w"])
        )
    output = _blank_with_anchors(facts)
    for (r, c), count in counts.items():
        if count % 2:
            output[r][c] = 4
    for r, c in facts["anchors"]:
        output[r][c] = 2
    return output


def _rival_yellow_overwrites_red(grid):
    facts = _facts_or_raise(grid)
    return _paint_offsets(
        facts,
        facts["anchors"],
        facts["shape_offsets"],
        repaint_anchors=False,
    )


def _rival_only_below_right(grid):
    facts = _facts_or_raise(grid)
    rr, rc = facts["ref"]
    selected = tuple(
        anchor
        for anchor in facts["anchors"]
        if anchor[0] >= rr and anchor[1] >= rc
    )
    return _paint_offsets(facts, selected, facts["shape_offsets"])


def _rival_drop_clipped_copy(grid):
    facts = _facts_or_raise(grid)
    return _paint_offsets(
        facts,
        facts["anchors"],
        facts["shape_offsets"],
        drop_if_clipped=True,
    )


def _rival_nearest_template_component(grid):
    facts = _facts_or_raise(grid)
    components = _connected_components(facts["fours"])
    rr, rc = facts["ref"]
    component = min(
        components,
        key=lambda comp: (
            min(abs(r - rr) + abs(c - rc) for r, c in comp),
            tuple(sorted(comp)),
        ),
    )
    offsets = tuple(sorted((r - rr, c - rc) for r, c in component))
    return _paint_offsets(facts, facts["anchors"], offsets)


SEMANTIC_RIVALS: dict[str, Callable] = {
    "source_scene_identity": _rival_identity,
    "first_anchor_only": _rival_first_anchor_only,
    "fill_template_bbox": _rival_fill_template_bbox,
    "fixed_canonical_down_t": _rival_fixed_down_t,
    "mirror_template_horizontally": _rival_horizontal_mirror,
    "local_radius_2_offsets_only": _rival_local_radius_2,
    "xor_overlapping_copies": _rival_xor_overlaps,
    "yellow_overwrites_red_anchor": _rival_yellow_overwrites_red,
    "only_below_right_destinations": _rival_only_below_right,
    "drop_entire_clipped_copy": _rival_drop_clipped_copy,
    "nearest_template_component_only": _rival_nearest_template_component,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These four wrong rules reproduce every official pair.  They are intentionally
# called out so the semantic gate verifies that generated counterexamples, not
# the canonical set, are doing the disambiguation work.
CANONICAL_SHORTCUTS = {
    "xor_overlapping_copies": _rival_xor_overlaps,
    "yellow_overwrites_red_anchor": _rival_yellow_overwrites_red,
    "only_below_right_destinations": _rival_only_below_right,
    "local_radius_2_offsets_only": _rival_local_radius_2,
}


def _refutes(name):
    rival = SEMANTIC_RIVALS[name]

    def predicate(grid):
        try:
            return rule_mirror(grid) != rival(grid)
        except Exception:
            return False

    return predicate


def _has_clipping(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and facts["clipped_offsets"] > 0


def _has_overlap(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and facts["overlap_cells"] > 0


def _has_anchor_collision(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and bool(facts["anchor_collision_cells"])


def _single_anchor(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and facts["n_anchors"] == 1


SEMANTIC_WITNESSES = {
    "clears_source_scene": _refutes("source_scene_identity"),
    "multiple_destinations": _refutes("first_anchor_only"),
    "template_bbox_has_holes": _refutes("fill_template_bbox"),
    "template_is_not_fixed_down_t": _refutes("fixed_canonical_down_t"),
    "asymmetric_template": _refutes("mirror_template_horizontally"),
    "long_range_offsets": _refutes("local_radius_2_offsets_only"),
    "overlapping_copies_use_union": _has_overlap,
    "red_anchor_repaint_priority": _has_anchor_collision,
    "destination_above_or_left": _refutes("only_below_right_destinations"),
    "per_cell_boundary_clipping": _refutes("drop_entire_clipped_copy"),
    "disconnected_template_uses_all_yellow": _refutes(
        "nearest_template_component_only"
    ),
    "single_destination_branch": _single_anchor,
}
BRANCH_WITNESSES = {"single_destination_branch"}
WITNESS_RIVALS = {
    "clears_source_scene": ["source_scene_identity"],
    "multiple_destinations": ["first_anchor_only"],
    "template_bbox_has_holes": ["fill_template_bbox"],
    "template_is_not_fixed_down_t": ["fixed_canonical_down_t"],
    "asymmetric_template": ["mirror_template_horizontally"],
    "long_range_offsets": ["local_radius_2_offsets_only"],
    "overlapping_copies_use_union": ["xor_overlapping_copies"],
    "red_anchor_repaint_priority": ["yellow_overwrites_red_anchor"],
    "destination_above_or_left": ["only_below_right_destinations"],
    "per_cell_boundary_clipping": ["drop_entire_clipped_copy"],
    "disconnected_template_uses_all_yellow": [
        "nearest_template_component_only"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible rival to be eliminated by demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    observations = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with offset replay")
            continue
        observations.append(semantic_observables(pair["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with offset replay")

    if len(observations) != len(demos):
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"rival {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"rival rule {name!r} still fits every demonstration")

    if len({row["template"] for row in observations}) < 2:
        reasons.append("demonstrations do not vary the yellow template")
    required_features = {
        "clipped_offsets": lambda row: row["clipped_offsets"] > 0,
        "overlap_cells": lambda row: row["overlap_cells"] > 0,
        "anchor_collision_cells": lambda row: row["anchor_collision_cells"] > 0,
        "destination_above_or_left": lambda row: row["has_anchor_above_or_left"],
        "long_range_offsets": lambda row: row["has_long_range_offset"],
        "disconnected_template": lambda row: row["template_components_4"] > 1,
    }
    for label, predicate in required_features.items():
        if not any(predicate(row) for row in observations):
            reasons.append(f"demonstrations lack {label} evidence")
    if not any(row["n_anchors"] > 1 for row in observations):
        reasons.append("demonstrations never require multiple destinations")
    return reasons
