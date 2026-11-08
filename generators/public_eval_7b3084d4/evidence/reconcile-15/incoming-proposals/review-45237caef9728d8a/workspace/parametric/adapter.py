"""Native jigsaw adapter with exact adjacent resources and matched inputs."""
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('_7b3084d4_native_kernel', BASE/'kernel.py')
kernel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kernel)
CORNERS = kernel.CORNERS


def corner_value(settings):
    if (type(settings) is not dict or set(settings) != {'anchor_corner'} or
            type(settings['anchor_corner']) is not str or settings['anchor_corner'] not in CORNERS):
        raise ValueError('settings must name exactly one declared anchor_corner')
    return settings['anchor_corner']


def program(settings):
    corner = corner_value(settings)
    canonical = (BASE/'canonical.rkt').read_text()
    marker = "(define anchor-corner 'northwest)"
    if canonical.count(marker) != 1:
        raise ValueError('Canonical anchor-corner marker changed')
    return canonical if corner == 'northwest' else canonical.replace(marker,f"(define anchor-corner '{corner})")


def generate(seed, settings, demos, queries):
    corner = corner_value(settings)
    kernel.integer(seed,'seed')
    kernel.integer(demos,'demos',2,6)
    kernel.integer(queries,'queries',1,4)
    demo_profiles = [(4,13,15),(5,16,18),(6,18,20),(7,20,22),(9,24,26),(10,26,28)]
    query_profiles = [(3,11,13),(5,15,17),(8,21,23),(12,30,30)]
    def pair(index, profile):
        q,height,width = profile
        grid = kernel.generate(seed,index,quarter_size=q,grid_h=height,grid_w=width)
        return {'input':grid,'output':kernel.solve(grid,corner)}
    return {'train':[pair(i,p) for i,p in enumerate(demo_profiles[:demos])],
            'test':[pair(100+i,p) for i,p in enumerate(query_profiles[:queries])],
            'program_solution':program(settings)}
