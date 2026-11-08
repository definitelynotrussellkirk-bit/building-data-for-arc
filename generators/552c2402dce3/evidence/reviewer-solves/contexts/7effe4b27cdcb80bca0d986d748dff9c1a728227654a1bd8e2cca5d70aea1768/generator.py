"""Generator for ARC task ``552c2402dce3`` (Missing Cyan Corner).

The canonical transformation is local: every 2x2 window containing exactly
three cyan (8) cells and one black (0) cell is completed by painting that one
black corner cyan.  Version 3 replaces the former acceptance-only checker and
nine mostly dead axes with a small exact contract.  Version 3.1 also mixes at
least two missing-corner orientations inside every generated input, preventing
a solver from broadcasting the first target's orientation to the whole grid.
Version 3.2 alternates canonical-like scenes with full-curriculum scenes.  Each
full-curriculum scene contains all three canonical-fitting shortcut killers, so
every consecutive five-pair lesson retains one after any single query rotation:

* an isolated three-cell cyan line that must remain unchanged;
* an already-complete 2x2 cyan square that must remain unchanged; and
* one valid L target connected to an extra cyan tail, which proves that the
  rule is about local 2x2 evidence rather than three-cell components or
  component bounding boxes.

All outputs remain 0/8 grids anchored to the canonical dimensions and palette.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "552c2402dce3"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "014607f2a279"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.10

SUMMARY = (
    "A black grid contains two to four cyan local targets with at least two "
    "different missing-corner orientations per input. Each target has "
    "exactly three cyan corners in a 2x2 window and one black missing corner. "
    "Complete every such window by painting only its missing corner cyan. "
    "Alternating full-curriculum scenes also contain a cyan line, a complete "
    "cyan 2x2 square, and a target joined to one extra cyan tail; those cells "
    "do not change unless "
    "they participate in an exact three-cyan/one-black 2x2 window."
)

INVARIANTS = [
    "grid cells are only black (0) and cyan (8)",
    "there are exactly 2..4 disjoint target windows with three cyan corners",
    "every generated input mixes at least two target missing-corner orientations",
    "different foreground components have a one-cell black moat",
    "curriculum fixtures are either absent or the complete tail+line+square trio",
    "the output changes exactly the missing black corner of every target window",
]

_GRID_SIZES = ("7x9", "8x10", "9x11", "10x12")
_CANONICAL_GRID_SIZES = frozenset(("7x9", "8x10", "9x11"))

AXES = {
    "grid_size": {
        "type": "str",
        "default": "difficulty-shaped choice among 7x9|8x10|9x11|10x12",
        "valid": "|".join(_GRID_SIZES),
    },
    "block_count": {
        "type": "int",
        "default": "easy=2, medium=2..3, hard=3..4, otherwise 2..4",
        "valid": "2..4",
    },
}

_CORNERS = ((0, 0), (0, 1), (1, 0), (1, 1))
_CORNER_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")
_MISSING_OFFSET = dict(zip(_CORNER_NAMES, _CORNERS))
_OFFSET_TO_MISSING = {offset: name for name, offset in _MISSING_OFFSET.items()}

# A fourth cyan cell at one of these positions keeps exactly one qualifying
# 2x2 window while making the foreground component larger than three cells.
_TAIL_OPTIONS = {
    "top_left": ((-1, 1), (1, -1)),
    "top_right": ((-1, 0), (1, 2)),
    "bottom_left": ((0, -1), (2, 1)),
    "bottom_right": ((0, 2), (2, 0)),
}

SCHEDULE_PROFILES = (
    "isolated_targets",
    "full_curriculum",
)

_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

Grid = list[list[int]]
Cell = tuple[int, int]
CellSet = frozenset[Cell]


def _normalize_grid(grid: Any) -> Grid:
    """Return a list-of-lists view, accepting canonical row strings."""
    if not isinstance(grid, (list, tuple)):
        return []
    normalized: Grid = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(char not in "0123456789" for char in row):
                return []
            normalized.append([int(char) for char in row])
        elif isinstance(row, (list, tuple)):
            normalized.append(list(row))
        else:
            return []
    return normalized


def _grid_size_label(h: int, w: int) -> str:
    return f"{h}x{w}"


def _parse_grid_size(label: str) -> tuple[int, int]:
    try:
        h_text, w_text = label.split("x", 1)
        dims = int(h_text), int(w_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid grid_size {label!r}") from exc
    if label not in _GRID_SIZES:
        raise ValueError(f"grid_size {label!r} is outside {_GRID_SIZES}")
    return dims


def _target_windows(grid: Grid) -> list[dict[str, Any]]:
    """Find exact 3-cyan/1-black 2x2 windows in the original grid."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    targets: list[dict[str, Any]] = []
    for r in range(h - 1):
        for c in range(w - 1):
            positions = tuple((r + dr, c + dc) for dr, dc in _CORNERS)
            values = tuple(grid[rr][cc] for rr, cc in positions)
            if values.count(8) != 3 or values.count(0) != 1:
                continue
            missing_index = values.index(0)
            missing_offset = _CORNERS[missing_index]
            targets.append(
                {
                    "anchor": (r, c),
                    "missing": _OFFSET_TO_MISSING[missing_offset],
                    "missing_cell": positions[missing_index],
                    "filled_cells": frozenset(
                        position
                        for position, value in zip(positions, values)
                        if value == 8
                    ),
                    "window_cells": frozenset(positions),
                }
            )
    return targets


