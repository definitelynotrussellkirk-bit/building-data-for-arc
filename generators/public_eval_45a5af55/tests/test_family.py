from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import shutil
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/runtime/reviewer_support.py').is_file())
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'shared/runtime')]


def load(path: Path, name: str):
    assert path.is_file(), f'missing implementation: {path}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def adapter():
    return load(HOME / 'workspace/parametric/adapter.py', '_rings_adapter_test')


@pytest.fixture(scope='module')
def executor():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    assert identity['backend'] == 'racket' and identity['protected'] is True
    yield apply
    bridge.close()


def official_pairs():
    return json.loads((HOME / 'tests/original-pairs.json').read_text())


def test_reference_reproduces_every_official_label(executor):
    source = (HOME / 'reference.rkt').read_text()
    pairs = official_pairs()
    assert len(pairs) == 3
    for index, pair in enumerate(pairs):
        assert executor(source, pair['input']) == pair['output'], index


def test_default_program_is_exact_reference(adapter):
    assert adapter.program(adapter.DEFAULT) == (HOME / 'reference.rkt').read_text()
    assert (HOME / 'reference.rkt').read_bytes() == (HOME / 'workspace/parametric/canonical.rkt').read_bytes()


@pytest.mark.parametrize('seed', [0, 1, 7, 17, 43])
def test_counts_prefixes_matched_inputs_and_stress(adapter, seed):
    full = adapter.generate(seed, adapter.DEFAULT, 6, 4)
    other = adapter.generate(seed, {'finish_rule': 'highlight_largest_region'}, 6, 4)
    assert [p['input'] for s in ('train', 'test') for p in full[s]] == [p['input'] for s in ('train', 'test') for p in other[s]]
    assert len({json.dumps(p['input']) for s in ('train', 'test') for p in full[s]}) == 10
    stress = [p for p in full['test'] if len(p['input']) == 16 and len(p['input'][0]) == 30]
    assert len(stress) == 1
    assert len(stress[0]['output']) == len(stress[0]['output'][0]) == 30
    for demos in range(2, 7):
        ep = adapter.generate(seed, adapter.DEFAULT, demos, 4)
        assert ep['train'] == full['train'][:demos]
        assert ep['test'] == full['test']
    for queries in range(1, 5):
        ep = adapter.generate(seed, adapter.DEFAULT, 2, queries)
        assert ep['test'] == full['test'][:queries]


def test_public_turn_is_whitelisted_deep_copy(adapter):
    ep = adapter.generate(17, {'finish_rule': 'highlight_largest_region'}, 2, 4)
    before = adapter.public_turn(ep, 0)
    ep['private'] = {'canary': 'secret'}
    ep['program_solution'] = 'secret'
    ep['test'][0]['output'] = [[9]]
    ep['test'][1]['input'] = [[8]]
    assert adapter.public_turn(ep, 0) == before
    before['train'][0]['input'][0][0] = 9
    assert adapter.public_turn(ep, 0) != before


def test_two_demos_reject_declared_rivals(adapter):
    for seed in range(32):
        for value in adapter.PARAMETERS['finish_rule']:
            ep = adapter.generate(seed, {'finish_rule': value}, 2, 4)
            names = list(adapter.rival_programs())
            survivors = [name for name in names if all(adapter.predict(p['input'], name) == p['output'] for p in ep['train'])]
            assert survivors == [value], (seed, value, survivors)


def test_correct_highlight_is_component_area_not_simple_stripe_statistic(adapter):
    ep = adapter.generate(17, {'finish_rule': 'highlight_largest_region'}, 2, 4)
    for pair in ep['train']:
        correct = adapter.predict(pair['input'], 'highlight_largest_region')
        assert correct != adapter.predict(pair['input'], 'longest_run')
        assert correct != adapter.predict(pair['input'], 'most_frequent_color')
        assert correct != adapter.predict(pair['input'], 'largest_color_total')


def test_declared_and_rival_racket_programs_execute(adapter, executor):
    ep = adapter.generate(17, adapter.DEFAULT, 2, 4)
    programs = adapter.rival_programs()
    for name, program in programs.items():
        for pair in ep['train'] + ep['test']:
            assert executor(program, pair['input']) == adapter.predict(pair['input'], name), name


def test_causal_intermediate_changes_output(adapter):
    pair = adapter.generate(17, {'finish_rule': 'highlight_largest_region'}, 2, 4)['test'][-1]
    info = adapter.intermediate(pair['input'], {'finish_rule': 'highlight_largest_region'})
    assert info['largest_component_cells'] != info['longest_run_cells']
    assert adapter.predict(pair['input'], 'highlight_largest_region') != adapter.predict(pair['input'], 'longest_run')


def test_relocated_adapter_uses_only_declared_local_resources(adapter, tmp_path):
    contract = json.loads((HOME / 'workspace/parametric/promotion.json').read_text())
    dst = tmp_path / 'native'
    dst.mkdir()
    for relative in [contract['adapter'], *contract['resources']]:
        shutil.copyfile(ROOT / relative, dst / Path(relative).name)
    moved = load(dst / 'adapter.py', '_rings_adapter_relocated')
    assert moved.generate(43, moved.DEFAULT, 2, 4) == adapter.generate(43, adapter.DEFAULT, 2, 4)


@pytest.mark.parametrize('args', [
    (True, {'finish_rule': 'rings_only'}, 2, 4),
    (0, {}, 2, 4),
    (0, {'finish_rule': 'bad'}, 2, 4),
    (0, {'finish_rule': 'rings_only', 'extra': 1}, 2, 4),
    (0, {'finish_rule': 'rings_only'}, 1, 4),
    (0, {'finish_rule': 'rings_only'}, 7, 4),
    (0, {'finish_rule': 'rings_only'}, 2, 0),
    (0, {'finish_rule': 'rings_only'}, 2, 5),
])
def test_invalid_requests_rejected(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_base_generator_is_repeatable(adapter):
    base = load(HOME / 'generator.py', '_rings_base_test')
    grids = [base.generate(17, i) for i in range(8)]
    assert len({json.dumps(g) for g in grids}) == 8
    assert base.generate(17, 4) == grids[4]
    assert base.self_check(grids[4]) == []
