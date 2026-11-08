"""Thin native adapter. No settings, answers or program belong in public views."""
import importlib.util
from pathlib import Path

BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_size_model_'+str(BASE).encode().hex(),BASE/'model.py')
model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(model)
SETTINGS=({'match_by':'occupied_area'},{'match_by':'bbox_area'})


def checked(settings):
    if type(settings) is not dict or set(settings)!={'match_by'} or type(settings['match_by']) is not str or settings not in SETTINGS:
        raise ValueError('expected match_by=occupied_area or bbox_area')
    return settings['match_by']


def program(settings):
    choice=checked(settings);source=(BASE/'canonical.rkt').read_text()
    if choice=='occupied_area':return source
    old="(define match-by 'occupied_area)"
    if source.count(old)!=1:raise ValueError('canonical declaration missing')
    return source.replace(old,"(define match-by 'bbox_area)")


def generate(seed, settings, demos=3, queries=4):
    choice=checked(settings)
    model.integer(seed,0,2**63-1,'seed');model.integer(demos,2,6,'demos');model.integer(queries,4,4,'queries')
    def pair(index,query):
        grid=model.scene(seed,index,query=query)
        return {'input':grid,'output':model.solve(grid,choice)}
    return {'train':[pair(i,False) for i in range(demos)],
            'test':[pair(i,True) for i in range(4)],'program_solution':program(settings)}
