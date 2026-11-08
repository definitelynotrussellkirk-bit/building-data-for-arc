# Full-Library Generator Review Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one reusable ARCpuzzles ZIP that lets each reviewer draw a random generator, optionally audit another, and return compact work that the operator can collect and triage in batches.

**Architecture:** Add a versioned full-packet route beside the existing preassigned review route. The full packet contains an immutable source snapshot and a local draw script; a shared validator checks both reviewer-built returns and operator intake. Batch collection registers offline assignments from their packet manifest, while candidate checks and explicit integration continue to use disposable copies and source-bound receipts.

**Tech Stack:** Python 3.12 standard library and existing ARCpuzzles code; Bash, Git, Racket, NumPy, Pillow, pytest for runnable checks; static HTML/JSON for the inbox.

**Spec:** `docs/superpowers/specs/2026-09-27-full-library-review-packet-design.md`

## Global Constraints

- Work in ARCpuzzles, retain the existing September 26 `review pick/pack/intake` behavior, and preserve all pre-existing dirty/untracked work. The v1 review implementation is partly uncommitted; do not stage unrelated changes or construct a worktree from HEAD that silently omits it. Use explicit staged-diff review for safe task-only commits; otherwise keep a verified task checkpoint without a commit.
- One identical ZIP must serve eight or more disconnected reviewers; occasional collision is accepted. Never reserve or remove a generator merely because it was drawn or finished.
- Include every currently cataloged generator and its authored notes/workspace; main draw is limited to unapproved generators with a present unambiguous canonical rule, while optional adversarial draw covers the whole catalog.
- `WELCOME.md` leads to `python3 assignment.py`; the assignment and audit commands use only the Python standard library and are stable on repeat invocation. Checks require the real Python 3.12+, Bash, Git, Racket, NumPy, Pillow, and pytest environment.
- Manifest identity is SHA-256 of canonical manifest JSON, excluding itself; the final ZIP digest lives only in the operator build receipt. Main and audit pools are sorted; `int.from_bytes(os.urandom(32), "big") % len(pool)` selects each target and the seed is recorded.
- Patches use exact `repo/`-rooted paths. Only the main generator home, bound task-local base authorities, and the assigned task's canonical row or rows may change; no shared helper, other generator, binary, symlink, executable, or deletion of the generator/rule is accepted.
- Retain every original return ZIP, including malformed, partial, collided, no-change, and failed candidates. Static intake never executes reviewer code. No automatic approval/review-hash changes, external sending, model training, or competition submission.
- Task-local reviewer reasoning and adversarial findings remain visible with original prose, source hashes, dispositions, and evidence; cumulative summaries never overwrite independent reports.

## Review Focus

1. A return from a locally drawn assignment arrives without an operator-side `ASSIGNMENT.json`: collect must validate it against the retained manifest and register it without manual mapping (Task 4).
2. A normal ZIP producer includes directory entries with executable directory bits: the return builder omits directory entries and the validator handles safe ordinary entries without accepting symlinks or executable files (Task 3).
3. Two returns change different tasks' rows of the same canonical JSONL after one integrates: the second remains integrable after task-row comparison and fresh checks, without replacing the first task's rows (Task 7).
4. Eight files contain a duplicate ZIP, a valid collision, a malformed archive, a partial result, and an audit of an approved generator: one batch continues, retains all distinct work, and reports independent statuses (Tasks 4 and 6).
5. A return contains useful decisions but no passing patch: its original rationale and evidence appear in the next packet's task-local review index with an honest disposition (Task 6).

## File map and interfaces

