"""Source inventories are author reports, never automatic qualification."""
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arcpuzzles.parametric_priority import _prototype


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def implementation():
    assert (Path(__file__).resolve().parents[1]/'src/arcpuzzles/parametric_manifest.py').is_file(), 'Missing native parametric manifest builder'
    return importlib.import_module('arcpuzzles.parametric_manifest')


@pytest.fixture
def candidate(library):
    tid='aaaa00000001';home=library/'generators'/tid;proto=home/'workspace/parametric';proto.mkdir(parents=True)
    # Inventorying this file must never import or execute it.
    (proto/'adapter.py').write_text("raise RuntimeError('inventory executed an adapter')\n")
    contract={'schema':'arcpuzzles-parametric-adapter-v1','adapter':f'generators/{tid}/workspace/parametric/adapter.py',
              'parameters':{'side':['left','right']},'default':{'side':'left'},'limits':{'demos':[2,8],'queries':[1,8]}}
    (proto/'promotion.json').write_text(json.dumps(contract));(proto/'alternate.rkt').write_text('(rule! g)')
    evidence=proto/'evidence/run';evidence.mkdir(parents=True);(evidence/'focused.log').write_text('3 passed\n')
    tests=home/'tests';tests.mkdir();(tests/'test_parameters.py').write_text('# retained test source\n')
    return Catalog(library),tid,proto,evidence,tests/'test_parameters.py'


def build(candidate,**options):
    catalog,tid,_,evidence,test=candidate
    return implementation().build_manifest(catalog,tid,evidence=evidence,include=[test],
                                           reported_checks='Author reports 3 focused tests passed.',**options)


def test_default_output_binds_live_identity_and_is_current_without_executing_code(candidate):
    catalog,tid,proto,evidence,test=candidate;before=(catalog.root/'catalog/puzzles.jsonl').read_bytes()
    result=build(candidate);path=proto/'evidence/manifest.json';value=json.loads(path.read_text());row=catalog.describe(tid)
    assert result['manifest']==str(path) and result['sha256']==sha(path)
    assert value['schema']=='arcpuzzles-parametric-prototype-evidence-v1'
    assert value['task_id']==tid and value['generator_sha256']==row['generator_sha256']
    assert value['canonical_rule_hash']==row['rule_hash'] and value['parameters']=={'side':['left','right']}
    assert value['verification_status']=='reviewer_reported' and value['builder_executed_checks'] is False
    assert value['variant_approved'] is False and value['training_admitted'] is False
    files={p['path']:p for p in value['files']}
    for source in [proto/'adapter.py',proto/'promotion.json',proto/'alternate.rkt',evidence/'focused.log',test]:
        assert files[source.relative_to(catalog.root).as_posix()]['sha256']==sha(source)
    assert _prototype(catalog.root,row)['status']=='current'
    assert (catalog.root/'catalog/puzzles.jsonl').read_bytes()==before
    assert not (catalog.root/'generators'/tid/'parametric/accepted.json').exists()


def test_explicit_preview_does_not_replace_the_current_manifest(candidate,tmp_path):
    _,_,proto,_,_=candidate;current=proto/'evidence/manifest.json';current.write_text('{"preserved":true}')
    out=tmp_path/'preview.json';build(candidate,output=out)
    assert json.loads(current.read_text())=={'preserved':True}
    assert json.loads(out.read_text())['reported_checks'].startswith('Author reports')


def test_existing_manifest_requires_matching_hash_and_old_claims_do_not_transfer(candidate):
    catalog,tid,proto,_,_=candidate;path=proto/'evidence/manifest.json'
    old={'variant_approved':True,'verification_status':'independently_checked','owner_checks':{'all_passed':True}}
    path.write_text(json.dumps(old));old_bytes=path.read_bytes();wanted=sha(path)
    with pytest.raises(FileExistsError):build(candidate)
    with pytest.raises(ValueError,match='hash|changed'):build(candidate,replace_sha256='0'*64)
    assert path.read_bytes()==old_bytes
    accepted=catalog.root/'generators'/tid/'parametric/accepted.json';accepted.parent.mkdir();accepted.write_text('separate acceptance stays untouched')
    result=build(candidate,replace_sha256=wanted);new=json.loads(path.read_text())
    assert result['replaced_sha256']==wanted and 'owner_checks' not in new
    assert new['verification_status']=='reviewer_reported' and new['variant_approved'] is False
    assert accepted.read_text()=='separate acceptance stays untouched'


