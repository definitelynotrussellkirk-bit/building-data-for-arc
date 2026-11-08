"""A mislabeled observer receipt cannot substitute for a real compression index."""
import gzip
import hashlib
import json
import pytest
from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies


def evidence():
    raw = b'original failure evidence'
    zipped = gzip.compress(raw, mtime=0)
    index = 'checks/compressed/archives.json'
    payload = 'checks/compressed/failures.tar.gz'
    receipt = 'checks/compressed/native-retention-verification.json'
    row = {'path': 'failures.tar', 'compressed_path': 'failures.tar.gz',
           'raw_size': len(raw), 'raw_sha256': hashlib.sha256(raw).hexdigest(),
           'compressed_size': len(zipped), 'compressed_sha256': hashlib.sha256(zipped).hexdigest()}
    observed = {'schema': 'arcpuzzles-evidence-gzip-v1', 'status': 'passed',
                'native_reader_verified_archives': 1, 'expanded_members': [index, payload]}
    files = {index: json.dumps({'schema': 'arcpuzzles-evidence-gzip-v1', 'files': [row]}).encode(),
             payload: zipped, receipt: json.dumps(observed).encode()}
    return files, receipt, index, payload


def test_observation_receipt_requires_and_retains_real_index_and_payload():
    files, receipt, index, payload = evidence()
    expanded, entries = _compressed_dependencies({receipt}, set(files), files.__getitem__)
    assert expanded == set(files) and len(entries) == 1
    _verify_compressed_dependencies(entries, files.__getitem__)


def test_reported_pass_does_not_override_corrupt_payload():
    files, receipt, index, payload = evidence()
    _, entries = _compressed_dependencies({receipt}, set(files), files.__getitem__)
    files[payload] = b'corrupt'
    with pytest.raises(ValueError, match='Compressed evidence'):
        _verify_compressed_dependencies(entries, files.__getitem__)


@pytest.mark.parametrize('change', [
    {'native_reader_verified_archives': True},
    {'native_reader_verified_archives': 2},
    {'expanded_members': ['checks/missing.json', 'checks/compressed/failures.tar.gz']},
    {'expanded_members': ['checks/../outside.json']},
    {'expanded_members': ['checks/compressed/native-retention-verification.json']},
    {'expanded_members': ['checks/compressed/archives.json', 'checks/compressed/failures.tar.gz', 'checks/extra.txt']},
])
def test_malformed_observation_receipts_still_block_retention(change):
    files, receipt, _, _ = evidence()
    body = json.loads(files[receipt]);body.update(change);files[receipt] = json.dumps(body).encode()
    with pytest.raises(ValueError, match='Compressed evidence'):
        _compressed_dependencies({receipt}, set(files), files.__getitem__)
