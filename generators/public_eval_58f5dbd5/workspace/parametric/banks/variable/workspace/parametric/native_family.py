"""Color-associated template claims; independent Racket execution owns labels."""
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
HOME = BASE.parents[1]
DEFAULT = {'ink_mode': 'carve'}
_GENERATOR = None


def normalize_settings(settings):
    if type(settings) is not dict or set(settings) != {'ink_mode'}:
        raise ValueError('settings must contain exactly ink_mode')
    value = settings['ink_mode']
    if type(value) is not str or value not in ('carve', 'stamp'):
        raise ValueError('ink_mode must be carve or stamp')
    return {'ink_mode': value}


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
        name = '_carving_generator_' + hashlib.sha256(str(path).encode()+raw).hexdigest()
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
    info = analyze(grid)
    background = info['background']
    output = normalize_grid(grid)
    for record in info['targets']:
        top,left,bottom,right = record['bbox']
        for r,row in enumerate(record['mask']):
            for c,bit in enumerate(row):
                ink = bit if settings['ink_mode']=='stamp' else not bit
                output[top+1+r][left+1+c] = record['color'] if ink else background
    top,left,bottom,right = info['crop']
    return [row[left:right+1] for row in output[top:bottom+1]]


def program(settings):
    settings = normalize_settings(settings)
    source = (BASE/'canonical.rkt').read_text()
    if settings['ink_mode']=='carve':
        return source
    needle = "(define ink-mode 'carve)"
    if source.count(needle)!=1:
        raise ValueError('canonical ink-mode anchor must occur once')
    return source.replace(needle,"(define ink-mode 'stamp)",1)


def rival_programs(settings):
    settings=normalize_settings(settings)
    opposite={'ink_mode':'stamp' if settings['ink_mode']=='carve' else 'carve'}
    source=program(settings)
    needle="(define association-mode 'color)"
    if source.count(needle)!=1:
        raise ValueError('canonical association marker must occur once')
    def changed(anchor,replacement):
        if source.count(anchor)!=1:
            raise ValueError('rival anchor must occur once: '+anchor)
        return source.replace(anchor,replacement,1)
    bit='(define occupied? (list-ref (list-ref mask dr) dc))'
    def fitted(edited):
        # Fit a wrongly selected stencil rather than counting runtime errors
        # as a refutation. Equal dimensions preserve the selected mask exactly.
        return edited.replace(bit,"""(define occupied?
                 (list-ref
                  (list-ref mask (/ (* dr (length mask)) (- (obj-h destination) 2)))
                  (/ (* dc (length (first mask))) (- (obj-w destination) 2))))""",1)
    select="""(define selected-template
               (if (eq? association-mode 'color)
                   record
                   (list-ref templates-in-reading-order index)))"""
    largest="""(define occupied?
                 (let* ((pieces
                         (filter (lambda (o)
                                   (and (= (obj-color o) color)
                                        (not (equal? (obj-bbox o)
                                                     (obj-bbox destination)))))
                                 components))
                        (piece (first (sort pieces
                                            (lambda (a b) (> (obj-size a) (obj-size b)))))))
                   (if (member (list (+ (first (second record)) dr)
                                     (+ (second (second record)) dc))
                               (obj-cells piece)) #t #f)))"""
    return {
        'opposite_ink':program(opposite),
        'template_reading_order':fitted(changed(needle,"(define association-mode 'reading-order)")),
        'first_target_template_for_all':fitted(changed(select,'(define selected-template (first records))')),
        'next_target_color_template':fitted(changed(select,'(define selected-template (list-ref records (modulo (+ index 1) (length records))))')),
        'horizontal_template_flip':changed(bit,'(define occupied? (list-ref (list-ref mask dr) (- (length (first mask)) 1 dc)))'),
        'vertical_template_flip':changed(bit,'(define occupied? (list-ref (list-ref mask (- (length mask) 1 dr)) dc))'),
        'template_half_turn':changed(bit,'(define occupied? (list-ref (list-ref mask (- (length mask) 1 dr)) (- (length (first mask)) 1 dc)))'),
        'template_bbox_filled':changed(bit,'(define occupied? #t)'),
        'template_ignored':changed(bit,'(define occupied? #f)'),
        'largest_template_component_only':changed(bit,largest),
        'paint_first_target_only':changed('((record (in-list records))','((record (in-list (take records 1)))'),
    }
