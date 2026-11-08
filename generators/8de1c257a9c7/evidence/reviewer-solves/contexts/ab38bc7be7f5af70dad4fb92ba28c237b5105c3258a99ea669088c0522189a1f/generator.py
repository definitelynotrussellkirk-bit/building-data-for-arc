"""Generator for puzzle f5c89df1 — transplant a cyan template to red anchors.

The input contains one green anchor, a cyan bitmap expressed as offsets from
that anchor, and one or more red destination markers.  The output is a blank
canvas with the cyan bitmap stamped at every red marker.  The original anchor,
template, and markers are cleared.

The default lesson schedule alternates the four exact linked canonical
profiles with two asymmetric generalization profiles.  The asymmetries are
intentional counterexamples to the plausible but wrong rule "mirror the cyan
shape horizontally before stamping", which fits every canonical example
because every official cyan bitmap happens to be horizontally symmetric.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8de1c257a9c7"
TASK_ID = "8de1c257a9c7"
VERSION = "3.1.1"
RULE_HASH = "c539e2039994"

SUMMARY = (
    "A zero-background grid contains exactly one green(3) anchor, a cyan(8) "
    "template represented by offsets from that anchor, and 1-5 red(2) "
    "destination markers.  Clear the input and stamp the exact cyan offsets "
    "at every red marker.  The default curriculum alternates all four linked "
    "13x13 canonical profiles with asymmetric templates, includes single and "
    "multiple destinations, and includes both overlapping and separated "
    "copies so fixed-shape, horizontal-mirroring, first-marker-only, local-" 
    "3x3, bbox-fill, XOR-overlap, and marker-as-answer shortcuts are visible."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.40

INVARIANTS = [
    "background is 0 and the only foreground colors are red(2), green(3), and cyan(8)",
    "exactly one green anchor and 4-14 cyan template cells",
    "the green cell plus cyan template is 8-connected",
    "1-5 distinct red destination markers",
    "the exact cyan template fits in-bounds when centered on every red marker",
    "default lessons alternate complete linked canonical profiles with asymmetric counterexamples",
]

# Exact cyan offsets relative to the green anchor.  The first four entries are
# derived from all canonical train and held-out test inputs; the final two are
# deliberate lawful generalizations that destroy the canonical-only horizontal
# symmetry correlation while preserving the true transplant rule.
_TEMPLATES: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical_diamond": tuple(sorted((
        (-2, 0),
        (-1, -1), (-1, 0), (-1, 1),
        (0, -2), (0, 2),
        (1, -1), (1, 0), (1, 1),
        (2, 0),
    ))),
    "canonical_cross": tuple(sorted((
        (-1, 0), (0, -1), (0, 1), (1, 0),
    ))),
    "canonical_arch": tuple(sorted((
        (-3, 0),
        (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
        (-1, -2), (-1, -1), (-1, 1), (-1, 2),
        (0, -2), (0, -1), (0, 1), (0, 2),
    ))),
    "canonical_fork": tuple(sorted((
        (-2, -1), (-2, 1),
        (-1, -2), (-1, -1), (-1, 1), (-1, 2),
        (0, -1), (0, 1),
        (1, 0),
    ))),
    "asymmetric_hook": tuple(sorted((
        (-2, 0),
        (-1, 0), (-1, 1),
        (0, 1),
        (1, 1), (1, 2),
    ))),
    "asymmetric_stair": tuple(sorted((
        (-2, -1),
        (-1, -1), (-1, 0),
        (0, -1),
        (1, -1), (1, 0), (1, 1),
        (2, 1),
    ))),
}
_TEMPLATE_NAMES = tuple(_TEMPLATES)

# Red offsets are linked to their exact canonical cyan bitmap.  A strict
# canonical profile is the whole tuple, never independent shape/count marginals.
_CANONICAL_RED_OFFSETS: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical_diamond": ((0, -3), (0, 3)),
    "canonical_cross": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
    "canonical_arch": ((-4, 0),),
    "canonical_fork": ((-3, -3), (-3, 3)),
}
_CANONICAL_SIGNATURES = frozenset(
    (13, 13, name, tuple(sorted(red_offsets)))
    for name, red_offsets in _CANONICAL_RED_OFFSETS.items()
)

# Eight slots guarantee every four consecutive examples contain at least one
# asymmetric template and multiple destinations.  Every five-slot cyclic lesson
# also contains at least two overlap witnesses, so any single held-out query still
# leaves a demonstration that distinguishes union from XOR overlap semantics.
# Canonical slots preserve the complete linked profile and use a 13x13 canvas;
# generalization slots vary size and marker geometry while keeping the oracle
# semantics unchanged.
_SCHEDULE: tuple[tuple[str, int, str], ...] = (
    ("canonical_diamond", 2, "canonical"),
    ("asymmetric_hook", 3, "clustered"),
    ("canonical_cross", 4, "canonical"),
    ("asymmetric_stair", 5, "clustered"),
    ("canonical_arch", 1, "canonical"),
    ("asymmetric_hook", 2, "clustered"),
    ("canonical_fork", 2, "canonical"),
    ("asymmetric_stair", 4, "clustered"),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "13 on canonical schedule slots; otherwise difficulty-skewed 10..22",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "13 on canonical schedule slots; otherwise difficulty-skewed 10..22",
        "valid": "10..22",
    },
    "template": {
        "type": "str",
        "default": "sample_index schedule over four canonical and two asymmetric templates",
        "valid": (
            "canonical_diamond|canonical_cross|canonical_arch|canonical_fork|"
            "asymmetric_hook|asymmetric_stair"
        ),
    },
    "n_reds": {
        "type": "int",
        "default": "sample_index schedule spanning 1..5",
        "valid": "1..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_ALLOWED_COLORS = {0, 2, 3, 8}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_public_controls(seed: Any, sample_index: Any, difficulty: Any) -> None:
    """Reject coercible public scalars before they alias curriculum draws."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared deterministic curriculum slot."""
    _validate_public_controls(seed, sample_index, difficulty)
    return int(sample_index) % len(_SCHEDULE)


