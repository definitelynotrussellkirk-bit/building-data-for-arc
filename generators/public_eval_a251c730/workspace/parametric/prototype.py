"""Infer framed template dictionaries and stamp them at color-matched anchors.

Python claim implementation. The separate Racket program is authoritative for
qualification. No original grids, labels, or reference-data files are read here.
"""
from collections import Counter, deque

SCOPES = ('all_templates', 'largest_template')


def validate_grid(grid):
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError('grid height must be 1..30')
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid width must be 1..30')
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('rectangular integer-color grid required')


def mode(values):
    counts = Counter(values)
    if not counts:
        raise ValueError('empty color collection')
    return min(counts, key=lambda v: (-counts[v], v))


def components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    p = (r + dr, c + dc)
                    if p in remaining:
                        remaining.remove(p)
                        component.append(p)
                        queue.append(p)
        result.append(sorted(component))
    return result


def find_frames(grid):
    """Find maximal monochrome borders whose interior background differs.

    The 2x2 corner test cheaply excludes uniform stripes and large blank areas.
    Five-cell minimum sides separate frames from the generated small motifs.
    Background inference includes color zero and has an explicit numeric tie-break.
    """
    height, width = len(grid), len(grid[0])
    candidates = []
    for top in range(height - 4):
        for left in range(width - 4):
            border = grid[top][left]
            if (grid[top][left + 1] != border or grid[top + 1][left] != border
                    or grid[top + 1][left + 1] == border):
                continue
            right_end = left
            while right_end + 1 < width and grid[top][right_end + 1] == border:
                right_end += 1
            bottom_end = top
            while bottom_end + 1 < height and grid[bottom_end + 1][left] == border:
                bottom_end += 1
            for bottom in range(top + 4, bottom_end + 1):
                for right in range(left + 4, right_end + 1):
                    if any(grid[bottom][c] != border for c in range(left, right + 1)):
                        continue
                    if any(grid[r][right] != border for r in range(top, bottom + 1)):
                        continue
                    board = [row[left:right + 1] for row in grid[top:bottom + 1]]
                    background = mode(v for row in board[1:-1] for v in row[1:-1])
                    if background == border:
                        continue
                    foreground = [(r, c) for r in range(1, len(board) - 1)
                                  for c in range(1, len(board[0]) - 1)
                                  if board[r][c] != background]
                    if not foreground:
                        continue
                    candidates.append({'bbox': (top, left, bottom, right),
                                       'board': board, 'background': background,
                                       'border': border, 'objects': components(foreground)})
    # Keep outer frames rather than a frame-shaped object nested inside one.
    selected = []
    for item in sorted(candidates, key=lambda x: (-len(x['board']) * len(x['board'][0]), x['bbox'])):
        r0, c0, r1, c1 = item['bbox']
        if any(not (r1 < a or z < r0 or c1 < b or t < c0)
               for old in selected for a, b, z, t in [old['bbox']]):
            continue
        selected.append(item)
    return sorted(selected, key=lambda x: x['bbox'])


def extract(grid):
    validate_grid(grid)
    frames = find_frames(grid)
    if len(frames) != 2:
        raise ValueError('expected two disjoint framed panels')
    targets = [f for f in frames if all(len(o) == 1 for o in f['objects'])]
    if len(targets) != 1:
        raise ValueError('exactly one panel must contain only singleton markers')
    target = targets[0]
    source = next(f for f in frames if f is not target)
    anchors = [(o[0][0], o[0][1], target['board'][o[0][0]][o[0][1]]) for o in target['objects']]
    marker_colors = {color for _, _, color in anchors}
    templates = {}
    for obj in source['objects']:
        marker = [(r, c, source['board'][r][c]) for r, c in obj
                  if source['board'][r][c] in marker_colors]
        if len(marker) != 1:
            raise ValueError('each source template needs one uniquely colored anchor')
        ar, ac, color = marker[0]
        mask = tuple((r - ar, c - ac, source['board'][r][c]) for r, c in obj)
        record = {'marker': color, 'mask': mask, 'size': len(mask),
                  'source_anchor': (ar, ac), 'source_bbox':
                  (min(r for r, c in obj), min(c for r, c in obj),
                   max(r for r, c in obj), max(c for r, c in obj)), 'copies': 1}
        if color in templates:
            if templates[color]['mask'] != mask:
                raise ValueError('inconsistent repeated template')
            templates[color]['copies'] += 1
        else:
            templates[color] = record
    if set(templates) != marker_colors:
        raise ValueError('every target marker needs a template')
    return source, target, templates, anchors


def paint(target, templates, anchors, selected=None):
    """Paint nonbackground payload only, protecting frame and existing markers."""
    board = target['board']
    output = [row[:] for row in board]
    for ar, ac, color in anchors:
        if selected is not None and color not in selected:
            continue
        for dr, dc, value in templates[color]['mask']:
            r, c = ar + dr, ac + dc
            if (0 < r < len(board) - 1 and 0 < c < len(board[0]) - 1
                    and board[r][c] == target['background']):
                output[r][c] = value
    return output


def solve(grid, scope='all_templates'):
    if scope not in SCOPES:
        raise ValueError('invalid transfer_scope')
    _, target, templates, anchors = extract(grid)
    largest = max(item['size'] for item in templates.values())
    selected = None if scope == 'all_templates' else {
        color for color, item in templates.items() if item['size'] == largest}
    return paint(target, templates, anchors, selected)
