"""Publish an owner-verified local packet without repeating its runtime checks."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from .catalog import Catalog
from .review import _lock
from .review_full_packet import RACKET_ARCHIVE_NAME, RACKET_ARCHIVE_SHA256
from .review_packet_publish_files import publish_files, sha, write_receipt
from .review_packet_verify import inspect_packet, _compare_owner
from .review_replay import _no_symlinks

HARNESS = ('review_packet_verify.py', 'review_packet_verify_probe.py',
           'review_packet_verify_process.py', 'review_packet_verify_landlock.py')


def _asset(base, row):
    base = base.resolve()
    path = Path(row['path'])
    if not path.is_absolute():path = base / path
    _no_symlinks(path);path = path.resolve()
    if not path.is_relative_to(base) or not path.is_file() or sha(path) != row['sha256']:
        raise ValueError('Missing or changed verification evidence hash: ' + str(path))
    return path


def _read_verification(path, checked):
    _no_symlinks(path);raw = path.read_bytes();report = json.loads(raw);manifest = checked['manifest']
    if (report.get('schema') != 'arcpuzzles-review-packet-verification-v1' or report.get('status') != 'passed'
            or report.get('packet_id') != checked['packet_id'] or report.get('packet', {}).get('sha256') != checked['zip_sha256']
            or (report.get('owner_sources') or {}).get('status') != 'passed' or report.get('training_admitted') is not False
            or report.get('archive_members_verified') != checked['member_count']):
        raise ValueError('Require a passed, source-bound owner verification for this exact ZIP')
    cold = report.get('cold_probe') or {};episode = cold.get('episode') or {};row = manifest.get('generators', {}).get(report.get('task_id'))
    demos, queries = report.get('demos'), report.get('queries')
    if (cold.get('status') != 'passed' or cold.get('packet_id') != checked['packet_id']
            or cold.get('source_reads_confined') is not True or cold.get('racket', {}).get('bundled_runtime_selected') is not True
            or report.get('task_id') not in manifest.get('main_ids', []) or not row
            or type(demos) is not int or type(queries) is not int or not 1 <= demos <= 16 or not 1 <= queries <= 16
            or episode.get('demonstrations') != demos or episode.get('queries') != queries
            or episode.get('reference_labels_replayed') != demos + queries
            or episode.get('generator_sha256') != row.get('generator_sha256') or episode.get('executed_rule_hash') != row.get('rule_hash')
            or manifest['files'].get('vendor/' + RACKET_ARCHIVE_NAME) != RACKET_ARCHIVE_SHA256):
        raise ValueError('Cold verification does not bind the selected source/reference/runtime')
    commands = report.get('commands', []) + cold.get('commands', [])
    if not report.get('commands') or not cold.get('commands'):raise ValueError('Verification command evidence is absent')
    for command in commands:
        if type(command.get('exit_code')) is not int or command['exit_code'] != 0 or command.get('failure') is not None:
            raise ValueError('Verification command failed or is incomplete')
        for stream in ['stdout', 'stderr']:_asset(path.parent, command[stream])
    harness = report.get('harness', [])
    if {item['path'] for item in harness} != {'harness/' + name for name in HARNESS} or len(harness) != len(HARNESS):
        raise ValueError('Verification harness inventory differs')
    for item in harness:
        observed = _asset(path.parent, item)
        if sha(observed) != sha(Path(__file__).with_name(observed.name)):
            raise ValueError('Verification used a different owner harness; run the current verifier')
    if path.read_bytes() != raw:raise ValueError('Verification receipt changed while checked')
    return report, hashlib.sha256(raw).hexdigest()


def _verification(path, checked):
    try:return _read_verification(path, checked)
    except (KeyError, TypeError, AttributeError, UnicodeError) as error:
        raise ValueError('Malformed verification receipt/evidence: ' + str(error)) from error


def _metadata(catalog, current, checked, proof, proof_path, proof_sha, stable, share):
    manifest = checked['manifest'];stats = Catalog(catalog.root).stats();now = datetime.now(timezone.utc).isoformat()
    try:
        git = subprocess.run(['git', '-C', str(catalog.root), 'rev-parse', '--verify', 'HEAD'], capture_output=True, text=True, timeout=10)
        commit = git.stdout.strip() if git.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):commit = None
    current.update(schema='arcpuzzles-full-packet-handoff-v1', status='ready', ready_to_send=True,
        current_artifact_verified=True, current_source_matches_packet=True, updated_at=now, updated_utc=now,
        packet_id=checked['packet_id'], sha256=checked['zip_sha256'], zip_sha256=checked['zip_sha256'],
        zip=str(stable), share_copy=str(share) if share else None, bytes=checked['zip_bytes'],
        zip_bytes=checked['zip_bytes'], source_commit=commit,
        source_commit_scope='Git HEAD anchor when available; exact current source bytes are bound by the packet manifest.',
        review_metadata_commit=None, generator_count=len(manifest['all_ids']), audit_count=len(manifest['all_ids']),
        eligible_main_count=len(manifest['main_ids']), packet_approved_generators=sum(bool(x.get('approved')) for x in manifest['generators'].values()),
        approved_generators=stats['approved'], owner_generator_count=stats['generators'], owner_stats=stats,
        publication_status='local_verified_ready', publication_verified=False, publication_url=None, publication_tag=None)
    current.pop('pending_owner_source_changes', None)
    build_receipt = catalog.root / 'var/review/full-packets' / checked['packet_id'] / 'receipt.json'
    current['build_receipt'] = None;current['build_receipt_sha256'] = None
    if build_receipt.is_file():
        _no_symlinks(build_receipt);built = json.loads(build_receipt.read_text())
        if not isinstance(built,dict) or built.get('packet_id') != checked['packet_id'] or built.get('zip_sha256') != checked['zip_sha256']:
            raise ValueError('Native cached build receipt differs from this packet')
        current['build_receipt'] = str(build_receipt);current['build_receipt_sha256'] = sha(build_receipt)
    current.update(packet_layout='clean-workspace-v1',workspace='WORK',entrypoint='review.py')
    selection = dict(manifest.get('selection') or {});selection.pop('reasons', None)
    selection.setdefault('selected_ids', manifest['all_ids'])
    if 'reasons' in (manifest.get('selection') or {}):selection['reasons_in_packet_manifest']='selection.reasons'
    selection['focus_rationale']='Frozen builder selection; main draw probabilities remain those in the manifest.'
    current['packet_selection'] = selection;current['main_draw_policy'] = manifest.get('main_draw_policy')
    size = current.setdefault('packet_size', {});size.update(files=checked['member_count'], zip_bytes=checked['zip_bytes'], expanded_bytes=checked['expanded_bytes']);size.pop('reduction_percent', None)
    if manifest.get('authoring_focus_policy'):
        focus = manifest['authoring_focus_policy'];current['authoring_focus_policy']={k:v for k,v in focus.items() if k!='anchors'}
        current['authoring_focus_policy']['anchors_count']=len(focus.get('anchors', []))
    if manifest.get('supplementary_ticket_policy', {}).get('nvarc_coverage'):
        current['nvarc_ticket_coverage']=manifest['supplementary_ticket_policy']['nvarc_coverage']
    cold = proof['cold_probe'];current['current_generation_smoke']=cold['episode']
    current.setdefault('bundled_racket', {}).update(version=cold['racket'].get('version'),binary_sha256=cold['racket'].get('binary_sha256'))
    current['publication_verification_scope']='Local file publication from the bound owner cold-check receipt and fresh source hashes; no independent receipt authentication. Runtime scope: '+proof.get('scope','one selected task')
    current['current_packet_validation']={'manifest':str(proof_path),'sha256':proof_sha,'packet_id':checked['packet_id'],
        'status':'passed','verification_reexecuted':False,'scope':proof['scope'] if 'scope' in proof else 'Bound owner verification receipt.',
        'basis':'Completed owner-supplied cold-check receipt, retained logs/harness and fresh owner-source hash comparison; not independent authentication of execution.',
        'generation':cold['episode'],'accepted_export':cold.get('accepted_export')}
    current['latest_combined_packet_check']=current['current_packet_validation']
    if cold.get('accepted_export') and 'inline_parametric_export' in current:
        current['inline_parametric_export']['latest_relocated_standard_export']=cold['accepted_export']
    return current


def publish_packet(catalog, packet, verification, out, *, share_dir=None):
    """Update the local sendable ZIP only after its supplied proof remains bound.

    No builds, runtime commands, approvals, training decisions, commits or pushes
    run here. Keep the input verification directory: metadata links its receipt
    and logs. The new output directory retains transaction/recovery information.
    """
    root = catalog.root.absolute();packet = Path(packet).absolute();verification = Path(verification).absolute();out = Path(out).absolute()
    for path in [root, packet, verification, out]:_no_symlinks(path)
    if out.exists():raise FileExistsError('Publication output must be new: ' + str(out))
    stable = root / 'var/review/SEND-THIS-ARCpuzzles-review.zip';metadata = root / 'REVIEW/full-packet-current.json'
    for path in [stable, metadata]:_no_symlinks(path)
    with _lock(root / 'REVIEW'):
        checked = inspect_packet(packet);report, proof_sha = _verification(verification, checked)
        owner = _compare_owner(root, checked['manifest'])
        checked['zip_bytes']=packet.stat().st_size
        with zipfile.ZipFile(packet) as archive:checked['expanded_bytes']=sum(x.file_size for x in archive.infolist())
        metadata_raw = metadata.read_bytes() if metadata.exists() else None
        metadata_sha = hashlib.sha256(metadata_raw).hexdigest() if metadata_raw is not None else None
        current = json.loads(metadata_raw) if metadata_raw is not None else {}
        if not isinstance(current,dict):raise ValueError('Current handoff metadata must be an object')
        stable_sha = sha(stable) if stable.exists() else None
        if stable_sha is not None and stable_sha != current.get('sha256'):
            raise ValueError('Current stable ZIP differs from its handoff; preserve/reconcile it first')
        share = None;share_sha = None
        if share_dir is not None:
            directory=Path(share_dir).absolute();_no_symlinks(directory)
            if not directory.is_dir():raise NotADirectoryError(directory)
            share=directory/('ARCpuzzles-review-current-'+checked['zip_sha256'][:8]+'.zip');_no_symlinks(share)
            share_sha = sha(share) if share.exists() else None
            if share_sha is not None and share_sha != checked['zip_sha256']:raise FileExistsError('Share copy conflicts: ' + str(share))
        destinations = [stable, metadata] + ([share] if share else [])
        if verification in destinations or len(set(destinations)) != len(destinations):raise ValueError('Publication paths collide')
        result = {'schema':'arcpuzzles-packet-publication-v1','status':'preparing','packet_id':checked['packet_id'],
            'packet':str(packet),'zip_sha256':checked['zip_sha256'],'zip_bytes':checked['zip_bytes'],
            'verification':{'path':str(verification),'sha256':proof_sha},'owner_sources':owner,
            'stable':str(stable),'share_copy':str(share) if share else None,'training_admitted':False,
            'scope':'Local file publication from bound owner evidence; no runtime re-execution, independent receipt authentication or source approval.'}
        value=_metadata(catalog,current,checked,report,verification,proof_sha,stable,share)
        value['publication_receipt']=str(out/'publication.json')
        out.mkdir(parents=True);candidate=out/'candidate-handoff.json';candidate.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
        if metadata_raw is not None:(out/'previous-handoff.json').write_bytes(metadata_raw)
        pairs=[(packet,stable,checked['zip_sha256'],stable_sha)]+([(packet,share,checked['zip_sha256'],share_sha)] if share else [])+[(candidate,metadata,sha(candidate),metadata_sha)]
        def before_commit():
            if sha(packet) != checked['zip_sha256'] or sha(verification) != proof_sha:
                raise ValueError('Packet or verification changed while publication was staged')
            _compare_owner(root,checked['manifest'])
        try:
            publish_files(pairs,out,result,before_commit=before_commit);result['status']='published'
        except BaseException as error:
            result.update(status='failed',error=f'{type(error).__name__}: {error}');raise
        finally:write_receipt(out/'publication.json',result)
        return result
