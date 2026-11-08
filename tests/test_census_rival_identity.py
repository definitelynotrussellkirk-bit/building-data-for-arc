"""Shared declarations reuse exact callables without merging distinct rules."""
from collections import Counter
from copy import deepcopy
import json
import sys
from types import SimpleNamespace

from test_lesson_census import ROOT, load
from test_census_rescore import saved


REGISTRIES = ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS', 'SEMANTIC_RIVALS')


def worker():
    return load('identity_census_worker', ROOT / 'shared/tools/lesson_census.py')


def lesson():
    return {'train': [{'input': [[1]], 'output': [[1]]}],
            'test': [{'input': [[2]], 'output': [[2]]}]}


def aliases(fn, name='identity'):
    return {namespace + ':' + name: fn for namespace in REGISTRIES}


def test_aliases_share_predictions_and_keep_every_namespace_outcome():
    tool = worker(); calls = []
    def identity(grid):
        calls.append(grid[0][0]); return grid
    instance = lesson(); before = deepcopy(instance); cache = {}
    result = tool.score_lesson(SimpleNamespace(), aliases(identity), instance, prediction_cache=cache)
    rotations = tool.score_rotations(SimpleNamespace(), aliases(identity), instance, prediction_cache=cache)
    assert calls == [1, 2]
    assert result['rivals'] == {namespace + ':identity': 'survived_all' for namespace in REGISTRIES}
    assert all(row['rivals'] == result['rivals'] for row in rotations)
    assert instance == before


def test_same_name_and_source_with_distinct_closures_are_not_merged():
    tool = worker()
    def make(value):
        return lambda grid: [[value]]
    rivals = {'LESSON_COMPETITORS:rule': make(1), 'SEMANTIC_RIVALS:rule': make(9)}
    result = tool.score_lesson(SimpleNamespace(), rivals, lesson())
    assert result['rivals'] == {'LESSON_COMPETITORS:rule': 'ambiguous', 'SEMANTIC_RIVALS:rule': 'refuted'}


def test_distinct_names_of_one_callable_keep_distinct_identities():
    tool = worker(); calls = []
    def identity(grid):
        calls.append(grid[0][0]); return grid
    tool.score_lesson(SimpleNamespace(), {'LESSON_COMPETITORS:a': identity,
                                        'SEMANTIC_RIVALS:b': identity}, lesson())
    assert calls == [1, 2, 1, 2]


def test_shared_exception_retains_all_declared_errors():
    tool = worker(); calls = []
    def broken(grid):
        calls.append(grid[0][0]); raise ValueError('fixture failure')
    result = tool.score_lesson(SimpleNamespace(), aliases(broken), lesson())
    assert calls == [1]
    assert result['rivals'] == {namespace + ':identity': 'error' for namespace in REGISTRIES}
    assert len(result['errors']) == 3
    assert all('ValueError: fixture failure' in error for error in result['errors'])


def test_census_counts_unique_callables_and_shares_canonical_scoring(tmp_path, monkeypatch):
    tool = worker(); calls = Counter()
    def make(name):
        def identity(grid):
            calls[name] += 1; return grid
        return identity
    functions = {name: make(name) for name in ('a', 'b', 'c')}
    gen = SimpleNamespace(__file__=__file__, **{namespace: dict(functions) for namespace in REGISTRIES})
    bundle = SimpleNamespace(kind='per_puzzle', generator_module=gen, rule_source='rule',
                             rule_callable_text='callable', rule_task_id='x', rule_file='canonical')
    runner = SimpleNamespace(_load_bundle=lambda task: bundle,
        _open_bridge_with_rule=lambda rule: (SimpleNamespace(shutdown=lambda: None), 'fn'),
        run_one=lambda *a, **kw: lesson())
    monkeypatch.setitem(sys.modules, 'puzzle_generators', SimpleNamespace(runner=runner))
    support = load('identity_census_support', ROOT / 'shared/runtime/reviewer_support.py')
    monkeypatch.setattr(tool, '_support', lambda: support)
    monkeypatch.setattr(support, 'canonical_pairs', lambda *a, **kw: lesson()['train'] + lesson()['test'])
    report = tool.census({'task_id': 'x', 'n_demos': 1, 'n_queries': 1, 'period': 1,
                          'per_band': 1, 'bands': ['easy'], 'rotate_query': True})
    assert report.get('unique_rivals') == 3
    assert report.get('declaration_bindings') == 9
    assert calls == {'a': 4, 'b': 4, 'c': 4}  # two canonical + two generated inputs each
    assert report['status'] == 'no_ambiguity_found'
    assert len(report['rivals']) == len(report['canonical_rival_fit']) == 9
    assert report['rival_identities']['CANONICAL_SHORTCUTS:a'] == {
        'name': 'a', 'declared_in': list(REGISTRIES),
        'bindings': ['CANONICAL_SHORTCUTS:a', 'LESSON_COMPETITORS:a', 'SEMANTIC_RIVALS:a']}
    json.dumps(report)


def test_rescore_preserves_each_alias_counterexample(saved, tmp_path):
    tool = worker(); source = tmp_path / 'generator.py'
    source.write_text("TASK_ID='x'\nRULE_HASH='rulepin'\ncalls=[]\n"
        "def wrong(grid):\n calls.append(grid[0][0])\n return [[9]] if grid == [[1]] else grid\n"
        "LESSON_COMPETITORS={'rule':wrong}\nSEMANTIC_RIVALS=dict(LESSON_COMPETITORS)\n"
        "CANONICAL_SHORTCUTS=dict(LESSON_COMPETITORS)\n")
    gen = SimpleNamespace(__file__=str(source)); exec(source.read_text(), gen.__dict__)
    bundle = SimpleNamespace(kind='per_puzzle', generator_module=gen, rule_source='rule',
                             rule_callable_text='callable', rule_task_id='x', rule_file='canonical')
    before = deepcopy(saved); report = tool.rescore_census(saved, bundle)
    assert report.get('unique_rivals') == 1 and report.get('declaration_bindings') == 3
    assert gen.calls == [1, 3, 2]
    assert report['status'] == 'ambiguous'
    assert len(report['rival_summary']) == 3
    for outcome in report['rival_summary'].values():
        assert outcome['counterexample']['prediction'] == [[9]]
        assert outcome['rotations'] == {'ambiguous': 1, 'refuted': 2}
    assert report['new_reference_executions'] == report['new_generated_instances'] == 0
    assert saved == before


def test_companion_retains_unique_counts_and_declaration_provenance():
    from arcpuzzles.lesson_census import census_companion
    report = {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': 'x',
              'unique_rivals': 1, 'declaration_bindings': 3,
              'rival_identities': {'CANONICAL_SHORTCUTS:a': {'name': 'a',
                 'declared_in': list(REGISTRIES),
                 'bindings': ['CANONICAL_SHORTCUTS:a', 'LESSON_COMPETITORS:a', 'SEMANTIC_RIVALS:a']}}}
    companion = census_companion(report, full_report_sha256='a' * 64,
                                  full_report_path='full.json', invocation=['arcpuzzles'])
    assert companion.get('unique_rivals') == 1 and companion.get('declaration_bindings') == 3
    assert companion['rival_identities'] == report['rival_identities']