def _components(grid: Grid) -> list[CellSet]:
    """Return cyan 4-connected components in reading order."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[CellSet] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: set[Cell] = set()
            while queue:
                cr, cc = queue.popleft()
                cells.add((cr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(frozenset(cells))
    return components


def _bbox(cells: Sequence[Cell]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_line_component(cells: CellSet) -> bool:
    if len(cells) != 3:
        return False
    r1, c1, r2, c2 = _bbox(tuple(cells))
    return (
        (r1 == r2 and c2 - c1 == 2 and cells == frozenset((r1, c) for c in range(c1, c2 + 1)))
        or (c1 == c2 and r2 - r1 == 2 and cells == frozenset((r, c1) for r in range(r1, r2 + 1)))
    )


def _is_solid_square_component(cells: CellSet) -> bool:
    if len(cells) != 4:
        return False
    r1, c1, r2, c2 = _bbox(tuple(cells))
    return r2 - r1 == 1 and c2 - c1 == 1 and cells == frozenset(
        (r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
    )


def _is_allowed_tailed_target(component: CellSet, target: dict[str, Any]) -> bool:
    if len(component) != 4:
        return False
    r0, c0 = target["anchor"]
    plain = set(target["filled_cells"])
    for dr, dc in _TAIL_OPTIONS[target["missing"]]:
        if component == frozenset((*plain, (r0 + dr, c0 + dc))):
            return True
    return False


def _components_have_black_moat(components: Sequence[CellSet]) -> bool:
    for index, left in enumerate(components):
        for right in components[index + 1 :]:
            if any(
                max(abs(lr - rr), abs(lc - rc)) <= 1
                for lr, lc in left
                for rr, rc in right
            ):
                return False
    return True


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    """Parse the complete generator grammar and return structured observables."""
    g = _normalize_grid(grid)
    if not g or not g[0]:
        return None, ["empty or malformed grid"]
    w = len(g[0])
    if any(len(row) != w for row in g):
        return None, ["ragged grid"]
    h = len(g)
    errors: list[str] = []
    size_label = _grid_size_label(h, w)
    if size_label not in _GRID_SIZES:
        errors.append(f"grid size {size_label} is outside {_GRID_SIZES}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or value not in (0, 8)
        for row in g
        for value in row
    ):
        errors.append("cells must be integer colors from the exact palette {0, 8}")
        return None, errors

    targets = _target_windows(g)
    components = _components(g)
    if not _components_have_black_moat(components):
        errors.append("foreground components do not have a one-cell black moat")

    component_kinds: list[str] = []
    target_components = 0
    tailed_targets = 0
    for component_index, component in enumerate(components):
        owned_targets = [
            target
            for target in targets
            if target["filled_cells"].issubset(component)
        ]
        if len(owned_targets) > 1:
            errors.append(
                f"component {component_index} participates in {len(owned_targets)} target windows"
            )
            component_kinds.append("invalid")
            continue
        if owned_targets:
            target = owned_targets[0]
            if component == target["filled_cells"]:
                component_kinds.append("isolated_target")
                target_components += 1
            elif _is_allowed_tailed_target(component, target):
                component_kinds.append("tailed_target")
                target_components += 1
                tailed_targets += 1
            else:
                errors.append(
                    f"component {component_index} contains a target plus unsupported extra cyan cells"
                )
                component_kinds.append("invalid")
            continue
        if _is_line_component(component):
            component_kinds.append("line_distractor")
        elif _is_solid_square_component(component):
            component_kinds.append("solid_square_distractor")
        else:
            errors.append(
                f"component {component_index} is neither a target nor a lawful distractor"
            )
            component_kinds.append("invalid")

    if not (2 <= len(targets) <= 4):
        errors.append(f"expected 2..4 target windows, found {len(targets)}")
    if target_components != len(targets):
        errors.append(
            f"recognized {target_components} target components for {len(targets)} target windows"
        )

    fixture_counts = {
        kind: component_kinds.count(kind)
        for kind in ("tailed_target", "line_distractor", "solid_square_distractor")
    }
    if any(count > 1 for count in fixture_counts.values()):
        errors.append(
            "expected at most one fixture of each kind, found "
            + ", ".join(f"{kind}={count}" for kind, count in fixture_counts.items())
        )
    fixture_signature = tuple(fixture_counts.values())
    if fixture_signature not in {(0, 0, 0), (1, 1, 1)}:
        errors.append(
            "curriculum fixtures must be absent or include exactly one tailed "
            "target, one line, and one solid square"
        )

    if errors:
        return None, errors

    profile = "full_curriculum" if fixture_signature == (1, 1, 1) else "isolated_targets"

    return {
        "grid": g,
        "grid_h": h,
        "grid_w": w,
        "grid_size": size_label,
        "block_count": len(targets),
        "targets": targets,
        "components": components,
        "component_kinds": tuple(component_kinds),
        "profile": profile,
        "missing_corners": tuple(target["missing"] for target in targets),
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting every canonical input."""
    _, errors = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    info, errors = _analyze(grid)
    if errors or info is None:
        raise ValueError("cannot observe malformed scene: " + "; ".join(errors))
    return {axis: info[axis] for axis in AXES}


