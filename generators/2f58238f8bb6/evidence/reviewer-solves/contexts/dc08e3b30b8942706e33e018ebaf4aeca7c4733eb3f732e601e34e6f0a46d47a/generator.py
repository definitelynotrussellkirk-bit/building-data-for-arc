"""Inputs for a row of transform keys applied to one cropped body template.

The unchanged Racket rule supplies all training labels. Even sample indices
teach the complete key map on an asymmetric rectangle, including a touching
repeat. Odd indices retain a broader connected-shape distribution. Any three
of four consecutive default draws contain a teaching example; see notes.md.
Python transformations below serve shape selection and diagnostic rivals only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f58238f8bb6"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6da56985f4bc"
SUMMARY = (
    "Read row-0 keys 1=identity, 2=clockwise, 3=180 degrees, 4=left-right flip; "
    "crop one monochrome body template and form a top-aligned strip with "
    "one-column gaps. Varied connected templates alternate with asymmetric "
    "examples that teach every key and repeated commands."
)
INVARIANTS = [
    "input is a 6..14 by 8..16 rectangular grid of integer ARC colors",
    "row 0 contains 1..6 keys in 1..4; row 1 is a blank separator",
    "body is one monochrome 4-connected template of 3..12 cells, bbox at most 4x4",
    "keys and template are never clipped; output is at most 4x29",
    "default even-index draws have five keys, all four codes, and a touching repeat",
]
AXES = {
    "grid_h": {"type": "int", "default": "6 on teaching draws; weighted 7..14 otherwise", "valid": "6..14"},
    "grid_w": {"type": "int", "default": "8 on teaching draws; weighted 8..16 otherwise", "valid": "8..16"},
    "n": {"type": "int", "default": "5 on teaching draws; weighted 1..6 otherwise", "valid": "1..6"},
    "template_color": {"type": "int", "default": "cycle 1..4 on teaching draws; 1..9 otherwise", "valid": "1..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("teaching", "broad")
_KEY_TRANSFORM = {1: 0, 2: 1, 3: 2, 4: 4}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 2]


def _cw(shape):
    return tuple(tuple(row) for row in zip(*shape[::-1]))


def _d4(shape):
    shape = tuple(tuple(row) for row in shape)
    rotated = [shape]
    for _ in range(3):
        rotated.append(_cw(rotated[-1]))
    reflected = [tuple(row[::-1] for row in shape)]
    for _ in range(3):
        reflected.append(_cw(reflected[-1]))
    return tuple(rotated + reflected)


def _crop(cells):
    top = min(r for r, c in cells)
    left = min(c for r, c in cells)
    height = max(r for r, c in cells) - top + 1
    width = max(c for r, c in cells) - left + 1
    return tuple(tuple(int((r + top, c + left) in cells) for c in range(width))
                 for r in range(height))


def _shape(rng, teaching, difficulty):
    # Grow through an available frontier: connectivity and bounds are constructive.
    # No independently sampled cell is discarded or clipped.
    low, high = {"easy": (3, 6), "medium": (4, 9), "hard": (5, 12)}[difficulty]
    for _ in range(96):
        count = rng.randint(max(4, low) if teaching else low, min(10, high) if teaching else high)
        cells = {(rng.randrange(4), rng.randrange(4))}
        for _ in range(count - 1):
            frontier = sorted({(r + dr, c + dc) for r, c in cells
                               for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                               if 0 <= r + dr < 4 and 0 <= c + dc < 4
                               and (r + dr, c + dc) not in cells})
            cells.add(rng.choice(frontier))
        shape = _crop(cells)
        if not teaching or (len(shape) != len(shape[0]) and len(set(_d4(shape))) == 8):
            return shape
    # Bound rejection cost with a lawful asymmetric fallback.
    return rng.choice(_d4(((1, 1), (1, 0), (1, 0))))


def _axis(ctx, name, low, high, choices):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_choice(name, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=band, overrides=overrides)
    teaching = schedule_profile(seed, sample_index, band) == "teaching"
    favored_h = {"easy": (7, 7, 8), "medium": (8, 9, 10), "hard": (10, 12, 14)}[band]
    h = _axis(ctx, "grid_h", 6, 14, (6,) if teaching else tuple(range(7, 15)) + favored_h * 3)
    w = _axis(ctx, "grid_w", 8, 16, (8,) if teaching else tuple(range(8, 17)) + (8, 9, 10) * 4)
    favored_n = {"easy": (4, 4, 5), "medium": (4, 5, 5), "hard": (5, 6, 6)}[band]
    n = _axis(ctx, "n", 1, 6, (5,) if teaching else tuple(range(1, 7)) + favored_n * 3)
    # Successive default teaching grids differ in body color; broad grids have
    # >=7 rows. Therefore neither can duplicate an anchor in a four-pair lesson.
    anchor_color = 1 + (seed + sample_index // 2) % 4
    color = _axis(ctx, "template_color", 1, 9, (anchor_color,) if teaching else tuple(range(1, 10)))
    shape = _shape(ctx.draw_rng(f"body:{band}"), teaching, band)
    sh, sw = len(shape), len(shape[0])
    rng = ctx.draw_rng("placement")
    top, left = rng.randint(2, h - sh), rng.randint(0, w - sw)
    grid = full_grid(h, w, 0)
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            if value:
                grid[top + r][left + c] = color
    rng = ctx.draw_rng("keys")
    if teaching:
        keys = [1, 2, 3, 4]
        rng.shuffle(keys)
        if keys in ([1, 2, 3, 4], [4, 3, 2, 1]):
            keys[0], keys[1] = keys[1], keys[0]
        if n < 4:
            keys = keys[:n]
        while len(keys) < n:
            index = rng.randrange(len(keys))
            keys.insert(index, keys[index])
        # Touching repeats distinguish key cells from same-color header objects.
        start = rng.randrange(w - n + 1)
        columns = range(start, start + n)
    else:
        keys = [rng.randint(1, 4) for _ in range(n)]
        columns = sorted(rng.sample(range(w), n))
    for column, key in zip(columns, keys):
        grid[0][column] = key
    return grid


def _template(grid):
    cells = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value]
    if not cells:
        raise ValueError("missing template")
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    return tuple(tuple(row[left:right + 1]) for row in grid[top:bottom + 1])


def observe_overrides(grid):
    colors = {v for row in grid[1:] for v in row if v}
    if len(colors) != 1:
        raise ValueError("body must have exactly one template color")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n": sum(v != 0 for v in grid[0]), "template_color": next(iter(colors))}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    h, w = len(grid), len(grid[0])
    if not (6 <= h <= 14 and 8 <= w <= 16):
        return ["input outside the supported 6..14 by 8..16 envelope"]
    keys = [v for v in grid[0] if v]
    errors = []
    if not 1 <= len(keys) <= 6 or any(v not in _KEY_TRANSFORM for v in keys):
        errors.append("row 0 requires 1..6 transform keys in 1..4")
    if any(grid[1]):
        errors.append("row 1 must separate keys from the template")
    cells = {(r, c) for r in range(2, h) for c in range(w) if grid[r][c]}
    if not 3 <= len(cells) <= 12:
        errors.append("body requires 3..12 template cells")
    if not cells:
        return errors
    if len({grid[r][c] for r, c in cells}) != 1:
        errors.append("template must be monochrome")
    reached = {min(cells)}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in reached:
                reached.add(neighbor)
                frontier.append(neighbor)
    if reached != cells:
        errors.append("body must be one 4-connected component")
    if max(r for r, c in cells) - min(r for r, c in cells) >= 4 or max(c for r, c in cells) - min(c for r, c in cells) >= 4:
        errors.append("template bounding box must fit within 4x4")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _gallery(tiles, *, gap=1, bottom=False):
    height = max(len(tile) for tile in tiles)
    width = sum(len(tile[0]) for tile in tiles) + gap * (len(tiles) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for tile in tiles:
        top = height - len(tile) if bottom else 0
        for r, row in enumerate(tile):
            out[top + r][left:left + len(row)] = row
        left += len(tile[0]) + gap
    return out


def _rival(grid, mode):
    """Deliberately wrong diagnostic interpretations; never training labels."""
    keys = [v for v in grid[0] if v]
    variants = _d4(_template(grid))
    if mode == "first_four_keys":
        keys = keys[:4]
    elif mode == "collapse_consecutive":
        keys = [key for i, key in enumerate(keys) if i == 0 or key != keys[i - 1]]
    elif mode == "header_components":
        keys = [key for i, key in enumerate(grid[0]) if key and (i == 0 or key != grid[0][i - 1])]
    elif mode == "unique_keys":
        keys = list(dict.fromkeys(keys))
    elif mode == "sorted_keys":
        keys = sorted(keys)
    elif mode == "reversed_keys":
        keys = keys[::-1]
    mapping = dict(_KEY_TRANSFORM)
    if mode == "all_identity":
        mapping = dict.fromkeys(mapping, 0)
    elif mode == "key_2_counterclockwise":
        mapping[2] = 3
    elif mode == "key_3_vertical_flip":
        mapping[3] = 6
    elif mode == "key_4_vertical_flip":
        mapping[4] = 6
    tiles = [variants[mapping[key]] for key in keys]
    return _gallery(tiles, gap=0 if mode == "no_gap" else 1, bottom=mode == "bottom_aligned")


def _bind_rival(name):
    def rival(grid):
        return _rival(grid, name)
    return rival


LESSON_COMPETITORS = {name: _bind_rival(name) for name in (
    "first_four_keys", "collapse_consecutive", "header_components", "unique_keys",
    "sorted_keys", "reversed_keys", "all_identity", "key_2_counterclockwise",
    "key_3_vertical_flip", "key_4_vertical_flip", "no_gap", "bottom_aligned",
)}
CANONICAL_SHORTCUTS = {name: LESSON_COMPETITORS[name] for name in (
    "first_four_keys", "collapse_consecutive", "header_components",
)}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)


def _repeat_witness(grid):
    return sum(bool(v) for v in grid[0]) > 4 and any(
        grid[0][i] != 0 and grid[0][i] == grid[0][i + 1] for i in range(len(grid[0]) - 1))


SEMANTIC_WITNESSES = {"cellwise_repeated_commands": _repeat_witness}
WITNESS_RIVALS = {"cellwise_repeated_commands": list(CANONICAL_SHORTCUTS)}


def _gallery_tiles(output):
    if not output or not output[0] or any(len(row) != len(output[0]) for row in output):
        raise ValueError("label is not a rectangular gallery")
    occupied = [any(row[c] for row in output) for c in range(len(output[0]))]
    tiles, start = [], None
    for column, active in enumerate(occupied + [False]):
        if active and start is None:
            start = column
        elif not active and start is not None:
            rows = [tuple(row[start:column]) for row in output]
            while rows and not any(rows[-1]):
                rows.pop()
            tiles.append(tuple(rows))
            start = None
    # A connected cropped template has no blank interior columns. Rebuilding
    # validates single gaps, top alignment, and absence of external padding.
    if not tiles or _gallery(tiles) != [list(row) for row in output]:
        raise ValueError("label is not a top-aligned single-gap gallery")
    return tiles


def lesson_identifiable(demos, query):
    """Check key-map sufficiency within the eight D4 choices for each key.

    Intersect transformations supported by demonstration labels. Multiple maps
    are harmless if they give the same query tile. Query output is never read.
    This finite class does not certify universal induction; separately declared
    rivals cover command ordering and gallery assembly.
    """
    possible = {key: set(range(8)) for key in _KEY_TRANSFORM}
    try:
        for demo in demos:
            keys = [v for v in demo["input"][0] if v]
            variants = _d4(_template(demo["input"]))
            tiles = _gallery_tiles(demo["output"])
            if len(keys) != len(tiles):
                return ["demonstration does not contain one tile per key cell"]
            for key, tile in zip(keys, tiles):
                if key not in possible:
                    return ["demonstration contains an unsupported transform key"]
                possible[key].intersection_update(i for i, variant in enumerate(variants) if variant == tile)
                if not possible[key]:
                    return [f"demonstrations give inconsistent D4 mappings for key {key}"]
        grid = query["input"] if isinstance(query, dict) else query
        variants = _d4(_template(grid))
        reasons = []
        for key in sorted({v for v in grid[0] if v}):
            if key not in possible:
                reasons.append(f"query contains unsupported key {key}")
            elif len({variants[i] for i in possible[key]}) != 1:
                reasons.append(f"key {key} has distinct query answers under demonstration-compatible D4 maps")
        return reasons
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return [f"cannot analyze key-map teaching: {exc}"]