- `src/arcpuzzles/review_full_packet.py`: source inventory, question validation, canonical manifest, ZIP build and operator receipt. Exposes `build_full_packet(catalog: Catalog, review_root: Path, out: Path) -> dict`.
- `src/arcpuzzles/review_full_draw.py`: reviewer main/audit draw, immutable local contracts, selected baseline, `DUTIES.md`. Exposes `draw_main(packet_root: Path, seed: bytes | None = None) -> dict` and `draw_audit(packet_root: Path, seed: bytes | None = None) -> dict`.
- `src/arcpuzzles/review_full_return.py`: v2 contract and artifact validation, `repo/` patch-path rules, compact return builder. Exposes `validate_full_return(archive: zipfile.ZipFile, packet_manifest: dict) -> dict` and `build_full_return(packet_root: Path, out: Path) -> dict`.
- `src/arcpuzzles/review_full_collect.py`: content-addressed raw retention, offline-assignment registration, idempotent batch receipts. Exposes `collect_full_returns(review_root: Path, directory: Path) -> dict`.
- `src/arcpuzzles/review_full_candidate.py`: apply v2 patches to a frozen source copy, prepare a selected runtime, run generator/Racket checks, and assess it. Exposes `check_full_candidate(catalog: Catalog, review_root: Path, assignment_id: str, version: int, timeout: float = 4000) -> dict` and `assess_full_candidate(review_root: Path, assignment_id: str, version: int) -> dict`.
- `src/arcpuzzles/review_full_inbox.py`: task-local cumulative decision/audit indexes and deterministic HTML/JSON triage. Exposes `build_full_inbox(review_root: Path, out: Path) -> dict` and `compile_task_review_index(review_root: Path, task_id: str) -> dict`. Durable indexes live under `REVIEW/task_indexes/`; Task 1 overlays them into the next ZIP under `repo/generators/<id>/evidence/` without editing generator source.
- `src/arcpuzzles/review_full_integrate.py`: explicit v2 component dispositions, row-level Racket merge, collision staging and checked integration. Exposes `integrate_full_candidate(catalog: Catalog, review_root: Path, assignment_id: str, version: int, components: set[str]) -> dict` and `stage_full_combination(review_root: Path, sources: list[tuple[str, int]], out: Path) -> dict`.
- `src/arcpuzzles/cli.py`: add `review pack-full`, `collect`, `inbox`, and route existing `check/assess/integrate` by contract schema. Do not change v1 public signatures.
- `REVIEW/questions/` and `REVIEW/README.md`: current versioned question records and reviewer/operator instructions; packet root `WELCOME.md`, `assignment.py`, and `package_return.py` are built from small sources in `src/arcpuzzles/review_full_packet_files/`.
- `tests/test_review_full_packet.py`, `test_review_full_draw.py`, `test_review_full_return.py`, `test_review_full_collect.py`, `test_review_full_candidate.py`, `test_review_full_inbox.py`, `test_review_full_integrate.py`, `test_review_full_portable.py`: focused tests using the existing `library` fixture extended only where needed. Existing v1 review tests stay green.

---

### Task 1: Build and register a complete immutable full packet

**Files:** Create `src/arcpuzzles/review_full_packet.py`, `tests/test_review_full_packet.py`, `REVIEW/questions/generator-shortcuts.json`, `REVIEW/questions/qwen9-data-value.json`; modify `src/arcpuzzles/cli.py`.

**Interfaces:** Produces `build_full_packet(catalog, review_root, out) -> {"packet_id", "zip_sha256", "zip", "receipt", "generator_count", "eligible_count"}`. The manifest has `schema: "arcpuzzles-full-packet-v2"`, `files`, sorted `all_ids`, sorted `main_ids`, and versioned `questions`; later tasks consume this schema and the cached packet ZIP under `var/review/full-packets/<packet_id>/`.

