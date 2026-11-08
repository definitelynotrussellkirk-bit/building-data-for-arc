# Working notes: d01b33f4a589

## Review review-9e5284a260d20a42 (2026-10-02)

Baseline generator version 3.0.0 / SHA256
`51adc00974fa848ec7ccd9c7552d8a2e6bb6f71656694c9867465b9f7ae505fe`.
Final generator version 3.1.0 / SHA256
`52b10583ab11154a71c7178c961bd98beeeae8c57ca8893c868476af09a17d66`.
The canonical rule's whitespace-normalized SHA256 stays
`0bc6b5986853ec262f10f7d8bc82118bf00d706ab6e55c0820bb5475f8dc30ab`.

**R1: Individual correctness did not make complete lessons informative.**
At baseline seed 661, difficulty easy, demonstration indices 0..3 omit command
4 and query index 4 introduces it. The rival `command_4_as_3` fits the entire
lesson but gives a different query. Other seeds have symmetric motifs that
alias commands despite exposing their colors.

The repair is a seed-phased period-four anchor, not a retry-until-lucky sampler.
At the anchor index generate an asymmetric L4 with the four commands and one of
23 non-public command orders. All thirteen declared rivals differ on that
single demonstration. The other three slots retain the original conditional
profile distribution; exact overrides disable this schedule. Generate the
phase context BEFORE the axis context so provenance observers see the correct
last GenCtx. A regression test protects this ordering.

Every four consecutive raw draws contain an anchor. Duplicate-input rejection
by the existing lesson runner cannot erase this evidence: a rejected duplicate
anchor means an identical informative input was already accepted. This argument
assumes the ordinary valid-draw path, shared seed and difficulty, and at least
four demos. It does not cover filtering by arbitrary external predicates,
nonconsecutive mixing, changed contracts, or explicitly pinned scenes.

**R2: Archival authority drift.** The selected archival target_code contained
three extra comment lines relative to its raw_code and the canonical ledger.
The existing baseline authority gate failed. Only that selected string was
synchronized to the existing raw_code; canonical source and executable behavior
were not changed. Exact before/after source diff is retained with the review.

## Measurements (not model training)

The return's `checks/lesson-before.json` and `checks/lesson-final.json` compare
12,288 draw requests each: seeds 0..255, indices 0..11, difficulty default/easy/
medium/hard. Those form 8,192 overlapping four-demo/one-query lessons, starts
0..7. Python-mirror ambiguity against actual declared rivals falls 297 -> 0;
all thirteen rivals are refuted in all final windows. Default and medium overlap,
so these are NOT 8,192 independent samples. Unique input grids fall 5,905 ->
5,118; unique output grids are 2,924 -> 2,923. This loss of scene diversity is an
explicit cost, not hidden evidence of improvement. Literal public draws are
630/12,288 before and 597/12,288 after. No trained-model result is claimed.

The independent Racket subset (`checks/verified-racket-{before,final}.json` in
the return) covers seeds 0..15 and the same indices/bands/starts: 768 requests,
512 overlapping lessons; ambiguity is 24 -> 0. No Python/Racket disagreements
or invalid grids appeared. A separate actual-runner check of 128 assembled
lessons (seeds 0..3, starts 0..7, four bands) gives 10 -> 0 ambiguities. The
seed-661 reproducer is separate from these denominators.

The final full twelve-stage battery and standalone lint pass. Frozen portable
fixture tests pass from a newly prepared, relocated runtime; new task-local tests
must also be run explicitly (the root test suite does not discover them).
Preserved failure history and exact commands are in the returned RESULTS.json.

## Scope and remaining work

