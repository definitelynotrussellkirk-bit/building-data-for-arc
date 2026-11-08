"""Resource-local marker-region family; labels are claims until protected execution."""
import copy
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_selector_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)
SETTINGS=({'assignment':'marker_first'},{'assignment':'marker_second'})

def validate(settings):
    if type(settings) is not dict or set(settings)!={'assignment'} or type(settings['assignment']) is not str or settings['assignment'] not in ('marker_first','marker_second'):
        raise ValueError('Expected exactly assignment=marker_first|marker_second')
    return settings['assignment']

def program(settings):
    setting=validate(settings);text=(BASE/'canonical.rkt').read_text()
    return text if setting=='marker_first' else text.replace('(define marker-first #t)','(define marker-first #f)')

def solve(grid,settings):return model.solve(grid,validate(settings))

def generate(seed,settings,demos=2,queries=4):
    validate(settings);model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    train,test=model.bank(seed)
    def pairs(grids):return [{'input':copy.deepcopy(g),'output':solve(g,settings)}for g in grids]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings)}

def public_view(episode,query_index=0):
    model.integer(query_index,0,len(episode['test'])-1,'query_index')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']}for p in episode['train']],
                          'test':[{'input':episode['test'][query_index]['input']}]})
