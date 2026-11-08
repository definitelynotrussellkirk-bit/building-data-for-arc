# Working notes: fc814cec3976

## Current rule and authority

Version 3.1.0 keeps the canonical transformation: scan 3x3 red/gray windows with
a gray center and at least one red; sort by decreasing red count then reading
order; reject a window that reuses a selected red cell; color selected gray
centers yellow and other selected gray cells orange, with first-selected
precedence on gray-only overlap. The canonical Racket program is unchanged
(SHA-256 c6a87747a9a048bea1b71268e82dfa62bcf096b49cd904493952d1ba5c94b895).
The two bound base `target_code` fields were synchronized to its exact text;
archival raw text, canonical records, approval hashes, and unrelated tasks were
preserved. Imported history remains in `evidence/associated_notes.jsonl` and
`evidence/review_index.json`.

## Reversed support choice: R1

The imported 3.0.0 generator held the candidate-relevant context fixed for each
of 32 red layouts while varying inert background cells. This made a fixed
red-layout-to-window lookup sufficient. The old choice plausibly protected
canonical geometry and exact scene decoding; the author's further rationale is
unknown. Review review-7230dfb20b17ba07 adds one-to-three protected 0/5 edits to
21 nonidentity layouts from public_2, public_3, and public_4. Both original and
altered contexts are generated for the same red keys. The edits alter actual
candidate competition and selected centers while retaining the calibrated
19x19 palette, density, four selected windows, and complete red coverage.

The investigation found 24 suitable original/modified contexts and executed
all 48 inputs through canonical Racket. Only the 21 nonidentity variants enter
the production repair; identity profiles stay available for canonical-family
coverage. public_1 has four forced local winner geometries under these bounded
edits, so no unsupported variant is invented for it. The minimal final generated
pair is in `counterexamples/structural-contrast.json`; full investigation and
execution receipts accompany this return under `checks/canonical-investigation/`.

Five consecutive draws contain two structural contrasts. Six labeled pairs
therefore retain at least one contrast after any one query holdout. The actual
`red_layout_lookup` rival is declared under all three relevant namespaces as
one callable, with a linked counterexample witness and an explicit lesson hook.
The hook certifies only refutation of that named rival. There is no claim of
universal rule identification or geometric rotation equivariance.

## Validation and portability: R2–R4

Seed and sample-index arguments must be literal integers; indices must be
nonnegative. Seeds remain arbitrary signed Python integers. An intermediate
uint32 restriction was an authoring mistake caught by the native census's
48-bit seeds; it was removed and the real failing logs are retained. A cropped
16x16 grid with a known red key previously reached out-of-range code positions.
Wrong shapes now return validation errors before decoding. The focused test
also checks the strict-family and override-observation hooks.

Task tests now use `reviewer_support.find_root`, `canonical_path`, and
`canonical_pairs`, so they work in the staged runtime. Rule identity tests use
the declared whitespace-normalized rule identifier separately from the exact
program SHA. No frozen fixture was changed.

## Measured outcome and remaining limits

Final generator SHA-256:
416d21b39294a0c88facbf8a094b492fe5a2fc67ed24330852d0faa776b10189.
The returned final-source battery passes all 12 stages; portable task tests
pass 97/97 with no skips. The required semantic smoke test covers 600 strict
inputs, 60 Racket-verified shortcut witnesses, 12 lessons and 72 held-out roles.
The larger census materializes 300 lessons, 1,800 labeled pairs, and 1,800
held-out roles (1,737 unique input grids), with no ambiguity against the one
declared rival. Exact seeds, accepted indices, labels and source bindings are
retained in the return's census evidence; these are finite measurements.

The generator still has 32,765 exact scene codes, 32 red layouts, 53 candidate
contexts, and 15 inert bit positions encoding the scene code. A richer context
lookup or code decoder can still exploit that finite support. The historical
broader memorization concern is therefore only partially addressed; this return
does not close the retained review index or approve training admission. A
procedural topology redesign remains a separate, larger decision.

## Separate parameter proposal: P1

`workspace/parametric/` implements `min_reds` in {1,2,3}, chosen once per episode.
Its default Racket file is byte-identical to the canonical program; alternatives
change one eligibility predicate. All labels come from executed Racket. The
retained prototype has three episodes, twelve labeled pairs, all twelve query
roles distinguished across the three settings, and 43 Racket test-position
outputs plus three canaries. Its 13x19 six-motif scaffold is intentionally small
and separate from the dense-noise production family. Status: proposed prototype,
with no production parameter API, variant approval, or training admission.
## Current reviewer considerations

Source SHA-256: `416d21b39294a0c88facbf8a094b492fe5a2fc67ed24330852d0faa776b10189`.

# Decisions and limits

## R1: preserve the canonical reasoning while changing relevant context

