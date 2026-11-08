"""Generator for ``dc657616ec21`` — thickness-congruence matrix.

Full-height color-9 columns divide the input into horizontal panels.  Each
panel contains one connected monochrome object.  Repeatedly peel the object's
cardinal boundary; its maximum peel layer is the panel's *thickness*.  The
answer is an ``n x n`` relation matrix with color 8 exactly where two panels
have equal thickness.

The generator deliberately uses non-rectangular objects and gives equal-depth
panels different silhouettes.  This prevents the rectangle-width and raw-area
shortcuts that the older generator taught instead of onion depth.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dc657616ec21"
TASK_ID = "dc657616ec21"
VERSION = "3.1.0"  # semantic rival contract and per-example witness scheduling
RULE_HASH = "51d1d5e43d4d"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Color-9 columns split the grid into panels.  Each panel contains one "
    "connected monochrome object whose onion-peel depth is its thickness.  "
    "The output is the square pairwise equality matrix: 8 for equal depths, "
    "0 otherwise.  Equal-depth panels intentionally vary in silhouette, area, "
    "color, and position."
)

INVARIANTS = [
    "every separator is one full-height color-9 column and color 9 appears nowhere else",
    "each panel contains one connected monochrome object in colors 1-7",
    "normal lessons contain at least two depth classes",
    "normal lessons with at least three panels contain both equal and unequal off-diagonal pairs",
    "normal lessons include non-rectangular shapes so thickness cannot be reduced to rectangle width",
    "every normal input makes bbox-min-side classification disagree with onion-depth equality",
]

DEGENERATE_TEXTURES = ("single_panel", "all_same_thickness", "all_distinct")
HELPFUL_TEXTURES = ("warm", "cool", "varied")
# These are lawful edge cases of the task, but they are excluded from ordinary
# lessons because each hides one branch of the equality relation.
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..12 with canonical 7/9-row prior",
        "valid": "7..12",
    },
    "n_panels": {
        "type": "int",
        "default": "3..4 easy, 4..5 medium, 5..6 hard",
        "valid": "2..6",
    },
    "texture": {
        "type": "str",
        "default": "rng warm|cool|varied",
        "valid": "warm|cool|varied|single_panel|all_same_thickness|all_distinct",
    },
}

_PALETTES = {
    "warm": (1, 2, 4, 7),
    "cool": (1, 3, 5, 6),
    "varied": (1, 2, 3, 4, 5, 6, 7),
}

# The canonical task has two exact input profiles.  A regular prior at those
# dimensions/palette anchors the generator to official morphology without
# copying any fixed object placement.
_CANONICAL_PROFILES = (
    {"grid_h": 7, "panel_widths": (7, 7, 7), "depths": (2, 3, 2)},
    {"grid_h": 9, "panel_widths": (9, 9, 9), "depths": (2, 2, 1)},
    {"grid_h": 9, "panel_widths": (9, 9, 9), "depths": (3, 2, 2)},
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _draw_int_axis(
    ctx,
    name: str,
    global_lo: int,
    global_hi: int,
    default_lo: int,
    default_hi: int,
    profile_value: int | None = None,
) -> int:
    """Consume full-domain explicit overrides; otherwise use the local prior."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, global_lo, global_hi)
    if profile_value is not None:
        return ctx.draw_int(name, profile_value, profile_value)
    return ctx.draw_int(name, default_lo, default_hi)


def _draw_texture(ctx) -> str:
    all_textures = HELPFUL_TEXTURES + DEGENERATE_TEXTURES
    if "texture" in ctx.overrides and ctx.overrides["texture"] is not None:
        return str(ctx.draw_choice("texture", all_textures))
    return str(ctx.draw_choice("texture", HELPFUL_TEXTURES))


