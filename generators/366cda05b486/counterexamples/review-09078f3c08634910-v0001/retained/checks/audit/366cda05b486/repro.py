"""Reproduce audit without modifying generator or shared sources.

From WORK/repo:
  PYTHONPATH=src:shared/runtime ../.venv/bin/python ../checks/audit/366cda05b486/repro.py prepare
From packet root (the supported runtime):
  python3 review.py run python3 -m arcpuzzles generate 366cda05b486 --seed 46 --difficulty easy --allow-unapproved --out ../checks/audit/366cda05b486/lesson.jsonl
  python3 review.py run python3 -m arcpuzzles apply 366cda05b486 --input ../checks/audit/366cda05b486/input.json --out ../checks/audit/366cda05b486/racket.json
From WORK/repo:
  PYTHONPATH=src:shared/runtime ../.venv/bin/python ../checks/audit/366cda05b486/repro.py verify

The rival uses no blue/cyan selection cue: choose the largest nonzero cardinal
connected cluster, retaining holes, crop tightly and recolor to 8. Ties use the
first cluster encountered in row-major order; this witness has no ties.
"""
import hashlib
import importlib.util
import json
import sys
from collections import deque
from pathlib import Path
from arcpuzzles.catalog import Catalog
from reviewer_support import canonical_pairs

TASK = '366cda05b486'
ROOT = Path.cwd().resolve()
OUT = ROOT.parent / 'checks/audit' / TASK
GENERATOR = ROOT / 'generators' / TASK / 'generator.py'


def load_module():
    spec = importlib.util.spec_from_file_location('audit_366c_generator', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contact_clusters(grid):
    h, w = len(grid), len(grid[0])
    seen, clusters = set(), []
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            cells, todo = set(), deque([(r, c)])
            seen.add((r, c))
            while todo:
                rr, cc = todo.popleft()
                cells.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (rr + dr, cc + dc)
                    if (0 <= nxt[0] < h and 0 <= nxt[1] < w
                            and grid[nxt[0]][nxt[1]] and nxt not in seen):
                        seen.add(nxt)
                        todo.append(nxt)
            clusters.append(cells)
    return clusters


def crop(cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def rival(grid):
    return crop(max(contact_clusters(grid), key=len))


def write(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2) + '\n')


def prepare():
    module = load_module()
    pairs = canonical_pairs(TASK, root=ROOT)
    generated = [module.generate(46, i, difficulty='easy') for i in range(4)]
    write('input.json', [p['input'] for p in pairs] + generated)
    rule = Catalog(ROOT).get(TASK)['variants'][0]['program_solution']
    write('source_hashes.json', {
        'generator_path': 'repo/generators/' + TASK + '/generator.py',
        'generator_sha256': hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        'canonical_rule_normalized_hash': hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
        'canonical_rule_source_sha256': hashlib.sha256(rule.encode()).hexdigest(),
        'canonical_input_count': len(pairs),
        'generation': {'seed': 46, 'difficulty': 'easy', 'sample_indices': list(range(4)),
                       'train': 3, 'test': 1, 'overrides': {}, 'sampling': 'default sequential production sampler'},
        'prior_lead': 'generators/366cda05b486/evidence/associated_notes.jsonl: '
                      'GNOTE-001102 tested only all-nonzero, blue-only and cyan-cluster rivals',
        'review_index': 'absent',
    })
    print('Prepared seven grids: canonical 0..2, generated demos 3..5, query 6.')


def verify():
    module = load_module()
    inputs = json.loads((OUT / 'input.json').read_text())
    application = json.loads((OUT / 'racket.json').read_text())
    episodes = [json.loads(line) for line in (OUT / 'lesson.jsonl').read_text().splitlines() if line.strip()]
    assert len(episodes) == 1
    episode = episodes[0]
    assert episode['sample_indices'] == [0, 1, 2, 3]
    assert episode['rejections'] == []
    assert episode['lesson_check']['status'] == 'not_declared'
    materialized = episode['train'] + episode['test']
    assert len(episode['train']) == 3 and len(episode['test']) == 1
    assert [p['input'] for p in materialized] == inputs[3:]
    results = application['results']
    assert len(results) == len(inputs) == 7
    canonical = canonical_pairs(TASK, root=ROOT)
    rows = []
    for i, (grid, applied) in enumerate(zip(inputs, results)):
        assert applied['error'] is None and applied['valid_output']
        actual = applied['output']
        competitor = rival(grid)
        clusters = contact_clusters(grid)
        selected = next(cells for cells in clusters if any(grid[r][c] == 1 for r, c in cells))
        distracted = next(cells for cells in clusters if cells != selected)
        meta = {'canonical': True} if i < 3 else None
        validation = module.self_check(grid, difficulty=None if i < 3 else 'easy', meta=meta)
        assert validation == []
        if i < 3:
            assert actual == canonical[i]['output']
            assert competitor == actual
        else:
            assert actual == materialized[i - 3]['output']
            assert competitor == actual if i < 6 else competitor != actual
        rows.append({'input_index': i,
                     'role': 'canonical ' + str(i) if i < 3 else 'demo ' + str(i - 3) if i < 6 else 'query',
                     'selected_cells': len(selected), 'distractor_cells': len(distracted),
                     'validator_pass': True, 'validator_errors': validation,
                     'documented_domain': 'authoritative canonical input' if i < 3 else
                                          'generated with default valid axes; all documented invariants pass',
                     'rival_equals_racket': competitor == actual,
                     'racket_output': actual, 'rival_output': competitor})
    bound = json.loads((OUT / 'source_hashes.json').read_text())
    assert bound['generator_sha256'] == hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert application['executed_rule_hash'] == bound['canonical_rule_normalized_hash']
    write('comparison.json', {'status': 'reproduced_teaching_defect',
                             'rival': 'largest cardinal contact cluster by occupied-cell count',
                             'canonical_agreement': '3/3', 'demonstration_agreement': '3/3',
                             'query_disagreement': True, 'source_hashes': bound,
                             'production_lesson_status': episode['lesson_check'], 'cases': rows})
    print(json.dumps({'status': 'reproduced_teaching_defect',
                      'counts': [[r['selected_cells'], r['distractor_cells']] for r in rows],
                      'validator_pass': '7/7 under appropriate canonical/generated mode',
                      'rival_agreement': [r['rival_equals_racket'] for r in rows]}))


if __name__ == '__main__':
    {'prepare': prepare, 'verify': verify}[sys.argv[1]]()
