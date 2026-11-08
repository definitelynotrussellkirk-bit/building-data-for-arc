"""Native completion of the existing projection-reach prototype."""
from collections import Counter
import importlib.util
from pathlib import Path

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
_selected, _, _ = load_selected_generator('48bda9528e71', root=HERE.parents[3])
_spec = importlib.util.spec_from_file_location('_native_projection_prototype', HERE / 'prototype.py')
_prototype = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_prototype)
MODES = _prototype.SETTINGS
BACKGROUND = 8
CANONICAL = (HERE / 'canonical.rkt').read_text(encoding='utf-8')


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'projection_reach'}
            or type(settings['projection_reach']) is not str
            or settings['projection_reach'] not in MODES):
        raise ValueError('settings must contain exactly projection_reach=one_step or to_boundary')
    return {'projection_reach': settings['projection_reach']}


def validate_grid(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or any(type(row) is not list or len(row) != len(grid)
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('need an exact-integer square ARC grid of size5..30')
    cells = _prototype._occupied(grid)
    counts = Counter(v for row in grid for v in row if v != BACKGROUND)
    if not 2 <= len(counts) <= 3 or not 7 <= len(cells) <= (len(grid)**2 - 1) // 2:
        raise ValueError('need two or three foreground colors and occupied area7..floor((n*n-1)/2)')
    if not _selected._is_connected(cells) or not _selected._is_orthogonally_convex(cells):
        raise ValueError('occupied shape must be four-connected and contiguous in every active row and column')
    if (max(r for r, c in cells) - min(r for r, c in cells) < 2
            or max(c for r, c in cells) - min(c for r, c in cells) < 2):
        raise ValueError('occupied shape must span at least three rows and columns')
    rare = _prototype._rare_color(grid)
    interior = _selected._interior_cells(cells)
    if not {(r, c) for r, c in cells if grid[r][c] == rare} <= interior:
        raise ValueError('every rare-color cell must have all four cardinal neighbors occupied')
    if len(_selected._extent_positions(cells, len(grid), len(grid))) < 4:
        raise ValueError('need at least four in-bounds extent markers')
    row_extents = {r: (min(c for rr, c in cells if rr == r), max(c for rr, c in cells if rr == r))
                   for r in sorted({r for r, c in cells})}
    col_extents = {c: (min(r for r, cc in cells if cc == c), max(r for r, cc in cells if cc == c))
                   for c in sorted({c for r, c in cells})}
    return {'cells': cells, 'rare_color': rare, 'counts': counts, 'interior': interior,
            'row_extents': row_extents, 'col_extents': col_extents}


def apply(grid, settings):
    mode = parse_settings(settings)['projection_reach']
    validate_grid(grid)
    return _prototype.project_extents(grid, mode)


def program(settings):
    mode = parse_settings(settings)['projection_reach']
    return CANONICAL if mode == 'one_step' else _prototype.program_for(mode)


def _replace(source, needle, replacement):
    if source.count(needle) != 1:
        raise ValueError('prototype substitution site must be unique: ' + needle)
    return source.replace(needle, replacement, 1)


COLOR_SELECTION = '''(car (sort (hash-keys freq)
                      (lambda (a b)
                        (< (hash-ref freq a 0)
                           (hash-ref freq b 0)))))'''
MOST_COMMON = '(car (sort (hash-keys freq) (lambda (a b) (> (hash-ref freq a 0) (hash-ref freq b 0)))))'

_HULL = '''(let* ((points (map (lambda (cell) (list (first cell) (second cell))) cells))
                  (hull (convex-hull points))
                  (edges (map list hull (append (rest hull) (list (first hull))))))
             (for*/list ((r (range 0 hh)) (c (range 0 ww))
               #:when (andmap (lambda (edge)
                 (let ((a (first edge)) (b (second edge)))
                   (>= (- (* (- (first b) (first a)) (- c (second a)))
                          (* (- (second b) (second a)) (- r (first a)))) 0))) edges))
               (list r c inner-color)))'''


def variant_program(settings, *, bbox_extents=False, color_expression=None,
                    geometry='all', keep_source=False, row_marks=None, col_marks=None):
    """Reuse the retained Racket builder for explicit spatial counterfactuals."""
    mode = parse_settings(settings)['projection_reach']
    source = _prototype.program_for(mode)
    if row_marks is not None or col_marks is not None:
        rows, cols = _marks(mode)
        source = _prototype._program_body(rows if row_marks is None else row_marks,
                                         cols if col_marks is None else col_marks)
    if color_expression is not None:
        source = _replace(source, COLOR_SELECTION, color_expression)
    if geometry == 'rare':
        expression = '(filter (lambda (cell) (= (third cell) inner-color)) cells)'
    elif geometry == 'common':
        expression = f'(filter (lambda (cell) (= (third cell) {MOST_COMMON})) cells)'
    elif geometry == 'convex':
        expression = _HULL
    elif geometry == 'all':
        expression = 'cells'
    else:
        raise ValueError('unknown projection geometry')
    if geometry != 'all':
        source = _replace(source, '(result (make-hash)))',
                          f'(projection-cells {expression})\n         (result (make-hash)))')
        for axis, coordinate in (('first', 'r'), ('second', 'c')):
            needle = f'(filter (lambda (cell) (= ({axis} cell) {coordinate})) cells)'
            source = _replace(source, needle, needle[:-6] + 'projection-cells)')
    if bbox_extents:
        cells = 'cells' if geometry == 'all' else 'projection-cells'
        for op, axis, seq in (('min', 'second', 'row-cs'), ('max', 'second', 'row-cs'),
                              ('min', 'first', 'col-rs'), ('max', 'first', 'col-rs')):
            source = _replace(source, f'({op}-list {seq})', f'({op}-list (map {axis} {cells}))')
    if keep_source:
        source = _replace(source, '(hash-set! result (list r c) bg)',
                          '(hash-set! result (list r c) (at g r c))')
    return source


def _marks(mode, *, distance=1, endpoints=False):
    if endpoints:
        return ('(when (> left 0) (hash-set! result (list r 0) inner-color)) '
                '(when (< right (- ww 1)) (hash-set! result (list r (- ww 1)) inner-color))',
                '(when (> top 0) (hash-set! result (list 0 c) inner-color)) '
                '(when (< bot (- hh 1)) (hash-set! result (list (- hh 1) c) inner-color))')
    if mode == 'one_step':
        return (f'(when (>= (- left {distance}) 0) (hash-set! result (list r (- left {distance})) inner-color)) '
                f'(when (< (+ right {distance}) ww) (hash-set! result (list r (+ right {distance})) inner-color))',
                f'(when (>= (- top {distance}) 0) (hash-set! result (list (- top {distance}) c) inner-color)) '
                f'(when (< (+ bot {distance}) hh) (hash-set! result (list (+ bot {distance}) c) inner-color))')
    return ('(for ((mark-c (range 0 left))) (hash-set! result (list r mark-c) inner-color)) '
            '(for ((mark-c (range (+ right 1) ww))) (hash-set! result (list r mark-c) inner-color))',
            '(for ((mark-r (range 0 top))) (hash-set! result (list mark-r c) inner-color)) '
            '(for ((mark-r (range (+ bot 1) hh))) (hash-set! result (list mark-r c) inner-color))')


def rivals(settings):
    rows, cols = _marks('one_step', distance=2)
    edge_rows, edge_cols = _marks('to_boundary', endpoints=True)
    menu = {
        'global_bbox_extents': variant_program(settings, bbox_extents=True),
        'convexify_then_project': variant_program(settings, geometry='convex'),
        'rare_color_geometry_only': variant_program(settings, geometry='rare'),
        'most_common_geometry_only': variant_program(settings, geometry='common'),
        'rows_only': variant_program(settings, col_marks='(void)'),
        'columns_only': variant_program(settings, row_marks='(void)'),
        'canvas_edge_endpoints': variant_program(settings, row_marks=edge_rows, col_marks=edge_cols),
        'distance_two_markers': variant_program(settings, row_marks=rows, col_marks=cols),
        'keep_original_shape': variant_program(settings, keep_source=True),
        'most_common_color': variant_program(settings, color_expression=MOST_COMMON),
        'lowest_numeric_color': variant_program(settings, color_expression='(min-list (hash-keys freq))'),
        'highest_numeric_color': variant_program(settings, color_expression='(max-list (hash-keys freq))'),
        'canvas_center_color': variant_program(settings, color_expression='(at g (/ hh 2) (/ ww 2))'),
        'first_occupied_color': variant_program(settings, color_expression='(third (first cells))'),
    }
    menu.update({f'fixed_color_{color}': variant_program(settings, color_expression=str(color))
                 for color in range(10) if color != BACKGROUND})
    menu.update(retained_rivals(settings))
    # Keep the opposite enclosure selector refuted when repairing its observed
    # highest-color counterpart; changing one palette alone can reverse a hole.
    menu['lowest_fully_enclosed'] = variant_program(settings,
        color_expression=_replace(EXPRESSIONS['highest_fully_enclosed'], '(> a b)', '(< a b)'))
    return menu


# Exact programs preserved from the independent color-selection review.
INNER_BINDINGS = '''(points (map (lambda (cell) (list (first cell) (second cell))) cells))
 (inner? (lambda (cell) (andmap (lambda (d)
   (member (list (+ (first cell) (first d)) (+ (second cell) (second d))) points))
   (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))))
 (inside-count (lambda (color) (count-where (lambda (cell)
   (and (= (third cell) color) (inner? cell))) cells)))'''

EXPRESSIONS = {
 'most_components_numeric_tie': '''(let* ((components (objects g 8))
  (score (lambda (color) (count-where (lambda (obj) (= (obj-color obj) color)) components))))
  (car (sort (hash-keys freq) (lambda (a b)
   (if (= (score a) (score b)) (< a b) (> (score a) (score b)))))))''',
 'fewest_interior_cells': f'''(let* ({INNER_BINDINGS})
  (car (sort (hash-keys freq) (lambda (a b)
   (if (= (inside-count a) (inside-count b)) (< a b) (< (inside-count a) (inside-count b)))))))''',
 'highest_fully_enclosed': f'''(let* ({INNER_BINDINGS}
  (enclosed? (lambda (color) (= (inside-count color) (hash-ref freq color 0)))))
  (car (sort (hash-keys freq) (lambda (a b)
   (if (equal? (enclosed? a) (enclosed? b)) (> a b) (enclosed? a))))))''',
}


def retained_rivals(settings):
    return {name: variant_program(settings, color_expression=expression)
            for name, expression in EXPRESSIONS.items()}