def test_replacement_hash_for_a_missing_output_fails(candidate):
    with pytest.raises(ValueError,match='exist|missing'):build(candidate,replace_sha256='0'*64)


def test_output_cannot_overwrite_a_declared_source(candidate):
    path=candidate[2]/'promotion.json';before=path.read_bytes()
    with pytest.raises(ValueError,match='source|overlap'):build(candidate,output=path,replace_sha256=sha(path))
    assert path.read_bytes()==before


@pytest.mark.parametrize('kind',['file','directory','include','output'])
def test_symlinks_are_rejected(candidate,tmp_path,kind):
    _,_,proto,evidence,_=candidate;outside=tmp_path/'outside';outside.mkdir();(outside/'x.log').write_text('foreign')
    options={}
    if kind=='file':(evidence/'linked.log').symlink_to(outside/'x.log')
    elif kind=='directory':(evidence/'linked').symlink_to(outside,target_is_directory=True)
    elif kind=='include':
        link=proto/'linked.py';link.symlink_to(outside/'x.log')
    else:
        link=tmp_path/'linked';link.symlink_to(outside,target_is_directory=True);options['output']=link/'manifest.json'
    with pytest.raises(ValueError,match='[Ss]ymlink'):build(candidate,**options)


def test_evidence_cannot_come_from_another_task(candidate):
    catalog,_,_,_,_=candidate
    with pytest.raises(ValueError,match='task|escape|outside'):
        implementation().build_manifest(catalog,candidate[1],evidence=catalog.root/'generators/aaaa00000002',reported_checks='Reported checks')


@pytest.mark.parametrize('checks',['',None,True])
def test_explicit_reported_checks_are_required(candidate,checks):
    catalog,tid,_,evidence,_=candidate
    with pytest.raises(ValueError,match='reported|checks'):
        implementation().build_manifest(catalog,tid,evidence=evidence,reported_checks=checks)


def test_empty_or_cache_only_evidence_cannot_form_a_report(candidate):
    _,_,proto,evidence,_=candidate;(evidence/'focused.log').unlink()
    cache=evidence/'__pycache__';cache.mkdir();(cache/'ignored.pyc').write_bytes(b'cache')
    with pytest.raises(ValueError,match='evidence|empty'):build(candidate)
    assert not (proto/'evidence/manifest.json').exists()


@pytest.mark.parametrize('mutation',[
    {'parameters':{'side':['left','left']}},{'default':{'side':'up'}},
    {'limits':{'demos':[True,8],'queries':[1,8]}},
    {'limits':{'demos':[2,8],'queries':[1,33]}},
    {'adapter':'generators/aaaa00000002/generator.py'},
    {'resources':['generators/aaaa00000002/generator.py']}])
def test_invalid_or_foreign_contract_fails_before_writing(candidate,mutation):
    proto=candidate[2];path=proto/'promotion.json';value=json.loads(path.read_text());value.update(mutation);path.write_text(json.dumps(value))
    with pytest.raises(ValueError):build(candidate)
    assert not (proto/'evidence/manifest.json').exists()


def test_command_is_available_through_the_normal_cli(candidate,capsys):
    from arcpuzzles.cli import main
    catalog,tid,proto,evidence,_=candidate
    code=main(['--library',str(catalog.root),'parametric','manifest',tid,'--evidence',str(evidence),
               '--reported-checks','Author reports 3 focused tests passed.'])
    assert code==0
    assert json.loads(capsys.readouterr().out)['manifest']==str(proto/'evidence/manifest.json')


