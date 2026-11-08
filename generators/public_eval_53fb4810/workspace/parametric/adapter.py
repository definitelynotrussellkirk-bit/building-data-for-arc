"""Native, matched-input adapter. Settings and labels are controller-private."""
from pathlib import Path
import copy
import importlib.util
import random

BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_beam_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)


def setting(settings):
    if type(settings) is not dict or set(settings)!={'continuation'} or type(settings['continuation']) is not str or settings['continuation'] not in ('repeat','bounce'):
        raise ValueError('Expected exactly continuation=repeat or continuation=bounce')
    return settings['continuation']


def program(settings):
    mode=setting(settings);text=(BASE/'canonical.rkt').read_text()
    return text if mode=='repeat' else text.replace('(define bounce? #f)','(define bounce? #t)')


def rival_program(settings,name):
    mode=setting(settings)
    if name not in model.RIVALS:raise ValueError('Unknown rival')
    if name=='identity':return '(rule! (lambda (g) g))'
    if name=='opposite_mode':return program({'continuation':'bounce' if mode=='repeat' else 'repeat'})
    text=program(settings)
    changes={
      'skip_wide':('(if first-only? (take rays (min 1 (length rays))) rays)','(filter (lambda (x) (< (length (third x)) 3)) rays)'),
      'period_one':('(define period (minimal-period strips))','(define period 1)'),
      'period_two':('(define period (minimal-period strips))','(define period (min 2 (length strips)))'),
      'reverse_word':('(define reverse-word? #f)','(define reverse-word? #t)'),
      'mirror_lanes':('(define mirror-lanes? #f)','(define mirror-lanes? #t)'),
      'phase_shift':('(define phase-offset 0)','(define phase-offset 1)'),
      'short_extension':('(define max-extension 60)','(define max-extension 2)'),
      'first_anchor':('(define first-only? #f)','(define first-only? #t)'),
      'background_only':('(define background-only? #f)','(define background-only? #t)')}
    old,new=changes[name]
    if text.count(old)!=1:raise ValueError('Counterfactual source marker drifted')
    return text.replace(old,new)


def generate(seed,settings,demos,queries):
    mode=setting(settings)
    model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    def pair(g):return {'input':g,'output':model.solve(g,mode)}
    train=[pair(model.sample_input(seed,i,'demo')) for i in range(demos)]
    bank=[pair(model.sample_input(seed,i,'query')) for i in range(4)]
    random.Random(f'53fb4810:{seed}:presentation').shuffle(bank)
    return {'train':train,'test':bank[:queries],'program_solution':program(settings),
            'settings':dict(settings),'seed':seed}


def public_view(episode,index=0):
    model.integer(index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':model.grid_copy(p['input']),'output':model.grid_copy(p['output'])} for p in episode['train']],
            'test':[{'input':model.grid_copy(episode['test'][index]['input'])}]}
