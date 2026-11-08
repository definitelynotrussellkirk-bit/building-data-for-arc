# Working notes: 0dba62203065

## Review diagnosis (2026-09-28)

The imported `2.2.1` generator did not represent its own summary or the public task:

- the summary claimed two or three sparse legend markers, while the canonical inputs and code use a full header row;
- header colors were independent random values in `2..9`, rather than a cyclic `2..8` sequence;
- reserving rows 0 and 1 in `grow_blob` also blocked row 2 through the helper's adjacency rule, so ordinary objects began too low and row-1 examples were impossible;
- objects could occupy the final column even though the selected Racket rule excludes that column from its body subgrid;
- four helpful textures were byte-identical, two declared degenerates passed `self_check`, exact axes were not observed, unknown overrides were swallowed, and `RULE_HASH` was missing;
- `self_check` accepted nearly every structural impostor.

## Implemented contract

Version `3.1.0` pins `RULE_HASH=75437b07b887`, uses exact observable axes, rejects unknown overrides, emits the three official dimensions on a deterministic cycle, and validates the full body grammar. The semantic contract names four rivals:

1. use the row-major first cell's column;
2. recolor each cell independently from its own column;
3. assume row 1 is always blank;
4. recolor only object sizes at most three.

The fourth rule reproduces every public pair because all public objects have size two or three. Alternating size-four examples are therefore a generated counterexample to a real canonical ambiguity. Two consecutive samples also contain a row-1 object and every sample contains a first-cell-versus-bbox-left trap. Easy, medium, and hard are no longer a dead control: their default header-direction distributions are ascending-only, mixed, and descending-only respectively, while overrides remain exact.

## Follow-up review (2026-10-03, assignment review-9e230aa538d1234f)

The accepted 3.1.0 generator passed the inherited before battery 12/12, but its
entire header distribution remained cyclic. A runnable rival could read only
header cells 0 and 1, reconstruct the full 2..8 cycle, and ignore the actual
header entry above every object. That rival matched all three public pairs and
all 300 unique lessons in a deterministic 100-per-band diagnosis. See
`checks/diagnosis/cycle_shortcut_before.json` in the review return.

Version 3.2.0 keeps the public six-axis override API and the selected Racket
authority unchanged. Row-2 lessons retain exact cyclic headers. Row-1 lessons
swap one header value above an object left edge with a non-anchor value, while
preserving the first two header cells and the full color multiset. The new
`cycle_from_first_two` executable rival therefore still fits every public pair
but is refuted in every row-1 lesson. The existing `row_one_body` witness claims
both the separator-row and cycle-reconstruction rivals, avoiding a gratuitous
public witness/API expansion.

The swap constructor also preserves the prior first-cell-column trap. An early
implementation allowed the swapped anchor and the trap's topmost-cell header to
become equal in 4/300 sampled lessons; seed 110043/sample 43 is retained as a
regression test. The corrected constructor rejects such swaps before returning.

The source-bound final probe sampled 100 lessons per band with seeds
`100000 + band_index*10000 + sample_index`, indices 0..99. It found 300/300
unique inputs, 150 cyclic and 150 anchor-swap headers, 150/300 refutations of
the cycle shortcut, 300/300 refutations of first-cell and per-cell lookup,
150/300 refutations of the row-1 and size-threshold shortcuts, and 297/297
identifiable two-demo windows. See
`checks/probe/0dba62203065_review_probe_100.json`.

Remaining limitation: the non-cyclic lesson profile is deliberately coupled to
row-1 examples rather than exposed as a seventh override axis. This preserves
the accepted external API and makes every ordinary two-demo window decisive,
but it introduces a curriculum correlation that future revisions should
monitor rather than silently generalize away.

### Exhaustive partner-search regression

The first after-battery retained in `checks/after-failed-anchor-swap/` found one
crash in the 600-draw semantic census:
`generate(easy, seed=225536731915187, sample_index=4037)` raised
`ValueError: cannot construct anchor_swap legend profile`. The layout had only
one eligible anchor. Its shuffled partner list began with a partner that would
have collapsed the established first-cell counterexample, and the constructor
incorrectly abandoned that anchor instead of trying its remaining valid
partners. A test now freezes the exact census seed/index, and the constructor
iterates every shuffled partner before failing. The final semantic gate is
600/600 strict draws, zero crashes, 12/12 identifiable lessons, and the complete
after battery is 12/12 green. Final generator SHA-256:
`6e12f3ea80b5735dc1ed12568cc7c1c18c8d3453b0f9542381df7492f57bf7a3`.
## Current reviewer considerations

Source SHA-256: `6e12f3ea80b5735dc1ed12568cc7c1c18c8d3453b0f9542381df7492f57bf7a3`.

# Decisions for `0dba62203065`

## D1 — Treat cycle reconstruction as the highest-value remaining shortcut

**Original state and rationale.** Version `3.1.0` intentionally used full cyclic
headers because that matched all public examples and made direction an explicit
difficulty control. The inherited 12-stage baseline battery was green.

**New observation.** The entire header was a deterministic function of cells 0
and 1. A runnable solver could therefore ignore the lookup entry above each
object. The rival fit all three public pairs and all 300 unique baseline lessons
in the 100-per-band diagnosis.

**Alternatives considered.** Leave the distribution unchanged because the
battery passed; merely document the ambiguity; or add a rival declaration
without generating counterexamples. All three leave the shortcut learnable and
unfalsified.

