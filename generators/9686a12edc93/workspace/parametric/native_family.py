"""Original-input versus evolving-occupancy clearance for endpoint connections.

Python supplies claims and inspectable traces. Protected Racket is label authority.
The selected canonical default is returned byte-for-byte, including color order.
"""
import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parent
CANONICAL = (HOME/'canonical.rkt').read_text()
MODES = ('input', 'painted')
BACKGROUND = 0

# Reuse the reviewed production segment geometry, without importing its sampler
# or the independent probe's reading-order output assumption.
_spec = importlib.util.spec_from_file_location('_endpoint_geometry_9686a12edc93', HOME.parents[1]/'generator.py')
_geometry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_geometry)
segment = _geometry._segment


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'clearance_stage'}
            or type(settings['clearance_stage']) is not str
            or settings['clearance_stage'] not in MODES):
        raise ValueError('settings must be exactly clearance_stage=input|painted')
    return dict(settings)


def validate_grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 3 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)
            or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)):
        raise ValueError('grid must be a rectangular exact-list integer0..9 matrix with axes3..30')
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r,c))
    pairs = []
    for color, cells in sorted(by_color.items()):
        if len(cells) == 2:
            path = segment(*cells)
            if path:
                pairs.append({'color':color, 'cells':tuple(cells), 'path':path,
                              'blockers':tuple((r,c) for r,c in path[1:-1] if grid[r][c]),
                              'orientation':'horizontal' if cells[0][0] == cells[1][0] else 'vertical'})
    return {'height':len(grid), 'width':len(grid[0]), 'by_color':by_color, 'pairs':pairs}


def trace(grid, settings):
    mode = parse_settings(settings)['clearance_stage']
    info = validate_grid(grid)
    state = [row[:] for row in grid]
    out = [[0]*info['width'] for _ in range(info['height'])]
    steps = []
    for pair in info['pairs']:
        color, path = pair['color'], pair['path']
        surface = grid if mode == 'input' else state
        blockers = [[r,c] for r,c in path[1:-1] if surface[r][c] != 0]
        accepted = not blockers
        if accepted:
            for r,c in path:
                state[r][c] = out[r][c] = color
        steps.append({'color':color, 'path':[list(p) for p in path],
                      'input_blockers':[list(p) for p in pair['blockers']],
                      'blockers':blockers, 'accepted':accepted,
                      'occupied_after':[[r,c,value] for r,row in enumerate(state)
                                        for c,value in enumerate(row) if value]})
    return {'order':sorted(info['by_color']), 'steps':steps, 'output':out}


def apply(grid, settings):
    return trace(grid, settings)['output']


def program(settings):
    mode = parse_settings(settings)['clearance_stage']
    return CANONICAL if mode == 'input' else variant_program(settings)


