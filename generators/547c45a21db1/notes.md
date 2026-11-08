# Working notes: 547c45a21db1

## Review 2026-10-04 — version 3.1.0

Assignment `review-54679fb53aee003c`; final generator SHA-256:
`3d898f37975aaf54e4868ac01e67598f564183ab488b59421be26f59e154bc41`.
The original notes were empty: the rationale for the earlier clipping and
difficulty-restricted overrides is unknown. Imported notes remain preserved in
`evidence/associated_notes.jsonl`.

### Domain and authority

Retain one simple induced cardinal path, background 0, interior 1, endpoints
2 and 3. The literal colors belong to the selected rule. Palette permutations,
branches, cycles, multiple components and interior seeds would change the
intended domain and are excluded. Python predictions are diagnostic rivals and
witness filters; production labels come from Racket. The exact canonical
program SHA is `44ec512ed7bb40370dd13ed35408a4c0ece07c3de292f157b51d6a4450ade2ea`;
neither the rule nor canonical fixtures changed.

`self_check` validates list-of-lists integer grids, connectivity, vertex degrees,
endpoint identity and at least two internal cells. `strict_canonical_like` uses
that structural definition without imposing sampler bounds on canonical input.
`observe_overrides` measures pixels. All bands accept height 5–14, width 6–14,
and total length 4–20. The old maximum 14 excluded the 19-cell canonical query.
A spaced snake fits length 20 even on 5×6, so no joint overrides are incompatible.
Bounded random walks and varied straight/L/snake paths retain geometry support
beyond the preferred witnesses. Every band favors canonical dimensions while
also sampling the full board range.

### Teaching decisions and retained failure

A monotone L-path does not separate Manhattan from path distance. Folds,
diagonal contacts, uneven turn placement and reversed raster endpoint ordering
provide actual contrasts. Seven declared canonical shortcuts fit all three
usable canonical pairs; the full declared lesson family has eleven rivals.

The first repair used odd contrast draws and four demonstrations. It passed its
nine initial rivals but missed a parity-conditioned rule: use correct cardinal
distance on odd lengths and raster-ordered endpoint colors on even lengths.
On the retained intermediate census, that rival gives 20/300 ambiguous lessons
and 111/1,500 ambiguous rotations. Evidence and original source are retained
under `checks/parity-probe/` and `checks/code-review/`; these are genuine review
failures, not fabricated solve attempts.

The final period-three schedule is odd contrast, even contrast, varied. Five
demonstrations plus one query give two raw draws of each kind in every six
consecutive indices. Both parity-conditioned raster rivals are now declared.
Contrast slots reverse seed raster order and separate all base metrics; varied
slots retain both seed orders and every length. Small fresh even paths came
from an independent exhaustive 5×6 search, not canonical fixtures; transformed
placements and generic end-extended snakes broaden the candidate family.

The schedule guarantee applies before rejections and without overrides. Hard
census lesson 53, seed 1179814037, rejects duplicate index 58 and accepts
`[53,54,55,56,57,59]`, leaving only one all-base even witness. Nevertheless all
six rotations refute every declared rival. Do not infer two witnesses per parity
for every accepted bundle from the raw schedule. Finite tests establish the
stated rival checks, not universal identifiability or any frequency lower bound
for the exact 19-cell canonical shape.

### Verification and tooling

The final source passes all twelve battery stages and 147 focused tests. The
exact-axis tests cover all 4,590 band/height/width/length combinations at seed
314159. The final production census has 100 lessons per band, five demos/one
query, starts 0–99, 1,800 rotations and no declared-rival ambiguity. Its 1,800
labeled positions represent 1,727 unique inputs. Exact commands, source hashes
and before/intermediate/final evidence are in the return's root reports.

The optional shared semantic-gate proposal lives in `workspace/tooling_proposal/`
and is not applied to shared code. The host-dependent offline test bootstrap
makes installed pytest visible to the isolated runner and checks NumPy/Pillow
availability. See `workspace/README.md` for reproducible entry points.
## Current reviewer considerations

