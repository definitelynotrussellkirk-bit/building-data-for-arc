"""Native two-scale compositor; all resources remain in this parametric home."""
from pathlib import Path
import copy
import importlib.util
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_quadrant_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
SETTINGS=({'background_sampling':'block'},{'background_sampling':'periodic'})


def validate(settings):
    if type(settings) is not dict or set(settings)!={'background_sampling'} or type(settings['background_sampling']) is not str or settings['background_sampling'] not in ('block','periodic'):
        raise ValueError('Expected exactly background_sampling=block|periodic')
    return settings['background_sampling']


def program(settings):
    mode=validate(settings);source=(BASE/'canonical.rkt').read_text()
    return source if mode=='block' else source.replace('(at g (+ side (quotient r side)) (quotient c side))','(at g (+ side (modulo r side)) (modulo c side))')


def solve(grid,settings):return model.solve(grid,validate(settings))


def generate(seed,settings,demos=2,queries=4):
    validate(settings);model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,1,4,'queries')
    train,test=model.bank(seed)
    def pairs(grids):return [{'input':copy.deepcopy(g),'output':solve(g,settings)} for g in grids]
    return {'train':pairs(train[:demos]),'test':pairs(test[:queries]),'program_solution':program(settings)}


def public_view(episode,query_index=0):
    model.integer(query_index,0,len(episode['test'])-1,'query_index')
    return copy.deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                          'test':[{'input':episode['test'][query_index]['input']}]})