def _clone(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _connected(cells: Iterable[tuple[int, int]], *, directions=_DIR8) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = next(iter(remaining))
    queue = deque([start])
    seen = {start}
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == remaining


def _grid_facts(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        facts["errors"].append("grid must be a nonempty list of rows")
        return facts
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        facts["errors"].append("grid must be rectangular with nonempty rows")
        return facts
    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or value not in _ALLOWED_COLORS
    ]
    if bad_values:
        facts["errors"].append("grid may use only colors 0, 2, 3, and 8")

    positions = {
        color: [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        for color in (2, 3, 8)
    }
    greens, reds, cyans = positions[3], positions[2], positions[8]
    if len(greens) != 1:
        facts["errors"].append(
            f"expected exactly one green anchor, found {len(greens)}"
        )
        return {**facts, "h": h, "w": w, "reds": reds, "cyans": cyans}

    green = greens[0]
    shape_offsets = tuple(sorted((r - green[0], c - green[1]) for r, c in cyans))
    template = next(
        (name for name, offsets in _TEMPLATES.items() if offsets == shape_offsets),
        None,
    )
    facts.update(
        {
            "h": h,
            "w": w,
            "green": green,
            "reds": tuple(sorted(reds)),
            "cyans": tuple(sorted(cyans)),
            "shape_offsets": shape_offsets,
            "template": template,
            "n_reds": len(reds),
        }
    )

    if not 4 <= len(cyans) <= 14:
        facts["errors"].append(
            f"expected 4-14 cyan template cells, found {len(cyans)}"
        )
    if template is None:
        facts["errors"].append("cyan offsets do not match a declared template")
    if not _connected([green, *cyans]):
        facts["errors"].append("green plus cyan template must be 8-connected")
    if not 1 <= len(reds) <= 5:
        facts["errors"].append(f"expected 1-5 red markers, found {len(reds)}")

    occupied = {green, *cyans}
    if any(red in occupied for red in reds):
        facts["errors"].append("red markers may not overwrite the source template")

    out_of_bounds = []
    for rr, rc in reds:
        for dr, dc in shape_offsets:
            nr, nc = rr + dr, rc + dc
            if not (0 <= nr < h and 0 <= nc < w):
                out_of_bounds.append((rr, rc, dr, dc))
                break
    if out_of_bounds:
        facts["errors"].append("the full cyan template must fit at every red marker")

    red_offsets = tuple(sorted((r - green[0], c - green[1]) for r, c in reds))
    facts["red_offsets"] = red_offsets
    stamp_counts: Counter[tuple[int, int]] = Counter()
    for rr, rc in reds:
        for dr, dc in shape_offsets:
            stamp_counts[(rr + dr, rc + dc)] += 1
    facts["stamp_counts"] = stamp_counts
    facts["overlap_cells"] = sum(count > 1 for count in stamp_counts.values())
    facts["output_cells"] = len(stamp_counts)
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and template/marker mutations."""
    del difficulty, meta
    return list(_grid_facts(grid)["errors"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the emitted grid."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "template": facts["template"],
        "n_reds": facts["n_reds"],
    }


def canonical_profile_signature(grid):
    """Return the complete linked canonical signature, or None."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        return None
    signature = (
        facts["h"],
        facts["w"],
        facts["template"],
        facts["red_offsets"],
    )
    return signature if signature in _CANONICAL_SIGNATURES else None


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact linked empirical manifold of all canonical inputs."""
    facts = _grid_facts(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if facts["h"] != 13 or facts["w"] != 13:
        reasons.append("canonical canvas is exactly 13x13")
    if facts["template"] not in _CANONICAL_RED_OFFSETS:
        reasons.append("template is a lawful generalization, not a canonical bitmap")
    else:
        expected = tuple(sorted(_CANONICAL_RED_OFFSETS[facts["template"]]))
        if facts["red_offsets"] != expected:
            reasons.append("red-marker offsets are not linked to this canonical bitmap")
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
    return {
        "template": facts["template"],
        "shape_cells": len(offsets),
        "shape_bbox": (max_r - min_r + 1, max_c - min_c + 1),
        "n_reds": facts["n_reds"],
        "overlap_cells": facts["overlap_cells"],
        "output_cells": facts["output_cells"],
        "horizontally_symmetric": tuple(sorted((r, -c) for r, c in offsets)) == offsets,
        "has_long_range_offset": any(abs(r) > 1 or abs(c) > 1 for r, c in offsets),
        "canonical_signature": canonical_profile_signature(grid),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains the authority."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = full_grid(facts["h"], facts["w"], 0)
    for rr, rc in facts["reds"]:
        for dr, dc in facts["shape_offsets"]:
            output[rr + dr][rc + dc] = 8
    return output


def _valid_centers(h: int, w: int, offsets: tuple[tuple[int, int], ...]):
    min_r = min(r for r, _ in offsets)
    max_r = max(r for r, _ in offsets)
    min_c = min(c for _, c in offsets)
    max_c = max(c for _, c in offsets)
    return [
        (r, c)
        for r in range(-min_r, h - max_r)
        for c in range(-min_c, w - max_c)
    ]


def _stamp_set(center, offsets):
    rr, rc = center
    return {(rr + dr, rc + dc) for dr, dc in offsets}


def _canonical_grid(h, w, template, rng):
    offsets = _TEMPLATES[template]
    red_offsets = _CANONICAL_RED_OFFSETS[template]
    all_relative = {(0, 0), *offsets, *red_offsets}
    for rr, rc in red_offsets:
        all_relative.update((rr + dr, rc + dc) for dr, dc in offsets)
    min_r = min(r for r, _ in all_relative)
    max_r = max(r for r, _ in all_relative)
    min_c = min(c for _, c in all_relative)
    max_c = max(c for _, c in all_relative)
    anchors = [
        (r, c)
        for r in range(-min_r, h - max_r)
        for c in range(-min_c, w - max_c)
    ]
    if not anchors:
        raise ValueError(f"canonical profile {template!r} does not fit {h}x{w}")
    gr, gc = rng.choice(anchors)
    grid = full_grid(h, w, 0)
    grid[gr][gc] = 3
    for dr, dc in offsets:
        grid[gr + dr][gc + dc] = 8
    for dr, dc in red_offsets:
        grid[gr + dr][gc + dc] = 2
    return grid


def _pick_clustered(candidates, offsets, n_reds, rng):
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    if n_reds == 1:
        return shuffled[:1]
    best_pair = None
    best_score = None
    for index, first in enumerate(shuffled):
        first_stamp = _stamp_set(first, offsets)
        for second in shuffled[index + 1:]:
            overlap = len(first_stamp & _stamp_set(second, offsets))
            if overlap <= 0:
                continue
            score = (-overlap, abs(first[0] - second[0]) + abs(first[1] - second[1]))
            if best_score is None or score < best_score:
                best_pair, best_score = (first, second), score
    chosen = list(best_pair) if best_pair is not None else shuffled[:2]
    remaining = [point for point in shuffled if point not in chosen]
    while len(chosen) < n_reds:
        point = min(
            remaining,
            key=lambda p: (
                min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in chosen),
                p,
            ),
        )
        chosen.append(point)
        remaining.remove(point)
    return chosen


def _pick_spread(candidates, n_reds, rng):
    remaining = list(candidates)
    rng.shuffle(remaining)
    chosen = [remaining.pop()]
    while len(chosen) < n_reds:
        point = max(
            remaining,
            key=lambda p: (
                min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in chosen),
                p,
            ),
        )
        chosen.append(point)
        remaining.remove(point)
    return chosen


def _general_grid(h, w, template, n_reds, layout, rng):
    offsets = _TEMPLATES[template]
    center_candidates = _valid_centers(h, w, offsets)
    if len(center_candidates) < n_reds + 1:
        raise ValueError(
            f"cannot place template={template!r}, n_reds={n_reds} in {h}x{w}"
        )

    # One valid template center always leaves many legal destination centers in
    # the declared 10..22 envelope.  Choosing it directly avoids the previous
    # O(N^2) all-anchor census, which made the override matrix unnecessarily
    # expensive while adding no semantic constraint.
    green = rng.choice(center_candidates)
    source = {green, *_stamp_set(green, offsets)}
    legal_reds = [point for point in center_candidates if point not in source]
    if len(legal_reds) < n_reds:
        raise ValueError(
            f"cannot place {n_reds} red markers for template={template!r} in {h}x{w}"
        )
    adjacent = [
        point
        for point in legal_reds
        if any(
            (point[0] + dr, point[1] + dc) in source
            for dr, dc in _DIR4
        )
    ]
    pool = adjacent if layout == "clustered" and len(adjacent) >= n_reds else legal_reds
    if layout == "clustered":
        reds = _pick_clustered(pool, offsets, n_reds, rng)
    else:
        reds = _pick_spread(pool, n_reds, rng)

    grid = full_grid(h, w, 0)
    gr, gc = green
    grid[gr][gc] = 3
    for dr, dc in offsets:
        grid[gr + dr][gc + dc] = 8
    for rr, rc in reds:
        grid[rr][rc] = 2
    return grid


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    """Validate exact controls and remove explicit no-op ``None`` values."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    active = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "n_reds"):
        if name in active and type(active[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    return active


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_public_controls(seed, sample_index, difficulty)
    active_overrides = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active_overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    scheduled_template, scheduled_reds, layout = _SCHEDULE[slot]
    canonical_slot = layout == "canonical"

    if canonical_slot and "grid_h" not in active_overrides:
        h = ctx.draw_int("grid_h", 13, 13)
    else:
        h = ctx.draw_int_diff("grid_h", 10, 22)
    if canonical_slot and "grid_w" not in active_overrides:
        w = ctx.draw_int("grid_w", 13, 13)
    else:
        w = ctx.draw_int_diff("grid_w", 10, 22)

    template_options = (
        _TEMPLATE_NAMES if "template" in active_overrides else (scheduled_template,)
    )
    template = ctx.draw_choice("template", template_options)
    if "n_reds" in active_overrides:
        n_reds = ctx.draw_int("n_reds", 1, 5)
    else:
        n_reds = ctx.draw_int("n_reds", scheduled_reds, scheduled_reds)

    rng = ctx.draw_rng("placement")
    linked_profile = (
        canonical_slot
        and template == scheduled_template
        and n_reds == scheduled_reds
    )
    if linked_profile:
        try:
            grid = _canonical_grid(h, w, template, rng)
        except ValueError:
            # An exact size override can make a linked canonical geometry too
            # small.  Preserve the unpinned template/count axes and fall back to
            # a lawful spread placement rather than mutating unrelated controls.
            grid = _general_grid(h, w, template, n_reds, "spread", rng)
    else:
        chosen_layout = layout if layout in {"clustered", "spread"} else "spread"
        grid = _general_grid(h, w, template, n_reds, chosen_layout, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # Never silently return a malformed teaching example.
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


def _rival_identity(grid):
    return _clone(grid)


def _rival_first_marker_only(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    rr, rc = facts["reds"][0]
    for dr, dc in facts["shape_offsets"]:
        output[rr + dr][rc + dc] = 8
    return output


def _rival_fill_template_bbox(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    offsets = facts["shape_offsets"]
    min_r = min(r for r, _ in offsets)
    max_r = max(r for r, _ in offsets)
    min_c = min(c for _, c in offsets)
    max_c = max(c for _, c in offsets)
    for rr, rc in facts["reds"]:
        for dr in range(min_r, max_r + 1):
            for dc in range(min_c, max_c + 1):
                output[rr + dr][rc + dc] = 8
    return output


def _rival_fixed_cross(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    for rr, rc in facts["reds"]:
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            output[rr + dr][rc + dc] = 8
    return output


def _rival_horizontal_mirror(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    for rr, rc in facts["reds"]:
        for dr, dc in facts["shape_offsets"]:
            output[rr + dr][rc - dc] = 8
    return output


def _rival_local_3x3_only(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    for rr, rc in facts["reds"]:
        for dr, dc in facts["shape_offsets"]:
            if abs(dr) <= 1 and abs(dc) <= 1:
                output[rr + dr][rc + dc] = 8
    return output


def _rival_xor_overlaps(grid):
    facts = _facts_or_raise(grid)
    counts: Counter[tuple[int, int]] = Counter()
    for rr, rc in facts["reds"]:
        for dr, dc in facts["shape_offsets"]:
            counts[(rr + dr, rc + dc)] += 1
    output = full_grid(facts["h"], facts["w"], 0)
    for (r, c), count in counts.items():
        if count % 2:
            output[r][c] = 8
    return output


def _rival_marker_cells_only(grid):
    facts = _facts_or_raise(grid)
    output = full_grid(facts["h"], facts["w"], 0)
    for r, c in facts["reds"]:
        output[r][c] = 8
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "marker_as_answer_identity": _rival_identity,
    "first_marker_only": _rival_first_marker_only,
    "fill_template_bbox": _rival_fill_template_bbox,
    "fixed_cardinal_cross": _rival_fixed_cross,
    "mirror_shape_horizontally": _rival_horizontal_mirror,
    "local_3x3_offsets_only": _rival_local_3x3_only,
    "xor_overlapping_copies": _rival_xor_overlaps,
    "cyan_at_marker_cells_only": _rival_marker_cells_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "mirror_shape_horizontally": _rival_horizontal_mirror,
}


def _refutes(name):
    rival = SEMANTIC_RIVALS[name]

    def predicate(grid):
        try:
            return rule_mirror(grid) != rival(grid)
        except Exception:
            return False

    return predicate


def _single_marker(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and facts["n_reds"] == 1


def _overlapping_stamps(grid):
    facts = _grid_facts(grid)
    return not facts["errors"] and facts["overlap_cells"] > 0


SEMANTIC_WITNESSES = {
    "clears_source_and_markers": _refutes("marker_as_answer_identity"),
    "multiple_destinations": _refutes("first_marker_only"),
    "template_has_bbox_holes": _refutes("fill_template_bbox"),
    "template_is_not_fixed_cross": _refutes("fixed_cardinal_cross"),
    "asymmetric_template": _refutes("mirror_shape_horizontally"),
    "long_range_offsets": _refutes("local_3x3_offsets_only"),
    "overlapping_copies_use_union": _overlapping_stamps,
    "output_is_full_template_not_markers": _refutes("cyan_at_marker_cells_only"),
    "single_destination_branch": _single_marker,
}
WITNESS_RIVALS = {
    "clears_source_and_markers": ["marker_as_answer_identity"],
    "multiple_destinations": ["first_marker_only"],
    "template_has_bbox_holes": ["fill_template_bbox"],
    "template_is_not_fixed_cross": ["fixed_cardinal_cross"],
    "asymmetric_template": ["mirror_shape_horizontally"],
    "long_range_offsets": ["local_3x3_offsets_only"],
    "overlapping_copies_use_union": ["xor_overlapping_copies"],
    "output_is_full_template_not_markers": ["cyan_at_marker_cells_only"],
}
# This predicate measures positive schedule coverage rather than disagreement
# with a named solver.  Declare it honestly so strict semantic lint does not
# mistake branch presence for rival-refutation evidence.
BRANCH_WITNESSES = ("single_destination_branch",)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible rival to be eliminated by the demos."""
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
            reasons.append(f"demo {index} output disagrees with exact offset stamping")
            continue
        observations.append(semantic_observables(pair["input"]))

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query malformed: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with exact offset stamping")

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
        reasons.append("demonstrations do not vary the cyan template")
    if not any(not row["horizontally_symmetric"] for row in observations):
        reasons.append("demonstrations never break the horizontal-mirroring shortcut")
    if not any(row["n_reds"] > 1 for row in observations):
        reasons.append("demonstrations never require copying to multiple red markers")
    if not any(row["overlap_cells"] > 0 for row in observations):
        reasons.append("demonstrations never show how overlapping copies combine")
    return reasons
