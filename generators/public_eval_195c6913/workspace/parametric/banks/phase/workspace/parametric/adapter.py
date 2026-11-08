"""Native fixed phase-policy family. Labels are claims, re-executed by preflight."""
from pathlib import Path
from functools import lru_cache
from copy import deepcopy
import importlib.util
BASE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_terrain195_core_'+str(BASE),BASE/'core.py')
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
RIVALS=('identity','opposite_setting','straight','down_turn','first_start',
        'no_markers','mark_last','keep_legends','unique_cycle','sorted_cycle',
        'descending_cycle','reverse_cycle','period_2','period_3','period_4',
        'global_phase','count_walls')


def setting(settings):
    if settings is None:return 'carry'
    if type(settings) is not dict or set(settings)!={'phase'} or settings['phase'] not in core.MODES:
        raise ValueError('settings must be exactly phase=carry|restart')
    return settings['phase']


def program(settings=None):
    mode=setting(settings)
    return (BASE/('canonical.rkt' if mode=='carry' else 'restart.rkt')).read_text()


@lru_cache(maxsize=64)
def _bank(seed):
    bank=[core.scene(seed,i) for i in range(10)]
    if len({repr(g) for g in bank})!=10:raise ValueError('Duplicate constructed input')
    return tuple(tuple(tuple(r) for r in g) for g in bank)


def inputs(seed):
    if type(seed) is not int or not 0<=seed<=2**63-1:raise ValueError('Exact seed in 0..2^63-1 required')
    return [[list(r) for r in g] for g in _bank(seed)]


def generate(seed,settings=None,demos=2,queries=4):
    mode=setting(settings)
    if type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or not 1<=queries<=4:
        raise ValueError('demos=2..6; queries=1..4 as exact integers')
    bank=inputs(seed);order=list(range(6,10));core.rng_for(seed,'private-presentation').shuffle(order)
    pair=lambda g:{'input':deepcopy(g),'output':core.solve(g,mode)}
    return {'train':[pair(g) for g in bank[:demos]],'test':[pair(bank[i]) for i in order[:queries]],
            'program_solution':program({'phase':mode})}


def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid query index')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})


def rival_program(mode,name):
    """Executable finite shortcuts, mirrored independently in core.solve()."""
    if mode not in core.MODES or name not in RIVALS:raise ValueError('Unknown rival')
    if name=='identity':return '(rule! (lambda (g) g))'
    if name=='opposite_setting':return program({'phase':'restart' if mode=='carry' else 'carry'})
    p=program({'phase':mode})
    def replace(old,new,count=1):
        nonlocal p
        if p.count(old)!=count:raise ValueError('Reference edit invalidates rival rewrite: '+name)
        p=p.replace(old,new)
    if name=='straight':replace('(if (passable tr tc)','(if #f')
    elif name=='down_turn':replace('(if (= direction 0) 0 -1)','(if (= direction 0) 0 1)');replace('(if (= next-dir 0) 0 -1)','(if (= next-dir 0) 0 1)')
    elif name=='first_start':replace('(trace (obj-r1 o) 0 0 0 0)) starts))','(trace (obj-r1 o) 0 0 0 0)) (list (first starts))))')
    elif name=='mark_last':replace('(define marker (list 1 nr nc total local))','(define marker (list 1 r c total local))')
    elif name=='no_markers':
        replace('(set-cell out (second e) (third e)','(set-cell out (second e) (third e)')
        replace('(if (= (first e) 1) stop-color','(if (= (first e) 1) (at out (second e) (third e))')
    elif name=='keep_legends':replace('(define cleaned (for/fold ((out g)) ((o chips)) (recolor-cells out (obj-cells o) bg)))','(define cleaned g)')
    elif name in ('unique_cycle','sorted_cycle','descending_cycle','reverse_cycle') or name.startswith('period_'):
        replace('(= (obj-color o) (first cycle))','(= (obj-color o) (obj-color (first ordered)))')
        raw='(map obj-color ordered)'
        expr={'unique_cycle':f'(remove-duplicates {raw})','sorted_cycle':f'(sort {raw} <)',
              'descending_cycle':f'(sort {raw} >)','reverse_cycle':f'(reverse {raw})'}.get(name)
        if name.startswith('period_'):
            n=int(name.split('_')[1]);expr=f'(for/list ((i (range {n}))) (list-ref {raw} (modulo i (length ordered))))'
        replace('(define cycle '+raw+')','(define cycle '+expr+')')
    elif name=='count_walls':replace('(define turn-tax 0)','(define turn-tax 1)')
    elif name=='global_phase':
        old='(define paths (map (lambda (o) (trace (obj-r1 o) 0 0 0 0)) starts))'
        new='''(define raw-paths (map (lambda (o) (trace (obj-r1 o) 0 0 0 0)) starts))
   (define paths (for/list ((i (range (length raw-paths))))
    (define offset (for/sum ((j (range i)))
      (length (filter (lambda (e) (= (first e) 0)) (list-ref raw-paths j)))))
    (map (lambda (e) (list (first e) (second e) (third e)
                     (+ (list-ref e 3) offset) (+ (list-ref e 4) offset))) (list-ref raw-paths i))))'''
        replace(old,new)
    return p
