"""Strict native adapter for matched-input, unapproved public-parent authoring."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent


def _load(filename):
    path = BASE / filename
    name = '_rooms_' + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


family = _load('native_family.py')
sampler = _load('sampler.py')


def program(settings):
    return family.program(settings)


def generate(seed, settings, demos, queries):
    settings = family.normalize_settings(settings)
    for name,value,lo,hi in [('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)]:
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    demo_bank,query_bank = sampler.sample_banks(seed)
    if len(demo_bank) != 6 or len(query_bank) != 4:
        raise ValueError('sampler must materialize complete six/four banks')
    all_inputs = demo_bank + query_bank
    if len({json.dumps(g,separators=(',',':')) for g in all_inputs}) != 10:
        raise ValueError('all demonstration and query inputs must be distinct')
    def pair(grid):
        independent = family.normalize_grid(grid)
        return {'input':independent, 'output':family.solve(independent,settings)}
    return {'train':[pair(g) for g in demo_bank[:demos]],
            'test':[pair(g) for g in query_bank[:queries]],
            'program_solution':program(settings)}
