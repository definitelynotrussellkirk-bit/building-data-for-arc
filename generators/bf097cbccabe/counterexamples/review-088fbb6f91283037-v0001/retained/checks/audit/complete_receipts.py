"""Join supported Racket receipts to reproducible diagnostic counterexamples."""
import json
from pathlib import Path
from probe_audits import load
ROOT=Path(__file__).resolve().parents[2]
for tid in ('bf097cbccabe','394fc1eaa85e'):
    base=ROOT/'checks/audit'/tid
    report=json.loads((base/'probe.json').read_text())
    racket=json.loads((base/'racket.json').read_text())
    provenance={k:racket[k] for k in ('task_id','generator_sha256','executed_rule_hash','catalog_rule_hash','rule_text_sha256','command','cwd')}
    if tid=='bf097cbccabe':
        records=[]
        for finding in report['findings']:
            row=racket['results'][finding['input_index']]
            records.append({**finding,'input':row['input'],'actual_racket_output':row['output'],
                            'reference_error':row['error'],
                            'rival_output':[[0]] if finding['kind']=='validator_accepts_documented_degenerate' else None,
                            'rival_definition':'Return empty fallback unless there is exactly one singleton shape class' if finding['kind']=='validator_accepts_documented_degenerate' else 'Not applicable: exact-control contract counterexample'})
        (base/'counterexamples.json').write_text(json.dumps({**provenance,'records':records},indent=2)+'\n')
    else:
        m=load(tid)
        def infinity_rival(g):
            out=m.rule_mirror(g)
            for r,c in m._analysis(g)['unreachable_open']:out[r][c]=8
            return out
        canonical=[]
        for line in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open():
            row=json.loads(line)
            if row.get('task_id')==tid:
                canonical=row['train']+(row['test'] if isinstance(row['test'],list) else [row['test']]);break
        matches=[infinity_rival(p['input'])==p['output'] for p in canonical]
        ordinary=racket['results'][:-1]
        normal_matches=[infinity_rival(p['input'])==p['output'] for p in ordinary]
        island=racket['results'][report['island']['input_index']]
        data={**provenance,'input_origin':'handmade, no sampling seed',
              'domain':report['island']['domain'],'self_check':report['island']['self_check'],
              'strict_canonical_like':report['island']['strict_canonical_like'],
              'input':island['input'],'actual_racket_output':island['output'],
              'rival_output':infinity_rival(island['input']),
              'rival_definition':'Canonical mirror plus cyan for cells unreachable from both seeds (infinity == infinity)',
              'reference_error':island['error'],'canonical_matches':matches,
              'canonical_match_count':sum(matches),'canonical_pair_count':len(matches),
              'ordinary_racket_matches':normal_matches,'ordinary_match_count':sum(normal_matches),
              'ordinary_pair_count':len(normal_matches),
              'ordinary_sampling':'seed 7, indices 0..11, easy/medium/hard, 36 grids',
              'island_rival_disagrees':infinity_rival(island['input'])!=island['output']}
        (base/'counterexample.json').write_text(json.dumps(data,indent=2)+'\n')
        print(tid,'canonical',sum(matches),'/',len(matches),'ordinary',sum(normal_matches),'/',len(normal_matches),'island mismatch',data['island_rival_disagrees'])
# Reconcile the six baseline labels against the independently obtained receipt.
p=ROOT/'checks/repro-before'; rr=json.loads((p/'racket.json').read_text()); lesson=json.loads((p/'lesson.json').read_text())
# The local census counterexample uses demos/query fields.
pairs=lesson['demos']+[lesson['query']]
checks=[a['input']==b['input'] and a['output']==b['output'] and b['error'] is None for a,b in zip(pairs,rr['results'])]
out={'task_id':'20859a33c80e','generator_sha256':rr['generator_sha256'],
     'rule_hash':rr['executed_rule_hash'],'rule_text_sha256':rr['rule_text_sha256'],
     'pairs_verified':sum(checks),'pairs':len(pairs),'each_pair_matches':checks,
     'rival_differs_on_query':lesson['rival_query_output']!=rr['results'][-1]['output'],
     'command':rr['command'],'cwd':rr['cwd'],'seed':lesson['seed'],'start':lesson['start']}
(p/'verified-summary.json').write_text(json.dumps(out,indent=2)+'\n')
assert len(checks)==6 and all(checks)
print('baseline six-pair public Racket reconciliation:',checks)
