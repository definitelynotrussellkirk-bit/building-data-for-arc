"""Bounded task-only replay: exact controls and two semantic edge surfaces."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
sys.path.insert(0, str(ROOT / 'src'))
from arcpuzzles import Catalog
spec = importlib.util.spec_from_file_location('task_plus', ROOT/'generators/68176b5eb124/generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
OUT = (ROOT / sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT.parent/'checks/68176b5eb124'
OUT.mkdir(exist_ok=True, parents=True)
ARMS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def reference(g):
    out = [row[:] for row in g]
    for r in range(1, len(g)-1):
        for c in range(1, len(g[0])-1):
            colors = [g[r+dr][c+dc] for dr, dc in ARMS]
            if g[r][c] == 0 and colors[0] != 0 and len(set(colors)) == 1:
                out[r][c] = colors[0]
    return out


def pair_rival(g, axis):
    out = [row[:] for row in g]
    for r in range(1, len(g)-1):
        for c in range(1, len(g[0])-1):
            a, b = (g[r][c-1], g[r][c+1]) if axis == 'horizontal' else (g[r-1][c], g[r+1][c])
            if g[r][c] == 0 and a != 0 and a == b:
                out[r][c] = a
    return out


cases = []
for mask in range(16):
    g = [[0]*5 for _ in range(5)]
    for i, (dr, dc) in enumerate(ARMS):
        if mask & (1 << i):
            g[2+dr][2+dc] = 4
    assert bool(gen.self_check(g)) == (mask != 15)
    cases.append({'name': f'arm-mask-{mask}', 'input': g})
# Second surface: exact parameter bounds, feasible counts, identity grammars.
controls = 0
for h in range(5, 15):
    for w in range(5, 15):
        capacity = len(range(1, h-1, 3))*len(range(1, w-1, 3))
        for n in (1, min(6, capacity)):
            g = gen.generate(31, controls, grid_h=h, grid_w=w, n_pluses=n)
            assert (len(g), len(g[0])) == (h, w)
            expected = reference(g)
            changed = sum(a != b for row, out in zip(g, expected) for a, b in zip(row, out))
            assert changed == n, (h, w, n, changed)
            assert not gen.self_check(g)
            controls += 1
        if capacity < 6:
            try:
                gen.generate(0, 0, grid_h=h, grid_w=w, n_pluses=capacity+1)
            except ValueError:
                pass
            else:
                raise AssertionError('impossible count silently accepted')
for seed in range(20):
    g = gen.generate(seed, 0)
    label = reference(g)
    assert pair_rival(g, 'horizontal') != label
    assert pair_rival(g, 'vertical') != label
    assert g == gen.generate(seed, 0)
    cases.append({'name': f'ordinary-seed-{seed}', 'input': g})
for texture in gen.DEGENERATE_TEXTURES:
    for h, w in ((5, 14), (14, 5)):
        g = gen.generate(11, 2, texture=texture, grid_h=h, grid_w=w)
        assert not gen.self_check(g, meta={'texture': texture})
        assert reference(g) == g
        cases.append({'name': f'{texture}-{h}-{w}', 'input': g})
for h, w, n in ((5, 5, 1), (5, 14, 4), (14, 5, 4), (14, 14, 6)):
    cases.append({'name': f'edge-{h}-{w}-{n}', 'input': gen.generate(88, 0, grid_h=h, grid_w=w, n_pluses=n)})
# Verify each palette style and explicit distinct target-arm counts.
for kind in gen.PALETTE_KINDS:
    for distinct in (1, 3, 6):
        g = gen.generate(18, 0, grid_h=14, grid_w=14, n_pluses=6, palette_kind=kind, n_distinct_colors=distinct)
        colors = {g[r-1][c] for r in range(1,len(g)-1) for c in range(1,len(g[0])-1) if reference(g)[r][c] != g[r][c]}
        assert len(colors) == distinct
        controls += 1
(OUT/'racket-inputs.json').write_text(json.dumps({'inputs': [row['input'] for row in cases]}, indent=2)+'\n')
receipt = Catalog(ROOT).apply(gen.TASK_ID, [row['input'] for row in cases], timeout=120, check_generator_domain=True)
(OUT/'racket-labels.json').write_text(json.dumps(receipt, indent=2)+'\n')
assert receipt['executed_rule_hash'] == '2dc205754ece'
assert len(receipt['results']) == len(cases)
for case, result in zip(cases, receipt['results']):
    assert result.get('error') is None, (case['name'], result)
    assert result['output'] == reference(case['input']), case['name']
report = {'task_id': gen.TASK_ID, 'generator_sha256': hashlib.sha256((ROOT/'generators/68176b5eb124/generator.py').read_bytes()).hexdigest(), 'rule_hash': receipt['executed_rule_hash'], 'reference_case_count': len(cases), 'control_cases': controls, 'ordinary_seeds_refuting_both_pair_rivals': 20, 'surfaces': ['all 16 arm-presence masks and ordinary rival discrimination', 'dimension/count feasibility, palette counts and named identity modes'], 'passed': True, 'case_names': [row['name'] for row in cases]}
(OUT/'bounded-verification.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
