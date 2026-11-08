"""Standalone native counted-canvas family with matched setting inputs."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_f931b4a8_native_kernel', BASE / 'kernel.py')
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)
MODES = kernel.MODES


def mode_value(settings):
    if (type(settings) is not dict or set(settings) != {'background_mode'}
            or type(settings['background_mode']) is not str or settings['background_mode'] not in MODES):
        raise ValueError('settings must name exactly one declared background_mode')
    return settings['background_mode']


def program(settings):
    mode = mode_value(settings)
    canonical = (BASE / 'canonical.rkt').read_text()
    marker = "(define background-mode 'stretch)"
    if canonical.count(marker) != 1:
        raise ValueError('Canonical background-mode marker changed')
    return canonical if mode == 'stretch' else canonical.replace(marker, "(define background-mode 'repeat)")


def generate(seed, settings, demos, queries):
    mode = mode_value(settings)
    kernel.integer(seed, 'seed')
    kernel.integer(demos, 'demos', 2, 6)
    kernel.integer(queries, 'queries', 1, 4)
    demo_profiles = [(3, 6, 9), (4, 12, 8), (5, 10, 15), (6, 18, 12), (7, 14, 21), (8, 16, 24)]
    query_profiles = [(2, 4, 4), (4, 12, 16), (6, 18, 30), (15, 30, 30)]
    def pair(index, profile):
        side, height, width = profile
        g = kernel.generate(seed, index, quadrant_side=side, output_h=height, output_w=width)
        return {'input': g, 'output': kernel.solve(g, mode)}
    return {'train': [pair(i, profile) for i, profile in enumerate(demo_profiles[:demos])],
            'test': [pair(100 + i, profile) for i, profile in enumerate(query_profiles[:queries])],
            'program_solution': program(settings)}