def _neighbors(cell: tuple[int, int]) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _CARDINAL:
        yield r + dr, c + dc


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = set(cells)
    if not cells:
        return frozenset()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _dilate_l1(
    skeleton: Iterable[tuple[int, int]], radius: int
) -> frozenset[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for r, c in skeleton:
        for dr in range(-radius, radius + 1):
            rem = radius - abs(dr)
            for dc in range(-rem, rem + 1):
                cells.add((r + dr, c + dc))
    return _normalize(cells)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _connected_components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        queue = deque([start])
        remaining.remove(start)
        comp = {start}
        while queue:
            cur = queue.popleft()
            for nxt in _neighbors(cur):
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        components.append(comp)
    return components


def _onion_depth(cells: Iterable[tuple[int, int]]) -> int:
    """Return cardinal boundary-peel depth, matching the canonical Racket rule."""
    remaining = set(cells)
    depth = 0
    while remaining:
        boundary = {
            cell
            for cell in remaining
            if any(neighbor not in remaining for neighbor in _neighbors(cell))
        }
        if not boundary:  # finite cell sets always have a boundary; defensive only
            raise ValueError("finite shape has no peelable boundary")
        remaining.difference_update(boundary)
        depth += 1
    return depth


def _is_rectangle(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return len(cells) == (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)


def _shape_library(depth: int) -> list[tuple[str, frozenset[tuple[int, int]]]]:
    """Candidate silhouettes whose exact depth is checked, not assumed."""
    radius = depth - 1
    skeletons: list[tuple[str, set[tuple[int, int]]]] = [
        ("diamond", {(0, 0)}),
        ("h_capsule_2", {(0, 0), (0, 1)}),
        ("h_capsule_3", {(0, 0), (0, 1), (0, 2)}),
        ("h_capsule_4", {(0, 0), (0, 1), (0, 2), (0, 3)}),
        ("h_capsule_5", {(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)}),
        ("v_capsule_2", {(0, 0), (1, 0)}),
        ("v_capsule_3", {(0, 0), (1, 0), (2, 0)}),
        ("v_capsule_4", {(0, 0), (1, 0), (2, 0), (3, 0)}),
        ("v_capsule_5", {(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}),
        ("elbow", {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}),
        ("zigzag", {(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}),
        ("tee", {(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)}),
    ]
    candidates: list[tuple[str, frozenset[tuple[int, int]]]] = []
    seen: set[frozenset[tuple[int, int]]] = set()
    for name, skeleton in skeletons:
        cells = _dilate_l1(skeleton, radius)
        if cells not in seen and _onion_depth(cells) == depth:
            seen.add(cells)
            candidates.append((name, cells))

    # Rectangles remain a minority branch; the non-rectangular witnesses above
    # are what separate onion depth from minimum-side shortcuts.
    for extra in (0, 1, 2, 3, 4):
        hh = 2 * depth - 1
        ww = hh + extra
        cells = frozenset((r, c) for r in range(hh) for c in range(ww))
        if cells not in seen and _onion_depth(cells) == depth:
            seen.add(cells)
            candidates.append((f"rectangle_{extra}", cells))
    return candidates


_SHAPES_BY_DEPTH = {depth: _shape_library(depth) for depth in (1, 2, 3)}


def _bbox_shortcut_class(cells: Iterable[tuple[int, int]]) -> int:
    """Class used by the strongest canonical-fitting bounding-box shortcut."""
    height, width = _shape_dims(_normalize(cells))
    return (min(height, width) + 1) // 2


def _choose_shape(
    depth: int,
    max_h: int,
    max_w: int,
    rng,
    *,
    prefer_nonrect: bool = False,
    prefer_large: bool = False,
    avoid_name: str | None = None,
    bbox_role: str | None = None,
) -> tuple[str, frozenset[tuple[int, int]]]:
    if bbox_role not in (None, "exact", "mismatch"):
        raise ValueError(f"unknown bbox teaching role {bbox_role!r}")
    choices = [
        item
        for item in _SHAPES_BY_DEPTH[depth]
        if _shape_dims(item[1])[0] <= max_h
        and _shape_dims(item[1])[1] <= max_w
        and item[0] != avoid_name
        and (
            bbox_role is None
            or (bbox_role == "exact" and _bbox_shortcut_class(item[1]) == depth)
            or (bbox_role == "mismatch" and _bbox_shortcut_class(item[1]) != depth)
        )
    ]
    if prefer_nonrect:
        nonrect = [item for item in choices if not _is_rectangle(item[1])]
        if nonrect:
            choices = nonrect
    if not choices:
        raise ValueError(
            f"no depth-{depth} shape fits panel interior {max_h}x{max_w}"
        )
    if prefer_large:
        max_area = max(len(cells) for _, cells in choices)
        choices = [item for item in choices if len(item[1]) == max_area]
    return rng.choice(choices)


def _ordinary_depths(n_panels: int, difficulty: str | None, rng) -> list[int]:
    """Produce both equality outcomes and broad depth support on normal draws."""
    if n_panels == 2:
        # Adjacent classes let the lower-depth panel use a broad, thin shape
        # whose bounding-box shortcut collides with the higher true class.
        pairs = [(1, 2), (2, 3)]
        depths = list(rng.choice(pairs))
        rng.shuffle(depths)
        return depths

    # The first two guarantee an off-diagonal equality; the third guarantees
    # an inequality.  Hard lessons also show the deepest class every time.
    allowed = (1, 2) if difficulty == "easy" else (1, 2, 3)
    repeated = rng.choice(allowed)
    different = rng.choice([d for d in allowed if d != repeated])
    depths = [repeated, repeated, different]
    if difficulty == "hard" and 3 not in depths and len(depths) < n_panels:
        depths.append(3)
    while len(depths) < n_panels:
        depths.append(rng.choice(allowed))
    rng.shuffle(depths)
    return depths


def _fit_panel_widths(depths: list[int], rng) -> list[int]:
    """Fit exact-depth objects plus useful blank space within ARC's 30 columns."""
    n = len(depths)
    max_content_total = 30 - (n - 1) - n  # reserve at least one blank col/panel
    while sum(2 * depth - 1 for depth in depths) > max_content_total:
        # Reduce a high class while preserving at least two classes.  This path
        # is rare but keeps every declared n_panels override feasible.
        changed = False
        for idx in sorted(range(n), key=lambda i: depths[i], reverse=True):
            if depths[idx] <= 1:
                continue
            trial = list(depths)
            trial[idx] -= 1
            if len(set(trial)) >= 2:
                depths[:] = trial
                changed = True
                break
        if not changed:
            raise ValueError("could not fit two thickness classes within 30 columns")

    widths = [2 * depth for depth in depths]  # minimum shape width + one blank col
    remaining = 30 - ((n - 1) + sum(widths))
    target_extra = rng.randint(0, remaining)
    for _ in range(target_extra):
        widths[rng.randrange(n)] += 1
    return widths


def _bbox_teaching_roles(depths: list[int]) -> tuple[int, int]:
    """Return (mismatch, exact-control) indexes that defeat the rival."""
    for depth in depths:
        matches = [index for index, value in enumerate(depths) if value == depth]
        if len(matches) >= 2:
            return matches[0], matches[1]
    for lower_index, lower in enumerate(depths):
        for upper_index, upper in enumerate(depths):
            if upper == lower + 1:
                return lower_index, upper_index
    raise ValueError(
        "normal lessons need a repeated class or adjacent classes to refute "
        "the bbox-min-side shortcut"
    )


def _reserve_bbox_witness_width(depths: list[int], widths: list[int]) -> None:
    """Give the mismatch panel room for a (2d+1)x(2d+1) thin silhouette."""
    witness_index, _ = _bbox_teaching_roles(depths)
    required = 2 * depths[witness_index] + 1
    while widths[witness_index] < required:
        total_width = sum(widths) + len(widths) - 1
        if total_width < 30:
            widths[witness_index] += 1
            continue
        donors = [
            index
            for index, (depth, width) in enumerate(zip(depths, widths))
            if index != witness_index and width > 2 * depth - 1
        ]
        if not donors:
            raise ValueError("could not reserve width for bbox shortcut witness")
        donor = max(
            donors,
            key=lambda index: widths[index] - (2 * depths[index] - 1),
        )
        widths[donor] -= 1
        widths[witness_index] += 1


def _panel_colors(texture: str, n_panels: int, rng) -> list[int]:
    palette = list(_PALETTES.get(texture, _PALETTES["varied"]))
    rng.shuffle(palette)
    colors = [palette[i % len(palette)] for i in range(n_panels)]
    # Do not let color become a thickness label: independently permute colors.
    rng.shuffle(colors)
    return colors


def _build_grid(
    h: int,
    depths: list[int],
    panel_widths: list[int],
    rng,
    *,
    texture: str,
    canonical_palette: bool = False,
    canonical_profile: bool = False,
    require_bbox_witness: bool = False,
) -> tuple[list[list[int]], list[dict[str, Any]]]:
    n = len(depths)
    width = sum(panel_widths) + n - 1
    if width > 30:
        raise ValueError(f"grid width {width} exceeds ARC limit")
    grid = full_grid(h, width, 0)
    colors = [1] * n if canonical_palette else _panel_colors(texture, n, rng)

    # Equal-depth panels are assigned distinct shape names whenever possible.
    prior_name_by_depth: dict[int, str] = {}
    nonrect_assigned = False
    specs: list[dict[str, Any]] = []
    panel_left = 0
    largest_depth_index = depths.index(max(depths)) if canonical_profile else -1
    if require_bbox_witness:
        mismatch_index, control_index = _bbox_teaching_roles(depths)
    else:
        mismatch_index, control_index = -1, -1
    for index, (depth, panel_w, color) in enumerate(zip(depths, panel_widths, colors)):
        prefer_nonrect = (not nonrect_assigned) or depth in prior_name_by_depth
        bbox_role = (
            "mismatch"
            if index == mismatch_index
            else "exact"
            if index == control_index
            else None
        )
        name, mask = _choose_shape(
            depth,
            h,
            panel_w,
            rng,
            prefer_nonrect=(prefer_nonrect and index != largest_depth_index),
            prefer_large=(index == largest_depth_index),
            avoid_name=prior_name_by_depth.get(depth),
            bbox_role=bbox_role,
        )
        prior_name_by_depth.setdefault(depth, name)
        nonrect_assigned = nonrect_assigned or not _is_rectangle(mask)
        shape_h, shape_w = _shape_dims(mask)
        row_room = h - shape_h
        col_room = panel_w - shape_w
        # Prefer internal margins when they exist, while allowing the full valid
        # boundary range so edge placement is also exercised.
        row0 = rng.randint(0, row_room)
        col0 = panel_left + rng.randint(0, col_room)
        for rr, cc in mask:
            grid[row0 + rr][col0 + cc] = color
        specs.append(
            {
                "panel": index,
                "depth": depth,
                "shape": name,
                "area": len(mask),
                "bbox": [shape_h, shape_w],
                "color": color,
            }
        )
        panel_left += panel_w
        if index < n - 1:
            for row in range(h):
                grid[row][panel_left] = 9
            panel_left += 1
    return grid, specs


def _split_panels(grid: list[list[int]]) -> tuple[list[tuple[int, int]], list[str]]:
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    errors: list[str] = []
    if any(b == a + 1 for a, b in zip(dividers, dividers[1:])):
        errors.append("divider columns must be single-width, not adjacent")
    if any(grid[r][c] == 9 and c not in dividers for r in range(h) for c in range(w)):
        errors.append("color 9 appears outside a full-height divider column")
    cuts = [-1] + dividers + [w]
    panels = [(a + 1, b) for a, b in zip(cuts, cuts[1:]) if b > a + 1]
    if len(panels) != len(dividers) + 1:
        errors.append("a divider creates an empty panel")
    return panels, errors


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return facts, ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    h = len(grid)
    facts.update(grid_h=h, grid_w=width)
    if not (1 <= h <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {h}x{width} exceed ARC bounds")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(f"invalid ARC color {value!r} at ({r},{c})")
            elif value == 8:
                errors.append(f"answer color 8 must not appear in the input at ({r},{c})")

    panels, panel_errors = _split_panels(grid)
    errors.extend(panel_errors)
    facts["n_panels"] = len(panels)
    if not (1 <= len(panels) <= 6):
        errors.append(f"expected 1..6 panels, found {len(panels)}")

    depths: list[int] = []
    panel_facts: list[dict[str, Any]] = []
    for index, (left, right) in enumerate(panels):
        cells = {
            (r, c - left)
            for r in range(h)
            for c in range(left, right)
            if grid[r][c] not in (0, 9)
        }
        colors = {
            grid[r][c]
            for r in range(h)
            for c in range(left, right)
            if grid[r][c] not in (0, 9)
        }
        if not cells:
            errors.append(f"panel {index} contains no object")
            continue
        if len(colors) != 1:
            errors.append(f"panel {index} must be monochrome, found {sorted(colors)}")
        if colors and not colors <= set(range(1, 8)):
            errors.append(f"panel {index} uses unsupported input color(s) {sorted(colors)}")
        components = _connected_components(set(cells))
        if len(components) != 1:
            errors.append(f"panel {index} has {len(components)} disconnected objects")
        depth = _onion_depth(cells)
        depths.append(depth)
        panel_facts.append(
            {
                "panel": index,
                "depth": depth,
                "area": len(cells),
                "bbox": list(_shape_dims(_normalize(cells))),
                "bbox_shortcut_class": _bbox_shortcut_class(cells),
                "rectangle": _is_rectangle(cells),
                "color": next(iter(colors)) if len(colors) == 1 else None,
            }
        )
    facts["depths"] = depths
    facts["panels"] = panel_facts
    return facts, errors


def _normal_lesson_errors(facts: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    n = int(facts.get("n_panels", 0))
    depths = list(facts.get("depths", []))
    panels = list(facts.get("panels", []))
    if not (2 <= n <= 6):
        errors.append(f"normal lessons require 2..6 panels, found {n}")
    if len(set(depths)) < 2:
        errors.append("normal lessons require at least two thickness classes")
    if n >= 3 and not any(depths.count(depth) >= 2 for depth in set(depths)):
        errors.append("normal lessons require an equal-depth off-diagonal pair")
    if n >= 3 and len(set(depths)) < 2:
        errors.append("normal lessons require an unequal-depth off-diagonal pair")
    if panels and all(panel.get("rectangle") for panel in panels):
        errors.append("normal lessons require at least one non-rectangular object")
    bbox_classes = [panel.get("bbox_shortcut_class") for panel in panels]
    if (
        len(bbox_classes) == len(depths)
        and _equality_matrix(bbox_classes) == _equality_matrix(depths)
    ):
        errors.append("normal lessons must refute the bbox-min-side shortcut")
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed task inputs while admitting a narrow lawful 1-panel edge."""
    del difficulty, meta
    facts, errors = _analyze(grid)
    if facts.get("n_panels", 0) == 1 and facts.get("panels"):
        panel = facts["panels"][0]
        # A one-panel case is useful only as an explicit 1x1-output edge case.
        # Keep that grammar narrow so generic singleton/line/full-canvas probes
        # do not pass merely because the oracle can technically execute them.
        if panel.get("depth") != 2 or panel.get("rectangle"):
            errors.append("single-panel edge cases require one non-rectangular depth-2 object")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Executable semantic envelope used by the generator semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact semantic count from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {"n_panels": int(facts["n_panels"])}


def _equality_matrix(classes: Iterable[int]) -> list[list[int]]:
    values = list(classes)
    return [[8 if left == right else 0 for right in values] for left in values]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for focused tests; Racket remains output authority."""
    source = deepcopy(grid)
    facts, errors = _analyze(source)
    if errors:
        raise ValueError("invalid task input: " + "; ".join(errors))
    return _equality_matrix(facts["depths"])


def _bbox_min_side_rival(grid: list[list[int]]) -> list[list[int]] | None:
    """Canonical-fitting rival: infer depth only from the shorter bbox side."""
    source = deepcopy(grid)
    facts, errors = _analyze(source)
    if errors:
        return None
    classes = [panel["bbox_shortcut_class"] for panel in facts["panels"]]
    return _equality_matrix(classes)


def _bbox_min_side_disagreement(grid: list[list[int]]) -> bool:
    rival = _bbox_min_side_rival(grid)
    try:
        return rival is not None and rival != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "bbox_min_side_disagreement": _bbox_min_side_disagreement,
}
SEMANTIC_RIVALS = {
    "bbox_min_side": _bbox_min_side_rival,
}
WITNESS_RIVALS = {
    "bbox_min_side_disagreement": ("bbox_min_side",),
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose labels are wrong or whose canonical rival survives."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        count = len(demos) if isinstance(demos, list) else 0
        return [f"need at least {EXAMPLES_NEEDED} demonstrations, got {count}"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index} has invalid input: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match onion-depth equality")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input")
        return reasons
    try:
        query_answer = rule_mirror(query["input"])
    except (TypeError, ValueError) as exc:
        reasons.append(f"query has invalid input: {exc}")
        return reasons
    if query.get("output") is not None and query["output"] != query_answer:
        reasons.append("query output does not match onion-depth equality")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        )
        if survives and rival(query["input"]) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = _draw_texture(ctx)
    rng = ctx.draw_rng("layout")

    # Explicit axes always win.  The canonical profile is an ordinary-draw
    # prior only, so it never clamps or masks a caller request.
    profile = None
    if not overrides and int(sample_index) % 3 == 0:
        profile_index = (int(sample_index) // 3) % len(_CANONICAL_PROFILES)
        profile = _CANONICAL_PROFILES[profile_index]

    if difficulty == "easy":
        h_range, n_range = (7, 8), (3, 4)
    elif difficulty == "medium":
        h_range, n_range = (8, 10), (4, 5)
    elif difficulty == "hard":
        h_range, n_range = (9, 12), (5, 6)
    else:
        h_range, n_range = (7, 12), (3, 6)

    profile_h = None if profile is None else int(profile["grid_h"])
    h = _draw_int_axis(ctx, "grid_h", 7, 12, *h_range, profile_h)

    if texture == "single_panel":
        if "n_panels" in overrides and int(overrides["n_panels"]) != 1:
            raise ValueError("texture='single_panel' is incompatible with n_panels=2..6")
        n_panels = 1
        depths = [2]
        panel_widths = [max(5, min(9, h))]
    elif texture == "all_distinct":
        if "n_panels" in overrides and int(overrides["n_panels"]) != 3:
            raise ValueError("texture='all_distinct' requires n_panels=3")
        n_panels = 3
        depths = [1, 2, 3]
        panel_widths = _fit_panel_widths(depths, rng)
    elif texture == "all_same_thickness":
        n_panels = _draw_int_axis(ctx, "n_panels", 2, 6, *n_range)
        depth = rng.choice((1, 2, 3))
        depths = [depth] * n_panels
        # Degenerate all-depth-3 with six panels cannot reserve blank space;
        # lower the lawful edge case to the deepest class that fits.
        while sum(2 * d for d in depths) + n_panels - 1 > 30:
            depth -= 1
            depths = [depth] * n_panels
        panel_widths = _fit_panel_widths_for_degenerate(depths, rng)
    elif profile is not None:
        n_panels = _draw_int_axis(ctx, "n_panels", 2, 6, *n_range, 3)
        depths = list(profile["depths"])
        panel_widths = list(profile["panel_widths"])
    else:
        n_panels = _draw_int_axis(ctx, "n_panels", 2, 6, *n_range)
        depths = _ordinary_depths(n_panels, difficulty, rng)
        panel_widths = _fit_panel_widths(depths, rng)

    require_bbox_witness = texture not in DEGENERATE_TEXTURES
    if require_bbox_witness:
        _reserve_bbox_witness_width(depths, panel_widths)

    canonical_palette = profile is not None and texture not in DEGENERATE_TEXTURES
    grid, _specs = _build_grid(
        h,
        depths,
        panel_widths,
        rng,
        texture=texture,
        canonical_palette=canonical_palette,
        canonical_profile=(profile is not None),
        require_bbox_witness=require_bbox_witness,
    )
    facts, errors = _analyze(grid)
    if texture not in DEGENERATE_TEXTURES:
        errors.extend(_normal_lesson_errors(facts))
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid


def _fit_panel_widths_for_degenerate(depths: list[int], rng) -> list[int]:
    """Width allocator for lawful all-same cases, where two classes are absent."""
    n = len(depths)
    widths = [2 * depth for depth in depths]
    while sum(widths) + n - 1 > 30:
        widest = max(range(n), key=widths.__getitem__)
        widths[widest] -= 1
    remaining = 30 - (sum(widths) + n - 1)
    for _ in range(rng.randint(0, remaining)):
        widths[rng.randrange(n)] += 1
    return widths
