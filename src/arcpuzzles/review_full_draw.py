"""Reproducible independent local main and adversarial review draws."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile

from .review_full_packet import SCHEMA, canonical_json
from .review_public_creation import PUBLIC_WORK_SCHEMA


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_manifest(packet_root: Path) -> tuple[dict, str]:
    raw = (packet_root / "PACKET-MANIFEST.json").read_bytes()
    manifest = json.loads(raw)
    if manifest.get("schema") != SCHEMA or canonical_json(manifest) != raw:
        raise ValueError("Packet manifest is not canonical or has wrong schema")
    return manifest, _sha(raw)


def _verify(packet_root: Path, manifest: dict, path: str) -> bytes:
    expected = manifest["files"].get(path)
    target = packet_root / path
    if not expected or not target.is_file() or target.is_symlink():
        raise ValueError(f"Missing packet source: {path}")
    raw = target.read_bytes()
    if _sha(raw) != expected:
        raise ValueError(f"Packet source changed: {path}")
    return raw


def _seed(seed: bytes | None) -> bytes:
    seed = os.urandom(32) if seed is None else seed
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError("Draw seed must be exactly 32 bytes")
    return seed


def _base_paths(packet_root: Path, manifest: dict, task_id: str) -> list[str]:
    row = manifest["generators"][task_id]
    home = f"repo/generators/{task_id}/"
    paths = [name for name in manifest["files"] if name.startswith(home)]
    canonical = "repo/shared/data/canonical/puzzles.jsonl"
    paths.append(canonical)
    mapping = json.loads(_verify(packet_root, manifest, "repo/catalog/runtime_files.json"))
    authorities = json.loads(_verify(packet_root, manifest, "repo/catalog/authority_files.json"))
    bound = {task_id, row["rule_task_id"]}
    for item in mapping:
        if item["target"].startswith("data/base/solutions/") and authorities.get(item["target"]) in bound:
            paths.append("repo/" + item["path"])
    return sorted(set(paths))


def _contract_path(packet_root: Path, name: str) -> Path:
    return packet_root / name


def blind_id_for_seed(manifest: dict, main_id: str, seed: bytes) -> str:
    """The untouched blind-solve task: an approved generator other than the repair target."""
    excluded = ({row['task_id'] for row in repair_selection_for_seed(manifest, seed)}
                if manifest.get('repair_target_policy') else {main_id})
    approved = sorted(tid for tid, row in manifest["generators"].items() if row.get("approved") and tid not in excluded)
    pool = approved or sorted(tid for tid in manifest["all_ids"] if tid not in excluded)
    if not pool:
        raise ValueError("Blind solve needs a generator other than the repair target")
    return pool[int.from_bytes(hashlib.sha256(seed + b":blind").digest(), "big") % len(pool)]


def _uniform_index(seed, domain, length):
    limit = (1 << 256) - ((1 << 256) % length)
    attempt = 0
    while True:
        value = int.from_bytes(hashlib.sha256(seed + domain + str(attempt).encode()).digest(), 'big')
        if value < limit:
            return value % length
        attempt += 1


def _base_priority_target(manifest, seed, *, excluded=(), slot=0):
    from .review_base_preflight import POLICY as BASE_REVIEW_POLICY
    from .review_targets import TWO_WORK_SCHEMA, ONE_WORK_SCHEMA
    policy = manifest['main_draw_policy']; pool = policy.get('ids')
    if (manifest.get('work_policy', {}).get('schema') not in {TWO_WORK_SCHEMA, ONE_WORK_SCHEMA}
            or manifest.get('base_review_policy') != BASE_REVIEW_POLICY
            or policy.get('distribution') != 'base_approval_mixture'
            or policy.get('base_approval_ratio') != {'unapproved': 4, 'approved': 1}
            or policy.get('eligibility_reason') != 'implemented_reference_and_parametric_not_accepted'
            or not isinstance(pool, list) or not pool or pool != sorted(set(pool))
            or not set(pool) <= set(manifest['main_ids'])):
        raise ValueError('Invalid eligible main draw pool or base approval ratio')
    available = [tid for tid in pool if tid not in excluded]
    groups = {False: [], True: []}
    for tid in available:
        groups[manifest['generators'][tid]['approved']].append(tid)
    approved = _uniform_index(seed, f':base-group:{slot}:'.encode(), 5) == 4
    selected = groups[approved] or groups[not approved]
    if not selected:
        raise ValueError('No remaining eligible targets')
    return selected[_uniform_index(seed, f':base-target:{slot}:'.encode(), len(selected))]


def main_selection_for_seed(manifest: dict, seed: bytes) -> tuple[str, dict | None]:
    """Draw uniformly in new packets while replaying issued policies exactly."""
    seed = _seed(seed)
    if manifest.get('work_policy', {}).get('schema') == PUBLIC_WORK_SCHEMA:
        from .review_public_creation import select
        return select(manifest, seed)[0]['task_id'], None
    policy = manifest.get('main_draw_policy')
    if policy and policy.get('schema') == 'arcpuzzles-main-draw-policy-v5':
        task_id = _base_priority_target(manifest, seed)
        return task_id, _independent_authoring_focus(manifest, task_id, seed)
    if policy is None:
        pool = manifest['main_ids']
        if not pool:
            raise ValueError('Empty main draw pool')
        return pool[int.from_bytes(seed, 'big') % len(pool)], None
    if policy.get('schema') in {'arcpuzzles-main-draw-policy-v3', 'arcpuzzles-main-draw-policy-v4'}:
        from .review_targets import NATIVE_WORK_SCHEMAS
        from .review_base_preflight import POLICY as BASE_REVIEW_POLICY
        wide = policy['schema'] == 'arcpuzzles-main-draw-policy-v4'
        pool = policy.get('ids')
        if (manifest.get('work_policy', {}).get('schema') not in NATIVE_WORK_SCHEMAS
                or policy.get('distribution') != 'uniform' or not isinstance(pool, list)
                or not pool or pool != sorted(set(pool)) or not set(pool) <= set(manifest['main_ids'])
                or (not wide and any(not manifest['generators'][tid]['approved'] for tid in pool))
                or (wide and manifest.get('base_review_policy') != BASE_REVIEW_POLICY)
                or policy.get('eligibility_reason') != ('implemented_reference_and_parametric_not_accepted'
                    if wide else 'canonical_approved_and_parametric_not_accepted')):
            raise ValueError('Invalid eligible main draw pool')
        # Rejection sampling removes modulo bias; no target-dependent rerolls.
        value = int.from_bytes(seed, 'big'); attempt = 0
        limit = (1 << 256) - ((1 << 256) % len(pool))
        while value >= limit:
            value = int.from_bytes(hashlib.sha256(seed + f':eligible-main:{attempt}'.encode()).digest(), 'big')
            attempt += 1
        task_id = pool[value % len(pool)]
        return task_id, _independent_authoring_focus(manifest, task_id, seed)
    if policy.get('schema') == 'arcpuzzles-main-draw-policy-v2':
        pool = policy.get('ids')
        if (policy.get('distribution') != 'uniform' or not isinstance(pool, list)
                or not pool or not all(isinstance(tid, str) for tid in pool)
                or pool != manifest.get('main_ids') or len(set(pool)) != len(pool)):
            raise ValueError('Invalid uniform main draw pool')
        task_id = pool[int.from_bytes(seed, 'big') % len(pool)]
        return task_id, _independent_authoring_focus(manifest, task_id, seed)
    if policy.get('schema') != 'arcpuzzles-main-draw-policy-v1':
        raise ValueError('Unknown main draw policy')
    pool = policy['normal_ids']
    if not pool or not set(pool) <= set(manifest['main_ids']):
        raise ValueError('Invalid normal main draw pool')
    normal = pool[int.from_bytes(seed, 'big') % len(pool)]
    focus = policy['evaluation_focus']
    if (focus.get('schema') != 'arcpuzzles-evaluation-focus-v1'
            or focus.get('probability') != {'numerator': 1, 'denominator': 10}):
        raise ValueError('Invalid evaluation focus policy')
    anchors = focus['anchors']
    roll = int.from_bytes(hashlib.sha256(seed + b':evaluation-focus').digest(), 'big') % 10
    if not anchors or roll != 0:
        return normal, None
    anchor = anchors[int.from_bytes(hashlib.sha256(seed + b':evaluation-origin').digest(), 'big') % len(anchors)]
    related = anchor['main_ids']
    if not set(related) <= set(manifest['main_ids']):
        raise ValueError('Invalid evaluation main draw pool')
    tid = (related[int.from_bytes(hashlib.sha256(seed + b':evaluation-generator').digest(), 'big') % len(related)]
           if related else normal)
    return tid, {
        'schema': 'arcpuzzles-assignment-authoring-focus-v1',
        'kind': 'public_evaluation', 'probability': focus['probability'],
        'source_split': 'evaluation', 'source_task_id': anchor['source_task_id'],
        'challenge_sha256': anchor['challenge_sha256'], 'source_path': anchor['source_path'],
        'mode': 'direct_related' if related else 'inspired_extension',
        'selected_tier': anchor['selected_tier'], 'relationship_verified': bool(related),
        'parameterization_first': True, 'training_admitted': False,
    }


def repair_selection_for_seed(manifest: dict, seed: bytes) -> list[dict]:
    """Reproduce equal-priority repair targets without changing the primary draw."""
    if manifest.get('work_policy', {}).get('schema') == PUBLIC_WORK_SCHEMA:
        from .review_public_creation import select
        return select(manifest, _seed(seed))
    primary, _ = main_selection_for_seed(manifest, seed)
    policy = manifest.get('repair_target_policy')
    ids = [primary]
    if policy is not None:
        from .review_targets import POLICY_SCHEMA, TWO_WORK_SCHEMA, ONE_WORK_SCHEMA
        schema = manifest.get('work_policy', {}).get('schema')
        two = schema == TWO_WORK_SCHEMA
        one = schema == ONE_WORK_SCHEMA
        count = 1 if one else 2 if two else 3
        pool = sorted(manifest['main_draw_policy']['ids'] if one or two else manifest['main_ids'])
        if (not isinstance(policy, dict) or policy.get('schema') != POLICY_SCHEMA or policy.get('count') != count
                or policy.get('distribution') != 'uniform_without_replacement'
                or policy.get('ids') != pool or len(pool) < count or len(set(pool)) != len(pool)):
            raise ValueError('Invalid repair target policy')
        remaining = [tid for tid in pool if tid != primary]
        for slot in range(count - 1):
            if manifest.get('main_draw_policy', {}).get('schema') == 'arcpuzzles-main-draw-policy-v5':
                ids.append(_base_priority_target(manifest, seed, excluded=ids, slot=slot+1))
                continue
            attempt = 0
            limit = (1 << 256) - ((1 << 256) % len(remaining))
            while True:
                suffix = f':repair-extra:{slot}:{attempt}'.encode('ascii')
                value = int.from_bytes(hashlib.sha256(seed + suffix).digest(), 'big')
                if value < limit:
                    break
                attempt += 1
            ids.append(remaining.pop(value % len(remaining)))
    return [{'task_id': tid, 'generator': manifest['generators'][tid]} for tid in ids]


def _independent_authoring_focus(manifest: dict, task_id: str, seed: bytes) -> dict | None:
    """An optional annotation; never redraw or reweight the selected generator."""
    policy = manifest.get('authoring_focus_policy')
    if policy is None:
        return None  # Issued v2 packets retain their original assignments.
    if (not isinstance(policy, dict) or policy.get('schema') != 'arcpuzzles-authoring-focus-policy-v1'
            or canonical_json(policy.get('probability')) != canonical_json({'numerator': 1, 'denominator': 10})
            or policy.get('target_selection') not in ({'unchanged_main_policy', 'unchanged_uniform_main'}
                if manifest.get('main_draw_policy', {}).get('schema') == 'arcpuzzles-main-draw-policy-v5'
                else {'unchanged_uniform_main'})
            or not isinstance(policy.get('anchors'), list)):
        raise ValueError('Invalid independent authoring focus policy')
    anchors = policy['anchors']
    if not anchors or int.from_bytes(hashlib.sha256(seed + b':evaluation-focus').digest(), 'big') % 10:
        return None
    anchor = anchors[int.from_bytes(hashlib.sha256(seed + b':evaluation-origin').digest(), 'big') % len(anchors)]
    if (not isinstance(anchor, dict) or anchor.get('source_split') != 'evaluation'
            or not isinstance(anchor.get('source_task_id'), str)
            or not re.fullmatch('[0-9a-f]{8}', anchor['source_task_id'])
            or not isinstance(anchor.get('challenge_sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', anchor['challenge_sha256'])
            or anchor.get('source_path') != 'shared/data/raw/arc-agi_evaluation_challenges.json'
            or not isinstance(anchor.get('main_ids'), list)
            or not all(isinstance(tid, str) for tid in anchor['main_ids'])
            or not set(anchor['main_ids']) <= set(manifest['main_ids'])):
        raise ValueError('Invalid independent authoring focus anchor')
    direct = task_id in anchor['main_ids']
    return {'schema': 'arcpuzzles-assignment-authoring-focus-v1', 'kind': 'public_evaluation',
            'probability': policy['probability'], 'source_split': 'evaluation',
            'source_task_id': anchor['source_task_id'], 'challenge_sha256': anchor['challenge_sha256'],
            'source_path': anchor['source_path'], 'mode': 'direct_related' if direct else 'inspired_extension',
            'selected_tier': anchor.get('selected_tier', 'inspired_extension'),
            'relationship_verified': direct, 'parameterization_first': True, 'training_admitted': False}


def blind_contract(manifest: dict, packet_id: str, contract: dict) -> dict:
    blind_id = blind_id_for_seed(manifest, contract["task_id"], bytes.fromhex(contract["seed"]))
    return {"schema": "arcpuzzles-blind-solve-assignment-v1", "assignment_id": contract["assignment_id"],
            "packet_id": packet_id, "task_id": blind_id, "generator": manifest["generators"][blind_id],
            "solve_kind": "blind_before_repair"}



def _sync_draw_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _draw_mkdir(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"Draw directory cannot be a symlink: {path}")
    if path.is_dir():
        return
    _draw_mkdir(path.parent)
    path.mkdir(exist_ok=True)
    _sync_draw_directory(path.parent)


@contextmanager
def _main_draw_lock(packet_root: Path, lock_name: str = "main-draw.lock"):
    # POSIX locks are released by the OS on process death; no stale lock recovery.
    review = packet_root / ".review"
    _draw_mkdir(review)
    lock = review / lock_name
    if lock.is_symlink():
        raise ValueError("Main draw lock cannot be a symlink")
    with lock.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_draw_bytes(path: Path, raw: bytes, staging: Path, *, replace=False) -> None:
    if path.is_symlink():
        raise ValueError(f"Draw output cannot be a symlink: {path}")
    if path.exists() and not replace:
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError(f"Existing draw output conflicts with pending contract: {path.name}")
        _sync_draw_directory(path.parent)
        return
    _draw_mkdir(path.parent)
    _draw_mkdir(staging)
    descriptor, name = tempfile.mkstemp(prefix="write-", dir=staging)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _sync_draw_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _copy_draw_baseline(source: Path, destination: Path, digest: str, staging: Path) -> None:
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"Invalid baseline destination: {destination}")
    if destination.is_file() and _sha(destination.read_bytes()) == digest:
        destination.chmod(0o444)
        _sync_draw_directory(destination.parent)
        return
    _draw_mkdir(destination.parent)
    _draw_mkdir(staging)
    descriptor, name = tempfile.mkstemp(prefix="copy-", dir=staging)
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copy2(source, temporary)
        if _sha(temporary.read_bytes()) != digest:
            raise ValueError(f"Packet source changed during baseline copy: {source}")
        temporary.chmod(0o444)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _sync_draw_directory(destination.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _draw_json(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def draw_main(packet_root: Path, seed: bytes | None = None) -> dict:
    packet_root = packet_root.resolve()
    with _main_draw_lock(packet_root):
        return _draw_main_locked(packet_root, seed)


def _draw_main_locked(packet_root: Path, seed: bytes | None = None) -> dict:
    packet_root = packet_root.resolve()
    contract_path = _contract_path(packet_root, "ASSIGNMENT.json")
    pending_path = packet_root / ".review/pending-main-draw.json"
    staging = packet_root / ".review/main-draw-staging"
    if pending_path.is_symlink():
        raise ValueError("Pending main draw cannot be a symlink")
    if contract_path.is_file() and not pending_path.exists():
        # Completed legacy/current draws remain idempotent after reviewer edits.
        return json.loads(contract_path.read_text())
    manifest, packet_id = load_manifest(packet_root)
    pending = None
    if pending_path.exists():
        pending = json.loads(pending_path.read_text())
        if (not isinstance(pending, dict)
                or pending.get("schema") != "arcpuzzles-pending-main-draw-v1"
                or not isinstance(pending.get("contract"), dict)):
            raise ValueError("Invalid pending main draw journal")
        saved = pending["contract"]
        if saved.get("packet_id") != packet_id:
            raise ValueError("Pending draw belongs to a different packet manifest")
        try:
            saved_seed = _seed(bytes.fromhex(saved["seed"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Invalid pending draw seed") from error
        if seed is not None and _seed(seed) != saved_seed:
            raise ValueError("Explicit seed conflicts with pending draw; resume without a new seed")
        seed = saved_seed
    else:
        existing = packet_root / ".review/baseline"
        if existing.is_symlink() or (existing.exists() and any(existing.rglob("*"))):
            raise ValueError("Unjournaled partial baseline requires explicit recovery; refusing a new draw")
    seed = _seed(seed)
    task_id, authoring_focus = main_selection_for_seed(manifest, seed)
    if authoring_focus is not None and 'authoring_focus_policy' in manifest:
        from .parametric_priority import _challenge, _digest
        public = json.loads(_verify(packet_root, manifest, 'repo/' + authoring_focus['source_path']))
        parent = public.get(authoring_focus['source_task_id'])
        if parent is None or _digest(_challenge(parent)) != authoring_focus['challenge_sha256']:
            raise ValueError('Public-evaluation authoring challenge hash changed')
    row = manifest["generators"][task_id]
    targets = repair_selection_for_seed(manifest, seed)
    paths = sorted({name for target in targets
                    for name in _base_paths(packet_root, manifest, target['task_id'])})
    baseline = {name: _sha(_verify(packet_root, manifest, name)) for name in paths}
    questions = sorted(manifest["questions"], key=lambda x: x["id"])
    question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]
    _verify(packet_root, manifest, f"repo/REVIEW/questions/{question['id']}.json")
    assignment_id = "review-" + _sha(bytes.fromhex(packet_id) + seed)[:16]
    contract = {"schema": "arcpuzzles-full-assignment-v2", "assignment_id": assignment_id,
                "packet_id": packet_id, "seed": seed.hex(), "task_id": task_id,
                "generator": row, "question": question, "baseline_sha256": baseline}
    if manifest.get('base_review_policy'):
        contract['base_review_policy'] = manifest['base_review_policy']
    if manifest.get('repair_target_policy'):
        from .review_targets import MULTI_SCHEMA
        contract['schema'] = MULTI_SCHEMA
        contract['repair_targets'] = targets
        if manifest.get('work_policy'):
            contract['work_policy'] = manifest['work_policy']
    if authoring_focus is not None:
        contract['authoring_focus'] = authoring_focus
    prepared = {"schema": "arcpuzzles-pending-main-draw-v1", "contract": contract}
    if pending is not None and pending != prepared:
        raise ValueError("Pending draw contract no longer matches the verified packet")
    # Commit the exact seed/task/question/source bindings before the first copy.
    _write_draw_bytes(pending_path, _draw_json(prepared), staging)
    baseline_root = packet_root / ".review/baseline"
    for name in paths:
        _copy_draw_baseline(packet_root / name, baseline_root / name, baseline[name], staging)
    _write_draw_bytes(contract_path, _draw_json(contract), staging)
    blind = None
    if manifest.get("reviewer_solve", {}).get("blind", {}).get("required"):
        blind = blind_contract(manifest, packet_id, contract)
        _write_draw_bytes(_contract_path(packet_root, "BLIND_ASSIGNMENT.json"),
                          _draw_json(blind), staging)
    priority = manifest.get("parametric_priority", {})
    origin = priority.get("related_generators", {}).get(task_id)
    priority_note = ""
    if origin:
        parents = ", ".join(f"{item['source_split']}:{item['source_task_id']}" for item in origin['origins'])
        priority_note = (f"\nParametric priority: supplied original ARC family {parents}. "
                         "Prioritize one or two meaningful rule parameters when missing, preserving "
                         "the original reasoning pattern and canonical default. Reuse a retained "
                         "prototype first; a thin promotion adapter, contract and focused qualification "
                         "evidence can be the main contribution. Source review, variant acceptance and "
                         "training admission remain separate.\n")
    if authoring_focus is not None:
        focus = authoring_focus
        priority_note += (
            f"\nPublic-evaluation focus (reserved 10% authoring draw): `{focus['source_task_id']}` "
            f"from `repo/{focus['source_path']}`; public challenge SHA-256 "
            f"`{focus['challenge_sha256']}`. Mode: `{focus['mode']}`.\n"
            "After the blind solve, study this public task's demonstrations and query inputs. "
            "Prioritize parameterizing its reasoning, directly improving its related generator "
            "where assigned, or using its reasoning to enhance the assigned family. Preserve "
            "the meaningful object roles, dependencies and contextual decisions; avoid reducing "
            "it to an easier shortcut or cosmetic reskin. If the canonical family cannot support "
            "the idea, retain a separate proposed extension instead of replacing its rule. "
            "Record the exact parent ID, what transferred, Racket evidence, four-query support "
            "and limits. Inspiration alone does not establish verified lineage or measured "
            "difficulty. See ARC-DESIGN.md.\n")
    edit_note = ("Editable paths within that folder: `generator.py`, `notes.md`, `SUMMARY.md`,\n"
                 "`tests/`, `workspace/`, `counterexamples/`. Task-root `test_generator_*.py`\n"
                 "is immutable; add new tests under `tests/`.\n")
    duties = f"""# Your generator assignment: {task_id}

