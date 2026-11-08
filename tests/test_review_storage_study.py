import hashlib
import io
import json
import zipfile

import pytest

from arcpuzzles import review_evidence_bundle as bundles


def observation(stage='before_extract', model='Astra Pro', available=100):
    return dict(schema='arcpuzzles-storage-observation-v1', study_id='model-storage-20261023',
                stage=stage, model=model, freshness='fresh', observed_utc='2026-10-23T13:00:00+00:00',
                archive=dict(sha256='a' * 64, bytes=60000000), mount_namespace='mnt:[1]',
                filesystems=[dict(path='/', device_id=1, total_bytes=1000, free_bytes=available,
                                  available_bytes=available, total_inodes=1000, free_inodes=50,
                                  available_inodes=50)], owned_trees=[])


def zipped(raw, *, bundled=False):
    payload = {'checks/storage-observations.jsonl': raw}
    if bundled:
        payload = bundles.pack(payload)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, value in payload.items():
            archive.writestr(name, value)
    stream.seek(0)
    return zipfile.ZipFile(stream)


@pytest.mark.parametrize('bundled', [False, True])
def test_imports_small_plain_or_bundled_observations_without_executing(tmp_path, bundled):
    from arcpuzzles.review_storage_study import retain_observations
    rows = [observation(), observation('after_extract', available=80)]
    raw = b'\n'.join(json.dumps(row).encode() for row in rows) + b'\n'
    with zipped(raw, bundled=bundled) as archive:
        result = retain_observations(tmp_path, archive, return_sha='b' * 64, packet_sha='a' * 64)
    assert result['status'] == 'recorded'
    state = json.loads((tmp_path / 'storage-study.json').read_text())
    assert len(state['returns']) == 1
    assert state['returns'][0]['observations_sha256'] == hashlib.sha256(raw).hexdigest()
    assert state['returns'][0]['missing_stages'] == ['after_setup', 'before_package']
    assert state['returns'][0]['deltas'][0]['available_bytes_change'] == -20
    assert state['startup_by_model'][0]['model'] == 'Astra Pro'


def test_wrong_archive_or_invalid_counters_cannot_enter_comparison(tmp_path):
    from arcpuzzles.review_storage_study import retain_observations
    bad = observation()
    bad['filesystems'][0]['available_inodes'] = False
    for row, expected in [(observation(), 'c' * 64), (bad, 'a' * 64)]:
        with zipped(json.dumps(row).encode()) as archive:
            result = retain_observations(tmp_path, archive, return_sha='b' * 64, packet_sha=expected)
        assert result['status'] == 'invalid'
    assert not (tmp_path / 'storage-study.json').exists()


def test_does_not_compare_across_mount_namespaces_and_deduplicates_return(tmp_path):
    from arcpuzzles.review_storage_study import retain_observations
    after = observation('after_extract')
    after['mount_namespace'] = 'mnt:[2]'
    raw = '\n'.join(json.dumps(row) for row in [observation(), after]).encode()
    for _ in range(2):
        with zipped(raw) as archive:
            retain_observations(tmp_path, archive, return_sha='b' * 64, packet_sha='a' * 64)
    state = json.loads((tmp_path / 'storage-study.json').read_text())
    assert len(state['returns']) == 1
    assert state['returns'][0]['deltas'] == []


def test_absent_observations_are_optional_and_create_no_state(tmp_path):
    from arcpuzzles.review_storage_study import retain_observations
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        archive.writestr('REVIEW.md', 'old packet')
    stream.seek(0)
    with zipfile.ZipFile(stream) as archive:
        assert retain_observations(tmp_path, archive, return_sha='b' * 64, packet_sha='a' * 64) is None
    assert not (tmp_path / 'storage-study.json').exists()


def test_study_manifest_expires_and_collection_is_bounded(tmp_path):
    from arcpuzzles.review_storage_study import study_policy, retain_observations
    assert study_policy(tmp_path, today='2026-10-30') is None
    assert study_policy(tmp_path, today='2026-10-23')['max_returns'] == 16
    for i in range(17):
        row = observation()
        row['observed_utc'] = f'2026-10-23T13:00:{i:02d}+00:00'
        with zipped(json.dumps(row).encode()) as archive:
            result = retain_observations(tmp_path, archive, return_sha=f'{i:064x}', packet_sha='a' * 64)
    assert result['status'] == 'study_full'
    assert study_policy(tmp_path, today='2026-10-23') is None
    assert len(json.loads((tmp_path / 'storage-study.json').read_text())['returns']) == 16


def test_supplement_cannot_count_same_observations_as_an_independent_chat(tmp_path):
    from arcpuzzles.review_storage_study import retain_observations
    raw = json.dumps(observation()).encode()
    for digest in ['b' * 64, 'c' * 64]:
        with zipped(raw) as archive:
            result = retain_observations(tmp_path, archive, return_sha=digest, packet_sha='a' * 64)
    assert result['status'] == 'duplicate_observations'
    assert len(json.loads((tmp_path / 'storage-study.json').read_text())['returns']) == 1
