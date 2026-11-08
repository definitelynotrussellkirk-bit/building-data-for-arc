"""Publisher transactions; fixtures do not claim to execute the reference runtime."""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def publication(library, tmp_path, monkeypatch, request):
    from arcpuzzles import review_full_packet as builder
    from arcpuzzles import review_packet_publish as publisher
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.review_packet_verify import inspect_packet, _compare_owner
    archive = library / 'var/review' / builder.RACKET_ARCHIVE_NAME
    archive.parent.mkdir(parents=True);archive.write_bytes(b'fixture runtime, never executed')
    monkeypatch.setattr(builder, 'RACKET_ARCHIVE_SHA256', sha(archive))
    monkeypatch.setattr(publisher, 'RACKET_ARCHIVE_SHA256', sha(archive))
    review = library / 'REVIEW';(review / 'questions').mkdir(parents=True)
    (review / 'questions/q.json').write_text(json.dumps({'schema':'arcpuzzles-review-question-v1',
        'id':'q','version':1,'owner':'test','text':'test'}))
    packet = tmp_path / 'packet.zip'
    builder.build_full_packet(Catalog(library), review, packet, archive,
                              selection_size=getattr(request,'param',None), workspace_layout=True)
    checked = inspect_packet(packet);task = checked['manifest']['main_ids'][0]
    verification = tmp_path / 'verified';verification.mkdir();(verification / 'logs').mkdir();(verification / 'harness').mkdir()
    commands = []
    for i in range(2):
        command = {'exit_code':0,'failure':None}
        for stream in ['stdout','stderr']:
            path = verification / 'logs' / f'{i}.{stream}';path.write_text('fixture output\n')
            command[stream] = {'path':str(path),'sha256':sha(path)}
        commands.append(command)
    harness = []
    for name in publisher.HARNESS:
        from arcpuzzles import review_packet_verify
        path = verification / 'harness' / name;path.write_bytes(Path(review_packet_verify.__file__).with_name(name).read_bytes())
        harness.append({'path':'harness/'+name,'sha256':sha(path)})
    row = checked['manifest']['generators'][task]
    report = {'schema':'arcpuzzles-review-packet-verification-v1','status':'passed',
        'packet_id':checked['packet_id'],'packet':{'path':str(packet),'sha256':sha(packet)},
        'archive_members_verified':checked['member_count'],'task_id':task,'seed':17,'demos':3,'queries':4,
        'owner_sources':_compare_owner(library,checked['manifest']), 'commands':[commands[0]],'harness':harness,
        'cold_probe':{'status':'passed','packet_id':checked['packet_id'],'source_reads_confined':True,
            'racket':{'bundled_runtime_selected':True,'version':'fixture runtime'},
            'episode':{'demonstrations':3,'queries':4,'reference_labels_replayed':7,
                       'generator_sha256':row['generator_sha256'],'executed_rule_hash':row['rule_hash']},
            'commands':[commands[1]],'accepted_export':None},'training_admitted':False}
    proof = verification / 'verification.json';proof.write_text(json.dumps(report))
    stable = library / 'var/review/SEND-THIS-ARCpuzzles-review.zip';stable.parent.mkdir(parents=True,exist_ok=True);stable.write_bytes(b'previous ZIP')
    metadata = review / 'full-packet-current.json';metadata.write_text(json.dumps({'schema':'arcpuzzles-full-packet-handoff-v1',
        'sha256':sha(stable),'zip':str(stable),'preserve_me':{'training_admitted':False}}))
    share = tmp_path / 'downloads';share.mkdir()
    return {'catalog':Catalog(library),'packet':packet,'proof':proof,'report':report,'checked':checked,
            'stable':stable,'metadata':metadata,'out':library/'var/review/publication', 'share_dir':share}


def publish(case, **kwargs):
    from arcpuzzles.review_packet_publish import publish_packet
    return publish_packet(case['catalog'],case['packet'],case['proof'],case['out'],**kwargs)