@pytest.mark.parametrize('limits',[None,[],12])
def test_malformed_limit_containers_are_clean_validation_errors(candidate,limits):
    path=candidate[2]/'promotion.json';value=json.loads(path.read_text());value['limits']=limits;path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='limit|count'):build(candidate)


@pytest.mark.parametrize('field',['adapter','resources'])
def test_contract_paths_match_qualifications_library_relative_format(candidate,field):
    proto=candidate[2];path=proto/'promotion.json';value=json.loads(path.read_text())
    value[field]=str(proto/'adapter.py') if field=='adapter' else [str(proto/'alternate.rkt')]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='relative|adapter|resource'):build(candidate)


def test_builder_does_not_remove_an_unapproved_base_blocker(candidate):
    catalog,tid,_,_,_=candidate;path=catalog.root/'catalog/puzzles.jsonl'
    rows=[json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['mix_weight']=0;path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    build(candidate)
    from arcpuzzles.parametric_promotion import _ready
    assert Catalog(catalog.root).describe(tid)['approved'] is False
    with pytest.raises(ValueError,match='Production generator must be approved'):_ready(Catalog(catalog.root),tid)


def test_special_evidence_files_fail_without_opening_them(candidate):
    import os
    fifo=candidate[3]/'pipe';os.mkfifo(fifo)
    with pytest.raises(ValueError,match='Special'):build(candidate)


@pytest.mark.parametrize('kind',['catalog','other_task'])
def test_library_outputs_stay_task_local_or_in_scratch(candidate,kind):
    catalog=candidate[0]
    out=(catalog.root/'catalog/runtime_files.json' if kind=='catalog'
         else catalog.root/'generators/aaaa00000002/evidence/manifest.json')
    before=out.read_bytes() if out.exists() else None
    options={'output':out}
    if before is not None:options['replace_sha256']=sha(out)
    with pytest.raises(ValueError,match='task|scratch|output'):build(candidate,**options)
    assert (out.read_bytes() if out.exists() else None)==before


@pytest.mark.parametrize('kind',['code','evidence'])
def test_changes_during_inventory_do_not_publish_a_stale_manifest(candidate,monkeypatch,kind):
    module=implementation();original=module._snapshot;calls=[];proto=candidate[2]
    def change(*args,**kwargs):
        result=original(*args,**kwargs);calls.append(1)
        if len(calls)==1:
            if kind=='code':(proto/'adapter.py').write_text('# changed while hashing\n')
            else:(candidate[3]/'late.log').write_text('arrived during inventory\n')
        return result
    monkeypatch.setattr(module,'_snapshot',change)
    with pytest.raises(ValueError,match='changed'):build(candidate)
    assert not (proto/'evidence/manifest.json').exists()
    assert not list((proto/'evidence').glob('.manifest-*.tmp'))


def test_concurrent_output_creation_is_preserved(candidate,monkeypatch):
    module=implementation();original=module._snapshot;calls=[];out=candidate[2]/'evidence/manifest.json'
    def change(*args,**kwargs):
        result=original(*args,**kwargs);calls.append(1)
        if len(calls)==2:out.write_text('{"other_writer":true}')
        return result
    monkeypatch.setattr(module,'_snapshot',change)
    with pytest.raises(FileExistsError):build(candidate)
    assert json.loads(out.read_text())=={'other_writer':True}
    assert not list(out.parent.glob('.manifest-*.tmp'))


@pytest.mark.parametrize('preview',[False,True])
def test_existing_public_identifier_hold_survives_new_inventory(candidate,tmp_path,preview):
    catalog,tid,proto,_,_=candidate;build(candidate);current=proto/'evidence/manifest.json'
    value=json.loads(current.read_text());value['public_identifier_status']='external_correction_pending'
    current.write_text(json.dumps(value));prior=sha(current)
    options={'output':tmp_path/'preview.json'} if preview else {'replace_sha256':prior}
    result=build(candidate,**options);new=json.loads(Path(result['manifest']).read_text())
    assert new.get('public_identifier_status')=='external_correction_pending'
    assert _prototype(catalog.root,catalog.describe(tid))['status']=='needs_followup'
