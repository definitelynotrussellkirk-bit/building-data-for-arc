"""Local transpose, then recompute same-color components before selection."""
from collections import deque
from pathlib import Path

SELECTIONS = ('all', 'largest', 'smallest')
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
if not CANONICAL.startswith('(rule!') or not CANONICAL.endswith(')'):
    raise ValueError('Expected the exact selected canonical resource')
CANONICAL_BODY = CANONICAL[len('(rule!'):-1].strip()


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'selection'}
            or type(settings['selection']) is not str or settings['selection'] not in SELECTIONS):
        raise ValueError('settings must be exactly selection=all,largest,or smallest')
    return {'selection': settings['selection']}


def components(grid, *, diagonal=False, colorblind=False):
    """Fresh four-connected monochromatic components in row-major order."""
    height, width = len(grid), len(grid[0])
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    steps = ((-1,0),(0,1),(1,0),(0,-1))
    if diagonal: steps += ((-1,-1),(-1,1),(1,-1),(1,1))
    result = []
    while remaining:
        start = min(remaining); color = grid[start[0]][start[1]]
        cells = {start}; remaining.remove(start); queue = deque([start])
        while queue:
            r,c = queue.popleft()
            for dr,dc in steps:
                p = (r+dr,c+dc)
                if p in remaining and (colorblind or grid[p[0]][p[1]] == color):
                    remaining.remove(p); cells.add(p); queue.append(p)
        r0,c0 = min(r for r,c in cells),min(c for r,c in cells)
        r1,c1 = max(r for r,c in cells),max(c for r,c in cells)
        shape = [[grid[r][c] if (r,c) in cells else 0 for c in range(c0,c1+1)]
                 for r in range(r0,r1+1)]
        result.append({'cells':cells,'color':color,'bbox':(r0,c0,r1,c1),'shape':shape})
    return result


