"""Verify authoritative apply/census receipts and retain exact rival outputs."""
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

p=Path(__file__).resolve().parent
g,source,sha=load_selected_generator('b8aea529acfd',root=find_root(__file__))
r=json.loads((p/'racket.json').read_text())
c=json.loads((p/'census.json').read_text())
expected=json.loads((p/'expected.json').read_text())
probe=json.loads((p/'probe.json').read_text())
assert r['generator_sha256']==c['generator_sha256']==probe['source_sha256']==sha
assert r['executed_rule_hash']==r['catalog_rule_hash']==g.RULE_HASH
assert c['rule_source_sha256'].startswith(g.RULE_HASH)
assert r['rule_hash_matches_catalog'] and len(r['results'])==len(expected)==10
assert all(a['output']==b['output'] and a['valid_output'] and not a['error'] and a['generator_domain']['status']=='valid' for a,b in zip(r['results'],expected))
assert c['status']=='no_ambiguity_found' and c['schedule_coverage']['status']=='complete_fixed_seed'
assert c['summary']['materialized']==24 and c['summary']['rotations']==96
assert all(c['summary'][key]==0 for key in ('ambiguous','ambiguous_rotations','materialization_errors','hook_warnings','scoring_errors','rotation_hook_warnings','rotation_scoring_errors'))
exact=[]
for a,b in zip(r['results'][4:],expected[4:]):
    rivals={n:f(a['input']) for n,f in g.SEMANTIC_RIVALS.items()}
    assert all(v!=a['output'] for v in rivals.values())
    exact.append({'band':b['band'],'seed':370,'sample_index':b['index'],
                  'input':a['input'],'racket_output':a['output'],'rival_outputs':rivals})
(p/'witness-rivals.json').write_text(json.dumps(exact,indent=2)+'\n')
summary={'source_sha256':sha,'selected_rule_sha256':c['rule_source_sha256'],
         'selected_rule_hash':g.RULE_HASH,'rule_text_sha256':r['rule_text_sha256'],
         'racket_apply_outputs_verified':len(expected),
         'generated_draws':len(probe['generated']),
         'joint_shortcut_witnesses':sum(not p['rivals_equal_mirror']['crop_majority_color_bbox'] and not p['rivals_equal_mirror']['crop_modal_background'] for p in probe['generated']),
         'exact_profile_overrides':len(probe['overrides']),
         'census_status':c['status'],'census_summary':c['summary']}
(p/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
