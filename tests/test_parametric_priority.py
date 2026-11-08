import hashlib
import json
import zipfile
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main
import pytest


def official(root, tid='aaaa00000001', original='0123abcd', split='training'):
    p = root / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    row = next(r for r in rows if r['task_id'] == tid)
    value = int(tid[-2:], 16) + 4
    row['train'] = [{'input': [[value]], 'output': [[2]]}]
    row['test'] = [{'input': [[value + 1]], 'output': [[4]]}]
    p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    p = root / f'shared/data/raw/arc-agi_{split}_challenges.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.loads(p.read_text()) if p.exists() else {}
    raw[original] = {'train': row['train'], 'test': [{'input': row['test'][0]['input']}]}
    p.write_text(json.dumps(raw))
    return raw[original]


def questions(root):
    p = root / 'REVIEW/questions/q.json'
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'schema': 'arcpuzzles-review-question-v1', 'id': 'q',
                            'version': 1, 'owner': 'ARCpuzzles', 'text': 'question'}))


def test_packet_priority_controls_inclusion_while_draw_is_uniform(library, tmp_path):
    official(library)
    questions(library)
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'packet.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
        assert manifest['main_ids'] == manifest['all_ids']
        assert manifest['parametric_priority']['main_ids'] == ['aaaa00000001']
        packet = tmp_path / 'unpacked'
        archive.extractall(packet)
    assignment = draw_main(packet, seed=b'\0' * 32)
    assert assignment['task_id'] == 'aaaa00000001'
    assert assignment['generator']['approved']
    assert '0123abcd' in (packet / 'DUTIES.md').read_text()
    assert 'parametric' in (packet / 'DUTIES.md').read_text().lower()


def test_evaluation_inspiration_is_independent_of_uniform_target_draw(library, tmp_path):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    official(library, split='evaluation'); questions(library)
    built=build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'focus.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        manifest=json.loads(archive.read('PACKET-MANIFEST.json'))
    policy=manifest['authoring_focus_policy']
    assert policy['schema']=='arcpuzzles-authoring-focus-policy-v1'
    assert policy['probability']=={'numerator':1,'denominator':10}
    focused=[]
    for index in range(300):
        seed=index.to_bytes(32,'big');tid,focus=main_selection_for_seed(manifest,seed)
        assert tid==manifest['main_ids'][index%len(manifest['main_ids'])]
        expected=int.from_bytes(hashlib.sha256(seed+b':evaluation-focus').digest(),'big')%10==0
        assert (focus is not None)==expected
        if focus:
            assert focus['source_task_id']=='0123abcd' and focus['training_admitted'] is False
            assert focus['mode']==('direct_related' if tid=='aaaa00000001' else 'inspired_extension')
            assert focus['relationship_verified'] is (tid=='aaaa00000001')
            focused.append((seed,tid))
    assert focused and any(tid!='aaaa00000001' for _,tid in focused)
    # An issued uniform packet without the new optional policy replays exactly.
    manifest.pop('authoring_focus_policy')
    assert all(main_selection_for_seed(manifest,seed)[1] is None for seed,_ in focused)


def test_evaluation_inspiration_reaches_unmapped_public_parent(library, tmp_path):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    official(library,split='evaluation');questions(library)
    p=library/'shared/data/raw/arc-agi_evaluation_challenges.json'
    raw=json.loads(p.read_text());raw['ffffffff']={'train':[{'input':[[9]],'output':[[8]]}],'test':[{'input':[[7]]}]};p.write_text(json.dumps(raw))
    built=build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'unmapped.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        manifest=json.loads(archive.read('PACKET-MANIFEST.json'));packet=tmp_path/'unpacked';archive.extractall(packet)
    seed=next(i.to_bytes(32,'big') for i in range(1000)
              if (main_selection_for_seed(manifest,i.to_bytes(32,'big'))[1] or {}).get('source_task_id')=='ffffffff')
    source=packet/'repo/shared/data/raw/arc-agi_evaluation_challenges.json'
    before=source.read_bytes();source.write_text('{}')
    with pytest.raises(ValueError,match='hash|changed'):
        draw_main(packet,seed=seed)
    assert not (packet/'ASSIGNMENT.json').exists()
    source.write_bytes(before)
    assignment=draw_main(packet,seed=seed)
    assert assignment['authoring_focus']['mode']=='inspired_extension'
    assert 'ffffffff' in (packet/'DUTIES.md').read_text()


