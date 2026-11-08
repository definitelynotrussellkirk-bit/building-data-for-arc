from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='43f15cc63654'
HERE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
GEN,SOURCE,SHA=load_selected_generator(TASK,root=ROOT)
all_zero=json.loads((HERE/'input-all-zero.json').read_text())
diagonal=json.loads((HERE/'input-diagonal-pair.json').read_text())
base=GEN.generate(721,3,difficulty='medium')
warm=GEN.generate(721,3,difficulty='medium',texture='warm')
palette=GEN.generate(721,3,difficulty='medium',palette_size=9)
distinct=GEN.generate(721,3,difficulty='medium',n_distinct_colors=9)
result={
  'schema':'audit-probe-v1',
  'task_id':TASK,
  'source_path':SOURCE.relative_to(ROOT).as_posix(),
  'source_sha256':SHA,
  'self_check':{
    'all_zero':GEN.self_check(all_zero),
    'diagonal_pair':GEN.self_check(diagonal),
  },
  'documented_invariants':list(getattr(GEN,'INVARIANTS',[])),
  'override_equality':{
    'texture_warm_equals_untextured':warm==base,
    'palette_size_9_equals_untextured':palette==base,
    'n_distinct_colors_9_equals_untextured':distinct==base,
  },
  'semantic_contract':{
    'strict_canonical_like':hasattr(GEN,'strict_canonical_like'),
    'SEMANTIC_WITNESSES':hasattr(GEN,'SEMANTIC_WITNESSES'),
    'lesson_identifiable':hasattr(GEN,'lesson_identifiable'),
  },
}
(HERE/'probe-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
