from __future__ import annotations
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime

TASK = '0f5fbe0de38e'
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n')

catalog = Catalog(REPO)
info = catalog.describe(TASK)
with tempfile.TemporaryDirectory(prefix='audit_0f5fbe0de38e_', dir=REPO / 'var') as dirname:
    runtime = Path(dirname)
    prepare_runtime(catalog, runtime, TASK)
    sys.path.insert(0, str(runtime))
    gen = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK}.generator')
    cases = []
    for i in range(6):
        cases.append({'seed': 71000+i, 'sample_index': i, 'difficulty': 'medium', 'overrides': {}})
    for profile in gen.TEMPLATE_PROFILE_NAMES:
        for lesson in ('unit_single', 'scaled2_single', 'scaled3_single'):
            for orientation in ('same', 'opposite'):
                i = len(cases)
                cases.append({'seed': 72000+i, 'sample_index': i, 'difficulty': 'hard', 'overrides': {'template_profile': profile, 'lesson_profile': lesson, 'orientation_profile': orientation, 'grid_h': 19, 'grid_w': 22, 'bg_color': 9, 'fill_color': 0, 'marker_a_color': 1, 'marker_b_color': 8}})
    for i in range(6):
        cases.append({'seed': 73000+i, 'sample_index': i, 'difficulty': 'easy', 'overrides': {'orientation_profile': 'mixed'}})
    grids = []
    expected = []
    rivals = []
    records = []
    for row in cases:
        g = gen.generate(row['seed'], row['sample_index'], difficulty=row['difficulty'], **row['overrides'])
        obs = gen.observe_overrides(g)
        self_errors = gen.self_check(g)
        strict_errors = gen.strict_canonical_like(g)
        assert self_errors == [] and strict_errors == []
        assert all(obs[k] == v for k, v in row['overrides'].items())
        grids.append(g)
        expected.append(gen._predict(g, 'canonical'))
        rivals.append(gen._predict(g, 'full_footprint'))
        records.append({**row, 'observed': obs, 'self_check': self_errors, 'strict_canonical_like': strict_errors, 'declared_domain_member': True})
    invalid = []
    for overrides in ({'grid_h':18}, {'grid_w':23}, {'bg_color':0,'fill_color':0}, {'lesson_profile':'unit_single','orientation_profile':'mixed'}, {'unknown_axis':1}):
        try:
            gen.generate(74000, 0, **overrides)
        except Exception as exc:
            invalid.append({'overrides':overrides, 'exception_type':type(exc).__name__, 'message':str(exc)})
        else:
            invalid.append({'overrides':overrides, 'unexpected_acceptance':True})
    dump('input.json', grids)
    dump('mirror.json', expected)
    dump('rival.json', rivals)
    dump('probe.json', {'task_id':TASK, 'generator_sha256': hashlib.sha256((REPO/'generators'/TASK/'generator.py').read_bytes()).hexdigest(), 'rule_hash':info.get('rule_hash'), 'generator_rule_hash':gen.RULE_HASH, 'case_count':len(records), 'cases':records, 'invalid_override_probes':invalid, 'rival':'full_footprint: fill every background cell in each inferred 3*scale square'})
    print(json.dumps({'cases':len(records), 'invalid_override_probes':invalid, 'generator_sha256':info.get('generator_sha256'), 'rule_hash':info.get('rule_hash')}))
