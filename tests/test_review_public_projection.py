"""Public-authoring projection uses the native serializer without qualification."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from test_review_public_admission import public_source
from test_review_sequential_replay import runtime
from arcpuzzles.review_public_creation import preflight

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME/'src/arcpuzzles/review_full_packet_files/preview_public.py'
SPEC = importlib.util.spec_from_file_location('public_projection', SOURCE)
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)

@pytest.fixture
def receipt(public_source, runtime, tmp_path):
    root, item, parent, program = public_source
    home = root/'generators'/item['task_id']
    (home/'workspace/public-parent.json').write_text(json.dumps(item))
    (home/'generator.py').write_text("RULE_TASK_ID='ee_1234abcd'\ndef generate(**kw):\n    return {'input': [[1, 2]]}\n")
    (home/'workspace/parametric/adapter.py').write_text(f'''
def program(settings):
    return '(rule! (flip-lr g))' if settings['reverse'] else {program!r}
def generate(seed, settings, demos, queries):
    pairs = [{{'input': [[seed//10, seed%10, i, 9]], 'output': [[9, i, seed%10, seed//10]] if settings['reverse'] else [[seed//10, seed%10, i, 9]]}}
             for i in range(demos + queries)]
    return {{'program_solution': program(settings), 'train': pairs[:demos], 'test': pairs[demos:]}}
''')
    out = tmp_path/'preflight'
    preflight(root, item['task_id'], out)
    return root, out/'preflight.json'

def test_export_verify_and_privacy(receipt, tmp_path):
    root, path = receipt
    catalog = (root/'catalog/puzzles.jsonl').read_bytes()
    out = tmp_path/'preview'
    result = EXPORTER.export_qualified(path, out, library=root, public_preflight=True)
    assert result['status'] == 'authoring_preflight_projection'
    assert result['views'] == 16 and result['training_admitted'] is False
    assert EXPORTER.verify_export(out, library=root)['source_status'] == result['status']
    assert (out/'private/original-pairs.json').read_bytes() == path.with_name('original-pairs.json').read_bytes()
    assert not (out/'private/qualification.json').exists()
    for f in (out/'public').iterdir():
        value = json.loads(f.read_bytes())
        assert set(value) == {'train', 'test'} and len(value['test']) == 1
        assert set(value['test'][0]) == {'input'}
    assert (root/'catalog/puzzles.jsonl').read_bytes() == catalog
    assert not list(tmp_path.glob('.arc-single-query-*'))
    with pytest.raises(ValueError, match='native qualified'):
        EXPORTER.export_qualified(path, tmp_path/'wrong', library=root)

@pytest.mark.parametrize('change', ['source', 'originals', 'public', 'receipt_mode', 'extra', 'symlink'])
def test_tamper_rejected(receipt, tmp_path, change):
    root, path = receipt; out = tmp_path/'preview'
    EXPORTER.export_qualified(path, out, library=root, public_preflight=True)
    if change == 'source':
        (root/'generators/public_eval_1234abcd/generator.py').write_text('# drift')
    elif change == 'originals':
        f=out/'private/original-pairs.json'; v=json.loads(f.read_bytes()); v['pairs'].pop(); f.write_text(json.dumps(v))
        p=out/'private/preflight.json'; q=json.loads(p.read_bytes()); q['evidence_sha256'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest(); p.write_text(json.dumps(q))
    elif change == 'public':
        next((out/'public').iterdir()).write_text('{}')
    elif change == 'receipt_mode':
        f=out/'private/manifest.json'; m=json.loads(f.read_bytes()); m['qualification']=m.pop('public_preflight'); f.write_text(json.dumps(m))
    elif change == 'symlink':
        f=out/'private/preflight.json'; f.unlink(); f.symlink_to(path)
    else:
        (out/'public/answers.json').write_text('{}')
    with pytest.raises((ValueError, FileNotFoundError)):
        EXPORTER.verify_export(out, library=root)

def test_source_change_while_serializing_cleans_scratch(receipt, tmp_path, monkeypatch):
    root, path = receipt; original = EXPORTER._projection
    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        (root/'generators/public_eval_1234abcd/generator.py').write_text('# changed')
        return result
    monkeypatch.setattr(EXPORTER, '_projection', mutate)
    with pytest.raises(ValueError, match='source differs'):
        EXPORTER.export_qualified(path, tmp_path/'preview', library=root, public_preflight=True)
    assert not (tmp_path/'preview').exists()
    assert not list(tmp_path.glob('.arc-single-query-*'))

def test_first_turn_checker_accepts_authoring_bundle(receipt, tmp_path, monkeypatch):
    root, path = receipt; out=tmp_path/'preview'
    EXPORTER.export_qualified(path, out, library=root, public_preflight=True)
    checker_source=HOME/'src/arcpuzzles/review_full_packet_files/check_first_turn.py'
    spec=importlib.util.spec_from_file_location('public_first_turn', checker_source)
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    verify=EXPORTER.verify_export
    monkeypatch.setattr(EXPORTER,'verify_export',lambda bundle: verify(bundle,library=root))
    result=checker.inspect_bundle(EXPORTER,out)
    assert result['public_views_checked']==16 and result['first_turns_checked']==4
    assert len(result['private_evidence'])==4
    assert result['native_verification']['source_status']=='authoring_preflight_projection'
