import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_return import build_full_return, _canonical_only_task
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_candidate import check_full_candidate
from arcpuzzles.review_full_integrate import integrate_full_candidate, stage_full_combination, record_full_disposition
from arcpuzzles.review_full_inbox import build_full_inbox
from test_review_full_collect import _return


def _make(library, tmp_path, seed, *, generator=False, rule=False, notes=False):
    q = library / "REVIEW/questions/q.json"
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_text(json.dumps({"schema": "arcpuzzles-review-question-v1", "id": "q",
                       "version": 1, "owner": "ARCpuzzles", "text": "Why?"}))
    wave_packet = tmp_path / "request-wave.zip"
    if not wave_packet.is_file():
        build_full_packet(Catalog(library), library / "REVIEW", wave_packet)
    packet = tmp_path / f"packet-{seed}"
    packet.mkdir()
    with zipfile.ZipFile(wave_packet) as archive:
        archive.extractall(packet)
    contract = draw_main(packet, seed.to_bytes(32, "big"))
    tid = contract["task_id"]
    for name in ("REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md"):
        (packet / name).write_text(name + "\n")
    (packet / "RESULTS.json").write_text(json.dumps({"completion_state": "complete"}))
    if generator:
        (packet / f"repo/generators/{tid}/generator.py").write_text(f"VERSION = 'new-{seed}'\n")
    if notes:
        (packet / f"repo/generators/{tid}/notes.md").write_text(f"Rationale {seed}\n")
    if rule:
        path = packet / "repo/shared/data/canonical/puzzles.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            if row["task_id"] == contract["generator"]["rule_task_id"]:
                row["program_solution"] = f"(rule-{seed} g)"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    returned = build_full_return(packet, tmp_path / f"review_response_{seed}.zip")
    collected = collect_full_returns(library / "REVIEW", tmp_path)
    receipt = next(r for r in collected["receipts"] if r.get("zip_sha256") == returned["zip_sha256"])
    checked = check_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"],
                                   receipt["version"], timeout=2)
    assert checked["paths"]
    checked["status"] = "passed"  # isolate merge mechanics from minimal fixture battery
    Path(checked["receipt_path"]).write_text(json.dumps(checked))
    return contract, receipt


def test_different_canonical_rows_integrate_without_clobber(library, tmp_path):
    path = library / "catalog/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        row["train_safety"] = "unverified"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    first, r1 = _make(library, tmp_path, 0, rule=True)
    second, r2 = _make(library, tmp_path, 1, rule=True)
    assert first["task_id"] != second["task_id"]
    integrate_full_candidate(Catalog(library), library / "REVIEW", first["assignment_id"], r1["version"], {"racket"})
    integrate_full_candidate(Catalog(library), library / "REVIEW", second["assignment_id"], r2["version"], {"racket"})
    canonical = [json.loads(line) for line in (library / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()]
    assert canonical[0]["program_solution"] == "(rule-0 g)"
    assert canonical[1]["program_solution"] == "(rule-1 g)"
    assert canonical[2]["program_solution"] == "(rule! g)"


def test_two_row_authority_requires_bound_rows_only(library):
    path = library / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    original = path.read_bytes()
    rows.append(dict(rows[2]))
    rows[2]["program_solution"] = "(new g)"
    rows[3]["program_solution"] = "(new g)"
    changed = "".join(json.dumps(row) + "\n" for row in rows).encode()
    _canonical_only_task(original + json.dumps(json.loads(original.splitlines()[2])).encode() + b"\n",
                         changed, "aaaa00000003")
    rows[0]["program_solution"] = "(bad g)"
    with pytest.raises(ValueError, match="unrelated"):
        _canonical_only_task(original + json.dumps(json.loads(original.splitlines()[2])).encode() + b"\n",
                             "".join(json.dumps(row) + "\n" for row in rows).encode(), "aaaa00000003")


def test_same_generator_collision_requires_combined_check(library, tmp_path):
    first, r1 = _make(library, tmp_path, 0, generator=True)
    second, r2 = _make(library, tmp_path, 3, generator=True)
    staged = stage_full_combination(library / "REVIEW", [(first["assignment_id"], r1["version"]),
                                                           (second["assignment_id"], r2["version"])],
                                    tmp_path / "combined")
    assert staged["status"] == "conflict"
    assert len(staged["sources"]) == 2
    integrate_full_candidate(Catalog(library), library / "REVIEW", first["assignment_id"], r1["version"], {"generator"})
    with pytest.raises(ValueError, match="drift|rebase|collision"):
        integrate_full_candidate(Catalog(library), library / "REVIEW", second["assignment_id"], r2["version"], {"generator"})


def test_component_selection_preserves_notes_and_catalog_labels(library, tmp_path):
    before_catalog = (library / "catalog/puzzles.jsonl").read_bytes()
    contract, receipt = _make(library, tmp_path, 0, generator=True, notes=True)
    result = integrate_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"],
                                      receipt["version"], {"tests_notes"})
    assert result["status"] == "integrated"
    assert (library / f"generators/{contract['task_id']}/notes.md").read_text().startswith("Rationale")
    assert (library / f"generators/{contract['task_id']}/generator.py").read_text().startswith("VERSION = '1")
    assert (library / "catalog/puzzles.jsonl").read_bytes() == before_catalog
    record_full_disposition(library / "REVIEW", contract["assignment_id"], receipt["version"],
                            "audit", "needs_evidence", "Need a concrete adversarial input")
    inbox = build_full_inbox(library / "REVIEW", tmp_path / "inbox")
    data = json.loads(Path(inbox["json"]).read_text())
    row = data["generators"][contract["task_id"]][0]
    assert any(item["reason"] == "Need a concrete adversarial input" for item in row["dispositions"])