@pytest.mark.parametrize('probability', [{'numerator':True,'denominator':10},
                                       {'numerator':1,'denominator':10.0}])
def test_new_authoring_probability_rejects_numeric_type_aliases(probability):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    manifest={'main_ids':['a'],'main_draw_policy':{'schema':'arcpuzzles-main-draw-policy-v2',
        'distribution':'uniform','ids':['a']},'authoring_focus_policy':{
        'schema':'arcpuzzles-authoring-focus-policy-v1','probability':probability,
        'target_selection':'unchanged_uniform_main','anchors':[]}}
    with pytest.raises(ValueError,match='authoring focus'):
        main_selection_for_seed(manifest,b'\0'*32)


def priority(root):
    from arcpuzzles.parametric_priority import build_parametric_priority
    return build_parametric_priority(Catalog(root))


def retain_prototype(root, tid='aaaa00000001', **changes):
    row = Catalog(root).describe(tid)
    home = root / 'generators' / tid / 'workspace/parametric/evidence'
    home.mkdir(parents=True)
    proof = home / 'program.rkt'
    proof.write_text('(rule! g)')
    record = {'task_id': tid, 'generator_sha256': row['generator_sha256'],
              'canonical_rule_hash': row['rule_hash'], 'verification_status': 'reviewer_reported',
              'parameters': {'direction': ['left', 'right']},
              'files': [{'path': proof.relative_to(root).as_posix(),
                         'sha256': hashlib.sha256(proof.read_bytes()).hexdigest()}]}
    record.update(changes)
    (home / 'manifest.json').write_text(json.dumps(record))
    return proof


def test_public_task_identity_is_required_not_an_official_looking_alias(library):
    official(library)
    p = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    rows[2]['aliases'] = ['0123abcd']
    p.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    result = priority(library)
    assert list(result['related_generators']) == ['aaaa00000001']
    assert result['covered_original_tasks'] == 1
    assert result['related_generators']['aaaa00000001']['origins'][0]['basis'] == 'exact_public_challenge'


def test_old_generator_lineage_hash_does_not_erase_original_ancestry(library):
    challenge = official(library)
    p = library / 'shared/data/derived/official_generator_lineage.jsonl'
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'generator_id': 'aaaa00000001', 'mapping_status': 'verified',
        'source_split': 'training', 'source_task_id': '0123abcd', 'relationship': 'exact_seed',
        'source_hashes': {'generator_sha256': '0' * 64,
                         'challenge_sha256': hashlib.sha256(json.dumps(challenge, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}}) + '\n')
    result = priority(library)
    assert result['main_ids'] == ['aaaa00000001']
    assert result['related_generators']['aaaa00000001']['ancestry_only']
    assert not Catalog(library).lineage('aaaa00000001')['verified']


def test_current_prototype_moves_queue_to_original_needing_repair(library):
    official(library)
    official(library, 'aaaa00000003', '89abcdef', 'evaluation')
    retain_prototype(library)
    result = priority(library)
    assert result['related_generators']['aaaa00000001']['prototype']['status'] == 'current'
    assert result['selected_tier'] == 'originals_need_repair_and_parameters'
    assert result['main_ids'] == ['aaaa00000003']
    assert result['provided_tasks'] == {'training': 1, 'evaluation': 1}


def test_stale_source_or_rule_or_evidence_requeues_original(library):
    official(library)
    proof = retain_prototype(library, generator_sha256='0' * 64)
    assert priority(library)['main_ids'] == ['aaaa00000001']
    manifest = proof.parent / 'manifest.json'
    value = json.loads(manifest.read_text())
    value['generator_sha256'] = Catalog(library).describe('aaaa00000001')['generator_sha256']
    value['canonical_rule_hash'] = 'bad-rule'
    manifest.write_text(json.dumps(value))
    assert priority(library)['related_generators']['aaaa00000001']['prototype']['status'] == 'stale'
    value['canonical_rule_hash'] = Catalog(library).describe('aaaa00000001')['rule_hash']
    manifest.write_text(json.dumps(value))
    proof.write_text('changed')
    assert priority(library)['related_generators']['aaaa00000001']['prototype']['status'] == 'stale'
    assert priority(library)['main_ids'] == ['aaaa00000001']


