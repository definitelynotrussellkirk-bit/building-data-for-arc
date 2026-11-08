# Full-library generator review packet and batch intake

Date: September 27, 2026
Owner: ARCpuzzles
Status: written spec approved by user September 27; implementation pending

## Purpose and success criteria

Send the **same self-contained ZIP** to many external reviewers. A reviewer
reads `WELCOME.md`, runs `python3 assignment.py`, and receives one random
generator improvement assignment and its exact duties. The packet contains all
3,941 ARCpuzzles generator implementations, their authored notes and
workspaces, canonical and task-local Racket authorities, the runnable check
stack, and enough current documentation to work without ARCagi2 or sibling
checkouts. A separate optional command draws one quick adversarial audit target
from the entire generator catalog, including finished, approved, active, and
unreviewed generators. The audit may report shortcomings without a repair.

Eight reviewers may draw independently from identical offline copies. Same-wave
collisions are an accepted risk; subsequent draws may intentionally revisit any
generator. Intake retains all distinct work, compares overlapping repairs, and
allows the operator to combine the best compatible parts after checking them.
The operator can ingest a folder of return ZIPs with one command and triage a
grouped inbox, without losing failed, partial, or no-change reports.

This is a new full-packet contract alongside the existing September 26
single-generator `review pick/pack` contract. The prepared 12 MB packet
`review-0aa785e71b514c44` is valid only for that narrower contract; it is
not the full-library packet described here. Neither contract launches workers,
contacts reviewers, trains a model, or changes approval labels.

## Approaches considered

1. **One reusable full packet with a local draw (chosen).** One file to send
   to every reviewer; a source-bound local draw and return builder preserve
   provenance. An offline draw cannot guarantee zero collisions, which the
   user explicitly accepts.
2. Eight separately reserved full packets. Unique targets would be guaranteed
   within a wave, but maintaining distinct ZIPs and handoffs is more work.
3. A shared library archive plus small assignment tickets. This sends fewer
   bytes, but each reviewer must receive and match two files.

## Packet build and inventory

`arcpuzzles review pack-full --out PATH` builds a fresh versioned archive from
the ARCpuzzles owner checkout. It includes a `repo/` working tree containing
all cataloged generator source files and each generator's `notes.md`,
`SUMMARY.md`, `workspace/`, focused tests, and retained task-local evidence;
the catalog, shared runtime/tools/tests, selected authorities, package code,
requirements, and relevant guides are also included. It excludes `.git/`,
`var/`, build products, caches, credentials, model weights, old incoming ZIPs,
and unrelated sibling or predecessor content. The executable tree remains
ARCpuzzles-owned; the packet does not import ARCagi2 at runtime.

A sorted `PACKET-MANIFEST.json` binds the packet schema, version, source path
and SHA-256 for every payload file except itself, the catalog and rule
authority hashes, the eligible main-draw list, question versions, and package
build inputs. Its canonical JSON digest is the embedded packet ID; the final
ZIP digest lives in the operator's local build receipt to avoid a
self-reference. The builder rejects missing or duplicated cataloged
generators, missing required runtime files, escaping symlinks, and source
changes during packaging. It
checks that a relocated extracted packet can query the full catalog and
prepare and run a selected-generator check without any local sibling source.
The immutable packet archive and receipt remain in ignored `var/review/`;
only small durable metadata belongs under `REVIEW/`.

As of this design, ARCpuzzles catalogs 3,941 generators. A read-only census
found 3,442 unapproved generators with a present unambiguous canonical rule;
the exact main pool is recomputed and frozen when the ZIP is built. The packet
includes the other generators for context and adversarial auditing even though
they are not main improvement candidates. No training admission follows from
inclusion in either pool.

## Reviewer entry and assignment

`WELCOME.md` contains only setup, `python3 assignment.py`, and the way to
package a return. It names Python 3.12+, Bash, Git, Racket, NumPy, Pillow, and
pytest as the actual tools needed for the subsequent checks; drawing itself
uses only the Python standard library. The assignment command reads the frozen
manifest, verifies the selected source hashes, draws one main generator with
32 bytes from operating-system randomness from the sorted frozen eligible
list (`int.from_bytes(seed, "big") % pool_size`), and writes an
immutable `ASSIGNMENT.json` exactly once per extraction. A later invocation
prints the same assignment and duties from the frozen baseline even after the
working source has been edited; it does not silently redraw. It records
the canonical manifest digest, draw seed, selected ID, source and rule hashes,
question version/hash, and a unique assignment ID. The question draw uses a
separate domain-separated digest of that seed over sorted question IDs. The
draw can be reproduced from its recorded seed; this proves consistency, not
that a worker chose the seed honestly. The command creates a small frozen
baseline of the selected generator home and relevant rule authorities for
local diffs and prints
`DUTIES.md` with exact paths and check commands. It does not need an external
service, Racket, or Python packages merely to draw.

