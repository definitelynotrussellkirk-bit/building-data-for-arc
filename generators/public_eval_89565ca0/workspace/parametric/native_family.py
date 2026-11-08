"""Occluded rectangular partitions; claims are independently executed in Racket."""
import hashlib
import importlib.util
from pathlib import Path
import sys

DEFAULT = {'sort_order': 'ascending'}
HOME = Path(__file__).resolve().parents[2]
_GENERATOR = None


def normalize_settings(settings):
    if type(settings) is not dict or set(settings) != {'sort_order'}:
        raise ValueError('settings must contain exactly sort_order')
    value = settings['sort_order']
    if type(value) is not str or value not in ('ascending', 'descending'):
        raise ValueError('sort_order must be ascending or descending')
    return {'sort_order': value}


def normalize_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid must have 1..30 exact-list rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError('grid must be rectangular exact lists')
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError('colors must be exact integers 0..9')
    return [row[:] for row in grid]


def _generator():
    global _GENERATOR
    if _GENERATOR is None:
        path = HOME / 'generator.py'
        name = '_rooms_generator_' + hashlib.sha256(str(path).encode()).hexdigest()
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _GENERATOR = module
    return _GENERATOR


def analyze(grid):
    """Return input-only recovered geometry, with strict grammar admission."""
    return _generator().analyze(normalize_grid(grid))


def solve(grid, settings):
    settings = normalize_settings(settings)
    info = analyze(grid)
    sign = 1 if settings['sort_order'] == 'ascending' else -1
    objects = sorted(info['objects'], key=lambda o:
                     (sign * o['rooms'], o['bbox'][1], o['bbox'][0], o['color']))
    width = max(o['rooms'] for o in objects)
    return [[o['color']] * o['rooms'] + [info['noise_color']] * (width-o['rooms'])
            for o in objects]


def program(settings):
    settings = normalize_settings(settings)
    source = (HOME / 'reference.rkt').read_text()
    if settings['sort_order'] == 'ascending':
        return source
    needle = '(define descending? #f)'
    if source.count(needle) != 1:
        raise ValueError('canonical order declaration must be unique')
    return source.replace(needle, '(define descending? #t)', 1)


def rival_programs(settings):
    """Executable nearby alternatives, evaluated against demonstrations first."""
    settings = normalize_settings(settings)
    other = {'sort_order': 'descending' if settings['sort_order'] == 'ascending' else 'ascending'}
    source = program(settings)
    def changed(needle, replacement, original=source):
        if original.count(needle) != 1:
            raise ValueError('rival replacement anchor must occur exactly once: ' + needle)
        return original.replace(needle, replacement, 1)
    count = '(define room-count region-count)'
    tie = '[(= (second a) (second b)) (spatial-before? a b)]'
    order = '(define ordered-records (sort records before?))'
    raw = changed('(define count-walls restored-walls)', '(define count-walls raw-walls)')
    return {
        'other_order': program(other),
        'full_axes_product_capped': changed(count,
            '(define room-count (min 30 (* (- (length horizontal-axes) 1) (- (length vertical-axes) 1))))'),
        'one_room_per_color': changed(count, '(define room-count 1)'),
        'raw_unhealed_count_capped': changed(count,
            '(define room-count (min 30 (max 1 region-count)))', raw),
        'numeric_color_ties': changed(tie,
            '[(= (second a) (second b)) (< (first a) (first b))]'),
        'topmost_ties': changed(tie,
            '[(= (second a) (second b)) (if (= (list-ref a 3) (list-ref b 3)) (spatial-before? a b) (< (list-ref a 3) (list-ref b 3)))]'),
        'sort_by_color': changed(order,
            '(define ordered-records (sort records (lambda (a b) (< (first a) (first b)))))'),
        'sort_by_position': changed(order,
            '(define ordered-records (sort records spatial-before?))'),
        'sort_by_area': changed(order,
            '(define ordered-records (sort records (lambda (a b) (cond [(= (list-ref a 4) (list-ref b 4)) (spatial-before? a b)] [descending? (> (list-ref a 4) (list-ref b 4))] [else (< (list-ref a 4) (list-ref b 4))]))))'),
        'reverse_complete_output': changed('(define final-output output)',
            '(define final-output (reverse output))'),
        'pad_with_black': changed('(define padding-color noise-color)',
            '(define padding-color 0)'),
    }
