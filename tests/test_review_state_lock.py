"""Review-state operations must wait before reading or rewriting a locked owner."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys

import pytest

from arcpuzzles.review import _lock


def setup_question(library):
    p=library/'REVIEW/questions/q.json'
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps({'schema':'arcpuzzles-review-question-v1','id':'q',
        'version':1,'owner':'ARCpuzzles','text':'Explain the generator contract.'}))


WORKER = r'''
import json, os, sys
from pathlib import Path
from arcpuzzles.catalog import Catalog
from arcpuzzles.review import _lock
from arcpuzzles.review_full_inbox import build_full_inbox
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_notes import migrate_notes
from arcpuzzles.review_retention import compact_reviews
from arcpuzzles.review_solve_tracker import build_solve_tracker, verify_return_solve

operation, root, signal = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
catalog = Catalog(root)
if operation == 'nested':
    with _lock(root / 'REVIEW'):
        with _lock(root / 'REVIEW/../REVIEW'):
            (root / 'nested-done').write_text('nested lock succeeded')
    raise SystemExit(0)

# Observe real file I/O, without supplying substitute contents or results.
real_open = Path.open
observed = False
def observed_open(path, mode='r', *args, **kwargs):
    global observed
    handle = real_open(path, mode, *args, **kwargs)
    if not observed and path.name != '.lock' and path.is_relative_to(root):
        observed = True
        os.write(signal, b'io\n')
    return handle
Path.open = observed_open
os.write(signal, b'ready\n')
if operation == 'inbox':
    build_full_inbox(root / 'REVIEW', root / 'var/inbox')
elif operation in ('compact-preview', 'compact-apply'):
    compact_reviews(root, apply=operation.endswith('apply'))
elif operation in ('notes-preview', 'notes-apply'):
    migrate_notes(root, apply=operation.endswith('apply'))
elif operation == 'packet':
    build_full_packet(catalog, root / 'REVIEW', root / 'var/request.zip')
elif operation == 'solve-feed':
    build_solve_tracker(root / 'REVIEW', root / 'var/feed')
elif operation == 'solve-replay-preflight':
    try:
        verify_return_solve(root / 'REVIEW', 'no-such-return', 1)
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise AssertionError('missing return must not be scored')
else:
    raise AssertionError(operation)
os.write(signal, b'done\n')
'''


def worker(library, operation, fd):
    # Use this source tree in both the owner and ordinary relocated packet.
    import arcpuzzles.review
    env = dict(os.environ, PYTHONPATH=str(Path(arcpuzzles.review.__file__).parents[1]),
               PYTHONNOUSERSITE='1', CUDA_VISIBLE_DEVICES='')
    return subprocess.Popen([sys.executable, '-c', WORKER, operation, str(library), str(fd)],
        pass_fds=(fd,), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_same_thread_nested_review_lock_does_not_deadlock(library):
    read_fd, write_fd = os.pipe()
    proc = worker(library, 'nested', write_fd)
    os.close(write_fd)
    try:
        try:
            out, err = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            pytest.fail('same-thread nested lock deadlocked')
        assert proc.returncode == 0, (out, err)
        assert (library / 'nested-done').read_text() == 'nested lock succeeded'
    finally:
        if proc.poll() is None:
            proc.kill(); proc.communicate(timeout=3)
        os.close(read_fd)


def test_packet_native_lock_stays_outside_source_and_preserves_coordination(tmp_path):
    import fcntl
    packet = tmp_path / 'packet'; root = packet / 'repo/REVIEW'
    root.mkdir(parents=True); (packet / 'PACKET-MANIFEST.json').write_text('{}')
    runtime_lock = packet / '.review/library-review.lock'
    with _lock(root):
        assert not (root / '.lock').exists()
        assert runtime_lock.is_file()
        with runtime_lock.open('a') as second:
            with pytest.raises(BlockingIOError):
                fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with _lock(root):
            assert runtime_lock.is_file()
    with runtime_lock.open('a') as second:
        fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_native_packet_lock_does_not_break_delta_packaging(library, tmp_path):
    from test_review_full_return import _draw, _docs
    from arcpuzzles.review_full_draw import draw_audit
    from arcpuzzles.review_full_return import build_full_return
    packet = _draw(library, tmp_path); _docs(packet)
    audit = draw_audit(packet, bytes(32))
    (packet / 'AUDIT.md').write_text(''.join(f"## {r['task_id']}\nNo issue found\n" for r in audit['targets']))
    with _lock(packet / 'repo/REVIEW'):
        built = build_full_return(packet, tmp_path / 'lock-safe-return.zip')
        assert Path(built['zip']).is_file()
        assert not (packet / 'repo/REVIEW/.lock').exists()


@pytest.mark.parametrize('operation', ['inbox', 'compact-preview', 'compact-apply',
    'notes-preview', 'notes-apply', 'packet', 'solve-feed', 'solve-replay-preflight'])
def test_review_operation_waits_before_owner_io(library, operation):
    setup_question(library)
    tid = 'aaaa00000001'
    source = library / f'generators/{tid}/generator.py'
    index = library / f'generators/{tid}/evidence/review_index.json'
    index.parent.mkdir(parents=True)
    state = {'schema':'arcpuzzles-task-review-current-v1','task_id':tid,
        'current_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'notes_path':f'generators/{tid}/notes.md','decisions':[], 'audits':[]}
    index.write_text(json.dumps(state))
    read_fd, write_fd = os.pipe()
    proc = None
    try:
        with _lock(library / 'REVIEW'):
            proc = worker(library, operation, write_fd)
            os.close(write_fd); write_fd = None
            assert select.select([read_fd], [], [], 3)[0], 'worker did not start'
            pending = os.read(read_fd, 4096)
            assert pending == b'ready\n', (operation, pending)
            # A bounded observation window distinguishes waiting at the owner
            # lock from taking a stale snapshot then waiting only during writes.
            assert not select.select([read_fd], [], [], 0.25)[0], \
                'operation accessed owner state before acquiring its lock'
        out, err = proc.communicate(timeout=8)
        assert proc.returncode == 0, (operation, out, err)
        signals = os.read(read_fd, 4096)
        assert b'done\n' in signals
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill(); proc.communicate(timeout=3)
        if write_fd is not None: os.close(write_fd)
        os.close(read_fd)


def test_other_thread_cannot_reuse_review_lock(library):
    from threading import Event, Thread
    started, entered = Event(), Event()
    def attempt():
        started.set()
        with _lock(library / 'REVIEW'):
            entered.set()
    with _lock(library / 'REVIEW'):
        thread = Thread(target=attempt, daemon=True); thread.start()
        assert started.wait(3)
        assert not entered.wait(0.25)
    thread.join(timeout=3)
    assert not thread.is_alive() and entered.is_set()


def test_nested_exception_releases_outer_review_lock(library):
    # Run the nested case out of process, so a broken lock cannot hang pytest.
    code = r'''
import fcntl, sys
from pathlib import Path
from arcpuzzles.review import _lock
root=Path(sys.argv[1])/'REVIEW'
try:
    with _lock(root):
        with _lock(root):
            raise ValueError('expected failure')
except ValueError:
    pass
with (root/'.lock').open('a') as handle:
    fcntl.flock(handle, fcntl.LOCK_EX|fcntl.LOCK_NB)
    fcntl.flock(handle, fcntl.LOCK_UN)
'''
    import arcpuzzles.review
    env=dict(os.environ, PYTHONPATH=str(Path(arcpuzzles.review.__file__).parents[1]),
             CUDA_VISIBLE_DEVICES='')
    try:
        result=subprocess.run([sys.executable,'-c',code,str(library)],env=env,
                              capture_output=True,timeout=3)
    except subprocess.TimeoutExpired:
        pytest.fail('nested exception path deadlocked')
    assert result.returncode == 0, result.stderr


def test_forked_process_cannot_reuse_parent_review_lock(library):
    from multiprocessing import get_context
    ctx = get_context('fork')
    started, entered = ctx.Event(), ctx.Event()
    def attempt():
        started.set()
        with _lock(library / 'REVIEW'):
            entered.set()
    proc = None
    try:
        with _lock(library / 'REVIEW'):
            proc = ctx.Process(target=attempt); proc.start()
            assert started.wait(3)
            assert not entered.wait(0.25)
        proc.join(timeout=3)
        assert not proc.is_alive() and proc.exitcode == 0 and entered.is_set()
    finally:
        if proc is not None and proc.is_alive():
            proc.terminate(); proc.join(timeout=3)


def test_packet_refreshes_catalog_after_acquiring_owner_lock(library, tmp_path):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.review_full_packet import build_full_packet, packet_member
    import zipfile
    setup_question(library)
    cached = Catalog(library)
    path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['train_safety'] = 'unverified'
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    built = build_full_packet(cached, library / 'REVIEW', tmp_path / 'request.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(packet_member(archive, 'PACKET-MANIFEST.json'))
    assert manifest['generators']['aaaa00000001']['approved'] is False
    assert manifest['main_ids'] == ['aaaa00000001', 'aaaa00000002', 'aaaa00000003']


def test_compaction_cannot_retire_return_between_integration_and_approval(
        library, tmp_path, monkeypatch):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    import arcpuzzles.review_approval as approval
    from test_review_full_collect import _return
    contract, returned = _return(library, tmp_path, edit=True)
    received = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    real_approve = approval.approve_reviews
    read_fd, write_fd = os.pipe()
    children = []
    def competing_compaction_then_approve(*args, **kwargs):
        # Instrument the real approval boundary; the competitor performs real
        # compaction and all ordinary evidence/approval checks remain enabled.
        proc = worker(library, 'compact-apply', write_fd); children.append(proc)
        assert select.select([read_fd], [], [], 3)[0]
        assert b'ready\n' in os.read(read_fd, 4096)
        try:
            proc.communicate(timeout=0.3)
        except subprocess.TimeoutExpired:
            pass
        return real_approve(*args, **kwargs)
    monkeypatch.setattr(approval, 'approve_reviews', competing_compaction_then_approve)
    try:
        result = integrate_full_candidate(Catalog(library), library / 'REVIEW',
            contract['assignment_id'], 1, {'generator'}, reviewer_reported=True)
        assert result['approval']['safety_reviews_recorded'] == 1
        assert Catalog(library).describe(contract['task_id'])['approved'] is True
        assert len(children) == 1
        out, err = children[0].communicate(timeout=5)
        assert children[0].returncode == 0, (out, err)
        assert not Path(received['archive_path']).exists()
    finally:
        for proc in children:
            if proc.poll() is None:
                proc.kill(); proc.communicate(timeout=3)
        os.close(write_fd); os.close(read_fd)