def test_successful_publication_binds_copies_proof_and_preserves_unrelated_state(publication):
    c=publication;result=publish(c,share_dir=c['share_dir'])
    assert result['status']=='published'
    current=json.loads(c['metadata'].read_text())
    assert c['stable'].read_bytes()==c['packet'].read_bytes()==Path(current['share_copy']).read_bytes()
    assert current['sha256']==sha(c['packet']) and current['packet_id']==c['checked']['packet_id']
    assert current['preserve_me']=={'training_admitted':False}
    assert current['build_receipt_sha256']==sha(Path(current['build_receipt']))
    assert current['publication_receipt']==str(c['out']/'publication.json')
    assert current['ready_to_send'] is True and current['current_source_matches_packet'] is True
    assert current['current_packet_validation']['verification_reexecuted'] is False
    assert json.loads((c['out']/'publication.json').read_text())['status']=='published'


@pytest.mark.parametrize('field,value', [('status','failed'),('packet_id','0'*64),
    ('owner_sources',None),('training_admitted',True)])
def test_rejects_failed_unbound_or_admitted_proof_before_publication(publication,field,value):
    c=publication;c['report'][field]=value;c['proof'].write_text(json.dumps(c['report']))
    with pytest.raises(ValueError):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP' and not c['out'].exists()


def test_missing_or_changed_log_and_harness_cannot_support_publication(publication):
    c=publication;Path(c['report']['commands'][0]['stdout']['path']).write_text('changed')
    with pytest.raises(ValueError,match='evidence|log|hash'):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP' and not c['out'].exists()


def test_stale_owner_source_rejects_an_otherwise_passing_receipt(publication):
    c=publication;tid=c['report']['task_id'];(c['catalog'].root/f'generators/{tid}/generator.py').write_text('changed\n')
    with pytest.raises(ValueError,match='Owner source differs'):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP' and not c['out'].exists()


def test_existing_share_collision_is_not_overwritten(publication):
    c=publication;target=c['share_dir']/('ARCpuzzles-review-current-'+sha(c['packet'])[:8]+'.zip');target.write_bytes(b'user file')
    with pytest.raises(FileExistsError):publish(c,share_dir=c['share_dir'])
    assert target.read_bytes()==b'user file' and c['stable'].read_bytes()==b'previous ZIP'


def test_symlink_destination_is_rejected_without_touching_its_target(publication,tmp_path):
    c=publication;target=tmp_path/'user.zip';target.write_bytes(b'user data');c['stable'].unlink();c['stable'].symlink_to(target)
    with pytest.raises(ValueError,match='[Ss]ymlink'):publish(c)
    assert target.read_bytes()==b'user data'


def test_metadata_failure_restores_the_previous_ready_pair(publication,monkeypatch):
    from arcpuzzles import review_packet_publish_files as files
    c=publication;before=c['metadata'].read_bytes();replace=files.os.replace;failed=False
    def fail_once(source,destination):
        nonlocal failed
        if Path(destination)==c['metadata'] and not failed:
            failed=True;raise OSError('injected metadata write failure')
        return replace(source,destination)
    monkeypatch.setattr(files.os,'replace',fail_once)
    with pytest.raises(OSError,match='injected'):publish(c,share_dir=c['share_dir'])
    assert c['stable'].read_bytes()==b'previous ZIP' and c['metadata'].read_bytes()==before
    assert list(c['share_dir'].iterdir())==[]
    receipt=json.loads((c['out']/'publication.json').read_text())
    assert receipt['status']=='failed' and receipt['previous_ready_restored'] is True


def test_unexpected_stable_bytes_are_not_replaced(publication):
    c=publication;c['stable'].write_bytes(b'unrecorded user change')
    with pytest.raises(ValueError,match='[Cc]urrent|[Ss]table'):publish(c)
    assert c['stable'].read_bytes()==b'unrecorded user change'


def test_packet_changed_after_validation_cannot_be_published_under_its_old_hash(publication,monkeypatch):
    from arcpuzzles import review_packet_publish as publisher
    c=publication;original=publisher._metadata
    def mutate_after_metadata(*args,**kwargs):
        result=original(*args,**kwargs);c['packet'].write_bytes(b'changed after validation');return result
    monkeypatch.setattr(publisher,'_metadata',mutate_after_metadata)
    with pytest.raises(ValueError,match='changed|differs|hash'):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP'


@pytest.mark.parametrize('field,value',[('cold_probe',[]),('commands',[{}]),('harness',[]),('owner_sources',[])])
def test_malformed_verification_is_a_rejection_not_a_traceback(publication,field,value):
    c=publication;c['report'][field]=value;c['proof'].write_text(json.dumps(c['report']))
    with pytest.raises(ValueError):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP'


