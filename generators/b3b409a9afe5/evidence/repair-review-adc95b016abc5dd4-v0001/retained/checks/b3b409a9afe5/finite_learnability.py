"""Bounded peer probe: canonical demos versus two historical shortcut families.

Run from packet root:
WORK/.venv/bin/python review.py run --receipt checks/b3b409a9afe5/command_protected.json python3 ../checks/b3b409a9afe5/finite_learnability.py
This is an ambiguity witness for the stated demos/query, not an approval check.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import load_selected_generator, canonical_pairs
from arc_repl.executor import ArcExecutor
from arc_repl.builtins import Grid, _unwrap

TASK = 'b3b409a9afe5'
gen, source, digest = load_selected_generator(TASK, root=ROOT)
expected = '1b82b6e9e911e1dd060db764b2f61f0da61585776093500c000f3df4cc7c988d'
assert digest == expected, 'Source drift: re-review required'
authority = ROOT / 'shared/data/base/solutions/banks/9cb3cc0a41e6/S24_M5__b3b409a9afe5.json'
program = json.loads(authority.read_text())['racket_target']['target_code']
pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
demos = [p for p in pairs if p['split'] == 'train']

def color_max_depth(grid):
    """Wrong rival: one object per color; use deepest disconnected component."""
    by_color = {}
    for comp in gen._components(grid):
        color = comp['color']
        by_color[color] = max(by_color.get(color, 0), gen._onion_depth(comp['cells']))
    return [[sum(d == k for d in by_color.values()) for k in range(1, 5)]]

def bbox_depth(grid):
    """Wrong rival: ceil(minimum bounding-box dimension / 2)."""
    depths = []
    for comp in gen._components(grid):
        r0, c0, r1, c1 = gen._bbox(comp['cells'])
        depths.append((min(r1-r0+1, c1-c0+1)+1)//2)
    return [[depths.count(k) for k in range(1, 5)]]

rivals = {'one_color_one_component_max_depth': color_max_depth, 'bbox_depth': bbox_depth}
report = {'task_id': TASK, 'generator_sha256': digest,
          'authority_path': str(authority.relative_to(ROOT)),
          'authority_sha256': hashlib.sha256(authority.read_bytes()).hexdigest(),
          'program_sha256': hashlib.sha256(program.encode()).hexdigest(),
          'program': program, 'demos': demos,
          'demo_rival_fit': {name: [fn(p['input']) == p['output'] for p in demos]
                             for name, fn in rivals.items()},
          'scope': 'Two canonical train demos, at most 12 ordinary medium generated queries; stop at first color-rival disagreement. No generator edits, battery, safety or audit disposition.'}
draws = []
for i in range(12):
    grid = gen.generate(910000+i, 37*i+11, difficulty='medium')
    assert not gen.self_check(grid)
    mirror = gen.rule_mirror(grid)
    row = {'seed': 910000+i, 'sample_index': 37*i+11, 'difficulty': 'medium',
           'input': grid, 'mirror_output': mirror,
           'rival_outputs': {name: fn(grid) for name, fn in rivals.items()}}
    draws.append(row)
    if color_max_depth(grid) != mirror:
        report['query'] = row
        break
assert 'query' in report, 'No finite witness found in bounded seeds'
report['draw_count'] = len(draws)
report['draws'] = draws
with ArcExecutor({'train': demos, 'test': [{'input': report['query']['input']}]}, use_racket=True) as ex:
    report['runtime_identity'] = ex._bridge.runtime_identity
    assert report['runtime_identity']['backend'] == 'racket'
    assert report['runtime_identity']['protected'] is True
    report['rule_install'] = ex.step(program)
    assert not report['rule_install'].startswith('ERROR'), report['rule_install']
    report['racket_demo_outputs'] = [_unwrap(ex._apply_rule(Grid(p['input']))) for p in demos]
    report['racket_query_output'] = _unwrap(ex._apply_rule(Grid(report['query']['input'])))
assert report['racket_demo_outputs'] == [p['output'] for p in demos]
assert report['racket_query_output'] == report['query']['mirror_output']
for name in rivals:
    assert all(report['demo_rival_fit'][name]), name
    assert report['racket_query_output'] != report['query']['rival_outputs'][name], name
report['conclusion'] = 'Concrete plausible wrong-rule ambiguity for canonical demos plus generated query. It does not establish ambiguity for every ordinary generated episode.'
report['reference_evaluations'] = len(demos)+1
report['probe_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(OUT / 'finite_learnability_protected.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: report[k] for k in ('generator_sha256','draw_count','demo_rival_fit','racket_demo_outputs','racket_query_output','reference_evaluations','conclusion')}, indent=2))
