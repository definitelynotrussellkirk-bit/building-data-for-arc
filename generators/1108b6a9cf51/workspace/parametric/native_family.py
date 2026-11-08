"""Infer a reviewed D4 operation, then transfer it forward, inversely or twice."""
from pathlib import Path

from reviewer_support import load_selected_generator

HERE = Path(__file__).resolve().parent
_selected, _, _ = load_selected_generator('1108b6a9cf51', root=HERE.parents[3])
TRANSFORMS = _selected.TRANSFORMS
MODES = ('forward', 'inverse', 'twice')
CANONICAL = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
TERMINAL = '(transform-code c code)'
PREDICATE = '(equal? (transform-code a t) b)'
if CANONICAL.count(TERMINAL) != 1 or CANONICAL.count(PREDICATE) != 1:
    raise ValueError('selected canonical application and inference sites must be unique')


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {'transfer'}
            or type(settings['transfer']) is not str or settings['transfer'] not in MODES):
        raise ValueError('settings must contain exactly transfer=forward, inverse or twice')
    return {'transfer': settings['transfer']}


def validate_grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 9
            or any(type(row) is not list or len(row) != 3 * len(grid) + 2
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('need exact-integer n by (3n+2) grid with n in 3..9')
    n = len(grid)
    separators = (n, 2 * n + 1)
    if any((v == 9) != (c in separators) for row in grid for c, v in enumerate(row)):
        raise ValueError('color 9 is reserved for the two complete separator columns')
    panels = [[row[left:left + n] for row in grid] for left in (0, n + 1, 2 * n + 2)]
    a, b, c = panels
    colors = {v for panel in (a, c) for row in panel for v in row if v}
    if not 2 <= len(colors) <= 8:
        raise ValueError('A and C must jointly use 2..8 nonzero colors')
    for name, panel in (('A', a), ('C', c)):
        if (not any(v == 0 for row in panel for v in row)
                or not any(v for row in panel for v in row)
                or _selected._orbit_size(panel) != 8):
            raise ValueError(f'{name} needs background, content and a full D4 orbit')
    matches = [name for name in TRANSFORMS if _selected._xform(a, name) == b]
    if len(matches) != 1:
        raise ValueError('A and B must identify one unique D4 operation')
    return {'size': n, 'panels': panels, 'inferred': matches[0],
            'code': TRANSFORMS.index(matches[0]) + 1, 'colors': sorted(colors)}


def apply(grid, settings):
    mode = parse_settings(settings)['transfer']
    info = validate_grid(grid)
    name = info['inferred']
    if mode == 'inverse':
        name = {'rotate_cw': 'rotate_ccw', 'rotate_ccw': 'rotate_cw'}.get(name, name)
    result = _selected._xform(info['panels'][2], name)
    return _selected._xform(result, name) if mode == 'twice' else result


def _application(mode, panel='c', code='code'):
    if mode == 'inverse':
        code = f'(let ((selected {code})) (cond [(= selected 2) 4] [(= selected 4) 2] [else selected]))'
    expression = f'(transform-code {panel} {code})'
    return f'(transform-code {expression} {code})' if mode == 'twice' else expression


def variant_program(settings, *, code_expression='code', panel='c', predicate=None,
                    definitions='', terminal=None):
    """Guarded substitutions for the three settings and explicit audit ablations."""
    mode = parse_settings(settings)['transfer']
    result = CANONICAL.replace(TERMINAL, terminal or _application(mode, panel, code_expression), 1)
    if predicate is not None:
        result = result.replace(PREDICATE, predicate, 1)
    if definitions:
        needle = '(define (split-panels grid)'
        if result.count(needle) != 1:
            raise ValueError('canonical definition insertion site must be unique')
        result = result.replace(needle, definitions + '\n    ' + needle, 1)
    return result


def program(settings):
    mode = parse_settings(settings)['transfer']
    return CANONICAL if mode == 'forward' else variant_program(settings)


_BINARY = '''(define (binary-mask grid)
      (grid-from-fn (rows grid) (cols grid)
        (lambda (r c) (if (= (at grid r c) 0) 0 1))))'''
_DOMINANT = '''(define (dominant grid)
      (for/fold ((best 1)) ((color (in-range 2 9)))
        (if (> (length (find-color grid color)) (length (find-color grid best))) color best)))
    (define (dominant-mask grid)
      (let ((color (dominant grid)))
        (grid-from-fn (rows grid) (cols grid)
          (lambda (r c) (if (= (at grid r c) color) 1 0)))))'''
_CROP = '''(define (crop-content grid)
      (let* ((cells (filter (lambda (p) (not (= (at grid (first p) (second p)) 0)))
                            (grid-positions grid)))
             (box (bbox-of-cells cells)))
        (subgrid grid (first box) (second box) (third box) (fourth box))))'''


def color_subset_program(settings, kind):
    """Replay the exact two color-subset shortcuts found by independent review."""
    if kind == 'lowest_color':
        definition = '''(define (chosen-color grid)
          (first (filter (lambda (color) (not (empty? (find-color grid color)))) (range 1 9))))'''
    elif kind == 'rarest_color':
        definition = '''(define (chosen-color grid)
          (let ((colors (filter (lambda (color) (not (empty? (find-color grid color)))) (range 1 9))))
            (for/fold ((best (first colors))) ((color (in-list (rest colors))))
              (if (< (length (find-color grid color)) (length (find-color grid best))) color best))))'''
    else:
        raise ValueError('unknown retained color-subset shortcut')
    definition += '''
        (define (mask-color grid color)
          (grid-from-fn (rows grid) (cols grid)
            (lambda (r c) (if (= (at grid r c) color) 1 0))))'''
    return variant_program(settings, definitions=definition,
        predicate='(equal? (transform-code (mask-color a (chosen-color a)) t) (mask-color b (chosen-color a)))')


def rivals(settings):
    """Finite lawful wrong rules; the generic auditor adds setting alternatives."""
    mode = parse_settings(settings)['transfer']
    menu = {'fixed_' + name: variant_program(settings, terminal=f'(transform-code c {i})')
            for i, name in enumerate(TRANSFORMS, 1)}
    menu.update({
        'copy_panel_a': variant_program(settings, terminal='a'),
        'copy_panel_b': variant_program(settings, terminal='b'),
        'transform_panel_a': variant_program(settings, panel='a'),
        'transform_panel_b': variant_program(settings, panel='b'),
        'binary_inference': variant_program(settings, definitions=_BINARY,
            predicate='(equal? (transform-code (binary-mask a) t) (binary-mask b))'),
        'dominant_color_inference': variant_program(settings, definitions=_DOMINANT,
            predicate='(equal? (transform-code (dominant-mask a) t) (dominant-mask b))'),
        'rarest_color_inference': color_subset_program(settings, 'rarest_color'),
        'lowest_color_inference': color_subset_program(settings, 'lowest_color'),
        'crop_before_transfer': variant_program(settings, definitions=_CROP, panel='(crop-content c)'),
        'rotations_only': variant_program(settings, code_expression='(if (>= code 5) 1 code)'),
        'reflections_only': variant_program(settings, code_expression='(if (and (>= code 2) (<= code 4)) 1 code)'),
        'omit_diagonal_reflections': variant_program(settings, code_expression='(if (>= code 7) 1 code)'),
        'omit_axis_reflections': variant_program(settings, code_expression='(if (or (= code 5) (= code 6)) 1 code)'),
        'erase_colors_after_transfer': variant_program(settings, definitions=_BINARY,
            terminal=f'(binary-mask {_application(mode)})'),
    })
    return menu
