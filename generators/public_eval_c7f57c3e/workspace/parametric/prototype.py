"""Infer scaled motif instances, then replace them at a shared color anchor.

The sampler is constructive and reads no public fixtures. Python outputs are
claims for independent protected-Racket execution by the native preflight.
"""
from collections import Counter
from math import gcd

from puzzle_generators.base import gen_ctx

TASK_ID = 'public_eval_c7f57c3e'
VERSION = '1.0.0'


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('expected a rectangular exact-integer ARC grid of size 1..30')
    return grid


def components(grid, background):
    """Eight-connected multicolor components and maximal integer block scales."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for column in range(width):
            if (row, column) in seen or grid[row][column] == background:
                continue
            queue = [(row, column)]
            seen.add((row, column))
            points = []
            while queue:
                r, c = queue.pop()
                points.append((r, c, grid[r][c]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if (0 <= rr < height and 0 <= cc < width
                                and (rr, cc) not in seen
                                and grid[rr][cc] != background):
                            seen.add((rr, cc))
                            queue.append((rr, cc))
            points.sort()
            top = min(p[0] for p in points)
            left = min(p[1] for p in points)
            bottom = max(p[0] for p in points)
            right = max(p[1] for p in points)
            crop = [[background] * (right - left + 1) for _ in range(bottom - top + 1)]
            for r, c, value in points:
                crop[r - top][c - left] = value
            nh, nw = len(crop), len(crop[0])
            scale = next(k for k in range(gcd(nh, nw), 0, -1)
                         if nh % k == nw % k == 0
                         and all(crop[r][c] == crop[r // k * k][c // k * k]
                                 for r in range(nh) for c in range(nw)))
            template = [[crop[r][c] for c in range(0, nw, scale)]
                        for r in range(0, nh, scale)]
            result.append(dict(top=top, left=left, scale=scale,
                               template=template, cells=points))
    return result


def color_mask(template, color):
    points = [(r, c) for r, row in enumerate(template)
              for c, value in enumerate(row) if value == color]
    if not points:
        return None
    top = min(r for r, c in points)
    left = min(c for r, c in points)
    return tuple((r - top, c - left) for r, c in points), (top, left)


def analyze(grid):
    """Return the actual input-derived templates, scales, counts and bindings."""
    validate_grid(grid)
    histogram = Counter(value for row in grid for value in row)
    background = min(histogram, key=lambda color: (-histogram[color], color))
    objects = components(grid, background)
    templates = []
    for obj in objects:
        if obj['template'] not in templates:
            templates.append(obj['template'])
    if len(templates) != 2:
        raise ValueError('the admitted grammar requires exactly two normalized motifs')
    candidates = []
    for color in range(10):
        if color == background:
            continue
        masks = [color_mask(template, color) for template in templates]
        if all(mask is not None for mask in masks) and masks[0][0] == masks[1][0]:
            candidates.append((len(masks[0][0]), color, masks))
    if not candidates:
        raise ValueError('the two motifs require a common translated color anchor')
    _, anchor_color, masks = max(candidates, key=lambda item: (item[0], -item[1]))
    offsets = [list(mask[1]) for mask in masks]
    counts = [0, 0]
    for obj in objects:
        index = templates.index(obj['template'])
        obj['template_index'] = index
        obj['anchor'] = [obj['top'] + offsets[index][0] * obj['scale'],
                         obj['left'] + offsets[index][1] * obj['scale']]
        counts[index] += 1
    return dict(background=background, templates=templates,
                anchor_color=anchor_color, anchor_offsets=offsets,
                candidate_anchor_colors=[item[1] for item in candidates],
                counts=counts, components=objects)


def solve(grid, replacement='swap'):
    if type(replacement) is not str or replacement not in ('swap', 'minority'):
        raise ValueError('replacement must be swap or minority')
    data = analyze(grid)
    if replacement == 'minority' and data['counts'][0] == data['counts'][1]:
        raise ValueError('minority replacement requires a unique smaller instance frequency')
    minority = data['counts'].index(min(data['counts']))
    background = data['background']
    output = [[background] * len(grid[0]) for _ in grid]
    painted = set()
    for obj in data['components']:
        target = 1 - obj['template_index'] if replacement == 'swap' else minority
        offset_r, offset_c = data['anchor_offsets'][target]
        anchor_r, anchor_c = obj['anchor']
        scale = obj['scale']
        for r, row in enumerate(data['templates'][target]):
            for c, color in enumerate(row):
                if color == background:
                    continue
                for dr in range(scale):
                    for dc in range(scale):
                        rr = anchor_r + (r - offset_r) * scale + dr
                        cc = anchor_c + (c - offset_c) * scale + dc
                        if not (0 <= rr < len(output) and 0 <= cc < len(output[0])):
                            raise ValueError('replacement extends outside grid bounds')
                        if (rr, cc) in painted:
                            raise ValueError('replacement motifs overlap')
                        painted.add((rr, cc))
                        output[rr][cc] = color
    return output


def _motifs(rng, profile):
    palette = list(range(10))
    rng.shuffle(palette)
    background, anchor, core_a, core_b, tail_a, tail_b = palette[:6]
    shapes = (
        ([(0, 1), (1, 0), (1, 2), (2, 1)], [(1, 1)], 3),
        ([(0, 0), (0, 2), (2, 0), (2, 2)], [(1, 1)], 3),
        ([(0, 1), (0, 2), (1, 0), (1, 3), (2, 1), (2, 2)], [(1, 1), (1, 2)], 4),
        ([(0, 1), (1, 0), (1, 2), (2, 0), (2, 1)], [(1, 1)], 3),
        ([(r, c) for r in range(3) for c in range(3) if (r, c) != (1, 1)], [(1, 1)], 3),
    )
    anchor_points, core_points, width = shapes[profile]
    left = {point: anchor for point in anchor_points}
    right = dict(left)
    left.update({point: core_a for point in core_points})
    right.update({point: core_b for point in core_points})
    center = (width - 1) // 2
    a_columns = [center] if rng.getrandbits(1) else list(range(width))
    b_columns = list(range(width)) if len(a_columns) == 1 else [center]
    left.update({(-1, c): tail_a for c in a_columns})
    right.update({(3, c): tail_b for c in b_columns})
    return background, [left, right], (5, width)


def _transform(grid, code):
    for _ in range(code % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    if code >= 4:
        grid = [row[::-1] for row in grid]
    return grid


def scene(seed, index, stress=False, *, instance_count=None):
    """Reserve the union of both motif footprints before placing any instance.

    Sources 0/1 form the two-example teaching curriculum. Sources 100..103
    form a distinct query bank; requesting fewer demos never changes it.
    """
    integer(seed, 0, 2**63 - 1, 'seed')
    integer(index, 0, 2**63 - 1, 'index')
    if type(stress) is not bool:
        raise ValueError('stress must be a boolean')
    if instance_count is not None:
        integer(instance_count, 3, 7, 'instance_count')
    ctx = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK_ID)
    rng = ctx.draw_rng('scene')
    profile = 0 if stress else rng.randrange(5)
    background, motifs, (eh, ew) = _motifs(rng, profile)
    count = instance_count if instance_count is not None else (7 if stress else (4 if index in (0, 1) else (3, 5, 6, 4)[index % 4]))
    if stress:
        height = width = 30
        slots = [(0, 0, 4), (0, 14, 2), (0, 22, 2),
                 (12, 14, 2), (12, 22, 2), (25, 0, 1), (25, 27, 1)][:count]
        if count == 7:
            middle = [1, 0, 1, 0, 0]
            rng.shuffle(middle)
            roles = [0] + middle + [1]
        else:
            majority = count // 2 + 1
            roles = [0] * majority + [1] * (count - majority)
            rng.shuffle(roles)
        orientation = rng.randrange(8)
    else:
        big = 3 if index in (0, 1) else rng.choice((2, 3))
        s1, s2 = (1, 1) if index in (0, 1) else (rng.choice((1, 2)), rng.choice((1, 2)))
        column = ew * big + 2 + rng.randrange(2)
        slots = [(0, 0, big), (0, column, s1), (eh * s1 + 2, column, s2)]
        lower = max(eh * big, eh * s1 + 2 + eh * s2) + 2
        slots += [(lower, j * (ew + 2), 1) for j in range(count - 3)]
        used_h = max(r + eh * s for r, c, s in slots)
        used_w = max(c + ew * s for r, c, s in slots)
        height = used_h + rng.randint(0, min(3, 30 - used_h))
        width = used_w + rng.randint(0, min(4, 30 - used_w))
        dr, dc = rng.randint(0, height - used_h), rng.randint(0, width - used_w)
        slots = [(r + dr, c + dc, s) for r, c, s in slots]
        if index == 0:
            roles = [0] + [1] * (count - 1)
            orientation = rng.choice((0, 4))
        elif index == 1:
            roles = [0] * count
            roles[1] = 1
            orientation = rng.choice((1, 5))
        else:
            majority = count // 2 + 1
            roles = [0] * majority + [1] * (count - majority)
            rng.shuffle(roles)
            orientation = rng.randrange(8)
    # Reserve enough background for the densest permitted replacement, not
    # just the currently drawn colors. This also preserves background recovery
    # after a swap, making swap an involution throughout the generated domain.
    # Existing placements and already-sufficient canvases are unchanged.
    max_foreground = max(map(len, motifs)) * sum(scale * scale for _, _, scale in slots)
    while height * width <= 2 * max_foreground:
        if height < 30 and (height <= width or width == 30):
            height += 1
        elif width < 30:
            width += 1
        else:
            raise ValueError('replacement envelopes exceed the 30x30 background budget')
    grid = [[background] * width for _ in range(height)]
    for (row, column, scale), role in zip(slots, roles):
        for (r, c), color in motifs[role].items():
            for dr in range(scale):
                for dc in range(scale):
                    rr, cc = row + (r + 1) * scale + dr, column + c * scale + dc
                    if grid[rr][cc] != background:
                        raise ValueError('constructive input overlap')
                    grid[rr][cc] = color
    grid = _transform(grid, orientation)
    validate_grid(grid)
    if sum(v == background for row in grid for v in row) <= len(grid) * len(grid[0]) // 2:
        raise ValueError('background must remain the strict majority')
    return grid