**Decision.** Add a controlled non-cyclic profile and make
`cycle_from_first_two` executable in `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`,
and `CANONICAL_SHORTCUTS`.

**Probe and limitation.** The final probe measures 150/300 direct
counterexamples and 297/297 identifiable sliding windows. This supports the
specified deterministic sampler, not every possible seed.

## D2 — Use one anchor/non-anchor swap instead of arbitrary header permutations

**Goal.** Break the cycle shortcut while retaining the task's lookup-table
structure and all seven header colors.

**Alternatives considered.** A fully random permutation would create a much
broader distribution than the public task and would erase the useful direction
control. Swapping two arbitrary columns could change no object-relevant lookup
cell, producing a visually non-cyclic but semantically useless lesson.

**Decision.** Preserve cells 0 and 1, choose a real object bounding-box-left
column at index 2 or later, and swap its header value with a non-anchor column
whose value differs. This preserves the complete color multiset while forcing
the actual lookup cell to matter.

**Failure modes checked.** `self_check` accepts only an exact base cycle or one
two-cell swap beyond the first two cells, and requires the changed columns to
include a real object left edge.

## D3 — Couple the new profile to the existing row-1 schedule

**Alternatives considered.** Add a public `legend_profile` override axis; add a
fourth public witness; or choose the profile independently at random.

**Decision.** Use `body_origin == 1` for the anchor-swap profile and
`body_origin == 2` for the exact cyclic profile. The existing `row_one_body`
witness now claims both `skip_row_one` and `cycle_from_first_two`.

**Rationale.** This preserves the accepted six-axis override API and the frozen
three-witness interface while guaranteeing that every consecutive two-demo
window contains one counterexample.

**Known limitation.** Header profile and body origin are correlated. A future
revision may expose an orthogonal axis after coordinating an API change, but
this review did not silently break the current contract.

## D4 — Preserve the prior first-cell-versus-bbox-left counterexample

**Observation.** A header swap can accidentally make the trap object's true
left-edge color equal the color over its row-major first cell. That would make
the existing `first_cell_column` rival agree despite the geometry.

**Probe.** The first draft produced this collapse on 4/300 sampled lessons;
medium seed `110043`, sample `43` is retained as a regression.

**Decision.** Reject any swap for which those two header values become equal.
The final probe refutes `first_cell_column` on 300/300 lessons.

## D5 — Exhaust all candidate partners before declaring construction failure

**Failed implementation.** The constructor shuffled valid partners but tested
only the first. If that first partner violated D4, it moved to the next anchor;
with a single eligible anchor it raised even though later partners were valid.

**Evidence.** The retained intermediate battery found exactly one crash in 600
semantic census draws: easy seed `225536731915187`, sample `4037`.

**Decision.** Iterate all shuffled partners for each shuffled anchor. Add the
exact census call as a test before changing production code.

**Result.** Final semantic gate completed 600/600 draws with zero crashes.

## D6 — Keep the selected Racket authority unchanged

**Probe.** Canonical parity, rule smoke, Racket lint, authority sync, and the
exact witness application all agree with rule hash `75437b07b887`.

**Decision.** Change only the lesson distribution and semantic contract. The
repair teaches solvers to read the authority's actual lookup input; it does not
require changing the authority.

## D7 — Extend a source-bound task-local probe instead of relying on the smoke sample

**Need.** The baseline battery was fully green even though the cycle shortcut
held on every generated lesson.

**Decision.** Expand `workspace/review_probe.py` to derive rival names from the
module declarations and report the final generator hash, exact sampler, unique
input counts, profile counts, all rival disagreements, witness counts, every
consecutive two-demo window, difficulty contrasts, canonical parity, and
boundary overrides.

**Sampling choice.** Exactly 100 samples per band, seeds
`100000 + band_index*10000 + sample_index`, sample indices `0..99`.

**Rejected claim.** These measurements are not presented as exhaustive proof of
all possible generator outputs.

## Native parametric review (2026-10-24, assignment `review-d291997af6a7de66`)

The task-local native family now exposes one episode-fixed `repeat_policy`:

- `retain` is the exact selected canonical Racket program byte-for-byte;
- `mark_repeated` first performs that lookup, then recomputes the resulting body
  objects and paints color 9 on every object whose looked-up color is shared by
  another object.

The required dependency is therefore not merely code order. Step A maps each
body object through the header above its bbox-left column. Its input-dependent
intermediate is the set of post-lookup object colors and their object-class
multiplicities. Step B consumes those multiplicities to decide which complete
objects are eligible for the color-9 mark; before Step A every object is blue,
so the eligibility partition does not yet exist. The retained protected witness
uses a `wrong_intermediate` counterfactual that keeps Step A but treats every
post-lookup color as unique.

The constructive sampler keeps matched inputs across settings, distinct left
anchors, one mixed-size repeated lookup-color class, unique lookup-color
classes, a non-anchor header-frequency decoy, row-1 and right-boundary objects,
and the source task's blank final body column. It supports 2–6 demonstrations
and 1–4 queries independently; the four-query bank reaches 30x30 with eight
objects. The finite self-audit covers the other declared setting plus fourteen
named shortcuts: bbox/row-major/right-edge/center/per-cell lookup, size caps,
row-1 omission, cycle reconstruction, and six incorrect repeat-mark policies.
These finite rivals do not prove universal uniqueness.

The selected production generator and canonical Racket authority remain
unchanged. Native qualification and the protected causal witness are reviewer
handoff evidence only; exact-source owner acceptance and any training admission
remain separate pending decisions.
