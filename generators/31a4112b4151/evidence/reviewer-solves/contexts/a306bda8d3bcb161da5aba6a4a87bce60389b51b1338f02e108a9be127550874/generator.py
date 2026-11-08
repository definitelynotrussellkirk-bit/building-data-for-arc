"""Generator for M124 — stamp an anchored prototype at every color-9 target.

The first 4-connected non-zero component containing a color-9 cell is the
prototype component.  Its first color-9 cell in row-major order is the origin;
all non-9 cells in that component are copied, at the same relative offsets and
colors, to every color-9 cell in the grid.  Stamps are clipped at grid edges and
all color-9 cells disappear from the output.

This source deliberately covers the three canonical complications that the old
fixture-style generator missed: variable prototype size/shape, a second target
that may touch and therefore belong to the prototype component, and targets
whose stamps are only partly (or wholly) in bounds.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "31a4112b4151"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "1c0487137cc2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains one 4-connected prototype component with "
    "one or more color-9 target cells and a single-colored 3-6 cell shape. "
    "The first 9 in that component is the origin. Additional 9 targets may be "
    "isolated or may touch the prototype, and some targets may lie near an "
    "edge. The rule erases every 9 and stamps the prototype's non-9 relative "
    "offsets at every 9, clipping cells that fall outside the grid."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "exactly one non-zero component of size >1 contains color 9",
    "the selected prototype has one non-9 color and 3-6 non-9 cells",
    "the grid has 2-4 color-9 targets; non-prototype non-zero components are singleton 9s",
    "at least one non-origin target produces a visible stamped cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted by difficulty over 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted by difficulty over 7..12",
        "valid": "7..12",
    },
    "n_anchors": {
        "type": "int",
        "default": "weighted by difficulty over 2..4 total color-9 targets",
        "valid": "2..4",
    },
    "template_color": {
        "type": "color",
        "default": "rng 1..8",
        "valid": "1..8",
    },
}

# Every profile is connected through the origin (0, 0), but the origin itself
# is the color-9 anchor and is therefore not included in these colored offsets.
# The first and fifth profiles are the exact canonical train/test shapes.
_TEMPLATE_PROFILES: tuple[tuple[str, tuple[tuple[int, int], ...]], ...] = (
    ("canonical_corner3", ((0, 1), (1, 0), (1, 1))),
    ("bar_below3", ((1, -1), (1, 0), (1, 1))),
    ("bar_right3", ((-1, 1), (0, 1), (1, 1))),
    ("hook4", ((0, 1), (1, 0), (1, 1), (2, 1))),
    ("canonical_cross4", ((-1, 0), (0, -1), (0, 1), (1, 0))),
    ("zigzag5", ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2))),
    ("asymmetric5", ((-1, 0), (0, 1), (1, -1), (1, 0), (1, 1))),
    ("branched6", ((-1, 0), (0, 1), (1, -1), (1, 0), (1, 1), (2, 1))),
)
PROFILE_BY_OFFSETS = {
    tuple(sorted(offsets)): name for name, offsets in _TEMPLATE_PROFILES
}
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_LAYOUTS_PER_ANCHOR = 4
_LAYOUT_ATTEMPTS_PER_ANCHOR = 64


def _weighted_values(values: Iterable[int], preferred: Iterable[int]) -> tuple[int, ...]:
    """Keep the full override domain while biasing ordinary draws."""
    base = tuple(values)
    return base + tuple(preferred) * 3


def _components_nonzero(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
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
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(sorted(cells))
    return sorted(components, key=lambda cells: cells[0])


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Return the exact rule-relevant scene facts, or structural errors."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of rows"], "facts": None}
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    h, w = len(grid), len(grid[0])
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")

    components = _components_nonzero(grid)
    candidates = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[r][c] == 9 for r, c in cells)
    ]
    if len(candidates) != 1:
        errors.append(
            f"expected exactly one non-zero component of size >1 containing 9, found {len(candidates)}"
        )
        return {"errors": errors, "facts": None}

    proto = candidates[0]
    proto_set = set(proto)
    proto_nines = sorted((r, c) for r, c in proto if grid[r][c] == 9)
    if not proto_nines:
        errors.append("prototype component has no color-9 origin")
        return {"errors": errors, "facts": None}
    anchor = proto_nines[0]
    template_cells = sorted(
        (r, c, grid[r][c]) for r, c in proto if grid[r][c] != 9
    )
    template_colors = {value for _, _, value in template_cells}
    if not 3 <= len(template_cells) <= 6:
        errors.append(
            f"prototype must contain 3-6 non-9 cells, found {len(template_cells)}"
        )
    if len(template_colors) != 1:
        errors.append(
            f"prototype non-9 cells must use one color, found {sorted(template_colors)}"
        )

    targets = sorted(
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 9
    )
    if not 2 <= len(targets) <= 4:
        errors.append(f"expected 2-4 color-9 targets, found {len(targets)}")

    for component in components:
        if component is proto or set(component) == proto_set:
            continue
        if len(component) != 1 or grid[component[0][0]][component[0][1]] != 9:
            errors.append("every non-prototype non-zero component must be a singleton 9")
            break

    offsets = tuple(
        sorted((r - anchor[0], c - anchor[1], value) for r, c, value in template_cells)
    )
    visible_by_target: dict[tuple[int, int], int] = {}
    clipped_by_target: dict[tuple[int, int], int] = {}
    for tr, tc in targets:
        visible = clipped = 0
        for dr, dc, _ in offsets:
            rr, cc = tr + dr, tc + dc
            if 0 <= rr < h and 0 <= cc < w:
                visible += 1
            else:
                clipped += 1
        visible_by_target[(tr, tc)] = visible
        clipped_by_target[(tr, tc)] = clipped

    non_origin_targets = [target for target in targets if target != anchor]
    if non_origin_targets and not any(visible_by_target[target] for target in non_origin_targets):
        errors.append("no non-origin target produces a visible stamp")

    template_color = next(iter(template_colors), None)
    profile_offsets = tuple(sorted((dr, dc) for dr, dc, _ in offsets))
    facts = {
        "height": h,
        "width": w,
        "components": components,
        "prototype": proto,
        "prototype_set": proto_set,
        "anchor": anchor,
        "prototype_nines": proto_nines,
        "targets": targets,
        "template_cells": template_cells,
        "template_color": template_color,
        "template_size": len(template_cells),
        "offsets": offsets,
        "profile_offsets": profile_offsets,
        "profile_name": PROFILE_BY_OFFSETS.get(profile_offsets, "other"),
        "touch_mode": "touching" if len(proto_nines) > 1 else "isolated",
        "clip_mode": (
            "partial"
            if any(clipped_by_target[target] > 0 for target in non_origin_targets)
            else "none"
        ),
        "visible_by_target": visible_by_target,
        "clipped_by_target": clipped_by_target,
    }
    return {"errors": errors, "facts": facts}


def _official_output(grid: list[list[int]]) -> list[list[int]]:
    """Python parity mirror used only for audits and rival-rule checks."""
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("outside the task grammar: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    out = full_grid(facts["height"], facts["width"], 0)
    for tr, tc in facts["targets"]:
        for dr, dc, value in facts["offsets"]:
            rr, cc = tr + dr, tc + dc
            if 0 <= rr < facts["height"] and 0 <= cc < facts["width"]:
                out[rr][cc] = value
    return out


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every declared exact semantic axis from the returned grid."""
    analysis = analyze_scene(grid)
    if analysis["facts"] is None:
        return {}
    facts = analysis["facts"]
    return {
        "n_anchors": len(facts["targets"]),
        "template_color": facts["template_color"],
    }


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full canonical-compatible teaching grammar."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = analyze_scene(grid)
    errors = list(analysis["errors"])
    if analysis["facts"] is None:
        return errors
    facts = analysis["facts"]

    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        observed = observe_overrides(grid)
        for axis in ("n_anchors", "template_color"):
            if axis in requested and observed.get(axis) != requested[axis]:
                errors.append(
                    f"{axis} requested {requested[axis]!r}, observed {observed.get(axis)!r}"
                )
        if "grid_h" in requested and facts["height"] != requested["grid_h"]:
            errors.append(
                f"grid_h requested {requested['grid_h']}, observed {facts['height']}"
            )
        if "grid_w" in requested and facts["width"] != requested["grid_w"]:
            errors.append(
                f"grid_w requested {requested['grid_w']}, observed {facts['width']}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """All generated scenes and all public pairs live on this manifold."""
    return self_check(grid)


def _cell_adjacent(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return abs(left[0] - right[0]) + abs(left[1] - right[1]) == 1


def _target_status(
    target: tuple[int, int],
    offsets: tuple[tuple[int, int], ...],
    h: int,
    w: int,
) -> tuple[int, int]:
    visible = sum(
        0 <= target[0] + dr < h and 0 <= target[1] + dc < w
        for dr, dc in offsets
    )
    return visible, len(offsets) - visible


def _omitted_targets_add_visible_cells(
    anchor: tuple[int, int],
    targets: tuple[tuple[int, int], ...],
    offsets: tuple[tuple[int, int], ...],
    h: int,
    w: int,
) -> bool:
    """Whether targets after the first extra change the stamped output.

    This is the concrete disagreement needed to refute the tempting shortcut
    "stamp only the prototype origin and the first additional 9".  All template
    cells share one color, so coordinate support is sufficient here.
    """
    ordered_targets = sorted((anchor, *targets))
    extras = [target for target in ordered_targets if target != anchor]
    if len(extras) < 2:
        return False

    def visible_cells(selected: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
        return {
            (target[0] + dr, target[1] + dc)
            for target in selected
            for dr, dc in offsets
            if 0 <= target[0] + dr < h and 0 <= target[1] + dc < w
        }

    limited = visible_cells((anchor, extras[0]))
    complete = visible_cells((anchor, *extras))
    return complete != limited


@lru_cache(maxsize=None)
def _candidate_layouts(
    h: int,
    w: int,
    offsets: tuple[tuple[int, int], ...],
    n_anchors: int,
    touch_mode: str,
    clip_mode: str,
    require_all_targets_evidence: bool = False,
) -> tuple[tuple[tuple[int, int], tuple[tuple[int, int], ...]], ...]:
    """Build a cached, spatially balanced bank of lawful layouts.

    The previous global ``256``-layout cutoff enumerated row-major and could
    fill the entire bank before advancing beyond the first prototype origin.
    Keep a small deterministic sample per lawful origin instead, with an
    exhaustive one-layout fallback so exact override combinations remain
    supported even when random proposals are unusually unlucky.
    """
    layouts: list[tuple[tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for ar in range(h):
        for ac in range(w):
            colored = {(ar + dr, ac + dc) for dr, dc in offsets}
            if any(not (0 <= r < h and 0 <= c < w) for r, c in colored):
                continue
            if (ar, ac) in colored:
                continue
            proto_cells = colored | {(ar, ac)}
            all_candidates = [
                (r, c)
                for r in range(h)
                for c in range(w)
                if (r, c) not in proto_cells
            ]
            touching = [
                cell
                for cell in all_candidates
                if cell > (ar, ac)
                and any(_cell_adjacent(cell, p) for p in colored)
            ]
            isolated = [
                cell
                for cell in all_candidates
                if not any(_cell_adjacent(cell, p) for p in proto_cells)
            ]

            if touch_mode == "touching" and not touching:
                continue

            bank_rng = stable_rng(
                0,
                (
                    f"{TASK_ID}|layout-bank|{h}|{w}|{offsets}|{n_anchors}|"
                    f"{touch_mode}|{clip_mode}|{require_all_targets_evidence}|{ar}|{ac}"
                ),
                VERSION,
            )
            anchor_layouts: list[
                tuple[tuple[int, int], tuple[tuple[int, int], ...]]
            ] = []
            seen_targets: set[tuple[tuple[int, int], ...]] = set()

            for _ in range(_LAYOUT_ATTEMPTS_PER_ANCHOR):
                if touch_mode == "touching":
                    chosen_prefix = (bank_rng.choice(touching),)
                else:
                    chosen_prefix = ()
                remaining = n_anchors - 1 - len(chosen_prefix)
                available = [
                    cell
                    for cell in isolated
                    if not chosen_prefix or not _cell_adjacent(cell, chosen_prefix[0])
                ]
                if len(available) < remaining:
                    continue
                rest = tuple(bank_rng.sample(available, remaining))
                targets = tuple(sorted(chosen_prefix + rest))
                if targets in seen_targets:
                    continue
                seen_targets.add(targets)
                if any(_cell_adjacent(a, b) for a, b in combinations(targets, 2)):
                    continue
                statuses = [_target_status(target, offsets, h, w) for target in targets]
                if any(visible == 0 for visible, _ in statuses):
                    continue
                has_clip = any(clipped > 0 for _, clipped in statuses)
                if (clip_mode == "partial") != has_clip:
                    continue
                if require_all_targets_evidence and not _omitted_targets_add_visible_cells(
                    (ar, ac), targets, offsets, h, w
                ):
                    continue
                anchor_layouts.append(((ar, ac), targets))
                if len(anchor_layouts) >= _LAYOUTS_PER_ANCHOR:
                    break

            if not anchor_layouts:
                # Preserve exact override support with a deterministic exhaustive
                # fallback.  This path is rare; the sampled bank is the normal
                # route and prevents row-major prefix collapse.
                first_choices: list[tuple[int, int] | None]
                first_choices = touching if touch_mode == "touching" else [None]
                for touching_target in first_choices:
                    chosen_prefix = () if touching_target is None else (touching_target,)
                    remaining = n_anchors - 1 - len(chosen_prefix)
                    available = [
                        cell
                        for cell in isolated
                        if touching_target is None
                        or not _cell_adjacent(cell, touching_target)
                    ]
                    for rest in combinations(available, remaining):
                        targets = tuple(sorted(chosen_prefix + rest))
                        if any(
                            _cell_adjacent(a, b)
                            for a, b in combinations(targets, 2)
                        ):
                            continue
                        statuses = [
                            _target_status(target, offsets, h, w)
                            for target in targets
                        ]
                        if any(visible == 0 for visible, _ in statuses):
                            continue
                        has_clip = any(clipped > 0 for _, clipped in statuses)
                        if (clip_mode == "partial") != has_clip:
                            continue
                        if (
                            require_all_targets_evidence
                            and not _omitted_targets_add_visible_cells(
                                (ar, ac), targets, offsets, h, w
                            )
                        ):
                            continue
                        anchor_layouts.append(((ar, ac), targets))
                        break
                    if anchor_layouts:
                        break

            layouts.extend(anchor_layouts)
    return tuple(layouts)


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


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

    if difficulty == "easy":
        h_pref, w_pref, n_pref = (7, 8, 9), (7, 8, 9), (2,)
    elif difficulty == "hard":
        # Keep hard examples large on average while anchoring canonical 9x9
        # scale in every pinned census, rather than starving this band.
        h_pref, w_pref, n_pref = (9, 9, 10, 11, 12), (9, 9, 10, 11, 12), (3, 4)
    else:
        h_pref, w_pref, n_pref = (8, 9, 10), (8, 9, 10), (2, 3)

    h = ctx.draw_choice("grid_h", _weighted_values(range(7, 13), h_pref))
    w = ctx.draw_choice("grid_w", _weighted_values(range(7, 13), w_pref))
    n_anchor_values = _weighted_values(range(2, 5), n_pref)
    teach_all_targets = (
        "n_anchors" not in overrides
        and sample_index % EXAMPLES_NEEDED == 2
    )
    if teach_all_targets:
        # Every consecutive four-demo window contains this residue.  Force at
        # least three targets so one demonstration can disprove the shortcut
        # that stamps only the first additional color-9 marker.
        n_anchor_values = tuple(value for value in n_anchor_values if value >= 3)
    n_anchors = ctx.draw_choice("n_anchors", n_anchor_values)
    template_color = ctx.draw_color("template_color", exclude={0, 9})
    rng = ctx.draw_rng("layout")

    # Sequential sample indices are intentionally a curriculum schedule: every
    # four-demo lesson sees four different shapes, both touching/isolation,
    # both clipping branches, and evidence that every target must be stamped.
    profile_name, offsets = _TEMPLATE_PROFILES[sample_index % len(_TEMPLATE_PROFILES)]
    del profile_name  # retained in scene analysis; no metadata-only axis claim.
    touch_mode = "touching" if sample_index % 3 == 1 else "isolated"
    clip_mode = "partial" if sample_index % 2 == 1 else "none"

    layouts = _candidate_layouts(
        h,
        w,
        offsets,
        n_anchors,
        touch_mode=touch_mode,
        clip_mode=clip_mode,
        require_all_targets_evidence=teach_all_targets,
    )
    if not layouts:
        raise ValueError(
            "no lawful layout for "
            f"{h}x{w}, n_anchors={n_anchors}, profile={sample_index % len(_TEMPLATE_PROFILES)}, "
            f"touch_mode={touch_mode}, clip_mode={clip_mode}"
        )
    (anchor_r, anchor_c), extra_targets = rng.choice(layouts)

    grid = full_grid(h, w, 0)
    grid[anchor_r][anchor_c] = 9
    for dr, dc in offsets:
        grid[anchor_r + dr][anchor_c + dc] = template_color
    for r, c in extra_targets:
        grid[r][c] = 9

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("internal generator error: " + "; ".join(errors))
    return grid


def _candidate_output(grid: list[list[int]], mode: str, fixed_offsets=None) -> list[list[int]]:
    analysis = analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        return deepcopy(grid)
    facts = analysis["facts"]
    h, w = facts["height"], facts["width"]
    offsets = facts["offsets"]
    if fixed_offsets is not None:
        offsets = tuple((dr, dc, facts["template_color"]) for dr, dc in fixed_offsets)
    out = full_grid(h, w, 0)

    if mode == "prototype_only":
        targets = facts["prototype_nines"]
    elif mode == "first_extra_only":
        targets = [facts["anchor"]]
        extras = [target for target in facts["targets"] if target != facts["anchor"]]
        if extras:
            targets.append(extras[0])
    else:
        targets = facts["targets"]

    for tr, tc in targets:
        if mode == "skip_clipped" and facts["clipped_by_target"][(tr, tc)] > 0:
            continue
        for dr, dc, value in offsets:
            rr, cc = tr + dr, tc + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    if mode == "keep_markers":
        for tr, tc in facts["targets"]:
            out[tr][tc] = 9
    return out


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons in which a concrete shortcut still predicts the query."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for label, pair in [
        *((f"demo {index}", pair) for index, pair in enumerate(demos)),
        ("query", query),
    ]:
        analysis = analyze_scene(pair.get("input"))
        if analysis["errors"] or analysis["facts"] is None:
            reasons.append(f"{label} input is outside the anchored-prototype grammar")
            continue
        if pair.get("output") != _official_output(pair["input"]):
            reasons.append(f"{label} output disagrees with the pinned prototype oracle")
    if reasons:
        return reasons

    first_facts = analyze_scene(demos[0]["input"])["facts"]
    fixed_offsets = tuple((dr, dc) for dr, dc, _ in first_facts["offsets"])
    rivals = {
        "fixed_first_demo_shape": lambda pair: _candidate_output(
            pair["input"], "official", fixed_offsets=fixed_offsets
        ),
        "prototype_component_targets_only": lambda pair: _candidate_output(
            pair["input"], "prototype_only"
        ),
        "first_extra_target_only": lambda pair: _candidate_output(
            pair["input"], "first_extra_only"
        ),
        "skip_edge_clipped_targets": lambda pair: _candidate_output(
            pair["input"], "skip_clipped"
        ),
        "preserve_color_9_markers": lambda pair: _candidate_output(
            pair["input"], "keep_markers"
        ),
    }
    for name, rival in rivals.items():
        survives = all(rival(pair) == pair["output"] for pair in demos)
        if survives and rival(query) != query["output"]:
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def mutation_fixtures():
    """Task-specific near-misses that the structural checker must reject."""
    base = generate(491, 8, difficulty="medium", n_anchors=3, template_color=4)
    facts = analyze_scene(base)["facts"]
    fixtures: list[tuple[str, list[list[int]]]] = []

    no_prototype = deepcopy(base)
    for r, c, _ in facts["template_cells"]:
        no_prototype[r][c] = 0
    fixtures.append(("all_targets_but_no_prototype", no_prototype))

    mixed_colors = deepcopy(base)
    r, c, _ = facts["template_cells"][0]
    mixed_colors[r][c] = 6
    fixtures.append(("mixed_template_colors", mixed_colors))

    second_prototype = deepcopy(base)
    isolated = next(target for target in facts["targets"] if target not in facts["prototype_set"])
    for dr, dc in DIR4:
        rr, cc = isolated[0] + dr, isolated[1] + dc
        if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and second_prototype[rr][cc] == 0:
            second_prototype[rr][cc] = 4
            break
    fixtures.append(("two_candidate_prototypes", second_prototype))

    stray_color = deepcopy(base)
    occupied = {cell for component in facts["components"] for cell in component}
    rr, cc = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if (r, c) not in occupied
        and base[r][c] == 0
        and all(not _cell_adjacent((r, c), p) for p in occupied)
    )
    stray_color[rr][cc] = 4
    fixtures.append(("disconnected_colored_distractor", stray_color))

    one_target = deepcopy(base)
    for target in facts["targets"]:
        if target != facts["anchor"]:
            one_target[target[0]][target[1]] = 0
    fixtures.append(("prototype_without_destination", one_target))
    return fixtures


SEMANTIC_WITNESSES = {
    "template_size_3": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["template_size"] == 3
    ),
    "template_size_4_plus": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["template_size"] >= 4
    ),
    "touching_target_in_prototype": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["touch_mode"] == "touching"
    ),
    "isolated_targets": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["touch_mode"] == "isolated"
    ),
    "edge_clipped_stamp": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["clip_mode"] == "partial"
    ),
    "all_stamps_in_bounds": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and analyze_scene(grid)["facts"]["clip_mode"] == "none"
    ),
    "three_or_more_targets": lambda grid: (
        analyze_scene(grid)["facts"] is not None
        and len(analyze_scene(grid)["facts"]["targets"]) >= 3
    ),
}

# These predicates are positive curriculum-branch coverage.  They intentionally
# do not claim that every firing refutes a particular rival; lesson_identifiable
# supplies the stronger, context-dependent shortcut check across demonstrations.
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
