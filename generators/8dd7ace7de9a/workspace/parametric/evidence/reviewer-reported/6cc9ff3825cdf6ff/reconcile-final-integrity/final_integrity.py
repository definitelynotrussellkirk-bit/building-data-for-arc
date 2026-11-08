from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUTER = Path('/mnt/data/arc_reconcile_160312')
BASE = OUTER / 'input/WORK'
CUR = OUTER / 'workspace/WORK'
TASK_REL = Path('repo/generators/8dd7ace7de9a')
EXPECTED_ARCHIVE = '99f34421d11b2a1b49d8e8ac304f945b0435e64b0cd0be8d03080cb4408de4c1'
EXPECTED_BEFORE = '2eea8b924e39232fedb437de952aa7e283a12f9fe3d532ea4a3791e9c8f0b2bb'
EXPECTED_AFTER = '5989a1f783b99c801dfaca05ae5d36bd777497bd7a1da985f53d7f742940cbf9'
EXPECTED_PROTOTYPE = 'f9938f0a8cbbecc3d8a28fa47b8f3b361fa85ed09ac75d2aa5e7a6cf2d7d6d67'
EXPECTED_PARAMETRIC_TEST = 'bd1525adb077941279a861925492260f83225ff425a18e2114bb7d642eea8489'
EXPECTED_PARAMETRIC_README = 'b9138fa777a6e6042802c742c3abaaf9244978ddb6aee353829c8466460e5b74'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root: Path):
    for path in root.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts and '.pytest_cache' not in path.parts:
            yield path.relative_to(root), path

archive = OUTER.parent / 'SEND-THIS-ARCpuzzles-review(20261023-160312).zip'
# The uploaded archive is under /mnt/data, one level above OUTER.
archive = Path('/mnt/data/SEND-THIS-ARCpuzzles-review(20261023-160312).zip')
assert sha(archive) == EXPECTED_ARCHIVE
assert sha(BASE / TASK_REL / 'generator.py') == EXPECTED_BEFORE
assert sha(CUR / TASK_REL / 'generator.py') == EXPECTED_AFTER
assert sha(CUR / TASK_REL / 'workspace/parametric/prototype.py') == EXPECTED_PROTOTYPE
assert sha(CUR / TASK_REL / 'tests/test_parametric_prototype.py') == EXPECTED_PARAMETRIC_TEST
assert sha(CUR / TASK_REL / 'workspace/parametric/README.md') == EXPECTED_PARAMETRIC_README

base_repo = {rel: sha(path) for rel, path in files(BASE / 'repo') if not rel.is_relative_to(Path('generators/8dd7ace7de9a'))}
cur_repo = {rel: sha(path) for rel, path in files(CUR / 'repo') if not rel.is_relative_to(Path('generators/8dd7ace7de9a'))}
changed_outside = sorted(str(rel) for rel in set(base_repo) | set(cur_repo) if base_repo.get(rel) != cur_repo.get(rel))
assert changed_outside == [], changed_outside

for required in (
    CUR / 'REVIEW.md',
    CUR / 'FEEDBACK_TO_CODEX.md',
    CUR / 'RESULTS.json',
    CUR / TASK_REL / 'workspace/parametric/prototype.py',
    CUR / TASK_REL / 'workspace/parametric/README.md',
    CUR / TASK_REL / 'tests/test_parametric_prototype.py',
    CUR / 'checks/reconcile-final-integrity/self-review.md',
):
    assert required.is_file(), required

results = json.loads((CUR / 'RESULTS.json').read_text())
assert results['completion_state'] == 'complete'
assert results['remaining_failures'] == []
assert len(results['supplementary_tickets']) == 2
assert {row['ticket_id'] for row in results['supplementary_tickets']} == {
    'ticket-8e6b8f00d3ad9b05', 'ticket-f8f970166f6fe635'
}
assert all(row['status'] == 'completed' for row in results['supplementary_tickets'])
assert not (CUR / 'AUDIT.md').exists()

final_test_log = (CUR / 'checks/reconcile-final-tests-v2/task-tests-final.log').read_text()
assert '42 passed in 21.57s' in final_test_log
assert (CUR / 'checks/reconcile-final-tests-v2/task-tests-final.exit').read_text().strip() == '0'

for setting, public_id in (
    ('full-grid', '495944c8b1fb992c5737e70871a90a679b074488c0f1fdb885e058c642fd872b'),
    ('tile-only', 'b39c58a59e381d6daf461b74bcab9d2ee30be71d48ae615e06accc9ee0466bad'),
):
    public = CUR / f'checks/parametric/output-extent/{setting}/public/{public_id}.json'
    assert sha(public) == public_id

storage = CUR / 'checks/storage-observations.jsonl'
assert storage.is_file()
stages = [json.loads(line)['stage'] for line in storage.read_text().splitlines() if line.strip()]
assert {'after_extract', 'after_setup', 'before_package'} <= set(stages)

report = {
    'schema': '8dd7ace7de9a-final-integrity-v1',
    'original_archive_sha256': EXPECTED_ARCHIVE,
    'baseline_generator_sha256': EXPECTED_BEFORE,
    'final_generator_sha256': EXPECTED_AFTER,
    'parametric_prototype_sha256': EXPECTED_PROTOTYPE,
    'parametric_test_sha256': EXPECTED_PARAMETRIC_TEST,
    'parametric_readme_sha256': EXPECTED_PARAMETRIC_README,
    'changed_repo_files_outside_selected_task': changed_outside,
    'results_complete': True,
    'final_task_tests': '42 passed in 21.57s',
    'supplementary_ticket_count': 2,
    'public_content_ids_exact': True,
    'audit_file_absent_without_new_peer_finding': True,
    'storage_stages_present': stages,
}
Path(__file__).with_name('result.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