- [ ] **Write failing tests.** `test_full_packet_inventory_and_manifest` asserts every fixture generator and each `notes.md`/`workspace/` file appears under `repo/`, approved fixture generators are absent from `main_ids` but present in `all_ids`, the two question records are bound, every file digest matches, and identical source builds have equal manifest digests. `test_pack_full_rejects_missing_or_drifting_source` removes a mapped generator or mutates it during packaging and asserts no complete ZIP/receipt is published. `test_packet_omits_private_and_generated_paths` checks `.git/`, `var/`, caches, and a synthetic credential path are absent.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_packet.py -q`; expect failures for the missing builder.
- [ ] **Implement inventory and build.** Allowlist `AGENTS.md`, `README.md`, `pyproject.toml`, `GUIDE/`, `catalog/`, `generators/`, `shared/`, `src/`, `tests/`, `tools/`, current `REVIEW/questions/`, and the named entry docs. Filter `.git`, `var`, build/dist, caches, credentials/weights and incoming review data. Include verified task-index overlays from `REVIEW/task_indexes/` in packet evidence paths without changing checkout source. Compare the catalog's generator paths against packaged paths exactly; hash before and during streaming ZIP write. Canonicalize manifest with sorted keys, compact separators and UTF-8; exclude the manifest itself from its file list. Publish ZIP/receipt atomically and never overwrite an existing different ZIP. Add two `arcpuzzles-review-question-v1` version-1 records: `generator-shortcuts` owned by ARCpuzzles asks, “For this generator, name the strongest plausible shortcut or rival rule that fits the canonical demonstrations. Give an exact input on which it disagrees with the intended rule, how you checked the output, and whether your proposed generator emits such cases.” `qwen9-data-value` owned by ARC2HQ asks, “Based on your generator review, what one additional automated gate would most improve Qwen3.5-9B training data quality? Name a reproducible failure it would catch, a possible false positive, and the cheapest way to test it.”
- [ ] **Run focused tests and inspect staged changes.** Same pytest command must pass; `git diff --check` must be clean. Commit only task-owned files if the staged diff excludes pre-existing work.

### Task 2: Let a reviewer draw and learn duties from the packet

**Files:** Create `src/arcpuzzles/review_full_draw.py`, `src/arcpuzzles/review_full_packet_files/WELCOME.md`, `assignment.py`, `tests/test_review_full_draw.py`; modify `src/arcpuzzles/review_full_packet.py` to include the entry files.

**Interfaces:** Consumes Task 1 manifest and emits `ASSIGNMENT.json` with `schema: "arcpuzzles-full-assignment-v2"`, packet ID, unique `review-[0-9a-f]{16}` assignment ID, seed hex, chosen ID, generator/rule hashes, question ID/version/hash, and baseline hashes. `draw_audit` emits `AUDIT_ASSIGNMENT.json` with `schema: "arcpuzzles-full-audit-v2"` and independent seed/target/hash. These are the Task 3 and Task 4 contracts.

- [ ] **Write failing tests.** `test_main_draw_is_stable_and_reproducible` injects known 32-byte seed, checks sorted-pool modulo selection, question selection, task baseline, and byte-identical second call after editing working source. `test_audit_draw_can_select_approved_or_finished` injects a seed that hits an approved fixture row, checks independence from main and stable repeat. `test_tampered_manifest_or_selected_source_fails_before_assignment` asserts no contract on failure. `test_welcome_is_sufficient` follows only its commands to produce `DUTIES.md` listing baseline/after checks, decision notes, question answer, feedback, and optional audit.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_draw.py -q`; expect missing draw/entry behavior.
- [ ] **Implement draw and duties.** Root `assignment.py` adds `repo/src` to `sys.path` and calls `review_full_draw.main`; `WELCOME.md` says read, run, then follow printed duties. Use 32-byte OS seed unless injected, `int.from_bytes(seed, "big") % len(sorted_ids)`, and `sha256(seed + b":question")` modulo sorted question count for the question. Copy the selected generator home and bound rule authorities to immutable local baseline before writing the contract; write contracts with exclusive create, and reprint without rehashing edited working files. Optional `audit` mode reads `all_ids` regardless of approval/history.
- [ ] **Run focused tests and inspect staged changes.** Same pytest command must pass; `git diff --check` must be clean. Commit only isolated task changes.

### Task 3: Package a compact, statically validated return