Assignment ID: `{assignment_id}`. Work under `repo/generators/{task_id}/`.
The canonical rule is in `repo/shared/data/canonical/puzzles.jsonl` at task ID `{row['rule_task_id']}`.
{edit_note}
{priority_note}

1. Read generator.py, its current notes.md and canonical examples. Check its
   unresolved audits and focused tests. Consult referenced workspace or historical
   evidence when needed for a specific finding; do not reread every old return.
   Read `ARC-DESIGN.md` for composition distinctions and optional `RESULTS.json`
   curriculum annotations. Unknown is valid; no new rule or battery is required.
   Prior review indexes can describe pending repairs. This draw uses the pinned
   selected baseline, not an unintegrated patch; prior claims are not measurements
   of the current source. Record which prior return you used as a lead.
   Run `python3 setup_racket.py`, then a before check:
   `python3 run_with_racket.py python3 -m arcpuzzles check {task_id} --battery --timeout 4000 --phase before --out ../checks/before`
2. Improve this generator's input distribution and, if justified, its Racket rule.
   For an original-family priority draw, reuse a retained prototype or add the missing extension first,
   preserving its original object roles, relationships and reasoning structure.
   Then repair concrete canonical-distribution defects as needed.
   Assess one or two small rule parameters using `PARAMETRIC-RULES.md`.
   Where suitable, return a runnable prototype under this task's
   `workspace/parametric/`, with matching Racket and examples; choose parameters
   once per episode and show that demonstrations distinguish the chosen rule.
   Keep proposed variants separate from the selected canonical execution path.
   Report the prototype's evidence and limits, or explain why it is not suitable.
   Aim to make four query/test inputs per episode easy to request, independently
   of the demonstration count needed to identify the rule. Follow ARC-DESIGN's
   four-query guidance for production and parametric prototypes; keep one rule
   and parameter setting across all pairs, and label all four queries via Racket.
   Try `python3 run_with_racket.py python3 -m arcpuzzles generate {task_id} --count 1 --seed 17 --test 4 --out ../checks/four-query.jsonl`.
   Expose separate demo/query counts in prototypes; retain distinct-query and
   per-query lesson/rival evidence or explain a concrete support limit.
   Keep one-query rotation checks separate; no global default or battery changes.
   Edit only selected task files. Put new or improved tests under
   `repo/generators/{task_id}/tests/`; the baseline root `test_generator_*.py`
   file is a frozen fixture, not a patchable test location. Run an after check:
   `python3 run_with_racket.py python3 -m arcpuzzles check {task_id} --battery --timeout 4000 --phase after --out ../checks/after`;
   iterate and retain failures as evidence.
   Also run the selected task tests explicitly; the general battery and root
   pytest do not discover these tests automatically:
   `python3 run_with_racket.py python3 -m arcpuzzles check {task_id} --stage task_tests --timeout 600 --phase after --out ../checks/task-tests`.
   This snapshots the selected task tests and workspace, the public API, and
   retained frozen fixtures into a portable runtime, and records all copied
   source hashes. Missing tests are reported as no-tests, never a pass.
   Do not rewrite a frozen fixture to make it pass. If its portable preflight
   fails, retain the diagnostic and report completion as blocked. The library
   maintainer owns migration of that fixture for a future packet; a blocked
   inherited fixture does not turn your passing new tests into an aggregate pass.
   Battery checks now checkpoint completed stage evidence under `--out` while
   running. A running/interrupted result is not a finished aggregate pass;
   retain it separately from a completed rerun. Resume unchanged sources/settings
   with `python3 run_with_racket.py python3 -m arcpuzzles check {task_id} --battery --resume --timeout 4000 --out ../checks/after`.
   Resume verifies source/runtime/checkpoint hashes and preserves earlier attempts;
   see `repo/docs/reviewer-check-resume.md`. Changed sources need a new output.
   Keep commands, actual working directories, return codes and failed evidence.
   If no task tests exist, record that; a missing test directory is not a pass.
   After-phase blockers (passing checks never changes training approval):

   | Gate | Required after repair |
   | --- | --- |
   | lint / defect lint | No blocking errors or warnings; pin the canonical RULE_HASH. |
   | authority / rule smoke | Selected rule and canonical outputs remain bound to the declared authority. |
   | self-check / strict profile | Lawful inputs, canonical support, and the reported strict fraction. |
   | profile floor | At least 1 exact canonical-profile hit in each band (easy, medium, hard), with 20 draws per band; pooled exact support ≥5% (3/60) and pooled envelope support ≥25% (15/60). |
   | overrides | Every advertised exact control is observable and honored, or declared incompatible. |
   | semantic contract | Executable task-domain witnesses/rivals and required teaching support. |

   Exact profiles match canonical height, width, and distinct-color count
   together. Envelope hits stay within the canonical min/max of each of those
   three values; every exact hit also counts toward envelope support. The pooled
   counts above assume all 60 draws succeed. The after command uses `--strict
   --require-pass --min-band-support 1`: crashes and other strict failures block,
   and warnings block even when the per-band minimum is met.

   See `repo/generators/b90d4c3d5553/` for a retained passing example; use its
   task-specific choices as an example, not a universal shape or palette rule.
   The small battery lesson sample is a smoke check. When plausible rivals
   fit the canonical pairs, inspect at least 100 lessons per band. The shared
   source-bound census saves materialized lessons, replay seeds, rival results
   and unique-input counts, checkpointing each completed lesson:
   `python3 run_with_racket.py python3 -m arcpuzzles lesson-census {task_id} --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census.json`.
   Use a new JSON output path for each run. Partial/error results are not a pass;
   no declared rivals is not evidence of identifiability. The census uses the
   production sampler; `--rotate-query` holds out every materialized pair once
   (requires one query). It does not enumerate every possible schedule start.
   Extend task-local probes for exhaustive cyclic starts, legal joint axis support
   or undeclared plausible rivals. Report domain limits and the actual sampler;
   finite declared-rival checks do not establish universal induction.
   Training lessons should teach the intended rule: a reference-lawful plausible
   rival that fits every demonstration but predicts a different query answer is
   a teaching defect, even when every saved label is correct. Retain that exact
   lesson, rival, differing query and source hashes; repair the teaching schedule
   or resample, then show the witness is distinguished. Check query rotations
   only when the downstream assembly permits them. Two inference guesses are
   not a substitute for sufficient demonstrations in generated training data.
   Record untested ambiguity as unknown; a finite rival pass is not a proof
   that the lesson uniquely determines every possible rule.
   `repo/shared/README.md` documents the census and portable canonical-data
   helpers for authoring tests. Those helpers expose answers: never use them
   during either visible-only solve.
