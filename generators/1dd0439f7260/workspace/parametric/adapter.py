"""Native promotion adapter; protected owner worker replays every output."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('cartesian_spokes',Path(__file__).with_name('prototype.py'))
prototype=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def _mode(settings):
    if type(settings) is not dict or set(settings)!={'paint_policy'}:
        raise ValueError('expected precisely paint_policy')
    m=settings['paint_policy']
    if type(m) is not str or m not in prototype.MODES:raise ValueError('unsupported paint_policy')
    return m


def program(settings):
    return prototype.program_for(_mode(settings))


def generate(seed,settings,demos=3,queries=4,difficulty='medium'):
    return prototype.generate_claims(seed,_mode(settings),demos=demos,queries=queries,difficulty=difficulty)
