# Current decisions: d07c7972d183, version 4.0.0

## Rule and authority

For a binary input, find its least finite whole-row period P. Continue that
period to h + floor(h/2) rows, recoloring every 1 to 2 throughout the output.
Racket remains the label authority, pinned by RULE_HASH `6358a7ca0f4d`.
The canonical ledger was not edited. The selected base authority's target_code
was synchronized byte-for-byte with the already equivalent canonical program;
this was a whitespace-only text correction. Archival raw_code is preserved.

## Proposed parametric extension: review-cb9d1e703331e9d2

The separate `workspace/parametric/` prototype adds `extension_divisor in {2,3}`
and `output_color in {2,3}`. Its original (2,2) setting materializes the exact
canonical program; the canonical generator, authority and approval are unchanged.
The four variants preserve whole-row period inference and continuation phase.

A fixed setting applies throughout each episode. Demonstrations 2..8 and
queries 1..8 are independent, with distinct inputs and a 256-additional-candidate
sampling limit. Height-9 and height-7 demonstrations identify the four settings
and seven parameter-aware Racket shortcuts using demonstrations only. Every
exported label executes protected Racket. This is finite-rival evidence, not a
claim of universal rule uniqueness or measured training benefit.

Public challenge bytes and full hash filenames come from the shared projection
helpers; seeds, settings, exact programs, query answers and certificates remain
private. The writer rechecks labels and private identities and pre-serializes
the full batch before publication. Current commands and limits are in the
prototype README; focused results and paired episodes are under the return's
`checks/parametric/`. A thin adapter/contract is proposed for later owner
qualification. No parametric acceptance or training admission is claimed.

## Resolved support defects

The 3.0.0 sampler forced its top-left cell to zero and prohibited the first row
from recurring inside the motif. Both choices excluded canonical features;
the original rationale is unknown. The prior audit
`review-c227d9afeed2a683:v0001` was a lead, independently reproduced on the
selected baseline: neither feature occurred in 400 draws per band. The new
sampler permits both corner values and repeated motif rows, checking the least
period of the complete emitted grid. Checking only the finite motif would
incorrectly reject the canonical A,B,A motif when its repeated grid has P=3.

The source-bound 400-per-band probe now observes top-left foreground
291/289/286 and early first-row recurrence 283/292/290 in easy/medium/hard.
All 1,200 generated grids validate. Canonical-size 6x3 support is 151/150/150.
The new workspace/probe_curriculum.py exposes an opt-in feature-support gate;
its baseline failure and repaired pass are retained in this review's checks/.
This explicitly addresses the old corner audit, without changing approval.

## Teaching schedule and distribution

The default eight-position schedule is canonical, witness, broad, witness,
canonical, witness, canonical, witness. It allocates 3/8 canonical-size inputs,
4/8 distinguishing inputs, and 1/8 general inputs. Each four consecutive
candidate positions contains two distinguishing grids. The two witness
subtypes differ in their fourth row's first cell, so they cannot be duplicates.
The production duplicate-rejection integration test exercises the real sampler
and Racket labels; it is part of the 42 passing selected tests.

A witness has height 9 and period 6, with motif A,B,A,D,C,E. One column has
finite period 5 over the nine input rows while the complete rows have period 6.
It refutes independent-column continuation, premature first-row recurrence,
constant output height 9, constant extension 3, ceiling-half extension,
unchanged top-left background, and repeating the entire input. The two D
choices alternate by witness position. A retained minimal input and actual
public Racket receipt live in counterexamples/review-914736475a6098c8/.

Three quarters of witness draws use contiguous rows sharing a foreground spine;
one quarter varies the nonessential bits. This retains a connected-shape mode
while avoiding a single fixed template. Initial unrestricted witness textures
failed the morphology marginal gate and were replaced. The final marginal gate
passes; it cannot certify semantic distribution quality. A randomized extra
canonical slot was replaced by the explicit eight-slot cycle so small checks
reliably encounter the broad branch. General axes mix 25% uniform draws with
75% difficulty-biased draws over the same legal bounds.

