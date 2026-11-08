"""Promotion adapter reusing the reviewed crossing-band sampler and rules."""
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec=spec_from_file_location('_crossing_bands_7b0cb3b9a618',Path(__file__).with_name('layer_selection.py'))
_prototype=module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _settings(settings):
    if type(settings) is not dict or set(settings)!={'target_layer'}:
        raise ValueError('Declare exactly target_layer=front|back')
    return _prototype._setting(settings['target_layer'])


def program(settings):
    return _prototype.program_for(_settings(settings))


def generate(seed,settings,demos,queries):
    """Use matched inputs and joint teaching; the shared worker checks labels."""
    target=_settings(settings)
    _prototype._integer(seed,'seed',0,2**63-1)
    _prototype._integer(demos,'demos',2,12)
    _prototype._integer(queries,'queries',1,32)
    input_seed=int.from_bytes(hashlib.sha256(b'crossing-band-input-v1:'+str(seed).encode()).digest(),'big')
    cache={}
    def scene(index):
        if index not in cache:
            grid=_prototype.sample_input(input_seed,index)
            cache[index]=(grid,_prototype.visible_endpoints(grid),_prototype.rival_predictions(grid))
        return cache[index]
    for attempt in range(_prototype.MAX_EPISODE_ATTEMPTS):
        scenes=[scene(attempt+i) for i in range(demos+queries)]
        if len({_prototype._key(s[0]) for s in scenes})!=len(scenes):
            continue
        teaching=scenes[:demos]
        # Choose the input schedule without consulting the selected target.
        # Query outputs do not enter either teaching test.
        if any(all(rivals[name]==[[endpoints[setting]]] for _,endpoints,rivals in teaching)
               for setting in _prototype.SETTINGS for name in teaching[0][2]):
            continue
        pairs=[{'input':grid,'output':[[endpoints[target]]]} for grid,endpoints,_ in scenes]
        return {'train':pairs[:demos],'test':pairs[demos:],'program_solution':program(settings)}
    raise ValueError('No setting-neutral lesson within64schedule attempts; no partial episode')
