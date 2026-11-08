"""Reproduce findings on unchanged audit sources; uses public declared rivals only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(Path.cwd())
CHECKS = Path(__file__).resolve().parent


def load(tid):
    source = ROOT/'generators'/tid/'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + tid, source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen, hashlib.sha256(source.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    tid = '306adf8e4c54'
    gen, digest = load(tid)
    census = json.loads((CHECKS/'audit306-census.json').read_text())
    lesson = census['lessons'][0]
    instance = lesson['instance']
    pairs = instance['train'] + instance['test']
    q = 1
    name = 'first_gap_per_line_only'
    fn = gen.LESSON_COMPETITORS[name]
    train = [p for i,p in enumerate(pairs) if i != q]
    prediction = fn(copy.deepcopy(pairs[q]['input']))
    assert all(fn(copy.deepcopy(p['input'])) == p['output'] for p in train)
    assert prediction != pairs[q]['output']
    record = dict(task_id=tid, generator_sha256=digest,
                  rule_source_sha256=census['rule_source_sha256'],
                  rule_callable_sha256=census['rule_callable_sha256'],
                  declared_rule_hash=gen.RULE_HASH,
                  seed=instance['seed'], sample_index=instance['sample_index'],
                  difficulty=lesson['band'], overrides={}, query_index=q,
                  train_indices=[i for i in range(len(pairs)) if i != q],
                  demonstrations=train, input=pairs[q]['input'],
                  census_racket_output=pairs[q]['output'], rival_name=name,
                  rival_output=prediction, self_check=gen.self_check(pairs[q]['input']),
                  provenance='Production lesson rotated to hold out pair 1; original-order query is identifiable against declared rivals.',
                  direct_racket_report='checks/audit/'+tid+'/racket.json')
    write(CHECKS/'audit'/tid/'input.json', record['input'])
    write(CHECKS/'audit'/tid/'counterexample.json', record)

    tid = '374fae0ec7a2'
    gen, digest = load(tid)
    grid = gen.generate(0, 0, texture='no_motifs')
    errors = gen.self_check(grid)
    assert errors == [] and not any(v for row in grid for v in row)
    override_results = []
    for overrides in ({'code1':7}, {'code2':7}, {'proto_size':6}, {'proto_size':2},
                      {'grid_h':8}, {'n_anchors':8}):
        try:
            gen.generate(0,0,**overrides)
            outcome = 'accepted'
        except ValueError as exc:
            outcome = str(exc)
        override_results.append(dict(overrides=overrides, outcome=outcome))
    canonical = canonical_pairs(tid, root=ROOT, labeled_only=True)
    proto_sizes = [sum(v==9 for row in p['input'] for v in row) for p in canonical]
    record = dict(task_id=tid, generator_sha256=digest, seed=0, sample_index=0,
                  overrides={'texture':'no_motifs'}, input=grid, self_check=errors,
                  documented_domain=True, rival_output=None,
                  issue='Generator advertises/emits a degenerate with no template; validator accepts it.',
                  direct_racket_report='checks/audit/'+tid+'/racket.json',
                  boundary_override_probes=override_results,
                  canonical_proto_cell_counts=proto_sizes)
    write(CHECKS/'audit'/tid/'input.json', grid)
    write(CHECKS/'audit'/tid/'counterexample.json', record)
    print(json.dumps({'audit306_query_index':q, 'audit374_validator': errors,
                      'audit374_boundary_probes':override_results}))


if __name__ == '__main__':
    main()
