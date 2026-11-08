# Generator review ZIP round trip

Date: September 26, 2026
Owner: ARCpuzzles
Status: approved by user September 26, 2026; local ZIP round trip implemented September 27

## Intent and boundary

Restore the useful `ARCagi2/reviews/2` assignment-and-return loop in the
maintained ARCpuzzles repository. A reviewer receives one randomly claimed
generator, works on its Python generator and canonical Racket solution until
they can explain what is improved and what remains, then returns code, check
evidence, an answer to any assigned question, and general feedback about
tooling or the process. The operator can inspect and integrate each part
without silently changing a rule or an approval label.

The old review packet and returned ZIPs are reference material, not runtime
dependencies. This design extends the existing `arcpuzzles review pick`,
`pack`, `list`, and `close` workflow. ARCpuzzles owns the puzzle and generator
work; cross-project strategy answers are routed to ARC2HQ after assessment.
No agent launch, external message, training, Kaggle submission, or bulk
generator rewrite is part of this workflow.

## Choices considered

1. **Extend the current review commands (chosen).** Keep their exclusive
   random claim and portable workspace, add an immutable assignment contract,
   validated return intake, isolated checks, and explicit integration. This
   keeps source ownership and existing CLI behavior in one place.
2. Port the old `reviews/2` scripts wholesale. This would drag old paths,
   database assumptions, and broad training review behavior into ARCpuzzles.
3. Use manual ZIP extraction and `git apply`. This is fast for one return but
   loses reproducible intake, source binding, and feedback disposition.

## Assignment and reviewer experience

`review pick` retains seeded random selection, filters, exclusive active
claims, and `--id` for deliberate inspection. A reviewer cannot claim a
second active assignment for the same generator. The packet retains its
human-readable `REQUEST.md`, `puzzle.json`, baseline generator, and complete
copied runtime. Add an immutable root `ASSIGNMENT.json` with a schema version,
assignment ID, generator ID, source path and SHA-256, selected canonical rule
identity and source hash, runtime manifest hash, and optional question ID/text
and source hash. The mutable local `assignment.json` continues to track status;
workers echo `ASSIGNMENT.json` byte-for-byte. The packet states which paths in
the portable workspace correspond to the authoritative ARCpuzzles files.

The instructions order the work: inspect baseline and canonical examples;
run before checks; improve the generator and, where justified, its Racket
solution; run after checks and compare distribution, rule parity, and examples;
iterate on defects and weak examples until the reviewer has made the assigned
generator as strong as they can; record remaining failures and why work stopped;
answer the assigned question; **then** write
general feedback. "Best they could" is the reviewer's stated completion
judgment with evidence, not a claim the CLI can prove. A bounded check failure
can be returned with a clear blocker and still be useful. Do not weaken a gate
to produce a green receipt.

Questions are optional, current, versioned assignment inputs managed in
ARCpuzzles `REVIEW/`; the pick command may draw one by seeded choice or accept
an exact question ID. Old question threads are not copied en masse. Each
question records its intended owner: puzzle questions stay in ARCpuzzles;
cross-project strategy answers are forwarded for assessment in ARC2HQ.

## Return contract

One returned `review_response_*.zip` has, at minimum:

- `ASSIGNMENT.json`, echoed unchanged;
- `RESULTS.json`, naming the generator, completion state, changed components,
  check outcomes, residual failures, and a short improvement claim;
- `REVIEW.md`, explaining the before/after findings and proposed integration;
- `FEEDBACK_TO_CODEX.md`, written after the task work, with zero or more
  evidence-backed general feedback items;
- `patches/generator__<id>.patch` and/or `patches/racket__<id>.patch` for code
  changes, with original workspace paths and one generator/rule per patch;
- optional `QUESTION_ANSWER.json` and `.md`, `checks/`, `notes/`, and changed
  focused tests.

An unchanged generator may be returned with a reason and useful findings.
`RESULTS.json` lists every supplied patch and check artifact. The intake
accepts a documented subset of historical `reviews/2` ZIPs when their
assignment and baseline can be matched to current source; otherwise it keeps
the archive and records a mapping/rebase need instead of guessing.

## Intake, verification, and integration

`review intake ZIP` copies the original archive to an assignment-bound
`var/review/returns/<assignment>/<version>/` directory and writes a
content-hashed receipt under `REVIEW/assignments/<assignment>/`. It first scans the ZIP
without extracting: allow only ordinary relative files, reject absolute or
traversing paths, duplicate/case-colliding names, symlinks, excessive member
counts (more than 256) or expanded size (more than 25 MiB), and executable
file mode bits. Verify assignment
ID and byte-identical immutable contract, declared files, generator ID, and
baseline hashes. A repeated identical return is idempotent; a different
return is a new numbered version under the same assignment.

Intake never applies a patch to selected sources. It extracts to an isolated
`var/review/` candidate, validates patch paths against the assignment mapping,
checks applicability against its frozen workspace, and records parse/apply
failures. For a generator candidate, run focused generator checks and the
relevant battery with bounded time and keep both failing and passing logs. For
a Racket candidate, require exact execution on every canonical input/output
pair for that task and generator-rule parity on representative fixed seeds;
keep the old rule and candidate results side by side. A changed Racket rule
never receives automatic approval. Question answers and general feedback are
indexed separately from code checks.

`review assess` emits a concise candidate report: baseline binding, changed
files, check comparison, failures, answer location, feedback items, and
suggested disposition. The operator reviews each source diff before an
explicit `review integrate` action. Integration requires a current-source
hash match and affirmative selection of generator, Racket rule, tests/notes,
or none. It writes source-bound evidence in the owning generator's `evidence/`
and notes, preserves the original return and failed attempts, and leaves
approval/review hashes untouched. A source drift or failed required check
blocks automatic integration and yields a rebase/manual-review state. Existing
`review close --status completed` records the final disposition and releases the
claim only after assessment; it is not an integration shortcut. A never-returned
assignment can still be cancelled with a reason, preserving its record and
releasing the claim.

General feedback gets stable local IDs, a reviewable inbox, and dispositions
(`accepted`, `implemented`, `needs_evidence`, `deferred`, `declined`) with
reason and evidence. The question answer records its question version and
owner; incorporating a strategy answer into ARC2HQ is a separate reviewed
edit, never automatic text injection from the ZIP.

## Failure handling and evidence

Every state transition leaves a receipt. Malformed or unsafe ZIPs are rejected
before extraction while retaining their original bytes and rejection reason.
Wrong-assignment, stale-baseline, invalid patch, failed generator/Racket check,
partial return, and source drift have distinct states. No failure deletes the
assignment or an earlier return. ZIP bytes and temporary checks stay in ignored
`var/`; durable request/return metadata and dispositions stay under `REVIEW/`
and task-local evidence stays under `generators/<id>/evidence/`.

The existing Python/Racket test environment is sufficient; this feature adds
no service, database, GPU job, or external dependency. Check a normal return,
an unchanged-but-informative return, a historical mapped return, a stale
baseline, unsafe ZIP paths/symlinks/duplicates, independent generator and
Racket failures, idempotent intake, and source drift before integration.
Run the focused review suite and repository lint; execute a real portable
packet/return smoke on a disposable fixture. Report exactly which checks were
run and never infer generator quality from a successful ZIP round trip alone.
