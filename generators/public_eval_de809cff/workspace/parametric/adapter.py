"""Native deterministic adapter; all imports/resources stay in this directory."""
import copy
import importlib.util
from pathlib import Path
import random

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_de809cff_kernel',BASE/'kernel.py')
kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)


def settings_value(settings):
    if type(settings) is not dict or set(settings)!={'hole_scope'} or type(settings['hole_scope']) is not str or settings['hole_scope'] not in ('all','largest_cluster'):
        raise ValueError('settings must name exactly hole_scope=all|largest_cluster')
    return settings['hole_scope']


def program(settings):
    scope=settings_value(settings)
    canonical=(BASE/'canonical.rkt').read_text()
    if scope=='all':return canonical
    marker="(define scope 'all)"
    if canonical.count(marker)!=1:raise ValueError('canonical selection marker changed')
    return canonical.replace(marker,"(define scope 'largest_cluster)")


def generate(seed,settings,demos,queries):
    scope=settings_value(settings)
    kernel.integer(seed,'seed');kernel.integer(demos,'demos',2,6);kernel.integer(queries,'queries',1,4)
    demo_sizes=[(18,20),(21,19),(22,24),(24,21),(26,28),(29,27)]
    query_sizes=[(18,20),(20,22),(24,27),(30,30)]
    def pair(index,shape):
        g=kernel.generate(seed,index,grid_h=shape[0],grid_w=shape[1])
        return {'input':g,'output':kernel.solve(g,scope)}
    return {'train':[pair(i,s) for i,s in enumerate(demo_sizes[:demos])],
            'test':[pair(100+i,s) for i,s in enumerate(query_sizes[:queries])],
            'program_solution':program(settings)}


def public_turns(episode,presentation_seed):
    """Controller-only list. Give the model ONE view, never this list/directory."""
    kernel.integer(presentation_seed,'presentation_seed')
    if len(episode['test'])!=4:raise ValueError('shuffle a complete four-query bank before truncating')
    order=list(range(4));random.Random(presentation_seed).shuffle(order)
    return [{'train':copy.deepcopy(episode['train']), 'test':[{'input':copy.deepcopy(episode['test'][i]['input'])}]} for i in order]
