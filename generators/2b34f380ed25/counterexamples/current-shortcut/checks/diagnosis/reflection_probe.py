"""Source-bound reflection rival probe, using only public canonical data.

Run from repository: PYTHONPATH=shared/runtime python3 ../checks/diagnosis/reflection_probe.py
This artifact is diagnostic evidence, never a blind solve.
"""
import hashlib
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ROOT = find_root(__file__)
GEN, SOURCE, SHA = load_selected_generator('2b34f380ed25', root=ROOT)

def geometric_reflection(grid):
    facts = GEN._extract_facts(grid)
    macro = facts['macro']
    # Keep the selected fill, panel detection and band painting. Change ONLY
    # the marked-panel operation from order-preserving half-swap to reflection.
    result = [line[:] for line in facts['new_macro']]
    for panel in facts['panel_facts']:
        r0, r1 = panel['row_group']
        c0, c1 = panel['col_group']
        for mark, balanced in zip(panel['vertical_marks'], panel['balanced_vertical']):
            if balanced:
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        result[r][c] = macro[r][c0 + c1 - c]
        for mark, balanced in zip(panel['horizontal_marks'], panel['balanced_horizontal']):
            if balanced:
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        result[r][c] = macro[r0 + r1 - r][c]
    output = [line[:] for line in grid]
    for ri, (rs, re) in enumerate(facts['row_bands']):
        for ci, (cs, ce) in enumerate(facts['col_bands']):
            for r in range(rs, re + 1):
                for c in range(cs, ce + 1):
                    output[r][c] = result[ri][ci]
    return output

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()

def main():
    destination = Path(__file__).parent
    public = canonical_pairs('2b34f380ed25', root=ROOT, labeled_only=True)
    fits = [geometric_reflection(p['input']) == p['output'] for p in public]
    assert len(fits) == 6 and all(fits), fits
    found = None
    # Find a normal consecutive 3-demo,1-query window where the rival survives
    # every demo but gives a different query label. No override manipulation.
    for band in (None, 'easy', 'medium', 'hard'):
        for seed in range(100):
            for start in range(20):
                grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
                agreement = [geometric_reflection(g) == GEN.rule_mirror(g) for g in grids]
                if agreement == [True, True, True, False]:
                    found = {'seed': seed, 'sample_index': start, 'difficulty': band}
                    break
            if found: break
        if found: break
    assert found, 'No ambiguity found in bounded search'
    profiles = [GEN.observe_overrides(g)['scene_profile'] for g in grids]
    for index, grid in enumerate(grids):
        assert not GEN.self_check(grid)
        (destination / f'input_{index}.json').write_text(json.dumps(grid) + '\n')
    query = grids[-1]
    (destination / 'input.json').write_text(json.dumps(query) + '\n')
    (destination / 'expected.json').write_text(json.dumps(GEN.rule_mirror(query)) + '\n')
    (destination / 'reflection.json').write_text(json.dumps(geometric_reflection(query)) + '\n')
    facts = GEN._extract_facts(query)
    report = {
        'task_id': '2b34f380ed25', 'source_sha256': SHA,
        'rival': 'geometric_reflection', 'canonical_pair_fits': fits,
        'lesson': found, 'profiles': profiles, 'agreement': agreement,
        'query_shape': [len(query),len(query[0])], 'query_macro':facts['macro'],
        'query_half_swap_macro':facts['new_macro'],
        'query_self_check': GEN.self_check(query),
        'query_cells_where_rivals_differ': sum(a != b for ra,rb in zip(GEN.rule_mirror(query),geometric_reflection(query)) for a,b in zip(ra,rb)),
        'query_input_sha256':digest(query), 'reference_expected_sha256':digest(GEN.rule_mirror(query)),
        'interpretation':'Exact lawful generated lesson with 3 consecutive demonstrations fitting both rules and next query distinguishing them; selected Racket must still independently validate query.'
    }
    (destination / 'reflection_probe.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