3. Write `REVIEW.md` with results and `DECISIONS.md` with each input choice,
   original rationale (or unknown), alternatives, probes, failure modes and limitations.
   Update `repo/generators/{task_id}/notes.md` as the concise current account:
   intended rule, assumptions, known limits, open findings and decisions. When
   reversing a decision, state the prior choice, new choice, reason and evidence
   here. Store minimal reproducible counterexamples in that generator's
   `counterexamples/` and cover them with focused tests. Use shared helpers for
   common sampling/runtime logic; do not copy entire review logs into notes.
4. Answer question `{question['id']}` in `QUESTION_ANSWER.md`. Read its exact text in
   `repo/REVIEW/questions/{question['id']}.json`.
5. Write general tooling or process feedback in `FEEDBACK_TO_CODEX.md`.
   Use `F1:`, `F2:`, etc. for distinct items, with a symptom or example and
   suggested change. Include one small **Randomized allocation and data-quality
   audit**, using assignment-derived seed `{hashlib.sha256(seed + b":allocation-audit").hexdigest()}`.
   With Python `random.Random(int(audit_seed, 16))`, sample up to three IDs from
   the sorted generator IDs in `PACKET-MANIFEST.json`. Inspect those current
   generator/evidence records and the actual manifest pools, draw policy/focus,
   catalog weights and `repo/src/arcpuzzles/review_full_draw.py`; distinguish
   authoring draw probabilities from dataset sampling weights. Assess whether
   the allocation efficiently produces high-quality data: representation,
   teachability, parameter coverage and four-query supervision versus review,
   Racket execution and deduplication cost. Inspect retained source-specific
   linter findings/rejections, repair cost,
   lesson ambiguity and grammar coverage, including ARC-GEN or RE-ARC where
   sampled. External or internal provenance alone guarantees no quality;
   do not recommend more source volume without checking this evidence.
   Compare at least one concrete alternative allocation by expected quality
   per cost; label estimates and
   propose a bounded test with a stopping rule. Record the seed, sampled IDs,
   exact source/evidence paths, observations and coverage limits under an F item.
   Use existing evidence; do not launch expensive corpus-wide reruns or model
   jobs. This audit proposes changes; it changes no draw policy, approval or
   training admission. See `PARAMETRIC-RULES.md` for scope.
   The included generator linter runs in the check battery;
   run it alone with
   `python3 run_with_racket.py python3 -m arcpuzzles check {task_id} --stage lint --phase after --out ../checks/lint`.
   Optional feedback on false alarms, missed defects, or usability is welcome.
