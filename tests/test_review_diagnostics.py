from types import SimpleNamespace
import pytest
import review_diagnostics as d

def test_structural_mismatch_retains_witness_and_does_not_claim_proof():
    canonical=[{'input':[[1,0,2]],'output':[[8]]}]
    generated=[{'input':[[1,0,2,0,3]],'output':[[8]]}]
    report=d.compare_structure(canonical,generated)
    assert report['status']=='advisory_mismatch'
    assert report['witness']==generated[0]
    assert 'object_count' in report['disjoint_features']
    assert d.compare_structure(canonical,canonical)['status']=='no_mismatch_found'

def test_scalar_probe_detects_bool_coercion_and_invalid_indices():
    gen=SimpleNamespace(AXES={'color':{'type':'color','valid':'1..9'}},generate=lambda seed,i,**kw:[[int(kw.get('color',1))]])
    rows=d.scalar_override_probes(gen)
    assert any(r['axis']=='color' and r['value'] is True for r in rows)
    assert any(r['axis']=='sample_index' and r['value']==-1 for r in rows)


def test_scalar_probe_checks_seed_as_a_call_argument():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if type(sample_index) is not int or sample_index < 0:
            raise ValueError('invalid index')
        return [[int(seed) % 10]]
    rows = d.scalar_override_probes(SimpleNamespace(AXES={}, generate=generate))
    bad_seeds = {(r['value_type'], repr(r['value'])) for r in rows
                 if r['axis'] == 'seed' and r['status'] == 'accepted_invalid_scalar'}
    assert {('bool', 'True'), ('float', '1.0'), ('str', "'1'")} <= bad_seeds
    assert all(r['probe_kind'] == 'call_argument' for r in rows if r['axis'] == 'seed')
    assert not any(r['axis'] == 'seed' and r['value_type'] == 'int' and r['value'] < 0 for r in rows)


def test_scalar_probe_uses_legal_axis_values_to_expose_coercion():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
            raise TypeError('bad call argument')
        value = int(overrides.get('side', 8))
        if not 8 <= value <= 12:
            raise ValueError('side out of range')
        return [[value % 10]]
    gen = SimpleNamespace(AXES={'side': {'type': 'int', 'valid': '8..12'}}, generate=generate)
    rows = d.scalar_override_probes(gen)
    found = {(r['value_type'], repr(r['value'])) for r in rows
             if r['axis'] == 'side' and r['status'] == 'accepted_invalid_scalar'}
    assert {('float', '8.0'), ('float', '8.75'), ('str', "'8'"), ('float', '12.75')} <= found
    assert all(r['probe_kind'] == 'declared_override' and r['control_value'] in (8, 12)
               for r in rows if r['axis'] == 'side' and r['status'] == 'accepted_invalid_scalar')


def test_scalar_probe_reuses_sparse_enum_and_color_exclusion_domains():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
            raise TypeError('bad call argument')
        value = int(overrides.get('count', 7))
        if value not in (7, 11):
            raise ValueError('outside domain')
        return [[value % 10]]
    gen = SimpleNamespace(AXES={'count': {'type': 'int', 'valid': '7|11'}}, generate=generate)
    rows = d.scalar_override_probes(gen)
    assert any(r['axis'] == 'count' and r['value_type'] == 'float' and r['value'] == 11.75 for r in rows)
    gen.AXES = {'count': {'type': 'color', 'valid': '1..9 (≠1 ≠2 ≠3 ≠4 ≠5 ≠6 ≠8 ≠9)'}}
    rows = d.scalar_override_probes(gen)
    assert any(r['axis'] == 'count' and r['value_type'] == 'str' and r['value'] == '7' for r in rows)


