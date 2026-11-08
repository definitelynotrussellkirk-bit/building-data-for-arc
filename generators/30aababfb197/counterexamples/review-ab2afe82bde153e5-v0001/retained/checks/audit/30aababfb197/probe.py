from __future__ import annotations
import importlib.util, json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PATH=ROOT/'repo/generators/30aababfb197/generator.py'
spec=importlib.util.spec_from_file_location('g30', PATH)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def schedule_rival(grid):
    a=g._analysis_or_raise(grid)
    comps=list(a['components'])
    if len(comps)==3:
        # Generated 3-blob cases have sizes t-2, t, t+2.
        chosen=sorted(comps,key=lambda x:x['size'])[1]
    else:
        # In 4-blob defaults, sample_index parity fixes palette_kind and
        # sample_index % 4 fixes the target quadrant: warm -> top-right,
        # varied -> bottom-right.  Recover the quadrant from body geometry.
        body_h=len(grid)-1; width=len(grid[0])
        gap_r=(body_h-1)//2; gap_c=(width-1)//2
        by_slot={}
        for comp in comps:
            r1,c1,r2,c2=comp['bbox']
            slot=(2 if r1>gap_r else 0)+(1 if c1>gap_c else 0)
            by_slot[slot]=comp
        kind=g.observe_overrides(grid)['palette_kind']
        chosen=by_slot[{'warm':1,'varied':3}[kind]]
    return g._crop_component(a['body'],chosen)

counts={}
examples=[]
for band in ('easy','medium','hard'):
    ok=0
    total=0
    for seed in range(100):
        for idx in range(12):
            grid=g.generate(seed,idx,difficulty=band)
            total += 1
            ok += schedule_rival(grid)==g.rule_mirror(grid)
    counts[band]={'matched':ok,'total':total}

# Find a lawful key-reassignment counterexample to show the shortcut is not the rule.
cex=None
for seed in range(1000):
    for idx in range(12):
        grid=g.generate(seed,idx,difficulty='medium')
        a=g._analysis_or_raise(grid)
        original=schedule_rival(grid)
        for comp in a['components']:
            if comp is a['target']:
                continue
            candidate=[row[:] for row in grid]
            key_col=a['key_column']
            candidate[-1]=[0]*len(candidate[-1])
            candidate[-1][key_col]=comp['color']
            if g.self_check(candidate)==[]:
                intended=g.rule_mirror(candidate)
                rival=schedule_rival(candidate)
                if intended!=rival:
                    cex={
                        'seed':seed,'sample_index':idx,'difficulty':'medium',
                        'input':candidate,'actual_rule_output':intended,'schedule_rival_output':rival,
                        'original_generated_input':grid,
                        'generator_self_check':g.self_check(candidate),
                        'note':'Changed only the bottom-row key to another lawful body component; body schedule stayed fixed.'
                    }
                    break
        if cex: break
    if cex: break
out={
 'task_id':'30aababfb197',
 'generator_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'default_schedule_rival_counts':counts,
 'counterexample':cex,
}
Path(__file__).with_name('probe.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
