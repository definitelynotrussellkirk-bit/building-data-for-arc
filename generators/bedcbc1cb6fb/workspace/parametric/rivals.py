"""Independent, finite wrong-rule diagnostics; never an authority for labels.

No sampler/prototype helper is imported. Missing count matches leave canonical A
unchanged; spatial/area ties are resolved in row-major component order. These
explicit totalizations are part of each diagnostic, not claims about all solvers.
"""
from __future__ import annotations

from collections import deque

PALETTE_RIVALS = (
    'rowmajor_all_colors', 'unique_scan_palette', 'reverse_palette',
    'sorted_colors', 'antidiagonal', 'fixed_two_markers', 'fixed_three_markers',
    'first_marker_fill', 'last_marker_fill', 'stop_diagonal_at_first_zero',
)
B_RIVALS = (
    'input_last_color_count', 'global_last_color_count', 'original_interior_area',
    'center_width', 'center_height', 'center_perimeter', 'inner_width',
    'inner_height', 'marker_count', 'same_shape_count', 'bbox_area_selector',
    'smallest_key', 'largest_key', 'middle_key', 'first_key', 'last_key',
    'nearest_key', 'farthest_key', 'fixed_color_2', 'minimum_color',
    'maximum_color', 'occupied_only', 'holes_only', 'all_keys',
    'fewest_holes', 'most_holes', 'leftmost_key', 'rightmost_key',
    'topmost_key', 'bottommost_key',
)
RIVALS = ('other_setting',) + PALETTE_RIVALS + B_RIVALS


def _bbox(cells):
    return [min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells)]


def _inside(r, c, box):
    return box[0] <= r <= box[2] and box[1] <= c <= box[3]


def analyze(grid):
    """Parse the visual grammar independently, including optional findings."""
    if not isinstance(grid, list) or not grid or not grid[0]:
        raise ValueError('empty grid')
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError('nonrectangular grid')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('invalid ARC color')
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not blues:
        raise ValueError('no blue frame')
    box = _bbox(blues)
    top, left, bottom, right = box
    inner = [top + 1, left + 1, bottom - 1, right - 1]
    palette = [grid[i][i] for i in range(min(h, w)) if grid[i][i] not in (0, 1)]
    if not palette:
        raise ValueError('no diagonal palette')
    markers = [[i, i, grid[i][i]] for i in range(min(h, w))
               if grid[i][i] not in (0, 1)]
    available = {(r, c) for r in range(h) for c in range(w)
                 if grid[r][c] not in (0, 1) and r != c and not _inside(r, c, box)}
    keys = []
    while available:
        origin = min(available)
        available.remove(origin)
        cells, queue = [origin], deque([origin])
        color = grid[origin[0]][origin[1]]
        while queue:
            r, c = queue.popleft()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in available and grid[p[0]][p[1]] == color:
                    available.remove(p)
                    cells.append(p)
                    queue.append(p)
        kb = _bbox(cells)
        keys.append({'color': color, 'area': len(cells), 'bbox': kb,
                     'bbox_area': (kb[2]-kb[0]+1)*(kb[3]-kb[1]+1),
                     'cells': [list(p) for p in sorted(cells)]})
    findings = []
    expected_blue = {(r, c) for r in range(top, bottom+1)
                     for c in range(left, right+1)
                     if r in (top, bottom) or c in (left, right)}
    if set(blues) != expected_blue:
        findings.append('blue cells are not exactly one rectangular perimeter')
    if len(set(palette)) != len(palette):
        findings.append('diagonal palette repeats colors')
    if len(keys) != 3:
        findings.append('external key count is not three')
    for key in keys:
        if key['color'] in palette:
            findings.append('external key color overlaps palette')
        if key['area'] == key['bbox_area']:
            findings.append('external key is rectangular')
    if any(grid[r][c] for r in range(top+1, bottom) for c in range(left+1, right)):
        findings.append('original frame interior is nonempty')
    return {'height': h, 'width': w, 'framebbox': box, 'innerbbox': inner,
            'markers': markers, 'markerlist': palette, 'keys': keys,
            'findings': findings}


def _paint_rings(grid, palette, info):
    output = [row[:] for row in grid]
    top, left, bottom, right = info['innerbbox']
    for color in palette:
        if top > bottom or left > right:
            break
        for r in range(top, bottom+1):
            for c in range(left, right+1):
                output[r][c] = color
        top, left, bottom, right = top+1, left+1, bottom-1, right-1
    return output


def _palette(grid, info, rival):
    colors = info['markerlist'][:]
    if rival == 'rowmajor_all_colors':
        return [v for row in grid for v in row if v not in (0, 1)]
    if rival == 'unique_scan_palette':
        return list(dict.fromkeys(v for row in grid for v in row if v not in (0, 1)))
    if rival == 'reverse_palette':
        return colors[::-1]
    if rival == 'sorted_colors':
        return sorted(colors)
    if rival == 'antidiagonal':
        return [grid[i][info['width']-1-i] for i in range(min(info['height'], info['width']))
                if grid[i][info['width']-1-i] not in (0, 1)]
    if rival == 'fixed_two_markers':
        return colors[:2]
    if rival == 'fixed_three_markers':
        return colors[:3]
    if rival == 'first_marker_fill':
        return colors[:1]
    if rival == 'last_marker_fill':
        return colors[-1:]
    if rival == 'stop_diagonal_at_first_zero':
        result = []
        for i in range(min(info['height'], info['width'])):
            v = grid[i][i]
            if v == 0:
                break
            if v != 1:
                result.append(v)
        return result
    return colors