## Controls, validator and limits

Exact integer controls remain height 4..18, width 3..12, and period 2..6.
Combinations with period > height-2 reject explicitly. Unknown keys, booleans,
strings and fractional values reject; malformed cells return validator reasons.
The palette and motif-density grammar are preserved. Non-None overrides select
general sampling and bypass the default teaching schedule: identifiability of
arbitrary override lessons is untested. All four canonical inputs remain valid.

The final battery has 12/12 green stages and no warnings. The declared-rival
census found no ambiguity in 300 three-demo/one-query production lessons
(1,200 labelled pairs, 522 distinct inputs) or 1,200 held-out-query rotations.
A separate seed-0 enumeration checked all eight starts in each band: 24 lessons,
96 rotations, 20 distinct inputs. These finite checks concern seven distinct
rivals; repeated registrations are not extra independent hypotheses.

The witness subtype correlates with height and some visual structure, and the
connected branch has limited combinatorial variety. No claim is made about
undeclared rivals, arbitrary train/query counts, shuffled multi-query lessons,
optimal curriculum weighting, or Qwen training gains. No runtime
lesson_identifiable hook is declared; the retained census checks rivals on
materialized lessons. Passing review checks does not grant training approval.
See the return's REVIEW.md and DECISIONS.md for exact commands and limitations.
## Current reviewer considerations

Source SHA-256: `2f2f8e0d2b8ef4f8ddd5c3e2b8a36abb07b4e96ef1a2d12eedd01547efada63a`.

# Design decisions and evidence

## D1. Restore canonical structural support

The baseline forced input[0][0]=0 in both morphological branches and rejected
every motif containing another copy of row zero. The source contained no
justification for those restrictions; their original rationale is unknown.
They exclude a foreground corner present in the canonical query and internal
first-row repetitions present in two canonical demonstrations. The old audit
was a lead, and the 1,200-draw input-only probe reproduced its corner finding
on the actual selected baseline.

The repair removes both conditions. A motif may repeat its first row before
its least complete cycle ends. Period is therefore verified on the emitted
grid, not just the finite motif: motif A,B,A is locally consistent with a
two-step recurrence but emitted A,B,A,A,B,A has period three. A regression
requires canonical acceptance and exercises early first-row recurrence in
every band. The final feature gate observes all five retained canonical
features in all bands. It deliberately does not require their empirical
frequencies to equal a four-example canonical sample.

Alternatives rejected: fixing the top-left cell to foreground would reverse
the shortcut rather than support both values; blindly removing all period
checks would make the advertised exact period unreliable; testing uniqueness
of rows would continue to exclude legitimate motifs. The chosen validator
still requires the documented binary periodic grammar, motif density and
visible repeated-row cues. Background 0 and recoloring 1->2 remain fixed
semantic color roles; no unsupported palette permutation was added.

## D2. Make plausible rivals distinguishable in complete lessons

The baseline's first-recurrence rule fit all 360 inputs in the independent
120-per-band probe while failing two canonical demonstrations. An
independent-column period rule fit all four canonical pairs; the baseline
probe refuted it in 0/120 easy, 0/120 medium, and 4/120 hard inputs. These are
Python diagnostic comparisons, not production-lesson verdicts. Their role
was to identify hypotheses for subsequent Racket-labelled checks.

I introduced seven executable rivals: preserve a black corner, use the first
recurrence, continue columns separately, use fixed height nine, append three
rows, extend by ceiling-half, and repeat the whole input. Only the four that
actually fit every canonical pair are named CANONICAL_SHORTCUTS. The census
verifies each such claim against all four pairs. All seven are also diagnostic
lesson competitors; multiple registrations do not create extra distinct rivals.

