"""Resource-local shape-vote family; private labels await protected execution."""
import copy
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_vote_model_'+str(BASE),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)
SETTINGS=({'vote':'most_frequent'},{'vote':'least_frequent'})

def validate(settings):
    if type(settings) is not dict or set(settings)!={'vote'} or type(settings['vote']) is not str or settings['vote']not in ('most_frequent','least_frequent'):
        raise ValueError('Expected exactly vote=most_frequent|least_frequent')
    return settings['vote']

def program(settings):
    vote=validate(settings);text=(BASE/'canonical.rkt').read_text()
    return text if vote=='most_frequent'else text.replace('(define most-frequent #t)','(define most-frequent #f)')

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
