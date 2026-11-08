from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

ROOT = Path(__file__).resolve().parents[2] / 'repo'
sys.path.insert(0, str(ROOT))


def load_gen(task):
    path = ROOT / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def marker_centers(g):
    h,w=len(g),len(g[0])
    return [(r,c) for r in range(1,h-1) for c in range(1,w-1)
            if g[r][c]==2 and all(g[r+dr][c+dc]==3
                for dr in (-1,0,1) for dc in (-1,0,1) if (dr,dc)!=(0,0))]


def process_markers(g, centers):
    out=deepcopy(g); h,w=len(g),len(g[0])
    col_red=lambda c: sum(g[r][c]==2 for r in range(h)) > h//2
    row_red=lambda r: sum(g[r][c]==2 for c in range(w)) > w//2
    for gr,gc in centers:
        if col_red(gc):
            for c in range(w):
                if (c < gc-1 or c > gc+1) and g[gr][c]==0:
                    out[gr][c]=1
            for oc in range(w):
                if abs(oc-gc)>1 and col_red(oc):
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if (dr,dc)==(0,0): continue
                            r,c=gr+dr,oc+dc
                            if 0<=r<h and 0<=c<w: out[r][c]=1
        elif row_red(gr):
            for r in range(h):
                if (r < gr-1 or r > gr+1) and g[r][gc]==0:
                    out[r][gc]=1
            for orow in range(h):
                if abs(orow-gr)>1 and row_red(orow):
                    for dr in (-1,0,1):
                        for dc in (-1,0,1):
                            if (dr,dc)==(0,0): continue
                            r,c=orow+dr,gc+dc
                            if 0<=r<h and 0<=c<w: out[r][c]=1
    return out


def plus_authority(g):
    out=deepcopy(g); h,w=len(g),len(g[0])
    for r in range(1,h-1):
        for c in range(1,w-1):
            color=g[r][c]
            if color and all(g[r+dr][c+dc]==0 for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))):
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    out[r+dr][c+dc]=color
    return out


def unique_color_shortcut(g):
    out=deepcopy(g); h,w=len(g),len(g[0]); counts=Counter(v for row in g for v in row if v)
    for r in range(1,h-1):
        for c in range(1,w-1):
            color=g[r][c]
            if color and counts[color]==1 and all(g[r+dr][c+dc]==0 for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))):
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    out[r+dr][c+dc]=color
    return out



report={}
# 87079...
t='87079dd3fc4a'; gen=load_gen(t); pairs=canonical_pairs(t, root=ROOT)
unique=[]; seen=set()
for p in pairs:
    key=json.dumps(p['input'],separators=(',',':'))
    if key not in seen:
        seen.add(key); unique.append(p)
canon_counts=[len(marker_centers(p['input'])) for p in unique]
py_mismatches=[i for i,p in enumerate(unique) if process_markers(p['input'], marker_centers(p['input']))!=p['output']]
example_index=next(i for i,p in enumerate(unique) if len(marker_centers(p['input']))>=2)
example=unique[example_index]; cs=marker_centers(example['input'])
first_only=process_markers(example['input'],cs[:1])
diffs=[{'r':r,'c':c,'shortcut':first_only[r][c],'authority':example['output'][r][c]}
       for r in range(len(first_only)) for c in range(len(first_only[0])) if first_only[r][c]!=example['output'][r][c]]
default_counts=Counter()
for band in ('easy','medium','hard'):
    for i in range(200):
        g=gen.generate(810000+i,i,difficulty=band)
        default_counts[len(marker_centers(g))]+=1
report[t]={
    'canonical_unique_pairs':len(unique),
    'canonical_marker_counts':canon_counts,
    'python_authority_mismatches':py_mismatches,
    'default_draw_marker_counts':dict(default_counts),
    'counterexample':{
        'canonical_unique_index':example_index,
        'shape':[len(example['input']),len(example['input'][0])],
        'marker_centers':cs,
        'first_marker_only_diff_count':len(diffs),
        'first_marker_only_diff_sample':diffs[:20],
        'input':example['input'],
        'authority_output':example['output'],
        'first_marker_only_output':first_only,
    }
}

# c969...
t='c96915f33c65'; gen=load_gen(t); pairs=canonical_pairs(t, root=ROOT)
shortcut_fits=[unique_color_shortcut(p['input'])==p['output'] for p in pairs]
repeated_default=0
for band in ('easy','medium','hard'):
    for i in range(200):
        g=gen.generate(910000+i,i,difficulty=band)
        counts=Counter(v for row in g for v in row if v)
        repeated_default += int(any(n>1 for n in counts.values()))
custom=[[0]*9 for _ in range(7)]
custom[2][2]=4; custom[4][6]=4
py=plus_authority(custom); shortcut=unique_color_shortcut(custom)
diffs=[{'r':r,'c':c,'shortcut':shortcut[r][c],'authority':py[r][c]}
       for r in range(7) for c in range(9) if shortcut[r][c]!=py[r][c]]
report[t]={
    'canonical_pairs':len(pairs),
    'unique_color_shortcut_fits_each':shortcut_fits,
    'default_draws_with_repeated_nonzero_color':repeated_default,
    'default_draws_checked':600,
    'counterexample':{
        'input':custom,
        'authority_output':py,
        'python_authority_matches_all_canonical':all(plus_authority(p['input'])==p['output'] for p in pairs),
        'unique_color_shortcut_output':shortcut,
        'diff_count':len(diffs),
        'diffs':diffs,
    }
}

out=Path(__file__).with_name('audit-probe.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:{kk:v for kk,v in val.items() if kk!='counterexample'} for k,val in report.items()},indent=2,sort_keys=True))
print(out)
