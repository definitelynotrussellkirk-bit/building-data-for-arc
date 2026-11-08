# Generator review ZIP round trip Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give one randomly assigned generator reviewer a portable packet, safely accept their best generator/Racket work and later question/feedback return, and integrate reviewed changes with source-bound evidence.

**Architecture:** Extend the existing `review pick/pack/list/close` commands. Bind each packet to immutable source hashes, store original returns before validation, test proposed edits in an isolated workspace, and require explicit component selection for integration. Keep quality and approval decisions separate from ZIP handling.

**Tech Stack:** Python 3.12 standard library, existing ARCpuzzles runtime and Racket battery, pytest, `git apply` in a disposable workspace.

**Spec:** `docs/superpowers/specs/2026-09-26-generator-review-zip-roundtrip-design.md`

## Global Constraints

- Work only in ARCpuzzles; preserve unrelated working-tree changes and predecessor sources.
- No service, database, GPU job, external dependency, agent launch, paid call, or training action.
- Original ZIPs and failed candidates survive in ignored `var/review/`; durable metadata stays in `REVIEW/`.
- A passing intake or check never upgrades approval/review hashes or proves semantic quality.
- No automatic Racket rule approval; a rule change needs explicit source review and selection.
- The reviewer sequence is generator/Racket iteration to their best result, remaining failures, assigned question answer, then general feedback.

## Review Focus

- A packet whose generator changes during preparation must fail visibly, leaving a released claim (Task 1 test).
- A ZIP with a duplicate or case-colliding name must be rejected before any extraction (Task 2 test).
- A returned patch touching another generator or a runtime helper must be rejected even if `git apply` accepts it (Task 3 test).
- A proposal whose authoritative source changed after assignment must remain reviewable but cannot integrate automatically (Task 4 test).
- A return with useful findings and no patch must remain assessable and closable (Task 5 test).
- A seeded random pick restricted to a source-bound review cohort must never choose a generator outside that cohort, and a stale cohort must fail before claiming anything (Task 1 test).

## File map

- `src/arcpuzzles/review.py`: existing claims, packet preparation, pack and close; keep its public entry points.
- `src/arcpuzzles/review_contract.py`: immutable assignment and optional question binding.
- `src/arcpuzzles/review_return.py`: ZIP scan, immutable archive receipt, and return metadata validation.
- `src/arcpuzzles/review_candidate.py`: confined patch application and bounded isolated checks.
- `src/arcpuzzles/review_assess.py`: assessment, selective integration, feedback disposition, and close precondition.
- `src/arcpuzzles/cli.py`: user-visible commands and flags; delegate work to the modules above.
- `tests/test_review_runtime.py`, `tests/test_review_contract.py`, `tests/test_review_return.py`, `tests/test_review_candidate.py`, `tests/test_review_assess.py`: real fixture and command behavior.
- `REVIEW/README.md`, `README.md`: packet, return, and operator commands.

---

### Task 1: Bind a random assignment and order the reviewer's work

**Files:** Modify `src/arcpuzzles/review.py`, `src/arcpuzzles/cli.py`; create `src/arcpuzzles/review_contract.py`, `tests/test_review_contract.py`; modify `tests/test_review_runtime.py`.

**Interfaces:** `build_contract(catalog: Catalog, record: dict, workspace: Path, question: dict | None) -> dict`; `load_question(review_root: Path, question_id: str | None, seed: int) -> dict | None`; `load_cohort(catalog: Catalog, receipt_path: Path) -> tuple[set[str], dict]`; `pick(..., question_id: str | None = None, cohort_receipt: Path | None = None) -> dict`. Questions live at `REVIEW/questions/<id>.json` with `schema`, `id`, `version`, `owner`, `text` and are included by exact ID or seeded selection when present. CLI `review pick --cohort RECEIPT` intersects a pinned ID set with the ordinary filters before seeded random choice.

- [ ] Write tests: the packet has byte-stable `ASSIGNMENT.json` with selected generator SHA-256, canonical rule identity/hash, runtime manifest hash, optional versioned question hash, and optional cohort receipt/rows hashes; `REQUEST.md` orders improvement, remaining failures, question, feedback; a preparation-time source change fails visibly and releases the claim. An optional cohort restricts the eligible pool before random selection and records its hash and count; a tampered rows file, mismatched receipt/source hash, or stale current generator hash fails before a claim is created.
- [ ] Run `python -m pytest tests/test_review_contract.py tests/test_review_runtime.py -q`; see the new assertions fail for missing contract/sequence.
- [ ] Implement `build_contract`, `load_question`, `load_cohort`, the `pick`/CLI extension, and a return template containing `RESULTS.json`, `REVIEW.md`, `FEEDBACK_TO_CODEX.md`, and patch path examples. `load_cohort` accepts the existing `verified-unapproved-official-generator-review-v1` receipt, verifies `rows_sha256` and the receipt's source hashes, reads the adjacent `rows.jsonl`, and checks each included generator's current hash before selection. Keep `assignment.json` mutable and out of the immutable echo contract. The first review tranche uses `--cohort var/derived/verified-unapproved-official-generator-review-20260926-v1/receipt.json --not-approved --source training --train-safety provisionally_safe`; this is 277 verified original-family generators today, whereas those filters alone select 288. Rebuild the cohort after source changes before another pick; no reviewer is launched by this command.
- [ ] Rerun the focused tests; expect pass. Commit only Task 1 files.

### Task 2: Retain and validate returned ZIPs

**Files:** Create `src/arcpuzzles/review_return.py`, `tests/test_review_return.py`; modify `src/arcpuzzles/cli.py`.

