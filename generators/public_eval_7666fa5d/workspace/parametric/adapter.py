"""Native matched-input adapter for diagonal-span bracketing."""
from pathlib import Path
import importlib.util
import random
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_bracket_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)

def setting(settings):
    if type(settings) is not dict or set(settings)!={'bracket_rule'} or type(settings['bracket_rule']) is not str or settings['bracket_rule'] not in ('all_spans','equal_length'):
        raise ValueError('Expected exactly bracket_rule=all_spans or equal_length')
    return settings['bracket_rule']

def program(settings):
    mode=setting(settings);text=(BASE/'canonical.rkt').read_text()
    return text if mode=='all_spans' else text.replace('(define length-match? #f)','(define length-match? #t)')

def rival_program(settings,name):
    mode=setting(settings)
    if name not in model.RIVALS:raise ValueError('Unknown rival')
    if name=='identity':return '(rule! (lambda (g) g))'
    if name=='opposite_mode':return program({'bracket_rule':'equal_length' if mode=='all_spans' else 'all_spans'})
    changes={
      'first_four':('(define segments (if first-pair-only? (take eligible (min 2 (length eligible))) eligible))','(define segments (take eligible (min 4 (length eligible))))'),
      'length_thirteen':('(define max-length 60)','(define max-length 13)'),
      'adjacent_only':('(define adjacent-only? #f)','(define adjacent-only? #t)'),
      'first_pair':('(define first-pair-only? #f)','(define first-pair-only? #t)'),
      'longest_only':('(define longest-only? #f)','(define longest-only? #t)'),
      'endpoint_rays':('(define exact-rays? #f)','(define exact-rays? #t)'),
      'union_spans':('(define union-spans? #f)','(define union-spans? #t)'),
      'redraw_strokes':('(define preserve-strokes? #t)','(define preserve-strokes? #f)'),
      'color_grouping':('(define same-color? #f)','(define same-color? #t)'),
      'short_strokes_only':('(define max-length 60)','(define max-length 5)'),
      'point_spans':('(define point-spans? #f)','(define point-spans? #t)')}
    old,new=changes[name];text=program(settings)
    if text.count(old)!=1:raise ValueError('Counterfactual source marker drifted')
    return text.replace(old,new)

def generate(seed,settings,demos,queries):
    mode=setting(settings)
    model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    def pair(g):return {'input':g,'output':model.solve(g,mode)}
    train=[pair(model.sample_input(seed,i,'demo')) for i in range(demos)]
    bank=[pair(model.sample_input(seed,i,'query')) for i in range(4)]
    random.Random(f'7666fa5d:{seed}:presentation').shuffle(bank)
    return {'train':train,'test':bank[:queries],'program_solution':program(settings),'settings':dict(settings),'seed':seed}

def public_view(episode,index=0):
    model.integer(index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':model.grid_copy(p['input']),'output':model.grid_copy(p['output'])} for p in episode['train']],
            'test':[{'input':model.grid_copy(episode['test'][index]['input'])}]}