def test_no_change_return_can_be_explicitly_recorded(library, tmp_path):
    contract, _ = _return(library, tmp_path, state="blocked")
    collect_full_returns(library / "REVIEW", tmp_path)
    result = integrate_full_candidate(Catalog(library), library / "REVIEW", contract["assignment_id"], 1, set())
    assert result["status"] == "no_changes"
    assert Path(result["evidence_path"]).is_file()


def test_reported_acceptance_keeps_verification_honest_and_copies_only_delta(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True)
    collect_full_returns(library / 'REVIEW', tmp_path)
    before = (library / 'catalog/puzzles.jsonl').read_bytes()
    with pytest.raises(ValueError, match='needs a check'):
        integrate_full_candidate(Catalog(library), library / 'REVIEW', contract['assignment_id'], 1, {'generator'})
    result = integrate_full_candidate(Catalog(library), library / 'REVIEW', contract['assignment_id'], 1,
                                      {'generator'}, reviewer_reported=True)
    evidence = json.loads(Path(result['evidence_path']).read_text())
    assert evidence['verification_status'] == 'reviewer_reported'
    assert evidence['check_receipt'] is None
    report = json.loads(Path(evidence['reported_acceptance_receipt']).read_text())
    assert report['checks'] == [] and report['training_admitted'] is False
    assert not (library / 'var/review/full-checks').exists()
    assert not (Path(report['candidate_path']) / 'repo/shared').exists()
    assert (library / 'catalog/puzzles.jsonl').read_bytes() != before
    assert Catalog(library).describe(contract['task_id'])['approved'] is True
    assert result['approval']['safety_reviews_recorded'] == 1
    assert (library / f"generators/{contract['task_id']}/generator.py").read_text() == "VERSION = '2.0'\n"
    assert Catalog(library).describe(contract['task_id'])['version'] == '2.0'


def test_reported_acceptance_does_not_overwrite_a_collision(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True)
    collect_full_returns(library / 'REVIEW', tmp_path)
    generator = library / f"generators/{contract['task_id']}/generator.py"
    generator.write_text("VERSION = 'someone-elses-change'\n")
    with pytest.raises(ValueError, match='drift|collision'):
        integrate_full_candidate(Catalog(library), library / 'REVIEW', contract['assignment_id'], 1,
                                 {'generator'}, reviewer_reported=True)
    assert generator.read_text() == "VERSION = 'someone-elses-change'\n"