def predict(grid, rule='rings', rival='intended'):
    """Return an independently derived diagnostic prediction, not a label."""
    if rule not in ('rings', 'ring_area_fill'):
        raise ValueError('unknown rule')
    if rival != 'intended' and rival not in RIVALS:
        raise ValueError('unknown rival')
    if rival == 'other_setting':
        return predict(grid, 'ring_area_fill' if rule == 'rings' else 'rings')
    info = analyze(grid)
    palette = _palette(grid, info, rival)
    output = _paint_rings(grid, palette, info)
    if rule == 'rings' or not palette:
        return output
    color = palette[-1]
    top, left, bottom, right = info['innerbbox']
    points = [(r, c) for r in range(top, bottom+1) for c in range(left, right+1)]
    count = sum(output[r][c] == color for r, c in points)
    ih, iw = bottom-top+1, right-left+1
    ch, cw = max(0, ih-2*(len(palette)-1)), max(0, iw-2*(len(palette)-1))
    metrics = {
        'input_last_color_count': sum(grid[r][c] == color for r, c in points),
        'global_last_color_count': sum(v == color for row in output for v in row),
        'original_interior_area': ih*iw, 'center_width': cw, 'center_height': ch,
        'center_perimeter': max(0, 2*(ch+cw)-4), 'inner_width': iw,
        'inner_height': ih, 'marker_count': len(palette),
        'same_shape_count': len(info['keys']),
    }
    count = metrics.get(rival, count)
    keys = info['keys']
    selected = [key for key in keys if key['area'] == count]
    if rival == 'bbox_area_selector':
        selected = [key for key in keys if key['bbox_area'] == count]
    elif rival in ('smallest_key', 'largest_key', 'middle_key'):
        ordered = sorted(keys, key=lambda k: (k['area'], k['bbox']))
        index = {'smallest_key': 0, 'largest_key': -1, 'middle_key': len(keys)//2}[rival]
        selected = [ordered[index]] if keys else []
    elif rival in ('first_key', 'last_key'):
        selected = keys[:1] if rival == 'first_key' else keys[-1:]
    elif rival in ('nearest_key', 'farthest_key'):
        def distance(key):
            return min(max(top-r, 0, r-bottom)+max(left-c, 0, c-right)
                       for r, c in key['cells'])
        ordered = sorted(keys, key=lambda k: (distance(k), k['bbox']))
        selected = (ordered[:1] if rival == 'nearest_key' else ordered[-1:])
    elif rival in ('fewest_holes', 'most_holes', 'leftmost_key', 'rightmost_key',
                   'topmost_key', 'bottommost_key'):
        scores = {
            'fewest_holes': lambda k: k['bbox_area'] - k['area'],
            'most_holes': lambda k: k['bbox_area'] - k['area'],
            'leftmost_key': lambda k: k['bbox'][1],
            'rightmost_key': lambda k: k['bbox'][3],
            'topmost_key': lambda k: k['bbox'][0],
            'bottommost_key': lambda k: k['bbox'][2],
        }
        # Match the literal Racket rivals: coordinate/hole ties select the
        # first component in original row-major discovery order.
        score = scores[rival]
        extreme = (max if rival in ('most_holes', 'rightmost_key', 'bottommost_key') else min)
        value = extreme((score(k) for k in keys), default=None)
        selected = [k for k in keys if score(k) == value][:1]
    elif rival == 'all_keys':
        selected = keys
    if rival == 'fixed_color_2':
        color = 2
    elif rival == 'minimum_color':
        color = min(info['markerlist'])
    elif rival == 'maximum_color':
        color = max(info['markerlist'])
    for key in selected:
        kt, kl, kb, kr = key['bbox']
        cells = key['cells'] if rival == 'occupied_only' else (
            (r, c) for r in range(kt, kb+1) for c in range(kl, kr+1))
        for r, c in cells:
            if rival != 'holes_only' or grid[r][c] == 0:
                output[r][c] = color
    return output


def active_rivals(rule):
    return ('other_setting',) + PALETTE_RIVALS + (B_RIVALS if rule == 'ring_area_fill' else ())


def teaching_report(train_pairs, query_pairs, rule):
    """Fit on demos only, then measure already selected rivals on queries.

    A prediction error is inconclusive rather than evidence of elimination.
    A fitting rival that agrees with all sampled queries is only observationally
    equivalent on this finite sample, never proof of rule equivalence.
    """
    rows = []
    for name in active_rivals(rule):
        row = {'rival': name, 'demo_fit': True, 'demo_mismatches': [],
               'query_mismatches': [], 'errors': []}
        for i, pair in enumerate(train_pairs):
            try:
                if predict(pair['input'], rule, name) != pair['output']:
                    row['demo_fit'] = False
                    row['demo_mismatches'].append(i)
            except Exception as exc:
                row['demo_fit'] = None
                row['errors'].append({'split': 'train', 'index': i, 'error': repr(exc)})
        if row['demo_fit'] is True:
            for i, pair in enumerate(query_pairs):
                try:
                    if predict(pair['input'], rule, name) != pair['output']:
                        row['query_mismatches'].append(i)
                except Exception as exc:
                    row['errors'].append({'split': 'test', 'index': i, 'error': repr(exc)})
        row['status'] = ('inconclusive' if row['errors'] else
                         'demo_fit_query_mismatch' if row['demo_fit'] and row['query_mismatches'] else
                         'observed_equivalent' if row['demo_fit'] else 'demo_refuted')
        rows.append(row)
    return {'rule': rule, 'rivals': rows,
            'failures': [r['rival'] for r in rows if r['status'] == 'demo_fit_query_mismatch'],
            'inconclusive': [r['rival'] for r in rows if r['status'] == 'inconclusive'],
            'limit': 'Finite named family and sampled queries only; no universal identifiability claim.'}
