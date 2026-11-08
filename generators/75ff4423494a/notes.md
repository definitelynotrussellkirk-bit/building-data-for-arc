# Working notes: 75ff4423494a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c3edb921acbb5111e3c9600d166742bdfd1fd7a831b12e54a9a09e559e58c88f`.

# Decisions for `75ff4423494a`

## Intended outcome and source leads

The target outcome was a generator that remains exactly faithful to the selected canonical Racket rule while producing useful three-demonstration lessons, exposing exact public controls, and retaining source-bound evidence. I used the immutable packet baseline, canonical pairs, selected base authority record, and the before battery as leads. There was no prior return or nonempty associated-note record to rely on; prior rationale for the baseline's many metadata axes was therefore **unknown**.

## D1 — Pin the authority and mirror it independently

**Choice.** Declare `RULE_HASH = "0124781298a5"` and implement a Python diagnostic oracle that independently follows the Racket data flow: select the largest multi-cell nonzero component containing 8; take the first row-major 8 in its bounding-box template as origin; copy at the original origin and every external 8; clip; resolve differing nonzero writes to 9.

**Why.** The baseline lacked a rule pin, and tests need a readable oracle without replacing Racket as authority. The task tests additionally call the live canonical Racket rule.

**Rejected alternatives.** Reusing the generator's own output helper as the sole test oracle would make shared bugs invisible. Changing the Racket program was unnecessary because all five canonical labels and generated probes agree with it.

**Failure mode / limit.** The Python mirror is still duplicate implementation code, not authority. Live parity tests and the battery rule-smoke stage guard against drift.

## D2 — Advertise only four exact, observable controls

**Choice.** Keep `grid_h`, `grid_w`, `n_anchors`, and `template_kind`. Reject unknown controls and validate strict types/ranges. Recover all four through `observe_overrides`.

**Why.** They are semantically meaningful, independently constructible, and visible in the returned input. The baseline metadata named controls that were never drawn or could not be recovered.

**Rejected alternatives.** Retaining decorative aliases, palette labels, or hidden layout modes would recreate a false exact-control contract. Advertising conflict/distractor booleans was also rejected because those are curriculum policy, not learner-facing task axes.

**Probe.** Final override stage: 101 cases, 9,090 accepted draws, zero findings in `checks/after-final/checks/75ff4423494a_after_override_results.json`.

## D3 — Preserve canonical morphology and profile support

**Choice.** Use the three exact canonical supports: `hook6`, `cross6`, and `step5`. Preserve the four canonical `(height, width, palette-size)` profiles `(9,10,4)`, `(10,11,4)`, `(9,12,4)`, and `(10,10,4)` in every band.

**Why.** This keeps the repair on the task-linked manifold rather than creating a superficially related copy puzzle.

**Rejected alternatives.** Arbitrary polyominoes would broaden visual diversity but weaken canonical ownership. Only replaying the five public inputs would be exact but would provide no new semantic teaching evidence.

**Failure mode / limit.** Default production uses only `cross6` and `step5` because both expose non-top-left origin alignment on every draw. `hook6` is still globally supported by exact override and canonical tests, but an all-hook default lesson could not distinguish the bounding-box-top-left rival.

## D4 — Make the default lesson contract rotation-safe

**Initial choice and failure.** The first repair used a six-profile schedule where adjacent-conflict cases appeared every third draw and ignored-foreground cases appeared every third draw. Ordered three-demo lessons passed, but the semantic smoke reported 14 ambiguous rotations out of 48. A failing regression captured the concrete case where the only ignored-foreground witness became the held-out query; `preserve_ignored_foreground` then fit all three demos.

**Final choice.** Every default draw now contains:

- at least two external destinations;
- an adjacent destination pair;
- a real differing-color overlap that yields 9;
- a prototype whose 8 origin is not its bounding-box top-left;
- payload colors other than the canonical pair `{2,3}`; and
- one isolated payload-colored distractor that the authority clears.

**Why.** With three demonstrations, any held-out member of a four-pair bundle still leaves three examples that each independently refute all seven declared rivals. This matches the downstream `--rotate-query` policy rather than relying on order.

**Rejected alternatives.** Keeping an ordered curriculum and marking rotations diagnostic was valid in principle, but less robust and inconsistent with the desired arbitrary-query support. Resampling only when ambiguity is detected would hide schedule weaknesses and complicate replay.

**Probe.** `checks/tdd-red-rotation.log` records the failure; `checks/final-required-rotations/` records 48/48 clean rotations; `checks/lesson-census-final.json` records 1,200/1,200 clean rotations.

## D5 — Use noncanonical payload colors but keep semantic color roles fixed