def strict_canonical_like(grid) -> list[str]:
    """Recognize the isolated-target manifold represented by canonical examples."""
    info, errors = _analyze(grid)
    if errors or info is None:
        return errors
    strict_errors: list[str] = []
    if info["profile"] != "isolated_targets":
        strict_errors.append(f"profile {info['profile']} contains a noncanonical curriculum fixture")
    if info["grid_size"] not in _CANONICAL_GRID_SIZES:
        strict_errors.append(f"grid size {info['grid_size']} is outside canonical linked profiles")
    return strict_errors


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Alternate canonical-like and redundant full-curriculum scenes."""
    index = (3 * int(sample_index) + int(seed) % len(SCHEDULE_PROFILES)) % len(
        SCHEDULE_PROFILES
    )
    return SCHEDULE_PROFILES[index]


def _scheduled_missing_corner(seed: int, sample_index: int) -> str:
    offset = (int(seed) // len(_CORNER_NAMES)) % len(_CORNER_NAMES)
    return _CORNER_NAMES[(int(sample_index) + offset) % len(_CORNER_NAMES)]


def _scheduled_missing_corners(
    seed: int, sample_index: int, block_count: int
) -> tuple[str, ...]:
    """Assign distinct cyclic orientations to targets within one input."""
    first = _CORNER_NAMES.index(_scheduled_missing_corner(seed, sample_index))
    return tuple(
        _CORNER_NAMES[(first + target_index) % len(_CORNER_NAMES)]
        for target_index in range(block_count)
    )


def _target_candidates(h: int, w: int, missing: str, *, tailed: bool) -> list[CellSet]:
    missing_offset = _MISSING_OFFSET[missing]
    plain_offsets = tuple(offset for offset in _CORNERS if offset != missing_offset)
    candidates: list[CellSet] = []
    tails: Sequence[Cell | None] = _TAIL_OPTIONS[missing] if tailed else (None,)
    for r0 in range(h - 1):
        for c0 in range(w - 1):
            for tail in tails:
                cells = {(r0 + dr, c0 + dc) for dr, dc in plain_offsets}
                if tail is not None:
                    tr, tc = r0 + tail[0], c0 + tail[1]
                    if not (0 <= tr < h and 0 <= tc < w):
                        continue
                    cells.add((tr, tc))
                candidates.append(frozenset(cells))
    return list(dict.fromkeys(candidates))


def _line_candidates(h: int, w: int) -> list[CellSet]:
    candidates: list[CellSet] = []
    for r in range(h):
        for c in range(w - 2):
            candidates.append(frozenset((r, c + delta) for delta in range(3)))
    for r in range(h - 2):
        for c in range(w):
            candidates.append(frozenset((r + delta, c) for delta in range(3)))
    return candidates


def _solid_square_candidates(h: int, w: int) -> list[CellSet]:
    return [
        frozenset((r + dr, c + dc) for dr, dc in _CORNERS)
        for r in range(h - 1)
        for c in range(w - 1)
    ]


def _separated_from_all(cells: CellSet, chosen: Sequence[CellSet]) -> bool:
    return all(
        max(abs(r - rr), abs(c - cc)) >= 2
        for r, c in cells
        for prior in chosen
        for rr, cc in prior
    )


def _choose_components(
    h: int,
    w: int,
    *,
    block_count: int,
    missings: Sequence[str],
    profile: str,
    rng,
) -> list[CellSet]:
    if len(missings) != block_count:
        raise ValueError(
            f"expected {block_count} target orientations, received {len(missings)}"
        )
    groups: list[tuple[str, list[CellSet]]] = []
    if profile == "full_curriculum":
        groups.append(
            ("tailed_target", _target_candidates(h, w, missings[0], tailed=True))
        )
        groups.extend(
            (
                "isolated_target",
                _target_candidates(h, w, missing, tailed=False),
            )
            for missing in missings[1:]
        )
        groups.append(("line_distractor", _line_candidates(h, w)))
        groups.append(("solid_square_distractor", _solid_square_candidates(h, w)))
    elif profile == "isolated_targets":
        groups.extend(
            (
                "isolated_target",
                _target_candidates(h, w, missing, tailed=False),
            )
            for missing in missings
        )
    else:
        raise ValueError(f"unknown schedule profile {profile!r}")

    for _, candidates in groups:
        rng.shuffle(candidates)
    groups.sort(key=lambda item: len(item[1]))

    chosen: list[CellSet] = []

    def search(group_index: int) -> bool:
        if group_index == len(groups):
            return True
        for cells in groups[group_index][1]:
            if not _separated_from_all(cells, chosen):
                continue
            chosen.append(cells)
            if search(group_index + 1):
                return True
            chosen.pop()
        return False

    if not search(0):
        raise ValueError(
            f"could not place profile={profile} block_count={block_count} in {h}x{w}"
        )
    return list(chosen)


def _draw_grid_size(ctx, difficulty, overrides: dict[str, Any]) -> str:
    if "grid_size" in overrides:
        return ctx.draw_choice("grid_size", _GRID_SIZES)
    if difficulty == "easy":
        options = _GRID_SIZES[:2]
    elif difficulty == "medium":
        options = _GRID_SIZES[1:]
    elif difficulty == "hard":
        options = _GRID_SIZES[2:]
    else:
        options = _GRID_SIZES
    return ctx.draw_choice("grid_size", options)


def _draw_block_count(ctx, difficulty, overrides: dict[str, Any]) -> int:
    if "block_count" in overrides:
        return ctx.draw_int("block_count", 2, 4)
    if difficulty == "easy":
        return ctx.draw_int("block_count", 2, 2)
    if difficulty == "medium":
        return ctx.draw_int("block_count", 2, 3)
    if difficulty == "hard":
        return ctx.draw_int("block_count", 3, 4)
    return ctx.draw_int("block_count", 2, 4)


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
    grid_size = _draw_grid_size(ctx, difficulty, overrides)
    block_count = _draw_block_count(ctx, difficulty, overrides)
    h, w = _parse_grid_size(grid_size)
    missings = _scheduled_missing_corners(seed, sample_index, block_count)
    profile = schedule_profile(seed, sample_index, difficulty)
    components = _choose_components(
        h,
        w,
        block_count=block_count,
        missings=missings,
        profile=profile,
        rng=ctx.draw_rng("layout"),
    )

    grid = full_grid(h, w, 0)
    for component in components:
        for r, c in component:
            grid[r][c] = 8

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {"grid_size": grid_size, "block_count": block_count}
    if observed != expected:
        raise AssertionError(f"axis observation mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Pure task-local solvers used only for semantic adversary audits.
# ---------------------------------------------------------------------------


def _copy_grid(grid: Any) -> Grid:
    return [list(row) for row in _normalize_grid(grid)]


def _fill_targets(grid: Any, *, allowed_missing: set[str] | None = None, limit: int | None = None) -> Grid:
    original = _normalize_grid(grid)
    out = _copy_grid(original)
    filled = 0
    for target in _target_windows(original):
        if allowed_missing is not None and target["missing"] not in allowed_missing:
            continue
        if limit is not None and filled >= limit:
            break
        r, c = target["missing_cell"]
        out[r][c] = 8
        filled += 1
    return out


def _solve_true_local_rule(grid: Any) -> Grid:
    return _fill_targets(grid)


def _fixed_corner_solver(name: str) -> Callable[[Any], Grid]:
    return lambda grid: _fill_targets(grid, allowed_missing={name})


def _solve_first_target_only(grid: Any) -> Grid:
    return _fill_targets(grid, limit=1)


def _solve_broadcast_first_orientation(grid: Any) -> Grid:
    """Canonical-train-fitting rival: reuse the first target's orientation."""
    original = _normalize_grid(grid)
    targets = _target_windows(original)
    if not targets:
        return _copy_grid(original)
    return _fill_targets(original, allowed_missing={targets[0]["missing"]})