The distinguishing family has motif A,B,A,D,C,E at height nine. A special
column has nine-row sequence 000010000, which admits period five; column zero
rules out that period for the whole grid. The least row period is six, while
the first recurrence of A is two. Output height is thirteen, distinguishing
fixed-nine, plus-three and ceiling-half alternatives. A foreground corner
distinguishes the corner rule. Continuing the full input resets at the wrong
phase. `counterexamples/review-914736475a6098c8/` retains a concrete 9x3
instance, the supported public Racket receipt, all rival outputs, and diffs.
The explicit expected-output test is separate from diagnostic mirrors.

Initial purely varied bit patterns made too many disconnected objects: the
first after battery flagged median object count four against canonical one.
The final branch uses connected contiguous rows sharing a spine 75% of the
time, with a varied-bit family the other 25%. Anchor bounds preserve strict
zero-majority even in the densest allowed connected subtype. The final
morphology gate passes and the finite witness checks remain sound. A single
fixed witness would have been simpler but needlessly repeated the same grid;
arbitrary noise failed the observed shape distribution. Neither alternative
was retained.

## D3. Use an explicit eight-position default schedule

The final cycle is C,W,B,W,C,W,C,W: three canonical-size draws, four witness
draws, and one broad draw. Two witness subtypes alternate and differ in the
first cell of the fourth row. Every four consecutive candidate positions
contains both subtypes. Their grids cannot be duplicates. Validating only
individual inputs would not establish that demonstrations teach the query;
the production census therefore uses actual assembly and recorded rejections.
The integration test additionally replaces a broad candidate by a duplicate
and checks the accepted lesson against every rival and held-out query.

A 25% canonical allocation first produced 11/60 profile hits and a pooled
warning. An intermediate randomized extra canonical slot retained morphology
but the small provenance sample happened not to visit the broad height draw.
The deterministic eight-slot allocation replaces that variance with explicit
coverage and declares LESSON_SCHEDULE_PERIOD=8 honestly. The final profile
check sees 17/60 exact hits with positive support in every band. The final
default input probe sees 151/150/150 canonical-size grids per 400 draws.

The final census checks 100 lessons per band, three demos plus one query,
requested start i=0..99 and the exact hash-derived per-band seeds recorded in
the report. It finds no declared-rival ambiguity in 300 ordered production
lessons or 1,200 query rotations. Its 1,200 labelled pairs comprise 522
distinct inputs. The additional production census enumerates every start
0..7 at seed zero for all three bands: 24 lessons, 96 rotations, 20 distinct
inputs. The focused unit test checks all eight starts at seeds 0,17,101 in
all bands using diagnostic outputs, a complementary check rather than extra
reference-labelled episodes.

The default census parameter named period is a residue-reporting modulus
(six in these receipts); schedule enumeration used the declared eight-slot
contract. I did not interpret the report's residue histogram as evidence of
a six-slot schedule. Query rotations were required, not merely diagnostic.
No larger counts or universal inductive guarantee are claimed.

## D4. Preserve real axis support and observable exact controls

General height, width and period draws mix 25% uniform sampling with 75%
difficulty-biased sampling over the same legal interval. Every legal value
retains positive probability in every band. Width includes three in hard,
unlike the baseline; canonical-size inputs are explicitly scheduled across
all bands. Known non-None overrides select general sampling and are exact
integer controls. Period > height-2 combinations are declared incompatible;
unrecognized keys and noninteger values reject visibly instead of disappearing
or truncating. The final 27,720-call public matrix passes with 900 expected
combination rejections, and the task regression covers 390 legal boundary
combinations plus 60 invalid ones in a separate explicit joint check.

An early weighted-choice implementation had genuine full numeric support,
but the shared axis provenance checker consulted only integer draw bounds
when both choice and bounded draws appeared. This is a reproduced shared
tool defect, with an optional patch under checks/proposals/axis-provenance/.
The applied generator uses direct bounded draws, so its final validation
does not depend on accepting or applying that shared proposal. The final
eight-slot adjustment also makes the broad branch observable to a short probe.
The shared checker was not weakened, suppressed, or edited.

