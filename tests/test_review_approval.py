"""Approval follows accepted repairs, with exact-byte drift and honest provenance."""
import json
from pathlib import Path
import zipfile

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_approval import approve_reviews, generator_metadata
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_integrate import integrate_full_candidate
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_return import build_full_return
from test_review_full_collect import _return


def test_accepted_disposition_without_integration_evidence_cannot_backfill_approval(library, tmp_path):
    from arcpuzzles.review_full_integrate import record_full_disposition
    contract, _ = _return(library, tmp_path, seed=2, edit=True)
    collect_full_returns(library / "REVIEW", tmp_path)
    record_full_disposition(library / "REVIEW", contract["assignment_id"], 1,
                            "generator", "accepted", "Disposition alone is not source integration.")
    before = (library / "catalog/puzzles.jsonl").read_bytes()
    result = approve_reviews(Catalog(library), library / "REVIEW", all_integrated=True)
    assert result["safety_reviews_recorded"] == 0
    assert result["skipped"][0]["reason"] == "missing_integration_evidence"
    assert (library / "catalog/puzzles.jsonl").read_bytes() == before
    assert not Catalog(library).describe(contract["task_id"])["approved"]


def repair(library, tmp_path):
    contract, _ = _return(library, tmp_path, seed=2, edit=True)
    collect_full_returns(library / 'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library / 'REVIEW',
              contract['assignment_id'], 1, {'generator'}, reviewer_reported=True)
    return contract, result


def test_repair_approval_is_source_bound_and_keeps_reported_provenance(library, tmp_path):
    contract, result = repair(library, tmp_path)
    row = Catalog(library).describe(contract['task_id'])
    assert row['approved']
    assert row['approval_verification_status'] == 'reviewer_reported'
    record = json.loads((library / row['approval_receipt']).read_text())
    assert record['previous_catalog_record']['train_safety'] == 'unverified'
    assert record['trajectory_training_admitted'] is False
    assert not (library / 'var/review/full-checks').exists()
    (library / row['generator']).write_text('VERSION = "unreviewed change"\n')
    row = Catalog(library).describe(contract['task_id'])
    assert not row['approved']
    assert 'generator_changed_since_review' in row['approval_reasons']
    again = approve_reviews(Catalog(library), library / 'REVIEW', all_integrated=True)
    assert again['safety_reviews_recorded'] == 0
    assert 'superseded_generator_source' in {r['reason'] for r in again['skipped']}


def test_backfill_is_idempotent(library, tmp_path):
    contract, result = repair(library, tmp_path)
    before = (library / 'catalog/puzzles.jsonl').read_bytes()
    again = approve_reviews(Catalog(library), library / 'REVIEW', all_integrated=True)
    assert again['safety_reviews_recorded'] == 0
    assert again['newly_effective_approvals'] == 0
    assert (library / 'catalog/puzzles.jsonl').read_bytes() == before


def test_literal_metadata_does_not_execute_reviewer_source(tmp_path):
    source = tmp_path / 'generator.py'
    source.write_text("raise RuntimeError('must not execute')\nVERSION: str = '3.1'\nSUMMARY = ('fresh ' 'description')\n")
    assert generator_metadata(source) == {'version': '3.1', 'summary': 'fresh description'}


def test_backfill_refreshes_stale_metadata_without_new_approval(library, tmp_path):
    contract, _ = repair(library, tmp_path)
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        if row['id'] == contract['task_id']:
            row['version'] = 'stale'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    before = Catalog(library).describe(contract['task_id'])
    result = approve_reviews(Catalog(library), library / 'REVIEW', all_integrated=True)
    after = Catalog(library).describe(contract['task_id'])
    assert after['version'] == '2.0'
    assert after['approval_receipt'] == before['approval_receipt']
    assert after['approval_verification_status'] == 'reviewer_reported'
    assert result['safety_reviews_recorded'] == 0
    assert len(result['metadata_refreshed']) == 1


def test_packet_transports_the_bound_approval_receipt(library, tmp_path):
    contract, result = repair(library, tmp_path)
    row = Catalog(library).describe(contract['task_id'])
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'updated.zip')
    with zipfile.ZipFile(built['zip']) as z:
        assert z.read('repo/' + row['approval_receipt']) == (library / row['approval_receipt']).read_bytes()
        manifest = json.loads(z.read('PACKET-MANIFEST.json'))
        assert manifest['generators'][contract['task_id']]['approved'] is True


def test_rule_drift_cannot_be_approved_from_old_review(library, tmp_path):
    contract, result = repair(library, tmp_path)
    path = library / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        if row['task_id'] == contract['task_id']:
            row['program_solution'] = '(different-unreviewed-rule g)'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    again = approve_reviews(Catalog(library), library / 'REVIEW', all_integrated=True)
    assert again['safety_reviews_recorded'] == 0
    assert 'missing_or_changed_rule_binding' in {r['reason'] for r in again['skipped']}
    assert not Catalog(library).describe(contract['task_id'])['approved']


def test_existing_semantic_veto_is_not_erased_by_backfill(library, tmp_path):
    contract, result = repair(library, tmp_path)
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        if row['id'] == contract['task_id']:
            row.update(semantic_veto=True, veto_reason='later adversarial counterexample')
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    again = approve_reviews(Catalog(library), library / 'REVIEW', all_integrated=True)
    row = Catalog(library).describe(contract['task_id'])
    assert row['train_safety'] == 'reviewed_safe' and not row['approved']
    assert row['veto_reason'] == 'later adversarial counterexample'


def test_complete_unchanged_generator_review_can_approve(library, tmp_path):
    contract, _ = _return(library, tmp_path)
    packet = tmp_path / 'packet-0'
    (packet / f"repo/generators/{contract['task_id']}/notes.md").write_text(
        'Reviewed the existing generator; no source repair needed.\n')
    (tmp_path / 'review_response_0.zip').unlink()
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    collect_full_returns(library / 'REVIEW', tmp_path)
    before = Catalog(library).describe(contract['task_id'])['generator_sha256']
    result = integrate_full_candidate(Catalog(library), library / 'REVIEW',
              contract['assignment_id'], 1, {'tests_notes'}, reviewer_reported=True)
    row = Catalog(library).describe(contract['task_id'])
    assert row['approved'] and row['generator_sha256'] == before
    assert result['approval']['safety_reviews_recorded'] == 1


def test_three_target_unchanged_and_prototype_never_approve(library, tmp_path):
    from test_review_full_collect import _return
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3,
                          target_outcomes=['repaired', 'unchanged', 'prototype'])
    collect_full_returns(library/'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                      1, {'generator'}, reviewer_reported=True)
    assert [r['task_id'] for r in result['approval']['approved']] == [contract['task_id']]
    skipped = {r['task_id']: r['reason'] for r in result['approval']['skipped']}
    for target in contract['repair_targets'][1:]:
        assert skipped[target['task_id']] == 'target_not_repaired'
