"""Source-bound authoring prototype for c8ab3fc199b1.

Canonical docking: each colored top marker selects its same-colored body object;
its tight 4-connected crop is bottom-aligned with left edge at that marker.

Area-queue docking: A identifies those objects *and counts their occupied cells*;
B sends the largest object to the leftmost marker dock, next to next, etc,
with original marker-column as the deterministic tie-break. It then crops and
bottom-aligns them as above. This genuinely reassigns source objects to docks.

All episode settings are private. Generated labels are deterministic Python
claims; independent protected Racket execution is the admission authority.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import random

TASK_ID = 'c8ab3fc199b1'
MODES = ('matching_color', 'area_queue')
PARAMETERS = {'dock_mode': list(MODES)}
DEFAULT = {'dock_mode': 'matching_color'}
CANONICAL_PATH = Path(__file__).with_name('canonical.rkt')
CANONICAL = CANONICAL_PATH.read_bytes().decode('utf8')
AREA_QUEUE = '''(rule!
  (let* ((markers (filter (lambda (cell) (and (= (first cell) 0)
                                            (not (= (third cell) 0))))
                          (grid-cells g)))
         (body (subgrid g 1 0 (- (rows g) 1) (- (cols g) 1)))
         (objs (objects body 0)))
    (define (extract m)
      (let* ((color (third m))
             (obj (first (filter (lambda (o) (= (obj-color o) color)) objs))))
        (list color (second m) (obj-size obj)
              (subgrid body (obj-r1 obj) (obj-c1 obj)
                            (obj-r2 obj) (obj-c2 obj)))))
    (define extracted (map extract markers))
    (define sorted-objects
      (sort extracted
            (lambda (a b)
              (or (> (third a) (third b))
                  (and (= (third a) (third b))
                       (< (second a) (second b)))))))
    (define docks (sort (map second extracted) <))
    (define placed
      (map (lambda (item col) (list (first item) col (fourth item)))
           sorted-objects docks))
    (define out-h (apply max (map (lambda (x) (rows (third x))) placed)))
    (for/fold ([out (empty-grid out-h (cols g) 0)]) ([item (in-list placed)])
      (let* ((left (second item))
             (crop (third item))
             (top (- out-h (rows crop))))
        (for*/fold ([acc out])
                   ([r (in-range (rows crop))]
                    [c (in-range (cols crop))])
          (let ((v (at crop r c)))
            (if (not (= v 0))
                (set-cell acc (+ top r) (+ left c) v)
                acc)))))))'''


def _settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {'dock_mode'}:
        raise ValueError('Exactly one dock_mode must be supplied')
    mode = settings['dock_mode']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('Unrecognized dock_mode')
    return mode


def program(settings: object) -> str:
    return CANONICAL if _settings(settings) == MODES[0] else AREA_QUEUE


def _exact_integer(x, name, low, high):
    if type(x) is not int or not low <= x <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return x


def _grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30
            or type(g[0]) is not list or not 1 <= len(g[0]) <= 30):
        raise ValueError('Invalid grid dimensions')
    w = len(g[0])
    if any(type(row) is not list or len(row) != w or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('Nonrectangular / noninteger / out-of-palette grid')
    return g


def _rng(seed: int, domain: str, index: int) -> random.Random:
    key = json.dumps([TASK_ID, 'area-queue-v2', seed, domain, index],
                     separators=(',', ':')).encode()
    return random.Random(int.from_bytes(sha256(key).digest(), 'big'))


def _connected_shape(height: int, width: int, occupied: int,
                     rng: random.Random) -> list[tuple[int, int]]:
    """Vary 4-connected footprints, with exact bbox, occupancy and orientation.

    The L scaffold spans all sides. Growing from randomly chosen neighboring
    cells creates many distinct holes / arms while preserving connectivity.
    """
    assert 1 <= width <= 8 and 2 <= height <= 12
    assert height + width - 1 <= occupied <= height * width
    cells = {(r, 0) for r in range(height)} | {(0, c) for c in range(width)}
    while len(cells) < occupied:
        frontier = {(r + dr, c + dc) for r, c in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if 0 <= r + dr < height and 0 <= c + dc < width
                    and (r + dr, c + dc) not in cells}
        cells.add(rng.choice(sorted(frontier)))
    if rng.randrange(2):
        cells = {(height - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, width - 1 - c) for r, c in cells}
    return sorted(cells)


def _descriptor(kind, max_h, max_w, rng, profile):
    """Cross actual area against bbox area, height and width.

    Profiles randomize the dimensions and role mapping; the rank cannot be
    inferred from the marker column, height, fixed shape, or body position.
    """
    if kind == 'compact':
        h = min(max_h, 3 + (max_h >= 8) + (profile % 3 == 2))
        w = min(max_w, 4 + (max_w >= 6))
        target = max(h + w - 1, h * w - 1 - (profile % 2))
    elif kind == 'sparse_tall':
        h = min(max_h, 5 + (max_h >= 7) + (max_h >= 9) * 2)
        w = min(max_w, 3 + (max_w >= 5))
        target = min(h * w, h + w - 1 + profile % 3)
    elif kind == 'medium':
        h = min(max_h, 4 + (max_h >= 7))
        w = min(max_w, 3 + (max_w >= 5))
        target = min(h * w, max(h + w - 1, (h * w * (65 + 5 * (profile % 3))) // 100))
    else:
        h = min(max_h, 3 + (profile % 3) + (max_h >= 9) * 2)
        w = min(max_w, 3 + (max_w >= 5))
        target = max(h + w - 1, min(h * w, (h * w * (55 + 10 * (profile % 3))) // 100))
    # Gentle jitter in dimensions via the independently seeded layout RNG.
    # The contrasts above survive because the compact object stays dense while
    # the tall one remains sparse (the counterexamples test actual scores).
    if profile >= 3 and rng.randrange(5) == 0:
        h = max(2, h - 1)
        target = max(h + w - 1, min(h * w, target))
    return h, w, target


def _scene(seed: int, domain: str, index: int):
    rng = _rng(seed, domain, index)
    if domain == 'query':
        sizes = [(10, 14), (16, 20), (24, 28), (30, 30)]
        # Vary source order across seeds; privacy exporter independently shuffles.
        rng_order = _rng(seed, 'query-size-schedule', 0)
        rng_order.shuffle(sizes)
        h, w = sizes[index]
        n = 4 if h >= 24 else (3 if h >= 16 else 2 + (index % 2))
    else:
        sizes = [(10, 15), (11, 16), (12, 18), (14, 20), (16, 22), (18, 24)]
        h, w = sizes[index]
        n = 3 if index < 3 else (2 + index % 3)
    if n < 2 or n > 4:
        raise AssertionError('invalid marker count')
    max_w = min(6, min((i + 1) * w // n - i * w // n for i in range(n)) - 1)
    max_h = min(10, h - 3)
    if max_w < 2 or max_h < 3:
        raise RuntimeError('Invalid profile geometry')
    types = ['compact', 'sparse_tall', 'medium', 'variable'][:n]
    # Occasionally switch the compact/mid roles to vary occupied-area rankings.
    if index > 0 and index % 2 == 1:
        types[0], types[-1] = types[-1], types[0]
    descriptors = [_descriptor(k, max_h, max_w, rng, index) for k in types]
    footprints = [_connected_shape(hh, ww, count, rng) for hh, ww, count in descriptors]
    scores = [len(cells) for cells in footprints]
    # Never teach the area-queue variant with only an identity permutation:
    # set the marker-color to footprint association to include an inversion.
    # Teach an input-dependent assignment rather than a memorized swap:
    # the first two demonstrations have deliberately different area orders.
    ranked_shapes = sorted(range(n), key=lambda i: (-scores[i], i))
    if domain == 'demo' and index == 0:
        order = list(reversed(ranked_shapes))
    elif domain == 'demo' and index == 1:
        order = [ranked_shapes[0], *reversed(ranked_shapes[1:])]
    else:
        order = list(range(n)); rng.shuffle(order)
        if [scores[i] for i in order] == sorted(scores, reverse=True):
            order[0], order[-1] = order[-1], order[0]
    palette = rng.sample(range(1, 10), 9)
    colors = palette[:n]
    if domain == 'demo' and index == 0 and n >= 3:
        # Non-monotone marker colors reject both sort-by-color shortcuts.
        ordered_colors = sorted(colors)
        if n == 3:
            colors = [ordered_colors[-1], ordered_colors[0], ordered_colors[1]]
        else:
            colors = [ordered_colors[-2], ordered_colors[0],
                      ordered_colors[-1], ordered_colors[1]]
    marker_to_shape = order
    grid = [[0] * w for _ in range(h)]
    starts = [i * w // n for i in range(n)]
    ends = [(i + 1) * w // n - 1 for i in range(n)]
    dock_w = max(ww for hh, ww, count in descriptors)
    slots = [rng.randint(start, end - dock_w + 1) for start, end in zip(starts, ends)]
    for j in range(n):
        grid[0][slots[j]] = colors[j]
    # Input geometry independent of the dock order, to defeat copying positions.
    body_strips = list(range(n))
    if domain == 'demo' and index == 0:
        body_strips = body_strips[1:] + body_strips[:1]
    else:
        rng.shuffle(body_strips)
    for marker_index, shape_index in enumerate(marker_to_shape):
        hh, ww, count = descriptors[shape_index]
        strip = body_strips[marker_index]
        x = rng.randint(starts[strip], ends[strip] - ww + 1)
        y = rng.randint(2, h - hh)
        for dy, dx in footprints[shape_index]:
            if grid[y + dy][x + dx]:
                raise AssertionError('Unexpected source collision')
            grid[y + dy][x + dx] = colors[marker_index]
    # Nuisance objects of colors not in row 0; never select or teach them as docks.
    if h >= 16:
        for extra_color in palette[n:n + (2 if h >= 24 else 1)]:
            decoy_h, decoy_w = (3 + rng.randrange(2), 2 + rng.randrange(2))
            decoy_cells = _connected_shape(decoy_h, decoy_w, decoy_h + decoy_w, rng)
            for _ in range(100):
                x = rng.randrange(w - decoy_w + 1)
                y = rng.randrange(2, h - decoy_h + 1)
                if all(grid[y + dy][x + dx] == 0 for dy, dx in decoy_cells):
                    for dy, dx in decoy_cells:
                        grid[y + dy][x + dx] = extra_color
                    break
    return _grid(grid)


def _extract(grid):
    """Python independent oracle for Racket object lookup and bbox cropping."""
    _grid(grid)
    markers = [(col, val) for col, val in enumerate(grid[0]) if val]
    if not 2 <= len(markers) <= 4 or len({c for _, c in markers}) != len(markers):
        raise ValueError('Scene must have 2..4 unique row-zero colors')
    h, w = len(grid), len(grid[0])
    records = []
    for anchor, color in markers:
        cells = {(r, col) for r in range(1, h) for col in range(w)
                 if grid[r][col] == color}
        if not cells:
            raise ValueError('Marker color has no body component')
        remaining = set(cells); stack = [next(iter(cells))]
        while stack:
            node = stack.pop()
            if node not in remaining:
                continue
            remaining.remove(node)
            row, col = node
            stack.extend((row + dr, col + dc)
                         for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                         if (row + dr, col + dc) in remaining)
        if remaining:
            raise ValueError('Multiple same-color components')
        row0 = min(r for r, col in cells); row1 = max(r for r, col in cells)
        col0 = min(col for r, col in cells); col1 = max(col for r, col in cells)
        crop = [[grid[r][col] for col in range(col0, col1 + 1)]
                for r in range(row0, row1 + 1)]
        records.append({'color': color, 'marker': anchor, 'area': len(cells),
                        'crop': crop, 'height': len(crop), 'width': len(crop[0]),
                        'bbox_area': len(crop) * len(crop[0])})
    return records


def transform(grid, settings):
    """Python mirror, not an authority: every retained pair is Racket verified."""
    mode = _settings(settings)
    records = _extract(grid)
    if mode == 'area_queue':
        slots = sorted(rec['marker'] for rec in records)
        # Stable tie rule is the originally leftmost marker, NOT body position.
        records = sorted(records, key=lambda rec: (-rec['area'], rec['marker']))
        records = [{**rec, 'marker': dock} for rec, dock in zip(records, slots)]
    out_h = max(rec['height'] for rec in records)
    out_w = len(grid[0]); out = [[0] * out_w for _ in range(out_h)]
    for rec in records:
        y = out_h - rec['height']; x = rec['marker']
        if x + rec['width'] > out_w:
            raise ValueError('Crop extends off the output')
        for dy, row in enumerate(rec['crop']):
            for dx, value in enumerate(row):
                if value:
                    if out[y + dy][x + dx]:
                        raise ValueError('Output crops collide')
                    out[y + dy][x + dx] = value
    return _grid(out)


def generate(seed, settings, demos, queries):
    _exact_integer(seed, 'seed', 0, 2**63 - 1)
    _exact_integer(demos, 'demos', 2, 6)
    _exact_integer(queries, 'queries', 4, 4)
    mode = _settings(settings)
    train = [_scene(seed, 'demo', i) for i in range(demos)]
    test = [_scene(seed, 'query', i) for i in range(queries)]
    seen = [json.dumps(g, separators=(',', ':')) for g in train + test]
    if len(seen) != len(set(seen)):
        raise ValueError('Repeated demonstration/query input')
    result = {'train': [{'input': g, 'output': transform(g, settings)} for g in train],
              'test': [{'input': g, 'output': transform(g, settings)} for g in test],
              'program_solution': program(settings)}
    competing = {'dock_mode': MODES[1 if mode == MODES[0] else 0]}
    if all(transform(p['input'], competing) == p['output'] for p in result['train']):
        raise ValueError('Demonstrations do not distinguish declared settings')
    return result
