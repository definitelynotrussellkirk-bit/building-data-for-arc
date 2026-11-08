"""Disjoint projection, bridge and largest-interior rules on shared scenes."""
import importlib.util
from pathlib import Path
from copy import deepcopy
HERE=Path(__file__).resolve().parent

def _load(name):
    spec=importlib.util.spec_from_file_location('rectangle_union_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=_load('prototype');interior=_load('interior_family')
SETTINGS=('project_only','project_then_bridge','largest_interior')

def normalize_settings(settings=None):
    if settings is None:return {'finish_rule':'project_only'}
    if type(settings) is dict and set(settings)=={'rectangle_scope'}:
        value=interior._validate_settings(settings)
        return {'finish_rule':'project_only' if value=='all_rectangles' else value}
    if type(settings) is not dict or set(settings)!={'finish_rule'} or type(settings['finish_rule']) is not str or settings['finish_rule'] not in SETTINGS:
        raise ValueError('settings must name one declared finish_rule')
    return dict(settings)

def program(settings=None):
    mode=normalize_settings(settings)['finish_rule']
    if mode=='largest_interior':return interior.program({'rectangle_scope':mode})
    return old.program({'finish_rule':mode})

def solve_python(grid,settings):
    mode=normalize_settings(settings)['finish_rule']
    if mode=='largest_interior':return interior.transform(grid,{'rectangle_scope':mode})
    return old.solve_python(grid,{'finish_rule':mode})

def _input(seed,split,index):
    old._integer(seed,0,2**63-1,'seed')
    height=(20,20,22,24,26,28)[index] if split=='train' else (21,24,27,30)[index]
    bg=old.BACKGROUND_COLORS[(seed+index)%len(old.BACKGROUND_COLORS)]
    grid=[[bg]*30 for _ in range(height)]
    rng=old._rng(seed,split,index)
    row=height//2+rng.choice((-1,0,1))
    side=rng.choice((7,8))
    thin_width=13 if side==8 else rng.choice((12,13))
    thin_left=rng.choice((0,1,2))
    compact_left=30-side-rng.choice((0,1))
    # Broad, thin outline has greater perimeter but smaller interior than the
    # compact rectangle. Opposite outward rays align to teach the bridge.
    old._draw_outline(grid,top=row-1,left=thin_left,height=4,width=thin_width,side='left',gap_offset=1)
    old._draw_outline(grid,top=row-3,left=compact_left,height=side,width=side,side='right',gap_offset=3)
    # One unmatched orthogonal ray rejects bridge-on-any-border-contact.
    old._draw_outline(grid,top=1,left=16,height=4,width=4,side='up',gap_offset=1)
    if index%2:
        grid=[list(row) for row in zip(*[r[::-1] for r in grid[::-1]])]
    interior.rectangle_facts(grid)
    old.analyze_input(grid)
    return grid

def generate(seed,settings=None,demos=3,queries=4):
    old._integer(seed,0,2**63-1,'seed');old._integer(demos,2,6,'demos');old._integer(queries,1,4,'queries')
    settings=normalize_settings(settings)
    def pair(g):return {'input':deepcopy(g),'output':solve_python(g,settings)}
    train=[pair(_input(seed,'train',i)) for i in range(demos)]
    test=[pair(_input(seed,'test',i)) for i in range(queries)]
    if len({repr(p['input']) for p in train+test})!=demos+queries:raise RuntimeError('duplicate inputs')
    return {'train':train,'test':test,'program_solution':program(settings)}