**Files:** Create `src/arcpuzzles/review_full_return.py`, `src/arcpuzzles/review_full_packet_files/package_return.py`, `tests/test_review_full_return.py`; modify `src/arcpuzzles/review_full_packet.py` to include the entry file.

**Interfaces:** `build_full_return(packet_root, out)` creates `review_response_<assignment_id>.zip`. `validate_full_return(archive, packet_manifest)` returns IDs, completion state, artifacts and patch paths; it must not require an operator-side assignment folder. Task 4 calls this exact validator after the existing `scan_zip` safety scan.

- [ ] **Write failing tests.** `test_return_echoes_contract_and_declares_every_artifact` asserts `RESULTS.json.artifacts` covers review, decisions, question answer, feedback, audit findings/probes and checks with SHA-256, while assignment contracts are byte-identical. `test_patch_scope_rejects_other_generator_and_shared_helper` covers `repo/` headers, all assigned canonical rows and no unrelated rows, bound base authorities, ordinary task notes/tests/workspace additions, binary/mode/symlink and deletion rejection. `test_return_builder_omits_directories_and_rejects_undeclared_files` covers ordinary ZIP producers and the review-focus directory mode case; `test_no_change_partial_return_keeps_decisions` accepts a declared blocked/no-patch return.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_return.py -q`; expect missing return builder/validator.
- [ ] **Implement return builder and one shared static validator.** Compare selected working files to frozen baseline, emit exact `diff --git a/repo/... b/repo/...` patches, populate declared artifact hashes, reject undeclared or out-of-scope changed source, and write files without directory entries. Reuse `review_return.scan_zip` for archive path/type/size checks; keep v1 rules unchanged. Reject any patch that changes a nonassigned canonical row even when Git applies it.
- [ ] **Run focused tests and inspect staged changes.** Same pytest command must pass; `git diff --check` must be clean. Commit only isolated task changes.

### Task 4: Collect many offline returns with one command

**Files:** Create `src/arcpuzzles/review_full_collect.py`, `tests/test_review_full_collect.py`; modify `src/arcpuzzles/cli.py` and, only for shared ZIP scanning, `src/arcpuzzles/review_return.py`.

**Interfaces:** `collect_full_returns(review_root, directory) -> {"counts", "receipts", "ignored", "inbox_hint"}`. Each receipt separates `validation_status`, `completion_status`, `check_status`, `disposition_status`, `packet_id`, `assignment_id`, `version`, `zip_sha256`, and retained archive path. Task 5 and Task 6 read these fields.

- [ ] **Write failing tests.** `test_collect_registers_offline_draw_without_precreated_assignment` validates manifest/draw, creates `REVIEW/assignments/<id>/` from the return, and checks byte-stable stored contract. `test_batch_isolates_failures_and_duplicates` feeds eight fixture ZIPs including exact duplicate, distinct same-generator collision, malformed, missing packet, partial, and approved-target audit; asserts all distinct originals survive, exact duplicate gets the same receipt, failures do not stop later files, and nonmatching filenames are reported. `test_parallel_collect_is_idempotent` runs two collectors against one folder and expects one version per digest.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_collect.py -q`; expect no batch collector.
- [ ] **Implement atomic batch collection.** Scan filenames in sorted order; preserve raw ZIP by SHA-256 before parsing; locate the locally retained packet by manifest digest; call Task 3 validator; reproduce both draws; register unique offline assignment under the existing review lock; write receipt/version atomically; continue after per-file exceptions. Do not execute a patch or discard `DECISIONS.md` on partial work.
- [ ] **Run focused tests and inspect staged changes.** Same pytest command must pass; `git diff --check` must be clean. Commit only isolated task changes.

### Task 5: Check and assess a full-packet candidate

**Files:** Create `src/arcpuzzles/review_full_candidate.py`, `tests/test_review_full_candidate.py`; modify `src/arcpuzzles/cli.py` to route `review check/assess` by assignment schema.

