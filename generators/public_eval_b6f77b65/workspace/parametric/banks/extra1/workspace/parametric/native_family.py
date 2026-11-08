"""Arch decomposition claims; protected Racket execution is the label authority."""
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
HOME = BASE.parents[1]
DEFAULT = {'support_mode': 'both'}
_GENERATOR = None

def normalize_settings(settings):
    if type(settings) is not dict or set(settings) != {'support_mode'}:
        raise ValueError('settings must contain exactly support_mode')
    value = settings['support_mode']
    if type(value) is not str or value not in ('both', 'either'):
        raise ValueError('support_mode must be both or either')
    return {'support_mode': value}

def normalize_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError('grid requires 1..30 exact-list rows')
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid requires 1..30 columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('rectangular exact integer color grid required')
    return [row[:] for row in grid]

def generator():
    global _GENERATOR
    if _GENERATOR is None:
        path = HOME / 'generator.py'
        raw = path.read_bytes()
        name = '_arch_support_generator_' + hashlib.sha256(str(path).encode()+raw).hexdigest()
        spec = importlib.util.spec_from_file_location(name,path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(raw,str(path),'exec'),module.__dict__)
        _GENERATOR = module
    return _GENERATOR

def analyze(grid):
    return generator().analyze(normalize_grid(grid))

def solve(grid,settings):
    settings = normalize_settings(settings)
    return generator().simulate(normalize_grid(grid), support_mode=settings['support_mode'])['output']

def program(settings):
    settings = normalize_settings(settings)
    source = (BASE/'canonical.rkt').read_text()
    if settings['support_mode']=='both':
        return source
    needle = "(define lateral-support 'both)"
    if source.count(needle)!=1:
        raise ValueError('canonical lateral-support anchor must occur once')
    return source.replace(needle,"(define lateral-support 'either)",1)

def rival_programs(settings):
    settings=normalize_settings(settings)
    opposite={'support_mode':'either' if settings['support_mode']=='both' else 'both'}
    source=program(settings)
    def changed(anchor,replacement):
        if source.count(anchor)!=1:
            raise ValueError('rival anchor must occur once: '+anchor)
        return source.replace(anchor,replacement,1)
    active="""(define active
       (filter (lambda (piece) (not (member (second piece) selected))) pieces))"""
    pixels="""(define active
       (apply append
              (for/list ((piece pieces) #:unless (member (second piece) selected))
                (for/list ((cell (third piece)))
                  (list 'vertical (second piece) (list cell))))))"""
    return {
        'opposite_support': program(opposite),
        'erase_without_gravity': changed('(define max-passes (* h (max 1 (length active))))','(define max-passes 0)'),
        'one_gravity_pass': changed('(define max-passes (* h (max 1 (length active))))','(define max-passes 1)'),
        'skip_selected_deletion': changed(active,'(define active pieces)'),
        'first_selector_only': changed("(filter (lambda (color) (not (= color 0))) (first g))","(list (at g 0 0))"),
        'ignore_lateral_support': changed("(and (eq? (first piece) 'horizontal)","(and #f (eq? (first piece) 'horizontal)"),
        'hold_every_beam': changed("(and clear-below (not held-laterally))","(and clear-below (not held-laterally) (eq? (first piece) 'vertical))"),
        'independent_pixels': changed(active,pixels),
        'delete_selected_posts_only': changed(active,"(define active (filter (lambda (piece) (not (and (eq? (first piece) 'vertical) (member (second piece) selected)))) pieces))"),
        'delete_selected_beams_only': changed(active,"(define active (filter (lambda (piece) (not (and (eq? (first piece) 'horizontal) (member (second piece) selected)))) pieces))"),
    }

