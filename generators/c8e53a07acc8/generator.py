"""Generator for c8e53a07acc8 / d6542281.

The modal-color field contains several multicolor templates.  Within each
Template, one color is an *anchor*: its cell count equals the size of one or
more isolated same-color objects.  The canonical rule aligns the full anchor
pattern to every matching standalone object, stamps the template there, and
removes source-template colors that occurred only once.  The generator makes
multiple independently actionable templates so an implementation must iterate
rather than stopping after the first one.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8e53a07acc8"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "559aa4d81a8f"
SUMMARY = (
    "Iterate over multiple multicolor templates; same-count standalone anchor "
    "objects receive translated template fragments, while unique source colors move."
)
EXAMPLES_NEEDED = 2
LESSON_SCHEDULE_PERIOD = 4

INVARIANTS = [
    "the nonzero modal background dominates the grid",
    "ordinary draws contain two or three separated multicolor templates",
    "every template has its own anchor color and one or two same-size standalone targets",
    "every later template changes the canonical output, defeating first-template-only rules",
    "source colors occurring once are erased only after that template stamps successfully",
]

AXES = {
    "grid_h": {"type": "int", "default": "four-profile schedule", "valid": "13..30"},
    "grid_w": {"type": "int", "default": "four-profile schedule", "valid": "13..30"},
    "n_templates": {"type": "int", "default": "schedule 2,2,3,3", "valid": "2..3"},
    "targets_per_template": {"type": "int", "default": "schedule 1,2,1,2", "valid": "1..2"},
}

SCHEDULE_PROFILES = (
    "two_templates_five_colors",
    "two_templates_repeated_targets",
    "three_templates_eight_colors",
    "three_templates_stress",
)

_PROFILE_COUNTS = (
    (2, 1, 0),  # templates, targets each, templates with a unique accent
    (2, 2, 1),
    (3, 1, 1),
    (3, 2, 3),
)
_PROFILE_DIMS = {
    # Profile zero intentionally anchors the exact canonical (19, 19, 5)
    # support point in every named band; the other profiles carry scale.
    "easy": ((19, 19), (14, 15), (16, 16), (17, 18)),
    "normal": ((19, 19), (16, 18), (21, 22), (24, 26)),
    "medium": ((19, 19), (19, 21), (23, 24), (26, 27)),
    "hard": ((19, 19), (24, 26), (27, 28), (30, 30)),
}

_ADJ8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Every footprint, including the one-cell larger alternate target used by the
# task-local parametric family, fits in 3x3.  ``body`` repeats; ``accent`` is
# optional and therefore exercises the canonical source-erasure branch.
_SHAPE_SPECS = (
    {
        "anchor": ((1, 0), (2, 1)),
        "body": ((0, 0), (0, 1), (1, 1), (1, 2)),
        "accent": (2, 2),
        "extra": (2, 0),
    },
    {
        "anchor": ((0, 0), (1, 0), (1, 1)),
        "body": ((0, 1), (0, 2), (1, 2), (2, 2)),
        "accent": (2, 1),
        "extra": (2, 0),
    },
    {
        "anchor": ((0, 0), (0, 1), (1, 2)),
        "body": ((1, 1), (2, 1), (2, 2)),
        "accent": (2, 0),
        "extra": (1, 0),
    },
)


def _band(difficulty) -> str:
    if difficulty == "easy":
        return "easy"
    if difficulty == "medium":
        return "medium"
    if difficulty == "hard":
        return "hard"
    return "normal"


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _normalize(*groups):
    all_cells = [cell for group in groups for cell in group]
    r0 = min(r for r, _ in all_cells)
    c0 = min(c for _, c in all_cells)
    return tuple(tuple((r - r0, c - c0) for r, c in group) for group in groups)


def _transform_point(point, rotation: int, reflect: bool):
    r, c = point
    if reflect:
        c = -c
    for _ in range(rotation % 4):
        r, c = c, -r
    return r, c


def _shape_variant(index: int, rng):
    spec = _SHAPE_SPECS[index % len(_SHAPE_SPECS)]
    rotation = rng.randrange(4)
    reflect = bool(rng.randrange(2))
    anchor = tuple(_transform_point(p, rotation, reflect) for p in spec["anchor"])
    body = tuple(_transform_point(p, rotation, reflect) for p in spec["body"])
    accent = (_transform_point(spec["accent"], rotation, reflect),)
    extra = (_transform_point(spec["extra"], rotation, reflect),)
    anchor, body, accent, extra = _normalize(anchor, body, accent, extra)
    return {
        "anchor": anchor,
        "body": body,
        "accent": accent[0],
        "extra": extra[0],
    }


def _slot_axis(length: int, rng):
    if length < 3:
        return []
    offsets = sorted({0, (length - 3) % 4})
    candidates = [list(range(offset, length - 2, 4)) for offset in offsets]
    best = max(len(values) for values in candidates)
    choices = [values for values in candidates if len(values) == best]
    return list(rng.choice(choices))


def _draw_scene(
    *,
    h: int,
    w: int,
    n_templates: int,
    targets_per_template: int,
    accent_count: int,
    rng,
):
    object_count = n_templates * (1 + targets_per_template)
    row_slots = _slot_axis(h, rng)
    col_slots = _slot_axis(w, rng)
    slots = [(r, c) for r in row_slots for c in col_slots]
    if len(slots) < object_count:
        raise ValueError(
            f"{h}x{w} cannot host {object_count} separated 3x3 object footprints"
        )
    rng.shuffle(slots)

    bg = rng.choice(tuple(range(1, 10)))
    needed = 2 * n_templates + accent_count
    palette = rng.sample([color for color in range(10) if color != bg], needed)
    anchor_colors = palette[:n_templates]
    body_colors = palette[n_templates : 2 * n_templates]
    accent_colors = palette[2 * n_templates :]

    grid = full_grid(h, w, bg)
    specs = []
    slot_index = 0
    for template_index in range(n_templates):
        shape = _shape_variant(template_index + rng.randrange(len(_SHAPE_SPECS)), rng)
        anchor = shape["anchor"]
        body = shape["body"]
        accent = shape["accent"]
        uses_accent = template_index < accent_count
        anchor_color = anchor_colors[template_index]
        body_color = body_colors[template_index]
        accent_color = accent_colors[template_index] if uses_accent else None

        tr, tc = slots[slot_index]
        slot_index += 1
        for dr, dc in anchor:
            grid[tr + dr][tc + dc] = anchor_color
        for dr, dc in body:
            grid[tr + dr][tc + dc] = body_color
        if uses_accent:
            grid[tr + accent[0]][tc + accent[1]] = accent_color

        target_origins = []
        for _ in range(targets_per_template):
            sr, sc = slots[slot_index]
            slot_index += 1
            target_origins.append((sr, sc))
            for dr, dc in anchor:
                grid[sr + dr][sc + dc] = anchor_color

        specs.append(
            {
                "anchor_color": anchor_color,
                "anchor": anchor,
                "body": body,
                "accent": accent if uses_accent else None,
                "template_origin": (tr, tc),
                "target_origins": target_origins,
            }
        )
    return grid, specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    profile_index = sample_index % len(SCHEDULE_PROFILES)
    default_templates, default_targets, accent_count = _PROFILE_COUNTS[profile_index]
    default_h, default_w = _PROFILE_DIMS[_band(difficulty)][profile_index]
    effective = dict(overrides)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("n_templates", default_templates)
    effective.setdefault("targets_per_template", default_targets)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 13, 30)
    w = ctx.draw_int("grid_w", 13, 30)
    n_templates = ctx.draw_int("n_templates", 2, 3)
    targets_per_template = ctx.draw_int("targets_per_template", 1, 2)
    rng = ctx.draw_rng("layout")

    # Preserve the requested palette profile where possible after exact count
    # overrides: 5 colors for two templates/no accents, 8 for three/one accent.
    accent_count = min(n_templates, accent_count)
    for _ in range(80):
        grid, _ = _draw_scene(
            h=h,
            w=w,
            n_templates=n_templates,
            targets_per_template=targets_per_template,
            accent_count=accent_count,
            rng=rng,
        )
        if not self_check(grid, difficulty=difficulty):
            return grid
    raise ValueError("could not construct a valid multi-template scene after 80 attempts")


def _mode(grid):
    counts = Counter(value for row in grid for value in row)
    return max(counts, key=counts.get)


def _components(grid, bg, *, adj8=True):
    h = len(grid)
    w = len(grid[0]) if h else 0
    neighbors = _ADJ8 if adj8 else ((-1, 0), (1, 0), (0, -1), (0, 1))
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in neighbors:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def _apply_templates(
    grid,
    *,
    first_template_only=False,
    first_target_only=False,
    erase_unique=True,
    adj8=True,
):
    """Faithful mirror of the selected canonical Racket on ordinary grids."""
    h, w = len(grid), len(grid[0])
    bg = _mode(grid)
    comps = _components(grid, bg, adj8=adj8)

    def colors_of(cells):
        return list(dict.fromkeys(grid[r][c] for r, c in cells))

    singles = [cells for cells in comps if len(colors_of(cells)) == 1]
    templates = [cells for cells in comps if len(colors_of(cells)) > 1]
    if first_template_only:
        templates = templates[:1]
    out = deepcopy(grid)

    for cells in templates:
        colors = colors_of(cells)

        def count_color(color):
            return sum(grid[r][c] == color for r, c in cells)

        anchor_colors = [
            color
            for color in colors
            if any(
                grid[obj[0][0]][obj[0][1]] == color and len(obj) == count_color(color)
                for obj in singles
            )
        ]
        anchor_cells = [(r, c) for r, c in cells if grid[r][c] in anchor_colors]
        non_anchor = [(r, c) for r, c in cells if grid[r][c] not in anchor_colors]
        stamped = False
        used_target_objects = set()
        for ar, ac in anchor_cells:
            color = grid[ar][ac]
            count = count_color(color)
            target_rows = [
                (object_index, point)
                for object_index, obj in enumerate(singles)
                if grid[obj[0][0]][obj[0][1]] == color and len(obj) == count
                for point in obj
            ]
            for object_index, (tr, tc) in target_rows:
                if first_target_only and used_target_objects and object_index not in used_target_objects:
                    continue
                dr, dc = tr - ar, tc - ac
                anchors_ok = all(
                    0 <= rr + dr < h
                    and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == grid[rr][cc]
                    for rr, cc in anchor_cells
                )
                fills_bg = any(
                    0 <= rr + dr < h
                    and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == bg
                    for rr, cc in non_anchor
                )
                if anchors_ok and fills_bg:
                    stamped = True
                    used_target_objects.add(object_index)
                    for rr, cc in cells:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            out[nr][nc] = grid[rr][cc]
        if stamped and erase_unique:
            for rr, cc in non_anchor:
                if count_color(grid[rr][cc]) == 1:
                    out[rr][cc] = bg
    return out


def rule_mirror(grid):
    return _apply_templates(grid)


def first_template_only_mirror(grid):
    return _apply_templates(grid, first_template_only=True)


def first_target_only_mirror(grid):
    return _apply_templates(grid, first_target_only=True)


def preserve_unique_source_mirror(grid):
    return _apply_templates(grid, erase_unique=False)


def four_connected_mirror(grid):
    return _apply_templates(grid, adj8=False)


def _analyze(grid):
    bg = _mode(grid)
    comps = _components(grid, bg)

    def colors(cells):
        return {grid[r][c] for r, c in cells}

    templates = [cells for cells in comps if len(colors(cells)) > 1]
    singles = [cells for cells in comps if len(colors(cells)) == 1]
    target_counts = []
    actionable = 0
    for cells in templates:
        matches = []
        for color in colors(cells):
            count = sum(grid[r][c] == color for r, c in cells)
            matching = [
                obj
                for obj in singles
                if len(obj) == count and grid[obj[0][0]][obj[0][1]] == color
            ]
            if matching:
                matches.append((color, matching))
        if matches:
            actionable += 1
            # Generated scenes deliberately have one anchor color per template.
            target_counts.append(sum(len(rows) for _, rows in matches))
    return {
        "background": bg,
        "components": comps,
        "templates": templates,
        "singles": singles,
        "actionable": actionable,
        "target_counts": target_counts,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    counts = analysis["target_counts"]
    if not counts or len(set(counts)) != 1:
        raise ValueError("generated scene does not expose a uniform targets_per_template value")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_templates": len(analysis["templates"]),
        "targets_per_template": counts[0],
    }


def _grid_errors(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a nonempty rectangular list"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an exact ARC color: {value!r}")
    return errors


def strict_canonical_like(grid):
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        errors.append(f"dimensions exceed ARC bounds: {h}x{w}")
        return errors
    counts = Counter(value for row in grid for value in row)
    bg = _mode(grid)
    if counts[bg] <= h * w // 2:
        errors.append("modal background must dominate")
    analysis = _analyze(grid)
    if not analysis["templates"]:
        errors.append("need at least one multicolor template")
    if not analysis["singles"]:
        errors.append("need at least one single-color component")
    if analysis["actionable"] < 1:
        errors.append("no template has a same-count standalone anchor")
    return errors


MIN_STRICT_FRAC = 0.95


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (13 <= h <= 30 and 13 <= w <= 30):
        errors.append(f"generated dimensions must be 13..30, got {h}x{w}")
        return errors
    counts = Counter(value for row in grid for value in row)
    bg = _mode(grid)
    if bg == 0:
        errors.append("generated modal background must be nonzero")
    if counts[bg] <= h * w // 2:
        errors.append("generated modal background must dominate")

    analysis = _analyze(grid)
    n_templates = len(analysis["templates"])
    if not 1 <= n_templates <= 3:
        errors.append(f"task instances need 1..3 templates, got {n_templates}")
    if analysis["actionable"] != n_templates:
        errors.append(
            f"every template must be actionable, got {analysis['actionable']}/{n_templates}"
        )
    target_counts = analysis["target_counts"]
    if target_counts and any(not 1 <= count <= 2 for count in target_counts):
        errors.append(f"targets per template must each be 1..2, got {target_counts}")
    if (
        not errors
        and n_templates > 1
        and rule_mirror(grid) == first_template_only_mirror(grid)
    ):
        errors.append("later templates do not change the output")
    return errors


SEMANTIC_RIVALS: dict[str, Callable] = {
    "process only the first template": first_template_only_mirror,
    "stamp only the first matching target": first_target_only_mirror,
    "preserve unique source colors": preserve_unique_source_mirror,
    "use four-connectivity for objects": four_connected_mirror,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _differs(grid, name):
    return SEMANTIC_RIVALS[name](deepcopy(grid)) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "multiple_templates_matter": lambda grid: _differs(grid, "process only the first template"),
    "all_matching_targets_matter": lambda grid: _differs(grid, "stamp only the first matching target"),
    "unique_source_colors_move": lambda grid: _differs(grid, "preserve unique source colors"),
    "diagonal_object_connectivity": lambda grid: _differs(grid, "use four-connectivity for objects"),
}
WITNESS_RIVALS = {
    "multiple_templates_matter": ["process only the first template"],
    "all_matching_targets_matter": ["stamp only the first matching target"],
    "unique_source_colors_move": ["preserve unique source colors"],
    "diagonal_object_connectivity": ["use four-connectivity for objects"],
}


def lesson_identifiable(demos, query):
    if type(demos) is not list or not demos:
        return ["at least one demonstration is required"]
    reasons = []
    for index, pair in enumerate([*demos, query]):
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with the canonical mirror")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
