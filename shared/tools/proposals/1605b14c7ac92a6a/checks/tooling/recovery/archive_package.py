#!/usr/bin/env python3
"""Explicit archive-backed alternative for ENOSPC sparse ARCpuzzles reviews.

The original official helper is never edited. This tool verifies the complete
source ZIP, the hash-linked materialization history, every materialized original,
and the unchanged frozen baseline before using official delta/return semantics.
It does not claim that the official physical full-tree check was run.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
from importlib.abc import Loader, MetaPathFinder
from contextlib import contextmanager
import linecache
import json
from pathlib import Path
import stat
import sys
import zipfile

import sparse_packet as sparse

CACHES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
# Assembly copied from this exact upstream generic helper, never from task code.
OFFICIAL_RETURN_SOURCE_SHA256 = 'a021d00ec056acbdf0958955f5d08f110bff934375a6dac397fc3f86089a2f74'


def no_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f'Symlink path or ancestor: {part}')


def receipt_history(state, binding, expected, head_sha256, work):
    snapshot, head = sparse.load_receipt(state, binding)
    if not snapshot or head['sha256'] != head_sha256:
        raise ValueError('Extraction receipt head differs from required receipt SHA256')
    successor_files = None
    reference = head
    while reference:
        event = json.loads((state / reference['filename']).read_bytes())
        if event.get('schema') != 'arcpuzzles-sparse-extraction-v1' or event.get('workspace') != str(work):
            raise ValueError('Extraction receipt schema/workspace differs')
        files = event.get('files')
        if not isinstance(files, dict) or any(expected.get(n) != h for n,h in files.items()):
            raise ValueError('Extraction receipt inventory differs from original archive')
        if successor_files is not None and not files.items() <= successor_files.items():
            raise ValueError('Extraction receipt cumulative inventory rolled back')
        successor_files = files
        reference = event['previous_receipt']
    return snapshot, head


def tracked_sources(work, manifest, contract, snapshot):
    """Check the physical overlay; omitted originals stay immutable in the ZIP."""
    home=f"repo/generators/{contract['task_id']}/"
    baseline=set(contract['baseline_sha256'])
    if any(manifest['files'].get(n) != h for n,h in contract['baseline_sha256'].items()):
        raise ValueError('Assignment baseline differs from original manifest')
    if not {n for n in manifest['files'] if n.startswith(home)} <= baseline:
        raise ValueError('Assignment baseline omits selected original source')
    candidates=set(baseline)
    for target in (work/home).rglob('*'):
        no_symlinks(target)
        relative=target.relative_to(work)
        if (target.is_file() and not any(p in CACHES for p in relative.parts)
                and target.suffix not in {'.pyc','.pyo'}):
            candidates.add(relative.as_posix())
    materialized=snapshot['files']
    for name in materialized:
        if not name.startswith('WORK/'):
            target=work.parent/name
        else:
            target=work/name.removeprefix('WORK/')
        no_symlinks(target)
        if not target.is_file():
            raise ValueError(f'Missing materialized source: {name}')
        relative=name.removeprefix('WORK/')
        if relative not in candidates and sparse.file_hash(target) != materialized[name]:
            raise ValueError(f'Changed materialized source: {name}')
    for path in baseline:
        if 'WORK/'+path not in materialized:
            raise ValueError(f'Selected baseline was not materialized: {path}')
        target=work/'.review/baseline'/path
        no_symlinks(target)
        if not target.is_file() or sparse.file_hash(target) != contract['baseline_sha256'][path]:
            raise ValueError(f'Frozen baseline changed: {path}')
    frozen_root=work/'.review/baseline'
    for target in frozen_root.rglob('*'):
        no_symlinks(target)
        if not target.is_dir() and (not target.is_file() or target.relative_to(frozen_root).as_posix() not in baseline):
            raise ValueError(f'Unexpected frozen baseline source: {target.relative_to(frozen_root)}')
    digests={}
    for target in (work/'repo').rglob('*'):
        no_symlinks(target)
        path=target.relative_to(work)
        if any(p in CACHES for p in path.parts) or target.suffix in {'.pyc','.pyo'}:
            continue
        if target.is_dir():
            # Directory aliases cannot shadow an omitted original regular file.
            if path.as_posix() in manifest['files']:
                raise ValueError(f'Nonregular original source: {path}')
            continue
        if not target.is_file():
            raise ValueError(f'Nonregular source: {path}')
        name=path.as_posix()
        if name not in manifest['files'] and name not in candidates:
            raise ValueError(f'Undeclared new source outside selected generator: {name}')
        digest=sparse.file_hash(target)
        if name in manifest['files'] and name not in candidates and digest != manifest['files'][name]:
            raise ValueError(f'Changed shared packet source: {name}')
        digests[name]=digest
    return candidates,digests


class _OriginalZipSource(Loader, MetaPathFinder):
    """Source-only importer supporting ZIP64, bound to verified original hashes.

    Python 3.12 zipimport cannot index this packet's ZIP64 central directory.
    No physical extraction or bytecode cache is used by this private importer.
    """
    def __init__(self, source_zip, archive, expected):
        self.source_zip=source_zip
        self.archive=archive
        self.expected=expected

    def _member(self, fullname):
        relative=fullname.replace('.', '/')
        for suffix in ('/__init__.py','.py'):
            member='WORK/repo/src/'+relative+suffix
            if member in self.expected:
                return member,suffix=='/__init__.py'
        raise ImportError(f'Original source module absent from manifest: {fullname}')

    def find_spec(self, fullname, path=None, target=None):
        if fullname!='arcpuzzles' and not fullname.startswith('arcpuzzles.'):
            return None
        member,is_package=self._member(fullname)
        filename=str(self.source_zip)+'/'+member
        return importlib.util.spec_from_file_location(fullname,filename,loader=self,
            submodule_search_locations=[filename.rsplit('/',1)[0]] if is_package else None)

    def create_module(self, spec):
        return None

    def get_source(self, fullname):
        member,_=self._member(fullname)
        raw=self.archive.read(member)
        if hashlib.sha256(raw).hexdigest()!=self.expected[member]:
            raise ValueError(f'Original helper source hash differs: {member}')
        return importlib.util.decode_source(raw)

    def exec_module(self, module):
        text=self.get_source(module.__name__)
        filename=module.__spec__.origin
        # Keep introspection available after this short-lived import context.
        linecache.cache[filename]=(len(text.encode()),None,text.splitlines(True),filename)
        exec(compile(text,filename,'exec'),module.__dict__)


@contextmanager
def load_official(source_zip, expected):
    # Called only after complete original archive streaming verification. Every
    # imported source is verified again against that same manifest before exec.
    source=Path(str(source_zip)+'/WORK/repo/src')
    for name,module in list(sys.modules.items()):
        if name=='arcpuzzles' or name.startswith('arcpuzzles.'):
            filename=getattr(module,'__file__',None)
            if (not filename or not Path(filename).resolve().is_relative_to(source.resolve())
                    or not isinstance(getattr(module,'__loader__',None),_OriginalZipSource)):
                raise ValueError('A different arcpuzzles package is already loaded')
    with zipfile.ZipFile(source_zip) as original:
        loader=_OriginalZipSource(source_zip,original,expected)
        sys.meta_path.insert(0,loader)
        try:
            yield importlib.import_module('arcpuzzles.review_full_return')
        finally:
            sys.meta_path.remove(loader)


def build_archive_return(source_zip, packet_root, out, *, receipt_sha256, bundle_evidence=False):
    source_zip=Path(source_zip).absolute();work=Path(packet_root).absolute();out=Path(out).absolute()
    no_symlinks(source_zip);no_symlinks(work);no_symlinks(out)
    if not source_zip.is_file(): raise ValueError('Source ZIP must be regular')
    if out.exists(): raise FileExistsError(out)
    archive_sha=sparse.file_hash(source_zip)
    with sparse.recovery_lock(work.parent) as state, zipfile.ZipFile(source_zip) as original:
        manifest,expected=sparse.verify_archive(original)
        if expected.get('WORK/repo/src/arcpuzzles/review_full_return.py') != OFFICIAL_RETURN_SOURCE_SHA256:
            raise ValueError('Unsupported official packager version; assembly equivalence must be reverified')
        binding={'archive_sha256':archive_sha,'manifest_sha256':expected['WORK/PACKET-MANIFEST.json']}
        if (work/'PACKET-MANIFEST.json').read_bytes() != original.read('WORK/PACKET-MANIFEST.json'):
            raise ValueError('Physical packet manifest differs from original archive')
        snapshot,head=receipt_history(state,binding,expected,receipt_sha256,work)
        no_symlinks(work/'ASSIGNMENT.json')
        contract_bytes=(work/'ASSIGNMENT.json').read_bytes();contract=json.loads(contract_bytes)
        if contract.get('packet_id') != hashlib.sha256(sparse.canonical(manifest)).hexdigest():
            raise ValueError('Assignment packet ID mismatch')
        if contract.get('task_id') != snapshot['main_task_id']:
            raise ValueError('Assignment differs from immutable materialization selection')
        seed_path=state/'seed.json';no_symlinks(seed_path)
        seed_state=json.loads(seed_path.read_bytes())
        if (seed_state.get('schema') != 'arcpuzzles-sparse-recovery-seed-v1'
                or any(seed_state.get(k) != v for k,v in binding.items())
                or seed_state.get('seed') != contract.get('seed')):
            raise ValueError('Assignment differs from immutable recovery seed binding')
        if snapshot.get('assignment_id',contract.get('assignment_id')) != contract.get('assignment_id'):
            raise ValueError('Assignment identity differs from materialization receipt')
        candidates,digests=tracked_sources(work,manifest,contract,snapshot)
        with load_official(source_zip,expected) as official:
            changes=[]
            for path in sorted(candidates):
                home=f"repo/generators/{contract['task_id']}/"
                if path not in manifest['files'] and not path.startswith(home):
                    raise ValueError(f'Unexpected new source path: {path}')
                target=work/path;no_symlinks(target)
                if target.is_symlink() or (target.exists() and (not target.is_file() or target.stat().st_mode & 0o111)):
                    raise ValueError(f'Unsafe changed source: {path}')
                baseline=work/'.review/baseline'/path;no_symlinks(baseline)
                before=baseline.read_bytes() if baseline.is_file() else None
                after=target.read_bytes() if target.is_file() else None
                if before==after: continue
                if not official._allowed(path,contract) or after is None:
                    raise ValueError(f'Changed source outside allowed task scope: {path}')
                if path=='repo/shared/data/canonical/puzzles.jsonl':
                    official._canonical_only_task(before,after,contract['generator']['rule_task_id'])
                changes.append(official._diff(path,before,after))
            if sparse.file_hash(source_zip) != archive_sha:
                raise ValueError('Original archive changed during verification')
            result=_assemble_return(work,out,bundle_evidence,manifest,contract_bytes,contract,contract['task_id'],changes)
            try:
                _,after_digests=tracked_sources(work,manifest,contract,snapshot)
                if after_digests != digests:
                    raise ValueError('Working sources changed during packaging')
                if sparse.file_hash(source_zip) != archive_sha:
                    raise ValueError('Original archive changed during packaging')
            except BaseException:
                out.unlink(missing_ok=True)
                raise
            result['archive_verification']={'schema':'arcpuzzles-archive-package-verification-v1',
                **binding,'materialization_receipt':head,'verified_source_files':len(expected),
                'materialized_source_files':len(snapshot['files']),
                'omitted_original_files':len(set(expected)-snapshot['files'].keys()),
                'mode':'verified_archive_and_materialized_overlay','full_physical_tree_check_run':False,
                'official_return_validator_passed':True,'official_return_helper_sha256':OFFICIAL_RETURN_SOURCE_SHA256,
                'tool_sha256':sparse.file_hash(Path(__file__)),
                'return_zip_sha256':result['zip_sha256'],'training_admitted':False}
            return result


def _assemble_return(packet_root,out,bundle_evidence,manifest,contract_bytes,contract,tid,changes):
    # Copied verbatim from the official builder starting at payload assembly,
    # apart from the explicit absolute import of review_curriculum below.
    from arcpuzzles.review_full_return import (_sha, REQUIRED_DOCS, MAX_MEMBERS,
        bundles, canonical_json, _intake_summary, check_zip_budget, validate_full_return)
    payload = {"ASSIGNMENT.json": contract_bytes}
    audit_path = packet_root / "AUDIT_ASSIGNMENT.json"
    if audit_path.is_file():
        payload["AUDIT_ASSIGNMENT.json"] = audit_path.read_bytes()
        if not (packet_root / "AUDIT.md").is_file():
            raise ValueError("Drawn audit needs AUDIT.md findings")
    blind_path = packet_root / "BLIND_ASSIGNMENT.json"
    if blind_path.is_file():
        payload["BLIND_ASSIGNMENT.json"] = blind_path.read_bytes()
    for name in REQUIRED_DOCS:
        path = packet_root / name
        if not path.is_file():
            raise ValueError(f"Missing review document: {name}")
        payload[name] = path.read_bytes()
    if audit_path.is_file():
        payload["AUDIT.md"] = (packet_root / "AUDIT.md").read_bytes()
    checks = packet_root / "checks"
    if checks.is_symlink():
        raise ValueError(f"Symlink check evidence: {checks}")
    if checks.exists():
        for path in checks.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink check evidence: {path}")
            if path.is_file():
                payload[path.relative_to(packet_root).as_posix()] = path.read_bytes()
    if changes:
        payload["patches/source.patch"] = "".join(changes).encode("utf-8")
    solve_root = packet_root / "solve"
    if solve_root.is_symlink():
        raise ValueError(f"Symlink solve evidence: {solve_root}")
    if solve_root.exists():
        for path in solve_root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink solve evidence: {path}")
            if path.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(solve_root).parts):
                payload[path.relative_to(packet_root).as_posix()] = path.read_bytes()
        frozen_generator = packet_root / ".review/solve-private/generator.py"
        if frozen_generator.is_file():
            payload["solve/source/generator.py"] = frozen_generator.read_bytes()
    blind_root = packet_root / "solve-blind"
    if blind_root.is_symlink():
        raise ValueError(f"Symlink solve evidence: {blind_root}")
    if blind_root.exists():
        for path in blind_root.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink solve evidence: {path}")
            if path.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(blind_root).parts):
                payload[path.relative_to(packet_root).as_posix()] = path.read_bytes()
        frozen_blind = packet_root / ".review/solve-private-blind/generator.py"
        if frozen_blind.is_file():
            payload["solve-blind/source/generator.py"] = frozen_blind.read_bytes()
    projected = len(payload) + 2  # INTAKE.json and RESULTS.json
    checks_files = {name: raw for name, raw in payload.items() if name.startswith("checks/")}
    if checks_files and (bundle_evidence or projected > MAX_MEMBERS):
        for name in checks_files:
            del payload[name]
        payload.update(bundles.pack(checks_files))
        print(f"Packed {len(checks_files)} checks/ files into {bundles.ARCHIVE}; "
              f"return members {projected} -> {len(payload) + 2} (limit {MAX_MEMBERS}).", file=sys.stderr)
    results_path = packet_root / "RESULTS.json"
    supplied = json.loads(results_path.read_text()) if results_path.is_file() else {}
    results = {"schema": "arcpuzzles-full-results-v2", "assignment_id": contract["assignment_id"],
               "generator_id": tid, "completion_state": supplied.get("completion_state", "in_progress"),
               "stopping_reason": supplied.get("stopping_reason", "not recorded"),
               "modified_components": supplied.get("modified_components", []),
               "remaining_failures": supplied.get("remaining_failures", []),
               "verification_commands": supplied.get("verification_commands", []),
               "artifacts": [{"path": name, "kind": ("patch" if name.startswith("patches/") else
                             "check" if name.startswith("checks/") or name.startswith("EVIDENCE-BUNDLE.") else
                             "document"), "sha256": _sha(raw)}
                             for name, raw in sorted(payload.items())
                             if name not in {"ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json", "BLIND_ASSIGNMENT.json"}]}
    if "curriculum" in supplied:
        from arcpuzzles.review_curriculum import bind_curriculum
        evidence = {name: _sha(raw) for name, raw in payload.items()}
        if bundles.MANIFEST in payload:
            evidence.update({row["path"]: row["sha256"] for row in
                             bundles.read_manifest(payload[bundles.MANIFEST])["files"]})
        results["curriculum"] = bind_curriculum(supplied["curriculum"], task_id=tid,
            generator=(packet_root / f"repo/generators/{tid}/generator.py").read_bytes(),
            canonical=(packet_root / "repo/shared/data/canonical/puzzles.jsonl").read_bytes(),
            rule_task_id=contract["generator"]["rule_task_id"], evidence=evidence)
    payload["INTAKE.json"] = canonical_json(_intake_summary(payload, contract, results))
    results["artifacts"].append({"path": "INTAKE.json", "kind": "document", "sha256": _sha(payload["INTAKE.json"])})
    payload["RESULTS.json"] = canonical_json(results)
    out = (out or packet_root / f"review_response_{contract['assignment_id']}.zip").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    expanded = (bundles.read_manifest(payload[bundles.MANIFEST])["expanded_bytes"]
                if bundles.MANIFEST in payload else None)
    check_zip_budget((name, expanded if name == bundles.ARCHIVE else len(raw)) for name, raw in payload.items())
    with zipfile.ZipFile(out, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    try:
        with zipfile.ZipFile(out) as archive:
            checked = validate_full_return(archive, manifest)
    except Exception:
        out.unlink()
        raise
    return {"zip": str(out), "zip_sha256": _sha(out.read_bytes()), **checked}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_zip',type=Path)
    parser.add_argument('work',type=Path,help='Sparse WORK directory, containing repo/')
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--receipt-sha256',required=True,help='Previously recorded latest materialization snapshot SHA256')
    parser.add_argument('--verification-out',required=True,type=Path,help='Separate new provenance receipt; this is not an official full-tree check')
    parser.add_argument('--bundle-evidence',action='store_true')
    args=parser.parse_args()
    try:
        no_symlinks(args.verification_out.absolute())
        if args.verification_out.exists():raise FileExistsError(args.verification_out)
        if args.verification_out.absolute()==args.out.absolute():raise ValueError('ZIP and verification receipt paths must differ')
        result=build_archive_return(args.source_zip,args.work,args.out,
            receipt_sha256=args.receipt_sha256,bundle_evidence=args.bundle_evidence)
        sparse.atomic_bytes(args.verification_out.absolute(),sparse.canonical(result['archive_verification'])+b'\n')
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error:
        parser.exit(2,f'Archive-backed packaging stopped: {error}\n')
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=='__main__':main()