def test_three_repaired_targets_integrate_with_separate_evidence(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    collect_full_returns(library/'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                      1, {'generator'}, reviewer_reported=True)
    assert len(result['targets']) == 3
    assert result['approval']['safety_reviews_recorded'] == 3
    for target in contract['repair_targets']:
        tid = target['task_id']
        evidence = json.loads((library/f"generators/{tid}/evidence/review-{contract['assignment_id']}-v0001.json").read_text())
        assert evidence['task_id'] == tid
        assert evidence['repair_outcome'] == 'repaired'
        assert evidence['components'] == ['generator']
        assert set(evidence['integrated_files']) == {f'generators/{tid}/generator.py'}


def test_three_target_mixed_outcomes_withhold_production_proposals(library, tmp_path):
    from arcpuzzles.review_full_inbox import _receipts, _incoming_task_index
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3,
                          target_outcomes=['repaired', 'prototype', 'blocked'])
    collect_full_returns(library/'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                      1, {'generator'}, reviewer_reported=True)
    assert result['approval']['safety_reviews_recorded'] == 1
    assert len(result['files']) == 1
    rows = _receipts(library/'REVIEW')
    assert len(rows) == 1
    assert len(rows[0]['repair_dispositions']) == 3
    for target, outcome in zip(contract['repair_targets'], ['repaired', 'prototype', 'blocked']):
        tid = target['task_id']
        current = Catalog(library).describe(tid)
        if outcome == 'repaired':
            assert current['generator_sha256'] != target['generator']['generator_sha256']
        else:
            assert current['generator_sha256'] == target['generator']['generator_sha256']
            assert rows[0]['repair_dispositions'][tid]['disposition_status'] == 'needs_evidence'
        index = _incoming_task_index(library/'REVIEW', tid)
        assert index['decisions'][0]['source_sha256'] == target['generator']['generator_sha256']


def test_three_target_source_drift_rolls_back_entire_selection(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    collect_full_returns(library/'REVIEW', tmp_path)
    second = contract['repair_targets'][1]
    (library/second['generator']['generator']).write_text("VERSION = 'owner-edit'\n")
    before = {r['task_id']: (library/r['generator']['generator']).read_bytes() for r in contract['repair_targets']}
    with pytest.raises(ValueError, match='drift|collision'):
        integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                 1, {'generator'}, reviewer_reported=True)
    for row in contract['repair_targets']:
        assert (library/row['generator']['generator']).read_bytes() == before[row['task_id']]
        assert not (library/f"generators/{row['task_id']}/evidence/review-{contract['assignment_id']}-v0001.json").exists()


def test_multi_rule_merge_preserves_unrelated_owner_edits():
    from arcpuzzles.review_full_integrate import _merge_rule
    def raw(*rows): return b''.join((json.dumps({'task_id': t, 'program_solution': v})+'\n').encode() for t,v in rows)
    baseline = raw(('a','old'), ('b','old'), ('c','old'))
    proposed = raw(('a','new'), ('b','new'), ('c','old'))
    current = raw(('a','old'), ('b','old'), ('c','owner'))
    merged = _merge_rule(baseline, proposed, current, {'a','b'})
    assert merged == raw(('a','new'), ('b','new'), ('c','owner'))


@pytest.mark.parametrize('outcomes', [None, ['repaired', 'prototype', 'blocked']])
def test_three_target_compaction_keeps_third_evidence_after_archive_removal(library, tmp_path, outcomes):
    import hashlib
    from arcpuzzles.review_retention import compact_reviews
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3, target_outcomes=outcomes)
    work = tmp_path/'packet-0'
    third = contract['repair_targets'][2]['task_id']
    evidence = work/'checks'/third/'probe.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"fixture": "third-target-retained"}\n')
    results = json.loads((work/'RESULTS.json').read_text())
    results['repair_targets'][2]['evidence_paths'] = [f'checks/{third}/probe.json']
    (work/'RESULTS.json').write_text(json.dumps(results))
    returned = tmp_path/'review_response_0.zip'
    returned.unlink()
    build_full_return(work, returned)
    collected = collect_full_returns(library/'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['validation_status'] == 'accepted')
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                      1, {'generator'}, reviewer_reported=True)
    assert result['approval']['safety_reviews_recorded'] == (1 if outcomes else 3)
    compact = compact_reviews(library, apply=True)
    assert compact['archives_deleted'] == 1
    assert not Path(receipt['archive_path']).exists()
    for row in contract['repair_targets']:
        tid = row['task_id']
        retained = json.loads((library/f"generators/{tid}/evidence/repair-{contract['assignment_id']}-v0001.json").read_text())
        assert retained['task_id'] == tid
        delta = retained['source_delta']
        if outcomes:
            assert hashlib.sha256((library/delta['path']).read_bytes()).hexdigest() == delta['sha256']
            assert set(delta['task_ids']) == {r['task_id'] for r in contract['repair_targets']}
        else:
            assert delta is None  # Accepted source is retained in its task home.
        assert retained['generator_contract'] == row['generator']
        if tid == third:
            assert len(retained['files']) == 1
            assert (library/retained['files'][0]['path']).read_bytes() == evidence.read_bytes()


