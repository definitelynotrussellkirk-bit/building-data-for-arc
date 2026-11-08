"""Native adapter; every runtime dependency is adjacent to this file."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_d59b0160_native_kernel', BASE / 'kernel.py')
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)
MODES = kernel.MODES


def mode_value(settings):
    if (type(settings) is not dict or set(settings) != {'match_mode'}
            or type(settings['match_mode']) is not str or settings['match_mode'] not in MODES):
        raise ValueError('settings must name exactly one declared match_mode')
    return settings['match_mode']


def program(settings):
    mode = mode_value(settings)
    canonical = (BASE / 'canonical.rkt').read_text()
    marker = "(define match-mode 'contains_all)"
    if canonical.count(marker) != 1:
        raise ValueError('Canonical match-mode marker changed')
    return canonical if mode == 'contains_all' else canonical.replace(marker, f"(define match-mode '{mode})")


def generate(seed, settings, demos, queries):
    mode = mode_value(settings)
    kernel.integer(seed, 'seed')
    kernel.integer(demos, 'demos', 2, 6)
    kernel.integer(queries, 'queries', 1, 4)
    demo_shapes = [(13, 16), (16, 15), (18, 21), (23, 19), (24, 26), (29, 27)]
    query_shapes = [(13, 14), (16, 22), (24, 27), (30, 30)]
    def pair(index, shape):
        grid = kernel.generate(seed, index, grid_h=shape[0], grid_w=shape[1], key_count=2 + (index % 3))
        return {'input': grid, 'output': kernel.solve(grid, mode)}
    return {'train': [pair(i, shape) for i, shape in enumerate(demo_shapes[:demos])],
            'test': [pair(100 + i, shape) for i, shape in enumerate(query_shapes[:queries])],
            'program_solution': program(settings)}
