"""Topmost-column survivors, optionally filtered by their own color plurality.

Python values are claims. Native qualification and audit.py obtain authoritative
labels by executing the exact Racket program in the protected reference runtime.
"""
from collections import Counter
from pathlib import Path

MODES = ('all', 'modal_color')
BACKGROUND = 0


def parse_settings(settings):
    if type(settings) is not dict:
        raise TypeError('settings must be an exact dict')
    if set(settings) != {'survivor_filter'}:
        raise ValueError('settings require only survivor_filter')
    mode = settings['survivor_filter']
    if type(mode) is not str or mode not in MODES:
        raise ValueError('survivor_filter must be all or modal_color')
    return mode


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 exact-list rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular exact lists')
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError('cells must be exact integer colors 0..9')
    return len(grid), width


def trace(grid, mode):
    height, width = validate_grid(grid)
    parse_settings({'survivor_filter': mode})
    tops = []
    for column in range(width):
        for row in range(height):
            if grid[row][column]:
                tops.append([row, column, grid[row][column]])
                break
    counts = Counter(cell[2] for cell in tops)
    largest = max(counts.values(), default=0)
    selected = sorted(color for color, count in counts.items()
                      if mode == 'all' or count == largest)
    output = [[0] * width for _ in range(height)]
    for row, column, color in tops:
        if color in selected:
            output[row][column] = color
    return {'survivors': tops, 'histogram': dict(sorted(counts.items())),
            'selected_colors': selected, 'output': output}


def apply(grid, mode):
    return trace(grid, mode)['output']


def _selected_cells(selection):
    if selection == 'all':
        return 'all-cells'
    if selection == 'left_row':
        return '''(apply append (for/list ((r (in-range h)))
          (let ((hits (filter (lambda (c) (not (= (at g r c) 0))) (range 0 w))))
            (if (empty? hits) (list) (list (list r (first hits) (at g r (first hits))))))))'''
    if selection == 'global_top':
        return '''(if (empty? all-cells) (list)
          (filter (lambda (p) (= (first p) (apply min (map first all-cells)))) all-cells))'''
    chosen = {'top': '(list (first hits))', 'bottom': '(list (last hits))',
              'top_two': '(take hits (min 2 (length hits)))',
              'erase_one_bottom': '(if (= (length hits) 1) hits (take hits (- (length hits) 1)))'}[selection]
    return f'''(apply append (for/list ((c (in-range w)))
      (let ((hits (filter (lambda (r) (not (= (at g r c) 0))) (range 0 h))))
        (if (empty? hits) (list)
          (map (lambda (r) (list r c (at g r c))) {chosen})))))'''


def variant_program(*, selection='top', filter_mode='modal_color', count_source='selected',
                    tie='all', output_scope='selected', row_mode='in_place', paint_color=None):
    """Small total executable counterfactuals for private teaching/witness audits."""
    choices = {'selection': (selection, ('top', 'bottom', 'top_two', 'erase_one_bottom', 'all', 'left_row', 'global_top')),
               'filter_mode': (filter_mode, ('all', 'modal_color', 'repeated', 'majority', 'rarest')),
               'count_source': (count_source, ('selected', 'original')),
               'tie': (tie, ('all', 'min', 'max', 'first', 'none')),
               'output_scope': (output_scope, ('selected', 'original')),
               'row_mode': (row_mode, ('in_place', 'top', 'bottom'))}
    for name, (value, allowed) in choices.items():
        if type(value) is not str or value not in allowed:
            raise ValueError(f'invalid {name}')
    if paint_color is not None and (type(paint_color) is not int or not 1 <= paint_color <= 9):
        raise ValueError('paint_color must be None or an integer in 1..9')
    counted = 'selected' if count_source == 'selected' else 'all-cells'
    candidates = 'selected' if output_scope == 'selected' else 'all-cells'
    score_condition = {
        'all': '(> n 0)',
        'modal_color': '(= n largest)',
        'repeated': '(>= n 2)',
        'majority': '(> (* 2 n) (length counted))',
        'rarest': '(= n smallest)',
    }[filter_mode]
    ties = {
        'all': 'eligible',
        'min': '(if (empty? eligible) (list) (list (first eligible)))',
        'max': '(if (empty? eligible) (list) (list (last eligible)))',
        'none': '(if (= (length eligible) 1) eligible (list))',
        'first': '''(if (empty? eligible) (list)
           (list (third (first (filter (lambda (p) (member (third p) eligible)) counted)))))''',
    }[tie]
    row = {'in_place': '(first p)', 'top': '0', 'bottom': '(- h 1)'}[row_mode]
    color = '(third p)' if paint_color is None else str(paint_color)
    return f'''(rule! (lambda (g)
      (let* ((h (rows g)) (w (cols g))
             (all-cells (for*/list ((r (in-range h)) (c (in-range w))
                          #:when (not (= (at g r c) 0))) (list r c (at g r c))))
             (selected {_selected_cells(selection)})
             (counted {counted})
             (counts (for/list ((k (in-range 1 10)))
                       (length (filter (lambda (p) (= (third p) k)) counted))))
             (positive (filter (lambda (n) (> n 0)) counts))
             (largest (apply max (cons 0 counts)))
             (smallest (if (empty? positive) 0 (apply min positive)))
             (eligible (filter (lambda (k)
                         (let ((n (list-ref counts (- k 1))))
                           (and (> n 0) {score_condition}))) (range 1 10)))
             (colors {ties}))
        (for/fold ((out (empty-grid h w 0))) ((p {candidates}))
          (if (member (third p) colors)
            (set-cell out {row} (second p) {color}) out)))))'''


def program(settings):
    mode = parse_settings(settings)
    if mode == 'all':
        return Path(__file__).with_name('canonical.rkt').read_text()
    return variant_program()


def rivals(settings):
    mode = parse_settings(settings)
    menu = {
        'bottommost': variant_program(selection='bottom', filter_mode=mode),
        'keep_top_two': variant_program(selection='top_two', filter_mode=mode),
        'erase_one_bottom': variant_program(selection='erase_one_bottom', filter_mode=mode),
        'leftmost_per_row': variant_program(selection='left_row', filter_mode=mode),
        'global_top_row': variant_program(selection='global_top', filter_mode=mode),
        'gravity_to_top': variant_program(filter_mode=mode, row_mode='top'),
        'paint_fixed_one': variant_program(filter_mode=mode, paint_color=1),
        'skip_column_selection': variant_program(selection='all', filter_mode=mode),
    }
    if mode == 'modal_color':
        menu.update({
            'count_original_colors': variant_program(count_source='original'),
            'paint_all_cells_of_winning_colors': variant_program(output_scope='original'),
            'tie_lowest_color': variant_program(tie='min'),
            'tie_highest_color': variant_program(tie='max'),
            'tie_first_color': variant_program(tie='first'),
            'require_unique_mode': variant_program(tie='none'),
            'keep_all_repeated_colors': variant_program(filter_mode='repeated'),
            'require_strict_majority': variant_program(filter_mode='majority'),
            'keep_rarest_color': variant_program(filter_mode='rarest'),
        })
    return menu