6. After the generator work, run `python3 assignment.py audit` once. This assigns two distinct
   random adversarial reviews. They can target finished or unfinished generators.
   Write `AUDIT.md` with one `## TASK_ID` section for each target. Give a concrete
   counterexample or possible shortcut, or say `No issue found` after checking.
   Intake keeps each actionable section in its audited generator's evidence/review_index.json,
   bound to the audited source hash. Audits do not approve repairs. Put reproduction
   files in the return and reference their exact paths in the relevant audit section.
   No fix is required for these two audits.
   For optional isolated checks, replace AUDIT_ID with the drawn target and run
   `python3 run_with_racket.py python3 -m arcpuzzles check AUDIT_ID --stage task_tests --phase audit --out ../checks/audit/AUDIT_ID-task-tests`.
   The audit phase retains that target and source snapshot; it uses strict check
   policy and does not approve the generator or close a finding.
7. Read `RETURN-GUIDE.md`. Record exact verification commands and their working
   directories in `RESULTS.json`, alongside completion state and stopping reason.
   Keep unsupported claims and unverified audit suspicions explicit. Then run
   `python3 package_return.py --out review_response_{assignment_id}.zip`.
   The builder automatically creates a hash-bound `INTAKE.json` summary; do not
   hand-write it. Return only the resulting small ZIP, with notes and evidence.

The draw and baseline are immutable. Rerunning `assignment.py` prints these duties.
"""
    if manifest.get("supplementary_ticket_policy"):
        duties = f"""# Your generator assignment: {task_id}

Assignment ID: `{assignment_id}`. Work under `repo/generators/{task_id}/`.
Canonical rule: `repo/shared/data/canonical/puzzles.jsonl`, task `{row['rule_task_id']}`.
{edit_note}
{priority_note}

1. Read this generator, current notes, canonical examples and relevant open findings.
   Finish any assigned blind solve first. Main shortcut/teaching assessment belongs
   in this repair, not a separate mandatory question essay. Consult ARC-DESIGN.md
   and PARAMETRIC-RULES.md where relevant; do not reread unrelated historical logs.
2. Work on this generator's concrete repair or small parametric extension.
   Reuse a useful retained prototype; making its adapter/contract ready for fresh
   qualification is a valid main improvement. Owner acceptance stays separate.
   Verify only what you changed. A prototype/tests/notes-only change does not
   require a production before/after battery, unrelated authority checks or frozen
   fixture migration. For changed generator/rule behavior, run relevant focused
   tests and execute matching Racket on representative changed behavior, boundary
   inputs and a new lesson; check plausible rivals where teaching changed.
   Keep the original canonical rule and proposed variants separate. For a
   parameter prototype, fix one setting per episode and retain its matching
   Racket, identifiable demos and four distinct queries when supported. Expose
   demo/query counts separately; document actual limits instead of cloning pairs.
   Use `python3 setup_racket.py` and `python3 run_with_racket.py COMMAND ...`.
   Retain exact commands, hashes, failures and what was actually exercised.
   A full production battery or large census is optional escalation for a
   concrete edited-scope concern, never automatic baseline or peer busywork.
   Unchanged scopes may be `not_applicable`; unrun checks are `not_run`, never pass.
   Edit only selected task files; frozen fixtures remain unchanged. If a relevant
   wrapper is blocked, retain its diagnostic and exercise authored tests separately;
   separate success does not establish a passing aggregate.
   For code/prototype edits, use up to five minutes for an adversarial pass over
   the artifact you built. Pick two relevant surfaces: sampler boundaries and
   retry schedules; parameter/Racket parity; public/private export and numeric
   types; lesson-certificate rivals; or verifier rejection paths. Prefer a fresh
   independent reader when available. Retain a concrete edge case, regression or
   bounded no-finding result in the existing command records and repair brief.
   Stop at the budget and state unresolved limits; no extra essay is required.
3. Write `REVIEW.md` with the concrete change, scoped checks and unresolved limits.
   `DECISIONS.md` is optional for a useful tradeoff not already in current notes.
   Update concise current task notes and minimal
   counterexamples/tests. Keep source/Racket identities exact. No approval or
   training admission follows merely from packaging or a proposed variant.
4. `QUESTION_ANSWER.md` is optional. Fold a relevant shortcut answer into the
   main semantic evidence; do not write a broad data-value essay by default.
5. General tooling feedback is optional. If useful, write actionable `F1:`, `F2:`
   items in `FEEDBACK_TO_CODEX.md`. Do not perform a universal allocation audit;
   do that work only if selected as a ticket.
6. Run `python3 assignment.py tickets` once after generator work (`audit` is an
   alias). Complete only the two selected bounded tickets in `TICKETS.md`.
   Each has ten authoring minutes and one targeted probe of at most 120 seconds;
   blocked/unknown is valid. Do not run full peer batteries or large censuses.
   Store structured rows in `RESULTS.json` under `supplementary_tickets`, including
   ticket ID/type/status/summary/evidence_paths/elapsed_minutes (null if unknown).
   Only real peer safety findings belong in `AUDIT.md`; parameter/tool/allocation
   support observations go to the ticket's stated consumer through feedback.
7. As a quick last step, name the biggest avoidable friction point and one concrete
   mitigation in 1–2 sentences in `FEEDBACK_TO_CODEX.md`, using an F heading titled
   `Biggest avoidable friction: ...`. Reuse an existing item if it already covers it.
   If nothing stood out, write `No avoidable friction identified.` without an F heading.
   No extra probe, timing study or report. Read RETURN-GUIDE.md, then run
   `python3 package_return.py --out review_response_{assignment_id}.zip`.
   Return ONLY the delta: source.patch plus compact evidence from work you did,
   concise docs and useful solves. No full checkout, original packet, Racket,
   environment or copied runtime trees. Do not invent unrelated inventories or
   passing checks. Use `RESULTS.json` for actual commands, stopping reason and
   optional `work_scope` verification statuses. The builder preserves source and
   patch hashes and omits copied transport/runtime material.

The draw and baseline remain immutable. Rerunning the assignment resumes it.
"""
    if manifest.get('repair_target_policy'):
        homes = '\n'.join(f"- `{target['task_id']}`: `repo/generators/{target['task_id']}/`; "
            f"canonical rule `{target['generator']['rule_task_id']}`." for target in targets)
        duties = f"""# Your three generator repairs