Source SHA-256: `3d898f37975aaf54e4868ac01e67598f564183ab488b59421be26f59e154bc41`.

# Decisions and rejected alternatives

## R1 — Make every advertised override exact

The baseline treated difficulty as a limit on valid overrides and silently
shortened paths that its constructor failed to fit. Concrete within-old-domain
examples requested lengths 6, 9 and 14 and got 5, 7 and 9. The original working
notes were empty; no original rationale was recorded. The regression artifacts
retain exact seeds, indices, dimensions and baseline source.

The repair accepts height 5–14, width 6–14 and total active length 4–20 in every
band. Unknown keys, booleans, strings, floats and out-of-range values fail
explicitly. A bounded random path search provides varied geometry; a spaced
snake provides an exact fallback even on the smallest board. Rejecting feasible
joint requests, clipping to the nearest length, or shrinking declared domains
would preserve the original contract failure and was rejected. The new maximum
20 admits the canonical 19-cell query while remaining constructively feasible
throughout the full joint domain. Tests cover every one of 4,590 combinations.

## R2 — Validate the intended graph and retain label authority

Keep a simple induced cardinal path, literal colors 0/1/2/3, and the two seeds
at opposite endpoints. Connectivity, degrees and exact colors are observable
input facts. The old shape/count-only validator accepted malformed graphs;
the first repair still accepted tuple rows until focused tests caught it.
The final validator uses the list-of-lists grid contract. Structural strictness
does not require sampler bounds for canonical examples. Generalizing to branches,
cycles, interior seeds or arbitrary palette permutations would change the
documented task and was not justified by the assignment.

Add `RULE_HASH` matching the existing catalog. The Racket source, canonical
fixtures and shared helpers are unchanged. Python competitor functions and a
cardinal prediction used for witness selection never supply training labels.
Public Racket apply receipts independently check retained separating inputs.
An early semantic verification compared raw program text with wrapped callable
text and failed; the corrected check compares the appropriate representations.
Both the failed diagnostic and corrected evidence remain under
`checks/semantic-review/`.

## R3 — Teach both parities, preserving varied support

A monotone L does not refute Manhattan distance. Appropriate folded paths have
diagonal shortcuts or unequal turn placement; reversed raster seed ordering
also distinguishes color-based from scan-order-based assignment. The initial
nine competitors included these plausible geometric errors. All five then
declared canonical shortcuts fit all three canonical pairs; Manhattan and
squared Euclidean fit the demonstrations but fail the labeled canonical query.

The intermediate odd-only contrast schedule passed its initial 300-lesson
census, but an independent review proposed correct behavior on odd lengths and
raster-ordered behavior on even lengths. The same retained Racket labels exposed
20/300 production ambiguities and 111/1,500 ambiguous rotations. Three additional
exact cases were replayed through public Racket apply. The new parity tests were
run before repair and failed 15/20; all evidence and source snapshots remain.

Use the final three-slot schedule odd contrast/even contrast/varied and increase
`EXAMPLES_NEEDED` to five. Any six consecutive unrejected raw draws contain two
contrast examples of each parity, so any holdout leaves one of each. Retaining
four demos with this period would permit a holdout to remove the only contrast
of one parity. Forcing all examples to be contrast paths would unnecessarily
remove broad geometry and ordinary short lengths. Leaving parity-conditioned
rules undeclared would conceal the reproduced weakness. Both conditional rivals
are now actual declarations, giving eleven distinct competitors and seven
canonical-fitting shortcuts.

Even contrasts of all selected lengths 10, 12, 14, 16, 18 and 20 are feasible on
the minimum board. An independent exhaustive induced-path search provided fresh
small constructions; no canonical fixtures were copied. Generic end extensions,
reflections and placements broaden the even family. The varied branch retains
both seed orders and all lengths, and the random walk branch has constructive
support for all canonical geometries. No empirical lower bound is claimed for
the frequency of any exact geometry. Difficulty changes preference, not override
validity. Exact overrides have priority and can opt out of teaching contrasts.

