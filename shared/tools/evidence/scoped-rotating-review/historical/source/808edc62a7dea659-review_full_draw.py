"""Reproducible independent local main and adversarial review draws."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from .review_full_packet import SCHEMA, canonical_json


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
    approved = sorted(tid for tid, row in manifest["generators"].items() if row.get("approved") and tid != main_id)
    pool = approved or sorted(tid for tid in manifest["all_ids"] if tid != main_id)
    if not pool:
        raise ValueError("Blind solve needs a generator other than the repair target")
    return pool[int.from_bytes(hashlib.sha256(seed + b":blind").digest(), "big") % len(pool)]


def main_selection_for_seed(manifest: dict, seed: bytes) -> tuple[str, dict | None]:
    """Replay old draws exactly; new packets reserve a 10% evaluation focus."""
    seed = _seed(seed)
    policy = manifest.get('main_draw_policy')
    if policy is None:
        pool = manifest['main_ids']
        if not pool:
            raise ValueError('Empty main draw pool')
        return pool[int.from_bytes(seed, 'big') % len(pool)], None
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
    row = manifest["generators"][task_id]
    paths = _base_paths(packet_root, manifest, task_id)
    baseline = {name: _sha(_verify(packet_root, manifest, name)) for name in paths}
    questions = sorted(manifest["questions"], key=lambda x: x["id"])
    question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]
    _verify(packet_root, manifest, f"repo/REVIEW/questions/{question['id']}.json")
    assignment_id = "review-" + _sha(bytes.fromhex(packet_id) + seed)[:16]
    contract = {"schema": "arcpuzzles-full-assignment-v2", "assignment_id": assignment_id,
                "packet_id": packet_id, "seed": seed.hex(), "task_id": task_id,
                "generator": row, "question": question, "baseline_sha256": baseline}
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
                         "Develop one or two small rule parameters first, preserving the original "
                         "reasoning pattern and canonical default. This authoring priority does not "
                         "grant source, variant or training approval. An already approved generator "
                         "can be assigned because its parametric extension is still missing.\n")
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
    duties = f"""# Your generator assignment: {task_id}

Assignment ID: `{assignment_id}`. Work under `repo/generators/{task_id}/`.
The canonical rule is in `repo/shared/data/canonical/puzzles.jsonl` at task ID `{row['rule_task_id']}`.
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
   For an original-family priority draw, develop the parametric extension first,
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
{priority_note}

1. Read this generator, current notes, canonical examples and relevant open findings.
   Finish any assigned blind solve first. Main shortcut/teaching assessment belongs
   in this repair, not a separate mandatory question essay. Consult ARC-DESIGN.md
   and PARAMETRIC-RULES.md where relevant; do not reread unrelated historical logs.
2. Work on this generator's concrete repair or small parametric extension.
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
7. Read RETURN-GUIDE.md, then run `python3 package_return.py --out review_response_{assignment_id}.zip`.
   Return ONLY the delta: source.patch plus compact evidence from work you did,
   concise docs and useful solves. No full checkout, original packet, Racket,
   environment or copied runtime trees. Do not invent unrelated inventories or
   passing checks. Use `RESULTS.json` for actual commands, stopping reason and
   optional `work_scope` verification statuses. The builder preserves source and
   patch hashes and omits copied transport/runtime material.

The draw and baseline remain immutable. Rerunning the assignment resumes it.
"""
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
        _write_draw_bytes(results_path, _draw_json({"completion_state": "in_progress",
            "stopping_reason": "Not recorded", "remaining_failures": [],
            "verification_commands": []}), staging)
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