Assignment ID: `{assignment_id}`. All three targets have equal priority, drawn
uniformly without replacement from the same packet pool. Work only in these homes:
{homes}

Editable files in each home: `generator.py`, `notes.md`, `SUMMARY.md`,
`tests/`, `workspace/`, `counterexamples/`. Issued task-root test files are frozen.
Only the three bound canonical rows and task-bound base authorities may change.

1. Read each assigned generator's current source, notes, examples and relevant
   findings. Finish any assigned blind solve first. Do not read unrelated history.
2. Repair or improve each target where useful. A focused parameter prototype,
   unchanged finding or blocked result is honest work; do not invent a fix.
   Keep variants separate from production. Run only checks relevant to changes:
   focused task tests and matching Racket labels for changed generator/rule behavior.
   Use `python3 setup_racket.py`, then `python3 run_with_racket.py COMMAND ...`.
   Supply the exact target ID to checks and use separate `../checks/TASK/...` paths.
   Large batteries/censuses are optional for a concrete concern, never routine.
   For code/prototype edits, spend up to five minutes on two relevant edge surfaces;
   retain one compact regression, counterexample or bounded no-finding result.
3. Record one row per target in `RESULTS.json` under `repair_targets`: `task_id`,
   `outcome` (`repaired`, `prototype`, `unchanged`, or `blocked`), nonempty `summary`,
   `changed_components` (from `generator`, `racket`, `tests_notes`), `evidence_paths`,
   and `remaining_failures`. Empty lists are valid. Report actual commands and
   source/rule hashes; unrun checks remain unrun. Packaging grants no approval.
4. Write `REVIEW.md` with concise target-specific changes, checks and limitations.
   Keep current decisions in each target's notes. `DECISIONS.md` and
   `QUESTION_ANSWER.md` are optional; no additional narrative is required.
5. Name the biggest avoidable friction and one mitigation briefly in
   `FEEDBACK_TO_CODEX.md`; none is valid. Package one source delta with compact
   evidence using `python3 package_return.py --out review_response_{assignment_id}.zip`.
   Return only that ZIP, never the checkout, environments or runtime copies.

There are no required supplementary audits or tickets. An optional spot check
never substitutes for an assigned repair. The draw and all three frozen baselines
are immutable; rerunning the assignment resumes the same work.
"""
        if manifest.get('work_policy'):
            primary = targets[0]['task_id']
            peers = ', '.join(f"`{r['task_id']}`" for r in targets[1:])
            parametric_checklist = """   Read `PARAMETRIC-RULES.md` and start with any existing task-local prototype.
   For rule ideas, scan `PARAMETRIC-EXAMPLES.md`: order swaps, input-derived
   selectors/colors, exceptions, triggers and constrained routes. Choose a
   useful nearby variant; this menu adds no extra assignment.
   Prefer the existing native adapter/promotion contract and manifest helper;
   keep one source of execution evidence instead of duplicate hand-made inventories.
   Read the relevant guidance in `ARC-DESIGN.md`: preserve the source task's
   reasoning and favor meaningful sequential state dependencies where suitable.
   Spend most effort on one meaningful rule parameter, episode-fixed settings,
   matching executed Racket rules and reliable demonstration/query generation.
   Preserve the canonical default. Support independent demonstration/query counts
   with 2–6demonstrations across supported families and always four distinct
   novel queries. Center ordinary demo counts near3(the provided public-eval
   spread is2:34,3:62,4:17,5:6,6:1tasks). Do not generate more than six demos.
   Store four controller-side queries for the existing consumer's sequential
   reveal: one query per user turn, no total-count hints or future inputs, and
   the same first-turn content as single-query use. Do not build a training loop
   or turn controller; document/check the export projection with existing helpers.
   Keep private settings, programs
   and query answers out of public challenges; hash only public bytes for IDs.
   Spend up to five minutes on two edge surfaces relevant to what changed (for example count/retry
   boundaries, coverage, export or verifier rejection). Do not turn that menu
   into another exhaustive battery. Keep a small Racket-backed four-query example
   for each demonstrated setting and its demonstration-only teaching check.
   Usable parametric episodes come before scalar-only fixes or more green logs.
   Fix observed failures in this artifact before starting another enhancement.
   Stress minimum and maximum supported sizes, including 30x30 wherever lawful.
   Execute those labels through Racket. Exercise real content spread, density,
   boundary contacts and distractors, rather than merely padding a small puzzle.
   If the canonical domain cannot reach 30x30, record why and extend only the
   separate parametric family when its semantics naturally support that size.
   Prefer constructive distinguishing demonstrations to merely rejecting many draws.
   Repair demonstrated teaching holes in the supported demo/query assembly;
   check rotations when the family explicitly supports them, not as a global duty.
   Do not defer a relevant repair for permission
   about demonstration cost. First strengthen or select demonstrations without
   increasing their count; increase it when needed and report the cost plainly.
   Keep the puzzle demanding through causal multi-step reasoning and robust
   generalization. Do not make it easier by removing meaningful rule branches.
   Retain a bounded success/failure rate for the exercised settings/counts; do not
   substitute a large test count for reliable usable episodes. Provide the native
   adapter/contract and source-bound inventory when ready for owner qualification.
   A genuine blocker is valid: record it and the next concrete repair, without
   pretending a canonical-only fix completes the parametric duty."""
            duties = f"""# MAIN: robust parametric generator; two bounded robustness checks

Assignment: `{assignment_id}`. Effort split: **70% / 15% / 15%**.
Targets are drawn uniformly without replacement; their work roles differ.

1. **70% — MAIN `{primary}`: build or improve its parametric version.**
{parametric_checklist}
2. **15% each — robustness checks on {peers}.** Inspect one likely hole in each
   generator's existing controls, validation, labels or teaching distribution.
   Run one bounded relevant probe. Fix an obvious local hole and its regression
   when feasible; otherwise retain a minimal source-bound finding or no-finding
   result. Do not build or repair parametric variants for the two secondary targets.
   Do not run their full batteries or turn these checks into new major projects.
3. Work only in these three homes:
{homes}
   Editable: `generator.py`, `notes.md`, `SUMMARY.md`, `tests/`, `workspace/`,
   `counterexamples/`. Issued root tests remain frozen. Only assigned canonical
   rows and bound base authorities may change. Use the bundled Racket setup and
   focused changed-scope checks, with evidence in separate `../checks/TASK/` paths.
4. Record one row per target under `RESULTS.json` → `repair_targets`: `task_id`,
   `outcome` (`repaired`, `prototype`, `unchanged`, `blocked`), nonempty `summary`,
   `changed_components`, `evidence_paths`, `remaining_failures`. The main row also
   requires `parametric_work`: `status` (`built`, `improved`, `blocked`), `summary`,
   `prototype_path` (`repo/generators/{primary}/workspace/parametric/` or null for
   blocked). This is a deliverable record, not semantic certification or approval.
5. Write a short target-specific `REVIEW.md`; keep decisions in each task's notes.
   Name the biggest avoidable friction briefly in `FEEDBACK_TO_CODEX.md`.
   Package only one source delta and compact evidence with `package_return.py`.
   No extra audit tickets, implementation diary or unrelated checks are required.

The 70/15/15 split guides effort; it is not a stopwatch or another reporting duty.
The draw and baselines are immutable. Proposed variants require separate owner
qualification/acceptance and are not automatically admitted to training.
"""
        if manifest.get('work_policy', {}).get('schema') == 'arcpuzzles-three-parametric-targets-v1':
            all_targets = ', '.join(f"`{r['task_id']}`" for r in targets)
            duties = f"""# Three robust parametric generators

Assignment: `{assignment_id}`. Apply the full parametric checklist to all three
uniformly drawn targets: {all_targets}. Each has the same deliverable requirements;
there is no main/peer effort split. Finish one usable artifact before the next.

1. **Build or improve the parametric version of each assigned generator.**
{parametric_checklist}
2. **Make a bounded adversarial pass on your own changes for each target.**
   Within the relevant-surface check budget above, deliberately try to break its
   teaching evidence, sampler boundaries, Racket labels, or serialized export.
   Choose cases likely to expose a real hole, not another broad battery. Fix an
   observed defect, keep its minimal regression and record the final result. A
   no-defect result is valid when it states exactly what was attempted; do not
   invent failures or count a hash check as a semantic audit. No separate audit
   diary or mandatory independent-agent review is required.
3. Work only in these three homes:
{homes}
   Editable: `generator.py`, `notes.md`, `SUMMARY.md`, `tests/`, `workspace/`,
   `counterexamples/`. Issued root tests remain frozen. Only assigned canonical
   rows and bound base authorities may change. Fix obvious canonical defects
   encountered in these homes, keeping variants separate from canonical authority.
   Use the bundled Racket setup and focused changed-scope checks, with evidence
   in separate `../checks/TASK/` paths. Do not rerun unrelated or unchanged suites.
4. Record one row per target under `RESULTS.json` → `repair_targets`: `task_id`,
   `outcome` (`repaired`, `prototype`, `unchanged`, `blocked`), nonempty `summary`,
   `changed_components`, `evidence_paths`, `remaining_failures`. Every row requires
   `parametric_work`: `status` (`built`, `improved`, `blocked`), concrete `summary`,
   and `prototype_path` in its own `repo/generators/TASK/workspace/parametric/`,
   or null for blocked work. A canonical-only repair does not complete that
   target's parametric duty. State genuine blockers and useful completed work.
   This record is not semantic certification, qualification or training admission.
5. Write a short target-specific `REVIEW.md`; keep decisions in each task's notes.
   Cite the bounded self-review result in the existing result/evidence record.
   Name the biggest avoidable friction briefly in `FEEDBACK_TO_CODEX.md`.
   Package only one source delta and compact evidence with `package_return.py`.
   No extra audit tickets, implementation diary or unrelated checks are required.

The draw and baselines are immutable. Proposed variants require separate owner
qualification/acceptance and are not automatically admitted to training.
"""
    if manifest.get('work_policy', {}).get('schema') == 'arcpuzzles-parametric-main-admission-v1':
        parametric_checklist = parametric_checklist.replace(
            'favor meaningful sequential state dependencies where suitable',
            'require a real input-dependent A-to-B sequential dependency')
        duties = f"""# MAIN first: one accepted usable parametric generator

Assignment: `{assignment_id}`. Finish MAIN `{primary}` before spending remaining
 time on optional helpful work in {peers}, such as bounded adversarial checks.
Order: strong MAIN -> visible-demo/query shortcut and ambiguity self-audit ->
fix findings -> native qualification and owner acceptance -> optional others.
The reviewer prepares qualification; exact-source acceptance is the owner handoff.
There is no peer quota or percentage split.
Time and compute are limited: maximize usable accepted data per reviewer hour
and per training hour. Reuse tools/evidence, check changed behavior, then move
on when MAIN meets the gate; avoid repeated unchanged checks and paperwork.
The main was drawn uniformly from included canonical-approved generators without
current native parametric acceptance; peers come from the remaining included pool.
Eligibility and exclusions are frozen in the manifest. No hidden rerolls.

1. **Nail the MAIN native parametric deliverable.**
{parametric_checklist}
   This is the one-shot best-effort build: finish it now; do not rely on another
   author to remake its parametric design. Later rounds may audit real errors.
   REQUIRED sequential dependency: name A, its input-dependent intermediate,
   and B that consumes that result. B cannot be chosen before A's result.
   Mere code order, cosmetic composition and a collapsing remap-then-paint do
   not count. For example, ray first-hit object -> its size -> next fill choice.
   Preserve the exact canonical default: demonstrate its existing dependency,
   or add a non-collapsing composed rule in an alternative parameter setting.
   Keep one bounded protected-Racket witness showing skip-A, wrong-intermediate
   or wrong-order changes final output. Name the actual programs, input, setting,
   intermediate and outputs in existing main check evidence; no new diary/battery.
   BEFORE optional peers, adversarially review MAIN itself for learnability:
   can a plausible wrong rule fit every visible demonstration yet disagree on
   a query? Test relevant shortcuts and ambiguity, fix findings, and retain a
   minimal Racket-labeled case in existing teaching/self-review evidence. A
   no-issue result covers only the finite tested rivals, not universal uniqueness.
   Reuse the bounded self-review and causal witness; no new report or battery.
   Native `adapter.py`, `promotion.json`, source-bound `evidence/manifest.json`
   and a passing native `qualification.json` with sibling `execution.json` are
   required for a complete return. Follow `repo/docs/parametric-promotion.md`.
   Run `python3 run_with_racket.py python3 -m arcpuzzles parametric qualify {primary} --out ../checks/{primary}/qualification --summary`.
   This is the main deliverable's qualification, not an unrelated battery.
   Fix failures before moving on. A proposed or canonical-only repair is incomplete.
2. **Optional help comes last, only with remaining time, in {peers}.**
   Historical returns generally leave time for about two small reviews; one to
   three is a normal range, overwhelmingly two. A complex MAIN may need most or
   all of the time. This is planning guidance, not a quota. Focus on
   learnability: can a plausible wrong rule fit all visible demos yet disagree
   on a query? If so explain the shortcut/ambiguity and retain a minimal
   Racket-labeled case. No issue means only the finite rivals tested.
   Comment or directly fix whichever is easier. Explain what seemed broken and
   why (shortcut, ambiguity, unlearnability, label or control defect), with a
   small source-bound case. A bounded probe may support it; unverified is honest. If no time remains, say unrun honestly.
   No parametric duty, required completion or full battery for either peer.
   Peer work may remain unverified and useful; the owner retains it as a proposal
   unless explicitly selecting checked integration.
   If you already have two executable rules that fit the same demonstrations
   but disagree on a query, retain that original lesson for the optional
   alternative-answer stream (repo/docs/datasets.md, "Find another valid solution").
   This adds no search or required task; repaired lessons keep their normal labels.
3. Work only in the three assigned homes:
{homes}
   Edit assigned generator/rule, notes, tests, workspace and counterexamples only.
   Keep labels/settings/private queries out of model-visible challenges.
4. Keep one row per target in `RESULTS.json` → `repair_targets` with outcome,
   summary, changed_components, evidence_paths and remaining_failures. MAIN alone
   needs `parametric_work`: status `ready` or `blocked`, concrete summary,
   prototype_path, promotion_path, inventory_path and qualification_path.
   Also include sequential_dependency: step_a, intermediate, step_b,
   why_b_depends_on_a, witness_path (packaged checks/... JSON; see PARAMETRIC-RULES).
   Source paths start `repo/generators/{primary}/workspace/parametric/`;
   qualification_path is `checks/{primary}/qualification/qualification.json`.
   For blocked work use null prototype_path and record the next concrete repair;
   completion_state must remain blocked or in_progress. Peer unrun is honest.
5. Package the delta, native source/inventory and qualification/execution evidence.
   Keep a short `REVIEW.md` and `FEEDBACK_TO_CODEX.md`; no extra diary.
   Reviewer `ready` means owner admission pending, never accepted. After source
   integration and canonical approval, the owner MUST run native qualification
   and fresh acceptance on exact live bytes. Only native accepted status meets
   this round's objective. Failures stay in a concrete main repair queue.

The goal is at least one APPROVED usable parametric generator per round. A real
blocker is retained honestly and leaves that goal unmet. No training activation.
Older issued packets retain their original policies and draw probabilities.
"""
    if manifest.get('work_policy', {}).get('schema') == 'arcpuzzles-one-parametric-admission-v1':
        primary = targets[0]['task_id']
        duties = f"""# One robust parametric generator — deep adversarial review

Assignment: `{assignment_id}`. Your only target is `{primary}`.
No peer reviews, second build, audit tickets or extra solves are assigned.
Spend the saved effort making this one artifact substantially harder to break.

1. **Build the complete native parametric family.**
   Read its source, current notes and relevant findings, then check and repair
   the base's original labels, ordinary generation and controls. Draws use the
   unapproved built-generator pool; an old label is not proof of correctness.
{parametric_checklist}
   Preserve the exact canonical default, matched inputs across episode-fixed
   settings, and a real A -> input-dependent intermediate -> B dependency.
   Keep a protected-Racket counterfactual where changing/skipping A changes B's
   final output. Cosmetic composition and a collapsing remap do not suffice.

2. **Deep adversarial self-review — make a serious attempt to break your own work.**
   Treat the first passing probe as the start of this phase, not its finish.
   Spend most discretionary effort here. Follow PARAMETRIC-RULES.md and attack
   the actual reasoning, not only distinctions between your declared settings:
   - Try plausible bypasses: fixed position/motif/rank, counts or frequencies,
     color shortcuts, wrong connectivity/order, and a partial intermediate.
     Choose attacks relevant to this rule; do not pad a universal checklist.
   - Use crossed controls: vary the intended intermediate at fixed dimensions
     and profile positions; vary those nuisance features at a fixed intermediate.
     Look for a wrong rule fitting ALL demos yet changing any query answer.
   - Attack the smallest promised lesson across fresh seeds and semantic branches.
     Vary meaningful geometry, roles, topology, ties and decoys; qualification's
     fixed shapes do not cover your sampler's declared domain.
   - Probe relevant minimum/maximum dimensions, count corners and degenerates;
     stress substantive 30x30 scenes where mathematically lawful. Exercise thin,
     rotated or boundary-touching cases when they challenge this rule.
   - Try to fool authored certificates and saved exporters with wrong counts,
     duplicate inputs, malformed numeric/grid types, stale source or programs,
     forged certificates and private/future-query leakage where applicable.
   Retain the smallest useful failing input and focused regression. Fix the cause,
   rerun the failed attack, then try a different failure mechanism. Repeat while
   useful work remains; extra settings or huge green logs do not replace this.
   If a known shortcut remains, repair the lesson or enforce an honest minimum
   within 2–6. Never report a known ambiguous minimum as ready. Keep unresolved
   defects explicit. Finite no-finding results are not universal uniqueness.

3. **Refresh evidence on final bytes and qualify the declared minimum.**
   Use focused changed-scope checks and matching protected Racket. Reuse existing
   evidence; no new report file, fixed seed quota or unrelated full battery.
   Create the native inventory after actual tests/self-review, before preflight:
   `python3 run_with_racket.py python3 -m arcpuzzles parametric manifest {primary} --evidence generators/{primary}/workspace/parametric/evidence --reported-checks 'ACTUAL_CHECKS'`.
   Then run `python3 run_with_racket.py python3 -m arcpuzzles.review_base_preflight {primary} --out ../checks/{primary}/qualification`.
   This authoring preflight writes qualification.json plus execution.json; use
   --qualification with witness/preview helpers. It is not owner acceptance.
   Preserve four distinct queries, randomized privately and shown one at a time
   after each answer, without future inputs, turn indices or a total-count hint.

