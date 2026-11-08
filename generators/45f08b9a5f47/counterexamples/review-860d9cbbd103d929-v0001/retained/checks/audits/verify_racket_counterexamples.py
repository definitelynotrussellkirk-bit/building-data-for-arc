from __future__ import annotations
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import rule_application

ROOT = Path('/mnt/data/arcpuzzles_review_002855_work')
CANON = Path('data/canonical/puzzles.jsonl')
PROBE = json.loads((ROOT / 'checks/audits/shortcut_probe.json').read_text())

def sources():
    out = {}
    for line in CANON.read_text().splitlines():
        row = json.loads(line)
        tid = row.get('task_id')
        if tid in {'3a4b67ab16ff','45f08b9a5f47','f1347e0836ec'}:
            out[tid] = row['program_solution']
    return out

def load_generator(task):
    path = ROOT / 'repo/generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'verify_{task}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod

src = sources()
assert set(src) == {'3a4b67ab16ff','45f08b9a5f47','f1347e0836ec'}

cases = {}
with RacketBridge() as bridge:
    for tid in ('3a4b67ab16ff','45f08b9a5f47'):
        item = PROBE[tid]['counterexample']
        actual = bridge.eval_text(rule_application(src[tid], item['input']))
        expected = item['canonical_output_python_mirror']
        shortcut_key = 'endpoint_shortcut_output' if tid == '3a4b67ab16ff' else 'largest_component_shortcut_output'
        cases[tid] = {
            'input': item['input'],
            'actual_racket_output': actual,
            'expected_python_output': expected,
            'shortcut_output': item[shortcut_key],
            'racket_matches_expected': actual == expected,
            'racket_differs_from_shortcut': actual != item[shortcut_key],
        }

    mod = load_generator('f1347e0836ec')
    grid = mod.generate(0, 1, difficulty='easy')
    actual = bridge.eval_text(rule_application(src['f1347e0836ec'], grid))
    expected = mod.rule_mirror(grid)
    rival = mod.SEMANTIC_RIVALS['dot_successor_predicate'](grid)
    analysis = mod._grid_analysis(grid)
    cases['f1347e0836ec'] = {
        'seed': 0,
        'sample_index': 1,
        'difficulty': 'easy',
        'schedule_profile': mod.schedule_profile(0,1,'easy'),
        'input': grid,
        'analysis': {k: analysis[k] for k in ('grid_n','bg_color','dot_color','dot_row','dot_col','on_diagonal','on_anti_diagonal','center_column')},
        'actual_racket_output': actual,
        'expected_python_output': expected,
        'dot_successor_rival_output': rival,
        'racket_matches_expected': actual == expected,
        'racket_differs_from_rival': actual != rival,
    }

result = {
    'schema': 'arc-review-racket-counterexamples-v1',
    'racket_cases': cases,
    'all_authority_checks_pass': all(
        c.get('racket_matches_expected') and (
            c.get('racket_differs_from_shortcut') or c.get('racket_differs_from_rival')
        ) for c in cases.values()
    ),
}
out = ROOT / 'checks/audits/racket_counterexamples.json'
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({
    'all_authority_checks_pass': result['all_authority_checks_pass'],
    'cases': {k: {kk: vv for kk,vv in v.items() if kk.startswith('racket_') or kk in {'schedule_profile','analysis'}} for k,v in cases.items()},
    'output': str(out),
}, indent=2))
raise SystemExit(0 if result['all_authority_checks_pass'] else 1)