The guaranteed raw sequence is not identical to the accepted production sequence.
One final census lesson rejects a duplicate and has only one all-base even
witness. All its rotations still refute every competitor, with a varied example
providing the needed even-only raster distinction. `accepted_schedule_exceptions.json`
preserves this case. The final result is a finite 300-lesson/1,800-rotation check
against declared rivals, not a universal proof or a claim about every seed.

## F1 — Build a shared proposal without changing the task's dependency surface

The shared semantic gate only scored whole lessons inside a custom-hook branch.
Declared rivals without that hook could therefore escape the intended check.
The optional patch scores those declarations directly and reports the limited
finite basis. It preserves legacy no-contract behavior and malformed/error
reporting. Seven of thirteen new synthetic regressions fail before the patch;
all thirteen and all 106 semantic-module tests pass after it in disposable
copies. Those are control-flow tests with synthetic labels, not Racket sampling.
The patch is retained separately in the selected workspace because shared code
is outside the authorized task delta. Its adoption needs a maintainer decision;
the assigned repair has its own hook and works without it.

## F2 — Make the portable test environment reproducible offline

The isolated runner correctly hides user-site packages. The original host's
pytest location caused an initial task-stage failure and three repository-test
failures. A fresh offline venv now receives the already installed pytest and
its four dependencies, with file hashes and an isolated import check. NumPy and
Pillow remain host system dependencies. This Linux helper is host-dependent,
downloads nothing and refuses existing destinations. It does not weaken runtime
isolation or claim to be a self-contained distributable environment. Final task
and repository runs pass; three optional PyTorch tests remain skipped.

## Audit-only follow-ups

A-DC3B-1 reproduces a production teaching defect in the exact sampled hard
lessons. A-FA355-1 separates a source-supported local-window shortcut using a
valid but currently unsampled radius-two piece. Expanding that second task's
shape support is a domain decision, not an automatic labeling fix. Neither
audit task is patched. Their exact authority-backed witnesses, denominators
and limits are in `AUDIT.md`.

## Evidence and final handoff

Preserve failed iterations and provenance, including the initial diagnostic
hash mistake, tuple validation failures, parity gap and environment failures.
Compress the large intermediate census losslessly, with both hashes, original
size/path and a verified restoration helper, rather than discard the evidence.
Keep the final generator bytes frozen through the final solve and fresh-packet
patch replay. Root report updates do not change those source bytes.

## Review 2026-10-24 — native parametric first-turn growth

Production `generator.py` remains byte-identical at SHA-256
`3d898f37975aaf54e4868ac01e67598f564183ab488b59421be26f59e154bc41`.
The new task-local adapter exposes two episode-fixed settings:
`nearest_seed`, whose program is loaded byte-for-byte from canonical authority,
and `first_turn_growth`. Inputs are matched across settings, distinct, prefix
stable for 2–6 demonstrations and 1–4 queries, and include a 30×30 query with a
121-cell induced path spanning 9 rows and all 30 columns.

The alternative is genuinely sequential. Step A traces the active path from
seed 2 and finds its first bend. The intermediate is that input-dependent path
distance (plus audited turn cell and directions). Step B cannot choose its
two-ended growth radius before that value exists; a standalone radius-1 Racket
counterfactual changes the final grid. Protected-Racket witness and replay are
retained at `checks/547c45a21db1/causal/witness.json` and
`checks/547c45a21db1/causal/replay.json`.

The focused suite passes 10/10 and the staged task suite passes 157/157. The
finite audit covers seeds 0 and 17, two declared-rival demonstrations per
setting, matched public inputs, private-field-independent public IDs, and the
large stress case. Native qualification is `qualified` for both settings at
seeds 0 and 17 with 3 demonstrations and 4 queries; current files still match
all 149 qualification-bound source/runtime hashes. The exact qualification is
at `checks/547c45a21db1/qualification/qualification.json` with sibling
`execution.json`.

Limits: the finite rivals are not a universal induction proof, and Python is
only a diagnostic mirror. Labels, qualification, and the wrong-intermediate
witness were executed through protected Racket. This return is reviewer-reported
`ready`; owner integration, fresh acceptance replay, and any training admission
remain pending.