4. **Return one compact source delta for this one assigned home.**
{homes}
   RESULTS.json has exactly one repair_targets row with outcome, summary,
   changed_components, evidence_paths, remaining_failures and parametric_work.
   Native ready requires adapter.py, promotion.json, current evidence/manifest.json,
   qualification_path plus sibling execution.json, and sequential_dependency:
   step_a, intermediate, step_b, why_b_depends_on_a, witness_path.
   Include the source-bound causal witness and qualification in evidence_paths.
   Use ready only when the artifact is complete; a genuine blocker stays blocked
   or in_progress. Put pending owner acceptance/training in status and limits,
   while preserving real unresolved failures. Never edit approval flags.
   Keep REVIEW.md short: explain attacks, actual findings/repairs and finite limits.
   Name the biggest avoidable friction briefly in FEEDBACK_TO_CODEX.md.
   Package only source.patch and useful compact evidence; no checkout/runtime.

The owner reviews the exact source, runs native qualification and fresh acceptance.
Only one actually accepted family meets this round's objective. Training admission
remains separate. Older issued packets retain their original counts and duties.
"""
    if manifest.get('work_policy', {}).get('schema') == 'arcpuzzles-two-parametric-admissions-v1':
        wide = bool(manifest.get('base_review_policy'))
        command = 'python3 -m arcpuzzles.review_base_preflight' if wide else 'python3 -m arcpuzzles parametric qualify'
        qualifications = '\n'.join(
            f'   `python3 run_with_racket.py {command} {t["task_id"]} '
            f'--out ../checks/{t["task_id"]}/qualification' + ('`' if wide else ' --summary`') for t in targets)
        unapproved_only = manifest.get('main_draw_policy', {}).get('target_scope') == 'unapproved_only'
        pool_description = ('included bases needing repair or first approval, without current native parametric acceptance' if unapproved_only else
                            'the whole included built-generator pool, approved or unapproved, without current native parametric acceptance'
                            if wide else 'included canonical-approved generators without current native parametric acceptance')
        draw_description = ('Both slots draw only unapproved bases, uniformly without replacement. Approved bases are not assignment targets.'
                            if unapproved_only else
                            'New version-5 draws choose unapproved versus approved bases at 4:1 (80%/20%),\nuniformly within each group. If a group is exhausted, use the other group.')
        base_duty = ('''   Reuse the existing generator and Racket rule. Check its original labels,
   ordinary generation, controls, learnability and plausible shortcuts; repair
   holes rather than trusting its old owner label. Preserve the canonical default
   unless a concrete rule defect needs an explicitly documented correction.
   The shared authoring preflight checks base originals, two ordinary staged
   draws (None and medium difficulty), then every parametric setting. It does
   not grant approval or require an already-approved base. Keep the resulting
   qualification.json path for existing witness and preview-public helpers;
   the receipt explicitly says authoring preflight, never owner qualification.
''' if wide else '')
        duties = f"""# Two accepted robust parametric generators

Assignment: `{assignment_id}`. Both targets have the full parametric duty.
Finish and adversarially self-review one usable build before starting the next.
There are no assigned peer reviews, audit tickets or extra solves. Independent
cross-generator reviews are deferred to later rounds; self-review is still required.
Both targets are drawn without replacement from {pool_description}.
{draw_description}
No hidden rerolls. Maximize distinct base-rule coverage before revisiting accepted families.

1. **Build the full native parametric version of each target.**
{base_duty}\
{parametric_checklist}
   Each must preserve the exact canonical default, have meaningful episode-fixed
   variants, and include a real input-dependent A -> intermediate -> B dependency.
   B must consume A's result. Keep a bounded protected-Racket counterfactual
   showing that skip-A, wrong-intermediate or wrong-order changes final output.
   Name step_a, intermediate, step_b, why_b_depends_on_a and witness_path in each
   target's sequential_dependency record; reuse existing evidence, not a new diary.
2. **Adversarial self-review and repair for each build, before moving on.**
   First attack the claimed intermediate: can dimensions, profile position or
   a fixed motif replace A while fitting all demos and changing a query answer?
   Cross controls to separate the intermediate from that shortcut. Then probe
   the declared minimum lesson and relevant size/tie/degenerate or certificate
   boundaries; comparing only your parameter settings is insufficient.
   Follow the short recommended order in PARAMETRIC-RULES.md. Fix the cause,
   retain a minimal Racket-labeled counterexample and focused regression, and
   recheck current bytes. Reuse existing evidence; no new checklist/report file.
   A finite no-finding result is honest; it does not prove universal uniqueness.
   Keep the full robustness standard for both; do not replace the second build
   with a scalar fix, an audit, or a proposed-only settings list.
3. **Qualify both native deliverables.** Each needs its own adapter.py,
   promotion.json, current evidence/manifest.json, passing qualification.json
   with sibling execution.json, and source-bound causal witness. Commands:
   Create the source inventory first from your actual focused-test/self-audit
   evidence; PARAMETRIC-RULES.md gives the guarded manifest command. Do not wait
   for qualification receipts to create its prerequisite inventory.
{qualifications}
   For a whole-pool assignment these are explicit unapproved authoring checks;
   native owner qualification still happens after source review and integration.
   Fix failures in the artifact before moving on. Use focused changed-scope
   checks; do not run unrelated batteries or increase paperwork to fill time.
4. Work only in these two assigned homes:
{homes}
   Keep settings, rules, seeds, query answers and future queries private. Each
   target declares its smallest supported demonstration count within 2–6; a
   narrower minimum such as 4–6 is allowed when fewer examples remain ambiguous.
   Repair teaching examples first, then qualify the declared minimum. Always
   retain four distinct novel controller-side queries, projected one at a time
   with no total-count hint. Stress 30x30 when lawful,
   with substantial content, and record domain limits honestly.
5. Record both targets in RESULTS.json repair_targets: task_id, outcome, summary,
   changed_components, evidence_paths, remaining_failures and parametric_work.
   Each parametric_work needs status ready/blocked, summary, prototype_path,
   promotion_path, inventory_path, qualification_path and sequential_dependency.
   Source paths must belong to that target's repo/generators/TASK/workspace/parametric/.
   Include each qualification and witness in that target's evidence_paths.
   Report repaired when base source changed; use prototype when the reviewed
   base needed no change and you added its full family. Record concrete remaining
   failures. Put normal pending owner acceptance or training admission in status
   and limits, not remaining_failures; preserve every actual unresolved failure.
   Do not edit catalog approval flags or claim owner acceptance.
   A complete return requires both ready. A genuine blocker leaves completion_state
   blocked or in_progress; preserve any finished first build rather than hiding it.
6. Package one compact delta with short REVIEW.md and FEEDBACK_TO_CODEX.md.
   The owner runs the existing native qualification and fresh acceptance separately
   on both exact integrated sources. The round succeeds only when BOTH are accepted.
   One accepted target and one blocked target is partial progress, never completion.
   No training admission follows automatically.

Older issued packets keep their original policies, target counts and seed identities.
"""
    if manifest.get('work_policy', {}).get('schema') == PUBLIC_WORK_SCHEMA:
        from .review_public_creation import duties as creation_duties
        duties = creation_duties(contract)
    if manifest.get("reviewer_solve", {}).get("required"):
        solve_duty = """3. After improving the generator, attempt a fresh puzzle from its visible examples:
   `python3 solve_episode.py prepare`
   Preparation displays visible examples with dimensions before every grid; the same
   labelled presentation is in `solve/README.md`, derived from `solve/challenge.json`.
   Write Python `solve(grid)` in `solve/solution.py`.
   **DO NOT consult the Racket rule while solving.** Also keep the generator code,
   reference solutions, private labels, and previous solution explanations closed.
   Racket is used automatically by the preparation tool; do not open its rule source.
   Record hypotheses, experiments, failed ideas, and reasons for changes in
   `solve/SOLVE_NOTES.md`. Check each revision with:
   `python3 solve_episode.py check --intent solve --note 'Hypothesis, probe, and reason for this revision'`
   Use `--intent teaching_negative` only for a deliberately wrong teaching
   example and `--intent diagnostic_probe` for a deliberate diagnostic. Do not
   invent failures; an accidental failed solution attempt still has intent solve.
   This gives visible-example and execution feedback only; masked-query correctness
   is withheld for independent maintainer scoring after you return the ZIP.
   Iterate, then record prior exposure honestly and whether you consulted a reference:
   `python3 solve_episode.py finish --earlier-exposure yes --reference-consulted no --reason 'Why I stopped'`
   Choose yes/no/unknown for earlier exposure. Wrong or blocked solves are useful;
   preserve them. Do not claim this is blind if you saw the rule during generator work.
   Finish freezes `solve/FINISHED_NOTES.md` and its hash. Keep every revision's
   original notes and this final snapshot; later edits are not that finish record.
