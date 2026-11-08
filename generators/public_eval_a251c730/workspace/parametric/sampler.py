"""Standalone framed marker-template input sampler; no sibling source imports."""
from puzzle_generators.base import gen_ctx

TASK_ID = 'public_eval_a251c730'
GENERATOR_ID = TASK_ID
RULE_TASK_ID = 'ee_a251c730'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Recover marker-relative templates from one panel and stamp a second panel.'
AXES = {'height': {'type': 'int', 'valid': '24..30'},
        'width': {'type': 'int', 'valid': '26..30'},
        'rotation': {'type': 'int', 'valid': '0..3'}}


def transform_cells(cells, turns, mirror):
    result = set(cells)
    if mirror:
        result = {(r, -c) for r, c in result}
    for _ in range(turns):
        result = {(c, -r) for r, c in result}
    r0 = min(r for r, c in result)
    c0 = min(c for r, c in result)
    return sorted((r - r0, c - c0) for r, c in result)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
        raise ValueError('exact integer seed and nonnegative sample_index required')
    if set(overrides) - set(AXES):
        raise ValueError('unknown override')
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, overrides=overrides)
    rng = ctx.draw_rng('geometry')
    color_rng = ctx.draw_rng('colors')
    height = overrides.get('height', (24, 26, 28, 30)[sample_index % 4])
    width = overrides.get('width', (26, 28, 29, 30)[sample_index % 4])
    rotation = overrides.get('rotation', sample_index % 4)
    if type(height) is not int or not 24 <= height <= 30:
        raise ValueError('height must be 24..30')
    if type(width) is not int or not 26 <= width <= 30:
        raise ValueError('width must be 26..30')
    if type(rotation) is not int or rotation not in range(4):
        raise ValueError('rotation must be 0..3')
    count = 2 if sample_index in (0, 1) else (3 if sample_index % 4 == 3 else rng.choice((2, 3)))
    palette = color_rng.sample(range(10), 10)
    source_bg, target_bg, source_frame, target_frame = palette[:4]
    if sample_index != 0 and color_rng.randrange(3) == 0:
        target_bg = source_bg
    markers = palette[4:4 + count]
    payload = palette[7:7 + count] if count == 3 else palette[6:8]

    # Sparse diagonal-rich and dense shapes reverse occupied-area versus bbox-area.
    sparse = {(i, i) for i in range(4)}
    extra = rng.sample([(r, c) for r in range(4) for c in range(4)
                        if abs(r-c) == 1], rng.randrange(3))
    if sample_index in (0, 1):
        # A diagonal-rich motif with a real cardinal neighbor: both 4-only
        # extraction and treating the motif as a pure singleton are teachably wrong.
        extra = [(0, 1)] + ([rng.choice([(1, 0), (1, 2), (2, 1), (2, 3), (3, 2)])] if rng.randrange(2) else [])
    sparse.update(extra)
    dense = {(r, c) for r in range(3) for c in range(3)}
    for p in rng.sample([(0, 0), (0, 2), (2, 0), (2, 2)], rng.randrange(3)):
        dense.remove(p)
    shapes = [sparse, dense]
    if count == 3:
        third = {(r, c) for r in range(2) for c in range(4)}
        if rng.randrange(2):
            third.remove(rng.choice(((0, 0), (0, 3), (1, 0), (1, 3))))
        shapes.append(third)
    rng.shuffle(shapes)
    patterns = []
    for i, shape in enumerate(shapes):
        cells = transform_cells(shape, rng.randrange(4), rng.randrange(2))
        ph = max(r for r, c in cells) + 1
        pw = max(c for r, c in cells) + 1
        anchors = [p for p in cells if p[0] in (0, ph-1) or p[1] in (0, pw-1)]
        if sample_index == 1:
            anchors = [p for p in anchors if any((p[0]+dr, p[1]+dc) in cells
                       for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))]
        anchor = rng.choice(anchors)
        colored = [(r, c, markers[i] if (r, c) == anchor else payload[i]) for r, c in cells]
        # Some motifs have two payload colors, ruling out silhouette-only copying.
        if sample_index == 0 or rng.randrange(2):
            j = rng.choice([j for j, (r, c, _) in enumerate(colored) if (r, c) != anchor])
            r, c, _ = colored[j]
            colored[j] = (r, c, payload[(i + 1) % count])
        patterns.append({'cells': colored, 'anchor': anchor, 'shape': (ph, pw)})

    sizes = [len(p['cells']) for p in patterns]
    largest = max(range(count), key=lambda i: sizes[i])
    if count == 2:
        source_counts = [2, 2]
        source_counts[largest] = 1 if sample_index % 2 == 0 else 2
        source_counts[1-largest] = 3 if sample_index % 2 == 0 else 1
        target_counts = [2, 2]
        target_counts[largest] = 4 if sample_index % 2 == 0 else 2
        target_counts[1-largest] = 2 if sample_index % 2 == 0 else 4
    else:
        source_counts = [rng.choice((1, 2)) for _ in range(count)]
        target_counts = [2] * count

    margin = 0 if sample_index % 4 == 3 else 1
    source_width = 11 if width == 26 else 12 if width < 30 else 13
    target_width = width - 2 * margin - source_width - 2
    panel_height = height - 2 * margin
    source_box = (margin, margin, panel_height, source_width)
    target_box = (margin, margin + source_width + 2, panel_height, target_width)
    stripe_colors = [v for v in palette if v not in (source_frame, target_frame)]
    stripe_colors = rng.sample(stripe_colors, rng.randint(3, 6))
    horizontal = bool(rng.randrange(2))
    phase = rng.randrange(len(stripe_colors))
    grid = [[stripe_colors[((r if horizontal else c) + phase) % len(stripe_colors)]
             for c in range(width)] for r in range(height)]

    def panel(box, background, border, copies, markers_only):
        top, left, hh, ww = box
        for r in range(hh):
            for c in range(ww):
                grid[top+r][left+c] = border if r in (0, hh-1) or c in (0, ww-1) else background
        inner_h, inner_w = hh - 2, ww - 2
        inventory = [i for i, n in enumerate(copies) for _ in range(n)]
        rng.shuffle(inventory)
        rows = (len(inventory) + 1) // 2
        row_starts = [i * (inner_h - 4) // (rows - 1) for i in range(rows)] if rows > 1 else [0]
        slots = [(r, c) for r in row_starts for c in (0, inner_w - 4)]
        rng.shuffle(slots)
        for i, (r, c) in zip(inventory, slots):
            pattern = patterns[i]
            ph, pw = pattern['shape']
            r += rng.randint(0, 4-ph)
            c += rng.randint(0, 4-pw)
            cells = [(pattern['anchor'][0], pattern['anchor'][1], markers[i])] if markers_only else pattern['cells']
            for dr, dc, color in cells:
                grid[top+1+r+dr][left+1+c+dc] = color

    panel(source_box, source_bg, source_frame, source_counts, False)
    panel(target_box, target_bg, target_frame, target_counts, True)
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rotation):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid
