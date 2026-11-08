"""Setting-neutral component adapter; the shared worker verifies its labels."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name('components.py')
_spec = importlib.util.spec_from_file_location('_task_57bafcdde8c3_components', _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def generate(seed, settings, demos, queries):
    chosen = _prototype._settings(settings)
    _prototype._integer(seed, 0, 2**63-1, 'seed')
    _prototype._integer(demos, 2, 8, 'demos')
    _prototype._integer(queries, 1, 8, 'queries')
    cache = {}
    # This rival is one of the six legitimate settings, already compared below.
    extras = {name:rival for name,rival in _prototype.GEN.SEMANTIC_RIVALS.items()
              if name != 'eight_connected'}
    def scene(index):
        if index not in cache:
            value = _prototype._candidate(seed, index)
            cache[index] = (value, [_prototype.transform(value,s) for s in _prototype.SETTINGS],
                            {name:rival(value) for name,rival in extras.items()})
        return cache[index]
    for attempt in range(512):
        teaching = [scene(attempt+i) for i in range(demos)]
        signatures = [tuple(_prototype._digest(s[1][j]) for s in teaching)
                      for j in range(len(_prototype.SETTINGS))]
        if len(set(signatures)) != len(signatures):
            continue
        if any(all(rivals[name] == outputs[j] for _,outputs,rivals in teaching)
               for j in range(len(_prototype.SETTINGS)) for name in extras):
            continue
        break
    else:
        raise ValueError('No jointly distinguishing lesson within512schedule attempts')
    train = [{'input':value, 'output':_prototype.transform(value,chosen)} for value,_,_ in teaching]
    seen = {_prototype._digest(p['input']) for p in train};test = []
    if len(seen) != demos:raise ValueError('Teaching inputs repeat')
    for i in range(queries):
        # A separate index region keeps query prefixes independent of demos.
        # Four queries retain one canonical anchor and three genuinely larger fields.
        cycle, slot = divmod(i,4)
        offset = [cycle%2, 2+cycle%2, 4, 5][slot]
        for retry in range(16):
            value = _prototype._candidate(seed, (1024+i*16+retry)*6+offset)
            key = _prototype._digest(value)
            if key not in seen:break
        else:
            raise ValueError('Distinct query budget exhausted; no partial episode')
        seen.add(key);test.append({'input':value,'output':_prototype.transform(value,chosen)})
    return {'train':train,'test':test,'program_solution':program(chosen)}