def test_owner_source_changed_while_staging_cannot_be_marked_current(publication,monkeypatch):
    from arcpuzzles import review_packet_publish as publisher
    c=publication;original=publisher._metadata
    def mutate_after_metadata(*args,**kwargs):
        result=original(*args,**kwargs)
        (c['catalog'].root/f"generators/{c['report']['task_id']}/generator.py").write_text('changed while staging\n')
        return result
    monkeypatch.setattr(publisher,'_metadata',mutate_after_metadata)
    with pytest.raises(ValueError,match='Owner source differs'):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP'


def test_public_cli_publishes_using_the_existing_completed_verification(publication,capsys):
    from arcpuzzles.cli import main
    c=publication
    assert main(['--library',str(c['catalog'].root),'review','publish-packet',str(c['packet']),
                 '--verification',str(c['proof']),'--out',str(c['out']),'--share-dir',str(c['share_dir'])])==0
    assert json.loads(capsys.readouterr().out)['status']=='published'
    assert c['stable'].read_bytes()==c['packet'].read_bytes()


def test_verification_asset_cannot_escape_its_retained_directory(publication,tmp_path):
    c=publication;outside=tmp_path/'outside-log';outside.write_text('not in the verification tree')
    c['report']['commands'][0]['stdout']={'path':str(c['proof'].parent/'..'/outside.name),'sha256':sha(outside)}
    c['proof'].write_text(json.dumps(c['report']))
    with pytest.raises(ValueError,match='evidence|directory'):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP'


@pytest.mark.parametrize('field,value',[('commands',None),('owner_sources',['bad']),('harness',[None])])
def test_malformed_nested_proof_is_rejected_cleanly(publication,field,value):
    c=publication;c['report'][field]=value;c['proof'].write_text(json.dumps(c['report']))
    with pytest.raises(ValueError):publish(c)
    assert c['stable'].read_bytes()==b'previous ZIP'


def test_publication_does_not_require_a_git_executable(publication,monkeypatch):
    from arcpuzzles import review_packet_publish as publisher
    def unavailable(*args,**kwargs):raise FileNotFoundError('git is not installed')
    monkeypatch.setattr(publisher.subprocess,'run',unavailable)
    result=publish(publication)
    assert result['status']=='published'
    assert json.loads(publication['metadata'].read_text())['source_commit'] is None


def test_matching_existing_share_copy_is_reused_without_losing_it(publication):
    c=publication;target=c['share_dir']/('ARCpuzzles-review-current-'+sha(c['packet'])[:8]+'.zip')
    target.write_bytes(c['packet'].read_bytes());before=target.stat().st_ino
    assert publish(c,share_dir=c['share_dir'])['status']=='published'
    assert target.stat().st_ino==before and target.read_bytes()==c['packet'].read_bytes()


@pytest.mark.parametrize('destination',['stable','metadata'])
def test_concurrent_destination_change_is_preserved_instead_of_overwritten(publication,monkeypatch,destination):
    from arcpuzzles import review_packet_publish as publisher
    c=publication;original=publisher._metadata;changed=None
    def change_destination(*args,**kwargs):
        nonlocal changed
        result=original(*args,**kwargs)
        if destination=='stable':changed=b'new user ZIP';c['stable'].write_bytes(changed)
        else:
            value=json.loads(c['metadata'].read_text());value['owner_user_note']='preserve this edit'
            changed=json.dumps(value).encode();c['metadata'].write_bytes(changed)
        return result
    monkeypatch.setattr(publisher,'_metadata',change_destination)
    with pytest.raises(ValueError,match='changed|differs'):publish(c)
    assert c[destination].read_bytes()==changed


@pytest.mark.parametrize('publication',[3],indirect=True)
def test_handoff_keeps_selection_identity_without_repeating_manifest_reason_rows(publication):
    c=publication;reasons=c['checked']['manifest']['selection']['reasons']
    assert reasons  # A real selected-packet fixture must exercise this detail.
    publish(c)
    current=json.loads(c['metadata'].read_text())
    assert current['packet_selection']['selected_ids']==c['checked']['manifest']['all_ids']
    assert 'reasons' not in current['packet_selection']
    assert current['packet_selection']['reasons_in_packet_manifest']=='selection.reasons'
    with zipfile.ZipFile(c['packet']) as z:
        assert json.loads(z.read('WORK/PACKET-MANIFEST.json'))['selection']['reasons']==reasons
