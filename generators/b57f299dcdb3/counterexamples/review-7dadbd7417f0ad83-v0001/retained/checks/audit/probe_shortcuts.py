from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
OUT = Path(__file__).with_name('shortcut_probe.json')


def b57_probe(gen, per_band=300):
    names = [
        'global_most_frequent_role', 'first_plus', 'last_plus',
        'min_petal_color', 'max_petal_color', 'first_nonbackground_role',
    ]
    totals = Counter()
    hits = Counter()
    first_counterexamples = {}
    profile_counts = Counter()
    for band_i, band in enumerate(('easy','medium','hard')):
        for i in range(per_band):
            seed = 1_000_000 + band_i * 100_000 + i
            grid = gen.generate(seed, i, difficulty=band)
            analysis = gen._analyze(grid)
            profile_counts[(band, analysis['scene_profile'])] += 1
            bg = analysis['background']
            centers = gen._plus_centers(grid, bg)
            correct = gen.solve_python(grid)[0][0]
            eligible = [c for c in {v for row in grid for v in row} if c not in (0,4,bg)]
            global_counts = Counter(v for row in grid for v in row if v in eligible)
            first_nonbg = next(v for row in grid for v in row if v not in (0,4,bg))
            preds = {
                'global_most_frequent_role': max(global_counts, key=global_counts.get),
                'first_plus': centers[0][2],
                'last_plus': centers[-1][2],
                'min_petal_color': min(c for _,_,c in centers),
                'max_petal_color': max(c for _,_,c in centers),
                'first_nonbackground_role': first_nonbg,
            }
            for name,pred in preds.items():
                totals[name]+=1
                hits[name]+=pred==correct
                if pred!=correct and name not in first_counterexamples:
                    first_counterexamples[name] = {
                        'band':band,'seed':seed,'sample_index':i,
                        'scene_profile':analysis['scene_profile'],
                        'correct':correct,'prediction':pred,
                        'center_colors':[c for _,_,c in centers],
                        'global_role_counts':dict(global_counts),
                    }
    return {
        'draws': sum(totals.values())//len(names),
        'accuracy': {n:hits[n]/totals[n] for n in names},
        'hits':dict(hits),'totals':dict(totals),
        'first_counterexamples':first_counterexamples,
        'profile_counts':{f'{b}:{p}':n for (b,p),n in profile_counts.items()},
    }


def apply_diff_no_carry(gen, grid):
    _, h, sections = gen._split_sections(grid)
    s_pprev,s_prev,s_last=sections[-3:]
    d_prev=gen._diff(s_pprev,s_prev)
    d_last=gen._diff(s_prev,s_last)
    shift=(min(d[1] for d in d_last)-min(d[1] for d in d_prev)) if d_prev and d_last else 0
    out=[row[:] for row in s_last]
    for row,col,old,new in d_last:
        target=col+shift
        if 0<=target<len(out[0]) and out[row][target]==old:
            out[row][target]=new
    return out


def shift_last(gen, grid):
    _,h,sections=gen._split_sections(grid)
    s_pprev,s_prev,s_last=sections[-3:]
    d_prev=gen._diff(s_pprev,s_prev); d_last=gen._diff(s_prev,s_last)
    shift=(min(d[1] for d in d_last)-min(d[1] for d in d_prev)) if d_prev and d_last else 0
    out=gen._blank(h,len(s_last[0]))
    for r,row in enumerate(s_last):
        for c,v in enumerate(row):
            if v and 0<=c+shift<len(row): out[r][c+shift]=v
    return out


def aea_probe(gen, per_band=300):
    names=['copy_last','repeat_latest_diff_no_carry','shift_whole_last']
    totals=Counter();hits=Counter();first_counterexamples={};profile_counts=Counter();carry_counts=Counter()
    for band_i,band in enumerate(('easy','medium','hard')):
        for i in range(per_band):
            seed=2_000_000+band_i*100_000+i
            grid=gen.generate(seed,i,difficulty=band)
            a=gen._analyze(grid); profile=a['scene_profile'];profile_counts[(band,profile)]+=1
            carry_counts[(band,'carry' if a['carry_row_count'] else 'no_carry')]+=1
            _,_,sections=gen._split_sections(grid)
            correct=gen.solve_python(grid)
            preds={
                'copy_last':sections[-1],
                'repeat_latest_diff_no_carry':apply_diff_no_carry(gen,grid),
                'shift_whole_last':shift_last(gen,grid),
            }
            for name,pred in preds.items():
                totals[name]+=1;hits[name]+=pred==correct
                if pred!=correct and name not in first_counterexamples:
                    first_counterexamples[name]={
                        'band':band,'seed':seed,'sample_index':i,'scene_profile':profile,
                        'section_height':a['section_height'],'width':a['width'],
                        'col_shift':a['col_shift'],'carry_row_count':a['carry_row_count'],
                    }
    return {
        'draws':sum(totals.values())//len(names),
        'accuracy':{n:hits[n]/totals[n] for n in names},
        'hits':dict(hits),'totals':dict(totals),
        'first_counterexamples':first_counterexamples,
        'profile_counts':{f'{b}:{p}':n for (b,p),n in profile_counts.items()},
        'carry_counts':{f'{b}:{p}':n for (b,p),n in carry_counts.items()},
    }


def main():
    b57, p1, h1 = load_selected_generator('b57f299dcdb3',root=ROOT)
    aea, p2, h2 = load_selected_generator('aea4d55345a1',root=ROOT)
    report={
        'b57f299dcdb3':{'source_sha256':h1,**b57_probe(b57)},
        'aea4d55345a1':{'source_sha256':h2,**aea_probe(aea)},
    }
    OUT.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
