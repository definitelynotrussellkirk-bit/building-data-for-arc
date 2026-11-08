"""Synthetic compatibility observations must stay passive, without hiding bad indexes."""
import json
import pytest
from arcpuzzles.review_retention import _compressed_dependencies, _verify_compressed_dependencies


def receipt():
    return {'schema': 'review-large-evidence-v1', 'status': 'native_retention_verified',
            'native_reader': 'arcpuzzles.review_retention._compressed_dependencies + _verify_compressed_dependencies',
            'synthetic_archives': 1, 'selected_manifest_and_payload_members': 2,
            'compressed_and_original_hashes_verified': True, 'tool_sha256': 'a' * 64,
            'scope': 'Synthetic compatibility only; temporary fixture removed.'}


def test_synthetic_observation_is_retained_without_creating_verified_payloads():
    name='checks/compression/native_compat.json';raw=json.dumps(receipt()).encode();files={name:raw}
    selected, entries=_compressed_dependencies({name},set(files),files.__getitem__)
    assert selected=={name} and entries==[]
    assert files[name]==raw


@pytest.mark.parametrize('change', [
    {'files': None}, {'entries': []}, {'compressed_path': 'checks/hidden.gz'},
    {'synthetic_archives': True}, {'selected_manifest_and_payload_members': 0},
    {'tool_sha256': 'bad'}, {'native_reader': 'an unrelated reader'},
    {'scope': ''},
])
def test_receipt_shape_does_not_bypass_malformed_index_validation(change):
    data=receipt();data.update(change);files={'checks/index.json':json.dumps(data).encode()}
    with pytest.raises(ValueError,match='Compressed evidence'):
        _compressed_dependencies(set(files),set(files),files.__getitem__)


def test_reported_compatibility_success_cannot_mask_corrupt_real_evidence():
    import gzip,hashlib
    raw=b'actual failure';compressed=gzip.compress(raw,mtime=0)
    files={'checks/compat.json':json.dumps(receipt()).encode(), 'checks/data.gz':b'corrupt'}
    files['checks/index.json']=json.dumps({'schema':'review-large-evidence-v1','compression':'gzip',
        'count':1,'original_bytes':len(raw),'compressed_bytes':len(compressed),'files':[{
            'original_path':'checks/data.txt','compressed_path':'checks/data.gz',
            'original_bytes':len(raw),'compressed_bytes':len(compressed),
            'original_sha256':hashlib.sha256(raw).hexdigest(),
            'compressed_sha256':hashlib.sha256(compressed).hexdigest()}]}).encode()
    _,entries=_compressed_dependencies({'checks/compat.json','checks/index.json'},set(files),files.__getitem__)
    assert len(entries)==1
    with pytest.raises(ValueError,match='Compressed evidence'):
        _verify_compressed_dependencies(entries,files.__getitem__)
