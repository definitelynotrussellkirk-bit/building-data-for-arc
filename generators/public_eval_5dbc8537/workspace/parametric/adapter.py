"""Finite native contract; claims are independently replayed by protected Racket."""
import importlib.util
import hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent


def _local(name):
    spec=importlib.util.spec_from_file_location('_packing_'+name,BASE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

CORE=_local('prototype')
SAMPLER=_local('sampler')


def _setting(settings):
    if type(settings) is not dict or set(settings)!={'frame_policy'} or type(settings['frame_policy']) is not str or settings['frame_policy'] not in ('original','first_placed_piece','last_placed_piece'):
        raise ValueError('settings must contain only a valid frame_policy')
    return settings['frame_policy']


def program(settings):
    value=_setting(settings)
    return (BASE/('canonical.rkt' if value=='original' else value+'.rkt')).read_text()


def generate(seed,settings,demos,queries):
    value=_setting(settings)
    if type(seed) is not int or type(demos) is not int or not 2<=demos<=6 or type(queries) is not int or queries!=4:
        raise ValueError('integer seed, 2..6 demonstrations and exactly four queries required')
    def pair(index):
        if index in (0,1):
            # Teach both destination extremes; only the current demo's input is
            # considered, never a query or a query label. The base sampler and
            # its ordinary query bank remain unchanged.
            for attempt in range(64):
                draw=seed if attempt==0 else int.from_bytes(hashlib.sha256(f'packing-demo-v2|{seed}|{index}|{attempt}'.encode()).digest(),'big')
                grid=SAMPLER.generate(draw,index,rotation=2*index)
                bg,_,board,pieces=CORE.parse(grid)
                _,records=CORE.pack(board,pieces,bg,require_unique=True)
                modal=lambda p:CORE.mode(v for row in p for v in row)
                ends={modal(records[0][2]),modal(records[-1][2])}
                source_ends={modal(pieces[0]),modal(pieces[-1])}
                if not ends & source_ends:break
            else:raise ValueError('bounded teaching-layout construction exhausted')
        else:
            grid=SAMPLER.generate(seed,index)
        return {'input':grid,'output':CORE.solve(grid,value,require_unique=True)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(100+i) for i in range(4)],'program_solution':program(settings)}

# Stable private shuffle of the complete bank precedes prefix projection.
_raw_generate=generate
def generate(seed,settings,demos,queries):
    if type(queries) is not int or not 1<=queries<=4:raise ValueError("queries must be 1..4")
    ep=_raw_generate(seed,settings,demos,4)
    import random
    random.Random(f"repeat-private-query-order:{seed}").shuffle(ep["test"])
    ep["test"]=ep["test"][:queries]
    return ep
def public_view(ep,index):
    import copy
    return copy.deepcopy(dict(train=[dict(input=p["input"],output=p["output"])for p in ep["train"]],test=[dict(input=ep["test"][index]["input"])]))