def _fill_component_bbox(out: Grid, component: CellSet) -> None:
    r1, c1, r2, c2 = _bbox(tuple(component))
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            out[r][c] = 8


def _solve_size3_components_only(grid: Any) -> Grid:
    original = _normalize_grid(grid)
    out = _copy_grid(original)
    for component in _components(original):
        if len(component) != 3:
            continue
        r1, c1, r2, c2 = _bbox(tuple(component))
        if r2 - r1 == 1 and c2 - c1 == 1:
            _fill_component_bbox(out, component)
    return out


def _solve_fill_component_bboxes(grid: Any) -> Grid:
    original = _normalize_grid(grid)
    out = _copy_grid(original)
    for component in _components(original):
        _fill_component_bbox(out, component)
    return out


def _first_in_bounds_zero(grid: Grid, candidates: Sequence[Cell]) -> Cell | None:
    h, w = len(grid), len(grid[0]) if grid else 0
    for r, c in candidates:
        if 0 <= r < h and 0 <= c < w and grid[r][c] == 0:
            return r, c
    return None


def _solve_complete_every_size3_object(grid: Any) -> Grid:
    """Canonical-fitting rival: turn every three-cell object into four cells."""
    original = _normalize_grid(grid)
    out = _copy_grid(original)
    for component in _components(original):
        if len(component) != 3:
            continue
        r1, c1, r2, c2 = _bbox(tuple(component))
        if r2 - r1 == 1 and c2 - c1 == 1:
            _fill_component_bbox(out, component)
            continue
        if _is_line_component(component):
            if r1 == r2:
                candidates = ((r1 + 1, c1 + 1), (r1 - 1, c1 + 1))
            else:
                candidates = ((r1 + 1, c1 + 1), (r1 + 1, c1 - 1))
            cell = _first_in_bounds_zero(original, candidates)
            if cell is not None:
                out[cell[0]][cell[1]] = 8
    return out


