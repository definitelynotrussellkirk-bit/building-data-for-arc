"""Thin native adapter for original-input or evolving-occupancy clearance."""
import importlib.util
from pathlib import Path

HOME=Path(__file__).resolve().parent


def _load(name):
    spec=importlib.util.spec_from_file_location('_clearance_9686a12edc93_'+name,HOME/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def program(settings):
    return _load('native_family').program(settings)


def generate(seed,settings=None,demos=3,queries=4):
    family=_load('native_family')
    inputs=_load('sampler').generate_inputs(seed,demos=demos,queries=queries)
    settings=({'clearance_stage':family.MODES[seed%len(family.MODES)]}
              if settings is None else family.parse_settings(settings))
    return {**{split:[{'input':grid,'output':family.apply(grid,settings)} for grid in inputs[split]]
               for split in ('train','test')},'program_solution':family.program(settings)}