def test_three_unchanged_targets_record_no_execution_or_approval(library, tmp_path):
    contract, _ = _return(library, tmp_path, repair_target_count=3)
    collect_full_returns(library/'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'], 1, set())
    assert result['approval']['safety_reviews_recorded'] == 0
    assert result['files'] == []
    for row in result['targets']:
        evidence = json.loads(Path(row['evidence_path']).read_text())
        assert evidence['verification_status'] == 'not_run'
        assert evidence['disposition'] == 'no_changes'


def test_three_target_integration_rechecks_truthful_components(library, tmp_path, monkeypatch):
    import copy
    import arcpuzzles.review_full_integrate as integration
    from arcpuzzles.review_targets import validate_target_outcomes
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    collect_full_returns(library/'REVIEW', tmp_path)
    def stale_report(assignment, results):
        rows = copy.deepcopy(validate_target_outcomes(assignment, results))
        rows[0]['changed_components'].append('racket')
        return rows
    monkeypatch.setattr(integration, 'validate_target_outcomes', stale_report)
    before = {r['task_id']: (library/r['generator']['generator']).read_bytes() for r in contract['repair_targets']}
    with pytest.raises(ValueError, match='components.*actual|actual.*components'):
        integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                 1, {'generator'}, reviewer_reported=True)
    for row in contract['repair_targets']:
        assert (library/row['generator']['generator']).read_bytes() == before[row['task_id']]


def test_three_target_generator_repair_rejects_changed_rule(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    collect_full_returns(library/'REVIEW', tmp_path)
    target = contract['repair_targets'][1]
    path = library/'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for row in rows:
        if row['task_id'] == target['generator']['rule_task_id']:
            row['program_solution'] = '(different-owner-rule g)'
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    before = {r['task_id']: (library/r['generator']['generator']).read_bytes() for r in contract['repair_targets']}
    with pytest.raises(ValueError, match='rule.*drift|authority.*drift'):
        integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                 1, {'generator'}, reviewer_reported=True)
    for row in contract['repair_targets']:
        assert (library/row['generator']['generator']).read_bytes() == before[row['task_id']]
        assert not (library/f"generators/{row['task_id']}/evidence/review-{contract['assignment_id']}-v0001.json").exists()


def test_three_target_changed_rule_accepts_matching_assignment_baseline(library, tmp_path):
    contract, _ = _return(library, tmp_path, edit=True, repair_target_count=3)
    work = tmp_path/'packet-0'
    canonical = work/'repo/shared/data/canonical/puzzles.jsonl'
    target = contract['repair_targets'][1]
    rows = [json.loads(line) for line in canonical.read_text().splitlines()]
    for row in rows:
        if row['task_id'] == target['generator']['rule_task_id']:
            row['program_solution'] = '(reviewed-rule-change g)'
    canonical.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    results = json.loads((work/'RESULTS.json').read_text())
    results['repair_targets'][1]['changed_components'].append('racket')
    (work/'RESULTS.json').write_text(json.dumps(results))
    returned = tmp_path/'review_response_0.zip'
    returned.unlink()
    build_full_return(work, returned)
    collect_full_returns(library/'REVIEW', tmp_path)
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', contract['assignment_id'],
                                      1, {'generator', 'racket'}, reviewer_reported=True)
    assert result['approval']['safety_reviews_recorded'] == 3
    updated = Catalog(library).describe(target['task_id'])
    assert updated['rule_hash'] != target['generator']['rule_hash']
    assert updated['approved'] is True
