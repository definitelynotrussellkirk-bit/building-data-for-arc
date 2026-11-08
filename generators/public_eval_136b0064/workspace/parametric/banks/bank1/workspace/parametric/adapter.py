"""Native adapter; private count prefixing follows a full shuffled query bank."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys

PATH=Path(__file__).resolve().with_name('family.py')
NAME='_path_family_'+hashlib.sha256(str(PATH).encode()).hexdigest()
if NAME not in sys.modules:
    spec=importlib.util.spec_from_file_location(NAME,PATH)
    module=importlib.util.module_from_spec(spec)
    sys.modules[NAME]=module
    spec.loader.exec_module(module)
family=sys.modules[NAME]


def program(settings):
    order=family.setting(settings)
    if order=='column_major':
        return Path(__file__).resolve().parents[2].joinpath('reference.rkt').read_text()
    return family.racket_program(order)


def generate(seed, settings, demos, queries):
    family.integer(seed,0,2**63-1,'seed')
    family.integer(demos,2,6,'demos'); family.integer(queries,1,4,'queries')
    order=family.setting(settings)
    cached=family.full_lesson(seed,order)
    lesson={split:[{'input':[list(r) for r in g],'output':[list(r) for r in o]}
                   for g,o in cached[split][:n]] for split,n in [('train',demos),('test',queries)]}
    lesson['program_solution']=program(settings)
    return lesson


def public_view(lesson, index):
    family.integer(index,0,len(lesson['test'])-1,'query index')
    return {'train':copy.deepcopy([{'input':p['input'],'output':p['output']} for p in lesson['train']]),
            'test':[{'input':copy.deepcopy(lesson['test'][index]['input'])}]}
