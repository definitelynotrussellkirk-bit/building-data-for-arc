"""Dual-anchor profile matching with constructive, independently varied shapes.

Blue supplies ordered row counts; red supplies ordered column counts. The
unchanged Racket rule selects and crops the first jointly matching candidate.
Generated inputs have one such candidate. This module never supplies labels.
Odd indices select the center of an L in candidate-profile space; even indices
select a leaf by changing the anchor profiles. Three demos plus one query
contain two of each phase, so every query rotation retains both witness kinds.
See notes.md for the bounded domain and deliberately omitted anchor copies.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_generator_objects

GENERATOR_ID = "0eb4eaa46003"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bb6e25e7de93"
SUMMARY = (
    "Independently shaped blue-row and red-column anchors select one connected "
    "candidate. Same-area, same-bbox near matches teach both ordered profiles; "
    "alternate anchor roles defeat candidate-only incidence. Color and layout vary."
)
INVARIANTS = [
    "zero background; one 4-connected color-1 anchor and one color-2 anchor",
    "exactly one candidate matches blue's ordered row counts and red's ordered column counts",
    "odd draws include both one-profile decoys; even draws select a peripheral profile instead",
    "the two main distractors share the target's area and bbox; anchors are not target copies",
    "all shapes are connected and separated by background; no partial-layout fallback",
    "Racket crops the selected component and recolors occupied cells to fixed color 8",
]
AXES = {
    "grid_h": {"type": "int", "default": "10..24; favors 11,12", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "14..24; favors 20,21,22", "valid": "14..24"},
    "shape_size": {"type": "int", "default": "4..10; core favors 6,8", "valid": "4..10"},
    "n_distract": {"type": "int", "default": "2..3", "valid": "2..3"},
    "palette_size": {"type": "int", "default": "4..6 including background; favors 6", "valid": "4..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
_COLORS = (3, 4, 5, 6, 7, 8, 9)


def _profiles(shape):
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    return (tuple(sum(r == i for r, _ in shape) for i in range(h)),
            tuple(sum(c == j for _, c in shape) for j in range(w)))


def _connected(shape):
    remaining = set(shape)
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if p in remaining:
                remaining.remove(p)
                stack.append(p)
    return not remaining


@lru_cache(maxsize=1)
def _shape_catalog():
    """Enumerate immutable geometry, not generated grids or seeded draws.

    The 4x3 footprint and its transpose include small shapes, not just shapes
    touching all four sides. Requiring independent peers preserves size-4 cases.
    """
    cells = tuple((r, c) for r in range(4) for c in range(3))
    shapes = set()
    for n in range(4, 11):
        for candidate in combinations(cells, n):
            if min(r for r, _ in candidate) or min(c for _, c in candidate):
                continue
            if _connected(candidate):
                shapes.add(candidate)
                shapes.add(tuple(sorted((c, r) for r, c in candidate)))
    profiles = {shape: _profiles(shape) for shape in sorted(shapes)}
    by_row, by_col = {}, {}
    for shape, (rows, cols) in profiles.items():
        by_row.setdefault((rows, len(cols)), []).append(shape)
        by_col.setdefault((cols, len(rows)), []).append(shape)
    by_size = {n: [] for n in range(4, 11)}
    peers = {}
    for shape, (rows, cols) in profiles.items():
        row_peers = tuple(s for s in by_row[rows, len(cols)] if profiles[s][1] != cols)
        col_peers = tuple(s for s in by_col[cols, len(rows)] if profiles[s][0] != rows)
        # One near-match also defeats unordered-count comparison. This leaves
        # both anchors and their distractors independently variable.
        unordered_row = tuple(s for s in row_peers if sorted(profiles[s][1]) == sorted(cols))
        unordered_col = tuple(s for s in col_peers if sorted(profiles[s][0]) == sorted(rows))
        if len(row_peers) >= 2 and len(col_peers) >= 2 and (unordered_row or unordered_col):
            by_size[len(shape)].append(shape)
            peers[shape] = (row_peers, col_peers, unordered_row, unordered_col)
    return {n: tuple(items) for n, items in by_size.items()}, peers, profiles


def _draw_axis(ctx, name, lo, hi, favored=()):
    return ctx.draw_choice(name, tuple(range(lo, hi+1)) + tuple(favored))


def _shape_roles(ctx, size, witness):
    by_size, peers, profiles = _shape_catalog()
    rng = ctx.draw_rng("shape_roles")
    target = rng.choice(by_size[size])
    row_peers, col_peers, unordered_row, unordered_col = peers[target]
    drow = rng.choice(unordered_row or row_peers)
    dcol = rng.choice(unordered_col or col_peers)
    if witness:
        blue_choices = tuple(s for s in row_peers if s != drow)
        red_choices = tuple(s for s in col_peers if s != dcol)
        return target, rng.choice(blue_choices), rng.choice(red_choices), drow, dcol
    # The candidate set is an L in (row-profile, column-profile) space. Its
    # center has incidence 4 and either leaf has incidence 3. Let the anchors
    # select a leaf, so the candidate-only "choose the center" shortcut fails.
    center = target
    target, other = (drow, dcol) if rng.randrange(2) else (dcol, drow)
    rows, cols = profiles[target]
    blue_choices = tuple(s for s, (r, c) in profiles.items()
                         if r == rows and len(c) == len(cols) and s != target)
    red_choices = tuple(s for s, (r, c) in profiles.items()
                        if c == cols and len(r) == len(rows) and s != target)
    # Every possible leaf in this finite bank has alternatives on both axes.
    # Non-target copies keep "copy an anchor, otherwise choose the center"
    # wrong in this phase too. Canonical target copies remain validator-valid.
    return target, rng.choice(blue_choices), rng.choice(red_choices), center, other


def _candidate_colors(ctx, count, palette_size, core, witness):
    """Return colors in target, two main decoys, optional extra order."""
    rng = ctx.draw_rng("candidate_colors")
    available = (4, 6, 7) if core else _COLORS
    colors = sorted(rng.sample(available, palette_size - 3))
    if witness:
        if len(colors) == 3:
            # The target is neither minimum nor maximum; color 4, when
            # present, goes to a decoy rather than becoming a target label.
            middle = colors[1]
            if middle == 4:
                middle = colors[2]
            other = [c for c in colors if c != middle]
            chosen = [middle, other[0], other[1]]
        elif len(colors) == 2:
            # A same-color earlier decoy defeats a color-only selector even
            # when only two candidate colors are requested.
            chosen = [colors[1], colors[0], colors[1]]
        else:
            chosen = colors * 3
    else:
        chosen = colors + [rng.choice(colors) for _ in range(3-len(colors))]
        rng.shuffle(chosen)
    chosen.extend(rng.choice(colors) for _ in range(count-3))
    return chosen


def _origins(ctx, h, w, count):
    """Five/six disjoint 4x4 cells fit every advertised dimension pair."""
    rng = ctx.draw_rng("placement_cells")
    arrangements = [(2, 3)]
    if h >= 14:
        arrangements.append((3, 2))
    nr, nc = rng.choice(arrangements)
    # Divide the usable cells after removing the separating gutters. Dividing
    # first would leave a three-cell slot at the legal 10x14 boundary.
    rows = [(i*(h-nr+1)//nr+i, (i+1)*(h-nr+1)//nr+i) for i in range(nr)]
    cols = [(i*(w-nc+1)//nc+i, (i+1)*(w-nc+1)//nc+i) for i in range(nc)]
    origins = [(rng.randint(a, b-4), rng.randint(c, d-4))
               for a, b in rows for c, d in cols]
    return sorted(rng.sample(origins, count))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool, float or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer (not {type(value).__name__})")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = ctx.draw_choice("profile_kind", ("core", "core", "core", "broad")) == "core"
    h = _draw_axis(ctx, "grid_h", 10, 24, (11, 12)*40 if core else ())
    w = _draw_axis(ctx, "grid_w", 14, 24, (20, 21, 22)*30 if core else ())
    favored = (4, 5, 6)*3 if difficulty == "easy" else ((8, 9, 10)*3 if difficulty == "hard" else ())
    size = _draw_axis(ctx, "shape_size", 4, 10, (6, 8)*25 if core else favored)
    nd = _draw_axis(ctx, "n_distract", 2, 3, (2,)*5 if core else ())
    palette = _draw_axis(ctx, "palette_size", 4, 6, (6,)*30 if core else ())
    witness = sample_index % LESSON_SCHEDULE_PERIOD == 1
    target, blue, red, drow, dcol = _shape_roles(ctx, size, witness)
    shapes = [target, drow, dcol]
    if nd == 3:
        # Also retain unequal-area distractors; never silently omit one.
        extra_size = ctx.draw_choice("extra_size", tuple(n for n in range(4, 11) if n != size))
        shapes.append(ctx.draw_rng("extra_shape").choice(_shape_catalog()[0][extra_size]))
    colors = _candidate_colors(ctx, len(shapes), palette, core, witness)
    items = [(blue, 1), (red, 2)] + list(zip(shapes, colors))
    rng = ctx.draw_rng("object_order")
    order = list(range(len(items)))
    rng.shuffle(order)
    if witness:
        # Candidate near-matches precede the target. Anchor positions and any
        # fourth candidate remain arbitrary; the even phase permits all orders.
        candidate_slots = sorted(order.index(i) for i in (2, 3, 4))
        decoys = [3, 4]
        rng.shuffle(decoys)
        for slot, role in zip(candidate_slots, decoys + [2]):
            order[slot] = role
        if order.index(2) == 2:
            # Canonical scenes always put the target third overall. Include
            # an anchor before it in each witness without fixing anchor order.
            later = rng.choice([order.index(0), order.index(1)])
            order[2], order[later] = order[later], order[2]
    grid = full_grid(h, w, 0)
    for (top, left), role in zip(_origins(ctx, h, w, len(items)), order):
        shape, color = items[role]
        for r, c in shape:
            grid[top+r][left+c] = color
    return grid


def _components(grid):
    result = []
    for obj in find_generator_objects(grid, univalued=True, diagonal=False, bg=0):
        cells = tuple(sorted(p for _, p in obj))
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        shape = tuple((r-top, c-left) for r, c in cells)
        rows, cols = _profiles(shape)
        result.append({"color": next(iter(obj))[0], "origin": (top, left),
                       "shape": shape, "rows": rows, "cols": cols})
    return sorted(result, key=lambda obj: obj["origin"])


def _parts(grid):
    items = _components(grid)
    blue = [o for o in items if o["color"] == 1]
    red = [o for o in items if o["color"] == 2]
    if not blue or not red:
        raise ValueError("both anchors are required")
    candidates = [o for o in items if o["color"] not in (1, 2)]
    return blue[0], red[0], candidates


def _matches(blue, red, candidates):
    return [o for o in candidates if o["rows"] == blue["rows"] and o["cols"] == red["cols"]]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    items = _components(grid)
    errors = []
    for color in (1, 2):
        count = sum(o["color"] == color for o in items)
        if count != 1:
            errors.append(f"expected one color-{color} anchor component, found {count}")
    if errors:
        return errors
    blue, red, candidates = _parts(grid)
    matches = _matches(blue, red, candidates)
    if len(matches) != 1:
        errors.append(f"expected exactly one joint-profile target, found {len(matches)}")
    return errors


def strict_canonical_like(grid):
    """Task-domain lawfulness, including every canonical input; not size equality."""
    return self_check(grid)


def observe_overrides(grid):
    blue, red, candidates = _parts(grid)
    target = _matches(blue, red, candidates)[0]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "shape_size": len(target["shape"]), "n_distract": len(candidates)-1,
            "palette_size": len({v for row in grid for v in row})}


def _crop(obj):
    if obj is None:
        return [[0]]
    out = full_grid(len(obj["rows"]), len(obj["cols"]), 0)
    for r, c in obj["shape"]:
        out[r][c] = 8
    return out


def _select(grid, mode):
    """Explicitly wrong hypotheses for authoring checks, never label authority."""
    blue, red, candidates = _parts(grid)
    if mode == "copy_blue":
        return _crop(blue)
    if mode == "copy_red":
        return _crop(red)
    if mode == "third_component":
        return _crop(_components(grid)[2])
    if mode in ("candidate_profile_incidence", "anchor_copy_then_incidence"):
        if mode == "anchor_copy_then_incidence":
            copied = next((o for o in candidates
                           if o["shape"] in (red["shape"], blue["shape"])), None)
            if copied is not None:
                return _crop(copied)
        def incidence(obj):
            return sum(o["rows"] == obj["rows"] for o in candidates) + sum(
                o["cols"] == obj["cols"] for o in candidates)
        return _crop(max(candidates, key=incidence, default=None))
    if mode == "minimum_candidate_color":
        candidates = sorted(candidates, key=lambda o: (o["color"], o["origin"]))
    predicates = {
        "exact_blue": lambda o: o["shape"] == blue["shape"],
        "exact_red": lambda o: o["shape"] == red["shape"],
        "row_only": lambda o: o["rows"] == blue["rows"],
        "column_only": lambda o: o["cols"] == red["cols"],
        "bbox_only": lambda o: len(o["rows"]) == len(blue["rows"]) and len(o["cols"]) == len(red["cols"]),
        "area_only": lambda o: len(o["shape"]) == len(blue["shape"]),
        "first_candidate": lambda o: True,
        "minimum_candidate_color": lambda o: True,
        "color_4": lambda o: o["color"] == 4,
        "unordered_profiles": lambda o: sorted(o["rows"]) == sorted(blue["rows"]) and sorted(o["cols"]) == sorted(red["cols"]),
    }
    chosen = next((o for o in candidates if predicates[mode](o)), None)
    return _crop(chosen)


def _rival(mode):
    def predict(grid):
        return _select(grid, mode)
    return predict


_PROFILE_RIVAL_NAMES = (
    "copy_blue", "copy_red", "exact_blue", "exact_red", "row_only", "column_only",
    "bbox_only", "area_only", "first_candidate", "minimum_candidate_color",
    "color_4", "unordered_profiles",
    "third_component",
)
_ANCHOR_ROLE_RIVAL_NAMES = ("candidate_profile_incidence", "anchor_copy_then_incidence")
SEMANTIC_RIVALS = {name: _rival(name)
                   for name in _PROFILE_RIVAL_NAMES + _ANCHOR_ROLE_RIVAL_NAMES}
# Exact/cropped blue fails canonical pairs; it is retained as a generated-support
# rival from the old audit, not falsely declared a canonical-fitting shortcut.
CANONICAL_SHORTCUTS = {name: fn for name, fn in SEMANTIC_RIVALS.items()
                       if name not in ("copy_blue", "exact_blue")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _joint_counterexample(grid):
    blue, red, candidates = _parts(grid)
    target = _crop(_matches(blue, red, candidates)[0])
    return all(SEMANTIC_RIVALS[name](grid) != target for name in _PROFILE_RIVAL_NAMES)


def _anchor_role_counterexample(grid):
    blue, red, candidates = _parts(grid)
    target = _crop(_matches(blue, red, candidates)[0])
    return all(SEMANTIC_RIVALS[name](grid) != target for name in _ANCHOR_ROLE_RIVAL_NAMES)


SEMANTIC_WITNESSES = {"joint_profile_counterexample": _joint_counterexample,
                      "anchor_role_counterexample": _anchor_role_counterexample}
WITNESS_RIVALS = {"joint_profile_counterexample": list(_PROFILE_RIVAL_NAMES),
                  "anchor_role_counterexample": list(_ANCHOR_ROLE_RIVAL_NAMES)}
