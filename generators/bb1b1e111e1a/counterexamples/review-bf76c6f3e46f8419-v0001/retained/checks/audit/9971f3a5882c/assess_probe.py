from pathlib import Path
import copy,hashlib,json
from reviewer_support import load_selected_generator
ROOT=Path.cwd();OUT=ROOT.parent/'checks/audit/9971f3a5882c'
p=json.loads((OUT/'probe.json').read_text());r=json.loads((OUT/'racket.json').read_text())
gen,source,sha=load_selected_generator('9971f3a5882c',root=ROOT)
assert sha==p['source_sha256']==r['generator_sha256']
assert r['executed_rule_hash']==gen.RULE_HASH
assert len(r['results'])==len(p['cases'])==5
checks=[]
for case,result in zip(p['cases'],r['results'],strict=True):
 assert result['input']==case['input']
 assert result['output'] is not None
 checks.append({'name':case['name'],'self_check':case['self_check'],'strict_canonical_like':case['strict_canonical_like'],'input_sha256':result['input_sha256'],'output_sha256':result['output_sha256'],'racket_matches_python_mirror':result['output']==case['python_mirror_output'],'racket_matches_rivals':{name:output==result['output'] for name,output in case['rival_outputs'].items()},'semantic_witnesses':case['semantic_witnesses']})
lesson=[{'input':x['input'],'output':x['output']} for x in r['results'][:4]]
hook=gen.lesson_identifiable(copy.deepcopy(lesson[:3]),copy.deepcopy(lesson[3]))
competitors={name:{'fits_all_demos':all(fn(copy.deepcopy(x['input']))==x['output'] for x in lesson[:3]),'same_query_answer':fn(copy.deepcopy(lesson[3]['input']))==lesson[3]['output']} for name,fn in gen.LESSON_COMPETITORS.items()}
tied=checks[-1]
result={'schema':'9971-source-bound-audit-assessment-v1','task_id':'9971f3a5882c','source_sha256':sha,'executed_rule_hash':r['executed_rule_hash'],'cases':checks,
 'answer_equivalent_lesson':{'demos_case_indices':[0,1,2],'query_case_index':3,'hook_reasons':hook,'competitors':competitors,'harmful_query_ambiguity_within_declared_rivals':any(v['fits_all_demos'] and not v['same_query_answer'] for v in competitors.values()),'false_hook_rejection':bool(hook) and all(v['fits_all_demos'] and v['same_query_answer'] for v in competitors.values())},
 'tied_marker_witness':{'case_index':4,'witness_fires':tied['semantic_witnesses']['multiple_same_side_markers'],'named_rival_agrees_with_racket':tied['racket_matches_rivals']['farthest_same_side_marker'],'false_refutation_witness':tied['semantic_witnesses']['multiple_same_side_markers'] and tied['racket_matches_rivals']['farthest_same_side_marker']},
 'scope':'Four actual generated inputs form an answer-equivalent lesson. A fifth input is an explicit mutation accepted by self_check, strict_canonical_like and observe_overrides; it is not claimed to be emitted unchanged by generate. All five reference outputs were executed through the selected-rule CLI and are retained in racket.json.'}
assert all(c['racket_matches_python_mirror'] for c in checks)
assert result['answer_equivalent_lesson']['false_hook_rejection']
assert result['tied_marker_witness']['false_refutation_witness']
(OUT/'assessment.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'source_sha256':sha,'executed_rule_hash':r['executed_rule_hash'],'racket_outputs':len(checks),'all_mirrors_match':True,'false_hook_rejection':result['answer_equivalent_lesson'],'false_refutation_witness':result['tied_marker_witness'],'target_source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==p['source_sha256']},indent=2))
