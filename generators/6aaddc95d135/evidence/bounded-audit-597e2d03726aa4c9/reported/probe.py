from __future__ import annotations
import hashlib, json
from reviewer_support import canonical_pairs, find_root, load_selected_generator
ROOT=find_root(__file__)
M, PATH, SHA=load_selected_generator('6aaddc95d135', root=ROOT)
canonical=canonical_pairs('6aaddc95d135', root=ROOT, labeled_only=True)
rows=[]
for pair in canonical:
    rows.append({
        'variant': pair['variant'], 'split': pair['split'], 'pair_index': pair['pair_index'],
        'self_check': M.self_check(pair['input']),
        'mirror_matches': M.rule_mirror(pair['input']) == pair['output'],
    })
generated=[]
for band in ('easy','medium','hard'):
    for index in range(200):
        grid=M.generate(0x6AADD, index, difficulty=band)
        generated.append({
            'band':band,'index':index,'errors':M.self_check(grid),
            'strict_errors':M.strict_canonical_like(grid),
            'rivals':M.lesson_identifiable(
                [{'input':grid,'output':M.rule_mirror(grid)}],
                {'input':grid,'output':M.rule_mirror(grid)},
            ),
        })
report={
  'task_id':'6aaddc95d135','generator_path':str(PATH),'generator_sha256':SHA,
  'canonical':rows,
  'generated_count':len(generated),
  'generated_self_check_failures':sum(bool(x['errors']) for x in generated),
  'strict_hits':sum(not x['strict_errors'] for x in generated),
  'single-pair_rival_findings':sum(bool(x['rivals']) for x in generated),
  'scope':'Canonical mirror/self-check plus 200 generated inputs per band; no universal shortcut proof.',
}
print(json.dumps(report,indent=2))