def _solve_complete_l_and_grow_solid(grid: Any) -> Grid:
    """Canonical-fitting rival that wrongly grows already-complete 2x2 objects."""
    original = _normalize_grid(grid)
    out = _solve_true_local_rule(original)
    for component in _components(original):
        if not _is_solid_square_component(component):
            continue
        r1, c1, r2, c2 = _bbox(tuple(component))
        candidates = (
            (r1, c2 + 1),
            (r2, c2 + 1),
            (r2 + 1, c1),
            (r2 + 1, c2),
            (r1, c1 - 1),
            (r2, c1 - 1),
            (r1 - 1, c1),
            (r1 - 1, c2),
        )
        cell = _first_in_bounds_zero(original, candidates)
        if cell is not None:
            out[cell[0]][cell[1]] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Grid]] = {
    "fixed_top_left": _fixed_corner_solver("top_left"),
    "fixed_top_right": _fixed_corner_solver("top_right"),
    "fixed_bottom_left": _fixed_corner_solver("bottom_left"),
    "fixed_bottom_right": _fixed_corner_solver("bottom_right"),
    "first_target_only": _solve_first_target_only,
    "broadcast_first_orientation": _solve_broadcast_first_orientation,
    "size3_components_only": _solve_size3_components_only,
    "fill_component_bboxes": _solve_fill_component_bboxes,
    "complete_every_size3_object": _solve_complete_every_size3_object,
    "complete_l_and_grow_solid": _solve_complete_l_and_grow_solid,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

CANONICAL_SHORTCUTS = {
    "size3_components_only": _solve_size3_components_only,
    "fill_component_bboxes": _solve_fill_component_bboxes,
    "complete_every_size3_object": _solve_complete_every_size3_object,
    "complete_l_and_grow_solid": _solve_complete_l_and_grow_solid,
}


def _has_missing_corner(grid: Any, corner: str) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and corner in info["missing_corners"])


