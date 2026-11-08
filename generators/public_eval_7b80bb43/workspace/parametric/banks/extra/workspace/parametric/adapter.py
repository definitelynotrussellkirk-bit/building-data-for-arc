"""Native adapter for hinge-cued restoration and newly created junction marking."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_7b80bb43_local_generator',HERE/'family.py')
family=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(family)
SETTINGS=('straighten','mark_new_junctions')

def checked(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in SETTINGS:
        raise ValueError('Expected exactly one declared finish setting')
    return settings['finish']

def program(settings):
    finish=checked(settings);canonical=(HERE/'canonical.rkt').read_text()
    if finish=='straighten':return canonical
    return canonical.replace("(define finish 'straighten)","(define finish 'mark_new_junctions)")

def generate(seed,settings,demos,queries):
    finish=checked(settings)
    for value,lo,hi,name in ((seed,0,2**63-1,'seed'),(demos,2,6,'demos'),(queries,1,4,'queries')):
        if type(value) is not int or not lo<=value<=hi:raise ValueError(f'Invalid exact integer {name}')
    def pair(index):
        g=family.generate(seed,index,stress=index==1000)
        return {'input':g,'output':family.solve(g,finish)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(1000+i) for i in range(4)][:queries],
            'program_solution':program(settings)}

def rival_programs(settings):
    selected=program(settings)
    rivals={
      'other_setting':program({'finish':SETTINGS[1-SETTINGS.index(checked(settings))]}),
      'delete_spurs_only':selected.replace("(define repair-mode 'cued)","(define repair-mode 'none)"),
      'close_uncued_gaps':selected.replace("(define repair-mode 'cued)","(define repair-mode 'all_gaps)"),
      'horizontal_only':selected.replace("(define repair-mode 'cued)","(define repair-mode 'horizontal)"),
      'vertical_only':selected.replace("(define repair-mode 'cued)","(define repair-mode 'vertical)"),
    }
    if settings['finish']=='mark_new_junctions':
        rivals.update({
          'before_restoration':selected.replace('(define junction-grid completed)','(define junction-grid cleaned)'),
          'all_repaired':selected.replace('(>= degree 3)','#t'),
          'all_junctions':selected.replace('(define candidates repaired)',
                '(define candidates (find-color completed fg))'),
          'cross_only':selected.replace('(>= degree 3)','(= degree 4)'),
        })
    return rivals