Arbitrary overrides bypass the witness schedule. That behavior is explicit:
input validity and exact controls are supported, but identifiability of
override-selected lessons is unknown. A period-two-only lesson cannot be
claimed to refute every continuation rival. Generalizing curriculum guarantees
to all controls would require separate assembly semantics and evidence.

## D5. Keep authority changes semantic-free

The before battery failed authority synchronization because the selected
base solution's target_code text and canonical program text differed only
in formatting. Whitespace-normalized comparison and execution parity already
agreed. I replaced only target_code with the exact canonical program text.
The canonical ledger SHA remains
`b3d50b8662ac352a020f475ccd5d32de464a16bff1ee1b9ae13c8e7c226150db`,
the normalized rule pin remains `6358a7ca0f4d`, and archival raw_code is
unchanged. The final authority gate reports selected authorities synchronized,
archival text divergent, execution parity PASS. No reference rule was changed
to excuse an input or to satisfy a rival check.

## D6. Repair portability and retain genuine failures

The selected old test used a fixed parent-depth guess for the canonical file.
The public isolated task-test stage exposed that bug after pytest was made
available in its isolated interpreter. The selected test now uses
reviewer_support.find_root and canonical_pairs; the frozen root fixture was
not touched. New tests cover the actual defect behaviors, malformed-cell
inputs, exact controls, witness outputs and production duplicate handling.
Final selected tests report 42 passed and zero skips.

The first TDD regression run returned 20 failed/10 passed on the baseline.
The first repair passed those 30 tests, then the broader tests were added for
schedule, connected-family, duplicate handling and old-test portability.
Both failed after batteries are retained, not overwritten or relabelled as
successes. Their census successes remain intermediate because their generator
bytes differ from the final hash. Final evidence uses verified-* paths.

The initial blind-check infrastructure error was inode exhaustion, before a
scored revision existed. Only our extraction was relocated to shared memory;
55,276 copied files were byte-hash checked before the old extraction was
removed. The upload was untouched. Later isolated checks initially could not
import pytest; ordinary pip saw a user-site installation that python -I
could not load. An own venv with system-site packages and an isolated
PYTHONNOUSERSITE=1 offline pytest installation resolved that setup issue.
Those are environment failures, not invented unsuccessful solve attempts.

## D7. Bound the final claims and audit scope

The repair intentionally does not promise every legal grid is equally likely,
all hypotheses are distinguishable, or Qwen learning improves by a measured
amount. Witness height and morphology can themselves correlate; connected
variants have limited variety. Finite unique-input counts and the broad branch
make the tradeoff inspectable, but do not remove it. No approval state changes.

The two assigned audit sources were inspected and left unchanged. Their
ordinary production episodes were verified through the public API and Racket
apply, then compared with concrete natural rivals. `AUDIT.md` separates the
48/384 preliminary input draws from the one/three confirmed episodes and
states the tested and untested rotation policies. These witness ratios are
not prevalence estimates.

The post-repair solve prepared the final generator hash with three visible
demos and two queries. That solve record has no separate lesson-identifiability
verdict and is not counted in the three-demo/one-query census. Earlier rule
exposure is yes, no reference was consulted during the solve, visible score
is 3/3 on one revision, and masked-query correctness remains unknown.

The handoff requires applying the exact generated source patch to an original
packet extraction with a verified local Git root, then rerunning all focused
task tests. Source identity, runtime manifests and replay receipts are kept
under checks/replay/. The package builder validates allowed changed paths,
assignment identity, evidence inventory and return budgets.

The first packaging attempt rejected a direct edit to the protected imported
review_index.json. That edit was restored byte-for-byte from the assignment
baseline; the current task notes retain the evidence-backed resolution request.
No guard was bypassed. The failed package receipt is retained under
checks/packaging/attempt1.log, and the imported audit awaits maintainer disposition.

The completed clean-copy replay applied the exact source patch, verified all
12 changed file hashes, and passed all 42 task tests with zero skips. The task-local
feature gate also passed from the fresh layout. The final archive uses this
same source patch; only reports and evidence changed after replay.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/d07c7972d183/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
