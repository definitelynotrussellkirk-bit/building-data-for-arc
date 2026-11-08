"""Isolated public-owner metadata/evidence tests; never native acceptance jobs."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog, sha256
from arcpuzzles.review_public_creation import SOURCE, SOLUTIONS, PREFLIGHT, creation_queue, digest
from arcpuzzles import review_public_admission as owner


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')


@pytest.fixture
def public_source(library):
    pid='1234abcd';tid='public_eval_'+pid
    parent={'train':[{'input':[[1,2]],'output':[[1,2]]}], 'test':[{'input':[[4,5]]}]}
    write(library/SOURCE,{pid:parent});write(library/SOLUTIONS,{pid:[[[4,5]]]})
    item=creation_queue(library)[0]
    home=library/'generators'/tid;home.mkdir(parents=True)
    (home/'generator.py').write_text("VERSION='1.0.0'\nSUMMARY='Test-only source'\nRULE_TASK_ID='ee_1234abcd'\n")
    program='(rule! (lambda (g) g))';(home/'reference.rkt').write_text(program)
    base=home/'workspace/parametric';base.mkdir(parents=True)
    (base/'adapter.py').write_text('# Test metadata only; never executed\n')
    (base/'family.py').write_text('# Adjacent runtime sampler resource\n')
    write(base/'promotion.json',{'schema':'arcpuzzles-parametric-adapter-v1',
        'adapter':f'generators/{tid}/workspace/parametric/adapter.py','parameters':{'reverse':[False,True]},
        'default':{'reverse':False},'limits':{'demos':[2,6],'queries':[1,4]}})
    return library,item,owner._parent(library,item),program


def authorities(root):
    return {name:(root/name).read_bytes() for name in ('catalog/puzzles.jsonl','catalog/runtime_files.json','shared/data/canonical/puzzles.jsonl')}


def test_legacy_reported_source_is_checked_before_reference_rebinding(public_source):
    from arcpuzzles.review_public_compatibility import repair_reference_id
    root, item, parent, program = public_source; tid = item['task_id']
    source = root / f'generators/{tid}/generator.py'
    source.write_text(source.read_text().replace("RULE_TASK_ID='ee_1234abcd'\n", ''))
    binding = {'task_id': tid, 'files': [{'path': source.relative_to(root).as_posix(), 'sha256': sha256(source)}]}
    before = source.read_bytes()
    assert owner._reviewer_binding(root, tid, item['public_task_id'], binding) == binding
    assert source.read_bytes() == before
    repair_reference_id(root, tid, item['public_task_id'])
    repaired = owner._reviewer_binding(root, tid, item['public_task_id'], binding)
    assert repaired['files'][0]['sha256'] == sha256(source)
    assert binding['files'][0]['sha256'] != repaired['files'][0]['sha256']


def test_authoring_contract_rejects_root_resource_before_runtime(public_source):
    from arcpuzzles.review_public_creation import authoring_contract
    root, item, parent, program = public_source
    tid = item['task_id']; base = root / f'generators/{tid}/workspace/parametric'
    path = base / 'promotion.json'; contract = json.loads(path.read_text())
    contract['resources'] = [f'generators/{tid}/reference.rkt']; write(path, contract)
    with pytest.raises(ValueError, match='Contract resources'):
        authoring_contract(root, tid)
    (base / 'canonical.rkt').write_text(program)
    contract['resources'] = [f'generators/{tid}/workspace/parametric/canonical.rkt']
    write(path, contract)
    assert authoring_contract(root, tid) == contract


def test_registration_is_unapproved_and_preserves_relocated_resource_layout(public_source):
    root,item,parent,program=public_source;tid=item['task_id']
    catalog=owner._register(Catalog(root),item,parent,program)
    selected=catalog.describe(tid)
    assert selected['approved'] is False and selected['train_safety']=='unverified'
    assert selected['mix_weight']==0
    assert selected['rule_task_id']=='ee_1234abcd'
    assert selected['parent_ids']==[item['public_task_id']]
    canonical = catalog._variants()[selected['rule_task_id']][0]
    assert len(canonical['content_hash']) == 64
    assert canonical['parent_hash'] == item['public_task_id']
    assert canonical['solution_language'] == 'racket'
    mappings=json.loads((root/'catalog/runtime_files.json').read_text())
    for suffix in ('generator.py','reference.rkt','workspace/parametric/family.py','workspace/parametric/promotion.json'):
        assert {'path':f'generators/{tid}/{suffix}','target':f'puzzle_generators/per_puzzle/{tid}/{suffix}'} in mappings
    # Re-registering the exact identity is idempotent at the data level.
    before=authorities(root);owner._register(Catalog(root),item,parent,program)
    assert authorities(root)==before


def test_registration_backfills_trainer_provenance_without_rule_change(public_source):
    root, item, parent, program = public_source
    catalog = owner._register(Catalog(root), item, parent, program)
    path = root / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        if row['task_id'] == 'ee_1234abcd':
            row.pop('content_hash', None); row.pop('parent_hash', None)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    updated = owner._register(Catalog(root), item, parent, program)
    row = updated._variants()['ee_1234abcd'][0]
    assert row['program_solution'] == program
    assert row['content_hash'] and row['parent_hash'] == item['public_task_id']


def test_registration_mapping_conflict_has_no_partial_canonical_write(public_source):
    root,item,parent,program=public_source
    path=root/'catalog/runtime_files.json';mappings=json.loads(path.read_text())
    mappings.append({'path':'generators/aaaa00000001/generator.py','target':f"puzzle_generators/per_puzzle/{item['task_id']}/reference.rkt"})
    write(path,mappings);before=authorities(root)
    with pytest.raises(ValueError,match='Conflicting runtime'):
        owner._register(Catalog(root),item,parent,program)
    assert authorities(root)==before


def test_invalid_generator_metadata_does_not_mutate_catalog(public_source):
    root,item,parent,program=public_source
    (root/'generators'/item['task_id']/'generator.py').write_text('def broken(\n')
    before=authorities(root)
    with pytest.raises(SyntaxError):owner._register(Catalog(root),item,parent,program)
    assert authorities(root)==before


def test_registration_write_failure_rolls_back_all_authorities(public_source,monkeypatch):
    root,item,parent,program=public_source;before=authorities(root)
    original=owner.os.replace;calls=[]
    def fail_second(source,destination):
        calls.append(destination)
        if len(calls)==2:raise OSError('simulated second authority write failure')
        return original(source,destination)
    monkeypatch.setattr(owner.os,'replace',fail_second)
    with pytest.raises(OSError,match='simulated'):owner._register(Catalog(root),item,parent,program)
    assert authorities(root)==before
    assert not list((root/'catalog').glob('*.public.tmp'))


def test_binding_rejects_duplicate_changed_and_symlinked_sources(public_source):
    root,item,parent,program=public_source
    relative=f"generators/{item['task_id']}/reference.rkt";path=root/relative
    row={'path':relative,'sha256':sha256(path)}
    with pytest.raises(ValueError,match='Duplicate'):owner._check_binding(root,{'files':[row,row]})
    with pytest.raises(ValueError,match='differs'):owner._check_binding(root,{'files':[{**row,'sha256':'0'*64}]})
    link=root/'generators'/item['task_id']/'copy.rkt';link.symlink_to(path)
    with pytest.raises(ValueError,match='regular'):owner._check_binding(root,{'files':[{'path':link.relative_to(root).as_posix(),'sha256':sha256(path)}]})


def coverage_fixture(public_source,monkeypatch):
    root,item,parent,program=public_source;tid=item['task_id'];home=root/'generators'/tid
    folder=home/'evidence/public-owner/isolated/preflight'
    pairs=[{'split':split,'index':i,**pair} for split in ('train','test') for i,pair in enumerate(parent[split]) if 'output' in pair]
    write(folder/'original-pairs.json',{'status':'passed','public_creation':item,'pairs':pairs,'racket':{'backend':'racket','protected':True}})
    write(folder/'execution.json',{'isolated_test_double':True})
    reference=hashlib.sha256(program.encode()).hexdigest()
    receipt={'schema':PREFLIGHT,'task_id':tid,'status':'passed','public_creation':item,'owner_accepted':False,
             'verification_status':'authoring_preflight_not_owner_qualification','contract':{'default':{'reverse':False}},
             'programs':{'{"reverse":false}':reference},
             'evidence_sha256':{n:sha256(folder/n) for n in ('original-pairs.json','execution.json')}}
    write(folder/'preflight.json',receipt)
    result={'status':'accepted','objective_met':True,'task_id':tid,'public_creation':item,
            'originals_owner_executed':True,'reference_sha256':reference,'acceptance_sha256':'a'*64,
            'owner_preflight':(folder/'preflight.json').relative_to(root).as_posix(),
            'owner_preflight_sha256':sha256(folder/'preflight.json')}
    current=home/'evidence/parametric-admission-current.json';write(current,result)
    monkeypatch.setattr('arcpuzzles.parametric_promotion.status',lambda catalog,task_id:{'status':'accepted','acceptance_sha256':'a'*64})
    owner.record_coverage(root,result,current)
    return root,item,result,folder,current


def test_coverage_requires_retained_original_execution_and_current_acceptance(public_source,monkeypatch):
    root,item,result,folder,current=coverage_fixture(public_source,monkeypatch)
    assert owner.verified_coverage(root)==[item['public_task_id']]
    (folder/'original-pairs.json').unlink()
    assert owner.verified_coverage(root)==[]


def test_rehashed_incomplete_original_pairs_cannot_count_as_coverage(public_source,monkeypatch):
    root,item,result,folder,current=coverage_fixture(public_source,monkeypatch)
    originals=json.loads((folder/'original-pairs.json').read_text());originals['pairs']=originals['pairs'][:1]
    write(folder/'original-pairs.json',originals)
    receipt=json.loads((folder/'preflight.json').read_text());receipt['evidence_sha256']['original-pairs.json']=sha256(folder/'original-pairs.json')
    write(folder/'preflight.json',receipt);result['owner_preflight_sha256']=sha256(folder/'preflight.json')
    owner.record_coverage(root,result,current)
    assert owner.verified_coverage(root)==[]


def test_blocked_retry_does_not_destroy_immutable_accepted_coverage_proof(public_source,monkeypatch):
    root,item,result,folder,current=coverage_fixture(public_source,monkeypatch)
    before=(root/owner.REGISTRY).read_bytes()
    blocked={**result,'status':'blocked','objective_met':False}
    write(current,blocked);owner.record_coverage(root,blocked,current)
    assert (root/owner.REGISTRY).read_bytes()==before
    assert owner.verified_coverage(root)==[item['public_task_id']]
    monkeypatch.setattr('arcpuzzles.parametric_promotion.status',lambda *args:{'status':'stale'})
    assert owner.verified_coverage(root)==[]


def test_gold_or_reference_drift_invalidates_coverage(public_source,monkeypatch):
    root,item,result,folder,current=coverage_fixture(public_source,monkeypatch)
    write(root/SOLUTIONS,{item['public_task_id']:[[[9]]]})
    assert owner.verified_coverage(root)==[]


@pytest.mark.parametrize('content',['not json','[]','{"schema":"arcpuzzles-public-eval-coverage-v1","parents":[]}'])
def test_corrupt_registry_fails_closed_without_breaking_queue(public_source,content):
    root,*_=public_source;path=root/owner.REGISTRY;path.parent.mkdir(exist_ok=True);path.write_text(content)
    assert owner.verified_coverage(root)==[]


def test_later_owner_receipt_writes_do_not_change_native_binding(public_source):
    from arcpuzzles.parametric_manifest import build_manifest
    from arcpuzzles.parametric_promotion import _ready
    root,item,parent,program=public_source;tid=item['task_id'];home=root/'generators'/tid
    catalog=owner._approve(owner._register(Catalog(root),item,parent,program),tid)
    folder=home/'evidence/public-owner/isolated';write(folder/'preflight.json',{'isolated_static_fixture':True})
    build_manifest(catalog,tid,evidence=folder.relative_to(root).as_posix(),reported_checks='Static isolated fixture; no execution.')
    before=_ready(Catalog(root),tid)[1]
    write(folder/'native-bound-witness.json',{'source_binding':before})
    write(home/'evidence/parametric-admission-current.json',{'status':'blocked'})
    assert _ready(Catalog(root),tid)[1]==before
    write(folder/'preflight.json',{'tampered':True})
    with pytest.raises(ValueError,match='not current'):_ready(Catalog(root),tid)


@pytest.mark.parametrize('program',['(rule! (lambda (g) g)))','(rule! (lambda (g) g)) 42','(rule! (lambda (g) g)','42'])
def test_owner_strict_parser_rejects_trailing_or_incomplete_forms(public_source,program):
    import shutil
    root,*_=public_source
    source=Path(__file__).resolve().parents[1]/'shared/runtime/arc_repl/parser.py'
    destination=root/'shared/runtime/arc_repl/parser.py';destination.parent.mkdir(parents=True)
    shutil.copyfile(source,destination)
    (destination.parent/'__init__.py').write_text('')
    owner._strict_programs(root,['(rule! (lambda (g) g)) ; valid complete expression'])
    with pytest.raises(ValueError,match='complete'):
        owner._strict_programs(root,[program])


def legacy_placeholder(public_source):
    """Recreate only the never-approved shape emitted by the first owner attempt."""
    root,item,parent,program=public_source;tid=item['task_id']
    owner._register(Catalog(root),item,parent,program)
    catalog=root/'catalog/puzzles.jsonl'
    rows=[json.loads(line) for line in catalog.read_text().splitlines()]
    for row in rows:
        if row['id']==tid:row['rule_task_id']=tid
    catalog.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    canonical=root/'shared/data/canonical/puzzles.jsonl'
    rows=[json.loads(line) for line in canonical.read_text().splitlines()]
    for row in rows:
        if row['task_id']=='ee_1234abcd':row['task_id']=tid
    canonical.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    return root,item,parent,program


def test_exact_never_approved_placeholder_migrates_authority_without_touching_other_rows(public_source):
    root,item,parent,program=legacy_placeholder(public_source);tid=item['task_id']
    canonical=root/'shared/data/canonical/puzzles.jsonl'
    unrelated=[line for line in canonical.read_bytes().splitlines() if json.loads(line)['task_id']!=tid]
    catalog=owner._register(Catalog(root),item,parent,program)
    assert catalog.describe(tid)['rule_task_id']=='ee_1234abcd'
    assert catalog.describe(tid)['approved'] is False
    assert catalog._variants().get(tid,[])==[]
    assert catalog._variants()['ee_1234abcd'][0]['program_solution']==program
    assert [line for line in canonical.read_bytes().splitlines() if json.loads(line)['task_id']!='ee_1234abcd']==unrelated


@pytest.mark.parametrize('condition',['reviewed_safety','positive_weight','review_hash','review_status','accepted_artifact','foreign_provenance','authority_collision'])
def test_placeholder_migration_refuses_approved_or_foreign_state(public_source,condition):
    root,item,parent,program=legacy_placeholder(public_source);tid=item['task_id']
    path=root/'catalog/puzzles.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
    selected=next(row for row in rows if row['id']==tid)
    if condition=='reviewed_safety':selected['train_safety']='reviewed_safe'
    if condition=='positive_weight':selected['mix_weight']=1
    if condition=='review_hash':selected['reviewed_rule_hash']='a'*12
    if condition=='review_status':selected['review_status']='previous_owner_approval'
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    if condition=='accepted_artifact':write(root/f'generators/{tid}/parametric/accepted.json',{'historical':True})
    canonical=root/'shared/data/canonical/puzzles.jsonl'
    rows=[json.loads(line) for line in canonical.read_text().splitlines()]
    if condition=='foreign_provenance':
        next(row for row in rows if row['task_id']==tid)['public_creation']['challenge_sha256']='0'*64
    if condition=='authority_collision':
        rows.append({**next(row for row in rows if row['task_id']==tid),'task_id':'ee_1234abcd'})
    canonical.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    before=authorities(root)
    with pytest.raises(ValueError,match='never-approved|provenance|authority'):
        owner._register(Catalog(root),item,parent,program)
    assert authorities(root)==before


def test_reference_id_is_accepted_by_actual_frozen_runner():
    from types import SimpleNamespace
    from arcpuzzles.parametric_worker import _local_imports
    from arcpuzzles.review_public_creation import reference_id
    runtime=Path(__file__).resolve().parents[1]/'shared/runtime'
    with _local_imports(runtime,runtime):
        from puzzle_generators.runner import _resolve_rule_task_id
        assert _resolve_rule_task_id('public_eval_1234abcd',SimpleNamespace(RULE_TASK_ID=reference_id('1234abcd')),kind='per_puzzle')=='ee_1234abcd'
        with pytest.raises(ValueError,match='unsafe RULE_TASK_ID'):
            _resolve_rule_task_id('public_eval_1234abcd',SimpleNamespace(),kind='per_puzzle')


@pytest.mark.parametrize('source',["# missing\n", "RULE_TASK_ID='public_eval_1234abcd'\n", "RULE_TASK_ID='ee_'+'1234abcd'\n", "RULE_TASK_ID='ee_1234abcd'\nRULE_TASK_ID='ee_1234abcd'\n"])
def test_preflight_reference_literal_check_rejects_missing_computed_or_wrong_id(tmp_path,source):
    from arcpuzzles.review_public_creation import validate_reference_id
    path=tmp_path/'generator.py';path.write_text(source)
    with pytest.raises(ValueError,match='literal RULE_TASK_ID'):
        validate_reference_id(path,'1234abcd')
