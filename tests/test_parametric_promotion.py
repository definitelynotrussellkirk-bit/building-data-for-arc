import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arcpuzzles import parametric_promotion as promotion


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'


@pytest.fixture
def candidate(library):
    tid = 'aaaa00000001'
    home = library / 'generators' / tid / 'workspace/parametric'
    home.mkdir(parents=True)
    (home / 'adapter.py').write_text('# test adapter\n')
    (home / 'promotion.json').write_bytes(raw({
        'schema': 'arcpuzzles-parametric-adapter-v1',
        'adapter': f'generators/{tid}/workspace/parametric/adapter.py',
        'parameters': {'side': ['left', 'right']}, 'default': {'side': 'left'},
        'limits': {'demos': [2, 8], 'queries': [1, 8]},
    }))
    evidence = home / 'evidence/manifest.json'
    evidence.parent.mkdir()
    row = Catalog(library).describe(tid)
    evidence.write_bytes(raw({'task_id': tid, 'generator_sha256': row['generator_sha256'],
        'canonical_rule_hash': row['rule_hash'], 'verification_status': 'reviewer_reported',
        'files': [{'path': (home/'adapter.py').relative_to(library).as_posix(),
                   'sha256': hashlib.sha256((home/'adapter.py').read_bytes()).hexdigest()}]}))
    return Catalog(library), tid, home


