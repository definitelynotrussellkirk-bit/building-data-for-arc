"""One retained-witness replay; current source and actual canonical Racket."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
from reviewer_support import load_selected_generator,canonical_pairs
OUT=Path(__file__).resolve().parent
WORK=OUT.parents[2]
REPO=WORK/'repo'
TASK='4c26a1072222'
OLD=REPO/'generators'/TASK/'counterexamples/review-24dc731d168d4a43-v0001/retained/checks/audit'/TASK
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
started=time.monotonic()
gen,source,source_sha=load_selected_generator(TASK,root=REPO)
assert source_sha=='c55bd10cff6e9f5846e33302b895c6316effa805d46c5b85f77bcdcbd1d99580'
assert sha(OUT/'input.json')=='5078c12d958f02dabee91a8eca6f6dc5b1e2e929f027880615f40f565e64a5ad'
assert sha(OLD/'probe.py')=='dbbdd6de7b183abbb691c9b7ed049d63dc6a404ef95ee425c47aa60906473d1b'
grid=json.loads((OUT/'input.json').read_text())
def rival(g):
    info,errors=gen._analyze(g)
    assert not errors,errors
    result=[[0,0] for _ in range(info['height'])]
    for band in info['bands']:
        follows_cue=(band['source_color_count']==3)==(band['transform'] in (6,7))
        gen._render_band(result,band,band['transform'] if follows_cue else 0,band['mapping'] if follows_cue else {})
    return result
info,errors=gen._analyze(grid)
assert not errors,errors
assert not gen.self_check(grid)
assert gen.strict_canonical_like(grid)
assert info['bands'][0]['source_color_count']==3 and info['bands'][0]['transform']==4
command=[sys.executable,'-m','arcpuzzles','apply',TASK,'--input',str(OUT/'input.json'),'--out',str(OUT/'racket.json')]
proc=subprocess.run(command,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
(OUT/'racket.log').write_text(proc.stdout)
assert proc.returncode==0,proc.stdout
result=json.loads((OUT/'racket.json').read_text())
assert result['executed_rule_hash']=='a86a18b84011'
assert result['generator_sha256']==source_sha
actual=result['results'][0]['output']
assert result['results'][0]['error'] is None
prediction=rival(grid)
retained_actual=json.loads((OLD/'racket-rerun.json').read_text())['results'][0]['output']
retained_rival=json.loads((OLD/'rival.json').read_text())['output']
assert actual==retained_actual
assert prediction==retained_rival
assert actual!=prediction
pairs=canonical_pairs(TASK,root=REPO,labeled_only=True)
canonical_rows=[{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],'rival_fits':rival(p['input'])==p['output']} for p in pairs]
assert len(pairs)==6 and all(r['rival_fits'] for r in canonical_rows)
report={'schema':'bounded-audit-replay-v1','ticket_id':'ticket-7bc6eda8c0a78813','task_id':TASK,'audit_return_id':'review-24dc731d168d4a43:v0001','generator_sha256':source_sha,'rule_hash':result['executed_rule_hash'],'rule_text_sha256':result['rule_text_sha256'],'retained_probe_sha256':sha(OLD/'probe.py'),'retained_input_sha256':sha(OUT/'input.json'),'replay_script_sha256':sha(Path(__file__)),'input':grid,'self_check':gen.self_check(grid),'strict_canonical_like':gen.strict_canonical_like(grid),'observed_overrides':gen.observe_overrides(grid),'band_signature':[{'source_color_count':b['source_color_count'],'transform':gen.TRANSFORM_NAMES[b['transform']],'cue_matches_family':(b['source_color_count']==3)==(b['transform'] in (6,7))} for b in info['bands']],'actual_racket_output':actual,'rival_output':prediction,'matches_retained_actual':actual==retained_actual,'matches_retained_rival':prediction==retained_rival,'outputs_disagree':actual!=prediction,'canonical_rows':canonical_rows,'canonical_pairs_checked':len(pairs),'generated_sample_census_run':False,'targeted_probe_count':1,'racket_command':command,'racket_cwd':str(REPO),'racket_returncode':proc.returncode,'elapsed_seconds':round(time.monotonic()-started,6),'status':'reproduced','scope':'One retained lawful witness plus six existing canonical pairs; no repetition of the historical 600-input census. Current static source still sets n_colors=3 exactly for transform indices 6 and 7. Existing audit remains for maintainer assessment, not automatically cleared.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ['status','generator_sha256','rule_hash','self_check','strict_canonical_like','outputs_disagree','canonical_pairs_checked','targeted_probe_count','elapsed_seconds']},sort_keys=True))
