"""Prepare and verify small source-bound gallery counterexamples.

Run with the public review wrapper. ``prepare`` reads canonical authoring data;
never run this tool during a visible-only solve. ``verify`` consumes outputs
from the public ``arcpuzzles apply`` command, not a Python-produced label.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK = "0db54f549d0e"
WINDOWS = ((0, 0), (4, 0), (0, 4), (0, 8))


def load_generator():
    root = find_root(__file__)
    candidates = (root / "generators" / TASK / "generator.py",
                  root / "puzzle_generators/per_puzzle" / TASK / "generator.py")
    path = next(p for p in candidates if p.exists())
    spec = importlib.util.spec_from_file_location("gallery_probe_subject", path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return root, path, gen


def rank_rival(grid, reverse=False):
    """Assign roles by numeric color rank, a diagnostic extra rival."""
    colors = sorted({v for row in grid for v in row if v}, reverse=reverse)
    shapes = []
    for color in colors[:4]:
        shapes.append({(r, c) for top, left in WINDOWS for r in range(3)
                       for c in range(3) if grid[top+r][left+c] == color})
    shapes += [set()] * (4-len(shapes))
    out = [[0]*7 for _ in range(7)]
    for i in range(2):
        for j in range(2):
            for r, c in shapes[i] & shapes[2+j]:
                out[4*i+r][4*j+c] = 8
    return out


def prepare(out):
    root, path, gen = load_generator()
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    fits = {name: sum(fn(p['input']) == p['output'] for p in pairs)
            for name, fn in gen.CANONICAL_SHORTCUTS.items()}
    assert fits and all(n == len(pairs) for n in fits.values())
    empty = [[0]*11 for _ in range(7)]
    small = [row[:] for row in empty]
    for r in range(2):
        for c in range(2):
            small[r][c] = 4
    teaching = gen.generate(0, 0, difficulty="easy")
    original = pairs[0]['input']
    # Swap the two canonical row-role colors; output color 8 stays fixed.
    swapped = [[{2: 3, 3: 2}.get(v, v) for v in row] for row in original]
    cases = [
        {"id": "lawful_all_background", "input": empty,
         "domain": "explicit empty_shapes endpoint", "origin": "constructed"},
        {"id": "lawful_top_left_2x2", "input": small,
         "domain": "row0 count 4; other counts 0; monochromatic fixed windows",
         "origin": "constructed, validator-domain and joint-count support"},
        {"id": "teaching_color_roles", "input": teaching,
         "origin": "generated", "seed": 0, "sample_index": 0,
         "difficulty": "easy", "overrides": {}},
        {"id": "canonical_original", "input": original,
         "origin": {k: pairs[0][k] for k in ('variant', 'split', 'pair_index')}},
        {"id": "canonical_row_color_swap", "input": swapped,
         "origin": "same canonical geometry; color permutation 2<->3"},
    ]
    for case in cases:
        case['validator_errors'] = gen.self_check(case['input'])
        assert not case['validator_errors']
        case['observed_counts'] = gen.observe_overrides(case['input'])
    record = {
        "schema": "gallery-source-bound-counterexamples-v1", "task_id": TASK,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_labeled_pairs": len(pairs), "canonical_shortcut_fits": fits,
        "extra_rank_rivals_canonical_fits": {
            str(reverse): sum(rank_rival(p['input'], reverse) == p['output'] for p in pairs)
            for reverse in (False, True)},
        "cases": cases,
        "label_status": "pending public Racket application",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out/'prepared.json').write_text(json.dumps(record, indent=2)+'\n')
    (out/'input.json').write_text(json.dumps([c['input'] for c in cases])+'\n')
    print(json.dumps({"prepared": len(cases), "canonical_shortcut_fits": fits}))


def verify(out, racket):
    _, path, gen = load_generator()
    record = json.loads((out/'prepared.json').read_text())
    actual = json.loads(racket.read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert record['generator_sha256'] == actual['generator_sha256'] == digest
    assert actual['executed_rule_hash'] == record['declared_rule_hash'] == gen.RULE_HASH
    assert len(actual['results']) == len(record['cases'])
    for case, result in zip(record['cases'], actual['results']):
        assert result['input'] == case['input']
        assert result['error'] is None and result['valid_output']
        case['actual_racket_output'] = result['output']
        case['rival_outputs'] = {name: fn(case['input'])
                                for name, fn in gen.LESSON_COMPETITORS.items()}
        case['rivals_refuted'] = [name for name, value in case['rival_outputs'].items()
                                 if value != result['output']]
        case['extra_rank_rivals_refuted'] = {
            str(reverse): rank_rival(case['input'], reverse) != result['output']
            for reverse in (False, True)}
    assert record['cases'][0]['actual_racket_output'] == [[0]*7 for _ in range(7)]
    assert record['cases'][1]['actual_racket_output'] == [[0]*7 for _ in range(7)]
    assert set(record['cases'][2]['rivals_refuted']) == set(gen.LESSON_COMPETITORS)
    assert record['cases'][3]['actual_racket_output'] == record['cases'][4]['actual_racket_output']
    assert 'canonical_color_roles' in record['cases'][4]['rivals_refuted']
    assert record['cases'][4]['extra_rank_rivals_refuted']['False']
    record.update(label_status="verified real Racket outputs",
                  executed_rule_hash=actual['executed_rule_hash'],
                  callable_rule_text_sha256=actual['rule_text_sha256'],
                  racket_receipt_sha256=hashlib.sha256(racket.read_bytes()).hexdigest(),
                  racket_command=actual['command'], racket_cwd=actual['cwd'],
                  scope="Five reference applications; ten declared rivals on one teaching grid; no universal identifiability claim")
    (out/'verified.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({"status": "verified", "real_racket_cases": len(record['cases']),
                      "lawful_linter_witnesses": 2,
                      "teaching_rivals_refuted": len(record['cases'][2]['rivals_refuted']),
                      "canonical_shortcut_fits": record['canonical_shortcut_fits']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'verify'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--racket', type=Path)
    args = parser.parse_args()
    if args.phase == 'verify':
        if args.racket is None:
            parser.error('verify requires --racket')
        verify(args.out, args.racket)
    else:
        prepare(args.out)