**Interfaces:** `check_full_candidate(...) -> {"status", "candidate_path", "paths", "checks", "candidate_file_sha256"}`; `assess_full_candidate(...) -> {"status", "blockers", "changed_paths", "decision_path", "audit_path", "question_answer", "feedback_items"}`. Task 7 consumes the checked hashes and assessment receipt.

- [ ] **Write failing tests.** `test_v2_check_builds_selected_runtime_from_patched_source` confirms the frozen full packet is copied to a disposable source, repo-rooted patches apply, and `prepare_runtime` plus inherited battery run on the selected task. `test_racket_candidate_checks_all_canonical_pairs_and_three_seeds` confirms bound rule edits trigger exact pairs and seeds 0, 1, 17; a nonassigned row fails. `test_failed_or_no_patch_return_is_assessable` keeps baseline failure logs, decisions, audit and answer paths; `test_v1_check_and_assess_still_dispatch_unchanged` covers regression.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_candidate.py tests/test_review_candidate.py tests/test_review_assess.py -q`; expect only new v2 assertions to fail.
- [ ] **Implement v2 candidate adapter and assessment.** Copy frozen `repo/` into ignored candidate space, statically revalidate paths and apply with `git apply --check`, use patched `Catalog` and `prepare_runtime` to run the inherited checks, and store original/candidate hashes plus logs. Read `RESULTS.json.artifacts` for question, decision, audit and feedback links. Keep v1 branches untouched.
- [ ] **Run focused and existing review tests.** Same pytest command must pass; inspect staged diff. Commit only isolated task changes.

### Task 6: Compile cumulative evidence and render a triage inbox

**Files:** Create `src/arcpuzzles/review_full_inbox.py`, `tests/test_review_full_inbox.py`; modify `src/arcpuzzles/cli.py`, `REVIEW/README.md`.

**Interfaces:** `compile_task_review_index(review_root, task_id) -> {"decisions", "audits", "source_hashes", "dispositions"}`; `build_full_inbox(review_root, out) -> {"html", "json", "counts"}`. Task 1 packet inventory includes the task-local indexed records from earlier batches, Task 7 adds dispositions.

- [ ] **Write failing tests.** `test_inbox_groups_collision_and_links_originals` collects two different returns for one generator, asserts both are listed side by side with their decision/evidence paths, and no patch is selected automatically. `test_audits_and_partial_decisions_accumulate_across_packet_builds` accepts repeated independent audits, a no-patch decision and a rejected patch with useful prose, then builds a fresh packet and checks the task-local index includes each labeled record. `test_inbox_rebuild_is_deterministic_and_safe` asserts identical JSON/HTML bytes on repeat and escaped reviewer text.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_inbox.py -q`; expect missing compiler/report.
- [ ] **Implement indexes and inbox.** Keep original prose/evidence under assignment receipts, write source-hash-bound task indexes to `REVIEW/task_indexes/<id>.json`, and render static HTML/JSON from retained receipts. Group by main and audit target, include separate validation/completion/check/disposition columns and collision links. The compiled view may group similar findings but must link every independent report and label old-source findings historical. Task 1 overlays the index into future packet task evidence.
- [ ] **Run focused tests and inspect staged changes.** Same pytest command must pass; `git diff --check` must be clean. Commit only isolated task changes.

### Task 7: Explicitly integrate components and resolve overlapping repairs

**Files:** Create `src/arcpuzzles/review_full_integrate.py`, `tests/test_review_full_integrate.py`; modify `src/arcpuzzles/cli.py` to route v2 `review integrate` and add a v2 disposition/combination command.

**Interfaces:** `integrate_full_candidate(catalog, review_root, assignment_id, version, components) -> dict`; v2 components are `generator`, `racket`, `tests_notes`, or empty set, matching v1 CLI choices. `stage_full_combination(review_root: Path, sources: list[tuple[str, int]], out: Path) -> dict` creates a reviewable merged candidate or a conflict report without writing authoritative source. CLI `review combine --source ID:VERSION --source ID:VERSION --out DIR` invokes it.