def variant_program(settings, *, clearance=None, order='ascending',
                    update_rejected=False, keep_input=False, eligibility='exact_two',
                    endpoints=True, minimum_span=2, paint_color=None, orientation='both',
                    memory='all'):
    """Build a complete standalone rule, including private executed ablations."""
    mode = parse_settings(settings)['clearance_stage']
    clearance = mode if clearance is None else clearance
    if type(clearance) is not str or clearance not in ('input','painted','output','ignore'):
        raise ValueError('unknown clearance surface')
    if type(order) is not str or order not in ('ascending','descending','reading','horizontal_first','vertical_first','longest','shortest'):
        raise ValueError('unknown processing order')
    if any(type(value) is not bool for value in (update_rejected,keep_input,endpoints)):
        raise ValueError('private switches require booleans')
    if type(eligibility) is not str or eligibility not in ('exact_two','at_least_two'):
        raise ValueError('unknown pair eligibility')
    if type(minimum_span) is not int or minimum_span not in (2,3):
        raise ValueError('minimum_span must be2or3')
    if paint_color is not None and (type(paint_color) is not int or not 1 <= paint_color <= 9):
        raise ValueError('paint_color must be an exact nonzero ARC color')
    if type(orientation) is not str or orientation not in ('both','horizontal','vertical'):
        raise ValueError('unknown orientation filter')
    if type(memory) is not str or memory not in ('all','last'):
        raise ValueError('memory must be all or last')
    eligible = '(= (length cells) 2)' if eligibility == 'exact_two' else '(>= (length cells) 2)'
    horizontal = '#f' if orientation == 'vertical' else '(= r1 r2)'
    vertical = '#f' if orientation == 'horizontal' else '(= c1 c2)'
    color_order = '(grid-colors g 0)'
    if order == 'descending':
        color_order = '(reverse (grid-colors g 0))'
    elif order != 'ascending':
        keys = {
            'reading':'(let ((p (first (find-color g color)))) (+ (* (first p) 30) (second p)))',
            'horizontal_first':'(+ (* (if (horizontal-path? (path-for color)) 0 1) 10) color)',
            'vertical_first':'(+ (* (if (horizontal-path? (path-for color)) 1 0) 10) color)',
            'longest':'(+ (* -10 (length (path-for color))) color)',
            'shortest':'(+ (* 10 (length (path-for color))) color)',
        }
        color_order = f'(sort (grid-colors g 0) (lambda (x y) (< (order-key x) (order-key y))))'
    key = 'color' if order in ('ascending','descending') else keys[order]
    surface = {'input':'g','painted':'(first acc)','output':'(second acc)'}.get(clearance)
    clear = '#t' if clearance == 'ignore' else f'(all? (lambda (p) (= (at {surface} (first p) (second p)) 0)) body)'
    base = 'g' if keep_input else '(empty-grid (rows g) (cols g) 0)'
    update = '(or accepted (not (null? path)))' if update_rejected else 'accepted'
    remember = '(paint g path color)' if memory == 'last' else '(paint (first acc) path color)'
    draw = 'path' if endpoints else 'body'
    paint = 'color' if paint_color is None else str(paint_color)
    return f'''(rule!
 (let ((dummy 0))
  (define (path-for color)
   (let ((cells (find-color g color)))
    (if {eligible}
     (let* ((a (first cells)) (b (last cells))
            (r1 (first a)) (c1 (second a)) (r2 (first b)) (c2 (second b))
            (path (cond
              ({horizontal} (map (lambda (c) (list r1 c)) (range (min c1 c2) (+ (max c1 c2) 1))))
              ({vertical} (map (lambda (r) (list r c1)) (range (min r1 r2) (+ (max r1 r2) 1))))
              (else (list)))))
      (if (>= (length path) {minimum_span}) path (list)))
     (list))))
  (define (horizontal-path? path)
   (and (not (null? path)) (= (first (first path)) (first (last path)))))
  (define (order-key color) {key})
  (define (paint grid path color)
   (for/fold ((out grid)) ((p (in-list path)))
    (set-cell out (first p) (second p) color)))
  (second
   (for/fold ((acc (list g {base}))) ((color (in-list {color_order})))
    (let* ((path (path-for color))
           (body (if (null? path) (list) (drop-right (rest path) 1)))
           (accepted (and (not (null? path)) {clear})))
     (list (if {update} {remember} (first acc))
           (if accepted (paint (second acc) {draw} {paint}) (second acc))))))))'''


def rivals(settings):
    mode = parse_settings(settings)['clearance_stage']
    menu = {
        'ignore_clearance':variant_program(settings,clearance='ignore'),
        'copy_input_endpoints':variant_program(settings,keep_input=True),
        'output_only_occupancy':variant_program(settings,clearance='output'),
        'nonpair_first_last':variant_program(settings,eligibility='at_least_two'),
        'omit_endpoints':variant_program(settings,endpoints=False),
        'ignore_adjacent_pairs':variant_program(settings,minimum_span=3),
        'horizontal_only':variant_program(settings,orientation='horizontal'),
        'vertical_only':variant_program(settings,orientation='vertical'),
        'constant_color_1':variant_program(settings,paint_color=1),
        'constant_color_9':variant_program(settings,paint_color=9),
    }
    menu.update({'order:'+name:variant_program(settings,order=name)
                 for name in ('descending','reading','horizontal_first','vertical_first','longest','shortest')})
    if mode == 'painted':
        menu['rejected_candidates_also_block'] = variant_program(settings,update_rejected=True)
        menu['last_accepted_memory'] = variant_program(settings,memory='last')
    return menu