The duties run in this order: read the selected generator, existing notes,
canonical examples, and prior adversarial findings; run before checks;
improve its input distribution and, if warranted, its canonical Racket rule;
run after checks and iterate; write a decision record explaining the input
choices, alternatives and shortcuts considered, counterexamples, failed
attempts, measured changes, and unresolved limitations; answer the assigned
current versioned question; finally give general tooling/process feedback.
A bounded failure or justified no-change result can still be returned.
Questions are curated current records in ARCpuzzles `REVIEW/questions/`; stale
historical threads are not copied wholesale. The builder requires a nonempty
current question set for the full-packet mode so the printed duty is real.

`python3 assignment.py audit` is optional and makes a separate immutable
`AUDIT_ASSIGNMENT.json`. It draws from all 3,941 cataloged generators,
regardless of approval, active work, or past audit status. It can draw a target
that another reviewer will later receive for improvement. The quick audit asks
for plausible failure modes, input-distribution shortcuts, rule/source drift,
or missing evidence, with a concrete example or probe where possible. It does
not require a fix and does not confer approval. A repeated invocation reprints
the same audit target in that extraction; a new packet extraction is a new draw.
Its 32-byte seed and sorted-pool index are recorded separately from the main
draw. An audit may target the reviewer's main generator; this remains an
independent assessment.

The reviewer edits only the selected generator's authored files and permitted
task-local authorities in `repo/`; the optional audit is findings-only in this
return. Permitted patch paths are `repo/generators/<main_id>/generator.py`,
`notes.md`, `SUMMARY.md`, and ordinary files under that task's `workspace/`
or `tests/`, plus the bound task-local base authorities and the assigned
task's row or rows of `repo/shared/data/canonical/puzzles.jsonl`. Some
generators have two canonical rows; a rule edit may update both while leaving
every other task's row unchanged. Patches use these
exact `repo/`-rooted paths. The generator and rule cannot be deleted; new
regular task-local notes/tests/workspace files are allowed, while binary,
symlink, executable, shared-helper, and other-generator changes are rejected.
The provided `package_return.py` compares permitted files with the
frozen selected baseline and builds a compact `review_response_*.zip` from
the contract, focused patches, decision record, results, check evidence,
optional audit findings, question answer, and general feedback. It does not
rezip the full library. It uses the same static path/declaration validator as
operator intake, omits directory ZIP entries, and rejects undeclared artifacts
or changes to shared helpers or another generator. Reviewers can preserve
useful tooling suggestions as feedback without modifying shared code in the
packet.

## Return contract and cumulative knowledge

The returned ZIP echoes `ASSIGNMENT.json` and, if drawn,
`AUDIT_ASSIGNMENT.json` byte for byte. It contains `RESULTS.json`,
`REVIEW.md`, `DECISIONS.md`, `FEEDBACK_TO_CODEX.md`, the question answer,
and any declared patches/checks. All files other than the two assignment
contracts and `RESULTS.json` appear in `RESULTS.json.artifacts` with kind,
relative path, and SHA-256; this includes decision notes, audit findings and
probes, question answer and attachments, checks, and general feedback.
`RESULTS.json` identifies completion state,
main generator, optional audit target, modified components, exact evidence
paths, remaining failures, and reason for stopping. `DECISIONS.md` is a
first-class artifact even when no patch is proposed: each substantive choice
states the candidate idea, why it seemed plausible, the discriminating
observation, outcome, and consequence for generation. It distinguishes the
original author's rationale as found in source/notes from the reviewer's own
interpretation; absent original rationale is recorded as unknown. Existing
task notes are included in the packet and can receive a separately reviewable
patch. Original prose and supporting evidence are retained even for partial,
rejected, no-change, or never-integrated returns. Each proposed component and
feedback item receives its own disposition and reason.

