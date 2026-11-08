from pathlib import Path
from copy import deepcopy
import importlib.util, random
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_chain_engine_'+str(HERE),HERE/'engine.py')
engine=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(engine)

def setting(settings):
    if (type(settings) is not dict or set(settings)!={'traversal'} or
        type(settings['traversal']) is not str or settings['traversal'] not in engine.SETTINGS):
        raise ValueError('settings must contain exactly traversal=forward|reverse')
    return settings['traversal']

def program(settings):
    mode=setting(settings)
    return (HERE/('canonical.rkt' if mode=='forward' else 'reverse.rkt')).read_text()

def generate(seed,settings,demos,queries):
    mode=setting(settings);engine.integer(seed,0,2**63-1,'seed')
    engine.integer(demos,2,6,'demos');engine.integer(queries,1,4,'queries')
    def pairs(kind,count):
        return [{'input':(g:=engine.scene(seed,i,kind)),'output':engine.solve(g,mode)} for i in range(count)]
    return {'train':pairs('demo',demos),'test':pairs('query',queries),'program_solution':program(settings),
            'private':{'seed':seed,'settings':deepcopy(settings)}}

def presentation_order(presentation_seed):
    engine.integer(presentation_seed,0,2**63-1,'presentation_seed')
    order=list(range(4));random.Random('78332cb0:presentation:v1:'+str(presentation_seed)).shuffle(order)
    return order

def public_turn(episode,turn,presentation_seed=0):
    if type(episode) is not dict or type(episode.get('train')) is not list or type(episode.get('test')) is not list:
        raise ValueError('invalid private episode')
    engine.integer(turn,0,len(episode['test'])-1,'turn')
    order=[i for i in presentation_order(presentation_seed) if i<len(episode['test'])]
    index=order[turn]
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}

def public_turns(seed,settings,demos,presentation_seed=0,count=4):
    engine.integer(count,1,4,'count')
    episode=generate(seed,settings,demos,4)
    return [public_turn(episode,i,presentation_seed) for i in range(count)]
