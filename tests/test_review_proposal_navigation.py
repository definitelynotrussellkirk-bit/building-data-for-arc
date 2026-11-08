import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

from arcpuzzles.review_full_inbox import _request_sections


def _proposal(owner, *, escape=False):
    request_id = 'tool:portable-probe'
    base = 'shared/tools/proposals/' + hashlib.sha256(request_id.encode()).hexdigest()[:16]
    rows = []
    for name in ['checks/probe contract.py', 'checks/test_probe.py']:
        relative = f'{base}/{name}'
        path = owner / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# passive proposal\n')
        rows.append({'path': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'bytes': path.stat().st_size, 'source_member': name})
    if escape:
        rows[0]['path'] = 'README.md'
        (owner / 'README.md').write_text('# outside proposal scope\n')
        rows[0]['sha256'] = hashlib.sha256((owner / 'README.md').read_bytes()).hexdigest()
    manifest = owner / base / 'manifest.json'
    manifest.write_text(json.dumps({'schema': 'arcpuzzles-tool-proposal-assets-v1',
        'request_id': request_id, 'runtime_approved': False, 'files': rows}))
    request = {'request_id': request_id, 'status': 'accepted', 'text': 'Improve portable probes',
        'reason': 'Retain for review.', 'assets_manifest': {'path': f'{base}/manifest.json',
            'sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()},
        'owner_tool_review': {'status': 'not_selected', 'runtime_qualified': False}}
    return request, rows, manifest


def test_inbox_links_passive_authored_files_and_preserves_request(tmp_path):
    owner = tmp_path / 'owner'
    row, assets, manifest = _proposal(owner)
    before = json.dumps(row, sort_keys=True), manifest.read_bytes()
    out = owner / 'var/review/full-inbox'
    page = _request_sections(owner, out, [row])
    for item in assets:
        href = quote(os.path.relpath(owner / item['path'], out), safe='/')
        assert f'href="{href}"' in page
        assert item['sha256'][:12] in page
    assert 'Retained files (2)' in page
    assert 'hashes checked for this view' in page
    assert 'passive' in page and 'not_selected' in page
    assert before == (json.dumps(row, sort_keys=True), manifest.read_bytes())


def test_changed_proposal_is_visible_but_not_linked_as_verified(tmp_path):
    row, assets, _ = _proposal(tmp_path)
    (tmp_path / assets[0]['path']).write_text('changed\n')
    page = _request_sections(tmp_path, tmp_path / 'out', [row])
    assert 'Retained file links unavailable' in page
    assert 'Missing or changed proposal asset' in page
    assert 'hashes checked for this view' not in page
    assert 'href="../' + quote(assets[0]['path'], safe='/') + '"' not in page


def test_proposal_manifest_cannot_link_outside_its_request(tmp_path):
    row, _, _ = _proposal(tmp_path, escape=True)
    page = _request_sections(tmp_path, tmp_path / 'out', [row])
    assert 'Retained file links unavailable' in page
    assert 'Proposal asset outside its request' in page
    assert 'href="../README.md"' not in page


def test_selected_source_links_distinguish_current_and_historical_bytes(tmp_path):
    source = tmp_path / 'src/tool.py'
    source.parent.mkdir()
    source.write_text('VERSION = 1\n')
    recorded = hashlib.sha256(source.read_bytes()).hexdigest()
    row = {'request_id': 'tool:selected', 'status': 'implemented', 'text': 'Selected tool',
           'owner_tool_review': {'selected_source': 'src/tool.py', 'selected_sha256': recorded,
                                 'status': 'implemented', 'runtime_qualified': False}}
    page = _request_sections(tmp_path, tmp_path / 'out', [row])
    assert 'href="../src/tool.py"' in page
    assert 'matches recorded SHA-256' in page
    assert 'do not rerun the recorded tests' in page
    source.write_text('VERSION = 2\n')
    page = _request_sections(tmp_path, tmp_path / 'out', [row])
    assert 'changed since recorded review' in page
    assert 'matches recorded SHA-256' not in page
    assert recorded in page


def test_source_mappings_and_review_files_are_portable(tmp_path):
    owner = tmp_path / 'relocated'
    for name in ['src/tool.py', 'tests/test_tool.py', 'shared/tools/README.md']:
        path = owner / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# retained source\n')
    row = {'request_id': 'tool:mapping', 'status': 'implemented', 'text': 'Mapped sources',
        'owner_tool_review': {'selected_sources': {
            'src/tool.py': hashlib.sha256((owner / 'src/tool.py').read_bytes()).hexdigest()},
            'tests': ['tests/test_tool.py'], 'index': 'shared/tools/README.md',
            'verification_receipt': 'var/missing.json'}}
    out = owner / 'var/review/full-inbox'
    page = _request_sections(owner, out, [row])
    for name in ['src/tool.py', 'tests/test_tool.py', 'shared/tools/README.md']:
        assert f'href="../../../{name}"' in page
    assert 'Unavailable evidence: var/missing.json' in page
    assert str(owner) not in page


def test_unavailable_or_unbound_selected_source_is_not_claimed_verified(tmp_path):
    (tmp_path / 'tool.py').write_text('# current\n')
    row = {'request_id': 'tool:unsafe', 'status': 'accepted', 'text': 'Unbound sources',
        'owner_tool_review': {'selected_source': {'tool.py': None, '../outside.py': 'a' * 64,
                                                  'javascript:alert(1)': 'a' * 64}}}
    page = _request_sections(tmp_path, tmp_path / 'out', [row])
    assert 'no valid recorded SHA-256' in page
    assert 'source unavailable' in page
    assert 'href="javascript:' not in page
    assert 'href="../../outside.py"' not in page
    assert 'matches recorded SHA-256' not in page
