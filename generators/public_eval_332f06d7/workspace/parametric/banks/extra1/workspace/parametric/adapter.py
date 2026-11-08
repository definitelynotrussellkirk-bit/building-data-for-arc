"""Source-local adapter for boat-sized navigation and route tracing."""
from pathlib import Path
import copy,hashlib,importlib.util,json,random,sys
BASE=Path(__file__).resolve().parent

def _load():
    path=BASE/'engine.py';key='_boat_nav_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec)
        sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]
G=_load()

def finish(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or type(settings['finish']) is not str or settings['finish'] not in G.VALUES:
        raise ValueError('settings must contain exactly finish=move_only|trace_route')
    return settings['finish']

def program(settings):
    return (BASE/('canonical.rkt' if finish(settings)=='move_only' else 'trace.rkt')).read_text()

def generate(seed,settings,demos=2,queries=4):
    value=finish(settings);G.integer(seed,0,2**63-1,'seed');G.integer(demos,2,6,'demos');G.integer(queries,1,4,'queries')
    ds,qs=G.input_bank(seed)
    def pair(text):
        g=json.loads(text);return {'input':g,'output':G.solve(g,value)}
    return {'train':[pair(x) for x in ds[:demos]],'test':[pair(x) for x in qs[:queries]],'program_solution':program(settings)}

def present(seed,settings,demos=2,queries=4,presentation_seed=0):
    G.integer(queries,1,4,'queries');G.integer(presentation_seed,0,2**63-1,'presentation_seed')
    ep=generate(seed,settings,demos,4);order=list(range(4))
    rng=random.Random(int.from_bytes(hashlib.sha256(f'332f06d7:present:{seed}:{presentation_seed}'.encode()).digest(),'big'));rng.shuffle(order)
    public=[{'train':copy.deepcopy(ep['train']),'test':[{'input':copy.deepcopy(ep['test'][i]['input'])}]} for i in order[:queries]]
    return {'public':public,'private':{'settings':copy.deepcopy(settings),'program':ep['program_solution'],'seed':seed,
            'presentation_seed':presentation_seed,'source_indices':order,'source_pairs':copy.deepcopy(ep['test'])}}

def counterfactual_program(settings):finish(settings);return (BASE/'wrong-intermediate.rkt').read_text()
def intermediate(g,settings):finish(settings);return G.analyze(g)
def dependency():
    return {'step_a':'Enumerate placements where the full boat rectangle fits, retain the start-connected placement graph, choose the dead end nearest the destination, and reconstruct its unique route.',
      'intermediate':'The ordered sequence of boat-sized placements from the initial rectangle to the selected reachable dead end.',
      'step_b':'Move the boat to that endpoint and recolor only corridor cells swept by the selected route, excluding the final boat, to 9.',
      'why_b_depends_on_a':'The reachable graph has unused branches. Marking every reachable placement rather than the selected start-to-end route changes the protected final grid.'}