Adversarial findings are append-only records keyed by audit target and return
ID, with the reviewed source hash, evidence, and disposition. Intake compiles
a per-generator view that links all original independent audits and groups
similar reported shortcomings without replacing or voting away a dissenting
observation. A compact task-local review index also links improvement decisions
and original evidence from every valid or partial return, regardless of whether
its patch was integrated. Future full packets include these original records
and the compiled view, with explicit `unverified`, `accepted`, or `rejected`
dispositions and source hashes, so a later assignee can benefit before editing
that generator. Compilation is an index, not an automatic code change or
safety judgment; a changed source hash leaves older observations visible but
marked as historical.

## Batch intake and operator workflow

`arcpuzzles review collect DIR` scans `review_response_*.zip` in stable path
order, reports ignored nonmatching files, atomically copies every original
archive to a content-addressed inbox before parsing, and gives idempotent
receipts for exact duplicates. It verifies ZIP paths, type/size bounds, packet
ID and manifest digest, reproduced draw, main eligibility, audit catalog
membership, source hashes, returned file
declarations, and task-scoped patch paths. Missing or stale contracts,
malformed ZIPs, partial work, invalid patches, and source drift get distinct
statuses while their bytes remain retained. Repeated reviews of the same
generator are accepted as independent returns. The batch continues after one
bad ZIP, a missing locally registered packet, or an extraction error, and ends
with totals and a path to the inbox. Intake locates the retained source packet
by canonical manifest digest, validates the locally drawn contract, and
registers its assignment ID idempotently; it does not require the operator to
have precreated that assignment. Packet ID, assignment ID, return version, and
ZIP digest are separate identities. Completion, static validation, check, and
disposition statuses are separate fields so useful partial work is not reduced
to a generic rejection.

`arcpuzzles review inbox` generates a static local report and machine-readable
index grouped by main generator and audit target. It shows each return's
validation/check/assessment status, improvements claimed, decision notes,
unresolved failures, question/feedback links, and a collision group when two
repairs target the same source. It presents focused diffs side by side and
marks shared-file or same-hunk conflicts. The operator can select compatible
components from distinct returns after review; there is no last-writer-wins
integration. General feedback and audit findings have their own queues and
stable IDs. Updating the report from receipts is deterministic and does not
alter source files.

Static intake does not execute returned code. After inspecting a candidate,
the operator runs a bounded check in a disposable source copy made from the
frozen packet. It applies only the `repo/` path patch contract, then prepares
the existing selected-task runtime from the patched source; this adapter keeps
the inherited battery and Racket checker working without accepting unrelated
edits. Generator checks use the existing battery; Racket edits
must pass exact canonical pairs and fixed-seed parity. Integration is explicit
per component and rechecks current source. A changed canonical ledger is
merged at the assigned task-row level only after confirming each changed
row's baseline and that all other rows remain unchanged; simultaneous
unrelated rule proposals must not
clobber one another. Same-generator collisions require a reviewed combined
candidate and fresh checks. No intake, audit, check, or integration action
automatically stamps approval or review hashes.

## Failure handling and verification

ZIP scans reject traversal, symlinks, duplicate/case-colliding paths,
unexpected executable members, undeclared files, and oversized expanded
payloads before extraction. Return limits apply to compact returns, not the
full source request ZIP. The original source snapshot, all return versions,
failed checks, decisions, audits, and integration dispositions remain
retrievable. `collect` takes a lock for receipt creation so repeated or
concurrent batch commands cannot create duplicate versions. The operator can
rebuild the inbox from receipts; it never depends on an untracked web server
or a single mutable dashboard file for evidence.

Verification will use a relocated packet with no access to ARCagi2 or sibling
source; confirm all 3,941 generator implementations and task-local workspaces
were packaged, draw and re-run stability, one main draw from the frozen pool,
one optional audit draw from the full catalog, and a complete return generated
using only `WELCOME.md` instructions. A fixture batch with at least eight
independent draws will cover duplicate uploads, same-generator collisions,
approved-generator audit, malformed/partial returns, adversarial compilation,
task-local note patches, source drift, an authority with multiple source files,
and combined-candidate review. The relocated end-to-end test follows
`WELCOME.md` through setup, draw, baseline check, edit, after-check, return
packaging, and collection. Run the
focused tests, existing repository suite and lint, and one real packet smoke.
Report measured archive size and draw/collect time before declaring it ready
to send. Do not infer generator quality from a successful packet round trip.
