"""Native authoring adapter for public_eval_581f7754."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,random,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
_name='_family581_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec=importlib.util.spec_from_file_location(_name,BASE/'family.py')
family=importlib.util.module_from_spec(_spec);sys.modules[_name]=family;_spec.loader.exec_module(family)

def _setting(settings):
    if (type(settings) is not dict or set(settings)!={'assignment'} or
        type(settings['assignment']) is not str or settings['assignment'] not in family.SETTINGS):
        raise ValueError('settings must be exactly assignment=matching_color|nearest_line')
    return settings['assignment']

def program(settings):
    s=_setting(settings)
    return (BASE/('canonical.rkt' if s=='matching_color' else 'nearest_line.rkt')).read_text()

def generate(seed,settings,demos,queries):
    s=_setting(settings);e=family.generate(seed,{'assignment':s},demos,queries)
    e['settings']={'assignment':s};e['seed']=seed;e['program_solution']=program(settings);return e

def presentation_order(presentation_seed):
    family.integer(presentation_seed,0,2**63-1,'presentation_seed');order=list(range(4))
    random.Random(int.from_bytes(hashlib.sha256(f'581:{presentation_seed}'.encode()).digest()[:16],'big')).shuffle(order)
    return order

def public_view(episode,source_query_index):
    family.integer(source_query_index,0,3,'source_query_index');bank=episode.get('private_query_bank')
    if type(bank) is not list or len(bank)!=4:raise ValueError('controller must retain four private queries')
    visible={'train':copy.deepcopy(episode['train']),'test':[{'input':copy.deepcopy(bank[source_query_index]['input'])}]}
    return json.loads(json.dumps(visible,sort_keys=True,separators=(',',':')))

def counterfactual_program():return program({'assignment':'matching_color'})
def intermediate(grid,settings=None):return family.intermediate(grid,'matching_color' if settings is None else _setting(settings))
def dependency():return family.dependency()