def test_scalar_probe_separates_rejected_controls_from_accepted_invalid_values():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if overrides:
            raise ValueError('this band cannot materialize the declared axis')
        return [[1]]
    gen = SimpleNamespace(AXES={'side': {'type': 'int', 'valid': '8..12'}}, generate=generate)
    rows = d.scalar_override_probes(gen)
    side = [r for r in rows if r['axis'] == 'side']
    assert side and all(r['status'] == 'no_accepted_control' for r in side)
    assert all(r['probe_kind'] == 'declared_override' for r in side)


def test_scalar_probe_skips_nonexact_and_noninteger_axes():
    gen = SimpleNamespace(AXES={
        'diagnostic': {'type': 'int', 'valid': '1..9', 'probe': 'diagnostic'},
        'nonexact': {'type': 'int', 'valid': '1..9', 'exact': False},
        'fraction': {'type': 'float', 'valid': '0..1'},
    }, generate=lambda seed, index, **kw: [[1]])
    assert not any(r['axis'] in gen.AXES for r in d.scalar_override_probes(gen))


def test_scalar_probe_checks_difficulty_type_with_a_supported_control():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
            raise TypeError('bad call argument')
        return [[1]]
    rows = d.scalar_override_probes(SimpleNamespace(AXES={}, generate=generate))
    assert any(r['axis'] == 'difficulty' and r['value'] is True
               and r['status'] == 'accepted_invalid_scalar' for r in rows)


def test_scalar_probe_does_not_flag_strict_signed_integer_controls():
    def generate(seed, sample_index, *, difficulty=None, **overrides):
        if type(seed) is not int or type(sample_index) is not int or sample_index < 0:
            raise TypeError('bad call argument')
        if difficulty not in (None, 'easy', 'medium', 'hard') or isinstance(difficulty, bool):
            raise ValueError('bad difficulty')
        shift = overrides.get('shift', -1)
        if type(shift) is not int or not -3 <= shift <= 3:
            raise TypeError('bad shift')
        return [[shift % 10]]
    gen = SimpleNamespace(AXES={'shift': {'type': 'int', 'valid': '-3..3'}}, generate=generate)
    assert d.scalar_override_probes(gen) == []

def test_generic_rival_search_finds_and_minimizes_multicolor_ambiguity():
    lesson={'train':[{'input':[[1,0]],'output':[[1,1]]}]*3,
            'test':[{'input':[[1,0,2,0]],'output':[[1,1,2,2]]}]}
    report=d.search_lesson(SimpleNamespace(),lesson)
    rival=report['candidates']['generic:first_color_only']
    assert rival['status']=='ambiguous'
    assert len(rival['witness']['train'])==1
    assert report['candidates']['generic:no_fill']['status']=='refuted'

def test_local_provider_independent_and_support_equivalence():
    gen=SimpleNamespace(SEARCHED_RIVAL_PROVIDER=lambda:[('identity',lambda g:g)])
    lesson={'train':[{'input':[[1]],'output':[[1]]}], 'test':[{'input':[[2]],'output':[[2]]}]}
    report=d.search_lesson(gen,lesson)
    assert report['candidates']['provider:identity']['status']=='support_equivalent'
    assert report['provider_status']=='loaded'

def test_schedule_fields_do_not_confuse_reporting_modulus():
    report=d.schedule_metadata(SimpleNamespace(LESSON_SCHEDULE_PERIOD=4),6,False)
    assert report['declared_schedule_period']==4
    assert report['reporting_residue_modulus']==6
    assert report['enumerated_schedule_period'] is None
    assert report['warnings']

def test_template_is_portable_and_preserves_destination(tmp_path):
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'shared/tools/write_generator_test.py'
    spec=importlib.util.spec_from_file_location('template_tool',path)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    out=tmp_path/'test_generator.py';tool.write_test('e2266501046d',out)
    source=out.read_text()
    compile(source,str(out),'exec')
    assert 'scripts.' not in source
    assert all(name in source for name in ('canonical_pairs','canonical_path','find_root'))
    with pytest.raises(FileExistsError): tool.write_test('e2266501046d',out)
