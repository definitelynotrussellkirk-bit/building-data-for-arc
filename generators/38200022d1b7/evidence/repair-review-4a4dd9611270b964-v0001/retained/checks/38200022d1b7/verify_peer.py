import hashlib, json
from collections import Counter
from pathlib import Path
out=Path('../checks/38200022d1b7')
c=json.loads((out/'candidate.json').read_text()); a=json.loads((out/'racket.json').read_text())
p=Path('generators/38200022d1b7/generator.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()==c['generator_sha256']==a['generator_sha256']
assert a['executed_rule_hash']==c['rule_hash'] and a['rule_hash_matches_catalog']
assert len(a['results'])==5
for pair,r in zip(c['pairs'],a['results']):
 assert r['error'] is None and r['valid_output'] and r['generator_domain']['errors']==[]
 assert pair['input']==r['input'] and pair['output']==r['output']
qi=c['query_index']; ds=[i for i in range(5) if i!=qi]
assert all(c['rival_predictions'][i]==a['results'][i]['output'] for i in ds)
x=c['pairs'][qi]['input']; expected=a['results'][qi]['output']; alternative=c['rival_predictions'][qi]
diffs=[{'row':r,'column':col,'racket':v,'rival':alternative[r][col]} for r,row in enumerate(expected) for col,v in enumerate(row) if v!=alternative[r][col]]
assert diffs and c['lesson_identifiable']==[]
summary={k:c[k] for k in ('schema','task_id','generator_sha256','rule_hash','seed','difficulty','sample_indices','query_index','rival','candidate_rotations_examined')}
summary.update({'executed_rule_sha256':a['rule_text_sha256'],'demonstration_indices':ds,'all_five_racket_labels_match_python_mirror':True,'all_five_generator_domain_valid':True,'rival_fits_all_four_demonstrations':True,'lesson_identifiable':[],'query_source_color_counts':dict(Counter(v for row in x for v in row if v not in (0,5))),'query_differences':diffs,'scope':'One frequency-threshold rival, eight candidate rotations screened, five retained inputs labeled by protected canonical Racket. This is an accepted leave-one-out lesson, not an observed production export. No full tests, batteries, broader census, or repair.'})
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lesson={'train':[dict(input=c['pairs'][i]['input'],output=a['results'][i]['output']) for i in ds],'test':[dict(input=x,output=expected)],'alternative_query_output':alternative,'private_provenance':summary}
(out/'original_lesson.json').write_text(json.dumps(lesson,indent=2)+'\n')
print(json.dumps(summary,indent=2))