- [ ] **Write failing tests.** `test_different_canonical_rows_integrate_without_clobber` integrates one checked rule edit, then a second return from the same packet touching another task's row; verifies the first task's rows stay and only the second task's rows change. `test_two_row_authority_requires_bound_rows_only` uses a main task with two canonical rows, requires parity on both, and rejects an unrelated row change. `test_same_generator_collision_requires_combined_check` rejects silent last-write-wins; `stage_full_combination` retains both source IDs, exposes conflicts or a candidate, and requires a fresh check before integration. `test_component_selection_and_disposition_preserve_notes` selects generator versus notes/tests versus Racket independently, records explicit reasons for accepted/rejected/audit/feedback items, and leaves approval hashes untouched. `test_v1_integration_dispatch_unchanged` covers existing behavior.
- [ ] **Run failing tests.** `python3 -m pytest tests/test_review_full_integrate.py tests/test_review_assess.py -q`; expect only v2 assertions to fail.
- [ ] **Implement source-bound integration.** Recheck each selected file or canonical row against its frozen baseline immediately before write, use staged replacements and rollback, require checked candidate byte hashes, and write per-component evidence/dispositions. Merge only the assigned task's changed canonical rows into current JSONL; treat a same-row change as a manual rebase. A combination is a separately checked candidate with provenance from every contributing return.
- [ ] **Run focused and v1 tests.** Same pytest command must pass; inspect staged diff. Commit only isolated task changes.

### Task 8: Prove portability and handoff the first full packet

**Files:** Create `tests/test_review_full_portable.py`; modify `README.md`, `REVIEW/README.md`, `docs/verification.md`, and `src/arcpuzzles/review_full_packet_files/WELCOME.md` if the smoke exposes missing setup details. Build ignored `var/review/full-packets/<packet_id>/request.zip` and its receipt.

**Interfaces:** Uses Tasks 1–7 without adding another public API. The operator handoff is one ZIP plus `arcpuzzles review collect DIR` and the generated inbox link.

- [ ] **Write failing portable-flow test.** `test_relocated_full_packet_round_trip` follows only `WELCOME.md` from a relocated extraction with sibling/predecessor source removed from `PYTHONPATH`: setup, draw, baseline check, edit, after-check, decision and optional audit, `package_return.py`, and batch collection. Assert every cataloged generator home and workspace was included, all contracts match, the candidate remains confined, and a real selected-source check receipt exists.
- [ ] **Run failing test.** `python3 -m pytest tests/test_review_full_portable.py -q`; expect it to expose any missing wiring or documentation.
- [ ] **Finish wiring and documentation.** Keep the reviewer path to `WELCOME.md` then `assignment.py`; document a one-folder batch receive command, inbox, explicit check/integrate, source drift and collision procedure. Do not copy source or rollout artifacts to ARC2HQ.
- [ ] **Run final verification.** `python3 -m pytest -q`, `PYTHONPATH=src python3 -m arcpuzzles lint`, focused relocated test, and `git diff --check`; then build one real full packet and report actual ZIP size, generator/eligible/audit counts, draw time, collect time, and source manifest hash. Inspect one real `WELCOME.md` and its printed duties. Only after this claim the packet is ready for external reviewers.
- [ ] **Record final state.** Preserve packet and test receipts in ARCpuzzles ignored `var/review/`, write the documented packet path and build receipt under `REVIEW/`, and commit only cleanly isolated task-owned changes; report any intentionally uncommitted overlap with pre-existing work.

## Self-review result

Tasks 1–8 cover every spec section: full inventory and source identity; local main/audit draw; current questions; compact source-scoped returns; offline registration and batch retention; isolated checks; cumulative rationale and audits; collision comparison, row-level integration; relocated end-to-end validation. The five review-focus cases each have a named test in its owning task. The v1 route is regression-tested and remains usable. Execution should proceed natively in the owning checkout unless the user explicitly authorizes broader delegation; the previously requested Astra design review is complete.
