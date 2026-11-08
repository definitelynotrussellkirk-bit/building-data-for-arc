"""Finite audit probe; run with public review.py run wrapper from packet root."""
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = 'b8aea529acfd'
g, source, sha = load_selected_generator(TASK, root=ROOT)
canon = canonical_pairs(TASK, root=ROOT, labeled_only=True)
result = {'source_sha256': sha, 'rule_hash': g.RULE_HASH,
          'seed': 370, 'indices_per_band': [0, 31],
          'canonical_count': len(canon), 'canonical': [], 'generated': [],
          'overrides': [], 'raw_windows': []}
inputs = []
expectations = []
for p in canon:
    result['canonical'].append({k:p[k] for k in ('variant','split','pair_index')} | {
        'self_check': g.self_check(p['input']),
        'strict_canonical_like': g.strict_canonical_like(p['input']),
        'mirror_matches_label': g.rule_mirror(p['input']) == p['output'],
        'canonical_shortcut_fits': {n:f(p['input']) == p['output'] for n,f in g.CANONICAL_SHORTCUTS.items()}})
    inputs.append(p['input'])
    expectations.append({'kind':'canonical', 'output':p['output']})
for band in ('easy','medium','hard'):
    draws = [g.generate(370, i, difficulty=band) for i in range(32)]
    for i, inp in enumerate(draws):
        y = g.rule_mirror(inp)
        result['generated'].append({'band':band,'index':i,
            'deterministic': inp == g.generate(370,i,difficulty=band),
            'self_check':g.self_check(inp), 'strict_canonical_like':g.strict_canonical_like(inp),
            'observables':g.semantic_observables(inp),
            'rivals_equal_mirror':{n:f(inp)==y for n,f in g.SEMANTIC_RIVALS.items()}})
    for start in range(8):
        pairs = [{'input':inp,'output':g.rule_mirror(inp)} for inp in draws[start:start+4]]
        result['raw_windows'].append({'band':band,'start':start,
            'unique_inputs':len({json.dumps(p['input']) for p in pairs}),
            'rotation_hook_reasons':[g.lesson_identifiable(pairs[:q]+pairs[q+1:],pairs[q]) for q in range(4)]})
    for i in (1,3):
        inputs.append(draws[i])
        expectations.append({'kind':'generated','band':band,'index':i,'output':g.rule_mirror(draws[i])})
for profile in g.SCENE_PROFILES:
    inp=g.generate(370,0,scene_profile=profile)
    result['overrides'].append({'profile':profile,'observed':g.observe_overrides(inp),
        'self_check':g.self_check(inp,meta={'scene_profile':profile}),
        'strict_canonical_like':g.strict_canonical_like(inp)})
result['claims'] = {
    'all_canonical_valid_and_mirror_equal': all(not p['self_check'] and not p['strict_canonical_like'] and p['mirror_matches_label'] for p in result['canonical']),
    'all_generated_valid_deterministic':all(not p['self_check'] and not p['strict_canonical_like'] and p['deterministic'] for p in result['generated']),
    'all_24_windows_distinct_rotation_safe_against_declared_rivals':all(p['unique_inputs']==4 and not any(p['rotation_hook_reasons']) for p in result['raw_windows']),
    'all_15_profiles_observed_exactly':all(p['observed']=={'scene_profile':p['profile']} and not p['self_check'] and not p['strict_canonical_like'] for p in result['overrides'])}
(HERE/'input.json').write_text(json.dumps({'inputs':inputs})+'\n')
(HERE/'expected.json').write_text(json.dumps(expectations,indent=2)+'\n')
(HERE/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['claims'],sort_keys=True))
assert all(result['claims'].values())