def _has_profile(grid: Any, profile: str) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and info["profile"] == profile)


def _has_component_kind(grid: Any, kind: str) -> bool:
    info, errors = _analyze(grid)
    return bool(
        info is not None
        and not errors
        and kind in info["component_kinds"]
    )


def _has_multiple_targets(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return bool(info is not None and not errors and info["block_count"] >= 2)


def _has_mixed_target_orientations(grid: Any) -> bool:
    info, errors = _analyze(grid)
    return bool(
        info is not None
        and not errors
        and len(set(info["missing_corners"])) >= 2
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "missing_top_left": lambda grid: _has_missing_corner(grid, "top_left"),
    "missing_top_right": lambda grid: _has_missing_corner(grid, "top_right"),
    "missing_bottom_left": lambda grid: _has_missing_corner(grid, "bottom_left"),
    "missing_bottom_right": lambda grid: _has_missing_corner(grid, "bottom_right"),
    "multiple_targets": _has_multiple_targets,
    "mixed_target_orientations": _has_mixed_target_orientations,
    "line_distractor": lambda grid: _has_component_kind(grid, "line_distractor"),
    "solid_square_distractor": lambda grid: _has_component_kind(
        grid, "solid_square_distractor"
    ),
    "attached_tail_target": lambda grid: _has_component_kind(grid, "tailed_target"),
}

WITNESS_RIVALS = {
    "missing_top_left": ["fixed_bottom_right"],
    "missing_top_right": ["fixed_bottom_right"],
    "missing_bottom_left": ["fixed_bottom_right"],
    "missing_bottom_right": ["fixed_top_left"],
    "multiple_targets": ["first_target_only"],
    "mixed_target_orientations": ["broadcast_first_orientation"],
    "line_distractor": ["complete_every_size3_object"],
    "solid_square_distractor": ["complete_l_and_grow_solid"],
    "attached_tail_target": ["size3_components_only", "fill_component_bboxes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where any named rival fits all demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query lacks input/output"]

    surviving: list[str] = []
    for name, solver in sorted(LESSON_COMPETITORS.items()):
        try:
            fits_demos = all(
                solver(demo["input"]) == _normalize_grid(demo["output"])
                for demo in demos
            )
            if not fits_demos:
                continue
            query_answer = solver(query["input"])
            if query_answer != _normalize_grid(query["output"]):
                surviving.append(name)
        except (KeyError, TypeError, ValueError) as exc:
            return [f"competitor {name!r} could not be evaluated: {type(exc).__name__}: {exc}"]
    if surviving:
        return [
            "rival rule(s) fit every demonstration but change the query: "
            + ", ".join(surviving)
        ]
    return []
