from __future__ import annotations
from collections import Counter
import hashlib, importlib.util, json, traceback
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
PATH=REPO/'generators/generic_bar_transfer_gen1/generator.py'
spec=importlib.util.spec_from_file_location('audit_bar',PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

stats=Counter(); count_pairs=Counter(); relative=Counter(); samples=[]; crashes=[]
for band in ('easy','medium','hard'):
    for seed in range(20000,20100):
        stats['tasks_attempted']+=1
        stats[f'tasks_attempted_{band}']+=1
        try:
            task=gen.generate_task(seed,difficulty=band)
        except Exception as exc:
            stats['task_crashes']+=1
            stats[f'task_crashes_{band}']+=1
            if len(crashes)<12:
                crashes.append({'band':band,'seed':seed,'type':type(exc).__name__,'message':str(exc)})
            continue
        stats['tasks_completed']+=1
        stats[f'tasks_completed_{band}']+=1
        for pair in task['train']+task['test']:
            g,out=pair['input'],pair['output']
            stats['pairs']+=1
            stats['python_mirror_mismatches'] += out != gen._apply(g)
            stats['identity_outputs'] += out == g
            h=len(g); bg=Counter(v for row in g for v in row).most_common(1)[0][0]
            objs=gen._components(g,bg)
            bars=[x for x in objs if gen._bbox(x[1])[0]==h-1]
            icons=[x for x in objs if gen._bbox(x[1])[0]!=h-1]
            green=next(x for x in bars if x[0]==3); red=next(x for x in bars if x[0]==2)
            def over(bar):
                b=gen._bbox(bar[1])
                return [x for x in icons if gen._bbox(x[1])[1] <= b[3] and gen._bbox(x[1])[3] >= b[1]]
            gi,ri=over(green),over(red)
            count_pairs[(len(gi),len(ri))]+=1
            gb,rb=gen._bbox(green[1]),gen._bbox(red[1])
            relative['green_left' if gb[1]<rb[1] else 'green_right']+=1
            stats['red_count_gt_1'] += len(ri)>1
            stats['unequal_green_red_counts'] += len(gi)!=len(ri)
            stats['has_barless_tower'] += len(icons)>len(gi)+len(ri)
            top=min(gi,key=lambda x:gen._bbox(x[1])[0])
            pitch=gen._bbox(top[1])[2]-gen._bbox(top[1])[0]+2
            minimum_new_row=min(r-pitch*len(ri) for r,_ in top[1])
            stats['negative_copy_rows'] += minimum_new_row<0
            if len(samples)<6:
                samples.append({'band':band,'seed':seed,'green_count':len(gi),'red_count':len(ri),'green_bar_bbox':gb,'red_bar_bbox':rb,'minimum_new_row':minimum_new_row})

# Capture the deterministic minimal replay traceback separately.
try:
    gen.generate_task(20000,difficulty='hard')
except Exception:
    (Path(__file__).parent/'hard_seed_20000_traceback.txt').write_text(traceback.format_exc())

report={
 'schema':'generic-bar-transfer-audit-probe-v1',
 'source_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'counts':dict(stats),
 'crash_examples':crashes,
 'green_red_count_pairs':{f'{a},{b}':n for (a,b),n in sorted(count_pairs.items())},
 'relative_bar_positions':dict(relative),
 'sample_cases':samples,
 'root_cause':{
   'hard_n_towers':5,
   'failing_icon_width':5,
   'computed_w_need':'1 + 5 * (5 + 1) = 31',
   'advertised_width_cap':30,
   'failing_call':'rng.randint(max(w_need, 22), 30) -> randint(31, 30)',
 },
}
(Path(__file__).parent/'support_probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
