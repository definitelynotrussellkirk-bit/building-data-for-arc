"""Setting-neutral component adapter; the shared worker verifies its labels."""
import importlib.util
from pathlib import Path

_path = Path(__file__).with_name('components.py')
_spec = importlib.util.spec_from_file_location('_task_57bafcdde8c3_components', _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def program(settings):
    return _prototype.program(settings)


def _palette(value):
    background = _prototype._grid(value)
    foreground = {c for row in value for c in row} - {background}
    if background not in (1,7) or len(foreground)!=1 or not foreground<={0,3}:
        raise ValueError('Prototype sampler left its declared two-color domain')
    return background,next(iter(foreground))


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
                            {name:rival(value) for name,rival in extras.items()},_palette(value))
        return cache[index]
    for attempt in range(512):
        teaching = [scene(attempt+i) for i in range(demos)]
        signatures = [tuple(_prototype._digest(s[1][j]) for s in teaching)
                      for j in range(len(_prototype.SETTINGS))]
        if len(set(signatures)) != len(signatures):
            continue
        if any(all(rivals[name] == outputs[j] for _,outputs,rivals,_ in teaching)
               for j in range(len(_prototype.SETTINGS)) for name in extras):
            continue
        # Color roles must carry actual positive evidence under every setting.
        if not all(any(palette[role]==color and outputs[j]!=value
                       for value,outputs,_,palette in teaching)
                   for j in range(len(_prototype.SETTINGS))
                   for role,colors in enumerate(((1,7),(0,3))) for color in colors):
            continue
        break
    else:
        raise ValueError('No jointly distinguishing lesson within512schedule attempts')
    train = [{'input':value, 'output':_prototype.transform(value,chosen)} for value,_,_,_ in teaching]
    seen = {_prototype._digest(p['input']) for p in train};test = []
    if len(seen) != demos:raise ValueError('Teaching inputs repeat')
    for i in range(queries):
        # A separate index region keeps query prefixes independent of demos.
        # Four queries retain one canonical anchor and three genuinely larger fields.
        cycle, slot = divmod(i,4)
        offset = [cycle%2, 2+cycle%2, 4, 5][slot]
        for retry in range(16):
            value = _prototype._candidate(seed, (1024+i*16+retry)*6+offset)
            bg,fg = _palette(value)
            rng = _prototype._rng(seed,'adapter-query-palette',i*16+retry)
            colors = {bg:rng.choice((1,7)),fg:rng.choice((0,3))}
            value = [[colors[c] for c in row] for row in value]
            key = _prototype._digest(value)
            if key not in seen:break
        else:
            raise ValueError('Distinct query budget exhausted; no partial episode')
        seen.add(key);test.append({'input':value,'output':_prototype.transform(value,chosen)})
    return {'train':train,'test':test,'program_solution':program(chosen)}