def validate_grid(grid):
    if (type(grid) is not list or not 8 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 8 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('grid must be rectangular8..30 with exact integer colors0..9')
    objects = components(grid)
    if not 2 <= len(objects) <= 24:
        raise ValueError('need2..24 source components')
    owner = {p:i for i,obj in enumerate(objects) for p in obj['cells']}
    destinations = []; used = set()
    for i,obj in enumerate(objects):
        for r,c in obj['cells']:
            if any((r+dr,c+dc) in owner and owner[(r+dr,c+dc)] != i
                   for dr,dc in ((-1,0),(0,1),(1,0),(0,-1))):
                raise ValueError('source components must have orthogonal clearance')
        r0,c0,_,_ = obj['bbox']
        target = {(r0+c-c0,c0+r-r0) for r,c in obj['cells']}
        if any(not(0 <= r < len(grid) and 0 <= c < len(grid[0])) for r,c in target):
            raise ValueError('local transpose must not clip')
        if used.intersection(target):
            raise ValueError('transposed destinations must not overlap')
        used.update(target); destinations.append(target)
    return {'components':objects, 'destinations':destinations}


def transformed(grid):
    info = validate_grid(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for obj, target in zip(info['components'],info['destinations']):
        for r,c in target: output[r][c] = obj['color']
    return output


def selected(grid, selection):
    if selection == 'all': return [row[:] for row in grid]
    if selection not in ('largest','smallest'): raise ValueError('unknown selection')
    objects = components(grid)
    if not objects: return [row[:] for row in grid]
    best = (max if selection == 'largest' else min)(len(obj['cells']) for obj in objects)
    output = [[0] * len(grid[0]) for _ in grid]
    for obj in objects:
        if len(obj['cells']) == best:
            for r,c in obj['cells']: output[r][c] = grid[r][c]
    return output


def apply(grid, settings):
    selection = parse_settings(settings)['selection']
    return selected(transformed(grid),selection)


def selection_body(expression, selection, *, connectivity='four', score='area', ties='all'):
    """Racket selector and narrowly named executable audit alternatives."""
    if selection == 'all': return expression
    if selection not in ('largest','smallest'): raise ValueError('unknown selection')
    groups = {'four':'(objects stage 0)', 'eight':'(objects-8 stage 0)',
              'colorblind_four':'''(objects (grid-from-fn (rows stage) (cols stage)
                (lambda (r c) (if (= (at stage r c) 0) 0 1))) 0)'''}[connectivity]
    scoring = {'area':'(obj-size obj)', 'bbox':'(* (obj-h obj) (obj-w obj))',
               'color_total':'(length (find-color stage (obj-color obj)))'}[score]
    chosen = {'all':'eligible', 'first':'(list (first eligible))', 'last':'(list (last eligible))'}[ties]
    extreme = 'max' if selection == 'largest' else 'min'
    return f'''(let* ((stage {expression}) (groups {groups}))
      (if (empty? groups) stage
        (let* ((score (lambda (obj) {scoring}))
               (best (apply {extreme} (map score groups)))
               (eligible (filter (lambda (obj) (= (score obj) best)) groups)))
          (for*/fold ((out (empty-grid (rows stage) (cols stage) 0)))
                     ((obj (in-list {chosen})) (p (in-list (obj-cells obj))))
            (set-cell out (first p) (second p) (at stage (first p) (second p)))))))'''


def program(settings):
    selection = parse_settings(settings)['selection']
    if selection == 'all': return CANONICAL
    return '(rule! (lambda (g) ' + selection_body(CANONICAL_BODY,selection) + '))'


def local_body(transform='transpose', *, condition='#t', connectivity='four'):
    transforms = {'identity':('dr','dc'), 'transpose':('dc','dr'),
                  'cw':('dc','(- h 1 dr)'), 'half_turn':('(- h 1 dr)','(- w 1 dc)'),
                  'ccw':('(- w 1 dc)','dr'), 'flip_lr':('dr','(- w 1 dc)'),
                  'flip_ud':('(- h 1 dr)','dc'), 'anti_transpose':('(- w 1 dc)','(- h 1 dr)')}
    rr,cc = transforms[transform]
    objects = '(objects g 0)' if connectivity == 'four' else '(objects-8 g 0)'
    return f'''(for/fold ((out (empty-grid (rows g) (cols g) 0))) ((obj (in-list {objects})))
      (let* ((r0 (obj-r1 obj)) (c0 (obj-c1 obj)) (h (obj-h obj)) (w (obj-w obj))
             (cells (map (lambda (p) (let ((dr (- (first p) r0)) (dc (- (second p) c0)))
                (if {condition} (list (+ r0 {rr}) (+ c0 {cc})) p))) (obj-cells obj))))
        (paint-cells out cells (obj-color obj))))'''


def wrong_order_program(settings):
    selection = parse_settings(settings)['selection']
    pre = selection_body('g',selection)
    return f'(rule! (lambda (g) (let ((g {pre})) {CANONICAL_BODY})))'


def rivals(settings):
    selection = parse_settings(settings)['selection']
    def finish(body, **kwargs):
        return '(rule! (lambda (g) ' + selection_body(body,selection,**kwargs) + '))'
    menu = {'skip_local_transpose': finish('g'),
            'global_transpose': finish('(transpose g)')}
    for transform in ('cw','half_turn','ccw','flip_lr','flip_ud','anti_transpose'):
        menu['local_' + transform] = finish(local_body(transform))
    for name,condition in {
        'skip_three_cell_objects':'(not (= (obj-size obj) 3))',
        'extent_at_most_three':'(<= (max h w) 3)',
        'tall_objects_only':'(> h w)',
        'max_color_only':'(= (obj-color obj) (apply max (map obj-color (objects g 0))))',
        'min_color_only':'(= (obj-color obj) (apply min (map obj-color (objects g 0))))'
    }.items():
        menu[name] = finish(local_body(condition=condition))
    menu['source_eight_connectivity'] = finish(local_body(connectivity='eight'))
    first_anchor = local_body().replace('(c0 (obj-c1 obj))',
        '(c0 (second (first (obj-cells obj))))')
    menu['anchor_first_occupied_cell'] = finish(first_anchor)
    retain = f'''(let ((stage {CANONICAL_BODY}))
      (grid-from-fn (rows g) (cols g) (lambda (r c)
        (if (= (at stage r c) 0) (at g r c) (at stage r c)))))'''
    menu['retain_original_cells'] = finish(retain)
    in_place = local_body().replace('(out (empty-grid (rows g) (cols g) 0))', '(out g)')
    in_place = in_place.replace('(paint-cells out cells (obj-color obj))',
        '(paint-cells (paint-cells out (obj-cells obj) 0) cells (obj-color obj))')
    menu['erase_and_paint_in_place'] = finish(in_place)
    by_color = '''(for/fold ((out (empty-grid (rows g) (cols g) 0))) ((color (in-range 1 10)))
      (let ((cells (find-color g color))) (if (empty? cells) out
        (let* ((bb (bbox-of-cells cells)) (r0 (first bb)) (c0 (second bb)))
          (paint-cells out (map (lambda (p) (list (+ r0 (- (second p) c0))
                                               (+ c0 (- (first p) r0)))) cells) color)))))'''
    menu['transpose_whole_color'] = finish(by_color)
    if selection != 'all':
        menu.update({'select_before_transpose':wrong_order_program(settings),
                     'post_eight_connectivity':finish(CANONICAL_BODY,connectivity='eight'),
                     'post_colorblind_four':finish(CANONICAL_BODY,connectivity='colorblind_four'),
                     'bbox_area_ranking':finish(CANONICAL_BODY,score='bbox'),
                     'total_color_ranking':finish(CANONICAL_BODY,score='color_total'),
                     'first_tie_only':finish(CANONICAL_BODY,ties='first'),
                     'last_tie_only':finish(CANONICAL_BODY,ties='last')})
    return menu
