from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPO = ROOT / 'WORK' / 'repo'
TASK = '6ecd8be24495'
GEN_PATH = REPO / 'generators' / TASK / 'generator.py'
OLD = REPO / 'generators' / TASK / 'counterexamples' / 'review-2bebd44e54ddafa3-v0001' / 'retained' / 'checks' / 'audit' / '6ecd8be24495-max-distinct-shortcut.json'
OUT = Path(__file__).with_name('result.json')

spec = importlib.util.spec_from_file_location('audit_6ecd', GEN_PATH)
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
sha = hashlib.sha256(GEN_PATH.read_bytes()).hexdigest()
old = json.loads(OLD.read_text())

coercions=[]
for kwargs in [
    {'grid_h':'9'}, {'grid_w':9.8}, {'n_chambers':'3'},
    {'winner_rank':1.9}, {'winner_rank':True},
    {'n_seed_colors':'3'}, {'majority_margin':2.7},
]:
    try:
        grid=gen.generate(123, 5, difficulty='medium', **kwargs)
        coercions.append({'kwargs':kwargs,'accepted':True,'observed':gen.observe_overrides(grid),'shape':[len(grid),len(grid[0])]})
    except Exception as exc:
        coercions.append({'kwargs':kwargs,'accepted':False,'error':f'{type(exc).__name__}: {exc}'})

def rival_rank(analysis):
    counts=[len(rec['counts']) for rec in analysis['chambers']]
    return max(range(len(counts)), key=lambda i: counts[i])

census={'draws':1000,'rival_correct':0,'unique_max':0,'unique_max_correct':0}
first_disagreement=None
for i in range(census['draws']):
    grid=gen.generate(200000+i, i*19+7, difficulty=('easy','medium','hard')[i%3])
    analysis=gen._analysis(grid)
    rr=rival_rank(analysis)
    census['rival_correct'] += int(rr == analysis['winner_rank'])
    distinct=[len(rec['counts']) for rec in analysis['chambers']]
    m=max(distinct)
    if distinct.count(m)==1:
        census['unique_max'] += 1
        census['unique_max_correct'] += int(rr == analysis['winner_rank'])
    if first_disagreement is None and rr != analysis['winner_rank']:
        first_disagreement={
            'seed':200000+i,'sample_index':i*19+7,'difficulty':('easy','medium','hard')[i%3],
            'self_check':gen.self_check(grid),'true_winner_rank':analysis['winner_rank'],'rival_winner_rank':rr,
            'seed_totals':[r['seed_total'] for r in analysis['chambers']],
            'distinct_color_counts':distinct,'input_grid':grid,
            'intended_output':gen.expected_output(grid),
        }
census['rival_rate']=census['rival_correct']/census['draws']

counter=old['counterexample']
replay_grid=counter['input_grid']
report={
    'schema':'arcpuzzles-current-audit-probe-v1','task_id':TASK,'generator_sha256':sha,
    'prior_finding_source_sha256':old['generator_sha256'],'prior_source_still_current':sha==old['generator_sha256'],
    'strict_axis_coercions':coercions,'census':census,'first_current_disagreement':first_disagreement,
    'retained_counterexample_replay':{
        'self_check':gen.self_check(replay_grid),
        'analysis':{
            'winner_rank':gen._analysis(replay_grid)['winner_rank'],
            'seed_totals':[r['seed_total'] for r in gen._analysis(replay_grid)['chambers']],
            'distinct_color_counts':[len(r['counts']) for r in gen._analysis(replay_grid)['chambers']],
        },
        'python_expected_matches_retained_racket':gen.expected_output(replay_grid)==counter['actual_racket_output'],
    },
}
OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'sha':sha,'coercions_accepted':sum(x['accepted'] for x in coercions),'census':census,'prior_source_still_current':report['prior_source_still_current']},indent=2))