Do not expand beyond the five demonstrated motif/canvas families merely to
inflate support. Public-profile grammar is deliberately narrow, while the
rule mirror and canonical Racket behavior remain broad. More D4 rivals, different
packing assumptions, variable demo counts, and adversarial post-filtering are
reasonable future probes; they are not covered by the present thirteen-rival
contract. Deterministic schedule position is metadata, never a visible-grid
answer cue, but shuffled/reassembled lessons need their own acceptance gate.
Evaluate a fixed-token, matched-compute learner experiment before deciding that
fewer ambiguous lessons outweigh the decreased distinct-input support.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`; those files are unchanged.
## Current reviewer considerations

Source SHA-256: `52b10583ab11154a71c7178c961bd98beeeae8c57ca8893c868476af09a17d66`.

# Decisions and rejected alternatives

All source hashes, sample populations, and commands are indexed in REVIEW.md and
RESULTS.json. R1/R2/I1/I2 refer to the corresponding finding IDs there.

## R1: Repair information in complete lessons, not just individual grids

**Original rationale:** the source documents canonical-profile calibration,
varied orientation/position/color, difficulty-weighted shapes, both command
multisets and a small literal-public prior. Independent selection appears to
have favored marginal diversity; its author's lesson-identifiability rationale
is unknown. Prior retained evidence already named the command-4 gap.

**Evidence:** baseline seed 661/easy/indices 0..3 lacks command 4, while index 4
needs it. A command-4-as-3 rule fits demonstrations but fails the query. Other
failures arise from symmetric figures, so merely including every command color
is insufficient. The Python census finds 297/8,192 ambiguous windows and the
independent subset 24/512; see the two before probe JSONs.

**Chosen:** one deterministic informative slot per four draws, with a
seed-dependent phase. Use L4 because its four command transforms are distinct,
including differing rectangular orientation. Use all four codes and uniformly
choose one of 23 non-public permutations to break the canonical profile/order
shortcut simultaneously. Any four consecutive slots cover the witness. This
needs no cross-call mutable state, retries, or hidden answer storage.

**Rejected alternatives:** always emit asymmetric motifs or only permutations
would remove useful canonical symmetric/repeated-command coverage. Increase
witness probability alone would lower average risk without a per-lesson
contract. Retry whole episodes until every rival is refuted is reasonable in a
training assembler, but would require shared changes here and can conceal retry
cost or biased acceptance. Globally redesigning the runner is out of scope.

**Assumptions and proof boundary:** common seed/difficulty, no explicit
overrides, ordinary consecutive generation, at least four demonstrations.
If the runner rejects an anchor as a duplicate, the already accepted identical
input supplies the same informative output. This does not justify guarantees
under arbitrary filtering or remixing. A smaller demo budget is intentionally
not certified. The actual runner is probed separately from raw windows.

## Preserve semantic override and geometry contracts

Keep both exact axes, all ten axis combinations, valid color reuse, all five
original shapes and their linked canvas sizes. Explicit overrides disable the
schedule: asking for repeated-two commands must not secretly produce a fourth
command or different motif. Unknown axes keep their existing rejection behavior.
The output rule and broad mirror are unchanged. We did not invent new motif
families, noise, bigger canvases, or a new training objective merely to inflate
support. Frozen fixtures still check strict grammar, public pairs, broad mirror
behavior, transformations, and difficulty ordering.

A schedule context initially became the last GenCtx and hid the true axis
context from provenance consumers (I1). The minimal repair is ordering the phase
context before the generation context; no changes to observers or shared code.
This is documented as a real intermediate failure and protected by a regression.

## Distribution tradeoff, explicitly accepted

Anchor frequency is exactly one quarter by slot. In ordinary slots original
conditional profile probabilities remain. Expected L4 shares become 0.50 easy,
0.40 medium/default, 0.325 hard; other profile shares are scaled by 0.75.
Permutation/repeated-two shares become approximately 0.85/0.15 instead of
0.80/0.20. Literal public draws are prohibited on anchors; their conditional
probability on ordinary slots is multiplied by 4/3 to retain an approximately
5% overall prior. Exact overrides retain their original literal behavior.

We kept the public prior rather than dropping all literal cases: the original
library intentionally tracks canonical support, and lawful non-public
recombinations remain dominant. Uniformly applying the literal probability to
anchors would destroy their guaranteed counterexample. Explicit task-local
witness predicates observe actual returned grids, not just planned schedule IDs.

Measured unique inputs decline from 5,905 to 5,118 in the fixed 12,288-request
population, while unique outputs are 2,924 and 2,923. The improved finite-rival
identifiability is the reason to accept this cost provisionally. VERSION changes
RNG identity, so this is a deterministic fixed-coordinate distribution comparison,
not a paired common-random-number causal estimate. A model experiment should
match tokens/compute and compare both held-out accuracy and duplicate-adjusted
support before permanently raising this family's training weight.

## Executable, finite contracts rather than unverifiable assurances

Declare twelve single-command substitutions as lesson competitors and one
public-profile/order rule as a canonical shortcut and lesson competitor. The
latter fits all five public pairs; alias competitors need not, and are not
misdeclared as canonical shortcuts. The witness refutes all thirteen. The
lesson hook checks whether a surviving rival actually changes the query, and
never reads a query label. It does not prove arbitrary-program uniqueness.

The reusable probe consumes declarations instead of maintaining another rival
list; checks canonical fit; records source and rule hashes; measures every cyclic
start twice; separates raw windows from materialized runner lessons; and keeps
full seed-661 counterexamples. We rejected "all rivals must always be refuted"
as the acceptance condition because a rival can survive harmlessly while agreeing
on the current query. The final schedule happens to refute all rivals, but the
hook and scorer do not require that stronger property.

The independent Racket mode initially failed because importing shared runtime
helpers first cached a package lacking the temporary per-task module path (I2).
Explicitly bind the requested sampled module in the existing GeneratorBundle;
do not mutate the cached package or shared runner. A live-Racket CLI regression
covers this path. Python-only reports are clearly labeled non-independent.

## R2: Synchronize text without altering the task

The canonical ledger and archival raw_code already agreed. The selected
archival target_code differed only by three comments; its normalized hash failed
existing checks. Change only that target string to existing raw_code, preserving
all other JSON fields and executable meaning. Retain both file hashes and exact
comment diff. We rejected weakening the hash checker, changing the canonical
program to follow drift, or patching frozen fixtures. Source provenance remains
verifiable and the actual training rule is unchanged.

## Scope discipline and testing outcome

Audit targets were drawn once and are findings-only. Their incorrect shortcuts,
public-input rejection, semantic descriptions and ignored palette overrides are
supported by actual Racket counterexamples; no unrelated generators were patched.

The root suite's startup-dependent timeout failure T1 remains unmodified. It
reproduces without the generator; the diagnostic shows disabling Python site
startup or allowing 1 s gets the expected progress text. A maintainer can isolate
that test's child environment, but fixing a shared test/infrastructure contract
would exceed this packet's allowed delta. This is why RESULTS lists a remaining
failure rather than claiming every repository test passed.

Fresh solve uses final generator bytes, visible examples only during the phase,
and an honest earlier-exposure declaration. Retain the genuine one-revision
success on visible examples; do not fabricate a failed attempt or infer hidden
query correctness from execution. No training accuracy, model trace, or approval
status was invented.

## Native parametric review — 2026-10-25

Built a source-bound `application_policy` family without changing the approved
production generator or canonical authority. `independent` is the exact canonical
Racket program; `cumulative` applies each corner command to the previous transformed
motif and packs the four prefix states. Inputs are setting-neutral, support 2–6
demonstrations and 1–4 prefix-stable queries, and include 14×16, 18×21, 24×27,
and 30×30 query canvases.

A native qualification dry run exposed a real construction defect: the original
large motif profiles yielded 40×40 and 50×50 outputs, outside ARC’s 30×30 grid
limit. A failing output-bound regression was added first; motif footprints were
then reduced while retaining the 30×30 dense input stress case. Final largest
input and output are both 30×30.

The required dependency is order-sensitive: step A produces four cumulative
transformed motif grids; step B measures and packs those exact states. The
protected counterfactual resets to the original motif for every command, replacing
the intermediate with independent transforms and changing the final 30×30 grid.

Retained evidence: 60 focused parametric tests; 83 complete task tests; a
12-episode audit with 92 selected labels, 120 rival checks, and no findings;
native qualification for 2 settings × seeds 0/17 with 40 protected-Racket
evaluations; 16 verified one-query public views; and a protected causal replay.
Inventory SHA-256 is `f7a468545223e8eb74c2372890f1f204ec68a20b81f10bbb58acbe63c938b91c`.
Owner exact-source integration and acceptance remain pending; no training
admission is claimed.