**Interfaces:** `intake(review_root: Path, zip_path: Path) -> dict` returns assignment ID, return version, ZIP SHA-256, status, receipt path. `scan_zip(archive: zipfile.ZipFile) -> list[zipfile.ZipInfo]` enforces ordinary relative files, no traversal, symlinks, executable bits, duplicate/case-colliding paths, more than 256 members, or more than 25 MiB expanded bytes. CLI: `review intake ZIP`.

- [ ] Write tests: a valid return is copied to `var/review/returns/<assignment>/<version>/`, retains the original bytes, and gets a durable content-hashed receipt; identical intake is idempotent; changed return is a new version; a historical `reviews/2` return with provably matching assignment and baseline is accepted; wrong assignment and every unsafe ZIP path/type/size are retained with a rejection reason and never extracted.
- [ ] Run `python -m pytest tests/test_review_return.py -q`; see failures for missing intake/scan behavior.
- [ ] Implement scan before extraction, byte-identical `ASSIGNMENT.json` comparison, `RESULTS.json` declared-file checks, immutable version receipts, and the CLI entry. Historical returns may enter a separate `mapping_required` state only when their assignment and baseline cannot be proven; never guess a mapping.
- [ ] Rerun focused tests; expect pass. Commit only Task 2 files.

### Task 3: Build and check an isolated candidate

**Files:** Create `src/arcpuzzles/review_candidate.py`, `tests/test_review_candidate.py`; modify `src/arcpuzzles/cli.py`.

**Interfaces:** `check_candidate(catalog: Catalog, review_root: Path, assignment_id: str, version: int, *, timeout: float = 4000) -> dict`. CLI: `review check ID --version N [--timeout SECONDS]`. The candidate starts from the assignment's frozen `workspace/` and only accepts the mapped generator path, the assigned task's row in `data/canonical/puzzles.jsonl`, any selected task-specific base authority path bound in `ASSIGNMENT.json`, and task-local tests/notes; unrelated canonical rows and shared helpers cannot change.

- [ ] Write tests: a generator patch applies only in a copied workspace; an unrelated path, binary patch, stale hunk, or second generator is rejected; a task-local test/notes patch is permitted and recorded separately; a failing battery leaves logs and a failed status; a Racket patch must satisfy every canonical pair and generator/rule parity at medium difficulty for seeds 0, 1 and 17 before it can be marked check-passing.
- [ ] Run `python -m pytest tests/test_review_candidate.py -q`; see failures for missing confined candidate/check behavior.
- [ ] Implement strict patch-path and canonical-row validation, `git apply --check` then apply inside the disposable candidate, bounded battery and Racket execution through the existing runtime, and side-by-side baseline/candidate receipts. Preserve failures; never edit authoritative sources here.
- [ ] Rerun focused tests; expect pass. Commit only Task 3 files.

### Task 4: Assess and explicitly integrate selected components

**Files:** Create `src/arcpuzzles/review_assess.py`, `tests/test_review_assess.py`; modify `src/arcpuzzles/cli.py`, `src/arcpuzzles/review.py`.

**Interfaces:** `assess(review_root: Path, assignment_id: str, version: int) -> dict`; `integrate(catalog: Catalog, review_root: Path, assignment_id: str, version: int, components: set[str]) -> dict`, with allowed components `generator`, `racket`, `tests_notes`, or an empty set; CLI `review assess ID --version N`, `review integrate ID --version N --component ...`.

- [ ] Write tests: assessment exposes diffs, check comparison, question/feedback paths and blocker states; source drift or a failed required check prevents automatic integration; selecting only generator leaves Racket untouched; Racket selection is explicit; integration writes source-bound evidence and never changes approval/review hashes; completed `review close` requires an assessment, while a never-returned assignment can be cancelled with a reason.
- [ ] Run `python -m pytest tests/test_review_assess.py tests/test_review_runtime.py -q`; see the new assertions fail.
- [ ] Implement the report and integration against exact authoritative paths bound in the contract. Recheck current source hashes immediately before any selected write; stage all selected files, then replace them with rollback copies if a later replacement fails, preserving the selected canonical row and authority sync. Preserve original return and failed versions. Keep question answers as reviewed artifacts, not automatic HQ edits.
- [ ] Rerun focused tests; expect pass. Commit only Task 4 files.

### Task 5: Feedback inbox and full portable round trip

**Files:** Modify `src/arcpuzzles/review_assess.py`, `src/arcpuzzles/cli.py`, `REVIEW/README.md`, `README.md`; create or modify `tests/test_review_assess.py` and one disposable packet/return smoke test.

**Interfaces:** `record_feedback(review_root: Path, assignment_id: str, version: int, item_id: str, status: str, reason: str) -> dict`; CLI `review feedback ID --version N --item ITEM --status accepted|implemented|needs_evidence|deferred|declined --reason TEXT`. Feedback IDs are stable within a return and retain evidence paths.

- [ ] Write tests: no-patch findings are assessable and closable; question answer retains question version and owner; feedback cannot be dispositioned without a nonempty reason; a complete packet/return works after relocation with no sibling import path.
- [ ] Run the focused tests; see failures for absent feedback and end-to-end behavior.
- [ ] Implement the feedback ledger and document the reviewer sequence, ZIP return command/shape, operator intake/check/assess/integrate/close commands, and partial/failed statuses.
- [ ] Run `python -m pytest -q`, `python -m arcpuzzles lint`, and the portable packet/return smoke; record exact outcomes, then commit only Task 5 files.

## Self-review result

The five tasks cover packet binding, optional question selection, safe original return retention, isolated generator/Racket checks, explicit integration, answers, feedback, and failure receipts. Interfaces pass assignment ID and return version consistently. The review-focus failure modes each have a named test in their owning task. No step launches a reviewer or changes training admission.
