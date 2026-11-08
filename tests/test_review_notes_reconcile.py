"""Only disjoint additions to an empty notes template may reconcile automatically."""
import hashlib
import pytest

from arcpuzzles import review_full_integrate as engine

PATH = 'generators/78a914ac492e/notes.md'
TITLE = '# Working notes: 78a914ac492e\n\n'
IMPORTED = 'Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.\n'
BASE = (TITLE + 'Record design decisions, hypotheses, review findings, and unresolved questions here.\n' + IMPORTED).encode()
CURRENT = (TITLE + '## Current validator contract\n\nKeep actual current repair.\n\n' + IMPORTED).encode()
PROPOSED = (TITLE + IMPORTED + '\n## Parametric decision\n\nKeep incoming parameter work.\n').encode()


def test_disjoint_sections_preserve_current_bytes_and_bind_four_hashes():
    merged, receipt = engine._merge_placeholder_notes(PATH, BASE, PROPOSED, CURRENT)
    assert merged.startswith(CURRENT)
    assert merged.count(b'## Current validator contract') == 1
    assert merged.count(b'## Parametric decision') == 1
    assert merged.count(IMPORTED.encode()) == 1
    for name, value in [('base', BASE), ('current', CURRENT), ('proposed', PROPOSED), ('merged', merged)]:
        assert receipt[name + '_sha256'] == hashlib.sha256(value).hexdigest()


@pytest.mark.parametrize('path,base,proposed,current', [
    (PATH.replace('notes.md', 'generator.py'), BASE, PROPOSED, CURRENT),
    (PATH, BASE + b'Important prior decision\n', PROPOSED, CURRENT),
    (PATH, BASE, PROPOSED.replace(b'Parametric decision', b'Current validator contract'), CURRENT),
    (PATH, BASE, PROPOSED.replace(b'Parametric decision', b'CURRENT VALIDATOR CONTRACT'), CURRENT),
    (PATH, BASE, PROPOSED.replace(IMPORTED.encode(), b'Changed unrelated preamble\n'), CURRENT),
    (PATH, BASE, PROPOSED + b'\n## Parametric decision\nDuplicate\n', CURRENT),
])
def test_nontrivial_or_overlapping_collisions_still_require_rebase(path, base, proposed, current):
    with pytest.raises(ValueError):
        engine._merge_placeholder_notes(path, base, proposed, current)


def test_integration_preserves_live_notes_and_records_reconciliation(library, tmp_path):
    import json
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import collect_full_returns
    from test_review_full_collect import _return
    tid = 'aaaa00000001'
    substitute = lambda raw: raw.replace(b'78a914ac492e', tid.encode())
    path = library / f'generators/{tid}/notes.md'
    path.write_bytes(substitute(BASE))
    contract, _ = _return(library, tmp_path, repair_target_count=3)
    packet = tmp_path / 'packet-0'
    (packet / f'repo/generators/{tid}/notes.md').write_bytes(substitute(PROPOSED))
    record = json.loads((packet / 'RESULTS.json').read_text())
    row = next(r for r in record['repair_targets'] if r['task_id'] == tid)
    row.update(outcome='repaired', changed_components=['tests_notes'])
    (packet / 'RESULTS.json').write_text(json.dumps(record))
    returned = build_full_return(packet, tmp_path / 'review_response_notes.zip')
    path.write_bytes(substitute(CURRENT))
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    integrated = engine.integrate_full_candidate(Catalog(library), library / 'REVIEW',
        contract['assignment_id'], receipt['version'], {'tests_notes'}, reviewer_reported=True)
    target = next(r for r in integrated['targets'] if r['task_id'] == tid)
    from pathlib import Path
    evidence = json.loads(Path(target['evidence_path']).read_text())
    proof = evidence['source_reconciliations'][0]
    assert path.read_bytes().startswith(substitute(CURRENT))
    assert b'Keep incoming parameter work.' in path.read_bytes()
    assert proof['current_sha256'] == hashlib.sha256(substitute(CURRENT)).hexdigest()
    assert proof['merged_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert evidence['integrated_files'][f'generators/{tid}/notes.md'] == proof['merged_sha256']


def test_failed_reported_attempt_can_retry_without_mutating_prior_candidate(library, tmp_path):
    import json
    from pathlib import Path
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import collect_full_returns
    from test_review_full_collect import _return
    tid = 'aaaa00000001'
    substitute = lambda raw: raw.replace(b'78a914ac492e', tid.encode())
    path = library / f'generators/{tid}/notes.md'
    path.write_bytes(substitute(BASE))
    contract, _ = _return(library, tmp_path, repair_target_count=3)
    packet = tmp_path / 'packet-0'
    (packet / f'repo/generators/{tid}/notes.md').write_bytes(substitute(PROPOSED))
    results = json.loads((packet / 'RESULTS.json').read_text())
    row = next(r for r in results['repair_targets'] if r['task_id'] == tid)
    row.update(outcome='repaired', changed_components=['tests_notes'])
    (packet / 'RESULTS.json').write_text(json.dumps(results))
    returned = build_full_return(packet, tmp_path / 'review_response_retry.zip')
    collected = collect_full_returns(library / 'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r['zip_sha256'] == returned['zip_sha256'])
    # A concrete overlap blocks after the reported candidate has been created.
    path.write_bytes(substitute(PROPOSED).replace(b'Keep incoming parameter work.', b'Competing current decision.'))
    args = (Catalog(library), library / 'REVIEW', contract['assignment_id'], receipt['version'], {'tests_notes'})
    with pytest.raises(ValueError, match='collision'):
        engine.integrate_full_candidate(*args, reviewer_reported=True)
    prior = library / 'var/review/reported-candidates' / contract['assignment_id'] / f"{receipt['version']:04d}"
    hashes = {p.relative_to(prior): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in prior.rglob('*') if p.is_file()}
    # Owner resolves the actual conflicting current section; retry uses new staging.
    path.write_bytes(substitute(CURRENT))
    result = engine.integrate_full_candidate(*args, reviewer_reported=True)
    assert path.read_bytes().startswith(substitute(CURRENT))
    assert b'Keep incoming parameter work.' in path.read_bytes()
    assert hashes == {p.relative_to(prior): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in prior.rglob('*') if p.is_file()}
    evidence = json.loads(Path(next(r for r in result['targets'] if r['task_id'] == tid)['evidence_path']).read_text())
    new_receipt = Path(evidence['reported_acceptance_receipt'])
    assert new_receipt.parent != prior and new_receipt.parent.parent == prior.parent
    assert new_receipt.is_file()
    with pytest.raises(FileExistsError, match='integration evidence'):
        engine.integrate_full_candidate(*args, reviewer_reported=True)