def fake_execution(catalog, tid, contract, jobs, timeout):
    episodes = []
    for job in jobs:
        offset = 1 if job['settings']['side'] == 'left' else 2
        pairs = [{'input': [[i % 10, i // 10]], 'output': [[offset]]}
                 for i in range(job['demos'] + job['queries'])]
        episodes.append({'task_id': tid, 'seed': job['seed'], 'settings': job['settings'],
                         'train': pairs[:job['demos']], 'test': pairs[job['demos']:],
                         'program': '(rule! g)', 'program_sha256': hashlib.sha256(b'(rule! g)').hexdigest(),
                         'reference': 'accepted_parametric'})
    return {'episodes': episodes,
            'checks': [{'seed': j['seed'], 'settings': j['settings'], 'demos': j['demos'],
                        'queries': j['queries'], 'survivors': [j['settings']],
                        'label_count': j['demos'] + j['queries']} for j in jobs],
            'racket': {'backend': 'racket', 'protected': True},
            'racket_evaluations': sum(j['demos'] + j['queries'] for j in jobs)}


def qualify_accept(candidate, monkeypatch, tmp_path):
    catalog, tid, _ = candidate
    monkeypatch.setattr(promotion, '_execute', fake_execution)
    report = promotion.qualify(catalog, tid, tmp_path/'qualification', seeds=[0, 17])
    accepted = promotion.accept(catalog, tid, Path(report['receipt']), reason='Reviewed finite settings')
    return catalog, tid, accepted


def test_unaccepted_prototype_cannot_generate(candidate):
    catalog, tid, _ = candidate
    with pytest.raises(ValueError, match='accepted'):
        promotion.generate(catalog, tid)


def test_acceptance_binds_code_rule_and_qualification(candidate, monkeypatch, tmp_path):
    catalog, tid, accepted = qualify_accept(candidate, monkeypatch, tmp_path)
    assert accepted['status'] == 'accepted'
    assert promotion.status(catalog, tid)['status'] == 'accepted'
    assert accepted['training_admitted'] is False
    (candidate[2]/'adapter.py').write_text('# changed\n')
    assert promotion.status(catalog, tid)['status'] == 'stale'
    with pytest.raises(ValueError, match='stale|changed'):
        promotion.generate(catalog, tid)


def test_pending_public_fix_and_unapproved_source_block_qualification(candidate, tmp_path):
    catalog, tid, home = candidate
    p = home/'evidence/manifest.json'; d=json.loads(p.read_text())
    d['public_identifier_status']='external_correction_pending';p.write_bytes(raw(d))
    with pytest.raises(ValueError, match='followup|prototype'):
        promotion.qualify(catalog, tid, tmp_path/'pending')
    d.pop('public_identifier_status');p.write_bytes(raw(d))
    rows=[json.loads(line) for line in (catalog.root/'catalog/puzzles.jsonl').read_text().splitlines()]
    rows[0]['semantic_veto']=True
    (catalog.root/'catalog/puzzles.jsonl').write_bytes(b''.join(raw(x) for x in rows))
    with pytest.raises(ValueError, match='approved'):
        promotion.qualify(Catalog(catalog.root), tid, tmp_path/'veto')


def test_test_backend_and_mutated_evidence_cannot_be_accepted(candidate, monkeypatch, tmp_path):
    catalog, tid, _ = candidate
    def synthetic(*args):
        result=fake_execution(*args);result['racket']={'backend':'test','protected':False};return result
    monkeypatch.setattr(promotion, '_execute', synthetic)
    with pytest.raises(ValueError, match='Racket|protected'):
        promotion.qualify(catalog, tid, tmp_path/'synthetic')
    monkeypatch.setattr(promotion, '_execute', fake_execution)
    q=promotion.qualify(catalog, tid, tmp_path/'real')
    (tmp_path/'real/execution.json').write_text('{}')
    with pytest.raises(ValueError, match='evidence|changed'):
        promotion.accept(catalog, tid, Path(q['receipt']), reason='reviewed')


@pytest.mark.parametrize('options', [{'count':True}, {'queries':0}, {'demos':1},
                                    {'seed':1.5}, {'settings':{'side':True}},
                                    {'settings':{'unknown':'left'}}])
def test_generation_rejects_bad_requests(candidate, monkeypatch, tmp_path, options):
    catalog, tid, _ = qualify_accept(candidate, monkeypatch, tmp_path)
    with pytest.raises(ValueError):
        promotion.generate(catalog, tid, **options)


def test_export_public_id_bytes_sort_and_private_separation(candidate, monkeypatch, tmp_path):
    catalog, tid, _ = qualify_accept(candidate, monkeypatch, tmp_path)
    written=[]; original=Path.write_bytes
    def observe_write(path, payload):
        if path.parent.name=='public' and path.suffix=='.json': written.append(path.stem)
        return original(path, payload)
    monkeypatch.setattr(Path, 'write_bytes', observe_write)
    first=promotion.export(catalog, tid, tmp_path/'export', count=2, seed=5)
    assert first['episodes'] == 2
    files=list((tmp_path/'export/public').glob('*.json'))
    assert written == sorted(written)
    for path in files:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == path.stem
        public=json.loads(path.read_bytes())
        assert set(public)=={'train','test'}
        assert all(set(pair)=={'input'} for pair in public['test'])
        assert len(public['test'])==4
    with pytest.raises(FileExistsError):
        promotion.export(catalog, tid, tmp_path/'export', count=2)
    # Same visible content under different private seeds is duplicate data.
    with pytest.raises(ValueError, match='duplicate'):
        promotion.export(catalog, tid, tmp_path/'duplicates', count=3,
                         settings={'side':'left'})
    assert not (tmp_path/'duplicates').exists()


def test_accept_rejects_shortened_qualification(candidate, monkeypatch, tmp_path):
    catalog, tid, _=candidate
    monkeypatch.setattr(promotion, '_execute', fake_execution)
    q=promotion.qualify(catalog, tid, tmp_path/'qual')
    path=Path(q['receipt']); report=json.loads(path.read_text())
    report['jobs']=[j for j in report['jobs'] if j['seed']==0]
    execution=fake_execution(catalog, tid, report['contract'], report['jobs'], 180)
    (path.parent/'execution.json').write_bytes(raw(execution))
    report['execution']['sha256']=hashlib.sha256(raw(execution)).hexdigest()
    path.write_bytes(raw(report))
    with pytest.raises(ValueError, match='seed|coverage|qualification'):
        promotion.accept(catalog, tid, path, reason='must retain required coverage')


def test_generation_cannot_switch_to_an_unaccepted_program(candidate, monkeypatch, tmp_path):
    catalog, tid, _=qualify_accept(candidate, monkeypatch, tmp_path)
    def different(*args):
        result=fake_execution(*args)
        for episode in result['episodes']:
            episode['program']='(rule! (reverse g))'
            episode['program_sha256']=hashlib.sha256(episode['program'].encode()).hexdigest()
        return result
    monkeypatch.setattr(promotion, '_execute', different)
    with pytest.raises(ValueError, match='program|canonical'):
        promotion.generate(catalog, tid, settings={'side':'right'})


def test_accept_reexecutes_instead_of_trusting_edited_receipt(candidate, monkeypatch, tmp_path):
    catalog, tid, _=candidate
    monkeypatch.setattr(promotion, '_execute', fake_execution)
    q=promotion.qualify(catalog, tid, tmp_path/'qual')
    path=Path(q['receipt']); report=json.loads(path.read_text())
    execution=json.loads((path.parent/'execution.json').read_text())
    execution['episodes'][0]['test'][0]['output']=[[9]]
    (path.parent/'execution.json').write_bytes(raw(execution))
    report['execution']['sha256']=hashlib.sha256(raw(execution)).hexdigest()
    path.write_bytes(raw(report))
    with pytest.raises(ValueError, match='replay|fresh|recheck'):
        promotion.accept(catalog, tid, path, reason='edited report is not execution')
    assert not (catalog.root/f'generators/{tid}/parametric/accepted.json').exists()


def test_actual_rule_parser_drift_revokes_acceptance(candidate, monkeypatch, tmp_path):
    catalog, tid, _=candidate
    parser=catalog.root/'shared/tools/comment_solutions.py';parser.parent.mkdir(parents=True)
    parser.write_text('# original parser\n')
    qualify_accept(candidate, monkeypatch, tmp_path)
    parser.write_text('# changed parser\n')
    assert promotion.status(catalog, tid)['status']=='stale'


def test_selected_authority_is_bound_without_its_catalog_record(candidate):
    catalog, tid, home=candidate; authority='aaaa00000002'
    program='(rule! (lambda (g) (reverse g)))'
    p=catalog.root/'catalog/puzzles.jsonl'
    rows=[json.loads(line) for line in p.read_text().splitlines()]
    rows[0].update(rule_task_id=authority,
                   reviewed_rule_hash=hashlib.sha256(' '.join(program.split()).encode()).hexdigest()[:12])
    p.write_bytes(b''.join(raw(r) for r in rows if r['id']!=authority))
    p=catalog.root/'shared/data/canonical/puzzles.jsonl'
    rows=[json.loads(line) for line in p.read_text().splitlines()]
    for row in rows:
        if row['task_id']==authority: row['program_solution']=program
    p.write_bytes(b''.join(raw(r) for r in rows))
    p=home/'evidence/manifest.json';d=json.loads(p.read_text())
    d['canonical_rule_hash']=Catalog(catalog.root).describe(tid)['rule_hash'];p.write_bytes(raw(d))
    _,binding=promotion._ready(Catalog(catalog.root),tid)
    assert binding['rule_task_id']==authority
    assert binding['canonical_program_sha256']==hashlib.sha256(program.encode()).hexdigest()


def test_corrupt_or_incomplete_acceptance_is_stale(candidate, monkeypatch, tmp_path):
    catalog, tid, _=qualify_accept(candidate, monkeypatch, tmp_path)
    p=catalog.root/f'generators/{tid}/parametric/accepted.json';d=json.loads(p.read_text())
    d['files']=[];p.write_bytes(raw(d))
    assert promotion.status(catalog,tid)['status']=='stale'
    p.write_text('[')
    assert promotion.status(catalog,tid)['status']=='stale'


def test_serialized_export_requires_complete_inventory_and_strict_grids(candidate, monkeypatch, tmp_path):
    catalog, tid, _=qualify_accept(candidate, monkeypatch, tmp_path)
    promotion.export(catalog, tid, tmp_path/'export', settings={'side':'left'})
    p=tmp_path/'export/manifest.json';manifest=json.loads(p.read_text())
    p.write_bytes(raw({**manifest, 'files':[]}))
    with pytest.raises(ValueError,match='inventory'):
        promotion.verify_export(tmp_path/'export')
    p.write_bytes(raw(manifest))
    private=tmp_path/'export/private.jsonl';episode=json.loads(private.read_text())
    episode['test'][0]['output']=[[False]];private.write_bytes(raw(episode))
    for row in manifest['files']:
        if row['path']=='private.jsonl':row['sha256']=hashlib.sha256(private.read_bytes()).hexdigest()
    p.write_bytes(raw(manifest))
    with pytest.raises(ValueError,match='integer|grid'):
        promotion.verify_export(tmp_path/'export')