def test_documented_variant_needs_bound_reviewed_parent_not_current_semantic_approval(library):
    challenge = official(library)
    p = library / 'shared/data/derived/official_generator_lineage.jsonl'
    p.parent.mkdir(parents=True)
    entry = {'generator_id': 'aaaa00000003', 'mapping_status': 'candidate',
             'relationship': 'semantic_variant', 'source_split': 'training', 'source_task_id': '0123abcd',
             'source_hashes': {'generator_sha256': '0' * 64,
                              'challenge_sha256': hashlib.sha256(json.dumps(challenge, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}}
    p.write_text(json.dumps(entry) + '\n')
    assert 'aaaa00000003' not in priority(library)['related_generators']
    entry['mapping_status'] = 'verified'
    p.write_text(json.dumps(entry) + '\n')
    related = priority(library)['related_generators']['aaaa00000003']
    assert related['origins'][0]['basis'] == 'reviewed_lineage'
    assert not related['origins'][0]['current_generator_matches_lineage']
    assert not related['approved'] and not related['training_admitted']
    entry['source_hashes']['challenge_sha256'] = 'bad-hash'
    p.write_text(json.dumps(entry) + '\n')
    assert 'aaaa00000003' not in priority(library)['related_generators']


def test_no_official_sources_or_finished_prototype_falls_back_to_normal_pool(library):
    assert priority(library)['main_ids'] == ['aaaa00000003']
    official(library)
    retain_prototype(library)
    result = priority(library)
    assert result['selected_tier'] == 'other_unapproved'
    assert result['main_ids'] == ['aaaa00000003']


def test_input_ancestry_does_not_read_or_require_evaluation_solutions(library):
    official(library, split='evaluation')
    p = library / 'shared/data/raw/arc-agi_evaluation_solutions.json'
    p.write_text('THIS IS NOT JSON AND MUST NOT BE READ')
    assert priority(library)['provided_task_count'] == 1
    assert priority(library)['main_ids'] == ['aaaa00000001']


def test_accepted_legacy_evidence_with_parameters_inside_reports_stays_complete(library):
    official(library)
    proof = retain_prototype(library)
    p = proof.parent / 'manifest.json'
    record = json.loads(p.read_text())
    record.pop('parameters')  # Older retained wrappers keep declarations in their hashed evidence files.
    p.write_text(json.dumps(record))
    state = priority(library)['related_generators']['aaaa00000001']['prototype']
    assert state['status'] == 'current'
    assert state['parameter_declaration'] == 'retained_evidence'


def test_priority_cli_writes_the_same_source_bound_queue(library, tmp_path):
    from arcpuzzles.cli import main
    official(library)
    out = tmp_path / 'priority.json'
    assert main(['--library', str(library), 'review', 'parametric-priority', '--out', str(out)]) == 0
    assert json.loads(out.read_text()) == priority(library)


def test_pending_public_identifier_repair_stays_in_external_queue(library):
    official(library)
    retain_prototype(library, public_identifier_status='external_correction_pending')
    result = priority(library)
    state = result['related_generators']['aaaa00000001']['prototype']
    assert state['status'] == 'needs_followup'
    assert state['reason'] == 'public_identifier_correction_pending'
    assert state['verification_status'] == 'reviewer_reported'
    assert result['main_ids'] == ['aaaa00000001']
    assert result['counts']['current_prototypes'] == 0
    assert Catalog(library).describe('aaaa00000001')['approved']


def test_pending_evaluation_prototype_keeps_parameter_priority(library):
    official(library, split='evaluation')
    proof = retain_prototype(library, public_identifier_status='external_correction_pending')
    anchor = priority(library)['evaluation_focus']['anchors'][0]
    assert anchor['selected_tier'] == 'approved_need_parameters'
    assert anchor['main_ids'] == ['aaaa00000001']
    # Pending status cannot hide changed or missing retained evidence.
    proof.write_text('corrupted evidence')
    assert priority(library)['related_generators']['aaaa00000001']['prototype']['status'] == 'stale'
