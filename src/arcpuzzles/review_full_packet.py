"""Build a source-bound, reusable full-library generator review packet."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone

from .catalog import Catalog, local_path
from .review_notes import compact_suggestions, validate_index, validate_proposal_assets
from .parametric_priority import build_parametric_priority
from .review_public_creation import PUBLIC_WORK_SCHEMA, PUBLIC_WORK_POLICY


SCHEMA = "arcpuzzles-full-packet-v2"
RACKET_ARCHIVE_NAME = "racket-minimal-8.10-x86_64-linux-cs.tgz"
RACKET_ARCHIVE_SHA256 = "2c5fdc02787ba569f03d89cad6086a5c3be49045d58281e2db7fe31b43650eb7"
ROOT_FILES = ("AGENTS.md", "README.md", "pyproject.toml", "setup.py", "requirements.txt")
SELECTED_DOCS = ("REVIEW/README.md", "REVIEW/solves/README.md", "docs/placement.md", "docs/datasets.md",
                 "docs/verification.md", "docs/teammate-start.md", "docs/reviewer-check-resume.md",
                 "docs/SEMANTIC_GATE_CONTRACT.md", "docs/reference/PUZZLE_GENERATOR_SPEC.md",
                 "docs/parametric-promotion.md")
ROOT_DIRS = ("GUIDE", "catalog", "generators", "shared", "src", "tests", "tools")
SKIP_PARTS = {".git", "var", "build", "dist", "__pycache__", ".pytest_cache",
              ".mypy_cache", ".ruff_cache", ".venv", "venv", "secrets", "credentials",
              "weights", "checkpoints", "incoming", ".superpowers"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".zst", ".safetensors", ".pt", ".pth"}
# Retired capacity checks are kept in the owner checkout for old recovery
# records, but are not part of new reviewer packets or their test dependencies.
PACKET_EXCLUDED_PATHS = {
    "shared/tools/arc_review_guard.py",
    "tests/test_review_resource_guard.py",
    "tests/test_review_resource_restore.py",
}


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _source_files(root: Path, review_root: Path, *, selection: dict | None = None, fast: bool = False) -> dict[str, Path]:
    if selection is not None:
        from .review_packet_selection import project_library
        projected, _ = project_library(root, review_root, selection, fast=fast)
        files = {'repo/' + name: path for name, path in projected.items()}
        entry = Path(__file__).with_name('review_full_packet_files')
        for path in sorted(entry.iterdir()):
            if path.is_file(): files[path.name] = path
        for name in (*ROOT_FILES, *SELECTED_DOCS):
            path = root/name
            if path.is_file(): files['repo/' + name] = path
        for path in sorted((review_root/'questions').glob('*.json')):
            if path.is_symlink(): raise ValueError(f'Symlink question: {path}')
            files['repo/REVIEW/questions/' + path.name] = path
        for name in PACKET_EXCLUDED_PATHS:
            files.pop('repo/' + name, None)
        return files
    files: dict[str, Path] = {}
    retained_witnesses = validate_proposal_assets(root, compact_suggestions(review_root))
    for pattern in ('*/counterexamples/*/audit_assets.json', '*/counterexamples/current-shortcut.json'):
        for manifest_path in (root / 'generators').glob(pattern):
            if manifest_path.is_symlink():
                raise ValueError(f'Symlink evidence manifest: {manifest_path}')
            record = json.loads(manifest_path.read_text())
            for item in record.get('files', []):
                path = local_path(root, item['path'])
                if not path.is_file() or _sha(path.read_bytes()) != item['sha256']:
                    raise ValueError(f'Missing or changed retained witness: {item["path"]}')
                retained_witnesses.add(item['path'])
    entry = Path(__file__).with_name("review_full_packet_files")
    for path in sorted(entry.iterdir()):
        if path.is_file():
            files[path.name] = path
    for name in (*ROOT_FILES, *SELECTED_DOCS):
        path = root / name
        if path.is_file():
            files[f"repo/{name}"] = path
    for name in ROOT_DIRS:
        folder = root / name
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            relative = path.relative_to(root)
            if relative.as_posix() in PACKET_EXCLUDED_PATHS:
                continue
            if any(part in SKIP_PARTS or part.startswith(".env") for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError(f"Symlink in packet source: {relative}")
            if path.is_file() and (path.suffix not in SKIP_SUFFIXES or relative.as_posix() in retained_witnesses):
                if not path.resolve().is_relative_to(root):
                    raise ValueError(f"Source escapes checkout: {relative}")
                files[f"repo/{relative.as_posix()}"] = path
    questions = review_root / "questions"
    for path in sorted(questions.glob("*.json")):
        if path.is_symlink():
            raise ValueError(f"Symlink question: {path}")
        files[f"repo/REVIEW/questions/{path.name}"] = path
    index_paths = [*sorted((review_root / "task_indexes").glob("*.json")),
                   *sorted((root / "generators").glob("*/evidence/review_index.json"))]
    seen_indexes = {}
    for path in index_paths:
        if path.is_symlink():
            raise ValueError(f"Symlink task index: {path}")
        task_id = path.parent.parent.name if path.name == "review_index.json" else path.stem
        index = json.loads(path.read_text(encoding="utf-8"))
        validate_index(index, task_id)
        if task_id in seen_indexes and seen_indexes[task_id] != path.read_bytes():
            raise ValueError(f"Conflicting task index: {task_id}; migrate before packaging")
        seen_indexes[task_id] = path.read_bytes()
        files[f"repo/generators/{task_id}/evidence/review_index.json"] = path
    suggestions = review_root / "suggestions.json"
    if not suggestions.is_file():
        suggestions = review_root / "suggestions.jsonl"  # Legacy migration input only.
    if suggestions.is_file():
        if suggestions.is_symlink():
            raise ValueError("Symlink suggestion history")
        files[f"repo/REVIEW/{suggestions.name}"] = suggestions
    for path in sorted((review_root / "approvals").glob("*.json")):
        if path.is_symlink():
            raise ValueError(f"Symlink approval receipt: {path}")
        record = json.loads(path.read_text())
        if record.get("schema") != "arcpuzzles-approval-v1":
            raise ValueError(f"Invalid approval receipt: {path}")
        files[f"repo/REVIEW/approvals/{path.name}"] = path
    return files


def _questions(review_root: Path) -> list[dict]:
    questions = []
    for path in sorted((review_root / "questions").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if (value.get("schema") != "arcpuzzles-review-question-v1"
                or value.get("id") != path.stem or type(value.get("version")) is not int
                or value["version"] < 1 or not value.get("owner") or not value.get("text")):
            raise ValueError(f"Invalid question: {path}")
        questions.append({"id": value["id"], "version": value["version"],
                          "sha256": _sha(path.read_bytes())})
    if not questions:
        raise ValueError("Full packet requires at least one current question")
    return questions


def build_full_packet(catalog: Catalog, review_root: Path, out: Path,
                      racket_archive: Path | None = None, *, reviewer_solve: bool = False,
                      blind_solve: bool = False, workspace_layout: bool = False,
                      selection_size: int | None = 500, focus_ids: list[str] | None = None,
                      task_ids: list[str] | None = None, supplementary_tickets: bool | None = None,
                      repair_target_count: int = 1, work_policy: dict | None = None, fast: bool = False) -> dict:
    from .review import _lock
    with _lock(review_root):
        # The caller may have loaded a Catalog before waiting for another
        # writer. Freeze current metadata, rather than its earlier cached rows.
        return _build_full_packet(Catalog(catalog.root), review_root, out, racket_archive,
            reviewer_solve=reviewer_solve, blind_solve=blind_solve, workspace_layout=workspace_layout,
            selection_size=selection_size, focus_ids=focus_ids, task_ids=task_ids,
            supplementary_tickets=supplementary_tickets, repair_target_count=repair_target_count, work_policy=work_policy, fast=fast)


def _owner_work_policy(review_root, repair_target_count, work_policy):
    """An owner default affects new packets, never issued manifests."""
    if work_policy is not None or repair_target_count not in {1, 2}:
        return work_policy
    current = Path(review_root) / 'full-packet-current.json'
    if not current.is_file():
        return None
    policy = json.loads(current.read_text()).get('default_work_policy')
    if policy is None:
        return None
    from .review_targets import TWO_WORK_POLICY, ONE_WORK_POLICY
    from .review_public_creation import PUBLIC_WORK_POLICY
    if policy not in (ONE_WORK_POLICY, TWO_WORK_POLICY, PUBLIC_WORK_POLICY):
        raise ValueError('default_work_policy must be a supported native/public work policy')
    if repair_target_count == 1:
        return ONE_WORK_POLICY if policy == ONE_WORK_POLICY else None
    if policy == ONE_WORK_POLICY:
        return TWO_WORK_POLICY
    if policy not in (TWO_WORK_POLICY, PUBLIC_WORK_POLICY):
        raise ValueError('default_work_policy must be an existing two-target work policy')
    return policy


def _build_full_packet(catalog: Catalog, review_root: Path, out: Path,
                      racket_archive: Path | None = None, *, reviewer_solve: bool = False,
                      blind_solve: bool = False, workspace_layout: bool = False,
                      selection_size: int | None = 500, focus_ids: list[str] | None = None,
                      task_ids: list[str] | None = None, supplementary_tickets: bool | None = None,
                      repair_target_count: int = 1, work_policy: dict | None = None, fast: bool = False) -> dict:
    if type(repair_target_count) is not int or repair_target_count not in {1, 2, 3}:
        raise ValueError("repair_target_count must be 1, 2 or 3")
    if repair_target_count in {2, 3}:
        supplementary_tickets = False
    root = catalog.root.resolve()
    review_root = review_root.resolve()
    work_policy = _owner_work_policy(review_root, repair_target_count, work_policy)
    from .review_targets import TWO_WORK_SCHEMA, ONE_WORK_SCHEMA
    focused_one = work_policy is not None and work_policy.get('schema') == ONE_WORK_SCHEMA
    if focused_one:
        supplementary_tickets = False
        reviewer_solve = blind_solve = False
    current_path = review_root / 'full-packet-current.json'
    owner_scope = json.loads(current_path.read_text()).get('default_base_target_scope', 'whole_pool') if current_path.is_file() else 'whole_pool'
    if owner_scope not in {'whole_pool', 'unapproved_only'}:
        raise ValueError('Invalid default_base_target_scope')
    unapproved_only = (repair_target_count in {1, 2} and work_policy is not None
                       and work_policy.get('schema') in {TWO_WORK_SCHEMA, ONE_WORK_SCHEMA}
                       and owner_scope == 'unapproved_only')
    out = out.resolve()
    if out.is_relative_to(root) and not out.is_relative_to(root / "var"):
        raise ValueError("Packet output inside checkout must be under ignored var/")
    if fast and racket_archive is None:
        local_archive = root / 'var/review' / RACKET_ARCHIVE_NAME
        if local_archive.is_file():
            racket_archive = local_archive
    if fast and (repair_target_count in {2, 3} or focused_one) and racket_archive is None:
        raise ValueError(f"Routine fast release requires bundled Racket: pass --racket-archive PATH "
                         f"or place the pinned archive at {root / 'var/review' / RACKET_ARCHIVE_NAME}")
    selection = None
    rotation_after = None
    if selection_size is not None:
        from .review_packet_selection import choose_selection
        selection, rotation_after = choose_selection(catalog, review_root,
            size=selection_size, focus_ids=focus_ids, task_ids=task_ids,
            unapproved_only=unapproved_only)
    elif task_ids is not None or focus_ids is not None:
        raise ValueError('Explicit packet selection requires selection_size')
    if fast and selection is None:
        raise ValueError('Fast release requires a bounded source selection')
    from .review_public_creation import creation_queue, add_creation_sources
    public_coverage_verification = {}
    public_creation = repair_target_count == 2 and (
        work_policy is None or work_policy.get('schema') == PUBLIC_WORK_SCHEMA)
    public_queue = creation_queue(root, fast=fast, verification=public_coverage_verification) if public_creation else []
    files = _source_files(root, review_root, selection=selection, fast=fast)
    from .review_python_wheels import verified_files as verified_pytest_wheels
    python_cache = root / 'var/review/python-wheels'
    python_wheels = verified_pytest_wheels(python_cache) if python_cache.exists() else {}
    files.update(python_wheels)
    if selection is not None:
        projected_catalog_path = files['repo/catalog/puzzles.jsonl']
        catalog = Catalog(projected_catalog_path.parent.parent)
    rows = catalog.query()
    all_ids = sorted(row["id"] for row in rows if row.get("generator"))
    priority = build_parametric_priority(catalog, rows=rows)
    # Inclusion carries authoring priority. Every reviewable included target has
    # the same draw weight, including approved targets with existing prototypes.
    from .review_packet_selection import reviewable_root
    main_ids = sorted(row['id'] for row in rows if reviewable_root(row))
    if racket_archive is not None:
        racket_archive = racket_archive.resolve()
        if racket_archive.name != RACKET_ARCHIVE_NAME or not racket_archive.is_file():
            raise ValueError(f"Expected offline Racket archive named {RACKET_ARCHIVE_NAME}")
        if _sha(racket_archive.read_bytes()) != RACKET_ARCHIVE_SHA256:
            raise ValueError("Racket archive SHA-256 differs from the pinned upstream release")
        files[f"vendor/{RACKET_ARCHIVE_NAME}"] = racket_archive
    for row in rows:
        if row.get("generator"):
            source = local_path(root, row["generator"])
            key = f"repo/{row['generator']}"
            if not source.is_file() or key not in files:
                raise FileNotFoundError(f"Missing cataloged generator: {key}")
    for name in ("catalog/puzzles.jsonl", "catalog/runtime_files.json", "catalog/authority_files.json",
                 "shared/data/canonical/puzzles.jsonl"):
        if f"repo/{name}" not in files:
            raise FileNotFoundError(f"Missing packet authority: {name}")
    for item in json.loads(files["repo/catalog/runtime_files.json"].read_text()):
        relative = item["path"]
        if f"repo/{relative}" not in files or not local_path(root, relative).is_file():
            raise FileNotFoundError(f"Missing mapped runtime source: {relative}")
    questions = _questions(review_root)
    # Optional external dataset sample is explicitly bundled once, never imported
    # into the puzzle catalog or expanded into the projected source library.
    if supplementary_tickets or (supplementary_tickets is None and selection and selection['owner_generator_count'] >= 300):
        from .review_nvarc import ARCHIVE_PATH, archive_candidates
        sample = root / 'var/review/ticket-data/NVARC-CHECK-001.zip'
        if sample.exists():
            archive_candidates(sample)
            files[ARCHIVE_PATH] = sample
    creation_rows = add_creation_sources(root, files, public_queue) if public_queue else {}
    digests = {name: _sha(path.read_bytes()) for name, path in sorted(files.items())}
    generators = {row["id"]: {
        "generator": row["generator"], "generator_sha256": row["generator_sha256"],
        "rule_task_id": row.get("rule_task_id", row["id"]), "rule_hash": row["rule_hash"],
        "approved": row["approved"],
    } for row in rows if row.get("generator")}
    for tid, row in creation_rows.items():
        row['catalog_present'] = tid in generators
    generators.update(creation_rows)
    if public_queue:
        main_ids = sorted(creation_rows)
        all_ids = sorted(set(all_ids) | set(main_ids))
    manifest = {"schema": SCHEMA, "files": digests, "all_ids": all_ids,
                "main_ids": main_ids, "generators": generators, "questions": questions,
                "parametric_priority": priority,
                "main_draw_policy": {"schema": "arcpuzzles-main-draw-policy-v2",
                    "distribution": "uniform", "ids": main_ids,
                    "priority_scope": "packet_inclusion_and_retention_only"},
                "canonical_sha256": digests["repo/shared/data/canonical/puzzles.jsonl"]}
    manifest['python_test_dependencies'] = {'bundled': bool(python_wheels),
        'scope': 'Pinned pytest and its Python3.12+ dependencies only; pip, NumPy and Pillow are not bundled.',
        'numpy_pillow_bundled': False, 'wheel_files': sorted(python_wheels),
        'wheel_bytes': sum(path.stat().st_size for path in python_wheels.values())}
    if repair_target_count in {2, 3} or focused_one:
        if len(main_ids) < repair_target_count:
            raise ValueError("Not enough generators for the required repair targets")
        from .review_targets import POLICY_SCHEMA
        manifest['repair_target_policy'] = {'schema': POLICY_SCHEMA, 'count': repair_target_count,
            'distribution': 'uniform_without_replacement', 'ids': main_ids}
        authorities = json.loads(files['repo/catalog/authority_files.json'].read_text())
        mapping = json.loads(files['repo/catalog/runtime_files.json'].read_text())
        manifest['repair_target_policy']['authority_owners'] = {
            'repo/' + item['path']: [tid for tid in main_ids
                if authorities.get(item['target']) in {tid, generators[tid]['rule_task_id']}]
            for item in mapping if item['target'].startswith('data/base/solutions/')}
        from .review_targets import (ADMISSION_WORK_POLICY, TWO_WORK_POLICY, TWO_WORK_SCHEMA,
                                     NATIVE_WORK_SCHEMAS, validate_work_policy)
        manifest['work_policy'] = work_policy if work_policy is not None else (
            PUBLIC_WORK_POLICY if public_queue else TWO_WORK_POLICY if repair_target_count == 2 else ADMISSION_WORK_POLICY)
        validate_work_policy(manifest, manifest)
        expected_count = (1 if focused_one else 2 if manifest['work_policy']['schema'] in {TWO_WORK_SCHEMA, PUBLIC_WORK_SCHEMA} else 3)
        if repair_target_count != expected_count:
            raise ValueError('Target count differs from the frozen work policy')
        if manifest['work_policy']['schema'] in NATIVE_WORK_SCHEMAS:
            from .review_base_preflight import eligible_ids, POLICY as BASE_REVIEW_POLICY
            wide_pool = manifest['work_policy']['schema'] in {TWO_WORK_SCHEMA, ONE_WORK_SCHEMA}
            from .parametric_promotion import status as parametric_status
            owner_catalog = Catalog(root)
            if fast:
                index_path = review_root/'parametric-families-current.json'
                accepted_snapshot = {r['task_id'] for r in json.loads(index_path.read_text()).get('families', [])} if index_path.is_file() else set()
                eligible = eligible_ids({tid: generators[tid] for tid in main_ids}, accepted_snapshot,
                                        include_unapproved=wide_pool)
            else:
                accepted = {tid for tid in main_ids if parametric_status(owner_catalog, tid)['status'] == 'accepted'}
                eligible = eligible_ids({tid: generators[tid] for tid in main_ids}, accepted,
                                        include_unapproved=wide_pool)
            required = repair_target_count if wide_pool else 1
            if unapproved_only:
                eligible = [tid for tid in eligible if not generators[tid]['approved']]
            if len(eligible) < required:
                if required == 1:
                    raise ValueError('No eligible main: need canonical-approved, not parametrically accepted generator')
                raise ValueError(f'Need {required} eligible built, not parametrically accepted generators')
            if wide_pool:
                manifest['base_review_policy'] = BASE_REVIEW_POLICY
            manifest['main_draw_policy'] = {'schema': 'arcpuzzles-main-draw-policy-v5' if wide_pool else 'arcpuzzles-main-draw-policy-v3',
                'distribution': 'base_approval_mixture' if wide_pool else 'uniform', 'ids': eligible,
                'eligibility_reason': 'implemented_reference_and_parametric_not_accepted' if wide_pool else 'canonical_approved_and_parametric_not_accepted',
                'excluded': {tid: ('canonical_not_approved' if not wide_pool and not generators[tid]['approved']
                                  else 'parametric_already_accepted') for tid in main_ids if tid not in eligible}}
            if wide_pool:
                manifest['main_draw_policy']['base_approval_ratio'] = {'unapproved': 4, 'approved': 1}
            if unapproved_only:
                # Reuse the issued uniform built-base draw implementation.
                # Existing v5 mixture packets and their replay stay unchanged.
                manifest['main_draw_policy'].update(schema='arcpuzzles-main-draw-policy-v4',
                    distribution='uniform', target_scope='unapproved_only')
                manifest['main_draw_policy'].pop('base_approval_ratio', None)
                manifest['main_draw_policy']['excluded'].update({
                    tid: 'base_already_approved' for tid in main_ids if generators[tid]['approved']})
            if repair_target_count == 2 or focused_one:
                manifest['repair_target_policy']['ids'] = eligible
    if public_queue:
        from .review_public_creation import allocation_policy
        manifest['public_eval_creation'] = {'schema': PUBLIC_WORK_SCHEMA, 'ids': main_ids,
            **allocation_policy(public_queue),
            'parents': public_queue, 'coverage_basis': 'current_owner_verified_parent_and_native_acceptance',
            'coverage_verification': public_coverage_verification,
            'reservations': 'frozen_packet_local_only; separate copies cannot share reservations'}
        manifest['main_draw_policy'] = {'schema': 'arcpuzzles-public-eval-creation-draw-v1',
            'distribution': 'uniform_without_replacement', 'ids': main_ids}
        reviewer_solve = blind_solve = False
    manifest['authoring_focus_policy'] = {
        'schema': 'arcpuzzles-authoring-focus-policy-v1',
        'probability': {'numerator': 1, 'denominator': 10},
        'target_selection': ('unchanged_main_policy' if manifest['main_draw_policy']['schema'] == 'arcpuzzles-main-draw-policy-v5'
                             else 'unchanged_uniform_main'),
        'anchors': priority['evaluation_focus']['anchors'],
        'scope': 'Independent public-evaluation inspiration; no main-target reweighting, lineage or training admission.'}
    from .review_storage_study import study_policy
    storage_study = study_policy(review_root)
    if storage_study is not None:
        manifest['storage_study'] = storage_study
    if selection is not None:
        manifest["selection"] = selection
    if supplementary_tickets is None:
        supplementary_tickets = bool(selection and selection['owner_generator_count'] >= 300)
    if supplementary_tickets:
        from .review_tickets import build_ticket_policy
        from .review_nvarc import ARCHIVE_PATH, completed_review_sources
        completed = completed_review_sources(root) if ARCHIVE_PATH in files else None
        manifest['supplementary_ticket_policy'] = build_ticket_policy(manifest, files, nvarc_completed=completed)
    if reviewer_solve:
        manifest["reviewer_solve"] = {"schema": "arcpuzzles-reviewer-solve-v1", "required": True,
            "policy": "visible_examples_only_no_reference_consultation", "feedback_policy": "visible_only"}
        if blind_solve:
            # A second, untouched task solved before any repair work; drawn from the
            # assignment seed so intake can recompute it.
            manifest["reviewer_solve"]["blind"] = {"schema": "arcpuzzles-blind-solve-assignment-v1",
                                                   "required": True, "pool": "approved_except_main"}
    entry_files = {}
    if workspace_layout:
        entry_root = Path(__file__).with_name("review_workspace_files")
        entry_files = {p.name: p for p in sorted(entry_root.iterdir()) if p.is_file()}
        manifest["layout"] = {"workspace": "WORK", "entry_files": {
            name: _sha(path.read_bytes()) for name, path in entry_files.items()}}
    if fast:
        manifest['release_verification'] = {'mode': 'fast', 'deep_validation': 'pending',
            'included': ['source_dependency_closure', 'content_hashes'] +
                        (['pinned_racket_archive'] if racket_archive is not None else []),
            'racket_archive_bundled': racket_archive is not None,
            'deferred': ['historical_evidence_graph', 'cold_environment_replay'],
            'accepted_family_eligibility': 'current_owner_index_snapshot'}
    manifest_bytes = canonical_json(manifest)
    packet_id = _sha(manifest_bytes)
    cache = root / "var/review/full-packets" / packet_id
    cache.mkdir(parents=True, exist_ok=True)
    cache_zip = cache / "request.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".packet-", suffix=".zip", dir=out.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as archive:
            archive_files = {("WORK/" + name if workspace_layout else name): path
                             for name, path in files.items()}
            archive_files.update(entry_files)
            for archive_name, path in sorted(archive_files.items()):
                name = archive_name.removeprefix("WORK/") if workspace_layout else archive_name
                raw = path.read_bytes()
                expected = manifest["layout"]["entry_files"][name] if name in entry_files else digests[name]
                if _sha(raw) != expected:
                    raise RuntimeError(f"Source changed during packet build: {name}")
                info = zipfile.ZipInfo(archive_name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, raw, compresslevel=1 if fast else 6)
            info = zipfile.ZipInfo(("WORK/" if workspace_layout else "") + "PACKET-MANIFEST.json", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, manifest_bytes)
        zip_sha = _sha(Path(temporary).read_bytes())
        if cache_zip.exists():
            if _sha(cache_zip.read_bytes()) != zip_sha:
                raise RuntimeError("Cached packet ID has different ZIP bytes")
        else:
            shutil.copy2(temporary, cache_zip)
        if out.exists() and not fast:
            if _sha(out.read_bytes()) != zip_sha:
                raise FileExistsError(f"Different packet already exists: {out}")
        else:
            os.replace(temporary, out)
        receipt = {"schema": "arcpuzzles-full-packet-build-v2", "packet_id": packet_id,
                   "zip_sha256": zip_sha, "zip": str(cache_zip),
                   "generator_count": len(all_ids), "eligible_count": len(manifest['main_draw_policy']['ids']),
                   "audit_count": len(all_ids),
                   "workspace": "WORK" if workspace_layout else ".",
                   "entrypoint": "review.py" if workspace_layout else "assignment.py"}
        receipt_path = cache / "receipt.json"
        if not receipt_path.exists():
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        if selection is not None:
            from .review_packet_selection import commit_rotation
            commit_rotation(review_root, selection, rotation_after)
        result = {**receipt, "zip": str(out), "receipt": str(receipt_path)}
        if fast:
            result['release_verification'] = manifest['release_verification']
            current_path = review_root/'full-packet-current.json'
            current = json.loads(current_path.read_text()) if current_path.is_file() else {}
            now = datetime.now(timezone.utc).isoformat()
            bundled = ({'archive': ('WORK/' if workspace_layout else '') + 'vendor/' + RACKET_ARCHIVE_NAME,
                        'archive_sha256': RACKET_ARCHIVE_SHA256, 'runtime_replayed': False}
                       if racket_archive is not None else None)
            current.update(zip=str(out), zip_sha256=zip_sha, sha256=zip_sha,
                packet_id=packet_id, zip_bytes=out.stat().st_size, bytes=out.stat().st_size,
                share_copy=str(out), status='ready_fast',
                ready_to_send=True, current_source_matches_packet=True,
                current_artifact_verified=False, publication_verified=False,
                publication_status='fast_published_validation_pending',
                current_packet_validation=manifest['release_verification'],
                latest_combined_packet_check=manifest['release_verification'],
                current_generation_smoke=None, bundled_racket=bundled,
                publication_verification_scope='Source closure and content hashes only; deep evidence and cold runtime replay pending.',
                publication_url=None, publication_tag=None,
                updated_at=now, updated_utc=now, source_commit=None,
                generator_count=len(all_ids), audit_count=len(all_ids), eligible_main_count=len(main_ids),
                packet_approved_generators=sum(bool(row['approved']) for row in generators.values()),
                packet_selection=manifest.get('selection'), main_draw_policy=manifest['main_draw_policy'],
                packet_size={'files': len(files) + len(entry_files) + 1, 'zip_bytes': out.stat().st_size},
                workspace=receipt['workspace'], entrypoint=receipt['entrypoint'],
                build_receipt=str(receipt_path), build_receipt_sha256=_sha(receipt_path.read_bytes()),
                publication_receipt=str(receipt_path))
            if isinstance(current.get('inline_parametric_export'), dict):
                current['inline_parametric_export'].pop('latest_relocated_standard_export', None)
            temporary_metadata = current_path.with_suffix('.fast.tmp')
            temporary_metadata.write_text(json.dumps(current, indent=2, sort_keys=True)+'\n')
            os.replace(temporary_metadata, current_path)
            result['published'] = True
        return result
    finally:
        Path(temporary).unlink(missing_ok=True)


def packet_member(packet: zipfile.ZipFile, name: str) -> bytes:
    """Read a logical workspace path from either supported packet layout."""
    try:
        packet.getinfo("WORK/PACKET-MANIFEST.json")
    except KeyError:
        prefix = ""
    else:
        prefix = "WORK/"
    return packet.read(prefix + name)


def packet_names(packet: zipfile.ZipFile) -> set[str]:
    """Return logical workspace members for source/patch comparison."""
    names = packet.namelist()
    if "WORK/PACKET-MANIFEST.json" in names:
        return {name.removeprefix("WORK/") for name in names if name.startswith("WORK/")}
    return set(names)