The exact Racket program is the authority. Window eligibility, red-count
priority, reading-order ties, greedy red coverage, and first-selected gray
ownership stay intact. The default prototype program is also byte-exact.
Changing the window size, swapping fixed output colors, or altering tie order
would change the task; none was used to obtain a passing repair.

The imported generator used four canonical inputs and their eight D8
orientations. Its safe background positions cannot participate in a 3x3
window containing a red cell. Consequently, the 32 red keys determine 32
fixed selected-window masks despite many exact-grid variants. Preserving
canonical density and replayability seems consistent with that construction;
the original author's complete rationale is unknown.

I tested local candidate-relevant 0/5 edits while keeping red cells fixed.
The investigation tried 4,168 single-cell edits and then 5,152 bounded
completion/blocker patches. Twenty-four nonidentity-or-identity contexts from
public_2/3/4 retained the calibrated counts and changed selected centers;
all 24 paired originals/mutations were independently executed through Racket.
The selected repair uses the 21 nonidentity contrasts, each with one to three
edits. It keeps identity profiles untouched for canonical-family coverage.
public_1's four local groups each have a single feasible winner under this
bounded search, so a public_1 variant was not invented. These are finite
search results, not a proof that every conceivable public_1 redesign is
impossible. Exact inputs and search bounds are in `checks/canonical-investigation/`.

Keeping both contexts for a red key matters: merely replacing its old context
would allow an updated fixed lookup. The final support has 32 red keys and
53 candidate contexts, with two different center masks for 21 keys. The
small final-generated Racket pair is in the task's `counterexamples/`.

## Density, exact overrides and the remaining finite support

The repair retains 19x19 shape; input colors 0,2,5; 177–223 gray cells; 10–16
red cells; four selected windows; four through seven candidates; and full
selected red coverage. Safe-noise filling now counts gray cells after
structural edits, avoiding an accidental change in the density budget.
`scene_code` still spans 0–32,764 and identifies exact reproducible inputs.
The existing protected bit positions and safe noise construction are retained.

An alternative would replace the finite bank with procedurally placed red
groups and independently sampled relevant backgrounds. That would address
more of the memorization concern, but requires a new calibrated domain,
override inversion strategy, candidate-competition coverage and fresh
distribution review. I did not disguise the present bounded repair as that
larger redesign. There are still fifteen inert code bits and 53 contexts;
this is an explicit remaining training-policy decision.

## Five-demo lesson assembly and named rivals

The natural lane is `(seed + sample_index + band_index) % 5`. Lanes 1 and 3
provide structural refutations, lane 0 preserves the official family, and
lanes 2 and 4 use ordinary transformed contexts. In every five consecutive
draws exactly two lanes refute the fixed red-layout lookup. In six labeled
pairs, withholding any one pair leaves at least one refutation. Five demos
are chosen to provide that simple bound without output-dependent filtering.

The bound covers lane scheduling, not a claim that all seeds or plausible
ARC programs are empirically exhausted. The final semantic battery requires
rotation identifiability and measures 12 lessons/72 held-out roles. The final
public census measures 300 lessons/1,800 roles and 1,737 unique input grids,
100 lessons per band with requested starts 0–99. The actual accepted indices
and exact labels are retained. Query rotation here means changing which
labeled pair is withheld; it does not mean a geometric symmetry of the rule.
`LESSON_SCHEDULE_PERIOD` is not asserted for the full input sequence, which
also depends on the finite variant arithmetic.

`red_layout_lookup` fits all eight canonical records, so it is valid as a
canonical shortcut. All three declaration namespaces alias that one callable.
The witness claims are checked against canonical Racket, not accepted merely
because a Python mirror says they disagree. The lesson hook only assesses
the named competitor; it does not promise universal teachability. Generic
searched label-mutation diagnostics in the public tool are advisory and are
not independent model-evaluation results.

## R2: literal scalar validation and an actual reversed implementation choice

Booleans must not silently act as seeds or indices, and indices must be
nonnegative. I initially also constrained seeds to uint32. The native profile
and semantic censuses immediately refuted that assumption with a legitimate
48-bit seed (`169446987945668`). That was my implementation error, not a
failure of the original generator's seed domain. I removed the range bound,
preserved negative and arbitrarily large integer seeds, and added regressions
for -1, 2**32, the actual failing seed, and 2**96+17. Both the red run and the
intermediate failed battery remain in the return.

## R3–R4: precise authority, portable tests and total rejection of malformed shapes

Two selected base `target_code` strings differed from canonical only in
formatting. The supported authority-sync proposal was inspected and applied
only to these two fields. Canonical `program_solution`, raw archival strings,
and approval metadata were preserved. Normalized rule ID and exact text hash
are distinct measurements and are now tested as such.

The mutable task test used fixed ancestor offsets and private module imports,
which failed in the staged runtime. It now uses the public reviewer helpers.
The calibrated rejected-candidate count permits one as well as zero, two or
three, because a valid new contrast has five candidates with four winners.
This intentional support extension is separate from fixture portability.