"""
        for number in range(7, 2, -1):
            duties = duties.replace(f"\n{number}. ", f"\n{number + 1}. ")
        if manifest.get('repair_target_policy'):
            marker = '\n4. Work only' if manifest.get('work_policy') else '\n4. Record one row'
            duties = duties.replace(marker, "\n" + solve_duty + marker.lstrip('\n'))
        else:
            duties = duties.replace("\n4. Write `REVIEW.md`", "\n" + solve_duty + "4. Write `REVIEW.md`")
    if blind:
        blind_duty = f"""0. **Blind solve first, before opening anything else.** Task `{blind['task_id']}` was
   drawn for you; it is not your repair or audit target. Do not open its generator,
   rule, notes, solutions or audit records, or your own generator, before finishing:
   `python3 solve_episode.py blind prepare`
   Preparation displays visible examples with dimensions before every grid; read the
   same public presentation in `solve-blind/README.md` or `solve-blind/challenge.json`.
   Write `solve(grid)` in `solve-blind/solution.py`,
   keep a work log in `solve-blind/SOLVE_NOTES.md`, and check each revision with
   `python3 solve_episode.py blind check --intent solve --note 'Hypothesis and reason'`.
   Finish with `python3 solve_episode.py blind finish --earlier-exposure no --reference-consulted no --reason 'Why I stopped'`
   (use yes/unknown honestly). Wrong or blocked blind solves are useful; keep them.
   This record stays separate from the later, exposed post-repair solve.
"""
        before, marker, after = duties.partition("\n1. ")
        if not marker:
            raise ValueError("Cannot insert the required blind-solve duty before the first repair step")
        duties = before + "\n" + blind_duty + "1. " + after
    _write_draw_bytes(packet_root / "DUTIES.md", duties.encode("utf-8"), staging, replace=True)
    results_path = packet_root / "RESULTS.json"
    if not results_path.exists():
        initial_results = {"completion_state": "in_progress",
            "stopping_reason": "Not recorded", "remaining_failures": [],
            "verification_commands": []}
        if manifest.get('repair_target_policy'):
            initial_results['repair_targets'] = [{'task_id': target['task_id'],
                'outcome': 'blocked', 'summary': 'Not yet reviewed',
                'changed_components': [], 'evidence_paths': [], 'remaining_failures': []}
                for target in targets]
            if manifest.get('work_policy'):
                from .review_targets import parametric_target_ids
                for row in initial_results['repair_targets']:
                    if row['task_id'] in parametric_target_ids(contract):
                        row['parametric_work'] = {
                            'status': 'blocked', 'summary': 'Parametric work not yet started',
                            'prototype_path': None}
        _write_draw_bytes(results_path, _draw_json(initial_results), staging)
    # Journal remains until every required output has been durably finalized.
    # Staging is a dedicated namespace owned only by this locked transaction.
    if staging.exists():
        shutil.rmtree(staging)
        _sync_draw_directory(staging.parent)
    pending_path.unlink()
    _sync_draw_directory(pending_path.parent)
    return contract


def _finish_audit_draw(pending: Path, staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)
        _sync_draw_directory(staging.parent)
    pending.unlink()
    _sync_draw_directory(pending.parent)


def draw_audit(packet_root: Path, seed: bytes | None = None) -> dict:
    packet_root = packet_root.resolve()
    with _main_draw_lock(packet_root, "audit-draw.lock"):
        return _draw_audit_locked(packet_root, seed)


def _draw_audit_locked(packet_root: Path, seed: bytes | None = None) -> dict:
    path = _contract_path(packet_root, "AUDIT_ASSIGNMENT.json")
    pending_path = packet_root / '.review/pending-audit-draw.json'
    staging = packet_root / '.review/audit-draw-staging'
    main_path = packet_root / 'ASSIGNMENT.json'
    if any(p.is_symlink() for p in (path, pending_path, staging, main_path)):
        raise ValueError('Audit draw state cannot be a symlink')
    if path.is_file() and not pending_path.exists():
        return json.loads(path.read_text())
    manifest, packet_id = load_manifest(packet_root)
    main_raw = main_path.read_bytes() if main_path.is_file() else None
    main_hash = _sha(main_raw) if main_raw is not None else None
    if manifest.get('supplementary_ticket_policy') and main_raw is None:
        raise ValueError('Draw the main assignment before supplementary tickets')
    if pending_path.exists():
        try:
            saved = json.loads(pending_path.read_text())
            if (not isinstance(saved, dict) or set(saved) != {'schema', 'packet_id', 'seed', 'main_contract_sha256'}
                    or saved['schema'] != 'arcpuzzles-pending-audit-draw-v1'
                    or saved['packet_id'] != packet_id or saved['main_contract_sha256'] != main_hash):
                raise ValueError('Pending audit draw identity changed')
            pinned_seed = _seed(bytes.fromhex(saved['seed']))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('Invalid pending audit draw; explicit recovery required') from error
        if seed is not None and _seed(seed) != pinned_seed:
            raise ValueError('Explicit seed conflicts with pending audit draw; resume without a new seed')
        seed = pinned_seed
    seed = _seed(seed)
    journal = {'schema': 'arcpuzzles-pending-audit-draw-v1', 'packet_id': packet_id,
               'seed': seed.hex(), 'main_contract_sha256': main_hash}
    # Persist before selecting or verifying any peer asset. Every retry uses
    # this same packet/main identity and seed, including process interruption.
    _write_draw_bytes(pending_path, _draw_json(journal), staging)
    if manifest.get("supplementary_ticket_policy"):
        from .review_tickets import supplementary_contract, ticket_duties
        main = json.loads(main_raw)
        blind_path = packet_root / "BLIND_ASSIGNMENT.json"
        blind_id = json.loads(blind_path.read_text())["task_id"] if blind_path.is_file() else None
        contract = supplementary_contract(manifest, packet_id, main, seed, blind_id)
        for ticket in contract['tickets']:
            for binding in ticket.values():
                if isinstance(binding, dict) and set(binding) == {'path', 'sha256'}:
                    source = binding['path']
                    frozen = packet_root / '.review/baseline' / source
                    if source == f"repo/{main['generator']['generator']}" and frozen.is_file():
                        if _sha(frozen.read_bytes()) != binding['sha256']:
                            raise ValueError('Frozen ticket source changed')
                    elif _sha(_verify(packet_root, manifest, source)) != binding['sha256']:
                        raise ValueError('Ticket asset source changed')
        _write_draw_bytes(path, _draw_json(contract), staging)
        _write_draw_bytes(packet_root / 'TICKETS.md', ticket_duties(contract).encode(), staging, replace=True)
        result_path = packet_root / 'RESULTS.json'
        if result_path.is_symlink():
            raise ValueError('Audit results cannot be a symlink')
        result = json.loads(result_path.read_text())
        result.setdefault('supplementary_tickets', [{'ticket_id': t['ticket_id'], 'type': t['type'],
            'status': 'unknown', 'summary': 'Not attempted; record the actual result or concrete blocker.',
            'evidence_paths': [], 'elapsed_minutes': None} for t in contract['tickets']])
        _write_draw_bytes(result_path, _draw_json(result), staging, replace=True)
        _finish_audit_draw(pending_path, staging)
        return contract
    pool = manifest["all_ids"]
    if len(pool) < 2:
        raise ValueError("Audit draw needs at least two generators")
    blind_path = packet_root / "BLIND_ASSIGNMENT.json"
    if blind_path.is_file():
        # Auditing the blind task would expose its rule; keep it out of the audit pool.
        blind_id = json.loads(blind_path.read_text())["task_id"]
        pool = [tid for tid in pool if tid != blind_id]
    ids = audit_ids_for_seed(pool, seed)
    main_contract = packet_root / "ASSIGNMENT.json"
    main_id = json.loads(main_contract.read_text()).get("task_id") if main_contract.is_file() else None
    targets = []
    for task_id in ids:
        row = manifest["generators"][task_id]
        source = f"repo/{row['generator']}"
        if main_id == task_id:
            frozen = packet_root / ".review/baseline" / source
            if not frozen.is_file() or frozen.is_symlink() or _sha(frozen.read_bytes()) != manifest["files"][source]:
                raise ValueError(f"Frozen audit source changed: {source}")
            digest = manifest["files"][source]
        else:
            digest = _sha(_verify(packet_root, manifest, source))
        targets.append({"task_id": task_id, "generator_sha256": digest})
    contract = {"schema": "arcpuzzles-full-audit-v3", "packet_id": packet_id,
                "seed": seed.hex(), "targets": targets}
    _write_draw_bytes(path, _draw_json(contract), staging)
    _finish_audit_draw(pending_path, staging)
    return contract


def audit_ids_for_seed(pool: list[str], seed: bytes) -> list[str]:
    """Draw two distinct generator IDs without replacement."""
    first = int.from_bytes(seed, "big") % len(pool)
    second = int.from_bytes(hashlib.sha256(seed + b":second").digest(), "big") % (len(pool) - 1)
    if second >= first:
        second += 1
    return [pool[first], pool[second]]


def main(packet_root: Path, args: list[str]) -> int:
    if args and args[0] == 'nvarc':
        from .review_nvarc import main as nvarc_main
        return nvarc_main(packet_root, args[1:])
    if args in (["audit"], ["tickets"]):
        value = draw_audit(packet_root)
        if value['schema'] == 'arcpuzzles-full-audit-v4':
            print((packet_root / 'TICKETS.md').read_text())
        else:
            print("Audit targets: " + ", ".join(row["task_id"] for row in value["targets"]))
            print("Write a separate ## TASK_ID section for each in AUDIT.md; no fix is required.")
    elif not args:
        value = draw_main(packet_root)
        print(f"Assignment: {value['task_id']} ({value['assignment_id']})")
        print((packet_root / "DUTIES.md").read_text())
    else:
        print("Usage: python3 assignment.py [tickets|audit]", file=sys.stderr)
        return 2
    return 0
