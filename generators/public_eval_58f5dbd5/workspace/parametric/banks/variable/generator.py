"""Color-bound template carving for public ARC evaluation parent 58f5dbd5.

This portable module samples inputs and validates their grammar. It does not
load a native adapter, read an answer, or supply authoritative output labels.
Sample indices 0..5 teach the family; 6..9 form its four-query coverage bank.
Later indices repeat those structural profiles with fresh keyed random draws.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import permutations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "public_eval_58f5dbd5"
TASK_ID = "public_eval_58f5dbd5"
RULE_TASK_ID = "ee_58f5dbd5"
VERSION = "1.0.0"
RULE_HASH = "99afe4c1e801"
EXAMPLES_NEEDED = 2
SUMMARY = (
    "Recognize solid colored target rectangles, bind each to all remaining "
    "same-color template cells, carve that mask inside its preserved frame, "
    "and crop the target array with one background cell of margin."
)
INVARIANTS = [
    "Exact integer grids use colors 0..9 and dimensions at most 30 by 30.",
    "The entire outer border has one background color, which may be any color.",
    "Each target color has one recognized solid rectangle and one tight same-color template mask.",
    "Template height and width equal the corresponding target interior dimensions.",
    "Targets are separated by background and their expanded union crop contains no template or decoy.",
    "Generated decoys use distinct colors without targets and occur outside the target crop.",
    "The first two examples use distinct asymmetric masks, disconnected keys and non-rank color bindings.",
]
AXES = {
    "decoy_count": {
        "type": "int",
        "default": "rng 0..2 (seven-target stress profile uses 2)",
        "valid": "0..2",
        "description": "Exact number of unused foreground colors; independent of target geometry and masks.",
    },
}

_MAX_INTEGER = 2**63 - 1
_STEPS4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
_STEPS8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def _bbox(points):
    return [min(r for r, _ in points), min(c for _, c in points),
            max(r for r, _ in points), max(c for _, c in points)]


def _inside(point, box):
    r, c = point
    r0, c0, r1, c1 = box
    return r0 <= r <= r1 and c0 <= c <= c1


def _components(points, diagonal=False):
    remaining = set(points)
    result = []
    steps = _STEPS8 if diagonal else _STEPS4
    while remaining:
        stack = [remaining.pop()]
        component = set(stack)
        while stack:
            r, c = stack.pop()
            for dr, dc in steps:
                point = r + dr, c + dc
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def analyze(grid):
    """Recover input roles using only geometry and color; bboxes are inclusive.

    All remaining cells of a target's color form its template, including
    disconnected pieces. Colors without a qualifying target are distractors.
    A large solid template is allowed: only the larger matching rectangle has
    the required remaining-color bounding box. Admission is intentionally
    stricter than the total reference on malformed or overlapping scenes.
    """
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a nonempty list of at most 30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid rows must be nonempty lists of at most 30 cells")
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with exact list rows")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers in 0..9")
    background = grid[0][0]
    if any(grid[r][c] != background for r in range(height) for c in range(width)
           if r in (0, height - 1) or c in (0, width - 1)):
        raise ValueError("the entire outer border must have one background color")
    by_color = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != background:
                by_color.setdefault(color, set()).add((r, c))
    targets = []
    for color, points in by_color.items():
        candidates = []
        for component in _components(points):
            r0, c0, r1, c1 = box = _bbox(component)
            h, w = r1 - r0 + 1, c1 - c0 + 1
            if min(h, w) < 4 or len(component) != h * w:
                continue
            remaining = points - component
            if not remaining:
                continue
            kr0, kc0, kr1, kc1 = key_box = _bbox(remaining)
            if (kr1 - kr0 + 1, kc1 - kc0 + 1) != (h - 2, w - 2):
                continue
            mask = [[(r, c) in remaining for c in range(kc0, kc1 + 1)]
                    for r in range(kr0, kr1 + 1)]
            candidates.append({"color": color, "bbox": box,
                               "template_bbox": key_box, "mask": mask})
        if len(candidates) > 1:
            raise ValueError("a target color has more than one matching rectangle")
        targets.extend(candidates)
    if not targets:
        raise ValueError("no solid rectangle has a matching same-color template")
    targets.sort(key=lambda target: target["bbox"][:2])
    for index, target in enumerate(targets):
        r0, c0, r1, c1 = target["bbox"]
        for other in targets[index + 1:]:
            sr0, sc0, sr1, sc1 = other["bbox"]
            if not (r1 + 1 < sr0 or sr1 + 1 < r0 or c1 + 1 < sc0 or sc1 + 1 < c0):
                raise ValueError("target rectangles need a background separator")
    crop = [min(target["bbox"][0] for target in targets) - 1,
            min(target["bbox"][1] for target in targets) - 1,
            max(target["bbox"][2] for target in targets) + 1,
            max(target["bbox"][3] for target in targets) + 1]
    r0, c0, r1, c1 = crop
    if not (0 <= r0 <= r1 < height and 0 <= c0 <= c1 < width):
        raise ValueError("target crop needs one background cell of margin")
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != background and not any(
                    grid[r][c] == target["color"] and _inside((r, c), target["bbox"])
                    for target in targets):
                raise ValueError("target crop contains a template or distractor")
    return {"background": background, "targets": targets, "crop": crop}


def observe_overrides(grid):
    """Measure unused colors in the actual grid, without seed or hidden state."""
    parsed = analyze(grid)
    core = {parsed["background"]} | {target["color"] for target in parsed["targets"]}
    return {"decoy_count": len({value for row in grid for value in row} - core)}


def self_check(grid, *, difficulty=None, meta=None):
    """Report real grammar violations, including malformed grids and dirty crops."""
    try:
        analyze(grid)
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _validate_request(seed, sample_index, difficulty, overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer, not bool or a coercible value")
        if not 0 <= value <= _MAX_INTEGER:
            raise ValueError(f"{name} must be in 0..2**63-1")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if "decoy_count" in overrides:
        value = overrides["decoy_count"]
        if type(value) is not int:
            raise TypeError("decoy_count must be an exact integer")
        if not 0 <= value <= 2:
            raise ValueError("decoy_count must be in 0..2")


def _transform(grid, turns, reflect):
    result = [row[::-1] if reflect else row[:] for row in grid]
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _freeze(mask):
    return tuple(tuple(row) for row in mask)


def _mask_variants(mask):
    turns = range(4) if len(mask) == len(mask[0]) else (0, 2)
    return [_freeze(_transform(mask, turn, reflect)) for turn in turns for reflect in (False, True)]


@lru_cache(maxsize=24)
def _small_mask_bank(height, width, disconnected, asymmetric):
    """Enumerate small masks from geometry, not stored puzzle examples."""
    result = []
    for bits in range(1, (1 << (height * width)) - 1):
        mask = [[bool(bits & (1 << (r * width + c))) for c in range(width)] for r in range(height)]
        points = {(r, c) for r in range(height) for c in range(width) if mask[r][c]}
        if _bbox(points) != [0, 0, height - 1, width - 1]:
            continue
        if disconnected and len(_components(points, diagonal=True)) == 1:
            continue
        if asymmetric and len(set(_mask_variants(mask))) != (8 if height == width else 4):
            continue
        result.append(_freeze(mask))
    return tuple(result)


def _draw_mask(ctx, index, height, width, profile, used, difficulty):
    rng = ctx.draw_rng(f"mask.{index}.{difficulty or 'medium'}")
    if height * width <= 12:
        disconnected = profile in (0, 1) and index == 0
        asymmetric = (height, width) != (2, 2)
        bank = _small_mask_bank(height, width, disconnected, asymmetric)
        # Small 2x3 masks have only five asymmetric reflection/rotation classes;
        # six differently oriented masks are still six distinct lawful keys.
        def shape_key(mask):
            return min(_mask_variants(mask)) if profile in (0, 1) else _freeze(mask)

        choices = [mask for mask in bank if shape_key(mask) not in used]
        if not choices:
            raise RuntimeError("small mask grammar exhausted its distinct shape classes")
        # A size-independent density branch retains sparse and dense templates.
        density = (profile + index) % 3
        if density == 0:
            subset = [mask for mask in choices if sum(map(sum, mask)) <= height * width / 2]
        elif density == 2:
            subset = [mask for mask in choices if sum(map(sum, mask)) >= height * width * 0.6]
        else:
            subset = choices
        chosen = rng.choice(subset or choices)
        used.add(shape_key(chosen))
        return [list(row) for row in chosen]
    # Larger masks include disconnected noise, hollow frames, dense fields and
    # complete rectangles. All four outer sides have occupied cells.
    mode = rng.randrange(5)
    if mode == 4:
        return [[True] * width for _ in range(height)]
    if mode == 3:
        mask = [[r in (0, height - 1) or c in (0, width - 1)
                 for c in range(width)] for r in range(height)]
        mask[rng.randrange(1, height - 1)][rng.randrange(1, width - 1)] = True
        return mask
    density = (0.18, 0.47, 0.81)[mode]
    mask = [[rng.random() < density for _ in range(width)] for _ in range(height)]
    mask[0][rng.randrange(width)] = True
    mask[-1][rng.randrange(width)] = True
    mask[rng.randrange(height)][0] = True
    mask[rng.randrange(height)][-1] = True
    return mask


def _profile(profile, gap):
    """Return mask sizes, target offsets and template-column count."""
    if profile in (0, 1, 4, 5, 9):
        height, width = {0: (3, 3), 1: (4, 3), 4: (3, 3), 5: (2, 3), 9: (3, 3)}[profile]
        slots = {
            0: [(0, 0), (0, 1), (1, 0), (1, 1)],
            1: [(0, 0), (0, 1), (1, 0)],
            4: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
            5: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
            9: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2)],
        }[profile]
        offsets = [(r * (height + 2 + gap), c * (width + 2 + gap)) for r, c in slots]
        return [(height, width)] * len(slots), offsets, 2 if profile in (0, 1) else 1
    if profile == 2:
        return [(5, 6)], [(0, 0)], 1
    if profile == 3:
        return [(2, 2), (2, 5)], [(0, 0), (6, 1)], 1
    if profile == 6:
        return [(4, 7), (7, 3)], [(0, 0), (8, 2)], 1
    if profile == 7:
        return [(3, 3)] * 4, [(7 * index, 0) for index in range(4)], 2
    return [(19, 10)], [(0, 0)], 1


def _transformed_corner(box, turns, reflect):
    r0, c0, r1, c1 = box
    points = []
    for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        if reflect:
            c = -c
        for _ in range(turns):
            r, c = c, -r
        points.append((r, c))
    return min(r for r, _ in points), min(c for _, c in points)


def _reading_orders(boxes, turns, reflect):
    points = [_transformed_corner(box, turns, reflect) for box in boxes]
    row = tuple(sorted(range(len(boxes)), key=lambda index: points[index]))
    col = tuple(sorted(range(len(boxes)), key=lambda index: points[index][::-1]))
    return row, col


def _draw_decoys(grid, crop, key_boxes, colors, ctx):
    """Reserve both latent decoys so overrides cannot perturb other placement."""
    staged = [row[:] for row in grid]
    background = grid[0][0]
    result = []
    patterns = [((0, 0),), ((0, 0), (0, 1)), ((0, 0), (1, 1)),
                ((0, 0), (1, 0), (1, 1)), ((0, 0), (0, 1), (1, 0), (1, 1)),
                ((0, 0), (1, 1), (2, 2))]
    for index, color in enumerate(colors):
        rng = ctx.draw_rng(f"decoy_placement.{index}")
        choices = patterns[:]
        rng.shuffle(choices)
        placements = []
        for pattern in choices:
            ph = max(r for r, _ in pattern) + 1
            pw = max(c for _, c in pattern) + 1
            for r in range(1, len(grid) - ph):
                for c in range(1, len(grid[0]) - pw):
                    points = [(r + dr, c + dc) for dr, dc in pattern]
                    if all(staged[rr][cc] == background and not _inside((rr, cc), crop)
                           and not any(_inside((rr, cc), box) for box in key_boxes)
                           for rr, cc in points):
                        placements.append(points)
            if placements:
                break
        if not placements:
            raise RuntimeError("layout has no room for its reserved decoys")
        points = rng.choice(placements)
        result.append((color, points))
        for r, c in points:
            staged[r][c] = color
    return result


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    """Draw a lawful input using independent GenCtx RNG labels only.

    Integers are restricted to 0..2**63-1; difficulty is a sampling hint from
    None/easy/medium/hard. decoy_count is an exact override in 0..2. Shapes and
    palette are independent of that override. There is no rejection loop.
    """
    _validate_request(seed, sample_index, difficulty, overrides)
    profile = sample_index % 10
    effective_overrides = dict(overrides)
    if profile == 9:
        effective_overrides.setdefault("decoy_count", 2)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective_overrides)
    layout_rng = ctx.draw_rng("layout")
    gap = 3 if profile == 9 else layout_rng.randint(1, 2)
    sizes, offsets, key_columns = _profile(profile, gap)
    target_count = len(sizes)
    turns = ctx.draw_rng("orientation").randrange(4)
    reflect = bool(ctx.draw_rng("reflection").randrange(2))
    target_boxes = [[r, c, r + h + 1, c + w + 1] for (h, w), (r, c) in zip(sizes, offsets)]
    if profile == 1:
        row_order, col_order = _reading_orders(target_boxes, turns, reflect)
        if row_order == col_order:
            # A rotated three-cell L can be monotone in both scan directions.
            # Reflect the array locally so the teaching roles remain distinct.
            last_col = max(box[3] for box in target_boxes)
            target_boxes = [[r0, last_col - c1, r1, last_col - c0]
                            for r0, c0, r1, c1 in target_boxes]
    panel_h = max(box[2] for box in target_boxes) + 3
    panel_w = max(box[3] for box in target_boxes) + 3
    max_key_h = max(h for h, _ in sizes)
    max_key_w = max(w for _, w in sizes)
    key_rows = (target_count + key_columns - 1) // key_columns
    key_h = key_rows * (max_key_h + 1) - 1
    key_w = key_columns * (max_key_w + 1) - 1
    slots = [[(index // key_columns) * (max_key_h + 1),
              (index % key_columns) * (max_key_w + 1),
              (index // key_columns) * (max_key_h + 1) + max_key_h - 1,
              (index % key_columns) * (max_key_w + 1) + max_key_w - 1]
             for index in range(target_count)]
    order_rng = ctx.draw_rng("template_assignment")
    assignment = list(range(target_count))
    target_orders = _reading_orders(target_boxes, turns, reflect)
    if profile in (0, 1):
        key_orders = _reading_orders(slots, turns, reflect)
        admissible = [order for order in permutations(assignment)
                      if all(tuple(order[index] for index in key_order) not in target_orders
                             for key_order in key_orders)]
        assignment = list(order_rng.choice(admissible))
    else:
        order_rng.shuffle(assignment)
    minimum_h = max(panel_h, key_h + 2)
    minimum_w = panel_w + key_w + 4
    if profile == 9:
        height = width = 30
    else:
        height = 30 if profile == 7 else minimum_h + layout_rng.randint(0, min(6, 30 - minimum_h))
        width = minimum_w + layout_rng.randint(0, min(6, 30 - minimum_w))
    panel_top = layout_rng.randint(0, height - panel_h)
    panel_left = layout_rng.randint(0, width - minimum_w)
    key_top = layout_rng.randint(1, height - key_h - 1)
    key_left = panel_left + panel_w + 2
    crop = [panel_top, panel_left, panel_top + panel_h - 1, panel_left + panel_w - 1]
    target_boxes = [[r0 + panel_top + 1, c0 + panel_left + 1,
                     r1 + panel_top + 1, c1 + panel_left + 1]
                    for r0, c0, r1, c1 in target_boxes]
    palette = list(range(10))
    ctx.draw_rng("palette").shuffle(palette)
    if profile in (0, 1):
        target_colors = palette[1:target_count + 1]
        ordered_colors = [colors for colors in permutations(target_colors)
                          if all(tuple(colors[index] for index in order) not in
                                 (tuple(sorted(colors)), tuple(sorted(colors, reverse=True)))
                                 for order in target_orders)]
        palette[1:target_count + 1] = ctx.draw_rng("target_color_order").choice(ordered_colors)
    background = palette[0]
    grid = [[background] * width for _ in range(height)]
    masks = []
    used = set()
    for index, ((mask_h, mask_w), box) in enumerate(zip(sizes, target_boxes)):
        mask = _draw_mask(ctx, index, mask_h, mask_w, profile, used, difficulty)
        masks.append(mask)
        r0, c0, r1, c1 = box
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                grid[r][c] = palette[index + 1]
    key_boxes = []
    for slot, index in zip(slots, assignment):
        kr0, kc0 = key_top + slot[0], key_left + slot[1]
        mask = masks[index]
        key_boxes.append([kr0, kc0, kr0 + len(mask) - 1, kc0 + len(mask[0]) - 1])
        for r, row in enumerate(mask):
            for c, occupied in enumerate(row):
                if occupied:
                    grid[kr0 + r][kc0 + c] = palette[index + 1]
    decoy_count = ctx.draw_int_strict("decoy_count", 0, 2)
    placements = _draw_decoys(grid, crop, key_boxes, palette[target_count + 1:target_count + 3], ctx)
    for color, points in placements[:decoy_count]:
        for r, c in points:
            grid[r][c] = color
    result = _transform(grid, turns, reflect)
    analyze(result)
    return result