Independent review found a known-key 16x16 crop that crashed code decoding.
Appending a shape error while continuing was insufficient; the analysis now
returns immediately on the wrong calibrated shape. The regression checks
`self_check`, `strict_canonical_like`, and `observe_overrides`. This is a
validator robustness repair outside generated support; it changes no valid
19x19 label or draw.

## P1: implemented parameter proposal

The chosen parameter is the minimum red count for candidate eligibility:
`min_reds` in {1,2,3}, canonical default 1. It changes one small predicate
while preserving scanning, ranking, greedy overlap and recoloring. Choosing
window size instead would alter more geometry and teaching structure; choosing
only output colors would add superficial variation. A threshold has visible
same-input counterexamples and a small fully enumerated parameter set.

The prototype selects one setting before drawing an episode, then constructs
three demonstrations and one query on independent 13x19 motif scenes. Every
input has threshold boundaries and genuine candidate competition. Inputs do
not depend on the chosen setting. The exact instantiated Racket file supplies
all labels, and all three settings are evaluated on all four pair inputs
before checking each held-out role. Rivals are eliminated only by demos;
hidden query correctness is never used to eliminate a surviving rival.

The retained seeds 4,0,1 choose thresholds 1,2,3. Twelve chosen labels, twenty-four
alternative-setting labels, three same-input setting outputs and four unique
canonical outputs account for 43 test-position Racket outputs; three canaries
are additional backend checks. All 12 query roles distinguish the three
settings. These are bounded prototype results, not approval or coverage of
the production dense-noise domain. `workspace/parametric/README.md` provides
the runnable materializer and exact parameter-program hashes.

## Exposure, audits and adoption

The unrelated blind solve preceded target-specific repair inspection and
passed its three visible examples. The final repair-task solve is explicitly
exposed and passes five visible examples; both hidden outcomes remain unknown.
The previous solve is preserved with its original hash and conservative
reference-consultation declaration.

The two random audits are findings only. The first shows actual demo-fit/query
disagreement for an undeclared positional rival; the second shows a key-ignoring
shortcut throughout generated support, plus a validator-accepted off-support
pair proving that the key can matter. Those are different failure types and
are reported separately in `AUDIT.md`. No audited target was modified.

Acceptance needs attention because the finite-code support limitation remains.
The historical retained review index is not edited to imply closure. The
canonical repair, proposed parameter family, passive tool proposal and audit
findings each have their own evidence and scope; none changes training admission.

## P2 — Promote `min_reds` to a native 2–6 demo / four-query family

**Decision.** Preserve the exact canonical `min_reds=1` program and retained
`min_reds=2,3` predicate-only alternatives, while adding native
`program(settings)` and `generate(seed, settings, demos, queries)` entry points.
The contract supports 2–6 demonstrations and 1–4 queries; qualification uses
three demonstrations and all four queries.

**Construction.** Every setting receives identical deterministic inputs. Demo
and query streams are independently keyed and prefix-stable. Every scene keeps
isolated one-, two-, and three-red threshold examples, a count-priority overlap
competition, selected windows that share gray cells, and a gray-only
distractor. Thus each demonstration separates all three settings while retaining
candidate ranking, greedy reused-red rejection, and first-selected precedence.
The fourth query is 30×30 with 25 separated motif slots, at least 180 nonzero
cells, at least 20 eligible windows, rejected candidates, and selected gray
overlaps.

**Evidence.** All 33 tests in the focused file pass when split at the bounded
Racket stages, including the historical 43-output materializer. The complete
task suite passes 113 tests. Native qualification covers all three settings on
seeds 0 and 17 with three demonstrations, four queries, and 78 protected-Racket
evaluations. Public projection produces 24 verified single-query views and the
first-turn checker covers six starts plus 36 invariance mutations.

## P3 — Bind greedy selection to downstream first-hit recoloring

**Sequential dependency.** Step A enumerates and ranks eligible windows, then
greedily produces an ordered list whose red cells are disjoint. That ordered
list is the input-dependent intermediate. Step B uses the first selected window
containing each gray cell to choose center color 4 versus non-center color 7. A
protected-Racket `skip_a` witness replaces the selected list with all candidates;
rejected overlapping windows then recolor additional cells and change the final
grid.

**Adversarial review.** The bounded audit covers seeds 0 and 17, demo counts 2
and 6, all four query profiles, all three settings, 32 all-setting separations,
18 direct protected-Racket labels, and 96 setting/pair rejections of the
skip-greedy shortcut. Native qualification supplies the independent full
source-bound replay.

**Status and limit.** Adapter, contract, current inventory, qualification,
execution evidence, public projection, and causal witness are ready for owner
acceptance. These finite scenes do not prove universal identifiability or broad
production-distribution coverage, and no training admission is implied.
