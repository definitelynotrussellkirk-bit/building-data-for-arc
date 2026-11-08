"""Native interface; every resource resolves relative to this source folder."""
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_20a9e565_native_family',HERE/'family.py')
family=importlib.util.module_from_spec(spec);spec.loader.exec_module(family)
SETTINGS=('extrapolate','largest_visible_region')

def setting(settings):
    if type(settings)is not dict or set(settings)!={'finish'} or type(settings['finish'])is not str or settings['finish']not in SETTINGS:
        raise ValueError('Expected exactly finish=extrapolate|largest_visible_region')
    return settings['finish']

def program(settings):
    return (HERE/('canonical.rkt' if setting(settings)=='extrapolate' else 'largest_visible_region.rkt')).read_text()

def generate(seed,settings,demos=2,queries=4):
    family.integer(seed,0,2**63-1,'seed');family.integer(demos,2,6,'demos');family.integer(queries,1,4,'queries')
    mode=setting(settings)
    def pair(i):
        g=family.scene(seed,i);return {'input':g,'output':family.solve(g,mode)}
    return {'train':[pair(i)for i in range(demos)],'test':[pair(6+i)for i in range(queries)],
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}

def rival_programs(settings):
    chosen=setting(settings)
    names=('all_nonzero','first_region','last_region','smallest_region','before_crop','next_palette')
    return {'other_setting':program({'finish':SETTINGS[1-SETTINGS.index(chosen)]}),
            **{name:(HERE/('next_palette_largest.rkt' if name=='next_palette' and chosen=='largest_visible_region' else name+'.rkt')).read_text()for name in names}}
