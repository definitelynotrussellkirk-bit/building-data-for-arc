"""Stable full banks; setting and requested prefix do not affect input sampling."""
import hashlib
import importlib.util
from pathlib import Path
import sys
from puzzle_generators.base import gen_ctx

BASE=Path(__file__).resolve().parent
_GENERATOR=None


def generator():
    global _GENERATOR
    if _GENERATOR is None:
        path=BASE.parents[1]/'generator.py'
        raw=path.read_bytes()
        name='_arch_support_sampler_'+hashlib.sha256(str(path).encode()+raw).hexdigest()
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        exec(compile(raw,str(path),'exec'),module.__dict__)
        _GENERATOR=module
    return _GENERATOR


def sample_banks(seed):
    if type(seed) is not int or not 0<=seed<=2**63-1:
        raise ValueError('seed must be an exact integer in 0..2**63-1')
    G=generator()
    demos=[G.generate(seed,index) for index in range(6)]
    queries=[G.generate(seed,index) for index in range(6,10)]
    ctx=gen_ctx(seed=seed,sample_index=0,version=G.VERSION,task_id=G.RULE_TASK_ID)
    ctx.draw_rng('native-full-query-order').shuffle(queries)
    return demos,queries
