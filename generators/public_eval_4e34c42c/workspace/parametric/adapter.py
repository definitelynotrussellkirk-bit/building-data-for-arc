"""Native, unapproved adapter. Public projections are controller operations."""
from pathlib import Path
import copy
import importlib.util
import random

HOME=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('_jigsaw_'+str(HOME).encode().hex(),Path(__file__).with_name('prototype.py'))
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)
SETTINGS=({'finish_rule':'assemble'},{'finish_rule':'assemble_then_bridge'})


def checked(settings):
    if type(settings) is not dict or set(settings)!={'finish_rule'} or type(settings['finish_rule']) is not str or settings not in SETTINGS:
        raise ValueError('expected one declared finish_rule')
    return settings['finish_rule']=='assemble_then_bridge'


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi: raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def program(settings):
    bridge=checked(settings)
    source=(HOME/'reference.rkt').read_text()
    if not bridge:return source
    assert source.count('(define bridge-after-assembly #f)')==1
    return source.replace('(define bridge-after-assembly #f)','(define bridge-after-assembly #t)')


def generate(seed,settings,demos=3,queries=4):
    bridge=checked(settings);integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    def pair(index,stress=False):
        x,y=_model.scene(seed,index,stress)
        if bridge:y=_model.bridge_pairs(y,_model.background(x))
        return {'input':x,'output':y}
    # Separate deterministic streams keep the complete query bank independent
    # of demonstration count. Presentation shuffles all four before prefixing.
    return {'train':[pair(i) for i in range(demos)],
            'test':[pair(100+i,i==3) for i in range(queries)],
            'program_solution':program(settings)}


def public_views(episode,presentation_seed=0,count=4):
    integer(presentation_seed,0,2**63-1,'presentation_seed');integer(count,1,4,'count')
    if len(episode.get('test',[]))!=4: raise ValueError('materialize the complete four-query bank before presentation')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return [copy.deepcopy({'train': [{'input':p['input'],'output':p['output']} for p in episode['train']],
                           'test':[{'input':episode['test'][i]['input']}]}) for i in order[:count]]
