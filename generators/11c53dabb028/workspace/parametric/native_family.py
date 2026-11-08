"""Color-preserving component extraction followed by retained negative tiling."""
from functools import lru_cache
import importlib.util
from pathlib import Path

FRAMES = ('input', 'largest_component')
BACKGROUND = 0
HERE = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def _prototype():
    spec = importlib.util.spec_from_file_location('_retained_tile_11c53dabb028', HERE / 'prototype.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_settings(settings):
    if type(settings) is not dict:
        raise TypeError('settings must be an exact dict')
    if set(settings) != {'input_frame', 'vertical_repeats', 'horizontal_repeats'}:
        raise ValueError('settings require exactly input_frame and both repeat counts')
    if type(settings['input_frame']) is not str or settings['input_frame'] not in FRAMES:
        raise ValueError('input_frame must be input or largest_component')
    for name in ('vertical_repeats', 'horizontal_repeats'):
        if type(settings[name]) is not int or settings[name] not in (1, 2):
            raise ValueError(name + ' must be exact integer1 or2')
    return dict(settings)


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 15:
        raise ValueError('grid must have1..15 exact-list rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 15:
        raise ValueError('grid must have1..15 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular exact lists')
    values = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in values):
        raise ValueError('cells must be exact integer0..9')
    if not any(values) or 0 not in values:
        raise ValueError('raw input requires both zero and nonzero cells')
    return len(grid), width


def components(grid, connectivity=4, monochrome=False):
    height, width = validate_grid(grid)
    if type(connectivity) is not int or connectivity not in (4, 8) or type(monochrome) is not bool:
        raise ValueError('components require connectivity4 or8 and a boolean monochrome flag')
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    result = []
    steps = [(-1, 0), (0, -1), (0, 1), (1, 0)]
    if connectivity == 8:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, found = [start], [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in steps:
                nxt = (row + dr, col + dc)
                if nxt in remaining and (not monochrome or grid[nxt[0]][nxt[1]] == grid[start[0]][start[1]]):
                    remaining.remove(nxt)
                    found.append(nxt)
                    stack.append(nxt)
        result.append(sorted(found))
    return result


def intermediate(grid, frame='input'):
    height, width = validate_grid(grid)
    if frame not in FRAMES:
        raise ValueError('unknown input frame')
    if frame == 'input':
        cells = [(r, c) for r in range(height) for c in range(width) if grid[r][c]]
        return {'grid': [row[:] for row in grid], 'cells': cells,
                'bbox': [0, 0, height - 1, width - 1], 'component_size': None}
    # Components are discovered by their actual first row-major occupied cell;
    # Python max keeps the first component when sizes tie, as Racket pick-max does.
    selected = max(components(grid), key=len)
    r0, r1 = min(r for r, c in selected), max(r for r, c in selected)
    c0, c1 = min(c for r, c in selected), max(c for r, c in selected)
    cropped = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for row, col in selected:
        cropped[row - r0][col - c0] = grid[row][col]
    return {'grid': cropped, 'cells': selected, 'bbox': [r0, c0, r1, c1],
            'component_size': len(selected)}


def trace(grid, settings):
    settings = parse_settings(settings)
    frame = intermediate(grid, settings['input_frame'])
    tile = frame['grid']
    selected_color = next(v for row in tile for v in row if v)
    output = _prototype().tile_output(tile, vertical_repeats=settings['vertical_repeats'],
                                      horizontal_repeats=settings['horizontal_repeats'])
    return {'frame': frame, 'selected_color': selected_color, 'output': output}


def apply(grid, settings):
    return trace(grid, settings)['output']


def _frame_expression(frame, component_selector='largest', connectivity=4,
                      monochrome=False, retain_inside_bbox=False, binary_colors=False):
    if frame == 'input':
        return 'g'
    source = 'g' if monochrome else '(build-grid (rows g) (cols g) (r c) (if (= (at g r c) 0) 0 1))'
    discover = 'objects' if connectivity == 4 else 'objects-8'
    pick = {
        'largest': '(pick-max objs obj-size)',
        'smallest': '(pick-min objs obj-size)',
        'first': '(first objs)',
        'last': '(last objs)',
        'last_tie': '(pick-max (reverse objs) obj-size)',
        'largest_bbox': '(pick-max objs (lambda (o) (* (obj-h o) (obj-w o))))',
        'leftmost_tie': '(pick-max (sort objs (lambda (a b) (< (obj-c1 a) (obj-c1 b)))) obj-size)',
    }[component_selector]
    value = '1' if binary_colors else '(at g rr cc)'
    cell = value if retain_inside_bbox else f'(if (member (list rr cc) chosen) {value} 0)'
    return f'''(let* ((objs ({discover} {source} 0))
                       (winner {pick}) (chosen (obj-cells winner))
                       (r0 (obj-r1 winner)) (c0 (obj-c1 winner)))
                  (build-grid (obj-h winner) (obj-w winner) (r c)
                    (let ((rr (+ r r0)) (cc (+ c c0))) {cell})))'''


def variant_program(settings, *, component_selector='largest', connectivity=4,
                    monochrome=False, retain_inside_bbox=False, binary_colors=False,
                    color_selector='first', original_color=False, layout='tile', invert=True):
    """Total executable private rivals and causal ablations on the raw grammar."""
    settings = parse_settings(settings)
    if component_selector not in ('largest', 'smallest', 'first', 'last', 'last_tie', 'largest_bbox', 'leftmost_tie'):
        raise ValueError('unknown component selector')
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError('connectivity must be4 or8')
    if any(type(v) is not bool for v in (monochrome, retain_inside_bbox, binary_colors, original_color, invert)):
        raise ValueError('variant switches must be booleans')
    selectors = ('first', 'last', 'minimum', 'maximum', 'mode', 'median', 'column_major', 'second_frequency', 'left_edge_last')
    if color_selector not in selectors or layout not in ('tile', 'scale', 'reflect', 'square_period'):
        raise ValueError('unknown tile selector or layout')
    frame = _frame_expression(settings['input_frame'], component_selector, connectivity,
                               monochrome, retain_inside_bbox, binary_colors)
    color_grid = 'g' if original_color else 'tile'
    values = '''(filter (lambda (v) (not (= v 0)))
                   (flatmap (lambda (r) (map (lambda (c) (at color-grid r c))
                     (range 0 (cols color-grid)))) (range 0 (rows color-grid))))'''
    selection = {
        'first': '(first values)', 'last': '(last values)', 'minimum': '(apply min values)',
        'maximum': '(apply max values)',
        'mode': '(pick-max (sort (remove-duplicates values) <) (lambda (k) (length (filter (lambda (v) (= v k)) values))))',
        'median': '(list-ref (sort (remove-duplicates values) <) (quotient (length (remove-duplicates values)) 2))',
        'second_frequency': '''(let ((ranked (sort (remove-duplicates values)
                                (lambda (a b) (> (length (filter (lambda (v) (= v a)) values))
                                                 (length (filter (lambda (v) (= v b)) values)))))))
                                (list-ref ranked (min 1 (- (length ranked) 1))))''',
        'column_major': '''(first (filter (lambda (v) (not (= v 0)))
                              (flatmap (lambda (c) (map (lambda (r) (at color-grid r c))
                                 (range 0 (rows color-grid)))) (range 0 (cols color-grid)))))''',
        'left_edge_last': '''(first (filter (lambda (v) (not (= v 0)))
                               (flatmap (lambda (r) (map (lambda (c) (at color-grid r c))
                                 (append (range 1 (cols color-grid)) (list 0)))) (range 0 (rows color-grid)))))''',
    }[color_selector]
    vertical, horizontal = settings['vertical_repeats'], settings['horizontal_repeats']
    rr, cc = '(mod r h)', '(mod c w)'
    if layout == 'scale':
        rr, cc = f'(quotient r {vertical})', f'(quotient c {horizontal})'
    elif layout == 'reflect':
        rr = '(if (>= r h) (- h 1 (mod r h)) (mod r h))'
        cc = '(if (>= c w) (- w 1 (mod c w)) (mod c w))'
    elif layout == 'square_period':
        cc = '(mod (mod c h) w)'
    condition = '(= v 0)' if invert else '(not (= v 0))'
    return f'''(rule! (lambda (g)
      (let* ((tile {frame}) (h (rows tile)) (w (cols tile))
             (color-grid {color_grid}) (values {values}) (nz {selection}))
        (build-grid (* {vertical} h) (* {horizontal} w) (r c)
          (let ((v (at tile {rr} {cc}))) (if {condition} nz 0))))))'''


def program(settings):
    settings = parse_settings(settings)
    base = _prototype().program_for(settings['vertical_repeats'], settings['horizontal_repeats'])
    if settings['input_frame'] == 'input':
        return base
    from puzzle_generators.rule_wrap import wrap_rule
    frame = _frame_expression('largest_component')
    return f'(rule! (lambda (g) ({wrap_rule(base)} {frame})))'


def rivals(settings):
    settings = parse_settings(settings)
    menu = {'color_' + selector: variant_program(settings, color_selector=selector)
            for selector in ('last', 'minimum', 'maximum', 'mode', 'median', 'column_major', 'second_frequency', 'left_edge_last')}
    menu.update({'scale_instead_of_tile': variant_program(settings, layout='scale'),
                 'reflect_tiles': variant_program(settings, layout='reflect'),
                 'square_period': variant_program(settings, layout='square_period'),
                 'keep_mask_instead_of_invert': variant_program(settings, invert=False)})
    if settings['input_frame'] == 'largest_component':
        menu.update({'component_' + selector: variant_program(settings, component_selector=selector)
                     for selector in ('smallest', 'first', 'last', 'last_tie', 'largest_bbox', 'leftmost_tie')})
        menu.update({'eight_connected': variant_program(settings, connectivity=8),
                     'same_color_components': variant_program(settings, monochrome=True),
                     'raw_bbox_keeps_clutter': variant_program(settings, retain_inside_bbox=True),
                     'render_binary_component': variant_program(settings, binary_colors=True),
                     'color_from_original_input': variant_program(settings, original_color=True)})
    return menu
