"""Generator for ARC task 994f16f93144 — highlight diagonal triple centers.

The canonical rule scans every interior nonzero cell.  When its two opposite
neighbors on either diagonal have the same color, that center is recolored to
cyan (8).  Endpoints and all non-matching structures stay unchanged.

Ordinary lessons deliberately mix exact canonical-profile anchors with
counterexamples: longer same-color diagonal chains, axis-aligned triples,
mismatched-color diagonals, repeated colors, and interior/border placements.
The longer chains distinguish the actual local-window predicate from the
canonical-compatible shortcut "only isolated exact three-cell objects count".
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "994f16f93144"
TASK_ID = "994f16f93144"
VERSION = "3.2.0"
RULE_HASH = "606a0be0f9ee"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "On a background-0 grid, recolor an interior nonzero cell to cyan (8) "
    "exactly when its two opposite diagonal neighbors have the same color as "
    "the center. Both down-right and down-left triples count. Endpoints, "
    "axis-aligned triples, diagonal pairs, and mismatched-color diagonals stay "
    "unchanged."
)

INVARIANTS = [
    "background is color 0 and input color 8 is absent",
    "each target is a local same-color diagonal window; collinear windows may overlap in a longer chain",
    "both diagonal slopes are lawful and ordinary lessons cover both",
    "non-target motifs are spatially separated and never create an accidental target",
    "normal draws contain at least one target, so the oracle output is never an identity",
]

# Some exact multi-axis requests are geometrically impossible under the declared
# isolation margin.  The override checker treats these as falsifiable contracts,
# not as arbitrary generation failures.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"diag_dir": "mixed", "n_triples": 1},
    {"grid_h": 7, "grid_w": 7},
    {"grid_h": 7, "n_triples": 5},
    {"grid_w": 7, "n_triples": 5},
]

DIAG_DIRECTIONS = ("main", "anti", "mixed")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded with a 25% canonical-profile schedule",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded with a 25% canonical-profile schedule",
        "valid": "7..12",
    },
    "n_triples": {
        "type": "int",
        "default": "difficulty-banded, capacity checked",
        "valid": "1..5",
    },
    "n_distractors": {
        "type": "int",
        "default": "0 for canonical anchors; otherwise difficulty-banded",
        "valid": "0..4",
    },
    "diag_dir": {
        "type": "str",
        "default": "scheduled main|anti|mixed",
        "valid": "main|anti|mixed",
    },
    "border_target": {
        "type": "bool",
        "default": "scheduled false|true",
        "valid": "false|true",
    },
}

_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_TARGET_OFFSETS = {
    "main": ((-1, -1), (0, 0), (1, 1)),
    "anti": ((-1, 1), (0, 0), (1, -1)),
}
_DISTRACTOR_KINDS = (
    "mismatched_main",
    "mismatched_anti",
    "row3",
    "col3",
    "diag_pair_main",
    "diag_pair_anti",
    "elbow",
    "singleton",
)
_DISTRACTOR_OFFSETS = {
    "mismatched_main": ((0, 0), (1, 1), (2, 2)),
    "mismatched_anti": ((0, 2), (1, 1), (2, 0)),
    "row3": ((0, 0), (0, 1), (0, 2)),
    "col3": ((0, 0), (1, 0), (2, 0)),
    "diag_pair_main": ((0, 0), (1, 1)),
    "diag_pair_anti": ((0, 1), (1, 0)),
    "elbow": ((0, 0), (1, 0), (1, 1)),
    "singleton": ((0, 0),),
}


@dataclass(frozen=True)
class Target:
    center: tuple[int, int]
    direction: str
    color: int
    cells: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class MotifPlacement:
    kind: str
    cells: tuple[tuple[int, int], ...]


def _is_arc_grid(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"], 0, 0
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["all cells must be literal ARC integers 0..9"], h, w
    return [], h, w


def _target_cells(center: tuple[int, int], direction: str) -> tuple[tuple[int, int], ...]:
    r, c = center
    return tuple((r + dr, c + dc) for dr, dc in _TARGET_OFFSETS[direction])


def _touches_border(cells: Iterable[tuple[int, int]], h: int, w: int) -> bool:
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)


def _find_targets(grid: list[list[int]]) -> list[Target]:
    h, w = len(grid), len(grid[0])
    targets: list[Target] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            if value in (0, 8):
                continue
            if grid[r - 1][c - 1] == value == grid[r + 1][c + 1]:
                targets.append(Target((r, c), "main", value, _target_cells((r, c), "main")))
            if grid[r - 1][c + 1] == value == grid[r + 1][c - 1]:
                targets.append(Target((r, c), "anti", value, _target_cells((r, c), "anti")))
    return targets


def _components8(
    grid: list[list[int]], cells: Iterable[tuple[int, int]]
) -> list[list[tuple[int, int]]]:
    remaining = set(cells)
    out: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        comp: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            comp.append((r, c))
            for dr, dc in _DIRS8:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        out.append(sorted(comp))
    return out


def _normalized_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _distractor_kind(grid: list[list[int]], cells: list[tuple[int, int]]) -> str | None:
    shape = _normalized_cells(cells)
    values = [grid[r][c] for r, c in cells]
    same = len(set(values)) == 1
    if shape == ((0, 0),):
        return "singleton"
    if shape in {((0, 0), (1, 1)), ((0, 1), (1, 0))} and same:
        return "diag_pair"
    if shape in {((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0))} and same:
        return "axis_line"
    if shape in {
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    } and same:
        return "elbow"
    if shape in {
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    } and not same:
        return "mismatched_diagonal"
    return None


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors, h, w = _is_arc_grid(grid)
    if errors:
        return {"errors": errors, "grid_h": h, "grid_w": w}

    if not (7 <= h <= 12):
        errors.append(f"height {h} outside 7..12")
    if not (7 <= w <= 12):
        errors.append(f"width {w} outside 7..12")
    if any(value == 8 for row in grid for value in row):
        errors.append("input color 8 is reserved for the output and must be absent")
    zero_count = sum(value == 0 for row in grid for value in row)
    if zero_count == 0:
        errors.append("background color 0 must be present")

    targets = _find_targets(grid)
    centers = [target.center for target in targets]
    if len(centers) != len(set(centers)):
        errors.append("a center matches both diagonal directions")

    owners: dict[tuple[int, int], list[Target]] = {}
    for target in targets:
        for cell in target.cells:
            owners.setdefault(cell, []).append(target)
    membership: Counter[tuple[int, int]] = Counter(
        {cell: len(cell_owners) for cell, cell_owners in owners.items()}
    )
    overlaps = sorted(cell for cell, count in membership.items() if count > 1)
    conflicting_overlaps = [
        cell
        for cell in overlaps
        if len({target.direction for target in owners[cell]}) > 1
        or len({target.color for target in owners[cell]}) > 1
    ]
    if conflicting_overlaps:
        errors.append(
            "overlapping target windows must be same-color and collinear; "
            f"conflicts at {conflicting_overlaps[:4]}"
        )

    target_cells = set(membership)
    for index, target in enumerate(targets):
        triple = set(target.cells)
        adjacent_external = {
            (rr, cc)
            for r, c in triple
            for dr, dc in _DIRS8
            for rr, cc in [(r + dr, c + dc)]
            if 0 <= rr < h
            and 0 <= cc < w
            and grid[rr][cc] != 0
            and (rr, cc) not in target_cells
        }
        if adjacent_external:
            errors.append(
                f"target {index} is not isolated; adjacent nonzero cells "
                f"{sorted(adjacent_external)[:4]}"
            )

    remaining_nonzero = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in target_cells
    }
    distractor_components = _components8(grid, remaining_nonzero)
    distractor_kinds: list[str] = []
    for index, component in enumerate(distractor_components):
        kind = _distractor_kind(grid, component)
        if kind is None:
            errors.append(
                f"distractor {index} has unsupported geometry/colors: "
                f"{_normalized_cells(component)}"
            )
        else:
            distractor_kinds.append(kind)

    if not (1 <= len(targets) <= 5):
        errors.append(f"expected 1..5 target triples, found {len(targets)}")
    if len(distractor_components) > 4:
        errors.append(
            f"expected at most 4 distractor components, found {len(distractor_components)}"
        )

    directions = {target.direction for target in targets}
    if directions == {"main"}:
        diag_dir = "main"
    elif directions == {"anti"}:
        diag_dir = "anti"
    elif directions == {"main", "anti"}:
        diag_dir = "mixed"
    else:
        diag_dir = "none"

    nonzero_colors = {
        value for row in grid for value in row if value not in (0, 8)
    }
    target_colors = {target.color for target in targets}
    distractor_colors = {
        grid[r][c] for component in distractor_components for r, c in component
    }
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "targets": targets,
        "target_cells": target_cells,
        "overlapping_target_cells": overlaps,
        "n_triples": len(targets),
        "n_distractors": len(distractor_components),
        "distractor_components": distractor_components,
        "distractor_kinds": distractor_kinds,
        "diag_dir": diag_dir,
        "border_target": any(
            _touches_border(target.cells, h, w) for target in targets
        ),
        "nonzero_colors": nonzero_colors,
        "target_colors": target_colors,
        "distractor_colors": distractor_colors,
        "shared_target_distractor_colors": target_colors & distractor_colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/ambiguous teaching scenes while accepting all canonicals."""
    return list(_analyze_scene(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | bool | str]:
    """Recover every declared exact semantic axis from the returned grid."""
    facts = _analyze_scene(grid)
    if facts["errors"]:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_triples": facts["n_triples"],
        "n_distractors": facts["n_distractors"],
        "diag_dir": facts["diag_dir"],
        "border_target": facts["border_target"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The linked empirical manifold shared by all train and held-out inputs."""
    facts = _analyze_scene(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    h, w = facts["grid_h"], facts["grid_w"]
    if h != w or h not in (7, 8, 9):
        reasons.append("canonical inputs are square with side length 7, 8, or 9")
    if facts["n_triples"] != 3:
        reasons.append("canonical inputs contain exactly three target triples")
    if facts["n_distractors"] != 0:
        reasons.append("canonical inputs contain no distractor components")
    if facts["diag_dir"] != "mixed":
        reasons.append("canonical inputs contain both diagonal slopes")
    if not facts["border_target"]:
        reasons.append("every canonical input has at least one border-touching target")
    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) != 3 or any(count != 3 for count in counts.values()):
        reasons.append("canonical inputs use three distinct colors, three cells each")
    target_colors = [target.color for target in facts["targets"]]
    if len(set(target_colors)) != 3:
        reasons.append("canonical targets use distinct colors")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small Python mirror for tests and visual review; Racket remains authority."""
    out = [row[:] for row in grid]
    for target in _find_targets(grid):
        r, c = target.center
        out[r][c] = 8
    return out


def _isolated_exact_triples_only(grid: list[list[int]]) -> list[list[int]]:
    """Plausible but wrong rival: mark only exact 3-cell color components.

    Every canonical demonstration is compatible with this object-level rule.
    It disagrees with the authority on a four-cell diagonal chain, where the
    true local predicate marks both interior cells.
    """
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            start = (start_r, start_c)
            if color in (0, 8) or start in seen:
                continue
            seen.add(start)
            queue = deque([start])
            component: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in _DIRS8:
                    rr, cc = r + dr, c + dc
                    neighbor = (rr, cc)
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and neighbor not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            shape = _normalized_cells(component)
            if len(component) == 3 and shape in {
                ((0, 0), (1, 1), (2, 2)),
                ((0, 2), (1, 1), (2, 0)),
            }:
                center = sorted(component)[1]
                out[center[0]][center[1]] = 8
    return out


def _has_main(grid) -> bool:
    return any(target.direction == "main" for target in _find_targets(grid))


def _has_anti(grid) -> bool:
    return any(target.direction == "anti" for target in _find_targets(grid))


def _has_mixed(grid) -> bool:
    directions = {target.direction for target in _find_targets(grid)}
    return directions == {"main", "anti"}


def _has_border_target(grid) -> bool:
    facts = _analyze_scene(grid)
    return not facts["errors"] and facts["border_target"]


def _has_interior_only_targets(grid) -> bool:
    facts = _analyze_scene(grid)
    return not facts["errors"] and not facts["border_target"]


def _has_distractor(grid) -> bool:
    facts = _analyze_scene(grid)
    return not facts["errors"] and facts["n_distractors"] > 0


def _has_mismatched_diagonal(grid) -> bool:
    facts = _analyze_scene(grid)
    return not facts["errors"] and "mismatched_diagonal" in facts["distractor_kinds"]


def _has_shared_target_distractor_color(grid) -> bool:
    facts = _analyze_scene(grid)
    return bool(not facts["errors"] and facts["shared_target_distractor_colors"])


def _has_overlapping_diagonal_targets(grid) -> bool:
    facts = _analyze_scene(grid)
    return bool(not facts["errors"] and facts["overlapping_target_cells"])


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "main_diagonal_target": _has_main,
    "anti_diagonal_target": _has_anti,
    "mixed_diagonal_directions": _has_mixed,
    "border_touching_target": _has_border_target,
    "interior_only_targets": _has_interior_only_targets,
    "non_target_motif": _has_distractor,
    "mismatched_diagonal_distractor": _has_mismatched_diagonal,
    "target_color_reused_in_distractor": _has_shared_target_distractor_color,
    "overlapping_diagonal_targets": _has_overlapping_diagonal_targets,
}

# These eight predicates are positive schedule coverage.  The ninth is a real
# counterexample witness tied to the named rival below.
BRANCH_WITNESSES = {
    "main_diagonal_target",
    "anti_diagonal_target",
    "mixed_diagonal_directions",
    "border_touching_target",
    "interior_only_targets",
    "non_target_motif",
    "mismatched_diagonal_distractor",
    "target_color_reused_in_distractor",
}
SEMANTIC_RIVALS = {
    "isolated_exact_triples_only": _isolated_exact_triples_only,
}
WITNESS_RIVALS = {
    "overlapping_diagonal_targets": ["isolated_exact_triples_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _separated(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        abs(r - rr) > 1 or abs(c - cc) > 1
        for r, c in cells
        for rr, cc in occupied
    )


def _all_target_candidates(
    h: int, w: int, direction: str, *, length: int = 3
) -> list[tuple[tuple[int, int], ...]]:
    """Enumerate consecutive same-slope chains.

    Length three is one local target. Length four deliberately contains two
    overlapping local targets and is the generated rival counterexample.
    """
    if length < 3:
        raise ValueError("target chains must contain at least three cells")
    if direction == "main":
        return [
            tuple((top + offset, left + offset) for offset in range(length))
            for top in range(h - length + 1)
            for left in range(w - length + 1)
        ]
    return [
        tuple((top + offset, right - offset) for offset in range(length))
        for top in range(h - length + 1)
        for right in range(length - 1, w)
    ]


def _all_distractor_candidates(h: int, w: int, kind: str) -> list[MotifPlacement]:
    offsets = _DISTRACTOR_OFFSETS[kind]
    max_r = max(r for r, _ in offsets)
    max_c = max(c for _, c in offsets)
    return [
        MotifPlacement(kind, tuple((top + r, left + c) for r, c in offsets))
        for top in range(h - max_r)
        for left in range(w - max_c)
    ]


def _direction_plan(n_triples: int, diag_dir: str, rng) -> list[str]:
    if diag_dir == "mixed":
        if n_triples < 2:
            raise ValueError("diag_dir='mixed' requires n_triples >= 2")
        plan = ["main", "anti"]
        plan.extend(rng.choice(("main", "anti")) for _ in range(n_triples - 2))
        rng.shuffle(plan)
        return plan
    return [diag_dir] * n_triples


def _search_layout(
    h: int,
    w: int,
    n_triples: int,
    n_distractors: int,
    diag_dir: str,
    border_target: bool,
    rng,
    *,
    extended_target: bool = False,
) -> tuple[list[tuple[str, tuple[tuple[int, int], ...]]], list[MotifPlacement]] | None:
    motif_count = n_triples - 1 if extended_target else n_triples
    if motif_count < 1:
        return None
    plan = _direction_plan(motif_count, diag_dir, rng)
    target_options: list[list[tuple[tuple[int, int], ...]]] = []
    for index, direction in enumerate(plan):
        length = 4 if extended_target and index == 0 else 3
        options = _all_target_candidates(h, w, direction, length=length)
        if not border_target:
            options = [cells for cells in options if not _touches_border(cells, h, w)]
        elif index == 0:
            options = [cells for cells in options if _touches_border(cells, h, w)]
        rng.shuffle(options)
        target_options.append(options)

    selected_targets: list[tuple[str, tuple[tuple[int, int], ...]]] = []

    def choose_target(index: int, occupied: set[tuple[int, int]]) -> bool:
        if index == len(plan):
            return True
        direction = plan[index]
        for cells in target_options[index]:
            if not _separated(cells, occupied):
                continue
            selected_targets.append((direction, cells))
            if choose_target(index + 1, occupied | set(cells)):
                return True
            selected_targets.pop()
        return False

    if not choose_target(0, set()):
        return None

    occupied = {cell for _, cells in selected_targets for cell in cells}
    kinds: list[str] = []
    if n_distractors:
        kinds.append(rng.choice(("mismatched_main", "mismatched_anti")))
    if n_distractors >= 2:
        kinds.append(rng.choice(("row3", "col3")))
    while len(kinds) < n_distractors:
        kinds.append(rng.choice(_DISTRACTOR_KINDS[2:]))
    rng.shuffle(kinds)

    options_by_kind: list[list[MotifPlacement]] = []
    for kind in kinds:
        options = _all_distractor_candidates(h, w, kind)
        rng.shuffle(options)
        options_by_kind.append(options)

    selected_distractors: list[MotifPlacement] = []

    def choose_distractor(index: int, used: set[tuple[int, int]]) -> bool:
        if index == len(kinds):
            return True
        for placement in options_by_kind[index]:
            if not _separated(placement.cells, used):
                continue
            selected_distractors.append(placement)
            if choose_distractor(index + 1, used | set(placement.cells)):
                return True
            selected_distractors.pop()
        return False

    if not choose_distractor(0, occupied):
        return None
    return selected_targets, selected_distractors


def _difficulty_ranges(difficulty: Any, profile: int) -> tuple[tuple[int, int], tuple[int, int], int, int]:
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    if band == "easy":
        if profile == 1:
            dims = ((8, 8), (9, 9))
        elif profile == 2:
            dims = ((10, 10), (8, 8))
        elif profile == 3:
            dims = ((9, 9), (9, 9))
        else:
            dims = ((7, 9), (7, 9))
        targets, distractors = (2 if profile == 1 else 3), 1
    elif band == "hard":
        dims = {
            1: ((10, 10), (12, 12)),
            2: ((11, 11), (10, 10)),
            3: ((12, 12), (11, 11)),
        }.get(profile, ((10, 12), (10, 12)))
        targets, distractors = (4 if profile != 3 else 5), (2 if profile == 2 else 3)
    else:
        dims = {
            1: ((8, 8), (10, 10)),
            2: ((9, 9), (11, 11)),
            3: ((10, 10), (9, 9)),
        }.get(profile, ((8, 11), (8, 11)))
        targets, distractors = (3 if profile != 3 else 4), (1 if profile == 2 else 2)
    return dims[0], dims[1], targets, distractors


def _pin_default(ctx, provided: set[str], name: str, value: Any) -> None:
    if name not in provided:
        ctx.overrides[name] = value


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
    provided = {name for name, value in overrides.items() if value is not None}
    raw_profile = sample_index % 4
    # Exact canonical anchors are ordinary-distribution priors, never a reason
    # to make an otherwise lawful explicit override fail.  Override calls use
    # one of the generalized profiles and adapt every unrequested companion
    # axis before any keyed draw is recorded.
    profile = raw_profile if not provided else 1 + (sample_index % 3)
    defaults_rng = ctx.draw_rng("scheduled_defaults")

    if profile == 0:
        canonical_size = defaults_rng.choice((7, 8, 9))
        _pin_default(ctx, provided, "grid_h", canonical_size)
        _pin_default(ctx, provided, "grid_w", canonical_size)
        _pin_default(ctx, provided, "n_triples", 3)
        _pin_default(ctx, provided, "n_distractors", 0)
        _pin_default(ctx, provided, "diag_dir", "mixed")
        _pin_default(ctx, provided, "border_target", True)
    else:
        h_range, w_range, target_default, distractor_default = _difficulty_ranges(
            difficulty, profile
        )
        _pin_default(ctx, provided, "grid_h", defaults_rng.randint(*h_range))
        _pin_default(ctx, provided, "grid_w", defaults_rng.randint(*w_range))
        _pin_default(ctx, provided, "n_triples", target_default)
        _pin_default(ctx, provided, "n_distractors", distractor_default)
        _pin_default(
            ctx,
            provided,
            "diag_dir",
            {1: "main", 2: "anti", 3: "mixed"}[profile],
        )
        _pin_default(ctx, provided, "border_target", profile == 2)

    # Make every single-axis boundary usable.  Incompatible *combinations*
    # still reject loudly, but an explicit count/position axis is paired with
    # spacious, conservative defaults rather than an accidental tiny profile.
    explicit_n = int(overrides["n_triples"]) if "n_triples" in provided else None
    explicit_d = int(overrides["n_distractors"]) if "n_distractors" in provided else None
    explicit_border = bool(overrides["border_target"]) if "border_target" in provided else None
    small_explicit_dimension = (
        ("grid_h" in provided and int(overrides["grid_h"]) <= 7)
        or ("grid_w" in provided and int(overrides["grid_w"]) <= 7)
    )
    spacious = (
        explicit_n is not None
        or explicit_d is not None
        or explicit_border is False
    )
    if spacious:
        _pin_default(ctx, provided, "grid_h", 12)
        _pin_default(ctx, provided, "grid_w", 12)
    if "grid_h" in provided and "grid_w" not in provided:
        ctx.overrides["grid_w"] = 12
    if "grid_w" in provided and "grid_h" not in provided:
        ctx.overrides["grid_h"] = 12
    if small_explicit_dimension:
        _pin_default(ctx, provided, "n_triples", 2)
        _pin_default(ctx, provided, "n_distractors", 0)
    if explicit_n == 1:
        _pin_default(ctx, provided, "diag_dir", "main")
        _pin_default(ctx, provided, "n_distractors", 1)
    elif explicit_n is not None and explicit_n >= 4:
        _pin_default(ctx, provided, "n_distractors", 0)
    if explicit_d is not None and explicit_d >= 3:
        _pin_default(ctx, provided, "n_triples", 2)
    if explicit_border is False:
        _pin_default(ctx, provided, "n_triples", 2)
        _pin_default(ctx, provided, "n_distractors", 1)

    h = ctx.draw_int("grid_h", 7, 12)
    w = ctx.draw_int("grid_w", 7, 12)
    diag_dir = ctx.draw_choice("diag_dir", DIAG_DIRECTIONS)
    border_target = ctx.draw_choice("border_target", (False, True))

    requested_n = int(ctx.overrides.get("n_triples", 3))
    requested_d = int(ctx.overrides.get("n_distractors", 1))
    if not 1 <= requested_n <= 5:
        raise ValueError(f"n_triples override {requested_n} outside 1..5")
    if not 0 <= requested_d <= 4:
        raise ValueError(f"n_distractors override {requested_d} outside 0..4")
    if diag_dir == "mixed" and requested_n < 2:
        if "diag_dir" in provided or "n_triples" in provided:
            raise ValueError("diag_dir='mixed' is incompatible with n_triples=1")
        diag_dir = "main"
        ctx.overrides["diag_dir"] = diag_dir

    layout_rng = ctx.draw_rng("layout")
    n_is_explicit = "n_triples" in provided
    d_is_explicit = "n_distractors" in provided
    extended_target = (
        profile != 0
        and requested_n >= 2
        and (diag_dir != "mixed" or requested_n >= 3)
    )
    layout = _search_layout(
        h,
        w,
        requested_n,
        requested_d,
        diag_dir,
        border_target,
        layout_rng,
        extended_target=extended_target,
    )
    if layout is None and not (n_is_explicit and d_is_explicit):
        target_values = [requested_n] if n_is_explicit else list(range(requested_n, 0, -1))
        distractor_values = [requested_d] if d_is_explicit else list(range(requested_d, -1, -1))
        for n_distractors in distractor_values:
            for n_triples in target_values:
                if diag_dir == "mixed" and n_triples < 2:
                    continue
                candidate_rng = ctx.draw_rng(
                    f"layout_fallback_{n_triples}_{n_distractors}"
                )
                candidate_extended = (
                    profile != 0
                    and n_triples >= 2
                    and (diag_dir != "mixed" or n_triples >= 3)
                )
                candidate = _search_layout(
                    h,
                    w,
                    n_triples,
                    n_distractors,
                    diag_dir,
                    border_target,
                    candidate_rng,
                    extended_target=candidate_extended,
                )
                if candidate is not None:
                    requested_n, requested_d, layout = n_triples, n_distractors, candidate
                    extended_target = candidate_extended
                    break
            if layout is not None:
                break
    if layout is None:
        raise ValueError(
            "requested motif combination cannot be placed without creating "
            f"accidental targets: {h}x{w}, n_triples={requested_n}, "
            f"n_distractors={requested_d}, diag_dir={diag_dir!r}, "
            f"border_target={border_target}"
        )

    ctx.overrides["n_triples"] = requested_n
    ctx.overrides["n_distractors"] = requested_d
    n_triples = ctx.draw_int("n_triples", 1, 5)
    n_distractors = ctx.draw_int("n_distractors", 0, 4)
    if (n_triples, n_distractors) != (requested_n, requested_d):
        raise AssertionError("internal count pin lost")

    target_layout, distractor_layout = layout
    target_motif_count = len(target_layout)
    g = full_grid(h, w, 0)
    color_rng = ctx.draw_rng("colors")
    legal_colors = [1, 2, 3, 4, 5, 6, 7, 9]

    if profile == 0 and not ({"n_triples", "n_distractors"} & provided):
        target_colors = color_rng.sample(legal_colors, target_motif_count)
    else:
        distinct = min(max(2, target_motif_count - 1), 4, target_motif_count)
        palette = color_rng.sample(legal_colors, distinct)
        target_colors = [
            palette[index % distinct] for index in range(target_motif_count)
        ]
        if target_motif_count >= 2:
            target_colors[-1] = target_colors[0]
        color_rng.shuffle(target_colors)

    for (direction, cells), color in zip(target_layout, target_colors):
        for r, c in cells:
            g[r][c] = color

    extra_colors = [color for color in legal_colors if color not in set(target_colors)]
    for index, placement in enumerate(distractor_layout):
        shared = target_colors[index % len(target_colors)]
        if placement.kind.startswith("mismatched_"):
            center_color = next(
                (color for color in target_colors if color != shared),
                extra_colors[0],
            )
            ordered = list(placement.cells)
            # All mismatched templates list the geometric center second.
            for cell_index, (r, c) in enumerate(ordered):
                g[r][c] = center_color if cell_index == 1 else shared
        else:
            color = shared if index % 2 == 0 or not extra_colors else extra_colors[index % len(extra_colors)]
            for r, c in placement.cells:
                g[r][c] = color

    errors = self_check(g, difficulty=difficulty)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(g)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_triples": n_triples,
        "n_distractors": n_distractors,
        "diag_dir": diag_dir,
        "border_target": border_target,
    }
    if observed != expected:
        raise AssertionError(f"constructed axes {expected!r}, observed {observed!r}")
    return g


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that refute the main plausible shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]

    demo_facts: list[dict[str, Any]] = []
    centers: set[tuple[int, int, int, int]] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts = _analyze_scene(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} malformed: {facts['errors'][0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the diagonal-center rule")
        demo_facts.append(facts)
        h, w = facts["grid_h"], facts["grid_w"]
        centers.update((target.center[0], target.center[1], h, w) for target in facts["targets"])

    if demo_facts:
        directions = {
            target.direction for facts in demo_facts for target in facts["targets"]
        }
        if directions != {"main", "anti"}:
            reasons.append("demos do not establish that both diagonal slopes count")
        if not any(facts["n_distractors"] for facts in demo_facts):
            reasons.append("demos contain no non-target motif to refute object-count shortcuts")
        if not any(
            "mismatched_diagonal" in facts["distractor_kinds"]
            for facts in demo_facts
        ):
            reasons.append("demos contain no mismatched diagonal counterexample")
        if not any(facts["shared_target_distractor_colors"] for facts in demo_facts):
            reasons.append("demos never reuse a target color in a non-target motif")
        if not any(facts["overlapping_target_cells"] for facts in demo_facts):
            reasons.append(
                "demos contain no longer diagonal chain to refute the "
                "isolated-exact-triples shortcut"
            )
        if len(centers) < 3:
            reasons.append("target centers do not vary enough to refute fixed-position rules")
        sizes = {(facts["grid_h"], facts["grid_w"]) for facts in demo_facts}
        if len(sizes) < 2:
            reasons.append("demos do not vary canvas size")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qfacts = _analyze_scene(query["input"])
        if qfacts["errors"]:
            reasons.append(f"query malformed: {qfacts['errors'][0]}")
        if "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the diagonal-center rule")

    if isinstance(query, dict) and "input" in query and "output" in query:
        for name, rival in LESSON_COMPETITORS.items():
            fits_demos = all(
                rival(pair["input"]) == pair["output"]
                for pair in demos
                if isinstance(pair, dict)
                and "input" in pair
                and "output" in pair
            )
            if fits_demos and rival(query["input"]) != query["output"]:
                reasons.append(
                    f"competitor {name!r} fits every demo but disagrees on the query"
                )
    return reasons
