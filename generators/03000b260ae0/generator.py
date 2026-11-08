"""Input generator for task 03000b260ae0: shifted-template overlap counts.

The first multi-cell nonzero component containing a maroon cell is the template.
Its *last maroon cell in the canonical BFS component order* is the anchor; every
singleton maroon cell is a placement marker.  A translated template copy is
centered on each marker by aligning the anchor.  The output is a fresh count map:
one covering copy is red (2), two are green (3), and three or more are yellow
(4).  Template body colors, including earlier maroon cells, do not affect labels.

Ordinary samples cycle through a canonical-scale disjoint anchor, a
double-overlap/multi-anchor case, and two complementary triple-overlap cases.
Thus every four-demonstration lesson plus query contains canonical linkage and
at least two witnesses for both multiplicity and anchor-selection rivals.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03000b260ae0"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "e140a6400a02"

SUMMARY = (
    "A connected 4-6 cell template containing one or more 9s and 1-5 singleton "
    "9 markers.  Align the template's last BFS-visited 9 to every marker and "
    "render copy coverage on a blank canvas: 1->2, 2->3, 3+->4.  A four-slot "
    "teaching schedule anchors canonical scale, then supplies repeated overlap "
    "and anchor-selection witnesses plus body-color variation."
)

EXAMPLES_NEEDED = 4
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "double_multi_anchor",
    "triple_multi_anchor",
    "triple_multicolor",
)
_CANONICAL_DIMS = ((11, 13), (14, 16), (12, 13), (13, 13))

INVARIANTS = [
    "background is 0 and the grid is 8..14 by 10..17",
    "exactly one 4-connected multi-cell component contains at least one 9",
    "the last BFS-visited 9 in that component is the anchor",
    "1..5 other 9 cells are isolated singleton components and are markers",
    "advertised overlap is measured from complete in-bounds translated copies",
    "multicolor and multi_anchor are independently observable template textures",
]

AXES = {
    "grid_h": {"type": "int", "default": "schedule/curriculum-weighted 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "schedule/curriculum-weighted 10..17", "valid": "10..17"},
    "n_markers": {"type": "int", "default": "2 canonical; otherwise 2..5 conditioned on overlap", "valid": "1..5"},
    "overlap": {
        "type": "enum",
        "default": "cyclic disjoint|double|triple; low n_markers may reduce overlap",
        "valid": "disjoint|double|triple",
        "doc": "Maximum visible translated-copy multiplicity.",
    },
    "texture": {
        "type": "enum",
        "default": "cyclic monochrome|multicolor|multi_anchor",
        "valid": "monochrome|multicolor|multi_anchor",
        "doc": "One body color, multiple body colors, or multiple template 9s.",
    },
}

# Only low marker counts conflict, and only when both controls are explicit.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (("n_markers", "overlap"),)
DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("multicolor", "multi_anchor")

_BODY_COLORS = (1, 2, 3, 4, 5, 6, 7, 8)
_OVERLAPS = ("disjoint", "double", "triple")
_TEXTURES = ("monochrome", "multicolor", "multi_anchor")
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_INT_DOMAINS = {
    "grid_h": (8, 14),
    "grid_w": (10, 17),
    "n_markers": (1, 5),
}


class OverrideConflict(ValueError):
    """A value-dependent conflict between otherwise valid exact controls."""

    def __init__(self, message, axes):
        super().__init__("incompatible overrides: " + message)
        self.incompatible_axes = tuple(sorted(axes))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the public semantic profile for this sample-index residue."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = {name: value for name, value in overrides.items() if value is not None}
    for name, (lo, hi) in _INT_DOMAINS.items():
        if name in clean:
            value = clean[name]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    for name, choices in (("overlap", _OVERLAPS), ("texture", _TEXTURES)):
        if name in clean:
            value = clean[name]
            if not isinstance(value, str) or value not in choices:
                raise ValueError(f"{name} must be one of {choices}")
    if "n_markers" in clean and "overlap" in clean:
        minimum = {"disjoint": 1, "double": 2, "triple": 3}[clean["overlap"]]
        if clean["n_markers"] < minimum:
            raise OverrideConflict(
                f"{clean['overlap']} overlap needs at least {minimum} markers",
                ("n_markers", "overlap"),
            )
    return clean


def _draw_weighted_int(ctx, name, lo, hi, favored):
    """Keep the full exact domain while reweighting ordinary defaults."""
    choices = list(range(lo, hi + 1))
    if ctx.overrides.get(name) is None:
        choices += [value for value in favored for _ in range(12)]
    return ctx.draw_choice(name, choices)


def _draw_enum(ctx, name, choices, default):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, choices)
    return ctx.draw_choice(name, (default,))


def _grow_template(rng, size):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = _DIRS4[rng.randrange(4)]
        point = (r + dr, c + dc)
        if point not in seen:
            cells.append(point)
            seen.add(point)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _relative_bfs_order(cells):
    allowed = set(cells)
    start = min(allowed)
    seen = {start}
    queue = [start]
    cursor = 0
    while cursor < len(queue):
        r, c = queue[cursor]
        cursor += 1
        for dr, dc in _DIRS4:
            point = (r + dr, c + dc)
            if point in allowed and point not in seen:
                seen.add(point)
                queue.append(point)
    return queue


def _removal_preserves_connectivity(cells, removed):
    allowed = set(cells) - {removed}
    if not allowed:
        return False
    start = min(allowed)
    seen = {start}
    queue = [start]
    for r, c in queue:
        for dr, dc in _DIRS4:
            point = (r + dr, c + dc)
            if point in allowed and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen == allowed


def _template_paint(occ, texture, rng, *, canonical_anchor=False):
    order = _relative_bfs_order(occ)
    if texture == "multi_anchor":
        anchor = order[-1]
        decoy_count = rng.randint(1, min(2, len(order) - 1))
        nines = {anchor, *rng.sample(order[:-1], decoy_count)}
        body_colors = [rng.choice(_BODY_COLORS)]
    else:
        if canonical_anchor:
            safe = [point for point in occ if _removal_preserves_connectivity(occ, point)]
            anchor = rng.choice(safe)
        else:
            anchor = rng.choice(occ)
        nines = {anchor}
        body_colors = (
            rng.sample(_BODY_COLORS, 2)
            if texture == "multicolor"
            else [7] if canonical_anchor else [rng.choice(_BODY_COLORS)]
        )
    paint = {}
    body_index = 0
    for point in occ:
        if point in nines:
            paint[point] = 9
        else:
            paint[point] = body_colors[body_index % len(body_colors)]
            body_index += 1
    return anchor, paint


def _full_footprint(marker, occ, anchor, h, w):
    mr, mc = marker
    ar, ac = anchor
    cells = {(mr + r - ar, mc + c - ac) for r, c in occ}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return None
    return cells


def _not_adjacent(point, others):
    return all(abs(point[0] - r) + abs(point[1] - c) > 1 for r, c in others)


def _add_counts(counts, footprint):
    updated = dict(counts)
    for point in footprint:
        updated[point] = updated.get(point, 0) + 1
    return updated


def _extend_markers(candidates, footprints, chosen, counts, target, needed, rng):
    if needed == 0:
        return list(chosen)
    pool = [point for point in candidates if point not in chosen and _not_adjacent(point, chosen)]
    rng.shuffle(pool)
    # Prefer additions that introduce fewer extra overlaps.  This keeps the
    # target multiplicity exact while still allowing varied copy intersections.
    pool.sort(key=lambda point: sum(counts.get(cell, 0) for cell in footprints[point]))
    for point in pool:
        footprint = footprints[point]
        if any(counts.get(cell, 0) + 1 > target for cell in footprint):
            continue
        result = _extend_markers(
            candidates,
            footprints,
            chosen + [point],
            _add_counts(counts, footprint),
            target,
            needed - 1,
            rng,
        )
        if result is not None:
            return result
    return None


def _choose_markers(rng, candidates, footprints, n_markers, overlap):
    target = {"disjoint": 1, "double": 2, "triple": 3}[overlap]
    if target == 1:
        return _extend_markers(candidates, footprints, [], {}, 1, n_markers, rng)

    coverers = {}
    for marker, footprint in footprints.items():
        for point in footprint:
            coverers.setdefault(point, []).append(marker)
    shared_points = [point for point, hits in coverers.items() if len(hits) >= target]
    rng.shuffle(shared_points)
    for shared in shared_points:
        hits = list(coverers[shared])
        rng.shuffle(hits)
        for stack in combinations(hits, target):
            if any(not _not_adjacent(point, stack[:index])
                   for index, point in enumerate(stack)):
                continue
            counts = {}
            for point in stack:
                counts = _add_counts(counts, footprints[point])
            if max(counts.values(), default=0) != target:
                continue
            result = _extend_markers(
                candidates,
                footprints,
                list(stack),
                counts,
                target,
                n_markers - target,
                rng,
            )
            if result is not None:
                return result
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    clean = _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_overlap, scheduled_texture = {
        "canonical_anchor": ("disjoint", "monochrome"),
        "double_multi_anchor": ("double", "multi_anchor"),
        "triple_multi_anchor": ("triple", "multi_anchor"),
        "triple_multicolor": ("triple", "multicolor"),
    }[profile]

    favored_h = {
        "easy": (8, 9, 10),
        "medium": (10, 11, 12),
        "hard": (12, 13, 14),
        None: (10, 11, 12),
    }[difficulty]
    favored_w = {
        "easy": (10, 11, 12, 13),
        "medium": (12, 13, 14, 15),
        "hard": (14, 15, 16, 17),
        None: (12, 13, 14, 15),
    }[difficulty]
    if profile == "canonical_anchor":
        canonical_h, canonical_w = _CANONICAL_DIMS[(seed + sample_index) % len(_CANONICAL_DIMS)]
        h_options = range(8, 15) if "grid_h" in clean else (canonical_h,)
        w_options = range(10, 18) if "grid_w" in clean else (canonical_w,)
        h = ctx.draw_choice("grid_h", h_options)
        w = ctx.draw_choice("grid_w", w_options)
    else:
        h = _draw_weighted_int(ctx, "grid_h", 8, 14, favored_h)
        w = _draw_weighted_int(ctx, "grid_w", 10, 17, favored_w)

    explicit_n = clean.get("n_markers")
    overlap_default = scheduled_overlap
    if explicit_n is not None and "overlap" not in clean:
        if explicit_n == 1:
            overlap_default = "disjoint"
        elif explicit_n == 2 and scheduled_overlap == "triple":
            overlap_default = "double"
    overlap = _draw_enum(ctx, "overlap", _OVERLAPS, overlap_default)
    texture = _draw_enum(ctx, "texture", _TEXTURES, scheduled_texture)

    minimum_markers = {"disjoint": 1, "double": 2, "triple": 3}[overlap]
    if explicit_n is not None:
        n_markers = ctx.draw_choice("n_markers", range(1, 6))
    elif profile == "canonical_anchor" and "overlap" not in clean:
        n_markers = ctx.draw_choice("n_markers", (2,))
    else:
        favored_n = {
            "easy": (minimum_markers, min(5, minimum_markers + 1)),
            "medium": (max(minimum_markers, 3), 4),
            "hard": (4, 5),
            None: (max(minimum_markers, 3), 4),
        }[difficulty]
        choices = list(range(minimum_markers, 6))
        choices += [value for value in favored_n if value >= minimum_markers for _ in range(12)]
        n_markers = ctx.draw_choice("n_markers", choices)

    rng = ctx.draw_rng("layout")
    if overlap == "triple":
        size_choices = (5, 6)
    elif difficulty == "easy":
        size_choices = (4, 4, 5)
    elif difficulty == "hard":
        size_choices = (5, 6, 6)
    else:
        size_choices = (4, 5, 6)

    # Geometry is selected by finite constructive search.  Every candidate copy
    # is fully in bounds, so a requested overlap is visible rather than satisfied
    # only beyond the canvas.
    for _attempt in range(600):
        occ = _grow_template(rng, rng.choice(size_choices))
        anchor, paint = _template_paint(
            occ,
            texture,
            rng,
            canonical_anchor=(
                profile == "canonical_anchor"
                and overlap == "disjoint"
                and texture == "monochrome"
            ),
        )
        th = max(r for r, _ in occ) + 1
        tw = max(c for _, c in occ) + 1
        placements = [(top, left) for top in range(h - th + 1) for left in range(w - tw + 1)]
        rng.shuffle(placements)
        if not placements:
            continue
        top, left = placements[0]
        template_cells = {(top + r, left + c) for r, c in occ}

        candidates = []
        footprints = {}
        for mr in range(h):
            for mc in range(w):
                marker = (mr, mc)
                if marker in template_cells or not _not_adjacent(marker, template_cells):
                    continue
                footprint = _full_footprint(marker, occ, anchor, h, w)
                if footprint is None:
                    continue
                candidates.append(marker)
                footprints[marker] = footprint
        rng.shuffle(candidates)
        markers = _choose_markers(rng, candidates, footprints, n_markers, overlap)
        if markers is None:
            continue

        grid = full_grid(h, w, 0)
        for (dr, dc), color in paint.items():
            grid[top + dr][left + dc] = color
        for mr, mc in markers:
            grid[mr][mc] = 9
        if self_check(grid):
            continue
        if observe_overrides(grid) != {
            "grid_h": h,
            "grid_w": w,
            "n_markers": n_markers,
            "overlap": overlap,
            "texture": texture,
        }:
            continue
        return grid
    raise ValueError("could not realize requested shifted-copy count-map board")


def _components_bfs(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            order = []
            cursor = 0
            while cursor < len(queue):
                r, c = queue[cursor]
                cursor += 1
                order.append((r, c))
                for dr, dc in _DIRS4:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(order)
    return components


def _analyze(grid, *, first_anchor=False):
    components = _components_bfs(grid)
    templates = [
        component for component in components
        if len(component) > 1 and any(grid[r][c] == 9 for r, c in component)
    ]
    if len(templates) != 1:
        raise ValueError(f"expected one multi-cell template containing 9, found {len(templates)}")
    template = templates[0]
    markers = [
        component[0] for component in components
        if len(component) == 1 and grid[component[0][0]][component[0][1]] == 9
    ]
    anchors = [(r, c) for r, c in template if grid[r][c] == 9]
    anchor = anchors[0] if first_anchor else anchors[-1]
    return template, markers, anchor, components


def _coverage_counts(grid, *, first_anchor=False):
    template, markers, anchor, _ = _analyze(grid, first_anchor=first_anchor)
    h, w = len(grid), len(grid[0])
    counts = [[0] * w for _ in range(h)]
    ar, ac = anchor
    for mr, mc in markers:
        for tr, tc in template:
            r, c = mr + tr - ar, mc + tc - ac
            if 0 <= r < h and 0 <= c < w:
                counts[r][c] += 1
    return counts


def _render_counts(counts, mode="full"):
    output = []
    for row in counts:
        rendered = []
        for count in row:
            if count == 0:
                rendered.append(0)
            elif mode == "binary":
                rendered.append(2)
            elif count == 1:
                rendered.append(2)
            elif mode == "cap_at_two" or count == 2:
                rendered.append(3)
            else:
                rendered.append(4)
        output.append(rendered)
    return output


def _rule_count_map(grid):
    """Independent Python mirror used only by semantic rivals and tests."""
    return _render_counts(_coverage_counts(grid))


def _binary_union(grid):
    """RIVAL: ignores multiplicity and paints every covered cell red."""
    return _render_counts(_coverage_counts(grid), mode="binary")


def _cap_at_two(grid):
    """RIVAL: distinguishes overlap, but maps every count >=2 to green."""
    return _render_counts(_coverage_counts(grid), mode="cap_at_two")


def _first_template_nine(grid):
    """RIVAL: uses the first rather than last BFS-visited template 9 as anchor."""
    return _render_counts(_coverage_counts(grid, first_anchor=True))


def _max_overlap(grid):
    return max((value for row in _coverage_counts(grid) for value in row), default=0)


def _template_nine_count(grid):
    template, _, _, _ = _analyze(grid)
    return sum(grid[r][c] == 9 for r, c in template)


def observe_overrides(grid):
    """Recover every exact advertised control from returned pixels."""
    template, markers, _, _ = _analyze(grid)
    overlap_count = _max_overlap(grid)
    overlap = "triple" if overlap_count >= 3 else "double" if overlap_count == 2 else "disjoint"
    template_nines = sum(grid[r][c] == 9 for r, c in template)
    body_colors = {grid[r][c] for r, c in template if grid[r][c] != 9}
    if template_nines > 1:
        texture = "multi_anchor"
    elif len(body_colors) > 1:
        texture = "multicolor"
    else:
        texture = "monochrome"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": len(markers),
        "overlap": overlap,
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    errors = []
    if not 8 <= len(grid) <= 14 or not 10 <= width <= 17:
        errors.append("grid dimensions must be 8..14 rows by 10..17 columns")
    components = _components_bfs(grid)
    templates = [
        component for component in components
        if len(component) > 1 and any(grid[r][c] == 9 for r, c in component)
    ]
    markers = [
        component for component in components
        if len(component) == 1 and grid[component[0][0]][component[0][1]] == 9
    ]
    if len(templates) != 1:
        errors.append(f"expected one multi-cell template containing 9, found {len(templates)}")
    elif not 4 <= len(templates[0]) <= 6:
        errors.append(f"template size {len(templates[0])} outside 4..6")
    if not 1 <= len(markers) <= 5:
        errors.append(f"expected 1-5 singleton 9 markers, found {len(markers)}")
    accepted = set(map(id, templates + markers))
    for component in components:
        if id(component) not in accepted:
            errors.append(f"unexpected non-template/non-marker component of size {len(component)}")
            break
    return errors


def strict_canonical_like(grid):
    """The lawful task manifold; every canonical input must pass."""
    return self_check(grid)


def _has_double_overlap(grid):
    return _max_overlap(grid) == 2


def _has_triple_overlap(grid):
    return _max_overlap(grid) >= 3


def _has_multiple_template_nines(grid):
    return _template_nine_count(grid) > 1


SEMANTIC_WITNESSES = {
    "double_overlap": _has_double_overlap,
    "triple_overlap": _has_triple_overlap,
    "multiple_template_nines": _has_multiple_template_nines,
}
SEMANTIC_RIVALS = {
    "binary_union": _binary_union,
    "cap_at_two": _cap_at_two,
    "first_template_nine": _first_template_nine,
}
WITNESS_RIVALS = {
    "double_overlap": ["binary_union"],
    "triple_overlap": ["binary_union", "cap_at_two"],
    "multiple_template_nines": ["first_template_nine"],
}
CANONICAL_SHORTCUTS = {
    "binary_union": _binary_union,
    "cap_at_two": _cap_at_two,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a universal induction proof."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
