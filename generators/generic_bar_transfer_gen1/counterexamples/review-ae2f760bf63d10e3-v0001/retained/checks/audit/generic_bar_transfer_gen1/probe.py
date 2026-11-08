from __future__ import annotations
from collections import Counter
import hashlib, importlib.util, json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / 'repo'
GEN_PATH = REPO / 'generators/generic_bar_transfer_gen1/generator.py'
spec = importlib.util.spec_from_file_location('audit_generic_bar_transfer_gen1', GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

failures=[]
inputs=[]
pair_count=0
for difficulty in ('easy','medium','hard'):
    for seed in range(100):
        try:
            task=module.generate_task(seed,difficulty=difficulty)
        except Exception as exc:
            failures.append({'difficulty':difficulty,'seed':seed,'kind':'generation','error':repr(exc)})
            continue
        pairs=list(task['train'])+list(task['test'])
        if not (2 <= len(task['train']) <= 4 and 1 <= len(task['test']) <= 2):
            failures.append({'difficulty':difficulty,'seed':seed,'kind':'pair_counts'})
        for index,pair in enumerate(pairs):
            pair_count += 1
            grid=pair['input']; output=pair['output']
            inputs.append(json.dumps(grid,separators=(',',':')))
            if output != module._apply(grid):
                failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'python_mirror'})
                continue
            h=len(grid); w=len(grid[0])
            if len(output)!=h or any(len(row)!=w for row in output):
                failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'shape'})
            bg=Counter(v for row in grid for v in row if v != 0).most_common(1)[0][0]
            objs=module._components(grid,bg)
            bars=[(col,comp) for col,comp in objs if module._bbox(comp)[0]==h-1]
            icons=[(col,comp) for col,comp in objs if module._bbox(comp)[0]!=h-1]
            red=[obj for obj in bars if obj[0]==2]
            green=[obj for obj in bars if obj[0]==3]
            if len(bars)!=2 or len(red)!=1 or len(green)!=1:
                failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'legend','bars':[(c,module._bbox(x)) for c,x in bars]})
                continue
            def over(bar):
                bb=module._bbox(bar[1])
                return [obj for obj in icons if module._bbox(obj[1])[1] <= bb[3] and module._bbox(obj[1])[3] >= bb[1]]
            red_icons=over(red[0]); green_icons=over(green[0])
            if not red_icons or not green_icons:
                failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'empty_tower'})
            for _color,cells in red_icons:
                if any(output[r][c] != 5 for r,c in cells):
                    failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'source_not_gray'})
                    break
            for _color,cells in red+green:
                if any(output[r][c] != bg for r,c in cells):
                    failures.append({'difficulty':difficulty,'seed':seed,'pair':index,'kind':'bar_not_erased'})
                    break

summary={
    'task_id':'generic_bar_transfer_gen1',
    'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'seeds_per_band':100,
    'bands':['easy','medium','hard'],
    'tasks':300,
    'pairs':pair_count,
    'unique_inputs':len(set(inputs)),
    'failures':failures,
    'status':'no_issue_found' if not failures else 'findings',
    'racket_parity_evidence':'checks/audit/generic_bar_transfer_gen1/parity.log',
}
out=Path(__file__).resolve().parent/'summary.json'
out.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
raise SystemExit(1 if failures else 0)
