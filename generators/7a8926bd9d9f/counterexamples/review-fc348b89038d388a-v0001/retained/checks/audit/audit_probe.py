from __future__ import annotations
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'

def load(task):
    path=REPO/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,path)
    module=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def nonzero_colors(grid):
    return sorted({value for row in grid for value in row if value})

def paired_only_rival(grid):
    h=len(grid); w=len(grid[0]); out=[row[:] for row in grid]
    by_ring={}
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color:
                ring=min(r,c,h-1-r,w-1-c)
                by_ring.setdefault(ring,[]).append((r,c,color))
    for ring,cells in by_ring.items():
        far=h-1-ring
        corners=[(r,c,color) for r,c,color in cells if r in (ring,far) and c in (ring,far)]
        for _r,_c,color in corners:
            for rr,cc in ((ring,ring),(ring,far),(far,ring),(far,far)):
                out[rr][cc]=color
        noncorners=[(r,c,color) for r,c,color in cells if not (r in (ring,far) and c in (ring,far))]
        color_groups={}
        for r,c,color in noncorners:
            color_groups.setdefault(color,[]).append((r,c))
        for color,positions in color_groups.items():
            # Shortcut: a side role is activated only by a same-color witness pair.
            if len(positions) < 2:
                continue
            offsets=range(ring+2,far-1,2)
            for offset in offsets:
                for rr,cc in ((ring,offset),(far,offset),(offset,ring),(offset,far)):
                    out[rr][cc]=color
    return out

m=load('7a8926bd9d9f')
override_samples=0
override_identical=0
requested_violations={"n_rects_1":0,"n_rects_8":0}
texture_alias_identical=0
for band_index,band in enumerate(('easy','medium','hard')):
    for index in range(100):
        seed=910000+10000*band_index+index
        sample=index
        one=m.generate(seed,sample,difficulty=band,n_rects=1)
        eight=m.generate(seed,sample,difficulty=band,n_rects=8)
        default=m.generate(seed,sample,difficulty=band)
        warm1=m.generate(seed,sample,difficulty=band,palette_kind='warm')
        warm2=m.generate(seed,sample,difficulty=band,texture='warm')
        override_samples+=1
        override_identical += one==eight
        requested_violations['n_rects_1'] += len(nonzero_colors(one)) != 1
        requested_violations['n_rects_8'] += len(nonzero_colors(eight)) != 8
        texture_alias_identical += default==warm1==warm2
axis=m.generate(1,0,texture='axis_aligned')
seven_report={
    'task_id':'7a8926bd9d9f',
    'generator_sha256':__import__('hashlib').sha256((REPO/'generators/7a8926bd9d9f/generator.py').read_bytes()).hexdigest(),
    'axis_aligned':{
        'self_check':m.self_check(axis),
        'input_path':'checks/audit/7a8926bd9d9f/input.json',
        'racket_path':'checks/audit/7a8926bd9d9f/racket.json',
        'racket_output_is_identity':json.load(open(ROOT/'checks/audit/7a8926bd9d9f/racket.json'))['results'][0]['output']==axis,
    },
    'override_probe':{
        'bands':['easy','medium','hard'],
        'samples_per_band':100,
        'draws':override_samples,
        'n_rects_1_vs_8_byte_identical':override_identical,
        'n_rects_contract_violations':requested_violations,
        'default_palette_kind_warm_texture_warm_all_identical':texture_alias_identical,
        'seed_formula':'910000 + 10000*band_index + index',
        'sample_index':'index',
    },
}
Path(ROOT/'checks/audit/7a8926bd9d9f/probe.json').write_text(json.dumps(seven_report,indent=2,sort_keys=True)+'\n')

n=load('d2534264df36')
paired_matches=0
samples=0
profiles={profile:0 for profile in n.SCENE_PROFILES}
for profile_index,profile in enumerate(n.SCENE_PROFILES):
    for band_index,band in enumerate(('easy','medium','hard')):
        for index in range(50):
            grid=n.generate(920000+10000*profile_index+1000*band_index+index,index,difficulty=band,scene_profile=profile)
            expected=n.solve_python(grid)
            paired_matches += paired_only_rival(grid)==expected
            samples += 1
            profiles[profile] += 1
single=json.load(open(ROOT/'checks/audit/d2534264df36/input.json'))
racket=json.load(open(ROOT/'checks/audit/d2534264df36/racket.json'))['results'][0]['output']
rival=paired_only_rival(single)
Path(ROOT/'checks/audit/d2534264df36/paired_only_rival.json').write_text(json.dumps(rival,indent=2)+'\n')
d_report={
    'task_id':'d2534264df36',
    'generator_sha256':__import__('hashlib').sha256((REPO/'generators/d2534264df36/generator.py').read_bytes()).hexdigest(),
    'generated_domain_probe':{
        'profiles':profiles,
        'bands':['easy','medium','hard'],
        'samples':samples,
        'paired_only_rival_matches_python_authority_mirror':paired_matches,
        'seed_formula':'920000 + 10000*profile_index + 1000*band_index + index',
        'sample_index':'index',
    },
    'single_witness_counterexample':{
        'self_check':n.self_check(single),
        'input_path':'checks/audit/d2534264df36/input.json',
        'racket_path':'checks/audit/d2534264df36/racket.json',
        'paired_only_rival_path':'checks/audit/d2534264df36/paired_only_rival.json',
        'rival_differs_from_racket':rival!=racket,
    },
}
Path(ROOT/'checks/audit/d2534264df36/probe.json').write_text(json.dumps(d_report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'7a':seven_report,'d253':d_report},indent=2,sort_keys=True))
