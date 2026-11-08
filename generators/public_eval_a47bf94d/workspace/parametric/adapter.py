"""Native unapproved adapter; all labels are independently checked at preflight."""
from pathlib import Path
import importlib.util

HOME=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('_a47bf94d_local_generator',HOME/'generator.py')
family=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)
SETTINGS=('paired','longest_sink_orange')

def checked(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in SETTINGS:
        raise ValueError('Expected exactly one declared finish setting')
    return settings['finish']

def program(settings):
    finish=checked(settings)
    canonical=(HOME/'reference.rkt').read_text()
    if finish=='paired':return canonical
    return canonical.replace("(define finish 'paired)","(define finish 'longest_sink_orange)")

def generate(seed, settings, demos, queries):
    finish=checked(settings)
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'{name} outside exact integer bounds')
    def pair(index):
        grid=family.generate(seed,index,stress=index==1000)
        return {'input':grid,'output':family.solve(grid,finish)}
    # Query indices do not depend on the number of demonstrations.
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(1000+i) for i in range(4)][:queries],
            'program_solution':program(settings)}

def rival_programs(settings):
    selected=program(settings)
    rivals={
        'unchanged_input':'(rule! (lambda (g) g))',
        'reversed_glyph_roles':selected.replace("color kind)","color original-kind)\n    (define kind (if (equal? original-kind 'x) 'diamond 'x))"),
        'other_setting':program({'finish':SETTINGS[1-SETTINGS.index(checked(settings))]}),
    }
    if settings['finish']=='longest_sink_orange':
        score='(define (score item) (- (length (first item)) 1))'
        replacements={
         'endpoint_distance':'''(define (score item)
          (define path (first item))
          (+ (abs (- (first (first path)) (first (last path))))
             (abs (- (second (first path)) (second (last path))))))''',
         'shortest_route':'(define (score item) (- 1 (length (first item))))',
         'first_route':'(define (score item) 0)',
         'last_route':'(define (score item) (index-of recovered item))',
        }
        rivals.update({k:selected.replace(score,v) for k,v in replacements.items()})
    return rivals