**Choice.** Draw distinct payload pairs from seven fixed pairs excluding `{2,3}` as a set. Keep color 8 as the marker and 9 as the authority-defined conflict output.

**Why.** The canonical demonstrations permit a strong shortcut that copies only colors 2, 3, and 8. Varying payload colors directly changes that shortcut's prediction. Fixed semantic colors 8 and 9 are not permuted because their roles are rule-defined.

**Rejected alternatives.** Full random color permutations would incorrectly treat marker and conflict colors as interchangeable. Always using 2 and 3 would preserve appearance but leave the shortcut unresolved.

## D6 — Construct overlap and distractor witnesses, do not sample for them

**Choice.** Search valid prototype origins and destination pairs until an orthogonally adjacent pair with a real color conflict is found. Add the ignored singleton only on an input blank that the authority output also leaves blank and that remains isolated.

**Why.** Witness claims should be deterministic properties of accepted draws. Randomly placing markers and checking afterward led to weak frequency guarantees and rejection risk.

**Rejected alternatives.** Retry-until-lucky generation was simpler but would make witness rates seed-dependent and could underproduce. Hand-coded full grids would eliminate geometric diversity.

**Failure mode / limit.** Exact `n_anchors=1` overrides cannot carry an adjacent-pair conflict. This is intentional: exact-axis support and the stronger default lesson policy are separate contracts.

## D7 — Model named rivals and witnesses as executable code

**Choice.** Declare seven `LESSON_COMPETITORS`/`SEMANTIC_RIVALS`, two `CANONICAL_SHORTCUTS`, six `SEMANTIC_WITNESSES`, and a `lesson_identifiable` hook that checks actual labeled demos and query predictions.

**Why.** Prose claims cannot establish that a rival both fits demonstrations and changes a query. Executable rivals let the semantic gate and lesson census retain exact evidence.

**Rejected alternatives.** A single aggregate "hard example" flag would not identify which hypothesis was ruled out. Claiming uniqueness from two human guesses was rejected.

**Limit.** The declared rival set is deliberately plausible, not exhaustive. Final `no_ambiguity_found` means no ambiguity among these hypotheses in the finite census.

## D8 — Normalize authority comments without changing semantics

**Choice.** Set the selected base record's `target_code` byte-for-byte equal to its `raw_code` by removing three comments that were absent from `raw_code`.

**Why.** Authority sync treats the two selected representations as one source. The executable forms were already identical after comment stripping.

**Rejected alternative.** Editing canonical Racket source or accepting permanent sync failure would add risk without semantic benefit.

## D9 — Testing and evidence policy

**Choice.** Add a portable task-local suite using `reviewer_support.find_root` and `canonical_pairs`. Tests cover all canonical pairs, exact controls in every band, invalid overrides, canonical profile support, shortcut fit/refutation, all cyclic starts and all four query rotations, malformed inputs, replay determinism/global RNG isolation, and live Racket parity.

**Why.** The general battery does not automatically discover task-local tests, and the rotation defect needed a permanent regression.

**Evidence policy.** Preserve red tests and interrupted battery state, then retain the final official task-test stage, required-rotation battery, and 300-lesson census. Report exact generator hash and denominators. Do not infer masked solve labels or universal identifiability.

## Composition annotation decision

No optional machine curriculum annotation was added. The task clearly combines contextual marker use with overlap resolution, but assigning the ARC-DESIGN categories would add a reviewer-reported taxonomy claim that was not needed for this repair. The exact semantic witnesses are retained instead.

## Native parametric build — ranked external anchor

**Decision.** Preserve exact canonical `all_anchors` as the default and add
`signal_ranked_anchor`. The alternative counts the separate color-1 signal and
uses its size as a one-based row-major external-anchor rank before copying the
canonical prototype at the origin and selected anchor.

**Why this parameter.** It keeps prototype discovery, origin alignment, clipping,
and conflict handling intact while adding an input-dependent selection step.
Inputs are setting-neutral, so demonstrations teach the changed rule rather than
a changed grammar. The first two demonstrations use ranks 2 and 4; four query
profiles extend through a substantive 30×30 scene.

**Self-review.** The finite audit covers both settings and eight named rivals
(first/last anchor, fixed ranks 2/4, reversed rank, row/component-count signal,
and omitting the origin). Across 64 seeds and demo counts 2, 3 and 6 it found no
harmful survivor and no public-projection failure. This is bounded evidence, not
a universal uniqueness claim.

**Causal claim.** Step A measures signal size; the intermediate is the rank and
selected external anchor; step B overlays the prototype there. A protected-Racket
wrong-rank counterfactual on the same qualified input changes the final output.
Owner exact-source qualification and acceptance remain pending; training remains disabled.
