"""Self-contained native adapter; only adjacent resources are read."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
NAME='_motif_family_'+hashlib.sha256(str(BASE).encode()).hexdigest()
if NAME not in sys.modules:
    spec=importlib.util.spec_from_file_location(NAME,BASE/'family.py')
    module=importlib.util.module_from_spec(spec);sys.modules[NAME]=module;spec.loader.exec_module(module)
family=sys.modules[NAME]

def program(settings):
    tiling=family.setting(settings)
    return (BASE/('canonical.rkt' if tiling=='translation' else 'alternate.rkt')).read_text()

def generate(seed,settings,demos,queries):
    family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    tiling=family.setting(settings);train,test=family.grids(seed)
    return {'train':[{'input':g,'output':family.solve(g,tiling)} for g in train[:demos]],
            'test':[{'input':g,'output':family.solve(g,tiling)} for g in test[:queries]],
            'program_solution':program(settings)}

def public_view(lesson,index):
    family.integer(index,0,len(lesson['test'])-1,'query index')
    return {'train':copy.deepcopy([{'input':p['input'],'output':p['output']} for p in lesson['train']]),
            'test':[{'input':copy.deepcopy(lesson['test'][index]['input'])}]}
